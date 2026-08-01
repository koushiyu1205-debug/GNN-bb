#include "lunar_spprc/native_pricer.hpp"

#if LUNAR_SPPRC_ENABLE_BIDIRECTIONAL_FEASIBILITY
#include "lunar_spprc/bidirectional_feasibility.hpp"
#endif

#include <bit>
#include <cmath>
#include <limits>
#include <string>
#include <unordered_map>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

namespace {

py::dict route_payload(const lunar_spprc::Route& route);

double optional_double(const py::dict& payload, const char* key, double fallback) {
    const auto name = py::str(key);
    if (!payload.contains(name)) {
        return fallback;
    }
    const auto value = payload[name];
    return value.is_none() ? fallback : py::cast<double>(value);
}

std::size_t optional_size_t(
    const py::dict& payload,
    const char* key,
    std::size_t fallback
) {
    const auto name = py::str(key);
    if (!payload.contains(name)) {
        return fallback;
    }
    const auto value = payload[name];
    return value.is_none() ? fallback : py::cast<std::size_t>(value);
}

bool optional_bool(
    const py::dict& payload,
    const char* key,
    bool fallback
) {
    const auto name = py::str(key);
    if (!payload.contains(name)) {
        return fallback;
    }
    const auto value = payload[name];
    return value.is_none() ? fallback : py::cast<bool>(value);
}

std::string optional_string(
    const py::dict& payload,
    const char* key,
    std::string fallback
) {
    const auto name = py::str(key);
    if (!payload.contains(name)) {
        return fallback;
    }
    const auto value = payload[name];
    return value.is_none() ? fallback : py::cast<std::string>(value);
}

lunar_spprc::Model parse_model(const py::dict& payload) {
    lunar_spprc::Model model;
    model.instance_id = py::cast<std::string>(payload["instance_id"]);
    model.structure_hash = py::cast<std::string>(payload["instance_hash"]);
    model.guidance_task_arc_enabled =
        py::cast<bool>(payload["guidance_task_arc_enabled"]);
    for (const auto item : py::cast<py::list>(payload["tasks"])) {
        const auto row = py::cast<py::dict>(item);
        model.tasks.push_back({
            .id = py::cast<std::string>(row["id"]),
            .index = py::cast<std::size_t>(row["index"]),
            .science_weight = py::cast<double>(row["science_weight"]),
            .demand = py::cast<double>(row["demand"]),
            .service_time = py::cast<double>(row["service_time"]),
            .service_energy = py::cast<double>(row["service_energy"]),
            .service_cost = py::cast<double>(row["service_cost"]),
            .ready_time = py::cast<double>(row["ready_time"]),
            .due_time = py::cast<double>(row["due_time"]),
            .local_shadow_score = py::cast<double>(row["local_shadow_score"]),
            .local_thermal_risk = py::cast<double>(row["local_thermal_risk"]),
            .dual = py::cast<double>(row["dual"]),
            .guidance_priority =
                model.guidance_task_arc_enabled
                    ? py::cast<double>(row["guidance_priority"])
                    : 0.0,
        });
    }
    for (const auto item : py::cast<py::list>(payload["arcs"])) {
        const auto row = py::cast<py::dict>(item);
        model.arcs.push_back({
            .source = py::cast<std::string>(row["source"]),
            .target = py::cast<std::string>(row["target"]),
            .path_type = py::cast<std::string>(row["path_type"]),
            .travel_time = py::cast<double>(row["travel_time"]),
            .energy = py::cast<double>(row["energy"]),
            .risk = py::cast<double>(row["risk"]),
            .distance = py::cast<double>(row["distance"]),
            .shadow = py::cast<double>(row["shadow"]),
            .guidance_priority =
                model.guidance_task_arc_enabled
                    ? py::cast<double>(row["guidance_priority"])
                    : 0.0,
        });
    }
    std::unordered_map<std::string, std::size_t> task_index_by_id;
    for (const auto& task : model.tasks) {
        task_index_by_id.emplace(task.id, task.index);
    }
    for (const auto item : py::cast<py::list>(payload["branch_decisions"])) {
        const auto row = py::cast<py::dict>(item);
        const auto task_a = py::cast<std::string>(row["task_a"]);
        const auto task_b = py::cast<std::string>(row["task_b"]);
        const auto sense = py::cast<std::string>(row["sense"]);
        if (sense != "same_journey" && sense != "different_journey") {
            throw std::invalid_argument("unsupported Ryan-Foster branch sense");
        }
        const auto a_it = task_index_by_id.find(task_a);
        const auto b_it = task_index_by_id.find(task_b);
        model.branch_decisions.push_back({
            .task_a = a_it == task_index_by_id.end() ? 0U : a_it->second,
            .task_b = b_it == task_index_by_id.end() ? 0U : b_it->second,
            .task_a_exists = a_it != task_index_by_id.end(),
            .task_b_exists = b_it != task_index_by_id.end(),
            .sense = sense == "same_journey"
                         ? lunar_spprc::BranchSense::SameJourney
                         : lunar_spprc::BranchSense::DifferentJourney,
        });
    }
    const auto cut_rows = py::cast<py::list>(payload["cuts"]);
    if (cut_rows.size() > 16U) {
        throw std::invalid_argument("native active cut count exceeds 16");
    }
    std::size_t cut_state_bit_offset = 0;
    for (const auto item : cut_rows) {
        const auto row = py::cast<py::dict>(item);
        const auto cut_type = py::cast<std::string>(row["cut_type"]);
        if (cut_type != "subset_row") {
            throw std::invalid_argument("native live-cut v1 supports subset_row only");
        }
        lunar_spprc::CutDefinition cut;
        cut.id = py::cast<std::string>(row["cut_id"]);
        cut.kind = lunar_spprc::CutKind::SubsetRow;
        cut.divisor = py::cast<std::size_t>(row["divisor"]);
        if (cut.divisor != 2U) {
            throw std::invalid_argument("native live-cut v1 supports divisor 2 only");
        }
        cut.dual = py::cast<double>(row["dual"]);
        cut.task_mask.assign((model.tasks.size() + 63U) / 64U, 0U);
        const auto cut_tasks = py::cast<py::list>(row["tasks"]);
        if (cut_tasks.size() != 3U && cut_tasks.size() != 5U) {
            throw std::invalid_argument("native live-cut v1 supports SRI-3 and SRI-5 only");
        }
        cut.state_bit_offset = static_cast<std::uint8_t>(cut_state_bit_offset);
        cut.state_bit_width =
            static_cast<std::uint8_t>(cut_tasks.size() == 3U ? 2U : 3U);
        cut.max_overlap = static_cast<std::uint8_t>(cut_tasks.size());
        cut_state_bit_offset += cut.state_bit_width;
        if (cut_state_bit_offset > 64U) {
            throw std::invalid_argument("native packed cut state exceeds 64 bits");
        }
        for (const auto task_value : cut_tasks) {
            const auto task_id = py::cast<std::string>(task_value);
            const auto found = task_index_by_id.find(task_id);
            if (found == task_index_by_id.end()) {
                throw std::invalid_argument("native cut references an unknown task");
            }
            cut.task_mask[found->second / 64U] |=
                (std::uint64_t{1} << (found->second % 64U));
        }
        std::size_t unique_cut_tasks = 0;
        for (const auto word : cut.task_mask) {
            unique_cut_tasks += std::popcount(word);
        }
        if (unique_cut_tasks != cut_tasks.size()) {
            throw std::invalid_argument("native cut task list contains duplicates");
        }
        model.cuts.push_back(std::move(cut));
    }
    model.max_tasks_per_trip = py::cast<std::size_t>(payload["max_tasks_per_trip"]);
    model.capacity = py::cast<double>(payload["capacity"]);
    model.energy_limit = py::cast<double>(payload["energy_limit"]);
    model.horizon = py::cast<double>(payload["horizon"]);
    model.dock_overhead = py::cast<double>(payload["dock_overhead"]);
    model.recharge_power = py::cast<double>(payload["recharge_power"]);
    model.shadow_limit = py::cast<double>(payload["shadow_limit"]);
    model.cost_coefficient = py::cast<double>(payload["weight_cost"]) /
                             py::cast<double>(payload["reference_cost"]);
    model.risk_coefficient = py::cast<double>(payload["weight_risk"]) /
                             py::cast<double>(payload["reference_risk"]);
    model.completion_coefficient = py::cast<double>(payload["weight_completion"]) /
                                   py::cast<double>(payload["reference_completion"]);
    model.fleet_dual = py::cast<double>(payload["fleet_dual"]);
    return model;
}

#if LUNAR_SPPRC_ENABLE_BIDIRECTIONAL_FEASIBILITY
std::vector<lunar_spprc::SortiePath> parse_sortie_paths(
    const py::dict& payload,
    const char* key
) {
    const auto name = py::str(key);
    if (!payload.contains(name)) {
        throw py::key_error(
            std::string("missing bidirectional route half: ") + key);
    }
    std::vector<lunar_spprc::SortiePath> result;
    for (const auto item : py::cast<py::list>(payload[name])) {
        const auto row = py::cast<py::dict>(item);
        result.push_back({
            .tasks =
                py::cast<std::vector<std::string>>(row["tasks"]),
            .path_types =
                py::cast<std::vector<std::string>>(row["path_types"]),
        });
    }
    return result;
}

py::dict bidirectional_feasibility_payload(const py::dict& payload) {
    const auto output = lunar_spprc::audit_bidirectional_depot_join(
        parse_model(payload),
        parse_sortie_paths(payload, "forward_sorties"),
        parse_sortie_paths(payload, "backward_sorties"));
    py::dict result;
    result["schema_version"] =
        "lunar_spprc.bidirectional_feasibility_probe.v1";
    result["policy_id"] =
        "p0v4_frozen_dual_depot_meet_max_plus_v1";
    result["status"] = output.status;
    result["feasible"] = output.feasible;
    result["task_sets_disjoint"] = output.task_sets_disjoint;
    result["suffix_boundary_feasible"] =
        output.suffix_boundary_feasible;
    result["branch_feasible"] = output.branch_feasible;
    result["static_objective_finite"] =
        output.static_objective_finite;
    result["can_certify_no_negative"] = false;
    result["certificate_scope"] =
        "DIAGNOSTIC_BIDIRECTIONAL_FEASIBILITY_ONLY";
    result["prefix_end_time"] = output.prefix_end_time;
    result["suffix_latest_input_time"] =
        output.suffix_latest_input_time;
    result["journey_end_time"] = output.journey_end_time;
    result["raw_operating_cost"] = output.raw_operating_cost;
    result["raw_risk"] = output.raw_risk;
    result["raw_weighted_completion"] =
        output.raw_weighted_completion;
    result["task_dual_reward"] = output.task_dual_reward;
    result["cut_dual_reward"] = output.cut_dual_reward;
    result["true_reduced_cost"] = output.true_reduced_cost;
    result["task_count"] = output.task_count;
    result["sortie_count"] = output.sortie_count;
    result["build_info"] = lunar_spprc::build_info();
    return result;
}

py::dict bidirectional_backward_frontier_payload(
    const py::dict& payload
) {
    lunar_spprc::BidirectionalBackwardProbeParams params;
    params.max_partial_states = optional_size_t(
        payload,
        "bidirectional_max_partial_states",
        params.max_partial_states);
    params.max_completed_sorties = optional_size_t(
        payload,
        "bidirectional_max_completed_sorties",
        params.max_completed_sorties);
    params.timeout_seconds = optional_double(
        payload,
        "bidirectional_wall_time_limit_sec",
        params.timeout_seconds);
    const auto output =
        lunar_spprc::probe_bidirectional_backward_frontier(
            parse_model(payload),
            params);
    py::dict result;
    result["schema_version"] =
        "lunar_spprc.bidirectional_backward_frontier_probe.v1";
    result["policy_id"] =
        "p0v4_frozen_dual_depot_meet_max_plus_v1";
    result["scope"] =
        "REVERSE_SORTIE_SEED_FRONTIER_DIAGNOSTIC_ONLY";
    result["status"] = output.status;
    result["search_exhaustive"] = output.search_exhaustive;
    result["frontier_empty"] = output.frontier_empty;
    result["can_certify_no_negative"] = false;
    result["processed_partial_states"] =
        output.processed_partial_states;
    result["generated_partial_states"] =
        output.generated_partial_states;
    result["resource_pruned_partial_states"] =
        output.resource_pruned_partial_states;
    result["duplicate_task_pruned_extensions"] =
        output.duplicate_task_pruned_extensions;
    result["completed_sortie_candidates"] =
        output.completed_sortie_candidates;
    result["feasible_backward_sortie_seeds"] =
        output.feasible_backward_sortie_seeds;
    result["infeasible_completed_sorties"] =
        output.infeasible_completed_sorties;
    result["max_frontier_size"] = output.max_frontier_size;
    result["wall_time_seconds"] = output.wall_time_seconds;
    result["partial_states_by_task_depth"] =
        output.partial_states_by_task_depth;
    result["feasible_sorties_by_task_depth"] =
        output.feasible_sorties_by_task_depth;
    result["build_info"] = lunar_spprc::build_info();
    return result;
}

py::dict bidirectional_task_meet_frontier_payload(
    const py::dict& payload
) {
    lunar_spprc::BidirectionalTaskMeetProbeParams params;
    params.max_partial_states_per_direction = optional_size_t(
        payload,
        "bidirectional_max_partial_states_per_direction",
        params.max_partial_states_per_direction);
    params.max_join_checks = optional_size_t(
        payload,
        "bidirectional_max_join_checks",
        params.max_join_checks);
    params.timeout_seconds = optional_double(
        payload,
        "bidirectional_wall_time_limit_sec",
        params.timeout_seconds);
    const auto output =
        lunar_spprc::probe_bidirectional_task_meet_frontier(
            parse_model(payload),
            params);
    py::dict result;
    result["schema_version"] =
        "lunar_spprc.bidirectional_task_meet_frontier_probe.v1";
    result["policy_id"] =
        "p0v4_frozen_dual_task_meet_max_plus_v1";
    result["scope"] =
        "TASK_LEVEL_SORTIE_MEET_DIAGNOSTIC_ONLY";
    result["status"] = output.status;
    result["forward_generation_exhaustive"] =
        output.forward_generation_exhaustive;
    result["backward_generation_exhaustive"] =
        output.backward_generation_exhaustive;
    result["join_exhaustive"] = output.join_exhaustive;
    result["can_certify_no_negative"] = false;
    result["forward_generated_states"] =
        output.forward_generated_states;
    result["backward_generated_states"] =
        output.backward_generated_states;
    result["forward_resource_pruned_states"] =
        output.forward_resource_pruned_states;
    result["backward_resource_pruned_states"] =
        output.backward_resource_pruned_states;
    result["forward_duplicate_task_pruned_extensions"] =
        output.forward_duplicate_task_pruned_extensions;
    result["backward_duplicate_task_pruned_extensions"] =
        output.backward_duplicate_task_pruned_extensions;
    result["join_pair_checks"] = output.join_pair_checks;
    result["disjoint_join_pairs"] =
        output.disjoint_join_pairs;
    result["resource_compatible_join_pairs"] =
        output.resource_compatible_join_pairs;
    result["feasible_joined_sorties"] =
        output.feasible_joined_sorties;
    result["infeasible_joined_sorties"] =
        output.infeasible_joined_sorties;
    result["distinct_task_set_count"] =
        output.distinct_task_set_count;
    result["task_set_duplicate_sortie_count"] =
        output.task_set_duplicate_sortie_count;
    result["nondominated_sortie_count"] =
        output.nondominated_sortie_count;
    result["dominated_sortie_count"] =
        output.dominated_sortie_count;
    result["max_variants_per_task_set"] =
        output.max_variants_per_task_set;
    result["sortie_dominance_candidate_checks"] =
        output.sortie_dominance_candidate_checks;
    result["wall_time_seconds"] = output.wall_time_seconds;
    result["forward_states_by_task_depth"] =
        output.forward_states_by_task_depth;
    result["backward_states_by_task_depth"] =
        output.backward_states_by_task_depth;
    result["feasible_joined_sorties_by_task_count"] =
        output.feasible_joined_sorties_by_task_count;
    result["nondominated_sorties_by_task_count"] =
        output.nondominated_sorties_by_task_count;
    result["build_info"] = lunar_spprc::build_info();
    return result;
}

py::dict bidirectional_journey_frontier_payload(
    const py::dict& payload
) {
    lunar_spprc::BidirectionalTaskMeetProbeParams sortie_params;
    sortie_params.max_partial_states_per_direction = optional_size_t(
        payload,
        "bidirectional_max_partial_states_per_direction",
        sortie_params.max_partial_states_per_direction);
    sortie_params.max_join_checks = optional_size_t(
        payload,
        "bidirectional_max_join_checks",
        sortie_params.max_join_checks);
    sortie_params.timeout_seconds = optional_double(
        payload,
        "bidirectional_sortie_wall_time_limit_sec",
        sortie_params.timeout_seconds);
    lunar_spprc::BidirectionalJourneyProbeParams journey_params;
    journey_params.max_labels = optional_size_t(
        payload,
        "bidirectional_max_journey_labels",
        journey_params.max_labels);
    journey_params.max_extension_checks = optional_size_t(
        payload,
        "bidirectional_max_journey_extension_checks",
        journey_params.max_extension_checks);
    journey_params.negative_route_target = optional_size_t(
        payload,
        "bidirectional_negative_route_target",
        journey_params.negative_route_target);
    journey_params.negative_epsilon = optional_double(
        payload,
        "negative_eps",
        journey_params.negative_epsilon);
    journey_params.timeout_seconds = optional_double(
        payload,
        "bidirectional_journey_wall_time_limit_sec",
        journey_params.timeout_seconds);
    journey_params.immediate_subset_dominance_enabled =
        optional_bool(
            payload,
            "bidirectional_immediate_subset_dominance_enabled",
            journey_params.immediate_subset_dominance_enabled);
    const auto output =
        lunar_spprc::probe_bidirectional_journey_frontier(
            parse_model(payload),
            sortie_params,
            journey_params);
    py::dict result;
    result["schema_version"] =
        "lunar_spprc.bidirectional_journey_frontier_probe.v1";
    result["policy_id"] =
        "p0v4_frozen_dual_task_meet_journey_label_v1";
    result["scope"] =
        "FROZEN_DUAL_JOURNEY_FRONTIER_DIAGNOSTIC_ONLY";
    result["status"] = output.status;
    result["search_exhaustive"] = output.search_exhaustive;
    result["frontier_empty"] = output.frontier_empty;
    result["can_certify_no_negative"] = false;
    result["sortie_pool_size"] = output.sortie_pool_size;
    result["generated_labels"] = output.generated_labels;
    result["processed_labels"] = output.processed_labels;
    result["dominated_labels"] = output.dominated_labels;
    result["subset_dominance_candidate_checks"] =
        output.subset_dominance_candidate_checks;
    result["subset_dominated_labels"] =
        output.subset_dominated_labels;
    result["removed_existing_labels"] =
        output.removed_existing_labels;
    result["extension_checks"] = output.extension_checks;
    result["task_overlap_rejected_extensions"] =
        output.task_overlap_rejected_extensions;
    result["branch_rejected_extensions"] =
        output.branch_rejected_extensions;
    result["time_rejected_extensions"] =
        output.time_rejected_extensions;
    result["accepted_extensions"] =
        output.accepted_extensions;
    result["negative_terminal_label_count"] =
        output.negative_terminal_label_count;
    result["max_frontier_size"] = output.max_frontier_size;
    result["best_true_reduced_cost"] =
        std::isfinite(output.best_true_reduced_cost)
            ? py::cast(output.best_true_reduced_cost)
            : py::none();
    result["first_negative_wall_time_seconds"] =
        std::isfinite(output.first_negative_wall_time_seconds)
            ? py::cast(output.first_negative_wall_time_seconds)
            : py::none();
    result["negative_target_wall_time_seconds"] =
        std::isfinite(output.negative_target_wall_time_seconds)
            ? py::cast(output.negative_target_wall_time_seconds)
            : py::none();
    result["wall_time_seconds"] = output.wall_time_seconds;
    result["accepted_labels_by_task_count"] =
        output.accepted_labels_by_task_count;
    result["build_info"] = lunar_spprc::build_info();
    return result;
}

py::dict bidirectional_midpoint_meet_payload(
    const py::dict& payload
) {
    lunar_spprc::BidirectionalTaskMeetProbeParams sortie_params;
    sortie_params.max_partial_states_per_direction = optional_size_t(
        payload,
        "bidirectional_max_partial_states_per_direction",
        sortie_params.max_partial_states_per_direction);
    sortie_params.max_join_checks = optional_size_t(
        payload,
        "bidirectional_max_join_checks",
        sortie_params.max_join_checks);
    sortie_params.timeout_seconds = optional_double(
        payload,
        "bidirectional_sortie_wall_time_limit_sec",
        sortie_params.timeout_seconds);
    lunar_spprc::BidirectionalMidpointProbeParams midpoint_params;
    midpoint_params.max_forward_labels = optional_size_t(
        payload,
        "bidirectional_midpoint_max_forward_labels",
        midpoint_params.max_forward_labels);
    midpoint_params.max_backward_labels = optional_size_t(
        payload,
        "bidirectional_midpoint_max_backward_labels",
        midpoint_params.max_backward_labels);
    midpoint_params.max_crossing_labels = optional_size_t(
        payload,
        "bidirectional_midpoint_max_crossing_labels",
        midpoint_params.max_crossing_labels);
    midpoint_params.max_extension_checks = optional_size_t(
        payload,
        "bidirectional_midpoint_max_extension_checks",
        midpoint_params.max_extension_checks);
    midpoint_params.max_join_checks = optional_size_t(
        payload,
        "bidirectional_midpoint_max_join_checks",
        midpoint_params.max_join_checks);
    midpoint_params.max_returned_negative_routes = optional_size_t(
        payload,
        "bidirectional_midpoint_max_returned_negative_routes",
        midpoint_params.max_returned_negative_routes);
    midpoint_params.split_fraction = optional_double(
        payload,
        "bidirectional_midpoint_split_fraction",
        midpoint_params.split_fraction);
    midpoint_params.negative_epsilon = optional_double(
        payload,
        "negative_eps",
        midpoint_params.negative_epsilon);
    midpoint_params.timeout_seconds = optional_double(
        payload,
        "bidirectional_midpoint_wall_time_limit_sec",
        midpoint_params.timeout_seconds);
    const auto output =
        lunar_spprc::probe_bidirectional_midpoint_journey_meet(
            parse_model(payload),
            sortie_params,
            midpoint_params);
    py::dict result;
    result["schema_version"] =
        "lunar_spprc.bidirectional_midpoint_journey_meet.v1";
    result["policy_id"] =
        "p0v4_frozen_dual_depot_midpoint_meet_v1";
    result["scope"] =
        "JOURNEY_LEVEL_FORWARD_BACKWARD_MEET_DIAGNOSTIC_ONLY";
    result["status"] = output.status;
    result["forward_exhaustive"] = output.forward_exhaustive;
    result["backward_exhaustive"] =
        output.backward_exhaustive;
    result["crossing_exhaustive"] =
        output.crossing_exhaustive;
    result["join_exhaustive"] = output.join_exhaustive;
    result["search_exhaustive"] = output.search_exhaustive;
    result["can_certify_no_negative"] = false;
    result["sortie_pool_size"] = output.sortie_pool_size;
    result["forward_generated_labels"] =
        output.forward_generated_labels;
    result["forward_processed_labels"] =
        output.forward_processed_labels;
    result["backward_generated_labels"] =
        output.backward_generated_labels;
    result["backward_processed_labels"] =
        output.backward_processed_labels;
    result["crossing_generated_labels"] =
        output.crossing_generated_labels;
    result["crossing_dominated_labels"] =
        output.crossing_dominated_labels;
    result["forward_dominated_labels"] =
        output.forward_dominated_labels;
    result["backward_dominated_labels"] =
        output.backward_dominated_labels;
    result["active_forward_labels"] =
        output.active_forward_labels;
    result["active_backward_labels"] =
        output.active_backward_labels;
    result["active_crossing_labels"] =
        output.active_crossing_labels;
    result["unindexed_active_join_pairs"] =
        output.unindexed_active_join_pairs;
    result["time_index_candidate_join_pairs"] =
        output.time_index_candidate_join_pairs;
    result["time_index_pruned_join_pairs"] =
        output.time_index_pruned_join_pairs;
    result["extension_checks"] = output.extension_checks;
    result["join_checks"] = output.join_checks;
    result["disjoint_join_checks"] =
        output.disjoint_join_checks;
    result["time_compatible_joins"] =
        output.time_compatible_joins;
    result["terminal_route_count"] =
        output.terminal_route_count;
    result["negative_terminal_route_count"] =
        output.negative_terminal_route_count;
    py::list routes;
    for (const auto& route : output.negative_routes) {
        routes.append(route_payload(route));
    }
    result["routes"] = std::move(routes);
    result["returned_negative_route_count"] =
        output.negative_routes.size();
    result["max_forward_frontier_size"] =
        output.max_forward_frontier_size;
    result["max_backward_frontier_size"] =
        output.max_backward_frontier_size;
    result["split_time"] = output.split_time;
    result["best_true_reduced_cost"] =
        std::isfinite(output.best_true_reduced_cost)
            ? py::cast(output.best_true_reduced_cost)
            : py::none();
    result["first_negative_wall_time_seconds"] =
        std::isfinite(output.first_negative_wall_time_seconds)
            ? py::cast(output.first_negative_wall_time_seconds)
            : py::none();
    result["wall_time_seconds"] = output.wall_time_seconds;
    result["build_info"] = lunar_spprc::build_info();
    return result;
}
#endif

lunar_spprc::SolveParams parse_params(const py::dict& payload) {
    lunar_spprc::SolveParams params;
    params.exact_proof = py::cast<std::string>(payload["mode"]) == "exact_proof";
    params.harvest_target = py::cast<std::size_t>(payload["harvest_target"]);
    params.exact_negative_escape_enabled = optional_bool(
        payload, "exact_negative_escape_enabled", false);
    params.exact_admission_batch_size = optional_size_t(
        payload, "exact_admission_batch_size", params.harvest_target);
    params.exact_raw_negative_pool_size = optional_size_t(
        payload,
        "exact_raw_negative_pool_size",
        params.exact_admission_batch_size * 4U);
    params.exact_negative_escape_policy_id = optional_string(
        payload,
        "exact_negative_escape_policy_id",
        "diverse_raw_4x_then_p0v4_selector_v1");
    params.harvest_max_processed_labels = optional_size_t(
        payload, "harvest_max_processed_labels", 0U);
    params.timeout_seconds = optional_double(payload, "wall_time_limit_sec",
                                             std::numeric_limits<double>::infinity());
    params.max_memory_gb = py::cast<double>(payload["memory_limit_gb"]);
    params.negative_epsilon = py::cast<double>(payload["negative_eps"]);
    params.dominance_epsilon = py::cast<double>(payload["dominance_eps"]);
    params.resource_epsilon = py::cast<double>(payload["resource_eps"]);
    params.graph_cache_entries = py::cast<std::size_t>(payload["graph_cache_entries"]);
    params.completion_bound_enabled = py::cast<bool>(payload["completion_bound_enabled"]);
    params.subset_dominance_enabled = py::cast<bool>(payload["subset_dominance_enabled"]);
    params.proof_queue_potential_trace_enabled =
        optional_bool(payload, "proof_queue_potential_trace_enabled", false);
    params.proof_queue_guidance_bucket_width =
        optional_double(payload, "proof_queue_guidance_bucket_width", 0.01);
    params.dssr_enabled =
        optional_bool(payload, "dssr_enabled", false);
    params.dssr_policy_version = py::cast<std::string>(
        payload["dssr_policy_version"]);
    params.dssr_negative_batch_target = optional_size_t(
        payload, "dssr_negative_batch_target", 16U);
    params.dssr_pressure_refinement_enabled = optional_bool(
        payload, "dssr_pressure_refinement_enabled", false);
    params.dssr_pressure_max_bucket_size = optional_size_t(
        payload, "dssr_pressure_max_bucket_size", 8192U);
    params.dssr_pressure_max_candidate_checks = optional_size_t(
        payload,
        "dssr_pressure_max_candidate_checks",
        200000000U);
    params.ng_dssr_initial_neighborhood_size = optional_size_t(
        payload, "ng_dssr_initial_neighborhood_size", 10U);
    const auto proof_queue_policy =
        py::cast<std::string>(payload["proof_queue_policy_id"]);
    if (proof_queue_policy == "Q0") {
        params.proof_queue_policy =
            lunar_spprc::ProofQueuePolicy::Q0PartialCost;
    } else if (proof_queue_policy == "QC0") {
        params.proof_queue_policy =
            lunar_spprc::ProofQueuePolicy::QC0CachedPartialCost;
    } else if (proof_queue_policy == "QD1") {
        params.proof_queue_policy =
            lunar_spprc::ProofQueuePolicy::QD1DeeperFirst;
    } else if (proof_queue_policy == "QB1") {
        params.proof_queue_policy =
            lunar_spprc::ProofQueuePolicy::QB1OptimisticCompletion;
    } else if (proof_queue_policy == "QG1") {
        params.proof_queue_policy =
            lunar_spprc::ProofQueuePolicy::QG1GuidancePotential;
    } else {
        throw py::value_error(
            "unsupported proof_queue_policy_id: " + proof_queue_policy);
    }
    return params;
}

py::dict route_payload(const lunar_spprc::Route& route) {
    py::list sorties;
    for (const auto& sortie : route.sorties) {
        py::dict row;
        row["tasks"] = sortie.tasks;
        row["path_types"] = sortie.path_types;
        sorties.append(std::move(row));
    }
    py::dict payload;
    payload["reduced_cost"] = route.reduced_cost;
    payload["arc_ids"] = route.arc_ids;
    payload["sorties"] = std::move(sorties);
    return payload;
}

py::dict solve_payload(const py::dict& payload) {
    const auto output = lunar_spprc::solve(parse_model(payload), parse_params(payload));
    py::list routes;
    for (const auto& route : output.routes) {
        routes.append(route_payload(route));
    }
    py::dict telemetry;
    telemetry["processed_labels"] = output.telemetry.processed_labels;
    telemetry["extended_labels"] = output.telemetry.extended_labels;
    telemetry["dominated_labels"] = output.telemetry.dominated_labels;
    telemetry["dominance_candidate_checks"] = output.telemetry.dominance_candidate_checks;
    telemetry["max_visited_bucket_size"] = output.telemetry.max_visited_bucket_size;
    telemetry["solution_count"] = output.telemetry.solution_count;
    telemetry["negative_escape_enabled"] =
        output.telemetry.negative_escape_enabled;
    telemetry["negative_escape_triggered"] =
        output.telemetry.negative_escape_triggered;
    telemetry["exact_admission_batch_size"] =
        output.telemetry.exact_admission_batch_size;
    telemetry["exact_raw_negative_pool_size"] =
        output.telemetry.exact_raw_negative_pool_size;
    telemetry["raw_unique_negative_count"] =
        output.telemetry.raw_unique_negative_count;
    telemetry["negative_escape_policy_id"] =
        output.telemetry.negative_escape_policy_id;
    telemetry["negative_escape_termination_reason"] =
        output.telemetry.negative_escape_termination_reason;
    telemetry["memory_pressure_triggered"] = output.telemetry.memory_pressure_triggered;
    telemetry["graph_cache_hit"] = output.telemetry.graph_cache_hit;
    telemetry["graph_cache_size"] = output.telemetry.graph_cache_size;
    telemetry["graph_cache_build_count"] = output.telemetry.graph_cache_build_count;
    telemetry["graph_cache_hit_count"] = output.telemetry.graph_cache_hit_count;
    telemetry["completion_bound_evaluated_labels"] =
        output.telemetry.completion_bound_evaluated_labels;
    telemetry["completion_bound_pruned_labels"] =
        output.telemetry.completion_bound_pruned_labels;
    telemetry["completion_bound_enabled"] =
        output.telemetry.completion_bound_evaluated_labels > 0;
    telemetry["subset_dominance_key_lookups"] =
        output.telemetry.subset_dominance_key_lookups;
    telemetry["subset_dominance_nonempty_buckets"] =
        output.telemetry.subset_dominance_nonempty_buckets;
    telemetry["subset_dominance_summary_skipped_buckets"] =
        output.telemetry.subset_dominance_summary_skipped_buckets;
    telemetry["subset_dominance_candidate_checks"] =
        output.telemetry.subset_dominance_candidate_checks;
    telemetry["subset_dominance_rejected_labels"] =
        output.telemetry.subset_dominance_rejected_labels;
    telemetry["extension_wall_time_seconds"] = output.telemetry.extension_wall_time_seconds;
    telemetry["dominance_wall_time_seconds"] = output.telemetry.dominance_wall_time_seconds;
    telemetry["wall_time_seconds"] = output.telemetry.wall_time_seconds;
    telemetry["proof_queue_policy_id"] =
        py::cast<std::string>(payload["proof_queue_policy_id"]);
    py::list best_reduced_cost_events;
    for (const auto& event : output.telemetry.best_reduced_cost_events) {
        py::dict row;
        row["elapsed_seconds"] = event.elapsed_seconds;
        row["extended_labels"] = event.extended_labels;
        row["solution_count"] = event.solution_count;
        row["discovered_reduced_cost"] = event.discovered_reduced_cost;
        row["best_reduced_cost"] = event.best_reduced_cost;
        best_reduced_cost_events.append(std::move(row));
    }
    telemetry["best_reduced_cost_event_schema"] =
        "lunar_spprc.best_reduced_cost_events.v1";
    telemetry["best_reduced_cost_events"] =
        std::move(best_reduced_cost_events);
    telemetry["best_reduced_cost_event_count_total"] =
        output.telemetry.best_reduced_cost_event_count_total;
    telemetry["best_reduced_cost_events_truncated"] =
        output.telemetry.best_reduced_cost_events_truncated;
    telemetry["proof_queue_potential_trace_enabled"] =
        output.telemetry.proof_queue_potential_trace_enabled;
    py::list proof_queue_potential_trace;
    const auto tasks = py::cast<py::list>(payload["tasks"]);
    for (const auto& row : output.telemetry.proof_queue_potential_trace) {
        py::dict trace_row;
        trace_row["task_index"] = row.task_index;
        trace_row["task_id"] = py::cast<py::dict>(tasks[row.task_index])["id"];
        trace_row["incoming_evaluated"] = row.incoming_evaluated;
        trace_row["incoming_rejected"] = row.incoming_rejected;
        trace_row["existing_dominator_wins"] = row.existing_dominator_wins;
        trace_row["accepted_removed_existing"] =
            row.accepted_removed_existing;
        trace_row["removed_as_existing"] = row.removed_as_existing;
        proof_queue_potential_trace.append(std::move(trace_row));
    }
    telemetry["proof_queue_potential_trace"] =
        std::move(proof_queue_potential_trace);
    py::list proof_queue_arc_potential_trace;
    const auto arcs = py::cast<py::list>(payload["arcs"]);
    for (const auto& row : output.telemetry.proof_queue_arc_potential_trace) {
        py::dict trace_row;
        const auto arc = py::cast<py::dict>(arcs[row.task_index]);
        trace_row["model_arc_index"] = row.task_index;
        trace_row["source"] = arc["source"];
        trace_row["target"] = arc["target"];
        trace_row["path_type"] = arc["path_type"];
        trace_row["incoming_evaluated"] = row.incoming_evaluated;
        trace_row["incoming_rejected"] = row.incoming_rejected;
        trace_row["existing_dominator_wins"] = row.existing_dominator_wins;
        trace_row["accepted_removed_existing"] =
            row.accepted_removed_existing;
        trace_row["removed_as_existing"] = row.removed_as_existing;
        proof_queue_arc_potential_trace.append(std::move(trace_row));
    }
    telemetry["proof_queue_arc_potential_trace"] =
        std::move(proof_queue_arc_potential_trace);
    telemetry["dssr_enabled"] = output.telemetry.dssr_enabled;
    telemetry["dssr_policy_version"] =
        output.telemetry.dssr_policy_version;
    telemetry["dssr_iteration_count"] =
        output.telemetry.dssr_iteration_count;
    telemetry["dssr_refinement_count"] =
        output.telemetry.dssr_refinement_count;
    telemetry["dssr_initial_critical_task_count"] =
        output.telemetry.dssr_initial_critical_task_count;
    telemetry["dssr_final_critical_task_count"] =
        output.telemetry.dssr_final_critical_task_count;
    telemetry["dssr_repeated_witness_count"] =
        output.telemetry.dssr_repeated_witness_count;
    telemetry["dssr_elementary_witness_returned"] =
        output.telemetry.dssr_elementary_witness_returned;
    telemetry["dssr_relaxation_no_negative_certificate"] =
        output.telemetry.dssr_relaxation_no_negative_certificate;
    telemetry["dssr_elementary_batch_count"] =
        output.telemetry.dssr_elementary_batch_count;
    telemetry["dssr_raw_solution_count"] =
        output.telemetry.dssr_raw_solution_count;
    telemetry["dssr_pressure_refinement_count"] =
        output.telemetry.dssr_pressure_refinement_count;
    telemetry["dssr_pressure_split_task_ids"] =
        output.telemetry.dssr_pressure_split_task_ids;
    telemetry["dssr_pressure_abandoned_iteration_count"] =
        output.telemetry.dssr_pressure_abandoned_iteration_count;
    telemetry["dssr_max_bucket_size"] =
        output.telemetry.dssr_max_bucket_size;
    telemetry["dssr_dominance_candidate_checks"] =
        output.telemetry.dssr_dominance_candidate_checks;
    telemetry["ng_dssr_enabled"] =
        output.telemetry.ng_dssr_enabled;
    telemetry["ng_dssr_initial_neighborhood_size"] =
        output.telemetry.ng_dssr_initial_neighborhood_size;
    telemetry["ng_dssr_initial_relation_count"] =
        output.telemetry.ng_dssr_initial_relation_count;
    telemetry["ng_dssr_final_relation_count"] =
        output.telemetry.ng_dssr_final_relation_count;
    telemetry["ng_dssr_relation_add_count"] =
        output.telemetry.ng_dssr_relation_add_count;
    telemetry["ng_dssr_forbidden_cycle_count"] =
        output.telemetry.ng_dssr_forbidden_cycle_count;
    telemetry["ng_dssr_full_elementary_fallback_count"] =
        output.telemetry.ng_dssr_full_elementary_fallback_count;
    py::list dssr_iteration_trace;
    for (const auto& row : output.telemetry.dssr_iteration_trace) {
        py::dict trace_row;
        trace_row["iteration"] = row.iteration;
        trace_row["critical_task_count_before"] =
            row.critical_task_count_before;
        trace_row["repeated_task_count"] = row.repeated_task_count;
        trace_row["processed_labels"] = row.processed_labels;
        trace_row["extended_labels"] = row.extended_labels;
        trace_row["dominated_labels"] = row.dominated_labels;
        trace_row["max_visited_bucket_size"] =
            row.max_visited_bucket_size;
        trace_row["wall_time_seconds"] = row.wall_time_seconds;
        trace_row["status"] = row.status;
        trace_row["search_exhaustive"] = row.search_exhaustive;
        trace_row["frontier_empty"] = row.frontier_empty;
        trace_row["labels_dropped"] = row.labels_dropped;
        trace_row["negative_witness_found"] =
            row.negative_witness_found;
        trace_row["witness_elementary"] = row.witness_elementary;
        trace_row["raw_solution_count"] = row.raw_solution_count;
        trace_row["elementary_solution_count"] =
            row.elementary_solution_count;
        trace_row["non_elementary_solution_count"] =
            row.non_elementary_solution_count;
        trace_row["pressure_refinement_triggered"] =
            row.pressure_refinement_triggered;
        trace_row["pressure_split_task_id"] =
            row.pressure_split_task_id;
        trace_row["ng_relation_count_before"] =
            row.ng_relation_count_before;
        trace_row["ng_relation_add_count"] =
            row.ng_relation_add_count;
        trace_row["ng_forbidden_cycle_count"] =
            row.ng_forbidden_cycle_count;
        dssr_iteration_trace.append(std::move(trace_row));
    }
    telemetry["dssr_iteration_trace"] =
        std::move(dssr_iteration_trace);

    py::dict result;
    result["status"] = output.status;
    result["routes"] = std::move(routes);
    result["search_exhaustive"] = output.search_exhaustive;
    result["frontier_empty"] = output.frontier_empty;
    result["labels_dropped"] = output.labels_dropped;
    result["best_found_rc"] = output.routes.empty()
                                  ? py::none()
                                  : py::cast(output.routes.front().reduced_cost);
    result["unexplored_rc_lower_bound"] = py::none();
    result["certificate_blockers"] = py::list();
    result["telemetry"] = std::move(telemetry);
    result["build_info"] = lunar_spprc::build_info();
    py::dict bindings;
    for (const auto* key : {
             "instance_hash",
             "config_hash",
             "engine_hash",
             "service_timing_policy_id",
             "exact_negative_escape_enabled",
             "exact_admission_batch_size",
             "exact_raw_negative_pool_size",
             "exact_negative_escape_policy_id",
             "dssr_enabled",
             "dssr_policy_version",
             "dssr_negative_batch_target",
             "dssr_pressure_refinement_enabled",
             "dssr_pressure_max_bucket_size",
             "dssr_pressure_max_candidate_checks",
             "ng_dssr_initial_neighborhood_size",
             "canonical_solve_binding_v2",
             "canonical_solve_binding_v2_schema",
             "canonical_solve_binding_v2_hash",
             "dual_binding_hash",
             "branch_context_hash",
             "objective_mode",
             "rmp_iteration_id",
             "active_cut_context_hash",
             "active_cut_count",
             "pricing_cut_context_hash",
             "pricing_cut_count",
             "cut_dual_projection_enabled",
             "cut_dual_projection_schema_version",
             "cut_lineage_hash",
             "live_cut_policy_hash",
             "cut_state_schema_version",
             "separator_policy_version",
             "negative_eps",
             "guidance_mode",
             "guidance_effective_mode",
             "guidance_binding_hash",
             "guidance_task_arc_enabled",
             "legal_task_universe_hash_before_sort",
             "legal_arc_universe_hash_before_sort",
             "guidance_native_install_sec",
         }) {
        bindings[py::str(key)] = payload[py::str(key)];
    }
    result["request_bindings"] = std::move(bindings);
    return result;
}

}  // namespace

PYBIND11_MODULE(lunar_spprc_native, module) {
    module.doc() = "Exact-safe lunar multi-sortie SPPRC extension";
    module.def("solve", &solve_payload, py::arg("request"));
    module.def("build_info", &lunar_spprc::build_info);
#if LUNAR_SPPRC_ENABLE_BIDIRECTIONAL_FEASIBILITY
    module.def(
        "bidirectional_feasibility_probe",
        &bidirectional_feasibility_payload,
        py::arg("request"));
    module.def(
        "bidirectional_backward_frontier_probe",
        &bidirectional_backward_frontier_payload,
        py::arg("request"));
    module.def(
        "bidirectional_task_meet_frontier_probe",
        &bidirectional_task_meet_frontier_payload,
        py::arg("request"));
    module.def(
        "bidirectional_journey_frontier_probe",
        &bidirectional_journey_frontier_payload,
        py::arg("request"));
    module.def(
        "bidirectional_midpoint_journey_meet",
        &bidirectional_midpoint_meet_payload,
        py::arg("request"));
#endif
}
