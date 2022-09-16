
"""
card_utilities contains many short methods for extracting information from game observations, and defines several core constants.
"""

import util.observation_reader as observation_reader
import util.action_reader as action_reader
import math
import copy

COLORS = ["B", "G", "R", "W", "Y"]
HAND_SIZE = 5
MAX_ENTROPY = 50 * 49 * 48 * 47 * 46

TOTAL_CARDS = 50
ALL_RANKS = [0, 0, 0, 1, 1, 2, 2, 3, 3, 4]
ALL_UNIQUE_RANKS = [0, 1, 2, 3, 4]
ALL_CARDS = [{"color": color, "rank": rank} for color in COLORS for rank in ALL_RANKS]
WILD = "wild"

EMPTY_CLUE = {"color": None, "rank": None}
EMPTY_NOT_CLUE = {"colors": [], "ranks": []}

def get_empty_clue():
	return EMPTY_CLUE.copy()
	
def get_empty_not_clue():
	return copy.deepcopy(EMPTY_NOT_CLUE)

def get_color(card):
	return card["color"]

def get_rank(card):
	if "rank" in card.keys():
		return card["rank"]
	if "card_rank" in card.keys():
		return card["card_rank"]
	return None

def rank_invalid(rank):
	return rank == None or rank < 0
	
def get_multiplicity_by_rank(rank):
	return int(rank == 0) + int(rank < 4) + 1

def does_card_match_clue(card, clue):

	# the clue doesn't need to fully specify the card; it simply needs to not contradict the card
	clue_color = get_color(clue)
	clue_rank = get_rank(clue)
	card_color = get_color(card)
	card_rank = get_rank(card)
	return (clue_color == None or clue_color == card_color) and (clue_rank == None or clue_rank == card_rank)

def get_cards_matching_clue(clue, not_clue):

	# This method does not return unique cards matching the clue, but all cards matching the clue. This mean,
	# for example, that there are three cards in the starting deck that match color=Y, rank=0.

	# Get possible colors from not_clue
	possible_colors = []
	for color in COLORS:
		if color not in not_clue["colors"]:
			possible_colors.append(color)
	
	# Get possible ranks from not_clue
	possible_ranks = []
	for rank in ALL_RANKS:
		if rank not in not_clue["ranks"]:
			possible_ranks.append(rank)

	clue_color = get_color(clue)
	clue_rank = get_rank(clue)
	ranks = [clue_rank] * get_multiplicity_by_rank(clue_rank) if clue_rank != None else possible_ranks
	colors = [clue_color] if clue_color != None else possible_colors
	
	matching_cards = []
	for color in colors:
		for rank in ranks:
			matching_cards.append(make_card(color, rank))
	return matching_cards

def get_indexed_wild_card(index):
	return {"color": WILD, "rank": index}

def is_card_wild(card):
	return get_color(card) == WILD

def make_card(color = None, rank = None):
	return {"color": color, "rank": rank}
	
def merge_clue(old_clues, clue):
	for i in range(len(old_clues)):
		old_clues_card = old_clues[i]
		new_clue_card = clue[i]
		if get_color(old_clues_card) == None and get_color(new_clue_card) != None:
			old_clues_card["color"] = get_color(new_clue_card)
		if rank_invalid(get_rank(old_clues_card)) and not rank_invalid(get_rank(new_clue_card)):
			old_clues_card["rank"] = get_rank(new_clue_card)

def merge_not_clue(old_not_clues, not_clue):
	for i in range(len(not_clue)):
		old_not_clues_card = old_not_clues[i]
		new_not_clue_card = not_clue[i]
		for color in new_not_clue_card["colors"]:
			if color not in old_not_clues_card["colors"]:
				old_not_clues_card["colors"].append(color)
				if color is None:
					print(f"Just merged a None color from this not clue {not_clue}")
					nothing = input()
		for rank in new_not_clue_card["ranks"]:
			if rank not in old_not_clues_card["ranks"]:
				old_not_clues_card["ranks"].append(rank)
				if rank is None:
					print(f"Just merged a None rank from this not clue {not_clue}")
					nothing = input()

