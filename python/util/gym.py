
"""
Gym is a Hanabi gym that can headlessly run a two player hanabi game between two policy agents. It uses the same game state format ("observations")
as the Hanabi Learning Environment
"""

import util.card_utilities as cu
import util.observation_reader as ob_reader
import util.observation_bundle_reader as bundle_reader
import util.action_reader as action_reader
import random
import copy
import csv

NUMBER_OF_PLAYERS = 2

ALICE_SUITE_MAP = {
	"A": "B",
	"B": "G",
	"C": "R",
	"D": "W",
	"E": "Y"
}

class Gym():

	def __init__(self, fixed_deck = None, full_file_path = None):
		if full_file_path is not None:
			self.hanab_lines = []
			with open(full_file_path, mode='r') as inp:
				reader = csv.DictReader(inp)
				for row in reader:
					self.hanab_lines.append(row)
			self.is_replay = True
		else:
			self.is_replay = False

		if self.is_replay:
			self.hanab_line_number = 0

		self.reset(fixed_deck)

	def reset(self, fixed_deck):

		self.deck = []
		self.player_to_end = None
		self.is_game_over_flag = False
		if fixed_deck is None:
			ordered_deck = [cu.make_card(color, rank) for color in cu.COLORS for rank in cu.ALL_RANKS]
			# Randomize the order of the deck
			while len(ordered_deck) > 0:
				# Select a random card from the ordered deck to recreate in the current deck
				index = random.randrange(len(ordered_deck))
				ordered_deck_card = ordered_deck[index]
				self.deck.append(cu.make_card(cu.get_color(ordered_deck_card), cu.get_rank(ordered_deck_card)))
				ordered_deck.remove(ordered_deck_card)
				# Technically, this algorithm could pick the index of a card in the ordered deck but actually remove a different, identical copy of that card from the ordered deck (e.g. index points to a yellow 1 from the ordered deck but then a different yellow 1 is removed from the ordered deck). I don't think this is a problem, but I'm recording the behavior here.
		else:
			self.deck = fixed_deck

		# Create an empty observation
		self.observation_bundle = self.get_new_observation_bundle(NUMBER_OF_PLAYERS)
		
		self.player_index_next_action_is_from = 0
		
		# Distribute cards from the deck to each player
		for i in range(NUMBER_OF_PLAYERS):
			for j in range(cu.HAND_SIZE):
				self.deal_new_card_to_player(i, j)
				
		# Now, update legal moves
		self.update_legal_moves()
	
	def step_from_log(self):
		if self.is_game_over():
			print("Cannot take another step in the logs. The end of the log has been reached.")
			return self.observation_bundle, None
		action = self.alice_get_action(self.hanab_line_number)
		if action is None:
			print("Parsing error. Likely the end of the file. Just going to skip that action and keep going.")
			return self.observation_bundle, None

		index_of_legal_move_made = -1
		legal_moves = ob_reader.get_legal_moves(bundle_reader.get_observations(self.observation_bundle)[self.player_index_next_action_is_from])
		for i in range(len(legal_moves)):
			if legal_moves[i] == action:
				index_of_legal_move_made = i
				break

		new_observation = self.step(action)
		self.hanab_line_number += 1
		if self.hanab_line_number >= len(self.hanab_lines):
			self.is_game_over_flag = True
		return new_observation, index_of_legal_move_made

	def step(self, action):
		
		# If the observation bundle has a deck size of 0, then this is the last turn this player can make.
		two_turns_left = False
		if bundle_reader.get_deck_size(self.observation_bundle) == 0 and self.player_to_end is None:
			self.player_to_end = not int(self.player_index_next_action_is_from)
			two_turns_left = True
		
		# Sometimes the action is none. This should only happen when the player has no legal moves to make. This is possible when it's their turn but they are out of cards and there are no information tokens left over. In this case, simply end the turn and update the legal moves. Note that this also requires methods to be willing to accept a previous move that is None
		if action is not None:
			action_type = action_reader.get_action_type(action)
			# If the action is a hint, change the card knowledge of the correct player
			if action_type == action_reader.REVEAL_COLOR or action_type == action_reader.REVEAL_RANK:
				# Handle receiving a hint
				self.update_player_knowledge_with_hint(action)
				# Decrement the number of information tokens
				bundle_reader.decrement_information_tokens(self.observation_bundle)
			if action_type == action_reader.DISCARD:
				# Handle a discard
				self.discard_card_from_player_hand_and_deal(action)
			if action_type == action_reader.PLAY:
				# Handle a play
				self.attempt_play(action)
			
		# Check if the last player made their last move
		if not two_turns_left and self.player_index_next_action_is_from == self.player_to_end:
			self.is_game_over_flag = True
			
		# Check if the game is over on account of the number of life tokens
		if bundle_reader.get_life_tokens(self.observation_bundle) == 0:
			self.is_game_over_flag = True
			
		# A step is guaranteed to end the current player's turn
		self.end_turn()
		
		# Non hint actions change the legal moves for a player. To be safe, always update the legal moves.
		self.update_legal_moves()
		
		for observation in bundle_reader.get_observations(self.observation_bundle):
			observation["prev_move"] = action
		
		# THERE IS A TUPLE THAT SHOULD BE RETURNED FOR CONSISTENCY WITH ISC HANABI, BUT FOR NOW I'LL JUST RETURN THE BUNDLE
		return self.observation_bundle
		
	def end_turn(self):
		# Change which player's turn it is
		self.player_index_next_action_is_from = int(not self.player_index_next_action_is_from)
		for observation in bundle_reader.get_observations(self.observation_bundle):
			observation["current_player"] = int(not observation["current_player"])
			observation["current_player_offset"] = int(not observation["current_player_offset"])
		
	def get_observation_bundle(self):
		return self.observation_bundle
		
	def get_current_player(self):
		return self.player_index_next_action_is_from

	def deal_new_card_to_player(self, player_index, slot_index = None):
		if len(self.deck) == 0:
			return False
		# Add to the observed hand of the other player
		other_player_index = not player_index
		card = self.deck[0]
		# If replaying from a log, overwrite which card is dealt here
		if self.is_replay:
			if slot_index is not None:
				card = self.alice_get_start_card(player_index, slot_index)
			else:
				card = self.alice_code_to_card(self.hanab_lines[self.hanab_line_number]["Draw"])
		self.deck.remove(card)
		observations = bundle_reader.get_observations(self.observation_bundle)

		blind_hand = ob_reader.get_observed_hand_by_index(observations[player_index], 0)
		observed_hand = ob_reader.get_observed_hand_by_index(observations[other_player_index], 1)
		observed_hand.append(card)
		# Add to the observed hand of the player, even though the player can't actually observe this card. Here we exploit that an empty clue is the same thing as a card you're not allowed to view.
		blind_hand.append(cu.get_empty_clue())
		# Add an empty clue to the card knowledge of the receiving player in both observations
		player_clues = ob_reader.get_my_clues(observations[player_index])
		player_clues.append(cu.get_empty_clue())
		player_clues_other_ob = ob_reader.get_other_player_clues(observations[other_player_index])
		player_clues_other_ob.append(cu.get_empty_clue())
		
		bundle_reader.decrement_deck_size(self.observation_bundle)
		return True
	
	def get_new_observation_bundle(self, number_of_players = 2):
		new_bundle = {"player_observations": []}
		
		for player_index in range(number_of_players):
			observation = {}
			observation["current_player"] = 0
			observation["current_player_offset"] = player_index
			observation["life_tokens"] = 3
			observation["information_tokens"] = 8
			observation["num_players"] = number_of_players
			observation["deck_size"] = 50
			observation["fireworks"] = {color: 0 for color in cu.COLORS}
			observation["legal_moves"] = [] # Will be updated one cards are dealt
			observation["legal_moves_as_int"] = []
			observation["observed_hands"] = [[], []]
			observation["discard_pile"] = []
			observation["card_knowledge"] = [[], []]
			observation["action_hist"] = []
			observation["prev_move"] = None
			new_bundle["player_observations"].append(observation)
			
		return new_bundle
	
	def update_legal_moves(self):
		
		for observation in bundle_reader.get_observations(self.observation_bundle):
		
			# To be consistent with ISC standard, only the player whose turn it is should have any legal moves
			current_player_offset = ob_reader.get_current_player_offset(observation)
			legal_moves = []
			observation["legal_moves"] = legal_moves
			if current_player_offset != 0:
				# Then it's not my turn. ISC standard is to have no legal moves. So there's nothing more to do here
				continue
			else:

				# Find all of the possible, unique hints
				# Only add hints as legal moves if the players have information tokens
				if bundle_reader.get_information_tokens(self.observation_bundle) > 0:
					other_player_hand = ob_reader.get_other_player_hand(observation)
					for color in cu.COLORS:
						for slot in other_player_hand:
							if cu.get_color(slot) == color:
								legal_moves.append({"action_type": "REVEAL_COLOR", "target_offset": 1, "color": color})
								break
					for rank in cu.ALL_UNIQUE_RANKS:
						for slot in other_player_hand:
							if cu.get_rank(slot) == rank:
								legal_moves.append({"action_type": "REVEAL_RANK", "target_offset": 1, "rank": rank})
								break
				
				# Add a discard for each slot for which there is still a card
				player_hand_size = len(ob_reader.get_my_clues(observation))
				for index in range(player_hand_size):
					legal_moves.append({"action_type": "DISCARD", "card_index": index})
				
				# Add a play for each slot for which there is still a card
				for index in range(player_hand_size):
					legal_moves.append({"action_type": "PLAY", "card_index": index})
					
			observation["legal_moves_as_int"] = list(range(len(legal_moves)))
		
	def update_player_knowledge_with_hint(self, hint_action):

		player_index_whose_cards_the_clue_concerns = not self.player_index_next_action_is_from

		# Need to get the clue from the hint
		clue_recipient_player_hand = bundle_reader.get_player_hand_by_index(self.observation_bundle, player_index_whose_cards_the_clue_concerns)

		observations = bundle_reader.get_observations(self.observation_bundle)
		for i in range(len(observations)):
			observation = observations[i]
			
			card_knowledge_to_update = observation["card_knowledge"][int(player_index_whose_cards_the_clue_concerns != i)]
			
			new_clue, _ = cu.get_clues_from_hint(hint_action, clue_recipient_player_hand)
			
			cu.merge_clue(card_knowledge_to_update, new_clue)

	def remove_card_from_player_hand_and_deal(self, player_index, card_index):
		# Need to update card knowledge for both observations in the bundle and update observed hands for the other player
		other_player_index = not player_index
		
		observations = bundle_reader.get_observations(self.observation_bundle)
		player_observation = observations[player_index]
		other_player_observation = observations[other_player_index]
		
		# For the player losing the card, change their knowledge and observed hand (even though they never observer their hand)
		cu.delete_slot(ob_reader.get_my_clues(player_observation), card_index)
		cu.delete_slot(player_observation["observed_hands"][0], card_index)
		
		# For the other player, change knowledge and observed hand
		cu.delete_slot(ob_reader.get_other_player_clues(other_player_observation), card_index)
		card_deleted = cu.delete_slot(ob_reader.get_other_player_hand(other_player_observation), card_index)
		self.deal_new_card_to_player(player_index)
		return card_deleted

	def discard_card_from_player_hand_and_deal(self, discard_action):
		player_index = self.player_index_next_action_is_from
		card_index = action_reader.get_card_index(discard_action)
		card = self.remove_card_from_player_hand_and_deal(player_index, card_index)
		self.add_card_to_discard_pile(card)
		# Add an information token because a card was discarded
		bundle_reader.increment_information_tokens(self.observation_bundle)

	def attempt_play(self, play_action):
		"""
		Makes modifications to the observation bundle if successful (fireworks changed) and if unsuccessful (life tokens changed, card discarded) and returns the boolean of whether the play was valid.
		"""
		
		# Determine the card that is trying to be played
		card_index = play_action["card_index"]
		
		hand_play_comes_from = bundle_reader.get_player_hand_by_index(self.observation_bundle, self.player_index_next_action_is_from)
		played_card = hand_play_comes_from[card_index]
		fireworks = bundle_reader.get_fireworks(self.observation_bundle)
		card_being_played = hand_play_comes_from[card_index]

		if cu.is_card_playable(card_being_played, fireworks):
			# Adjust the fireworks
			bundle_reader.adjust_fireworks_with_playable_card(self.observation_bundle, card_being_played)
			# Remove the card from the hand and do nothing with it (not even put it in the discard pile)
			card_played = self.remove_card_from_player_hand_and_deal(self.player_index_next_action_is_from, card_index)
			# If the card rank was 4, an information token should be added
			if cu.get_rank(card_played) == 4:
				bundle_reader.increment_information_tokens(self.observation_bundle)
		else:
			# Adjust the life tokens
			bundle_reader.decrement_life_tokens(self.observation_bundle)
			# Remove the card from the hand and add it to the discard pile
			card_deleted = self.remove_card_from_player_hand_and_deal(self.player_index_next_action_is_from, card_index)
			self.add_card_to_discard_pile(card_deleted)
			
	def add_card_to_discard_pile(self, card):
		observations = bundle_reader.get_observations(self.observation_bundle)
		for observation in observations:
			discard_pile = ob_reader.get_discarded_cards(observation)
			discard_pile.append(copy.deepcopy(card))
		
	def is_game_over(self):
		return self.is_game_over_flag

	def alice_get_start_card(self, player_index, slot_index):
		top_row = self.hanab_lines[0]
		return self.alice_code_to_card(top_row[f"Start_P{player_index}_c{slot_index + 1}"])

	def alice_code_to_card(self, code):
		letter = code[0]
		number = int(code[1])
		return cu.make_card(ALICE_SUITE_MAP[letter], number - 1)

	def alice_get_action(self, line_index):
		row = self.hanab_lines[line_index]
		alice_action_type = row["Action"]
		if alice_action_type not in ["reveals", "plays", "discards"]:
			return None
		action_type = ""
		next_attribute = ""
		if alice_action_type == "reveals":
			if row["Card"].isnumeric():
				action_type = action_reader.REVEAL_RANK
				next_attribute = int(row["Card"]) - 1
			else:
				action_type = action_reader.REVEAL_COLOR
				next_attribute = ALICE_SUITE_MAP[row["Card"]]
		else:
			if alice_action_type == "plays":
				action_type = action_reader.PLAY
			else:
				action_type = action_reader.DISCARD
			next_attribute = int(row["CardIndex"])
		return action_reader.get_new_action(action_type, next_attribute)
