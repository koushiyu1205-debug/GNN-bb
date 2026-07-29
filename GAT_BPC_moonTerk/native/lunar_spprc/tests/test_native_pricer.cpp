#include "lunar_spprc/native_pricer.hpp"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <iostream>

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

}  // namespace

int main() {
    verify_upstream_pressure_false_complete_reproduction();
    verify_task_waiting_is_forbidden_but_depot_departure_may_shift();
    verify_dssr_refines_non_elementary_cut_witness_and_certifies();
    verify_dssr_returns_only_elementary_negative_witness();
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