def delete_slot(clues, index, replacement = None):
	# Keep in mind it is important to add the replacement to the end of the array, since this is how the hanabi gym operates.
	element_to_remove = clues[index]
	clues.pop(index)
	if replacement != None:
		clues.append(replacement)
	return element_to_remove

def get_not_clue_from_clue(clue):
	not_clue = [get_empty_not_clue() for i in range(HAND_SIZE)]
	colors = []
	ranks = []
	for card in clue:
		color = get_color(card)
		rank = get_rank(card)
		if color != None:
			colors.append(color)
			break
		if rank_invalid(rank):
			ranks.append(rank)
			break
	for i in range(HAND_SIZE):
		card = clue[i]
		if card == EMPTY_CLUE:
			not_clue[i]["colors"] = colors.copy()
			not_clue[i]["ranks"] = ranks.copy()
	return not_clue

def has_overrepresented_card(card_list):
	unique_cards = []
	multiplicities = []
	for card in card_list:
		if card not in unique_cards:
			unique_cards.append(card)
			multiplicities.append(1)
		else:
			for i in range(len(unique_cards)):
				unique_card = unique_cards[i]
				if card == unique_card:
					multiplicities[i] += 1
	
	# Check if any multiplicity is too high
	for i in range(len(unique_cards)):
		if multiplicities[i] > get_multiplicity_by_rank(get_rank(unique_cards[i])):
			return True
	return False

def get_hand_entropy(clues, not_clues, reserved_cards):
	# clues is a list of list of clues, telling you what is known about each card in hand.
	# reserved_cards are any cards that, for any reason, are known to not be in the hand in question.
	# This helps the function be used generally for self hand entropy calculations as well as calculating the entropy of the other player's hand.
	
	# If the clues are empty, there is only one possible hand (that of having no cards)
	if len(clues) == 0:
		return (0, [], 0)

	# For each card in hand, generate a list of independently possible cards
	possible_card_lists = []
	for i in range(len(clues)):
		possible_card_lists.append([])
	for i in range(len(possible_card_lists)):
		clue = clues[i]
		not_clue = not_clues[i]
		# TODO Don't want to make a wild card off of a slot that has no clue but has some not clues!!!
		if clue == EMPTY_CLUE:# and not_clue == EMPTY_NOT_CLUE:
			# Rather than fill the list with every possible card, let's use a shorthand notation to show that this card could be any not-otherwise-present-in-hand card.
			possible_card_lists[i] = [get_indexed_wild_card(i)]
			# Ready to work with the next slot in hand
			continue
		else:
			# We want to enumerate all cards that could be in this slot
			card_list = get_cards_matching_clue(clue, not_clue)

			# We need to remove any cards that are reserved
			for reserved_card in reserved_cards:
				if reserved_card in card_list:
					card_list.remove(reserved_card)

			# Now we can save this card list
			possible_card_lists[i] = card_list
	
	# We'd like to find the wild_card_entropy_multiplier for the wildcards.
	wild_card_count = 0

	for slot in possible_card_lists:
		if is_card_wild(slot[0]):
			wild_card_count += 1
	possible_card_pool_size = TOTAL_CARDS - len(possible_card_lists) + wild_card_count - len(reserved_cards)
	if possible_card_pool_size - wild_card_count < 0 or possible_card_pool_size < 0:
		print(f"Negative factorial encountered. Total cards: {TOTAL_CARDS}, hand size (the fixed constant): {HAND_SIZE}, wild_card_count: {wild_card_count}, reserved_cards: {len(reserved_cards)}. Possible card pool size of {possible_card_pool_size}")
	wild_card_entropy_multiplier = int(math.factorial(possible_card_pool_size) / math.factorial(possible_card_pool_size - wild_card_count))

	# Iterate through all combinations of cards in hand using each card's list.
	# Keep a running list of cards used so far in the combination. This allows you to short circuit if a card is duplicated.
	entropy = 0
	list_of_possible_hands = []

	recursive_get_possible_hands(possible_card_lists, possible_card_lists[0], [], list_of_possible_hands)
	
	entropy = len(list_of_possible_hands)
	
	# Multiply the entropy by the wild_card_entropy_multiplier
	entropy *= wild_card_entropy_multiplier

	# Return a tuple with a list of all possible hands and a count
	return (entropy, list_of_possible_hands, wild_card_entropy_multiplier)

