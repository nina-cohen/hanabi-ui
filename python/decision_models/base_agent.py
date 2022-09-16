from decision_models.decision_model import DecisionModel
import util.action_reader as action_reader
import util.observation_reader as ob_reader
import util.card_utilities as cu
import numpy

FIXED_ACTIONS = [
	action_reader.get_new_action(action_reader.DISCARD, 0),
	action_reader.get_new_action(action_reader.DISCARD, 1),
	action_reader.get_new_action(action_reader.DISCARD, 2),
	action_reader.get_new_action(action_reader.DISCARD, 3),
	action_reader.get_new_action(action_reader.DISCARD, 4),
	action_reader.get_new_action(action_reader.PLAY, 0),
	action_reader.get_new_action(action_reader.PLAY, 1),
	action_reader.get_new_action(action_reader.PLAY, 2),
	action_reader.get_new_action(action_reader.PLAY, 3),
	action_reader.get_new_action(action_reader.PLAY, 4),
	action_reader.get_new_action(action_reader.REVEAL_COLOR, "B"),
	action_reader.get_new_action(action_reader.REVEAL_COLOR, "G"),
	action_reader.get_new_action(action_reader.REVEAL_COLOR, "R"),
	action_reader.get_new_action(action_reader.REVEAL_COLOR, "W"),
	action_reader.get_new_action(action_reader.REVEAL_COLOR, "Y"),
	action_reader.get_new_action(action_reader.REVEAL_RANK, 0),
	action_reader.get_new_action(action_reader.REVEAL_RANK, 1),
	action_reader.get_new_action(action_reader.REVEAL_RANK, 2),
	action_reader.get_new_action(action_reader.REVEAL_RANK, 3),
	action_reader.get_new_action(action_reader.REVEAL_RANK, 4),
]

