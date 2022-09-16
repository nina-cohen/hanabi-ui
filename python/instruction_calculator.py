
import sys
import os
import pickle
import time
import numpy
import json
from util.instructive_stepper import find_instructions
from decision_models.self_play_agent import SelfPlayAgent as SelfPlayAgent

GAME_FILE_DIRECTORY = "completed_games"
INSTRUCTIONS_LOG_DIRECTORY = "instructions_log"

def main():
    
    if not os.path.isdir(INSTRUCTIONS_LOG_DIRECTORY):
        os.makedirs(INSTRUCTIONS_LOG_DIRECTORY)

    player_name = sys.argv[1]

    game_directories_found = [directory for directory in os.listdir(GAME_FILE_DIRECTORY) if directory.startswith(player_name + "__0") or directory.startswith(player_name + "__1")]
    isMissing = len(game_directories_found) == 0

    if isMissing:
        print(f"There is no decision bases log for {player_name}")
        sys.stdout.flush()
        return

    decision_bases = []
    for index, directory in enumerate(game_directories_found):
        # If the player is playing extra games, give instructions based only on the most recent game
        # if len(game_directories_found) > 4 and index < len(game_directories_found) - 1:
        #     continue
        with open(os.path.join(GAME_FILE_DIRECTORY, directory, "decision_bases.obj"), "rb") as decision_bases_log:
            game_decision_bases = pickle.load(decision_bases_log)
            decision_bases += game_decision_bases

    if (len(decision_bases) == 0):
        print("The log exists, but there are no decisions in the log.")
        sys.stdout.flush()
        return

    best_match_fraction, best_matching_weights, initial_match_fraction, initial_weights = \
        find_instructions(decision_bases, SelfPlayAgent())

    print(best_matching_weights - initial_weights)
    json_object = {
        "instructions": (initial_weights - best_matching_weights).tolist()
    }

    # Save the instructions given in a log file
    json_object_for_log = {
        "instructions": (initial_weights - best_matching_weights).tolist(),
        "time": time.time()
    }

    player_instructions_log_path = os.path.join(INSTRUCTIONS_LOG_DIRECTORY, f"{player_name}.txt")
    if not os.path.exists(player_instructions_log_path):
        with open(player_instructions_log_path, "w"):
            pass
    with open(player_instructions_log_path, "a") as file:
        file.write(f"{json.dumps(json_object_for_log)}\n")

    print(f"client:{json.dumps(json_object)}")
    sys.stdout.flush()

if __name__ == "__main__":
    main()

