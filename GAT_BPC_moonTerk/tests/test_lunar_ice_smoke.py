from __future__ import annotations

import csv
import json
import re
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
from lunar_ice_bpc.exact.bpc.pricing.harvest import harvest_addable_negative_columns
from lunar_ice_bpc.exact.bpc.pricing.hidden_negative_audit import build_hidden_negative_audit
from lunar_ice_bpc.exact.bpc.solver.branch_tree_solver import (
    _QueuedNode,
    _solve_b3_node,
    solve_b3_branch_price_tree_baseline,
)
from lunar_ice_bpc.exact.bpc.solver.cut_formulation_solver import solve_b4_cut_formulation_baseline
from lunar_ice_bpc.exact.bpc.solver.gat_guidance_solver import (
    run_b5_guidance_ablation_suite,
    solve_b5_gat_guidance_shadow_baseline,
)
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import solve_b2_pricing_tail_baseline
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
        self.assertEqual(b1["final_judge_status"], "EXHAUSTIVE_DIRECT_LABEL_PRICED")
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
        sortie = one_sortie_column.sorties[0]
        sortie_cost = (
            data.objective.alpha_discovery_completion * sortie.discovery_completion_term
            + data.objective.beta_journey_end_time * sortie.end_time
            + data.objective.gamma_lunar_ice_risk * sortie.risk_integral
            + data.objective.delta_energy * sortie.energy_proxy
        )
        self.assertAlmostEqual(one_sortie_column.objective, round(sortie_cost, 6), places=6)

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

    def test_b2_pricing_tail_matches_b1_scope_and_objective(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        b2 = solve_b2_pricing_tail_baseline(data, max_direct_tasks=5, max_rounds=8)

        self.assertEqual(b2["algorithm_status"], "BPC_GAP_AVAILABLE")
        self.assertEqual(b2["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertEqual(b2["pricing_state"], "CERTIFIED_NO_NEGATIVE")
        self.assertEqual(b2["exact_status"], "BPC_NODE_LP_CERTIFIED")
        self.assertTrue(b2["root_lp_bound_official"])
        self.assertEqual(b2["objective_diff_vs_B1"], 0.0)
        self.assertEqual(b2["certificate_scope_diff_vs_B1"], "")
        self.assertEqual(b2["b1_ablation"]["objective_diff_vs_B1"], 0.0)
        self.assertEqual(b2["b1_ablation"]["certificate_scope_diff_vs_B1"], "")
        self.assertLessEqual(b2["final_judge_call_count"], b2["b1_ablation"]["final_judge_call_count_vs_B1"] + 1)
        self.assertEqual(b2["harvest_selected_count"], b2["harvest_addable_candidate_count"])
        self.assertEqual(b2["duplicate_only_count"], 0)
        self.assertEqual(b2["hidden_negative_count"], 0)
        self.assertEqual(b2["replacement_only_round_count"], 0)
        self.assertFalse(b2["completion_bound_policy"]["pruning_enabled"])
        self.assertFalse(b2["completion_bound_policy"]["can_certify_no_negative"])
        self.assertEqual(b2["proof_debt_unreleased_count"], 0)

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
            negative_eps=1.0e-6,
            max_columns_per_round=64,
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
        self.assertEqual(payload["harvest_selected_count"], 1)
        self.assertGreaterEqual(payload["harvest_duplicate_signature_count"], 1)
        self.assertTrue(all(row["would_enter_master"] for row in payload["reports"] if row["task_set"] == sorted(fresh.task_set)))

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
        self.assertFalse(audit["mutates_solver"])
        self.assertFalse(audit["changes_certificate_semantics"])
        self.assertEqual(audit["rows"][0]["worker_kind"], "test_worker")

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
            {"DIRECT_ROOT_FIXED_GRAPH_LP_CERTIFIED", "DIRECT_ROOT_FIXED_GRAPH_INTEGER_CERTIFIED"},
        )
        self.assertIn(
            direct_root["exact_status"],
            {"FIXED_GRAPH_ROOT_LP_CERTIFIED", "FIXED_GRAPH_INTEGER_OPTIMAL"},
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
