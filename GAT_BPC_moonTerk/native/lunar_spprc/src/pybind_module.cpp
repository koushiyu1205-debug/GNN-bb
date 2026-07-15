#include "lunar_spprc/native_pricer.hpp"

#include <cmath>
#include <limits>
#include <string>
#include <unordered_map>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

namespace {

double optional_double(const py::dict& payload, const char* key, double fallback) {
    const auto value = payload[py::str(key)];
    return value.is_none() ? fallback : py::cast<double>(value);
}

lunar_spprc::Model parse_model(const py::dict& payload) {
    lunar_spprc::Model model;
    model.instance_id = py::cast<std::string>(payload["instance_id"]);
    model.structure_hash = py::cast<std::string>(payload["instance_hash"]);
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
    for (const auto item : py::cast<py::list>(payload["cuts"])) {
        const auto row = py::cast<py::dict>(item);
        const auto cut_type = py::cast<std::string>(row["cut_type"]);
        if (cut_type != "subset_row" && cut_type != "fleet_lower_bound") {
            throw std::invalid_argument("unsupported native cut type");
        }
        lunar_spprc::CutDefinition cut;
        cut.id = py::cast<std::string>(row["cut_id"]);
        cut.kind = cut_type == "subset_row"
                       ? lunar_spprc::CutKind::SubsetRow
                       : lunar_spprc::CutKind::FleetLowerBound;
        cut.divisor = py::cast<std::size_t>(row["divisor"]);
        cut.dual = py::cast<double>(row["dual"]);
        cut.task_mask.assign((model.tasks.size() + 63U) / 64U, 0U);
        for (const auto task_value : py::cast<py::list>(row["tasks"])) {
            const auto task_id = py::cast<std::string>(task_value);
            const auto found = task_index_by_id.find(task_id);
            if (found == task_index_by_id.end()) {
                throw std::invalid_argument("native cut references an unknown task");
            }
            cut.task_mask[found->second / 64U] |=
                (std::uint64_t{1} << (found->second % 64U));
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

lunar_spprc::SolveParams parse_params(const py::dict& payload) {
    lunar_spprc::SolveParams params;
    params.exact_proof = py::cast<std::string>(payload["mode"]) == "exact_proof";
    params.harvest_target = py::cast<std::size_t>(payload["harvest_target"]);
    params.timeout_seconds = optional_double(payload, "wall_time_limit_sec",
                                             std::numeric_limits<double>::infinity());
    params.max_memory_gb = py::cast<double>(payload["memory_limit_gb"]);
    params.negative_epsilon = py::cast<double>(payload["negative_eps"]);
    params.dominance_epsilon = py::cast<double>(payload["dominance_eps"]);
    params.resource_epsilon = py::cast<double>(payload["resource_eps"]);
    params.graph_cache_entries = py::cast<std::size_t>(payload["graph_cache_entries"]);
    params.completion_bound_enabled = py::cast<bool>(payload["completion_bound_enabled"]);
    params.subset_dominance_enabled = py::cast<bool>(payload["subset_dominance_enabled"]);
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
    telemetry["extended_labels"] = output.telemetry.extended_labels;
    telemetry["dominated_labels"] = output.telemetry.dominated_labels;
    telemetry["dominance_candidate_checks"] = output.telemetry.dominance_candidate_checks;
    telemetry["max_visited_bucket_size"] = output.telemetry.max_visited_bucket_size;
    telemetry["solution_count"] = output.telemetry.solution_count;
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
    return result;
}

}  // namespace

PYBIND11_MODULE(lunar_spprc_native, module) {
    module.doc() = "Exact-safe lunar multi-sortie SPPRC extension";
    module.def("solve", &solve_payload, py::arg("request"));
    module.def("build_info", &lunar_spprc::build_info);
}
