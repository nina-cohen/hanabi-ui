
import util.action_reader as action_reader
import util.card_utilities as cu
import util.observation_reader as reader
import copy

class HintNugget():

	def __init__(self, observation, other_player_not_clues, action):
		self.action = action
		deck_size = reader.get_deck_size(observation)
		other_player_hand = reader.get_other_player_hand(observation)
		other_player_clues = reader.get_other_player_clues(observation)
		other_player_reserved_cards = reader.get_other_player_reserved_cards(observation)
		discarded_cards = reader.get_discarded_cards(observation)
		new_clue, new_not_clue = cu.get_clues_from_hint(action, reader.get_other_player_hand(observation))
		self.entropy_change_factor, other_player_old_hand_entropy, other_player_old_possible_hands, other_player_new_hand_entropy, other_player_new_possible_hands = cu.get_entropy_change_factor_for_clue(
					other_player_clues,
					other_player_not_clues,
					other_player_reserved_cards,
					new_clue,
					new_not_clue)

		# Update the before and after playable probabilities
		fireworks = reader.get_fireworks(observation)
		unique_playable_cards = cu.get_unique_playable_cards(fireworks)
		self.before_playable_probabilities = cu.get_playable_probabilities(other_player_clues, other_player_not_clues, other_player_reserved_cards, fireworks)
		other_player_new_clues = copy.deepcopy(other_player_clues)
		cu.merge_clue(other_player_new_clues, new_clue)
		other_player_new_not_clues = copy.deepcopy(other_player_not_clues)
		cu.merge_not_clue(other_player_new_not_clues, new_not_clue)
		self.after_playable_probabilities = cu.get_playable_probabilities(other_player_new_clues, other_player_new_not_clues, other_player_reserved_cards, fireworks)

		# Update the before and after safely discardable probabilities
		self.before_safely_discardable_probabilities = cu.get_safely_discardable_probabilities(other_player_clues, other_player_not_clues, discarded_cards, fireworks, deck_size)
		self.after_safely_discardable_probabilities = cu.get_safely_discardable_probabilities(other_player_new_clues, other_player_new_not_clues, discarded_cards, fireworks, deck_size)
		
		# Get a count of the other player's known unneeded cards
		known_unneeded_cards = 0
		for clue in other_player_clues:
			if cu.get_color(clue) is not None and cu.get_rank(clue) is not None and cu.is_unneeded(clue, fireworks, discarded_cards):
				known_unneeded_cards += 1
		
		# Get a count of the other player's known unneeded cards after hint
		new_known_unneeded_cards = 0
		for clue in other_player_new_clues:
			if cu.get_color(clue) is not None and cu.get_rank(clue) is not None and cu.is_unneeded(clue, fireworks, discarded_cards):
				known_unneeded_cards += 1
				
		self.net_learned_unneeded_cards = new_known_unneeded_cards - known_unneeded_cards
		
		# Determine whether this hint would single out a playable card to the other player. To do this, the hint must only change the other play's card knowledge (clues) with respect to one slot, and the slot must contain a playable card.
		self.would_single_out_playable_card = False
		self.would_single_out_non_playable_card = False
		clue_differences = 0
		most_recent_difference_slot_index = 0
		for i in range(len(other_player_clues)):
			if other_player_clues[i] != other_player_new_clues[i]:
				clue_differences += 1
				most_recent_difference_slot_index = i
		if clue_differences == 1 and cu.is_card_playable(other_player_hand[most_recent_difference_slot_index], fireworks):
			self.would_single_out_playable_card = True
		if clue_differences == 1 and not cu.is_card_playable(other_player_hand[most_recent_difference_slot_index], fireworks):
			self.would_single_out_non_playable_card = True
		self.singled_out_card_index = most_recent_difference_slot_index

	def get_action(self):
		return self.action
		
	def get_action_type(self):
		return action_reader.get_action_type(self.action)
		
	def get_hint_detail(self):
		return action_reader.get_hint_detail(self.action)
		
	def get_entropy_change_factor(self):
		return self.entropy_change_factor
		
	def set_entropy_change_factor(self, factor):
		self.entropy_change_factor = factor
		
	def get_before_playable_probabilities(self):
		return self.before_playable_probabilities
		
	def set_before_playable_probabilities(self, probabilities):
		self.before_playable_probabilities = probabilities
		
	def get_after_playable_probabilities(self):
		return self.after_playable_probabilities
		
	def set_after_playable_probabilities(self, probabilities):
		self.after_playable_probabilities = probabilities
		
	def get_before_safely_discardable_probabilities(self):
		return self.before_safely_discardable_probabilities
		
	def set_before_safely_discardable_probabilities(self, probabilities):
		self.before_safely_discardable_probabilities = probabilities
		
	def get_after_safely_discardable_probabilities(self):
		return self.after_safely_discardable_probabilities
		
	def set_after_safely_discardable_probabilities(self, probabilities):
		self.after_safely_discardable_probabilities
		
	def get_net_learned_unneeded_cards(self):
		return self.net_learned_unneeded_cards
		
	def get_would_single_out_playable_card(self):
		return self.would_single_out_playable_card
		
	def get_would_single_out_non_playable_card(self):
		return self.would_single_out_non_playable_card
		
	def get_singled_out_card_index(self):
		return self.singled_out_card_index