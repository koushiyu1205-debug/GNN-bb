#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace lunar_spprc {

namespace detail {

// Production QD1 -> Q0 migration and its native fault-injection tests share
// this exact staging primitive.  The live source is accepted by const
// reference and copied before any pop, so duplicate detection, allocation
// failure, conversion failure, and explicit test injection cannot partially
// drain the active frontier.
template <typename TargetQueue, typename BindingKey>
struct AtomicFrontierMigrationStage {
    TargetQueue target;
    std::vector<std::pair<BindingKey, std::uint64_t>> bindings;
    std::size_t source_size = 0U;
    std::size_t staged_count = 0U;
    std::size_t duplicate_creation_id_count = 0U;
    std::uint64_t creation_hash_before = 0U;
    std::uint64_t creation_hash_after = 0U;
};

template <
    typename SourceQueue,
    typename TargetQueue,
    typename CreationIdFn,
    typename BindingKeyFn,
    typename ConvertFn,
    typename HashFn>
auto stage_atomic_frontier_migration(
    const SourceQueue& live_source,
    TargetQueue empty_target,
    CreationIdFn creation_id_of,
    BindingKeyFn binding_key_of,
    ConvertFn convert,
    HashFn hash,
    std::optional<std::size_t> inject_exception_after = std::nullopt
) {
    using SourceValue = typename SourceQueue::value_type;
    using BindingKey = std::remove_cvref_t<
        std::invoke_result_t<BindingKeyFn, const SourceValue&>>;
    AtomicFrontierMigrationStage<TargetQueue, BindingKey> staged{
        .target = std::move(empty_target),
        .source_size = live_source.size(),
    };
    staged.bindings.reserve(live_source.size());
    std::unordered_set<std::uint64_t> identifiers;
    identifiers.reserve(live_source.size());
    auto source_copy = live_source;
    while (!source_copy.empty()) {
        const auto entry = source_copy.top();
        source_copy.pop();
        const auto creation_id = creation_id_of(entry);
        ++staged.staged_count;
        staged.creation_hash_before ^= hash(creation_id);
        if (!identifiers.insert(creation_id).second) {
            ++staged.duplicate_creation_id_count;
            throw std::runtime_error(
                "atomic frontier staging duplicate creation id");
        }
        staged.target.push(convert(entry));
        staged.bindings.emplace_back(binding_key_of(entry), creation_id);
        staged.creation_hash_after ^= hash(creation_id);
        if (inject_exception_after.has_value() &&
            staged.staged_count == *inject_exception_after) {
            throw std::runtime_error(
                "atomic frontier staging injected exception");
        }
    }
    if (staged.source_size != staged.staged_count ||
        staged.staged_count != staged.target.size() ||
        staged.creation_hash_before != staged.creation_hash_after) {
        throw std::runtime_error(
            "atomic frontier staging conservation redline");
    }
    return staged;
}

}  // namespace detail

enum class ActionKind { VisitTask, ReturnDepot, Terminate };

enum class BranchSense { SameJourney, DifferentJourney };

enum class CutKind { SubsetRow, FleetLowerBound };

enum class ProofQueuePolicy {
    Q0PartialCost,
    QC0CachedPartialCost,
    QD1DeeperFirst,
    QB1OptimisticCompletion,
    QG1GuidancePotential,
    QG2LabelStatePotential,
    QGR1DepthResidualGAT,
};

enum class LabelTraceSamplingMode {
    PrefixV1,
    QGR1StratifiedReservoirV1,
};

enum class FrontierProbeMode {
    Disabled,
    CollectForceQ0,
    ForceQD1,
    Learned,
    CollectTrial,
    ForceTrialContinue,
    ForceTrialRevert,
    LearnedAfterTrial,
};

inline constexpr std::size_t kFrontierNodeCount = 64U;
inline constexpr std::size_t kFrontierNodeFeatureCount = 16U;
inline constexpr std::size_t kFrontierEdgeFeatureCount = 10U;
inline constexpr std::size_t kFrontierContextFeatureCount = 28U;
inline constexpr std::size_t kFrontierHiddenSize = 16U;
inline constexpr std::size_t kFrontierHeadCount = 2U;

