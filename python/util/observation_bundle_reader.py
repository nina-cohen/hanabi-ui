
import util.observation_reader as ob_reader

def get_observations(observation_bundle):
	return observation_bundle["player_observations"]
	
def get_number_of_players(observation_bundle):
	return ob_reader.get_number_of_players(get_observations(observation_bundle)[0])

def get_player_hand_by_index(observation_bundle, player_index):
	return observation_bundle["player_observations"][not player_index]["observed_hands"][1]
	
def get_player_clues_by_index(observation_bundle, player_index):
	return ob_reader.get_my_clues(get_observations(observation_bundle)[player_index])
	
def get_fireworks(observation_bundle):
	return ob_reader.get_fireworks(get_observations(observation_bundle)[0])
	
def adjust_fireworks_with_playable_card(observation_bundle, card):
	observations = get_observations(observation_bundle)
	for observation in observations:
		ob_reader.adjust_fireworks_with_playable_card(observation, card)

def get_deck_size(observation_bundle):
	return ob_reader.get_deck_size(get_observations(observation_bundle)[0])

def decrement_deck_size(observation_bundle):
	for observation in get_observations(observation_bundle):
		ob_reader.decrement_deck_size(observation)
		
def get_life_tokens(observation_bundle):
	return ob_reader.get_life_tokens(get_observations(observation_bundle)[0])

def decrement_life_tokens(observation_bundle):
	for observation in get_observations(observation_bundle):
		ob_reader.decrement_life_tokens(observation)
		
def get_information_tokens(observation_bundle):
	return ob_reader.get_information_tokens(get_observations(observation_bundle)[0])
	
def increment_information_tokens(observation_bundle):
	for observation in get_observations(observation_bundle):
		ob_reader.increment_information_tokens(observation)
	
def decrement_information_tokens(observation_bundle):
	for observation in get_observations(observation_bundle):
		ob_reader.decrement_information_tokens(observation)
		
def get_discarded_cards(observation_bundle):
	return ob_reader.get_discarded_cards(get_observations(observation_bundle)[0])
	
def is_game_over(observation_bundle):
	return (len(get_player_hand_by_index(observation_bundle, 0)) == 0 and len(get_player_hand_by_index(observation_bundle, 1)) == 0) or get_life_tokens(observation_bundle) == 0