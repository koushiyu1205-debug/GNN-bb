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

}  // namespace

int main() {
    verify_upstream_pressure_false_complete_reproduction();
    lunar_spprc::SolveParams params;
    params.exact_proof = true;
    params.negative_epsilon = 1.0e-6;
    const auto negative = lunar_spprc::solve(model(), params);
    assert(negative.status == "complete");
    assert(negative.search_exhaustive);
    assert(!negative.labels_dropped);
    assert(!negative.routes.empty());
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

    auto subset_cut_model = model();
    subset_cut_model.cuts.push_back({
        .id = "sri",
        .kind = lunar_spprc::CutKind::SubsetRow,
        .task_mask = {0b11U},
        .divisor = 2,
        .dual = 5.0,
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