enum class CounterfactualPrefixMode {
    Disabled,
    Q0Prefix,
    QD1Prefix,
};

inline constexpr std::size_t kCounterfactualPrefixCheckpointCount = 3U;
inline constexpr std::size_t kCounterfactualLabelSampleCap = 256U;
inline constexpr std::size_t kCounterfactualLabelNodeFeatureCount = 24U;
inline constexpr std::size_t kCounterfactualLabelEdgeFeatureCount = 8U;
inline constexpr std::size_t kCounterfactualPortableNodeFeatureCount = 40U;
inline constexpr std::size_t kCounterfactualPortableEdgeFeatureCount = 10U;
inline constexpr std::size_t kCounterfactualCounterFeatureCount = 24U;
inline constexpr std::size_t kTemporalGatNodeFeatureCount = 40U;
inline constexpr std::size_t kTemporalGatEdgeFeatureCount = 11U;
inline constexpr std::size_t kTemporalGatCounterFeatureCount = 24U;
inline constexpr std::size_t kTemporalGatHiddenSize = 32U;
inline constexpr std::size_t kTemporalGatHeadCount = 4U;

struct CounterfactualPrefixConfig {
    CounterfactualPrefixMode mode = CounterfactualPrefixMode::Disabled;
    std::size_t processed_label_boundary = 4096U;
    std::array<std::size_t, kCounterfactualPrefixCheckpointCount>
        rollout_checkpoints{128U, 512U, 2048U};
    // Representation collection keeps all three checkpoints in one request.
    // Frozen runtime bundles stop at their selected budget so the auxiliary
    // wall is not silently charged as a 2048-pop rollout for B=128/512.
    std::size_t maximum_rollout_budget = 2048U;
    std::size_t label_sample_cap = kCounterfactualLabelSampleCap;
    std::uint64_t sampling_seed = 0;
    std::array<double, kFrontierContextFeatureCount> context_features{};
    bool telemetry_only = true;
    bool public_routes_forbidden = true;
    bool certificate_forbidden = true;
};

struct CounterfactualLabelNode {
    std::uint64_t creation_sequence_id = 0;
    std::uint64_t parent_creation_sequence_id =
        std::numeric_limits<std::uint64_t>::max();
    std::size_t last_task_index = std::numeric_limits<std::size_t>::max();
    std::size_t depth_rc_cell = 0U;
    std::uint64_t dominance_surface_hash = 0;
    std::array<double, kCounterfactualLabelNodeFeatureCount> features{};
};

struct CounterfactualLabelEdge {
    std::size_t source = 0;
    std::size_t target = 0;
    std::array<double, kCounterfactualLabelEdgeFeatureCount> features{};
};

struct CounterfactualFrontierGraph {
    std::string schema_version =
        "lunar_ice_bpc.p0v5_frontier_label_sample_graph.v1";
    std::string graph_hash;
    std::size_t frontier_size = 0;
    std::size_t sampled_label_count = 0;
    std::size_t terminal_family_count = 0;
    std::size_t q0_family_count = 0;
    std::size_t qd1_family_count = 0;
    std::size_t deepest_family_count = 0;
    std::size_t depth_rc_family_count = 0;
    std::size_t bottom_k_family_count = 0;
    std::vector<CounterfactualLabelNode> label_nodes;
    std::vector<CounterfactualLabelEdge> label_edges;
    std::array<double, kFrontierContextFeatureCount> context_features{};
    double build_wall_seconds = 0.0;
};

