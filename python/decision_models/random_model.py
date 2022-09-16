
from decision_models.decision_model import DecisionModel
import util.action_reader as action_reader
import util.observation_reader as ob_reader
import random

class RandomAgent(DecisionModel):

	"""
	RandomAgent selects a random move from the list of available moves.
	"""

	def get_variant_name(self):
		return f"RandomAgent"

	def decide_move(self, observation, my_not_clues, other_player_not_clues, playable_probabilities, safely_discardable_probabilities, unneeded_probabilities,
		hint_nuggets, singled_out_playable_card_index, singled_out_cards, say):
	
		legal_moves = ob_reader.get_legal_moves(observation)
		
		if len(legal_moves) == 0:
			return None
		
		move_index = random.randrange(len(legal_moves))
		return legal_moves[move_index], move_index, None
	