def recursive_get_possible_hands(possible_card_lists, temporary_card_list, current_cards, list_of_possible_hands):
	level = len(current_cards)
	for card in temporary_card_list:
		new_current_cards = current_cards.copy()
		new_current_cards.append(card)
		if level == len(possible_card_lists) - 1:
			# End of the recursion
			list_of_possible_hands.append(new_current_cards.copy())
		else:
			next_temporary_card_list = possible_card_lists[level + 1].copy()
			for used_card in new_current_cards:
				if used_card in next_temporary_card_list:
					next_temporary_card_list.remove(used_card)
			recursive_get_possible_hands(possible_card_lists, next_temporary_card_list, new_current_cards, list_of_possible_hands)

def get_clues_from_hint(hint, hand):
	current_hand_size = len(hand)
	clue_hand_relevance = [get_empty_clue() for i in range(current_hand_size)]
	not_clue_hand_relevance = [get_empty_not_clue() for i in range(current_hand_size)]
	if action_reader.get_action_type(hint) == action_reader.REVEAL_COLOR:
		clue_color = get_color(hint)
		for i in range(current_hand_size):
			hand_card = hand[i]
			if get_color(hand_card) == clue_color:
				clue_hand_relevance[i]["color"] = clue_color
			else:
				not_clue_hand_relevance[i]["colors"].append(clue_color)
	else:
		clue_rank = get_rank(hint)
		for i in range(current_hand_size):
			hand_card = hand[i]
			if get_rank(hand_card) == clue_rank:
				clue_hand_relevance[i]["rank"] = clue_rank
			else:
				not_clue_hand_relevance[i]["ranks"].append(clue_rank)
				
	return (clue_hand_relevance, not_clue_hand_relevance)

def get_clues_from_observation_change(old_observation, new_observation):
	
	# Judge the clue that was given by new information in card_knowledge
	old_clues = observation_reader.get_my_clues(old_observation)
	new_clues = observation_reader.get_my_clues(new_observation)
	
	current_hand_size = len(new_clues)

	clues_to_return = [get_empty_clue() for i in range(current_hand_size)]
	not_clues_to_return = [get_empty_not_clue() for i in range(current_hand_size)]
	does_clue_concern_a_color = False
	clue_color_or_rank = None
	
	# Sometimes a hint gives the player no information. We can check for that now and save some computation time.
	if old_clues == new_clues:
		return (clues_to_return, not_clues_to_return)

	for i in range(len(new_clues)):
		old_card_clue = old_clues[i]
		new_card_clue = new_clues[i]
		if old_card_clue != new_card_clue:
			# Then there is fresh information in the new clue
			# We've added a check here to make sure that the new card clue is not none. This can happen if a discard caused a slot with a previously known color to now have a card with an unknown color. From a raw observation comparison, it appears as if the color knowledge went from some color to None.
			if get_color(new_card_clue) != get_color(old_card_clue) and get_color(new_card_clue) is not None:
				# Then the hint was the color of this card
				clue_color_or_rank = get_color(new_card_clue)
				clues_to_return[i]["color"] = clue_color_or_rank
				does_clue_concern_a_color = True
				
			elif get_rank(new_card_clue) is not None:
				# Then the clues was the rank of this card
				clue_color_or_rank = get_rank(new_card_clue)
				clues_to_return[i]["rank"] = clue_color_or_rank

	# Now to build the not_clue_to_return
	if does_clue_concern_a_color:
		for i in range(len(clues_to_return)):
			card = new_clues[i]
			# Here, you can't just add to the not clue if the clue is missing the color or rank. It might be missing because the player already had card knowledge conerning that card. Therefore, you need to verify that the ith card in the recipient player's care knowledge is NOT equal to get_color(card)
			if get_color(card) != clue_color_or_rank:
				not_clues_to_return[i]["colors"].append(clue_color_or_rank)
	else:
		for i in range(len(clues_to_return)):
			card = new_clues[i]
			if get_rank(card) != clue_color_or_rank:
				not_clues_to_return[i]["ranks"].append(clue_color_or_rank)
				
	return (clues_to_return, not_clues_to_return)
	