struct CounterfactualPrefixEndpoint {
    std::size_t rollout_budget = 0;
    std::size_t processed_labels = 0;
    std::size_t extended_labels = 0;
    std::size_t dominated_labels = 0;
    std::size_t dominance_candidate_checks = 0;
    std::size_t subset_dominance_candidate_checks = 0;
    std::size_t subset_dominance_rejected_labels = 0;
    std::size_t frontier_size = 0;
    std::size_t max_visited_bucket_size = 0;
    std::size_t negative_label_event_count = 0;
    double best_true_reduced_cost = std::numeric_limits<double>::infinity();
    std::size_t base_label_survival_count = 0;
    std::size_t new_label_count = 0;
    double frontier_churn = 0.0;
    double request_elapsed_wall_seconds = 0.0;
    double rollout_elapsed_wall_seconds = 0.0;
    double graph_build_wall_seconds = 0.0;
    CounterfactualFrontierGraph graph;
};

struct CounterfactualPrefixTelemetry {
    bool enabled = false;
    bool reached_boundary = false;
    bool complete = false;
    bool truncated_diagnostic = false;
    bool exact = false;
    bool public_routes_forbidden = true;
    bool certificate_forbidden = true;
    bool routes_suppressed = true;
    bool certificate_suppressed = true;
    bool switched_to_qd1 = false;
    std::string mode = "disabled";
    std::string stop_reason = "prefix_disabled";
    std::size_t processed_label_boundary = 0;
    std::array<std::size_t, kCounterfactualPrefixCheckpointCount>
        rollout_checkpoints{};
    std::size_t maximum_rollout_budget = 0;
    std::string base_graph_hash;
    std::size_t base_processed_labels = 0;
    std::size_t base_extended_labels = 0;
    std::size_t base_dominated_labels = 0;
    std::size_t base_dominance_candidate_checks = 0;
    std::size_t base_subset_dominance_candidate_checks = 0;
    std::size_t base_subset_dominance_rejected_labels = 0;
    std::size_t base_max_visited_bucket_size = 0;
    std::size_t base_negative_label_event_count = 0;
    double base_best_true_reduced_cost =
        std::numeric_limits<double>::infinity();
    double base_request_elapsed_wall_seconds = 0.0;
    double base_graph_build_wall_seconds = 0.0;
    double migration_wall_seconds = 0.0;
    double request_elapsed_wall_seconds = 0.0;
    CounterfactualFrontierGraph base_graph;
    std::vector<CounterfactualPrefixEndpoint> endpoints;
};

struct FrontierDenseTensor {
    std::vector<std::size_t> shape;
    std::vector<double> values;
};

struct FrontierGatSeedModel {
    std::uint64_t seed = 0;
    std::unordered_map<std::string, FrontierDenseTensor> tensors;
};

struct FrontierProbabilityCalibration {
    bool constant = false;
    double probability = 0.5;
    double a = 1.0;
    double b = 0.0;
};

struct TemporalNormalizationGroup {
    std::vector<double> mean;
    std::vector<double> scale;
    std::vector<double> minimum;
    std::vector<double> maximum;
};

struct TemporalGraphEdge {
    std::size_t source = 0;
    std::size_t target = 0;
    std::array<double, kTemporalGatEdgeFeatureCount> features{};
};

struct TemporalPortableGraph {
    std::vector<std::array<double, kTemporalGatNodeFeatureCount>> node_features;
    std::vector<TemporalGraphEdge> edges;
    // UINT64_MAX identifies a static task node.  Label nodes retain the
    // request-local monotone creation ID so t0/tK survival is auditable.
    std::vector<std::uint64_t> creation_sequence_ids;
    std::array<double, kFrontierContextFeatureCount> context_features{};
    std::string graph_hash;
};

