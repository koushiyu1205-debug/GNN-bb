#include "lunar_spprc/native_pricer.hpp"
#if LUNAR_SPPRC_ENABLE_BIDIRECTIONAL_FEASIBILITY
#include "lunar_spprc/bidirectional_feasibility.hpp"
#endif

#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string>
#include <vector>

#include "rcspp/rcspp.hpp"

namespace {

lunar_spprc::Model model() {
    lunar_spprc::Model value;
    value.instance_id = "native_test";
    value.structure_hash = "native_test_structure_v1";
    value.max_tasks_per_trip = 1;
    value.capacity = 10.0;
    value.energy_limit = 100.0;
    value.horizon = 100.0;
    value.dock_overhead = 1.0;
    value.recharge_power = 10.0;
    value.shadow_limit = 100.0;
    value.cost_coefficient = 1.0;
    value.risk_coefficient = 1.0;
    value.completion_coefficient = 0.1;
    value.tasks = {
        {.id = "a", .index = 0, .science_weight = 1.0, .demand = 1.0,
         .service_time = 1.0, .service_energy = 1.0, .service_cost = 1.0,
         .ready_time = 0.0, .due_time = 80.0, .dual = 20.0},
        {.id = "b", .index = 1, .science_weight = 1.0, .demand = 1.0,
         .service_time = 1.0, .service_energy = 1.0, .service_cost = 1.0,
         .ready_time = 0.0, .due_time = 80.0, .dual = 20.0},
    };
    const std::vector<std::string> nodes{"depot", "a", "b"};
    for (const auto& source : nodes) {
        for (const auto& target : nodes) {
            if (source == target || target == "depot" && source == "depot") {
                continue;
            }
            value.arcs.push_back({.source = source,
                                  .target = target,
                                  .path_type = "low_time",
                                  .travel_time = 1.0,
                                  .energy = 1.0,
                                  .risk = 0.1,
                                  .distance = 1.0,
                                  .shadow = 0.1});
        }
    }
    return value;
}

void verify_upstream_pressure_false_complete_reproduction() {
    using namespace rcspp;
    auto make_graph = [] {
        auto graph = std::make_unique<ResourceGraph<RealResource, IntResource>>();
        graph->add_resource<RealResource>(
            std::make_unique<AdditionExtensionFunction<RealResource>>(),
            std::make_unique<TrivialFeasibilityFunction<RealResource>>(),
            std::make_unique<ValueCostFunction<RealResource>>(),
            std::make_unique<ValueDominanceFunction<RealResource>>());
        graph->add_resource<IntResource>(
            std::make_unique<AdditionExtensionFunction<IntResource>>(),
            std::make_unique<MinMaxFeasibilityFunction<IntResource>>(0, 10),
            std::make_unique<TrivialCostFunction<IntResource>>(),
            std::make_unique<ValueDominanceFunction<IntResource>>());
        graph->add_node(0, true, false);
        graph->add_node(1, false, false);
        graph->add_node(2, false, true);
        for (int cost = 0; cost < 10; ++cost) {
            graph->add_arc<RealResource, IntResource>(
                {std::make_tuple(static_cast<double>(cost)), std::make_tuple(10 - cost)}, 0, 1);
        }
        graph->add_arc<RealResource, IntResource>({std::make_tuple(0.0), std::make_tuple(3)}, 1, 2);
        return graph;
    };

    AlgorithmBaseParams reference_params;
    const auto reference = make_graph()->solve<SimpleDominanceAlgorithm>(
        reference_params, std::numeric_limits<double>::infinity(), false, 0);
    assert(reference.status == AlgorithmStatus::COMPLETE);
    assert(!reference.solutions.empty());
    assert(reference.solutions.front().cost == 3.0);

    AlgorithmBaseParams pressure_params;
    pressure_params.max_memory_gb = 1e9;
    pressure_params.memory_pressure_fraction = 0.0;
    pressure_params.memory_check_interval = 1;
    pressure_params.memory_pressure_max_labels_per_node = 1;
    pressure_params.release_after_solve = true;
    const auto pressure = make_graph()->solve<SimpleDominanceAlgorithm>(
        pressure_params, std::numeric_limits<double>::infinity(), false, 0);
    // Pinned upstream reports COMPLETE after pressure trimming released the only feasible
    // non-dominated labels. The project exact wrapper therefore disables pressure trimming
    // and treats any observed pressure event as a certificate blocker.
    assert(pressure.status == AlgorithmStatus::COMPLETE);
    assert(pressure.solutions.empty());
}

void verify_task_waiting_is_forbidden_but_depot_departure_may_shift() {
    auto value = model();
    value.structure_hash = "native_no_task_wait_structure_v1";
    value.max_tasks_per_trip = 2;
    value.tasks[0].service_time = 5.0;
    value.tasks[0].ready_time = 20.0;
    value.tasks[0].due_time = 30.0;
    value.tasks[0].dual = 100.0;
    value.tasks[1].service_time = 5.0;
    value.tasks[1].ready_time = 50.0;
    value.tasks[1].due_time = 60.0;
    value.tasks[1].dual = 100.0;
    for (auto& arc : value.arcs) {
        arc.travel_time = 50.0;
        if (arc.source == "depot" && arc.target == "a") {
            arc.travel_time = 10.0;
        } else if (arc.source == "a" && arc.target == "b") {
            arc.travel_time = 5.0;
        } else if (arc.source == "b" && arc.target == "depot") {
            arc.travel_time = 10.0;
        }
    }
    value.branch_decisions.push_back({
        .task_a = 0,
        .task_b = 1,
        .task_a_exists = true,
        .task_b_exists = true,
        .sense = lunar_spprc::BranchSense::SameJourney,
    });
    lunar_spprc::SolveParams params;
    params.exact_proof = true;
    const auto result = lunar_spprc::solve(value, params);
    assert(result.status == "complete");
    assert(result.search_exhaustive);
    assert(result.routes.empty());
}

void verify_qg2_reorders_only_within_rc_buckets() {
    auto value = model();
    lunar_spprc::SolveParams q0_params;
    q0_params.exact_proof = true;
    q0_params.negative_epsilon = 1.0e-6;
    const auto q0 = lunar_spprc::solve(value, q0_params);

    value.guidance_task_arc_enabled = true;
    value.guidance_label_state_enabled = true;
    value.tasks[0].guidance_priority = 0.75;
    value.tasks[1].guidance_priority = -0.25;
    for (std::size_t index = 0; index < value.arcs.size(); ++index) {
        value.arcs[index].guidance_priority =
            static_cast<double>(index % 3U) * 0.1;
    }
    value.guidance_label_state_coefficients = {
        0.2, -0.1, 0.05, 0.0, 0.4,
        -0.2, 0.1, 0.1, -0.1, 0.05,
        0.2, -0.2, 0.1, -0.1, 0.25,
    };
    auto qg2_params = q0_params;
    qg2_params.proof_queue_policy =
        lunar_spprc::ProofQueuePolicy::QG2LabelStatePotential;
    qg2_params.proof_queue_guidance_bucket_width = 1.0e-3;
    qg2_params.proof_queue_label_trace_enabled = true;
    qg2_params.proof_queue_label_trace_max_rows = 50'000;
    const auto qg2 = lunar_spprc::solve(value, qg2_params);

    assert(qg2.status == q0.status);
    assert(qg2.search_exhaustive == q0.search_exhaustive);
    assert(qg2.frontier_empty == q0.frontier_empty);
    assert(qg2.labels_dropped == q0.labels_dropped);
    assert(qg2.routes.size() == q0.routes.size());
    std::vector<double> q0_costs;
    std::vector<double> qg2_costs;
    for (const auto& route : q0.routes) {
        q0_costs.push_back(route.reduced_cost);
    }
    for (const auto& route : qg2.routes) {
        qg2_costs.push_back(route.reduced_cost);
    }
    std::ranges::sort(q0_costs);
    std::ranges::sort(qg2_costs);
    assert(q0_costs == qg2_costs);
    assert(qg2.telemetry.proof_queue_label_trace_enabled);
    assert(!qg2.telemetry.proof_queue_label_state_trace.empty());
    assert(qg2.telemetry.proof_queue_label_state_scored_count > 0U);
    assert(qg2.telemetry.proof_queue_guidance_nonzero_score_count > 0U);
    // A legal guidance score need not change the stable order when every
    // encountered tie already agrees with it.  Debug/sanitizer allocation
    // order exposes that valid zero-reorder path; the exact-safe invariant is
    // that any reported reorder is drawn from scored labels in an RC bucket.
    assert(
        qg2.telemetry.proof_queue_guidance_reordered_label_hash_count <=
        qg2.telemetry.proof_queue_label_state_scored_count);
    assert(
        qg2.telemetry.proof_queue_guidance_bucket_hash_count > 0U);
    assert(
        std::isfinite(
            qg2.telemetry.first_true_negative_wall_time_seconds));
    assert(!qg2.telemetry.proof_queue_negative_witness_trace.empty());
    for (const auto& witness :
         qg2.telemetry.proof_queue_negative_witness_trace) {
        assert(std::isfinite(witness.elapsed_seconds));
        assert(witness.elapsed_seconds >= 0.0);
    }

    auto no_negative = value;
    for (auto& task : no_negative.tasks) {
        task.dual = 0.0;
        task.guidance_priority = 0.0;
    }
    for (auto& arc : no_negative.arcs) {
        arc.guidance_priority = 0.0;
    }
    no_negative.guidance_label_state_coefficients.fill(0.0);
    const auto qg2_closure = lunar_spprc::solve(
        no_negative, qg2_params);
    assert(qg2_closure.status == "complete");
    assert(qg2_closure.search_exhaustive);
    assert(qg2_closure.frontier_empty);
    assert(qg2_closure.routes.empty());
    assert(
        !std::isfinite(
            qg2_closure.telemetry.first_true_negative_wall_time_seconds));
}

void verify_qgr1_is_a_depth_residual_and_zero_score_matches_qd1() {
    auto value = model();
    for (auto& task : value.tasks) {
        task.guidance_priority = 0.0;
    }
    for (auto& arc : value.arcs) {
        arc.guidance_priority = 0.0;
    }
    value.guidance_task_arc_enabled = false;
    value.guidance_label_state_enabled = false;
    value.guidance_label_state_coefficients.fill(0.0);

    lunar_spprc::SolveParams qd1_params;
    qd1_params.exact_proof = true;
    qd1_params.proof_queue_policy =
        lunar_spprc::ProofQueuePolicy::QD1DeeperFirst;
    const auto qd1 = lunar_spprc::solve(value, qd1_params);

    value.guidance_task_arc_enabled = true;
    value.guidance_label_state_enabled = true;
    auto qgr1_params = qd1_params;
    qgr1_params.proof_queue_policy =
        lunar_spprc::ProofQueuePolicy::QGR1DepthResidualGAT;
    qgr1_params.proof_queue_guidance_bucket_width = 1.0e-4;
    const auto qgr1_zero = lunar_spprc::solve(value, qgr1_params);

    assert(qgr1_zero.status == qd1.status);
    assert(qgr1_zero.search_exhaustive == qd1.search_exhaustive);
    assert(qgr1_zero.frontier_empty == qd1.frontier_empty);
    assert(qgr1_zero.labels_dropped == qd1.labels_dropped);
    assert(
        qgr1_zero.telemetry.processed_labels ==
        qd1.telemetry.processed_labels);
    assert(
        qgr1_zero.telemetry.extended_labels ==
        qd1.telemetry.extended_labels);
    assert(
        qgr1_zero.telemetry.dominance_candidate_checks ==
        qd1.telemetry.dominance_candidate_checks);

    value.tasks[0].guidance_priority = 0.75;
    value.tasks[1].guidance_priority = -0.25;
    value.guidance_label_state_coefficients = {
        0.2, -0.1, 0.05, 0.0, 0.4,
        -0.2, 0.1, 0.1, -0.1, 0.05,
        0.2, -0.2, 0.1, -0.1, 0.25,
    };
    const auto qgr1 = lunar_spprc::solve(value, qgr1_params);
    assert(qgr1.status == qd1.status);
    assert(qgr1.search_exhaustive == qd1.search_exhaustive);
    assert(qgr1.frontier_empty == qd1.frontier_empty);
    assert(!qgr1.labels_dropped);
    std::vector<double> qd1_costs;
    std::vector<double> qgr1_costs;
    for (const auto& route : qd1.routes) {
        qd1_costs.push_back(route.reduced_cost);
    }
    for (const auto& route : qgr1.routes) {
        qgr1_costs.push_back(route.reduced_cost);
    }
    std::ranges::sort(qd1_costs);
    std::ranges::sort(qgr1_costs);
    assert(qd1_costs == qgr1_costs);
    assert(qgr1.telemetry.proof_queue_label_state_scored_count > 0U);
    assert(qgr1.telemetry.proof_queue_guidance_nonzero_score_count > 0U);
}

void verify_qgr1_stratified_trace_reservoir_is_deterministic_and_exact_safe() {
    auto value = model();
    lunar_spprc::SolveParams baseline_params;
    baseline_params.exact_proof = true;
    const auto baseline = lunar_spprc::solve(value, baseline_params);

    auto trace_params = baseline_params;
    trace_params.proof_queue_label_trace_enabled = true;
    trace_params.proof_queue_label_trace_max_rows = 100'000;
    trace_params.proof_queue_label_trace_sampling_mode =
        lunar_spprc::LabelTraceSamplingMode::QGR1StratifiedReservoirV1;
    trace_params.proof_queue_label_trace_seed = 0x260815ULL;
    trace_params.proof_queue_preference_cap_per_family = 4;
    trace_params.proof_queue_surface_reservoir_count = 8;
    trace_params.proof_queue_surface_labels_per_bucket = 2;
    trace_params.proof_queue_witness_route_cap = 512;
    trace_params.proof_queue_witness_ancestor_cap = 25'000;
    const auto first = lunar_spprc::solve(value, trace_params);
    const auto second = lunar_spprc::solve(value, trace_params);

    assert(first.status == baseline.status);
    assert(first.search_exhaustive == baseline.search_exhaustive);
    assert(first.frontier_empty == baseline.frontier_empty);
    assert(first.labels_dropped == baseline.labels_dropped);
    assert(first.routes.size() == baseline.routes.size());
    assert(!first.telemetry.proof_queue_label_trace_incomplete);
    assert(
        first.telemetry.proof_queue_label_trace_sampling_mode ==
        "qgr1_stratified_reservoir_v1");
    assert(first.telemetry.proof_queue_label_trace_seed == 0x260815ULL);
    assert(
        first.telemetry.proof_queue_label_trace_final_rows ==
        first.telemetry.proof_queue_label_state_trace.size());
    assert(
        first.telemetry.proof_queue_surface_retained <=
        trace_params.proof_queue_surface_reservoir_count);
    assert(
        first.telemetry.proof_queue_surface_label_retained <=
        trace_params.proof_queue_surface_reservoir_count *
            trace_params.proof_queue_surface_labels_per_bucket);
    assert(
        first.telemetry.proof_queue_existing_preference_retained <=
        trace_params.proof_queue_preference_cap_per_family);
    assert(
        first.telemetry.proof_queue_incoming_preference_retained <=
        trace_params.proof_queue_preference_cap_per_family);

    assert(
        first.telemetry.proof_queue_label_state_trace.size() ==
        second.telemetry.proof_queue_label_state_trace.size());
    for (std::size_t index = 0;
         index < first.telemetry.proof_queue_label_state_trace.size();
         ++index) {
        assert(
            first.telemetry.proof_queue_label_state_trace[index].label_id ==
            second.telemetry.proof_queue_label_state_trace[index].label_id);
    }
    assert(
        first.telemetry.proof_queue_label_preference_trace.size() ==
        second.telemetry.proof_queue_label_preference_trace.size());
    for (std::size_t index = 0;
         index < first.telemetry.proof_queue_label_preference_trace.size();
         ++index) {
        const auto& lhs =
            first.telemetry.proof_queue_label_preference_trace[index];
        const auto& rhs =
            second.telemetry.proof_queue_label_preference_trace[index];
        assert(lhs.kind == rhs.kind);
        assert(lhs.winner_label_id == rhs.winner_label_id);
        assert(lhs.loser_label_id == rhs.loser_label_id);
    }
}

void verify_frontier_probe_switch_is_deterministic_and_exact_safe() {
    auto value = model();
    lunar_spprc::SolveParams q0_params;
    q0_params.exact_proof = true;
    const auto q0 = lunar_spprc::solve(value, q0_params);

    auto qpf0_params = q0_params;
    qpf0_params.frontier_probe.mode =
        lunar_spprc::FrontierProbeMode::CollectForceQ0;
    qpf0_params.frontier_probe.processed_label_boundary = 1U;
    const auto qpf0_first = lunar_spprc::solve(value, qpf0_params);
    const auto qpf0_second = lunar_spprc::solve(value, qpf0_params);
    assert(qpf0_first.status == q0.status);
    assert(qpf0_first.search_exhaustive == q0.search_exhaustive);
    assert(qpf0_first.frontier_empty == q0.frontier_empty);
    assert(qpf0_first.routes.size() == q0.routes.size());
    assert(qpf0_first.telemetry.processed_labels ==
           q0.telemetry.processed_labels);
    assert(qpf0_first.telemetry.frontier_probe.enabled);
    assert(qpf0_first.telemetry.frontier_probe.reached);
    assert(qpf0_first.telemetry.frontier_probe.graph_built);
    assert(!qpf0_first.telemetry.frontier_probe.switched_to_qd1);
    assert(qpf0_first.telemetry.frontier_probe.node_features.size() == 64U);
    assert(qpf0_first.telemetry.frontier_probe.edge_count >= 64U);
    assert(
        qpf0_first.telemetry.frontier_probe.graph_hash ==
        qpf0_second.telemetry.frontier_probe.graph_hash);

    auto qpd1_params = q0_params;
    qpd1_params.frontier_probe.mode =
        lunar_spprc::FrontierProbeMode::ForceQD1;
    qpd1_params.frontier_probe.processed_label_boundary = 1U;
    const auto qpd1 = lunar_spprc::solve(value, qpd1_params);
    assert(qpd1.status == q0.status);
    assert(qpd1.search_exhaustive == q0.search_exhaustive);
    assert(qpd1.frontier_empty == q0.frontier_empty);
    assert(qpd1.routes.size() == q0.routes.size());
    const auto& probe = qpd1.telemetry.frontier_probe;
    assert(probe.reached);
    assert(probe.graph_built);
    assert(probe.switched_to_qd1);
    assert(probe.action == "SWITCH_QD1");
    assert(probe.frontier_before_migration == probe.drained_count);
    assert(probe.drained_count == probe.migrated_count);
    assert(probe.duplicate_count == 0U);
    assert(probe.creation_hash_before == probe.creation_hash_after);
    std::vector<double> q0_costs;
    std::vector<double> qpd1_costs;
    for (const auto& route : q0.routes) {
        q0_costs.push_back(route.reduced_cost);
    }
    for (const auto& route : qpd1.routes) {
        qpd1_costs.push_back(route.reduced_cost);
    }
    std::ranges::sort(q0_costs);
    std::ranges::sort(qpd1_costs);
    assert(q0_costs == qpd1_costs);
}

void verify_temporal_frontier_snapshots_are_single_request_and_exact_safe() {
    auto value = model();
    lunar_spprc::SolveParams q0_params;
    q0_params.exact_proof = true;
    const auto q0 = lunar_spprc::solve(value, q0_params);

    auto temporal_q0_params = q0_params;
    temporal_q0_params.frontier_probe.mode =
        lunar_spprc::FrontierProbeMode::CollectForceQ0;
    temporal_q0_params.frontier_probe.processed_label_boundary = 2U;
    temporal_q0_params.frontier_probe.observation_boundaries = {1U, 2U};
    const auto temporal_first = lunar_spprc::solve(value, temporal_q0_params);
    const auto temporal_second = lunar_spprc::solve(value, temporal_q0_params);
    assert(temporal_first.status == q0.status);
    assert(temporal_first.search_exhaustive == q0.search_exhaustive);
    assert(temporal_first.frontier_empty == q0.frontier_empty);
    assert(temporal_first.routes.size() == q0.routes.size());
    assert(temporal_first.telemetry.processed_labels ==
           q0.telemetry.processed_labels);
    assert(temporal_first.telemetry.extended_labels ==
           q0.telemetry.extended_labels);
    assert(temporal_first.telemetry.dominated_labels ==
           q0.telemetry.dominated_labels);
    assert(temporal_first.telemetry.dominance_candidate_checks ==
           q0.telemetry.dominance_candidate_checks);
    assert(temporal_first.telemetry.subset_dominance_candidate_checks ==
           q0.telemetry.subset_dominance_candidate_checks);
    const auto& snapshots = temporal_first.telemetry.frontier_probe.snapshots;
    const auto& repeated = temporal_second.telemetry.frontier_probe.snapshots;
    assert(snapshots.size() == 2U);
    assert(repeated.size() == snapshots.size());
    for (std::size_t index = 0; index < snapshots.size(); ++index) {
        assert(snapshots[index].reached);
        assert(snapshots[index].graph_built);
        assert(snapshots[index].boundary == index + 1U);
        assert(snapshots[index].processed_labels == index + 1U);
        assert(snapshots[index].node_features.size() == 64U);
        assert(snapshots[index].graph_hash == repeated[index].graph_hash);
    }

    auto temporal_qd1_params = temporal_q0_params;
    temporal_qd1_params.frontier_probe.mode =
        lunar_spprc::FrontierProbeMode::ForceQD1;
    const auto temporal_qd1 = lunar_spprc::solve(value, temporal_qd1_params);
    assert(temporal_qd1.status == q0.status);
    assert(temporal_qd1.search_exhaustive == q0.search_exhaustive);
    assert(temporal_qd1.frontier_empty == q0.frontier_empty);
    assert(temporal_qd1.routes.size() == q0.routes.size());
    const auto& probe = temporal_qd1.telemetry.frontier_probe;
    assert(probe.snapshots.size() == 2U);
    assert(probe.switched_to_qd1);
    assert(probe.frontier_before_migration == probe.migrated_count);
    assert(probe.creation_hash_before == probe.creation_hash_after);
    assert(probe.duplicate_count == 0U);

    auto trial_revert_params = q0_params;
    trial_revert_params.frontier_probe.mode =
        lunar_spprc::FrontierProbeMode::ForceTrialRevert;
    trial_revert_params.frontier_probe.processed_label_boundary = 1U;
    trial_revert_params.frontier_probe.trial_pop_budget = 1U;
    trial_revert_params.frontier_probe.problem_scale = 30U;
    trial_revert_params.frontier_probe.pricing_lifecycle = "root_cg";
    const auto trial_revert = lunar_spprc::solve(value, trial_revert_params);
    assert(trial_revert.status == q0.status);
    assert(trial_revert.search_exhaustive == q0.search_exhaustive);
    assert(trial_revert.frontier_empty == q0.frontier_empty);
    assert(trial_revert.routes.size() == q0.routes.size());
    const auto& reverted = trial_revert.telemetry.frontier_probe;
    assert(reverted.trial_started);
    assert(reverted.trial_completed);
    assert(reverted.trial_pops == 1U);
    assert(reverted.migrated_back_to_q0);
    assert(reverted.action == "MIGRATE_BACK_TO_Q0");
    assert(reverted.reverse_frontier_before_migration ==
           reverted.reverse_staged_count);
    assert(reverted.reverse_staged_count == reverted.reverse_migrated_count);
    assert(reverted.reverse_duplicate_count == 0U);
    assert(reverted.reverse_creation_hash_before ==
           reverted.reverse_creation_hash_after);
    assert(reverted.trial_start_snapshot.graph_built);
    assert(reverted.trial_end_snapshot.graph_built);
    assert(reverted.temporal_graph_build_wall_seconds >=
           reverted.trial_start_snapshot.graph_build_wall_seconds +
               reverted.trial_end_snapshot.graph_build_wall_seconds);
    assert(!reverted.trial_start_label_graph.graph_hash.empty());
    assert(!reverted.trial_end_label_graph.graph_hash.empty());
    assert(!reverted.trial_start_temporal_graph.graph_hash.empty());
    assert(!reverted.trial_end_temporal_graph.graph_hash.empty());
    assert(reverted.trial_start_temporal_graph.node_features.size() ==
           reverted.trial_start_label_graph.label_nodes.size() +
               value.tasks.size());
    assert(reverted.trial_end_temporal_graph.node_features.size() ==
           reverted.trial_end_label_graph.label_nodes.size() +
               value.tasks.size());
    assert(reverted.temporal_cell_edge_count == 64U);
    assert(reverted.temporal_label_edge_count ==
           reverted.temporal_surviving_label_count);
    assert(reverted.temporal_extended_label_delta >= 1U);
    assert(reverted.temporal_survival_fraction >= 0.0);
    assert(reverted.temporal_survival_fraction <= 1.0);
    assert(reverted.temporal_frontier_churn >= 0.0);
    assert(reverted.temporal_frontier_churn <= 1.0);
    assert(reverted.temporal_edges.size() ==
           reverted.temporal_cell_edge_count +
               reverted.temporal_label_edge_count);
    assert(!reverted.temporal_edge_hash.empty());
    assert(reverted.temporal_counter_features[0] == 1.0);
    assert(!reverted.temporal_counter_hash.empty());
    const auto trial_revert_repeated = lunar_spprc::solve(
        value, trial_revert_params);
    const auto& repeated_revert =
        trial_revert_repeated.telemetry.frontier_probe;
    assert(repeated_revert.trial_start_snapshot.graph_hash ==
           reverted.trial_start_snapshot.graph_hash);
    assert(repeated_revert.trial_end_snapshot.graph_hash ==
           reverted.trial_end_snapshot.graph_hash);
    assert(repeated_revert.trial_start_temporal_graph.graph_hash ==
           reverted.trial_start_temporal_graph.graph_hash);
    assert(repeated_revert.trial_end_temporal_graph.graph_hash ==
           reverted.trial_end_temporal_graph.graph_hash);
    assert(repeated_revert.temporal_edge_hash == reverted.temporal_edge_hash);
    assert(repeated_revert.temporal_counter_hash ==
           reverted.temporal_counter_hash);

    auto trial_continue_params = trial_revert_params;
    trial_continue_params.frontier_probe.mode =
        lunar_spprc::FrontierProbeMode::ForceTrialContinue;
    const auto trial_continue = lunar_spprc::solve(value, trial_continue_params);
    assert(trial_continue.status == q0.status);
    assert(trial_continue.search_exhaustive == q0.search_exhaustive);
    assert(trial_continue.frontier_empty == q0.frontier_empty);
    assert(trial_continue.routes.size() == q0.routes.size());
    assert(trial_continue.telemetry.frontier_probe.trial_completed);
    assert(!trial_continue.telemetry.frontier_probe.migrated_back_to_q0);
    assert(trial_continue.telemetry.frontier_probe.action == "CONTINUE_QD1");

    auto unsafe_temporal_params = trial_revert_params;
    unsafe_temporal_params.frontier_probe.require_root_cg = false;
    bool unsafe_temporal_rejected = false;
    try {
        static_cast<void>(lunar_spprc::solve(value, unsafe_temporal_params));
    } catch (const std::invalid_argument&) {
        unsafe_temporal_rejected = true;
    }
    assert(unsafe_temporal_rejected);
    unsafe_temporal_params = trial_revert_params;
    unsafe_temporal_params.frontier_probe.fail_closed_on_ood = false;
    unsafe_temporal_rejected = false;
    try {
        static_cast<void>(lunar_spprc::solve(value, unsafe_temporal_params));
    } catch (const std::invalid_argument&) {
        unsafe_temporal_rejected = true;
    }
    assert(unsafe_temporal_rejected);

    auto learned_temporal_params = trial_revert_params;
    learned_temporal_params.frontier_probe.mode =
        lunar_spprc::FrontierProbeMode::LearnedAfterTrial;
    bool unbound_learned_rejected = false;
    try {
        static_cast<void>(lunar_spprc::solve(value, learned_temporal_params));
    } catch (const std::invalid_argument&) {
        unbound_learned_rejected = true;
    }
    assert(unbound_learned_rejected);
    learned_temporal_params.frontier_probe.manifest_sha256 =
        std::string(64U, 'a');
    learned_temporal_params.frontier_probe.bundle_file_sha256 =
        std::string(64U, 'b');
    learned_temporal_params.frontier_probe.temporal_bundle.bundle_sha256 =
        std::string(64U, 'c');
    const auto invalid_bundle_fallback = lunar_spprc::solve(
        value, learned_temporal_params);
    assert(invalid_bundle_fallback.status == q0.status);
    assert(invalid_bundle_fallback.search_exhaustive == q0.search_exhaustive);
    assert(invalid_bundle_fallback.frontier_empty == q0.frontier_empty);
    assert(invalid_bundle_fallback.telemetry.frontier_probe.fail_closed);
    assert(
        invalid_bundle_fallback.telemetry.frontier_probe.decision_reason ==
        "invalid_temporal_bundle");
    assert(
        invalid_bundle_fallback.telemetry.frontier_probe.action ==
        "MIGRATE_BACK_TO_Q0");

    auto natural_end_params = trial_revert_params;
    natural_end_params.frontier_probe.mode =
        lunar_spprc::FrontierProbeMode::LearnedAfterTrial;
    natural_end_params.frontier_probe.trial_pop_budget = 2048U;
    natural_end_params.frontier_probe.manifest_sha256 =
        std::string(64U, 'd');
    natural_end_params.frontier_probe.bundle_file_sha256 =
        std::string(64U, 'e');
    natural_end_params.frontier_probe.temporal_bundle.bundle_sha256 =
        std::string(64U, 'f');
    const auto natural_end = lunar_spprc::solve(value, natural_end_params);
    const auto& natural_probe = natural_end.telemetry.frontier_probe;
    assert(natural_end.status == q0.status);
    assert(natural_end.search_exhaustive == q0.search_exhaustive);
    assert(natural_end.frontier_empty == q0.frontier_empty);
    assert(natural_end.routes.size() == q0.routes.size());
    assert(natural_probe.trial_started);
    assert(!natural_probe.trial_completed);
    assert(!natural_probe.model_called);
    assert(natural_probe.action == "TRIAL_EXHAUSTED_BEFORE_DECISION");
    assert(natural_probe.decision_reason ==
           "frontier_exhausted_before_trial_budget");

    lunar_spprc::TemporalGatBundle decision_bundle;
    decision_bundle.controller_kind = "temporal_gat";
    decision_bundle.gain_scale = 10.0;
    decision_bundle.minimum_benefit_probability = 0.5;
    decision_bundle.maximum_adverse_probability = 0.5;
    decision_bundle.minimum_expected_gain = 0.2;
    decision_bundle.adverse_penalty = 0.1;
    decision_bundle.maximum_disagreement = 1.0;
    const std::vector<std::array<double, 3>> decision_outputs{
        {0.8, 0.2, 0.1}, {0.8, 0.2, 0.1}, {0.8, 0.2, 0.1},
    };
    const auto accepted = lunar_spprc::decide_temporal_gat_outputs(
        decision_bundle, decision_outputs);
    assert(accepted.continue_qd1);
    assert(accepted.positive_gain == 1.0);
    assert(accepted.expected_gain == accepted.p_benefit);
    decision_bundle.maximum_disagreement = 0.01;
    const auto rejected = lunar_spprc::decide_temporal_gat_outputs(
        decision_bundle,
        {{0.8, 0.2, 0.1}, {0.6, 0.2, 0.1}, {0.7, 0.2, 0.1}});
    assert(!rejected.continue_qd1);
}

void verify_atomic_frontier_staging_contract() {
    using Queue = std::priority_queue<std::uint64_t>;
    const auto stage = [](
        const Queue& source,
        std::optional<std::size_t> inject_after = std::nullopt) {
        return lunar_spprc::detail::stage_atomic_frontier_migration(
            source,
            Queue{},
            [](std::uint64_t value) { return value; },
            [](std::uint64_t value) { return value; },
            [](std::uint64_t value) { return value; },
            [](std::uint64_t value) {
                return value * 0x9e3779b97f4a7c15ULL;
            },
            inject_after);
    };

    const Queue empty;
    const auto empty_stage = stage(empty);
    assert(empty.empty());
    assert(empty_stage.source_size == 0U);
    assert(empty_stage.staged_count == 0U);
    assert(empty_stage.target.empty());

    Queue single;
    single.push(17U);
    const auto single_top = single.top();
    const auto single_stage = stage(single);
    assert(single.size() == 1U);
    assert(single.top() == single_top);
    assert(single_stage.source_size == 1U);
    assert(single_stage.staged_count == 1U);
    assert(single_stage.target.size() == 1U);
    assert(single_stage.creation_hash_before ==
           single_stage.creation_hash_after);

    Queue large;
    for (std::uint64_t id = 0U; id < 16'384U; ++id) {
        large.push(id);
    }
    const auto large_size = large.size();
    const auto large_top = large.top();
    const auto large_stage = stage(large);
    assert(large.size() == large_size);
    assert(large.top() == large_top);
    assert(large_stage.staged_count == large_size);
    assert(large_stage.target.size() == large_size);
    assert(large_stage.bindings.size() == large_size);
    assert(large_stage.creation_hash_before ==
           large_stage.creation_hash_after);

    Queue duplicate;
    duplicate.push(7U);
    duplicate.push(7U);
    bool duplicate_rejected = false;
    try {
        static_cast<void>(stage(duplicate));
    } catch (const std::runtime_error& exception) {
        duplicate_rejected =
            std::string(exception.what()) ==
            "atomic frontier staging duplicate creation id";
    }
    assert(duplicate_rejected);
    assert(duplicate.size() == 2U);
    assert(duplicate.top() == 7U);

    bool exception_injected = false;
    try {
        static_cast<void>(stage(large, 8'192U));
    } catch (const std::runtime_error& exception) {
        exception_injected =
            std::string(exception.what()) ==
            "atomic frontier staging injected exception";
    }
    assert(exception_injected);
    assert(large.size() == large_size);
    assert(large.top() == large_top);
}

void verify_counterfactual_prefix_is_truncated_route_free_and_deterministic() {
    lunar_spprc::Model value;
    value.instance_id = "counterfactual_prefix_native_test";
    value.structure_hash = "counterfactual_prefix_native_test_v1";
    value.max_tasks_per_trip = 13;
    value.capacity = 100.0;
    value.energy_limit = 1000.0;
    value.horizon = 1000.0;
    value.dock_overhead = 1.0;
    value.recharge_power = 10.0;
    value.shadow_limit = 1000.0;
    value.cost_coefficient = 1.0;
    value.risk_coefficient = 0.0;
    value.completion_coefficient = 0.0;
    std::vector<std::string> nodes{"depot"};
    for (std::size_t index = 0; index < 13U; ++index) {
        const auto id = "t" + std::to_string(index);
        nodes.push_back(id);
        value.tasks.push_back({
            .id = id,
            .index = index,
            .science_weight = 1.0,
            .demand = 1.0,
            .service_time = 1.0,
            .service_energy = 1.0,
            .service_cost = 1.0,
            .ready_time = 0.0,
            .due_time = 900.0,
            .dual = 2.0,
        });
    }
    for (const auto& source : nodes) {
        for (const auto& target : nodes) {
            if (source == target) {
                continue;
            }
            value.arcs.push_back({
                .source = source,
                .target = target,
                .path_type = "low_time",
                .travel_time = 1.0,
                .energy = 1.0,
                .risk = 0.0,
                .distance = 1.0,
                .shadow = 0.0,
            });
        }
    }
    lunar_spprc::SolveParams q0_prefix;
    q0_prefix.exact_proof = true;
    q0_prefix.counterfactual_prefix.mode =
        lunar_spprc::CounterfactualPrefixMode::Q0Prefix;
    q0_prefix.counterfactual_prefix.sampling_seed = 170141U;
    q0_prefix.counterfactual_prefix.context_features[15] = 3.25;
    q0_prefix.counterfactual_prefix.context_features[16] = 1.0;
    const auto q0_first = lunar_spprc::solve(value, q0_prefix);
    const auto q0_second = lunar_spprc::solve(value, q0_prefix);
    assert(q0_first.status == "COUNTERFACTUAL_PREFIX_COMPLETE");
    assert(!q0_first.search_exhaustive);
    assert(!q0_first.frontier_empty);
    assert(q0_first.routes.empty());
    const auto& q0 = q0_first.telemetry.counterfactual_prefix;
    assert(q0.enabled && q0.reached_boundary && q0.complete);
    assert(q0.truncated_diagnostic && !q0.exact);
    assert(q0.public_routes_forbidden && q0.certificate_forbidden);
    assert(q0.routes_suppressed && q0.certificate_suppressed);
    assert(q0.endpoints.size() == 3U);
    assert(q0.maximum_rollout_budget == 2048U);
    assert(q0.base_request_elapsed_wall_seconds >= 0.0);
    assert(q0.base_graph_build_wall_seconds >= 0.0);
    assert(q0.request_elapsed_wall_seconds >=
           q0.base_request_elapsed_wall_seconds);
    assert(q0.base_graph.context_features[15] == 3.25);
    assert(q0.base_graph.context_features[16] == 1.0);
    double previous_elapsed = q0.base_request_elapsed_wall_seconds;
    for (const auto& endpoint : q0.endpoints) {
        assert(endpoint.request_elapsed_wall_seconds >= previous_elapsed);
        assert(endpoint.rollout_elapsed_wall_seconds >= 0.0);
        assert(endpoint.graph_build_wall_seconds >= 0.0);
        assert(endpoint.graph_build_wall_seconds ==
               endpoint.graph.build_wall_seconds);
        previous_elapsed = endpoint.request_elapsed_wall_seconds;
    }
    assert(q0.base_graph.sampled_label_count <= 256U);
    assert(!q0.base_graph.graph_hash.empty());
    assert(
        q0.base_graph.graph_hash ==
        q0_second.telemetry.counterfactual_prefix.base_graph.graph_hash);

    auto qd1_prefix = q0_prefix;
    qd1_prefix.counterfactual_prefix.mode =
        lunar_spprc::CounterfactualPrefixMode::QD1Prefix;
    const auto qd1 = lunar_spprc::solve(value, qd1_prefix);
    assert(qd1.status == "COUNTERFACTUAL_PREFIX_COMPLETE");
    assert(qd1.routes.empty());
    assert(qd1.telemetry.counterfactual_prefix.switched_to_qd1);
    assert(
        qd1.telemetry.counterfactual_prefix.base_graph_hash ==
        q0.base_graph_hash);
    assert(qd1.telemetry.counterfactual_prefix.migration_wall_seconds >= 0.0);

    auto selected_prefix = q0_prefix;
    selected_prefix.counterfactual_prefix.maximum_rollout_budget = 128U;
    const auto selected = lunar_spprc::solve(value, selected_prefix);
    const auto& selected_telemetry =
        selected.telemetry.counterfactual_prefix;
    assert(selected.status == "COUNTERFACTUAL_PREFIX_COMPLETE");
    assert(selected_telemetry.endpoints.size() == 1U);
    assert(selected_telemetry.endpoints.front().rollout_budget == 128U);
    assert(selected_telemetry.endpoints.front().processed_labels == 4224U);
    assert(selected_telemetry.stop_reason ==
           "selected_rollout_checkpoint_reached");
}

void verify_qg2_500_randomized_exact_differentials() {
    std::uint64_t state = 0x6A09E667F3BCC909ULL;
    const auto sample = [&state]() {
        state = state * 6364136223846793005ULL +
                1442695040888963407ULL;
        return static_cast<double>((state >> 11U) & 0x1FFFFFU) /
               static_cast<double>(0x1FFFFFU);
    };
    for (std::size_t trial = 0; trial < 500U; ++trial) {
        auto value = model();
        value.structure_hash =
            "native_qg2_random_differential_" + std::to_string(trial);
        value.max_tasks_per_trip = trial % 3U == 0U ? 2U : 1U;
        value.fleet_dual = sample() * 3.0;
        for (auto& task : value.tasks) {
            task.dual = sample() * 35.0;
            task.service_cost = 0.5 + sample() * 2.0;
            task.guidance_priority = sample() * 2.0 - 1.0;
        }
        for (auto& arc : value.arcs) {
            arc.travel_time = 0.5 + sample() * 3.0;
            arc.energy = 0.5 + sample() * 2.0;
            arc.risk = sample();
            arc.guidance_priority = sample() * 2.0 - 1.0;
        }
        value.guidance_task_arc_enabled = true;
        value.guidance_label_state_enabled = true;
        for (auto& coefficient :
             value.guidance_label_state_coefficients) {
            coefficient = sample() * 2.0 - 1.0;
        }
        if (trial % 7U == 0U) {
            value.branch_decisions.push_back({
                .task_a = 0,
                .task_b = 1,
                .task_a_exists = true,
                .task_b_exists = true,
                .sense = trial % 14U == 0U
                    ? lunar_spprc::BranchSense::SameJourney
                    : lunar_spprc::BranchSense::DifferentJourney,
            });
        }
        if (trial % 11U == 0U) {
            value.cuts.push_back({
                .id = "random_sri",
                .kind = lunar_spprc::CutKind::SubsetRow,
                .task_mask = {0b11U},
                .divisor = 2,
                .dual = sample() * 5.0,
                .state_bit_offset = 0,
                .state_bit_width = 2,
                .max_overlap = 2,
            });
        }

        lunar_spprc::SolveParams q0_params;
        q0_params.exact_proof = true;
        q0_params.negative_epsilon = 1.0e-6;
        auto qg2_params = q0_params;
        qg2_params.proof_queue_policy =
            lunar_spprc::ProofQueuePolicy::QG2LabelStatePotential;
        qg2_params.proof_queue_guidance_bucket_width =
            trial % 3U == 0U ? 1.0e-4
            : trial % 3U == 1U ? 3.0e-4
                              : 1.0e-3;
        auto qgr1_params = qg2_params;
        qgr1_params.proof_queue_policy =
            lunar_spprc::ProofQueuePolicy::QGR1DepthResidualGAT;
        qgr1_params.proof_queue_guidance_bucket_width = 1.0e-4;
        auto q0_value = value;
        q0_value.guidance_label_state_enabled = false;
        const auto q0 = lunar_spprc::solve(q0_value, q0_params);
        auto qpf0_params = q0_params;
        qpf0_params.frontier_probe.mode =
            lunar_spprc::FrontierProbeMode::CollectForceQ0;
        qpf0_params.frontier_probe.processed_label_boundary = 1U;
        auto qpd1_params = q0_params;
        qpd1_params.frontier_probe.mode =
            lunar_spprc::FrontierProbeMode::ForceQD1;
        qpd1_params.frontier_probe.processed_label_boundary = 1U;
        const auto qpf0 = lunar_spprc::solve(q0_value, qpf0_params);
        const auto qpd1 = lunar_spprc::solve(q0_value, qpd1_params);
        auto trial_revert_params = q0_params;
        trial_revert_params.frontier_probe.mode =
            lunar_spprc::FrontierProbeMode::ForceTrialRevert;
        trial_revert_params.frontier_probe.processed_label_boundary = 1U;
        trial_revert_params.frontier_probe.trial_pop_budget = 1U;
        trial_revert_params.frontier_probe.problem_scale = 30U;
        trial_revert_params.frontier_probe.pricing_lifecycle = "root_cg";
        auto trial_continue_params = trial_revert_params;
        trial_continue_params.frontier_probe.mode =
            lunar_spprc::FrontierProbeMode::ForceTrialContinue;
        const auto trial_revert = lunar_spprc::solve(
            q0_value, trial_revert_params);
        const auto trial_continue = lunar_spprc::solve(
            q0_value, trial_continue_params);
        auto traced_q0_params = q0_params;
        traced_q0_params.proof_queue_label_trace_enabled = true;
        traced_q0_params.proof_queue_label_trace_max_rows = 100'000;
        traced_q0_params.proof_queue_label_trace_sampling_mode =
            lunar_spprc::LabelTraceSamplingMode::QGR1StratifiedReservoirV1;
        traced_q0_params.proof_queue_label_trace_seed =
            0x2608150000000000ULL + trial;
        const auto traced_q0 = lunar_spprc::solve(q0_value, traced_q0_params);
        const auto qg2 = lunar_spprc::solve(value, qg2_params);
        const auto qgr1 = lunar_spprc::solve(value, qgr1_params);
        assert(q0.status == traced_q0.status);
        assert(q0.search_exhaustive == traced_q0.search_exhaustive);
        assert(q0.frontier_empty == traced_q0.frontier_empty);
        assert(q0.labels_dropped == traced_q0.labels_dropped);
        assert(q0.routes.size() == traced_q0.routes.size());
        assert(q0.status == qpf0.status);
        assert(q0.search_exhaustive == qpf0.search_exhaustive);
        assert(q0.frontier_empty == qpf0.frontier_empty);
        assert(q0.routes.size() == qpf0.routes.size());
        assert(q0.status == qpd1.status);
        assert(q0.search_exhaustive == qpd1.search_exhaustive);
        assert(q0.frontier_empty == qpd1.frontier_empty);
        assert(q0.routes.size() == qpd1.routes.size());
        for (const auto& candidate : {&trial_revert, &trial_continue}) {
            assert(q0.status == candidate->status);
            assert(q0.search_exhaustive == candidate->search_exhaustive);
            assert(q0.frontier_empty == candidate->frontier_empty);
            assert(q0.labels_dropped == candidate->labels_dropped);
            assert(q0.routes.size() == candidate->routes.size());
        }
        if (qpd1.telemetry.frontier_probe.reached) {
            assert(qpd1.telemetry.frontier_probe.switched_to_qd1);
            assert(
                qpd1.telemetry.frontier_probe.frontier_before_migration ==
                qpd1.telemetry.frontier_probe.migrated_count);
            assert(
                qpd1.telemetry.frontier_probe.creation_hash_before ==
                qpd1.telemetry.frontier_probe.creation_hash_after);
            assert(qpd1.telemetry.frontier_probe.duplicate_count == 0U);
        }
        assert(q0.status == qg2.status);
        assert(q0.search_exhaustive == qg2.search_exhaustive);
        assert(q0.frontier_empty == qg2.frontier_empty);
        assert(!q0.labels_dropped);
        assert(!qg2.labels_dropped);
        assert(q0.routes.size() == qg2.routes.size());
        std::vector<double> q0_costs;
        std::vector<double> traced_q0_costs;
        std::vector<double> qg2_costs;
        std::vector<double> qpf0_costs;
        std::vector<double> qpd1_costs;
        std::vector<double> trial_revert_costs;
        std::vector<double> trial_continue_costs;
        for (const auto& route : q0.routes) {
            q0_costs.push_back(route.reduced_cost);
        }
        for (const auto& route : qg2.routes) {
            qg2_costs.push_back(route.reduced_cost);
        }
        for (const auto& route : traced_q0.routes) {
            traced_q0_costs.push_back(route.reduced_cost);
        }
        for (const auto& route : qpf0.routes) {
            qpf0_costs.push_back(route.reduced_cost);
        }
        for (const auto& route : qpd1.routes) {
            qpd1_costs.push_back(route.reduced_cost);
        }
        for (const auto& route : trial_revert.routes) {
            trial_revert_costs.push_back(route.reduced_cost);
        }
        for (const auto& route : trial_continue.routes) {
            trial_continue_costs.push_back(route.reduced_cost);
        }
        std::ranges::sort(q0_costs);
        std::ranges::sort(traced_q0_costs);
        std::ranges::sort(qg2_costs);
        std::ranges::sort(qpf0_costs);
        std::ranges::sort(qpd1_costs);
        std::ranges::sort(trial_revert_costs);
        std::ranges::sort(trial_continue_costs);
        assert(q0_costs == traced_q0_costs);
        assert(q0_costs == qg2_costs);
        assert(q0_costs == qpf0_costs);
        assert(q0_costs == qpd1_costs);
        assert(q0_costs == trial_revert_costs);
        assert(q0_costs == trial_continue_costs);
        assert(q0.status == qgr1.status);
        assert(q0.search_exhaustive == qgr1.search_exhaustive);
        assert(q0.frontier_empty == qgr1.frontier_empty);
        assert(!qgr1.labels_dropped);
        assert(q0.routes.size() == qgr1.routes.size());
        std::vector<double> qgr1_costs;
        for (const auto& route : qgr1.routes) {
            qgr1_costs.push_back(route.reduced_cost);
        }
        std::ranges::sort(qgr1_costs);
        assert(q0_costs == qgr1_costs);
    }
    std::cout
        << "TEMPORAL_ACTION_RANDOMIZED_EXACT cases=500 mismatches=0\n";

    auto invalid = model();
    invalid.guidance_task_arc_enabled = true;
    invalid.guidance_label_state_enabled = true;
    invalid.guidance_label_state_coefficients[3] =
        std::numeric_limits<double>::quiet_NaN();
    lunar_spprc::SolveParams invalid_params;
    invalid_params.proof_queue_policy =
        lunar_spprc::ProofQueuePolicy::QG2LabelStatePotential;
    bool rejected = false;
    try {
        static_cast<void>(lunar_spprc::solve(invalid, invalid_params));
    } catch (const std::invalid_argument&) {
        rejected = true;
    }
    assert(rejected);

    invalid = model();
    invalid.guidance_task_arc_enabled = true;
    invalid.guidance_label_state_enabled = true;
    invalid_params.dssr_enabled = true;
    rejected = false;
    try {
        static_cast<void>(lunar_spprc::solve(invalid, invalid_params));
    } catch (const std::invalid_argument&) {
        rejected = true;
    }
    assert(rejected);
}

#if LUNAR_SPPRC_ENABLE_BIDIRECTIONAL_FEASIBILITY
void verify_bidirectional_depot_join_is_exact_and_fail_closed() {
    auto value = model();
    value.structure_hash = "native_bidirectional_feasibility_v1";
    value.tasks[1].ready_time = 20.0;
    value.fleet_dual = 0.75;
    value.cuts.push_back({
        .id = "sri",
        .kind = lunar_spprc::CutKind::SubsetRow,
        .task_mask = {0b11U},
        .divisor = 2,
        .dual = 5.0,
        .state_bit_offset = 0,
        .state_bit_width = 2,
        .max_overlap = 2,
    });
    value.branch_decisions.push_back({
        .task_a = 0,
        .task_b = 1,
        .task_a_exists = true,
        .task_b_exists = true,
        .sense = lunar_spprc::BranchSense::SameJourney,
    });
    const lunar_spprc::SortiePath a{
        .tasks = {"a"},
        .path_types = {"low_time", "low_time"},
    };
    const lunar_spprc::SortiePath b{
        .tasks = {"b"},
        .path_types = {"low_time", "low_time"},
    };
    const auto full = lunar_spprc::audit_bidirectional_depot_join(
        value, {}, {a, b});
    const auto split = lunar_spprc::audit_bidirectional_depot_join(
        value, {a}, {b});
    const auto all_forward =
        lunar_spprc::audit_bidirectional_depot_join(
            value, {a, b}, {});
    for (const auto* result : {&full, &split, &all_forward}) {
        assert(result->status == "FEASIBLE_JOIN_DIAGNOSTIC_ONLY");
        assert(result->feasible);
        assert(result->task_sets_disjoint);
        assert(result->suffix_boundary_feasible);
        assert(result->branch_feasible);
        assert(result->static_objective_finite);
        assert(!result->can_certify_no_negative);
        assert(result->task_count == 2);
        assert(result->sortie_count == 2);
    }
    assert(std::abs(full.true_reduced_cost - split.true_reduced_cost) < 1.0e-12);
    assert(
        std::abs(
            full.true_reduced_cost -
            all_forward.true_reduced_cost
        ) < 1.0e-12);
    assert(std::abs(full.raw_operating_cost - 12.0) < 1.0e-12);
    assert(std::abs(full.raw_risk - 0.4) < 1.0e-12);
    assert(
        std::abs(full.raw_weighted_completion - 23.0) <
        1.0e-12);
    assert(std::abs(full.cut_dual_reward - 5.0) < 1.0e-12);
    assert(std::abs(full.true_reduced_cost + 31.05) < 1.0e-12);

    const auto overlap =
        lunar_spprc::audit_bidirectional_depot_join(
            value, {a}, {a});
    assert(!overlap.feasible);
    assert(overlap.status == "TASK_SET_OVERLAP");
    assert(!overlap.can_certify_no_negative);

    value.branch_decisions.front().sense =
        lunar_spprc::BranchSense::DifferentJourney;
    const auto forbidden =
        lunar_spprc::audit_bidirectional_depot_join(
            value, {a}, {b});
    assert(!forbidden.feasible);
    assert(forbidden.status == "BRANCH_CONTEXT_INFEASIBLE");
    assert(!forbidden.can_certify_no_negative);

    lunar_spprc::BidirectionalBackwardProbeParams probe_params;
    probe_params.max_partial_states = 10'000;
    probe_params.max_completed_sorties = 10'000;
    probe_params.timeout_seconds = 5.0;
    const auto backward =
        lunar_spprc::probe_bidirectional_backward_frontier(
            value,
            probe_params);
    assert(
        backward.status ==
        "BACKWARD_SORTIE_SEED_ENUMERATION_COMPLETE");
    assert(backward.search_exhaustive);
    assert(backward.frontier_empty);
    assert(!backward.can_certify_no_negative);
    assert(backward.processed_partial_states > 0);
    assert(backward.generated_partial_states > 0);
    assert(backward.completed_sortie_candidates > 0);
    assert(backward.feasible_backward_sortie_seeds > 0);
    assert(
        backward.partial_states_by_task_depth.size() ==
        value.max_tasks_per_trip + 1U);

    lunar_spprc::BidirectionalTaskMeetProbeParams meet_params;
    meet_params.max_partial_states_per_direction = 10'000;
    meet_params.max_join_checks = 100'000;
    meet_params.timeout_seconds = 5.0;
    const auto meet =
        lunar_spprc::probe_bidirectional_task_meet_frontier(
            value,
            meet_params);
    assert(
        meet.status ==
        "TASK_MEET_SORTIE_ENUMERATION_COMPLETE");
    assert(meet.forward_generation_exhaustive);
    assert(meet.backward_generation_exhaustive);
    assert(meet.join_exhaustive);
    assert(!meet.can_certify_no_negative);
    assert(meet.forward_generated_states > 0);
    assert(meet.backward_generated_states > 0);
    assert(meet.join_pair_checks > 0);
    assert(meet.feasible_joined_sorties > 0);
    assert(meet.distinct_task_set_count > 0);
    assert(meet.nondominated_sortie_count > 0);
    assert(
        meet.nondominated_sortie_count +
        meet.dominated_sortie_count ==
        meet.feasible_joined_sorties);

    lunar_spprc::BidirectionalJourneyProbeParams journey_params;
    journey_params.max_labels = 100'000;
    journey_params.max_extension_checks = 1'000'000;
    journey_params.timeout_seconds = 5.0;
    const auto journey =
        lunar_spprc::probe_bidirectional_journey_frontier(
            value,
            meet_params,
            journey_params);
    assert(
        journey.status ==
        "JOURNEY_FRONTIER_COMPLETE_DIAGNOSTIC_ONLY");
    assert(journey.search_exhaustive);
    assert(journey.frontier_empty);
    assert(!journey.can_certify_no_negative);
    assert(journey.sortie_pool_size > 0);
    assert(journey.generated_labels > 1);
    assert(std::isfinite(journey.best_true_reduced_cost));
    lunar_spprc::SolveParams solve_params;
    solve_params.exact_proof = true;
    const auto reference = lunar_spprc::solve(
        value,
        solve_params);
    const auto reference_best = std::ranges::min_element(
        reference.routes,
        {},
        &lunar_spprc::Route::reduced_cost);
    assert(reference_best != reference.routes.end());
    assert(
        std::abs(
            reference_best->reduced_cost -
            journey.best_true_reduced_cost
        ) < 1.0e-9);

    lunar_spprc::BidirectionalMidpointProbeParams midpoint_params;
    midpoint_params.max_forward_labels = 100'000;
    midpoint_params.max_backward_labels = 100'000;
    midpoint_params.max_crossing_labels = 100'000;
    midpoint_params.max_extension_checks = 1'000'000;
    midpoint_params.max_join_checks = 1'000'000;
    midpoint_params.timeout_seconds = 5.0;
    const auto midpoint =
        lunar_spprc::probe_bidirectional_midpoint_journey_meet(
            value,
            meet_params,
            midpoint_params);
    assert(
        midpoint.status ==
        "MIDPOINT_MEET_COMPLETE_DIAGNOSTIC_ONLY");
    assert(midpoint.search_exhaustive);
    assert(midpoint.forward_exhaustive);
    assert(midpoint.backward_exhaustive);
    assert(midpoint.crossing_exhaustive);
    assert(midpoint.join_exhaustive);
    assert(!midpoint.can_certify_no_negative);
    assert(
        midpoint.time_index_candidate_join_pairs <=
        midpoint.unindexed_active_join_pairs);
    assert(
        midpoint.time_index_pruned_join_pairs +
        midpoint.time_index_candidate_join_pairs ==
        midpoint.unindexed_active_join_pairs);
    assert(
        midpoint.join_checks ==
        midpoint.time_index_candidate_join_pairs);
    assert(
        std::abs(
            reference_best->reduced_cost -
            midpoint.best_true_reduced_cost
        ) < 1.0e-9);
}
#endif

void verify_dssr_refines_non_elementary_cut_witness_and_certifies() {
    auto value = model();
    value.structure_hash = "native_dssr_refinement_structure_v1";
    value.cost_coefficient = 1.0;
    value.risk_coefficient = 0.0;
    value.completion_coefficient = 0.0;
    value.tasks[0].dual = 0.0;
    value.tasks[1].dual = 0.0;
    value.tasks[1].due_time = 0.5;
    value.cuts.push_back({
        .id = "sri",
        .kind = lunar_spprc::CutKind::SubsetRow,
        .task_mask = {0b11U},
        .divisor = 2,
        .dual = 100.0,
        .state_bit_offset = 0,
        .state_bit_width = 2,
        .max_overlap = 2,
    });

    lunar_spprc::SolveParams exact_params;
    exact_params.exact_proof = true;
    const auto elementary = lunar_spprc::solve(value, exact_params);
    assert(elementary.status == "complete");
    assert(elementary.search_exhaustive);
    assert(elementary.frontier_empty);
    assert(elementary.routes.empty());

    auto dssr_params = exact_params;
    dssr_params.dssr_enabled = true;
    dssr_params.completion_bound_enabled = true;
    dssr_params.subset_dominance_enabled = true;
    const auto dssr = lunar_spprc::solve(value, dssr_params);
    assert(dssr.status == "complete");
    assert(dssr.search_exhaustive);
    assert(dssr.frontier_empty);
    assert(!dssr.labels_dropped);
    assert(dssr.routes.empty());
    assert(dssr.telemetry.dssr_enabled);
    assert(dssr.telemetry.dssr_iteration_count >= 2);
    assert(dssr.telemetry.dssr_refinement_count >= 1);
    assert(dssr.telemetry.dssr_repeated_witness_count >= 1);
    assert(dssr.telemetry.dssr_final_critical_task_count >= 1);
    assert(!dssr.telemetry.dssr_elementary_witness_returned);
    assert(dssr.telemetry.dssr_relaxation_no_negative_certificate);
    assert(dssr.telemetry.completion_bound_evaluated_labels == 0);
    assert(dssr.telemetry.subset_dominance_candidate_checks == 0);
    assert(
        std::ranges::any_of(
            dssr.telemetry.dssr_iteration_trace,
            [](const lunar_spprc::DssrIterationTraceRow& row) {
                return row.negative_witness_found &&
                       !row.witness_elementary &&
                       row.repeated_task_count > 0;
            }));

    auto dssr_v2_params = exact_params;
    dssr_v2_params.dssr_enabled = true;
    dssr_v2_params.dssr_policy_version =
        "multi_sortie_counterexample_pressure_refinement_v2";
    dssr_v2_params.dssr_negative_batch_target = 8;
    dssr_v2_params.dssr_pressure_refinement_enabled = false;
    const auto dssr_v2 =
        lunar_spprc::solve(value, dssr_v2_params);
    assert(dssr_v2.status == elementary.status);
    assert(dssr_v2.search_exhaustive == elementary.search_exhaustive);
    assert(dssr_v2.frontier_empty == elementary.frontier_empty);
    assert(dssr_v2.routes.empty() == elementary.routes.empty());
    assert(!dssr_v2.labels_dropped);
    assert(
        dssr_v2.telemetry.dssr_final_critical_task_count >= 1);
    assert(
        dssr_v2.telemetry.dssr_relaxation_no_negative_certificate);
}

void verify_dssr_returns_only_elementary_negative_witness() {
    auto params = lunar_spprc::SolveParams{};
    params.exact_proof = true;
    params.dssr_enabled = true;
    const auto result = lunar_spprc::solve(model(), params);
    assert(result.telemetry.dssr_enabled);
    assert(result.telemetry.dssr_elementary_witness_returned);
    assert(!result.telemetry.dssr_relaxation_no_negative_certificate);
    assert(!result.routes.empty());
    for (const auto& route : result.routes) {
        std::vector<std::string> task_ids;
        for (const auto& sortie : route.sorties) {
            task_ids.insert(
                task_ids.end(), sortie.tasks.begin(), sortie.tasks.end());
        }
        std::ranges::sort(task_ids);
        assert(
            std::ranges::adjacent_find(task_ids) == task_ids.end());
    }
}

void verify_dssr_v2_returns_an_elementary_negative_batch() {
    auto params = lunar_spprc::SolveParams{};
    params.exact_proof = true;
    params.dssr_enabled = true;
    params.dssr_policy_version =
        "multi_sortie_counterexample_pressure_refinement_v2";
    params.dssr_negative_batch_target = 4;
    params.dssr_pressure_refinement_enabled = false;
    const auto result = lunar_spprc::solve(model(), params);
    assert(result.telemetry.dssr_enabled);
    assert(
        result.telemetry.dssr_policy_version ==
        "multi_sortie_counterexample_pressure_refinement_v2");
    assert(result.telemetry.dssr_elementary_witness_returned);
    assert(!result.telemetry.dssr_relaxation_no_negative_certificate);
    assert(!result.routes.empty());
    assert(result.routes.size() <= 4);
    assert(
        result.telemetry.dssr_elementary_batch_count ==
        result.routes.size());
    assert(
        result.telemetry.dssr_raw_solution_count >=
        result.routes.size());
    for (const auto& route : result.routes) {
        std::vector<std::string> task_ids;
        for (const auto& sortie : route.sorties) {
            task_ids.insert(
                task_ids.end(), sortie.tasks.begin(), sortie.tasks.end());
        }
        std::ranges::sort(task_ids);
        assert(
            std::ranges::adjacent_find(task_ids) == task_ids.end());
    }
}

void verify_dssr_v2_pressure_refinement_never_leaks_a_result() {
    auto params = lunar_spprc::SolveParams{};
    params.exact_proof = true;
    params.dssr_enabled = true;
    params.dssr_policy_version =
        "multi_sortie_counterexample_pressure_refinement_v2";
    params.dssr_negative_batch_target = 4;
    params.dssr_pressure_refinement_enabled = true;
    params.dssr_pressure_max_bucket_size = 1;
    params.dssr_pressure_max_candidate_checks =
        std::numeric_limits<std::size_t>::max();
    const auto result = lunar_spprc::solve(model(), params);
    assert(
        !result.telemetry.dssr_relaxation_no_negative_certificate);
    assert(
        result.telemetry.dssr_pressure_refinement_count ==
        model().tasks.size());
    assert(
        result.telemetry.dssr_pressure_abandoned_iteration_count >=
        result.telemetry.dssr_pressure_refinement_count);
    assert(
        result.telemetry.dssr_pressure_split_task_ids ==
        std::vector<std::string>({"a", "b"}));
    for (const auto& row : result.telemetry.dssr_iteration_trace) {
        if (!row.pressure_refinement_triggered) {
            continue;
        }
        assert(!row.negative_witness_found);
        assert(row.raw_solution_count == 0);
        assert(row.elementary_solution_count == 0);
        assert(row.non_elementary_solution_count == 0);
    }
}

void verify_ng_dssr_v3_returns_only_elementary_negative_routes() {
    auto params = lunar_spprc::SolveParams{};
    params.exact_proof = true;
    params.dssr_enabled = true;
    params.dssr_policy_version =
        "multi_sortie_ng_memory_counterexample_refinement_v3";
    params.dssr_negative_batch_target = 4;
    params.ng_dssr_initial_neighborhood_size = 1;
    params.completion_bound_enabled = true;
    params.subset_dominance_enabled = true;
    const auto result = lunar_spprc::solve(model(), params);
    assert(result.telemetry.dssr_enabled);
    assert(result.telemetry.ng_dssr_enabled);
    assert(
        result.telemetry.dssr_policy_version ==
        "multi_sortie_ng_memory_counterexample_refinement_v3");
    assert(result.telemetry.ng_dssr_initial_neighborhood_size == 1);
    assert(
        result.telemetry.ng_dssr_final_relation_count >=
        result.telemetry.ng_dssr_initial_relation_count);
    assert(!result.routes.empty());
    assert(result.routes.size() <= 4);
    assert(result.telemetry.completion_bound_evaluated_labels == 0);
    assert(result.telemetry.subset_dominance_candidate_checks == 0);
    for (const auto& route : result.routes) {
        std::vector<std::string> task_ids;
        for (const auto& sortie : route.sorties) {
            task_ids.insert(
                task_ids.end(), sortie.tasks.begin(), sortie.tasks.end());
        }
        std::ranges::sort(task_ids);
        assert(
            std::ranges::adjacent_find(task_ids) == task_ids.end());
    }
}

void verify_ng_dssr_v3_refines_local_cycle_relations_and_certifies() {
    auto value = model();
    value.structure_hash = "native_ng_dssr_refinement_structure_v1";
    value.cost_coefficient = 1.0;
    value.risk_coefficient = 0.0;
    value.completion_coefficient = 0.0;
    value.tasks[0].dual = 0.0;
    value.tasks[1].dual = 0.0;
    value.tasks[1].due_time = 0.5;
    value.cuts.push_back({
        .id = "sri",
        .kind = lunar_spprc::CutKind::SubsetRow,
        .task_mask = {0b11U},
        .divisor = 2,
        .dual = 100.0,
        .state_bit_offset = 0,
        .state_bit_width = 2,
        .max_overlap = 2,
    });

    lunar_spprc::SolveParams params;
    params.exact_proof = true;
    params.dssr_enabled = true;
    params.dssr_policy_version =
        "multi_sortie_ng_memory_counterexample_refinement_v3";
    params.dssr_negative_batch_target = 8;
    params.ng_dssr_initial_neighborhood_size = 1;
    const auto result = lunar_spprc::solve(value, params);
    assert(result.status == "complete");
    assert(result.search_exhaustive);
    assert(result.frontier_empty);
    assert(!result.labels_dropped);
    assert(result.routes.empty());
    assert(result.telemetry.ng_dssr_enabled);
    assert(result.telemetry.dssr_relaxation_no_negative_certificate);
    assert(result.telemetry.dssr_refinement_count >= 1);
    assert(result.telemetry.ng_dssr_relation_add_count >= 1);
    assert(result.telemetry.ng_dssr_forbidden_cycle_count >= 1);
    assert(
        result.telemetry.ng_dssr_final_relation_count >
        result.telemetry.ng_dssr_initial_relation_count);

    auto full_params = params;
    full_params.ng_dssr_initial_neighborhood_size =
        value.tasks.size();
    const auto full = lunar_spprc::solve(value, full_params);
    lunar_spprc::SolveParams p0_params;
    p0_params.exact_proof = true;
    const auto p0 = lunar_spprc::solve(value, p0_params);
    assert(full.status == p0.status);
    assert(full.search_exhaustive == p0.search_exhaustive);
    assert(full.frontier_empty == p0.frontier_empty);
    assert(full.routes.empty() == p0.routes.empty());
    assert(full.telemetry.ng_dssr_relation_add_count == 0);
}

}  // namespace

int main() {
    const auto native_build = lunar_spprc::build_info();
    assert(native_build.at("label_state_bytes") == "176");
    assert(native_build.at("journey_value_bytes") == "184");
    assert(native_build.at("journey_resource_bytes") == "184");
    assert(native_build.at("rcspp_label_object_bytes") == "64");
    assert(native_build.at("rcspp_outer_resource_object_bytes") == "96");
    assert(native_build.at("rcspp_journey_component_object_bytes") == "240");
    assert(
        native_build.at("label_memory_representation") ==
        "u16_counts_single_component_variant_compact_bucket_v2");
#if LUNAR_SPPRC_ENABLE_BIDIRECTIONAL_FEASIBILITY
    assert(
        native_build.at("bidirectional_feasibility_compiled") ==
        "true");
    verify_bidirectional_depot_join_is_exact_and_fail_closed();
#else
    assert(
        native_build.at("bidirectional_feasibility_compiled") ==
        "false");
#endif
    verify_upstream_pressure_false_complete_reproduction();
    verify_task_waiting_is_forbidden_but_depot_departure_may_shift();
    verify_qg2_reorders_only_within_rc_buckets();
    verify_qgr1_is_a_depth_residual_and_zero_score_matches_qd1();
    verify_qgr1_stratified_trace_reservoir_is_deterministic_and_exact_safe();
    verify_frontier_probe_switch_is_deterministic_and_exact_safe();
    verify_temporal_frontier_snapshots_are_single_request_and_exact_safe();
    verify_atomic_frontier_staging_contract();
    verify_counterfactual_prefix_is_truncated_route_free_and_deterministic();
    verify_qg2_500_randomized_exact_differentials();
    verify_dssr_refines_non_elementary_cut_witness_and_certifies();
    verify_dssr_returns_only_elementary_negative_witness();
    verify_dssr_v2_returns_an_elementary_negative_batch();
    verify_dssr_v2_pressure_refinement_never_leaks_a_result();
    if (
        lunar_spprc::build_info().at("ng_dssr_v3_compiled") ==
        "true"
    ) {
        verify_ng_dssr_v3_returns_only_elementary_negative_routes();
        verify_ng_dssr_v3_refines_local_cycle_relations_and_certifies();
    }
    lunar_spprc::SolveParams params;
    params.exact_proof = true;
    params.negative_epsilon = 1.0e-6;
    const auto negative = lunar_spprc::solve(model(), params);
    assert(negative.status == "complete");
    assert(negative.search_exhaustive);
    assert(!negative.labels_dropped);
    assert(!negative.routes.empty());
    assert(negative.telemetry.best_reduced_cost_events.empty());
    assert(!negative.telemetry.graph_cache_hit);
    bool found_multi_sortie = false;
    for (const auto& route : negative.routes) {
        if (route.sorties.size() == 2) {
            found_multi_sortie = true;
            assert(route.sorties[0].tasks.size() == 1);
            assert(route.sorties[1].tasks.size() == 1);
        }
    }
    assert(found_multi_sortie);

    auto harvest_params = params;
    harvest_params.exact_proof = false;
    harvest_params.harvest_target = 2;
    const auto harvest = lunar_spprc::solve(model(), harvest_params);
    assert(!harvest.routes.empty());
    assert(!harvest.telemetry.best_reduced_cost_events.empty());
    assert(
        harvest.telemetry.best_reduced_cost_event_count_total >=
        harvest.telemetry.best_reduced_cost_events.size());
    double previous_elapsed = -1.0;
    double previous_best = std::numeric_limits<double>::infinity();
    std::size_t previous_labels = 0;
    std::size_t previous_solutions = 0;
    for (const auto& event : harvest.telemetry.best_reduced_cost_events) {
        assert(event.elapsed_seconds >= previous_elapsed);
        assert(event.extended_labels >= previous_labels);
        assert(event.solution_count > previous_solutions);
        assert(event.discovered_reduced_cost == event.best_reduced_cost);
        assert(event.best_reduced_cost < previous_best);
        previous_elapsed = event.elapsed_seconds;
        previous_labels = event.extended_labels;
        previous_solutions = event.solution_count;
        previous_best = event.best_reduced_cost;
    }

    auto work_limited_params = harvest_params;
    work_limited_params.harvest_target = 1000;
    work_limited_params.harvest_max_processed_labels = 1;
    const auto work_limited_first =
        lunar_spprc::solve(model(), work_limited_params);
    const auto work_limited_second =
        lunar_spprc::solve(model(), work_limited_params);
    assert(work_limited_first.status == "max_phases");
    assert(!work_limited_first.search_exhaustive);
    assert(!work_limited_first.frontier_empty);
    assert(!work_limited_first.labels_dropped);
    assert(work_limited_first.telemetry.processed_labels == 1);
    assert(
        work_limited_second.status ==
        work_limited_first.status);
    assert(
        work_limited_second.telemetry.processed_labels ==
        work_limited_first.telemetry.processed_labels);
    assert(
        work_limited_second.telemetry.extended_labels ==
        work_limited_first.telemetry.extended_labels);

    auto subset_cut_model = model();
    subset_cut_model.cuts.push_back({
        .id = "sri",
        .kind = lunar_spprc::CutKind::SubsetRow,
        .task_mask = {0b11U},
        .divisor = 2,
        .dual = 5.0,
        .state_bit_offset = 0,
        .state_bit_width = 2,
        .max_overlap = 2,
    });
    const auto subset_cut = lunar_spprc::solve(subset_cut_model, params);
    assert(subset_cut.status == "complete");
    assert(!subset_cut.routes.empty());
    const auto baseline_best = std::ranges::min_element(
        negative.routes, {}, &lunar_spprc::Route::reduced_cost)->reduced_cost;
    const auto cut_best = std::ranges::min_element(
        subset_cut.routes, {}, &lunar_spprc::Route::reduced_cost)->reduced_cost;
    assert(std::abs((baseline_best - 5.0) - cut_best) < 1.0e-9);

    auto same_model = model();
    same_model.branch_decisions.push_back({
        .task_a = 0,
        .task_b = 1,
        .task_a_exists = true,
        .task_b_exists = true,
        .sense = lunar_spprc::BranchSense::SameJourney,
    });
    const auto same = lunar_spprc::solve(same_model, params);
    assert(same.status == "complete");
    assert(!same.routes.empty());
    for (const auto& route : same.routes) {
        std::size_t task_count = 0;
        for (const auto& sortie : route.sorties) {
            task_count += sortie.tasks.size();
        }
        assert(task_count == 2);
    }

    auto different_model = model();
    different_model.branch_decisions.push_back({
        .task_a = 0,
        .task_b = 1,
        .task_a_exists = true,
        .task_b_exists = true,
        .sense = lunar_spprc::BranchSense::DifferentJourney,
    });
    const auto different = lunar_spprc::solve(different_model, params);
    assert(different.status == "complete");
    assert(!different.routes.empty());
    for (const auto& route : different.routes) {
        std::size_t task_count = 0;
        for (const auto& sortie : route.sorties) {
            task_count += sortie.tasks.size();
        }
        assert(task_count == 1);
    }

    auto no_negative_model = model();
    for (auto& task : no_negative_model.tasks) {
        task.dual = 0.0;
    }
    const auto no_negative = lunar_spprc::solve(no_negative_model, params);
    assert(no_negative.status == "complete");
    assert(no_negative.search_exhaustive);
    assert(no_negative.frontier_empty);
    assert(no_negative.routes.empty());
    assert(no_negative.telemetry.graph_cache_hit);
    assert(no_negative.telemetry.graph_cache_size == 1);

    std::cout << "native lunar SPPRC smoke passed\n";
    return 0;
}
