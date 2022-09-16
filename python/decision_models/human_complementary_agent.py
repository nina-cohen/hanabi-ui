
from decision_models.base_agent import BaseAgent
import numpy

class HumanComplementaryAgent(BaseAgent):

    """
    HumanComplementaryAgent was optimized to achieve high score when paired with the HumanLikeAgent.
    """

    def __init__(self):
        self.cost_misplay_by_strikes = [1, 1, 1000000]
        self.singled_out_playable_value_bump = 1.5
        self.decision_to_single_out_playable_card_bonus = 3
        self.decision_to_single_out_non_playable_card_penalty = 5
        self.singled_out_playable_discard_penalty = 2
        self.info_token_end_discard_penalty_factor = 5
        self.cost_misplay_other_player = 0
        self.play_multiplier = 10
        self.self_certain_play_bonus = 1000
        self.clue_bonus_per_info_token = 0.1
        self.value_good_discard = 0.55
        self.force_safe_discard_factor = 1

        self.w = numpy.array([self.cost_misplay_by_strikes[0], self.cost_misplay_by_strikes[2], self.singled_out_playable_value_bump, self.decision_to_single_out_playable_card_bonus,
            self.decision_to_single_out_non_playable_card_penalty, self.singled_out_playable_discard_penalty, self.cost_misplay_other_player, self.play_multiplier, 
            self.self_certain_play_bonus, self.clue_bonus_per_info_token, self.value_good_discard, self.force_safe_discard_factor])

    def get_variant_name(self):
        return f"HumanComplementaryAgent"