struct TemporalGatBundle {
    std::string controller_kind = "temporal_gat";
    std::string schema_version;
    std::string graph_schema_version;
    std::string feature_schema_version;
    std::string bundle_sha256;
    std::vector<std::string> cell_node_feature_names;
    std::vector<std::string> cell_edge_feature_names;
    std::vector<std::string> node_feature_names;
    std::vector<std::string> edge_feature_names;
    std::vector<std::string> counter_feature_names;
    std::vector<std::string> context_feature_names;
    TemporalNormalizationGroup cell_node;
    TemporalNormalizationGroup cell_edge;
    TemporalNormalizationGroup node;
    TemporalNormalizationGroup edge;
    TemporalNormalizationGroup counter;
    TemporalNormalizationGroup context;
    std::vector<FrontierGatSeedModel> models;
    FrontierProbabilityCalibration benefit_calibration;
    FrontierProbabilityCalibration adverse_calibration;
    double gain_scale = 1.0;
    double minimum_benefit_probability = 1.0;
    double maximum_adverse_probability = 0.0;
    double minimum_expected_gain = 1.0;
    double adverse_penalty = 1.0;
    double maximum_disagreement = 0.0;
    double layer_norm_epsilon = 1.0e-5;
    std::size_t selected_scale = 0U;
};

struct TemporalGatDecision {
    bool continue_qd1 = false;
    double p_benefit = 0.0;
    double positive_gain = 0.0;
    double p_adverse = 1.0;
    double expected_gain = 0.0;
    double risk_score = -1.0;
    double disagreement = 0.0;
};

struct FrontierGatBundle {
    std::string schema_version;
    std::string graph_schema_version;
    std::string feature_schema_version;
    std::string bundle_sha256;
    std::vector<std::string> node_feature_names;
    std::vector<std::string> edge_feature_names;
    std::vector<std::string> context_feature_names;
    std::vector<double> node_mean;
    std::vector<double> node_scale;
    std::vector<double> node_min;
    std::vector<double> node_max;
    std::vector<double> edge_mean;
    std::vector<double> edge_scale;
    std::vector<double> edge_min;
    std::vector<double> edge_max;
    std::vector<double> context_mean;
    std::vector<double> context_scale;
    std::vector<double> context_min;
    std::vector<double> context_max;
    std::vector<FrontierGatSeedModel> models;
    FrontierProbabilityCalibration benefit_calibration;
    FrontierProbabilityCalibration adverse_calibration;
    double gain_scale = 1.0;
    double minimum_benefit_probability = 1.0;
    double maximum_adverse_probability = 0.0;
    double minimum_expected_gain = 1.0;
    double adverse_penalty = 1.0;
    double maximum_disagreement = 0.0;
    double layer_norm_epsilon = 1.0e-5;
};

struct FrontierProbeConfig {
    FrontierProbeMode mode = FrontierProbeMode::Disabled;
    std::size_t processed_label_boundary = 4096U;
    std::size_t trial_pop_budget = 0U;
    std::size_t problem_scale = 0U;
    std::string pricing_lifecycle = "unbound";
    bool require_root_cg = true;
    bool fail_closed_on_ood = true;
    // External immutable artifact bindings are distinct from the bundle's
    // canonical internal payload hash.  Learned production mode requires all
    // three; forced/collection modes remain usable for outcome generation.
    std::string manifest_sha256;
    std::string bundle_file_sha256;
    std::vector<std::size_t> observation_boundaries;
    std::array<double, kFrontierContextFeatureCount> context_features{};
    FrontierGatBundle bundle;
    TemporalGatBundle temporal_bundle;
};

struct FrontierGraphEdge {
    std::size_t source = 0;
    std::size_t target = 0;
    std::array<double, kFrontierEdgeFeatureCount> features{};
};

struct FrontierProbeSnapshot {
    bool reached = false;
    bool graph_built = false;
    std::size_t boundary = 0;
    std::size_t processed_labels = 0;
    std::size_t extended_labels = 0;
    std::size_t dominated_labels = 0;
    std::size_t dominance_candidate_checks = 0;
    std::size_t subset_dominance_candidate_checks = 0;
    std::size_t subset_dominance_rejected_labels = 0;
    std::size_t max_visited_bucket_size = 0;
    std::size_t negative_label_event_count = 0;
    double best_true_reduced_cost =
        std::numeric_limits<double>::infinity();
    std::string graph_hash;
    std::size_t frontier_size = 0;
    std::size_t nonempty_node_count = 0;
    std::size_t edge_count = 0;
    double graph_build_wall_seconds = 0.0;
    std::vector<std::array<double, kFrontierNodeFeatureCount>> node_features;
    std::vector<FrontierGraphEdge> edges;
    std::array<double, kFrontierContextFeatureCount> context_features{};
};