def get_entropy_change_factor_for_clue(clues, not_clues, reserved_cards, new_clue, new_not_clue):
	old_entropy, possible_hand_list, _ = get_hand_entropy(clues, not_clues, reserved_cards)
	new_clues = copy.deepcopy(clues)
	merge_clue(new_clues, new_clue)
	new_not_clues = copy.deepcopy(not_clues)
	merge_not_clue(new_not_clues, new_not_clue)
	
	# Find the hypothetical new entropy if this clue was given
	new_entropy, new_possible_hand_list, _ = get_hand_entropy(new_clues, new_not_clues, reserved_cards)
	
	# Return the entropy change factor, and the old entropy
	return (new_entropy / old_entropy, old_entropy, possible_hand_list, new_entropy, new_possible_hand_list)

def is_card_playable(card, fireworks):
	for color, cards_played in fireworks.items():
		if color == get_color(card) and cards_played == get_rank(card):
			return True
	return False
	
def get_unique_playable_cards(fireworks):
	playable_cards = []
	for color, count in fireworks.items():
		if count < 5:
			playable_cards.append(make_card(color, count))
	return playable_cards

def get_playable_probabilities(clues, not_clues, reserved_cards, fireworks):

	# Get the pool of non-reserved cards
	non_reserved_cards = []
	reserved_cards_copy = reserved_cards.copy()
	for card in ALL_CARDS:
		if card not in reserved_cards_copy:
			non_reserved_cards.append(card)
		else:
			# Need to remove from the copy
			reserved_cards_copy.remove(card)

	# Find the playable probabilities
	playable_probabilities = [[] for i in range(len(clues))]
	for i in range(len(clues)):
		clue = clues[i]
		not_clue = not_clues[i]
		
		cards_matching_clue = get_cards_matching_clue(clue, not_clue)
		
		possible_card_count = 0
		playable_card_count = 0
		for card in non_reserved_cards:
			if card in cards_matching_clue:
				other_occurrences = 0
				for j in range(len(clues)):
					if i != j:
						other_clue = clues[j]
						if other_clue == card:
							other_occurrences += 1
				if other_occurrences < non_reserved_cards.count(card):
					possible_card_count += 1
					if is_card_playable(card, fireworks):
						playable_card_count += 1
		
		playable_probabilities[i] = playable_card_count / possible_card_count
		
	return playable_probabilities
	
def is_already_played(card, fireworks):
	color = get_color(card)
	return get_rank(card) < fireworks[color]
	