class BaseAgent(DecisionModel):

	"""
	All HPF based agents extend BaseAgent. The only variation between derived agents is their weights
	"""

	def __init__(self):
		self.cost_misplay_by_strikes = [1, 1.5, 3]
		self.singled_out_playable_value_bump = 6
		self.decision_to_single_out_playable_card_bonus = 3
		self.decision_to_single_out_non_playable_card_penalty = 1
		self.singled_out_playable_discard_penalty = 0.5
		self.info_token_end_discard_penalty_factor = 4
		self.cost_misplay_other_player = 1
		self.play_multiplier = 2
		self.self_certain_play_bonus = 11
		self.clue_bonus_per_info_token = 0
		self.value_good_discard = 10
		self.force_safe_discard_factor = 0

		self.w = numpy.array([self.cost_misplay_by_strikes[0], self.cost_misplay_by_strikes[2], self.singled_out_playable_value_bump, self.decision_to_single_out_playable_card_bonus,
		 self.decision_to_single_out_non_playable_card_penalty, self.singled_out_playable_discard_penalty, self.cost_misplay_other_player, self.play_multiplier, 
		 self.self_certain_play_bonus, self.clue_bonus_per_info_token, self.value_good_discard, self.force_safe_discard_factor])

	def load_new_weights(self, weights):
		self.w = weights
		self.cost_misplay_by_strikes[0] = weights[0]
		self.cost_misplay_by_strikes[1] = weights[0]
		self.cost_misplay_by_strikes[2] = weights[1]
		self.singled_out_playable_value_bump = weights[2]
		self.decision_to_single_out_playable_card_bonus = weights[3]
		self.decision_to_single_out_non_playable_card_penalty = weights[4]
		self.singled_out_playable_discard_penalty = weights[5]
		self.cost_misplay_other_player = weights[6]
		self.play_multiplier = weights[7]
		self.self_certain_play_bonus = weights[8]
		self.clue_bonus_per_info_token = weights[9]
		self.value_good_discard = weights[10]
		self.force_safe_discard_factor = weights[11]

	def get_variant_name(self):
		return "BaseAgent"

	def decide_move(self, observation, my_not_clues, other_player_not_clues, playable_probabilities, safely_discardable_probabilities, unneeded_probabilities,
		hint_nuggets, singled_out_playable_card_index, singled_out_cards, say):
		
		legal_moves = observation["legal_moves"]
		fireworks = ob_reader.get_fireworks(observation)
		other_player_hand = ob_reader.get_other_player_hand(observation)
		other_player_non_reserved_cards = ob_reader.get_other_player_non_reserved_cards(observation)
		discarded_cards = ob_reader.get_discarded_cards(observation)
		my_clues = ob_reader.get_my_clues(observation)
		life_tokens = ob_reader.get_life_tokens(observation)
		info_tokens = ob_reader.get_information_tokens(observation)
		my_non_reserved_cards = ob_reader.get_my_non_reserved_cards(observation)
		discarded_cards = ob_reader.get_discarded_cards(observation)
		deck_size = ob_reader.get_deck_size(observation)

		move_score_descriptions = []
		
		turns_left_after_this_one = None
		if ob_reader.get_deck_size(observation) == 0:
			turns_left_after_this_one = int(not action_reader.is_action_hint(ob_reader.get_previous_move(observation)))
		
		# If there are no legal moves, need to give None to the gym.
		if len(legal_moves) == 0:
			return None, None, None, None, None, None
		
		# Find the current misplay cost, based on the number of life tokens
		misplay_cost = self.cost_misplay_by_strikes[3 - life_tokens]
			
		# If this is the very last turn, then there should be no cost to misplay. Also, if this is the second to last turn and there are 2 or more life tokens, there should be no cost to play.
		if turns_left_after_this_one is not None and life_tokens > turns_left_after_this_one:
			misplay_cost = 0

		# Every legal move can be assigned a point value. So we'll go through an assign all of the point values and then select the move with the highest point value.
		# Create an h_matrix and y_vector variable. These will be returned at the end of this method. These satisfy the following factorization
		# h_matrix * self.w = y_vector
		# The elements of y_vector are the expected values for each of the moves in FIXED_ACTIONS. If any of the moves are not currently legal (e.g. clueing
		# a play that they have 0 red cards), these will show in the y_vector as moves with an expected value of 0.
		h_matrix = numpy.zeros((20, 12))
		y_vector = numpy.zeros((20,))

		legal_move_point_values = [0 for point in range(len(legal_moves))]
		for index in range(len(legal_moves)):

			move_score_description = ""
			
			candidate_move = legal_moves[index]
			move_expected_value_change = 0

			fixed_action_index = FIXED_ACTIONS.index(candidate_move)

			# Sort based on the type of move
			move_type = action_reader.get_action_type(candidate_move)
			card_index = action_reader.get_card_index(candidate_move)
			
			# Handle hint options
			if action_reader.is_action_hint(candidate_move):
			
				# If this is the very last turn, harshly penalize a hint. There is nothing to gain from a final hint.
				if turns_left_after_this_one == 0:
					h_matrix[fixed_action_index, 3] = -self.cost_misplay_by_strikes[2]
					legal_move_point_values[index] -= self.cost_misplay_by_strikes[2]
			
				# Entropy changes and changes in opponent knowledge
				# Find this hint in the entropy changes by hint list
				for nugget in hint_nuggets:
					if candidate_move == nugget.get_action():

						# Now get the before and after playable probabilities and safely discardable probabilities
						before_playable_probabilities = nugget.get_before_playable_probabilities()
						after_playable_probabilities = nugget.get_after_playable_probabilities()
						before_safely_discardable_probabilities = nugget.get_before_safely_discardable_probabilities()
						after_safely_discardable_probabilities = nugget.get_after_safely_discardable_probabilities()
						
						say(f"The hint {candidate_move} would take my opponent from these playable probabilities")
						say(before_playable_probabilities)
						say(f"To these playable probabilities")
						say(after_playable_probabilities)
						say(f"And from these safely discardabilities")
						say(before_safely_discardable_probabilities)
						say(f"To these safely discardabilities")
						say(after_safely_discardable_probabilities)
					
						# Factor in playable probability changes
						total_playable_probabilities_change_value = 0
						for i in range(len(other_player_hand)):
							card = other_player_hand[i]
							playable_probability_change = after_playable_probabilities[i] - before_playable_probabilities[i]
							if cu.is_card_playable(card, fireworks):
							# TODO could magnify this by a factor and experiment with the value of the factor
								move_expected_value_change += playable_probability_change * self.play_multiplier
								h_matrix[fixed_action_index, 7] += playable_probability_change
								total_playable_probabilities_change_value += playable_probability_change * self.play_multiplier
							else:
								# Previously we used misplay_cost here that could be set to infinity with one life token left. However, this puts the human in info token hell since dormammu is constantly trying to inform the human player of their most recently drawn card and that it's not playable. So we'll use the self.cost_misplay_normal here instead
								move_expected_value_change -= self.cost_misplay_other_player * playable_probability_change
								h_matrix[fixed_action_index, 6] -= playable_probability_change
								total_playable_probabilities_change_value -= self.cost_misplay_other_player * playable_probability_change
								
						move_score_description += "{:.2f} for playable prob change, ".format(total_playable_probabilities_change_value)

						# Factor in safely discardable probability changes, but only if the deck size is greater than 0
						if deck_size > 0:
							total_safely_discardable_probabilities_change_value = 0
							for i in range(len(other_player_hand)):
								card = other_player_hand[i]
								safely_discardable_probability_change = after_safely_discardable_probabilities[i] - before_safely_discardable_probabilities[i]
								if cu.is_safely_discardable(card, fireworks, other_player_non_reserved_cards, discarded_cards, deck_size):
									move_expected_value_change += self.value_good_discard * safely_discardable_probability_change
									h_matrix[fixed_action_index, 10] += safely_discardable_probability_change
									total_safely_discardable_probabilities_change_value += self.value_good_discard * safely_discardable_probability_change

							move_score_description += "{:.2f} for discard prob change, ".format(total_safely_discardable_probabilities_change_value)
						else:
							move_score_description += "No discardabilities bonus - too close to game end, "

						# If this hint singles out a playable card, give it the corresponding bonus now
						if nugget.get_would_single_out_playable_card():
							move_expected_value_change += self.decision_to_single_out_playable_card_bonus
							h_matrix[fixed_action_index, 3] = 1
							move_score_description += "{:.2f} for singling out playable card, ".format(self.decision_to_single_out_playable_card_bonus)
							say(f"I'm slightly biased in favor of the clue {legal_moves[index]} because it would single out a playable card.")
							
						# If this hint singles out a non-playable card and the other player thinks its still playable, we need to incur a penalty here since we will make the other player much more likely to attempt to play this non-playable card
						if nugget.get_would_single_out_non_playable_card():
							# This might not need a penalty if the other player knows for certain that the card is not playable
							say(f"The clue {legal_moves[index]} would single out a card that is not playable. Let's see if that's a problem.")
							singled_out_card_index = nugget.get_singled_out_card_index()
							if nugget.get_after_playable_probabilities()[singled_out_card_index] > 0:
								say(f"Yes, this is a problem. The other player thinks this card is possible playable.")
								# Then we just singled out a non-playable card that the other player thinks is still playable. This will make the other player very likely to play a card that cannot be played.
								move_expected_value_change -= self.decision_to_single_out_non_playable_card_penalty
								h_matrix[fixed_action_index, 4] = -1
								move_score_description += "{:.2f} for singling out non-playable card, ".format(-self.decision_to_single_out_non_playable_card_penalty)
							else:
								say(f"No, this isn't a problem. The other player is aware that the singled out card is not playable. Might want to consider that a human player may have forgotten information and in this case might still be liable to play the non-playable card.")
						
						# Record the point value of this hint
						legal_move_point_values[index] += move_expected_value_change
			
			else:
				# Handle play options
				if move_type == action_reader.PLAY:
					# TODO add a play multiplier for the playable probabilites. This might make Jarvis take big risks early on, but after misplay_cost gets big enough than this will no induce any additional risk
					misplay_contribution = playable_probabilities[card_index] - (1 - playable_probabilities[card_index]) * misplay_cost
					legal_move_point_values[index] = misplay_contribution

					if life_tokens > 1:
						h_matrix[fixed_action_index, 0] = misplay_contribution / self.cost_misplay_by_strikes[0]
					else:
						h_matrix[fixed_action_index, 1] = misplay_contribution / self.cost_misplay_by_strikes[2]
				
					# If the playable probability is 1 (the card is certainply playable), let's give a self certain playability bonus
					if playable_probabilities[card_index] == 1:
						legal_move_point_values[index] += self.self_certain_play_bonus
						h_matrix[fixed_action_index, 8] = 1
						move_score_description += "{:.2f} for self certain play, ".format(self.self_certain_play_bonus)
						
					# If this is a singled out playable card that it needs to receive the bump
					if singled_out_playable_card_index == card_index:
						legal_move_point_values[index] += self.singled_out_playable_value_bump
						h_matrix[fixed_action_index, 2] = 1
						move_score_description += "{:.2f} for playing a singled out card, ".format(self.singled_out_playable_value_bump)
						say(f"I'm slightly biased in favor of {legal_moves[index]} because it would involve playing a singled out playable card.")
				
				# Handle discard options
				if move_type == action_reader.DISCARD:
				
					# Give bonus based on number of info tokens stored
					# Find probability p that the card is unneeded, then apply a discard penalty of (1 - p) * self.clue_bonus_per_info_token * info_tokens
					info_token_contribution = (1 - unneeded_probabilities[card_index]) * self.clue_bonus_per_info_token * info_tokens
					legal_move_point_values[index] -= (1 - unneeded_probabilities[card_index]) * self.clue_bonus_per_info_token * info_tokens
					if self.clue_bonus_per_info_token != 0:
						h_matrix[fixed_action_index, 9] = -info_token_contribution / self.clue_bonus_per_info_token
					move_score_description += "{:.2f} for discarding when we have {} info tokens, ".format(-(1 - unneeded_probabilities[card_index]) * self.clue_bonus_per_info_token * info_tokens, info_tokens)
				
					discard_contribution = self.value_good_discard * safely_discardable_probabilities[card_index]
					h_matrix[fixed_action_index, 10] = discard_contribution / self.value_good_discard
					legal_move_point_values[index] += self.value_good_discard * safely_discardable_probabilities[card_index]
					move_score_description += "{:.2f} for discardability, ".format(self.value_good_discard * safely_discardable_probabilities[card_index])
					
					legal_move_point_values[index] -= self.force_safe_discard_factor * unneeded_probabilities[card_index]
					h_matrix[fixed_action_index, 11] = -unneeded_probabilities[card_index]
					move_score_description += "{:.2f} since unneeded prob is {:.2f}, ".format(-self.force_safe_discard_factor * unneeded_probabilities[card_index], unneeded_probabilities[card_index])
							
					# If there are enough life tokens left to allow for plays for the rest of the game without death by strike, then we do NOT want to discard. A clue or a play would be much better.
					if turns_left_after_this_one is not None and life_tokens > turns_left_after_this_one:
						h_matrix[fixed_action_index, 10] = -self.cost_misplay_by_strikes[2]
						legal_move_point_values[index] -= self.cost_misplay_by_strikes[2]
						move_score_description += "{:.2f} for discarding when we could play the game out, ".format(self.cost_misplay_by_strikes[2])
						
					# If this is a singled out playable card than we need to penalize discarding it (probably just a little bit)
					if singled_out_playable_card_index == card_index:
					# if singled_out_cards[card_index]:
						legal_move_point_values[index] -= self.singled_out_playable_discard_penalty
						h_matrix[fixed_action_index, 5] = -1
						move_score_description += "{:.2f} for discarding a singled out playable card, ".format(-self.singled_out_playable_discard_penalty)
						say(f"I'm slightly biased against {legal_moves[index]} because it would discard a card that was singled out and playable.")
						
					# If there are more info tokens than cards left in the deck, apply a penalty on more discards
					if info_tokens > deck_size:
						legal_move_point_values[index] -= self.info_token_end_discard_penalty_factor * (info_tokens - deck_size)
						h_matrix[fixed_action_index, 10] -= self.info_token_end_discard_penalty_factor * (info_tokens - deck_size) / self.value_good_discard
						move_score_description += "{:.2f} for discarding when we have more info tokens than cards left in deck, ".format(-self.info_token_end_discard_penalty_factor * (info_tokens - deck_size))
			
			move_score_description += f"total of {legal_move_point_values[index]}"
			move_score_descriptions.append(move_score_description)	

			y_vector[fixed_action_index] = legal_move_point_values[index]

		# select the move with the highest point value and return it
		highest_point_move_index = 0
		highest_point_move_value = None
		for i in range(len(legal_moves)):
			candidate_move = legal_moves[i]
			point_value = legal_move_point_values[i]
			if highest_point_move_value is None or point_value > highest_point_move_value:
				highest_point_move_value = point_value
				highest_point_move_index = i
		"""
		# Rank the fixed index move indices by expected value
		def get_index_of_move(move_to_index):
			for index, candidate_move in enumerate(legal_moves):
				if candidate_move == move_to_index:
					return index

		fixed_action_indices_sorted_by_value = sorted([i for i in range(len(FIXED_ACTIONS))], key=lambda x: legal_move_point_values[get_index_of_move(x)])
		# Create a dictionary to return that includes the values
		action_values_sorted_by_value = [legal_move_point_values[fixed_action_indices_sorted_by_value[i]] for i in range(len(FIXED_ACTIONS))]
		"""
		# Show me what you had
		say("----------------\n")
		for i in range(len(legal_moves)):
			say(f"{legal_moves[i]} -> {legal_move_point_values[i]}\n")
		say("----------------\n")

		# Find all of the moves that have the same value as the highest point move, and send those back too
		tied_top_moves = []
		for i in range(len(legal_moves)):
			if legal_move_point_values[i] == legal_move_point_values[highest_point_move_index]:
				tied_top_moves.append(legal_moves[i])

		# Return the best move
		return legal_moves[highest_point_move_index], highest_point_move_index, tied_top_moves, move_score_descriptions, h_matrix, y_vector