struct FrontierProbeTelemetry {
    bool enabled = false;
    bool reached = false;
    bool graph_built = false;
    bool model_called = false;
    bool switched_to_qd1 = false;
    bool trial_started = false;
    bool trial_completed = false;
    bool migrated_back_to_q0 = false;
    bool inference_ood = false;
    bool fail_closed = false;
    std::string mode = "disabled";
    std::string action = "CONTINUE_Q0";
    std::string decision_reason = "probe_disabled";
    std::string graph_hash;
    std::size_t boundary = 0;
    std::size_t trial_pop_budget = 0;
    std::size_t trial_pops = 0;
    std::size_t frontier_size = 0;
    std::size_t nonempty_node_count = 0;
    std::size_t edge_count = 0;
    std::size_t frontier_before_migration = 0;
    std::size_t drained_count = 0;
    std::size_t migrated_count = 0;
    std::size_t duplicate_count = 0;
    std::uint64_t creation_hash_before = 0;
    std::uint64_t creation_hash_after = 0;
    std::size_t reverse_frontier_before_migration = 0;
    std::size_t reverse_staged_count = 0;
    std::size_t reverse_migrated_count = 0;
    std::size_t reverse_duplicate_count = 0;
    std::uint64_t reverse_creation_hash_before = 0;
    std::uint64_t reverse_creation_hash_after = 0;
    std::size_t q0_post_probe_pops = 0;
    std::size_t qd1_post_probe_pops = 0;
    double graph_build_wall_seconds = 0.0;
    double temporal_graph_build_wall_seconds = 0.0;
    double inference_wall_seconds = 0.0;
    double migration_wall_seconds = 0.0;
    double reverse_migration_wall_seconds = 0.0;
    double trial_wall_seconds = 0.0;
    double p_benefit = 0.0;
    double positive_gain = 0.0;
    double p_adverse = 1.0;
    double expected_gain = 0.0;
    double risk_score = -1.0;
    double disagreement = 1.0;
    std::string ood_reason;
    std::vector<std::array<double, 3>> seed_outputs;
    std::vector<std::array<double, kFrontierNodeFeatureCount>> node_features;
    std::vector<FrontierGraphEdge> edges;
    std::array<double, kFrontierContextFeatureCount> context_features{};
    std::vector<std::size_t> observation_boundaries;
    std::vector<FrontierProbeSnapshot> snapshots;
    FrontierProbeSnapshot trial_start_snapshot;
    FrontierProbeSnapshot trial_end_snapshot;
    CounterfactualFrontierGraph trial_start_label_graph;
    CounterfactualFrontierGraph trial_end_label_graph;
    TemporalPortableGraph trial_start_temporal_graph;
    TemporalPortableGraph trial_end_temporal_graph;
    std::size_t temporal_surviving_label_count = 0;
    std::size_t temporal_new_label_count = 0;
    std::size_t temporal_extended_label_delta = 0;
    std::size_t temporal_dominated_label_delta = 0;
    double temporal_survival_fraction = 0.0;
    double temporal_frontier_churn = 0.0;
    std::size_t temporal_cell_edge_count = 0;
    std::size_t temporal_label_edge_count = 0;
    // (edge type, t0 identity, tK identity): type 0 is the fixed cell
    // alignment and type 1 is a surviving label creation ID.
    std::vector<std::array<std::uint64_t, 3>> temporal_edges;
    std::string temporal_edge_hash;
    std::array<double, kTemporalGatCounterFeatureCount>
        temporal_counter_features{};
    std::string temporal_counter_hash;
};

struct CounterfactualPortableGraph {
    std::vector<std::vector<double>> node_features;
    std::vector<FrontierGraphEdge> edges;
    std::array<double, kFrontierContextFeatureCount> context_features{};
};

