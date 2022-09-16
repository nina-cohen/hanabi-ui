
import util.card_utilities as cu
import util.action_reader as action_reader
import copy

def get_other_player_hand(observation):
	return observation["observed_hands"][1]

def get_discarded_cards(observation):
	return observation["discard_pile"]

def get_played_cards(observation):
	played_cards = []
	fireworks = observation["fireworks"]
	for color in cu.COLORS:
		cards_played_of_this_color = fireworks[color]
		for rank in range(cards_played_of_this_color):
			played_cards.append(cu.make_card(color, rank))
	return played_cards

def get_my_clues(observation):
	# This method returns clues that PERTAIN to my cards, NOT clues I've given to the other player about his cards.
	return observation["card_knowledge"][0]

def get_other_player_clues(observation):
	# This method returns clues that PERTAIN to the other player's cards , clues that I've given the other player.
	return observation["card_knowledge"][1]

def get_my_reserved_cards(observation):
	"""
	This method returns a list of cards that are:
		1) Played (i.e. in the fireworks list)
		2) Discarded
		3) In the other player's hand
		
	Therefore, the exclusion of these cards from the deck are the cards that are
		1) In my hand
		2) In the deck
	"""
	reserved_cards = get_played_cards(observation)
	reserved_cards.extend(get_discarded_cards(observation))
	reserved_cards.extend(get_other_player_hand(observation))
	
	return reserved_cards

def get_other_player_reserved_cards(observation):
	reserved_cards = get_played_cards(observation)
	reserved_cards.extend(get_discarded_cards(observation))
	
	return reserved_cards
	
def get_my_non_reserved_cards(observation):
	reserved_cards = get_my_reserved_cards(observation)
	non_reserved_cards = copy.deepcopy(cu.ALL_CARDS)
	for card in reserved_cards:
		if card in non_reserved_cards:
			non_reserved_cards.remove(card)
	return non_reserved_cards
	
def get_other_player_non_reserved_cards(observation):
	reserved_cards = get_other_player_reserved_cards(observation)
	non_reserved_cards = copy.deepcopy(cu.ALL_CARDS)
	for card in reserved_cards:
		if card in non_reserved_cards:
			non_reserved_cards.remove(card)
	return non_reserved_cards

def get_fireworks(observation):
	return observation["fireworks"]
	
def adjust_fireworks_with_playable_card(observation, card):
	fireworks = get_fireworks(observation)
	if not cu.is_card_playable(card, fireworks):
		return
	fireworks[cu.get_color(card)] += 1

def get_deck_size(observation):
	return observation["deck_size"]
	
def decrement_deck_size(observation):
	observation["deck_size"] -= 1
	
def get_life_tokens(observation):
	return observation["life_tokens"]
	
def decrement_life_tokens(observation):
	observation["life_tokens"] -= 1
	
def get_information_tokens(observation):
	return observation["information_tokens"]
	
def increment_information_tokens(observation):
	observation["information_tokens"] += 1
	
def decrement_information_tokens(observation):
	observation["information_tokens"] -= 1
	
def get_number_of_players(observation):
	return observation["num_players"]
	
def get_current_player(observation):
	return observation["current_player"]
	
def get_current_player_offset(observation):
	return observation["current_player_offset"]

def get_observed_hand_by_index(observation, index):
	return observation["observed_hands"][index]
	
def get_legal_moves(observation):
	return observation["legal_moves"]
	
def get_previous_move(observation):
	return observation["prev_move"]