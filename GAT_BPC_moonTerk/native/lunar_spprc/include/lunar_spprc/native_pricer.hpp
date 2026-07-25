#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>
#include <string>
#include <unordered_map>
#include <vector>

namespace lunar_spprc {

enum class ActionKind { VisitTask, ReturnDepot, Terminate };

enum class BranchSense { SameJourney, DifferentJourney };

enum class CutKind { SubsetRow, FleetLowerBound };

enum class ProofQueuePolicy {
    Q0PartialCost,
    QC0CachedPartialCost,
    QD1DeeperFirst,
    QB1OptimisticCompletion,
};

struct PairBranchDecision {
    std::size_t task_a = 0;
    std::size_t task_b = 0;
    bool task_a_exists = false;
    bool task_b_exists = false;
    BranchSense sense = BranchSense::SameJourney;
};

struct CutDefinition {
    std::string id;
    CutKind kind = CutKind::SubsetRow;
    std::vector<std::uint64_t> task_mask;
    std::size_t divisor = 2;
    double dual = 0.0;
    std::uint8_t state_bit_offset = 0;
    std::uint8_t state_bit_width = 0;
    std::uint8_t max_overlap = 0;
};

struct Task {
    std::string id;
    std::size_t index = 0;
    double science_weight = 0.0;
    double demand = 0.0;
    double service_time = 0.0;
    double service_energy = 0.0;
    double service_cost = 0.0;
    double ready_time = 0.0;
    double due_time = 0.0;
    double local_shadow_score = 0.0;
    double local_thermal_risk = 0.0;
    double dual = 0.0;
    double guidance_priority = 0.0;
};

struct ArcData {
    std::string source;
    std::string target;
    std::string path_type;
    double travel_time = 0.0;
    double energy = 0.0;
    double risk = 0.0;
    double distance = 0.0;
    double shadow = 0.0;
    double guidance_priority = 0.0;
};

struct Model {
    std::string instance_id;
    std::string structure_hash;
    std::vector<Task> tasks;
    std::vector<ArcData> arcs;
    std::vector<PairBranchDecision> branch_decisions;
    std::vector<CutDefinition> cuts;
    std::size_t max_tasks_per_trip = 0;
    double capacity = 0.0;
    double energy_limit = 0.0;
    double horizon = 0.0;
    double dock_overhead = 0.0;
    double recharge_power = 1.0;
    double shadow_limit = 0.0;
    double cost_coefficient = 0.0;
    double risk_coefficient = 0.0;
    double completion_coefficient = 0.0;
    double fleet_dual = 0.0;
    double positive_task_dual_sum = 0.0;
    bool completion_bound_enabled = false;
    double completion_bound_threshold = -1.0e-6;
    mutable std::size_t completion_bound_evaluated_labels = 0;
    mutable std::size_t completion_bound_pruned_labels = 0;
    bool subset_dominance_enabled = false;
    bool guidance_task_arc_enabled = false;
};

struct SolveParams {
    bool exact_proof = true;
    std::size_t harvest_target = 16;
    double timeout_seconds = std::numeric_limits<double>::infinity();
    double max_memory_gb = 0.0;
    double negative_epsilon = 1.0e-6;
    double dominance_epsilon = 1.0e-12;
    double resource_epsilon = 1.0e-9;
    std::size_t graph_cache_entries = 1;
    bool completion_bound_enabled = false;
    bool subset_dominance_enabled = false;
    ProofQueuePolicy proof_queue_policy = ProofQueuePolicy::Q0PartialCost;
};

struct SortiePath {
    std::vector<std::string> tasks;
    std::vector<std::string> path_types;
};

struct Route {
    double reduced_cost = std::numeric_limits<double>::infinity();
    std::vector<std::size_t> arc_ids;
    std::vector<SortiePath> sorties;
};

struct BestReducedCostEvent {
    double elapsed_seconds = 0.0;
    std::size_t extended_labels = 0;
    std::size_t solution_count = 0;
    double discovered_reduced_cost = std::numeric_limits<double>::infinity();
    double best_reduced_cost = std::numeric_limits<double>::infinity();
};

struct Telemetry {
    std::size_t extended_labels = 0;
    std::size_t dominated_labels = 0;
    std::size_t dominance_candidate_checks = 0;
    std::size_t max_visited_bucket_size = 0;
    std::size_t solution_count = 0;
    bool memory_pressure_triggered = false;
    bool graph_cache_hit = false;
    std::size_t graph_cache_size = 0;
    std::size_t graph_cache_build_count = 0;
    std::size_t graph_cache_hit_count = 0;
    std::size_t completion_bound_evaluated_labels = 0;
    std::size_t completion_bound_pruned_labels = 0;
    std::size_t subset_dominance_key_lookups = 0;
    std::size_t subset_dominance_nonempty_buckets = 0;
    std::size_t subset_dominance_summary_skipped_buckets = 0;
    std::size_t subset_dominance_candidate_checks = 0;
    std::size_t subset_dominance_rejected_labels = 0;
    double extension_wall_time_seconds = 0.0;
    double dominance_wall_time_seconds = 0.0;
    double wall_time_seconds = 0.0;
    std::vector<BestReducedCostEvent> best_reduced_cost_events;
    std::size_t best_reduced_cost_event_count_total = 0;
    bool best_reduced_cost_events_truncated = false;
};

struct SolveOutput {
    std::string status;
    std::vector<Route> routes;
    bool search_exhaustive = false;
    bool frontier_empty = false;
    bool labels_dropped = false;
    Telemetry telemetry;
};

SolveOutput solve(const Model& model, const SolveParams& params);

std::unordered_map<std::string, std::string> build_info();

}  // namespace lunar_spprc
