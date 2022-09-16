
class DecisionModel:

	def __init__(self):
		self.need_probabilities = True

	def decide_move(self, observation, my_not_clues, other_player_not_clues, playable_probabilities, safely_discardable_probabilities, hint_nuggets, singled_out_playable_card_index, say):
		say("Looks like the decide_move method for a decision model was not overridden.")
		return None