def is_safely_discardable(card, fireworks, non_discarded_cards, discarded_cards, deck_size):
	if is_card_wild(card):
		# This is very intentional. Code that calls this method relies on wildcards being considered non-safely discardable even if they technically are.
		return False
	
	# Apply the progressive max rank based on the state of the game
	deficit = get_rank(card) - fireworks[get_color(card)]
	rank_above_which_safely_discardable = 1.5 + 3**2 * (deck_size / (40/3))**2

	if deficit > rank_above_which_safely_discardable:
		return True
	
	if is_already_played(card, fireworks) or non_discarded_cards.count(card) > 1:
		return True
	# Then this card is not played and is the only copy of itself left in play. However, we might be locked out of ever playing this card based on the state of cards below it (e.g. A white 3 is safely discardable if all white 2's are discarded (the players can never play a white 3 or higher)).
	for lower_rank in range(get_rank(card)):
		lower_card = make_card(get_color(card), lower_rank)
		if discarded_cards.count(lower_card) == get_multiplicity_by_rank(lower_rank):
			return True
	# Then this card is the last copy of itself in the non_reserved_cards and it is not already played and not locked out. This is not safely discardable.
	return False
	
def is_unneeded(card, fireworks, discarded_cards):
	# An unneeded card is one that is either already played or can never be played (because all copies of a lower card are discarded).
	if is_already_played(card, fireworks):
		return True
	for lower_rank in range(get_rank(card)):
		lower_card = make_card(get_color(card), lower_rank)
		if discarded_cards.count(lower_card) == get_multiplicity_by_rank(lower_rank):
			return True
	# Then this card is not already played and not locked out.
	return False

def get_safely_discardable_probabilities(clues, not_clues, discarded_cards, fireworks, deck_size, other_player_hand = None):
	
	# Get the pool of non-discarded cards
	unseen_cards = get_unseen_cards(discarded_cards, fireworks, other_player_hand)

	# Find the safely discardable probabilities
	safely_discardable_probabilities = [[] for i in range(len(clues))]
	for i in range(len(clues)):
		clue = clues[i]
		not_clue = not_clues[i]
		
		cards_matching_clue = get_cards_matching_clue(clue, not_clue)
		
		possible_card_count = 0
		safely_discardable_card_count = 0
		for card in unseen_cards:
			if card in cards_matching_clue:
				possible_card_count += 1
				if is_safely_discardable(card, fireworks, unseen_cards, discarded_cards, deck_size):
					safely_discardable_card_count += 1
		
		safely_discardable_probabilities[i] = safely_discardable_card_count / possible_card_count
		
	return safely_discardable_probabilities

def get_unneeded_probabilities(clues, not_clues, discarded_cards, fireworks, other_player_hand = None):
	
	# Get the pool of non-discarded cards
	unseen_cards = get_unseen_cards(discarded_cards, fireworks, other_player_hand)

	# Find the playable probabilities
	unneeded_probabilities = [[] for i in range(len(clues))]
	for i in range(len(clues)):
		clue = clues[i]
		not_clue = not_clues[i]
		
		cards_matching_clue = get_cards_matching_clue(clue, not_clue)
		
		possible_card_count = 0
		unneeded_card_count = 0
		for card in unseen_cards:
			if card in cards_matching_clue:
				possible_card_count += 1
				if is_unneeded(card, fireworks, discarded_cards):
					unneeded_card_count += 1
		
		unneeded_probabilities[i] = unneeded_card_count / possible_card_count
		
	return unneeded_probabilities
	
def get_unseen_cards(discarded_cards, fireworks, other_player_hand = None):

	# Get the pool of non-discarded cards
	unseen_cards = []
	discarded_cards_copy = discarded_cards.copy()
	for card in ALL_CARDS:
		if card not in discarded_cards_copy:
			unseen_cards.append(card)
		else:
			# Need to remove from the copy
			discarded_cards_copy.remove(card)

	# Need to also remove from the pool of non-discarded cards all cards that have been played
	for color, count in fireworks.items():
		for rank in range(count):
			played_card = make_card(color, rank)
			if played_card in unseen_cards:
				unseen_cards.remove(played_card)

	# Finally, remove cards that are seen in the other player's hand
	if other_player_hand is not None:
		for card in other_player_hand:
			if card in unseen_cards:
				unseen_cards.remove(card)

	return unseen_cards

def fast_binom(a, b):
	result = 1
	for i in range(b + 1, a + 1):
		result *= i
	return result