struct CounterfactualPortableTriplet {
    CounterfactualPortableGraph base;
    CounterfactualPortableGraph q0;
    CounterfactualPortableGraph qd1;
    std::array<double, kCounterfactualCounterFeatureCount> counter_features{};
};

struct CounterfactualPortableBundle {
    std::string schema_version;
    std::vector<double> node_mean;
    std::vector<double> node_scale;
    std::vector<double> edge_mean;
    std::vector<double> edge_scale;
    std::vector<double> context_mean;
    std::vector<double> context_scale;
    std::vector<double> counter_mean;
    std::vector<double> counter_scale;
    std::vector<FrontierGatSeedModel> models;
    double layer_norm_epsilon = 1.0e-5;
};

inline constexpr std::size_t kLabelStateFeatureCount = 15U;

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
    double absolute_dual_sum = 1.0;
    bool completion_bound_enabled = false;
    double completion_bound_threshold = -1.0e-6;
    mutable std::size_t completion_bound_evaluated_labels = 0;
    mutable std::size_t completion_bound_pruned_labels = 0;
    bool subset_dominance_enabled = false;
    bool guidance_task_arc_enabled = false;
    bool guidance_label_state_enabled = false;
    std::array<double, kLabelStateFeatureCount>
        guidance_label_state_coefficients{};
    bool dssr_relaxation_enabled = false;
    std::vector<std::uint64_t> dssr_critical_task_mask;
    std::vector<std::uint64_t> dssr_branch_task_mask;
    bool ng_dssr_memory_enabled = false;
    std::vector<std::vector<std::uint64_t>> ng_dssr_task_memory_masks;
};

