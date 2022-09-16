
import numpy
from decision_models.base_agent import FIXED_ACTIONS
import util.observation_reader as ob_reader

def find_instructions(decision_bases, ref_decision_model, instruction_sets=100, verbose=False):

    number_of_instruction_sets = instruction_sets
    instructor_decision_model = ref_decision_model
    initial_weights = instructor_decision_model.w.copy()
    best_matching_weights = instructor_decision_model.w.copy()
    best_match_fraction = 0
    all_matching_fractions = []
    _, initial_match_fraction, _, _ = take_instruction_step(decision_bases, instructor_decision_model, True, verbose)
    all_matching_fractions.append(initial_match_fraction)
    for i in range(number_of_instruction_sets):
        instructor_decision_model, local_corrects, number_of_decisions, delta_w_norm = take_instruction_step(decision_bases, instructor_decision_model, False, verbose)
        if verbose:
            print(f"Finished analysis step {i}/{number_of_instruction_sets} with a matching fraction of {local_corrects}. delta_w_norm: {delta_w_norm}")
        all_matching_fractions.append(local_corrects)
        if local_corrects > best_match_fraction:
            best_matching_weights = instructor_decision_model.w.copy()
            best_match_fraction = local_corrects

    return best_match_fraction, best_matching_weights, initial_match_fraction, initial_weights

