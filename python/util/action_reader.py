
"""
action_reader is a utility class to parse game actions.
"""

REVEAL_COLOR = "REVEAL_COLOR"
REVEAL_RANK = "REVEAL_RANK"
PLAY = "PLAY"
DISCARD = "DISCARD"

ACTION_TYPES = [REVEAL_COLOR, REVEAL_RANK, PLAY, DISCARD]

def get_action_type(action):
	return action["action_type"]
	
def get_hint_detail(action):
	if "color" in action.keys():
		return action["color"]
	if "card_rank" in action.keys():
		return action["rank"]
	
def is_action_hint(action):
	return action is not None and "REVEAL" in get_action_type(action)
	
def get_card_index(action):
	if "card_index" in action.keys():
		return action["card_index"]
	return None

def get_new_action(action_type, next_attribute):
	action = {}
	action["action_type"] = action_type
	if action_type == REVEAL_COLOR:
		action["color"] = next_attribute
		action["target_offset"] = 1
	if action_type == REVEAL_RANK:
		action["rank"] = next_attribute
		action["target_offset"] = 1
	if action_type == DISCARD or action_type == PLAY:
		action["card_index"] = next_attribute
	return action