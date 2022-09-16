
class DecisionBasis:

    def __init__(self, observation, my_not_clues, other_player_not_clues, playable_probabilities, \
        safely_discardable_probabilities, unneeded_probabilities, hint_nuggets, singled_out_playable_card_index, singled_out_cards, human_legal_move_index):
        self.observation = observation
        self.my_not_clues = my_not_clues
        self.other_player_not_clues = other_player_not_clues
        self.playable_probabilities = playable_probabilities
        self.safely_discardable_probabilities = safely_discardable_probabilities
        self.unneeded_probabilities = unneeded_probabilities
        self.hint_nuggets = hint_nuggets
        self.singled_out_playable_card_index = singled_out_playable_card_index
        self.singled_out_cards = singled_out_cards
        self.human_legal_move_index = human_legal_move_index