def take_instruction_step(decision_bases, decision_model, preserve_instructee = False, verbose = False):
    
    human_decisions_by_fixed_index = []

    number_of_decisions = len(decision_bases)
    stacked_H = numpy.zeros((len(FIXED_ACTIONS) * number_of_decisions, len(decision_model.w)))
    stacked_ideal_outputs = numpy.zeros((len(FIXED_ACTIONS) * number_of_decisions,))
    stacked_norm_minimal_output_difference_ideal_v_current = numpy.zeros((len(FIXED_ACTIONS) * number_of_decisions,))
    
    # This will be the MIN of the norm of the step needed to break any correct decision
    max_step_for_instructions = None

    for line_index, decoded_decision_basis in enumerate(decision_bases):
        _, move_index, _, _, h_matrix, y_vector = decision_model.decide_move(decoded_decision_basis.observation, decoded_decision_basis.my_not_clues, decoded_decision_basis.other_player_not_clues, decoded_decision_basis.playable_probabilities,
        decoded_decision_basis.safely_discardable_probabilities, decoded_decision_basis.unneeded_probabilities,
        decoded_decision_basis.hint_nuggets, decoded_decision_basis.singled_out_playable_card_index, decoded_decision_basis.singled_out_cards, lambda x : x)
        legal_moves = ob_reader.get_legal_moves(decoded_decision_basis.observation)
        
        human_move_index = decoded_decision_basis.human_legal_move_index

        # Calculate norm minimal Y diff
        instructee_choice_fixed_index = FIXED_ACTIONS.index(legal_moves[move_index])
        human_move_index
        human_choice_fixed_index = FIXED_ACTIONS.index(legal_moves[human_move_index])
        human_decisions_by_fixed_index.append(human_choice_fixed_index)
        if instructee_choice_fixed_index != human_choice_fixed_index:
            elements_to_average = [element for element in y_vector if element >= y_vector[instructee_choice_fixed_index]]
            max_element_allowed = numpy.mean(elements_to_average)
            # max_element_allowed = (y_vector[instructee_choice_fixed_index] + y_vector[human_choice_fixed_index]) / 2
            norm_min_z = y_vector.copy()
            for i in range(len(norm_min_z)):
                if norm_min_z[i] > max_element_allowed:
                    norm_min_z[i] = max_element_allowed
                if i == human_choice_fixed_index:
                    norm_min_z[i] = max_element_allowed
            stacked_ideal_outputs[line_index * len(FIXED_ACTIONS):(line_index + 1) * len(FIXED_ACTIONS)] = y_vector
            stacked_norm_minimal_output_difference_ideal_v_current[line_index * len(FIXED_ACTIONS):(line_index + 1) * len(FIXED_ACTIONS)] = norm_min_z - y_vector
            if numpy.linalg.norm(norm_min_z - y_vector) > 100 and verbose:
                print("Got a humungous difference")
                print(norm_min_z)
                print(y_vector)
                print(f"H (with norm {numpy.linalg.norm(h_matrix)})")
                print(h_matrix)
        else:
            # This decision was correct. We need to find the norm of the norm minimal change to be incorrect
            # First, we need the index of the second largest element of y_vector.
            altered_y_vector = y_vector.copy()
            highest_element_value = numpy.max(altered_y_vector)
            for i in range(len(altered_y_vector)):
                if altered_y_vector[i] >= highest_element_value:
                    altered_y_vector[i] = -999
            second_highest_element_value = numpy.max(altered_y_vector)
            second_highest_element_index = None
            for i in range(len(altered_y_vector)):
                if second_highest_element_value == altered_y_vector[i]:
                    second_highest_element_index = i
            
            element_change = (highest_element_value - second_highest_element_value) / 2
            altered_y_vector = numpy.zeros(altered_y_vector.shape)
            altered_y_vector[instructee_choice_fixed_index] = -element_change
            altered_y_vector[second_highest_element_index] = element_change
            norm_minimal_delta_w = numpy.linalg.lstsq(h_matrix, altered_y_vector, rcond=None)[0]
            candidate_norm_limit = numpy.linalg.norm(norm_minimal_delta_w)
            if max_step_for_instructions is None or max_step_for_instructions > candidate_norm_limit:
                max_step_for_instructions = candidate_norm_limit

        # Store the vectors and matrices
        stacked_H[line_index * len(FIXED_ACTIONS):(line_index + 1) * len(FIXED_ACTIONS),:] = h_matrix

    # Uncomment below if you want to analyze the impact of truncation and the norms of the norm minimal differences
    # Reorder columns of h_hat_matrix, then vectorize h_hat, then solve linear system
    column_stack_order = [i for i in range(number_of_decisions)]
    column_stack_order = sorted(column_stack_order, key=lambda i: numpy.linalg.norm(stacked_norm_minimal_output_difference_ideal_v_current[i * len(FIXED_ACTIONS):(i + 1) * len(FIXED_ACTIONS)]))
    sorted_stacked_y_hat = numpy.zeros(stacked_norm_minimal_output_difference_ideal_v_current.shape)
    sorted_stacked_H = numpy.zeros(stacked_H.shape)
    for i in column_stack_order:
        sorted_stacked_y_hat[i * len(FIXED_ACTIONS):(i + 1) * len(FIXED_ACTIONS)] = stacked_norm_minimal_output_difference_ideal_v_current[column_stack_order[i] * len(FIXED_ACTIONS):(column_stack_order[i] + 1) * len(FIXED_ACTIONS)]
        sorted_stacked_H[i * len(FIXED_ACTIONS):(i + 1) * len(FIXED_ACTIONS), :] = stacked_H[column_stack_order[i] * len(FIXED_ACTIONS):(column_stack_order[i] + 1) * len(FIXED_ACTIONS)]

    # Calculate instruction
    delta_w = numpy.zeros((len(decision_model.w)))
    cutoff_fraction = 1
    cutoff_decision_index = int(number_of_decisions * cutoff_fraction)
    truncated_H = sorted_stacked_H[:cutoff_decision_index * len(FIXED_ACTIONS),:]
    truncated_y = sorted_stacked_y_hat[:cutoff_decision_index * len(FIXED_ACTIONS)]

    # For linear system method, just find the solution to the entire linear system
    """
    delta_w = numpy.linalg.lstsq(truncated_H, truncated_y, rcond=None)
    delta_w = delta_w[0]
    """

    # For gradient method, choose a batch size. Then find the gradient contribution from one linear system
    # per batch
    # TODO MIGHT BE GOOD TO RANDOMLY BUILD BATCHES RATHER THAN HAVING THE SAME BATCH MEMBERSHIP FOR EACH STEP
    batch_size = 1
    num_batches = int(len(truncated_y) / batch_size)
    delta_w = numpy.zeros((len(decision_model.w)))
    # delta_w_equity = numpy.zeros((len(decision_model.w)))
    for batch_index in range(num_batches):
        lower_index = batch_index * len(FIXED_ACTIONS)
        upper_index = min((batch_index + 1) * len(FIXED_ACTIONS), len(truncated_y))
        delta_w_contribution = numpy.linalg.lstsq(truncated_H[lower_index:upper_index,:], truncated_y[lower_index:upper_index], rcond=None)[0]
        delta_w += delta_w_contribution / num_batches

    # TODO copy the old w vector here
    starting_w = decision_model.w.copy()

    # See how human like self_play_cyclone is with the corrections applied. stacked_H * (self_play_cyclone.w + delta_w) should be used
    times_agreed_uncorrected = 0
    times_agreed_corrected = 0
    close_enough = 0.001
    new_w = starting_w + delta_w
    for i in range(number_of_decisions):
        human_index = human_decisions_by_fixed_index[i]
        h_matrix = stacked_H[i * len(FIXED_ACTIONS):(i + 1) * len(FIXED_ACTIONS),:]
        self_play_cyclone_output = numpy.matmul(h_matrix, starting_w)
        self_play_cyclone_corrected_output = numpy.matmul(h_matrix, new_w)
        if abs(self_play_cyclone_corrected_output[human_index] - max(self_play_cyclone_corrected_output)) < close_enough:
            times_agreed_corrected += 1
        if abs(self_play_cyclone_output[human_index] - max(self_play_cyclone_output)) < close_enough:
            times_agreed_uncorrected += 1

    # Change and return the decision model
    if not preserve_instructee:
        decision_model.load_new_weights(decision_model.w + delta_w)

    return decision_model, times_agreed_corrected / number_of_decisions, number_of_decisions, numpy.linalg.norm(delta_w)
	
