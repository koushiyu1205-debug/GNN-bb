#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <string>
#include <vector>

#include "lunar_spprc/native_pricer.hpp"

namespace lunar_spprc {

struct BidirectionalStaticSortie {
    SortiePath skeleton;
    std::array<std::uint64_t, 2> task_mask{};
    double release_time = 0.0;
    double latest_departure = -std::numeric_limits<double>::infinity();
    double duration = 0.0;
    double science_weight = 0.0;
    double weighted_completion_offset = 0.0;
    double raw_operating_cost = 0.0;
    double raw_risk = 0.0;
    double task_dual_reward = 0.0;
    bool structurally_feasible = false;
};

struct BidirectionalSuffixSummary {
    std::vector<BidirectionalStaticSortie> sorties;
    std::array<std::uint64_t, 2> task_mask{};
    double latest_input_time = std::numeric_limits<double>::infinity();
    bool structurally_feasible = false;
};

struct BidirectionalFeasibilityOutput {
    std::string status;
    bool feasible = false;
    bool task_sets_disjoint = false;
    bool suffix_boundary_feasible = false;
    bool branch_feasible = false;
    bool static_objective_finite = false;
    bool can_certify_no_negative = false;
    double prefix_end_time = 0.0;
    double suffix_latest_input_time =
        -std::numeric_limits<double>::infinity();
    double journey_end_time = 0.0;
    double raw_operating_cost = 0.0;
    double raw_risk = 0.0;
    double raw_weighted_completion = 0.0;
    double task_dual_reward = 0.0;
    double cut_dual_reward = 0.0;
    double true_reduced_cost =
        std::numeric_limits<double>::infinity();
    std::size_t task_count = 0;
    std::size_t sortie_count = 0;
};

struct BidirectionalBackwardProbeParams {
    std::size_t max_partial_states = 1'000'000;
    std::size_t max_completed_sorties = 1'000'000;
    double timeout_seconds = 30.0;
};

struct BidirectionalBackwardProbeOutput {
    std::string status;
    bool search_exhaustive = false;
    bool frontier_empty = false;
    bool can_certify_no_negative = false;
    std::size_t processed_partial_states = 0;
    std::size_t generated_partial_states = 0;
    std::size_t resource_pruned_partial_states = 0;
    std::size_t duplicate_task_pruned_extensions = 0;
    std::size_t completed_sortie_candidates = 0;
    std::size_t feasible_backward_sortie_seeds = 0;
    std::size_t infeasible_completed_sorties = 0;
    std::size_t max_frontier_size = 0;
    double wall_time_seconds = 0.0;
    std::vector<std::size_t> partial_states_by_task_depth;
    std::vector<std::size_t> feasible_sorties_by_task_depth;
};

struct BidirectionalTaskMeetProbeParams {
    std::size_t max_partial_states_per_direction = 1'000'000;
    std::size_t max_join_checks = 2'000'000;
    double timeout_seconds = 30.0;
};

struct BidirectionalTaskMeetProbeOutput {
    std::string status;
    bool forward_generation_exhaustive = false;
    bool backward_generation_exhaustive = false;
    bool join_exhaustive = false;
    bool can_certify_no_negative = false;
    std::size_t forward_generated_states = 0;
    std::size_t backward_generated_states = 0;
    std::size_t forward_resource_pruned_states = 0;
    std::size_t backward_resource_pruned_states = 0;
    std::size_t forward_duplicate_task_pruned_extensions = 0;
    std::size_t backward_duplicate_task_pruned_extensions = 0;
    std::size_t join_pair_checks = 0;
    std::size_t disjoint_join_pairs = 0;
    std::size_t resource_compatible_join_pairs = 0;
    std::size_t feasible_joined_sorties = 0;
    std::size_t infeasible_joined_sorties = 0;
    std::size_t distinct_task_set_count = 0;
    std::size_t task_set_duplicate_sortie_count = 0;
    std::size_t nondominated_sortie_count = 0;
    std::size_t dominated_sortie_count = 0;
    std::size_t max_variants_per_task_set = 0;
    std::size_t sortie_dominance_candidate_checks = 0;
    double wall_time_seconds = 0.0;
    std::vector<std::size_t> forward_states_by_task_depth;
    std::vector<std::size_t> backward_states_by_task_depth;
    std::vector<std::size_t> feasible_joined_sorties_by_task_count;
    std::vector<std::size_t> nondominated_sorties_by_task_count;
    std::vector<BidirectionalStaticSortie> nondominated_sorties;
};

struct BidirectionalJourneyProbeParams {
    std::size_t max_labels = 1'000'000;
    std::size_t max_extension_checks = 200'000'000;
    std::size_t negative_route_target = 512;
    double negative_epsilon = 1.0e-6;
    double timeout_seconds = 30.0;
    bool immediate_subset_dominance_enabled = true;
};

struct BidirectionalJourneyProbeOutput {
    std::string status;
    bool search_exhaustive = false;
    bool frontier_empty = false;
    bool can_certify_no_negative = false;
    std::size_t sortie_pool_size = 0;
    std::size_t generated_labels = 0;
    std::size_t processed_labels = 0;
    std::size_t dominated_labels = 0;
    std::size_t subset_dominance_candidate_checks = 0;
    std::size_t subset_dominated_labels = 0;
    std::size_t removed_existing_labels = 0;
    std::size_t extension_checks = 0;
    std::size_t task_overlap_rejected_extensions = 0;
    std::size_t branch_rejected_extensions = 0;
    std::size_t time_rejected_extensions = 0;
    std::size_t accepted_extensions = 0;
    std::size_t negative_terminal_label_count = 0;
    std::size_t max_frontier_size = 0;
    double best_true_reduced_cost =
        std::numeric_limits<double>::infinity();
    double first_negative_wall_time_seconds =
        std::numeric_limits<double>::infinity();
    double negative_target_wall_time_seconds =
        std::numeric_limits<double>::infinity();
    double wall_time_seconds = 0.0;
    std::vector<std::size_t> accepted_labels_by_task_count;
};

struct BidirectionalMidpointProbeParams {
    std::size_t max_forward_labels = 250'000;
    std::size_t max_backward_labels = 250'000;
    std::size_t max_crossing_labels = 250'000;
    std::size_t max_extension_checks = 200'000'000;
    std::size_t max_join_checks = 200'000'000;
    std::size_t max_returned_negative_routes = 512;
    double split_fraction = 0.5;
    double negative_epsilon = 1.0e-6;
    double timeout_seconds = 30.0;
};

struct BidirectionalMidpointProbeOutput {
    std::string status;
    bool forward_exhaustive = false;
    bool backward_exhaustive = false;
    bool crossing_exhaustive = false;
    bool join_exhaustive = false;
    bool search_exhaustive = false;
    bool can_certify_no_negative = false;
    std::size_t sortie_pool_size = 0;
    std::size_t forward_generated_labels = 0;
    std::size_t forward_processed_labels = 0;
    std::size_t backward_generated_labels = 0;
    std::size_t backward_processed_labels = 0;
    std::size_t crossing_generated_labels = 0;
    std::size_t crossing_dominated_labels = 0;
    std::size_t forward_dominated_labels = 0;
    std::size_t backward_dominated_labels = 0;
    std::size_t active_forward_labels = 0;
    std::size_t active_backward_labels = 0;
    std::size_t active_crossing_labels = 0;
    std::size_t unindexed_active_join_pairs = 0;
    std::size_t time_index_candidate_join_pairs = 0;
    std::size_t time_index_pruned_join_pairs = 0;
    std::size_t extension_checks = 0;
    std::size_t join_checks = 0;
    std::size_t disjoint_join_checks = 0;
    std::size_t time_compatible_joins = 0;
    std::size_t terminal_route_count = 0;
    std::size_t negative_terminal_route_count = 0;
    std::size_t max_forward_frontier_size = 0;
    std::size_t max_backward_frontier_size = 0;
    double split_time = 0.0;
    double best_true_reduced_cost =
        std::numeric_limits<double>::infinity();
    double first_negative_wall_time_seconds =
        std::numeric_limits<double>::infinity();
    double wall_time_seconds = 0.0;
    std::vector<Route> negative_routes;
};

BidirectionalStaticSortie build_bidirectional_static_sortie(
    const Model& model,
    const SortiePath& skeleton
);

BidirectionalSuffixSummary summarize_bidirectional_suffix(
    const std::vector<BidirectionalStaticSortie>& sorties
);

BidirectionalFeasibilityOutput audit_bidirectional_depot_join(
    const Model& model,
    const std::vector<SortiePath>& forward_sorties,
    const std::vector<SortiePath>& backward_sorties
);

BidirectionalBackwardProbeOutput probe_bidirectional_backward_frontier(
    const Model& model,
    const BidirectionalBackwardProbeParams& params
);

BidirectionalTaskMeetProbeOutput probe_bidirectional_task_meet_frontier(
    const Model& model,
    const BidirectionalTaskMeetProbeParams& params
);

BidirectionalJourneyProbeOutput probe_bidirectional_journey_frontier(
    const Model& model,
    const BidirectionalTaskMeetProbeParams& sortie_params,
    const BidirectionalJourneyProbeParams& journey_params
);

BidirectionalMidpointProbeOutput
probe_bidirectional_midpoint_journey_meet(
    const Model& model,
    const BidirectionalTaskMeetProbeParams& sortie_params,
    const BidirectionalMidpointProbeParams& midpoint_params
);

}  // namespace lunar_spprc
