import sys
import os
import json
import pickle
from util.gym import Gym as Gym
import util.observation_bundle_reader as bundle_reader
import util.observation_reader as observation_reader
import policy
from decision_models.self_play_agent import SelfPlayAgent as SelfPlayAgent
import util.action_reader as action_reader
import copy
from canned_decks import get_canned_deck

GAME_FILE_DIRECTORY = "games_files"
COMPLETED_GAME_FILE_DIRECTORY = "completed_games"
REFRESH_SUFFIX = ",0,0,0"
RANK_CLUE_CODE = "R"
COLOR_CLUE_CODE = "C"
PLAY_CLUE_CODE = "P"
ADVICE_STRING = "advice"
SET_DECK = True

def main():

    message = sys.argv[1]

    message_parts = message.split(",")
    player_name = message_parts[0]

    # If no game exists for this player, then a new game will be started
    player_root_path = os.path.join(os.getcwd(), GAME_FILE_DIRECTORY, player_name)
    is_new_game = not os.path.isdir(player_root_path)

    # Figure out the game index for selecting the deck. Store the game index in a file so it is easily found later
    deck_type = 0

    directories = os.listdir(COMPLETED_GAME_FILE_DIRECTORY)
    for directory in directories:
        if player_name + "__" in directory:
            deck_type += 1

    if is_new_game:

        os.mkdir(player_root_path)

        new_deck = None
        if deck_type < 4 and SET_DECK:
            new_deck = get_canned_deck(deck_type)

        gym = Gym(new_deck)
        agent0 = policy.MyPolicy(SelfPlayAgent())
        agent1 = policy.MyPolicy(SelfPlayAgent())
        agent0.game_reset(0)
        agent1.game_reset(1)
        agent0.set_verbosity(False)
        agent1.set_verbosity(False)

        print(gym.deck)

        agents = [agent0, agent1]

        observation_bundle = gym.get_observation_bundle()

        # Save this game to file
        save_state(gym, agents, player_root_path)

        # Start the decision bases log
        with open(os.path.join(player_root_path, "decision_bases.obj"), "wb") as decision_bases_log:
            pickle.dump([], decision_bases_log)

        # Create logs
        with open(os.path.join(player_root_path, "game_log.txt"), "w") as file:
            file.write(json.dumps(gym.get_observation_bundle()) + "\n")

        # Store in a file which deck was used
        with open(os.path.join(player_root_path, "deck_type.txt"), "w") as file:
            file.write(str(deck_type))

        after_human = observation_bundle
        # Since this is the beginning of the game, just give the same bundle for after human and after cyclone
        after_cyclone = after_human
        print(get_client_message_from_two_observation_bundles(after_human, after_cyclone, deck_type))
        sys.stdout.flush()

    else:

        gym = Gym()

        agents = [None, None]

        # Load in the game
        for player_index in range(2):
            file_handler = open(os.path.join(player_root_path, f"agent_{player_index}.obj"), "rb")
            agents[player_index] = pickle.load(file_handler)
            file_handler.close()

        agent0 = agents[0]
        agent1 = agents[1]

        file_handler = open(os.path.join(player_root_path, "gym.obj"), "rb")
        gym = pickle.load(file_handler)
        file_handler.close()

        # Do not call agent0.get_actions if this is a refresh (suffix ",0,0,0"). Doing so would advance the game state.
        if REFRESH_SUFFIX in message:
            observation_bundle = gym.get_observation_bundle()
            print(get_client_message_from_two_observation_bundles(observation_bundle, observation_bundle, deck_type))
            sys.stdout.flush()
            return

        # If the client just asked for advice, return the cyclone recommended move and terminate.
        if ADVICE_STRING in message:
            # It's ok to update the agent here, but make sure not to save this, since the move was not actually made
            cyclone_recommended_move, decision_basis, _ = agent0.get_actions(gym.get_observation_bundle())
            response_object = {
                "move": cyclone_recommended_move
            }
            print(f"client:{json.dumps(response_object)}")
            sys.stdout.flush()
            return

        # Even though this is the client's turn, the bot agent needs to be given the bundle to update not clues etc.
        cyclone_recommended_move, decision_basis, tied_top_moves = agent0.get_actions(gym.get_observation_bundle())
        print("Tied top moves")
        print(tied_top_moves)
        agent1.get_actions(gym.get_observation_bundle())

        print("Updated human not clues are", agent0.my_not_clues)
        print("Human's perception of bot not clues are", agent0.other_player_not_clues)

        client_move_count = message_parts[1]
        client_move_code = message_parts[2]
        client_move_subcode = message_parts[3]

        action_type = action_reader.DISCARD
        if client_move_code == RANK_CLUE_CODE:
            action_type = action_reader.REVEAL_RANK
        if client_move_code == COLOR_CLUE_CODE:
            action_type = action_reader.REVEAL_COLOR
        if client_move_code == PLAY_CLUE_CODE:
            action_type = action_reader.PLAY

        # Enforce the 0-4 rank convention for Cyclone, since the client uses the 1-5 rank convention
        if client_move_subcode.isnumeric():
            client_move_subcode = int(client_move_subcode)

        move = action_reader.get_new_action(action_type, client_move_subcode)
        legal_moves = observation_reader.get_legal_moves(bundle_reader.get_observations(gym.get_observation_bundle())[0])
        legal_move_index = legal_moves.index(move)

        if legal_move_index < 0:
            print("Problem. Could not find legal move " + move + " in legal moves: " + legal_moves)
        else:
            print("Success. " + str(legal_move_index))

        # Update the decision basis so that the client's move index is recorded
        decision_basis.human_legal_move_index = legal_move_index

        # Load the decision basis file to append the decision basis, or create the file if it does not exist
        decision_bases = None
        with open(os.path.join(player_root_path, "decision_bases.obj"), "rb") as decision_bases_log:
            decision_bases = pickle.load(decision_bases_log)

        decision_bases.append(decision_basis)
        print(f"There are now {len(decision_bases)} decisions in the log.")

        # Save the decision basis file
        with open(os.path.join(player_root_path, "decision_bases.obj"), "wb") as decision_bases_log:
            pickle.dump(decision_bases, decision_bases_log)

        # Intercept the move and do not advance the game state if the game is already over
        if gym.is_game_over():
            print(get_client_message_from_two_observation_bundles(gym.get_observation_bundle(), gym.get_observation_bundle(), deck_type, cyclone_recommended_move, tied_top_moves))
            return

        # Make the client move
        gym.step(move)

        # Store the after_human_move observation bundle for returning to the UI
        after_human = copy.deepcopy(gym.get_observation_bundle())

        # Start collecting observation bundles for the l2rm style log
        observation_bundles_for_l2rm_log = [after_human]

        # Check if the game is over
        if gym.is_game_over():
            # Save the l2rm style logs now
            with open(os.path.join(player_root_path, "game_log.txt"), "a") as file:
                for observation in observation_bundles_for_l2rm_log:
                    file.write(json.dumps(observation) + "\n")
            print(get_client_message_from_two_observation_bundles(after_human, after_human, deck_type, cyclone_recommended_move, tied_top_moves))
            return

        # Get Cyclone's move
        _, _, _ = agent0.get_actions(gym.get_observation_bundle())
        cyclone_move, _, _ = agent1.get_actions(gym.get_observation_bundle())

        print("Bot not clues are", agent1.my_not_clues)
        print("Bot perception of human not clues are", agent1.other_player_not_clues)

        # Make Cyclone's move
        gym.step(cyclone_move)

        # Record observation bundle for l2rm style log
        observation_bundles_for_l2rm_log.append(gym.get_observation_bundle())

        # Save the l2rm style logs now
        with open(os.path.join(player_root_path, "game_log.txt"), "a") as file:
            for observation in observation_bundles_for_l2rm_log:
                file.write(json.dumps(observation) + "\n")

        # Save the game state
        save_state(gym, agents, player_root_path)

        # Send back the observation from the human player's perspective
        print(get_client_message_from_two_observation_bundles(after_human, gym.get_observation_bundle(), deck_type, cyclone_recommended_move, tied_top_moves))


def save_state(gym, agents, path):
    for player_index in range(2):
        agent = agents[player_index]
        file_handler = open(os.path.join(path, f"agent_{player_index}.obj"), "wb")
        pickle.dump(agent, file_handler)
        file_handler.close()

    file_handler = open(os.path.join(path, "gym.obj"), "wb")
    pickle.dump(gym, file_handler)
    file_handler.close()


def get_client_message_from_observation_bundle(bundle):
    response = bundle_reader.get_observations(bundle)[0]
    # Manually add the information about the human player's hand
    response["observed_hands"][0] = bundle_reader.get_player_hand_by_index(bundle, 0)
    return response


def get_client_message_from_two_observation_bundles(after_human_move, after_cyclone_move, deck_type, cyclone_recommendation = None, tied_top_moves = None):
    top_level_object = {
        "after_human_move": get_client_message_from_observation_bundle(after_human_move),
        "after_cyclone_move": get_client_message_from_observation_bundle(after_cyclone_move),
        "cyclone_recommendation": cyclone_recommendation,
        "deck_type": deck_type,
        "tied_top_moves": tied_top_moves
    }
    return f"client:{json.dumps(top_level_object)}"

if __name__ == "__main__":
    main()