struct SolveParams {
    bool exact_proof = true;
    std::size_t harvest_target = 16;
    bool exact_negative_escape_enabled = false;
    std::size_t exact_admission_batch_size = 16;
    std::size_t exact_raw_negative_pool_size = 64;
    std::string exact_negative_escape_policy_id =
        "diverse_raw_4x_then_p0v4_selector_v1";
    std::size_t harvest_max_processed_labels = 0;
    double timeout_seconds = std::numeric_limits<double>::infinity();
    double max_memory_gb = 0.0;
    double negative_epsilon = 1.0e-6;
    double dominance_epsilon = 1.0e-12;
    double resource_epsilon = 1.0e-9;
    std::size_t graph_cache_entries = 1;
    bool completion_bound_enabled = false;
    bool subset_dominance_enabled = false;
    bool proof_queue_potential_trace_enabled = false;
    bool proof_queue_label_trace_enabled = false;
    std::size_t proof_queue_label_trace_max_rows = 50000;
    LabelTraceSamplingMode proof_queue_label_trace_sampling_mode =
        LabelTraceSamplingMode::PrefixV1;
    std::uint64_t proof_queue_label_trace_seed = 0;
    std::size_t proof_queue_preference_cap_per_family = 12500;
    std::size_t proof_queue_surface_reservoir_count = 3125;
    std::size_t proof_queue_surface_labels_per_bucket = 8;
    std::size_t proof_queue_witness_route_cap = 512;
    std::size_t proof_queue_witness_ancestor_cap = 25000;
    double proof_queue_guidance_bucket_width = 0.01;
    bool dssr_enabled = false;
    std::string dssr_policy_version =
        "multi_sortie_counterexample_refinement_v1";
    std::size_t dssr_negative_batch_target = 16;
    bool dssr_pressure_refinement_enabled = false;
    std::size_t dssr_pressure_max_bucket_size = 8192;
    std::size_t dssr_pressure_max_candidate_checks = 200000000;
    std::size_t ng_dssr_initial_neighborhood_size = 10;
    ProofQueuePolicy proof_queue_policy = ProofQueuePolicy::Q0PartialCost;
    FrontierProbeConfig frontier_probe;
    CounterfactualPrefixConfig counterfactual_prefix;
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

struct TaskDominanceTraceRow {
    std::size_t task_index = 0;
    std::uint64_t incoming_evaluated = 0;
    std::uint64_t incoming_rejected = 0;
    std::uint64_t existing_dominator_wins = 0;
    std::uint64_t accepted_removed_existing = 0;
    std::uint64_t removed_as_existing = 0;
};

struct LabelStateTraceRow {
    std::uint64_t label_id = 0;
    std::uint64_t parent_label_id = std::numeric_limits<std::uint64_t>::max();
    std::uint64_t current_node_id = 0;
    std::uint64_t last_task_index = std::numeric_limits<std::uint64_t>::max();
    std::uint64_t last_model_arc_index = std::numeric_limits<std::uint64_t>::max();
    std::size_t visited_count = 0;
    std::int64_t reduced_cost_bucket = 0;
    double partial_reduced_cost = 0.0;
    double label_state_priority = 0.0;
    bool can_terminate = false;
    std::array<double, kLabelStateFeatureCount> features{};
};

enum class LabelPreferenceKind {
    ExistingDominator,
    IncomingDominator,
};

struct LabelPreferenceTraceRow {
    std::uint64_t winner_label_id = 0;
    std::uint64_t loser_label_id = 0;
    LabelPreferenceKind kind = LabelPreferenceKind::ExistingDominator;
};

struct NegativeWitnessTraceRow {
    std::size_t solution_index = 0;
    double reduced_cost = std::numeric_limits<double>::infinity();
    double elapsed_seconds = 0.0;
    std::vector<std::uint64_t> ancestor_label_ids;
};

struct DssrIterationTraceRow {
    std::size_t iteration = 0;
    std::size_t critical_task_count_before = 0;
    std::size_t repeated_task_count = 0;
    std::size_t processed_labels = 0;
    std::size_t extended_labels = 0;
    std::size_t dominated_labels = 0;
    std::size_t max_visited_bucket_size = 0;
    double wall_time_seconds = 0.0;
    std::string status;
    bool search_exhaustive = false;
    bool frontier_empty = false;
    bool labels_dropped = false;
    bool negative_witness_found = false;
    bool witness_elementary = false;
    std::size_t raw_solution_count = 0;
    std::size_t elementary_solution_count = 0;
    std::size_t non_elementary_solution_count = 0;
    bool pressure_refinement_triggered = false;
    std::string pressure_split_task_id;
    std::size_t ng_relation_count_before = 0;
    std::size_t ng_relation_add_count = 0;
    std::size_t ng_forbidden_cycle_count = 0;
};

struct Telemetry {
    std::size_t processed_labels = 0;
    std::size_t extended_labels = 0;
    std::size_t dominated_labels = 0;
    std::size_t dominance_candidate_checks = 0;
    std::size_t max_visited_bucket_size = 0;
    std::size_t solution_count = 0;
    bool negative_escape_enabled = false;
    bool negative_escape_triggered = false;
    std::size_t exact_admission_batch_size = 0;
    std::size_t exact_raw_negative_pool_size = 0;
    std::size_t raw_unique_negative_count = 0;
    std::string negative_escape_policy_id;
    std::string negative_escape_termination_reason;
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
    bool proof_queue_potential_trace_enabled = false;
    std::vector<TaskDominanceTraceRow> proof_queue_potential_trace;
    std::vector<TaskDominanceTraceRow> proof_queue_arc_potential_trace;
    bool proof_queue_label_trace_enabled = false;
    bool proof_queue_label_trace_truncated = false;
    bool proof_queue_label_trace_incomplete = false;
    std::string proof_queue_label_trace_sampling_mode;
    std::uint64_t proof_queue_label_trace_seed = 0;
    std::size_t proof_queue_existing_preference_seen = 0;
    std::size_t proof_queue_existing_preference_retained = 0;
    std::size_t proof_queue_incoming_preference_seen = 0;
    std::size_t proof_queue_incoming_preference_retained = 0;
    std::size_t proof_queue_surface_seen = 0;
    std::size_t proof_queue_surface_retained = 0;
    std::size_t proof_queue_surface_label_retained = 0;
    std::size_t proof_queue_witness_seen = 0;
    std::size_t proof_queue_witness_retained = 0;
    std::size_t proof_queue_witness_ancestor_retained = 0;
    std::size_t proof_queue_label_trace_final_rows = 0;
    std::vector<LabelStateTraceRow> proof_queue_label_state_trace;
    std::vector<LabelPreferenceTraceRow> proof_queue_label_preference_trace;
    std::vector<NegativeWitnessTraceRow> proof_queue_negative_witness_trace;
    std::size_t proof_queue_label_state_scored_count = 0;
    std::size_t proof_queue_guidance_nonzero_score_count = 0;
    std::size_t proof_queue_guidance_ordering_decision_count = 0;
    std::size_t proof_queue_guidance_reordered_label_hash_count = 0;
    std::size_t proof_queue_guidance_bucket_hash_count = 0;
    double proof_queue_label_state_scoring_estimated_wall_seconds = 0.0;
    double first_true_negative_wall_time_seconds =
        std::numeric_limits<double>::infinity();
    std::size_t labels_processed_before_first_true_negative = 0;
    bool dssr_enabled = false;
    std::string dssr_policy_version;
    std::size_t dssr_iteration_count = 0;
    std::size_t dssr_refinement_count = 0;
    std::size_t dssr_initial_critical_task_count = 0;
    std::size_t dssr_final_critical_task_count = 0;
    std::size_t dssr_repeated_witness_count = 0;
    bool dssr_elementary_witness_returned = false;
    bool dssr_relaxation_no_negative_certificate = false;
    std::size_t dssr_elementary_batch_count = 0;
    std::size_t dssr_raw_solution_count = 0;
    std::size_t dssr_pressure_refinement_count = 0;
    std::vector<std::string> dssr_pressure_split_task_ids;
    std::size_t dssr_pressure_abandoned_iteration_count = 0;
    std::size_t dssr_max_bucket_size = 0;
    std::size_t dssr_dominance_candidate_checks = 0;
    bool dssr_pressure_triggered = false;
    std::string dssr_pressure_split_task_id;
    bool ng_dssr_enabled = false;
    std::size_t ng_dssr_initial_neighborhood_size = 0;
    std::size_t ng_dssr_initial_relation_count = 0;
    std::size_t ng_dssr_final_relation_count = 0;
    std::size_t ng_dssr_relation_add_count = 0;
    std::size_t ng_dssr_forbidden_cycle_count = 0;
    std::size_t ng_dssr_full_elementary_fallback_count = 0;
    std::vector<DssrIterationTraceRow> dssr_iteration_trace;
    FrontierProbeTelemetry frontier_probe;
    CounterfactualPrefixTelemetry counterfactual_prefix;
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

std::array<double, 3> evaluate_frontier_gat_seed(
    const FrontierGatSeedModel& model,
    const FrontierGatBundle& bundle,
    const FrontierProbeTelemetry& graph
);

std::array<double, 3> evaluate_counterfactual_gat_seed(
    const FrontierGatSeedModel& model,
    const CounterfactualPortableBundle& bundle,
    const CounterfactualPortableTriplet& triplet
);

std::array<double, 3> evaluate_temporal_gat_seed(
    const FrontierGatSeedModel& model,
    const TemporalGatBundle& bundle,
    const FrontierProbeSnapshot& cell_t0,
    const FrontierProbeSnapshot& cell_tk,
    const TemporalPortableGraph& graph_t0,
    const TemporalPortableGraph& graph_tk,
    const std::array<double, kTemporalGatCounterFeatureCount>& counters,
    const std::array<double, kFrontierContextFeatureCount>& context,
    std::size_t scale
);

TemporalGatDecision decide_temporal_gat_outputs(
    const TemporalGatBundle& bundle,
    const std::vector<std::array<double, 3>>& outputs
);

std::unordered_map<std::string, std::string> build_info();

}  // namespace lunar_spprc
