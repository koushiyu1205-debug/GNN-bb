from __future__ import annotations

import csv
import importlib.util
import inspect
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

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
from lunar_ice_bpc.domain.real_maps import (
    REAL_MAP_REQUIRED_LOLA_LAYERS,
    REAL_MAP_SOURCE_CATALOG_SCHEMA_VERSION,
    build_real_map_edge_options,
    build_real_map_preview,
    real_map_source_catalog,
    write_real_map_preview_svg,
)
from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.bpc.certificates.certificate_ledger import CertificateLedger
from lunar_ice_bpc.exact.bpc.certificates.proof_debt_queue import ProofDebtQueue
from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import ColumnSemanticSignature, column_signature_from_journey
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
from lunar_ice_bpc.exact.bpc.core.task_index import TaskIndexMap
from lunar_ice_bpc.exact.bpc.guidance.shadow import build_guidance_output_bundle
from lunar_ice_bpc.exact.bpc.master.reduced_cost import ReducedCostContext
from lunar_ice_bpc.exact.bpc.pricing.status import (
    AlgorithmStatus,
    CertificateScope,
    PricingState,
    certificate_scope_for_algorithm_status,
)
from lunar_ice_bpc.exact.bpc.pricing.completion_bounds import build_completion_bound_tail_policy
from lunar_ice_bpc.exact.bpc.pricing.duplicate_only_audit import build_duplicate_only_audit
from lunar_ice_bpc.exact.bpc.pricing.dual_stabilization import (
    build_tail_dual_center,
    build_worker_duals_with_tail_center,
)
from lunar_ice_bpc.exact.bpc.pricing.harvest import harvest_addable_negative_columns
from lunar_ice_bpc.exact.bpc.pricing.hidden_negative_audit import build_hidden_negative_audit
from lunar_ice_bpc.exact.bpc.pricing import final_judge as final_judge_module
from lunar_ice_bpc.exact.bpc.pricing.final_judge import _run_compact_single_journey_pricing_final_judge
from lunar_ice_bpc.exact.bpc.cuts.cut_audit import (
    audit_cut_reduced_cost_consistency,
    build_cut_dominance_compatibility_report,
    cut_aware_column_signature_from_journey,
    cut_coefficient_vector_hash,
)
from lunar_ice_bpc.exact.bpc.solver.branch_tree_solver import (
    B3_COMPLETE_UNIVERSE_NODE_MODE,
    TASK_SUBSET_REPRESENTATIVE_UNIVERSE_SEMANTICS,
    _QueuedNode,
    _solve_b3_node,
    _tree_payload,
    solve_b3_branch_price_tree_baseline,
)
from lunar_ice_bpc.exact.bpc.solver.cut_formulation_solver import solve_b4_cut_formulation_baseline
from lunar_ice_bpc.exact.bpc.solver.gat_guidance_solver import (
    run_b5_guidance_ablation_suite,
    solve_b5_gat_guidance_shadow_baseline,
)
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (
    B2A_MODE,
    B2B_MODE,
    B2B_R2_MODE,
    B2B_R3_MODE,
    B2C_MODE,
    B2D_MODE,
    B2_PRODUCT_MODE,
    solve_node_pricing_with_b2b_r3,
    solve_b2_pricing_tail_baseline,
)
import lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver as pricing_tail_solver_module
from lunar_ice_bpc.exact.bpc.solver.root_node_solver import solve_b1_root_node_baseline
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
    CutDefinition,
    CutContext,
    cut_coefficients_for_journey,
    cut_context_from_payload,
    fleet_lower_bound_cut,
    subset_row_cut,
)
from lunar_ice_bpc.exact.core.columns import build_timed_sortie
from lunar_ice_bpc.exact.core.journey import journey_column_from_solution_payload
import lunar_ice_bpc.exact.core.objective as objective_module
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals, manual_journey_reduced_cost, solve_restricted_journey_rmp
from lunar_ice_bpc.exact.pricing.completion_bounds import build_positive_cover_completion_bound
from lunar_ice_bpc.exact.pricing.journey_pricing import (
    DirectPricingCache,
    price_canonical_journey_universe,
    price_direct_journey_columns,
    price_direct_journey_columns_incremental,
    price_exhaustive_direct_journey_columns,
    price_direct_journey_labels,
)
import lunar_ice_bpc.exact.pricing.journey_pricing as journey_pricing_module
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
from lunar_ice_bpc.exact.solver.gurobi_compact import (
    solve_highs_compact_fixed_graph,
    solve_highs_compact_single_journey_pricing,
)
import lunar_ice_bpc.exact.solver.gurobi_compact as gurobi_compact_module
from lunar_ice_bpc.exact.solver.column_pool import select_journey_column_pool
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
import lunar_ice_bpc.runners.b0_b1_ablation as b0_b1_ablation_module
import lunar_ice_bpc.runners.b2_pricing_tail_ablation as b2_pricing_tail_ablation_module
import lunar_ice_bpc.runners.b3_branch_tree_ablation as b3_branch_tree_ablation_module
import lunar_ice_bpc.runners.b4_1_true_dual_proof_tail as b4_1_runner_module
from lunar_ice_bpc.runners.b4_cut_formulation_ablation import (
    B4A_MODE,
    B4B_MODE,
    run_b4_cut_formulation_ablation,
    write_b4_cut_formulation_artifacts,
)
from lunar_ice_bpc.runners.b4_1_true_dual_proof_tail import (
    build_b4_1_report,
    write_b4_1_artifacts,
)
from lunar_ice_bpc.runners.b4_pricing_formulation_diagnostic import (
    B4D_VARIANT_CONFIGS,
    b4_pricing_matrix_row_key,
    build_b4_pricing_formulation_report_from_rows,
    iter_b4_pricing_formulation_matrix_rows_from_probe,
    run_b4_pricing_formulation_diagnostic_from_json,
    run_b4_pricing_formulation_matrix_from_probe,
    write_b4_pricing_formulation_artifacts,
)
from lunar_ice_bpc.runners.b0_b1_ablation import (
    B0_MODE,
    B1A_MODE,
    B1B_MODE,
    run_b0_b1_ablation,
)
from lunar_ice_bpc.runners.b2_pricing_tail_ablation import (
    _acceptance,
    _row_from_raw,
    merge_b2_pricing_tail_reports,
    render_b2_pricing_tail_markdown,
    run_b2_pricing_tail_b2b_r2_incremental,
    run_b2_pricing_tail_ablation,
    write_b2_pricing_tail_ablation_artifacts,
)
from lunar_ice_bpc.runners.benchmark import run_benchmark
from lunar_ice_bpc.runners.refactor_audit import _audit_b5_guidance_suite, audit_refactor_state
from lunar_ice_bpc.runners.generate_instances import generate_benchmark
from lunar_ice_bpc.runners.solve import _fallback_baseline_for_reporting, solve_reference


class LunarIceSmokeTests(unittest.TestCase):
    def test_real_map_source_catalog_records_required_lola_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            catalog = real_map_source_catalog(Path(tmp) / "raw_maps")
        self.assertEqual(catalog["schema_version"], REAL_MAP_SOURCE_CATALOG_SCHEMA_VERSION)
        self.assertEqual(tuple(catalog["required_lola_layers"]), REAL_MAP_REQUIRED_LOLA_LAYERS)
        by_key = {item["key"]: item for item in catalog["layers"]}
        for key in REAL_MAP_REQUIRED_LOLA_LAYERS:
            self.assertIn(key, by_key)
            self.assertTrue(by_key[key]["required_for_lola_preview"])
            self.assertFalse(by_key[key]["local_exists"])
            self.assertTrue(by_key[key]["source_url"].startswith("https://"))
        self.assertFalse(catalog["local_ready"])

    def test_real_map_preview_missing_layers_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            preview = build_real_map_preview(raw_map_dir=root / "raw_maps")
            svg_path = root / "real_map_preview.svg"
            write_real_map_preview_svg(preview, svg_path)
            self.assertTrue(svg_path.exists())
        self.assertEqual(preview["status"], "MISSING_REQUIRED_REAL_MAP_LAYERS")
        self.assertFalse(preview["uses_synthetic_fallback"])
        self.assertEqual(tuple(preview["missing_required_lola_layers"]), REAL_MAP_REQUIRED_LOLA_LAYERS)
        self.assertEqual(preview["targets"], [])
        self.assertEqual(preview["path_options"], [])

    def test_real_map_preview_reads_local_geotiffs_and_builds_paths(self) -> None:
        try:
            import numpy as np
            import rasterio
            from rasterio.transform import from_origin
        except Exception as exc:
            self.skipTest(f"rasterio/numpy unavailable: {exc}")
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp) / "raw_maps"
            raw_dir.mkdir()
            n = 48
            y, x = np.mgrid[0:n, 0:n]
            slope = (x + y).astype("float32") / float(2 * n)
            roughness = np.abs(x - y).astype("float32") / float(n)
            dem = x.astype("float32") * 20.0
            psr = np.zeros((n, n), dtype="float32")
            psr[6:20, 28:42] = 1.0
            transform = from_origin(-15000.0, 15000.0, 30000.0 / n, 30000.0 / n)
            for filename, array in (
                ("LOLA_80S_dem_80m.tif", dem),
                ("LOLA_80S_slope_100m.tif", slope),
                ("LOLA_80S_roughness_100m.tif", roughness),
                ("LOLA_80S_psr_20m.tif", psr),
            ):
                with rasterio.open(
                    raw_dir / filename,
                    "w",
                    driver="GTiff",
                    height=n,
                    width=n,
                    count=1,
                    dtype="float32",
                    transform=transform,
                    nodata=-9999.0,
                ) as dataset:
                    dataset.write(array, 1)
            preview = build_real_map_preview(
                raw_map_dir=raw_dir,
                output_cells=40,
                target_count=5,
                path_target_count=2,
                active_footprint_km=12.0,
            )
            edges = build_real_map_edge_options(
                raw_map_dir=raw_dir,
                nodes={"west": (8.0, 15.0), "east": (22.0, 15.0)},
                output_cells=40,
            )
        self.assertEqual(preview["status"], "REAL_MAP_PREVIEW_READY")
        self.assertFalse(preview["uses_synthetic_fallback"])
        self.assertEqual(preview["missing_required_lola_layers"], [])
        self.assertEqual(len(preview["targets"]), 5)
        self.assertEqual(len(preview["path_options"]), 2 * len(PATH_TYPES))
        self.assertEqual({option["path_type"] for option in preview["path_options"]}, set(PATH_TYPES))
        for option in preview["path_options"]:
            self.assertGreater(option["path_distance_km"], 0.0)
            self.assertGreater(option["travel_time_min"], 0.0)
            self.assertGreater(option["energy_proxy"], 0.0)
            self.assertGreaterEqual(option["risk_integral"], 0.0)
            self.assertGreaterEqual(option["shadow_exposure_min"], 0.0)
            self.assertIn("generalized_cost", option)
            self.assertEqual(option["directional_elevation_status"], "available")
        for target in preview["targets"]:
            self.assertLessEqual(abs(float(target["xy_km"][0]) - 15.0), 6.0 + 1.0e-9)
            self.assertLessEqual(abs(float(target["xy_km"][1]) - 15.0), 6.0 + 1.0e-9)
        by_direction = {(edge["from"], edge["to"]): {option["path_type"]: option for option in edge["path_options"]} for edge in edges}
        uphill = by_direction[("west", "east")]["low_energy"]
        downhill = by_direction[("east", "west")]["low_energy"]
        self.assertGreater(uphill["positive_elevation_gain_m"], downhill["positive_elevation_gain_m"])
        self.assertGreater(uphill["energy_proxy"], downhill["energy_proxy"])

    def test_real_map_download_script_dry_run_records_planned_layers(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "download_manifest.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "scripts" / "download_lunar_real_maps.py"),
                    "--raw-map-dir",
                    str(root / "raw_maps"),
                    "--manifest-output",
                    str(manifest_path),
                    "--dry-run",
                    "--print-curl",
                ],
                cwd=project_root,
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn("curl -L", completed.stdout)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "DRY_RUN")
        self.assertEqual(tuple(manifest["requested_layers"]), REAL_MAP_REQUIRED_LOLA_LAYERS)
        self.assertEqual(len(manifest["planned_downloads"]), len(REAL_MAP_REQUIRED_LOLA_LAYERS))
        self.assertEqual(manifest["downloads"], [])
        self.assertTrue(all("curl" in item for item in manifest["planned_downloads"]))

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
        self.assertEqual(instance["resource_map"]["grid_shape"], [500, 500])
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
        first_task["xy_km"] = [51.0, 51.0]
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

    def test_task_index_map_preserves_external_string_ids(self) -> None:
        task_index = TaskIndexMap(("001", "010", "task-A"))

        self.assertEqual(task_index.external_id_to_index("001"), 0)
        self.assertEqual(task_index.index_to_external_id(1), "010")
        self.assertEqual(task_index.mask_of("001"), 0b001)
        self.assertEqual(task_index.mask_of("010"), 0b010)
        self.assertEqual(task_index.ids_from_mask(0b101), ("001", "task-A"))
        self.assertEqual(task_index.mask_from_ids(("010", "001")), 0b011)
        with self.assertRaises(KeyError):
            task_index.mask_of("1")
        with self.assertRaises(ValueError):
            task_index.ids_from_mask(0b1000)

    def test_bpc_core_primitives_keep_pool_master_and_proof_debt_separate(self) -> None:
        signature = ColumnSemanticSignature(
            task_set=("001",),
            sortie_partition=(("001",),),
            ordered_task_sequences=(("001",),),
            path_option_signature=(("low_time", "low_energy"),),
            service_timing_signature=(("001", 12.0),),
            resource_profile_signature=(("energy", 4.0),),
        )
        column = BpcColumn(signature=signature, objective=12.5)
        pool = ColumnPool()
        view = MasterColumnView()

        self.assertFalse(pool.contains_signature(signature))
        self.assertTrue(pool.addability_check(column).addable)
        self.assertTrue(pool.add(column).added)
        self.assertFalse(pool.add(column).added)
        self.assertFalse(view.contains_signature(signature, node_id="root"))
        self.assertTrue(view.add_from_pool(column, node_id="root", pool=pool))
        self.assertFalse(view.add_from_pool(column, node_id="root", pool=pool))
        self.assertTrue(view.contains_signature(signature, node_id="root"))

        rc_context = ReducedCostContext(
            task_duals={"001": 3.0},
            fleet_dual=2.0,
            cut_duals={"subset:001": 0.5},
            dual_fingerprint="fp",
            rmp_iteration_id="root-0",
        )
        self.assertEqual(rc_context.task_duals["001"], 3.0)
        with self.assertRaises(TypeError):
            rc_context.task_duals["001"] = 4.0

        debt = ProofDebtQueue()
        debt.add({"candidate_id": "neg-001", "true_reduced_cost": -0.1})
        ledger = CertificateLedger(
            algorithm_status=AlgorithmStatus.BPC_OPTIMAL,
            certificate_scope=CertificateScope.BPC_NODE_LP_CERTIFIED,
            pricing_state=PricingState.CERTIFIED_NO_NEGATIVE,
            uses_true_dual_bpc_certificate=True,
        )
        blocked = ledger.validate(proof_debt_queue=debt)
        self.assertFalse(blocked["valid"])
        self.assertIn("unreleased_true_rc_negative_proof_debt", blocked["issues"])
        debt.release_all_before_certificate()
        self.assertTrue(ledger.validate(proof_debt_queue=debt)["valid"])

        self.assertEqual(
            certificate_scope_for_algorithm_status(AlgorithmStatus.DIRECT_DP_BASELINE_OPTIMAL),
            CertificateScope.DIRECT_DP_FIXED_GRAPH_OPTIMAL,
        )
        self.assertEqual(
            certificate_scope_for_algorithm_status(AlgorithmStatus.DIRECT_DP_NO_COVER),
            CertificateScope.DIRECT_DP_NO_COVER,
        )

    def test_b1_root_node_baseline_certifies_node_lp_not_tree_optimal(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b0 = solve_direct_journey_baseline(data, max_exact_tasks=5)
        b1 = solve_b1_root_node_baseline(data, max_direct_tasks=5, max_rounds=8)
        b1_repeat = solve_b1_root_node_baseline(data, max_direct_tasks=5, max_rounds=8)

        self.assertEqual(b0.status, "DIRECT_DP_BASELINE_OPTIMAL")
        self.assertEqual(b0.certificate_scope, "DIRECT_DP_FIXED_GRAPH_OPTIMAL")
        self.assertEqual(b1["algorithm_status"], "BPC_GAP_AVAILABLE")
        self.assertEqual(b1["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertNotEqual(b1["certificate_scope"], "BPC_TREE_OPTIMAL")
        self.assertEqual(b1["pricing_state"], "CERTIFIED_NO_NEGATIVE")
        self.assertEqual(b1["exact_status"], "BPC_NODE_LP_CERTIFIED")
        self.assertEqual(b1["b1_mode"], "B1A_full_universe_root_audit")
        self.assertEqual(b1["seed_mode"], "full_universe")
        self.assertTrue(b1["full_universe_preloaded"])
        self.assertEqual(b1["initial_column_count"], b1["full_universe_column_count"])
        self.assertTrue(b1["uses_true_dual_bpc_certificate"])
        self.assertTrue(b1["certificate_ledger"]["valid"])
        self.assertEqual(b1["certificate_ledger"]["issues"], [])
        self.assertFalse(b1["proof_debt_queue"]["blocks_certificate"])
        self.assertEqual(b1["proof_debt_unreleased_count"], 0)
        self.assertEqual(b1["root_rmp_status"], "RESTRICTED_RMP_OPTIMAL")
        self.assertEqual(b1["root_rmp_objective"], b1["root_lp_bound"])
        self.assertTrue(b1["root_lp_bound_official"])
        self.assertIsNotNone(b1["root_lp_vs_direct_dp_gap"])
        self.assertIsInstance(b1["integral_root"], bool)
        self.assertGreaterEqual(b1["rmp_iteration_count"], 1)
        self.assertEqual(b1["pricing_round_count"], b1["round_count"])
        self.assertEqual(b1["final_judge_status"], "COMPLETE_DIRECT_UNIVERSE_RC_AUDITED")
        self.assertEqual(b1["final_judge"]["complete_universe_source"], "provided_complete_universe_cache")
        self.assertEqual(b1["final_judge"]["manual_priced_column_count"], b1["full_universe_column_count"])
        self.assertEqual(b1["final_judge_min_reduced_cost"], b1["final_judge"]["best_reduced_cost"])
        self.assertTrue(b1["manual_rc_audit_pass"])
        self.assertTrue(b1["pricing_rc_audit_pass"])
        self.assertFalse(b1["final_judge"]["completion_bound_pruning_enabled"])
        self.assertEqual(b1["final_judge"]["pricing_state"], "CERTIFIED_NO_NEGATIVE")
        self.assertEqual(
            b1["final_judge"]["manual_best_reduced_cost"],
            b1["final_judge"]["pricing_best_reduced_cost"],
        )
        self.assertEqual(b1["dual_fingerprint"], b1_repeat["dual_fingerprint"])
        self.assertLessEqual(b1["root_lp_bound"], b0.objective + 1.0e-6)
        self.assertEqual(b1["b0_ablation"]["direct_dp_objective"], b0.objective)
        self.assertTrue(b1["b0_ablation"]["root_bound_le_direct_dp_integer_objective"])
        self.assertEqual(b1["b0_ablation"]["root_lp_vs_direct_dp_gap"], b1["root_lp_vs_direct_dp_gap"])
        self.assertEqual(b1["b0_ablation"]["integral_root"], b1["integral_root"])
        self.assertEqual(
            b1["b0_ablation"]["direct_dp_certificate_scope"],
            "DIRECT_DP_FIXED_GRAPH_OPTIMAL",
        )

    def test_b1_seeded_column_root_cg_finds_missing_columns_then_closes(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b1b = solve_b1_root_node_baseline(
            data,
            max_direct_tasks=5,
            max_rounds=8,
            seed_mode="b0_incumbent_plus_singletons",
        )

        self.assertEqual(b1b["b1_mode"], "B1B_seeded_root_CG")
        self.assertEqual(b1b["seed_mode"], "b0_incumbent_plus_singletons")
        self.assertFalse(b1b["full_universe_preloaded"])
        self.assertLess(b1b["initial_column_count"], b1b["full_universe_column_count"])
        self.assertGreater(b1b["added_column_count"], 0)
        self.assertGreater(b1b["pricing_round_count"], 1)
        self.assertEqual(b1b["history"][0]["pricing_state"], "FOUND_NEGATIVE")
        self.assertGreater(b1b["history"][0]["negative_column_count"], 0)
        self.assertGreater(b1b["history"][0]["added_column_count"], 0)
        self.assertEqual(b1b["history"][0]["dual_context"]["rmp_iteration_id"], "root-1")
        self.assertEqual(set(b1b["history"][0]["dual_context"]["task_duals"]), set(data.task_ids))
        self.assertEqual(b1b["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertEqual(b1b["pricing_state"], "CERTIFIED_NO_NEGATIVE")
        self.assertEqual(b1b["exact_status"], "BPC_NODE_LP_CERTIFIED")
        self.assertTrue(b1b["root_lp_bound_official"])
        self.assertTrue(b1b["manual_rc_audit_pass"])
        self.assertTrue(b1b["pricing_rc_audit_pass"])
        self.assertEqual(b1b["proof_debt_unreleased_count"], 0)
        self.assertTrue(b1b["b0_ablation"]["root_bound_le_direct_dp_integer_objective"])

    def test_b0_b1_ablation_gate_reports_redlines_and_seeded_cg(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        report = run_b0_b1_ablation([instance], max_direct_tasks=5, b1_max_rounds=8)

        self.assertEqual(report["schema_version"], "lunar_ice_bpc.b0_b1_ablation.v1")
        self.assertEqual(report["accepted_baseline_layers"], ["B0", "B1"])
        self.assertIn("B2", report["not_accepted_layers"])
        self.assertEqual(report["row_count"], 3)
        self.assertEqual(
            report["redlines"],
            {
                "root_bound_gt_B0_violation_count": 0,
                "direct_root_official_leak_count": 0,
                "manual_rc_fail_count": 0,
                "pricing_rc_fail_count": 0,
            },
        )
        rows_by_mode = {row["mode"]: row for row in report["rows"]}
        self.assertEqual(rows_by_mode[B0_MODE]["certificate_scope"], "DIRECT_DP_FIXED_GRAPH_OPTIMAL")
        self.assertEqual(rows_by_mode[B0_MODE]["bpc_certificate_status"], "NOT_PORTED_TRUE_DUAL_BPC")
        self.assertFalse(rows_by_mode[B0_MODE]["uses_true_dual_bpc_certificate"])
        self.assertEqual(rows_by_mode[B1A_MODE]["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertTrue(rows_by_mode[B1A_MODE]["full_universe_preloaded"])
        self.assertEqual(rows_by_mode[B1B_MODE]["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertFalse(rows_by_mode[B1B_MODE]["full_universe_preloaded"])
        self.assertGreater(rows_by_mode[B1B_MODE]["added_column_count"], 0)
        self.assertGreater(rows_by_mode[B1B_MODE]["pricing_round_count"], 1)

    def test_b0_b1_ablation_fail_closes_over_task_limit(self) -> None:
        instance = generate_instance(20, seed=829001, index=1)
        report = run_b0_b1_ablation(
            [instance],
            modes=(B0_MODE, B1A_MODE, B1B_MODE),
            max_direct_tasks=10,
            b1_max_rounds=8,
        )

        rows_by_mode = {row["mode"]: row for row in report["rows"]}
        self.assertEqual(rows_by_mode[B0_MODE]["certificate_scope"], "FEASIBLE_INCUMBENT_ONLY")
        self.assertEqual(rows_by_mode[B1A_MODE]["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(rows_by_mode[B1A_MODE]["certificate_scope"], "FEASIBLE_INCUMBENT_ONLY")
        self.assertFalse(rows_by_mode[B1A_MODE]["uses_true_dual_bpc_certificate"])
        self.assertFalse(rows_by_mode[B1A_MODE]["root_lp_bound_official"])
        self.assertEqual(rows_by_mode[B1B_MODE]["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(rows_by_mode[B1B_MODE]["certificate_scope"], "FEASIBLE_INCUMBENT_ONLY")
        self.assertFalse(rows_by_mode[B1B_MODE]["uses_true_dual_bpc_certificate"])
        self.assertFalse(rows_by_mode[B1B_MODE]["root_lp_bound_official"])
        self.assertEqual(report["redlines"]["direct_root_official_leak_count"], 0)

    def test_b0_b1_guarded_row_records_memory_error_attempt(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        row = b0_b1_ablation_module._run_guarded_row(
            instance,
            mode=B1A_MODE,
            matrix_group="memory-error-test",
            max_direct_tasks=5,
            row_time_limit_sec=10.0,
            fn=lambda: (_ for _ in ()).throw(MemoryError()),
        )

        self.assertEqual(row["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(row["certificate_scope"], "FEASIBLE_INCUMBENT_ONLY")
        self.assertEqual(row["pricing_state"], "INCOMPLETE_LIMIT")
        self.assertEqual(row["attempted_exception_type"], "MemoryError")
        self.assertEqual(row["attempted_max_direct_tasks"], 5)
        self.assertIn("MemoryError", row["fail_closed_reason"])
        self.assertFalse(row["root_lp_bound_official"])

    def test_b1a_full_universe_rmp_memory_precheck_fails_closed_before_b0(self) -> None:
        instance = generate_instance(20, seed=829001, index=1)
        data = load_lunar_ice_data(instance)
        with patch(
            "lunar_ice_bpc.exact.bpc.solver.root_node_solver.solve_direct_journey_baseline",
            side_effect=AssertionError("B0 should not run before B1A RMP memory precheck"),
        ):
            b1a = solve_b1_root_node_baseline(
                data,
                max_direct_tasks=20,
                max_rounds=1,
                seed_mode="full_universe",
            )

        self.assertEqual(b1a["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(b1a["certificate_scope"], "FEASIBLE_INCUMBENT_ONLY")
        self.assertFalse(b1a["root_lp_bound_official"])
        self.assertTrue(b1a["rmp_memory_precheck_failed"])
        self.assertEqual(b1a["rmp_memory_precheck_stage"], "b1a_full_universe_active_rmp")
        self.assertEqual(b1a["full_universe_column_count"], (1 << 20) - 1)
        self.assertGreater(
            b1a["rmp_memory_precheck_estimated_tableau_cells"],
            b1a["rmp_memory_precheck_cell_limit"],
        )
        self.assertIsNone(b1a["b0_ablation"]["direct_dp_objective"])

    def test_b2_guarded_mode_records_memory_error_attempt(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        with patch.object(
            b2_pricing_tail_ablation_module,
            "_run_mode",
            side_effect=MemoryError(),
        ):
            row = b2_pricing_tail_ablation_module._run_guarded_mode(
                instance,
                mode=B2A_MODE,
                baseline_cache={},
                max_direct_tasks=5,
                b1_max_rounds=1,
                b2_max_rounds=1,
                matrix_group="memory-error-test",
                row_time_limit_sec=10.0,
            )

        self.assertEqual(row["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(row["certificate_scope"], "FEASIBLE_INCUMBENT_ONLY")
        self.assertEqual(row["pricing_state"], "INCOMPLETE_LIMIT")
        self.assertEqual(row["attempted_exception_type"], "MemoryError")
        self.assertEqual(row["attempted_max_direct_tasks"], 5)
        self.assertIn("MemoryError", row["fail_closed_reason"])
        self.assertFalse(row["root_lp_bound_official"])

    def test_b2a_full_universe_rmp_memory_precheck_fails_closed_before_b0(self) -> None:
        instance = generate_instance(20, seed=829001, index=1)
        data = load_lunar_ice_data(instance)
        with patch(
            "lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver.solve_direct_journey_baseline",
            side_effect=AssertionError("B0 should not run before B2A RMP memory precheck"),
        ):
            b2a = solve_b2_pricing_tail_baseline(
                data,
                max_direct_tasks=20,
                max_rounds=1,
                mode=B2A_MODE,
            )

        self.assertEqual(b2a["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(b2a["certificate_scope"], "FEASIBLE_INCUMBENT_ONLY")
        self.assertFalse(b2a["root_lp_bound_official"])
        self.assertTrue(b2a["rmp_memory_precheck_failed"])
        self.assertEqual(b2a["rmp_memory_precheck_stage"], "b2a_full_universe_active_rmp")
        self.assertEqual(b2a["full_universe_column_count"], (1 << 20) - 1)
        self.assertIsNone(b2a["b0_ablation"]["direct_dp_objective"])

    def test_b3_guarded_row_records_memory_error_attempt(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        with patch.object(
            b3_branch_tree_ablation_module,
            "_run_mode",
            side_effect=MemoryError(),
        ):
            row, cache_value = b3_branch_tree_ablation_module._run_guarded_row(
                instance,
                mode=b3_branch_tree_ablation_module.B3A_MODE,
                max_direct_tasks=5,
                b2_max_rounds=1,
                b3_max_rounds_per_node=1,
                max_tree_nodes=1,
                max_branch_depth=1,
                matrix_group="memory-error-test",
                row_time_limit_sec=10.0,
                allow_b3a_full_universe=True,
                b0_direct=None,
                b2b_r3=None,
            )

        self.assertIsNone(cache_value)
        self.assertEqual(row["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(row["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
        self.assertEqual(row["pricing_state"], "INCOMPLETE_LIMIT")
        self.assertEqual(row["attempted_exception_type"], "MemoryError")
        self.assertEqual(row["attempted_max_direct_tasks"], 5)
        self.assertIn("MemoryError", row["fail_closed_reason"])

    def test_b3a_full_universe_rmp_memory_precheck_fails_closed_before_b0(self) -> None:
        instance = generate_instance(20, seed=829001, index=1)
        with patch.object(
            b3_branch_tree_ablation_module,
            "solve_direct_journey_baseline",
            side_effect=AssertionError("B0 should not run before B3A RMP memory precheck"),
        ):
            raw = b3_branch_tree_ablation_module._run_mode(
                instance,
                mode=b3_branch_tree_ablation_module.B3A_MODE,
                max_direct_tasks=20,
                b2_max_rounds=1,
                b3_max_rounds_per_node=1,
                max_tree_nodes=1,
                max_branch_depth=1,
                allow_b3a_full_universe=True,
                row_time_limit_sec=10.0,
                b0_direct=None,
                b2b_r3=None,
            )

        self.assertEqual(raw["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(raw["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
        self.assertFalse(raw["B3_tree_closed"])
        self.assertTrue(raw["rmp_memory_precheck_failed"])
        self.assertEqual(raw["rmp_memory_precheck_stage"], "b3a_full_universe_node_active_rmp")
        self.assertEqual(raw["rmp_memory_precheck_estimated_column_count"], (1 << 20) - 1)

    def test_b2_pricing_tail_ablation_reports_fast_path_and_keeps_b2b_diagnostic(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        report = run_b2_pricing_tail_ablation([instance], max_direct_tasks=5, b1_max_rounds=8, b2_max_rounds=8)

        self.assertEqual(report["schema_version"], "lunar_ice_bpc.b2_pricing_tail_ablation.v1")
        self.assertEqual(report["row_count"], 10)
        self.assertEqual(report["redlines"]["root_bound_gt_B0_violation_count"], 0)
        self.assertEqual(report["redlines"]["manual_rc_fail_count"], 0)
        self.assertEqual(report["redlines"]["selected_harvest_addability_fail_count"], 0)
        rows_by_mode = {row["candidate_name"]: row for row in report["rows"]}
        self.assertEqual(rows_by_mode[B2A_MODE]["baseline_name"], B1A_MODE)
        self.assertEqual(rows_by_mode[B2A_MODE]["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertIn("final_judge_call_count_lower", rows_by_mode[B2A_MODE]["improvement_reason"])
        self.assertEqual(rows_by_mode[B2B_MODE]["baseline_name"], B1B_MODE)
        self.assertEqual(rows_by_mode[B2B_MODE]["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertEqual(rows_by_mode[B2B_R2_MODE]["baseline_name"], B1B_MODE)
        self.assertEqual(rows_by_mode[B2B_R2_MODE]["seed_builder"], "b2b_r2_lightweight_no_full_universe_enumeration")
        self.assertFalse(rows_by_mode[B2B_R2_MODE]["full_universe_preloaded"])
        self.assertEqual(rows_by_mode[B2B_R2_MODE]["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertTrue(rows_by_mode[B2B_R2_MODE]["selected_all_would_enter_master"])
        self.assertGreater(rows_by_mode[B2B_R2_MODE]["worker_call_count"], 0)
        self.assertGreater(rows_by_mode[B2B_R2_MODE]["final_judge_call_count"], 0)
        self.assertEqual(rows_by_mode[B2B_R3_MODE]["baseline_name"], B1B_MODE)
        self.assertEqual(rows_by_mode[B2B_R3_MODE]["seed_builder"], "b2b_r3_lightweight_no_full_universe_enumeration")
        self.assertFalse(rows_by_mode[B2B_R3_MODE]["full_universe_preloaded"])
        self.assertEqual(rows_by_mode[B2B_R3_MODE]["diagnostic_dual_source"], "master.reduced_cost_context")
        self.assertTrue(rows_by_mode[B2B_R3_MODE]["diagnostic_dual_fingerprint"])
        self.assertGreater(rows_by_mode[B2B_R3_MODE]["labels_generated_total"], 0)
        self.assertIsNotNone(rows_by_mode[B2B_R3_MODE]["labels_generated_before_first_negative"])
        self.assertEqual(rows_by_mode[B2B_R3_MODE]["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertFalse(rows_by_mode[B2B_R2_MODE]["exact_first_step_bound_pruning_enabled"])
        self.assertEqual(rows_by_mode[B2_PRODUCT_MODE]["certificate_scope"], "DIRECT_DP_FIXED_GRAPH_OPTIMAL")
        self.assertEqual(rows_by_mode[B2_PRODUCT_MODE]["product_exact_solution_count"], 1)
        self.assertEqual(rows_by_mode[B2C_MODE]["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
        self.assertEqual(rows_by_mode[B2D_MODE]["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
        for mode in (B2C_MODE, B2D_MODE):
            self.assertEqual(rows_by_mode[mode]["diagnostic_dual_source"], "master.reduced_cost_context")
            self.assertTrue(rows_by_mode[mode]["diagnostic_dual_fingerprint"])
            self.assertGreater(rows_by_mode[mode]["labels_generated_total"], 0)
            self.assertIsNotNone(rows_by_mode[mode]["worker_wall_time"])
            self.assertEqual(rows_by_mode[mode]["final_judge_wall_time"], 0.0)
            self.assertIn(rows_by_mode[mode]["exit_reason"], {"FOUND_NEGATIVE", "LOCAL_NO_COLUMN_UNCERTIFIED"})
        self.assertFalse(rows_by_mode[B2_PRODUCT_MODE]["root_lp_bound_official"])
        self.assertFalse(report["acceptance"]["b2_accepted"])
        self.assertTrue(report["acceptance"]["b2a_fast_path_accepted"])
        self.assertFalse(report["acceptance"]["b2b_seeded_tail_accepted"])
        self.assertFalse(report["acceptance"]["b2b_r2_seeded_tail_accepted"])

    def test_b2_pricing_tail_ablation_writes_required_artifacts(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        report = run_b2_pricing_tail_ablation([instance], max_direct_tasks=5)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows_csv = root / "rows.csv"
            summary_json = root / "summary.json"
            report_md = root / "report_zh.md"
            write_b2_pricing_tail_ablation_artifacts(
                report,
                rows_csv=rows_csv,
                summary_json=summary_json,
                report_md=report_md,
            )
            self.assertTrue(rows_csv.exists())
            self.assertTrue(summary_json.exists())
            self.assertTrue(report_md.exists())
            text = report_md.read_text(encoding="utf-8")
            self.assertIn("B2 Accepted?", text)
            self.assertIn("B2 Round3 Answers", text)

    def test_b2_report_backfills_mode_from_legacy_candidate_name(self) -> None:
        legacy_report = b2_pricing_tail_ablation_module._report_from_rows(
            [
                {
                    "matrix_group": "legacy",
                    "scale": 20,
                    "instance_id": "legacy_instance",
                    "baseline_name": B1B_MODE,
                    "candidate_name": B2B_R3_MODE,
                    "algorithm_status": "BPC_INCOMPLETE_PRICING",
                    "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                    "pricing_state": "INCOMPLETE_LIMIT",
                    "wall_time": 1.0,
                }
            ]
        )

        self.assertEqual(legacy_report["rows"][0]["mode"], B2B_R3_MODE)
        with tempfile.TemporaryDirectory() as tmp:
            rows_csv = Path(tmp) / "rows.csv"
            write_b2_pricing_tail_ablation_artifacts(
                legacy_report,
                rows_csv=rows_csv,
                summary_json=Path(tmp) / "summary.json",
                report_md=Path(tmp) / "report_zh.md",
            )
            with rows_csv.open(newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
        self.assertEqual(rows[0]["mode"], B2B_R3_MODE)

    def test_b2_acceptance_requires_direct20_probe_and_report_disambiguates_guard(self) -> None:
        redlines = {
            "root_bound_gt_B0_violation_count": 0,
            "direct_root_official_leak_count": 0,
            "manual_rc_fail_count": 0,
            "pricing_rc_fail_count": 0,
            "certificate_scope_regression_count": 0,
            "objective_mismatch_count": 0,
            "b1_5scale_regression_count": 0,
            "proof_debt_unreleased_certified_count": 0,
        }
        rows = [
            {
                "scale": 10,
                "matrix_group": "10-scale selected5",
                "candidate_name": B2B_R2_MODE,
                "improvement_reason": "wall_time_lower",
            }
        ]
        matrix = {
            "scale10_selected_count": 5,
            "scale10_total_count": 20,
            "scale20_fail_closed_count": 20,
            "scale20_probe_count": 0,
            "scale20_probe_modes": [B0_MODE, B1A_MODE, B1B_MODE, B2_PRODUCT_MODE, B2A_MODE, B2B_R2_MODE, B2B_R3_MODE, B2C_MODE, B2D_MODE],
            "scale30_count": 20,
            "notes": ["20-scale fail-closed guard deliberately sets max_direct_tasks below 20."],
        }
        acceptance = _acceptance(rows, redlines, matrix=matrix)

        self.assertFalse(acceptance["b2_accepted"])
        self.assertFalse(acceptance["required_coverage_met"])
        self.assertIn("20-scale selected direct20", acceptance["reason"])

        rendered = render_b2_pricing_tail_markdown(
            {
                "redlines": redlines,
                "acceptance": acceptance,
                "matrix": matrix,
                "summary_rows": [],
                "totals": {},
                "duplicate_only_audit_status_counts": {},
            },
            rows_csv="rows.csv",
            summary_json="summary.json",
        )
        self.assertIn("proof_debt_unreleased_certified_count", rendered)
        self.assertIn("not evidence that B0 direct20 failed", rendered)
        self.assertIn("20-scale selected direct20 probe did not run", rendered)

    def test_b2_duplicate_only_row_exports_audit_status_and_fail_reason(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        row = _row_from_raw(
            data,
            mode=B2B_MODE,
            matrix_group="unit",
            elapsed=0.1,
            raw={
                "algorithm_status": "BPC_INCOMPLETE_PRICING",
                "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                "pricing_state": "DUPLICATE_ONLY",
                "uses_true_dual_bpc_certificate": False,
                "root_lp_bound": 10.0,
                "root_lp_bound_official": False,
                "B0_direct_objective": 12.0,
                "root_bound_le_direct_dp_integer_objective": True,
                "pricing_round_count": 1,
                "final_judge_call_count": 1,
                "candidate_negative_count": 3,
                "addable_negative_count": 0,
                "selected_count": 0,
                "added_to_master_count": 0,
                "duplicate_only_count": 1,
                "duplicate_only_audit_status": "DUPLICATE_ONLY_AUDITED",
                "manual_rc_audit_pass": False,
                "pricing_rc_audit_pass": True,
                "proof_debt_unreleased_count": 0,
                "fail_closed_reason": "DUPLICATE_ONLY: negative candidates were not master-addable.",
            },
        )

        self.assertEqual(row["pricing_state"], "DUPLICATE_ONLY")
        self.assertEqual(row["duplicate_only_count"], 1)
        self.assertEqual(row["duplicate_only_audit_status"], "DUPLICATE_ONLY_AUDITED")
        self.assertIn("DUPLICATE_ONLY", row["fail_closed_reason"])

    def test_b2_product_exact_solver_keeps_direct_scope_separate_from_bpc_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        product = solve_b2_pricing_tail_baseline(data, max_direct_tasks=5, mode=B2_PRODUCT_MODE)

        self.assertEqual(product["algorithm_status"], "DIRECT_DP_BASELINE_OPTIMAL")
        self.assertEqual(product["certificate_scope"], "DIRECT_DP_FIXED_GRAPH_OPTIMAL")
        self.assertEqual(product["product_exact_solution_scope"], "DIRECT_DP_FIXED_GRAPH_OPTIMAL")
        self.assertEqual(product["product_exact_solution_count"], 1)
        self.assertTrue(product["direct_dp_fallback_used"])
        self.assertFalse(product["uses_true_dual_bpc_certificate"])
        self.assertFalse(product["root_lp_bound_official"])
        self.assertIsNone(product["root_lp_bound"])

    def test_b2c_b2d_limited_diagnostics_never_create_official_bound(self) -> None:
        instance = generate_instance(10, seed=629101, index=1)
        data = load_lunar_ice_data(instance)
        for mode in (B2C_MODE, B2D_MODE):
            diagnostic = solve_b2_pricing_tail_baseline(data, max_direct_tasks=10, mode=mode, max_columns_per_round=4)
            self.assertEqual(diagnostic["algorithm_status"], "BPC_INCOMPLETE_PRICING")
            self.assertEqual(diagnostic["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
            self.assertFalse(diagnostic["uses_true_dual_bpc_certificate"])
            self.assertFalse(diagnostic["root_lp_bound_official"])
            self.assertFalse(diagnostic["completion_bound_pruning_enabled"])
            self.assertGreaterEqual(diagnostic["labels_generated"], 0)
            self.assertGreaterEqual(diagnostic["candidate_sequences"], 0)
        self.assertTrue(
            solve_b2_pricing_tail_baseline(data, max_direct_tasks=10, mode=B2D_MODE)["proof_tail_kernel_profile"]["enabled"]
        )

    def test_b2_direct20_only_report_can_merge_into_existing_matrix(self) -> None:
        def row(
            mode: str,
            *,
            wall_time: float,
            fail_reason: str = "",
            instance_id: str = "instance_020_probe",
            scale: int = 20,
            matrix_group: str = "20-scale selected direct20 probe",
        ) -> dict:
            return {
                "matrix_group": matrix_group,
                "scale": scale,
                "instance_id": instance_id,
                "baseline_name": B1B_MODE if mode in {B2B_MODE, B2B_R2_MODE, B2B_R3_MODE} else "accepted_B1",
                "candidate_name": mode,
                "algorithm_status": "BPC_INCOMPLETE_PRICING" if mode != B0_MODE else "DIRECT_DP_BASELINE_OPTIMAL",
                "certificate_scope": "FEASIBLE_INCUMBENT_ONLY",
                "pricing_state": "INCOMPLETE_LIMIT",
                "uses_true_dual_bpc_certificate": False,
                "official_lower_bound_source": "",
                "official_lower_bound_scope": "",
                "B0_direct_objective": 100.0,
                "root_lp_bound": "",
                "root_lp_bound_official": False,
                "root_bound_le_B0_objective": None,
                "pricing_round_count": 0,
                "final_judge_call_count": 0,
                "candidate_negative_count": 0,
                "addable_negative_count": 0,
                "duplicate_in_current_master_count": 0,
                "in_pool_not_master_count": 0,
                "forbidden_signature_count": 0,
                "branch_filtered_count": 0,
                "cut_filtered_count": 0,
                "selected_count": 0,
                "added_to_master_count": 0,
                "added_column_count": 0,
                "duplicate_only_count": 0,
                "duplicate_only_audit_status": "",
                "hidden_negative_count": 0,
                "replacement_only_round_count": 0,
                "manual_rc_audit_pass": None,
                "pricing_rc_audit_pass": None,
                "proof_debt_unreleased_count": 0,
                "worker_call_count": 0,
                "worker_found_addable_negative_count": 0,
                "final_judge_wall_time": None,
                "time_to_first_addable_negative": None,
                "exact_first_step_bound_pruning_enabled": False,
                "wall_time": wall_time,
                "fail_closed_reason": fail_reason,
                "certificate_scope_regression": False,
                "objective_mismatch": False,
                "improvement_reason": "",
            }

        base = {
            "rows": [
                row(
                    B1B_MODE,
                    wall_time=30.0,
                    fail_reason="row_time_limit_sec=30 exceeded",
                    instance_id="instance_010_selected",
                    scale=10,
                    matrix_group="10-scale selected5",
                ),
                row(
                    B2B_R2_MODE,
                    wall_time=3.0,
                    fail_reason="",
                    instance_id="instance_010_selected",
                    scale=10,
                    matrix_group="10-scale selected5",
                ),
                row(
                    B2B_R3_MODE,
                    wall_time=2.0,
                    fail_reason="",
                    instance_id="instance_010_selected",
                    scale=10,
                    matrix_group="10-scale selected5",
                ),
            ],
            "matrix": {
                "scale10_selected_count": 5,
                "scale20_probe_count": 0,
                "scale20_probe_modes": [B0_MODE, B1A_MODE, B1B_MODE, B2_PRODUCT_MODE, B2A_MODE, B2B_R2_MODE, B2B_R3_MODE, B2C_MODE, B2D_MODE],
                "notes": [],
            },
        }
        extra_rows = []
        for index in range(5):
            instance_id = f"instance_020_probe_{index + 1:03d}"
            extra_rows.extend(
                [
                    row(B0_MODE, wall_time=5.0, instance_id=instance_id),
                    row(B1A_MODE, wall_time=60.0, fail_reason="row_time_limit_sec=60 exceeded", instance_id=instance_id),
                    row(B1B_MODE, wall_time=60.0, fail_reason="row_time_limit_sec=60 exceeded", instance_id=instance_id),
                    row(B2_PRODUCT_MODE, wall_time=5.0, instance_id=instance_id),
                    row(B2A_MODE, wall_time=10.0, instance_id=instance_id),
                    row(B2B_R2_MODE, wall_time=10.0, fail_reason="worker diagnostic", instance_id=instance_id),
                    row(B2B_R3_MODE, wall_time=9.0, fail_reason="", instance_id=instance_id),
                    row(B2C_MODE, wall_time=1.0, instance_id=instance_id),
                    row(B2D_MODE, wall_time=1.0, instance_id=instance_id),
                ]
            )
        extra = {
            "rows": extra_rows,
            "matrix": {
                "scale20_probe_count": 5,
                "scale20_probe_modes": [B0_MODE, B1A_MODE, B1B_MODE, B2_PRODUCT_MODE, B2A_MODE, B2B_R2_MODE, B2B_R3_MODE, B2C_MODE, B2D_MODE],
                "direct20_probe_time_limit_sec": 60.0,
                "notes": ["direct20-only unit test"],
            },
        }
        merged = merge_b2_pricing_tail_reports(base, extra)

        self.assertEqual(merged["matrix"]["scale20_probe_count"], 5)
        self.assertTrue(merged["acceptance"]["required_coverage_met"])
        self.assertTrue(merged["acceptance"]["b2b_r3_seeded_tail_accepted"])
        self.assertEqual(merged["redlines"]["root_bound_gt_B0_violation_count"], 0)
        b2b_row = next(row for row in merged["rows"] if row["candidate_name"] == B2B_R3_MODE)
        self.assertIn("wall_time_lower", b2b_row["improvement_reason"])

    def test_b2b_r2_incremental_report_runs_only_b2b_r2_groups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_rows = []
            for scale, seed in ((5, 629001), (10, 629101), (20, 629201), (30, 629301)):
                instance = generate_instance(scale, seed=seed, index=1)
                path = root / f"instance_{scale:03d}.json"
                write_json(path, instance)
                manifest_rows.append({"task_count": scale, "path": str(path)})
            manifest_path = root / "manifest.json"
            write_json(manifest_path, {"instances": manifest_rows})

            report = run_b2_pricing_tail_b2b_r2_incremental(
                manifest_path=manifest_path,
                project_root=root,
                scale10_limit=1,
                scale10_row_time_limit_sec=10.0,
                scale20_probe_limit=0,
                fail_closed_max_direct_tasks=10,
                b2_max_rounds=1,
            )

        self.assertEqual({row["candidate_name"] for row in report["rows"]}, {B2B_R2_MODE})
        self.assertEqual(report["matrix"]["scale20_probe_count"], 0)
        self.assertIn("5-scale full", {row["matrix_group"] for row in report["rows"]})
        self.assertIn("10-scale full", {row["matrix_group"] for row in report["rows"]})
        self.assertIn("20-scale fail-closed guard", {row["matrix_group"] for row in report["rows"]})
        self.assertIn("30-scale fail-closed diagnostic", {row["matrix_group"] for row in report["rows"]})
        fail_closed_rows = [
            row for row in report["rows"]
            if row["matrix_group"] in {"20-scale fail-closed guard", "30-scale fail-closed diagnostic"}
        ]
        self.assertTrue(fail_closed_rows)
        self.assertTrue(all(row["certificate_scope"] == "FEASIBLE_INCUMBENT_ONLY" for row in fail_closed_rows))
        self.assertTrue(all(row["root_lp_bound_official"] is False for row in fail_closed_rows))

    def test_b1_alignment_costs_and_reduced_costs_match_b0_oracle(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        b0 = solve_direct_journey_baseline(data, max_exact_tasks=5)
        b1 = solve_b1_root_node_baseline(data, max_direct_tasks=5, max_rounds=8)

        full_cover_column = next(column for column in universe.columns if set(column.task_set) == set(data.task_ids))
        one_column_rmp = solve_restricted_journey_rmp(
            data.task_ids,
            (full_cover_column,),
            fleet_size=data.fleet_size,
        )
        self.assertEqual(one_column_rmp.status, "RESTRICTED_RMP_OPTIMAL")
        self.assertAlmostEqual(one_column_rmp.objective_bound, full_cover_column.objective, places=6)

        one_sortie_column = next(column for column in universe.columns if len(column.sorties) == 1)
        breakdown = one_sortie_column.objective_breakdown
        expected_objective = (
            data.objective.weight_operating_cost * breakdown["normalized_operating_cost"]
            + data.objective.weight_risk * breakdown["normalized_risk"]
            + data.objective.weight_completion * breakdown["normalized_weighted_completion_time"]
        )
        self.assertAlmostEqual(one_sortie_column.objective, round(expected_objective, 6), places=6)
        self.assertAlmostEqual(
            breakdown["normalized_objective"],
            round(expected_objective, 6),
            places=6,
        )
        self.assertEqual(breakdown["official_objective"], breakdown["normalized_objective"])
        self.assertGreater(breakdown["raw_objective_unscaled_weighted_sum"], breakdown["official_objective"])
        self.assertFalse(breakdown["makespan_enters_pricing_objective"])

        columns_by_signature = {column_signature_from_journey(column): column for column in universe.columns}
        for journey in b0.journeys:
            matched = columns_by_signature[column_signature_from_journey(journey)]
            self.assertAlmostEqual(matched.objective, journey.objective, places=6)

        rmp = solve_restricted_journey_rmp(
            data.task_ids,
            universe.columns,
            fleet_size=data.fleet_size,
        )
        pricing, priced_columns = price_exhaustive_direct_journey_columns(
            data,
            rmp.duals,
            max_direct_tasks=5,
            completion_bound_enabled=False,
        )
        manual_best = min(manual_journey_reduced_cost(column, rmp.duals) for column in priced_columns)
        self.assertEqual(pricing["status"], "EXHAUSTIVE_DIRECT_LABEL_PRICED")
        self.assertTrue(pricing["pricing_complete_for_all_task_subsets"])
        self.assertAlmostEqual(manual_best, pricing["best_reduced_cost"], places=6)
        self.assertLessEqual(b1["root_lp_bound"], b0.objective + 1.0e-6)
        self.assertEqual(b1["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertEqual(b1["final_judge"]["pricing_state"], "CERTIFIED_NO_NEGATIVE")
        self.assertTrue(b1["final_judge"]["can_certify_no_negative"])
        self.assertEqual(
            b1["final_judge"]["manual_best_reduced_cost"],
            b1["final_judge"]["pricing_best_reduced_cost"],
        )

    def test_b1_active_column_payload_can_seed_resume_without_certificate_leak(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        first = solve_b1_root_node_baseline(
            data,
            max_direct_tasks=5,
            max_rounds=8,
            seed_mode="b0_incumbent_plus_singletons",
            return_active_columns_payload=True,
        )

        self.assertIn("active_columns", first)
        self.assertGreater(len(first["active_columns"]), 0)
        resumed_columns = tuple(
            journey_column_from_solution_payload(data, row)
            for row in first["active_columns"]
        )
        self.assertEqual(
            len({column_signature_from_journey(column) for column in resumed_columns}),
            len(resumed_columns),
        )

        resumed = solve_b1_root_node_baseline(
            data,
            initial_columns=resumed_columns,
            max_direct_tasks=5,
            max_rounds=8,
            solve_b0_direct_first=False,
        )

        self.assertEqual(resumed["seed_mode"], "custom_initial_columns")
        self.assertFalse(resumed["solve_b0_direct_first"])
        self.assertIsNotNone(resumed["b0_ablation"]["reference_solution_upper_bound"])
        self.assertEqual(resumed["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertEqual(resumed["pricing_state"], "CERTIFIED_NO_NEGATIVE")
        self.assertAlmostEqual(resumed["root_lp_bound"], first["root_lp_bound"], places=6)

    def test_objective_reference_cache_rejects_reused_object_id_entries(self) -> None:
        first = load_lunar_ice_data(generate_instance(5, seed=629001, index=1))
        second = load_lunar_ice_data(generate_instance(5, seed=679123, index=17))
        first_refs = objective_module.objective_references(first)
        second_refs = objective_module.objective_references(second)
        self.assertNotEqual(first_refs, second_refs)

        objective_module._REFERENCE_CACHE[id(second)] = (objective_module.weakref.ref(first), first_refs)
        recovered_refs = objective_module.objective_references(second)

        self.assertEqual(recovered_refs, second_refs)
        cached_data_ref, cached_refs = objective_module._REFERENCE_CACHE[id(second)]
        self.assertIs(cached_data_ref(), second)
        self.assertEqual(cached_refs, second_refs)

    def test_path_choice_keeps_all_path_metrics(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_id = data.task_ids[0]
        for path_type in ("low_time", "low_risk"):
            sortie = build_timed_sortie(
                data,
                (task_id,),
                (path_type, path_type),
                start_time=0.0,
            )
            self.assertTrue(sortie.feasible)
            self.assertGreater(sortie.travel_time, 0.0)
            self.assertGreater(sortie.distance_km, 0.0)
            self.assertGreater(sortie.energy_proxy, 0.0)
            self.assertGreater(sortie.risk_integral, 0.0)

    def test_exact_bpc_modules_do_not_import_guidance_or_ml_stack(self) -> None:
        bpc_root = Path(__file__).resolve().parents[1] / "src" / "lunar_ice_bpc" / "exact" / "bpc"
        banned = ("torch", "checkpoint", "gat", "ood")
        offenders: list[tuple[str, str]] = []
        for path in sorted(bpc_root.rglob("*.py")):
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip().lower()
                if not (stripped.startswith("import ") or stripped.startswith("from ")):
                    continue
                if any(re.search(rf"(?<![a-z0-9_]){term}(?![a-z0-9_])", stripped) for term in banned):
                    offenders.append((str(path.relative_to(bpc_root)), line.strip()))
        self.assertEqual(offenders, [])

    def test_b2_pricing_tail_defaults_to_seeded_cg_without_preloaded_universe(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b2 = solve_b2_pricing_tail_baseline(data, max_direct_tasks=5, max_rounds=8)

        self.assertEqual(b2["b2_mode"], B2B_MODE)
        self.assertFalse(b2["full_universe_preloaded"])
        self.assertEqual(b2["seed_mode"], "b0_incumbent_plus_singletons")
        self.assertEqual(b2["algorithm_status"], "BPC_GAP_AVAILABLE")
        self.assertEqual(b2["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertEqual(b2["pricing_state"], "CERTIFIED_NO_NEGATIVE")
        self.assertEqual(b2["exact_status"], "BPC_NODE_LP_CERTIFIED")
        self.assertTrue(b2["root_lp_bound_official"])
        self.assertIsNone(b2["objective_diff_vs_B1"])
        self.assertEqual(b2["certificate_scope_diff_vs_B1"], "")
        self.assertGreater(b2["final_judge_call_count"], 0)
        self.assertGreater(b2["candidate_negative_count"], 0)
        self.assertGreater(b2["addable_negative_count"], 0)
        self.assertEqual(b2["selected_count"], b2["harvest_selected_count"])
        self.assertEqual(b2["selected_count"], b2["selected_would_enter_master_count"])
        self.assertTrue(b2["selected_all_would_enter_master"])
        self.assertEqual(b2["added_to_master_count"], b2["added_column_count"])
        self.assertEqual(b2["harvest_selected_count"], b2["harvest_addable_candidate_count"])
        self.assertEqual(b2["duplicate_only_count"], 0)
        self.assertEqual(b2["hidden_negative_count"], 0)
        self.assertEqual(b2["replacement_only_round_count"], 0)
        self.assertFalse(b2["completion_bound_policy"]["pruning_enabled"])
        self.assertFalse(b2["completion_bound_policy"]["can_certify_no_negative"])
        self.assertEqual(b2["proof_debt_unreleased_count"], 0)

    def test_b2b_r2_worker_found_negative_does_not_certify_without_final_judge(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b2 = solve_b2_pricing_tail_baseline(
            data,
            max_direct_tasks=5,
            max_rounds=1,
            mode=B2B_R2_MODE,
        )

        self.assertEqual(b2["b2_mode"], B2B_R2_MODE)
        self.assertEqual(b2["seed_builder"], "b2b_r2_lightweight_no_full_universe_enumeration")
        self.assertFalse(b2["full_universe_preloaded"])
        self.assertEqual(b2["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(b2["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
        self.assertEqual(b2["pricing_state"], "INCOMPLETE_LIMIT")
        self.assertFalse(b2["root_lp_bound_official"])
        self.assertFalse(b2["uses_true_dual_bpc_certificate"])
        self.assertEqual(b2["final_judge_call_count"], 0)
        self.assertGreater(b2["worker_found_addable_negative_count"], 0)
        self.assertEqual(
            b2["final_judge_saved_by_worker_count"],
            sum(1 for row in b2["history"] if row.get("final_judge_called") is False and int(row.get("added_to_master_count") or 0) > 0),
        )
        self.assertEqual(b2["selected_count"], b2["harvest_selected_count"])
        self.assertEqual(b2["added_to_master_count"], b2["added_column_count"])
        self.assertFalse(b2["exact_first_step_bound_profile"]["exact_first_step_bound_pruning_enabled"])

    def test_b4_1_tail_dual_stabilization_worker_opt_in_remains_noncertifying(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b2 = solve_b2_pricing_tail_baseline(
            data,
            max_direct_tasks=5,
            max_rounds=1,
            mode=B2B_R2_MODE,
            tail_dual_stabilization_enabled=True,
            tail_dual_stabilization_alpha=0.7,
            tail_dual_stabilization_window=5,
        )
        worker_rows = [row for row in b2["history"] if row.get("final_judge_called") is False]
        self.assertGreater(len(worker_rows), 0)
        first_worker = worker_rows[0]
        self.assertEqual(first_worker["diagnostic_dual_source"], "tail_dual_stabilized_worker_dual")
        self.assertEqual(first_worker["worker_dual_source"], "tail_dual_stabilized_worker_dual")
        self.assertEqual(first_worker["official_dual_source"], "current_true_rmp_dual")
        self.assertTrue(first_worker["worker_dual_only"])
        self.assertTrue(first_worker["true_dual_rc_recomputed"])
        self.assertFalse(first_worker["tail_dual_no_column_can_certify"])
        self.assertTrue(first_worker["tail_dual_stabilization"]["tail_dual_stabilization_enabled"])
        self.assertEqual(first_worker["tail_dual_stabilization"]["tail_dual_stabilization_alpha"], 0.7)
        self.assertEqual(first_worker["tail_dual_stabilization"]["tail_dual_stabilization_window"], 5)
        self.assertEqual(
            first_worker["tail_dual_stabilization"]["official_dual_source"],
            "current_true_rmp_dual",
        )
        self.assertFalse(first_worker["tail_dual_stabilization"]["can_certify_no_negative"])
        self.assertNotEqual(first_worker["pricing_state"], "CERTIFIED_NO_NEGATIVE")

    def test_b4_1_b2b_r2_passes_remaining_wall_time_to_final_judge(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        captured_limits = []

        def fake_final_judge(*args, **kwargs):
            captured_limits.append(kwargs.get("wall_time_limit_sec"))
            return SimpleNamespace(
                pricing_state=PricingState.CERTIFIED_NO_NEGATIVE,
                pricing_payload={
                    "pricing_state": "CERTIFIED_NO_NEGATIVE",
                    "pricing_rc_audit_pass": True,
                    "all_priced_columns_satisfy_branch_context": True,
                    "can_certify_no_negative": True,
                    "negative_column_count": 0,
                },
                all_priced_columns=tuple(),
            )

        with patch(
            "lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver.run_true_dual_root_final_judge",
            side_effect=fake_final_judge,
        ):
            result = solve_b2_pricing_tail_baseline(
                data,
                max_direct_tasks=5,
                max_rounds=2,
                wall_time_limit_sec=5.0,
                max_columns_per_round=4,
                mode=B2B_R2_MODE,
            )

        self.assertEqual(result["final_judge_call_count"], 1)
        self.assertEqual(len(captured_limits), 1)
        self.assertIsNotNone(captured_limits[0])
        self.assertGreater(captured_limits[0], 0.0)
        self.assertLessEqual(captured_limits[0], 5.0)

    def test_b2b_r3_worker_uses_true_rmp_dual_and_cannot_certify_locally(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b2 = solve_b2_pricing_tail_baseline(
            data,
            max_direct_tasks=5,
            max_rounds=1,
            mode=B2B_R3_MODE,
        )

        self.assertEqual(b2["b2_mode"], B2B_R3_MODE)
        self.assertEqual(b2["seed_builder"], "b2b_r3_lightweight_no_full_universe_enumeration")
        self.assertEqual(b2["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(b2["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
        self.assertEqual(b2["pricing_state"], "INCOMPLETE_LIMIT")
        self.assertFalse(b2["root_lp_bound_official"])
        self.assertFalse(b2["uses_true_dual_bpc_certificate"])
        self.assertEqual(b2["final_judge_call_count"], 0)
        self.assertEqual(b2["diagnostic_dual_source"], "master.reduced_cost_context")
        self.assertTrue(b2["diagnostic_dual_fingerprint"])
        self.assertGreater(b2["worker_found_addable_negative_count"], 0)
        self.assertGreater(b2["labels_generated_total"], 0)
        self.assertIsNotNone(b2["labels_generated_before_first_negative"])
        self.assertEqual(b2["history"][0]["diagnostic_dual_source"], "master.reduced_cost_context")
        self.assertTrue(b2["history"][0]["diagnostic_dual_fingerprint"])
        self.assertFalse(b2["history"][0]["rmp_dual_diagnostic"]["can_certify_no_negative"])

    def test_b2a_full_universe_rc_audit_fast_path_is_explicit(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b2a = solve_b2_pricing_tail_baseline(data, max_direct_tasks=5, max_rounds=8, mode=B2A_MODE)

        self.assertEqual(b2a["b2_mode"], B2A_MODE)
        self.assertTrue(b2a["full_universe_preloaded"])
        self.assertEqual(b2a["algorithm_status"], "BPC_GAP_AVAILABLE")
        self.assertEqual(b2a["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertEqual(b2a["pricing_state"], "CERTIFIED_NO_NEGATIVE")
        self.assertEqual(b2a["final_judge_call_count"], 0)
        self.assertEqual(b2a["manual_rc_audit"]["status"], "FULL_UNIVERSE_RC_AUDIT_PASS")
        self.assertTrue(b2a["manual_rc_audit"]["full_universe_complete"])
        self.assertTrue(b2a["manual_rc_audit"]["all_columns_in_master"])
        self.assertTrue(b2a["manual_rc_audit_pass"])
        self.assertTrue(b2a["pricing_rc_audit_pass"])
        self.assertTrue(b2a["root_lp_bound_official"])

    def test_b3_root_integral_node_closes_branch_price_tree(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b3 = solve_b3_branch_price_tree_baseline(data, max_direct_tasks=5, max_rounds_per_node=8)

        self.assertEqual(b3["algorithm_status"], "BPC_OPTIMAL")
        self.assertEqual(b3["certificate_scope"], "BPC_TREE_OPTIMAL")
        self.assertEqual(b3["exact_status"], "BPC_TREE_OPTIMAL")
        self.assertTrue(b3["uses_true_dual_bpc_certificate"])
        self.assertTrue(b3["certificate_ledger"]["valid"])
        self.assertEqual(b3["tree_certificate_gate_issues"], [])
        self.assertTrue(b3["tree_closed"])
        self.assertTrue(b3["all_nodes_fathomed"])
        self.assertTrue(b3["all_node_lower_bounds_official"])
        self.assertEqual(b3["node_count"], 1)
        self.assertEqual(b3["open_node_count"], 0)
        self.assertEqual(b3["root_node_status"], "INTEGER_INCUMBENT")
        self.assertTrue(b3["root_integral"])
        self.assertEqual(b3["root_integral_count"], 1)
        self.assertEqual(b3["root_fractional_count"], 0)
        self.assertEqual(b3["incomplete_node_count"], 0)
        self.assertEqual(b3["bpc_tree_optimal_count"], 1)
        self.assertEqual(b3["global_gap"], 0.0)
        self.assertEqual(b3["global_lower_bound"], b3["incumbent_objective"])
        self.assertEqual(b3["objective_match_direct_dp_count"], 1)
        self.assertFalse(b3["b0_ablation"]["direct_dp_used_as_bpc_certificate"])
        self.assertTrue(b3["b0_ablation"]["objective_match_direct_dp"])
        self.assertEqual(b3["b2_ablation"]["objective_diff_vs_B2"], 0.0)
        self.assertEqual(
            b3["b2_ablation"]["certificate_scope_diff_vs_B2"],
            "BPC_NODE_LP_CERTIFIED->BPC_TREE_OPTIMAL",
        )
        root_node = b3["nodes"][0]
        self.assertEqual(root_node["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertTrue(root_node["node_lp_bound_official"])
        self.assertTrue(root_node["certificate_ledger"]["valid"])
        self.assertTrue(root_node["all_priced_columns_satisfy_branch_context"])
        self.assertFalse(root_node["completion_bound_pruning_enabled"])

    def test_b3_tree_can_close_from_provided_initial_columns_without_b0_prerun(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)

        b3 = solve_b3_branch_price_tree_baseline(
            data,
            initial_columns=universe.columns,
            max_direct_tasks=5,
            max_rounds_per_node=2,
            use_complete_universe_audit=False,
            run_b2_root_diagnostic=False,
            solve_b0_direct_first=False,
        )

        self.assertEqual(b3["certificate_scope"], "BPC_TREE_OPTIMAL")
        self.assertEqual(b3["exact_status"], "BPC_TREE_OPTIMAL")
        self.assertEqual(b3["tree_seed_source"], "provided_initial_columns")
        self.assertEqual(b3["initial_tree_seed_column_count"], len(universe.columns))
        self.assertFalse(b3["solve_b0_direct_first"])
        self.assertEqual(b3["b0_ablation"]["direct_dp_status"], "NOT_RUN")
        self.assertFalse(b3["b0_ablation"]["direct_dp_used_as_bpc_certificate"])

    def test_b3_fail_closed_records_reference_incumbent_without_certificate(self) -> None:
        instance = generate_instance(10, seed=729001, index=1)
        data = load_lunar_ice_data(instance)
        b0_timeout = SimpleNamespace(
            status="DIRECT_DP_TIME_LIMIT",
            certificate_scope="FEASIBLE_INCUMBENT_ONLY",
            objective=None,
            journeys=tuple(),
            objective_breakdown=None,
            reference_solution_upper_bound=None,
            reference_solution_upper_bound_source="",
            direct_bound_pruning_root_bound=None,
            direct_bound_pruning_active=False,
            journey_label_bound_pruned_count=0,
            note="synthetic direct timeout",
        )

        b3 = solve_b3_branch_price_tree_baseline(
            data,
            b0_direct=b0_timeout,
            max_direct_tasks=10,
            max_rounds_per_node=1,
            max_tree_nodes=1,
            max_branch_depth=0,
            run_b2_root_diagnostic=False,
        )

        self.assertEqual(b3["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(b3["certificate_scope"], "FEASIBLE_INCUMBENT_ONLY")
        self.assertEqual(b3["exact_status"], "NOT_SOLVED")
        self.assertFalse(b3["uses_true_dual_bpc_certificate"])
        self.assertIn("direct_dp_incumbent_missing", b3["tree_certificate_gate_issues"])
        self.assertIsNotNone(b3["reference_solution_upper_bound"])
        self.assertEqual(b3["reference_solution_upper_bound_source"], "instance_reference_solution_best_path_repair")
        self.assertEqual(b3["global_ub"], b3["reference_solution_upper_bound"])
        self.assertEqual(b3["incumbent_objective"], b3["reference_solution_upper_bound"])
        self.assertTrue(str(b3["feasible_incumbent_source"]).startswith("REFERENCE_FEASIBLE_INCUMBENT"))
        self.assertFalse(b3["feasible_incumbent_used_as_bpc_certificate"])
        self.assertIsNotNone(b3["objective_breakdown"])
        self.assertEqual(b3["b0_ablation"]["direct_dp_objective"], None)
        self.assertFalse(b3["b0_ablation"]["direct_dp_used_as_bpc_certificate"])

    def test_b3_node_final_judge_respects_branch_context(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        task_a, task_b = data.task_ids[:2]
        context = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))
        node = _solve_b3_node(
            data,
            universe.columns,
            _QueuedNode("node_same", None, 0, context),
            incumbent_objective_at_entry=None,
            max_direct_tasks=5,
            max_rounds=8,
            wall_time_limit_sec=30.0,
            negative_eps=1.0e-6,
            max_columns_per_round=64,
            use_complete_universe_audit=True,
        )

        self.assertEqual(node["schema_version"], "lunar_ice_bpc.b3_branch_node.v1")
        self.assertEqual(node["node_status"], "NODE_LP_CERTIFIED")
        self.assertEqual(node["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertTrue(node["node_lp_bound_official"])
        self.assertTrue(node["certificate_ledger"]["valid"])
        self.assertTrue(node["all_priced_columns_satisfy_branch_context"])
        self.assertGreater(node["branch_filtered_column_count"], 0)
        self.assertTrue(node["final_judge"]["branch_context_active"])
        self.assertEqual(node["final_judge"]["branch_decision_count"], 1)
        self.assertGreater(node["final_judge"]["branch_filtered_column_count"], 0)
        self.assertEqual(node["final_judge"]["pricing_state"], "CERTIFIED_NO_NEGATIVE")
        self.assertTrue(node["final_judge"]["all_priced_columns_satisfy_branch_context"])
        self.assertEqual(
            node["final_judge"]["column_universe_semantics"],
            TASK_SUBSET_REPRESENTATIVE_UNIVERSE_SEMANTICS,
        )
        self.assertFalse(node["final_judge"]["complete_universe_contains_all_route_variants"])

    def test_b3_uses_complete_universe_node_pricing_audit(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b3 = solve_b3_branch_price_tree_baseline(data, max_direct_tasks=5, max_rounds_per_node=8)

        self.assertEqual(b3["b3_mode"], "B3B_seeded_branch_price_tree")
        self.assertEqual(b3["node_pricing_mode"], B3_COMPLETE_UNIVERSE_NODE_MODE)
        self.assertEqual(b3["nodes"][0]["node_pricing_mode"], B3_COMPLETE_UNIVERSE_NODE_MODE)
        self.assertEqual(
            b3["nodes"][0]["node_certificate_source"],
            "complete_universe_branch_membership_rc_audit",
        )
        self.assertEqual(b3["nodes"][0]["complete_universe_source"], "provided_complete_universe_cache")
        self.assertEqual(
            b3["nodes"][0]["column_universe_semantics"],
            TASK_SUBSET_REPRESENTATIVE_UNIVERSE_SEMANTICS,
        )
        self.assertFalse(b3["nodes"][0]["complete_universe_contains_all_route_variants"])
        self.assertFalse(b3["nodes"][0]["full_universe_preloaded"])
        self.assertFalse(b3["b0_ablation"]["direct_dp_used_as_bpc_certificate"])

    def test_b3_tree_gate_downgrades_if_tree_ledger_validation_fails(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        direct = solve_direct_journey_baseline(data, max_exact_tasks=5)
        node = {
            "node_id": "node_000",
            "node_status": "INTEGER_INCUMBENT",
            "node_lp_bound": direct.objective,
            "node_lp_bound_official": True,
            "child_node_ids": [],
            "certificate_ledger": {"valid": True},
            "integer_incumbent": {"matches_node_lp_bound": True},
        }

        class FlakyTreeLedger:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def validate(self, proof_debt_queue=None):
                if str(self.kwargs["certificate_scope"]) == "BPC_TREE_OPTIMAL":
                    return {
                        "algorithm_status": str(self.kwargs["algorithm_status"]),
                        "certificate_scope": "BPC_TREE_OPTIMAL",
                        "pricing_state": str(self.kwargs["pricing_state"]),
                        "uses_true_dual_bpc_certificate": True,
                        "certificate_status": "INVALID_CERTIFICATE_SCOPE",
                        "issues": ["forced_tree_ledger_invalid"],
                        "valid": False,
                    }
                return CertificateLedger(**self.kwargs).validate(proof_debt_queue=proof_debt_queue)

        with patch("lunar_ice_bpc.exact.bpc.solver.branch_tree_solver.CertificateLedger", FlakyTreeLedger):
            payload = _tree_payload(
                data=data,
                b2={"root_rmp_objective": direct.objective, "certificate_scope": "BPC_NODE_LP_CERTIFIED"},
                b0_direct=direct,
                nodes=[node],
                open_node_count=0,
                incumbent_objective=direct.objective,
                incumbent_source="B3_INTEGER_NODE:node_000",
                incumbent_columns=tuple(direct.journeys),
                proof_debt=ProofDebtQueue(),
                node_limit_hit=False,
                max_tree_nodes=31,
                max_branch_depth=4,
                negative_eps=1.0e-6,
            )

        self.assertEqual(payload["algorithm_status"], "BPC_GAP_AVAILABLE")
        self.assertEqual(payload["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertEqual(payload["exact_status"], "BPC_NODE_LP_CERTIFIED")
        self.assertEqual(payload["bpc_tree_optimal_count"], 0)
        self.assertIn("forced_tree_ledger_invalid", payload["tree_certificate_gate_issues"])

    def test_b2b_r3_node_engine_worker_no_column_is_not_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        node = solve_node_pricing_with_b2b_r3(
            data,
            node_id="node_probe",
            max_direct_tasks=5,
            max_rounds=1,
            max_columns_per_round=1,
        )

        worker_rounds = [row for row in node["history"] if not row.get("final_judge_called")]
        for row in worker_rounds:
            self.assertNotEqual(row["pricing_state"], "CERTIFIED_NO_NEGATIVE")
            self.assertFalse(row["rmp_dual_diagnostic"]["can_certify_no_negative"])
        if node["certificate_scope"] == "BPC_NODE_LP_CERTIFIED":
            self.assertGreater(node["final_judge_call_count"], 0)
            self.assertEqual(node["final_judge"]["pricing_state"], "CERTIFIED_NO_NEGATIVE")

    def test_b2b_r3_node_engine_harvest_respects_branch_context(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        task_a, task_b = data.task_ids[:2]
        same_context = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))
        one_only = next(column for column in universe.columns if task_a in column.task_set and task_b not in column.task_set)
        both_or_neither = next(column for column in universe.columns if journey_satisfies_branch_context(column, same_context))

        selected, payload = harvest_addable_negative_columns(
            ((-10.0, one_only), (-5.0, both_or_neither)),
            pool=ColumnPool(),
            view=MasterColumnView(),
            node_id="node_same",
            negative_eps=1.0e-6,
            max_selected=10,
            branch_context=same_context,
        )

        self.assertEqual(selected, (both_or_neither,))
        self.assertEqual(payload["branch_filtered_count"], 1)
        rejected = [row for row in payload["reports"] if row["task_set"] == sorted(one_only.task_set)]
        self.assertEqual(rejected[0]["reject_reason"], "branch_infeasible")
        self.assertFalse(rejected[0]["is_allowed_by_branch"])

    def test_b3_direct_dp_incumbent_does_not_create_tree_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b3 = solve_b3_branch_price_tree_baseline(data, max_direct_tasks=4, max_rounds_per_node=1)

        self.assertNotEqual(b3["certificate_scope"], "BPC_TREE_OPTIMAL")
        self.assertFalse(b3["uses_true_dual_bpc_certificate"])
        self.assertFalse(b3["b0_ablation"]["direct_dp_used_as_bpc_certificate"])
        self.assertIn("task_count_exceeds_exhaustive_pricing_limit", b3["tree_certificate_gate_issues"])

    def test_no_fractional_rf_pair_is_not_integrality_proof(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        full_cover = next(column for column in universe.columns if set(column.task_set) == set(data.task_ids))
        duplicate_relation_primal = (
            {
                "lambda_value": 0.5,
                "tasks": sorted(full_cover.task_set),
            },
            {
                "lambda_value": 0.5,
                "tasks": sorted(full_cover.task_set),
            },
        )
        probe = build_fractional_branch_probe(
            data.task_ids,
            duplicate_relation_primal,
            (full_cover,),
            max_candidates=3,
        )

        self.assertEqual(probe["status"], "NO_FRACTIONAL_BRANCH_CANDIDATE")
        self.assertTrue(any(float(row["lambda_value"]) < 1.0 for row in duplicate_relation_primal))
        self.assertFalse(probe["can_certify"])
        self.assertEqual(probe["exact_status_effect"], "none")

    def test_b4_subset_row_diagnostic_mode_preserves_b3_certificate_scope(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b4 = solve_b4_cut_formulation_baseline(data, max_direct_tasks=5, max_rounds=8)

        self.assertEqual(b4["schema_version"], "lunar_ice_bpc.b4_cut_formulation_baseline.v1")
        self.assertEqual(b4["algorithm_status"], "BPC_OPTIMAL")
        self.assertEqual(b4["certificate_scope"], "BPC_TREE_OPTIMAL")
        self.assertEqual(b4["exact_status"], "BPC_TREE_OPTIMAL")
        self.assertFalse(b4["live_subset_rows"])
        self.assertFalse(b4["cut_rows_active"])
        self.assertEqual(b4["cut_added_count"], 0)
        self.assertFalse(b4["fleet_lower_bound_live_enabled"])
        self.assertEqual(b4["lp_bound_delta"], 0.0)
        self.assertEqual(b4["root_gap_delta"], 0.0)
        self.assertFalse(b4["cut_effective_claim"])
        self.assertEqual(b4["b3_ablation"]["objective_diff_vs_B3"], 0.0)
        self.assertEqual(b4["b3_ablation"]["certificate_scope_diff_vs_B3"], "")
        self.assertFalse(b4["completion_bound_policy"]["pruning_enabled"])
        self.assertEqual(b4["cut_probe"]["schema_version"], "lunar_ice_bpc.cut_probe.v1")
        self.assertFalse(b4["diagnostic_cut_separation_round"]["lower_bound_official"])
        self.assertFalse(b4["diagnostic_cut_separation_round"]["can_certify"])
        self.assertTrue(b4["final_integer_optimum_unchanged_vs_B3"])

    def test_b4_live_subset_row_opt_in_keeps_cut_certificate_audits_tight(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b4 = solve_b4_cut_formulation_baseline(
            data,
            max_direct_tasks=5,
            max_rounds=8,
            live_subset_rows=True,
            max_live_cuts=1,
            add_violated_only=False,
        )

        self.assertTrue(b4["live_subset_rows"])
        self.assertTrue(b4["cut_rows_active"])
        self.assertEqual(b4["cut_added_count"], 1)
        self.assertFalse(b4["fleet_lower_bound_live_enabled"])
        self.assertEqual(b4["certificate_scope"], "BPC_TREE_OPTIMAL")
        self.assertEqual(b4["exact_status"], "BPC_TREE_OPTIMAL")
        self.assertTrue(b4["uses_true_dual_bpc_certificate"])
        self.assertTrue(b4["certificate_ledger"]["valid"])
        self.assertTrue(b4["root_lp_bound_official"])
        self.assertTrue(b4["final_integer_optimum_unchanged_vs_B3"])
        self.assertFalse(b4["completion_bound_policy"]["pruning_enabled"])
        self.assertTrue(b4["completion_bound_policy"]["cut_context_active"])
        self.assertFalse(b4["completion_bound_policy"]["can_certify_no_negative"])
        audit = b4["cut_reduced_cost_audit"]
        self.assertTrue(audit["manual_rc_cut_consistency_pass"])
        self.assertTrue(audit["manual_rc_with_cuts_matches_pricing_rc"])
        self.assertTrue(audit["cut_dual_sign_audit_pass"])
        self.assertEqual(
            audit["manual_best_reduced_cost"],
            audit["pricing_best_reduced_cost"],
        )
        self.assertEqual(b4["final_judge"]["pricing_state"], "CERTIFIED_NO_NEGATIVE")
        self.assertTrue(b4["final_judge"]["cut_context_active"])
        self.assertFalse(b4["final_judge"]["completion_bound_pruning_enabled"])
        self.assertTrue(b4["cut_dominance_compatibility_report"]["valid"])
        self.assertGreaterEqual(b4["cut_pricing_supported_count"], 1)
        self.assertGreaterEqual(b4["cut_completion_bound_fail_closed_count"], 1)
        self.assertTrue(b4["cut_aware_signature_summary"]["all_active_signatures_include_cut_hash"])
        self.assertFalse(b4["cut_effective_claim"])
        self.assertEqual(b4["b3_ablation"]["objective_diff_vs_B3"], 0.0)

    def test_b4_ten_task_over_limit_fails_closed_without_cut_certificate(self) -> None:
        instance = generate_instance(10, seed=729101, index=1)
        data = load_lunar_ice_data(instance)
        b4 = solve_b4_cut_formulation_baseline(data, max_direct_tasks=5, max_rounds=8)

        self.assertEqual(b4["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(b4["certificate_scope"], "FEASIBLE_INCUMBENT_ONLY")
        self.assertEqual(b4["exact_status"], "NOT_SOLVED")
        self.assertFalse(b4["uses_true_dual_bpc_certificate"])
        self.assertFalse(b4["live_subset_rows"])
        self.assertFalse(b4["cut_rows_active"])
        self.assertEqual(b4["cut_added_count"], 0)
        self.assertEqual(b4["b3_ablation"]["certificate_scope_diff_vs_B3"], "FEASIBLE_INCUMBENT_ONLY->FEASIBLE_INCUMBENT_ONLY")
        self.assertIn("exceeds max_direct_tasks", b4["note"])

    def test_b4_memory_guard_uses_restricted_pool_cut_diagnostic_without_certificate(self) -> None:
        instance = generate_instance(20, seed=829001, index=1)
        data = load_lunar_ice_data(instance)
        b4 = solve_b4_cut_formulation_baseline(data, max_direct_tasks=20, max_rounds=8)

        self.assertTrue(b4["rmp_memory_precheck_failed"])
        self.assertEqual(b4["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
        self.assertEqual(b4["exact_status"], "NOT_SOLVED")
        self.assertFalse(b4["uses_true_dual_bpc_certificate"])
        self.assertEqual(
            b4["restricted_pool_cut_diagnostic"]["status"],
            "RESTRICTED_POOL_CUT_DIAGNOSTIC_READY",
        )
        self.assertEqual(
            b4["cut_probe"]["evaluation_scope"],
            "safe_restricted_seed_pool_only",
        )
        self.assertFalse(b4["cut_probe"]["can_certify"])
        self.assertFalse(b4["diagnostic_cut_separation_round"]["can_certify"])

    def test_b5_shadow_guidance_preserves_b4_do_no_harm_after_debt_release(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b5 = solve_b5_gat_guidance_shadow_baseline(
            data,
            guidance_hints=(
                {
                    "candidate_id": "neg-001",
                    "priority": 0.9,
                    "source": "shadow_unit_test",
                    "finite_delay_budget": 1,
                    "diagnostic_only": True,
                },
            ),
            true_rc_candidates=(
                {
                    "candidate_id": "neg-001",
                    "true_reduced_cost": -0.25,
                    "addability_accepted": True,
                    "reject_reason": "",
                },
            ),
            release_before_certificate=True,
            max_direct_tasks=5,
            max_rounds=8,
        )

        self.assertEqual(b5["schema_version"], "lunar_ice_bpc.b5_gat_guidance_shadow_baseline.v1")
        self.assertEqual(b5["mode"], "shadow_only")
        self.assertEqual(b5["certificate_scope"], "BPC_TREE_OPTIMAL")
        self.assertEqual(b5["exact_status"], "BPC_TREE_OPTIMAL")
        self.assertTrue(b5["uses_true_dual_bpc_certificate"])
        self.assertTrue(b5["do_no_harm_pass"])
        self.assertEqual(b5["do_no_harm_issues"], [])
        self.assertEqual(b5["b4_ablation"]["objective_diff"], 0.0)
        self.assertEqual(b5["b4_ablation"]["certificate_scope_diff"], "")
        self.assertEqual(b5["b4_ablation"]["BPC_INCOMPLETE_count_diff"], 0)
        metrics = b5["proof_debt_metrics"]
        self.assertEqual(metrics["delayed_negative_count"], 1)
        self.assertEqual(metrics["released_before_certificate_count"], 1)
        self.assertEqual(metrics["rechecked_before_certificate_count"], 1)
        self.assertFalse(metrics["certificate_blocked_by_delayed_negative"])
        self.assertTrue(metrics["proof_debt_queue_empty_before_certificate"])
        safety = b5["safety_metrics"]
        self.assertTrue(safety["objective_unchanged"])
        self.assertTrue(safety["certificate_scope_unchanged"])
        self.assertTrue(safety["no_permanent_negative_drop"])
        self.assertEqual(safety["delayed_true_negative_release_rate"], 1.0)
        self.assertEqual(safety["false_safe_rate"], 0.0)
        shadow = b5["guidance_shadow_accounting"]
        self.assertFalse(shadow["guidance_can_construct_certificate"])
        self.assertFalse(shadow["guidance_can_mutate_exact_state"])
        self.assertFalse(shadow["mutates_solver"])
        self.assertFalse(shadow["can_certify"])
        self.assertEqual(shadow["candidate_addability_labels"][0]["label_type"], "candidate_addability_label")
        self.assertEqual(shadow["delayed_negative_debt_labels"][0]["label_type"], "delayed_negative_debt_label")
        self.assertTrue(shadow["delayed_negative_debt_labels"][0]["released_before_certificate"])
        label_manifest = b5["shadow_label_manifest"]
        self.assertEqual(label_manifest["schema_version"], "lunar_ice_bpc.b5_shadow_label_manifest.v1")
        self.assertTrue(label_manifest["required_label_sections_present"])
        self.assertTrue(label_manifest["mandatory_first_batch_labels_present"])
        self.assertGreaterEqual(label_manifest["label_counts"]["observed_true_rc_negative_found_by_final_judge"], 1)
        self.assertEqual(label_manifest["label_counts"]["candidate_addability_label"], 1)
        self.assertEqual(label_manifest["label_counts"]["delayed_negative_debt_label"], 1)
        self.assertEqual(label_manifest["split_policy"]["main_split_keys"], ["instance", "scale", "seed_family"])
        self.assertFalse(label_manifest["split_policy"]["random_row_split_is_main_claim"])

    def test_b5_unreleased_delayed_negative_blocks_guidance_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b5 = solve_b5_gat_guidance_shadow_baseline(
            data,
            guidance_hints=(
                {
                    "candidate_id": "neg-001",
                    "priority": 0.9,
                    "source": "shadow_unit_test",
                    "finite_delay_budget": 1,
                    "diagnostic_only": True,
                },
            ),
            true_rc_candidates=(
                {
                    "candidate_id": "neg-001",
                    "true_reduced_cost": -0.25,
                    "addability_accepted": True,
                },
            ),
            release_before_certificate=False,
            max_direct_tasks=5,
            max_rounds=8,
        )

        self.assertEqual(b5["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(b5["certificate_scope"], "FEASIBLE_INCUMBENT_ONLY")
        self.assertEqual(b5["exact_status"], "NOT_SOLVED")
        self.assertFalse(b5["uses_true_dual_bpc_certificate"])
        self.assertFalse(b5["do_no_harm_pass"])
        self.assertIn("proof_debt_not_released_before_certificate", b5["do_no_harm_issues"])
        self.assertIn("certificate_scope_changed_by_guidance", b5["do_no_harm_issues"])
        self.assertIn("additional_bpc_incomplete_caused_by_guidance", b5["do_no_harm_issues"])
        metrics = b5["proof_debt_metrics"]
        self.assertEqual(metrics["delayed_negative_count"], 1)
        self.assertEqual(metrics["released_before_certificate_count"], 0)
        self.assertTrue(metrics["certificate_blocked_by_delayed_negative"])
        self.assertFalse(metrics["proof_debt_queue_empty_before_certificate"])
        self.assertEqual(b5["safety_metrics"]["delayed_true_negative_release_rate"], 0.0)
        self.assertFalse(b5["performance_metrics"]["eligible_for_performance_claim"])
        self.assertEqual(
            b5["b4_ablation"]["certificate_scope_diff"],
            "BPC_TREE_OPTIMAL->FEASIBLE_INCUMBENT_ONLY",
        )

    def test_b5_ordering_opt_in_reorders_without_dropping_or_certifying(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b5 = solve_b5_gat_guidance_shadow_baseline(
            data,
            guidance_hints=(
                {"candidate_id": "p2", "priority": 0.95, "source": "ordering_unit_test"},
                {"candidate_id": "p1", "priority": 0.25, "source": "ordering_unit_test"},
                {"candidate_id": "b2", "priority": 0.80, "source": "ordering_unit_test"},
                {"candidate_id": "h2", "priority": 0.70, "source": "ordering_unit_test"},
            ),
            pricing_candidates=(
                {"candidate_id": "p1", "task_set": ["ice_site_001"]},
                {"candidate_id": "p2", "task_set": ["ice_site_002"]},
                {"candidate_id": "p3", "task_set": ["ice_site_003"]},
            ),
            branch_candidates=(
                {"candidate_id": "b1", "pair": ["ice_site_001", "ice_site_002"]},
                {"candidate_id": "b2", "pair": ["ice_site_002", "ice_site_003"]},
            ),
            harvest_candidates=(
                {"candidate_id": "h1", "true_reduced_cost": -0.2},
                {"candidate_id": "h2", "true_reduced_cost": -0.1},
            ),
            enabled_ordering_modes=("pricing", "branch", "harvest"),
            max_direct_tasks=5,
            max_rounds=8,
        )

        self.assertEqual(b5["mode"], "ordering_opt_in")
        self.assertTrue(b5["do_no_harm_pass"])
        self.assertEqual(b5["certificate_scope"], "BPC_TREE_OPTIMAL")
        self.assertEqual(b5["exact_status"], "BPC_TREE_OPTIMAL")
        self.assertEqual(b5["b4_ablation"]["objective_diff"], 0.0)
        self.assertEqual(b5["b4_ablation"]["certificate_scope_diff"], "")
        ordering = b5["ordering_ablation"]
        self.assertTrue(ordering["all_candidate_sets_preserved"])
        self.assertFalse(ordering["mutates_solver"])
        self.assertFalse(ordering["can_certify"])
        self.assertEqual(ordering["exact_status_effect"], "none")
        self.assertEqual(ordering["enabled_ordering_count"], 3)
        self.assertEqual(ordering["pricing_ordering_opt_in"]["before_ids"], ["p1", "p2", "p3"])
        self.assertEqual(ordering["pricing_ordering_opt_in"]["after_ids"], ["p2", "p1", "p3"])
        self.assertEqual(ordering["branch_ordering_opt_in"]["after_ids"], ["b2", "b1"])
        self.assertEqual(ordering["harvest_ordering_opt_in"]["after_ids"], ["h2", "h1"])
        self.assertEqual(ordering["pricing_ordering_opt_in"]["rejected_candidate_count"], 0)
        self.assertEqual(ordering["pricing_ordering_opt_in"]["permanently_dropped_candidate_count"], 0)
        self.assertTrue(b5["safety_metrics"]["ordering_candidate_sets_preserved"])
        self.assertTrue(b5["performance_metrics"]["eligible_for_performance_claim"])
        self.assertTrue(b5["performance_metrics"]["pricing_ordering_enabled"])
        self.assertTrue(b5["performance_metrics"]["branch_ordering_enabled"])
        self.assertTrue(b5["performance_metrics"]["harvest_ordering_enabled"])

    def test_b5_guidance_output_bundle_records_heads_and_diagnostics_as_audit_only(self) -> None:
        bundle = build_guidance_output_bundle(
            pricing_priority_head=(
                {
                    "candidate_id": "p2",
                    "priority": 0.9,
                    "uncertainty": 0.1,
                    "model_version": "gat_shadow_test_v1",
                },
            ),
            branch_priority_head=({"candidate_id": "b2", "priority": 0.8},),
            harvest_priority_head=({"candidate_id": "h2", "priority": 0.7},),
            ood_diagnostics={"status": "IN_DISTRIBUTION", "knn_distance": 0.12, "ood_rule_hash": "ood-v1"},
            confidence_diagnostics={"min_confidence": 0.81, "threshold": 0.75, "threshold_version": "thr-v1"},
        )

        self.assertEqual(bundle["schema_version"], "lunar_ice_bpc.b5_guidance_output_bundle.v1")
        self.assertEqual(
            bundle["required_heads"],
            ["pricing_priority_head", "branch_priority_head", "harvest_priority_head"],
        )
        self.assertTrue(bundle["required_heads_present"])
        self.assertEqual(bundle["head_counts"]["pricing_priority_head"], 1)
        self.assertEqual(bundle["head_counts"]["branch_priority_head"], 1)
        self.assertEqual(bundle["head_counts"]["harvest_priority_head"], 1)
        self.assertEqual(bundle["head_counts"]["proof_tail_risk_head"], 0)
        self.assertEqual(bundle["heads"]["pricing_priority_head"][0]["model_version"], "gat_shadow_test_v1")
        self.assertTrue(bundle["ood_confidence_diagnostics_present"])
        self.assertTrue(bundle["diagnostic_versions_complete"])
        self.assertEqual(bundle["diagnostic_version_issues"], [])
        self.assertFalse(bundle["diagnostics_can_certify"])
        self.assertFalse(bundle["diagnostics_lower_bound_official"])
        self.assertFalse(bundle["guidance_can_construct_certificate"])
        self.assertFalse(bundle["guidance_can_mutate_exact_state"])
        self.assertFalse(bundle["can_fathom"])
        self.assertFalse(bundle["can_prune"])
        self.assertEqual(bundle["exact_status_effect"], "none")

        unversioned = build_guidance_output_bundle(
            pricing_priority_head=(),
            branch_priority_head=(),
            harvest_priority_head=(),
            ood_diagnostics={"status": "IN_DISTRIBUTION"},
            confidence_diagnostics={"min_confidence": 0.81},
        )
        self.assertFalse(unversioned["diagnostic_versions_complete"])
        self.assertIn("missing_ood_rule_version_or_hash", unversioned["diagnostic_version_issues"])
        self.assertIn(
            "missing_confidence_or_threshold_version_or_hash",
            unversioned["diagnostic_version_issues"],
        )
        self.assertFalse(unversioned["diagnostics_can_certify"])

    def test_b5_solver_consumes_head_specific_guidance_bundle_for_ordering_only(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        bundle = build_guidance_output_bundle(
            pricing_priority_head=({"candidate_id": "p2", "priority": 0.95},),
            branch_priority_head=({"candidate_id": "b2", "priority": 0.80},),
            harvest_priority_head=({"candidate_id": "h2", "priority": 0.70},),
            ood_diagnostics={"status": "SHADOW_AUDIT_ONLY", "ood_rule_version": "shadow-ood-v1"},
        )
        b5 = solve_b5_gat_guidance_shadow_baseline(
            data,
            guidance_output_bundle=bundle,
            pricing_candidates=(
                {"candidate_id": "p1", "task_set": ["ice_site_001"]},
                {"candidate_id": "p2", "task_set": ["ice_site_002"]},
                {"candidate_id": "p3", "task_set": ["ice_site_003"]},
            ),
            branch_candidates=(
                {"candidate_id": "b1", "pair": ["ice_site_001", "ice_site_002"]},
                {"candidate_id": "b2", "pair": ["ice_site_002", "ice_site_003"]},
            ),
            harvest_candidates=(
                {"candidate_id": "h1", "true_reduced_cost": -0.2},
                {"candidate_id": "h2", "true_reduced_cost": -0.1},
            ),
            enabled_ordering_modes=("pricing", "branch", "harvest"),
            max_direct_tasks=5,
            max_rounds=8,
        )

        self.assertTrue(b5["do_no_harm_pass"])
        self.assertEqual(b5["certificate_scope"], "BPC_TREE_OPTIMAL")
        self.assertEqual(b5["b4_ablation"]["certificate_scope_diff"], "")
        self.assertEqual(b5["guidance_output_bundle"]["head_counts"]["pricing_priority_head"], 1)
        self.assertTrue(b5["guidance_output_bundle"]["ood_confidence_diagnostics_present"])
        self.assertTrue(b5["guidance_output_bundle"]["diagnostic_versions_complete"])
        ordering = b5["ordering_ablation"]
        self.assertEqual(ordering["pricing_ordering_opt_in"]["after_ids"], ["p2", "p1", "p3"])
        self.assertEqual(ordering["branch_ordering_opt_in"]["after_ids"], ["b2", "b1"])
        self.assertEqual(ordering["harvest_ordering_opt_in"]["after_ids"], ["h2", "h1"])
        self.assertTrue(ordering["all_candidate_sets_preserved"])
        self.assertFalse(ordering["can_certify"])
        self.assertFalse(b5["guidance_output_bundle"]["can_prune"])

    def test_b5_workload_ablation_requires_safety_then_non_regressing_improvement(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b5 = solve_b5_gat_guidance_shadow_baseline(
            data,
            guidance_hints=({"candidate_id": "p2", "priority": 0.9},),
            pricing_candidates=({"candidate_id": "p1"}, {"candidate_id": "p2"}),
            enabled_ordering_modes=("pricing",),
            no_guidance_workload={
                "wall_time": 10.0,
                "pricing_calls": 7,
                "final_judge_calls": 2,
                "generated_labels": 100,
                "rmp_iterations": 4,
                "node_count": 1,
            },
            guidance_workload={
                "wall_time": 8.0,
                "pricing_calls": 6,
                "final_judge_calls": 2,
                "generated_labels": 90,
                "rmp_iterations": 4,
                "node_count": 1,
            },
            max_direct_tasks=5,
            max_rounds=8,
        )

        self.assertTrue(b5["do_no_harm_pass"])
        self.assertEqual(b5["certificate_scope"], "BPC_TREE_OPTIMAL")
        workload = b5["workload_ablation"]
        self.assertTrue(workload["workload_observed"])
        self.assertTrue(workload["performance_success"])
        self.assertEqual(workload["gate_issues"], [])
        self.assertEqual(workload["diffs"]["wall_time"], -2.0)
        self.assertEqual(workload["diffs"]["pricing_calls"], -1.0)
        self.assertEqual(workload["diffs"]["final_judge_calls"], 0.0)
        self.assertIn("wall_time", workload["improving_metrics"])
        self.assertEqual(workload["regressing_metrics"], [])
        self.assertTrue(b5["performance_metrics"]["performance_success"])
        self.assertEqual(b5["b4_ablation"]["wall_time_diff"], -2.0)
        self.assertEqual(b5["b4_ablation"]["pricing_call_diff"], -1.0)

    def test_b5_workload_regression_blocks_performance_claim_even_when_safe(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b5 = solve_b5_gat_guidance_shadow_baseline(
            data,
            guidance_hints=({"candidate_id": "p2", "priority": 0.9},),
            pricing_candidates=({"candidate_id": "p1"}, {"candidate_id": "p2"}),
            enabled_ordering_modes=("pricing",),
            no_guidance_workload={
                "wall_time": 10.0,
                "pricing_calls": 7,
                "final_judge_calls": 2,
                "generated_labels": 100,
                "rmp_iterations": 4,
                "node_count": 1,
            },
            guidance_workload={
                "wall_time": 11.0,
                "pricing_calls": 6,
                "final_judge_calls": 2,
                "generated_labels": 90,
                "rmp_iterations": 4,
                "node_count": 1,
            },
            max_direct_tasks=5,
            max_rounds=8,
        )

        self.assertTrue(b5["do_no_harm_pass"])
        self.assertEqual(b5["certificate_scope"], "BPC_TREE_OPTIMAL")
        workload = b5["workload_ablation"]
        self.assertTrue(workload["workload_observed"])
        self.assertFalse(workload["performance_success"])
        self.assertIn("wall_time", workload["regressing_metrics"])
        self.assertIn("workload_metric_regressed:wall_time", workload["gate_issues"])
        self.assertFalse(b5["performance_metrics"]["performance_success"])

    def test_b5_guidance_ablation_suite_aggregates_split_safe_rows(self) -> None:
        instance_a = generate_instance(5, seed=629001, index=1)
        instance_b = generate_instance(5, seed=629002, index=2)
        data_a = load_lunar_ice_data(instance_a)
        data_b = load_lunar_ice_data(instance_b)

        suite = run_b5_guidance_ablation_suite(
            (
                {
                    "data": data_a,
                    "guidance_hints": ({"candidate_id": "p2", "priority": 0.9},),
                    "pricing_candidates": ({"candidate_id": "p1"}, {"candidate_id": "p2"}),
                    "enabled_ordering_modes": ("pricing",),
                    "no_guidance_workload": {
                        "wall_time": 10.0,
                        "pricing_calls": 7,
                        "final_judge_calls": 2,
                        "generated_labels": 100,
                        "rmp_iterations": 4,
                        "node_count": 1,
                    },
                    "guidance_workload": {
                        "wall_time": 8.0,
                        "pricing_calls": 6,
                        "final_judge_calls": 2,
                        "generated_labels": 90,
                        "rmp_iterations": 4,
                        "node_count": 1,
                    },
                },
                {
                    "data": data_b,
                    "guidance_hints": (),
                },
            ),
            max_direct_tasks=5,
            max_rounds=8,
        )

        self.assertEqual(suite["schema_version"], "lunar_ice_bpc.b5_guidance_ablation_suite.v1")
        self.assertEqual(suite["row_count"], 2)
        self.assertEqual(suite["split_policy"]["main_split_keys"], ["instance", "scale", "seed_family"])
        self.assertFalse(suite["split_policy"]["random_row_split_is_main_claim"])
        self.assertTrue(suite["suite_do_no_harm_pass"])
        self.assertEqual(suite["suite_performance_success_count"], 1)
        self.assertEqual(suite["do_no_harm_pass_count"], 2)
        self.assertEqual(suite["do_no_harm_fail_count"], 0)
        self.assertEqual(suite["certificate_scope_diff_count"], 0)
        self.assertEqual(suite["additional_bpc_incomplete_count"], 0)
        self.assertEqual(suite["mode_counts"], {"ordering_opt_in": 1, "shadow_only": 1})
        self.assertEqual(suite["certificate_scope_counts"], {"BPC_TREE_OPTIMAL": 2})
        self.assertEqual(suite["scale_counts"], {str(data_a.scale): 2})
        self.assertEqual(suite["seed_family_counts"], {"629": 2})
        self.assertEqual(suite["performance_success_instance_ids"], [data_a.instance_id])
        self.assertEqual(suite["do_no_harm_fail_instance_ids"], [])
        self.assertTrue(all(row["do_no_harm_pass"] for row in suite["rows"]))
        self.assertTrue(all(row["certificate_scope"] == "BPC_TREE_OPTIMAL" for row in suite["rows"]))
        self.assertEqual(suite["rows"][0]["split_keys"]["instance"], data_a.instance_id)
        self.assertEqual(suite["rows"][1]["split_keys"]["instance"], data_b.instance_id)
        self.assertFalse(suite["rows"][0]["result"]["guidance_can_construct_certificate"])

    def test_b5_guidance_ablation_suite_counts_failed_debt_release(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)

        suite = run_b5_guidance_ablation_suite(
            (
                {
                    "data": data,
                    "guidance_hints": (
                        {
                            "candidate_id": "neg-001",
                            "priority": 0.9,
                            "finite_delay_budget": 1,
                            "diagnostic_only": True,
                        },
                    ),
                    "true_rc_candidates": (
                        {
                            "candidate_id": "neg-001",
                            "true_reduced_cost": -0.25,
                            "addability_accepted": True,
                        },
                    ),
                    "release_before_certificate": False,
                },
            ),
            max_direct_tasks=5,
            max_rounds=8,
        )

        self.assertFalse(suite["suite_do_no_harm_pass"])
        self.assertEqual(suite["do_no_harm_pass_count"], 0)
        self.assertEqual(suite["do_no_harm_fail_count"], 1)
        self.assertEqual(suite["certificate_scope_diff_count"], 1)
        self.assertEqual(suite["additional_bpc_incomplete_count"], 1)
        self.assertEqual(suite["mode_counts"], {"shadow_only": 1})
        self.assertEqual(suite["certificate_scope_counts"], {"FEASIBLE_INCUMBENT_ONLY": 1})
        self.assertEqual(suite["do_no_harm_fail_instance_ids"], [data.instance_id])
        self.assertEqual(suite["performance_success_instance_ids"], [])
        row = suite["rows"][0]
        self.assertEqual(row["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(row["certificate_scope_diff"], "BPC_TREE_OPTIMAL->FEASIBLE_INCUMBENT_ONLY")
        self.assertEqual(row["BPC_INCOMPLETE_count_diff"], 1)
        self.assertIn("proof_debt_not_released_before_certificate", row["do_no_harm_issues"])
        self.assertTrue(row["proof_debt_metrics"]["certificate_blocked_by_delayed_negative"])

    def test_b2_harvest_only_selects_columns_that_would_enter_master(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        duplicate = universe.columns[0]
        fresh = universe.columns[1]
        pool = ColumnPool()
        view = MasterColumnView()
        duplicate_bpc = BpcColumn(
            signature=column_signature_from_journey(duplicate),
            objective=duplicate.objective,
            payload=duplicate,
        )
        self.assertTrue(pool.add(duplicate_bpc).added)
        self.assertTrue(view.add_from_pool(duplicate_bpc, node_id="root", pool=pool))

        selected, payload = harvest_addable_negative_columns(
            ((-10.0, duplicate), (-5.0, fresh)),
            pool=pool,
            view=view,
            negative_eps=1.0e-6,
            max_selected=10,
        )

        self.assertEqual(selected, (fresh,))
        self.assertEqual(payload["harvest_candidate_negative_count"], 2)
        self.assertEqual(payload["harvest_addable_candidate_count"], 1)
        self.assertEqual(payload["harvest_source_phase"], "addability_harvest")
        self.assertEqual(payload["harvest_selected_count"], 1)
        self.assertEqual(payload["harvest_selected_new_task_set_count"], 1)
        self.assertEqual(payload["harvest_selected_replacement_task_set_count"], 0)
        self.assertGreaterEqual(payload["harvest_rejected_duplicate_count"], 1)
        self.assertGreaterEqual(payload["harvest_rejected_not_addable_count"], 1)
        self.assertAlmostEqual(payload["harvest_best_true_rc"], -5.0, delta=1.0e-9)
        self.assertAlmostEqual(payload["harvest_worst_selected_true_rc"], -5.0, delta=1.0e-9)
        self.assertGreaterEqual(payload["harvest_duplicate_signature_count"], 1)
        self.assertTrue(all(row["would_enter_master"] for row in payload["reports"] if row["task_set"] == sorted(fresh.task_set)))

    def test_b4_1_harvest_prefers_new_task_sets_and_filters_duplicate_candidates(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        first = universe.columns[0]
        second = next(column for column in universe.columns if frozenset(column.task_set) != frozenset(first.task_set))
        third = next(
            column
            for column in universe.columns
            if frozenset(column.task_set) not in {frozenset(first.task_set), frozenset(second.task_set)}
        )
        pool = ColumnPool()
        view = MasterColumnView()

        selected, payload = harvest_addable_negative_columns(
            ((-10.0, first), (-9.0, first), (-1.0, second)),
            pool=pool,
            view=view,
            negative_eps=1.0e-6,
            max_selected=2,
        )

        self.assertEqual(selected, (first, second))
        self.assertEqual(payload["harvest_priority"], "prefer_new_task_set_then_true_rc_then_replacements")
        self.assertEqual(payload["harvest_selected_new_task_set_count"], 2)
        self.assertEqual(payload["harvest_selected_replacement_task_set_count"], 0)
        self.assertGreaterEqual(payload["harvest_rejected_duplicate_count"], 1)
        duplicate_reports = [
            row
            for row in payload["reports"]
            if row["task_set"] == sorted(first.task_set)
            and row["reject_reason"] == "duplicate_candidate_signature"
        ]
        self.assertEqual(len(duplicate_reports), 1)

        selected_new_first, payload_new_first = harvest_addable_negative_columns(
            ((-10.0, first), (-1.0, third)),
            pool=ColumnPool(),
            view=MasterColumnView(),
            negative_eps=1.0e-6,
            max_selected=1,
            active_task_sets={frozenset(first.task_set)},
        )

        self.assertEqual(selected_new_first, (third,))
        self.assertEqual(payload_new_first["harvest_selected_new_task_set_count"], 1)
        self.assertEqual(payload_new_first["harvest_selected_replacement_task_set_count"], 0)

    def test_b4_1_harvest_totals_preserve_reject_and_diversity_telemetry(self) -> None:
        totals = pricing_tail_solver_module._empty_harvest_totals()
        pricing_tail_solver_module._accumulate_harvest_totals(
            totals,
            {
                "candidate_negative_count": 3,
                "addable_negative_count": 2,
                "selected_count": 2,
                "selected_would_enter_master_count": 2,
                "harvest_candidate_negative_count": 3,
                "harvest_addable_candidate_count": 2,
                "harvest_selected_count": 2,
                "harvest_selected_new_task_set_count": 1,
                "harvest_selected_replacement_task_set_count": 1,
                "harvest_rejected_duplicate_count": 4,
                "harvest_rejected_not_addable_count": 1,
                "harvest_best_true_rc": -0.8,
                "harvest_worst_selected_true_rc": -0.2,
                "harvest_avg_pairwise_jaccard": 0.25,
            },
        )
        pricing_tail_solver_module._accumulate_harvest_totals(
            totals,
            {
                "candidate_negative_count": 2,
                "addable_negative_count": 1,
                "selected_count": 1,
                "selected_would_enter_master_count": 1,
                "harvest_candidate_negative_count": 2,
                "harvest_addable_candidate_count": 1,
                "harvest_selected_count": 1,
                "harvest_selected_new_task_set_count": 1,
                "harvest_selected_replacement_task_set_count": 0,
                "harvest_rejected_duplicate_count": 1,
                "harvest_rejected_not_addable_count": 1,
                "harvest_best_true_rc": -1.2,
                "harvest_worst_selected_true_rc": -0.4,
                "harvest_avg_pairwise_jaccard": 0.75,
            },
        )

        self.assertEqual(totals["harvest_candidate_negative_count"], 5)
        self.assertEqual(totals["harvest_selected_count"], 3)
        self.assertEqual(totals["harvest_selected_new_task_set_count"], 2)
        self.assertEqual(totals["harvest_selected_replacement_task_set_count"], 1)
        self.assertEqual(totals["harvest_rejected_duplicate_count"], 5)
        self.assertEqual(totals["harvest_rejected_not_addable_count"], 2)
        self.assertAlmostEqual(totals["harvest_best_true_rc"], -1.2, delta=1.0e-9)
        self.assertAlmostEqual(totals["harvest_worst_selected_true_rc"], -0.2, delta=1.0e-9)
        self.assertAlmostEqual(totals["harvest_avg_pairwise_jaccard"], (0.25 * 2.0 + 0.75) / 3.0, delta=1.0e-9)
        self.assertFalse(any(str(key).startswith("_") for key in totals))

    def test_b4_1_final_judge_harvest_addability_filters_current_master_duplicates(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        duplicate = universe.columns[0]
        fresh = universe.columns[1]
        pool = ColumnPool()
        view = MasterColumnView()
        duplicate_bpc = BpcColumn(
            signature=column_signature_from_journey(duplicate),
            objective=duplicate.objective,
            payload=duplicate,
        )
        pool.add(duplicate_bpc)
        view.add_from_pool(duplicate_bpc, node_id="root", pool=pool)

        harvest_duals = JourneyDuals(cover={task_id: 1000.0 for task_id in data.task_ids}, fleet_limit=0.0)
        pricing_rc_by_signature = {
            column_signature_from_journey(column): manual_journey_reduced_cost(column, harvest_duals)
            for column in (duplicate, fresh)
        }
        payload = final_judge_module._compact_negative_harvest_payload(
            [duplicate, fresh],
            harvest_duals,
            CutContext(),
            negative_eps=1.0e-6,
            candidate_negative_count=2,
            max_selected=5,
            pricing_rc_by_signature=pricing_rc_by_signature,
            column_pool=pool,
            master_view=view,
            node_id="root",
            active_task_sets={frozenset(duplicate.task_set)},
            branch_context=BranchContext(),
        )
        selected = payload.pop("_selected_columns")

        self.assertEqual(selected, (fresh,))
        self.assertTrue(payload["harvest_addability_audit_available"])
        self.assertTrue(payload["harvest_selected_all_addability_audited"])
        self.assertTrue(payload["harvest_selected_all_would_enter_master"])
        self.assertTrue(payload["harvest_manual_rc_audit_pass"])
        self.assertTrue(payload["harvest_pricing_rc_audit_available"])
        self.assertTrue(payload["harvest_pricing_rc_audit_pass"])
        self.assertEqual(payload["harvest_pricing_rc_max_abs_diff"], 0.0)
        self.assertTrue(payload["harvest_branch_context_audit_pass"])
        self.assertTrue(payload["harvest_cut_context_audit_pass"])
        self.assertTrue(payload["harvest_addability_audit_pass"])
        self.assertEqual(payload["harvest_source_phase"], "compact_final_judge_negative_feasibility_batch")
        self.assertEqual(payload["harvest_target"], 5)
        self.assertEqual(payload["harvest_selected_new_task_set_count"], 1)
        self.assertEqual(payload["harvest_selected_replacement_task_set_count"], 0)
        self.assertEqual(payload["harvest_rejected_not_addable_count"], 1)
        self.assertEqual(payload["harvest_addability_reject_reasons"], {"duplicate_in_current_master": 1})

    def test_b4_1_final_judge_harvest_prefers_new_task_set_before_replacement(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        replacement = universe.columns[0]
        fresh = next(column for column in universe.columns if frozenset(column.task_set) != frozenset(replacement.task_set))
        harvest_duals = JourneyDuals(cover={task_id: 1000.0 for task_id in data.task_ids}, fleet_limit=0.0)
        pricing_rc_by_signature = {
            column_signature_from_journey(column): manual_journey_reduced_cost(column, harvest_duals)
            for column in (replacement, fresh)
        }

        payload = final_judge_module._compact_negative_harvest_payload(
            [replacement, fresh],
            harvest_duals,
            CutContext(),
            negative_eps=1.0e-6,
            candidate_negative_count=2,
            max_selected=2,
            pricing_rc_by_signature=pricing_rc_by_signature,
            column_pool=ColumnPool(),
            master_view=MasterColumnView(),
            node_id="root",
            active_task_sets={frozenset(replacement.task_set)},
            branch_context=BranchContext(),
        )
        selected = payload.pop("_selected_columns")

        self.assertEqual(selected, (fresh, replacement))
        self.assertEqual(payload["harvest_priority"], "prefer_new_task_set_then_true_rc_then_replacements")
        self.assertEqual(payload["harvest_selected_new_task_set_count"], 1)
        self.assertEqual(payload["harvest_selected_replacement_task_set_count"], 1)
        self.assertTrue(payload["harvest_addability_audit_pass"])
        replacement_report = next(
            row for row in payload["harvest_reports"] if row["task_set"] == sorted(replacement.task_set)
        )
        self.assertTrue(replacement_report["would_enter_master"])
        self.assertFalse(replacement_report["would_change_active_support"])

    def test_b2_duplicate_only_audit_blocks_silent_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        column = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns[0]
        pool = ColumnPool()
        view = MasterColumnView()
        signature = column_signature_from_journey(column)
        bpc_column = BpcColumn(signature=signature, objective=column.objective, payload=column)
        pool.add(bpc_column)
        view.add_from_pool(bpc_column, node_id="root", pool=pool)
        duals = JourneyDuals(cover={task_id: 1000.0 for task_id in column.task_set}, fleet_limit=0.0)
        audit = build_duplicate_only_audit(
            ((-1.0, column),),
            pool=pool,
            view=view,
            duals=duals,
            negative_eps=1.0e-6,
        )

        self.assertEqual(audit["status"], "DUPLICATE_ONLY_AUDITED")
        self.assertEqual(audit["duplicate_only_count"], 1)
        self.assertGreater(audit["categories"]["DUPLICATE_IN_CURRENT_MASTER_NEGATIVE_RC"], 0)
        self.assertFalse(audit["manual_reduced_cost_audit_pass"])
        self.assertFalse(audit["can_close_node"])

    def test_b2_hidden_negative_audit_records_worker_miss_without_certificate_effect(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        column = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns[0]
        audit = build_hidden_negative_audit(
            worker_payload={
                "pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
                "worker_kind": "test_worker",
                "worker_candidate_budget": 3,
                "worker_generated_count": 3,
            },
            final_judge_payload={"pricing_state": "FOUND_NEGATIVE", "candidate_round_count": 7},
            negative_candidates=((-2.0, column),),
            node_id="root",
            cg_iter=4,
        )

        self.assertEqual(audit["status"], "HIDDEN_NEGATIVE_FOUND")
        self.assertEqual(audit["hidden_negative_count"], 1)
        self.assertEqual(audit["miss_reason_counts"], {"worker_not_generated": 1})
        self.assertEqual(audit["hidden_negative_miss_reason_counts"], {"worker_not_generated": 1})
        self.assertEqual(audit["hidden_negative_top_miss_reason"], "worker_not_generated")
        self.assertFalse(audit["mutates_solver"])
        self.assertFalse(audit["changes_certificate_semantics"])
        self.assertEqual(audit["rows"][0]["worker_kind"], "test_worker")
        self.assertEqual(audit["rows"][0]["hidden_negative_task_set_size"], len(column.task_set))
        self.assertEqual(audit["rows"][0]["hidden_negative_source_phase"], "final_judge")
        self.assertEqual(audit["rows"][0]["miss_reason"], "worker_not_generated")
        self.assertEqual(audit["rows"][0]["replacement_or_new_task_set"], "new_task_set")
        self.assertFalse(audit["rows"][0]["worker_seen_same_task_set"])

    def test_b4_1_hidden_negative_audit_records_enum_reasons(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        column = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns[0]
        task_set = tuple(sorted(column.task_set))
        audit = build_hidden_negative_audit(
            worker_payload={
                "pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
                "worker_kind": "test_worker",
                "miss_reason": "pruned_by_dominance",
                "worker_seen_task_sets": (task_set,),
                "best_reduced_cost": 0.25,
            },
            final_judge_payload={"pricing_state": "FOUND_NEGATIVE", "compact_pricing_phase": "negative_feasibility_batch"},
            negative_candidates=((-2.0, column),),
        )

        row = audit["rows"][0]
        self.assertEqual(audit["miss_reason_counts"], {"pruned_by_dominance": 1})
        self.assertEqual(audit["top_miss_reason"], "pruned_by_dominance")
        self.assertEqual(row["miss_reason"], "pruned_by_dominance")
        self.assertTrue(row["worker_seen_same_task_set"])
        self.assertEqual(row["replacement_or_new_task_set"], "replacement")
        self.assertEqual(row["worker_best_rc_before_judge"], 0.25)

    def test_b4_1_tail_dual_stabilization_is_worker_only(self) -> None:
        current = JourneyDuals(cover={"t1": 10.0, "t2": 2.0}, fleet_limit=1.5, cuts={"c1": -0.25})
        history = (
            JourneyDuals(cover={"t1": 1.0, "t2": 3.0}, fleet_limit=0.0),
            JourneyDuals(cover={"t1": 3.0, "t2": 5.0}, fleet_limit=0.0),
        )
        center = build_tail_dual_center(history, window=2)
        self.assertEqual(center, {"t1": 2.0, "t2": 4.0})

        disabled, disabled_payload = build_worker_duals_with_tail_center(
            current,
            tail_dual_center=center,
            enabled=False,
        )
        self.assertIs(disabled, current)
        self.assertFalse(disabled_payload["tail_dual_stabilization_enabled"])
        self.assertFalse(disabled_payload["can_certify_no_negative"])
        self.assertEqual(disabled_payload["tail_dual_stabilization_window"], 5)
        self.assertEqual(disabled_payload["tail_dual_current_task_count"], 2)

        worker_duals, payload = build_worker_duals_with_tail_center(
            current,
            tail_dual_center=center,
            enabled=True,
            alpha=0.7,
            window=2,
        )
        self.assertAlmostEqual(worker_duals.cover["t1"], 7.6, delta=1.0e-9)
        self.assertAlmostEqual(worker_duals.cover["t2"], 2.6, delta=1.0e-9)
        self.assertEqual(worker_duals.fleet_limit, current.fleet_limit)
        self.assertEqual(worker_duals.cuts, current.cuts)
        self.assertEqual(payload["worker_dual_source"], "tail_dual_stabilized_worker_dual")
        self.assertEqual(payload["official_dual_source"], "current_true_rmp_dual")
        self.assertEqual(payload["tail_dual_stabilization_window"], 2)
        self.assertEqual(payload["tail_dual_center_task_count"], 2)
        self.assertEqual(payload["tail_dual_current_task_count"], 2)
        self.assertTrue(payload["worker_dual_only"])
        self.assertTrue(payload["requires_true_dual_rc_recompute"])
        self.assertTrue(payload["true_dual_rc_recomputed"])
        self.assertFalse(payload["tail_dual_no_column_can_certify"])
        self.assertFalse(payload["official_bound_safe"])
        self.assertFalse(payload["can_certify_no_negative"])

    def test_b2_completion_bound_policy_pruning_is_opt_in_and_fail_closed_with_context(self) -> None:
        default_policy = build_completion_bound_tail_policy()
        self.assertTrue(default_policy["ordering_enabled"])
        self.assertTrue(default_policy["audit_enabled"])
        self.assertFalse(default_policy["pruning_enabled"])
        opt_in = build_completion_bound_tail_policy(pruning_opt_in=True)
        self.assertTrue(opt_in["pruning_enabled"])
        branch_context = build_completion_bound_tail_policy(pruning_opt_in=True, branch_context_active=True)
        cut_context = build_completion_bound_tail_policy(pruning_opt_in=True, cut_context_active=True)
        self.assertFalse(branch_context["pruning_enabled"])
        self.assertFalse(cut_context["pruning_enabled"])

    def test_b0_direct_baseline_is_fixed_graph_oracle_not_bpc_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        with tempfile.TemporaryDirectory() as tmp:
            instance_path = Path(tmp) / "instance.json"
            solution_path = Path(tmp) / "solution.json"
            write_json(instance_path, instance)
            result = solve_reference(
                instance_path,
                solution_path,
                restricted_rmp_enabled=False,
                direct_pricing_enabled=False,
            )
        self.assertEqual(result["status"], "DIRECT_DP_BASELINE_OPTIMAL")
        self.assertEqual(result["algorithm_status"], "DIRECT_DP_BASELINE_OPTIMAL")
        self.assertEqual(result["exact_status"], "EXACT_BASELINE_OPTIMAL")
        self.assertEqual(result["exact_claim_scope"], "fixed_logical_graph_exhaustive_direct_dp")
        self.assertEqual(result["certificate_scope"], "DIRECT_DP_FIXED_GRAPH_OPTIMAL")
        self.assertEqual(result["path_option_dominance_policy"], PATH_OPTION_POLICY_ID)
        self.assertGreaterEqual(result["path_option_dominance_filtered_count"], 0)
        self.assertEqual(result["infeasibility_scope_if_any"], "")
        self.assertEqual(result["bpc_certificate_status"], "NOT_PORTED_TRUE_DUAL_BPC")
        self.assertFalse(result["uses_true_dual_bpc_certificate"])
        self.assertEqual(result["pricing_certificate"]["status"], "NOT_PORTED_TRUE_DUAL_BPC")
        self.assertFalse(result["pricing_certificate"]["can_certify_no_negative"])
        self.assertEqual(result["pricing_certificate"]["selected_certificate_source"], "diagnostic_fallback")
        self.assertIn("true_dual_bpc_pricing_not_used", result["pricing_certificate"]["issues"])
        self.assertEqual(result["pricing_certificate"]["frontier_ledger"]["status"], "DIAGNOSTIC_FRONTIER_ONLY")
        self.assertFalse(result["pricing_certificate"]["frontier_ledger"]["lower_bound_official"])
        self.assertEqual(result["node_bound_certificate"]["status"], "NODE_BOUND_FAIL_CLOSED")
        self.assertFalse(result["node_bound_certificate"]["can_fathom_by_bound"])
        self.assertFalse(result["node_bound_certificate"]["lower_bound_official"])
        self.assertIn("pricing_certificate_not_certified", result["node_bound_certificate"]["issues"])
        readiness = result["true_dual_certificate_readiness"]
        self.assertEqual(readiness["status"], "BLOCKED_BY_RMP_STATUS")
        self.assertFalse(readiness["mutates_solver"])
        self.assertFalse(readiness["can_certify"])
        self.assertFalse(readiness["true_dual_pricing_used"])
        self.assertIn("restricted_or_node_rmp_not_optimal", readiness["missing_inputs"])
        self.assertIn("true_dual_pricing_proof_not_used", readiness["missing_inputs"])
        self.assertEqual(result["covered_task_count"], result["task_count"])
        self.assertEqual(result["incumbent_source"], "direct_dp_exact_baseline")
        self.assertEqual(result["objective"], result["direct_exact_objective"])
        self.assertLessEqual(result["lower_bound"], result["objective"])
        self.assertEqual(result["gap_type"], "analytic_relaxation_not_bpc_certificate")
        self.assertGreaterEqual(result["relaxation_gap"], 0.0)
        self.assertEqual(result["lower_bound_source"], "analytic_relaxation")
        self.assertEqual(result["lower_bound_scope"], "global_relaxation")
        self.assertEqual(result["bound_ledger"]["official_lower_bound"], result["lower_bound"])
        self.assertEqual(result["bound_ledger"]["official_lower_bound_source"], "analytic_relaxation")
        self.assertFalse(result["bound_ledger"]["diagnostic_bound_is_official"])
        self.assertTrue(
            any(
                record["name"] == "direct_fixed_graph_root_lp"
                and record["certificate_status"] == "FIXED_GRAPH_ROOT_DIAGNOSTIC"
                and record["official_lower_bound"] is False
                for record in result["bound_ledger"]["records"]
            )
        )
        self.assertEqual(result["best_diagnostic_bound_source"], "direct_fixed_graph_root_lp")
        self.assertEqual(result["analytic_lower_bound"]["exact_status"], "RELAXATION_LOWER_BOUND")
        self.assertLessEqual(result["objective"], result["canonical_objective"])
        self.assertFalse(result["solver_options"]["uses_true_dual_bpc_certificate"])
        self.assertEqual(result["direct_exact_baseline"]["status"], "DIRECT_DP_BASELINE_OPTIMAL")
        self.assertEqual(result["direct_exact_baseline"]["certificate_scope"], "DIRECT_DP_FIXED_GRAPH_OPTIMAL")
        self.assertEqual(result["direct_exact_baseline"]["path_option_dominance_policy"], PATH_OPTION_POLICY_ID)
        self.assertGreaterEqual(result["direct_exact_baseline"]["path_option_dominance_filtered_count"], 0)
        self.assertEqual(result["canonical_baseline"]["status"], "CANONICAL_DP_BASELINE_OPTIMAL")
        self.assertEqual(result["canonical_baseline"]["certificate_scope"], "FEASIBLE_INCUMBENT_ONLY")
        direct_root = result["direct_root_certificate"]
        self.assertIn(
            direct_root["status"],
            {
                "DIRECT_ROOT_FIXED_GRAPH_LP_AUDIT_DIAGNOSTIC",
                "DIRECT_ROOT_FIXED_GRAPH_INTEGER_MATCH_DIAGNOSTIC",
            },
        )
        self.assertIn(
            direct_root["exact_status"],
            {
                "FIXED_GRAPH_ROOT_LP_DIAGNOSTIC",
                "FIXED_GRAPH_ROOT_LP_INTEGRAL_DIAGNOSTIC",
            },
        )
        self.assertEqual(direct_root["certificate_scope"], "fixed_logical_graph_direct_root")
        self.assertFalse(direct_root["uses_true_dual_bpc_certificate"])
        self.assertEqual(direct_root["task_count"], 5)
        self.assertLessEqual(direct_root["lp_bound"], result["objective"] + 1.0e-6)
        self.assertGreaterEqual(direct_root["min_reduced_cost"], -1.0e-6)
        self.assertGreater(result["route_template_count"], 0)
        self.assertGreater(result["pareto_label_count"], 0)
        self.assertEqual(result["restricted_rmp"], {"enabled": False})
        self.assertEqual(result["true_dual_pricing_tail"]["status"], "TRUE_DUAL_PRICING_TAIL_NOT_PORTED")
        self.assertEqual(result["true_dual_pricing_tail"]["source"], "diagnostic_fixed_graph_root_lp")

    def test_large_reference_fallback_reports_relaxation_gap(self) -> None:
        instance = generate_instance(20, seed=829001, index=1)
        with tempfile.TemporaryDirectory() as tmp:
            instance_path = Path(tmp) / "instance.json"
            solution_path = Path(tmp) / "solution.json"
            write_json(instance_path, instance)
            result = solve_reference(instance_path, solution_path)

        self.assertEqual(result["status"], "FEASIBLE_REFERENCE")
        self.assertEqual(result["algorithm_status"], "SKIPPED_TOO_LARGE_FOR_ENUM_BASELINE")
        self.assertEqual(result["exact_status"], "NOT_SOLVED")
        self.assertEqual(result["exact_claim_scope"], "none")
        self.assertEqual(result["certificate_scope"], "FEASIBLE_INCUMBENT_ONLY")
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
        self.assertEqual(direct.certificate_scope, "DIRECT_DP_FIXED_GRAPH_OPTIMAL")
        self.assertEqual(direct.path_option_dominance_policy, PATH_OPTION_POLICY_ID)
        self.assertGreaterEqual(direct.path_option_dominance_filtered_count, 0)
        self.assertEqual(canonical.status, "CANONICAL_DP_BASELINE_OPTIMAL")
        self.assertEqual(canonical.certificate_scope, "FEASIBLE_INCUMBENT_ONLY")
        self.assertLessEqual(direct.objective, canonical.objective + 1.0e-6)
        self.assertGreater(direct.generated_sortie_count, 0)
        self.assertGreater(direct.route_template_count, 0)

    def test_reference_solution_upper_bound_does_not_change_direct_dp_optimum(self) -> None:
        instance = generate_instance(10, seed=729001, index=1)
        with_reference = solve_direct_journey_baseline(load_lunar_ice_data(instance), max_exact_tasks=10)
        without_reference_payload = json.loads(json.dumps(instance))
        without_reference_payload.pop("reference_solution", None)
        without_reference = solve_direct_journey_baseline(
            load_lunar_ice_data(without_reference_payload),
            max_exact_tasks=10,
        )

        self.assertEqual(with_reference.status, "DIRECT_DP_BASELINE_OPTIMAL")
        self.assertEqual(without_reference.status, "DIRECT_DP_BASELINE_OPTIMAL")
        self.assertAlmostEqual(with_reference.objective, without_reference.objective, delta=1.0e-6)
        self.assertIsNotNone(with_reference.reference_solution_upper_bound)
        self.assertEqual(
            with_reference.reference_solution_upper_bound_source,
            "instance_reference_solution_best_path_repair",
        )
        self.assertIsNotNone(with_reference.direct_bound_pruning_root_bound)
        self.assertIsInstance(with_reference.direct_bound_pruning_active, bool)
        self.assertIsNone(without_reference.reference_solution_upper_bound)
        self.assertIsNone(without_reference.direct_bound_pruning_root_bound)
        self.assertFalse(without_reference.direct_bound_pruning_active)

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

    def test_partial_direct_pricing_keeps_multi_sortie_seed_task_sets(self) -> None:
        instance = generate_instance(10, seed=729001, index=1)
        data = load_lunar_ice_data(instance)
        seed = tuple(data.task_ids[:8])

        merged = journey_pricing_module._merge_candidate_sets(
            data,
            tuple(),
            (seed,),
            max_candidate_task_count=8,
        )

        self.assertGreater(len(seed), data.max_tasks_per_trip)
        self.assertIn(seed, merged)

    def test_incremental_direct_pricing_matches_template_pricing_on_seed_set(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 0.03 * (index + 1) for index, task_id in enumerate(data.task_ids)},
            fleet_limit=-0.02,
        )
        seed = (tuple(data.task_ids),)

        template_payload, _ = price_direct_journey_columns(
            data,
            duals,
            max_direct_tasks=5,
            seed_task_sets=seed,
            completion_bound_enabled=True,
        )
        incremental_payload, _ = price_direct_journey_columns_incremental(
            data,
            duals,
            max_direct_tasks=5,
            seed_task_sets=seed,
            wall_time_limit_sec=30.0,
            stop_at_first_negative=False,
        )

        self.assertAlmostEqual(
            incremental_payload["best_reduced_cost"],
            template_payload["best_reduced_cost"],
            delta=1.0e-6,
        )
        self.assertFalse(incremental_payload["can_certify_no_negative"])

    def test_incremental_direct_pricing_prioritizes_seed_task_sets(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)
        seed = (tuple(data.task_ids[-2:]),)

        payload, _ = price_direct_journey_columns_incremental(
            data,
            duals,
            max_direct_tasks=5,
            seed_task_sets=seed,
            max_candidate_sets=1,
            wall_time_limit_sec=30.0,
            stop_at_first_negative=False,
        )

        self.assertTrue(payload["seed_task_sets_first"])
        self.assertEqual(payload["candidate_sets"][0], list(seed[0]))

    def test_full_fixed_column_ip_equals_direct_dp_integer_oracle(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        direct_baseline = solve_direct_journey_baseline(data, max_exact_tasks=5)
        direct_universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        selection = select_journey_column_pool(
            data.task_ids,
            direct_universe.columns,
            fleet_size=data.fleet_size,
        )

        self.assertEqual(direct_baseline.status, "DIRECT_DP_BASELINE_OPTIMAL")
        self.assertEqual(selection.status, "COLUMN_POOL_EXACT_COVER")
        self.assertAlmostEqual(selection.objective, direct_baseline.objective, delta=1.0e-6)

    def test_highs_compact_oracle_matches_direct_dp_on_small_instance_when_available(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        direct_baseline = solve_direct_journey_baseline(data, max_exact_tasks=5)
        compact = solve_highs_compact_fixed_graph(
            data,
            time_limit_sec=30.0,
            threads=1,
            reference_solution=instance.get("reference_solution"),
        )

        self.assertEqual(direct_baseline.status, "DIRECT_DP_BASELINE_OPTIMAL")
        self.assertEqual(compact["algorithm_status"], "HIGHS_COMPACT_OPTIMAL")
        self.assertEqual(compact["certificate_scope"], "DIRECT_DP_FIXED_GRAPH_OPTIMAL")
        self.assertTrue(compact["has_feasible_incumbent"])
        self.assertTrue(compact["mip_start"]["enabled"])
        self.assertIn(compact["mip_start"]["status"], {"OK", "NO_FEASIBLE_SINGLETON_SCHEDULE"})
        self.assertIn("solver_info", compact)
        self.assertIn("mip_node_count", compact["solver_info"])
        self.assertAlmostEqual(compact["objective"], direct_baseline.objective, delta=1.0e-6)
        self.assertIn("not a BPC certificate", compact["note"])

    def test_highs_compact_single_journey_pricing_matches_exhaustive_reduced_cost(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)},
            fleet_limit=0.123,
        )
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        expected = min(manual_journey_reduced_cost(column, duals) for column in universe.columns)
        connectivity_variants = (
            {"flow_connectivity": False, "mtz_connectivity": False},
            {"flow_connectivity": True, "mtz_connectivity": False},
            {"flow_connectivity": False, "mtz_connectivity": True},
            {"flow_connectivity": False, "mtz_connectivity": True, "pair_adjacency_cuts": True},
        )
        for variant in connectivity_variants:
            compact = solve_highs_compact_single_journey_pricing(
                data,
                duals,
                time_limit_sec=30.0,
                threads=1,
                **variant,
            )

            self.assertEqual(compact["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
            self.assertEqual(compact["pricing_complete_by_compact_milp"], True)
            self.assertEqual(compact["flow_connectivity_enabled"], variant["flow_connectivity"])
            self.assertEqual(compact["mtz_connectivity_enabled"], variant["mtz_connectivity"])
            self.assertGreaterEqual(
                compact["fixed_active_sortie_redundant_constraint_skipped_count"],
                compact["sortie_slots_per_journey"],
            )
            self.assertEqual(compact["pair_adjacency_cuts_enabled"], bool(variant.get("pair_adjacency_cuts", False)))
            self.assertEqual(
                compact["mtz_endpoint_order_cuts_enabled"],
                bool(variant["mtz_connectivity"]),
            )
            self.assertAlmostEqual(compact["best_reduced_cost"], expected, delta=1.0e-6)
            self.assertAlmostEqual(compact["manual_best_reduced_cost"], expected, delta=1.0e-6)
            self.assertTrue(compact["pricing_rc_audit_pass"])

    def test_highs_compact_single_journey_pricing_accepts_journey_mip_start(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)},
            fleet_limit=0.123,
        )
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        warm_start = min(universe.columns, key=lambda column: manual_journey_reduced_cost(column, duals))
        expected = manual_journey_reduced_cost(warm_start, duals)

        cold = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
        )
        warm = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            mip_start_journey=warm_start,
        )
        warm_inactive_tail = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            mip_start_journey=warm_start,
            mip_start_inactive_tail_time=True,
        )
        warm_zero_fill = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            mip_start_journey=warm_start,
            mip_start_zero_fill_integers=True,
        )

        self.assertEqual(warm["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertTrue(warm["single_journey_mip_start_enabled"])
        self.assertEqual(warm["single_journey_mip_start_status"], "OK")
        self.assertEqual(warm["single_journey_mip_start_source"], "column_pool_journey")
        self.assertGreater(warm["single_journey_mip_start_entry_count"], 0)
        self.assertEqual(warm["single_journey_mip_start_inactive_tail_time_entry_count"], 0)
        self.assertEqual(warm["single_journey_mip_start_sortie_count"], len(warm_start.sorties))
        self.assertEqual(warm["single_journey_mip_start_task_count"], len(warm_start.task_set))
        self.assertAlmostEqual(warm["single_journey_mip_start_reduced_cost"], expected, delta=1.0e-6)
        self.assertAlmostEqual(warm["best_reduced_cost"], cold["best_reduced_cost"], delta=1.0e-6)
        self.assertTrue(warm["pricing_rc_audit_pass"])
        self.assertEqual(warm_inactive_tail["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertEqual(warm_inactive_tail["single_journey_mip_start_status"], "OK")
        self.assertGreater(
            warm_inactive_tail["single_journey_mip_start_inactive_tail_time_entry_count"],
            0,
        )
        self.assertAlmostEqual(
            warm_inactive_tail["best_reduced_cost"],
            cold["best_reduced_cost"],
            delta=1.0e-6,
        )
        self.assertTrue(warm_inactive_tail["pricing_rc_audit_pass"])
        self.assertEqual(warm_zero_fill["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertEqual(warm_zero_fill["single_journey_mip_start_status"], "OK")
        self.assertTrue(warm_zero_fill["single_journey_mip_start_zero_fill_integers"])
        self.assertGreater(
            warm_zero_fill["single_journey_mip_start_zero_fill_integer_entry_count"],
            warm["single_journey_mip_start_entry_count"],
        )
        self.assertGreater(
            warm_zero_fill["single_journey_mip_start_entry_count"],
            warm["single_journey_mip_start_entry_count"],
        )
        self.assertAlmostEqual(
            warm_zero_fill["best_reduced_cost"],
            cold["best_reduced_cost"],
            delta=1.0e-6,
        )
        self.assertTrue(warm_zero_fill["pricing_rc_audit_pass"])

    def test_highs_compact_slot_sequence_capacity_arc_pruning_preserves_rc(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)

        base = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            latest_service_start_slot_bound=True,
            time_window_arc_pruning=True,
            resource_arc_pruning=True,
            slot_task_time_pruning=True,
            max_sorties_per_journey=8,
        )
        pruned = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            latest_service_start_slot_bound=True,
            time_window_arc_pruning=True,
            resource_arc_pruning=True,
            slot_task_time_pruning=True,
            slot_sequence_capacity_arc_pruning=True,
            max_sorties_per_journey=8,
        )

        self.assertEqual(base["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertEqual(pruned["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertAlmostEqual(
            pruned["best_reduced_cost"],
            base["best_reduced_cost"],
            delta=1.0e-6,
        )
        self.assertTrue(pruned["pricing_rc_audit_pass"])
        self.assertTrue(pruned["slot_sequence_capacity_arc_pruning_enabled"])
        self.assertGreater(pruned["slot_sequence_capacity_mtz_disabled_slot_count"], 0)
        self.assertLess(pruned["variable_count"], base["variable_count"])
        self.assertLess(pruned["constraint_count"], base["constraint_count"])

    def test_compact_sortie_slot_bound_includes_recharge_lower_bound(self) -> None:
        instance_path = Path("data/instances/lunar_ice_sp50_030/instance_001_logical_graph.json")
        data = load_lunar_ice_data(json.loads(instance_path.read_text()))
        default_bound = gurobi_compact_module._safe_sortie_slot_bound(data)
        slot_bound = gurobi_compact_module._safe_sortie_slot_bound(
            data,
            recharge_aware_duration_bound=True,
        )
        travel_service_dock_lb = (
            float(slot_bound["min_return_duration_lower_bound"])
            + float(data.dock_overhead_min)
        )

        self.assertFalse(default_bound["recharge_aware_duration_bound_enabled"])
        self.assertEqual(default_bound["min_energy_recharge_duration_lower_bound"], 0.0)
        self.assertEqual(default_bound["slot_count"], 21)
        self.assertTrue(slot_bound["recharge_aware_duration_bound_enabled"])
        self.assertGreater(slot_bound["min_energy_recharge_duration_lower_bound"], 0.0)
        self.assertGreater(slot_bound["min_sortie_energy_lower_bound"], 0.0)
        self.assertAlmostEqual(
            slot_bound["min_duration_lower_bound"],
            travel_service_dock_lb + slot_bound["min_energy_recharge_duration_lower_bound"],
            delta=1.0e-9,
        )
        self.assertEqual(slot_bound["slot_count"], 18)
        self.assertEqual(slot_bound["latest_start_slot_count_bound"], 18)

    def test_compact_zero_capacity_slot_truncation_finds_prefix_cut(self) -> None:
        self.assertIsNone(gurobi_compact_module._first_zero_capacity_slot([3, 2, 1]))
        self.assertEqual(gurobi_compact_module._first_zero_capacity_slot([3, 0, 2]), 1)
        self.assertEqual(gurobi_compact_module._first_zero_capacity_slot([0, 2, 2]), 0)

    def test_highs_compact_single_journey_slot_sequence_capacity_live_bound(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        raw = json.loads(json.dumps(generate_instance(5, seed=629003, index=1)))
        probe_data = load_lunar_ice_data(raw)
        for task_id, task_payload in raw["tasks"].items():
            min_depot_travel = min(
                float(option.travel_time_min)
                for option in probe_data.arcs[("depot", str(task_id))].values()
            )
            task_payload["D"] = min_depot_travel + float(task_payload["sigma"]) + 0.1
        data = load_lunar_ice_data(raw)
        result = solve_highs_compact_single_journey_pricing(
            data,
            JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0),
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=1,
            slot_task_time_pruning=True,
            slot_sequence_capacity_live_bound=True,
        )

        self.assertTrue(result["slot_sequence_capacity_live_bound_enabled"])
        self.assertEqual(result["slot_sequence_capacity_live_bound_by_slot"], [1])
        self.assertEqual(result["slot_sequence_capacity_live_bound_tightened_slot_count"], 1)
        self.assertEqual(result["slot_task_sequence_capacity_by_slot"], [1])
        self.assertTrue(result["pricing_rc_audit_pass"])

    def test_highs_compact_single_journey_tight_service_start_bounds_preserve_rc(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)
        base = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=1,
            slot_task_time_pruning=True,
        )
        tightened = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=1,
            slot_task_time_pruning=True,
            tight_service_start_bounds=True,
        )

        self.assertEqual(base["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertEqual(tightened["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertTrue(tightened["tight_service_start_bounds_enabled"])
        self.assertGreater(tightened["tight_service_start_bound_count"], 0)
        self.assertLessEqual(tightened["tight_service_start_bound_max"], float(data.horizon))
        self.assertAlmostEqual(
            tightened["best_reduced_cost"],
            base["best_reduced_cost"],
            delta=1.0e-6,
        )
        self.assertTrue(tightened["pricing_rc_audit_pass"])

    def test_highs_compact_single_journey_tight_time_arc_big_m_preserves_rc(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)
        base = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=1,
            slot_task_time_pruning=True,
        )
        tightened = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=1,
            slot_task_time_pruning=True,
            tight_time_arc_big_m=True,
        )

        self.assertEqual(base["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertEqual(tightened["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertTrue(tightened["tight_time_arc_big_m_enabled"])
        self.assertGreater(tightened["tight_time_arc_big_m_depot_arc_count"], 0)
        self.assertGreater(tightened["tight_time_arc_big_m_max_reduction"], 0.0)
        self.assertLess(tightened["sortie_start_upper_bound"], float(data.horizon))
        self.assertAlmostEqual(
            tightened["best_reduced_cost"],
            base["best_reduced_cost"],
            delta=1.0e-6,
        )
        self.assertTrue(tightened["pricing_rc_audit_pass"])

    def test_highs_compact_tight_time_big_m_accepts_inactive_tail_mip_start(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        warm_start = next(column for column in universe.columns if len(column.sorties) == 1)

        result = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=2,
            slot_task_time_pruning=True,
            sortie_slot_position_bounds=True,
            tight_service_start_bounds=True,
            tight_time_arc_big_m=True,
            active_time_z_bounds=True,
            mip_start_journey=warm_start,
            mip_start_inactive_tail_time=True,
        )

        self.assertEqual(result["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertTrue(result["tight_time_arc_big_m_enabled"])
        self.assertTrue(result["active_time_z_bounds_enabled"])
        self.assertGreater(result["tight_time_arc_big_m_active_time_bound_count"], 0)
        self.assertTrue(result["single_journey_mip_start_enabled"])
        self.assertEqual(result["single_journey_mip_start_status"], "OK")
        self.assertGreater(result["single_journey_mip_start_entry_count"], 0)
        self.assertGreater(result["single_journey_mip_start_inactive_tail_time_entry_count"], 0)
        self.assertTrue(result["pricing_rc_audit_pass"])
        self.assertFalse(result["tight_conditional_sequence_big_m_enabled"])

    def test_highs_compact_legacy_sequence_chain_preserves_rc(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)
        legacy = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=2,
            slot_task_time_pruning=True,
        )
        active_time = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=2,
            slot_task_time_pruning=True,
            active_time_z_bounds=True,
        )

        self.assertEqual(legacy["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertTrue(legacy["tight_conditional_sequence_big_m_enabled"])
        self.assertGreater(legacy["tight_conditional_sequence_big_m_count"], 0)
        self.assertAlmostEqual(
            legacy["tight_conditional_sequence_big_m_max_reduction"],
            data.horizon,
            delta=1.0e-6,
        )
        self.assertEqual(active_time["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertTrue(active_time["active_time_z_bounds_enabled"])
        self.assertFalse(active_time["tight_conditional_sequence_big_m_enabled"])
        self.assertAlmostEqual(
            legacy["best_reduced_cost"],
            active_time["best_reduced_cost"],
            delta=1.0e-6,
        )
        self.assertTrue(legacy["pricing_rc_audit_pass"])
        self.assertTrue(active_time["pricing_rc_audit_pass"])

    def test_highs_compact_tight_conditional_sequence_big_m_preserves_rc(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)
        base = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=2,
            slot_task_time_pruning=True,
        )
        tightened = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=2,
            slot_task_time_pruning=True,
            tight_time_arc_big_m=True,
        )

        self.assertEqual(base["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertEqual(tightened["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertTrue(tightened["tight_time_arc_big_m_enabled"])
        self.assertTrue(tightened["tight_conditional_sequence_big_m_enabled"])
        self.assertGreater(tightened["tight_conditional_sequence_big_m_count"], 0)
        self.assertGreater(tightened["tight_conditional_sequence_big_m_max_reduction"], 0.0)
        self.assertAlmostEqual(
            tightened["best_reduced_cost"],
            base["best_reduced_cost"],
            delta=1.0e-6,
        )
        self.assertTrue(tightened["pricing_rc_audit_pass"])

    def test_highs_compact_slot_service_start_y_lb_preserves_rc(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)
        base = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=2,
            slot_task_time_pruning=True,
            sortie_slot_position_bounds=True,
        )
        tightened = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=2,
            slot_task_time_pruning=True,
            sortie_slot_position_bounds=True,
            slot_service_start_y_lower_bound=True,
        )

        self.assertEqual(base["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertEqual(tightened["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertTrue(tightened["slot_service_start_y_lower_bound_enabled"])
        self.assertGreater(tightened["slot_service_start_y_lower_bound_count"], 0)
        self.assertGreater(tightened["slot_service_start_y_lower_bound_max_lift"], 0.0)
        self.assertAlmostEqual(
            tightened["best_reduced_cost"],
            base["best_reduced_cost"],
            delta=1.0e-6,
        )
        self.assertTrue(tightened["pricing_rc_audit_pass"])

    def test_highs_compact_single_journey_pricing_required_task_set_region(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)},
            fleet_limit=0.123,
        )
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        target_column = next(column for column in universe.columns if len(column.task_set) >= 2)
        target_task_set = tuple(sorted(target_column.task_set))
        expected = min(
            manual_journey_reduced_cost(column, duals)
            for column in universe.columns
            if tuple(sorted(column.task_set)) == target_task_set
        )
        unrestricted = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
        )

        region = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            required_task_set=target_task_set,
            mip_start_journey=target_column,
        )

        self.assertEqual(region["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertEqual(region["exact_status"], "REQUIRED_TASK_SET_PRICING_OPTIMAL")
        self.assertTrue(region["required_task_set_enabled"])
        self.assertEqual(region["required_task_set"], list(target_task_set))
        self.assertEqual(region["required_task_set_count"], len(target_task_set))
        self.assertTrue(region["required_task_set_model_reduction_enabled"])
        self.assertEqual(region["pricing_model_task_count"], len(target_task_set))
        self.assertEqual(
            region["required_task_set_model_task_reduction_count"],
            len(data.task_ids) - len(target_task_set),
        )
        self.assertLess(region["variable_count"], unrestricted["variable_count"])
        self.assertLess(region["constraint_count"], unrestricted["constraint_count"])
        self.assertTrue(region["pricing_complete_for_required_task_set"])
        self.assertFalse(region["pricing_complete_for_all_task_subsets"])
        self.assertFalse(region["can_certify_no_negative"])
        self.assertFalse(region["required_task_set_can_certify_full_space"])
        self.assertAlmostEqual(region["best_reduced_cost"], expected, delta=1.0e-6)
        self.assertTrue(region["pricing_rc_audit_pass"])
        self.assertTrue(region["single_journey_mip_start_enabled"])
        self.assertEqual(region["single_journey_mip_start_status"], "OK")

        mismatch = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            required_task_set=target_task_set,
            mip_start_journey=next(column for column in universe.columns if tuple(sorted(column.task_set)) != target_task_set),
        )
        self.assertEqual(mismatch["single_journey_mip_start_status"], "MISMATCH_REQUIRED_TASK_SET")
        self.assertEqual(mismatch["exact_status"], "REQUIRED_TASK_SET_PRICING_OPTIMAL")

        tight_raw = json.loads(json.dumps(generate_instance(5, seed=629003, index=1)))
        tight_probe_data = load_lunar_ice_data(tight_raw)
        for task_id, task_payload in tight_raw["tasks"].items():
            min_depot_travel = min(
                float(option.travel_time_min)
                for option in tight_probe_data.arcs[("depot", str(task_id))].values()
            )
            task_payload["D"] = min_depot_travel + float(task_payload["sigma"]) + 0.1
        tight_data = load_lunar_ice_data(tight_raw)
        tight_task_set = tuple(sorted(list(tight_data.task_ids)[:2]))
        task_set_infeasible = solve_highs_compact_single_journey_pricing(
            tight_data,
            JourneyDuals(cover={task_id: 0.0 for task_id in tight_data.task_ids}, fleet_limit=0.0),
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=1,
            required_task_set=tight_task_set,
            slot_task_time_pruning=True,
        )
        self.assertEqual(
            task_set_infeasible["status"],
            "COMPACT_HIGHS_PRICING_REQUIRED_TASK_SET_INFEASIBLE",
        )
        self.assertEqual(
            task_set_infeasible["exact_status"],
            "REQUIRED_TASK_SET_PRICING_INFEASIBLE",
        )
        self.assertTrue(task_set_infeasible["pricing_complete_for_required_task_set"])
        self.assertTrue(task_set_infeasible["required_task_set_region_can_certify_no_negative"])
        self.assertFalse(task_set_infeasible["can_certify_no_negative"])
        self.assertTrue(task_set_infeasible["required_task_set_infeasible_by_slot_sequence_capacity"])
        self.assertEqual(task_set_infeasible["variable_count"], 0)
        self.assertEqual(task_set_infeasible["constraint_count"], 0)

    def test_highs_compact_single_journey_pricing_required_task_count_region(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)},
            fleet_limit=0.123,
        )
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        target_task_count = 2
        target_column = next(column for column in universe.columns if len(column.task_set) == target_task_count)
        mismatch_column = next(column for column in universe.columns if len(column.task_set) != target_task_count)
        expected = min(
            manual_journey_reduced_cost(column, duals)
            for column in universe.columns
            if len(column.task_set) == target_task_count
        )
        unrestricted = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
        )

        region = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            required_task_count=target_task_count,
            mip_start_journey=target_column,
        )

        self.assertEqual(region["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertEqual(region["exact_status"], "REQUIRED_TASK_COUNT_PRICING_OPTIMAL")
        self.assertTrue(region["required_task_count_enabled"])
        self.assertEqual(region["required_task_count"], target_task_count)
        self.assertTrue(region["pricing_complete_for_required_task_count"])
        self.assertFalse(region["pricing_complete_for_all_task_subsets"])
        self.assertFalse(region["can_certify_no_negative"])
        self.assertFalse(region["required_task_count_can_certify_full_space"])
        expected_min_active = (
            target_task_count + int(data.max_tasks_per_trip) - 1
        ) // int(data.max_tasks_per_trip)
        self.assertEqual(region["required_task_count_min_active_sorties"], expected_min_active)
        self.assertEqual(region["required_task_count_active_sortie_lb_count"], expected_min_active)
        self.assertGreaterEqual(region["required_task_count_feasible_task_count"], target_task_count)
        self.assertGreaterEqual(
            region["required_task_count_slot_capacity_task_upper_bound"],
            target_task_count,
        )
        self.assertGreaterEqual(
            region["required_task_count_slot_sequence_capacity_upper_bound"],
            target_task_count,
        )
        self.assertGreaterEqual(
            region["required_task_count_slot_matching_capacity_upper_bound"],
            target_task_count,
        )
        self.assertFalse(region["required_task_count_infeasible_by_feasible_task_count"])
        self.assertFalse(region["required_task_count_infeasible_by_slot_capacity"])
        self.assertFalse(region["required_task_count_infeasible_by_slot_sequence_capacity"])
        self.assertFalse(region["required_task_count_infeasible_by_slot_matching"])
        self.assertEqual(region["sortie_slots_per_journey"], target_task_count)
        self.assertLess(region["variable_count"], unrestricted["variable_count"])
        self.assertLess(region["constraint_count"], unrestricted["constraint_count"])
        self.assertAlmostEqual(region["best_reduced_cost"], expected, delta=1.0e-6)
        self.assertTrue(region["required_task_count_region_can_certify_no_negative"])
        self.assertTrue(region["pricing_rc_audit_pass"])
        self.assertEqual(region["single_journey_mip_start_status"], "OK")

        mismatch = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            required_task_count=target_task_count,
            mip_start_journey=mismatch_column,
        )
        self.assertEqual(mismatch["single_journey_mip_start_status"], "MISMATCH_REQUIRED_TASK_COUNT")
        self.assertEqual(mismatch["exact_status"], "REQUIRED_TASK_COUNT_PRICING_OPTIMAL")

        target_active_sorties = len(target_column.sorties)
        active_expected = min(
            manual_journey_reduced_cost(column, duals)
            for column in universe.columns
            if len(column.task_set) == target_task_count
            and len(column.sorties) == target_active_sorties
        )
        active_region = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            required_task_count=target_task_count,
            required_active_sortie_count=target_active_sorties,
            mip_start_journey=target_column,
        )
        self.assertEqual(active_region["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertEqual(active_region["exact_status"], "REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_OPTIMAL")
        self.assertTrue(active_region["required_active_sortie_count_enabled"])
        self.assertEqual(active_region["required_active_sortie_count"], target_active_sorties)
        self.assertEqual(active_region["sortie_slots_per_journey"], target_active_sorties)
        self.assertTrue(active_region["required_active_sortie_count_slots_fixed"])
        self.assertEqual(
            active_region["required_active_sortie_count_fixed_slot_count"],
            target_active_sorties,
        )
        self.assertTrue(active_region["pricing_complete_for_required_active_sortie_count"])
        self.assertTrue(active_region["required_active_sortie_count_region_can_certify_no_negative"])
        self.assertFalse(active_region["required_active_sortie_count_can_certify_full_space"])
        self.assertLessEqual(active_region["variable_count"], region["variable_count"])
        self.assertLessEqual(active_region["constraint_count"], region["constraint_count"])
        self.assertIn(
            target_active_sorties,
            active_region["required_active_sortie_count_expected_counts"],
        )
        self.assertAlmostEqual(active_region["best_reduced_cost"], active_expected, delta=1.0e-6)
        self.assertEqual(active_region["single_journey_mip_start_status"], "OK")

        split_column = next(
            column
            for column in universe.columns
            if len(column.task_set) == target_task_count and len(column.sorties) == target_task_count
        )
        unpruned_split_active_region = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            required_task_count=target_task_count,
            required_active_sortie_count=target_task_count,
            single_task_per_active_sortie_arc_pruning=False,
            mip_start_journey=split_column,
        )
        split_active_region = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            required_task_count=target_task_count,
            required_active_sortie_count=target_task_count,
            mip_start_journey=split_column,
        )
        self.assertEqual(split_active_region["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertEqual(
            split_active_region["exact_status"],
            "REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_OPTIMAL",
        )
        self.assertEqual(
            unpruned_split_active_region["exact_status"],
            "REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_OPTIMAL",
        )
        self.assertTrue(
            split_active_region["single_task_per_active_sortie_arc_pruning_enabled"]
        )
        self.assertFalse(
            unpruned_split_active_region["single_task_per_active_sortie_arc_pruning_enabled"]
        )
        self.assertTrue(unpruned_split_active_region["mtz_connectivity_effective"])
        self.assertFalse(unpruned_split_active_region["single_task_per_active_sortie_mtz_disabled"])
        self.assertGreater(
            split_active_region["single_task_per_active_sortie_arc_pruned_option_count"],
            0,
        )
        self.assertFalse(split_active_region["mtz_connectivity_effective"])
        self.assertTrue(split_active_region["single_task_per_active_sortie_mtz_disabled"])
        self.assertLess(split_active_region["variable_count"], unpruned_split_active_region["variable_count"])
        self.assertLess(split_active_region["constraint_count"], unpruned_split_active_region["constraint_count"])
        self.assertAlmostEqual(
            split_active_region["best_reduced_cost"],
            unpruned_split_active_region["best_reduced_cost"],
            delta=1.0e-6,
        )
        self.assertTrue(split_active_region["pricing_rc_audit_pass"])

        active_infeasible = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            required_task_count=target_task_count,
            required_active_sortie_count=target_task_count + 1,
        )
        self.assertEqual(
            active_infeasible["status"],
            "COMPACT_HIGHS_PRICING_REQUIRED_ACTIVE_SORTIE_COUNT_INFEASIBLE",
        )
        self.assertEqual(
            active_infeasible["exact_status"],
            "REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE",
        )
        self.assertTrue(active_infeasible["pricing_complete_for_required_active_sortie_count"])
        self.assertTrue(active_infeasible["required_active_sortie_count_region_can_certify_no_negative"])
        self.assertTrue(active_infeasible["required_active_sortie_count_infeasible"])
        self.assertEqual(active_infeasible["variable_count"], 0)
        self.assertEqual(active_infeasible["constraint_count"], 0)

        one_task_per_sortie_raw = json.loads(json.dumps(generate_instance(5, seed=629002, index=1)))
        one_task_per_sortie_raw["vehicle"]["max_tasks_per_trip"] = 1
        one_task_per_sortie_data = load_lunar_ice_data(one_task_per_sortie_raw)
        active_capacity_min_infeasible = solve_highs_compact_single_journey_pricing(
            one_task_per_sortie_data,
            JourneyDuals(
                cover={task_id: 0.0 for task_id in one_task_per_sortie_data.task_ids},
                fleet_limit=0.0,
            ),
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=2,
            required_task_count=2,
            required_active_sortie_count=1,
            slot_task_time_pruning=True,
        )
        self.assertEqual(active_capacity_min_infeasible["variable_count"], 0)
        self.assertEqual(active_capacity_min_infeasible["constraint_count"], 0)
        self.assertTrue(active_capacity_min_infeasible["required_active_sortie_count_enabled"])
        self.assertTrue(
            active_capacity_min_infeasible["pricing_complete_for_required_active_sortie_count"]
        )
        self.assertTrue(
            active_capacity_min_infeasible[
                "required_active_sortie_count_infeasible_by_capacity_min"
            ]
        )
        self.assertEqual(
            active_capacity_min_infeasible["required_active_sortie_count_capacity_min"],
            2,
        )
        self.assertTrue(
            active_capacity_min_infeasible[
                "required_active_sortie_count_region_can_certify_no_negative"
            ]
        )

        active_only_infeasible = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            required_active_sortie_count=10_000,
        )
        self.assertEqual(
            active_only_infeasible["status"],
            "COMPACT_HIGHS_PRICING_REQUIRED_ACTIVE_SORTIE_COUNT_INFEASIBLE",
        )
        self.assertEqual(
            active_only_infeasible["exact_status"],
            "REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_INFEASIBLE",
        )
        self.assertFalse(active_only_infeasible["required_task_count_enabled"])
        self.assertFalse(active_only_infeasible["pricing_complete_for_required_task_count"])
        self.assertFalse(
            active_only_infeasible["required_task_count_region_can_certify_no_negative"]
        )
        self.assertTrue(active_only_infeasible["required_active_sortie_count_enabled"])
        self.assertTrue(active_only_infeasible["pricing_complete_for_required_active_sortie_count"])
        self.assertTrue(
            active_only_infeasible["required_active_sortie_count_region_can_certify_no_negative"]
        )
        self.assertTrue(active_only_infeasible["required_active_sortie_count_infeasible"])

        tight_raw = json.loads(json.dumps(generate_instance(5, seed=629003, index=1)))
        tight_probe_data = load_lunar_ice_data(tight_raw)
        for task_id, task_payload in tight_raw["tasks"].items():
            min_depot_travel = min(
                float(option.travel_time_min)
                for option in tight_probe_data.arcs[("depot", str(task_id))].values()
            )
            task_payload["D"] = min_depot_travel + float(task_payload["sigma"]) + 0.1
        tight_data = load_lunar_ice_data(tight_raw)
        empty_active_slot = solve_highs_compact_single_journey_pricing(
            tight_data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=2,
            required_active_sortie_count=2,
            slot_task_time_pruning=True,
        )
        self.assertEqual(
            empty_active_slot["status"],
            "COMPACT_HIGHS_PRICING_REQUIRED_ACTIVE_SORTIE_COUNT_INFEASIBLE",
        )
        self.assertTrue(empty_active_slot["pricing_complete_for_required_active_sortie_count"])
        self.assertTrue(empty_active_slot["required_active_sortie_count_infeasible_by_empty_slot"])
        self.assertTrue(empty_active_slot["required_active_sortie_count_region_can_certify_no_negative"])
        self.assertFalse(empty_active_slot["can_certify_no_negative"])
        self.assertEqual(empty_active_slot["variable_count"], 0)
        self.assertEqual(empty_active_slot["constraint_count"], 0)

        sequence_infeasible = solve_highs_compact_single_journey_pricing(
            tight_data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=1,
            required_task_count=2,
            slot_task_time_pruning=True,
        )
        self.assertEqual(
            sequence_infeasible["status"],
            "COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE",
        )
        self.assertEqual(
            sequence_infeasible["exact_status"],
            "REQUIRED_TASK_COUNT_PRICING_INFEASIBLE",
        )
        self.assertTrue(sequence_infeasible["pricing_complete_for_required_task_count"])
        self.assertTrue(sequence_infeasible["required_task_count_region_can_certify_no_negative"])
        self.assertFalse(sequence_infeasible["can_certify_no_negative"])
        self.assertGreaterEqual(
            sequence_infeasible["required_task_count_slot_capacity_task_upper_bound"],
            2,
        )
        self.assertLess(
            sequence_infeasible["required_task_count_slot_sequence_capacity_upper_bound"],
            2,
        )
        self.assertTrue(sequence_infeasible["required_task_count_infeasible_by_slot_sequence_capacity"])
        self.assertEqual(sequence_infeasible["variable_count"], 0)
        self.assertEqual(sequence_infeasible["constraint_count"], 0)

        limited_raw = json.loads(json.dumps(generate_instance(5, seed=629002, index=1)))
        limited_raw["vehicle"]["max_tasks_per_trip"] = 2
        limited_data = load_lunar_ice_data(limited_raw)
        infeasible = solve_highs_compact_single_journey_pricing(
            limited_data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            required_task_count=3,
            max_sorties_per_journey=1,
        )
        self.assertEqual(
            infeasible["status"],
            "COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE",
        )
        self.assertEqual(infeasible["exact_status"], "REQUIRED_TASK_COUNT_PRICING_INFEASIBLE")
        self.assertTrue(infeasible["pricing_complete_for_required_task_count"])
        self.assertTrue(infeasible["required_task_count_region_can_certify_no_negative"])
        self.assertFalse(infeasible["can_certify_no_negative"])
        self.assertEqual(infeasible["required_task_count_slot_capacity_task_upper_bound"], 2)
        self.assertTrue(infeasible["required_task_count_infeasible_by_slot_capacity"])
        self.assertEqual(infeasible["variable_count"], 0)
        self.assertEqual(infeasible["constraint_count"], 0)

    def test_highs_compact_pair_conflict_capacity_bound_can_fail_scoped_region_before_main_milp(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        raw = json.loads(json.dumps(generate_instance(5, seed=641777, index=1)))
        for task_payload in raw["tasks"].values():
            task_payload["r"] = 300.0
            task_payload["D"] = 300.0 + float(task_payload["d"]) + 0.001
        data = load_lunar_ice_data(raw)
        duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)

        base = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=1,
            required_task_count=2,
            required_active_sortie_count=1,
            slot_task_time_pruning=True,
            pair_time_window_infeasible_cut=True,
        )
        bounded = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            max_sorties_per_journey=1,
            required_task_count=2,
            required_active_sortie_count=1,
            slot_task_time_pruning=True,
            pair_time_window_infeasible_cut=True,
            task_slot_pair_conflict_capacity_bound=True,
        )

        self.assertFalse(base["task_slot_pair_conflict_capacity_bound_enabled"])
        self.assertFalse(base["task_slot_pair_conflict_capacity_bound_requested"])
        self.assertGreater(base["variable_count"], 0)
        self.assertTrue(bounded["task_slot_pair_conflict_capacity_bound_requested"])
        self.assertTrue(bounded["task_slot_pair_conflict_capacity_bound_enabled"])
        self.assertTrue(bounded["task_slot_pair_conflict_capacity_bound_optimal"])
        self.assertEqual(bounded["required_task_count_pair_conflict_capacity_upper_bound"], 1)
        self.assertTrue(bounded["required_task_count_infeasible_by_pair_conflict_capacity"])
        self.assertTrue(bounded["pricing_complete_for_required_task_count"])
        self.assertTrue(bounded["required_task_count_region_can_certify_no_negative"])
        self.assertTrue(bounded["pricing_complete_for_required_active_sortie_count"])
        self.assertTrue(bounded["required_active_sortie_count_region_can_certify_no_negative"])
        self.assertFalse(bounded["can_certify_no_negative"])
        self.assertEqual(
            bounded["status"],
            "COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_INFEASIBLE",
        )
        self.assertEqual(bounded["variable_count"], 0)
        self.assertEqual(bounded["constraint_count"], 0)

    def test_pair_time_window_infeasible_pairs_detects_safe_task_pair_cut(self) -> None:
        raw = json.loads(json.dumps(generate_instance(5, seed=641777, index=1)))
        task_ids = list(raw["tasks"])
        first_id, second_id = task_ids[:2]
        first = raw["tasks"][first_id]
        second = raw["tasks"][second_id]
        first["r"] = 300.0
        first["D"] = 300.0 + float(first["d"]) + 0.001
        second["r"] = 300.0
        second["D"] = 300.0 + float(second["d"]) + 0.001

        data = load_lunar_ice_data(raw)
        infeasible = gurobi_compact_module._pair_time_window_infeasible_pairs(data)

        self.assertIn((first_id, second_id), infeasible)
        self.assertGreater(infeasible[(first_id, second_id)], 0.0)

    def test_pair_time_window_precedence_pairs_detects_safe_forced_order(self) -> None:
        raw = json.loads(json.dumps(generate_instance(5, seed=641777, index=1)))
        early_id, late_id = list(raw["tasks"])[:2]
        baseline = load_lunar_ice_data(raw)
        depot_to = gurobi_compact_module._single_source_shortest_travel_lower_bounds(
            baseline,
            "depot",
        )
        from_early = gurobi_compact_module._single_source_shortest_travel_lower_bounds(
            baseline,
            early_id,
        )
        early = raw["tasks"][early_id]
        late = raw["tasks"][late_id]
        early_service = float(baseline.tasks[early_id].service_time)
        late_service = float(baseline.tasks[late_id].service_time)
        early_start_lb = float(depot_to[early_id])
        early["r"] = 0.0
        early["D"] = early_start_lb + early_service + 5.0
        late_ready = early_start_lb + early_service + float(from_early[late_id]) + 20.0
        late["r"] = late_ready
        late["D"] = late_ready + late_service + 200.0

        data = load_lunar_ice_data(raw)
        forced = gurobi_compact_module._pair_time_window_forced_precedence_pairs(data)

        self.assertIn((early_id, late_id), forced)
        self.assertGreater(forced[(early_id, late_id)], 0.0)

    def test_highs_compact_single_journey_formulation_switches_are_reported(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)},
            fleet_limit=0.123,
        )
        compact = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=False,
            mtz_endpoint_order_cuts=False,
            pair_adjacency_cuts=False,
            latest_service_start_slot_bound=False,
            time_window_arc_pruning=False,
        )

        self.assertEqual(compact["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertFalse(compact["latest_service_start_slot_bound_enabled"])
        self.assertFalse(compact["time_window_arc_pruning_enabled"])
        self.assertEqual(compact["time_window_impossible_arc_option_count"], 0)
        self.assertFalse(compact["mtz_endpoint_order_cuts_enabled"])
        self.assertFalse(compact["pair_adjacency_cuts_enabled"])
        self.assertFalse(compact["service_start_depot_travel_lb_enabled"])
        self.assertEqual(compact["service_start_depot_travel_lb_count"], 0)
        self.assertFalse(compact["task_to_depot_return_travel_lb_enabled"])
        self.assertEqual(compact["task_to_depot_return_travel_lb_count"], 0)
        self.assertFalse(compact["pair_route_duration_lb_enabled"])
        self.assertEqual(compact["pair_route_duration_lb_count"], 0)
        self.assertFalse(compact["pair_weighted_completion_lb_enabled"])
        self.assertEqual(compact["pair_weighted_completion_lb_count"], 0)
        self.assertFalse(compact["sortie_slot_position_bounds_enabled"])
        self.assertEqual(compact["sortie_slot_position_bound_count"], 0)
        self.assertFalse(compact["demand_cover_cut_enabled"])
        self.assertEqual(compact["demand_cover_cut_count"], 0)
        self.assertFalse(compact["single_task_energy_lb_enabled"])
        self.assertEqual(compact["single_task_energy_lb_count"], 0)
        self.assertFalse(compact["single_task_shadow_lb_enabled"])
        self.assertEqual(compact["single_task_shadow_lb_count"], 0)
        self.assertFalse(compact["pair_energy_lb_enabled"])
        self.assertEqual(compact["pair_energy_lb_count"], 0)
        self.assertFalse(compact["pair_shadow_lb_enabled"])
        self.assertEqual(compact["pair_shadow_lb_count"], 0)
        self.assertFalse(compact["pair_energy_infeasible_cut_enabled"])
        self.assertEqual(compact["pair_energy_infeasible_cut_count"], 0)
        self.assertFalse(compact["pair_time_window_infeasible_cut_enabled"])
        self.assertEqual(compact["pair_time_window_infeasible_cut_count"], 0)
        self.assertEqual(compact["pair_time_window_infeasible_pair_count"], 0)
        self.assertFalse(compact["pair_time_window_precedence_cut_enabled"])
        self.assertEqual(compact["pair_time_window_precedence_cut_count"], 0)
        self.assertEqual(compact["pair_time_window_precedence_pair_count"], 0)
        self.assertFalse(compact["triple_time_window_infeasible_cut_enabled"])
        self.assertEqual(compact["triple_time_window_infeasible_cut_count"], 0)
        self.assertEqual(compact["triple_time_window_infeasible_triple_count"], 0)
        self.assertFalse(compact["quad_time_window_infeasible_cut_enabled"])
        self.assertEqual(compact["quad_time_window_infeasible_cut_count"], 0)
        self.assertEqual(compact["quad_time_window_infeasible_quad_count"], 0)
        self.assertFalse(compact["pair_shadow_infeasible_cut_enabled"])
        self.assertEqual(compact["pair_shadow_infeasible_cut_count"], 0)
        self.assertFalse(compact["triple_shadow_infeasible_cut_enabled"])
        self.assertEqual(compact["triple_shadow_infeasible_cut_count"], 0)
        self.assertFalse(compact["triple_energy_infeasible_cut_enabled"])
        self.assertEqual(compact["triple_energy_infeasible_cut_count"], 0)

        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        expected = min(manual_journey_reduced_cost(column, duals) for column in universe.columns)
        strengthened = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            latest_service_start_slot_bound=True,
            service_start_depot_travel_lb=True,
            task_to_depot_return_travel_lb=True,
            pair_route_duration_lb=True,
            pair_weighted_completion_lb=True,
            sortie_slot_position_bounds=True,
            demand_cover_cut=True,
            single_task_energy_lb=True,
            single_task_shadow_lb=True,
            pair_energy_lb=True,
            pair_shadow_lb=True,
            pair_energy_infeasible_cut=True,
            pair_time_window_infeasible_cut=True,
            pair_time_window_precedence_cut=True,
            triple_time_window_infeasible_cut=True,
            quad_time_window_infeasible_cut=True,
            pair_shadow_infeasible_cut=True,
            triple_shadow_infeasible_cut=True,
            triple_energy_infeasible_cut=True,
        )
        self.assertEqual(strengthened["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertTrue(strengthened["service_start_depot_travel_lb_enabled"])
        self.assertEqual(
            strengthened["service_start_depot_travel_lb_count"],
            len(data.task_ids) * strengthened["sortie_slots_per_journey"],
        )
        self.assertGreater(strengthened["service_start_depot_travel_lb_max"], 0.0)
        self.assertTrue(strengthened["task_to_depot_return_travel_lb_enabled"])
        self.assertEqual(
            strengthened["task_to_depot_return_travel_lb_count"],
            len(data.task_ids) * strengthened["sortie_slots_per_journey"],
        )
        self.assertGreater(strengthened["task_to_depot_return_travel_lb_max"], 0.0)
        self.assertTrue(strengthened["pair_route_duration_lb_enabled"])
        self.assertEqual(
            strengthened["pair_route_duration_lb_count"],
            (len(data.task_ids) * (len(data.task_ids) - 1) // 2)
            * strengthened["sortie_slots_per_journey"],
        )
        self.assertGreater(strengthened["pair_route_duration_lb_max"], 0.0)
        self.assertTrue(strengthened["pair_weighted_completion_lb_enabled"])
        self.assertEqual(
            strengthened["pair_weighted_completion_lb_count"],
            (len(data.task_ids) * (len(data.task_ids) - 1) // 2)
            * strengthened["sortie_slots_per_journey"],
        )
        self.assertGreater(strengthened["pair_weighted_completion_lb_max"], 0.0)
        self.assertTrue(strengthened["triple_time_window_infeasible_cut_enabled"])
        self.assertGreaterEqual(strengthened["triple_time_window_infeasible_cut_count"], 0)
        self.assertEqual(
            strengthened["triple_time_window_infeasible_cut_count"],
            strengthened["triple_time_window_infeasible_triple_count"]
            * strengthened["sortie_slots_per_journey"],
        )
        self.assertTrue(strengthened["quad_time_window_infeasible_cut_enabled"])
        self.assertGreaterEqual(strengthened["quad_time_window_infeasible_cut_count"], 0)
        self.assertEqual(
            strengthened["quad_time_window_infeasible_cut_count"],
            strengthened["quad_time_window_infeasible_quad_count"]
            * strengthened["sortie_slots_per_journey"],
        )
        self.assertTrue(strengthened["sortie_slot_position_bounds_enabled"])
        self.assertGreater(strengthened["sortie_slot_position_bound_count"], 0)
        self.assertGreaterEqual(strengthened["sortie_slot_latest_start_upper_bound"], 0.0)
        self.assertTrue(strengthened["demand_cover_cut_enabled"])
        self.assertGreaterEqual(strengthened["demand_cover_cut_count"], 0)
        self.assertTrue(strengthened["single_task_energy_lb_enabled"])
        self.assertEqual(
            strengthened["single_task_energy_lb_count"],
            len(data.task_ids) * strengthened["sortie_slots_per_journey"],
        )
        self.assertGreater(strengthened["single_task_energy_lb_max"], 0.0)
        self.assertTrue(strengthened["single_task_shadow_lb_enabled"])
        self.assertEqual(
            strengthened["single_task_shadow_lb_count"],
            len(data.task_ids) * strengthened["sortie_slots_per_journey"],
        )
        self.assertGreater(strengthened["single_task_shadow_lb_max"], 0.0)
        self.assertTrue(strengthened["pair_energy_lb_enabled"])
        self.assertEqual(
            strengthened["pair_energy_lb_count"],
            (len(data.task_ids) * (len(data.task_ids) - 1) // 2)
            * strengthened["sortie_slots_per_journey"],
        )
        self.assertGreater(strengthened["pair_energy_lb_max"], 0.0)
        self.assertTrue(strengthened["pair_shadow_lb_enabled"])
        self.assertEqual(
            strengthened["pair_shadow_lb_count"],
            (len(data.task_ids) * (len(data.task_ids) - 1) // 2)
            * strengthened["sortie_slots_per_journey"],
        )
        self.assertGreater(strengthened["pair_shadow_lb_max"], 0.0)
        self.assertTrue(strengthened["pair_energy_infeasible_cut_enabled"])
        self.assertGreaterEqual(strengthened["pair_energy_infeasible_cut_count"], 0)
        self.assertTrue(strengthened["pair_time_window_infeasible_cut_enabled"])
        self.assertGreaterEqual(strengthened["pair_time_window_infeasible_cut_count"], 0)
        self.assertGreaterEqual(strengthened["pair_time_window_infeasible_pair_count"], 0)
        self.assertTrue(strengthened["pair_time_window_precedence_cut_enabled"])
        self.assertGreaterEqual(strengthened["pair_time_window_precedence_cut_count"], 0)
        self.assertGreaterEqual(strengthened["pair_time_window_precedence_pair_count"], 0)
        self.assertTrue(strengthened["pair_shadow_infeasible_cut_enabled"])
        self.assertGreaterEqual(strengthened["pair_shadow_infeasible_cut_count"], 0)
        self.assertTrue(strengthened["triple_shadow_infeasible_cut_enabled"])
        self.assertGreaterEqual(strengthened["triple_shadow_infeasible_cut_count"], 0)
        self.assertTrue(strengthened["triple_energy_infeasible_cut_enabled"])
        self.assertGreaterEqual(strengthened["triple_energy_infeasible_cut_count"], 0)
        self.assertAlmostEqual(strengthened["best_reduced_cost"], expected, delta=1.0e-6)
        self.assertAlmostEqual(strengthened["manual_best_reduced_cost"], expected, delta=1.0e-6)
        self.assertTrue(strengthened["pricing_rc_audit_pass"])

    def test_highs_compact_slot_task_time_pruning_preserves_pricing_optimum(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        task_id = sorted(instance["tasks"])[0]
        baseline_data = load_lunar_ice_data(instance)
        min_depot_travel = min(
            option.travel_time_min
            for option in baseline_data.arcs[("depot", task_id)].values()
        )
        service_time = baseline_data.tasks[task_id].service_time
        instance["tasks"][task_id]["r"] = 0.0
        instance["tasks"][task_id]["D"] = float(min_depot_travel) + float(service_time) + 0.5
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)},
            fleet_limit=0.123,
        )

        unpruned = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            mtz_endpoint_order_cuts=True,
            pair_adjacency_cuts=True,
            latest_service_start_slot_bound=True,
            time_window_arc_pruning=True,
            slot_task_time_pruning=False,
        )
        pruned = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            mtz_endpoint_order_cuts=True,
            pair_adjacency_cuts=True,
            latest_service_start_slot_bound=True,
            time_window_arc_pruning=True,
            slot_task_time_pruning=True,
        )

        self.assertEqual(unpruned["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertEqual(pruned["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertFalse(unpruned["slot_task_time_pruning_enabled"])
        self.assertTrue(pruned["slot_task_time_pruning_enabled"])
        self.assertGreater(pruned["slot_task_time_pruned_assignment_count"], 0)
        self.assertGreater(pruned["slot_arc_time_pruned_option_count"], 0)
        self.assertEqual(
            pruned["slot_task_time_total_assignment_count"],
            pruned["slot_task_time_feasible_assignment_count"]
            + pruned["slot_task_time_pruned_assignment_count"],
        )
        self.assertLess(pruned["variable_count"], unpruned["variable_count"])
        self.assertLess(pruned["constraint_count"], unpruned["constraint_count"])
        self.assertAlmostEqual(
            pruned["best_reduced_cost"],
            unpruned["best_reduced_cost"],
            delta=1.0e-6,
        )
        self.assertTrue(pruned["pricing_rc_audit_pass"])

    def test_highs_compact_resource_arc_pruning_preserves_pricing_optimum(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        instance["vehicle"]["B_use"] = 80.0
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)},
            fleet_limit=0.123,
        )

        unpruned = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            mtz_endpoint_order_cuts=True,
            pair_adjacency_cuts=True,
            latest_service_start_slot_bound=True,
            time_window_arc_pruning=True,
            resource_arc_pruning=False,
            slot_task_time_pruning=True,
        )
        pruned = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            mtz_endpoint_order_cuts=True,
            pair_adjacency_cuts=True,
            latest_service_start_slot_bound=True,
            time_window_arc_pruning=True,
            resource_arc_pruning=True,
            slot_task_time_pruning=True,
        )

        self.assertEqual(unpruned["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertEqual(pruned["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertFalse(unpruned["resource_arc_pruning_enabled"])
        self.assertTrue(pruned["resource_arc_pruning_enabled"])
        self.assertGreater(pruned["resource_arc_pruned_option_count"], 0)
        self.assertEqual(
            pruned["resource_arc_pruned_option_count"],
            pruned["resource_arc_energy_pruned_option_count"]
            + pruned["resource_arc_shadow_pruned_option_count"]
            + pruned["resource_arc_demand_pruned_option_count"],
        )
        self.assertLess(pruned["variable_count"], unpruned["variable_count"])
        self.assertAlmostEqual(
            pruned["best_reduced_cost"],
            unpruned["best_reduced_cost"],
            delta=1.0e-6,
        )
        self.assertAlmostEqual(
            pruned["manual_best_reduced_cost"],
            unpruned["manual_best_reduced_cost"],
            delta=1.0e-6,
        )
        self.assertTrue(pruned["pricing_rc_audit_pass"])

    def test_highs_compact_slot_arc_support_pruning_preserves_pricing_optimum(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629003, index=1)
        instance["vehicle"]["B_use"] = 80.0
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)},
            fleet_limit=0.123,
        )

        base = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            mtz_endpoint_order_cuts=True,
            pair_adjacency_cuts=True,
            latest_service_start_slot_bound=True,
            time_window_arc_pruning=True,
            resource_arc_pruning=True,
            slot_task_time_pruning=True,
            slot_arc_support_pruning=False,
        )
        pruned = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            mtz_endpoint_order_cuts=True,
            pair_adjacency_cuts=True,
            latest_service_start_slot_bound=True,
            time_window_arc_pruning=True,
            resource_arc_pruning=True,
            slot_task_time_pruning=True,
            slot_arc_support_pruning=True,
        )

        self.assertEqual(base["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertEqual(pruned["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertFalse(base["slot_arc_support_pruning_enabled"])
        self.assertTrue(pruned["slot_arc_support_pruning_enabled"])
        self.assertGreater(pruned["slot_arc_support_pruned_assignment_count"], 0)
        self.assertGreater(pruned["slot_arc_support_pruned_option_count"], 0)
        self.assertLessEqual(
            pruned["slot_arc_support_pruned_assignment_count"],
            pruned["slot_arc_support_pruned_unreachable_count"]
            + pruned["slot_arc_support_pruned_no_return_count"],
        )
        self.assertLess(pruned["slot_task_model_assignment_count"], base["slot_task_model_assignment_count"])
        self.assertLess(pruned["variable_count"], base["variable_count"])
        self.assertAlmostEqual(pruned["best_reduced_cost"], base["best_reduced_cost"], delta=1.0e-6)
        self.assertAlmostEqual(
            pruned["manual_best_reduced_cost"],
            base["manual_best_reduced_cost"],
            delta=1.0e-6,
        )
        self.assertTrue(pruned["pricing_rc_audit_pass"])

    def test_highs_compact_dual_task_slot_lower_bound_certifies_scoped_region_only(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)

        result = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            latest_service_start_slot_bound=True,
            time_window_arc_pruning=True,
            slot_task_time_pruning=True,
            pair_energy_infeasible_cut=True,
            pair_time_window_infeasible_cut=True,
            dual_task_slot_lower_bound=True,
            required_task_count=2,
            required_active_sortie_count=1,
        )

        self.assertEqual(
            result["status"],
            "COMPACT_HIGHS_PRICING_REQUIRED_TASK_COUNT_DUAL_TASK_SLOT_LB_CERTIFIED",
        )
        self.assertEqual(
            result["exact_status"],
            "REQUIRED_TASK_COUNT_PRICING_DUAL_TASK_SLOT_LB_CERTIFIED",
        )
        self.assertTrue(result["required_task_count_certified_by_dual_task_slot_lower_bound"])
        self.assertTrue(result["dual_task_slot_lower_bound_enabled"])
        self.assertTrue(result["dual_task_slot_lower_bound_applicable"])
        self.assertTrue(result["dual_task_slot_lower_bound_optimal"])
        self.assertGreaterEqual(result["dual_task_slot_lower_bound_value"], -1.0e-6)
        self.assertEqual(result["dual_bound"], result["dual_task_slot_lower_bound_value"])
        self.assertTrue(result["pricing_complete_for_required_task_count"])
        self.assertTrue(result["required_task_count_region_can_certify_no_negative"])
        self.assertTrue(result["pricing_complete_for_required_active_sortie_count"])
        self.assertTrue(result["required_active_sortie_count_region_can_certify_no_negative"])
        self.assertFalse(result["can_certify_no_negative"])
        self.assertEqual(result["variable_count"], 0)
        self.assertEqual(result["constraint_count"], 0)
        self.assertGreater(result["dual_task_slot_lower_bound_variable_count"], 0)

    def test_highs_compact_dual_task_slot_route_arc_lb_is_safe_for_scoped_region(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)
        common_kwargs = {
            "time_limit_sec": 30.0,
            "threads": 1,
            "mtz_connectivity": True,
            "latest_service_start_slot_bound": True,
            "time_window_arc_pruning": True,
            "slot_task_time_pruning": True,
            "pair_energy_infeasible_cut": True,
            "pair_time_window_infeasible_cut": True,
            "required_task_count": 2,
            "required_active_sortie_count": 1,
        }

        exact = solve_highs_compact_single_journey_pricing(data, duals, **common_kwargs)
        lower_bound = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            dual_task_slot_lower_bound=True,
            **common_kwargs,
        )

        self.assertEqual(exact["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertIsNotNone(exact["best_reduced_cost"])
        self.assertTrue(lower_bound["dual_task_slot_lower_bound_enabled"])
        self.assertTrue(lower_bound["dual_task_slot_lower_bound_optimal"])
        self.assertEqual(
            lower_bound["dual_task_slot_lower_bound_route_arc_mode"],
            "slot_incoming_outgoing_max",
        )
        self.assertEqual(lower_bound["dual_task_slot_lower_bound_route_arc_row_count"], 3)
        self.assertIsNotNone(lower_bound["dual_task_slot_lower_bound_route_arc_value"])
        self.assertGreater(
            lower_bound["dual_task_slot_lower_bound_pair_route_arc_bound_row_count"],
            0,
        )
        self.assertIsNotNone(lower_bound["dual_task_slot_lower_bound_pair_route_arc_bound_max"])
        self.assertGreater(
            lower_bound["dual_task_slot_lower_bound_pair_completion_lift_var_count"],
            0,
        )
        self.assertGreater(
            lower_bound["dual_task_slot_lower_bound_pair_completion_lift_row_count"],
            0,
        )
        self.assertIsNotNone(lower_bound["dual_task_slot_lower_bound_pair_completion_lift_max"])
        self.assertLessEqual(
            lower_bound["dual_task_slot_lower_bound_value"],
            exact["best_reduced_cost"] + 1.0e-6,
        )

    def test_highs_compact_dual_task_slot_single_route_lb_is_safe_when_task_count_matches_sorties(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)
        common_kwargs = {
            "time_limit_sec": 30.0,
            "threads": 1,
            "mtz_connectivity": True,
            "latest_service_start_slot_bound": True,
            "time_window_arc_pruning": True,
            "slot_task_time_pruning": True,
            "pair_energy_infeasible_cut": True,
            "pair_time_window_infeasible_cut": True,
            "required_task_count": 2,
            "required_active_sortie_count": 2,
        }

        exact = solve_highs_compact_single_journey_pricing(data, duals, **common_kwargs)
        lower_bound = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            dual_task_slot_lower_bound=True,
            **common_kwargs,
        )

        self.assertEqual(exact["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertTrue(lower_bound["dual_task_slot_lower_bound_optimal"])
        self.assertEqual(
            lower_bound["dual_task_slot_lower_bound_single_task_route_arc_bound_row_count"],
            1,
        )
        self.assertIsNotNone(
            lower_bound["dual_task_slot_lower_bound_single_task_route_arc_bound_max"]
        )
        self.assertLessEqual(
            lower_bound["dual_task_slot_lower_bound_value"],
            exact["best_reduced_cost"] + 1.0e-6,
        )

    def test_highs_compact_dual_task_slot_triple_route_lb_is_safe_for_single_sortie(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)
        common_kwargs = {
            "time_limit_sec": 30.0,
            "threads": 1,
            "mtz_connectivity": True,
            "latest_service_start_slot_bound": True,
            "time_window_arc_pruning": True,
            "slot_task_time_pruning": True,
            "pair_energy_infeasible_cut": True,
            "pair_time_window_infeasible_cut": True,
            "required_task_count": 3,
            "required_active_sortie_count": 1,
        }

        exact = solve_highs_compact_single_journey_pricing(data, duals, **common_kwargs)
        lower_bound = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            dual_task_slot_lower_bound=True,
            **common_kwargs,
        )

        self.assertEqual(exact["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertTrue(lower_bound["dual_task_slot_lower_bound_optimal"])
        self.assertGreater(
            lower_bound["dual_task_slot_lower_bound_triple_route_arc_bound_row_count"],
            0,
        )
        self.assertIsNotNone(
            lower_bound["dual_task_slot_lower_bound_triple_route_arc_bound_max"]
        )
        self.assertLessEqual(
            lower_bound["dual_task_slot_lower_bound_value"],
            exact["best_reduced_cost"] + 1.0e-6,
        )

    def test_highs_compact_dual_task_slot_one_pair_rest_single_route_lb_is_safe(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)
        common_kwargs = {
            "time_limit_sec": 30.0,
            "threads": 1,
            "mtz_connectivity": True,
            "latest_service_start_slot_bound": True,
            "time_window_arc_pruning": True,
            "slot_task_time_pruning": True,
            "pair_energy_infeasible_cut": True,
            "pair_time_window_infeasible_cut": True,
            "required_task_count": 3,
            "required_active_sortie_count": 2,
        }

        exact = solve_highs_compact_single_journey_pricing(data, duals, **common_kwargs)
        lower_bound = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            dual_task_slot_lower_bound=True,
            **common_kwargs,
        )

        self.assertEqual(exact["status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
        self.assertTrue(lower_bound["dual_task_slot_lower_bound_optimal"])
        self.assertEqual(
            lower_bound[
                "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_var_count"
            ],
            0,
        )
        self.assertGreater(
            lower_bound[
                "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_row_count"
            ],
            0,
        )
        self.assertGreater(
            lower_bound[
                "dual_task_slot_lower_bound_one_pair_rest_single_route_arc_pair_count"
            ],
            0,
        )
        self.assertLessEqual(
            lower_bound["dual_task_slot_lower_bound_value"],
            exact["best_reduced_cost"] + 1.0e-6,
        )

    def test_highs_compact_full_space_dual_task_slot_lb_early_stop_is_not_certificate(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 10.0 for task_id in data.task_ids}, fleet_limit=0.0)

        result = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            mtz_endpoint_order_cuts=True,
            pair_adjacency_cuts=True,
            latest_service_start_slot_bound=True,
            time_window_arc_pruning=True,
            resource_arc_pruning=True,
            slot_task_time_pruning=True,
            dual_task_slot_full_space_lower_bound=True,
            dual_task_slot_full_space_lb_time_limit_sec=0.1,
            dual_task_slot_full_space_lb_early_stop_on_negative=True,
        )

        self.assertTrue(result["dual_task_slot_full_space_lower_bound_enabled"])
        self.assertTrue(result["dual_task_slot_full_space_lower_bound_applicable"])
        self.assertTrue(result["dual_task_slot_full_space_lower_bound_early_stop_on_negative"])
        self.assertTrue(result["dual_task_slot_full_space_lower_bound_early_stopped_on_negative"])
        self.assertFalse(result["dual_task_slot_full_space_lower_bound_coverage_complete"])
        self.assertFalse(result["dual_task_slot_full_space_lower_bound_can_certify"])
        self.assertGreater(result["dual_task_slot_full_space_lower_bound_negative_region_count"], 0)
        self.assertEqual(
            result["dual_task_slot_full_space_lower_bound_status"],
            "BOUND_SCAN_NEGATIVE_REGION_EARLY_STOP",
        )
        self.assertNotEqual(
            result["status"],
            "COMPACT_HIGHS_PRICING_DUAL_TASK_SLOT_FULL_SPACE_LB_CERTIFIED",
        )
        self.assertFalse(result["can_certify_no_negative"])
        self.assertLess(result["best_reduced_cost"], -1.0e-6)
        self.assertTrue(result["pricing_rc_audit_pass"])

    def test_highs_compact_single_journey_negative_feasibility_search(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)

        no_negative_duals = JourneyDuals(cover=cover_duals, fleet_limit=0.0)
        no_negative_expected = min(manual_journey_reduced_cost(column, no_negative_duals) for column in universe.columns)
        self.assertGreater(no_negative_expected, 0.0)
        no_negative = solve_highs_compact_single_journey_pricing(
            data,
            no_negative_duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            negative_feasibility_search=True,
        )
        self.assertEqual(no_negative["pricing_state"], "CERTIFIED_NO_NEGATIVE")
        self.assertEqual(no_negative["exact_status"], "EXACT_NEGATIVE_FEASIBILITY_INFEASIBLE")
        self.assertTrue(no_negative["can_certify_no_negative"])
        self.assertTrue(no_negative["negative_feasibility_search_enabled"])
        self.assertTrue(no_negative["negative_feasibility_zero_objective_enabled"])
        self.assertTrue(no_negative["mtz_connectivity_enabled"])

        negative_duals = JourneyDuals(cover=cover_duals, fleet_limit=2.0)
        negative_expected = min(manual_journey_reduced_cost(column, negative_duals) for column in universe.columns)
        self.assertLess(negative_expected, -1.0e-6)
        negative = solve_highs_compact_single_journey_pricing(
            data,
            negative_duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            negative_feasibility_search=True,
        )
        self.assertEqual(negative["pricing_state"], "FOUND_NEGATIVE")
        self.assertTrue(negative["negative_found"])
        self.assertTrue(negative["negative_feasibility_zero_objective_enabled"])
        self.assertLess(negative["manual_best_reduced_cost"], -1.0e-6)
        self.assertTrue(negative["pricing_rc_audit_pass"])
        forbidden_pattern = tuple(
            (slot, leg.source, leg.target, leg.path_type)
            for slot, sortie in enumerate(negative["journeys"][0].sorties)
            for leg in sortie.legs
        )
        restricted_no_negative = solve_highs_compact_single_journey_pricing(
            data,
            no_negative_duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            negative_feasibility_search=True,
            forbidden_arc_patterns=(forbidden_pattern,),
        )
        self.assertEqual(restricted_no_negative["pricing_state"], "INCOMPLETE_LIMIT")
        self.assertFalse(restricted_no_negative["can_certify_no_negative"])
        self.assertFalse(restricted_no_negative["pricing_complete_for_all_task_subsets"])
        self.assertEqual(
            restricted_no_negative["exact_status"],
            "RESTRICTED_NEGATIVE_FEASIBILITY_INFEASIBLE",
        )
        restricted_task_set_no_negative = solve_highs_compact_single_journey_pricing(
            data,
            no_negative_duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            negative_feasibility_search=True,
            forbidden_task_sets=(tuple(sorted(negative["journeys"][0].task_set)),),
        )
        self.assertEqual(restricted_task_set_no_negative["pricing_state"], "INCOMPLETE_LIMIT")
        self.assertFalse(restricted_task_set_no_negative["can_certify_no_negative"])
        self.assertFalse(restricted_task_set_no_negative["pricing_complete_for_all_task_subsets"])
        self.assertEqual(restricted_task_set_no_negative["forbidden_task_set_count"], 1)
        self.assertEqual(
            restricted_task_set_no_negative["exact_status"],
            "RESTRICTED_NEGATIVE_FEASIBILITY_INFEASIBLE",
        )

    def test_highs_compact_single_journey_objective_bound_cutoff_certifies_no_negative(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        duals = JourneyDuals(cover=cover_duals, fleet_limit=0.0)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        expected = min(manual_journey_reduced_cost(column, duals) for column in universe.columns)
        self.assertGreater(expected, 0.0)

        result = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=30.0,
            threads=1,
            mtz_connectivity=True,
            objective_bound_no_negative_cutoff=True,
            negative_eps=1.0e-6,
        )

        self.assertEqual(result["pricing_state"], "CERTIFIED_NO_NEGATIVE")
        self.assertIn(
            result["status"],
            {
                "COMPACT_HIGHS_PRICING_OBJECTIVE_BOUND_NO_NEGATIVE",
                "COMPACT_HIGHS_PRICING_OPTIMAL",
            },
        )
        self.assertIn(
            result["exact_status"],
            {
                "EXACT_OBJECTIVE_BOUND_NO_NEGATIVE",
                "EXACT_PRICING_OPTIMAL",
            },
        )
        self.assertTrue(result["can_certify_no_negative"])
        self.assertTrue(result["objective_bound_no_negative_cutoff_enabled"])
        self.assertAlmostEqual(result["objective_bound_no_negative_cutoff_value"], -1.0e-6)
        self.assertEqual(
            bool(result["objective_bound_no_negative_cutoff_can_certify"]),
            result["status"] == "COMPACT_HIGHS_PRICING_OBJECTIVE_BOUND_NO_NEGATIVE",
        )
        self.assertFalse(result["negative_feasibility_zero_objective_enabled"])
        self.assertFalse(result["negative_found"])

    def test_compact_final_judge_hybrid_uses_negative_search_for_negative_columns(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=2.0,
            dual_fingerprint="compact-hybrid-test",
        )

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_NEGATIVE_BATCH_TARGET": "2",
                "LUNAR_ICE_COMPACT_NEGATIVE_SEARCH_CAP_SEC": "30",
                "LUNAR_ICE_COMPACT_NEGATIVE_NO_GOOD_SCOPE": "task_set",
            },
        ):
            result = _run_compact_single_journey_pricing_final_judge(
                data,
                JourneyDuals(cover=cover_duals, fleet_limit=2.0),
                context=context,
                branch_context=BranchContext(),
                cut_context=CutContext(),
                negative_eps=1.0e-6,
                wall_time_limit_sec=30.0,
            )

        self.assertEqual(result.pricing_state, PricingState.FOUND_NEGATIVE)
        self.assertGreater(len(result.negative_columns), 0)
        self.assertEqual(result.pricing_payload["compact_pricing_phase"], "negative_feasibility_batch")
        self.assertTrue(result.pricing_payload["negative_found"])
        self.assertFalse(result.pricing_payload["mtz_connectivity_enabled"])
        self.assertFalse(result.pricing_payload["mtz_endpoint_order_cuts_enabled"])
        self.assertFalse(result.pricing_payload["pair_adjacency_cuts_enabled"])
        self.assertTrue(result.pricing_payload["latest_service_start_slot_bound_enabled"])
        self.assertEqual(result.pricing_payload["sortie_slots_per_journey"], len(data.task_ids))
        self.assertIn(
            result.pricing_payload["sortie_slot_bound_source"],
            {"task_count_bound", "latest_service_start_min_active_sortie_duration_bound"},
        )
        self.assertFalse(result.pricing_payload["time_window_arc_pruning_enabled"])
        self.assertGreater(result.pricing_payload["time_window_arc_option_count"], 0)
        self.assertEqual(result.pricing_payload["time_window_impossible_arc_option_count"], 0)
        phase_payloads = result.pricing_payload["compact_pricing_phase_payloads"]
        first_phase = phase_payloads["negative_feasibility_search_1"]
        self.assertEqual(first_phase["sortie_slots_per_journey"], len(data.task_ids))
        self.assertTrue(first_phase["latest_service_start_slot_bound_enabled"])
        self.assertFalse(first_phase["mtz_endpoint_order_cuts_enabled"])
        self.assertFalse(first_phase["pair_adjacency_cuts_enabled"])
        self.assertFalse(first_phase["time_window_arc_pruning_enabled"])
        self.assertGreater(first_phase["time_window_arc_option_count"], 0)
        self.assertTrue(result.pricing_payload["pricing_rc_audit_pass"])
        self.assertFalse(result.pricing_payload["can_certify_no_negative"])
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], "FRONTIER_BOUND_INCOMPLETE")
        self.assertFalse(result.pricing_payload["global_remaining_rc_lb_coverage_complete"])
        self.assertEqual(result.pricing_payload["compact_negative_batch_target"], 2)
        self.assertEqual(result.pricing_payload["compact_negative_no_good_scope"], "task_set")
        self.assertEqual(result.pricing_payload["compact_negative_search_cap_sec"], 30.0)
        self.assertGreaterEqual(result.pricing_payload["compact_negative_batch_search_call_count"], 1)
        self.assertEqual(
            result.pricing_payload["compact_negative_batch_found_count"],
            len(result.negative_columns),
        )
        self.assertEqual(
            result.pricing_payload["forbidden_task_set_count"],
            len({tuple(sorted(column.task_set)) for column in result.negative_columns}),
        )
        self.assertEqual(result.pricing_payload["harvest_selected_count"], len(result.negative_columns))
        self.assertEqual(result.pricing_payload["harvest_candidate_negative_count"], len(result.negative_columns))
        self.assertEqual(result.pricing_payload["harvest_source_phase"], "compact_final_judge_negative_feasibility_batch")
        self.assertEqual(result.pricing_payload["harvest_target"], 2)
        self.assertTrue(result.pricing_payload["harvest_pricing_rc_audit_available"])
        self.assertTrue(result.pricing_payload["harvest_pricing_rc_audit_pass"])
        self.assertLessEqual(result.pricing_payload["harvest_pricing_rc_max_abs_diff"], 1.0e-6)
        self.assertLess(result.pricing_payload["harvest_best_true_rc"], -1.0e-6)
        self.assertFalse(result.pricing_payload["restricted_harvest_can_certify_no_negative"])
        self.assertLess(
            manual_journey_reduced_cost(result.negative_columns[0], JourneyDuals(cover=cover_duals, fleet_limit=2.0)),
            -1.0e-6,
        )

    def test_b4_1_compact_final_judge_optimization_harvest_is_restricted_and_uncertified(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        columns = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
        first = columns[0]
        second = next(column for column in columns[1:] if set(column.task_set) != set(first.task_set))
        duals = JourneyDuals(cover={task_id: 1000.0 for task_id in data.task_ids}, fleet_limit=0.0)
        first_rc = manual_journey_reduced_cost(first, duals)
        second_rc = manual_journey_reduced_cost(second, duals)
        context = ReducedCostContext(
            task_duals=dict(duals.cover),
            fleet_dual=duals.fleet_limit,
            dual_fingerprint="b4-1-optimization-harvest-test",
        )
        first_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "FOUND_NEGATIVE",
            "exact_status": "EXACT_PRICING_OPTIMAL",
            "best_reduced_cost": first_rc,
            "manual_best_reduced_cost": first_rc,
            "pricing_model_reduced_cost": first_rc,
            "pricing_best_reduced_cost": first_rc,
            "dual_bound": first_rc,
            "can_certify_no_negative": False,
            "pricing_rc_audit_pass": True,
            "negative_found": True,
            "journeys": (first,),
        }
        second_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "FOUND_NEGATIVE",
            "exact_status": "EXACT_PRICING_OPTIMAL",
            "best_reduced_cost": second_rc,
            "manual_best_reduced_cost": second_rc,
            "pricing_model_reduced_cost": second_rc,
            "pricing_best_reduced_cost": second_rc,
            "dual_bound": second_rc,
            "can_certify_no_negative": False,
            "pricing_rc_audit_pass": True,
            "negative_found": True,
            "journeys": (second,),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
                "LUNAR_ICE_COMPACT_OPTIMIZATION_HARVEST_TARGET": "2",
                "LUNAR_ICE_COMPACT_NEGATIVE_NO_GOOD_SCOPE": "arc",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                side_effect=(first_probe, second_probe),
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    duals,
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(mocked_solver.call_count, 2)
        self.assertFalse(mocked_solver.call_args_list[0].kwargs.get("negative_feasibility_search", False))
        self.assertFalse(mocked_solver.call_args_list[1].kwargs.get("negative_feasibility_search", False))
        self.assertEqual(
            mocked_solver.call_args_list[1].kwargs["forbidden_task_sets"],
            (tuple(sorted(first.task_set)),),
        )
        self.assertEqual(mocked_solver.call_args_list[1].kwargs["forbidden_arc_patterns"], tuple())
        self.assertEqual(result.pricing_state, PricingState.FOUND_NEGATIVE)
        self.assertEqual(len(result.negative_columns), 2)
        self.assertEqual(result.pricing_payload["compact_pricing_phase"], "optimization_harvest")
        self.assertTrue(result.pricing_payload["compact_optimization_harvest_enabled"])
        self.assertEqual(result.pricing_payload["compact_optimization_harvest_target"], 2)
        self.assertEqual(result.pricing_payload["compact_negative_no_good_scope"], "arc")
        self.assertEqual(result.pricing_payload["compact_optimization_harvest_no_good_scope"], "task_set")
        self.assertEqual(result.pricing_payload["compact_optimization_harvest_found_count"], 2)
        self.assertEqual(result.pricing_payload["compact_optimization_harvest_search_call_count"], 2)
        self.assertEqual(result.pricing_payload["harvest_source_phase"], "compact_final_judge_optimization_harvest")
        self.assertEqual(result.pricing_payload["harvest_selected_count"], 2)
        self.assertTrue(result.pricing_payload["harvest_pricing_rc_audit_available"])
        self.assertTrue(result.pricing_payload["harvest_pricing_rc_audit_pass"])
        self.assertLessEqual(result.pricing_payload["harvest_pricing_rc_max_abs_diff"], 1.0e-6)
        self.assertFalse(result.pricing_payload["restricted_harvest_can_certify_no_negative"])
        self.assertFalse(result.pricing_payload["can_certify_no_negative"])
        self.assertFalse(result.pricing_payload["uses_true_dual_bpc_certificate"])
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], "FRONTIER_BOUND_INCOMPLETE")

    def test_b4_1_compact_final_judge_default_uses_v2_formulation(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v2-default",
        )
        negative_probe = {
            "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
            "pricing_state": "INCOMPLETE_LIMIT",
            "exact_status": "NOT_SOLVED",
            "can_certify_no_negative": False,
            "pricing_rc_audit_pass": True,
            "journeys": tuple(),
        }
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "journeys": tuple(),
        }

        with patch.dict("os.environ", {"LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": ""}):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                side_effect=(negative_probe, proof_probe),
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)
        self.assertEqual(mocked_solver.call_count, 2)
        negative_kwargs = mocked_solver.call_args_list[0].kwargs
        proof_kwargs = mocked_solver.call_args_list[1].kwargs
        self.assertFalse(negative_kwargs["mtz_connectivity"])
        self.assertTrue(negative_kwargs["negative_feasibility_search"])
        self.assertFalse(negative_kwargs["mtz_endpoint_order_cuts"])
        self.assertFalse(negative_kwargs["pair_adjacency_cuts"])
        self.assertTrue(negative_kwargs["latest_service_start_slot_bound"])
        self.assertFalse(negative_kwargs["time_window_arc_pruning"])
        self.assertFalse(negative_kwargs["slot_task_time_pruning"])
        self.assertFalse(negative_kwargs["slot_arc_support_pruning"])
        self.assertFalse(negative_kwargs["dual_task_slot_full_space_lower_bound"])
        self.assertTrue(negative_kwargs["dual_task_slot_full_space_lb_early_stop_on_negative"])
        self.assertFalse(negative_kwargs["service_start_depot_travel_lb"])
        self.assertFalse(negative_kwargs["task_to_depot_return_travel_lb"])
        self.assertFalse(negative_kwargs["pair_route_duration_lb"])
        self.assertFalse(negative_kwargs["sortie_slot_position_bounds"])
        self.assertFalse(negative_kwargs["demand_cover_cut"])
        self.assertFalse(negative_kwargs["single_task_energy_lb"])
        self.assertFalse(negative_kwargs["single_task_shadow_lb"])
        self.assertFalse(negative_kwargs["pair_energy_lb"])
        self.assertFalse(negative_kwargs["pair_shadow_lb"])
        self.assertFalse(negative_kwargs["pair_energy_infeasible_cut"])
        self.assertFalse(negative_kwargs["pair_time_window_infeasible_cut"])
        self.assertFalse(negative_kwargs["pair_time_window_precedence_cut"])
        self.assertFalse(negative_kwargs["pair_shadow_infeasible_cut"])
        self.assertFalse(negative_kwargs["triple_shadow_infeasible_cut"])
        self.assertFalse(negative_kwargs["triple_energy_infeasible_cut"])
        self.assertTrue(proof_kwargs["mtz_connectivity"])
        self.assertFalse(proof_kwargs["mtz_endpoint_order_cuts"])
        self.assertFalse(proof_kwargs["pair_adjacency_cuts"])
        self.assertTrue(proof_kwargs["latest_service_start_slot_bound"])
        self.assertFalse(proof_kwargs["time_window_arc_pruning"])
        self.assertFalse(proof_kwargs["resource_arc_pruning"])
        self.assertFalse(proof_kwargs["slot_task_time_pruning"])
        self.assertFalse(proof_kwargs["slot_arc_support_pruning"])
        self.assertFalse(proof_kwargs["dual_task_slot_full_space_lower_bound"])
        self.assertTrue(proof_kwargs["dual_task_slot_full_space_lb_early_stop_on_negative"])
        self.assertFalse(proof_kwargs["service_start_depot_travel_lb"])
        self.assertFalse(proof_kwargs["task_to_depot_return_travel_lb"])
        self.assertFalse(proof_kwargs["pair_route_duration_lb"])
        self.assertFalse(proof_kwargs["sortie_slot_position_bounds"])
        self.assertFalse(proof_kwargs["demand_cover_cut"])
        self.assertFalse(proof_kwargs["single_task_energy_lb"])
        self.assertFalse(proof_kwargs["single_task_shadow_lb"])
        self.assertFalse(proof_kwargs["pair_energy_lb"])
        self.assertFalse(proof_kwargs["pair_shadow_lb"])
        self.assertFalse(proof_kwargs["pair_energy_infeasible_cut"])
        self.assertFalse(proof_kwargs["pair_time_window_infeasible_cut"])
        self.assertFalse(proof_kwargs["pair_time_window_precedence_cut"])
        self.assertFalse(proof_kwargs["pair_shadow_infeasible_cut"])
        self.assertFalse(proof_kwargs["triple_shadow_infeasible_cut"])
        self.assertFalse(proof_kwargs["triple_energy_infeasible_cut"])
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "B4V2")
        self.assertEqual(result.pricing_payload["compact_final_judge_formulation_profile"], "B4V2_latest_start_only")
        self.assertTrue(result.pricing_payload["compact_final_judge_profile_official_default"])
        self.assertEqual(result.pricing_payload["compact_final_judge_phase_mode"], "harvest_then_proof")
        self.assertFalse(result.pricing_payload["negative_feasibility_skipped_for_proof_only"])
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], "EXHAUSTIVE_NO_NEGATIVE")

    def test_b4_1_compact_final_judge_v4_profile_is_explicit_opt_in(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4-profile",
        )
        negative_probe = {
            "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
            "pricing_state": "INCOMPLETE_LIMIT",
            "exact_status": "NOT_SOLVED",
            "can_certify_no_negative": False,
            "pricing_rc_audit_pass": True,
            "journeys": tuple(),
        }
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "journeys": tuple(),
        }

        with patch.dict("os.environ", {"LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4"}):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                side_effect=(negative_probe, proof_probe),
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)
        self.assertEqual(mocked_solver.call_count, 2)
        negative_kwargs = mocked_solver.call_args_list[0].kwargs
        proof_kwargs = mocked_solver.call_args_list[1].kwargs
        for kwargs in (negative_kwargs, proof_kwargs):
            self.assertTrue(kwargs["mtz_connectivity"])
            self.assertTrue(kwargs["mtz_endpoint_order_cuts"])
            self.assertTrue(kwargs["pair_adjacency_cuts"])
            self.assertTrue(kwargs["latest_service_start_slot_bound"])
            self.assertTrue(kwargs["time_window_arc_pruning"])
            self.assertTrue(kwargs["resource_arc_pruning"])
            self.assertTrue(kwargs["slot_task_time_pruning"])
            self.assertFalse(kwargs["slot_arc_support_pruning"])
            self.assertFalse(kwargs["dual_task_slot_full_space_lower_bound"])
            self.assertTrue(kwargs["dual_task_slot_full_space_lb_early_stop_on_negative"])
            self.assertFalse(kwargs["service_start_depot_travel_lb"])
            self.assertFalse(kwargs["task_to_depot_return_travel_lb"])
            self.assertFalse(kwargs["pair_route_duration_lb"])
            self.assertFalse(kwargs["sortie_slot_position_bounds"])
            self.assertFalse(kwargs["demand_cover_cut"])
            self.assertFalse(kwargs["single_task_energy_lb"])
            self.assertFalse(kwargs["single_task_shadow_lb"])
            self.assertFalse(kwargs["pair_energy_lb"])
            self.assertFalse(kwargs["pair_shadow_lb"])
            self.assertFalse(kwargs["pair_energy_infeasible_cut"])
            self.assertFalse(kwargs["pair_time_window_infeasible_cut"])
            self.assertFalse(kwargs["pair_time_window_precedence_cut"])
            self.assertFalse(kwargs["pair_shadow_infeasible_cut"])
            self.assertFalse(kwargs["triple_shadow_infeasible_cut"])
            self.assertFalse(kwargs["triple_energy_infeasible_cut"])
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4")
        self.assertEqual(
            result.pricing_payload["compact_final_judge_formulation_profile"],
            "B4V4_endpoint_pair_latest_start_time_window",
        )
        self.assertFalse(result.pricing_payload["compact_final_judge_profile_official_default"])
        self.assertEqual(result.pricing_payload["compact_final_judge_phase_mode"], "harvest_then_proof")
        self.assertFalse(result.pricing_payload["negative_feasibility_skipped_for_proof_only"])
        self.assertEqual(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "compact_final_judge_profile"
            ],
            "V4",
        )

    def test_b4_1_v4_final_judge_cut_strengthening_can_be_opted_out(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4-lean-proof-profile",
        )
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
                "LUNAR_ICE_COMPACT_MTZ_ENDPOINT_ORDER_CUTS": "0",
                "LUNAR_ICE_COMPACT_PAIR_ADJACENCY_CUTS": "0",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(mocked_solver.call_count, 1)
        proof_kwargs = mocked_solver.call_args.kwargs
        self.assertTrue(proof_kwargs["mtz_connectivity"])
        self.assertFalse(proof_kwargs["mtz_endpoint_order_cuts"])
        self.assertFalse(proof_kwargs["pair_adjacency_cuts"])
        self.assertTrue(proof_kwargs["latest_service_start_slot_bound"])
        self.assertTrue(proof_kwargs["time_window_arc_pruning"])
        self.assertTrue(proof_kwargs["resource_arc_pruning"])
        self.assertTrue(proof_kwargs["slot_task_time_pruning"])
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4")
        self.assertEqual(result.pricing_payload["compact_final_judge_phase_mode"], "proof_only")

    def test_b4_1_v4_final_judge_proof_mtz_can_be_opted_out(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4-no-mtz-proof-profile",
        )
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
                "LUNAR_ICE_COMPACT_PROOF_MTZ_CONNECTIVITY": "0",
                "LUNAR_ICE_COMPACT_MTZ_ENDPOINT_ORDER_CUTS": "0",
                "LUNAR_ICE_COMPACT_PAIR_ADJACENCY_CUTS": "0",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(mocked_solver.call_count, 1)
        proof_kwargs = mocked_solver.call_args.kwargs
        self.assertFalse(proof_kwargs["mtz_connectivity"])
        self.assertFalse(proof_kwargs["mtz_endpoint_order_cuts"])
        self.assertFalse(proof_kwargs["pair_adjacency_cuts"])
        self.assertTrue(proof_kwargs["latest_service_start_slot_bound"])
        self.assertTrue(proof_kwargs["time_window_arc_pruning"])
        self.assertTrue(proof_kwargs["resource_arc_pruning"])
        self.assertTrue(proof_kwargs["slot_task_time_pruning"])
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4")
        self.assertFalse(
            result.pricing_payload["compact_final_judge_profile_proof_mtz_connectivity"]
        )
        self.assertEqual(result.pricing_payload["compact_final_judge_phase_mode"], "proof_only")

    def test_b4_1_v4_final_judge_pair_weighted_strengthening_can_be_opted_in(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4-pair-weighted-strengthening",
        )
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4S",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(mocked_solver.call_count, 1)
        proof_kwargs = mocked_solver.call_args.kwargs
        self.assertTrue(proof_kwargs["mtz_connectivity"])
        self.assertFalse(proof_kwargs["mtz_endpoint_order_cuts"])
        self.assertFalse(proof_kwargs["pair_adjacency_cuts"])
        self.assertTrue(proof_kwargs["resource_arc_pruning"])
        self.assertTrue(proof_kwargs["slot_task_time_pruning"])
        self.assertTrue(proof_kwargs["sortie_slot_position_bounds"])
        self.assertTrue(proof_kwargs["pair_weighted_completion_lb"])
        self.assertTrue(proof_kwargs["pair_energy_infeasible_cut"])
        self.assertTrue(proof_kwargs["pair_time_window_infeasible_cut"])
        self.assertTrue(proof_kwargs["pair_shadow_infeasible_cut"])
        self.assertFalse(proof_kwargs["recharge_aware_slot_bound"])
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4S")
        self.assertEqual(
            result.pricing_payload["compact_final_judge_formulation_profile"],
            "B4V4_strengthened_pair_weighted_final_tail",
        )
        self.assertTrue(
            result.pricing_payload["compact_final_judge_profile_pair_weighted_completion_lb"]
        )
        self.assertFalse(
            result.pricing_payload["compact_final_judge_profile_recharge_aware_slot_bound"]
        )
        self.assertEqual(result.pricing_payload["compact_final_judge_phase_mode"], "proof_only")

    def test_b4_1_v4sr_final_judge_enables_recharge_aware_slot_bound(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4sr-recharge-slot-bound",
        )
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4SR",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(mocked_solver.call_count, 1)
        self.assertTrue(mocked_solver.call_args.kwargs["recharge_aware_slot_bound"])
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4SR")
        self.assertTrue(
            result.pricing_payload["compact_final_judge_profile_recharge_aware_slot_bound"]
        )

    def test_b4_1_v4sc_final_judge_enables_objective_bound_cutoff(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4sc-objective-bound-cutoff",
        )
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OBJECTIVE_BOUND_NO_NEGATIVE",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "EXACT_OBJECTIVE_BOUND_NO_NEGATIVE",
            "best_reduced_cost": None,
            "manual_best_reduced_cost": None,
            "pricing_best_reduced_cost": None,
            "dual_bound": None,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "objective_bound_no_negative_cutoff_enabled": True,
            "objective_bound_no_negative_cutoff_can_certify": True,
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4SC",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(mocked_solver.call_count, 1)
        self.assertTrue(mocked_solver.call_args.kwargs["objective_bound_no_negative_cutoff"])
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4SC")
        self.assertEqual(
            result.pricing_payload["compact_final_judge_formulation_profile"],
            "B4V4_strengthened_pair_weighted_objective_bound_cutoff",
        )
        self.assertTrue(
            result.pricing_payload[
                "compact_final_judge_profile_objective_bound_no_negative_cutoff"
            ]
        )
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)

    def test_b4_1_v4sz_final_judge_enables_zero_capacity_slot_truncation(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4sz-zero-capacity-slot-truncation",
        )
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "zero_capacity_slot_truncation_enabled": True,
            "zero_capacity_slot_truncation_original_slot_count": 5,
            "zero_capacity_slot_truncation_effective_slot_count": 4,
            "zero_capacity_slot_truncation_trimmed_slot_count": 1,
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4SZ",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(mocked_solver.call_count, 1)
        self.assertTrue(mocked_solver.call_args.kwargs["zero_capacity_slot_truncation"])
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4SZ")
        self.assertEqual(
            result.pricing_payload["compact_final_judge_formulation_profile"],
            "B4V4_strengthened_pair_weighted_zero_capacity_slot_truncation",
        )
        self.assertTrue(
            result.pricing_payload[
                "compact_final_judge_profile_zero_capacity_slot_truncation"
            ]
        )
        self.assertTrue(result.pricing_payload["zero_capacity_slot_truncation_enabled"])
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)

    def test_b4_1_v4szcap_final_judge_enables_slot_sequence_capacity_arc_pruning(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4szcap-slot-sequence-capacity-arc-pruning",
        )
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "zero_capacity_slot_truncation_enabled": True,
            "slot_sequence_capacity_arc_pruning_enabled": True,
            "slot_sequence_capacity_arc_pruned_option_count": 3,
            "slot_sequence_capacity_mtz_disabled_slot_count": 2,
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4SZCAP",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(mocked_solver.call_count, 1)
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4SZCAP")
        self.assertTrue(mocked_solver.call_args.kwargs["zero_capacity_slot_truncation"])
        self.assertTrue(mocked_solver.call_args.kwargs["slot_sequence_capacity_arc_pruning"])
        self.assertTrue(
            result.pricing_payload[
                "compact_final_judge_profile_slot_sequence_capacity_arc_pruning"
            ]
        )
        self.assertTrue(result.pricing_payload["slot_sequence_capacity_arc_pruning_enabled"])
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)

    def test_b4_1_v4szpc_final_judge_enables_pair_conflict_capacity_bound(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4szpc-pair-conflict-capacity-bound",
        )
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "zero_capacity_slot_truncation_enabled": True,
            "task_slot_pair_conflict_capacity_bound_requested": True,
            "task_slot_pair_conflict_capacity_bound_enabled": True,
            "task_slot_pair_conflict_capacity_bound_optimal": True,
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4SZPC",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(mocked_solver.call_count, 1)
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4SZPC")
        self.assertTrue(mocked_solver.call_args.kwargs["zero_capacity_slot_truncation"])
        self.assertTrue(mocked_solver.call_args.kwargs["task_slot_pair_conflict_capacity_bound"])
        self.assertTrue(
            result.pricing_payload[
                "compact_final_judge_profile_task_slot_pair_conflict_capacity_bound"
            ]
        )
        self.assertTrue(result.pricing_payload["task_slot_pair_conflict_capacity_bound_enabled"])
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)

    def test_b4_1_v4szw_final_judge_enables_warm_integer_start(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4szw-warm-integer-start",
        )
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "zero_capacity_slot_truncation_enabled": True,
            "single_journey_mip_start_zero_fill_integers": True,
            "single_journey_mip_start_zero_fill_integer_entry_count": 42,
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4SZW",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(mocked_solver.call_count, 1)
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4SZW")
        self.assertTrue(mocked_solver.call_args.kwargs["zero_capacity_slot_truncation"])
        self.assertTrue(mocked_solver.call_args.kwargs["mip_start_zero_fill_integers"])
        self.assertTrue(
            result.pricing_payload[
                "compact_final_judge_profile_mip_start_zero_fill_integers"
            ]
        )
        self.assertTrue(result.pricing_payload["single_journey_mip_start_zero_fill_integers"])
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)

    def test_b4_1_v4sl_final_judge_enables_slot_sequence_capacity_live_bound(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4sl-slot-sequence-live-bound",
        )
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "slot_sequence_capacity_live_bound_enabled": True,
            "slot_sequence_capacity_live_bound_tightened_slot_count": 2,
            "slot_sequence_capacity_live_bound_by_slot": [6, 5, 3],
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4SL",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(mocked_solver.call_count, 1)
        self.assertTrue(mocked_solver.call_args.kwargs["zero_capacity_slot_truncation"])
        self.assertTrue(mocked_solver.call_args.kwargs["slot_sequence_capacity_live_bound"])
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4SL")
        self.assertEqual(
            result.pricing_payload["compact_final_judge_formulation_profile"],
            "B4V4_strengthened_pair_weighted_slot_sequence_live_bound",
        )
        self.assertTrue(
            result.pricing_payload[
                "compact_final_judge_profile_slot_sequence_capacity_live_bound"
            ]
        )
        self.assertTrue(result.pricing_payload["slot_sequence_capacity_live_bound_enabled"])
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)

    def test_b4_1_v4st_final_judge_enables_tight_service_start_bounds(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4st-tight-service-start-bounds",
        )
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "zero_capacity_slot_truncation_enabled": True,
            "tight_service_start_bounds_enabled": True,
            "tight_service_start_bound_count": 15,
            "tight_service_start_bound_min": 12.0,
            "tight_service_start_bound_max": 128.0,
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4ST",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(mocked_solver.call_count, 1)
        self.assertTrue(mocked_solver.call_args.kwargs["zero_capacity_slot_truncation"])
        self.assertTrue(mocked_solver.call_args.kwargs["tight_service_start_bounds"])
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4ST")
        self.assertEqual(
            result.pricing_payload["compact_final_judge_formulation_profile"],
            "B4V4_strengthened_pair_weighted_tight_service_start_bounds",
        )
        self.assertTrue(
            result.pricing_payload[
                "compact_final_judge_profile_tight_service_start_bounds"
            ]
        )
        self.assertTrue(result.pricing_payload["tight_service_start_bounds_enabled"])
        self.assertEqual(result.pricing_payload["tight_service_start_bound_count"], 15)
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)

    def test_b4_1_v4_final_judge_passes_column_pool_mip_start_to_proof(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        duals = JourneyDuals(cover=cover_duals, fleet_limit=0.0)
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4-mip-start",
        )
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        warm_start = min(universe.columns, key=lambda column: manual_journey_reduced_cost(column, duals))
        pool = ColumnPool()
        signature = column_signature_from_journey(warm_start)
        pool.add(BpcColumn(signature=signature, objective=warm_start.objective, payload=warm_start))
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "single_journey_mip_start_enabled": True,
            "single_journey_mip_start_status": "OK",
            "single_journey_mip_start_source": "column_pool_journey",
            "single_journey_mip_start_entry_count": 10,
            "single_journey_mip_start_sortie_count": len(warm_start.sorties),
            "single_journey_mip_start_task_count": len(warm_start.task_set),
            "single_journey_mip_start_objective": warm_start.objective,
            "single_journey_mip_start_reduced_cost": manual_journey_reduced_cost(warm_start, duals),
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    duals,
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                    column_pool=pool,
                )

        self.assertEqual(mocked_solver.call_count, 1)
        self.assertIs(mocked_solver.call_args.kwargs["mip_start_journey"], warm_start)
        self.assertTrue(result.pricing_payload["compact_final_judge_mip_start_from_column_pool"])
        self.assertTrue(result.pricing_payload["single_journey_mip_start_enabled"])
        self.assertEqual(result.pricing_payload["single_journey_mip_start_status"], "OK")
        self.assertEqual(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "single_journey_mip_start_status"
            ],
            "OK",
        )

    def test_b4_1_v4_final_judge_can_pass_mip_start_to_negative_search(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        duals = JourneyDuals(cover=cover_duals, fleet_limit=0.0)
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4-negative-search-mip-start",
        )
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        warm_start = min(universe.columns, key=lambda column: manual_journey_reduced_cost(column, duals))
        pool = ColumnPool()
        signature = column_signature_from_journey(warm_start)
        pool.add(BpcColumn(signature=signature, objective=warm_start.objective, payload=warm_start))
        negative_probe = {
            "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
            "pricing_state": "INCOMPLETE_LIMIT",
            "exact_status": "NOT_SOLVED",
            "best_reduced_cost": None,
            "manual_best_reduced_cost": None,
            "pricing_best_reduced_cost": None,
            "dual_bound": 0.0,
            "negative_found": False,
            "can_certify_no_negative": False,
            "pricing_complete_by_compact_milp": False,
            "single_journey_mip_start_enabled": True,
            "single_journey_mip_start_status": "OK",
            "single_journey_mip_start_source": "column_pool_journey",
            "single_journey_mip_start_entry_count": 10,
            "single_journey_mip_start_sortie_count": len(warm_start.sorties),
            "single_journey_mip_start_task_count": len(warm_start.task_set),
            "single_journey_mip_start_objective": warm_start.objective,
            "single_journey_mip_start_reduced_cost": manual_journey_reduced_cost(warm_start, duals),
            "journeys": tuple(),
        }
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "single_journey_mip_start_enabled": True,
            "single_journey_mip_start_status": "OK",
            "single_journey_mip_start_source": "column_pool_journey",
            "single_journey_mip_start_entry_count": 10,
            "single_journey_mip_start_sortie_count": len(warm_start.sorties),
            "single_journey_mip_start_task_count": len(warm_start.task_set),
            "single_journey_mip_start_objective": warm_start.objective,
            "single_journey_mip_start_reduced_cost": manual_journey_reduced_cost(warm_start, duals),
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4",
                "LUNAR_ICE_COMPACT_NEGATIVE_SEARCH_MIP_START": "1",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                side_effect=(negative_probe, proof_probe),
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    duals,
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                    column_pool=pool,
                )

        self.assertEqual(mocked_solver.call_count, 2)
        self.assertIs(mocked_solver.call_args_list[0].kwargs["mip_start_journey"], warm_start)
        self.assertIs(mocked_solver.call_args_list[1].kwargs["mip_start_journey"], warm_start)
        self.assertTrue(result.pricing_payload["compact_final_judge_mip_start_from_column_pool"])
        self.assertEqual(
            result.pricing_payload["compact_pricing_phase_payloads"]["negative_feasibility_search_1"][
                "single_journey_mip_start_status"
            ],
            "OK",
        )
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)

    def test_b4_1_route_template_pre_harvest_returns_audited_negative(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 1000.0 for task_id in data.task_ids}
        duals = JourneyDuals(cover=cover_duals, fleet_limit=0.0)
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-route-template-pre-harvest",
        )
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        seed_column = next(
            column for column in universe.columns if len(column.task_set) == len(data.task_ids)
        )
        pool = ColumnPool()
        pool.add(
            BpcColumn(
                signature=column_signature_from_journey(seed_column),
                objective=seed_column.objective,
                payload=seed_column,
            )
        )

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST": "1",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_TIME_CAP_SEC": "10",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_DIRECT_TASKS": "5",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_ACTIVE_SEEDS": "4",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_CANDIDATE_SETS": "12",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_TARGET": "2",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                side_effect=AssertionError("compact solver should not run after pre-harvest negative"),
            ):
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    duals,
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                    column_pool=pool,
                    master_view=MasterColumnView(),
                    node_id="root",
                )

        self.assertEqual(result.pricing_state, PricingState.FOUND_NEGATIVE)
        self.assertGreater(len(result.negative_columns), 0)
        self.assertEqual(result.pricing_payload["compact_pricing_phase"], "route_template_pre_harvest")
        self.assertEqual(
            result.pricing_payload["route_template_pre_harvest_status"],
            "ROUTE_TEMPLATE_PRE_HARVEST_FOUND_NEGATIVE",
        )
        self.assertFalse(result.pricing_payload["can_certify_no_negative"])
        self.assertFalse(result.pricing_payload["uses_true_dual_bpc_certificate"])
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], "FRONTIER_BOUND_INCOMPLETE")
        self.assertFalse(result.pricing_payload["route_template_pre_harvest_can_certify_no_negative"])
        self.assertTrue(result.pricing_payload["harvest_manual_rc_audit_pass"])
        self.assertTrue(result.pricing_payload["harvest_pricing_rc_audit_pass"])
        self.assertTrue(result.pricing_payload["harvest_addability_audit_available"])
        self.assertEqual(result.pricing_payload["variable_count"], 0)
        self.assertEqual(result.pricing_payload["constraint_count"], 0)

    def test_b4_1_v4sh_profile_enables_route_template_pre_harvest(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 1000.0 for task_id in data.task_ids}
        duals = JourneyDuals(cover=cover_duals, fleet_limit=0.0)
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4sh-route-template-profile",
        )
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        seed_column = next(
            column for column in universe.columns if len(column.task_set) == len(data.task_ids)
        )
        pool = ColumnPool()
        pool.add(
            BpcColumn(
                signature=column_signature_from_journey(seed_column),
                objective=seed_column.objective,
                payload=seed_column,
            )
        )

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4SH",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST": "",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_TIME_CAP_SEC": "",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_DIRECT_TASKS": "",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_ACTIVE_SEEDS": "",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_CANDIDATE_SETS": "",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_TARGET": "",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                side_effect=AssertionError("V4SH pre-harvest should return before compact proof"),
            ):
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    duals,
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                    column_pool=pool,
                    master_view=MasterColumnView(),
                    node_id="root",
                )

        self.assertEqual(result.pricing_state, PricingState.FOUND_NEGATIVE)
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4SH")
        self.assertTrue(result.pricing_payload["compact_final_judge_profile_route_template_pre_harvest"])
        self.assertEqual(result.pricing_payload["compact_final_judge_profile_route_template_pre_harvest_target"], 1)
        self.assertEqual(
            result.pricing_payload["compact_pricing_phase"],
            "route_template_pre_harvest",
        )
        self.assertEqual(
            result.pricing_payload["route_template_pre_harvest_target"],
            1,
        )
        self.assertEqual(
            result.pricing_payload["route_template_pre_harvest_max_candidate_sets"],
            180,
        )
        self.assertFalse(result.pricing_payload["can_certify_no_negative"])
        self.assertFalse(result.pricing_payload["route_template_pre_harvest_can_certify_no_negative"])
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], "FRONTIER_BOUND_INCOMPLETE")

    def test_b4_1_route_template_pre_harvest_no_column_fallback_disabled_is_incomplete(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.0 for task_id in data.task_ids}
        duals = JourneyDuals(cover=cover_duals, fleet_limit=0.0)
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-route-template-no-fallback",
        )
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        seed_column = next(
            column for column in universe.columns if len(column.task_set) == len(data.task_ids)
        )
        pool = ColumnPool()
        pool.add(
            BpcColumn(
                signature=column_signature_from_journey(seed_column),
                objective=seed_column.objective,
                payload=seed_column,
            )
        )

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST": "1",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_FALLBACK": "0",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_TIME_CAP_SEC": "10",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_DIRECT_TASKS": "5",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_ACTIVE_SEEDS": "4",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_CANDIDATE_SETS": "12",
                "LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_TARGET": "1",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                side_effect=AssertionError("compact solver should not run when fallback is disabled"),
            ):
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    duals,
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                    column_pool=pool,
                    master_view=MasterColumnView(),
                    node_id="root",
                )

        self.assertEqual(result.pricing_state, PricingState.INCOMPLETE_LIMIT)
        self.assertEqual(result.negative_columns, tuple())
        self.assertEqual(result.pricing_payload["compact_pricing_phase"], "route_template_pre_harvest")
        self.assertEqual(
            result.pricing_payload["status"],
            "ROUTE_TEMPLATE_PRE_HARVEST_NO_NEGATIVE_FALLBACK_DISABLED",
        )
        self.assertFalse(result.pricing_payload["can_certify_no_negative"])
        self.assertFalse(result.pricing_payload["uses_true_dual_bpc_certificate"])
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], "FRONTIER_BOUND_INCOMPLETE")
        self.assertFalse(result.pricing_payload["route_template_pre_harvest_fallback_enabled"])

    def test_b4_1_route_template_pre_harvest_expands_seed_neighborhood(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 10.0 - index for index, task_id in enumerate(data.task_ids)},
            fleet_limit=0.0,
        )
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        seed_column = next(
            column for column in universe.columns if len(column.task_set) == len(data.task_ids)
        )
        pool = ColumnPool()
        pool.add(
            BpcColumn(
                signature=column_signature_from_journey(seed_column),
                objective=seed_column.objective,
                payload=seed_column,
            )
        )

        seeds = final_judge_module._route_template_pre_harvest_seed_task_sets(
            data,
            duals,
            CutContext(),
            branch_context=BranchContext(),
            column_pool=pool,
            max_direct_tasks=5,
            max_active_seeds=1,
            neighborhood_enabled=True,
            max_neighborhood_seeds=8,
        )

        self.assertEqual(seeds[0], tuple(sorted(seed_column.task_set)))
        self.assertGreater(len(seeds), 1)
        self.assertTrue(any(len(seed) == len(data.task_ids) - 1 for seed in seeds[1:]))

    def test_b4_1_route_template_pre_harvest_neighborhood_respects_branch_context(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_a, task_b = data.task_ids[:2]
        third_task = data.task_ids[2]
        duals = JourneyDuals(cover={task_id: 1.0 for task_id in data.task_ids}, fleet_limit=0.0)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        seed_column = next(
            column
            for column in universe.columns
            if tuple(sorted(column.task_set)) == tuple(sorted((task_a, task_b, third_task)))
        )
        pool = ColumnPool()
        pool.add(
            BpcColumn(
                signature=column_signature_from_journey(seed_column),
                objective=seed_column.objective,
                payload=seed_column,
            )
        )
        branch = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))

        seeds = final_judge_module._route_template_pre_harvest_seed_task_sets(
            data,
            duals,
            CutContext(),
            branch_context=branch,
            column_pool=pool,
            max_direct_tasks=5,
            max_active_seeds=1,
            neighborhood_enabled=True,
            max_neighborhood_seeds=20,
        )

        for seed in seeds:
            self.assertEqual(str(task_a) in seed, str(task_b) in seed)

    def test_b4_1_compact_final_judge_service_start_depot_travel_lb_is_env_opt_in(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-service-start-lb",
        )
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "service_start_depot_travel_lb_enabled": True,
            "service_start_depot_travel_lb_count": 25,
            "task_to_depot_return_travel_lb_enabled": True,
            "task_to_depot_return_travel_lb_count": 25,
            "pair_route_duration_lb_enabled": True,
            "pair_route_duration_lb_count": 250,
            "pair_weighted_completion_lb_enabled": True,
            "pair_weighted_completion_lb_count": 250,
            "pair_weighted_completion_lb_min": 3.5,
            "pair_weighted_completion_lb_max": 42.0,
            "sortie_slot_position_bounds_enabled": True,
            "sortie_slot_position_bound_count": 14,
            "demand_cover_cut_enabled": True,
            "demand_cover_cut_count": 0,
            "demand_cover_subset_count": 0,
            "single_task_energy_lb_enabled": True,
            "single_task_energy_lb_count": 25,
            "single_task_shadow_lb_enabled": True,
            "single_task_shadow_lb_count": 25,
            "pair_energy_lb_enabled": True,
            "pair_energy_lb_count": 250,
            "pair_energy_lb_exceeds_limit_count": 0,
            "pair_shadow_lb_enabled": True,
            "pair_shadow_lb_count": 250,
            "pair_shadow_lb_exceeds_limit_count": 0,
            "pair_energy_infeasible_cut_enabled": True,
            "pair_energy_infeasible_cut_count": 0,
            "pair_energy_infeasible_pair_count": 0,
            "pair_time_window_infeasible_cut_enabled": True,
            "pair_time_window_infeasible_cut_count": 7,
            "pair_time_window_infeasible_pair_count": 7,
            "pair_time_window_infeasible_margin_min": 0.25,
            "pair_time_window_infeasible_margin_max": 4.0,
            "pair_time_window_precedence_cut_enabled": True,
            "pair_time_window_precedence_cut_count": 9,
            "pair_time_window_precedence_pair_count": 9,
            "pair_time_window_precedence_margin_min": 0.5,
            "pair_time_window_precedence_margin_max": 6.0,
            "triple_time_window_infeasible_cut_enabled": True,
            "triple_time_window_infeasible_cut_count": 15,
            "triple_time_window_infeasible_triple_count": 15,
            "triple_time_window_infeasible_margin_min": 0.75,
            "triple_time_window_infeasible_margin_max": 8.0,
            "quad_time_window_infeasible_cut_enabled": True,
            "quad_time_window_infeasible_cut_count": 20,
            "quad_time_window_infeasible_quad_count": 5,
            "quad_time_window_infeasible_margin_min": 1.25,
            "quad_time_window_infeasible_margin_max": 9.5,
            "pair_shadow_infeasible_cut_enabled": True,
            "pair_shadow_infeasible_cut_count": 0,
            "pair_shadow_infeasible_pair_count": 0,
            "triple_shadow_infeasible_cut_enabled": True,
            "triple_shadow_infeasible_cut_count": 0,
            "triple_shadow_infeasible_triple_count": 0,
            "triple_energy_infeasible_cut_enabled": True,
            "triple_energy_infeasible_cut_count": 0,
            "triple_energy_infeasible_triple_count": 0,
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
                "LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB": "1",
                "LUNAR_ICE_COMPACT_TASK_TO_DEPOT_RETURN_TRAVEL_LB": "1",
                "LUNAR_ICE_COMPACT_PAIR_ROUTE_DURATION_LB": "1",
                "LUNAR_ICE_COMPACT_PAIR_WEIGHTED_COMPLETION_LB": "1",
                "LUNAR_ICE_COMPACT_SORTIE_SLOT_POSITION_BOUNDS": "1",
                "LUNAR_ICE_COMPACT_DEMAND_COVER_CUT": "1",
                "LUNAR_ICE_COMPACT_SINGLE_TASK_ENERGY_LB": "1",
                "LUNAR_ICE_COMPACT_SINGLE_TASK_SHADOW_LB": "1",
                "LUNAR_ICE_COMPACT_PAIR_ENERGY_LB": "1",
                "LUNAR_ICE_COMPACT_PAIR_SHADOW_LB": "1",
                "LUNAR_ICE_COMPACT_PAIR_ENERGY_INFEASIBLE_CUT": "1",
                "LUNAR_ICE_COMPACT_PAIR_TIME_WINDOW_INFEASIBLE_CUT": "1",
                "LUNAR_ICE_COMPACT_PAIR_TIME_WINDOW_PRECEDENCE_CUT": "1",
                "LUNAR_ICE_COMPACT_TRIPLE_TIME_WINDOW_INFEASIBLE_CUT": "1",
                "LUNAR_ICE_COMPACT_QUAD_TIME_WINDOW_INFEASIBLE_CUT": "1",
                "LUNAR_ICE_COMPACT_PAIR_SHADOW_INFEASIBLE_CUT": "1",
                "LUNAR_ICE_COMPACT_TRIPLE_SHADOW_INFEASIBLE_CUT": "1",
                "LUNAR_ICE_COMPACT_TRIPLE_ENERGY_INFEASIBLE_CUT": "1",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(mocked_solver.call_count, 1)
        self.assertTrue(mocked_solver.call_args.kwargs["service_start_depot_travel_lb"])
        self.assertTrue(mocked_solver.call_args.kwargs["task_to_depot_return_travel_lb"])
        self.assertTrue(mocked_solver.call_args.kwargs["pair_route_duration_lb"])
        self.assertTrue(mocked_solver.call_args.kwargs["pair_weighted_completion_lb"])
        self.assertTrue(mocked_solver.call_args.kwargs["sortie_slot_position_bounds"])
        self.assertTrue(mocked_solver.call_args.kwargs["demand_cover_cut"])
        self.assertTrue(mocked_solver.call_args.kwargs["single_task_energy_lb"])
        self.assertTrue(mocked_solver.call_args.kwargs["single_task_shadow_lb"])
        self.assertTrue(mocked_solver.call_args.kwargs["pair_energy_lb"])
        self.assertTrue(mocked_solver.call_args.kwargs["pair_shadow_lb"])
        self.assertTrue(mocked_solver.call_args.kwargs["pair_energy_infeasible_cut"])
        self.assertTrue(mocked_solver.call_args.kwargs["pair_time_window_infeasible_cut"])
        self.assertTrue(mocked_solver.call_args.kwargs["pair_time_window_precedence_cut"])
        self.assertTrue(mocked_solver.call_args.kwargs["triple_time_window_infeasible_cut"])
        self.assertTrue(mocked_solver.call_args.kwargs["quad_time_window_infeasible_cut"])
        self.assertTrue(mocked_solver.call_args.kwargs["pair_shadow_infeasible_cut"])
        self.assertTrue(mocked_solver.call_args.kwargs["triple_shadow_infeasible_cut"])
        self.assertTrue(mocked_solver.call_args.kwargs["triple_energy_infeasible_cut"])
        self.assertTrue(result.pricing_payload["service_start_depot_travel_lb_enabled"])
        self.assertEqual(result.pricing_payload["service_start_depot_travel_lb_count"], 25)
        self.assertTrue(result.pricing_payload["task_to_depot_return_travel_lb_enabled"])
        self.assertEqual(result.pricing_payload["task_to_depot_return_travel_lb_count"], 25)
        self.assertTrue(result.pricing_payload["pair_route_duration_lb_enabled"])
        self.assertEqual(result.pricing_payload["pair_route_duration_lb_count"], 250)
        self.assertTrue(result.pricing_payload["pair_weighted_completion_lb_enabled"])
        self.assertEqual(result.pricing_payload["pair_weighted_completion_lb_count"], 250)
        self.assertEqual(result.pricing_payload["pair_weighted_completion_lb_min"], 3.5)
        self.assertEqual(result.pricing_payload["pair_weighted_completion_lb_max"], 42.0)
        self.assertTrue(result.pricing_payload["sortie_slot_position_bounds_enabled"])
        self.assertEqual(result.pricing_payload["sortie_slot_position_bound_count"], 14)
        self.assertTrue(result.pricing_payload["demand_cover_cut_enabled"])
        self.assertEqual(result.pricing_payload["demand_cover_cut_count"], 0)
        self.assertEqual(result.pricing_payload["demand_cover_subset_count"], 0)
        self.assertTrue(result.pricing_payload["single_task_energy_lb_enabled"])
        self.assertEqual(result.pricing_payload["single_task_energy_lb_count"], 25)
        self.assertTrue(result.pricing_payload["single_task_shadow_lb_enabled"])
        self.assertEqual(result.pricing_payload["single_task_shadow_lb_count"], 25)
        self.assertTrue(result.pricing_payload["pair_energy_lb_enabled"])
        self.assertEqual(result.pricing_payload["pair_energy_lb_count"], 250)
        self.assertEqual(result.pricing_payload["pair_energy_lb_exceeds_limit_count"], 0)
        self.assertTrue(result.pricing_payload["pair_shadow_lb_enabled"])
        self.assertEqual(result.pricing_payload["pair_shadow_lb_count"], 250)
        self.assertEqual(result.pricing_payload["pair_shadow_lb_exceeds_limit_count"], 0)
        self.assertTrue(result.pricing_payload["pair_energy_infeasible_cut_enabled"])
        self.assertEqual(result.pricing_payload["pair_energy_infeasible_cut_count"], 0)
        self.assertEqual(result.pricing_payload["pair_energy_infeasible_pair_count"], 0)
        self.assertTrue(result.pricing_payload["pair_time_window_infeasible_cut_enabled"])
        self.assertEqual(result.pricing_payload["pair_time_window_infeasible_cut_count"], 7)
        self.assertEqual(result.pricing_payload["pair_time_window_infeasible_pair_count"], 7)
        self.assertEqual(result.pricing_payload["pair_time_window_infeasible_margin_min"], 0.25)
        self.assertEqual(result.pricing_payload["pair_time_window_infeasible_margin_max"], 4.0)
        self.assertTrue(result.pricing_payload["pair_time_window_precedence_cut_enabled"])
        self.assertEqual(result.pricing_payload["pair_time_window_precedence_cut_count"], 9)
        self.assertEqual(result.pricing_payload["pair_time_window_precedence_pair_count"], 9)
        self.assertEqual(result.pricing_payload["pair_time_window_precedence_margin_min"], 0.5)
        self.assertEqual(result.pricing_payload["pair_time_window_precedence_margin_max"], 6.0)
        self.assertTrue(result.pricing_payload["triple_time_window_infeasible_cut_enabled"])
        self.assertEqual(result.pricing_payload["triple_time_window_infeasible_cut_count"], 15)
        self.assertEqual(result.pricing_payload["triple_time_window_infeasible_triple_count"], 15)
        self.assertEqual(result.pricing_payload["triple_time_window_infeasible_margin_min"], 0.75)
        self.assertEqual(result.pricing_payload["triple_time_window_infeasible_margin_max"], 8.0)
        self.assertTrue(result.pricing_payload["quad_time_window_infeasible_cut_enabled"])
        self.assertEqual(result.pricing_payload["quad_time_window_infeasible_cut_count"], 20)
        self.assertEqual(result.pricing_payload["quad_time_window_infeasible_quad_count"], 5)
        self.assertEqual(result.pricing_payload["quad_time_window_infeasible_margin_min"], 1.25)
        self.assertEqual(result.pricing_payload["quad_time_window_infeasible_margin_max"], 9.5)
        self.assertTrue(result.pricing_payload["pair_shadow_infeasible_cut_enabled"])
        self.assertEqual(result.pricing_payload["pair_shadow_infeasible_cut_count"], 0)
        self.assertEqual(result.pricing_payload["pair_shadow_infeasible_pair_count"], 0)
        self.assertTrue(result.pricing_payload["triple_shadow_infeasible_cut_enabled"])
        self.assertEqual(result.pricing_payload["triple_shadow_infeasible_cut_count"], 0)
        self.assertEqual(result.pricing_payload["triple_shadow_infeasible_triple_count"], 0)
        self.assertTrue(result.pricing_payload["triple_energy_infeasible_cut_enabled"])
        self.assertEqual(result.pricing_payload["triple_energy_infeasible_cut_count"], 0)
        self.assertEqual(result.pricing_payload["triple_energy_infeasible_triple_count"], 0)
        self.assertTrue(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "service_start_depot_travel_lb_enabled"
            ]
        )
        self.assertTrue(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "pair_weighted_completion_lb_enabled"
            ]
        )
        self.assertEqual(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "pair_weighted_completion_lb_count"
            ],
            250,
        )
        self.assertTrue(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "triple_time_window_infeasible_cut_enabled"
            ]
        )
        self.assertEqual(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "triple_time_window_infeasible_cut_count"
            ],
            15,
        )
        self.assertTrue(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "quad_time_window_infeasible_cut_enabled"
            ]
        )
        self.assertEqual(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "quad_time_window_infeasible_cut_count"
            ],
            20,
        )
        self.assertTrue(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "task_to_depot_return_travel_lb_enabled"
            ]
        )
        self.assertTrue(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "pair_route_duration_lb_enabled"
            ]
        )
        self.assertTrue(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "demand_cover_cut_enabled"
            ]
        )
        self.assertTrue(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "pair_energy_lb_enabled"
            ]
        )
        self.assertTrue(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "pair_shadow_lb_enabled"
            ]
        )
        self.assertTrue(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "pair_energy_infeasible_cut_enabled"
            ]
        )
        self.assertTrue(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "pair_time_window_infeasible_cut_enabled"
            ]
        )
        self.assertTrue(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "pair_time_window_precedence_cut_enabled"
            ]
        )
        self.assertTrue(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "pair_shadow_infeasible_cut_enabled"
            ]
        )
        self.assertTrue(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "triple_shadow_infeasible_cut_enabled"
            ]
        )
        self.assertTrue(
            result.pricing_payload["compact_pricing_phase_payloads"]["optimization_proof"][
                "triple_energy_infeasible_cut_enabled"
            ]
        )

    def test_b4_1_compact_final_judge_proof_only_skips_negative_discovery(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-proof-only",
        )
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
            "pricing_state": "INCOMPLETE_LIMIT",
            "exact_status": "NOT_SOLVED",
            "best_reduced_cost": 0.02,
            "dual_bound": -0.03,
            "can_certify_no_negative": False,
            "pricing_rc_audit_pass": True,
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(mocked_solver.call_count, 1)
        proof_kwargs = mocked_solver.call_args.kwargs
        self.assertFalse(proof_kwargs.get("negative_feasibility_search", False))
        self.assertTrue(proof_kwargs["mtz_connectivity"])
        self.assertTrue(proof_kwargs["mtz_endpoint_order_cuts"])
        self.assertTrue(proof_kwargs["pair_adjacency_cuts"])
        self.assertTrue(proof_kwargs["latest_service_start_slot_bound"])
        self.assertTrue(proof_kwargs["time_window_arc_pruning"])
        self.assertFalse(proof_kwargs["slot_arc_support_pruning"])
        self.assertFalse(proof_kwargs["dual_task_slot_full_space_lower_bound"])
        self.assertTrue(proof_kwargs["dual_task_slot_full_space_lb_early_stop_on_negative"])
        self.assertEqual(result.pricing_state, PricingState.INCOMPLETE_LIMIT)
        self.assertEqual(result.pricing_payload["compact_pricing_phase"], "optimization_proof")
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4")
        self.assertEqual(result.pricing_payload["compact_final_judge_phase_mode"], "proof_only")
        self.assertTrue(result.pricing_payload["negative_feasibility_skipped_for_proof_only"])
        self.assertNotIn("negative_feasibility_search_1", result.pricing_payload["compact_pricing_phase_payloads"])
        self.assertIn("optimization_proof", result.pricing_payload["compact_pricing_phase_payloads"])
        self.assertFalse(result.pricing_payload["can_certify_no_negative"])

    def test_b4_1_compact_final_judge_feasibility_proof_can_certify_full_space(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-feasibility-proof",
        )
        infeasible_probe = {
            "status": "COMPACT_HIGHS_PRICING_INFEASIBLE_NO_NEGATIVE",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "EXACT_NEGATIVE_FEASIBILITY_INFEASIBLE",
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "forbidden_arc_pattern_count": 0,
            "forbidden_task_set_count": 0,
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "feasibility_proof_only",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=infeasible_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        self.assertEqual(mocked_solver.call_count, 1)
        kwargs = mocked_solver.call_args.kwargs
        self.assertTrue(kwargs["negative_feasibility_search"])
        self.assertEqual(kwargs.get("forbidden_arc_patterns"), None)
        self.assertEqual(kwargs.get("forbidden_task_sets"), None)
        self.assertTrue(kwargs["mtz_connectivity"])
        self.assertTrue(kwargs["mtz_endpoint_order_cuts"])
        self.assertTrue(kwargs["pair_adjacency_cuts"])
        self.assertTrue(kwargs["latest_service_start_slot_bound"])
        self.assertTrue(kwargs["time_window_arc_pruning"])
        self.assertFalse(kwargs["slot_arc_support_pruning"])
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)
        self.assertEqual(result.pricing_payload["compact_pricing_phase"], "negative_feasibility_proof")
        self.assertEqual(result.pricing_payload["compact_final_judge_phase_mode"], "feasibility_proof_only")
        self.assertTrue(result.pricing_payload["negative_feasibility_full_space_proof_attempted"])
        self.assertTrue(result.pricing_payload["negative_feasibility_full_space_proof_can_certify"])
        self.assertTrue(result.pricing_payload["can_certify_no_negative"])
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], "EXHAUSTIVE_NO_NEGATIVE")
        self.assertIn("negative_feasibility_proof", result.pricing_payload["compact_pricing_phase_payloads"])

    def test_b4_1_compact_final_judge_v4szt_profile_enables_tight_big_m(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4szt-profile",
        )
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "EXACT_PRICING_OPTIMAL",
            "best_reduced_cost": 0.02,
            "dual_bound": 0.02,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4SZT",
                "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE": "proof_only",
            },
        ):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        kwargs = mocked_solver.call_args.kwargs
        self.assertTrue(kwargs["zero_capacity_slot_truncation"])
        self.assertTrue(kwargs["tight_service_start_bounds"])
        self.assertTrue(kwargs["tight_time_arc_big_m"])
        self.assertFalse(kwargs["slot_service_start_y_lower_bound"])
        self.assertTrue(kwargs["pair_weighted_completion_lb"])
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4SZT")
        self.assertTrue(result.pricing_payload["compact_final_judge_profile_tight_time_arc_big_m"])
        self.assertFalse(
            result.pricing_payload[
                "compact_final_judge_profile_slot_service_start_y_lower_bound"
            ]
        )
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)

    def test_b4_1_compact_final_judge_v4sztp_profile_defaults_to_proof_only(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-v4sztp-profile",
        )
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "EXACT_PRICING_OPTIMAL",
            "best_reduced_cost": 0.02,
            "dual_bound": 0.02,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "journeys": tuple(),
        }

        with patch.dict(
            "os.environ",
            {"LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE": "V4SZTP"},
            clear=False,
        ):
            os.environ.pop("LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE", None)
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                return_value=proof_probe,
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                )

        kwargs = mocked_solver.call_args.kwargs
        self.assertTrue(kwargs["tight_time_arc_big_m"])
        self.assertTrue(kwargs["zero_capacity_slot_truncation"])
        self.assertEqual(result.pricing_payload["compact_final_judge_profile"], "V4SZTP")
        self.assertEqual(
            result.pricing_payload["compact_final_judge_profile_phase_mode_default"],
            "proof_only",
        )
        self.assertEqual(result.pricing_payload["compact_final_judge_phase_mode"], "proof_only")
        self.assertEqual(result.pricing_payload["compact_pricing_phase"], "optimization_proof")
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)

    def test_b4_1_compact_final_judge_downgrades_unproven_frontier_no_negative(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        cover_duals = {task_id: 0.05 * (index + 1) for index, task_id in enumerate(data.task_ids)}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-frontier-downgrade",
        )
        result = final_judge_module._compact_final_judge_result(
            data,
            context=context,
            branch_context=BranchContext(),
            cut_context=CutContext(),
            result={
                "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                "pricing_state": "INCOMPLETE_LIMIT",
                "exact_status": "NOT_SOLVED",
                "pricing_proof_kind": "FRONTIER_BOUND_NO_NEGATIVE",
                "global_remaining_rc_lb": 0.1,
                "global_remaining_rc_lb_valid": True,
                "global_remaining_rc_lb_coverage_complete": True,
                "frontier_region_count": 1,
                "frontier_unsupported_region_count": 0,
                "can_certify_no_negative": False,
                "pricing_rc_audit_pass": True,
                "journeys": tuple(),
            },
            state=PricingState.INCOMPLETE_LIMIT,
            negative_columns=tuple(),
            can_certify=False,
            started_at=0.0,
            phase="optimization_proof",
            phase_payloads={},
            phase_mode="harvest_then_proof",
        )

        self.assertEqual(result.pricing_state, PricingState.INCOMPLETE_LIMIT)
        self.assertFalse(result.pricing_payload["can_certify_no_negative"])
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], "FRONTIER_BOUND_INCOMPLETE")
        self.assertFalse(result.pricing_payload["global_remaining_rc_lb_coverage_complete"])
        self.assertGreaterEqual(result.pricing_payload["frontier_unsupported_region_count"], 1)

    def test_b4_1_final_judge_no_addable_harvest_falls_through_to_proof(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duplicate = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns[0]
        pool = ColumnPool()
        view = MasterColumnView()
        duplicate_bpc = BpcColumn(
            signature=column_signature_from_journey(duplicate),
            objective=duplicate.objective,
            payload=duplicate,
        )
        pool.add(duplicate_bpc)
        view.add_from_pool(duplicate_bpc, node_id="root", pool=pool)
        cover_duals = {task_id: 1000.0 for task_id in data.task_ids}
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            dual_fingerprint="b4-1-no-addable-harvest",
        )
        negative_probe = {
            "status": "COMPACT_HIGHS_PRICING_FOUND_NEGATIVE",
            "pricing_state": "FOUND_NEGATIVE",
            "exact_status": "NOT_SOLVED",
            "negative_found": True,
            "can_certify_no_negative": False,
            "pricing_rc_audit_pass": True,
            "journeys": (duplicate,),
        }
        proof_probe = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "best_reduced_cost": 0.1,
            "manual_best_reduced_cost": 0.1,
            "pricing_best_reduced_cost": 0.1,
            "dual_bound": 0.1,
            "can_certify_no_negative": True,
            "pricing_rc_audit_pass": True,
            "pricing_complete_by_compact_milp": True,
            "journeys": tuple(),
        }

        with patch.dict("os.environ", {"LUNAR_ICE_COMPACT_NEGATIVE_BATCH_TARGET": "1"}):
            with patch.object(
                final_judge_module,
                "solve_highs_compact_single_journey_pricing",
                side_effect=(negative_probe, proof_probe),
            ) as mocked_solver:
                result = _run_compact_single_journey_pricing_final_judge(
                    data,
                    JourneyDuals(cover=cover_duals, fleet_limit=0.0),
                    context=context,
                    branch_context=BranchContext(),
                    cut_context=CutContext(),
                    negative_eps=1.0e-6,
                    wall_time_limit_sec=30.0,
                    column_pool=pool,
                    master_view=view,
                    node_id="root",
                    active_task_sets={frozenset(duplicate.task_set)},
                )

        self.assertEqual(mocked_solver.call_count, 2)
        self.assertTrue(mocked_solver.call_args_list[0].kwargs["negative_feasibility_search"])
        self.assertFalse(mocked_solver.call_args_list[1].kwargs.get("negative_feasibility_search", False))
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)
        self.assertEqual(result.negative_columns, tuple())
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], "EXHAUSTIVE_NO_NEGATIVE")

    def test_compact_reference_warm_start_repairs_shifted_sortie_start_times(self) -> None:
        instance = generate_instance(20, seed=829001, index=1)
        reference_solution = json.loads(json.dumps(instance["reference_solution"]))
        journey = next(row for row in reference_solution["journeys"] if len(row.get("sorties", [])) >= 2)
        journey["sorties"][1]["start_time"] = 0.0
        data = load_lunar_ice_data(instance)
        schedule, failure = gurobi_compact_module._build_reference_warm_start_schedule(
            data,
            tasks=tuple(data.task_ids),
            reference_solution=reference_solution,
            path_type_cache=journey_driver_module._nondominated_path_type_cache(data),
            vehicle_count=data.fleet_size,
            sortie_slots=len(data.task_ids),
        )

        self.assertEqual(failure, "")
        self.assertIsNotNone(schedule)
        repaired_journey = next(row for row in schedule if len(row) >= 2)
        self.assertGreaterEqual(repaired_journey[1].start_time, repaired_journey[0].end_time)
        covered = {task_id for sorties in schedule for sortie in sorties for task_id in sortie.tasks}
        self.assertEqual(covered, set(data.task_ids))

    def test_direct_baseline_time_limit_fails_closed(self) -> None:
        instance = generate_instance(10, seed=729001, index=1)
        data = load_lunar_ice_data(instance)
        direct = solve_direct_journey_baseline(data, max_exact_tasks=10, wall_time_limit_sec=0.0)

        self.assertEqual(direct.status, "DIRECT_DP_TIME_LIMIT")
        self.assertEqual(direct.exact_status, "NOT_SOLVED")
        self.assertEqual(direct.certificate_scope, "FEASIBLE_INCUMBENT_ONLY")
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

        self.assertEqual(direct.status, "DIRECT_DP_TIME_LIMIT")
        self.assertEqual(direct.exact_status, "NOT_SOLVED")
        self.assertEqual(direct.certificate_scope, "FEASIBLE_INCUMBENT_ONLY")
        self.assertIsNone(direct.objective)
        self.assertFalse(direct.journeys)
        self.assertEqual(direct.generated_journey_count, 7)
        self.assertEqual(direct.generated_sortie_count, 11)
        self.assertEqual(direct.route_template_count, 13)
        self.assertEqual(direct.pareto_label_count, 17)
        self.assertIn("journey_label_dp", direct.note)
        self.assertIn("diagnostic only", direct.note)

    def test_direct_sortie_generation_can_be_restricted_to_remaining_tasks(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_to_bit = journey_driver_module._task_to_bit_mapping(TaskIndexMap(data.task_ids))
        full_mask = journey_driver_module._full_task_mask(data)
        served_bit = task_to_bit[data.task_ids[0]]
        remaining_mask = full_mask ^ served_bit
        path_type_cache = journey_driver_module._nondominated_path_type_cache(data)

        full_candidates, _, _, _ = journey_driver_module._direct_sortie_candidates_from_start(
            data,
            task_to_bit,
            remaining_mask=full_mask,
            start_time=0.0,
            path_type_cache=path_type_cache,
        )
        remaining_candidates, _, _, _ = journey_driver_module._direct_sortie_candidates_from_start(
            data,
            task_to_bit,
            remaining_mask=remaining_mask,
            start_time=0.0,
            path_type_cache=path_type_cache,
        )

        filtered = [candidate for candidate in full_candidates if candidate.task_mask & served_bit == 0]
        full_by_signature = {
            (
                candidate.task_mask,
                candidate.sortie.tasks,
                tuple(leg.path_type for leg in candidate.sortie.legs),
                candidate.sortie.end_time,
                candidate.base_cost,
            )
            for candidate in filtered
        }
        remaining_by_signature = {
            (
                candidate.task_mask,
                candidate.sortie.tasks,
                tuple(leg.path_type for leg in candidate.sortie.legs),
                candidate.sortie.end_time,
                candidate.base_cost,
            )
            for candidate in remaining_candidates
        }
        self.assertEqual(remaining_by_signature, full_by_signature)

    def test_path_option_dominance_keeps_shorter_distance_tradeoff(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        source, target = next(
            (source, target)
            for (source, target), options in data.arcs.items()
            if options["low_time"].travel_time_min <= options["low_energy"].travel_time_min + 1.0e-9
        )
        low_time = data.arcs[(source, target)]["low_time"]
        low_energy = data.arcs[(source, target)]["low_energy"]
        patched = json.loads(json.dumps(instance))
        for edge in patched["logical_graph"]["edges"]:
            if str(edge["from"]) == str(source) and str(edge["to"]) == str(target):
                for option in edge["path_options"]:
                    if option["path_type"] == "low_time":
                        option["travel_time_min"] = low_energy.travel_time_min
                        option["energy_proxy"] = low_energy.energy_proxy
                        option["risk_integral"] = low_energy.risk_integral
                        option["shadow_exposure_min"] = low_energy.shadow_exposure_min
                        option["path_distance_km"] = max(0.0, low_energy.distance_km - 1.0)
                    elif option["path_type"] == "low_energy":
                        option["travel_time_min"] = low_energy.travel_time_min
                        option["energy_proxy"] = low_energy.energy_proxy
                        option["risk_integral"] = low_energy.risk_integral
                        option["shadow_exposure_min"] = low_energy.shadow_exposure_min
                        option["path_distance_km"] = low_energy.distance_km
                break
        patched_data = load_lunar_ice_data(patched)

        kept = journey_driver_module._nondominated_path_types(patched_data, source, target)

        self.assertIn("low_time", kept)
        self.assertNotIn("low_energy", kept)

    def test_time_aware_return_lower_bound_stays_below_reference_upper_bound(self) -> None:
        instance = generate_instance(10, seed=729001, index=1)
        data = load_lunar_ice_data(instance)
        full_mask = journey_driver_module._full_task_mask(data)
        task_visit = journey_driver_module._remaining_task_visit_lower_bound_fn(data)
        return_lb = journey_driver_module._remaining_return_path_lower_bound_fn(data)
        endpoint_lb = journey_driver_module._remaining_endpoint_path_lower_bound_fn(data)
        reference = journey_driver_module._reference_solution_upper_bound(data)

        self.assertIsNotNone(reference)
        root_lb = task_visit(full_mask, 0.0) + return_lb(full_mask)
        endpoint_root_lb = task_visit(full_mask, 0.0) + endpoint_lb(full_mask)
        delayed_lb = task_visit(full_mask, 120.0) + return_lb(full_mask)

        self.assertGreaterEqual(delayed_lb, root_lb - 1.0e-9)
        self.assertGreaterEqual(endpoint_root_lb, root_lb - 1.0e-9)
        self.assertLessEqual(root_lb, reference.objective + 1.0e-6)
        self.assertLessEqual(endpoint_root_lb, reference.objective + 1.0e-6)

    def test_partition_cover_dual_lower_bound_is_column_feasible(self) -> None:
        cost_by_mask = {
            0b001: 3.0,
            0b010: 4.0,
            0b100: 5.0,
            0b011: 6.0,
            0b110: 8.0,
            0b111: 12.0,
        }
        masks_by_required_bit: dict[int, list[int]] = {}
        for mask in cost_by_mask:
            bits = mask
            while bits:
                bit = bits & -bits
                bits -= bit
                masks_by_required_bit.setdefault(bit, []).append(mask)

        lower_bound = journey_driver_module._remaining_cover_dual_lower_bound_fn(
            cost_by_mask,
            masks_by_required_bit,
            task_count=3,
        )

        self.assertGreater(lower_bound(0b111), 0.0)
        for mask, cost in cost_by_mask.items():
            self.assertLessEqual(lower_bound(mask), cost + 1.0e-6)

    def test_partition_cardinality_lower_bound_is_relaxed_cover_bound(self) -> None:
        cost_by_mask = {
            0b001: 3.0,
            0b010: 4.0,
            0b100: 5.0,
            0b011: 6.0,
            0b110: 8.0,
            0b111: 12.0,
        }
        lower_bound = journey_driver_module._remaining_cardinality_lower_bound_fn(
            cost_by_mask,
            task_count=3,
            max_slots=2,
        )

        feasible_cover_cost = cost_by_mask[0b001] + cost_by_mask[0b110]
        self.assertLessEqual(lower_bound(0b111, 2), feasible_cover_cost + 1.0e-6)
        self.assertGreaterEqual(lower_bound(0b111, 1), lower_bound(0b111, 2) - 1.0e-6)

    def test_partition_lp_cover_lower_bound_is_column_feasible(self) -> None:
        cost_by_mask = {
            0b001: 3.0,
            0b010: 4.0,
            0b100: 5.0,
            0b011: 6.0,
            0b110: 8.0,
            0b111: 12.0,
        }
        lower_bound = journey_driver_module._remaining_lp_cover_lower_bound_fn(
            cost_by_mask,
            task_count=3,
            max_rounds=4,
        )

        self.assertGreater(lower_bound(0b111), 0.0)
        for mask, cost in cost_by_mask.items():
            self.assertLessEqual(lower_bound(mask), cost + 1.0e-6)

    def test_fallback_reporting_prefers_direct_timeout_workload(self) -> None:
        direct = JourneyBaselineResult(
            status="DIRECT_DP_TIME_LIMIT",
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

    def test_subset_row_coefficient_overlap_floor_divisor(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        journey = solve_small_journey_baseline(data).journeys[0]
        tasks = tuple(sorted(journey.task_set))[:3]
        cut = subset_row_cut("sri_floor", tasks, divisor=2)

        self.assertEqual(cut.coefficient(journey), 1.0)

    def test_subset_row_rhs_floor_size_divisor(self) -> None:
        cut = subset_row_cut("sri_rhs", ("a", "b", "c"), divisor=2)

        self.assertEqual(cut.rhs, 1.0)

    def test_cut_coefficients_for_journey_stable_order(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        journey = solve_small_journey_baseline(data).journeys[0]
        tasks = tuple(sorted(journey.task_set))[:3]
        context = CutContext(
            (
                subset_row_cut("z_cut", tasks, divisor=2),
                subset_row_cut("a_cut", tasks, divisor=2),
            )
        )

        first = cut_coefficients_for_journey(journey, context)
        second = cut_coefficients_for_journey(journey, cut_context_from_payload(context.to_payload()))

        self.assertEqual(first, second)

    def test_cut_coefficient_vector_hash_changes_when_cut_active(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        journey = solve_small_journey_baseline(data).journeys[0]
        tasks = tuple(sorted(journey.task_set))[:3]

        self.assertEqual(cut_coefficient_vector_hash(journey, CutContext()), "")
        self.assertNotEqual(
            cut_coefficient_vector_hash(journey, CutContext((subset_row_cut("sri_hash", tasks),))),
            "",
        )

    def test_manual_rc_with_subset_row_cut_matches_pricing_rc(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        journey = solve_small_journey_baseline(data).journeys[0]
        tasks = tuple(sorted(journey.task_set))[:3]
        context = CutContext((subset_row_cut("sri_rc", tasks),))
        duals = JourneyDuals(cover={}, fleet_limit=0.0, cuts={"sri_rc": -0.5})
        manual = manual_journey_reduced_cost(journey, duals, cut_coefficients=context.coefficients_for(journey))

        audit = audit_cut_reduced_cost_consistency(
            (journey,),
            duals,
            context,
            {"best_reduced_cost": manual},
        )

        self.assertTrue(audit["manual_rc_cut_consistency_pass"])
        self.assertTrue(audit["manual_rc_with_cuts_matches_pricing_rc"])

    def test_cut_dual_sign_for_subset_row_is_nonpositive(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        journey = solve_small_journey_baseline(data).journeys[0]
        tasks = tuple(sorted(journey.task_set))[:3]
        context = CutContext((subset_row_cut("sri_sign", tasks),))
        duals = JourneyDuals(cover={}, fleet_limit=0.0, cuts={"sri_sign": -1.0})
        manual = manual_journey_reduced_cost(journey, duals, cut_coefficients=context.coefficients_for(journey))

        audit = audit_cut_reduced_cost_consistency((journey,), duals, context, {"best_reduced_cost": manual})

        self.assertTrue(audit["cut_dual_sign_audit_pass"])
        self.assertEqual(audit["cut_dual_sign_audit"]["rows"][0]["expected_sign"], "<= 0")

    def test_cut_context_empty_does_not_change_rc(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        journey = solve_small_journey_baseline(data).journeys[0]
        duals = JourneyDuals(cover={}, fleet_limit=0.0, cuts={})

        self.assertEqual(
            manual_journey_reduced_cost(journey, duals),
            manual_journey_reduced_cost(journey, duals, cut_coefficients=CutContext().coefficients_for(journey)),
        )

    def test_live_cut_fails_closed_when_pricing_audit_missing(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        journey = solve_small_journey_baseline(data).journeys[0]
        tasks = tuple(sorted(journey.task_set))[:3]
        context = CutContext((subset_row_cut("sri_bad_pricing", tasks),))
        duals = JourneyDuals(cover={}, fleet_limit=0.0, cuts={"sri_bad_pricing": -0.5})
        manual = manual_journey_reduced_cost(journey, duals, cut_coefficients=context.coefficients_for(journey))

        audit = audit_cut_reduced_cost_consistency(
            (journey,),
            duals,
            context,
            {"best_reduced_cost": manual + 1.0},
        )

        self.assertFalse(audit["manual_rc_cut_consistency_pass"])
        self.assertFalse(audit["manual_rc_with_cuts_matches_pricing_rc"])

    def test_cut_aware_signature_includes_cut_hash(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        journey = solve_small_journey_baseline(data).journeys[0]
        tasks = tuple(sorted(journey.task_set))[:3]
        signature = cut_aware_column_signature_from_journey(
            journey,
            cut_context=CutContext((subset_row_cut("sri_signature", tasks),)),
        )

        self.assertTrue(signature.cut_coefficient_vector_hash)

    def test_task_set_dominance_not_enabled_under_active_resource_sensitive_cut(self) -> None:
        with self.assertRaises(ValueError):
            CutDefinition("resource_sensitive", "resource_profile", tasks=("a", "b"), rhs=1.0)

    def test_completion_bound_pruning_disabled_under_active_cut(self) -> None:
        policy = build_completion_bound_tail_policy(pruning_opt_in=True, cut_context_active=True)

        self.assertFalse(policy["pruning_enabled"])
        self.assertTrue(policy["cut_context_active"])
        self.assertFalse(policy["can_certify_no_negative"])

    def test_fleet_lower_bound_cut_diagnostic_only(self) -> None:
        report = build_cut_dominance_compatibility_report(
            CutContext((fleet_lower_bound_cut("fleet_diag", min_vehicles=1),))
        )

        self.assertFalse(report["valid"])
        self.assertTrue(report["rows"][0]["diagnostic_only"])
        self.assertFalse(report["rows"][0]["live_supported"])

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
        self.assertIn("max_violation", probe)
        self.assertIn("mean_violation", probe)
        self.assertIn("violated_subset_size_histogram", probe)
        self.assertIn("affected_column_count", probe)
        self.assertIn("active_support_overlap", probe)
        top = probe["subset_candidates"][0]
        self.assertEqual(top["cut_kind"], "subset_row")
        self.assertEqual(top["sense"], "<=")
        self.assertEqual(top["coefficient_dependency"], "task_set")
        self.assertTrue(top["pricing_supported"])
        self.assertFalse(top["completion_bound_supported"])
        self.assertTrue(top["dominance_compatible"])
        self.assertIn("coefficient_vector_hash", top)
        self.assertIn("would_bind_on_current_rmp", top)
        self.assertIn("would_change_dual_support", top)

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
        self.assertFalse(forced_round["restricted_pricing_claimed_no_negative"])
        self.assertEqual(forced_round["selected_cut_diagnostics"][0]["cut_kind"], "subset_row")

    def test_b4_cut_formulation_runner_writes_diagnostic_artifacts(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        report = run_b4_cut_formulation_ablation(
            [instance],
            modes=(B4A_MODE,),
            max_direct_tasks=5,
            max_rounds=8,
            matrix_group="smoke",
        )

        self.assertEqual(report["schema_version"], "lunar_ice_bpc.b4_cut_formulation_ablation.v1")
        self.assertEqual(report["row_count"], 1)
        row = report["rows"][0]
        self.assertEqual(row["mode"], B4A_MODE)
        self.assertEqual(row["cut_probe_status"], "CUT_PROBE_READY")
        self.assertGreaterEqual(row["cut_candidate_count"], 1)
        self.assertFalse(row["diagnostic_lower_bound_official"])
        self.assertFalse(row["diagnostic_can_certify"])
        self.assertEqual(report["redlines"]["restricted_pricing_claimed_no_negative_count"], 0)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            write_b4_cut_formulation_artifacts(
                report,
                rows_csv=out / "b4_cut_rows.csv",
                summary_json=out / "b4_cut_summary.json",
                report_md=out / "b4_cut_report_zh.md",
            )
            with (out / "b4_cut_rows.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["mode"], B4A_MODE)
            summary = json.loads((out / "b4_cut_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["row_count"], 1)
            self.assertIn("B4 Cut/Formulation", (out / "b4_cut_report_zh.md").read_text(encoding="utf-8"))

    def test_b4_diagnostic_does_not_change_certificate_scope(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b4 = solve_b4_cut_formulation_baseline(data, max_direct_tasks=5, max_rounds=8)

        self.assertFalse(b4["cut_rows_active"])
        self.assertEqual(b4["b3_ablation"]["certificate_scope_diff_vs_B3"], "")

    def test_5_scale_b3b_objective_unchanged_with_b4a(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b4 = solve_b4_cut_formulation_baseline(data, max_direct_tasks=5, max_rounds=8)

        self.assertTrue(b4["final_integer_optimum_unchanged_vs_B3"])
        self.assertEqual(b4["b3_ablation"]["objective_diff_vs_B3"], 0.0)

    def test_10_scale_b3b_objective_unchanged_with_b4a(self) -> None:
        instance = generate_instance(10, seed=729101, index=1)
        data = load_lunar_ice_data(instance)
        b4 = solve_b4_cut_formulation_baseline(data, max_direct_tasks=10, max_rounds=8)

        self.assertTrue(b4["final_integer_optimum_unchanged_vs_B3"])
        self.assertEqual(b4["b3_ablation"]["objective_diff_vs_B3"], 0.0)

    def test_20_scale_b3b_objective_unchanged_with_b4a(self) -> None:
        instance = generate_instance(20, seed=829001, index=1)
        data = load_lunar_ice_data(instance)
        b4 = solve_b4_cut_formulation_baseline(data, max_direct_tasks=20, max_rounds=8)

        self.assertTrue(b4["rmp_memory_precheck_failed"])
        self.assertFalse(b4["uses_true_dual_bpc_certificate"])
        self.assertFalse(b4["restricted_pool_cut_diagnostic"]["can_certify"])

    def test_b4b_live_subset_row_no_regression_on_smoke(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b4 = solve_b4_cut_formulation_baseline(
            data,
            max_direct_tasks=5,
            max_rounds=8,
            live_subset_rows=True,
            max_live_cuts=1,
            add_violated_only=False,
        )

        self.assertEqual(b4["certificate_scope"], "BPC_TREE_OPTIMAL")
        self.assertTrue(b4["final_integer_optimum_unchanged_vs_B3"])
        self.assertTrue(b4["cut_reduced_cost_audit"]["manual_rc_cut_consistency_pass"])

    def test_b4_pricing_formulation_diagnostic_from_probe_json_keeps_certificate_boundary(self) -> None:
        payload = {
            "instance_id": "lunar_ice_sp50_030_001_seed929001",
            "pricing_round_count": 1,
            "history": [
                {
                    "round": 1,
                    "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                    "exact_status": "NOT_SOLVED",
                    "best_reduced_cost": -0.01,
                    "dual_bound": -0.02,
                    "mip_gap": 1.0,
                    "negative_column_count": 1,
                    "added_column_count": 1,
                    "active_column_count": 294,
                    "pool_column_count": 296,
                    "wall_time_sec": 12.5,
                    "can_certify_no_negative": False,
                    "pricing_complete_by_compact_milp": False,
                    "negative_feasibility_search_enabled": False,
                    "mtz_endpoint_order_cuts_enabled": True,
                    "mtz_endpoint_order_cut_count": 10,
                    "pair_adjacency_cuts_enabled": True,
                    "pair_adjacency_cut_count": 20,
                    "sortie_slots_per_journey": 7,
                    "sortie_slot_bound_source": "latest_service_start_min_active_sortie_duration_bound",
                    "sortie_slot_horizon_count_bound": 10,
                    "sortie_slot_latest_start_count_bound": 7,
                    "time_window_arc_pruning_enabled": True,
                    "time_window_arc_option_count": 100,
                    "time_window_impossible_arc_option_count": 30,
                    "variable_count": 1000,
                    "constraint_count": 2000,
                }
            ],
            "final_judge": {
                "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                "exact_status": "NOT_SOLVED",
                "dual_bound": -0.02,
                "can_certify_no_negative": False,
                "negative_feasibility_search_enabled": False,
            },
            "merged_replay_column": {
                "added": True,
                "replay_best_reduced_cost": -0.01,
                "replay_dual_bound": -0.02,
                "after_active_column_count": 297,
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "probe.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = run_b4_pricing_formulation_diagnostic_from_json([path])
            self.assertEqual(report["schema_version"], "lunar_ice_bpc.b4_pricing_formulation_diagnostic.v1")
            self.assertGreaterEqual(report["row_count"], 2)
            self.assertEqual(report["redlines"]["positive_incumbent_rc_claimed_certificate_count"], 0)
            self.assertTrue(report["acceptance"]["b4_pricing_formulation_diagnostic_accepted"])
            self.assertEqual(report["acceptance"]["no_negative_certified_row_count"], 0)
            out = Path(tmp) / "out"
            write_b4_pricing_formulation_artifacts(
                report,
                rows_csv=out / "b4_pricing_rows.csv",
                summary_json=out / "b4_pricing_summary.json",
                report_md=out / "b4_pricing_report_zh.md",
            )
            with (out / "b4_pricing_rows.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["variant"], "V4_combined_endpoint_pair_latest_start_time_window")
            self.assertIn("B4C/B4D", (out / "b4_pricing_report_zh.md").read_text(encoding="utf-8"))

    def test_b4_pricing_formulation_diagnostic_from_replay_json_honors_explicit_variant(self) -> None:
        payload = {
            "schema_version": "lunar_ice_bpc.compact_pricing_replay.v1",
            "instance_id": "diagnostic",
            "selected_history_round": 3,
            "replay_config": {
                "b4_variant": "V1_endpoint_order_plus_pair_adjacency",
                "b4_formulation_kind": "endpoint_order+pair_adjacency",
            },
            "result": {
                "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                "exact_status": "NOT_SOLVED",
                "best_reduced_cost": -0.01,
                "dual_bound": -0.03,
                "negative_column_count": 1,
                "added_column_count": 1,
                "can_certify_no_negative": False,
                "mtz_endpoint_order_cuts_enabled": True,
                "mtz_endpoint_order_cut_count": 10,
                "pair_adjacency_cuts_enabled": True,
                "pair_adjacency_cut_count": 20,
                "latest_service_start_slot_bound_enabled": False,
                "time_window_arc_pruning_enabled": False,
                "variable_count": 100,
                "constraint_count": 200,
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "replay.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = run_b4_pricing_formulation_diagnostic_from_json([path])

        self.assertEqual(report["row_count"], 1)
        self.assertEqual(report["rows"][0]["variant"], "V1_endpoint_order_plus_pair_adjacency")
        self.assertEqual(report["rows"][0]["formulation_kind"], "endpoint_order+pair_adjacency")
        self.assertIn("V0_current_compact_pricing", report["acceptance"]["missing_variants"])

    def test_b4_pricing_formulation_matrix_runner_suppresses_negative_feasibility_certificate(self) -> None:
        try:
            import highspy  # noqa: F401
        except Exception as exc:
            self.skipTest(f"optional highspy dependency unavailable: {exc}")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        with tempfile.TemporaryDirectory() as tmp:
            instance_path = Path(tmp) / "instance.json"
            instance_path.write_text(json.dumps(instance), encoding="utf-8")
            probe_path = Path(tmp) / "probe.json"
            probe_path.write_text(
                json.dumps(
                    {
                        "instance_path": str(instance_path),
                        "instance_id": data.instance_id,
                        "history": [
                            {
                                "round": 1,
                                "dual_context": {
                                    "task_duals": {
                                        task_id: 0.05 * (index + 1)
                                        for index, task_id in enumerate(data.task_ids)
                                    },
                                    "fleet_dual": 0.0,
                                    "cut_duals": {},
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            report = run_b4_pricing_formulation_matrix_from_probe(
                probe_path,
                variants=("V0_current_compact_pricing",),
                negative_feasibility_time_limit_sec=30.0,
                optimization_proof_time_limit_sec=0.0,
            )

        self.assertEqual(report["row_count"], 1)
        self.assertEqual(report["rows"][0]["variant"], "V0_current_compact_pricing")
        self.assertEqual(report["rows"][0]["phase"], "negative_feasibility")
        self.assertFalse(report["rows"][0]["can_certify_no_negative"])
        self.assertEqual(report["acceptance"]["no_negative_certified_row_count"], 0)

    def test_b4_pricing_formulation_matrix_iterator_skips_existing_row_key(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        with tempfile.TemporaryDirectory() as tmp:
            instance_path = Path(tmp) / "instance.json"
            instance_path.write_text(json.dumps(instance), encoding="utf-8")
            probe_path = Path(tmp) / "probe.json"
            probe_path.write_text(
                json.dumps(
                    {
                        "instance_path": str(instance_path),
                        "instance_id": data.instance_id,
                        "history": [
                            {
                                "round": 1,
                                "dual_context": {
                                    "task_duals": {task_id: 0.0 for task_id in data.task_ids},
                                    "fleet_dual": 0.0,
                                    "cut_duals": {},
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            existing = {
                b4_pricing_matrix_row_key(
                    {
                        "source_json": str(probe_path),
                        "round": 1,
                        "variant": "V0_current_compact_pricing",
                        "phase": "negative_feasibility",
                    }
                )
            }
            rows = list(
                iter_b4_pricing_formulation_matrix_rows_from_probe(
                    probe_path,
                    variants=("V0_current_compact_pricing",),
                    negative_feasibility_time_limit_sec=30.0,
                    optimization_proof_time_limit_sec=0.0,
                    skip_keys=existing,
                )
            )

        self.assertEqual(rows, [])
        report = build_b4_pricing_formulation_report_from_rows(rows)
        self.assertEqual(report["row_count"], 0)
        self.assertFalse(report["acceptance"]["b4_pricing_formulation_diagnostic_accepted"])

    def test_b4_pricing_formulation_improvement_requires_same_source_and_round(self) -> None:
        source = "/tmp/probe.json"
        rows = [
            {
                "source_json": source,
                "round": "3",
                "variant": "V0_current_compact_pricing",
                "phase": "optimization_proof",
                "compact_pricing_dual_bound": -0.008,
                "new_negative_columns_found": 1,
            },
            {
                "source_json": source,
                "round": "",
                "variant": "V4_combined_endpoint_pair_latest_start_time_window",
                "phase": "staged_frontier_merge",
                "compact_pricing_dual_bound": -0.007,
                "new_negative_columns_found": 1,
            },
            {"source_json": source, "round": "3", "variant": "V1_endpoint_order_plus_pair_adjacency", "phase": "negative_feasibility"},
            {"source_json": source, "round": "3", "variant": "V2_latest_service_start_slot_bound", "phase": "negative_feasibility"},
            {"source_json": source, "round": "3", "variant": "V3_time_window_arc_pruning", "phase": "negative_feasibility"},
            {"source_json": source, "round": "3", "variant": "V5_subset_row_master_diagnostic_only", "phase": "diagnostic"},
        ]

        report = build_b4_pricing_formulation_report_from_rows(rows)
        self.assertEqual(report["acceptance"]["measurable_improvement_row_count"], 0)
        self.assertFalse(report["acceptance"]["b4e_pricing_formulation_accepted"])

        rows[1]["round"] = "3"
        report = build_b4_pricing_formulation_report_from_rows(rows)
        self.assertEqual(report["acceptance"]["measurable_improvement_row_count"], 1)
        self.assertTrue(report["acceptance"]["b4e_pricing_formulation_accepted"])

    def test_b4_pricing_formulation_reports_missing_optimization_proof(self) -> None:
        payload = {
            "instance_id": "diagnostic",
            "history": [
                {
                    "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                    "exact_status": "NOT_SOLVED",
                    "compact_pricing_phase": "negative_feasibility_search",
                    "negative_feasibility_search_enabled": True,
                    "best_reduced_cost": None,
                    "dual_bound": None,
                    "can_certify_no_negative": False,
                    "compact_final_judge_profile": "V4",
                    "compact_final_judge_formulation_profile": "B4V4_endpoint_pair_latest_start_time_window",
                    "compact_final_judge_phase_mode": "proof_only",
                    "negative_feasibility_skipped_for_proof_only": True,
                    "negative_feasibility_full_space_proof_attempted": False,
                    "negative_feasibility_full_space_proof_can_certify": False,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "probe.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = run_b4_pricing_formulation_diagnostic_from_json([path])

        self.assertEqual(report["row_count"], 1)
        row = report["rows"][0]
        self.assertTrue(row["negative_discovery_budget_exhausted"])
        self.assertTrue(row["optimization_proof_missing"])
        self.assertEqual(row["compact_final_judge_profile"], "V4")
        self.assertEqual(row["compact_final_judge_phase_mode"], "proof_only")
        self.assertTrue(row["negative_feasibility_skipped_for_proof_only"])
        self.assertFalse(row["negative_feasibility_full_space_proof_attempted"])
        self.assertFalse(row["negative_feasibility_full_space_proof_can_certify"])
        self.assertEqual(report["acceptance"]["negative_discovery_budget_exhausted_count"], 1)
        self.assertEqual(report["acceptance"]["feasibility_proof_budget_exhausted_count"], 0)
        self.assertEqual(report["acceptance"]["optimization_proof_missing_count"], 1)
        self.assertFalse(row["can_certify_no_negative"])

        feasibility_payload = {
            "instance_id": "diagnostic",
            "history": [
                {
                    "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                    "exact_status": "NOT_SOLVED",
                    "compact_pricing_phase": "negative_feasibility_proof",
                    "negative_feasibility_search_enabled": True,
                    "can_certify_no_negative": False,
                    "negative_feasibility_full_space_proof_attempted": True,
                    "negative_feasibility_full_space_proof_can_certify": False,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feasibility_probe.json"
            path.write_text(json.dumps(feasibility_payload), encoding="utf-8")
            feasibility_report = run_b4_pricing_formulation_diagnostic_from_json([path])
        self.assertEqual(feasibility_report["acceptance"]["negative_discovery_budget_exhausted_count"], 0)
        self.assertEqual(feasibility_report["acceptance"]["feasibility_proof_budget_exhausted_count"], 1)

    def test_b4_1_v2_default_and_v4_diagnostic_configs_are_explicit(self) -> None:
        v2 = B4D_VARIANT_CONFIGS["V2_latest_service_start_slot_bound"]
        self.assertFalse(v2["mtz_endpoint_order_cuts"])
        self.assertFalse(v2["pair_adjacency_cuts"])
        self.assertTrue(v2["latest_service_start_slot_bound"])
        self.assertFalse(v2["time_window_arc_pruning"])
        self.assertFalse(v2["resource_arc_pruning"])
        self.assertFalse(v2["slot_arc_support_pruning"])

        v4 = B4D_VARIANT_CONFIGS["V4_combined_endpoint_pair_latest_start_time_window"]
        self.assertTrue(v4["mtz_endpoint_order_cuts"])
        self.assertTrue(v4["pair_adjacency_cuts"])
        self.assertTrue(v4["latest_service_start_slot_bound"])
        self.assertTrue(v4["time_window_arc_pruning"])
        self.assertTrue(v4["resource_arc_pruning"])
        self.assertFalse(v4["slot_arc_support_pruning"])

    def test_b4_1_runner_report_keeps_full_experiment_gate_closed(self) -> None:
        rows = [
            {
                "stage": "A",
                "matrix_group": "smoke",
                "instance_path": "data/instances/lunar_ice_sp50_005/instance_001_logical_graph.json",
                "scale": 5,
                "instance_id": "smoke-001",
                "mode": "stageA_B2B_R2_worker_tail_dual_on",
                "variant": "",
                "phase": "stage_a_solver",
                "algorithm_status": "BPC_INCOMPLETE_PRICING",
                "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                "pricing_state": "INCOMPLETE_LIMIT",
                "exact_status": "NOT_SOLVED",
                "bpc_tree_optimal": False,
                "manual_rc_fail": 0,
                "pricing_rc_fail": 0,
                "certificate_leak": 0,
                "diagnostic_claimed_certificate": 0,
                "tail_dual_stabilization_enabled": True,
                "worker_dual_only": True,
                "true_dual_rc_recomputed": True,
                "worker_dual_source": "tail_dual_stabilized_worker_dual",
                "official_dual_source": "current_true_rmp_dual",
                "tail_dual_stabilization_alpha": 0.7,
                "tail_dual_stabilization_window": 5,
                "tail_dual_center_task_count": 5,
                "tail_dual_current_task_count": 5,
                "tail_dual_no_column_can_certify": False,
                "negative_column_count": 0,
                "wall_time": 0.01,
            }
        ]
        report = build_b4_1_report(rows)
        self.assertFalse(report["acceptance"]["stage_a_regression_clean"])
        self.assertFalse(report["acceptance"]["stage_c_diagnostic_clean"])
        self.assertTrue(report["acceptance"]["b4_1_code_path_exercised"])
        self.assertFalse(report["acceptance"]["b4_1_full_experiment_complete"])
        self.assertTrue(report["acceptance"]["requires_long_experiment_completion"])
        self.assertEqual(report["redlines"]["diagnostic_claimed_certificate_count"], 0)
        self.assertEqual(report["redlines"]["tail_dual_certificate_leak_count"], 0)
        self.assertEqual(report["redlines"]["exception_fail_closed_count"], 0)
        self.assertEqual(report["diagnostics"]["tail_dual_enabled_count"], 1)
        self.assertEqual(report["diagnostics"]["tail_dual_worker_only_count"], 1)
        self.assertEqual(report["diagnostics"]["tail_dual_true_dual_recomputed_count"], 1)
        self.assertEqual(report["diagnostics"]["tail_dual_no_column_can_certify_count"], 0)
        self.assertEqual(
            report["diagnostics"]["stage_a_missing_regression_modes"],
            ["stageA_B3B_accepted_baseline", "stageA_B4V2_default_final_judge_harvesting"],
        )
        requirement_status = {item["id"]: item["status"] for item in report["requirement_audit"]}
        self.assertEqual(requirement_status["R1_redlines_zero"], "pass")
        self.assertEqual(requirement_status["R2_stage_a_regression_clean"], "missing")
        self.assertEqual(requirement_status["R3_stage_b_matrix_complete"], "missing")
        self.assertEqual(requirement_status["R4_stage_c_selected_diagnostic"], "missing")
        self.assertEqual(requirement_status["R6_tail_dual_worker_only"], "pass")
        self.assertEqual(requirement_status["R7_30_scale_exact_closure"], "incomplete")

        unsafe_tail = dict(rows[0])
        unsafe_tail["can_certify_no_negative"] = True
        unsafe_report = build_b4_1_report([unsafe_tail])
        self.assertEqual(unsafe_report["redlines"]["tail_dual_certificate_leak_count"], 1)
        unsafe_status = {item["id"]: item["status"] for item in unsafe_report["requirement_audit"]}
        self.assertEqual(unsafe_status["R1_redlines_zero"], "fail")
        self.assertEqual(unsafe_status["R6_tail_dual_worker_only"], "fail")

        exception_report = build_b4_1_report(
            [
                {
                    "stage": "A",
                    "mode": "stageA_B3B_accepted_baseline",
                    "algorithm_status": "EXCEPTION_FAIL_CLOSED",
                    "manual_rc_fail": 0,
                    "pricing_rc_fail": 0,
                    "certificate_leak": 0,
                    "diagnostic_claimed_certificate": 0,
                }
            ]
        )
        self.assertEqual(exception_report["redlines"]["exception_fail_closed_count"], 1)
        self.assertFalse(exception_report["acceptance"]["stage_a_regression_clean"])
        miss_report = build_b4_1_report(
            [
                {
                    "stage": "A",
                    "mode": "stageA_B4V2_default_final_judge_harvesting",
                    "algorithm_status": "BPC_INCOMPLETE_PRICING",
                    "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                    "manual_rc_fail": 0,
                    "pricing_rc_fail": 0,
                    "certificate_leak": 0,
                    "diagnostic_claimed_certificate": 0,
                }
            ]
        )
        self.assertEqual(miss_report["redlines"]["stage_a_tree_closure_miss_count"], 1)
        self.assertFalse(miss_report["acceptance"]["stage_a_regression_clean"])

        stage_a = b4_1_runner_module._stage_a_row(
            {
                "instance_id": "safe-b0-none",
                "algorithm_status": "BPC_GAP_AVAILABLE",
                "certificate_scope": "BPC_NODE_LP_CERTIFIED",
                "pricing_state": "CERTIFIED_NO_NEGATIVE",
                "exact_status": "BPC_NODE_LP_CERTIFIED",
                "B0_direct_objective": 1.25,
                "b0_ablation": None,
                "root_lp_bound": 1.25,
                "manual_rc_audit_pass": True,
                "pricing_rc_audit_pass": True,
                "final_judge": {
                    "variable_count": 6009,
                    "constraint_count": 14743,
                    "harvest_selected_count": 2,
                    "harvest_candidate_negative_count": 4,
                    "harvest_selected_new_task_set_count": 1,
                    "harvest_selected_replacement_task_set_count": 1,
                    "harvest_rejected_duplicate_count": 3,
                    "harvest_rejected_not_addable_count": 2,
                    "harvest_best_true_rc": -0.9,
                    "harvest_worst_selected_true_rc": -0.1,
                    "harvest_avg_pairwise_jaccard": 0.333333333,
                    "harvest_addability_audit_pass": True,
                },
                "max_tree_nodes": 31,
                "max_branch_depth": 4,
                "node_count": 1,
                "nodes": [
                    {
                        "round_count": 7,
                        "added_column_count": 531,
                        "history": [
                            {
                                "pricing_state": "CERTIFIED_NO_NEGATIVE",
                                "negative_column_count": 0,
                            }
                        ],
                    }
                ],
            },
            stage="A",
            matrix_group="smoke",
            instance_path="data/instances/lunar_ice_sp50_005/instance_001_logical_graph.json",
            scale=5,
            mode="stageA_B3B_accepted_baseline",
            wall_time=0.01,
            max_rounds=16,
            max_columns_per_round=128,
        )
        self.assertEqual(stage_a["b3_objective_diff_vs_b0"], 0.0)
        self.assertEqual(stage_a["max_rounds"], 16)
        self.assertEqual(stage_a["max_columns_per_round"], 128)
        self.assertEqual(stage_a["max_tree_nodes"], 31)
        self.assertEqual(stage_a["max_branch_depth"], 4)
        self.assertEqual(stage_a["node_count"], 1)
        self.assertEqual(stage_a["root_round_count"], 7)
        self.assertEqual(stage_a["root_added_column_count"], 531)
        self.assertEqual(stage_a["root_last_pricing_state"], "CERTIFIED_NO_NEGATIVE")
        self.assertEqual(stage_a["root_last_negative_column_count"], 0)
        self.assertEqual(stage_a["tree_gate_issue_count"], 0)
        self.assertEqual(stage_a["variable_count"], 6009)
        self.assertEqual(stage_a["constraint_count"], 14743)
        self.assertEqual(stage_a["b4_1_matrix_cell"], "B3B_accepted_tree_baseline")
        self.assertEqual(stage_a["b4_1_proof_tail_component"], "true_dual_final_judge_tree_closure")
        self.assertEqual(stage_a["b4_1_formulation_profile"], "B3B_representative_universe_branch_rc_audit")
        self.assertFalse(stage_a["b4_1_harvesting_enabled"])
        self.assertFalse(stage_a["b4_1_frontier_ledger_enabled"])
        self.assertTrue(stage_a["b4_1_official_certificate_allowed"])
        self.assertEqual(stage_a["harvest_rejected_duplicate_count"], 3)
        self.assertEqual(stage_a["harvest_rejected_not_addable_count"], 2)
        self.assertAlmostEqual(stage_a["harvest_avg_pairwise_jaccard"], 0.333333333, delta=1.0e-12)
        signature = inspect.signature(b4_1_runner_module.run_b4_1_stage_a_regression)
        self.assertEqual(signature.parameters["max_columns_per_round"].default, 128)
        self.assertEqual(signature.parameters["max_rounds"].default, 16)

        stage_c_rows = [
            {
                "stage": "C",
                "matrix_group": "selected diagnostic",
                "source_probe_json": "runs/probes/instance_001.json",
                "instance_id": "selected-001",
                "mode": "B4.1_selected_30_diagnostic",
                "variant": "V2_latest_service_start_slot_bound",
                "phase": "optimization_proof",
                "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                "can_certify_no_negative": False,
                "diagnostic_claimed_certificate": 0,
                "manual_rc_fail": 0,
                "pricing_rc_fail": 0,
                "certificate_leak": 0,
                "negative_column_count": 2,
                "global_remaining_rc_lb": -0.01,
                "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
                "negative_discovery_budget_exhausted": True,
                "optimization_proof_missing": True,
                "active_column_count": 300,
                "active_columns_after_merge": 304,
                "best_negative_rc": -0.03,
                "last_best_reduced_cost": 0.01,
                "final_judge_wall_time": 2.5,
                "wall_time": 1.0,
            }
        ]
        stage_c_report = build_b4_1_report(stage_c_rows)
        self.assertTrue(stage_c_report["acceptance"]["stage_c_diagnostic_clean"])
        self.assertFalse(stage_c_report["acceptance"]["b4_1_full_experiment_complete"])
        self.assertEqual(stage_c_report["diagnostics"]["negative_discovery_budget_exhausted_count"], 1)
        self.assertEqual(stage_c_report["diagnostics"]["optimization_proof_missing_count"], 1)
        self.assertEqual(stage_c_report["summary_rows"][0]["mean_active_column_count"], 300.0)
        self.assertEqual(stage_c_report["summary_rows"][0]["mean_active_columns_after_merge"], 304.0)
        self.assertEqual(stage_c_report["summary_rows"][0]["best_negative_rc"], -0.03)
        self.assertEqual(stage_c_report["summary_rows"][0]["best_last_best_reduced_cost"], 0.01)
        self.assertEqual(stage_c_report["summary_rows"][0]["mean_final_judge_wall_time"], 2.5)

        stage_b_partial_report = build_b4_1_report(
            [
                {
                    "stage": "B",
                    "mode": "B4.1_compact_pricing_formulation",
                    "variant": "V2_latest_service_start_slot_bound",
                    "b4_1_matrix_cell": "B4V2_frontier_ledger_diagnostic",
                    "b4_1_frontier_ledger_enabled": True,
                    "diagnostic_claimed_certificate": 0,
                },
                {
                    "stage": "B",
                    "mode": "B4.1_compact_pricing_formulation",
                    "variant": "V4_combined_endpoint_pair_latest_start_time_window",
                    "b4_1_matrix_cell": "B4V4_combined_formulation_diagnostic",
                    "diagnostic_claimed_certificate": 0,
                },
            ]
        )
        self.assertTrue(stage_b_partial_report["acceptance"]["stage_b_diagnostic_clean"])
        self.assertFalse(stage_b_partial_report["acceptance"]["stage_b_matrix_complete"])
        self.assertEqual(
            stage_b_partial_report["diagnostics"]["stage_b_observed_matrix_cells"],
            [
                "B4V2_baseline",
                "B4V2_frontier_ledger_diagnostic",
                "B4V4_combined_formulation_diagnostic",
            ],
        )
        self.assertEqual(
            stage_b_partial_report["diagnostics"]["stage_b_missing_matrix_cells"],
            [
                "B4V2_harvesting",
                "B4V2_hidden_negative_audit",
                "B4V2_harvesting_frontier_ledger_diagnostic",
            ],
        )

        stage_b_complete_report = build_b4_1_report(
            [
                {
                    "stage": "B",
                    "mode": "B4.1_compact_pricing_formulation",
                    "variant": "V2_latest_service_start_slot_bound",
                    "b4_1_matrix_cell": "B4V2_frontier_ledger_diagnostic",
                    "b4_1_harvesting_enabled": True,
                    "b4_1_hidden_negative_audit_enabled": True,
                    "b4_1_frontier_ledger_enabled": True,
                    "harvest_source_phase": "compact_final_judge_negative_feasibility_batch",
                    "diagnostic_claimed_certificate": 0,
                },
                {
                    "stage": "B",
                    "mode": "B4.1_compact_pricing_formulation",
                    "variant": "V4_combined_endpoint_pair_latest_start_time_window",
                    "b4_1_matrix_cell": "B4V4_combined_formulation_diagnostic",
                    "diagnostic_claimed_certificate": 0,
                },
            ]
        )
        self.assertTrue(stage_b_complete_report["acceptance"]["stage_b_matrix_complete"])
        self.assertEqual(stage_b_complete_report["diagnostics"]["stage_b_missing_matrix_cells"], [])

        with tempfile.TemporaryDirectory() as tmp:
            evidence_probe = Path(tmp) / "probe.json"
            evidence_probe.write_text(
                json.dumps(
                    {
                        "schema_version": "lunar_ice_bpc.compact_pricing_batch_probe.v1",
                        "instance_id": "stage-b-evidence",
                        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                        "pricing_round_count": 3,
                        "active_column_count": 297,
                        "pool_column_count": 310,
                        "added_column_count": 2,
                        "active_columns_after_merge": 299,
                        "hidden_negative_audit": {
                            "status": "NO_HIDDEN_NEGATIVE",
                            "hidden_negative_count": 0,
                            "rows": [],
                        },
                        "final_judge": {
                            "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                            "exact_status": "NOT_SOLVED",
                            "compact_final_judge_profile": "B4V2",
                            "compact_final_judge_formulation_profile": "B4V2_latest_start_only",
                            "compact_final_judge_phase_mode": "harvest_then_proof",
                            "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
                            "global_remaining_rc_lb": -0.12,
                            "global_remaining_rc_lb_coverage_complete": False,
                            "frontier_unsupported_region_count": 1,
                            "pending_complete_min_rc": -0.12,
                            "best_reduced_cost": -0.8,
                            "negative_rc": -0.8,
                            "final_judge_wall_time": 12.5,
                            "harvest_schema_version": "lunar_ice_bpc.b4_1_final_judge_harvest.v1",
                            "harvest_selected_count": 5,
                            "harvest_candidate_negative_count": 8,
                            "harvest_selected_new_task_set_count": 4,
                            "harvest_selected_replacement_task_set_count": 1,
                            "harvest_rejected_duplicate_count": 2,
                            "harvest_rejected_not_addable_count": 1,
                            "harvest_best_true_rc": -0.8,
                            "harvest_worst_selected_true_rc": -0.05,
                            "harvest_avg_pairwise_jaccard": 0.2,
                            "harvest_addability_audit_pass": True,
                        },
                    }
                ),
                encoding="utf-8",
            )
            evidence_report = b4_1_runner_module.run_b4_1_stage_b_from_probe(
                evidence_probe,
                variants=(),
                matrix_group="stage-b evidence smoke",
            )

        self.assertEqual(evidence_report["row_count"], 1)
        evidence_row = evidence_report["rows"][0]
        self.assertEqual(evidence_row["mode"], "B4.1_probe_final_judge_evidence")
        self.assertTrue(evidence_row["b4_1_harvesting_enabled"])
        self.assertTrue(evidence_row["b4_1_hidden_negative_audit_enabled"])
        self.assertTrue(evidence_row["b4_1_frontier_ledger_enabled"])
        self.assertEqual(evidence_row["harvest_selected_count"], 5)
        self.assertEqual(evidence_row["active_column_count"], 297)
        self.assertEqual(evidence_row["pool_column_count"], 310)
        self.assertEqual(evidence_row["columns_added"], 2)
        self.assertEqual(evidence_row["active_columns_after_merge"], 299)
        self.assertEqual(evidence_row["new_task_set_count"], 4)
        self.assertEqual(evidence_row["replacement_task_set_count"], 1)
        self.assertEqual(evidence_row["best_negative_rc"], -0.8)
        self.assertEqual(evidence_row["last_best_reduced_cost"], -0.8)
        self.assertEqual(evidence_row["final_judge_wall_time"], 12.5)
        self.assertEqual(evidence_row["rmp_round_count"], 3)
        self.assertEqual(evidence_row["hidden_negative_count"], 0)
        self.assertEqual(
            evidence_report["diagnostics"]["stage_b_observed_matrix_cells"],
            [
                "B4V2_baseline",
                "B4V2_frontier_ledger_diagnostic",
                "B4V2_harvesting",
                "B4V2_harvesting_frontier_ledger_diagnostic",
                "B4V2_hidden_negative_audit",
            ],
        )
        self.assertEqual(evidence_report["diagnostics"]["stage_b_missing_matrix_cells"], ["B4V4_combined_formulation_diagnostic"])

        with tempfile.TemporaryDirectory() as tmp:
            v4_probe = Path(tmp) / "probe.json"
            v4_probe.write_text(
                json.dumps(
                    {
                        "schema_version": "lunar_ice_bpc.compact_pricing_batch_probe.v1",
                        "instance_id": "stage-b-v4-evidence",
                        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                        "pricing_round_count": 1,
                        "added_column_count": 3,
                        "active_columns": [{}, {}, {}],
                        "final_judge": {
                            "status": "COMPACT_HIGHS_PRICING_OPTIMIZATION_HARVEST_FOUND_NEGATIVE",
                            "exact_status": "NOT_SOLVED",
                            "compact_final_judge_profile": "V4",
                            "compact_final_judge_formulation_profile": "B4V4_endpoint_pair_latest_start_time_window",
                            "compact_final_judge_phase_mode": "proof_only",
                            "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
                            "global_remaining_rc_lb": -0.002031064,
                            "global_remaining_rc_lb_coverage_complete": False,
                            "frontier_unsupported_region_count": 3,
                            "pending_complete_min_rc": -0.002031375,
                            "best_reduced_cost": -0.002031375,
                            "negative_column_count": 3,
                            "final_judge_wall_time": 597.266705,
                            "harvest_schema_version": "lunar_ice_bpc.b4_1_final_judge_harvest.v1",
                            "harvest_source_phase": "compact_final_judge_optimization_harvest",
                            "harvest_selected_count": 3,
                            "harvest_candidate_negative_count": 3,
                            "harvest_selected_new_task_set_count": 2,
                            "harvest_selected_replacement_task_set_count": 1,
                            "harvest_rejected_duplicate_count": 0,
                            "harvest_rejected_not_addable_count": 0,
                            "harvest_best_true_rc": -0.002031375,
                            "harvest_worst_selected_true_rc": -0.000923125,
                            "harvest_avg_pairwise_jaccard": 0.186202686,
                            "harvest_addability_audit_pass": True,
                            "harvest_pricing_rc_audit_available": True,
                            "harvest_pricing_rc_audit_pass": True,
                            "harvest_pricing_rc_max_abs_diff": 0.000000311,
                            "compact_optimization_harvest_enabled": True,
                            "compact_optimization_harvest_target": 5,
                            "compact_optimization_harvest_no_good_scope": "task_set",
                            "compact_optimization_harvest_found_count": 3,
                            "compact_optimization_harvest_search_call_count": 4,
                        },
                    }
                ),
                encoding="utf-8",
            )
            v4_report = b4_1_runner_module.run_b4_1_stage_b_from_probe(
                v4_probe,
                variants=(),
                matrix_group="stage-b v4 evidence smoke",
            )

        self.assertEqual(v4_report["row_count"], 1)
        v4_row = v4_report["rows"][0]
        self.assertEqual(v4_row["variant"], "V4_combined_endpoint_pair_latest_start_time_window")
        self.assertEqual(v4_row["b4_1_matrix_cell"], "B4V4_combined_formulation_diagnostic")
        self.assertEqual(v4_row["active_column_count"], 3)
        self.assertEqual(v4_row["active_columns_after_merge"], 3)
        self.assertTrue(v4_row["b4_1_harvesting_enabled"])
        self.assertTrue(v4_row["b4_1_frontier_ledger_enabled"])
        self.assertFalse(v4_row["can_certify_no_negative"])
        self.assertEqual(v4_row["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
        self.assertEqual(v4_row["harvest_source_phase"], "compact_final_judge_optimization_harvest")
        self.assertEqual(v4_row["harvest_selected_count"], 3)
        self.assertEqual(v4_row["new_task_set_count"], 2)
        self.assertEqual(v4_row["replacement_task_set_count"], 1)
        self.assertEqual(v4_row["compact_optimization_harvest_found_count"], 3)
        self.assertEqual(
            v4_report["diagnostics"]["stage_b_observed_matrix_cells"],
            ["B4V4_combined_formulation_diagnostic"],
        )
        self.assertNotIn("B4V2_harvesting", v4_report["diagnostics"]["stage_b_observed_matrix_cells"])
        self.assertEqual(v4_report["redlines"]["diagnostic_claimed_certificate_count"], 0)

        latest_frontier_report = build_b4_1_report(
            [
                {
                    "stage": "B",
                    "mode": "B4.1_probe_final_judge_evidence",
                    "variant": "V4_combined_endpoint_pair_latest_start_time_window",
                    "source_probe_json": "runs/after_333/stage_001/probe.json",
                    "phase": "probe_final_judge_evidence",
                    "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                    "diagnostic_claimed_certificate": 0,
                    "active_column_count": 333,
                    "active_columns_after_merge": 333,
                    "columns_added": 3,
                    "negative_column_count": 3,
                    "best_negative_rc": -0.005,
                    "last_best_reduced_cost": -0.005,
                    "global_remaining_rc_lb": -0.005,
                    "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
                    "final_judge_wall_time": 597.0,
                },
                {
                    "stage": "B",
                    "mode": "B4.1_probe_final_judge_evidence",
                    "variant": "V4_combined_endpoint_pair_latest_start_time_window",
                    "source_probe_json": "runs/after_345/stage_001/probe.json",
                    "phase": "probe_final_judge_evidence",
                    "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                    "diagnostic_claimed_certificate": 0,
                    "active_column_count": 345,
                    "active_columns_after_merge": 345,
                    "columns_added": 3,
                    "negative_column_count": 3,
                    "best_negative_rc": -0.001,
                    "last_best_reduced_cost": -0.001,
                    "global_remaining_rc_lb": -0.001,
                    "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
                    "final_judge_wall_time": 600.0,
                },
            ]
        )
        self.assertEqual(latest_frontier_report["summary_rows"][0]["best_negative_rc"], -0.005)
        self.assertEqual(len(latest_frontier_report["latest_frontier_rows"]), 1)
        self.assertEqual(latest_frontier_report["latest_frontier_rows"][0]["active_columns_after_merge"], 345)
        self.assertEqual(latest_frontier_report["latest_frontier_rows"][0]["best_negative_rc"], -0.001)
        self.assertEqual(
            latest_frontier_report["latest_frontier_rows"][0]["source_probe_json"],
            "runs/after_345/stage_001/probe.json",
        )

        with tempfile.TemporaryDirectory() as tmp:
            no_hidden_probe = Path(tmp) / "probe.json"
            no_hidden_probe.write_text(
                json.dumps(
                    {
                        "schema_version": "lunar_ice_bpc.compact_pricing_batch_probe.v1",
                        "instance_id": "stage-b-no-hidden-evidence",
                        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                        "pricing_round_count": 1,
                        "final_judge": {
                            "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                            "compact_final_judge_profile": "B4V2",
                            "harvest_schema_version": "lunar_ice_bpc.b4_1_final_judge_harvest.v1",
                            "harvest_selected_count": 1,
                        },
                    }
                ),
                encoding="utf-8",
            )
            no_hidden_report = b4_1_runner_module.run_b4_1_stage_b_from_probe(
                no_hidden_probe,
                variants=(),
                matrix_group="stage-b no-hidden smoke",
            )
        no_hidden_row = no_hidden_report["rows"][0]
        self.assertFalse(no_hidden_row["b4_1_hidden_negative_audit_enabled"])
        self.assertEqual(no_hidden_row["hidden_negative_count"], "")
        self.assertNotIn("B4V2_hidden_negative_audit", no_hidden_report["diagnostics"]["stage_b_observed_matrix_cells"])

        with tempfile.TemporaryDirectory() as tmp:
            worker_tail_payload = Path(tmp) / "b2_payload.json"
            worker_tail_payload.write_text(
                json.dumps(
                    {
                        "schema_version": "lunar_ice_bpc.b2_pricing_tail_baseline.v2",
                        "instance_id": "stage-b-worker-tail-evidence",
                        "b2_mode": "B2B_R2_worker_before_final_judge",
                        "algorithm_status": "BPC_INCOMPLETE_PRICING",
                        "certificate_scope": "FEASIBLE_INCUMBENT_ONLY",
                        "exact_status": "NOT_SOLVED",
                        "pricing_round_count": 6,
                        "candidate_negative_count": 9,
                        "harvest_selected_count": 3,
                        "harvest_candidate_negative_count": 9,
                        "harvest_selected_new_task_set_count": 2,
                        "harvest_selected_replacement_task_set_count": 1,
                        "harvest_rejected_duplicate_count": 4,
                        "harvest_rejected_not_addable_count": 2,
                        "harvest_best_true_rc": -0.7,
                        "harvest_worst_selected_true_rc": -0.03,
                        "harvest_avg_pairwise_jaccard": 0.4,
                        "hidden_negative_count": 2,
                        "hidden_negative_audit": {
                            "schema_version": "lunar_ice_bpc.b2_hidden_negative_audit.v1",
                            "status": "HIDDEN_NEGATIVE_FOUND",
                            "hidden_negative_count": 2,
                            "mutates_solver": False,
                            "changes_certificate_semantics": False,
                            "rows": [
                                {
                                    "hidden_negative_task_set": ["t1", "t2"],
                                    "hidden_negative_true_rc": -0.7,
                                    "miss_reason": "worker_not_generated",
                                },
                                {
                                    "hidden_negative_task_set": ["t3"],
                                    "hidden_negative_true_rc": -0.03,
                                    "miss_reason": "pruned_by_dominance",
                                },
                            ],
                        },
                        "final_judge": {
                            "status": "FOUND_NEGATIVE",
                            "exact_status": "NOT_SOLVED",
                            "compact_final_judge_profile": "B4V2",
                            "compact_final_judge_formulation_profile": "B4V2_latest_start_only",
                            "compact_final_judge_phase_mode": "harvest_then_proof",
                            "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
                            "global_remaining_rc_lb": -0.7,
                            "global_remaining_rc_lb_coverage_complete": False,
                            "frontier_unsupported_region_count": 1,
                            "pending_complete_min_rc": -0.7,
                            "can_certify_no_negative": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            worker_tail_report = b4_1_runner_module.run_b4_1_stage_b_from_probe(
                worker_tail_payload,
                variants=(),
                matrix_group="stage-b worker-tail evidence smoke",
            )
        self.assertEqual(worker_tail_report["row_count"], 1)
        worker_tail_row = worker_tail_report["rows"][0]
        self.assertEqual(worker_tail_row["mode"], "B4.1_worker_tail_hidden_negative_evidence")
        self.assertEqual(worker_tail_row["phase"], "worker_tail_hidden_negative_evidence")
        self.assertFalse(worker_tail_row["b4_1_harvesting_enabled"])
        self.assertTrue(worker_tail_row["b4_1_hidden_negative_audit_enabled"])
        self.assertTrue(worker_tail_row["b4_1_frontier_ledger_enabled"])
        self.assertFalse(worker_tail_row["b4_1_official_certificate_allowed"])
        self.assertFalse(worker_tail_row["can_certify_no_negative"])
        self.assertEqual(worker_tail_row["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
        self.assertEqual(worker_tail_row["underlying_certificate_scope"], "FEASIBLE_INCUMBENT_ONLY")
        self.assertEqual(worker_tail_row["hidden_negative_count"], 2)
        self.assertEqual(
            worker_tail_row["hidden_negative_miss_reason_counts"],
            {"worker_not_generated": 1, "pruned_by_dominance": 1},
        )
        self.assertEqual(worker_tail_row["hidden_negative_top_miss_reason"], "worker_not_generated")
        self.assertEqual(worker_tail_row["hidden_negative_worker_not_generated_count"], 1)
        self.assertEqual(worker_tail_row["hidden_negative_pruned_by_dominance_count"], 1)
        self.assertEqual(worker_tail_row["harvest_selected_count"], 3)
        self.assertEqual(worker_tail_row["harvest_candidate_negative_count"], 9)
        self.assertEqual(worker_tail_row["harvest_rejected_duplicate_count"], 4)
        self.assertEqual(worker_tail_row["harvest_rejected_not_addable_count"], 2)
        self.assertEqual(worker_tail_row["harvest_source_phase"], "")
        self.assertEqual(worker_tail_row["fail_closed_reason"], "HIDDEN_NEGATIVE_FOUND")
        self.assertIn("B4V2_hidden_negative_audit", worker_tail_report["diagnostics"]["stage_b_observed_matrix_cells"])
        self.assertNotIn("B4V2_harvesting", worker_tail_report["diagnostics"]["stage_b_observed_matrix_cells"])
        self.assertEqual(
            worker_tail_report["diagnostics"]["hidden_negative_miss_reason_counts"],
            {"worker_not_generated": 1, "pruned_by_dominance": 1},
        )
        self.assertEqual(worker_tail_report["diagnostics"]["hidden_negative_top_miss_reason"], "worker_not_generated")
        self.assertEqual(worker_tail_report["diagnostics"]["hidden_negative_worker_not_generated_count"], 1)
        self.assertEqual(worker_tail_report["diagnostics"]["hidden_negative_pruned_by_dominance_count"], 1)
        self.assertEqual(worker_tail_report["redlines"]["diagnostic_claimed_certificate_count"], 0)

        with tempfile.TemporaryDirectory() as tmp:
            probe_path = Path(tmp) / "worker_tail_probe.json"
            live_probe_report = b4_1_runner_module.run_b4_1_stage_b_worker_tail_hidden_probe(
                generate_instance(5, seed=629001, index=1),
                output_probe_json=probe_path,
                max_direct_tasks=5,
                max_rounds=2,
                wall_time_limit_sec=30.0,
                max_columns_per_round=4,
                skip_b0_direct=True,
            )
            live_payload = json.loads(probe_path.read_text(encoding="utf-8"))
        self.assertEqual(live_payload["schema_version"], "lunar_ice_bpc.b4_1_worker_tail_hidden_negative_probe.v1")
        self.assertTrue(live_payload["config"]["skip_b0_direct"])
        self.assertFalse(live_payload["config"]["official_certificate_allowed"])
        self.assertIn("hidden_negative_audit", live_payload)
        self.assertEqual(live_probe_report["redlines"]["diagnostic_claimed_certificate_count"], 0)
        if live_payload["final_judge_call_count"]:
            self.assertEqual(live_probe_report["row_count"], 1)
            live_row = live_probe_report["rows"][0]
            self.assertEqual(live_row["mode"], "B4.1_worker_tail_hidden_negative_evidence")
            self.assertEqual(live_row["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
            self.assertFalse(live_row["can_certify_no_negative"])
            self.assertIn("B4V2_hidden_negative_audit", live_probe_report["diagnostics"]["stage_b_observed_matrix_cells"])

        suppressed = b4_1_runner_module._stage_probe_row(
            {
                "source_json": "runs/probes/instance_001.json",
                "instance_id": "selected-001",
                "variant": "V2_latest_service_start_slot_bound",
                "phase": "optimization_proof",
                "round": 1,
                "compact_pricing_status": "COMPACT_HIGHS_PRICING_OPTIMAL",
                "compact_pricing_exact_status": "EXACT_PRICING_OPTIMAL",
                "certificate_scope": "BPC_NODE_LP_CERTIFIED",
                "can_certify_no_negative": True,
                "pricing_proof_kind": "EXHAUSTIVE_NO_NEGATIVE",
                "global_remaining_rc_lb": 0.25,
                "frontier_coverage_complete": True,
                "frontier_unsupported_region_count": 0,
                "pending_complete_min_rc": 0.25,
                "compact_final_judge_profile": "V4",
                "compact_final_judge_formulation_profile": "B4V4_endpoint_pair_latest_start_time_window",
                "compact_final_judge_phase_mode": "proof_only",
                "negative_feasibility_skipped_for_proof_only": True,
                "phase_budget_sec": 900.0,
                "negative_feasibility_budget_sec": 600.0,
                "optimization_proof_budget_sec": 900.0,
                "negative_discovery_budget_exhausted": False,
                "optimization_proof_missing": False,
            },
            stage="C",
            mode="B4.1_selected_30_diagnostic",
            matrix_group="selected diagnostic",
        )
        self.assertEqual(suppressed["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
        self.assertEqual(suppressed["underlying_certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertFalse(suppressed["can_certify_no_negative"])
        self.assertTrue(suppressed["underlying_can_certify_no_negative"])
        self.assertTrue(suppressed["b4_1_certificate_suppressed"])
        self.assertEqual(suppressed["pricing_proof_kind"], "FRONTIER_BOUND_INCOMPLETE")
        self.assertEqual(suppressed["underlying_pricing_proof_kind"], "EXHAUSTIVE_NO_NEGATIVE")
        self.assertFalse(suppressed["frontier_lb_official"])
        self.assertEqual(suppressed["global_remaining_rc_lb"], 0.25)
        self.assertEqual(suppressed["underlying_global_remaining_rc_lb"], 0.25)
        self.assertFalse(suppressed["frontier_coverage_complete"])
        self.assertTrue(suppressed["underlying_frontier_coverage_complete"])
        self.assertEqual(suppressed["frontier_unsupported_region_count"], 1)
        self.assertEqual(suppressed["underlying_frontier_unsupported_region_count"], 0)
        self.assertEqual(suppressed["pending_complete_min_rc"], 0.25)
        self.assertEqual(suppressed["underlying_pending_complete_min_rc"], 0.25)
        self.assertEqual(suppressed["compact_final_judge_profile"], "V4")
        self.assertEqual(
            suppressed["compact_final_judge_formulation_profile"],
            "B4V4_endpoint_pair_latest_start_time_window",
        )
        self.assertEqual(suppressed["compact_final_judge_phase_mode"], "proof_only")
        self.assertTrue(suppressed["negative_feasibility_skipped_for_proof_only"])
        self.assertEqual(suppressed["phase_budget_sec"], 900.0)
        self.assertFalse(suppressed["negative_discovery_budget_exhausted"])
        self.assertFalse(suppressed["optimization_proof_missing"])
        self.assertEqual(suppressed["diagnostic_claimed_certificate"], 0)
        self.assertEqual(suppressed["b4_1_matrix_cell"], "B4V2_frontier_ledger_diagnostic")
        self.assertEqual(suppressed["b4_1_proof_tail_component"], "compact_pricing_frontier_ledger_diagnostic")
        self.assertEqual(suppressed["b4_1_formulation_profile"], "B4V2_latest_start_only")
        self.assertFalse(suppressed["b4_1_harvesting_enabled"])
        self.assertFalse(suppressed["b4_1_hidden_negative_audit_enabled"])
        self.assertTrue(suppressed["b4_1_frontier_ledger_enabled"])
        self.assertFalse(suppressed["b4_1_official_certificate_allowed"])

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            write_b4_1_artifacts(
                report,
                rows_csv=out / "rows.csv",
                summary_json=out / "summary.json",
                report_md=out / "report.md",
            )
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            self.assertFalse(summary["acceptance"]["b4_1_full_experiment_complete"])
            self.assertFalse(summary["acceptance"]["stage_c_diagnostic_clean"])
            self.assertIn("diagnostics", summary)
            self.assertIn("Full long experiment complete", (out / "report.md").read_text(encoding="utf-8"))
            self.assertIn("Stage C selected diagnostic clean", (out / "report.md").read_text(encoding="utf-8"))
            self.assertIn("Proof-Tail Diagnostics", (out / "report.md").read_text(encoding="utf-8"))
            self.assertIn("Requirement Audit", (out / "report.md").read_text(encoding="utf-8"))

    def test_b4_1_restricted_region_taskset_diagnostic_is_noncertifying(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            probe = tmp_path / "probe.json"
            probe.write_text(
                json.dumps(
                    {
                        "instance_id": "restricted-region-smoke",
                        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                        "final_judge": {
                            "compact_final_judge_profile": "V4",
                            "compact_final_judge_phase_mode": "proof_only",
                            "compact_optimization_harvest_no_good_scope": "task_set",
                            "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
                            "global_remaining_rc_lb": -0.00770611,
                            "global_remaining_rc_lb_coverage_complete": False,
                            "frontier_unsupported_region_count": 3,
                            "harvest_selected_count": 3,
                            "harvest_selected_new_task_set_count": 3,
                            "harvest_selected_replacement_task_set_count": 0,
                            "harvest_pricing_rc_audit_pass": True,
                            "harvest_pricing_rc_max_abs_diff": 3.61e-7,
                            "harvest_reports": [
                                {
                                    "true_reduced_cost": -0.007705961,
                                    "pricing_reduced_cost": -0.00770611,
                                    "task_set": ["ice_site_008", "ice_site_009", "ice_site_010", "ice_site_026"],
                                    "would_enter_master": True,
                                    "selected_after_addability_audit": True,
                                },
                                {
                                    "true_reduced_cost": -0.002763549,
                                    "pricing_reduced_cost": -0.002763188,
                                    "task_set": ["ice_site_001", "ice_site_002", "ice_site_008", "ice_site_020", "ice_site_026"],
                                    "would_enter_master": True,
                                    "selected_after_addability_audit": True,
                                },
                                {
                                    "true_reduced_cost": -0.000586,
                                    "pricing_reduced_cost": -0.000586223,
                                    "task_set": ["ice_site_001", "ice_site_002", "ice_site_008", "ice_site_020", "ice_site_026"],
                                    "would_enter_master": True,
                                    "selected_after_addability_audit": True,
                                },
                            ],
                            "compact_pricing_phase_payloads": {
                                "optimization_proof": {
                                    "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
                                    "exact_status": "EXACT_PRICING_OPTIMAL",
                                    "best_reduced_cost": -0.007705961,
                                    "dual_bound": -0.00770611,
                                    "wall_time_sec": 186.7,
                                    "forbidden_task_set_count": 0,
                                    "forbidden_task_sets_can_certify_full_space": True,
                                },
                                "optimization_harvest_3": {
                                    "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                                    "exact_status": "NOT_SOLVED",
                                    "best_reduced_cost": -0.000586,
                                    "dual_bound": -0.121782748,
                                    "wall_time_sec": 169.1,
                                    "forbidden_task_set_count": 2,
                                    "forbidden_task_sets_can_certify_full_space": False,
                                },
                                "optimization_harvest_4": {
                                    "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                                    "exact_status": "NOT_SOLVED",
                                    "best_reduced_cost": 0.169087764,
                                    "dual_bound": -0.317649341,
                                    "wall_time_sec": 14.7,
                                    "forbidden_task_set_count": 3,
                                    "forbidden_task_sets_can_certify_full_space": False,
                                },
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            diagnostic = b4_1_runner_module.build_b4_1_restricted_region_taskset_diagnostic(probe)
            self.assertEqual(
                diagnostic["schema_version"],
                "lunar_ice_bpc.b4_1_restricted_region_taskset_diagnostic.v1",
            )
            self.assertTrue(diagnostic["diagnostic_only"])
            self.assertFalse(diagnostic["can_claim_certificate"])
            self.assertFalse(diagnostic["no_negative_certificate_claimed"])
            self.assertEqual(diagnostic["pricing_proof_kind"], "FRONTIER_BOUND_INCOMPLETE")
            self.assertEqual(diagnostic["harvested_negative_count"], 3)
            frequency = {row["task"]: row["count"] for row in diagnostic["task_frequency"]}
            self.assertEqual(frequency["ice_site_008"], 3)
            self.assertEqual(frequency["ice_site_026"], 3)
            high_overlap = diagnostic["cluster_summary"]["high_overlap_pairs"]
            self.assertEqual(high_overlap[0]["pair"], "H2-H3")
            self.assertAlmostEqual(high_overlap[0]["jaccard"], 1.0, delta=1.0e-12)
            self.assertEqual(diagnostic["cluster_summary"]["negative_time_limit_region_count"], 1)
            self.assertEqual(diagnostic["cluster_summary"]["incomplete_time_limit_region_count"], 2)
            self.assertIn("diagnostic non-certifying", diagnostic["recommended_next_actions"][0])

            b4_1_runner_module.write_b4_1_restricted_region_taskset_diagnostic(
                diagnostic,
                summary_json=tmp_path / "restricted.json",
                report_md=tmp_path / "restricted_zh.md",
            )
            self.assertIn(
                "No no-negative certificate is claimed",
                (tmp_path / "restricted_zh.md").read_text(encoding="utf-8"),
            )

            cli_out = tmp_path / "cli"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "scripts" / "run_lunar_ice_b4_1_true_dual_proof_tail.py"),
                    "--output-dir",
                    str(cli_out),
                    "--source-probe-json",
                    str(probe),
                    "--restricted-region-taskset-diagnostic",
                    "--no-resume",
                ],
                cwd=project_root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((cli_out / "restricted_region_taskset_diagnostic.json").exists())
            self.assertTrue((cli_out / "restricted_region_taskset_diagnostic_zh.md").exists())

    def test_b4_1_targeted_restricted_region_probe_stays_diagnostic(self) -> None:
        raw = generate_instance(5, seed=641001, index=1)
        data = load_lunar_ice_data(raw)
        tasks = list(data.task_ids)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance_path = tmp_path / "instance.json"
            instance_path.write_text(json.dumps(raw), encoding="utf-8")
            probe = tmp_path / "probe.json"
            probe.write_text(
                json.dumps(
                    {
                        "instance_id": "targeted-region-smoke",
                        "instance_path": str(instance_path),
                        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                        "history": [
                            {
                                "round": 1,
                                "dual_context": {
                                    "task_duals": {task: 0.1 for task in tasks},
                                    "fleet_dual": 0.0,
                                    "cut_duals": {},
                                },
                            }
                        ],
                        "final_judge": {
                            "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
                            "global_remaining_rc_lb": -0.7,
                            "global_remaining_rc_lb_coverage_complete": False,
                            "frontier_unsupported_region_count": 3,
                            "harvest_reports": [
                                {
                                    "true_reduced_cost": -0.7,
                                    "pricing_reduced_cost": -0.7,
                                    "task_set": tasks[:2],
                                    "would_enter_master": True,
                                    "selected_after_addability_audit": True,
                                },
                                {
                                    "true_reduced_cost": -0.2,
                                    "pricing_reduced_cost": -0.2,
                                    "task_set": tasks[1:4],
                                    "would_enter_master": True,
                                    "selected_after_addability_audit": True,
                                },
                                {
                                    "true_reduced_cost": -0.01,
                                    "pricing_reduced_cost": -0.01,
                                    "task_set": tasks[2:5],
                                    "would_enter_master": True,
                                    "selected_after_addability_audit": True,
                                },
                            ],
                            "compact_pricing_phase_payloads": {
                                "optimization_harvest_3": {
                                    "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                                    "exact_status": "NOT_SOLVED",
                                    "best_reduced_cost": -0.01,
                                    "dual_bound": -0.12,
                                    "wall_time_sec": 20.0,
                                    "forbidden_task_set_count": 2,
                                },
                                "optimization_harvest_4": {
                                    "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                                    "exact_status": "NOT_SOLVED",
                                    "best_reduced_cost": 0.3,
                                    "dual_bound": -0.3,
                                    "wall_time_sec": 10.0,
                                    "forbidden_task_set_count": 3,
                                },
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(
                b4_1_runner_module,
                "solve_highs_compact_single_journey_pricing",
                side_effect=[
                    {
                        "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                        "exact_status": "NOT_SOLVED",
                        "pricing_state": "INCOMPLETE_LIMIT",
                        "best_reduced_cost": -0.04,
                        "dual_bound": -0.08,
                        "negative_found": True,
                        "negative_column_count": 1,
                        "wall_time_sec": 3.0,
                        "pricing_rc_audit_pass": True,
                        "variable_count": 10,
                        "constraint_count": 20,
                        "single_journey_mip_start_enabled": True,
                        "single_journey_mip_start_status": "OK",
                        "single_journey_mip_start_source": "column_pool_journey",
                        "single_journey_mip_start_entry_count": 12,
                        "single_journey_mip_start_sortie_count": 1,
                        "single_journey_mip_start_task_count": 2,
                        "single_journey_mip_start_objective": 0.4,
                        "single_journey_mip_start_reduced_cost": -0.04,
                        "required_task_set_enabled": True,
                        "required_task_set_count": 2,
                        "required_task_set_region_can_certify_no_negative": False,
                        "pricing_complete_for_required_task_set": True,
                    },
                    {
                        "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
                        "exact_status": "RESTRICTED_PRICING_OPTIMAL",
                        "pricing_state": "FOUND_NEGATIVE",
                        "best_reduced_cost": -0.03,
                        "dual_bound": -0.02,
                        "negative_found": True,
                        "negative_column_count": 1,
                        "wall_time_sec": 4.0,
                        "pricing_rc_audit_pass": True,
                        "variable_count": 11,
                        "constraint_count": 22,
                        "service_start_depot_travel_lb_enabled": True,
                        "task_to_depot_return_travel_lb_enabled": True,
                        "pair_route_duration_lb_enabled": True,
                        "sortie_slot_position_bounds_enabled": True,
                        "pair_energy_infeasible_cut_enabled": True,
                        "pair_time_window_infeasible_cut_enabled": True,
                        "pair_time_window_infeasible_cut_count": 7,
                        "pair_time_window_infeasible_pair_count": 7,
                        "pair_time_window_infeasible_margin_min": 0.25,
                        "pair_time_window_infeasible_margin_max": 4.0,
                    },
                ],
            ) as mocked_solver:
                report = b4_1_runner_module.run_b4_1_targeted_restricted_region_probe(
                    probe,
                    variants=(
                        "V2_latest_service_start_slot_bound",
                        "V4_current_strengthening",
                    ),
                    time_limit_sec=5.0,
                    max_regions=1,
                )

            self.assertEqual(report["row_count"], 2)
            self.assertTrue(report["diagnostic_only"])
            self.assertFalse(report["can_claim_certificate"])
            self.assertEqual(report["redlines"]["certificate_claim_count"], 0)
            self.assertEqual(report["redlines"]["restricted_no_good_claimed_certificate_count"], 0)
            self.assertEqual(report["summary"][0]["region_id"], "prefix_2")
            self.assertEqual(report["summary"][0]["forbidden_task_set_count"], 2)
            self.assertEqual(report["summary"][0]["best_bound_variant"], "V4_current_strengthening")
            self.assertEqual(report["summary"][0]["source_bound_improved_count"], 2)
            self.assertTrue(all(row["official_certificate_allowed"] is False for row in report["rows"]))
            self.assertTrue(all(row["can_certify_no_negative"] is False for row in report["rows"]))
            self.assertEqual(mocked_solver.call_count, 2)
            first_call_kwargs = mocked_solver.call_args_list[0].kwargs
            self.assertEqual(len(first_call_kwargs["forbidden_task_sets"]), 2)
            self.assertEqual(tuple(first_call_kwargs["forbidden_task_sets"][0]), tuple(sorted(tasks[:2])))
            self.assertFalse(first_call_kwargs["pair_time_window_infeasible_cut"])
            second_call_kwargs = mocked_solver.call_args_list[1].kwargs
            self.assertFalse(second_call_kwargs["pair_shadow_lb"])
            self.assertTrue(second_call_kwargs["pair_time_window_infeasible_cut"])
            self.assertFalse(second_call_kwargs["pair_time_window_precedence_cut"])
            self.assertTrue(report["rows"][0]["single_journey_mip_start_enabled"])
            self.assertEqual(report["rows"][0]["single_journey_mip_start_status"], "OK")
            self.assertEqual(report["rows"][0]["single_journey_mip_start_entry_count"], 12)
            self.assertEqual(report["rows"][0]["single_journey_mip_start_task_count"], 2)
            self.assertTrue(report["rows"][0]["required_task_set_enabled"])
            self.assertEqual(report["rows"][0]["required_task_set_count"], 2)
            self.assertTrue(report["rows"][0]["pricing_complete_for_required_task_set"])
            self.assertEqual(report["rows"][1]["pair_time_window_infeasible_cut_count"], 7)
            self.assertEqual(report["rows"][1]["pair_time_window_infeasible_pair_count"], 7)
            self.assertEqual(report["rows"][1]["pair_time_window_infeasible_margin_min"], 0.25)

            b4_1_runner_module.write_b4_1_targeted_restricted_region_probe(
                report,
                summary_json=tmp_path / "targeted.json",
                report_md=tmp_path / "targeted_zh.md",
            )
            self.assertIn(
                "diagnostic-only",
                (tmp_path / "targeted_zh.md").read_text(encoding="utf-8"),
            )

            with patch.object(
                b4_1_runner_module,
                "solve_highs_compact_single_journey_pricing",
                return_value={
                    "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                    "exact_status": "NOT_SOLVED",
                    "pricing_state": "INCOMPLETE_LIMIT",
                    "best_reduced_cost": 0.01,
                    "dual_bound": -0.3,
                    "negative_found": False,
                    "negative_column_count": 0,
                    "wall_time_sec": 1.0,
                    "pair_weighted_completion_lb_enabled": True,
                    "pair_weighted_completion_lb_count": 25,
                    "pair_weighted_completion_lb_min": 1.0,
                    "pair_weighted_completion_lb_max": 9.0,
                },
            ) as targeted_region_solver:
                prefix_3_report = b4_1_runner_module.run_b4_1_targeted_restricted_region_probe(
                    probe,
                    variants=("V4_current_pair_weighted_completion_lb",),
                    time_limit_sec=5.0,
                    target_region_ids=("prefix_3",),
                )

            self.assertEqual(prefix_3_report["target_region_ids"], ["prefix_3"])
            self.assertEqual(prefix_3_report["row_count"], 1)
            self.assertEqual(prefix_3_report["rows"][0]["region_id"], "prefix_3")
            self.assertEqual(prefix_3_report["rows"][0]["forbidden_task_set_count"], 3)
            self.assertEqual(prefix_3_report["rows"][0]["variant"], "V4_current_pair_weighted_completion_lb")
            self.assertTrue(prefix_3_report["rows"][0]["pair_weighted_completion_lb_enabled"])
            self.assertEqual(prefix_3_report["rows"][0]["pair_weighted_completion_lb_count"], 25)
            self.assertEqual(targeted_region_solver.call_count, 1)
            self.assertEqual(len(targeted_region_solver.call_args.kwargs["forbidden_task_sets"]), 3)
            self.assertTrue(targeted_region_solver.call_args.kwargs["pair_weighted_completion_lb"])

            with patch.object(
                b4_1_runner_module,
                "solve_highs_compact_single_journey_pricing",
                return_value={
                    "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                    "exact_status": "NOT_SOLVED",
                    "pricing_state": "INCOMPLETE_LIMIT",
                    "best_reduced_cost": 0.02,
                    "dual_bound": -0.25,
                    "negative_found": False,
                    "negative_column_count": 0,
                    "wall_time_sec": 1.5,
                    "triple_time_window_infeasible_cut_enabled": True,
                    "triple_time_window_infeasible_cut_count": 30,
                    "triple_time_window_infeasible_triple_count": 10,
                    "triple_time_window_infeasible_margin_min": 0.75,
                    "triple_time_window_infeasible_margin_max": 8.0,
                },
            ) as triple_tw_solver:
                triple_tw_report = b4_1_runner_module.run_b4_1_targeted_restricted_region_probe(
                    probe,
                    variants=("V4_current_triple_time_window_infeasible",),
                    time_limit_sec=5.0,
                    target_region_ids=("prefix_3",),
                )

            self.assertEqual(triple_tw_report["row_count"], 1)
            self.assertEqual(triple_tw_report["rows"][0]["variant"], "V4_current_triple_time_window_infeasible")
            self.assertTrue(triple_tw_report["rows"][0]["triple_time_window_infeasible_cut_enabled"])
            self.assertEqual(triple_tw_report["rows"][0]["triple_time_window_infeasible_cut_count"], 30)
            self.assertEqual(triple_tw_report["rows"][0]["triple_time_window_infeasible_triple_count"], 10)
            self.assertEqual(triple_tw_solver.call_count, 1)
            self.assertTrue(triple_tw_solver.call_args.kwargs["triple_time_window_infeasible_cut"])
            self.assertFalse(triple_tw_report["can_claim_certificate"])

            with patch.object(
                b4_1_runner_module,
                "solve_highs_compact_single_journey_pricing",
                return_value={
                    "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                    "exact_status": "NOT_SOLVED",
                    "pricing_state": "INCOMPLETE_LIMIT",
                    "best_reduced_cost": -0.03,
                    "dual_bound": -0.2,
                    "negative_found": True,
                    "negative_column_count": 1,
                    "wall_time_sec": 2.0,
                    "best_column": {
                        "task_count": 2,
                        "tasks": ["ice_site_099", "ice_site_100"],
                    },
                    "journeys": (
                        SimpleNamespace(
                            to_solution_payload=lambda *, vehicle_id: {
                                "vehicle_id": vehicle_id,
                                "sorties": [
                                    {
                                        "tasks": ["ice_site_099", "ice_site_100"],
                                        "legs": [
                                            {
                                                "from": "depot",
                                                "to": "ice_site_099",
                                                "path_type": "low_time",
                                            },
                                            {
                                                "from": "ice_site_099",
                                                "to": "ice_site_100",
                                                "path_type": "low_risk",
                                            },
                                            {
                                                "from": "ice_site_100",
                                                "to": "depot",
                                                "path_type": "low_time",
                                            },
                                        ],
                                        "start_time": 0.0,
                                    }
                                ],
                                "objective_breakdown": {"objective": 1.25},
                            }
                        ),
                    ),
                    "quad_time_window_infeasible_cut_enabled": True,
                    "quad_time_window_infeasible_cut_count": 12,
                    "quad_time_window_infeasible_quad_count": 4,
                    "quad_time_window_infeasible_margin_min": 1.25,
                    "quad_time_window_infeasible_margin_max": 9.5,
                },
            ) as quad_tw_solver:
                quad_tw_report = b4_1_runner_module.run_b4_1_targeted_restricted_region_probe(
                    probe,
                    variants=("V4_current_quad_time_window_infeasible",),
                    time_limit_sec=5.0,
                    target_region_ids=("prefix_3",),
                )

            self.assertEqual(quad_tw_report["row_count"], 1)
            self.assertEqual(quad_tw_report["rows"][0]["variant"], "V4_current_quad_time_window_infeasible")
            self.assertTrue(quad_tw_report["rows"][0]["quad_time_window_infeasible_cut_enabled"])
            self.assertEqual(quad_tw_report["rows"][0]["quad_time_window_infeasible_cut_count"], 12)
            self.assertEqual(quad_tw_report["rows"][0]["quad_time_window_infeasible_quad_count"], 4)
            self.assertEqual(
                quad_tw_report["rows"][0]["targeted_negative_task_set"],
                ["ice_site_099", "ice_site_100"],
            )
            self.assertEqual(quad_tw_report["rows"][0]["targeted_negative_task_set_size"], 2)
            self.assertEqual(quad_tw_report["rows"][0]["targeted_negative_true_rc"], -0.03)
            self.assertEqual(
                quad_tw_report["rows"][0]["targeted_negative_source_phase"],
                "optimization_harvest_4",
            )
            self.assertFalse(quad_tw_report["rows"][0]["targeted_negative_task_set_forbidden_seen"])
            self.assertEqual(
                quad_tw_report["rows"][0]["targeted_negative_solution_payload"]["vehicle_id"],
                "targeted_restricted_region_negative",
            )
            self.assertEqual(
                quad_tw_report["rows"][0]["targeted_negative_solution_payload"]["sorties"][0]["tasks"],
                ["ice_site_099", "ice_site_100"],
            )
            self.assertEqual(quad_tw_solver.call_count, 1)
            self.assertTrue(quad_tw_solver.call_args.kwargs["quad_time_window_infeasible_cut"])
            self.assertFalse(quad_tw_report["can_claim_certificate"])

            with self.assertRaisesRegex(ValueError, "prefix_999"):
                b4_1_runner_module.run_b4_1_targeted_restricted_region_probe(
                    probe,
                    variants=("V4_current_strengthening",),
                    target_region_ids=("prefix_999",),
                )

    def test_b4_1_required_task_set_partition_probe_is_diagnostic_candidate(self) -> None:
        raw = generate_instance(5, seed=641001, index=1)
        data = load_lunar_ice_data(raw)
        tasks = list(data.task_ids)
        first_task_set = tuple(sorted(tasks[:2]))
        second_task_set = tuple(sorted(tasks[2:4]))
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        first_start = next(
            column for column in universe.columns if tuple(sorted(column.task_set)) == first_task_set
        )
        second_start = next(
            column for column in universe.columns if tuple(sorted(column.task_set)) == second_task_set
        )
        residual_start = next(
            column
            for column in universe.columns
            if tuple(sorted(column.task_set)) not in {first_task_set, second_task_set}
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance_path = tmp_path / "instance.json"
            instance_path.write_text(json.dumps(raw), encoding="utf-8")
            probe = tmp_path / "probe.json"
            probe.write_text(
                json.dumps(
                    {
                        "instance_id": "partition-probe-smoke",
                        "instance_path": str(instance_path),
                        "history": [
                            {
                                "round": 1,
                                "dual_context": {
                                    "task_duals": {task: 0.1 for task in tasks},
                                    "fleet_dual": 0.0,
                                    "cut_duals": {},
                                },
                            }
                        ],
                        "active_columns": [
                            first_start.to_solution_payload(vehicle_id="warm_exact_001"),
                            second_start.to_solution_payload(vehicle_id="warm_exact_002"),
                            residual_start.to_solution_payload(vehicle_id="warm_residual_001"),
                        ],
                        "final_judge": {
                            "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
                            "global_remaining_rc_lb": -0.5,
                            "harvest_reports": [
                                {
                                    "true_reduced_cost": -0.4,
                                    "pricing_reduced_cost": -0.4,
                                    "task_set": list(first_task_set),
                                    "would_enter_master": True,
                                    "selected_after_addability_audit": True,
                                },
                                {
                                    "true_reduced_cost": -0.2,
                                    "pricing_reduced_cost": -0.2,
                                    "task_set": list(second_task_set),
                                    "would_enter_master": True,
                                    "selected_after_addability_audit": True,
                                },
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )
            side_effect = [
                {
                    "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
                    "exact_status": "REQUIRED_TASK_SET_PRICING_OPTIMAL",
                    "pricing_state": "CERTIFIED_NO_NEGATIVE",
                    "best_reduced_cost": 0.11,
                    "dual_bound": 0.11,
                    "negative_found": False,
                    "negative_column_count": 0,
                    "pricing_complete_for_required_task_set": True,
                    "required_task_set_enabled": True,
                    "required_task_set_count": len(first_task_set),
                    "required_task_set_region_can_certify_no_negative": True,
                    "variable_count": 10,
                    "constraint_count": 20,
                    "pricing_rc_audit_pass": True,
                },
                {
                    "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
                    "exact_status": "REQUIRED_TASK_SET_PRICING_OPTIMAL",
                    "pricing_state": "CERTIFIED_NO_NEGATIVE",
                    "best_reduced_cost": 0.07,
                    "dual_bound": 0.07,
                    "negative_found": False,
                    "negative_column_count": 0,
                    "pricing_complete_for_required_task_set": True,
                    "required_task_set_enabled": True,
                    "required_task_set_count": len(second_task_set),
                    "required_task_set_region_can_certify_no_negative": True,
                    "variable_count": 11,
                    "constraint_count": 22,
                    "pricing_rc_audit_pass": True,
                },
                {
                    "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
                    "exact_status": "RESTRICTED_PRICING_OPTIMAL",
                    "pricing_state": "CERTIFIED_NO_NEGATIVE",
                    "best_reduced_cost": 0.03,
                    "dual_bound": 0.03,
                    "negative_found": False,
                    "negative_column_count": 0,
                    "forbidden_task_set_count": 2,
                    "variable_count": 12,
                    "constraint_count": 24,
                    "pricing_rc_audit_pass": True,
                },
            ]
            with patch.object(
                b4_1_runner_module,
                "solve_highs_compact_single_journey_pricing",
                side_effect=side_effect,
            ) as mocked_solver:
                report = b4_1_runner_module.run_b4_1_required_task_set_partition_probe(
                    probe,
                    variants=("V4_current_strengthening",),
                    time_limit_sec=5.0,
                )

            self.assertEqual(report["row_count"], 3)
            self.assertTrue(report["diagnostic_only"])
            self.assertFalse(report["official_certificate_allowed"])
            self.assertFalse(report["can_claim_certificate"])
            self.assertEqual(report["redlines"]["certificate_claim_count"], 0)
            self.assertEqual(report["redlines"]["official_certificate_claim_count"], 0)
            self.assertEqual(report["redlines"]["full_space_certificate_claim_count"], 0)
            summary = report["summary"]
            self.assertTrue(summary["partition_regions_disjoint"])
            self.assertTrue(summary["partition_regions_cover_full_space"])
            self.assertTrue(summary["partition_candidate_complete"])
            self.assertTrue(summary["partition_candidate_can_certify_no_negative"])
            self.assertTrue(summary["partition_candidate_gate_pass"])
            self.assertEqual(summary["partition_candidate_gate_issue_codes"], [])
            self.assertTrue(summary["partition_candidate_gate_full_space_partition_valid"])
            self.assertEqual(summary["partition_candidate_gate_exact_regions_proven"], 2)
            self.assertTrue(summary["partition_candidate_gate_residual_proven"])
            self.assertFalse(summary["partition_candidate_gate_official_certificate_allowed"])
            self.assertFalse(summary["official_certificate_allowed"])
            self.assertEqual(summary["exact_region_proven_count"], 2)
            self.assertTrue(summary["residual_region_proven"])
            self.assertEqual(summary["best_partition_region_lb"], 0.03)
            self.assertEqual(mocked_solver.call_count, 3)
            self.assertEqual(tuple(mocked_solver.call_args_list[0].kwargs["required_task_set"]), first_task_set)
            self.assertEqual(tuple(mocked_solver.call_args_list[1].kwargs["required_task_set"]), second_task_set)
            self.assertIsNotNone(mocked_solver.call_args_list[0].kwargs["mip_start_journey"])
            self.assertEqual(
                tuple(sorted(mocked_solver.call_args_list[0].kwargs["mip_start_journey"].task_set)),
                first_task_set,
            )
            self.assertIsNotNone(mocked_solver.call_args_list[1].kwargs["mip_start_journey"])
            self.assertEqual(
                tuple(sorted(mocked_solver.call_args_list[1].kwargs["mip_start_journey"].task_set)),
                second_task_set,
            )
            self.assertEqual(
                tuple(tuple(row) for row in mocked_solver.call_args_list[2].kwargs["forbidden_task_sets"]),
                (first_task_set, second_task_set),
            )
            self.assertIsNotNone(mocked_solver.call_args_list[2].kwargs["mip_start_journey"])
            self.assertNotIn(
                tuple(sorted(mocked_solver.call_args_list[2].kwargs["mip_start_journey"].task_set)),
                {first_task_set, second_task_set},
            )
            exact_row = report["rows"][0]
            self.assertTrue(exact_row["region_can_certify_no_negative"])
            self.assertFalse(exact_row["can_certify_no_negative"])
            self.assertEqual(exact_row["region_kind"], "exact_task_set")
            residual_row = report["rows"][2]
            self.assertEqual(residual_row["region_kind"], "residual_after_exact_task_sets")
            self.assertTrue(residual_row["region_can_certify_no_negative"])

            out_json = tmp_path / "partition.json"
            out_md = tmp_path / "partition_zh.md"
            b4_1_runner_module.write_b4_1_required_task_set_partition_probe(
                report,
                summary_json=out_json,
                report_md=out_md,
            )
            self.assertTrue(out_json.exists())
            markdown = out_md.read_text(encoding="utf-8")
            self.assertIn("diagnostic-only", markdown)
            self.assertIn("partition_candidate_complete", markdown)
            self.assertIn("partition_candidate_gate_pass", markdown)

            audit = b4_1_runner_module.build_b4_1_partition_candidate_audit([out_json])
            self.assertTrue(audit["diagnostic_only"])
            self.assertFalse(audit["official_certificate_allowed"])
            self.assertFalse(audit["can_claim_certificate"])
            self.assertEqual(audit["partition_probe_count"], 1)
            self.assertEqual(audit["partition_gate_pass_count"], 1)
            self.assertEqual(audit["partition_gate_fail_count"], 0)
            self.assertEqual(audit["partition_candidate_can_certify_no_negative_count"], 1)
            self.assertEqual(audit["partition_gate_issue_counts"], {})
            self.assertEqual(audit["redline_fail_count"], 0)
            self.assertEqual(
                audit["redlines"]["partition_row_certificate_claim_count"],
                0,
            )
            audit_json = tmp_path / "partition_audit.json"
            audit_md = tmp_path / "partition_audit_zh.md"
            b4_1_runner_module.write_b4_1_partition_candidate_audit(
                audit,
                summary_json=audit_json,
                report_md=audit_md,
            )
            audit_markdown = audit_md.read_text(encoding="utf-8")
            self.assertIn("Partition Candidate Audit", audit_markdown)
            self.assertIn("partition_gate_pass_count", audit_markdown)

            project_root = Path(__file__).resolve().parents[1]
            cli_out = tmp_path / "partition_cli"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "scripts" / "run_lunar_ice_b4_1_true_dual_proof_tail.py"),
                    "--output-dir",
                    str(cli_out),
                    "--stage-b-v4-root-tail-partition-proof",
                    "--partition-region-result-json",
                    str(out_json),
                    "--no-resume",
                ],
                cwd=project_root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            cli_audit = json.loads((cli_out / "partition_candidate_audit.json").read_text(encoding="utf-8"))
            self.assertEqual(cli_audit["partition_gate_pass_count"], 1)
            self.assertEqual(cli_audit["redline_fail_count"], 0)
            self.assertTrue((cli_out / "partition_candidate_audit_zh.md").exists())
            cli_summary = json.loads((cli_out / "b4_1_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(cli_summary["diagnostics"]["partition_candidate_audit_row_count"], 1)
            self.assertEqual(cli_summary["diagnostics"]["partition_candidate_gate_pass_count"], 1)
            self.assertEqual(cli_summary["redlines"]["partition_candidate_certificate_leak_count"], 0)
            self.assertTrue((cli_out / "b4_1_report_zh.md").exists())

            empty_alias_out = tmp_path / "partition_empty_alias_cli"
            empty_alias = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "scripts" / "run_lunar_ice_b4_1_true_dual_proof_tail.py"),
                    "--output-dir",
                    str(empty_alias_out),
                    "--stage-b-v4-root-tail-partition-proof",
                    "--no-resume",
                ],
                cwd=project_root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(empty_alias.returncode, 2)
            self.assertIn("no partition probe JSON", empty_alias.stderr)
            self.assertFalse((empty_alias_out / "partition_candidate_audit.json").exists())

            cli_spec = importlib.util.spec_from_file_location(
                "b4_1_cli_smoke",
                project_root / "scripts" / "run_lunar_ice_b4_1_true_dual_proof_tail.py",
            )
            self.assertIsNotNone(cli_spec)
            self.assertIsNotNone(cli_spec.loader)
            cli_module = importlib.util.module_from_spec(cli_spec)
            cli_spec.loader.exec_module(cli_module)
            alias_args = SimpleNamespace(
                stage_b_v4_root_tail_partition_proof=True,
                source_probe_json=["probe.json"],
                required_task_set_partition_proof_probe=False,
                partition_candidate_audit=False,
                partition_candidate_audit_import_rows=False,
                partition_region_max_task_sets=0,
            )
            cli_module._apply_stage_b_v4_root_tail_partition_alias(alias_args)
            self.assertTrue(alias_args.required_task_set_partition_proof_probe)
            self.assertTrue(alias_args.partition_candidate_audit)
            self.assertTrue(alias_args.partition_candidate_audit_import_rows)
            self.assertEqual(
                alias_args.partition_region_max_task_sets,
                cli_module.B41_ROOT_TAIL_PARTITION_DEFAULT_MAX_TASK_SETS,
            )
            explicit_alias_args = SimpleNamespace(
                stage_b_v4_root_tail_partition_proof=True,
                source_probe_json=["probe.json"],
                required_task_set_partition_proof_probe=False,
                partition_candidate_audit=False,
                partition_candidate_audit_import_rows=False,
                partition_region_max_task_sets=9,
            )
            cli_module._apply_stage_b_v4_root_tail_partition_alias(explicit_alias_args)
            self.assertEqual(explicit_alias_args.partition_region_max_task_sets, 9)

            evidence_rows = b4_1_runner_module.rows_from_b4_1_partition_candidate_audit(audit_json)
            self.assertEqual(len(evidence_rows), 1)
            self.assertEqual(evidence_rows[0]["mode"], "B4.1_partition_candidate_audit")
            self.assertEqual(evidence_rows[0]["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
            self.assertFalse(evidence_rows[0]["can_certify_no_negative"])
            self.assertTrue(evidence_rows[0]["underlying_can_certify_no_negative"])
            self.assertTrue(evidence_rows[0]["partition_candidate_gate_pass"])
            self.assertEqual(evidence_rows[0]["partition_candidate_redline_fail_count"], 0)
            main_report = b4_1_runner_module.build_b4_1_report(evidence_rows)
            self.assertEqual(main_report["redlines"]["partition_candidate_certificate_leak_count"], 0)
            self.assertEqual(main_report["diagnostics"]["partition_candidate_audit_row_count"], 1)
            self.assertEqual(main_report["diagnostics"]["partition_candidate_gate_pass_count"], 1)
            self.assertEqual(main_report["diagnostics"]["partition_candidate_gate_fail_count"], 0)
            self.assertEqual(
                main_report["diagnostics"]["partition_candidate_can_certify_no_negative_count"],
                1,
            )
            self.assertFalse(main_report["acceptance"]["b4_1_full_experiment_complete"])

            import_out = tmp_path / "partition_import_cli"
            imported = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "scripts" / "run_lunar_ice_b4_1_true_dual_proof_tail.py"),
                    "--output-dir",
                    str(import_out),
                    "--import-partition-candidate-audit-json",
                    str(audit_json),
                    "--no-resume",
                ],
                cwd=project_root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(imported.returncode, 0, imported.stderr)
            imported_summary = json.loads((import_out / "b4_1_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(imported_summary["diagnostics"]["partition_candidate_audit_row_count"], 1)
            self.assertEqual(imported_summary["diagnostics"]["partition_candidate_gate_pass_count"], 1)
            self.assertEqual(imported_summary["redlines"]["partition_candidate_certificate_leak_count"], 0)
            self.assertTrue((import_out / "b4_1_report_zh.md").exists())

    def test_b4_1_residual_task_count_partition_probe_is_fail_closed_until_complete(self) -> None:
        raw = generate_instance(5, seed=641002, index=1)
        data = load_lunar_ice_data(raw)
        tasks = list(data.task_ids)
        first_task_set = tuple(sorted(tasks[:2]))
        second_task_set = tuple(sorted(tasks[2:4]))
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        first_start = next(
            column for column in universe.columns if tuple(sorted(column.task_set)) == first_task_set
        )
        second_start = next(
            column for column in universe.columns if tuple(sorted(column.task_set)) == second_task_set
        )
        residual_count_one_start = next(
            column
            for column in universe.columns
            if len(column.task_set) == 1
            and tuple(sorted(column.task_set)) not in {first_task_set, second_task_set}
        )
        residual_count_two_start = next(
            column
            for column in universe.columns
            if len(column.task_set) == 2
            and tuple(sorted(column.task_set)) not in {first_task_set, second_task_set}
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance_path = tmp_path / "instance.json"
            instance_path.write_text(json.dumps(raw), encoding="utf-8")
            probe = tmp_path / "probe.json"
            probe.write_text(
                json.dumps(
                    {
                        "instance_id": "partition-task-count-smoke",
                        "instance_path": str(instance_path),
                        "history": [
                            {
                                "round": 1,
                                "dual_context": {
                                    "task_duals": {task: 0.1 for task in tasks},
                                    "fleet_dual": 0.0,
                                    "cut_duals": {},
                                },
                            }
                        ],
                        "active_columns": [
                            first_start.to_solution_payload(vehicle_id="warm_exact_001"),
                            second_start.to_solution_payload(vehicle_id="warm_exact_002"),
                            residual_count_one_start.to_solution_payload(vehicle_id="warm_residual_k1"),
                            residual_count_two_start.to_solution_payload(vehicle_id="warm_residual_k2"),
                        ],
                        "final_judge": {
                            "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
                            "harvest_reports": [
                                {
                                    "true_reduced_cost": -0.4,
                                    "pricing_reduced_cost": -0.4,
                                    "task_set": list(first_task_set),
                                    "would_enter_master": True,
                                    "selected_after_addability_audit": True,
                                },
                                {
                                    "true_reduced_cost": -0.2,
                                    "pricing_reduced_cost": -0.2,
                                    "task_set": list(second_task_set),
                                    "would_enter_master": True,
                                    "selected_after_addability_audit": True,
                                },
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            exact_result = {
                "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
                "exact_status": "REQUIRED_TASK_SET_PRICING_OPTIMAL",
                "pricing_state": "CERTIFIED_NO_NEGATIVE",
                "best_reduced_cost": 0.11,
                "dual_bound": 0.11,
                "negative_found": False,
                "negative_column_count": 0,
                "pricing_complete_for_required_task_set": True,
                "required_task_set_enabled": True,
                "required_task_set_region_can_certify_no_negative": True,
                "pricing_rc_audit_pass": True,
                "single_journey_mip_start_enabled": True,
                "single_journey_mip_start_status": "OK",
            }
            task_count_one = {
                "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
                "exact_status": "REQUIRED_TASK_COUNT_PRICING_OPTIMAL",
                "pricing_state": "CERTIFIED_NO_NEGATIVE",
                "best_reduced_cost": 0.08,
                "dual_bound": 0.08,
                "negative_found": False,
                "negative_column_count": 0,
                "pricing_complete_for_required_task_count": True,
                "required_task_count_enabled": True,
                "required_task_count": 1,
                "required_task_count_region_can_certify_no_negative": True,
                "pricing_rc_audit_pass": True,
                "single_journey_mip_start_enabled": True,
                "single_journey_mip_start_status": "OK",
            }
            task_count_two = dict(task_count_one)
            task_count_two.update(
                {
                    "best_reduced_cost": 0.05,
                    "dual_bound": 0.05,
                    "required_task_count": 2,
                }
            )
            with patch.object(
                b4_1_runner_module,
                "solve_highs_compact_single_journey_pricing",
                side_effect=[dict(exact_result), dict(exact_result), task_count_one, task_count_two],
            ) as mocked_solver:
                report = b4_1_runner_module.run_b4_1_required_task_set_partition_probe(
                    probe,
                    variants=("V4_current_strengthening",),
                    time_limit_sec=5.0,
                    residual_task_count_partition=True,
                    residual_task_count_max_regions=2,
                )

            self.assertEqual(report["row_count"], 4)
            summary = report["summary"]
            self.assertTrue(summary["residual_task_count_partition_enabled"])
            self.assertEqual(summary["residual_task_count_region_expected_count"], len(tasks))
            self.assertEqual(summary["residual_task_count_region_observed_count"], 2)
            self.assertEqual(summary["residual_task_count_region_proven_count"], 2)
            self.assertEqual(summary["residual_task_count_region_missing_count"], len(tasks) - 2)
            self.assertEqual(summary["residual_task_count_region_missing_counts"], [3, 4, 5])
            self.assertFalse(summary["partition_regions_cover_full_space"])
            self.assertFalse(summary["partition_candidate_gate_pass"])
            self.assertIn(
                "missing_residual_task_count_region",
                summary["partition_candidate_gate_issue_codes"],
            )
            self.assertEqual(mocked_solver.call_count, 4)
            self.assertEqual(tuple(mocked_solver.call_args_list[0].kwargs["required_task_set"]), first_task_set)
            self.assertEqual(tuple(mocked_solver.call_args_list[1].kwargs["required_task_set"]), second_task_set)
            self.assertEqual(mocked_solver.call_args_list[2].kwargs["required_task_count"], 1)
            self.assertEqual(mocked_solver.call_args_list[3].kwargs["required_task_count"], 2)
            self.assertEqual(
                tuple(tuple(row) for row in mocked_solver.call_args_list[2].kwargs["forbidden_task_sets"]),
                (first_task_set, second_task_set),
            )
            self.assertEqual(
                tuple(tuple(row) for row in mocked_solver.call_args_list[3].kwargs["forbidden_task_sets"]),
                (first_task_set, second_task_set),
            )
            self.assertIsNotNone(mocked_solver.call_args_list[2].kwargs["mip_start_journey"])
            self.assertEqual(len(mocked_solver.call_args_list[2].kwargs["mip_start_journey"].task_set), 1)
            self.assertIsNotNone(mocked_solver.call_args_list[3].kwargs["mip_start_journey"])
            self.assertEqual(len(mocked_solver.call_args_list[3].kwargs["mip_start_journey"].task_set), 2)
            self.assertEqual(summary["partition_residual_region_mip_start_ok_count"], 2)

            out_json = tmp_path / "partition_task_count.json"
            b4_1_runner_module.write_b4_1_required_task_set_partition_probe(
                report,
                summary_json=out_json,
                report_md=tmp_path / "partition_task_count_zh.md",
            )
            audit = b4_1_runner_module.build_b4_1_partition_candidate_audit([out_json])
            self.assertEqual(audit["partition_gate_fail_count"], 1)
            self.assertEqual(audit["partition_gate_pass_count"], 0)
            self.assertEqual(audit["partition_residual_region_mip_start_ok_count"], 2)
            self.assertEqual(audit["residual_task_count_partition_enabled_count"], 1)
            self.assertEqual(audit["residual_task_count_region_observed_count"], 2)
            self.assertEqual(audit["residual_task_count_region_missing_count"], len(tasks) - 2)
            self.assertEqual(
                audit["partition_gate_issue_counts"]["missing_residual_task_count_region"],
                1,
            )
            audit_json = tmp_path / "partition_task_count_audit.json"
            b4_1_runner_module.write_b4_1_partition_candidate_audit(
                audit,
                summary_json=audit_json,
                report_md=tmp_path / "partition_task_count_audit_zh.md",
            )
            evidence_rows = b4_1_runner_module.rows_from_b4_1_partition_candidate_audit(audit_json)
            self.assertEqual(len(evidence_rows), 1)
            self.assertFalse(evidence_rows[0]["partition_candidate_gate_pass"])
            self.assertTrue(evidence_rows[0]["residual_task_count_partition_enabled"])
            self.assertEqual(evidence_rows[0]["residual_task_count_region_observed_count"], 2)
            main_report = b4_1_runner_module.build_b4_1_report(evidence_rows)
            self.assertEqual(
                main_report["diagnostics"]["residual_task_count_partition_enabled_count"],
                1,
            )
            self.assertEqual(
                main_report["diagnostics"]["residual_task_count_region_missing_count"],
                len(tasks) - 2,
            )
            self.assertEqual(main_report["redlines"]["partition_candidate_certificate_leak_count"], 0)

            pure_probe = tmp_path / "pure_residual_probe.json"
            pure_probe.write_text(
                json.dumps(
                    {
                        "instance_id": "pure-residual-task-count-smoke",
                        "instance_path": str(instance_path),
                        "history": [
                            {
                                "round": 1,
                                "dual_context": {
                                    "task_duals": {task: 0.1 for task in tasks},
                                    "fleet_dual": 0.0,
                                    "cut_duals": {},
                                },
                            }
                        ],
                        "active_columns": [
                            residual_count_one_start.to_solution_payload(vehicle_id="pure_warm_k1"),
                            residual_count_two_start.to_solution_payload(vehicle_id="pure_warm_k2"),
                        ],
                        "final_judge": {
                            "pricing_proof_kind": "EXHAUSTIVE_NO_NEGATIVE",
                            "harvest_reports": [],
                        },
                    }
                ),
                encoding="utf-8",
            )
            pure_side_effect = []
            for required_count in range(1, len(tasks) + 1):
                row = dict(task_count_one)
                row.update(
                    {
                        "best_reduced_cost": 0.01 * required_count,
                        "dual_bound": 0.01 * required_count,
                        "required_task_count": required_count,
                    }
                )
                pure_side_effect.append(row)
            with patch.object(
                b4_1_runner_module,
                "solve_highs_compact_single_journey_pricing",
                side_effect=pure_side_effect,
            ) as pure_mocked_solver:
                pure_report = b4_1_runner_module.run_b4_1_required_task_set_partition_probe(
                    pure_probe,
                    variants=("V4_current_strengthening",),
                    time_limit_sec=5.0,
                    residual_task_count_partition=True,
                    residual_task_count_max_regions=len(tasks),
                )

            pure_summary = pure_report["summary"]
            self.assertEqual(pure_report["target_task_set_count"], 0)
            self.assertEqual(pure_report["row_count"], len(tasks))
            self.assertTrue(pure_summary["partition_regions_cover_full_space"])
            self.assertTrue(pure_summary["partition_candidate_gate_pass"])
            self.assertTrue(pure_summary["partition_candidate_can_certify_no_negative"])
            self.assertFalse(pure_summary["official_certificate_allowed"])
            self.assertEqual(pure_summary["partition_candidate_gate_issue_codes"], [])
            self.assertEqual(pure_summary["residual_task_count_region_observed_count"], len(tasks))
            self.assertEqual(pure_summary["residual_task_count_region_proven_count"], len(tasks))
            self.assertEqual(pure_summary["residual_task_count_region_missing_count"], 0)
            self.assertEqual(pure_mocked_solver.call_count, len(tasks))
            self.assertEqual(pure_mocked_solver.call_args_list[0].kwargs["forbidden_task_sets"], [])

    def test_b4_1_adaptive_active_sortie_refinement_discards_failed_coarse_region(self) -> None:
        raw = generate_instance(5, seed=641004, index=1)
        data = load_lunar_ice_data(raw)
        tasks = list(data.task_ids)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        warm_columns = []
        for task_count in range(1, len(tasks) + 1):
            warm_columns.append(
                next(column for column in universe.columns if len(column.task_set) == task_count)
            )

        def certified_task_count_row(required_count: int) -> dict:
            return {
                "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
                "exact_status": "REQUIRED_TASK_COUNT_PRICING_OPTIMAL",
                "pricing_state": "CERTIFIED_NO_NEGATIVE",
                "best_reduced_cost": 0.01 * required_count,
                "dual_bound": 0.01 * required_count,
                "negative_found": False,
                "negative_column_count": 0,
                "pricing_complete_for_required_task_count": True,
                "required_task_count_enabled": True,
                "required_task_count": required_count,
                "required_task_count_region_can_certify_no_negative": True,
                "pricing_rc_audit_pass": True,
                "single_journey_mip_start_enabled": True,
                "single_journey_mip_start_status": "OK",
            }

        def timeout_task_count_row(required_count: int) -> dict:
            row = certified_task_count_row(required_count)
            row.update(
                {
                    "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                    "exact_status": "REQUIRED_TASK_COUNT_PRICING_TIME_LIMIT_REACHED",
                    "pricing_state": "FAIL_CLOSED",
                    "best_reduced_cost": 0.02,
                    "dual_bound": -0.25,
                    "pricing_complete_for_required_task_count": False,
                    "required_task_count_region_can_certify_no_negative": False,
                }
            )
            return row

        def certified_active_sortie_row(required_count: int, active_count: int) -> dict:
            row = certified_task_count_row(required_count)
            row.update(
                {
                    "exact_status": "REQUIRED_ACTIVE_SORTIE_COUNT_PRICING_OPTIMAL",
                    "required_active_sortie_count_enabled": True,
                    "required_active_sortie_count": active_count,
                    "required_active_sortie_count_expected_counts": list(
                        range(1, required_count + 1)
                    ),
                    "pricing_complete_for_required_active_sortie_count": True,
                    "required_active_sortie_count_region_can_certify_no_negative": True,
                }
            )
            return row

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance_path = tmp_path / "instance.json"
            instance_path.write_text(json.dumps(raw), encoding="utf-8")
            probe = tmp_path / "adaptive_probe.json"
            probe.write_text(
                json.dumps(
                    {
                        "instance_id": "adaptive-active-sortie-smoke",
                        "instance_path": str(instance_path),
                        "history": [
                            {
                                "round": 1,
                                "dual_context": {
                                    "task_duals": {task: 0.1 for task in tasks},
                                    "fleet_dual": 0.0,
                                    "cut_duals": {},
                                },
                            }
                        ],
                        "active_columns": [
                            column.to_solution_payload(vehicle_id=f"warm_k{index}")
                            for index, column in enumerate(warm_columns, start=1)
                        ],
                        "final_judge": {
                            "pricing_proof_kind": "EXHAUSTIVE_NO_NEGATIVE",
                            "harvest_reports": [],
                        },
                    }
                ),
                encoding="utf-8",
            )
            side_effect = [
                certified_task_count_row(1),
                timeout_task_count_row(2),
                certified_active_sortie_row(2, 1),
                certified_active_sortie_row(2, 2),
                certified_task_count_row(3),
                certified_task_count_row(4),
                certified_task_count_row(5),
            ]
            with patch.object(
                b4_1_runner_module,
                "solve_highs_compact_single_journey_pricing",
                side_effect=side_effect,
            ) as mocked_solver:
                report = b4_1_runner_module.run_b4_1_required_task_set_partition_probe(
                    probe,
                    variants=("V4_current_strengthening",),
                    time_limit_sec=5.0,
                    residual_task_count_partition=True,
                    residual_task_count_max_regions=len(tasks),
                    residual_active_sortie_count_partition=True,
                    residual_active_sortie_count_min=1,
                    residual_active_sortie_count_max=len(tasks),
                    residual_active_sortie_adaptive_refinement=True,
                )

            summary = report["summary"]
            rows = report["rows"]
            self.assertEqual(mocked_solver.call_count, 7)
            self.assertEqual(report["row_count"], 6)
            self.assertTrue(summary["partition_regions_cover_full_space"])
            self.assertTrue(summary["partition_candidate_gate_pass"])
            self.assertTrue(summary["partition_candidate_can_certify_no_negative"])
            self.assertFalse(summary["official_certificate_allowed"])
            self.assertEqual(summary["partition_candidate_gate_issue_codes"], [])
            self.assertTrue(summary["residual_task_count_partition_enabled"])
            self.assertTrue(summary["residual_active_sortie_count_partition_enabled"])
            self.assertEqual(summary["residual_task_count_region_observed_count"], len(tasks))
            self.assertEqual(summary["residual_task_count_region_proven_count"], len(tasks))
            self.assertEqual(summary["residual_task_count_region_missing_count"], 0)
            self.assertEqual(summary["residual_active_sortie_count_missing_group_count"], 0)
            self.assertEqual(summary["residual_active_sortie_count_duplicate_group_count"], 0)
            self.assertTrue(summary["partition_adaptive_active_sortie_refinement_enabled"])
            self.assertEqual(summary["partition_adaptive_active_sortie_refinement_attempt_count"], 5)
            self.assertEqual(
                summary["partition_adaptive_active_sortie_refinement_coarse_accepted_count"],
                4,
            )
            self.assertEqual(summary["partition_adaptive_active_sortie_refinement_refined_count"], 1)
            self.assertGreaterEqual(
                summary["partition_adaptive_active_sortie_refinement_discarded_coarse_wall_time_sec"],
                0.0,
            )
            self.assertNotIn("residual_task_count_002", {row["region_id"] for row in rows})
            self.assertEqual(
                {
                    (row["region_id"], row["partition_adaptive_active_sortie_refinement_role"])
                    for row in rows
                },
                {
                    ("residual_task_count_001", "coarse_accepted"),
                    ("residual_task_count_002_active_sorties_001", "refined_active_sortie"),
                    ("residual_task_count_002_active_sorties_002", "refined_active_sortie"),
                    ("residual_task_count_003", "coarse_accepted"),
                    ("residual_task_count_004", "coarse_accepted"),
                    ("residual_task_count_005", "coarse_accepted"),
                },
            )
            self.assertIsNone(mocked_solver.call_args_list[0].kwargs["required_active_sortie_count"])
            self.assertIsNone(mocked_solver.call_args_list[1].kwargs["required_active_sortie_count"])
            self.assertEqual(mocked_solver.call_args_list[2].kwargs["required_active_sortie_count"], 1)
            self.assertEqual(mocked_solver.call_args_list[3].kwargs["required_active_sortie_count"], 2)
            self.assertIsNone(mocked_solver.call_args_list[4].kwargs["required_active_sortie_count"])
            self.assertIsNone(mocked_solver.call_args_list[5].kwargs["required_active_sortie_count"])
            self.assertIsNone(mocked_solver.call_args_list[6].kwargs["required_active_sortie_count"])

    def test_b4_1_residual_task_count_partition_negative_feasibility_fallback(self) -> None:
        raw = generate_instance(5, seed=641003, index=1)
        data = load_lunar_ice_data(raw)
        tasks = list(data.task_ids)
        first_task_set = tuple(sorted(tasks[:2]))
        second_task_set = tuple(sorted(tasks[2:4]))
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        first_start = next(
            column for column in universe.columns if tuple(sorted(column.task_set)) == first_task_set
        )
        second_start = next(
            column for column in universe.columns if tuple(sorted(column.task_set)) == second_task_set
        )
        residual_count_one_start = next(
            column
            for column in universe.columns
            if len(column.task_set) == 1
            and tuple(sorted(column.task_set)) not in {first_task_set, second_task_set}
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance_path = tmp_path / "instance.json"
            instance_path.write_text(json.dumps(raw), encoding="utf-8")
            probe = tmp_path / "probe.json"
            probe.write_text(
                json.dumps(
                    {
                        "instance_id": "partition-task-count-fallback-smoke",
                        "instance_path": str(instance_path),
                        "history": [
                            {
                                "round": 1,
                                "dual_context": {
                                    "task_duals": {task: 0.1 for task in tasks},
                                    "fleet_dual": 0.0,
                                    "cut_duals": {},
                                },
                            }
                        ],
                        "active_columns": [
                            first_start.to_solution_payload(vehicle_id="warm_exact_001"),
                            second_start.to_solution_payload(vehicle_id="warm_exact_002"),
                            residual_count_one_start.to_solution_payload(vehicle_id="warm_residual_k1"),
                        ],
                        "final_judge": {
                            "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
                            "harvest_reports": [
                                {
                                    "true_reduced_cost": -0.4,
                                    "pricing_reduced_cost": -0.4,
                                    "task_set": list(first_task_set),
                                    "would_enter_master": True,
                                    "selected_after_addability_audit": True,
                                },
                                {
                                    "true_reduced_cost": -0.2,
                                    "pricing_reduced_cost": -0.2,
                                    "task_set": list(second_task_set),
                                    "would_enter_master": True,
                                    "selected_after_addability_audit": True,
                                },
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )
            exact_result = {
                "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
                "exact_status": "REQUIRED_TASK_SET_PRICING_OPTIMAL",
                "pricing_state": "CERTIFIED_NO_NEGATIVE",
                "best_reduced_cost": 0.11,
                "dual_bound": 0.11,
                "negative_found": False,
                "negative_column_count": 0,
                "pricing_complete_for_required_task_set": True,
                "required_task_set_enabled": True,
                "required_task_set_region_can_certify_no_negative": True,
                "pricing_rc_audit_pass": True,
            }
            incomplete_optimization = {
                "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT",
                "exact_status": "NOT_SOLVED",
                "pricing_state": "INCOMPLETE_LIMIT",
                "best_reduced_cost": 0.02,
                "dual_bound": None,
                "negative_found": False,
                "negative_column_count": 0,
                "pricing_complete_for_required_task_count": False,
                "required_task_count_enabled": True,
                "required_task_count": 1,
                "required_task_count_region_can_certify_no_negative": False,
                "pricing_rc_audit_pass": True,
            }
            fallback_infeasible = {
                "status": "COMPACT_HIGHS_PRICING_RESTRICTED_INFEASIBLE",
                "exact_status": "RESTRICTED_NEGATIVE_FEASIBILITY_INFEASIBLE",
                "pricing_state": "INCOMPLETE_LIMIT",
                "best_reduced_cost": None,
                "dual_bound": None,
                "negative_found": False,
                "negative_column_count": 0,
                "pricing_complete_for_required_task_count": True,
                "required_task_count_enabled": True,
                "required_task_count": 1,
                "required_task_count_region_can_certify_no_negative": True,
                "pricing_rc_audit_pass": True,
            }
            with patch.object(
                b4_1_runner_module,
                "solve_highs_compact_single_journey_pricing",
                side_effect=[dict(exact_result), dict(exact_result), incomplete_optimization, fallback_infeasible],
            ) as mocked_solver:
                report = b4_1_runner_module.run_b4_1_required_task_set_partition_probe(
                    probe,
                    variants=("V4_current_strengthening",),
                    time_limit_sec=5.0,
                    residual_task_count_partition=True,
                    residual_task_count_max_regions=1,
                    negative_feasibility_fallback=True,
                )

            self.assertEqual(mocked_solver.call_count, 4)
            self.assertFalse(mocked_solver.call_args_list[2].kwargs["negative_feasibility_search"])
            self.assertTrue(mocked_solver.call_args_list[3].kwargs["negative_feasibility_search"])
            residual_row = report["rows"][2]
            self.assertEqual(residual_row["region_kind"], "residual_task_count")
            self.assertEqual(residual_row["exact_status"], "RESTRICTED_NEGATIVE_FEASIBILITY_INFEASIBLE")
            self.assertTrue(residual_row["region_pricing_complete"])
            self.assertTrue(residual_row["region_can_certify_no_negative"])
            self.assertTrue(residual_row["partition_negative_feasibility_fallback_enabled"])
            self.assertTrue(residual_row["partition_negative_feasibility_fallback_run"])
            self.assertTrue(residual_row["partition_negative_feasibility_fallback_used"])
            self.assertEqual(
                residual_row["partition_negative_feasibility_fallback_exact_status"],
                "RESTRICTED_NEGATIVE_FEASIBILITY_INFEASIBLE",
            )
            self.assertEqual(residual_row["partition_optimization_best_reduced_cost"], 0.02)
            summary = report["summary"]
            self.assertEqual(summary["residual_task_count_region_observed_count"], 1)
            self.assertEqual(summary["residual_task_count_region_proven_count"], 1)
            self.assertFalse(summary["partition_candidate_gate_pass"])
            self.assertIn(
                "missing_residual_task_count_region",
                summary["partition_candidate_gate_issue_codes"],
            )
            self.assertFalse(report["can_claim_certificate"])
            self.assertEqual(report["redlines"]["certificate_claim_count"], 0)

    def test_b4_1_partition_candidate_gate_rejects_unsafe_rows(self) -> None:
        first_task_set = ("ice_site_001", "ice_site_002")
        second_task_set = ("ice_site_003", "ice_site_004")
        task_sets = [first_task_set, second_task_set]

        negative_journey = SimpleNamespace(
            task_set=frozenset(first_task_set),
            to_solution_payload=lambda *, vehicle_id: {
                "vehicle_id": vehicle_id,
                "sorties": [
                    {
                        "tasks": list(first_task_set),
                        "legs": [
                            {"from": "depot", "to": first_task_set[0], "path_type": "low_time"},
                            {"from": first_task_set[0], "to": first_task_set[1], "path_type": "low_risk"},
                            {"from": first_task_set[1], "to": "depot", "path_type": "low_time"},
                        ],
                        "start_time": 0.0,
                    }
                ],
            },
        )
        negative_probe_row = b4_1_runner_module._partition_probe_row(
            {
                "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
                "exact_status": "REQUIRED_TASK_SET_PRICING_OPTIMAL",
                "pricing_state": "FOUND_NEGATIVE",
                "best_reduced_cost": -0.015,
                "dual_bound": -0.014,
                "negative_found": True,
                "negative_column_count": 1,
                "pricing_complete_for_required_task_set": True,
                "required_task_set_region_can_certify_no_negative": False,
                "journeys": (negative_journey,),
            },
            source_probe_json=Path("probe.json"),
            instance_id="partition-negative-payload-smoke",
            history_round=1,
            region_id="exact_001",
            region_kind="exact_task_set",
            task_set=first_task_set,
            forbidden_task_sets=tuple(),
            variant="V4_current_strengthening",
            formulation_kind="v4_current_strengthening",
            wall_time=0.25,
            negative_eps=1.0e-6,
            source_active_column_count=10,
            dual_active_column_count=5,
        )
        self.assertTrue(negative_probe_row["negative_found"])
        self.assertEqual(negative_probe_row["partition_negative_task_set"], list(first_task_set))
        self.assertEqual(negative_probe_row["partition_negative_task_set_size"], 2)
        self.assertEqual(negative_probe_row["partition_negative_true_rc"], -0.015)
        self.assertEqual(negative_probe_row["partition_negative_source_region_id"], "exact_001")
        self.assertTrue(negative_probe_row["partition_negative_payload_available"])
        self.assertFalse(negative_probe_row["partition_negative_already_active"])
        self.assertFalse(negative_probe_row["partition_negative_active_task_set_seen"])
        self.assertEqual(
            negative_probe_row["partition_negative_replacement_or_new_task_set"],
            "new_task_set",
        )
        self.assertEqual(negative_probe_row["partition_source_active_column_count"], 10)
        self.assertEqual(negative_probe_row["partition_dual_active_column_count"], 5)
        self.assertEqual(negative_probe_row["partition_active_pool_after_dual_delta"], 5)
        self.assertFalse(negative_probe_row["partition_dual_scope_matches_active_pool"])
        self.assertEqual(negative_probe_row["partition_negative_rc_audit_pass"], "")
        self.assertEqual(
            negative_probe_row["partition_negative_solution_payload"]["vehicle_id"],
            "targeted_restricted_region_negative",
        )
        self.assertEqual(
            negative_probe_row["partition_negative_solution_payload"]["sorties"][0]["tasks"],
            list(first_task_set),
        )
        negative_result = {
            "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
            "exact_status": "REQUIRED_TASK_SET_PRICING_OPTIMAL",
            "pricing_state": "FOUND_NEGATIVE",
            "best_reduced_cost": -0.015,
            "dual_bound": -0.014,
            "negative_found": True,
            "negative_column_count": 1,
            "pricing_complete_for_required_task_set": True,
            "required_task_set_region_can_certify_no_negative": False,
            "journeys": (negative_journey,),
        }
        replacement_probe_row = b4_1_runner_module._partition_probe_row(
            negative_result,
            source_probe_json=Path("probe.json"),
            instance_id="partition-replacement-payload-smoke",
            history_round=1,
            region_id="exact_001",
            region_kind="exact_task_set",
            task_set=first_task_set,
            forbidden_task_sets=tuple(),
            variant="V4_current_strengthening",
            formulation_kind="v4_current_strengthening",
            wall_time=0.25,
            negative_eps=1.0e-6,
            active_task_sets={first_task_set},
            active_column_keys=set(),
            source_active_column_count=10,
            dual_active_column_count=5,
        )
        self.assertTrue(replacement_probe_row["partition_negative_active_task_set_seen"])
        self.assertFalse(replacement_probe_row["partition_negative_already_active"])
        self.assertEqual(
            replacement_probe_row["partition_negative_replacement_or_new_task_set"],
            "replacement",
        )
        active_column_key = b4_1_runner_module._solution_payload_column_key(
            negative_probe_row["partition_negative_solution_payload"]
        )
        already_active_probe_row = b4_1_runner_module._partition_probe_row(
            negative_result,
            source_probe_json=Path("probe.json"),
            instance_id="partition-already-active-payload-smoke",
            history_round=1,
            region_id="exact_001",
            region_kind="exact_task_set",
            task_set=first_task_set,
            forbidden_task_sets=tuple(),
            variant="V4_current_strengthening",
            formulation_kind="v4_current_strengthening",
            wall_time=0.25,
            negative_eps=1.0e-6,
            active_task_sets={first_task_set},
            active_column_keys={active_column_key},
            source_active_column_count=10,
            dual_active_column_count=10,
            dual_source="refreshed_active_pool_restricted_rmp",
            dual_refresh_payload={
                "partition_dual_refresh_status": "RESTRICTED_RMP_OPTIMAL",
                "partition_dual_refresh_min_rc": 0.0,
                "partition_dual_refresh_negative_count": 0,
                "partition_dual_refresh_input_column_count": 10,
                "partition_dual_refresh_rmp_active_column_count": 10,
            },
        )
        self.assertTrue(already_active_probe_row["partition_negative_active_task_set_seen"])
        self.assertTrue(already_active_probe_row["partition_negative_already_active"])
        self.assertEqual(
            already_active_probe_row["partition_negative_replacement_or_new_task_set"],
            "already_active",
        )
        self.assertEqual(
            already_active_probe_row["partition_dual_source"],
            "refreshed_active_pool_restricted_rmp",
        )
        self.assertEqual(
            already_active_probe_row["partition_dual_refresh_status"],
            "RESTRICTED_RMP_OPTIMAL",
        )
        self.assertEqual(already_active_probe_row["partition_dual_refresh_negative_count"], 0)

        def row(
            *,
            region_id: str,
            region_kind: str,
            required_task_set: tuple[str, ...] = (),
            required_task_count: int | None = None,
            forbidden_task_sets: tuple[tuple[str, ...], ...] = (),
            negative_found: bool = False,
            region_complete: bool = True,
            region_certifies: bool = True,
            variant: str = "V4_current_strengthening",
            formulation_kind: str = "v4_current_strengthening",
            variable_count: int = 10,
            constraint_count: int = 20,
        ) -> dict:
            return {
                "source_probe_json": "probe.json",
                "instance_id": "partition-gate-smoke",
                "history_round": 1,
                "region_id": region_id,
                "region_kind": region_kind,
                "required_task_set": list(required_task_set),
                "required_task_count": required_task_count,
                "forbidden_task_sets": [list(item) for item in forbidden_task_sets],
                "variant": variant,
                "formulation_kind": formulation_kind,
                "best_reduced_cost": 0.05 if not negative_found else -0.02,
                "dual_bound": 0.05 if not negative_found else -0.02,
                "negative_found": negative_found,
                "region_pricing_complete": region_complete,
                "region_can_certify_no_negative": region_certifies,
                "region_can_certify_full_space": False,
                "official_certificate_allowed": False,
                "can_claim_certificate": False,
                "can_certify_no_negative": False,
                "diagnostic_only": True,
                "pricing_rc_audit_pass": True,
                "variable_count": variable_count,
                "constraint_count": constraint_count,
                "slot_task_time_feasible_assignment_count": 7,
                "slot_task_time_pruned_assignment_count": 3,
                "slot_arc_time_pruned_option_count": 2,
            }

        safe_rows = [
            row(region_id="exact_001", region_kind="exact_task_set", required_task_set=first_task_set),
            row(region_id="exact_002", region_kind="exact_task_set", required_task_set=second_task_set),
            row(
                region_id="residual_after_exact_task_sets",
                region_kind="residual_after_exact_task_sets",
                forbidden_task_sets=(first_task_set, second_task_set),
            ),
        ]
        safe_summary = b4_1_runner_module._partition_probe_summary(
            safe_rows,
            task_sets=task_sets,
            negative_eps=1.0e-6,
        )
        self.assertTrue(safe_summary["partition_candidate_gate_pass"])
        self.assertEqual(safe_summary["partition_candidate_gate_issue_codes"], [])

        missing_residual_summary = b4_1_runner_module._partition_probe_summary(
            safe_rows[:2],
            task_sets=task_sets,
            negative_eps=1.0e-6,
        )
        self.assertFalse(missing_residual_summary["partition_candidate_gate_pass"])
        self.assertIn(
            "missing_residual_region",
            missing_residual_summary["partition_candidate_gate_issue_codes"],
        )
        self.assertFalse(missing_residual_summary["partition_candidate_can_certify_no_negative"])

        negative_exact_rows = [
            row(
                region_id="exact_001",
                region_kind="exact_task_set",
                required_task_set=first_task_set,
                negative_found=True,
                region_certifies=False,
            ),
            safe_rows[1],
            safe_rows[2],
        ]
        negative_exact_summary = b4_1_runner_module._partition_probe_summary(
            negative_exact_rows,
            task_sets=task_sets,
            negative_eps=1.0e-6,
        )
        self.assertFalse(negative_exact_summary["partition_candidate_gate_pass"])
        self.assertIn(
            "negative_exact_task_set_region",
            negative_exact_summary["partition_candidate_gate_issue_codes"],
        )
        self.assertIn(
            "unproven_exact_task_set_region",
            negative_exact_summary["partition_candidate_gate_issue_codes"],
        )
        negative_payload_rows = [negative_probe_row, safe_rows[1], safe_rows[2]]
        negative_payload_summary = b4_1_runner_module._partition_probe_summary(
            negative_payload_rows,
            task_sets=task_sets,
            negative_eps=1.0e-6,
        )
        self.assertEqual(negative_payload_summary["exact_region_negative_count"], 1)
        self.assertEqual(negative_payload_summary["partition_negative_new_task_set_count"], 1)
        self.assertEqual(negative_payload_summary["partition_negative_replacement_task_set_count"], 0)
        self.assertEqual(negative_payload_summary["partition_negative_already_active_count"], 0)
        self.assertEqual(negative_payload_summary["partition_source_active_column_count"], 10)
        self.assertEqual(negative_payload_summary["partition_dual_active_column_count"], 5)
        self.assertEqual(negative_payload_summary["partition_active_pool_after_dual_delta"], 5)
        self.assertEqual(negative_payload_summary["partition_dual_scope_mismatch_count"], 1)
        self.assertEqual(negative_payload_summary["partition_negative_rc_audit_fail_count"], 0)

        bad_residual_rows = [
            safe_rows[0],
            safe_rows[1],
            row(
                region_id="residual_after_exact_task_sets",
                region_kind="residual_after_exact_task_sets",
                forbidden_task_sets=(first_task_set,),
            ),
        ]
        bad_residual_summary = b4_1_runner_module._partition_probe_summary(
            bad_residual_rows,
            task_sets=task_sets,
            negative_eps=1.0e-6,
        )
        self.assertFalse(bad_residual_summary["partition_candidate_gate_pass"])
        self.assertIn(
            "residual_forbidden_task_sets_do_not_match_exact_regions",
            bad_residual_summary["partition_candidate_gate_issue_codes"],
        )
        self.assertFalse(bad_residual_summary["partition_candidate_gate_full_space_partition_valid"])

        mixed_variant_rows = [
            safe_rows[0],
            row(
                region_id="exact_002",
                region_kind="exact_task_set",
                required_task_set=second_task_set,
                variant="V2_latest_service_start_slot_bound",
            ),
            safe_rows[2],
        ]
        mixed_variant_summary = b4_1_runner_module._partition_probe_summary(
            mixed_variant_rows,
            task_sets=task_sets,
            negative_eps=1.0e-6,
        )
        self.assertFalse(mixed_variant_summary["partition_candidate_gate_pass"])
        self.assertIn(
            "mixed_variant_partition_rows",
            mixed_variant_summary["partition_candidate_gate_issue_codes"],
        )

        mixed_variant_residual_rows = [
            row(
                region_id="residual_task_count_005",
                region_kind="residual_task_count",
                required_task_count=5,
                forbidden_task_sets=(first_task_set, second_task_set),
            ),
            row(
                region_id="residual_task_count_005",
                region_kind="residual_task_count",
                required_task_count=5,
                forbidden_task_sets=(first_task_set, second_task_set),
                negative_found=True,
                region_certifies=False,
                variant="V4_current_triple_time_window_infeasible",
                formulation_kind="v4_current_triple_time_window_infeasible",
                variable_count=12,
                constraint_count=24,
            ),
        ]
        mixed_variant_residual_summary = b4_1_runner_module._partition_probe_summary(
            mixed_variant_residual_rows,
            task_sets=task_sets,
            negative_eps=1.0e-6,
            total_task_count=5,
        )
        self.assertEqual(
            mixed_variant_residual_summary["residual_task_count_region_negative_count"],
            1,
        )
        self.assertEqual(mixed_variant_residual_summary["partition_best_negative_rc"], -0.02)
        self.assertEqual(mixed_variant_residual_summary["partition_region_variable_count_max"], 12)
        self.assertEqual(mixed_variant_residual_summary["partition_region_constraint_count_max"], 24)
        self.assertEqual(mixed_variant_residual_summary["partition_region_variable_count_mean"], 11.0)
        self.assertEqual(mixed_variant_residual_summary["partition_region_constraint_count_mean"], 22.0)
        self.assertEqual(
            mixed_variant_residual_summary[
                "partition_region_slot_task_time_feasible_assignment_count_max"
            ],
            7,
        )
        self.assertEqual(
            mixed_variant_residual_summary["partition_region_slot_task_time_pruned_assignment_count_sum"],
            6,
        )
        self.assertEqual(
            mixed_variant_residual_summary["partition_region_slot_arc_time_pruned_option_count_sum"],
            4,
        )
        self.assertFalse(mixed_variant_residual_summary["partition_candidate_gate_pass"])
        self.assertIn(
            "mixed_variant_partition_rows",
            mixed_variant_residual_summary["partition_candidate_gate_issue_codes"],
        )
        self.assertIn(
            "duplicate_residual_task_count_region",
            mixed_variant_residual_summary["partition_candidate_gate_issue_codes"],
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            unsafe_json = tmp_path / "unsafe_partition.json"
            unsafe_json.write_text(
                json.dumps(
                    {
                        "schema_version": "lunar_ice_bpc.b4_1_required_task_set_partition_probe.v1",
                        "instance_id": "partition-gate-smoke",
                        "diagnostic_only": True,
                        "official_certificate_allowed": False,
                        "can_claim_certificate": False,
                        "target_task_set_count": len(task_sets),
                        "row_count": len(bad_residual_rows),
                        "rows": bad_residual_rows,
                        "summary": bad_residual_summary,
                        "redlines": {
                            "certificate_claim_count": 0,
                            "official_certificate_claim_count": 0,
                            "full_space_certificate_claim_count": 0,
                        },
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            unsafe_audit = b4_1_runner_module.build_b4_1_partition_candidate_audit([unsafe_json])
            self.assertEqual(unsafe_audit["partition_gate_pass_count"], 0)
            self.assertEqual(unsafe_audit["partition_gate_fail_count"], 1)
            self.assertEqual(unsafe_audit["redline_fail_count"], 0)
            self.assertEqual(
                unsafe_audit["partition_gate_issue_counts"][
                    "residual_forbidden_task_sets_do_not_match_exact_regions"
                ],
                1,
            )
            self.assertFalse(unsafe_audit["can_claim_certificate"])
            unsafe_audit_json = tmp_path / "unsafe_audit.json"
            b4_1_runner_module.write_b4_1_partition_candidate_audit(
                unsafe_audit,
                summary_json=unsafe_audit_json,
                report_md=tmp_path / "unsafe_audit_zh.md",
            )
            unsafe_rows = b4_1_runner_module.rows_from_b4_1_partition_candidate_audit(unsafe_audit_json)
            self.assertEqual(len(unsafe_rows), 1)
            self.assertFalse(unsafe_rows[0]["partition_candidate_gate_pass"])
            self.assertFalse(unsafe_rows[0]["partition_candidate_can_certify_no_negative"])
            unsafe_report = b4_1_runner_module.build_b4_1_report(unsafe_rows)
            self.assertEqual(unsafe_report["diagnostics"]["partition_candidate_gate_fail_count"], 1)
            self.assertEqual(
                unsafe_report["diagnostics"]["partition_candidate_issue_counts"][
                    "residual_forbidden_task_sets_do_not_match_exact_regions"
                ],
                1,
            )
            self.assertEqual(unsafe_report["redlines"]["partition_candidate_certificate_leak_count"], 0)

            negative_json = tmp_path / "negative_partition.json"
            negative_json.write_text(
                json.dumps(
                    {
                        "schema_version": "lunar_ice_bpc.b4_1_required_task_set_partition_probe.v1",
                        "instance_id": "partition-negative-payload-smoke",
                        "diagnostic_only": True,
                        "official_certificate_allowed": False,
                        "can_claim_certificate": False,
                        "target_task_set_count": len(task_sets),
                        "row_count": len(negative_payload_rows),
                        "rows": negative_payload_rows,
                        "summary": negative_payload_summary,
                        "redlines": {
                            "certificate_claim_count": 0,
                            "official_certificate_claim_count": 0,
                            "full_space_certificate_claim_count": 0,
                        },
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            negative_audit = b4_1_runner_module.build_b4_1_partition_candidate_audit([negative_json])
            self.assertEqual(negative_audit["partition_negative_region_count"], 1)
            self.assertEqual(negative_audit["partition_negative_payload_available_count"], 1)
            self.assertEqual(negative_audit["partition_best_negative_rc"], -0.015)
            self.assertEqual(negative_audit["partition_negative_new_task_set_count"], 1)
            self.assertEqual(negative_audit["partition_negative_replacement_task_set_count"], 0)
            self.assertEqual(negative_audit["partition_negative_already_active_count"], 0)
            self.assertEqual(negative_audit["partition_dual_scope_mismatch_count"], 1)
            self.assertEqual(negative_audit["partition_negative_rc_audit_fail_count"], 0)
            self.assertEqual(negative_audit["redline_fail_count"], 0)
            negative_audit_json = tmp_path / "negative_audit.json"
            b4_1_runner_module.write_b4_1_partition_candidate_audit(
                negative_audit,
                summary_json=negative_audit_json,
                report_md=tmp_path / "negative_audit_zh.md",
            )
            negative_rows = b4_1_runner_module.rows_from_b4_1_partition_candidate_audit(
                negative_audit_json
            )
            self.assertEqual(negative_rows[0]["partition_negative_region_count"], 1)
            self.assertEqual(negative_rows[0]["partition_negative_payload_available_count"], 1)
            self.assertEqual(negative_rows[0]["partition_best_negative_rc"], -0.015)
            self.assertEqual(negative_rows[0]["partition_negative_new_task_set_count"], 1)
            self.assertEqual(negative_rows[0]["partition_dual_scope_mismatch_count"], 1)
            self.assertEqual(negative_rows[0]["partition_active_pool_after_dual_delta"], 5)
            negative_report = b4_1_runner_module.build_b4_1_report(negative_rows)
            self.assertEqual(negative_report["diagnostics"]["partition_negative_region_count"], 1)
            self.assertEqual(
                negative_report["diagnostics"]["partition_negative_payload_available_count"],
                1,
            )
            self.assertEqual(negative_report["diagnostics"]["partition_best_negative_rc"], -0.015)
            self.assertEqual(negative_report["diagnostics"]["partition_negative_new_task_set_count"], 1)
            self.assertEqual(
                negative_report["diagnostics"]["partition_negative_already_active_count"],
                0,
            )
            self.assertEqual(negative_report["diagnostics"]["partition_dual_scope_mismatch_count"], 1)
            self.assertEqual(negative_report["diagnostics"]["partition_active_pool_after_dual_delta_max"], 5)
            self.assertEqual(negative_report["diagnostics"]["partition_negative_rc_audit_fail_count"], 0)
            self.assertEqual(
                negative_report["redlines"]["partition_candidate_certificate_leak_count"],
                0,
            )

    def test_merge_targeted_restricted_region_column_into_probe(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            base = tmp_path / "base_probe.json"
            targeted = tmp_path / "targeted.json"
            merged = tmp_path / "merged_probe.json"
            base.write_text(
                json.dumps(
                    {
                        "instance_id": "merge-targeted-smoke",
                        "active_columns": [],
                    }
                ),
                encoding="utf-8",
            )
            first_payload = {
                "vehicle_id": "first",
                "sorties": [
                    {
                        "tasks": ["ice_site_001"],
                        "legs": [
                            {"from": "depot", "to": "ice_site_001", "path_type": "low_time"},
                            {"from": "ice_site_001", "to": "depot", "path_type": "low_time"},
                        ],
                        "start_time": 0.0,
                    }
                ],
            }
            best_payload = {
                "vehicle_id": "best",
                "sorties": [
                    {
                        "tasks": ["ice_site_002", "ice_site_003"],
                        "legs": [
                            {"from": "depot", "to": "ice_site_002", "path_type": "low_risk"},
                            {"from": "ice_site_002", "to": "ice_site_003", "path_type": "low_time"},
                            {"from": "ice_site_003", "to": "depot", "path_type": "low_risk"},
                        ],
                        "start_time": 10.0,
                    }
                ],
            }
            targeted.write_text(
                json.dumps(
                    {
                        "schema_version": "lunar_ice_bpc.b4_1_targeted_restricted_region_probe.v1",
                        "instance_id": "merge-targeted-smoke",
                        "rows": [
                            {
                                "region_id": "prefix_2",
                                "variant": "V4_current_strengthening",
                                "targeted_negative_true_rc": -0.01,
                                "targeted_negative_task_set": ["ice_site_001"],
                                "targeted_negative_solution_payload": first_payload,
                                "dual_bound": -0.2,
                            },
                            {
                                "region_id": "prefix_3",
                                "variant": "V4_current_triple_time_window_infeasible",
                                "targeted_negative_true_rc": -0.05,
                                "targeted_negative_task_set": ["ice_site_002", "ice_site_003"],
                                "targeted_negative_solution_payload": best_payload,
                                "dual_bound": -0.15,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "scripts" / "merge_lunar_ice_replay_column_into_probe.py"),
                    "--base-probe",
                    str(base),
                    "--targeted-json",
                    str(targeted),
                    "--output-json",
                    str(merged),
                    "--vehicle-id",
                    "merged_targeted_best",
                ],
                cwd=project_root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(merged.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["active_columns"]), 1)
            self.assertEqual(payload["active_columns"][0]["vehicle_id"], "merged_targeted_best")
            self.assertEqual(payload["active_columns"][0]["sorties"][0]["tasks"], ["ice_site_002", "ice_site_003"])
            self.assertTrue(payload["merged_replay_column"]["added"])
            self.assertEqual(
                payload["merged_replay_column"]["source_kind"],
                "b4_1_targeted_restricted_region_probe",
            )
            self.assertEqual(payload["merged_replay_column"]["targeted_row_index"], 1)
            self.assertEqual(payload["merged_replay_column"]["replay_best_reduced_cost"], -0.05)

            partition = tmp_path / "partition.json"
            partition_merged = tmp_path / "partition_merged.json"
            partition_duplicate = tmp_path / "partition_duplicate.json"
            partition.write_text(
                json.dumps(
                    {
                        "schema_version": "lunar_ice_bpc.b4_1_required_task_set_partition_probe.v1",
                        "instance_id": "merge-targeted-smoke",
                        "rows": [
                            {
                                "region_id": "exact_001",
                                "region_kind": "exact_task_set",
                                "variant": "V4_current_strengthening",
                                "partition_negative_true_rc": -0.02,
                                "partition_negative_task_set": ["ice_site_004"],
                                "partition_negative_solution_payload": first_payload,
                                "dual_bound": -0.025,
                            },
                            {
                                "region_id": "exact_002",
                                "region_kind": "exact_task_set",
                                "variant": "V4_current_strengthening",
                                "partition_negative_true_rc": -0.08,
                                "partition_negative_task_set": ["ice_site_002", "ice_site_003"],
                                "partition_negative_solution_payload": best_payload,
                                "dual_bound": -0.081,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            partition_completed = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "scripts" / "merge_lunar_ice_replay_column_into_probe.py"),
                    "--base-probe",
                    str(base),
                    "--partition-json",
                    str(partition),
                    "--output-json",
                    str(partition_merged),
                    "--vehicle-id",
                    "merged_partition_best",
                ],
                cwd=project_root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(partition_completed.returncode, 0, partition_completed.stderr)
            partition_payload = json.loads(partition_merged.read_text(encoding="utf-8"))
            self.assertEqual(len(partition_payload["active_columns"]), 1)
            self.assertEqual(partition_payload["active_columns"][0]["vehicle_id"], "merged_partition_best")
            self.assertEqual(
                partition_payload["active_columns"][0]["sorties"][0]["tasks"],
                ["ice_site_002", "ice_site_003"],
            )
            self.assertTrue(partition_payload["merged_replay_column"]["added"])
            self.assertEqual(
                partition_payload["merged_replay_column"]["source_kind"],
                "b4_1_required_task_set_partition_probe",
            )
            self.assertEqual(partition_payload["merged_replay_column"]["partition_row_index"], 1)
            self.assertEqual(partition_payload["merged_replay_column"]["replay_best_reduced_cost"], -0.08)

            duplicate_completed = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "scripts" / "merge_lunar_ice_replay_column_into_probe.py"),
                    "--base-probe",
                    str(partition_merged),
                    "--partition-json",
                    str(partition),
                    "--output-json",
                    str(partition_duplicate),
                    "--vehicle-id",
                    "merged_partition_best_again",
                ],
                cwd=project_root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(duplicate_completed.returncode, 0, duplicate_completed.stderr)
            duplicate_payload = json.loads(partition_duplicate.read_text(encoding="utf-8"))
            self.assertEqual(len(duplicate_payload["active_columns"]), 1)
            self.assertFalse(duplicate_payload["merged_replay_column"]["added"])
            self.assertEqual(duplicate_payload["merged_replay_column"]["after_active_column_count"], 1)

    def test_staged_resume_report_refreshes_feasibility_proof_rows(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "staged"
            stage_dir = out / "stage_001"
            stage_dir.mkdir(parents=True)
            probe = stage_dir / "probe.json"
            probe.write_text(
                json.dumps(
                    {
                        "instance_id": "staged-refresh-smoke",
                        "config": {"resume_initial_column_count": 364},
                        "elapsed_sec": 42.0,
                        "algorithm_status": "BPC_INCOMPLETE_PRICING",
                        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                        "pricing_state": "INCOMPLETE_LIMIT",
                        "pricing_round_count": 1,
                        "added_column_count": 1,
                        "active_columns": [{"vehicle_id": "c"}],
                        "final_judge": {
                            "compact_pricing_phase": "negative_feasibility_proof",
                            "compact_final_judge_profile": "V4",
                            "compact_final_judge_phase_mode": "feasibility_proof_only",
                            "negative_feasibility_full_space_proof_can_certify": False,
                            "best_reduced_cost": -0.003,
                            "dual_bound": -0.004,
                            "compact_pricing_phase_payloads": {
                                "negative_feasibility_proof": {
                                    "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
                                    "exact_status": "EXACT_PRICING_OPTIMAL",
                                    "pricing_state": "FOUND_NEGATIVE",
                                    "negative_found": True,
                                    "best_reduced_cost": -0.003,
                                    "dual_bound": -0.004,
                                    "wall_time_sec": 41.0,
                                }
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            manifest = {
                "schema_version": "lunar_ice_bpc.compact_pricing_staged_resume.v1",
                "instance_path": "unused_instance.json",
                "latest_probe": str(probe),
                "stages": [
                    {
                        "stage_index": 1,
                        "probe_path": str(probe),
                        "compact_final_judge_phase_mode": "feasibility_proof_only",
                    }
                ],
            }
            (out / "staged_resume_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "scripts" / "run_lunar_ice_compact_pricing_staged_resume.py"),
                    "--instance",
                    "unused_instance.json",
                    "--output-dir",
                    str(out),
                    "--stage-count",
                    "0",
                    "--compact-final-judge-profile",
                    "V4",
                    "--compact-final-judge-phase-mode",
                    "feasibility_proof_only",
                ],
                cwd=project_root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            refreshed = json.loads((out / "staged_resume_manifest.json").read_text(encoding="utf-8"))
            row = refreshed["stages"][0]
            self.assertEqual(row["feasibility_proof_status"], "COMPACT_HIGHS_PRICING_OPTIMAL")
            self.assertTrue(row["feasibility_proof_negative_found"])
            self.assertFalse(row["feasibility_proof_can_certify"])
            report = (out / "staged_resume_report_zh.md").read_text(encoding="utf-8")
            self.assertIn("feas status", report)
            self.assertIn("COMPACT_HIGHS_PRICING_OPTIMAL", report)

    def test_b4_1_report_tracks_underlying_30_root_no_negative_without_tree_claim(self) -> None:
        report = b4_1_runner_module.build_b4_1_report(
            [
                {
                    "stage": "B",
                    "matrix_group": "B4.1 Stage B 30-scale root-tail feasibility closure evidence",
                    "source_probe_json": "runs/example_sp50_030/stage_002/probe.json",
                    "instance_id": "lunar_ice_sp50_030_001_seed929001",
                    "mode": "B4.1_probe_final_judge_evidence",
                    "variant": "V4_combined_endpoint_pair_latest_start_time_window",
                    "b4_1_matrix_cell": "B4V4_combined_formulation_diagnostic",
                    "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                    "underlying_certificate_scope": "BPC_NODE_LP_CERTIFIED",
                    "can_certify_no_negative": False,
                    "underlying_can_certify_no_negative": True,
                    "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
                    "underlying_pricing_proof_kind": "EXHAUSTIVE_NO_NEGATIVE",
                    "underlying_frontier_coverage_complete": True,
                    "underlying_frontier_unsupported_region_count": 0,
                    "active_columns_after_merge": 371,
                    "active_column_count": 371,
                    "columns_added": 0,
                    "diagnostic_claimed_certificate": 0,
                    "manual_rc_fail": 0,
                    "pricing_rc_fail": 0,
                    "certificate_leak": 0,
                }
            ]
        )

        self.assertEqual(report["diagnostics"]["thirty_scale_underlying_node_lp_certified_count"], 1)
        self.assertEqual(report["diagnostics"]["thirty_scale_underlying_exhaustive_no_negative_count"], 1)
        latest = report["latest_frontier_rows"][0]
        self.assertEqual(latest["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
        self.assertEqual(latest["underlying_certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertTrue(latest["underlying_can_certify_no_negative"])
        r7 = {row["id"]: row for row in report["requirement_audit"]}["R7_30_scale_exact_closure"]
        self.assertEqual(r7["status"], "incomplete")
        self.assertEqual(r7["evidence"]["thirty_scale_underlying_node_lp_certified_count"], 1)
        self.assertEqual(r7["evidence"]["thirty_scale_bpc_tree_optimal_count"], 0)

    def test_b4_1_stage_d_tree_closure_row_satisfies_r7_without_stage_b_leak(self) -> None:
        report = b4_1_runner_module.build_b4_1_report(
            [
                {
                    "stage": "D",
                    "matrix_group": "B4.1 Stage D 30-scale tree closure from root-tail probe",
                    "source_probe_json": "runs/example_sp50_030/stage_002/probe.json",
                    "instance_path": "data/instances/lunar_ice_sp50_030/instance_001_logical_graph.json",
                    "scale": 30,
                    "instance_id": "lunar_ice_sp50_030_001_seed929001",
                    "mode": "B4.1_30_tree_closure_from_probe",
                    "variant": "V4_root_tail_probe_tree_gate",
                    "b4_1_matrix_cell": "B4.1_30_tree_closure_from_probe",
                    "certificate_scope": "BPC_TREE_OPTIMAL",
                    "pricing_state": "CERTIFIED_NO_NEGATIVE",
                    "exact_status": "BPC_TREE_OPTIMAL",
                    "bpc_tree_optimal": True,
                    "can_certify_no_negative": True,
                    "manual_rc_fail": 0,
                    "pricing_rc_fail": 0,
                    "certificate_leak": 0,
                    "diagnostic_claimed_certificate": 0,
                }
            ]
        )

        self.assertEqual(report["stage_counts"], {"D": 1})
        self.assertEqual(report["redlines"]["diagnostic_claimed_certificate_count"], 0)
        self.assertEqual(report["redlines"]["certificate_leak_count"], 0)
        r5 = {row["id"]: row for row in report["requirement_audit"]}["R5_stage_bc_diagnostic_only"]
        self.assertEqual(r5["status"], "pass")
        r7 = {row["id"]: row for row in report["requirement_audit"]}["R7_30_scale_exact_closure"]
        self.assertEqual(r7["status"], "pass")
        self.assertEqual(r7["evidence"]["thirty_scale_bpc_tree_optimal_count"], 1)

    def test_b4_1_restricted_region_bound_ledger_reuses_strongest_known_bound(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            probe = tmp_path / "probe.json"
            probe.write_text(
                json.dumps(
                    {
                        "instance_id": "bound-ledger-smoke",
                        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                        "final_judge": {
                            "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
                            "global_remaining_rc_lb": -0.00770611,
                            "global_remaining_rc_lb_coverage_complete": False,
                            "frontier_unsupported_region_count": 3,
                            "harvest_reports": [
                                {
                                    "true_reduced_cost": -0.7,
                                    "pricing_reduced_cost": -0.7,
                                    "task_set": ["ice_site_001", "ice_site_002"],
                                    "would_enter_master": True,
                                    "selected_after_addability_audit": True,
                                },
                                {
                                    "true_reduced_cost": -0.2,
                                    "pricing_reduced_cost": -0.2,
                                    "task_set": ["ice_site_003"],
                                    "would_enter_master": True,
                                    "selected_after_addability_audit": True,
                                },
                                {
                                    "true_reduced_cost": -0.01,
                                    "pricing_reduced_cost": -0.01,
                                    "task_set": ["ice_site_004"],
                                    "would_enter_master": True,
                                    "selected_after_addability_audit": True,
                                },
                            ],
                            "compact_pricing_phase_payloads": {
                                "optimization_harvest_3": {
                                    "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                                    "exact_status": "NOT_SOLVED",
                                    "best_reduced_cost": -0.01,
                                    "dual_bound": -0.121782748,
                                    "wall_time_sec": 169.1,
                                    "forbidden_task_set_count": 2,
                                    "forbidden_task_sets_can_certify_full_space": False,
                                },
                                "optimization_harvest_4": {
                                    "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                                    "exact_status": "NOT_SOLVED",
                                    "best_reduced_cost": 0.169,
                                    "dual_bound": -0.317649341,
                                    "wall_time_sec": 14.7,
                                    "forbidden_task_set_count": 3,
                                    "forbidden_task_sets_can_certify_full_space": False,
                                },
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            targeted = tmp_path / "targeted.json"
            targeted.write_text(
                json.dumps(
                    {
                        "schema_version": "lunar_ice_bpc.b4_1_targeted_restricted_region_probe.v1",
                        "source_probe_json": str(probe),
                        "diagnostic_only": True,
                        "official_certificate_allowed": False,
                        "rows": [
                            {
                                "source_probe_json": str(probe),
                                "region_id": "prefix_2",
                                "forbidden_task_set_count": 2,
                                "variant": "V4_current_strengthening",
                                "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                                "exact_status": "NOT_SOLVED",
                                "best_reduced_cost": 0.05,
                                "dual_bound": -0.188384591,
                                "official_certificate_allowed": False,
                                "can_certify_no_negative": False,
                            },
                            {
                                "source_probe_json": str(probe),
                                "region_id": "prefix_3",
                                "forbidden_task_set_count": 3,
                                "variant": "V4_current_strengthening",
                                "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                                "exact_status": "NOT_SOLVED",
                                "best_reduced_cost": 0.08,
                                "dual_bound": -0.2,
                                "official_certificate_allowed": False,
                                "can_certify_no_negative": False,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            ledger = b4_1_runner_module.build_b4_1_restricted_region_bound_ledger(
                probe,
                targeted_probe_jsons=[targeted],
            )

            self.assertEqual(
                ledger["schema_version"],
                "lunar_ice_bpc.b4_1_restricted_region_bound_ledger.v1",
            )
            self.assertTrue(ledger["diagnostic_only"])
            self.assertFalse(ledger["official_certificate_allowed"])
            self.assertFalse(ledger["can_claim_certificate"])
            self.assertEqual(ledger["pricing_proof_kind"], "FRONTIER_BOUND_INCOMPLETE")
            self.assertEqual(ledger["redlines"]["certificate_claim_count"], 0)
            by_region = {row["region_id"]: row for row in ledger["rows"]}
            self.assertEqual(by_region["prefix_2"]["selected_bound_source"], "source_phase")
            self.assertTrue(by_region["prefix_2"]["source_bound_reused"])
            self.assertEqual(by_region["prefix_2"]["best_known_dual_bound"], -0.121782748)
            self.assertEqual(by_region["prefix_3"]["selected_bound_source"], "targeted_probe")
            self.assertFalse(by_region["prefix_3"]["source_bound_reused"])
            self.assertTrue(by_region["prefix_3"]["targeted_bound_improved_over_source"])
            self.assertEqual(by_region["prefix_3"]["best_known_dual_bound"], -0.2)
            self.assertEqual(ledger["best_known_global_remaining_rc_lb"], -0.2)
            self.assertEqual(ledger["supported_bound_region_count"], 2)
            self.assertEqual(ledger["unsupported_bound_region_count"], 0)
            self.assertEqual(ledger["negative_bound_region_count"], 2)
            self.assertEqual(ledger["nonnegative_bound_region_count"], 0)
            self.assertEqual(ledger["region_bound_gap_to_zero"], 0.2)
            self.assertEqual(ledger["region_bound_gap_source_region_id"], "prefix_3")
            self.assertEqual(ledger["region_bound_gap_source"], "targeted_probe")
            self.assertEqual(ledger["region_partition_family"], "prefix_no_good_residual_regions")
            self.assertEqual(ledger["region_partition_required_model"], "exact_task_set_regions_plus_final_residual")
            self.assertEqual(ledger["region_partition_observed_prefixes"], [2, 3])
            self.assertTrue(ledger["region_partition_prefix_regions_nested"])
            self.assertFalse(ledger["region_partition_regions_disjoint"])
            self.assertFalse(ledger["region_partition_complete"])
            self.assertFalse(ledger["region_partition_can_certify"])
            self.assertEqual(ledger["region_partition_required_exact_task_set_region_count"], 3)
            self.assertEqual(ledger["region_partition_observed_exact_task_set_region_count"], 0)
            self.assertEqual(ledger["region_partition_missing_exact_task_set_region_count"], 3)
            self.assertEqual(ledger["region_partition_residual_region_id"], "prefix_3")
            self.assertEqual(ledger["region_partition_residual_best_known_dual_bound"], -0.2)
            self.assertFalse(ledger["region_partition_residual_bound_nonnegative"])
            self.assertIn(
                "prefix_no_good_regions_are_nested_not_disjoint",
                ledger["region_partition_issue_codes"],
            )
            self.assertIn("missing_exact_task_set_region_proofs", ledger["region_partition_issue_codes"])
            self.assertTrue(ledger["summary"]["region_bound_diagnostic_complete_for_listed_regions"])
            self.assertFalse(ledger["summary"]["region_bound_can_certify_if_partition"])
            self.assertFalse(ledger["summary"]["region_bound_official_certificate_allowed"])
            self.assertEqual(by_region["prefix_3"]["best_known_dual_bound_gap_to_zero"], 0.2)
            self.assertFalse(by_region["prefix_3"]["best_known_dual_bound_nonnegative"])

            positive_targeted = tmp_path / "targeted_positive.json"
            positive_targeted.write_text(
                json.dumps(
                    {
                        "schema_version": "lunar_ice_bpc.b4_1_targeted_restricted_region_probe.v1",
                        "source_probe_json": str(probe),
                        "diagnostic_only": True,
                        "official_certificate_allowed": False,
                        "rows": [
                            {
                                "source_probe_json": str(probe),
                                "region_id": "prefix_2",
                                "forbidden_task_set_count": 2,
                                "variant": "V4_current_strengthening",
                                "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
                                "exact_status": "RESTRICTED_PRICING_OPTIMAL",
                                "best_reduced_cost": 0.05,
                                "dual_bound": 0.05,
                                "official_certificate_allowed": False,
                                "can_certify_no_negative": False,
                            },
                            {
                                "source_probe_json": str(probe),
                                "region_id": "prefix_3",
                                "forbidden_task_set_count": 3,
                                "variant": "V4_current_strengthening",
                                "status": "COMPACT_HIGHS_PRICING_OPTIMAL",
                                "exact_status": "RESTRICTED_PRICING_OPTIMAL",
                                "best_reduced_cost": 0.08,
                                "dual_bound": 0.08,
                                "official_certificate_allowed": False,
                                "can_certify_no_negative": False,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            positive_ledger = b4_1_runner_module.build_b4_1_restricted_region_bound_ledger(
                probe,
                targeted_probe_jsons=[positive_targeted],
            )
            self.assertEqual(positive_ledger["best_known_global_remaining_rc_lb"], 0.05)
            self.assertEqual(positive_ledger["region_bound_gap_to_zero"], 0.0)
            self.assertEqual(positive_ledger["negative_bound_region_count"], 0)
            self.assertEqual(positive_ledger["nonnegative_bound_region_count"], 2)
            self.assertTrue(positive_ledger["summary"]["region_bound_can_certify_if_partition"])
            self.assertFalse(positive_ledger["region_partition_can_certify"])
            self.assertFalse(positive_ledger["region_partition_complete"])
            self.assertEqual(positive_ledger["region_partition_missing_exact_task_set_region_count"], 3)
            self.assertEqual(positive_ledger["region_partition_residual_region_id"], "prefix_3")
            self.assertTrue(positive_ledger["region_partition_residual_bound_nonnegative"])
            self.assertIn(
                "missing_exact_task_set_region_proofs",
                positive_ledger["region_partition_issue_codes"],
            )
            self.assertFalse(positive_ledger["official_certificate_allowed"])
            self.assertFalse(positive_ledger["can_claim_certificate"])
            self.assertFalse(positive_ledger["frontier_coverage_complete"])
            self.assertEqual(positive_ledger["pricing_proof_kind"], "FRONTIER_BOUND_INCOMPLETE")

            b4_1_runner_module.write_b4_1_restricted_region_bound_ledger(
                ledger,
                summary_json=tmp_path / "ledger.json",
                report_md=tmp_path / "ledger_zh.md",
            )
            ledger_markdown = (tmp_path / "ledger_zh.md").read_text(encoding="utf-8")
            self.assertIn("diagnostic-only", ledger_markdown)
            self.assertIn("region_bound_gap_to_zero", ledger_markdown)
            self.assertIn("missing exact-task-set regions", ledger_markdown)

            cli_out = tmp_path / "cli"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "scripts" / "run_lunar_ice_b4_1_true_dual_proof_tail.py"),
                    "--output-dir",
                    str(cli_out),
                    "--source-probe-json",
                    str(probe),
                    "--restricted-region-bound-ledger",
                    "--targeted-region-result-json",
                    str(targeted),
                    "--no-resume",
                ],
                cwd=project_root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((cli_out / "restricted_region_bound_ledger.json").exists())
            self.assertTrue((cli_out / "restricted_region_bound_ledger_zh.md").exists())

    def test_b4_1_cli_resource_guard_fails_closed_before_row(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "b4_1_guard"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "scripts" / "run_lunar_ice_b4_1_true_dual_proof_tail.py"),
                    "--stage-a",
                    "--instance",
                    "data/instances/lunar_ice_sp50_005/instance_001_logical_graph.json",
                    "--stage-a-modes",
                    "stageA_B2B_R2_worker_tail_dual_on",
                    "--output-dir",
                    str(out),
                    "--min-available-mem-gb",
                    "999999",
                    "--no-resume",
                ],
                cwd=project_root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn("resource gate failed", completed.stderr)
            summary = json.loads((out / "b4_1_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["redlines"]["resource_guard_stopped_count"], 1)
            self.assertFalse(summary["acceptance"]["stage_a_regression_clean"])
            self.assertFalse(summary["acceptance"]["b4_1_full_experiment_complete"])
            with (out / "b4_1_rows.csv").open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["algorithm_status"], "RESOURCE_GUARD_STOPPED")
            self.assertIn("resource_guard_failed", rows[0]["fail_closed_reason"])
            rerun = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "scripts" / "run_lunar_ice_b4_1_true_dual_proof_tail.py"),
                    "--stage-a",
                    "--instance",
                    "data/instances/lunar_ice_sp50_005/instance_001_logical_graph.json",
                    "--stage-a-modes",
                    "stageA_B2B_R2_worker_tail_dual_on",
                    "--output-dir",
                    str(out),
                    "--min-available-mem-gb",
                    "999999",
                    "--no-resume",
                ],
                cwd=project_root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(rerun.returncode, 2)
            self.assertEqual(len((out / "b4_1_rows.jsonl").read_text(encoding="utf-8").splitlines()), 1)

    def test_b4_1_cli_import_rows_jsonl_consolidates_stage_b_matrix(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            worker_tail_rows = tmp_path / "worker_tail_rows.jsonl"
            final_judge_rows = tmp_path / "final_judge_rows.jsonl"
            v4_rows = tmp_path / "v4_rows.jsonl"
            worker_tail_rows.write_text(
                json.dumps(
                    {
                        "stage": "B",
                        "matrix_group": "v2 evidence",
                        "source_probe_json": "runs/probes/v2.json",
                        "mode": "B4.1_worker_tail_hidden_negative_evidence",
                        "variant": "V2_latest_service_start_slot_bound",
                        "b4_1_matrix_cell": "B4V2_hidden_negative_audit",
                        "b4_1_harvesting_enabled": True,
                        "b4_1_hidden_negative_audit_enabled": True,
                        "b4_1_frontier_ledger_enabled": True,
                        "harvest_source_phase": "b2b_r2_post_final_judge_addability_harvest",
                        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                        "can_certify_no_negative": False,
                        "diagnostic_claimed_certificate": 0,
                        "manual_rc_fail": 0,
                        "pricing_rc_fail": 0,
                        "certificate_leak": 0,
                        "phase": "worker_tail_hidden_negative_evidence",
                        "round": 2,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            final_judge_rows.write_text(
                json.dumps(
                    {
                        "stage": "B",
                        "matrix_group": "final judge harvest evidence",
                        "source_probe_json": "runs/probes/final_judge_v2.json",
                        "mode": "B4.1_probe_final_judge_evidence",
                        "variant": "V2_latest_service_start_slot_bound",
                        "b4_1_matrix_cell": "B4V2_frontier_ledger_diagnostic",
                        "b4_1_harvesting_enabled": True,
                        "b4_1_hidden_negative_audit_enabled": False,
                        "b4_1_frontier_ledger_enabled": True,
                        "harvest_source_phase": "compact_final_judge_negative_feasibility_batch",
                        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                        "can_certify_no_negative": False,
                        "diagnostic_claimed_certificate": 0,
                        "manual_rc_fail": 0,
                        "pricing_rc_fail": 0,
                        "certificate_leak": 0,
                        "phase": "probe_final_judge_evidence",
                        "round": 2,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            v4_rows.write_text(
                json.dumps(
                    {
                        "stage": "B",
                        "matrix_group": "v4 evidence",
                        "source_probe_json": "runs/probes/v4.json",
                        "mode": "B4.1_compact_pricing_formulation",
                        "variant": "V4_combined_endpoint_pair_latest_start_time_window",
                        "b4_1_matrix_cell": "B4V4_combined_formulation_diagnostic",
                        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                        "can_certify_no_negative": False,
                        "diagnostic_claimed_certificate": 0,
                        "manual_rc_fail": 0,
                        "pricing_rc_fail": 0,
                        "certificate_leak": 0,
                        "phase": "optimization_proof",
                        "round": 1,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            partial_report = b4_1_runner_module.build_b4_1_report(
                [
                    json.loads(worker_tail_rows.read_text(encoding="utf-8").splitlines()[0]),
                    json.loads(v4_rows.read_text(encoding="utf-8").splitlines()[0]),
                ]
            )
            self.assertIn("B4V2_harvesting", partial_report["diagnostics"]["stage_b_missing_matrix_cells"])
            self.assertIn(
                "B4V2_harvesting_frontier_ledger_diagnostic",
                partial_report["diagnostics"]["stage_b_missing_matrix_cells"],
            )
            out = tmp_path / "merged"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(project_root / "scripts" / "run_lunar_ice_b4_1_true_dual_proof_tail.py"),
                    "--output-dir",
                    str(out),
                    "--import-rows-jsonl",
                    str(worker_tail_rows),
                    "--import-rows-jsonl",
                    str(final_judge_rows),
                    "--import-rows-jsonl",
                    str(v4_rows),
                    "--no-resume",
                ],
                cwd=project_root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads((out / "b4_1_summary.json").read_text(encoding="utf-8"))
            self.assertTrue(summary["acceptance"]["stage_b_diagnostic_clean"])
            self.assertTrue(summary["acceptance"]["stage_b_matrix_complete"])
            self.assertFalse(summary["acceptance"]["b4_1_full_experiment_complete"])
            self.assertEqual(summary["diagnostics"]["stage_b_missing_matrix_cells"], [])
            self.assertEqual(summary["redlines"]["diagnostic_claimed_certificate_count"], 0)
            requirement_status = {item["id"]: item["status"] for item in summary["requirement_audit"]}
            self.assertEqual(requirement_status["R2_stage_a_regression_clean"], "missing")
            self.assertEqual(requirement_status["R3_stage_b_matrix_complete"], "pass")
            self.assertEqual(requirement_status["R4_stage_c_selected_diagnostic"], "missing")
            self.assertEqual(requirement_status["R5_stage_bc_diagnostic_only"], "pass")
            self.assertEqual(requirement_status["R7_30_scale_exact_closure"], "incomplete")
            self.assertEqual(len((out / "b4_1_rows.jsonl").read_text(encoding="utf-8").splitlines()), 3)

    def test_restricted_negative_feasibility_cannot_certify_no_negative(self) -> None:
        payload = {
            "instance_id": "diagnostic",
            "history": [
                {
                    "status": "RESTRICTED_NEGATIVE_FEASIBILITY_INFEASIBLE",
                    "exact_status": "NOT_SOLVED",
                    "negative_feasibility_search_enabled": True,
                    "forbidden_arc_patterns_can_certify_full_space": False,
                    "can_certify_no_negative": True,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "probe.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = run_b4_pricing_formulation_diagnostic_from_json([path])

        self.assertEqual(report["redlines"]["restricted_negative_feasibility_claimed_certificate_count"], 1)

    def test_positive_best_rc_with_negative_dual_bound_is_not_certificate(self) -> None:
        payload = {
            "instance_id": "diagnostic",
            "history": [
                {
                    "status": "COMPACT_HIGHS_PRICING_TIME_LIMIT_REACHED",
                    "exact_status": "NOT_SOLVED",
                    "best_reduced_cost": 0.01,
                    "dual_bound": -0.5,
                    "can_certify_no_negative": True,
                    "negative_feasibility_search_enabled": False,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "probe.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = run_b4_pricing_formulation_diagnostic_from_json([path])

        self.assertEqual(report["redlines"]["positive_incumbent_rc_claimed_certificate_count"], 1)

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
        self.assertEqual(frontier["pricing_proof_kind"], "NONE")
        self.assertEqual(frontier["global_remaining_rc_lb"], 0.0)

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

        incomplete_frontier = build_pricing_frontier_ledger(
            source="b4_1_frontier_ledger_diagnostic",
            pricing_payload={
                "pricing_proof_kind": "FRONTIER_BOUND_INCOMPLETE",
                "global_remaining_rc_lb": -0.01,
                "global_remaining_rc_lb_valid": True,
                "global_remaining_rc_lb_coverage_complete": False,
                "frontier_region_count": 3,
                "frontier_unsupported_region_count": 1,
                "pending_complete_min_rc": -0.02,
                "best_reduced_cost": 0.0,
            },
            uses_true_dual_bpc_certificate=True,
            pricing_complete=False,
            coverage_complete=False,
        ).to_payload()
        self.assertEqual(incomplete_frontier["pricing_proof_kind"], "FRONTIER_BOUND_INCOMPLETE")
        self.assertEqual(incomplete_frontier["frontier_region_count"], 3)
        self.assertEqual(incomplete_frontier["frontier_unsupported_region_count"], 1)
        self.assertFalse(incomplete_frontier["lower_bound_official"])
        self.assertFalse(incomplete_frontier["can_certify_no_negative"])
        self.assertIn("frontier_bound_incomplete", incomplete_frontier["issues"])

    def test_b4_1_frontier_lb_audits_against_exhaustive_remaining_best_rc(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        priced, _columns = price_exhaustive_direct_journey_columns(
            data,
            JourneyDuals(cover={}, fleet_limit=0.0),
            max_direct_tasks=5,
        )
        true_best = float(priced["best_reduced_cost"])
        self.assertGreaterEqual(true_best, 0.0)

        audited = build_pricing_frontier_ledger(
            source="b4_1_frontier_ledger_exhaustive_check",
            pricing_payload={
                "pricing_proof_kind": "FRONTIER_BOUND_NO_NEGATIVE",
                "global_remaining_rc_lb": max(0.0, true_best - 1.0e-6),
                "global_remaining_rc_lb_valid": True,
                "global_remaining_rc_lb_coverage_complete": True,
                "frontier_region_count": 1,
                "frontier_unsupported_region_count": 0,
                "true_remaining_best_rc": true_best,
                "best_reduced_cost": true_best,
            },
            uses_true_dual_bpc_certificate=True,
            pricing_complete=True,
            coverage_complete=True,
        ).to_payload()

        self.assertTrue(audited["global_remaining_rc_lb_leq_true_remaining_best_rc"])
        self.assertTrue(audited["can_certify_no_negative"])
        self.assertEqual(audited["status"], "CERTIFIED_FRONTIER_NO_NEGATIVE")

        unsafe = build_pricing_frontier_ledger(
            source="b4_1_frontier_ledger_exhaustive_check",
            pricing_payload={
                "pricing_proof_kind": "FRONTIER_BOUND_NO_NEGATIVE",
                "global_remaining_rc_lb": true_best + 1.0,
                "global_remaining_rc_lb_valid": True,
                "global_remaining_rc_lb_coverage_complete": True,
                "frontier_region_count": 1,
                "frontier_unsupported_region_count": 0,
                "true_remaining_best_rc": true_best,
                "best_reduced_cost": true_best,
            },
            uses_true_dual_bpc_certificate=True,
            pricing_complete=True,
            coverage_complete=True,
        ).to_payload()

        self.assertFalse(unsafe["global_remaining_rc_lb_leq_true_remaining_best_rc"])
        self.assertFalse(unsafe["can_certify_no_negative"])
        self.assertFalse(unsafe["lower_bound_official"])
        self.assertIn("frontier_lower_bound_exceeds_true_remaining_best_rc", unsafe["issues"])

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
            3.0,
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
            self.assertEqual(summary["fixed_graph_root_lp_diagnostic_audit_count"], 1)
            self.assertEqual(summary["exact_claim_scope_counts"], {"fixed_logical_graph_exhaustive_direct_dp": 1})
            self.assertEqual(summary["certificate_scope_counts"], {"DIRECT_DP_FIXED_GRAPH_OPTIMAL": 1})
            self.assertEqual(summary["bpc_certificate_status_counts"], {"CERTIFIED_NO_NEGATIVE": 1})
            self.assertEqual(summary["true_dual_bpc_certificate_count"], 1)
            self.assertEqual(SOLVE_TIME_LIMIT_SEC_BY_SCALE[5], 600.0)
            self.assertEqual(summary["time_limit_exceeded_count"], 0)
            self.assertEqual(summary["certified_optimal_count"], 1)
            self.assertIsNotNone(summary["mean_relaxation_gap"])
            with Path(summary["results_csv"]).open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["lower_bound_source"], "fixed_graph_pricing_closure_lp")
            self.assertEqual(rows[0]["lower_bound_scope"], "fixed_logical_graph_exhaustive_pricing_closure")
            self.assertEqual(rows[0]["algorithm_status"], "DIRECT_DP_BASELINE_OPTIMAL")
            self.assertEqual(rows[0]["certificate_scope"], "DIRECT_DP_FIXED_GRAPH_OPTIMAL")
            self.assertEqual(rows[0]["direct_baseline_certificate_scope"], "DIRECT_DP_FIXED_GRAPH_OPTIMAL")
            self.assertEqual(rows[0]["canonical_baseline_certificate_scope"], "FEASIBLE_INCUMBENT_ONLY")
            self.assertEqual(rows[0]["path_option_dominance_policy"], PATH_OPTION_POLICY_ID)
            self.assertTrue(rows[0]["best_diagnostic_bound_source"])
            self.assertEqual(rows[0]["true_dual_pricing_tail_source"], "true_dual_fixed_graph_pricing_closure")
            solution = json.loads(Path(rows[0]["solution_path"]).read_text(encoding="utf-8"))
            self.assertEqual(solution["lower_bound_source"], "fixed_graph_pricing_closure_lp")
            self.assertEqual(solution["lower_bound_scope"], "fixed_logical_graph_exhaustive_pricing_closure")
            self.assertEqual(solution["bound_ledger"]["official_lower_bound_source"], "fixed_graph_pricing_closure_lp")
            self.assertFalse(solution["bound_ledger"]["diagnostic_bound_is_official"])
            direct_records = [
                record
                for record in solution["bound_ledger"]["records"]
                if record["name"] == "direct_fixed_graph_root_lp"
            ]
            self.assertEqual(len(direct_records), 1)
            self.assertEqual(direct_records[0]["certificate_status"], "FIXED_GRAPH_ROOT_DIAGNOSTIC")
            self.assertFalse(direct_records[0]["official_lower_bound"])
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
            self.assertEqual(
                audit["scales"]["005"]["certificate_scope_counts"],
                {"DIRECT_DP_FIXED_GRAPH_OPTIMAL": 1},
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
            self.assertEqual(summary["fixed_graph_root_lp_diagnostic_audit_count"], 1)
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
        for feature in (
            "is_depot",
            "is_task",
            "time_window_start_norm",
            "time_window_end_norm",
            "time_window_width_norm",
        ):
            self.assertIn(feature, graph["node_feature_schema"])
        for feature in (
            "source_is_depot",
            "target_is_depot",
            "dx_norm",
            "dy_norm",
            "pair_distance_norm",
            "same_sector",
            "travel_time_norm",
            "energy_norm",
            "risk_norm",
            "shadow_exposure_norm",
            "is_low_time",
            "is_low_energy",
            "is_low_risk",
        ):
            self.assertIn(feature, graph["edge_feature_schema"])
        self.assertEqual(graph["task_node_count"], len(instance["tasks"]))
        self.assertEqual(graph["depot_node_count"], 1)
        self.assertEqual(len(graph["nodes"]), len(instance["tasks"]) + 1)
        self.assertTrue(all(len(node["features"]) == len(graph["node_feature_schema"]) for node in graph["nodes"]))
        self.assertTrue(all(len(edge["features"]) == len(graph["edge_feature_schema"]) for edge in graph["edges"]))
        self.assertTrue(any(edge["source"] == "depot" for edge in graph["edges"]))
        self.assertTrue(any(edge["target"] == "depot" for edge in graph["edges"]))
        edge_schema = graph["edge_feature_schema"]
        idx_dx = edge_schema.index("dx_norm")
        idx_dy = edge_schema.index("dy_norm")
        task_a, task_b = sorted(instance["tasks"])[:2]
        forward = next(edge for edge in graph["edges"] if edge["source"] == task_a and edge["target"] == task_b and edge["path_type"] == "low_time")
        reverse = next(edge for edge in graph["edges"] if edge["source"] == task_b and edge["target"] == task_a and edge["path_type"] == "low_time")
        self.assertAlmostEqual(forward["features"][idx_dx], -reverse["features"][idx_dx], delta=1.0e-9)
        self.assertAlmostEqual(forward["features"][idx_dy], -reverse["features"][idx_dy], delta=1.0e-9)
        self.assertEqual(report["mode"], "shadow_only")
        self.assertFalse(report["mutates_solver"])
        self.assertFalse(report["can_certify"])
        self.assertEqual(report["exact_status_effect"], "none")
        self.assertEqual(report["node_count"], len(instance["tasks"]) + 1)
        self.assertEqual(report["task_node_count"], len(instance["tasks"]))
        self.assertEqual(report["depot_node_count"], 1)
        self.assertEqual(len(report["task_priority"]), len(instance["tasks"]))
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

    def test_b5_guidance_suite_cli_batches_manifest_by_scale_and_rejects_mutation(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance_5 = generate_instance(5, seed=629001, index=1)
            instance_10 = generate_instance(10, seed=729001, index=1)
            instance_5_path = root / "instances" / "lunar_ice_005" / "instance.json"
            instance_10_path = root / "instances" / "lunar_ice_010" / "instance.json"
            manifest_path = root / "manifest.json"
            output_path = root / "b5_suite.json"
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
            config_path = root / "b5_suite.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "guidance_mode: ordering_opt_in",
                        "journey_gat_shadow_enabled: true",
                        "journey_gat_optin_enabled: false",
                        "mutates_solver: false",
                        "can_certify: false",
                        "can_prune: false",
                        "can_fathom: false",
                        f"manifest: {manifest_path}",
                        "scales: [5]",
                        "enabled_ordering_modes: [pricing, branch, harvest]",
                        f"output_json: {output_path}",
                        "max_direct_tasks: 5",
                        "max_rounds: 8",
                        "diagnostic_policy_version: test_policy_v1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(project_root / "scripts" / "run_lunar_ice_b5_guidance_suite.py"), "--config", str(config_path)],
                cwd=project_root,
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn("ran 1 B5 guidance rows", completed.stdout)
            suite = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(suite["schema_version"], "lunar_ice_bpc.b5_guidance_ablation_suite.v1")
            self.assertEqual(suite["row_count"], 1)
            self.assertTrue(suite["suite_do_no_harm_pass"])
            self.assertEqual(suite["suite_performance_success_count"], 0)
            self.assertEqual(suite["mode_counts"], {"ordering_opt_in": 1})
            self.assertEqual(suite["certificate_scope_counts"], {"BPC_TREE_OPTIMAL": 1})
            self.assertEqual(suite["rows"][0]["guidance_output_head_counts"]["pricing_priority_head"], 5)
            self.assertEqual(suite["rows"][0]["guidance_output_head_counts"]["branch_priority_head"], 10)
            self.assertEqual(suite["rows"][0]["guidance_output_head_counts"]["harvest_priority_head"], 5)
            self.assertTrue(suite["rows"][0]["guidance_output_required_heads_present"])
            self.assertFalse(suite["rows"][0]["result"]["guidance_output_bundle"]["can_prune"])
            self.assertFalse(suite["rows"][0]["result"]["guidance_output_bundle"]["can_fathom"])
            self.assertFalse(suite["rows"][0]["result"]["guidance_output_bundle"]["can_certify"])
            self.assertTrue(suite["rows"][0]["result"]["guidance_output_bundle"]["diagnostic_versions_complete"])
            self.assertEqual(
                suite["rows"][0]["workload_diffs"],
                {
                    "wall_time": 0.0,
                    "pricing_calls": 0.0,
                    "final_judge_calls": 0.0,
                    "generated_labels": 0.0,
                    "rmp_iterations": 0.0,
                    "node_count": 0.0,
                },
            )
            workload = suite["rows"][0]["result"]["workload_ablation"]
            self.assertTrue(workload["workload_observed"])
            self.assertFalse(workload["performance_success"])
            self.assertEqual(workload["observation_source"], "dry_run_no_solver_mutation_zero_diff")
            self.assertEqual(workload["workload_units"], "guidance_delta_proxy")
            self.assertEqual(workload["gate_issues"], ["no_workload_metric_improved"])
            self.assertEqual(suite["runner"]["enabled_ordering_modes"], ["pricing", "branch", "harvest"])
            self.assertFalse(suite["runner"]["mutates_solver"])
            self.assertFalse(suite["runner"]["can_certify"])

            unsafe_config = root / "unsafe_b5_suite.yaml"
            unsafe_config.write_text(
                "\n".join(
                    [
                        "guidance_mode: ordering_opt_in",
                        "journey_gat_shadow_enabled: true",
                        "journey_gat_optin_enabled: true",
                        "mutates_solver: true",
                        "can_certify: false",
                        f"manifest: {manifest_path}",
                        "scales: [5]",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            rejected = subprocess.run(
                [sys.executable, str(project_root / "scripts" / "run_lunar_ice_b5_guidance_suite.py"), "--config", str(unsafe_config)],
                cwd=project_root,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("refuses mutates_solver=true", rejected.stderr)

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
            b5_suite = payload["sections"]["b5_guidance_suite"]
            self.assertEqual(b5_suite["status"], "PASS")
            self.assertEqual(len(b5_suite["summaries"]), 5)
            matrix = b5_suite["matrix_summary"]
            self.assertEqual(
                matrix["schema_version"],
                "lunar_ice_bpc.b5_guidance_ab_matrix_summary.v1",
            )
            self.assertEqual(matrix["expected_suite_count"], 5)
            self.assertEqual(matrix["observed_suite_count"], 5)
            self.assertEqual(
                matrix["required_ab_modes"],
                [
                    "shadow_only",
                    "all_ordering_opt_in",
                    "pricing_ordering_opt_in",
                    "branch_ordering_opt_in",
                    "harvest_ordering_opt_in",
                ],
            )
            self.assertEqual(matrix["missing_ab_modes"], [])
            self.assertTrue(matrix["all_suites_do_no_harm_pass"])
            self.assertTrue(matrix["all_suites_workload_observed"])
            self.assertFalse(matrix["any_performance_success"])
            self.assertFalse(matrix["performance_claim_allowed"])
            self.assertEqual(matrix["performance_claim_status"], "NO_IMPROVEMENT_DRY_RUN")
            self.assertFalse(matrix["random_row_split_is_main_claim"])
            self.assertEqual(
                matrix["row_counts_by_mode"],
                {
                    "shadow_only": 40,
                    "all_ordering_opt_in": 40,
                    "pricing_ordering_opt_in": 40,
                    "branch_ordering_opt_in": 40,
                    "harvest_ordering_opt_in": 40,
                },
            )
            self.assertEqual(
                matrix["workload_observed_by_mode"],
                {
                    "shadow_only": 40,
                    "all_ordering_opt_in": 40,
                    "pricing_ordering_opt_in": 40,
                    "branch_ordering_opt_in": 40,
                    "harvest_ordering_opt_in": 40,
                },
            )
            self.assertEqual(
                matrix["enabled_ordering_modes_by_mode"],
                {
                    "shadow_only": [],
                    "all_ordering_opt_in": ["pricing", "branch", "harvest"],
                    "pricing_ordering_opt_in": ["pricing"],
                    "branch_ordering_opt_in": ["branch"],
                    "harvest_ordering_opt_in": ["harvest"],
                },
            )
            b5_by_path = {summary["path"]: summary for summary in b5_suite["summaries"]}
            shadow_b5 = b5_by_path["runs/logs/b5_guidance_suite_summary.json"]
            ordering_b5 = b5_by_path["runs/logs/b5_guidance_ordering_suite_summary.json"]
            pricing_b5 = b5_by_path["runs/logs/b5_guidance_pricing_ordering_suite_summary.json"]
            branch_b5 = b5_by_path["runs/logs/b5_guidance_branch_ordering_suite_summary.json"]
            harvest_b5 = b5_by_path["runs/logs/b5_guidance_harvest_ordering_suite_summary.json"]
            for summary in (shadow_b5, ordering_b5, pricing_b5, branch_b5, harvest_b5):
                self.assertEqual(summary["row_count"], 40)
                self.assertEqual(summary["scale_counts"], {"5": 20, "10": 20})
                self.assertTrue(summary["suite_do_no_harm_pass"])
                self.assertEqual(summary["do_no_harm_fail_count"], 0)
                self.assertEqual(summary["certificate_scope_diff_count"], 0)
                self.assertEqual(summary["additional_bpc_incomplete_count"], 0)
                self.assertEqual(summary["workload_observed_count"], 40)
                self.assertFalse(summary["runner"]["mutates_solver"])
                self.assertFalse(summary["runner"]["can_certify"])
            self.assertEqual(shadow_b5["mode_counts"], {"shadow_only": 40})
            self.assertEqual(shadow_b5["runner"]["enabled_ordering_modes"], [])
            self.assertEqual(ordering_b5["mode_counts"], {"ordering_opt_in": 40})
            self.assertEqual(ordering_b5["runner"]["enabled_ordering_modes"], ["pricing", "branch", "harvest"])
            self.assertEqual(pricing_b5["runner"]["enabled_ordering_modes"], ["pricing"])
            self.assertEqual(branch_b5["runner"]["enabled_ordering_modes"], ["branch"])
            self.assertEqual(harvest_b5["runner"]["enabled_ordering_modes"], ["harvest"])
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
            closure_gap = benchmark["closure_gap_summary"]
            self.assertEqual(
                closure_gap["schema_version"],
                "lunar_ice_bpc.benchmark_closure_gap_summary.v1",
            )
            self.assertEqual(closure_gap["target_scale_labels"], ["030", "050"])
            self.assertEqual(closure_gap["blocking_scale_labels"], ["030", "050"])
            self.assertEqual(closure_gap["total_missing_exact_optimal_count"], 18)
            self.assertTrue(closure_gap["all_scalable_diagnostic_evidence_complete"])
            self.assertFalse(closure_gap["diagnostic_gap_can_complete_project"])
            self.assertEqual(closure_gap["blockers"]["030"]["required_exact_optimal_count"], 15)
            self.assertEqual(closure_gap["blockers"]["030"]["exact_optimal_count"], 0)
            self.assertEqual(closure_gap["blockers"]["030"]["missing_exact_optimal_count"], 15)
            self.assertEqual(
                closure_gap["blockers"]["030"]["true_dual_pricing_tail_status_counts"],
                {"TRUE_DUAL_PRICING_TAIL_NEGATIVE_FOUND": 20},
            )
            self.assertEqual(
                closure_gap["blockers"]["030"]["true_dual_readiness_status_counts"],
                {"BLOCKED_BY_NEGATIVE_REDUCED_COST": 20},
            )
            self.assertEqual(closure_gap["blockers"]["050"]["required_exact_optimal_count"], 3)
            self.assertEqual(closure_gap["blockers"]["050"]["exact_optimal_count"], 0)
            self.assertEqual(closure_gap["blockers"]["050"]["missing_exact_optimal_count"], 3)
            self.assertTrue(closure_gap["blockers"]["050"]["scalable_diagnostic_evidence_complete"])

    def test_b5_guidance_suite_audit_is_incomplete_when_summary_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audit = _audit_b5_guidance_suite(Path(tmp))

        self.assertEqual(audit["status"], "INCOMPLETE")
        self.assertEqual(audit["issues"], [])
        self.assertEqual(len(audit["incomplete"]), 5)
        self.assertTrue(all("B5 guidance suite summary is missing" in item for item in audit["incomplete"]))
        matrix = audit["matrix_summary"]
        self.assertEqual(matrix["observed_suite_count"], 0)
        self.assertEqual(
            matrix["missing_ab_modes"],
            [
                "shadow_only",
                "all_ordering_opt_in",
                "pricing_ordering_opt_in",
                "branch_ordering_opt_in",
                "harvest_ordering_opt_in",
            ],
        )
        self.assertFalse(matrix["all_suites_do_no_harm_pass"])
        self.assertFalse(matrix["all_suites_workload_observed"])
        self.assertFalse(matrix["performance_claim_allowed"])
        self.assertEqual(matrix["performance_claim_status"], "MISSING_AB_MODES")

    def test_b4_2_cold_runner_rejects_external_probe_cli(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location(
            "b4_2_cold_runner",
            project_root / "scripts" / "run_lunar_ice_b4_2_cold_exact.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        parser = module._build_parser()
        help_text = parser.format_help()
        self.assertNotIn("--reuse-probe", help_text)
        self.assertNotIn("--initial-resume-probe", help_text)
        self.assertNotIn("--source-probe-json", help_text)
        with self.assertRaises(SystemExit):
            parser.parse_args(["--reuse-probe", "instance_001=probe.json"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["--source-probe-json", "probe.json"])

    def test_b4_2_config_hash_and_summary_gate_no_cheat(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location(
            "b4_2_cold_runner_summary",
            project_root / "scripts" / "run_lunar_ice_b4_2_cold_exact.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        args = module._build_parser().parse_args([])
        config = module._official_config(args)
        self.assertEqual(config["model_id"], "B4_2_COLD_EXACT_V1")
        self.assertFalse(config["no_cheat_policy"]["external_source_probe_allowed"])
        self.assertTrue(config["no_cheat_policy"]["checkpoint_time_counted"])
        first_hash = module._config_hash(config)
        self.assertEqual(first_hash, module._config_hash(dict(config)))
        changed = dict(config)
        changed["threads"] = 8
        self.assertNotEqual(first_hash, module._config_hash(changed))

        rows = [
            {
                "scale": 30,
                "instance_key": "instance_001",
                "config_hash": first_hash,
                "certificate_scope": "BPC_TREE_OPTIMAL",
                "exact_certificate": True,
                "under_500": True,
                "cold_start_total_sec": 120.0,
                "root_cg_sec": 80.0,
                "tree_sec": 40.0,
                "no_cheat_pass": True,
                "external_probe_used": False,
                "mature_pool_used": False,
                "manual_columns_used": False,
                "per_instance_override_used": False,
            }
        ]
        limited_summary = module._summary(
            rows,
            config=config,
            limited_run=True,
            discovered_instance_count=1,
        )
        self.assertFalse(limited_summary["acceptance"]["b4_2_cold_exact_accepted"])
        self.assertEqual(limited_summary["redlines"]["no_cheat_fail_count"], 0)

        cheat_rows = [dict(rows[0], external_probe_used=True, no_cheat_pass=False)]
        cheat_summary = module._summary(
            cheat_rows,
            config=config,
            limited_run=False,
            discovered_instance_count=1,
        )
        self.assertEqual(cheat_summary["redlines"]["no_cheat_fail_count"], 1)
        self.assertFalse(cheat_summary["acceptance"]["b4_2_cold_exact_accepted"])

    def test_b4_2_report_marks_seed_instrumentation_boundary(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location(
            "b4_2_cold_runner_report",
            project_root / "scripts" / "run_lunar_ice_b4_2_cold_exact.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        args = module._build_parser().parse_args([])
        config = module._official_config(args)
        config_hash = module._config_hash(config)
        rows = [
            {
                "scale": 30,
                "instance_key": "instance_001",
                "config_hash": config_hash,
                "algorithm_status": "BPC_INCOMPLETE_PRICING",
                "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                "pricing_state": "INCOMPLETE_LIMIT",
                "exact_certificate": False,
                "under_500": False,
                "cold_start_total_sec": 500.1,
                "root_cg_sec": 500.1,
                "tree_sec": None,
                "root_pool_active_column_count": 151,
                "column_provenance": "instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback",
                "fail_reason": "root pool did not certify",
                "no_cheat_pass": True,
                "external_probe_used": False,
                "mature_pool_used": False,
                "manual_columns_used": False,
                "per_instance_override_used": False,
            }
        ]
        summary = module._summary(
            rows,
            config=config,
            limited_run=False,
            discovered_instance_count=1,
        )
        report = module._render_report(rows, summary)
        self.assertIn("B4.2 Cold-Start Exact 500s Report", report)
        self.assertIn("B0 incumbent + singleton", report)
        self.assertIn("instance_json_fixed_seed_same_run_checkpoint_and_partition_feedback", report)
        self.assertFalse(summary["acceptance"]["b4_2_cold_exact_accepted"])

    def test_b4_2_partition_feedback_merges_only_audited_negative_payloads(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location(
            "b4_2_cold_runner_partition_feedback",
            project_root / "scripts" / "run_lunar_ice_b4_2_cold_exact.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        base_column = {
            "vehicle_id": "active_column_001",
            "sorties": [
                {
                    "tasks": ["ice_site_001"],
                    "legs": [
                        {"from": "depot", "to": "ice_site_001", "path_type": "low_time"},
                        {"from": "ice_site_001", "to": "depot", "path_type": "low_time"},
                    ],
                    "start_time": 0.0,
                    "service_starts": {"ice_site_001": 10.0},
                }
            ],
        }
        new_payload = {
            "vehicle_id": "partition_negative",
            "sorties": [
                {
                    "tasks": ["ice_site_002", "ice_site_003"],
                    "legs": [
                        {"from": "depot", "to": "ice_site_002", "path_type": "low_time"},
                        {"from": "ice_site_002", "to": "ice_site_003", "path_type": "low_risk"},
                        {"from": "ice_site_003", "to": "depot", "path_type": "low_time"},
                    ],
                    "start_time": 0.0,
                    "service_starts": {"ice_site_002": 20.0, "ice_site_003": 30.0},
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_probe = tmp_path / "probe.json"
            source_probe.write_text(
                json.dumps(
                    {
                        "instance_id": "demo_instance",
                        "active_columns_payload_version": "journey_solution_payload.v1",
                        "active_columns": [base_column],
                    }
                ),
                encoding="utf-8",
            )
            partition_dir = tmp_path / "partition"
            worker_dir = partition_dir / "worker_01_k002_002"
            worker_dir.mkdir(parents=True)
            (worker_dir / "required_task_set_partition_probe.json").write_text(
                json.dumps(
                    {
                        "rows": [
                            {
                                "region_id": "residual_task_count_002_active_sorties_001",
                                "partition_negative_solution_payload": new_payload,
                                "partition_negative_true_rc": -0.5,
                                "partition_negative_pricing_rc_diff": 0.0,
                                "partition_negative_rc_audit_pass": True,
                                "partition_negative_task_set": ["ice_site_002", "ice_site_003"],
                                "partition_negative_task_set_size": 2,
                                "partition_negative_replacement_or_new_task_set": "new_task_set",
                            },
                            {
                                "region_id": "bad_rc_audit",
                                "partition_negative_solution_payload": {
                                    **new_payload,
                                    "vehicle_id": "bad_partition_negative",
                                },
                                "partition_negative_true_rc": -1.0,
                                "partition_negative_pricing_rc_diff": 0.0,
                                "partition_negative_rc_audit_pass": False,
                            },
                            {
                                "region_id": "positive_rc",
                                "partition_negative_solution_payload": {
                                    **new_payload,
                                    "vehicle_id": "positive_partition_negative",
                                },
                                "partition_negative_true_rc": 0.01,
                                "partition_negative_pricing_rc_diff": 0.0,
                                "partition_negative_rc_audit_pass": True,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            output_probe = tmp_path / "merged.json"
            result = module._merge_partition_negative_columns_into_probe(
                source_probe=source_probe,
                partition_dir=partition_dir,
                output_probe=output_probe,
                max_columns=4,
                negative_eps=1.0e-6,
                round_index=1,
            )
            self.assertEqual(result["candidate_count"], 1)
            self.assertEqual(result["added_count"], 1)
            merged = json.loads(output_probe.read_text(encoding="utf-8"))
            self.assertEqual(len(merged["active_columns"]), 2)
            self.assertEqual(
                merged["b4_2_partition_feedback_merge"]["selected"][0]["region_id"],
                "residual_task_count_002_active_sorties_001",
            )

    def test_b4_2_root_partition_gate_requires_integral_root(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location(
            "b4_2_cold_runner_partition_gate",
            project_root / "scripts" / "run_lunar_ice_b4_2_cold_exact.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        partition_row = {"root_partition_certified_no_negative": True, "root_partition_sec": 12.0}
        with tempfile.TemporaryDirectory() as tmp:
            source_probe = Path(tmp) / "probe.json"
            source_probe.write_text(
                json.dumps(
                    {
                        "integral_root": True,
                        "root_lp_bound": 1.25,
                        "root_lp_vs_direct_dp_gap": 0.0,
                        "b0_ablation": {"direct_dp_objective": 1.25},
                    }
                ),
                encoding="utf-8",
            )
            gate = module._root_partition_tree_gate(source_probe, partition_row)
            self.assertTrue(gate["exact_certificate"])
            self.assertEqual(gate["certificate_scope"], "BPC_TREE_OPTIMAL")

            source_probe.write_text(
                json.dumps(
                    {
                        "integral_root": False,
                        "root_lp_bound": 1.1,
                        "root_lp_vs_direct_dp_gap": 0.2,
                        "b0_ablation": {"direct_dp_objective": 1.3},
                    }
                ),
                encoding="utf-8",
            )
            gate = module._root_partition_tree_gate(source_probe, partition_row)
            self.assertFalse(gate["exact_certificate"])
            self.assertEqual(gate["certificate_scope"], "BPC_NODE_LP_CERTIFIED")


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
