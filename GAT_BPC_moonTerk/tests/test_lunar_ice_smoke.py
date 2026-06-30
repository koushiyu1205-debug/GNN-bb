from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from lunar_ice_bpc.io.config import apply_overrides, load_config
from lunar_ice_bpc.domain.scenario import (
    ACTIVE_FOOTPRINT_BY_SCALE,
    FLEET_BY_SCALE,
    HORIZON_BY_SCALE,
    LunarIceConfig,
    PATH_OPTION_POLICY_ID,
    PATH_TYPES,
    RISK_SCHEMA_VERSION,
    SHADOW_CAP_BY_SCALE,
    SOLVE_TIME_LIMIT_SEC_BY_SCALE,
    SYNTHETIC_GENERATOR_ID,
    TIME_WINDOW_POLICY_ID,
)
from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.certificates.pricing_certificate import (
    build_pricing_certificate,
    select_effective_pricing_certificate,
)
from lunar_ice_bpc.exact.certificates.pricing_frontier import build_pricing_frontier_ledger
from lunar_ice_bpc.exact.certificates.node_bound import build_node_bound_certificate
from lunar_ice_bpc.exact.certificates.certificate_readiness import build_true_dual_certificate_readiness
from lunar_ice_bpc.exact.certificates.completion_bound_consistency import build_completion_bound_consistency_audit
from lunar_ice_bpc.exact.certificates.dual_binding import build_rmp_dual_binding_from_result
from lunar_ice_bpc.exact.certificates.fixed_graph_pricing_proof import build_fixed_graph_pricing_proof
from lunar_ice_bpc.exact.certificates.true_dual_pricing_tail import build_true_dual_pricing_tail
from lunar_ice_bpc.exact.core.branching import (
    DIFFERENT_JOURNEY,
    SAME_JOURNEY,
    BranchContext,
    PairBranchDecision,
    filter_journey_columns_by_branch_context,
    journey_satisfies_branch_context,
)
from lunar_ice_bpc.exact.core.cuts import (
    CutContext,
    cut_coefficients_for_journey,
    cut_context_from_payload,
    fleet_lower_bound_cut,
    subset_row_cut,
)
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals, manual_journey_reduced_cost, solve_restricted_journey_rmp
from lunar_ice_bpc.exact.pricing.completion_bounds import build_positive_cover_completion_bound
from lunar_ice_bpc.exact.pricing.journey_pricing import (
    DirectPricingCache,
    price_canonical_journey_universe,
    price_direct_journey_columns,
    price_exhaustive_direct_journey_columns,
    price_direct_journey_labels,
)
import lunar_ice_bpc.exact.solver.journey_driver as journey_driver_module
from lunar_ice_bpc.exact.solver.journey_driver import (
    DirectBaselineTimeLimitExceeded,
    JourneyBaselineResult,
    enumerate_direct_journey_columns,
    enumerate_direct_journey_columns_by_template,
    enumerate_canonical_journey_columns,
    solve_direct_journey_baseline,
    solve_small_journey_baseline,
)
from lunar_ice_bpc.exact.solver.branch_probe import build_branch_probe, build_fractional_branch_probe
from lunar_ice_bpc.exact.solver.branch_node_queue import run_restricted_branch_node_queue
from lunar_ice_bpc.exact.solver.branch_tree import build_branch_tree_probe
from lunar_ice_bpc.exact.solver.cut_probe import build_cut_probe
from lunar_ice_bpc.exact.solver.cut_separator import run_restricted_cut_separation_round
from lunar_ice_bpc.exact.solver.fixed_graph_pricing_closure import run_fixed_graph_pricing_closure
from lunar_ice_bpc.guidance.graph_builder import build_guidance_graph
from lunar_ice_bpc.guidance.shadow_policy import build_shadow_report
from lunar_ice_bpc.io.instance_io import validate_instance, write_json
from lunar_ice_bpc.runners.audit import audit_benchmark_csv
from lunar_ice_bpc.runners.benchmark import run_benchmark
from lunar_ice_bpc.runners.refactor_audit import audit_refactor_state
from lunar_ice_bpc.runners.generate_instances import generate_benchmark
from lunar_ice_bpc.runners.solve import _fallback_baseline_for_reporting, solve_reference


