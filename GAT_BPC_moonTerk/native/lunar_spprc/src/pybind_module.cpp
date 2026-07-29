#include "lunar_spprc/native_pricer.hpp"

#include <bit>
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

lunar_spprc::SolveParams parse_params(const py::dict& payload) {
    lunar_spprc::SolveParams params;
    params.exact_proof = py::cast<std::string>(payload["mode"]) == "exact_proof";
    params.harvest_target = py::cast<std::size_t>(payload["harvest_target"]);
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
             "dssr_enabled",
             "dssr_policy_version",
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
}
