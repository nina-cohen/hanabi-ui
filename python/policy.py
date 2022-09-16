import util.observation_reader as reader
import util.action_reader as action_reader
import util.card_utilities as cu
from util.decision_basis import DecisionBasis
import copy
from util.hint_nugget import HintNugget

class MyPolicy():

	# Note: When fitting into ISC gym, must hard code the chosen decision model in this method rather than expecting one to be passed in.
	def __init__(self, decision_model):
		self.verbose = True
		self.decision_model = decision_model
		self.record = ""

	def game_reset(self, agent_id):
		# reset your agent. get it ready for a new game
		self.my_not_clues = []
		self.other_player_not_clues = []
		self.singled_out_cards = [False for i in range(5)]
		self.cached_observation = None
		self.cached_card_knowledge = [cu.get_empty_clue() for i in range(5)]
		self.errors = []

		# you should keep track of agent_id
		self.agent_id = agent_id
		
		# Some information is not tracked in the observations and must be recorded here
		self.my_not_clues = [cu.get_empty_not_clue() for i in range(cu.HAND_SIZE)]
		self.other_player_not_clues = [cu.get_empty_not_clue() for i in range(cu.HAND_SIZE)]
		self.cached_observation = None

	def get_actions(self, observation):
		# observation is the full state dictionary
		# pull out your agent's observation
		my_observation = observation["player_observations"][self.agent_id]

		# Update not clues
		self.update_other_player_not_clues(my_observation)
		# The method below also checks the previous move against the observation change
		self.update_my_not_clues(my_observation)

		# Distill the observation into quantities that influence our upcoming decision
		playable_probabilities, safely_discardable_probabilities, unneeded_probabilities, hint_nuggets, _, singled_out_playable_card_index = self.run_checks(my_observation)
		
		# Store a cache of the observation so that we can infer hints from observation changes
		self.cached_observation = copy.deepcopy(my_observation)

		# Apply the decision model. Pass in all of the distilled quantities that we calculated earlier in this method.
		next_move, _, tied_top_moves, _, _, _ = self.decision_model.decide_move(my_observation, self.my_not_clues, self.other_player_not_clues, playable_probabilities,
			safely_discardable_probabilities, unneeded_probabilities, hint_nuggets, singled_out_playable_card_index, self.singled_out_cards, self.say)
		
		# Build a decision basis to return as well
		move_index = -1
		legal_moves = reader.get_legal_moves(my_observation)
		for i in range(len(legal_moves)):
			if legal_moves[i] == next_move:
				move_index = i

		decision_basis = DecisionBasis(my_observation, self.my_not_clues, self.other_player_not_clues, playable_probabilities, safely_discardable_probabilities, unneeded_probabilities,
		hint_nuggets, singled_out_playable_card_index, self.singled_out_cards, move_index)

		return next_move, copy.deepcopy(decision_basis), tied_top_moves
		
	def update_other_player_not_clues(self, my_observation):
		# This method also edits the cached observation so that my discards and plays don't get interpreted as hints from the other player.
		
		index_player_who_just_moved = int(not reader.get_current_player(my_observation))
		
		latest_action = my_observation["prev_move"]
		
		# If the latest action is None, then this is probably the start of the game and there is no maintenance to do.
		if latest_action is None:
			return

		# If the latest action is a discard or a play that I made, adjust my not_clues and the observation cache in relation to my card knowledge.
		# By adjusting the observation cache, I can ensure the only differences in my card knowledge from the observation passed in and my cached observation
		# is due to a hint I received from the other player.
		if index_player_who_just_moved == self.agent_id and not action_reader.is_action_hint(latest_action):
			index = latest_action["card_index"]
			# Adjust the cached singled out cards. We'll piggy-back adding a new False to the end of the array when we check whether an empty clue should be added
			# To the card knowledge
			self.singled_out_cards.pop(index)
			# Only append an empty clue if it is needed to keep the not clue length the same as the clue length. This is important because as cards run out the clue list might start to shorten, so the not clues should as well.
			cu.delete_slot(self.my_not_clues, index)
			# The deletion above has reduced our number of not clues. This might be correct if the deck is run out (I'm actually holding fewer than 5 cards).
			# Usually, I also drew a card and should have 5 not clues, so the check below handles this.
			if len(self.my_not_clues) == len(reader.get_my_clues(my_observation)) - 1:
				self.my_not_clues.append(cu.get_empty_not_clue())
				# We removed an element from the cached singled out cards, so we need to build that list to be as long as our clues.
				self.singled_out_cards.append(False)
			# Let's reach in and change the clues in the cached observation to reflect the play or discard that I'm about to do. This is helpful, since on the next observation received I won't see changes in the clues AS A RESULT OF MY DISCARD and try to think of how these could have originated from a hint from the other player. This was the root cause of a bug where "None" was showing up in not clues for colors and rank.
			if self.cached_observation is not None:
				my_cached_clues = reader.get_my_clues(self.cached_observation)
				cu.delete_slot(my_cached_clues, index)
				# The deletion above has reduced our number of cached clues. This might be correct if the deck is run out (I'm actually holding fewer than 5 cards).
				# Usually, I also drew a card and should have 5 clues, so the check below handles this.
				if len(my_cached_clues) == len(reader.get_my_clues(my_observation)) - 1:
					my_cached_clues.append(cu.get_empty_clue())
		# If the other player made a play or a discard, then I need to update the stored not clues for the other player (since they could have shifted)
		if index_player_who_just_moved != self.agent_id and not action_reader.is_action_hint(latest_action):
			index = latest_action["card_index"]
			cu.delete_slot(self.other_player_not_clues, index, cu.get_empty_not_clue())

		# If the action is a clue, adjust the other player not clues
		if index_player_who_just_moved == self.agent_id and action_reader.is_action_hint(latest_action):
			_, not_clue = cu.get_clues_from_hint(latest_action, reader.get_other_player_hand(my_observation))
			cu.merge_not_clue(self.other_player_not_clues, not_clue)
		
	# This method includes many of the error checks that the policy_test relies on
	def update_my_not_clues(self, observation):
	
		self.say("REPORT BEGIN ---------------------------------------")
		self.say(f"Here is my observation as player {self.agent_id}:")
		self.say(observation)

		# If I am the current player of this observation, that means the previous move was made by the other player, and vice versa.
		player_index_previous_move = int(not reader.get_current_player(observation))

		# Print the previous move for debugger awareness.
		self.say("The previous move was:")
		self.say(observation["prev_move"])

		# Before considering a difference in card knowledge from the previous observation (cached) to this one, make sure that there even is a cached observation (there won't be one at the game start).
		if self.cached_observation == None:
			self.say("First move, so there is no hint to infer.")
		else:
			# Below is where card knowledge changes are captured and my not clues are updated. I only want to create new not clues if I am certain that the other player just gave me a clue. So we'll check if the previous move was made by the other player (i.e. I am the current player).
			if player_index_previous_move != self.agent_id:
				self.say("The last move was done by the other player. I'm going to check if I can infer a hint just from the change in card knowledge.")
				clues_from_observation_change, new_not_clues = cu.get_clues_from_observation_change(self.cached_observation, observation)
				self.say("I get a clue from the observation change of:")
				self.say(clues_from_observation_change)
				self.say("And a not clue of:")
				self.say(new_not_clues)
			
				# We'll assume for now that the calculated not clue from the latest hint is correct, and merge it into our cached not clues
				cu.merge_not_clue(self.my_not_clues, new_not_clues)
			
				previous_move = observation["prev_move"]
				# Check for lots of good and bad cases
				if action_reader.is_action_hint(previous_move):
					if clues_from_observation_change != [cu.get_empty_clue() for i in range(len(reader.get_my_clues(observation)))]:
						self.say("The previous move was a clue, and I did observe a difference in my clues.")
						
						# Infer what clue was given based on how my card knowledge changed.
						inferred_hint = None
						for slot in clues_from_observation_change:
							if cu.get_color(slot) is not None:
								self.say(f"The hint I received should be REVEAL_COLOR: {cu.get_color(slot)}")
								inferred_hint = action_reader.get_new_action(action_reader.REVEAL_COLOR, cu.get_color(slot))
								break
							if cu.get_rank(slot) is not None:
								self.say(f"The hint I received should be REVEAL_RANK: {cu.get_rank(slot)}")
								inferred_hint = action_reader.get_new_action(action_reader.REVEAL_RANK, cu.get_rank(slot))
								break
								
						# Check that the previous move and the inferred hint agree
						if inferred_hint == previous_move:
							self.say("The inferred hint and the previous move agree")
						else:
							self.log_error(f"The previous move {previous_move} does not agree with the inferred hint of {inferred_hint}")
						
					else:
						self.say("The previous move was a hint, but I observed no change in my card knowledge. This could still be correct if my opponent gave me an unhelpful clue.")
						
				else:
					if clues_from_observation_change != [cu.get_empty_clue() for i in range(len(reader.get_my_clues(observation)))]:
						self.log_error("The previous move was not a hint, yet I got a hint from the observation change that was non-trivial.")
					else:
						self.say("The previous move was not a hint, and I correctly observed no difference in my clues from an observation comparison.")
				
			else:
				self.say("I'm not going to pay close attention to changes in card knowledge because the previous move was made by me. The impact of any discard or play of mine on my own not clues should have already been handled.")

		# Discuss updated hand knowledge
		self.say("I have these clues:")
		self.say(reader.get_my_clues(observation))
		self.say("I have these not clues:")
		self.say(self.my_not_clues)

	def run_checks(self, observation):
		deck_size = reader.get_deck_size(observation)
		self.say(f"Deck size is {reader.get_deck_size(observation)} cards")
		if deck_size < 0 or deck_size > len(cu.ALL_CARDS):
			self.log_error(f"Got an unacceptable deck size of {deck_size}")
			
		number_of_cards_in_my_hand = len(reader.get_my_clues(observation))
			
		# Check if there are any contradictions in the clues and not clues
		for slot in range(len(reader.get_my_clues(observation))):
			clue_slot = reader.get_my_clues(observation)[slot]
			not_clue_slot = self.my_not_clues[slot]
			if cu.get_color(clue_slot) in not_clue_slot["colors"] or cu.get_rank(clue_slot) in not_clue_slot["ranks"]:
				self.log_error(f"Contradiction between clues and not clues for slot {slot}.")

		hand_entropy, hand_list, _ = cu.get_hand_entropy(reader.get_my_clues(observation), self.my_not_clues, reader.get_my_reserved_cards(observation))
		self.say(f"Currently, my hand has an entropy of {hand_entropy}")
		
		# Verify that the entropy is within an acceptable range
		if hand_entropy > cu.MAX_ENTROPY or hand_entropy < 0:
			self.log_error(f"Received an invalid entropy of {hand_entropy}")

		self.say("My card playable probabilities are:")
		my_clues = reader.get_my_clues(observation)
		reserved_cards = reader.get_my_reserved_cards(observation)
		fireworks = reader.get_fireworks(observation)
		other_player_hand = reader.get_other_player_hand(observation)
		playable_probabilities = cu.get_playable_probabilities(my_clues, self.my_not_clues, reserved_cards, fireworks)
		self.say(playable_probabilities)
		
		# Check if any card playable probabilties are outside the range of valid probabilities
		for probability in playable_probabilities:
			if probability < 0 or probability > 1:
				self.log_error(f"Obtained an invalid card playable probabiltiy of {probability}")
		
		if len(playable_probabilities) > number_of_cards_in_my_hand:
			self.log_error(f"Have playable probabilites for {len(playable_probabilities)} slots when I only have clues for {number_of_cards_in_my_hand} slots.")
		
		self.say("My safely discardable probabilities are:")
		discarded_cards = reader.get_discarded_cards(observation)
		safely_discardable_probabilities = cu.get_safely_discardable_probabilities(my_clues, self.my_not_clues, discarded_cards, fireworks, deck_size, other_player_hand)
		self.say(safely_discardable_probabilities)
		
		# Check if any safely_discardable_probabilities are outside the valid range
		for probability in safely_discardable_probabilities:
			if probability < 0 or probability > 1:
				self.log_error(f"Obtained an invalid safely discardable probability of {probability}")
		
		if len(safely_discardable_probabilities) > number_of_cards_in_my_hand:
			self.log_error(f"Have playable probabilites for {len(safely_discardable_probabilities)} slots when I only have clues for {number_of_cards_in_my_hand} slots.")
		
		unneeded_probabilities = cu.get_unneeded_probabilities(my_clues, self.my_not_clues, discarded_cards, fireworks)
		self.say(f"Got unneeded probabilities:")
		self.say(unneeded_probabilities)

		self.say("If my opponent has a good memory, he'll have clues of:")
		self.say(reader.get_other_player_clues(observation))
		self.say("And not clues of:")
		self.say(self.other_player_not_clues)

		other_player_hand_entropy, _, _ = cu.get_hand_entropy(reader.get_other_player_clues(observation), self.other_player_not_clues, reader.get_other_player_reserved_cards(observation))
		
		# Verify that the entropy is within an acceptable range
		if other_player_hand_entropy > cu.MAX_ENTROPY or other_player_hand_entropy < 0:
			self.log_error(f"Received an invalid entropy of {hand_entropy}")

		self.say(f"My opponent has an upper bound entropy of {other_player_hand_entropy}")

		self.say("My opponent has this hand:")
		self.say(other_player_hand)

		self.say("And my opponent not clues are:")
		self.say(self.other_player_not_clues)

		self.say("Let's list each possible clue I could give and the entropy change factor for it.")
		hint_nuggets = []
		for move in reader.get_legal_moves(observation):
			# Replace the logical expression below with one that uses action_reader.is_action_hint()
			if action_reader.is_action_hint(move):
				nugget = HintNugget(observation, self.other_player_not_clues, move)
				hint_nuggets.append(nugget)
				factor = nugget.get_entropy_change_factor()
				if factor > 1 or factor <= 0:
					self.log_error(f"Received an invalid entropy change factor of {factor}")

		# Create a variable that can store information about which (if any) slot was singled out by a hint we just received.
		singled_out_playable_card_index = -1

		# Singled out cards should only be updated if it's our turn. Otherwise, since this method is called even when it is NOT this bot's turn,
		# this bot can infer a card was singled out in response to other actions (discards, plays) since those change the card knowledge.
		if len(reader.get_legal_moves(observation)) > 0:
		
			# If the hint we received only changed our card knowledge with respect to one slot, and the playable probability for that slot is greater than 0, then we need to classify this as singling out a playable card.
			card_knowledge_differences = 0
			card_knowledge_last_different_index = 0
			self.say("I'm going to now appraise whether the hint singled out a card. I have these cached clues:")
			self.say(self.cached_card_knowledge)
			self.say("But my clues now are ")
			self.say(my_clues)
			for i in range(len(my_clues)):
				if self.cached_card_knowledge[i] != my_clues[i]:
					card_knowledge_differences += 1
					card_knowledge_last_different_index = i
					self.say(f"Card slot {i} contains new information and brings out card knowledge differences count to {card_knowledge_differences}")
				else:
					self.say(f"Card slot {i} does not contain any information change.")
			if card_knowledge_differences == 1 and playable_probabilities[card_knowledge_last_different_index] > 0:
				singled_out_playable_card_index = card_knowledge_last_different_index
				self.say(f"I noticed that the other player singled out my {singled_out_playable_card_index}th card and after receiving the hint I know that it might be playable. I'll consider this with extra weight for being playable.")
				# Update the cached singled out cards
				self.singled_out_cards[singled_out_playable_card_index] = True
			else:
				self.say(f"The hint did not single out a playable card.")
			
			self.say(f"My singled out cards list is now {self.singled_out_cards}")

		# Store cached card knowledge so that we can detect future singling out of cards
		self.cached_card_knowledge = copy.deepcopy(my_clues)

		self.say("REPORT COMPLETE -------------------------------------")
		
		# Return a tuple that contains the playability probabilities, safely_discardable_probabilities, and entropy changes
		return (playable_probabilities, safely_discardable_probabilities, unneeded_probabilities, hint_nuggets, hand_list, singled_out_playable_card_index)

	def log_error(self, message):
		self.errors.append(message)
		line = "\n----------------------------------------------------\n"
		print(line, line, "ERROR", line, line, sep="")
		print()
		print(message)
		if self.verbose:
			# Block on user input so the error can be viewed.
			nothing = input()
	
	# This message allows print statements from the report to be toggled on and off.
	def say(self, message):
		self.record += str(message) + "\n"
		if self.verbose:
			print(message)
			
	def set_verbosity(self, new_verbosity):
		self.verbose = new_verbosity
		
	def get_errors(self):
		return self.errors