class LunarIceSmokeTests(unittest.TestCase):
    def test_generated_instance_schema_has_three_paths_and_no_comm(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        config = LunarIceConfig()
        self.assertFalse(validate_instance(instance))
        edge_types = {tuple(option["path_type"] for option in edge["path_options"]) for edge in instance["logical_graph"]["edges"]}
        self.assertEqual(edge_types, {PATH_TYPES})
        forbidden_fragments = ("comm", "communication", "earth_visibility", "relay", "link_margin")
        serialized_keys = str(list(_walk_keys(instance))).lower()
        self.assertFalse(any(fragment in serialized_keys for fragment in forbidden_fragments))
        self.assertEqual(instance["resource_map"]["generator"], SYNTHETIC_GENERATOR_ID)
        self.assertEqual(instance["resource_map"]["risk_schema_version"], RISK_SCHEMA_VERSION)
        self.assertEqual(instance["resource_map"]["extent_km"], config.resource_map_extent_km)
        self.assertEqual(instance["resource_map"]["resolution_m"], config.synthetic_grid_resolution_m)
        self.assertEqual(instance["resource_map"]["grid_shape"], [300, 300])
        self.assertEqual(instance["resource_map"]["active_footprint_km"], ACTIVE_FOOTPRINT_BY_SCALE[5])
        self.assertEqual(instance["vehicle"]["fleet_size"], FLEET_BY_SCALE[5])
        self.assertEqual(instance["vehicle"]["B_use"], config.b_use)
        self.assertEqual(instance["vehicle"]["max_shadow_exposure_per_sortie"], SHADOW_CAP_BY_SCALE[5])
        self.assertEqual(instance["scheduling"]["horizon_min"], HORIZON_BY_SCALE[5])
        self.assertEqual(instance["scheduling"]["time_window_policy_id"], TIME_WINDOW_POLICY_ID)
        self.assertEqual(instance["logical_graph"]["path_option_policy_id"], PATH_OPTION_POLICY_ID)

    def test_instance_validation_rejects_lunar_scenario_parameter_drift(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)

        drifted_energy = json.loads(json.dumps(instance))
        drifted_energy["vehicle"]["B_use"] = 200.0
        self.assertTrue(any("vehicle.B_use" in issue for issue in validate_instance(drifted_energy)))

        drifted_shadow = json.loads(json.dumps(instance))
        drifted_shadow["reference_solution"]["journeys"][0]["sorties"][0]["shadow_exposure_min"] = (
            SHADOW_CAP_BY_SCALE[5] + 1.0
        )
        self.assertTrue(any("exceeds max_shadow_exposure_per_sortie" in issue for issue in validate_instance(drifted_shadow)))

        drifted_footprint = json.loads(json.dumps(instance))
        first_task = next(iter(drifted_footprint["tasks"].values()))
        first_task["xy_km"] = [29.0, 29.0]
        self.assertTrue(any("outside active footprint" in issue for issue in validate_instance(drifted_footprint)))

    def test_operation_mode_is_single_task_attribute(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        task_ids = set(instance["tasks"])
        covered = [
            task_id
            for journey in instance["reference_solution"]["journeys"]
            for sortie in journey["sorties"]
            for task_id in sortie["tasks"]
        ]
        self.assertEqual(set(covered), task_ids)
        self.assertEqual(len(covered), len(task_ids))
        self.assertTrue(all(task["operation_mode"] in {"detect", "sample", "drill"} for task in instance["tasks"].values()))

    def test_small_direct_baseline_can_close_fixed_graph_bpc_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        with tempfile.TemporaryDirectory() as tmp:
            instance_path = Path(tmp) / "instance.json"
            solution_path = Path(tmp) / "solution.json"
            write_json(instance_path, instance)
            result = solve_reference(instance_path, solution_path)
        self.assertEqual(result["status"], "DIRECT_DP_BASELINE_OPTIMAL")
        self.assertEqual(result["exact_status"], "EXACT_BASELINE_OPTIMAL")
        self.assertEqual(result["exact_claim_scope"], "fixed_logical_graph_exhaustive_direct_dp")
        self.assertEqual(result["bpc_certificate_status"], "CERTIFIED_NO_NEGATIVE")
        self.assertTrue(result["uses_true_dual_bpc_certificate"])
        self.assertEqual(result["pricing_certificate"]["status"], "CERTIFIED_NO_NEGATIVE")
        self.assertTrue(result["pricing_certificate"]["can_certify_no_negative"])
        self.assertEqual(result["pricing_certificate"]["selected_certificate_source"], "true_dual_pricing_tail")
        self.assertEqual(result["pricing_certificate"]["issues"], [])
        self.assertEqual(result["pricing_certificate"]["frontier_ledger"]["status"], "CERTIFIED_FRONTIER_NO_NEGATIVE")
        self.assertTrue(result["pricing_certificate"]["frontier_ledger"]["lower_bound_official"])
        self.assertEqual(result["node_bound_certificate"]["status"], "NODE_BOUND_FATHOMED")
        self.assertTrue(result["node_bound_certificate"]["can_fathom_by_bound"])
        self.assertTrue(result["node_bound_certificate"]["lower_bound_official"])
        self.assertEqual(result["node_bound_certificate"]["issues"], [])
        readiness = result["true_dual_certificate_readiness"]
        self.assertEqual(readiness["status"], "TRUE_DUAL_CERTIFICATE_READY")
        self.assertFalse(readiness["mutates_solver"])
        self.assertTrue(readiness["can_certify"])
        self.assertTrue(readiness["true_dual_pricing_used"])
        self.assertEqual(readiness["missing_inputs"], [])
        self.assertEqual(result["covered_task_count"], result["task_count"])
        self.assertEqual(result["incumbent_source"], "direct_dp_exact_baseline")
        self.assertEqual(result["objective"], result["direct_exact_objective"])
        self.assertLessEqual(result["lower_bound"], result["objective"])
        self.assertEqual(result["gap_type"], "official_bpc_node_bound")
        self.assertGreaterEqual(result["relaxation_gap"], 0.0)
        self.assertEqual(result["lower_bound_source"], "direct_fixed_graph_root_lp")
        self.assertEqual(result["lower_bound_scope"], "fixed_logical_graph_direct_root")
        self.assertEqual(result["bound_ledger"]["official_lower_bound"], result["lower_bound"])
        self.assertEqual(result["bound_ledger"]["official_lower_bound_source"], "direct_fixed_graph_root_lp")
        self.assertFalse(result["bound_ledger"]["diagnostic_bound_is_official"])
        self.assertTrue(
            any(
                record["name"] == "direct_fixed_graph_root_lp"
                and record["certificate_status"] == "BPC_NODE_BOUND_CERTIFIED"
                and record["official_lower_bound"] is True
                for record in result["bound_ledger"]["records"]
            )
        )
        self.assertEqual(result["analytic_lower_bound"]["exact_status"], "RELAXATION_LOWER_BOUND")
        self.assertLessEqual(result["objective"], result["canonical_objective"])
        self.assertTrue(result["solver_options"]["uses_true_dual_bpc_certificate"])
        self.assertEqual(result["direct_exact_baseline"]["status"], "DIRECT_DP_BASELINE_OPTIMAL")
        self.assertEqual(result["canonical_baseline"]["status"], "CANONICAL_DP_BASELINE_OPTIMAL")
        direct_root = result["direct_root_certificate"]
        self.assertIn(
            direct_root["status"],
            {"DIRECT_ROOT_FIXED_GRAPH_LP_CERTIFIED", "DIRECT_ROOT_FIXED_GRAPH_INTEGER_CERTIFIED"},
        )
        self.assertIn(
            direct_root["exact_status"],
            {"FIXED_GRAPH_ROOT_LP_CERTIFIED", "FIXED_GRAPH_INTEGER_OPTIMAL"},
        )
        self.assertEqual(direct_root["certificate_scope"], "fixed_logical_graph_direct_root")
        self.assertTrue(direct_root["uses_true_dual_bpc_certificate"])
        self.assertEqual(direct_root["task_count"], 5)
        self.assertLessEqual(direct_root["lp_bound"], result["objective"] + 1.0e-6)
        self.assertGreaterEqual(direct_root["min_reduced_cost"], -1.0e-6)
        self.assertGreater(result["route_template_count"], 0)
        self.assertGreater(result["pareto_label_count"], 0)
        self.assertEqual(result["restricted_rmp"]["status"], "RESTRICTED_RMP_OPTIMAL")
        self.assertEqual(result["restricted_rmp"]["exact_status"], "NOT_BPC_CERTIFIED")
        self.assertGreaterEqual(result["restricted_rmp"]["min_reduced_cost"], -1.0e-6)
        direct = result["restricted_rmp"]["direct_pricing"]
        self.assertEqual(direct["status"], "DIRECT_LABEL_PRICED")
        self.assertEqual(direct["exact_status"], "NOT_BPC_CERTIFIED")
        self.assertIsInstance(direct["negative_found"], bool)
        self.assertGreater(direct["feasible_sortie_template_count"], 0)
        self.assertEqual(result["restricted_rmp"]["cut_context"]["cut_count"], 0)
        self.assertFalse(result["restricted_rmp"]["cut_rows_active"])
        direct_cg = result["restricted_rmp"]["direct_column_generation"]
        self.assertIn(direct_cg["status"], {"DIRECT_CG_ROUND_LIMIT", "DIRECT_CG_NO_NEGATIVE"})
        self.assertGreater(direct_cg["added_column_count"], 0)
        self.assertLess(direct_cg["final_bound"], result["restricted_rmp"]["objective_bound"])

    def test_large_reference_fallback_reports_relaxation_gap(self) -> None:
        instance = generate_instance(20, seed=829001, index=1)
        with tempfile.TemporaryDirectory() as tmp:
            instance_path = Path(tmp) / "instance.json"
            solution_path = Path(tmp) / "solution.json"
            write_json(instance_path, instance)
            result = solve_reference(instance_path, solution_path)

        self.assertEqual(result["status"], "FEASIBLE_REFERENCE")
        self.assertEqual(result["exact_status"], "NOT_SOLVED")
        self.assertEqual(result["exact_claim_scope"], "none")
        self.assertEqual(result["bpc_certificate_status"], "NOT_PORTED_TRUE_DUAL_BPC")
        self.assertFalse(result["uses_true_dual_bpc_certificate"])
        self.assertEqual(result["pricing_certificate"]["status"], "NOT_PORTED_TRUE_DUAL_BPC")
        self.assertFalse(result["pricing_certificate"]["can_certify_no_negative"])
        self.assertIn("pricing_coverage_not_complete", result["pricing_certificate"]["issues"])
        self.assertIn(
            result["pricing_certificate"]["frontier_ledger"]["status"],
            {"DIAGNOSTIC_FRONTIER_ONLY", "NEGATIVE_REDUCED_COST_FOUND"},
        )
        self.assertFalse(result["pricing_certificate"]["frontier_ledger"]["lower_bound_official"])
        self.assertEqual(result["node_bound_certificate"]["status"], "NODE_BOUND_FAIL_CLOSED")
        self.assertFalse(result["node_bound_certificate"]["can_fathom_by_bound"])
        self.assertGreater(result["lower_bound"], 0.0)
        self.assertLessEqual(result["lower_bound"], result["objective"])
        self.assertGreaterEqual(result["relaxation_gap"], 0.0)
        self.assertEqual(result["gap_type"], "analytic_relaxation_not_bpc_certificate")
        self.assertEqual(result["lower_bound_source"], "analytic_relaxation")
        self.assertEqual(result["bound_ledger"]["official_lower_bound"], result["lower_bound"])
        self.assertFalse(result["bound_ledger"]["diagnostic_bound_is_official"])
        self.assertTrue(
            any(
                record["name"] == "restricted_journey_rmp"
                and record["official_lower_bound"] is False
                for record in result["bound_ledger"]["records"]
            )
        )
        self.assertEqual(result["analytic_lower_bound"]["status"], "ANALYTIC_RELAXATION_BOUND")
        self.assertEqual(result["direct_root_certificate"]["status"], "SKIPPED_TOO_LARGE_FOR_DIRECT_ROOT_CERTIFICATE")
        self.assertFalse(result["direct_root_certificate"]["uses_true_dual_bpc_certificate"])
        self.assertIn(result["incumbent_source"], {"reference_solution", "seeded_column_pool"})
        if result["seeded_column_pool_selection"]["objective"] is not None:
            self.assertLessEqual(result["objective"], result["seeded_column_pool_selection"]["objective"])
        self.assertLessEqual(result["objective"], instance["reference_solution"]["objective"])
        self.assertGreater(result["seeded_journey_pool"]["column_count"], 0)
        self.assertIn(
            result["seeded_column_pool_selection"]["status"],
            {"COLUMN_POOL_EXACT_COVER", "COLUMN_POOL_STATE_LIMIT", "NO_EXACT_COVER_IN_COLUMN_POOL"},
        )
        self.assertLessEqual(
            result["seeded_column_pool_selection"]["state_count"],
            result["seeded_column_pool_selection"]["max_states"] + 1,
        )
        self.assertEqual(result["restricted_rmp"]["pool_type"], "seeded_reference_singleton_pool")
        self.assertIn(result["restricted_rmp"]["status"], {"RESTRICTED_RMP_OPTIMAL", "RESTRICTED_RMP_ITERATION_LIMIT"})
        self.assertIn(result["restricted_rmp"]["direct_pricing"]["status"], {"PARTIAL_DIRECT_LABEL_PRICED", "NO_DIRECT_LABEL_FOUND"})
        self.assertLessEqual(result["restricted_rmp"]["direct_pricing"]["candidate_round_count"], 8)
        self.assertEqual(result["restricted_rmp"]["direct_pricing"]["candidate_round_limit"], 8)
        self.assertFalse(result["solver_options"]["uses_true_dual_bpc_certificate"])

    def test_ten_task_direct_label_dp_is_fixed_graph_exact_baseline(self) -> None:
        instance = generate_instance(10, seed=729001, index=1)
        data = load_lunar_ice_data(instance)
        direct = solve_direct_journey_baseline(data, max_exact_tasks=10)
        canonical = solve_small_journey_baseline(data, max_exact_tasks=10)

        self.assertEqual(direct.status, "DIRECT_DP_BASELINE_OPTIMAL")
        self.assertEqual(direct.exact_status, "EXACT_BASELINE_OPTIMAL")
        self.assertEqual(canonical.status, "CANONICAL_DP_BASELINE_OPTIMAL")
        self.assertLessEqual(direct.objective, canonical.objective + 1.0e-6)
        self.assertGreater(direct.generated_sortie_count, 0)
        self.assertGreater(direct.route_template_count, 0)

    def test_remaining_aware_direct_dp_matches_template_universe_on_small_instance(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        direct = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        template = enumerate_direct_journey_columns_by_template(data, max_exact_tasks=5)
        direct_by_tasks = {frozenset(column.task_set): column.objective for column in direct.columns}
        template_by_tasks = {frozenset(column.task_set): column.objective for column in template.columns}

        self.assertEqual(set(direct_by_tasks), set(template_by_tasks))
        for task_set, objective in direct_by_tasks.items():
            self.assertAlmostEqual(objective, template_by_tasks[task_set], delta=2.0e-6)
        self.assertLessEqual(direct.route_template_count, template.route_template_count)

    def test_direct_baseline_time_limit_fails_closed(self) -> None:
        instance = generate_instance(10, seed=729001, index=1)
        data = load_lunar_ice_data(instance)
        direct = solve_direct_journey_baseline(data, max_exact_tasks=10, wall_time_limit_sec=0.0)

        self.assertEqual(direct.status, "DIRECT_DP_BASELINE_TIME_LIMIT")
        self.assertEqual(direct.exact_status, "NOT_SOLVED")
        self.assertIsNone(direct.objective)
        self.assertFalse(direct.journeys)

    def test_direct_baseline_timeout_keeps_partial_diagnostics(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        original = journey_driver_module.enumerate_direct_journey_columns

        def raise_timeout(*args, **kwargs):
            raise DirectBaselineTimeLimitExceeded(
                stage="journey_label_dp",
                generated_journey_count=7,
                generated_sortie_count=11,
                route_template_count=13,
                pareto_label_count=17,
            )

        journey_driver_module.enumerate_direct_journey_columns = raise_timeout
        try:
            direct = solve_direct_journey_baseline(data, max_exact_tasks=5, wall_time_limit_sec=1.0)
        finally:
            journey_driver_module.enumerate_direct_journey_columns = original

        self.assertEqual(direct.status, "DIRECT_DP_BASELINE_TIME_LIMIT")
        self.assertEqual(direct.exact_status, "NOT_SOLVED")
        self.assertIsNone(direct.objective)
        self.assertFalse(direct.journeys)
        self.assertEqual(direct.generated_journey_count, 7)
        self.assertEqual(direct.generated_sortie_count, 11)
        self.assertEqual(direct.route_template_count, 13)
        self.assertEqual(direct.pareto_label_count, 17)
        self.assertIn("journey_label_dp", direct.note)
        self.assertIn("diagnostic only", direct.note)

    def test_fallback_reporting_prefers_direct_timeout_workload(self) -> None:
        direct = JourneyBaselineResult(
            status="DIRECT_DP_BASELINE_TIME_LIMIT",
            exact_status="NOT_SOLVED",
            objective=None,
            journeys=tuple(),
            generated_journey_count=7,
            generated_sortie_count=11,
            route_template_count=13,
            pareto_label_count=17,
            set_partition_state_count=0,
            note="timeout",
        )
        canonical = JourneyBaselineResult(
            status="SKIPPED_TOO_LARGE_FOR_ENUM_BASELINE",
            exact_status="NOT_SOLVED",
            objective=None,
            journeys=tuple(),
            generated_journey_count=0,
            generated_sortie_count=0,
            route_template_count=0,
            pareto_label_count=0,
            set_partition_state_count=0,
            note="skipped",
        )

        self.assertIs(_fallback_baseline_for_reporting(direct, canonical), direct)

    def test_manual_reduced_cost_formula(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        result = solve_small_journey_baseline(data)
        self.assertTrue(result.journeys)
        journey = result.journeys[0]
        cover_dual = {task: 3.0 for task in journey.task_set}
        duals = JourneyDuals(cover=cover_dual, fleet_limit=7.0)
        expected = journey.objective - 7.0 - 3.0 * len(journey.task_set)
        self.assertAlmostEqual(manual_journey_reduced_cost(journey, duals), round(expected, 9))

    def test_cut_context_coefficients_feed_manual_reduced_cost(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        result = solve_small_journey_baseline(data)
        journey = result.journeys[0]
        tasks = tuple(sorted(journey.task_set))[:3]
        context = CutContext(
            (
                subset_row_cut("sri_001", tasks, divisor=2),
                fleet_lower_bound_cut("fleet_lb_001", min_vehicles=1),
            )
        )
        coefficients = cut_coefficients_for_journey(journey, context)
        self.assertEqual(coefficients["sri_001"], 1.0)
        self.assertEqual(coefficients["fleet_lb_001"], 1.0)
        duals = JourneyDuals(cover={}, fleet_limit=0.0, cuts={"sri_001": 2.5, "fleet_lb_001": 4.0})
        expected = journey.objective - 2.5 - 4.0
        self.assertAlmostEqual(
            manual_journey_reduced_cost(journey, duals, cut_coefficients=coefficients),
            round(expected, 9),
        )
        reloaded = cut_context_from_payload(context.to_payload())
        self.assertEqual(reloaded.to_payload(), context.to_payload())
        with self.assertRaises(ValueError):
            CutContext((subset_row_cut("dup", tasks), subset_row_cut("dup", tasks)))

    def test_restricted_rmp_accepts_active_cut_context_as_diagnostic_rows(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_canonical_journey_columns(data, max_exact_tasks=5)
        context = CutContext(
            (
                subset_row_cut("sri_active", data.task_ids[:3], divisor=2),
                fleet_lower_bound_cut("fleet_lb_active", min_vehicles=1),
            )
        )
        rmp = solve_restricted_journey_rmp(
            data.task_ids,
            universe.columns,
            fleet_size=data.fleet_size,
            cut_context=context,
        )

        self.assertEqual(rmp.status, "RESTRICTED_RMP_OPTIMAL")
        self.assertEqual(rmp.exact_status, "NOT_BPC_CERTIFIED")
        self.assertTrue(rmp.cut_rows_active)
        self.assertEqual(rmp.cut_count, 2)
        self.assertEqual(rmp.cut_context["cut_count"], 2)
        self.assertEqual(set(rmp.duals.cuts), {"sri_active", "fleet_lb_active"})
        self.assertEqual(len(rmp.primal_cut_activities), 2)
        self.assertIsNotNone(rmp.primal_cut_violation_max)
        self.assertLessEqual(rmp.primal_cut_violation_max, 1.0e-6)
        self.assertTrue(any(row.get("cut_coefficients") for row in rmp.primal_columns))

    def test_cut_probe_is_diagnostic_only(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_canonical_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        probe = build_cut_probe(data.task_ids, universe.columns, rmp.primal_columns, fleet_size=data.fleet_size)

        self.assertEqual(probe["schema_version"], "lunar_ice_bpc.cut_probe.v1")
        self.assertEqual(probe["status"], "CUT_PROBE_READY")
        self.assertEqual(probe["evaluation_scope"], "restricted_rmp_primal_only")
        self.assertGreaterEqual(probe["subset_candidate_count"], 1)
        self.assertIsNotNone(probe["fleet_lower_bound_candidate"])
        self.assertEqual(probe["rows_added_to_rmp"], 0)
        self.assertFalse(probe["cut_rows_active"])
        self.assertFalse(probe["lower_bound_official"])
        self.assertFalse(probe["mutates_solver"])
        self.assertFalse(probe["can_certify"])
        self.assertEqual(probe["exact_status_effect"], "none")

    def test_cut_separation_round_re_solves_restricted_rmp_but_cannot_certify(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_canonical_journey_columns(data, max_exact_tasks=5)
        root = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        probe = build_cut_probe(data.task_ids, universe.columns, root.primal_columns, fleet_size=data.fleet_size)

        default_round = run_restricted_cut_separation_round(
            data.task_ids,
            universe.columns,
            fleet_size=data.fleet_size,
            root_rmp=root,
            cut_probe=probe,
            max_rows=3,
        )
        self.assertEqual(default_round["schema_version"], "lunar_ice_bpc.cut_separation_round.v1")
        self.assertEqual(default_round["status"], "NO_CUT_ROW_ADDED")
        self.assertEqual(default_round["rows_added_to_rmp"], 0)
        self.assertFalse(default_round["cut_rows_active"])
        self.assertFalse(default_round["lower_bound_official"])
        self.assertFalse(default_round["can_certify"])

        forced_round = run_restricted_cut_separation_round(
            data.task_ids,
            universe.columns,
            fleet_size=data.fleet_size,
            root_rmp=root,
            cut_probe=probe,
            max_rows=1,
            add_violated_only=False,
        )
        self.assertEqual(forced_round["status"], "RESTRICTED_CUT_SEPARATION_EVALUATED")
        self.assertEqual(forced_round["rows_added_to_rmp"], 1)
        self.assertTrue(forced_round["cut_rows_active"])
        self.assertEqual(forced_round["cut_context"]["cut_count"], 1)
        self.assertEqual(forced_round["cut_rmp_status"], "RESTRICTED_RMP_OPTIMAL")
        self.assertFalse(forced_round["lower_bound_official"])
        self.assertFalse(forced_round["mutates_solver"])
        self.assertFalse(forced_round["can_certify"])
        self.assertEqual(forced_round["exact_status_effect"], "none")

    def test_pricing_certificate_is_fail_closed_until_true_dual_complete(self) -> None:
        frontier = build_pricing_frontier_ledger(
            source="diagnostic_direct_pricing",
            pricing_payload={"best_reduced_cost": 0.0},
            rmp_payload={"min_reduced_cost": 0.0},
            uses_true_dual_bpc_certificate=False,
            pricing_complete=True,
            coverage_complete=True,
        ).to_payload()
        self.assertEqual(frontier["status"], "DIAGNOSTIC_FRONTIER_ONLY")
        self.assertFalse(frontier["lower_bound_official"])
        self.assertFalse(frontier["can_certify_no_negative"])

        diagnostic = build_pricing_certificate(
            source="diagnostic_direct_pricing",
            pricing_payload={"best_reduced_cost": 0.0},
            rmp_payload={"min_reduced_cost": 0.0},
            uses_true_dual_bpc_certificate=False,
            pricing_complete=True,
            coverage_complete=True,
        ).to_payload()
        self.assertEqual(diagnostic["status"], "NOT_PORTED_TRUE_DUAL_BPC")
        self.assertFalse(diagnostic["can_certify_no_negative"])
        self.assertIn("true_dual_bpc_pricing_not_used", diagnostic["issues"])
        self.assertEqual(diagnostic["frontier_ledger"]["status"], "DIAGNOSTIC_FRONTIER_ONLY")
        self.assertFalse(diagnostic["frontier_ledger"]["lower_bound_official"])

        certified = build_pricing_certificate(
            source="true_dual_pricing",
            pricing_payload={"best_reduced_cost": 0.0},
            rmp_payload={"min_reduced_cost": 0.0},
            uses_true_dual_bpc_certificate=True,
            pricing_complete=True,
            coverage_complete=True,
        ).to_payload()
        self.assertEqual(certified["status"], "CERTIFIED_NO_NEGATIVE")
        self.assertTrue(certified["can_certify_no_negative"])
        self.assertEqual(certified["issues"], [])
        self.assertEqual(certified["frontier_ledger"]["status"], "CERTIFIED_FRONTIER_NO_NEGATIVE")
        self.assertTrue(certified["frontier_ledger"]["lower_bound_official"])

    def test_true_dual_pricing_tail_has_single_certifying_entrypoint(self) -> None:
        diagnostic_tail = build_true_dual_pricing_tail(
            source="diagnostic_fixed_graph_pricing_closure",
            pricing_payload={
                "best_reduced_cost": -0.0,
                "pricing_complete_for_all_task_subsets": True,
                "coverage_complete": True,
                "uses_true_dual_bpc_certificate": False,
            },
            rmp_payload={"status": "RESTRICTED_RMP_OPTIMAL", "min_reduced_cost": 0.0},
        )
        self.assertEqual(diagnostic_tail["status"], "TRUE_DUAL_PRICING_TAIL_NOT_PORTED")
        self.assertFalse(diagnostic_tail["can_certify_no_negative"])
        self.assertFalse(diagnostic_tail["lower_bound_official"])
        self.assertIn("true_dual_bpc_pricing_not_used", diagnostic_tail["missing_inputs"])

        certified_tail = build_true_dual_pricing_tail(
            source="true_dual_pricing_tail",
            pricing_payload={
                "best_reduced_cost": 0.0,
                "pricing_complete": True,
                "coverage_complete": True,
                "uses_true_dual_bpc_certificate": True,
                "dual_vector_bound_to_rmp": True,
            },
            rmp_payload={"status": "RESTRICTED_RMP_OPTIMAL", "min_reduced_cost": 0.0},
        )
        self.assertEqual(certified_tail["status"], "TRUE_DUAL_PRICING_TAIL_CERTIFIED")
        self.assertTrue(certified_tail["can_certify_no_negative"])
        self.assertTrue(certified_tail["lower_bound_official"])
        self.assertEqual(certified_tail["pricing_certificate"]["status"], "CERTIFIED_NO_NEGATIVE")
        self.assertEqual(certified_tail["missing_inputs"], [])

    def test_effective_pricing_certificate_selects_certified_tail_only(self) -> None:
        diagnostic = build_pricing_certificate(
            source="diagnostic_direct_pricing",
            pricing_payload={"best_reduced_cost": 0.0},
            rmp_payload={"min_reduced_cost": 0.0},
            uses_true_dual_bpc_certificate=False,
            pricing_complete=True,
            coverage_complete=True,
        ).to_payload()
        not_ported_tail = build_true_dual_pricing_tail(
            source="diagnostic_fixed_graph_pricing_closure",
            pricing_payload={
                "best_reduced_cost": 0.0,
                "pricing_complete_for_all_task_subsets": True,
                "coverage_complete": True,
                "dual_vector_bound_to_rmp": True,
            },
            rmp_payload={"status": "RESTRICTED_RMP_OPTIMAL", "min_reduced_cost": 0.0},
        )
        fallback = select_effective_pricing_certificate(
            diagnostic_certificate=diagnostic,
            true_dual_pricing_tail=not_ported_tail,
        )
        self.assertEqual(fallback["status"], "NOT_PORTED_TRUE_DUAL_BPC")
        self.assertEqual(fallback["selected_certificate_source"], "diagnostic_fallback")

        certified_tail = build_true_dual_pricing_tail(
            source="true_dual_pricing_tail",
            pricing_payload={
                "best_reduced_cost": 0.0,
                "pricing_complete": True,
                "coverage_complete": True,
                "uses_true_dual_bpc_certificate": True,
                "dual_vector_bound_to_rmp": True,
            },
            rmp_payload={"status": "RESTRICTED_RMP_OPTIMAL", "min_reduced_cost": 0.0},
        )
        selected = select_effective_pricing_certificate(
            diagnostic_certificate=diagnostic,
            true_dual_pricing_tail=certified_tail,
        )
        self.assertEqual(selected["status"], "CERTIFIED_NO_NEGATIVE")
        self.assertTrue(selected["uses_true_dual_bpc_certificate"])
        self.assertEqual(selected["selected_certificate_source"], "true_dual_pricing_tail")
        self.assertEqual(selected["diagnostic_fallback_status"], "NOT_PORTED_TRUE_DUAL_BPC")

    def test_rmp_dual_binding_is_proof_input_not_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_canonical_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        binding = build_rmp_dual_binding_from_result(
            rmp,
            source="unit_test_restricted_rmp",
            binding_scope="fixed_logical_graph",
            pricing_source="unit_test_pricing",
        )

        self.assertEqual(binding["schema_version"], "lunar_ice_bpc.rmp_dual_binding.v1")
        self.assertEqual(binding["status"], "RMP_DUAL_VECTOR_BOUND")
        self.assertTrue(binding["dual_vector_bound_to_rmp"])
        self.assertEqual(binding["missing_inputs"], [])
        self.assertGreater(binding["task_cover_dual_count"], 0)
        self.assertTrue(binding["has_fleet_dual"])
        self.assertTrue(binding["dual_vector_fingerprint"])
        self.assertFalse(binding["can_certify_no_negative"])
        self.assertFalse(binding["mutates_solver"])

    def test_completion_bound_consistency_audit_compares_bound_on_and_off(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_canonical_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        audit = build_completion_bound_consistency_audit(data, rmp.duals, max_direct_tasks=5)

        self.assertEqual(audit["schema_version"], "lunar_ice_bpc.completion_bound_consistency.v1")
        self.assertEqual(audit["status"], "COMPLETION_BOUND_CONSISTENT")
        self.assertTrue(audit["consistent"])
        self.assertEqual(audit["with_bound_best_reduced_cost"], audit["without_bound_best_reduced_cost"])
        self.assertEqual(audit["with_bound_negative_found"], audit["without_bound_negative_found"])
        self.assertGreaterEqual(audit["with_bound_evaluated_label_count"], 1)
        self.assertGreaterEqual(audit["without_bound_evaluated_label_count"], 1)
        self.assertFalse(audit["can_certify_no_negative"])
        self.assertEqual(audit["exact_status_effect"], "none")
        self.assertFalse(audit["mutates_solver"])

    def test_fixed_graph_pricing_proof_binds_rmp_duals_but_is_not_bpc_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_canonical_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        proof = build_fixed_graph_pricing_proof(data, rmp.duals, max_direct_tasks=5)

        self.assertEqual(proof["schema_version"], "lunar_ice_bpc.fixed_graph_pricing_proof.v1")
        self.assertEqual(proof["status"], "FIXED_GRAPH_NEGATIVE_REDUCED_COST_FOUND")
        self.assertEqual(proof["pricing_status"], "EXHAUSTIVE_DIRECT_LABEL_PRICED")
        self.assertTrue(proof["pricing_complete_for_all_task_subsets"])
        self.assertLess(proof["min_reduced_cost"], 0.0)
        self.assertTrue(proof["negative_found"])
        self.assertFalse(proof["fixed_graph_no_negative_proved"])
        self.assertFalse(proof["uses_true_dual_bpc_certificate"])
        self.assertFalse(proof["lower_bound_official"])
        self.assertFalse(proof["can_certify_no_negative"])

    def test_fixed_graph_pricing_closure_can_certify_closed_small_node(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_canonical_journey_columns(data, max_exact_tasks=5)
        closure = run_fixed_graph_pricing_closure(data, universe.columns, max_direct_tasks=5, max_rounds=3)

        self.assertEqual(closure["schema_version"], "lunar_ice_bpc.fixed_graph_pricing_closure.v1")
        self.assertEqual(closure["status"], "FIXED_GRAPH_PRICING_CLOSED")
        self.assertGreaterEqual(closure["round_count"], 2)
        self.assertGreater(closure["added_column_count"], 0)
        self.assertEqual(closure["final_rmp_status"], "RESTRICTED_RMP_OPTIMAL")
        self.assertTrue(closure["fixed_graph_no_negative_proved"])
        self.assertEqual(closure["completion_bound_consistency"]["status"], "COMPLETION_BOUND_CONSISTENT")
        self.assertTrue(closure["completion_bound_consistency"]["consistent"])
        self.assertFalse(closure["completion_bound_consistency"]["can_certify_no_negative"])
        self.assertTrue(closure["uses_true_dual_bpc_certificate"])
        self.assertTrue(closure["lower_bound_official"])
        self.assertTrue(closure["can_certify_no_negative"])
        self.assertEqual(closure["exact_status"], "BPC_NO_NEGATIVE_CERTIFIED")
        self.assertEqual(closure["exact_status_effect"], "pricing_certificate")
        self.assertFalse(closure["mutates_solver"])

    def test_readiness_uses_fixed_graph_closure_as_diagnostic_not_certificate(self) -> None:
        diagnostic = build_pricing_certificate(
            source="diagnostic_direct_pricing",
            pricing_payload={"best_reduced_cost": -5.0},
            rmp_payload={"min_reduced_cost": 0.0},
            uses_true_dual_bpc_certificate=False,
            pricing_complete=False,
            coverage_complete=False,
        ).to_payload()
        readiness = build_true_dual_certificate_readiness(
            pricing_certificate=diagnostic,
            restricted_rmp={
                "status": "RESTRICTED_RMP_OPTIMAL",
                "min_reduced_cost": 0.0,
                "fixed_graph_pricing_closure": {
                    "status": "FIXED_GRAPH_PRICING_CLOSED",
                    "fixed_graph_no_negative_proved": True,
                    "last_best_reduced_cost": -0.0,
                },
            },
            node_bound_certificate={"lower_bound_official": False},
        )

        self.assertEqual(readiness["status"], "WAITING_TRUE_DUAL_PRICING_PROOF")
        self.assertTrue(readiness["diagnostic_fixed_graph_closure_complete"])
        self.assertEqual(readiness["fixed_graph_closure_status"], "FIXED_GRAPH_PRICING_CLOSED")
        self.assertTrue(readiness["fixed_graph_closure_no_negative_proved"])
        self.assertTrue(readiness["diagnostic_no_negative"])
        self.assertFalse(readiness["true_dual_pricing_used"])
        self.assertFalse(readiness["can_certify"])
        self.assertIn("true_dual_pricing_proof_not_used", readiness["missing_inputs"])
        self.assertIn("pricing_not_complete", readiness["missing_inputs"])

    def test_true_dual_certificate_readiness_reports_missing_proof_inputs(self) -> None:
        diagnostic = build_pricing_certificate(
            source="diagnostic_direct_pricing",
            pricing_payload={"best_reduced_cost": 0.0},
            rmp_payload={"min_reduced_cost": 0.0},
            uses_true_dual_bpc_certificate=False,
            pricing_complete=True,
            coverage_complete=True,
        ).to_payload()
        readiness = build_true_dual_certificate_readiness(
            pricing_certificate=diagnostic,
            restricted_rmp={
                "status": "RESTRICTED_RMP_OPTIMAL",
                "min_reduced_cost": 0.0,
                "direct_pricing": {"status": "DIRECT_LABEL_PRICED", "pricing_complete_for_all_tasks": True},
            },
            node_bound_certificate={"lower_bound_official": False},
        )

        self.assertEqual(readiness["schema_version"], "lunar_ice_bpc.true_dual_certificate_readiness.v1")
        self.assertEqual(readiness["status"], "WAITING_TRUE_DUAL_PRICING_PROOF")
        self.assertFalse(readiness["mutates_solver"])
        self.assertFalse(readiness["can_certify"])
        self.assertFalse(readiness["lower_bound_official"])
        self.assertIn("true_dual_pricing_proof_not_used", readiness["missing_inputs"])
        self.assertIn("official_bpc_node_bound_missing", readiness["missing_inputs"])

        certified = build_pricing_certificate(
            source="true_dual_pricing",
            pricing_payload={"best_reduced_cost": 0.0},
            rmp_payload={"min_reduced_cost": 0.0},
            uses_true_dual_bpc_certificate=True,
            pricing_complete=True,
            coverage_complete=True,
        ).to_payload()
        certified_readiness = build_true_dual_certificate_readiness(
            pricing_certificate=certified,
            restricted_rmp={"status": "RESTRICTED_RMP_OPTIMAL", "min_reduced_cost": 0.0},
            node_bound_certificate={"lower_bound_official": True},
        )

        self.assertEqual(certified_readiness["status"], "TRUE_DUAL_CERTIFICATE_READY")
        self.assertTrue(certified_readiness["can_certify"])
        self.assertEqual(certified_readiness["missing_inputs"], [])

    def test_node_bound_certificate_fathoms_only_with_official_bpc_bound(self) -> None:
        diagnostic = build_node_bound_certificate(
            incumbent_objective=100.0,
            bound_ledger={
                "records": [
                    {
                        "name": "analytic_relaxation",
                        "value": 120.0,
                        "scope": "global_relaxation",
                        "official_lower_bound": True,
                        "certificate_status": "RELAXATION_NOT_BPC_CERTIFICATE",
                    }
                ]
            },
            pricing_certificate={
                "status": "NOT_PORTED_TRUE_DUAL_BPC",
                "can_certify_no_negative": False,
                "uses_true_dual_bpc_certificate": False,
            },
        ).to_payload()
        self.assertEqual(diagnostic["status"], "NODE_BOUND_FAIL_CLOSED")
        self.assertFalse(diagnostic["can_fathom_by_bound"])
        self.assertFalse(diagnostic["lower_bound_official"])
        self.assertIn("official_bpc_node_bound_missing", diagnostic["issues"])

        certified = build_node_bound_certificate(
            incumbent_objective=100.0,
            bound_ledger={
                "records": [
                    {
                        "name": "true_dual_journey_rmp",
                        "value": 100.0,
                        "scope": "branch_price_node",
                        "official_lower_bound": True,
                        "certificate_status": "BPC_NODE_BOUND_CERTIFIED",
                    }
                ]
            },
            pricing_certificate={
                "status": "CERTIFIED_NO_NEGATIVE",
                "can_certify_no_negative": True,
                "uses_true_dual_bpc_certificate": True,
            },
        ).to_payload()
        self.assertEqual(certified["status"], "NODE_BOUND_FATHOMED")
        self.assertTrue(certified["can_fathom_by_bound"])
        self.assertTrue(certified["lower_bound_official"])

    def test_pair_branch_context_filters_journey_columns(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_canonical_journey_columns(data, max_exact_tasks=5)
        task_a, task_b = data.task_ids[:2]
        together = next(column for column in universe.columns if {task_a, task_b}.issubset(column.task_set))
        one_only = next(column for column in universe.columns if task_a in column.task_set and task_b not in column.task_set)

        same_context = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))
        different_context = BranchContext((PairBranchDecision(task_a, task_b, DIFFERENT_JOURNEY),))
        self.assertTrue(journey_satisfies_branch_context(together, same_context))
        self.assertFalse(journey_satisfies_branch_context(one_only, same_context))
        self.assertFalse(journey_satisfies_branch_context(together, different_context))
        self.assertTrue(journey_satisfies_branch_context(one_only, different_context))

        filtered = filter_journey_columns_by_branch_context(universe.columns, same_context)
        self.assertLess(len(filtered), len(universe.columns))
        self.assertTrue(all(journey_satisfies_branch_context(column, same_context) for column in filtered))

        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size, branch_context=same_context)
        self.assertEqual(rmp.branch_context["pair_decision_count"], 1)
        self.assertGreater(rmp.branch_filtered_column_count, 0)
        self.assertIn(rmp.status, {"RESTRICTED_RMP_OPTIMAL", "RMP_UNBOUNDED", "RMP_NO_CONSTRAINTS"})

        with self.assertRaises(ValueError):
            BranchContext(
                (
                    PairBranchDecision(task_a, task_b, SAME_JOURNEY),
                    PairBranchDecision(task_b, task_a, DIFFERENT_JOURNEY),
                )
            )

    def test_branch_probe_is_diagnostic_only(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_canonical_journey_columns(data, max_exact_tasks=5)
        probe = build_branch_probe(data.task_ids, universe.columns, max_candidates=3)

        self.assertEqual(probe["schema_version"], "lunar_ice_bpc.branch_probe.v1")
        self.assertEqual(probe["status"], "BRANCH_PROBE_READY")
        self.assertFalse(probe["mutates_solver"])
        self.assertFalse(probe["can_certify"])
        self.assertEqual(probe["exact_status_effect"], "none")
        self.assertGreaterEqual(probe["candidate_count"], probe["reported_candidate_count"])
        self.assertLessEqual(probe["reported_candidate_count"], 3)
        first = probe["candidates"][0]
        self.assertIn("same_child_context", first)
        self.assertIn("different_child_context", first)
        self.assertEqual(first["same_child_context"]["pair_decisions"][0]["sense"], SAME_JOURNEY)
        self.assertEqual(first["different_child_context"]["pair_decisions"][0]["sense"], DIFFERENT_JOURNEY)

    def test_fractional_branch_probe_uses_restricted_rmp_primal_lambdas(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_canonical_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        probe = build_fractional_branch_probe(data.task_ids, rmp.primal_columns, universe.columns, max_candidates=3)

        self.assertEqual(probe["schema_version"], "lunar_ice_bpc.fractional_branch_probe.v1")
        self.assertIn(probe["status"], {"FRACTIONAL_BRANCH_PROBE_READY", "NO_FRACTIONAL_BRANCH_CANDIDATE"})
        self.assertFalse(probe["mutates_solver"])
        self.assertFalse(probe["can_certify"])
        self.assertEqual(probe["exact_status_effect"], "none")
        self.assertGreater(len(rmp.primal_columns), 0)
        self.assertIsNotNone(rmp.primal_cover_residual_max)
        self.assertLessEqual(rmp.primal_cover_residual_max, 1.0e-6)
        if probe["candidates"]:
            first = probe["candidates"][0]
            self.assertGreater(first["same_fraction"], 0.0)
            self.assertLess(first["same_fraction"], 1.0)
            self.assertIn("same_child_context", first)
            self.assertIn("different_child_context", first)

    def test_branch_tree_probe_materializes_context_only_nodes(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_canonical_journey_columns(data, max_exact_tasks=5)
        probe = build_branch_probe(data.task_ids, universe.columns, max_candidates=3)
        tree = build_branch_tree_probe(
            universe.columns,
            probe,
            max_branch_pairs=1,
            task_ids=data.task_ids,
            fleet_size=data.fleet_size,
            evaluate_restricted_rmp=True,
            max_child_evaluations=2,
        )

        self.assertEqual(tree["schema_version"], "lunar_ice_bpc.branch_tree_probe.v1")
        self.assertEqual(tree["status"], "BRANCH_TREE_RESTRICTED_RMP_EVALUATED")
        self.assertEqual(tree["node_count"], 3)
        self.assertEqual(tree["child_count"], 2)
        self.assertEqual(tree["reported_branch_pair_count"], 1)
        self.assertTrue(tree["restricted_rmp_evaluation_enabled"])
        self.assertEqual(tree["evaluated_node_count"], 3)
        self.assertEqual(tree["child_evaluated_count"], 2)
        self.assertGreaterEqual(tree["child_restricted_rmp_value_count"], 1)
        self.assertFalse(tree["mutates_solver"])
        self.assertFalse(tree["can_certify"])
        self.assertFalse(tree["can_fathom_by_bound"])
        self.assertEqual(tree["exact_status_effect"], "none")
        self.assertEqual(tree["root_node"]["branch_context"]["pair_decision_count"], 0)
        self.assertEqual(tree["root_node"]["solve_status"], "RESTRICTED_RMP_OPTIMAL")
        self.assertEqual(tree["root_node"]["bound_status"], "DIAGNOSTIC_RESTRICTED_RMP_VALUE")
        self.assertFalse(tree["root_node"]["lower_bound_official"])
        self.assertEqual({node["branch_sense"] for node in tree["child_nodes"]}, {SAME_JOURNEY, DIFFERENT_JOURNEY})
        self.assertTrue(all(node["branch_context"]["pair_decision_count"] == 1 for node in tree["child_nodes"]))
        self.assertTrue(all(node["restricted_rmp_evaluated"] for node in tree["child_nodes"]))
        self.assertTrue(all(node["bound_status"] != "NOT_EVALUATED" for node in tree["child_nodes"]))
        self.assertTrue(all(not node["lower_bound_official"] for node in tree["child_nodes"]))
        self.assertTrue(all(not node["can_certify"] for node in tree["child_nodes"]))

    def test_restricted_branch_node_queue_is_diagnostic_only(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_canonical_journey_columns(data, max_exact_tasks=5)
        queue = run_restricted_branch_node_queue(
            data.task_ids,
            universe.columns,
            fleet_size=data.fleet_size,
            max_nodes=7,
            max_depth=2,
            max_candidates_per_node=1,
            data=data,
            direct_pricing_probe_enabled=True,
            direct_pricing_max_tasks=5,
            direct_pricing_max_candidate_sets=2,
            max_pricing_probe_nodes=3,
        )

        self.assertEqual(queue["schema_version"], "lunar_ice_bpc.branch_node_queue.v1")
        self.assertEqual(queue["status"], "RESTRICTED_BRANCH_NODE_QUEUE_EVALUATED")
        self.assertEqual(queue["evaluation_scope"], "supplied_column_pool_only")
        self.assertGreaterEqual(queue["node_count"], 3)
        self.assertLessEqual(queue["node_count"], 7)
        self.assertEqual(queue["evaluated_node_count"], queue["node_count"])
        self.assertGreaterEqual(queue["expanded_node_count"], 1)
        self.assertGreaterEqual(queue["max_depth_reached"], 1)
        self.assertGreaterEqual(queue["restricted_rmp_value_count"], 1)
        self.assertTrue(queue["direct_pricing_probe_enabled"])
        self.assertEqual(queue["direct_pricing_probe_node_count"], 3)
        self.assertFalse(queue["direct_pricing_probe_can_certify_no_negative"])
        self.assertGreaterEqual(queue["post_pricing_restricted_rmp_node_count"], 0)
        self.assertGreaterEqual(queue["post_pricing_added_column_count"], 0)
        self.assertFalse(queue["post_pricing_lower_bound_official"])
        self.assertEqual(queue["node_pricing_certificate_can_certify_count"], 0)
        self.assertEqual(queue["node_bound_fail_closed_count"], queue["node_count"])
        self.assertEqual(queue["node_bound_can_fathom_count"], 0)
        self.assertNotIn("node_bound_incumbent_attached_count", queue)
        self.assertEqual(
            queue["node_pricing_certificate_status_counts"],
            {"NOT_PORTED_TRUE_DUAL_BPC": queue["node_count"]},
        )
        self.assertEqual(queue["node_bound_certificate_status_counts"], {"NODE_BOUND_FAIL_CLOSED": queue["node_count"]})
        self.assertFalse(queue["lower_bound_official"])
        self.assertFalse(queue["mutates_solver"])
        self.assertFalse(queue["can_certify"])
        self.assertFalse(queue["can_fathom_by_bound"])
        self.assertEqual(queue["exact_status_effect"], "none")
        self.assertEqual(queue["nodes"][0]["node_id"], "node_000")
        self.assertIsNone(queue["nodes"][0]["parent_node_id"])
        self.assertTrue(all(node["evaluation_scope"] == "supplied_column_pool_only" for node in queue["nodes"]))
        self.assertTrue(all("fractional_branch_probe" in node for node in queue["nodes"]))
        self.assertTrue(
            all(
                node["fractional_branch_probe_status"]
                in {"FRACTIONAL_BRANCH_PROBE_READY", "NO_FRACTIONAL_BRANCH_CANDIDATE"}
                for node in queue["nodes"]
            )
        )
        branch_sources = {
            node["selected_branch_candidate_source"]
            for node in queue["nodes"]
            if node.get("selected_branch_candidate_source") is not None
        }
        self.assertTrue(branch_sources.issubset({"fractional_rmp_primal", "support_pool"}))
        self.assertTrue(all(not node["lower_bound_official"] for node in queue["nodes"]))
        self.assertTrue(all(not node["can_certify"] for node in queue["nodes"]))
        priced_nodes = [node for node in queue["nodes"] if node["direct_pricing_probe"]["enabled"]]
        self.assertEqual(len(priced_nodes), 3)
        self.assertTrue(
            all(
                node["direct_pricing_probe"]["evaluation_scope"] == "direct_label_probe_filtered_by_branch_context"
                for node in priced_nodes
            )
        )
        self.assertTrue(all(not node["direct_pricing_probe"]["can_certify_no_negative"] for node in priced_nodes))
        self.assertTrue(all(not node["direct_pricing_probe"]["lower_bound_official"] for node in priced_nodes))
        self.assertTrue(all(node["post_pricing_restricted_rmp"]["enabled"] for node in priced_nodes))
        self.assertTrue(all(not node["post_pricing_restricted_rmp"]["lower_bound_official"] for node in priced_nodes))
        self.assertTrue(all(not node["post_pricing_restricted_rmp"]["can_certify"] for node in priced_nodes))
        self.assertTrue(
            all(node["pricing_certificate"]["status"] == "NOT_PORTED_TRUE_DUAL_BPC" for node in queue["nodes"])
        )
        self.assertTrue(all(not node["pricing_certificate"]["can_certify_no_negative"] for node in queue["nodes"]))
        self.assertTrue(
            all(node["node_bound_certificate"]["status"] == "NODE_BOUND_FAIL_CLOSED" for node in queue["nodes"])
        )
        self.assertTrue(all(not node["node_bound_certificate"]["can_fathom_by_bound"] for node in queue["nodes"]))

    def test_canonical_pricing_wrapper_uses_dp_universe(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        priced = price_canonical_journey_universe(data, JourneyDuals(cover={}, fleet_limit=0.0))
        self.assertEqual(priced["status"], "CANONICAL_UNIVERSE_PRICED")
        self.assertEqual(priced["exact_status"], "NOT_BPC_CERTIFIED")
        self.assertGreater(priced["generated_journey_count"], 0)
        self.assertGreater(priced["route_template_count"], 0)

    def test_completion_bound_uses_only_task_cover_duals(self) -> None:
        task_ids = ("a", "b", "c")
        bound = build_positive_cover_completion_bound(task_ids, {"a": 5.0, "b": -7.0, "c": 2.0})
        payload = bound.to_payload()

        self.assertEqual(bound.remaining_lower_bound(("a", "b", "c")), -7.0)
        self.assertEqual(
            bound.optimistic_label_bound(
                current_reduced_base=10.0,
                current_end_time=20.0,
                beta_journey_end_time=0.5,
                remaining_task_ids=("a", "c"),
            ),
            13.0,
        )
        self.assertFalse(payload["includes_fleet_dual"])
        self.assertFalse(payload["includes_cut_duals"])
        self.assertFalse(payload["includes_branch_duals"])
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertTrue(payload["pruning_is_exact_safe"])

    def test_direct_pricing_respects_task_limit(self) -> None:
        instance = generate_instance(10, seed=729101, index=1)
        data = load_lunar_ice_data(instance)
        priced = price_direct_journey_labels(data, JourneyDuals(cover={}, fleet_limit=0.0), max_direct_tasks=5)
        self.assertEqual(priced["status"], "PARTIAL_DIRECT_LABEL_PRICED")
        self.assertEqual(priced["exact_status"], "NOT_SOLVED")
        self.assertFalse(priced["pricing_complete_for_all_tasks"])
        self.assertEqual(priced["candidate_task_count"], 5)
        skipped = price_direct_journey_labels(data, JourneyDuals(cover={}, fleet_limit=0.0), max_direct_tasks=5, allow_partial=False)
        self.assertEqual(skipped["status"], "SKIPPED_TOO_LARGE_FOR_DIRECT_LABEL_PRICING")
        self.assertEqual(skipped["exact_status"], "NOT_SOLVED")

    def test_direct_pricing_uses_cut_duals_without_completion_bound_pruning(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        base_duals = JourneyDuals(cover={}, fleet_limit=0.0)
        base, _ = price_direct_journey_columns(data, base_duals, max_direct_tasks=5)
        context = CutContext((fleet_lower_bound_cut("fleet_lb_active", min_vehicles=1),))
        cut_duals = JourneyDuals(cover={}, fleet_limit=0.0, cuts={"fleet_lb_active": 25.0})
        priced, columns = price_direct_journey_columns(
            data,
            cut_duals,
            max_direct_tasks=5,
            cut_context=context,
            completion_bound_enabled=True,
        )

        self.assertEqual(priced["status"], "DIRECT_LABEL_PRICED")
        self.assertTrue(priced["cut_context_active"])
        self.assertEqual(priced["cut_count"], 1)
        self.assertFalse(priced["completion_bound"]["enabled"])
        self.assertEqual(priced["completion_bound"]["pruned_label_count"], 0)
        self.assertAlmostEqual(
            priced["best_reduced_cost"],
            round(float(base["best_reduced_cost"]) - 25.0, 9),
        )
        best_column = columns[0]
        self.assertAlmostEqual(
            priced["best_reduced_cost"],
            manual_journey_reduced_cost(
                best_column,
                cut_duals,
                cut_coefficients=context.coefficients_for(best_column),
            ),
        )

    def test_direct_pricing_filters_branch_infeasible_columns(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_a, task_b = data.task_ids[:2]
        context = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))
        priced, columns = price_direct_journey_columns(
            data,
            JourneyDuals(cover={task_a: 50.0}, fleet_limit=0.0),
            max_direct_tasks=5,
            seed_task_sets=((task_a,), (task_a, task_b)),
            branch_context=context,
            completion_bound_enabled=True,
        )

        self.assertTrue(priced["branch_context_active"])
        self.assertEqual(priced["branch_decision_count"], 1)
        self.assertGreaterEqual(priced["branch_filtered_column_count"], 1)
        self.assertFalse(priced["completion_bound"]["enabled"])
        self.assertEqual(priced["completion_bound"]["pruned_label_count"], 0)
        self.assertTrue(columns)
        self.assertTrue(all(journey_satisfies_branch_context(column, context) for column in columns))
        self.assertTrue(all(not (task_a in column.task_set and task_b not in column.task_set) for column in columns))

    def test_exhaustive_direct_pricing_covers_all_small_task_subsets_but_cannot_certify(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        priced, columns = price_exhaustive_direct_journey_columns(
            data,
            JourneyDuals(cover={}, fleet_limit=0.0),
            max_direct_tasks=5,
        )

        self.assertEqual(priced["status"], "EXHAUSTIVE_DIRECT_LABEL_PRICED")
        self.assertEqual(priced["exact_status"], "NOT_BPC_CERTIFIED")
        self.assertTrue(priced["pricing_complete_for_all_task_subsets"])
        self.assertEqual(priced["exhaustive_candidate_set_count"], 31)
        self.assertFalse(priced["can_certify_no_negative"])
        self.assertGreater(len(columns), 0)

    def test_direct_pricing_completion_bound_preserves_best_reduced_cost(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 20.0 - index for index, task_id in enumerate(data.task_ids)},
            fleet_limit=3.0,
        )
        pruned, _ = price_direct_journey_columns(data, duals, max_direct_tasks=5, completion_bound_enabled=True)
        unpruned, _ = price_direct_journey_columns(data, duals, max_direct_tasks=5, completion_bound_enabled=False)

        self.assertEqual(pruned["status"], "DIRECT_LABEL_PRICED")
        self.assertEqual(unpruned["status"], "DIRECT_LABEL_PRICED")
        self.assertEqual(pruned["best_reduced_cost"], unpruned["best_reduced_cost"])
        self.assertTrue(pruned["completion_bound"]["enabled"])
        self.assertFalse(unpruned["completion_bound"]["enabled"])
        self.assertFalse(pruned["completion_bound"]["can_certify_no_negative"])
        self.assertFalse(pruned["completion_bound"]["includes_fleet_dual"])
        self.assertGreater(pruned["completion_bound"]["evaluated_label_count"], 0)

    def test_direct_pricing_cache_reuses_sortie_templates(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={}, fleet_limit=0.0)
        cache = DirectPricingCache()
        first, first_columns = price_direct_journey_columns(data, duals, max_direct_tasks=5, cache=cache)
        second, second_columns = price_direct_journey_columns(data, duals, max_direct_tasks=5, cache=cache)

        self.assertTrue(first_columns)
        self.assertTrue(second_columns)
        self.assertEqual(first["best_reduced_cost"], second["best_reduced_cost"])
        self.assertEqual(first["feasible_sortie_template_count"], second["feasible_sortie_template_count"])
        self.assertEqual(first["sortie_template_cache"]["miss_count"], 1)
        self.assertEqual(second["sortie_template_cache"]["hit_count"], 1)
        self.assertGreater(second["sortie_template_cache"]["reused_sortie_attempt_count"], 0)

    def test_config_loader_and_benchmark_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = generate_instance(5, seed=629001, index=1)
            instance_path = root / "data" / "instances" / "lunar_ice_005" / "instance_001_logical_graph.json"
            manifest_path = root / "data" / "manifests" / "manifest.json"
            write_json(instance_path, instance)
            write_json(
                manifest_path,
                {
                    "schema_version": "lunar_ice_bpc.manifest.v1",
                    "instances": [{"path": "data/instances/lunar_ice_005/instance_001_logical_graph.json"}],
                },
            )
            config_path = root / "config.yaml"
            config_path.write_text(
                "instances:\n  - data/instances/lunar_ice_005/instance_001_logical_graph.json\nmax_workers: 4\n",
                encoding="utf-8",
            )
            config = apply_overrides(load_config(config_path), ["max_workers=2"])
            self.assertEqual(config["instances"], ["data/instances/lunar_ice_005/instance_001_logical_graph.json"])
            self.assertEqual(config["max_workers"], 2)
            summary = run_benchmark(project_root=root, manifest_path=manifest_path, max_workers=2)
            self.assertEqual(summary["run_count"], 1)
            self.assertEqual(summary["exact_baseline_optimal_count"], 1)
            self.assertEqual(summary["fixed_graph_root_lp_certified_count"], 1)
            self.assertEqual(summary["exact_claim_scope_counts"], {"fixed_logical_graph_exhaustive_direct_dp": 1})
            self.assertEqual(summary["bpc_certificate_status_counts"], {"CERTIFIED_NO_NEGATIVE": 1})
            self.assertEqual(summary["true_dual_bpc_certificate_count"], 1)
            self.assertEqual(SOLVE_TIME_LIMIT_SEC_BY_SCALE[5], 600.0)
            self.assertEqual(summary["time_limit_exceeded_count"], 0)
            self.assertEqual(summary["certified_optimal_count"], 1)
            self.assertIsNotNone(summary["mean_relaxation_gap"])
            with Path(summary["results_csv"]).open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["lower_bound_source"], "direct_fixed_graph_root_lp")
            self.assertEqual(rows[0]["lower_bound_scope"], "fixed_logical_graph_direct_root")
            self.assertTrue(rows[0]["best_diagnostic_bound_source"])
            solution = json.loads(Path(rows[0]["solution_path"]).read_text(encoding="utf-8"))
            self.assertEqual(solution["lower_bound_source"], "direct_fixed_graph_root_lp")
            self.assertEqual(solution["lower_bound_scope"], "fixed_logical_graph_direct_root")
            self.assertEqual(solution["bound_ledger"]["official_lower_bound_source"], "direct_fixed_graph_root_lp")
            self.assertFalse(solution["bound_ledger"]["diagnostic_bound_is_official"])
            direct_records = [
                record
                for record in solution["bound_ledger"]["records"]
                if record["name"] == "direct_fixed_graph_root_lp"
            ]
            self.assertEqual(len(direct_records), 1)
            self.assertEqual(direct_records[0]["certificate_status"], "BPC_NODE_BOUND_CERTIFIED")
            self.assertTrue(direct_records[0]["official_lower_bound"])
            closure_records = [
                record
                for record in solution["bound_ledger"]["records"]
                if record["name"] == "fixed_graph_pricing_closure_lp"
            ]
            self.assertEqual(len(closure_records), 1)
            self.assertEqual(closure_records[0]["certificate_status"], "BPC_NODE_BOUND_CERTIFIED")
            self.assertTrue(closure_records[0]["official_lower_bound"])
            self.assertEqual(rows[0]["pricing_certificate_status"], "CERTIFIED_NO_NEGATIVE")
            self.assertEqual(rows[0]["pricing_certificate_selected_source"], "true_dual_pricing_tail")
            self.assertEqual(rows[0]["pricing_certificate_true_dual_tail_status"], "TRUE_DUAL_PRICING_TAIL_CERTIFIED")
            self.assertEqual(rows[0]["pricing_certificate_can_certify_no_negative"], "True")
            self.assertEqual(rows[0]["pricing_frontier_status"], "CERTIFIED_FRONTIER_NO_NEGATIVE")
            self.assertEqual(rows[0]["pricing_frontier_lower_bound_official"], "True")
            self.assertEqual(rows[0]["pricing_frontier_can_certify_no_negative"], "True")
            self.assertEqual(summary["pricing_frontier_status_counts"], {rows[0]["pricing_frontier_status"]: 1})
            self.assertEqual(summary["official_pricing_frontier_count"], 1)
            self.assertEqual(solution["true_dual_pricing_tail"]["status"], "TRUE_DUAL_PRICING_TAIL_CERTIFIED")
            self.assertTrue(solution["true_dual_pricing_tail"]["can_certify_no_negative"])
            self.assertTrue(solution["true_dual_pricing_tail"]["dual_vector_bound_to_rmp"])
            self.assertTrue(solution["true_dual_pricing_tail"]["dual_vector_fingerprint"])
            self.assertEqual(solution["true_dual_pricing_tail"]["missing_inputs"], [])
            self.assertEqual(rows[0]["true_dual_pricing_tail_status"], "TRUE_DUAL_PRICING_TAIL_CERTIFIED")
            self.assertEqual(rows[0]["true_dual_pricing_tail_uses_true_dual"], "True")
            self.assertEqual(rows[0]["true_dual_pricing_tail_dual_vector_bound_to_rmp"], "True")
            self.assertTrue(rows[0]["true_dual_pricing_tail_dual_vector_fingerprint"])
            self.assertEqual(rows[0]["true_dual_pricing_tail_can_certify_no_negative"], "True")
            self.assertEqual(rows[0]["true_dual_pricing_tail_lower_bound_official"], "True")
            self.assertEqual(
                summary["true_dual_pricing_tail_status_counts"],
                {"TRUE_DUAL_PRICING_TAIL_CERTIFIED": 1},
            )
            self.assertEqual(summary["true_dual_pricing_tail_certified_count"], 1)
            self.assertEqual(summary["true_dual_pricing_tail_dual_vector_bound_count"], 1)
            self.assertEqual(rows[0]["node_bound_certificate_status"], "NODE_BOUND_FATHOMED")
            self.assertEqual(rows[0]["node_bound_lower_bound_official"], "True")
            self.assertEqual(rows[0]["node_bound_can_fathom_by_bound"], "True")
            self.assertEqual(summary["node_bound_certificate_status_counts"], {"NODE_BOUND_FATHOMED": 1})
            self.assertEqual(summary["node_bound_fathomed_count"], 1)
            self.assertEqual(rows[0]["true_dual_readiness_status"], "TRUE_DUAL_CERTIFICATE_READY")
            self.assertEqual(rows[0]["true_dual_readiness_true_dual_pricing_used"], "True")
            self.assertEqual(rows[0]["true_dual_readiness_diagnostic_fixed_graph_closure_complete"], "True")
            self.assertEqual(
                rows[0]["true_dual_readiness_fixed_graph_closure_status"],
                "FIXED_GRAPH_PRICING_CLOSED",
            )
            self.assertEqual(rows[0]["true_dual_readiness_fixed_graph_closure_no_negative_proved"], "True")
            self.assertEqual(rows[0]["true_dual_readiness_can_certify"], "True")
            self.assertEqual(int(rows[0]["true_dual_readiness_missing_input_count"]), 0)
            self.assertEqual(
                summary["true_dual_readiness_status_counts"],
                {rows[0]["true_dual_readiness_status"]: 1},
            )
            self.assertEqual(summary["true_dual_readiness_missing_input_count"], 0)
            self.assertEqual(rows[0]["branch_probe_status"], "BRANCH_PROBE_READY")
            self.assertEqual(rows[0]["branch_probe_mutates_solver"], "False")
            self.assertEqual(rows[0]["branch_probe_can_certify"], "False")
            self.assertGreaterEqual(int(rows[0]["restricted_rmp_primal_active_column_count"]), 1)
            self.assertLessEqual(float(rows[0]["restricted_rmp_primal_cover_residual_max"]), 1.0e-6)
            self.assertGreater(float(rows[0]["restricted_rmp_primal_fleet_usage"]), 0.0)
            self.assertIn(
                rows[0]["fractional_branch_probe_status"],
                {"FRACTIONAL_BRANCH_PROBE_READY", "NO_FRACTIONAL_BRANCH_CANDIDATE"},
            )
            self.assertEqual(rows[0]["fractional_branch_probe_mutates_solver"], "False")
            self.assertEqual(rows[0]["fractional_branch_probe_can_certify"], "False")
            self.assertEqual(
                summary["fractional_branch_probe_status_counts"],
                {rows[0]["fractional_branch_probe_status"]: 1},
            )
            self.assertEqual(rows[0]["branch_tree_probe_status"], "BRANCH_TREE_RESTRICTED_RMP_EVALUATED")
            self.assertEqual(rows[0]["branch_tree_probe_node_count"], "3")
            self.assertEqual(rows[0]["branch_tree_probe_child_count"], "2")
            self.assertEqual(rows[0]["branch_tree_probe_reported_branch_pair_count"], "1")
            self.assertEqual(rows[0]["branch_tree_probe_restricted_rmp_evaluation_enabled"], "True")
            self.assertEqual(rows[0]["branch_tree_probe_evaluated_node_count"], "3")
            self.assertEqual(rows[0]["branch_tree_probe_child_evaluated_count"], "2")
            self.assertGreaterEqual(int(rows[0]["branch_tree_probe_child_restricted_rmp_value_count"]), 1)
            self.assertEqual(rows[0]["branch_tree_probe_mutates_solver"], "False")
            self.assertEqual(rows[0]["branch_tree_probe_can_certify"], "False")
            self.assertEqual(summary["branch_tree_probe_status_counts"], {"BRANCH_TREE_RESTRICTED_RMP_EVALUATED": 1})
            self.assertEqual(summary["branch_tree_probe_evaluated_node_count"], 3)
            self.assertEqual(summary["branch_tree_probe_child_evaluated_count"], 2)
            self.assertEqual(rows[0]["branch_node_queue_status"], "RESTRICTED_BRANCH_NODE_QUEUE_EVALUATED")
            self.assertGreaterEqual(int(rows[0]["branch_node_queue_node_count"]), 3)
            self.assertEqual(rows[0]["branch_node_queue_evaluated_node_count"], rows[0]["branch_node_queue_node_count"])
            self.assertGreaterEqual(int(rows[0]["branch_node_queue_expanded_node_count"]), 1)
            self.assertGreaterEqual(int(rows[0]["branch_node_queue_restricted_rmp_value_count"]), 1)
            self.assertEqual(rows[0]["branch_node_queue_direct_pricing_probe_enabled"], "True")
            self.assertEqual(rows[0]["branch_node_queue_direct_pricing_probe_node_count"], "3")
            self.assertEqual(rows[0]["branch_node_queue_direct_pricing_probe_can_certify_no_negative"], "False")
            self.assertGreaterEqual(int(rows[0]["branch_node_queue_post_pricing_restricted_rmp_node_count"]), 0)
            self.assertGreaterEqual(int(rows[0]["branch_node_queue_post_pricing_added_column_count"]), 0)
            self.assertEqual(rows[0]["branch_node_queue_post_pricing_lower_bound_official"], "False")
            self.assertEqual(rows[0]["branch_node_queue_node_pricing_certificate_can_certify_count"], "0")
            self.assertEqual(
                rows[0]["branch_node_queue_node_bound_incumbent_attached_count"],
                rows[0]["branch_node_queue_node_count"],
            )
            self.assertEqual(rows[0]["branch_node_queue_node_bound_incumbent_missing_count"], "0")
            self.assertEqual(
                rows[0]["branch_node_queue_node_bound_fail_closed_count"],
                rows[0]["branch_node_queue_node_count"],
            )
            self.assertEqual(rows[0]["branch_node_queue_node_bound_can_fathom_count"], "0")
            self.assertEqual(rows[0]["branch_node_queue_lower_bound_official"], "False")
            self.assertEqual(rows[0]["branch_node_queue_mutates_solver"], "False")
            self.assertEqual(rows[0]["branch_node_queue_can_certify"], "False")
            self.assertEqual(
                summary["branch_node_queue_status_counts"],
                {"RESTRICTED_BRANCH_NODE_QUEUE_EVALUATED": 1},
            )
            self.assertGreaterEqual(summary["branch_node_queue_evaluated_node_count"], 3)
            self.assertGreaterEqual(summary["branch_node_queue_expanded_node_count"], 1)
            self.assertEqual(summary["branch_node_queue_direct_pricing_probe_node_count"], 3)
            self.assertGreaterEqual(summary["branch_node_queue_post_pricing_restricted_rmp_node_count"], 0)
            self.assertGreaterEqual(summary["branch_node_queue_post_pricing_added_column_count"], 0)
            self.assertEqual(summary["branch_node_queue_node_pricing_certificate_can_certify_count"], 0)
            self.assertEqual(
                summary["branch_node_queue_node_bound_incumbent_attached_count"],
                int(rows[0]["branch_node_queue_node_count"]),
            )
            self.assertEqual(summary["branch_node_queue_node_bound_incumbent_missing_count"], 0)
            self.assertEqual(
                summary["branch_node_queue_node_bound_fail_closed_count"],
                int(rows[0]["branch_node_queue_node_count"]),
            )
            self.assertEqual(summary["branch_node_queue_node_bound_can_fathom_count"], 0)
            self.assertEqual(rows[0]["restricted_rmp_cut_count"], "0")
            self.assertEqual(rows[0]["restricted_rmp_cut_rows_active"], "False")
            self.assertEqual(rows[0]["cut_probe_status"], "CUT_PROBE_READY")
            self.assertGreaterEqual(int(rows[0]["cut_probe_subset_candidate_count"]), 1)
            self.assertEqual(rows[0]["cut_probe_rows_added_to_rmp"], "0")
            self.assertEqual(rows[0]["cut_probe_cut_rows_active"], "False")
            self.assertEqual(rows[0]["cut_probe_mutates_solver"], "False")
            self.assertEqual(rows[0]["cut_probe_can_certify"], "False")
            self.assertEqual(summary["cut_probe_status_counts"], {"CUT_PROBE_READY": 1})
            self.assertIn("cut_probe_violated_subset_candidate_count", summary)
            self.assertEqual(rows[0]["direct_pricing_completion_bound_enabled"], "True")
            self.assertEqual(rows[0]["direct_pricing_completion_bound_can_certify"], "False")
            self.assertGreaterEqual(int(rows[0]["direct_pricing_completion_bound_evaluated_label_count"]), 1)
            self.assertEqual(rows[0]["direct_pricing_branch_context_active"], "False")
            self.assertEqual(rows[0]["direct_pricing_branch_decision_count"], "0")
            self.assertEqual(rows[0]["direct_pricing_branch_filtered_column_count"], "0")
            self.assertEqual(
                rows[0]["fixed_graph_pricing_proof_status"],
                "FIXED_GRAPH_NEGATIVE_REDUCED_COST_FOUND",
            )
            self.assertEqual(rows[0]["fixed_graph_pricing_proof_complete"], "True")
            self.assertEqual(rows[0]["fixed_graph_pricing_proof_negative_found"], "True")
            self.assertEqual(rows[0]["fixed_graph_pricing_proof_no_negative_proved"], "False")
            self.assertEqual(rows[0]["fixed_graph_pricing_proof_uses_true_dual_bpc_certificate"], "False")
            self.assertEqual(rows[0]["fixed_graph_pricing_proof_lower_bound_official"], "False")
            self.assertEqual(rows[0]["fixed_graph_pricing_proof_can_certify_no_negative"], "False")
            self.assertEqual(rows[0]["fixed_graph_pricing_closure_status"], "FIXED_GRAPH_PRICING_CLOSED")
            self.assertGreaterEqual(int(rows[0]["fixed_graph_pricing_closure_round_count"]), 2)
            self.assertGreater(int(rows[0]["fixed_graph_pricing_closure_added_column_count"]), 0)
            self.assertEqual(rows[0]["fixed_graph_pricing_closure_no_negative_proved"], "True")
            self.assertEqual(rows[0]["fixed_graph_pricing_closure_uses_true_dual_bpc_certificate"], "True")
            self.assertEqual(rows[0]["fixed_graph_pricing_closure_lower_bound_official"], "True")
            self.assertEqual(rows[0]["fixed_graph_pricing_closure_can_certify_no_negative"], "True")
            self.assertEqual(rows[0]["completion_bound_consistency_status"], "COMPLETION_BOUND_CONSISTENT")
            self.assertEqual(rows[0]["completion_bound_consistency_consistent"], "True")
            self.assertEqual(
                rows[0]["completion_bound_consistency_with_bound_best_reduced_cost"],
                rows[0]["completion_bound_consistency_without_bound_best_reduced_cost"],
            )
            self.assertEqual(rows[0]["completion_bound_consistency_can_certify_no_negative"], "False")
            self.assertEqual(summary["completion_bound_consistency_pass_count"], 1)
            self.assertIn("direct_pricing_completion_bound_evaluated_label_count", summary)
            self.assertGreaterEqual(summary["direct_pricing_completion_bound_evaluated_label_count"], 1)
            audit = audit_benchmark_csv(summary["results_csv"], scales=(5,), expected_per_scale=1)
            self.assertEqual(audit["overall_status"], "PASS")
            self.assertEqual(audit["scales"]["005"]["node_count_reported_count"], 1)
            self.assertEqual(audit["scales"]["005"]["incomplete_reason_reported_count"], 1)
            self.assertEqual(
                audit["scales"]["005"]["exact_claim_scope_counts"],
                {"fixed_logical_graph_exhaustive_direct_dp": 1},
            )
            self.assertEqual(audit["scales"]["005"]["true_dual_bpc_certificate_count"], 1)
            self.assertEqual(audit["scales"]["005"]["no_negative_certificate_count"], 1)
            self.assertEqual(audit["scales"]["005"]["true_dual_pricing_tail_certified_count"], 1)
            self.assertEqual(audit["scales"]["005"]["true_dual_pricing_tail_not_ported_count"], 0)
            self.assertEqual(audit["scales"]["005"]["true_dual_pricing_tail_dual_vector_bound_count"], 1)
            self.assertEqual(
                audit["scales"]["005"]["true_dual_pricing_tail_status_counts"],
                {"TRUE_DUAL_PRICING_TAIL_CERTIFIED": 1},
            )
            self.assertEqual(audit["scales"]["005"]["fixed_graph_pricing_closure_closed_count"], 1)
            self.assertEqual(audit["scales"]["005"]["fixed_graph_pricing_closure_diagnostic_only_count"], 0)
            self.assertEqual(audit["scales"]["005"]["completion_bound_consistency_pass_count"], 1)
            self.assertEqual(
                audit["scales"]["005"]["completion_bound_consistency_status_counts"],
                {"COMPLETION_BOUND_CONSISTENT": 1},
            )
            self.assertEqual(
                audit["scales"]["005"]["fixed_graph_pricing_closure_status_counts"],
                {"FIXED_GRAPH_PRICING_CLOSED": 1},
            )
            self.assertEqual(audit["scales"]["005"]["true_dual_readiness_waiting_true_dual_count"], 0)
            self.assertEqual(
                audit["scales"]["005"]["true_dual_readiness_status_counts"],
                {"TRUE_DUAL_CERTIFICATE_READY": 1},
            )
            self.assertEqual(
                audit["scales"]["005"]["pricing_certificate_status_counts"],
                {"CERTIFIED_NO_NEGATIVE": 1},
            )
            self.assertEqual(
                audit["scales"]["005"]["pricing_certificate_selected_source_counts"],
                {"true_dual_pricing_tail": 1},
            )

    def test_benchmark_manifest_records_generation_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = generate_benchmark(
                output_root=root / "data" / "instances",
                manifest_path=root / "data" / "manifests" / "manifest.json",
                project_root=root,
                scales=(5, 10),
                per_scale=1,
                seed_base=629000,
            )

            self.assertEqual(manifest["generator"], SYNTHETIC_GENERATOR_ID)
            self.assertEqual(manifest["risk_schema_version"], RISK_SCHEMA_VERSION)
            self.assertEqual(manifest["time_window_policy_id"], TIME_WINDOW_POLICY_ID)
            self.assertEqual(manifest["path_option_policy_id"], PATH_OPTION_POLICY_ID)
            self.assertEqual(manifest["resource_map_extent_km"], LunarIceConfig().resource_map_extent_km)
            self.assertEqual(manifest["synthetic_grid_resolution_m"], LunarIceConfig().synthetic_grid_resolution_m)
            self.assertEqual(manifest["B_use"], LunarIceConfig().b_use)
            self.assertEqual(manifest["accepted_total_count"], 2)
            self.assertEqual(manifest["total_target_count"], 2)
            self.assertEqual(manifest["status"], "complete")
            for label in ("005", "010"):
                row = manifest["scales"][label]
                scale = int(label)
                self.assertEqual(row["accepted_count"], 1)
                self.assertGreaterEqual(row["attempt_count"], 1)
                self.assertIn("skip_reason_counts", row)
                self.assertEqual(row["risk_schema_version"], RISK_SCHEMA_VERSION)
                self.assertEqual(row["time_window_policy_id"], TIME_WINDOW_POLICY_ID)
                self.assertEqual(row["active_footprint_km"], ACTIVE_FOOTPRINT_BY_SCALE[scale])
                self.assertEqual(row["max_shadow_exposure_per_sortie"], SHADOW_CAP_BY_SCALE[scale])
            for item in manifest["instances"]:
                scale = int(item["scale"])
                self.assertIn("attempt_index", item)
                self.assertLessEqual(float(item["max_window_width"]), float(item["max_effective_window_width_cap"]) + 1.0e-9)
                self.assertEqual(item["risk_schema_version"], RISK_SCHEMA_VERSION)
                self.assertEqual(item["time_window_policy_id"], TIME_WINDOW_POLICY_ID)
                self.assertEqual(item["path_option_policy_id"], PATH_OPTION_POLICY_ID)
                self.assertEqual(item["synthetic_grid_resolution_m"], LunarIceConfig().synthetic_grid_resolution_m)
                self.assertEqual(item["active_footprint_km"], ACTIVE_FOOTPRINT_BY_SCALE[scale])
                self.assertEqual(item["B_use"], LunarIceConfig().b_use)
                self.assertEqual(item["max_shadow_exposure_per_sortie"], SHADOW_CAP_BY_SCALE[scale])

    def test_custom_generation_manifest_paths_are_project_relative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "runs" / "generation_audit" / "manifest.json"
            manifest = generate_benchmark(
                output_root=root / "runs" / "generation_audit" / "instances",
                manifest_path=manifest_path,
                project_root=root,
                scales=(5,),
                per_scale=1,
                seed_base=629000,
            )
            path = Path(manifest["instances"][0]["path"])
            self.assertFalse(path.is_absolute())
            self.assertTrue((root / path).exists())
            summary = run_benchmark(
                project_root=root,
                manifest_path=manifest_path,
                max_workers=1,
                results_csv=root / "runs" / "generation_audit" / "audit.csv",
                solution_dir=root / "runs" / "generation_audit" / "solutions",
                summary_json=root / "runs" / "generation_audit" / "summary.json",
            )
            self.assertEqual(summary["run_count"], 1)
            self.assertEqual(summary["exact_baseline_optimal_count"], 1)

    def test_benchmark_script_accepts_config_file(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance_5 = generate_instance(5, seed=629001, index=1)
            instance_10 = generate_instance(10, seed=729001, index=1)
            instance_5_path = root / "instances" / "lunar_ice_005" / "instance.json"
            instance_10_path = root / "instances" / "lunar_ice_010" / "instance.json"
            manifest_path = root / "manifest.json"
            write_json(instance_5_path, instance_5)
            write_json(instance_10_path, instance_10)
            write_json(
                manifest_path,
                {
                    "schema_version": "lunar_ice_bpc.manifest.v1",
                    "instances": [
                        {"scale": 5, "scale_label": "005", "path": str(instance_5_path)},
                        {"scale": 10, "scale_label": "010", "path": str(instance_10_path)},
                    ],
                },
            )
            config_path = root / "benchmark.yaml"
            results_csv = root / "benchmark.csv"
            solution_dir = root / "solutions"
            summary_json = root / "summary.json"
            config_path.write_text(
                "\n".join(
                    [
                        "master_mode: journey",
                        f"manifest: {manifest_path}",
                        "scales: [5]",
                        "max_workers: 1",
                        f"results_csv: {results_csv}",
                        f"solution_dir: {solution_dir}",
                        f"summary_json: {summary_json}",
                        "time_limit: 600",
                        "canonical_dp_max_tasks: 10",
                        "direct_pricing_max_tasks: 5",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(project_root / "scripts" / "run_lunar_ice_benchmark.py"), "--config", str(config_path)],
                cwd=project_root,
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn("ran 1 instances", completed.stdout)
            summary = json.loads(summary_json.read_text(encoding="utf-8"))
            self.assertEqual(summary["run_count"], 1)
            self.assertEqual(summary["fixed_graph_root_lp_certified_count"], 1)
            self.assertEqual(summary["time_limit_exceeded_count"], 0)
            self.assertTrue((solution_dir / "lunar_ice_005" / "instance_solution.json").exists())
            self.assertFalse((solution_dir / "lunar_ice_010" / "instance_solution.json").exists())
            audit_json = root / "audit.json"
            audit_completed = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "scripts" / "audit_lunar_ice_benchmark.py"),
                    "--results-csv",
                    str(results_csv),
                    "--output-json",
                    str(audit_json),
                    "--scales",
                    "5",
                    "--expected-per-scale",
                    "1",
                ],
                cwd=project_root,
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn("audit PASS", audit_completed.stdout)
            audit_payload = json.loads(audit_json.read_text(encoding="utf-8"))
            self.assertEqual(audit_payload["overall_status"], "PASS")

    def test_shadow_guidance_is_diagnostic_only(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        graph = build_guidance_graph(instance)
        report = build_shadow_report(instance)
        schema_text = " ".join(graph["node_feature_schema"] + graph["edge_feature_schema"]).lower()
        self.assertNotIn("comm", schema_text)
        self.assertNotIn("earth", schema_text)
        self.assertEqual(report["mode"], "shadow_only")
        self.assertFalse(report["mutates_solver"])
        self.assertFalse(report["can_certify"])
        self.assertEqual(report["exact_status_effect"], "none")
        self.assertEqual(report["node_count"], len(instance["tasks"]))
        self.assertTrue(report["task_priority"])

    def test_shadow_cli_accepts_only_shadow_config(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = generate_instance(5, seed=629001, index=1)
            instance_path = root / "instance.json"
            shadow_config = root / "shadow.yaml"
            optin_config = root / "optin.yaml"
            output_path = root / "shadow_report.json"
            write_json(instance_path, instance)
            shadow_config.write_text(
                "\n".join(
                    [
                        "guidance_mode: shadow_only",
                        "journey_gat_shadow_enabled: true",
                        "journey_gat_optin_enabled: false",
                        "mutates_solver: false",
                        "can_certify: false",
                        f"instance: {instance_path}",
                        f"output: {output_path}",
                        "expected_shadow_report_schema_version: lunar_ice_bpc.gat_shadow_report.v1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(project_root / "scripts" / "run_lunar_ice_gat_shadow.py"), "--config", str(shadow_config)],
                cwd=project_root,
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn("mode=shadow_only", completed.stdout)
            shadow_payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(shadow_payload["mutates_solver"])
            self.assertFalse(shadow_payload["can_certify"])

            optin_config.write_text(
                "\n".join(
                    [
                        "guidance_mode: opt_in",
                        "journey_gat_shadow_enabled: true",
                        "journey_gat_optin_enabled: true",
                        "mutates_solver: true",
                        "can_certify: false",
                        f"instance: {instance_path}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            rejected = subprocess.run(
                [sys.executable, str(project_root / "scripts" / "run_lunar_ice_gat_shadow.py"), "--config", str(optin_config)],
                cwd=project_root,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("guidance_mode", rejected.stderr)

    def test_shadow_cli_batches_manifest_by_scale(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance_5 = generate_instance(5, seed=629001, index=1)
            instance_10 = generate_instance(10, seed=729001, index=1)
            instance_5_path = root / "instances" / "lunar_ice_005" / "instance.json"
            instance_10_path = root / "instances" / "lunar_ice_010" / "instance.json"
            manifest_path = root / "manifest.json"
            output_dir = root / "shadow_reports"
            summary_path = root / "shadow_summary.json"
            write_json(instance_5_path, instance_5)
            write_json(instance_10_path, instance_10)
            write_json(
                manifest_path,
                {
                    "schema_version": "lunar_ice_bpc.manifest.v1",
                    "instances": [
                        {"scale": 5, "scale_label": "005", "path": str(instance_5_path)},
                        {"scale": 10, "scale_label": "010", "path": str(instance_10_path)},
                    ],
                },
            )
            config_path = root / "batch_shadow.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "guidance_mode: shadow_only",
                        "journey_gat_shadow_enabled: true",
                        "journey_gat_optin_enabled: false",
                        "mutates_solver: false",
                        "can_certify: false",
                        f"manifest: {manifest_path}",
                        "scales: [10]",
                        f"output_dir: {output_dir}",
                        f"summary_json: {summary_path}",
                        "expected_guidance_graph_schema_version: lunar_ice_bpc.guidance_graph.v1",
                        "expected_shadow_report_schema_version: lunar_ice_bpc.gat_shadow_report.v1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(project_root / "scripts" / "run_lunar_ice_gat_shadow.py"), "--config", str(config_path)],
                cwd=project_root,
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn("wrote 1 shadow reports", completed.stdout)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["run_count"], 1)
            self.assertEqual(summary["mode_counts"], {"shadow_only": 1})
            self.assertEqual(summary["exact_status_effect_counts"], {"none": 1})
            self.assertEqual(summary["mutates_solver_count"], 0)
            self.assertEqual(summary["can_certify_count"], 0)
            report_path = Path(summary["reports"][0]["report_path"])
            self.assertTrue(report_path.exists())
            self.assertIn("lunar_ice_010", str(report_path))

    def test_refactor_audit_reports_current_state_boundaries(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "refactor_audit.json"
            payload = audit_refactor_state(
                project_root,
                output_json=output_path,
                instance_samples_per_scale=1,
            )
            self.assertTrue(output_path.exists())
            self.assertEqual(payload["overall_status"], "IN_PROGRESS")
            self.assertEqual(payload["hard_failure_sections"], [])
            self.assertIn("benchmark_evidence", payload["incomplete_sections"])
            self.assertEqual(payload["sections"]["runtime_legacy_link_scan"]["status"], "PASS")
            self.assertEqual(payload["sections"]["manifest"]["status"], "PASS")
            self.assertEqual(payload["sections"]["manifest"]["validated_instance_count"], 6)
            self.assertEqual(payload["sections"]["gat_shadow"]["status"], "PASS")
            benchmark = payload["sections"]["benchmark_evidence"]
            self.assertEqual(benchmark["status"], "INCOMPLETE")
            self.assertEqual(benchmark["scales"]["005"]["audit_status"], "PASS")
            self.assertEqual(benchmark["scales"]["010"]["audit_status"], "PASS")
            self.assertEqual(benchmark["scales"]["020"]["audit_status"], "PASS")
            self.assertEqual(benchmark["scales"]["100"]["audit_status"], "PASS")
            self.assertEqual(benchmark["scales"]["005"]["true_dual_bpc_certificate_count"], 20)
            self.assertEqual(benchmark["scales"]["005"]["true_dual_pricing_tail_certified_count"], 20)
            self.assertEqual(benchmark["scales"]["010"]["true_dual_bpc_certificate_count"], 20)
            self.assertEqual(benchmark["scales"]["010"]["true_dual_pricing_tail_certified_count"], 20)
            self.assertEqual(benchmark["scales"]["020"]["true_dual_bpc_certificate_count"], 0)
            self.assertEqual(benchmark["scales"]["030"]["exact_optimal_count"], 0)
            self.assertEqual(benchmark["scales"]["050"]["exact_optimal_count"], 0)
            self.assertEqual(
                benchmark["incomplete"],
                ["030: final exact closure target is not met yet", "050: final exact closure target is not met yet"],
            )
            for label in ("005", "010", "030", "050"):
                self.assertIn("fixed_graph_pricing_closure_closed_count", benchmark["scales"][label])
                self.assertIn("fixed_graph_pricing_closure_diagnostic_only_count", benchmark["scales"][label])
                self.assertIn("completion_bound_consistency_pass_count", benchmark["scales"][label])
                self.assertIn("true_dual_pricing_tail_certified_count", benchmark["scales"][label])
                self.assertIn("true_dual_pricing_tail_not_ported_count", benchmark["scales"][label])
                self.assertIn("true_dual_pricing_tail_dual_vector_bound_count", benchmark["scales"][label])
                self.assertIn("true_dual_readiness_waiting_true_dual_count", benchmark["scales"][label])
            self.assertEqual(benchmark["true_dual_bpc_certificate_total"], 40)


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


if __name__ == "__main__":
    unittest.main()
