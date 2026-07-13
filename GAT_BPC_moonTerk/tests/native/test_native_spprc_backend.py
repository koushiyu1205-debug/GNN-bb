from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import MappingProxyType, SimpleNamespace
import unittest
from unittest.mock import patch

from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.exact.bpc.pricing.backends import (
    BACKEND_MODE_NEGATIVE_HARVEST,
    BACKEND_OBJECTIVE_PHASE_ONE,
    BackendPricingRequest,
    NativeRcsppInprocessBackend,
    NativeRcsppHostBackend,
    native_spprc_scale_profile,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (
    SPPRC_EXACT_MODE,
    build_spprc_request,
    run_spprc_pricer,
    spprc_instance_hash,
)
from lunar_ice_bpc.exact.core.branching import (
    DIFFERENT_JOURNEY,
    SAME_JOURNEY,
    BranchContext,
    PairBranchDecision,
    journey_satisfies_branch_context,
)
from lunar_ice_bpc.exact.core.cuts import CutContext, fleet_lower_bound_cut, subset_row_cut
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.solver.journey_driver import enumerate_direct_journey_columns
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals, manual_journey_reduced_cost
from lunar_ice_bpc.exact.master.journey_rmp import solve_phase_one_journey_rmp


NATIVE_AVAILABLE = importlib.util.find_spec("lunar_spprc_native") is not None


@unittest.skipUnless(NATIVE_AVAILABLE, "native extension is not installed")
class NativeSpprcBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_lunar_ice_data(generate_instance(5, seed=629001, index=1))
        project_root = Path(__file__).resolve().parents[2]
        cls.data10 = load_lunar_ice_data(
            json.loads(
                (
                    project_root
                    / "data/instances/lunar_ice_sp50_010/instance_001_logical_graph.json"
                ).read_text(encoding="utf-8")
            )
        )

    def test_zero_dual_exact_proves_threshold_without_fake_global_minimum(self) -> None:
        result = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(data=self.data, true_duals=JourneyDuals(cover={}))
        )

        self.assertEqual(result.engine_status, "COMPLETE")
        self.assertTrue(result.search_exhaustive)
        self.assertTrue(result.frontier_empty)
        self.assertEqual(result.proved_no_rc_below, -1.0e-6)
        self.assertIsNone(result.global_min_rc)
        self.assertFalse(result.global_min_rc_is_exact)
        self.assertTrue(result.can_enter_certificate_audit)

    def test_native_and_python_match_exact_best_rc_and_negative_count(self) -> None:
        duals = JourneyDuals(cover={task_id: 10.0 for task_id in self.data.task_ids})
        native = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(data=self.data, true_duals=duals)
        )
        request = build_spprc_request(
            self.data,
            mode=SPPRC_EXACT_MODE,
            config_hash="native-differential",
            backend_id="python_reference",
            max_exact_tasks=5,
            harvest_target=1000,
            exact_negative_harvest_target=1000,
        )
        python = run_spprc_pricer(self.data, duals, request)

        self.assertEqual(native.engine_status, "COMPLETE")
        self.assertAlmostEqual(native.best_found_rc, python.best_found_rc, places=8)
        self.assertEqual(len(native.columns), len(python.columns))
        self.assertFalse(native.certificate_blockers)
        self.assertGreater(native.telemetry["dominance_candidate_checks"], 0)
        self.assertGreaterEqual(native.telemetry["max_visited_bucket_size"], 1)
        self.assertLess(
            native.telemetry["dominance_wall_time_seconds"],
            native.telemetry["wall_time_seconds"],
        )

    def test_exact_completion_bound_preserves_negative_columns_and_certificate(self) -> None:
        duals = JourneyDuals(cover={task_id: 0.2 for task_id in self.data.task_ids})
        baseline = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(data=self.data, true_duals=duals)
        )
        bounded = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=duals,
                completion_bound_enabled=True,
            )
        )

        def signatures(result):
            return {
                (
                    tuple(
                        tuple((leg.source, leg.target, leg.path_type) for leg in sortie.legs)
                        for sortie in column.sorties
                    ),
                    column.objective,
                )
                for column in result.columns
            }

        self.assertEqual(baseline.engine_status, "COMPLETE")
        self.assertEqual(bounded.engine_status, "COMPLETE")
        self.assertEqual(signatures(baseline), signatures(bounded))
        self.assertEqual(baseline.best_found_rc, bounded.best_found_rc)
        self.assertGreater(bounded.telemetry["completion_bound_pruned_labels"], 0)
        self.assertLess(
            bounded.telemetry["extended_labels"],
            baseline.telemetry["extended_labels"],
        )

        no_negative = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=JourneyDuals(cover={}),
                completion_bound_enabled=True,
            )
        )
        self.assertTrue(no_negative.can_enter_certificate_audit)
        self.assertEqual(no_negative.proved_no_rc_below, -1.0e-6)

    def test_subset_dominance_preserves_exact_optimum_and_branch_proof(self) -> None:
        contexts = (
            BranchContext(),
            BranchContext(
                pair_decisions=(
                    PairBranchDecision(
                        self.data.task_ids[0],
                        self.data.task_ids[1],
                        SAME_JOURNEY,
                    ),
                )
            ),
            BranchContext(
                pair_decisions=(
                    PairBranchDecision(
                        self.data.task_ids[0],
                        self.data.task_ids[1],
                        DIFFERENT_JOURNEY,
                    ),
                )
            ),
        )
        dual_cases = (
            JourneyDuals(cover={}),
            JourneyDuals(
                cover={task_id: 0.2 for task_id in self.data.task_ids},
                fleet_limit=-0.05,
            ),
        )
        for branch_context in contexts:
            for duals in dual_cases:
                with self.subTest(
                    branch=branch_context.to_payload(),
                    duals=duals.cover,
                ):
                    baseline = NativeRcsppInprocessBackend().solve(
                        BackendPricingRequest(
                            data=self.data,
                            true_duals=duals,
                            branch_context=branch_context,
                        )
                    )
                    accelerated = NativeRcsppInprocessBackend().solve(
                        BackendPricingRequest(
                            data=self.data,
                            true_duals=duals,
                            branch_context=branch_context,
                            subset_dominance_enabled=True,
                        )
                    )

                    self.assertEqual(baseline.engine_status, "COMPLETE")
                    self.assertEqual(accelerated.engine_status, "COMPLETE")
                    self.assertEqual(
                        baseline.can_enter_certificate_audit,
                        accelerated.can_enter_certificate_audit,
                    )
                    self.assertEqual(
                        baseline.proved_no_rc_below,
                        accelerated.proved_no_rc_below,
                    )
                    if baseline.best_found_rc is None:
                        self.assertIsNone(accelerated.best_found_rc)
                    else:
                        self.assertAlmostEqual(
                            baseline.best_found_rc,
                            accelerated.best_found_rc,
                            places=8,
                        )
                    self.assertGreaterEqual(
                        accelerated.telemetry["subset_dominance_candidate_checks"],
                        accelerated.telemetry["subset_dominance_rejected_labels"],
                    )

        for duals in (
            JourneyDuals(cover={}),
            JourneyDuals(
                cover={task_id: 0.15 for task_id in self.data10.task_ids},
                fleet_limit=-0.03,
            ),
        ):
            with self.subTest(scale=10, duals=duals.cover):
                baseline = NativeRcsppInprocessBackend().solve(
                    BackendPricingRequest(data=self.data10, true_duals=duals)
                )
                accelerated = NativeRcsppInprocessBackend().solve(
                    BackendPricingRequest(
                        data=self.data10,
                        true_duals=duals,
                        subset_dominance_enabled=True,
                    )
                )
                self.assertEqual(baseline.engine_status, "COMPLETE")
                self.assertEqual(accelerated.engine_status, "COMPLETE")
                self.assertEqual(
                    baseline.proved_no_rc_below,
                    accelerated.proved_no_rc_below,
                )
                if baseline.best_found_rc is None:
                    self.assertIsNone(accelerated.best_found_rc)
                else:
                    self.assertAlmostEqual(
                        baseline.best_found_rc,
                        accelerated.best_found_rc,
                        places=8,
                    )

    def test_ten_task_objective_best_representatives_match_python(self) -> None:
        duals = JourneyDuals(cover={task_id: 1.0 for task_id in self.data10.task_ids})
        native = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(data=self.data10, true_duals=duals)
        )
        request = build_spprc_request(
            self.data10,
            mode=SPPRC_EXACT_MODE,
            config_hash="native-differential-10",
            backend_id="python_reference",
            max_exact_tasks=10,
            harvest_target=5000,
            exact_negative_harvest_target=5000,
        )
        python = run_spprc_pricer(self.data10, duals, request)

        def objective_best(columns):
            best = {}
            for column in columns:
                key = frozenset(column.task_set)
                old = best.get(key)
                if old is None or column.objective < old.objective:
                    best[key] = column
            return best

        native_best = objective_best(native.columns)
        python_best = objective_best(python.columns)
        self.assertEqual(native.engine_status, "COMPLETE")
        self.assertTrue(native.search_exhaustive)
        self.assertAlmostEqual(native.best_found_rc, python.best_found_rc, places=8)
        self.assertEqual(set(native_best), set(python_best))
        self.assertTrue(native_best)
        self.assertLessEqual(
            max(
                abs(native_best[key].objective - python_best[key].objective)
                for key in native_best
            ),
            2.0e-6,
        )

    def test_negative_harvest_is_partial_and_never_certifies(self) -> None:
        duals = JourneyDuals(cover={task_id: 10.0 for task_id in self.data.task_ids})
        result = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=duals,
                mode=BACKEND_MODE_NEGATIVE_HARVEST,
                harvest_target=2,
            )
        )

        self.assertEqual(result.engine_status, "MAX_SOLUTIONS")
        self.assertFalse(result.search_exhaustive)
        self.assertLessEqual(len(result.columns), 2)
        self.assertEqual(
            len({frozenset(column.task_set) for column in result.columns}),
            len(result.columns),
        )
        self.assertIsNotNone(result.best_found_rc)
        self.assertFalse(result.can_enter_certificate_audit)

    def test_phase_one_native_columns_restore_zero_artificial_objective(self) -> None:
        phase_one = solve_phase_one_journey_rmp(
            self.data.task_ids,
            tuple(),
            fleet_size=self.data.fleet_size,
        )
        self.assertEqual(phase_one.status, "PHASE_ONE_OPTIMAL")
        self.assertEqual(phase_one.artificial_objective, float(len(self.data.task_ids)))
        self.assertEqual(phase_one.artificial_positive_count, len(self.data.task_ids))

        priced = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=phase_one.duals,
                objective_mode=BACKEND_OBJECTIVE_PHASE_ONE,
            )
        )
        self.assertEqual(priced.engine_status, "COMPLETE")
        self.assertTrue(priced.search_exhaustive)
        self.assertEqual(priced.best_found_rc, -float(len(self.data.task_ids)))
        self.assertTrue(priced.columns)

        restored = solve_phase_one_journey_rmp(
            self.data.task_ids,
            priced.columns,
            fleet_size=self.data.fleet_size,
        )
        self.assertTrue(restored.feasible_without_artificials)
        self.assertEqual(restored.artificial_objective, 0.0)
        self.assertEqual(restored.artificial_positive_count, 0)

    def test_same_and_different_branch_children_match_python_reference(self) -> None:
        duals = JourneyDuals(cover={task_id: 10.0 for task_id in self.data.task_ids})
        for sense in (SAME_JOURNEY, DIFFERENT_JOURNEY):
            with self.subTest(sense=sense):
                branch = BranchContext(
                    pair_decisions=(
                        PairBranchDecision(self.data.task_ids[0], self.data.task_ids[1], sense),
                    )
                )
                native = NativeRcsppInprocessBackend().solve(
                    BackendPricingRequest(
                        data=self.data,
                        true_duals=duals,
                        branch_context=branch,
                    )
                )
                request = build_spprc_request(
                    self.data,
                    mode=SPPRC_EXACT_MODE,
                    config_hash=f"native-branch-{sense}",
                    backend_id="python_reference",
                    max_exact_tasks=5,
                    harvest_target=1000,
                    exact_negative_harvest_target=1000,
                    branch_context=branch,
                )
                python = run_spprc_pricer(
                    self.data,
                    duals,
                    request,
                    branch_context=branch,
                )

                self.assertEqual(native.engine_status, "COMPLETE")
                self.assertTrue(native.search_exhaustive)
                self.assertTrue(native.frontier_empty)
                self.assertFalse(native.certificate_blockers)
                self.assertAlmostEqual(native.best_found_rc, python.best_found_rc, places=8)
                self.assertEqual(
                    {frozenset(column.task_set) for column in native.columns},
                    {frozenset(column.task_set) for column in python.columns},
                )
                self.assertTrue(
                    all(
                        journey_satisfies_branch_context(column, branch)
                        for column in native.columns
                    )
                )

    def test_subset_row_and_fleet_cut_reduced_costs_match_python(self) -> None:
        for cut in (
            subset_row_cut("sri-1", self.data.task_ids[:3]),
            fleet_lower_bound_cut("fleet-1", min_vehicles=2),
        ):
            with self.subTest(cut_type=cut.cut_type):
                cut_context = CutContext(cuts=(cut,))
                duals = JourneyDuals(
                    cover={task_id: 0.2 for task_id in self.data.task_ids},
                    cuts={cut.cut_id: 0.3},
                )
                native = NativeRcsppInprocessBackend().solve(
                    BackendPricingRequest(
                        data=self.data,
                        true_duals=duals,
                        cut_context=cut_context,
                        cut_state_enabled=True,
                    )
                )
                request = build_spprc_request(
                    self.data,
                    mode=SPPRC_EXACT_MODE,
                    config_hash=f"native-cut-{cut.cut_type}",
                    backend_id="python_reference",
                    max_exact_tasks=5,
                    harvest_target=1000,
                    exact_negative_harvest_target=1000,
                    cut_context=cut_context,
                )
                python = run_spprc_pricer(
                    self.data,
                    duals,
                    request,
                    cut_context=cut_context,
                )

                self.assertEqual(native.engine_status, "COMPLETE")
                self.assertFalse(native.certificate_blockers)
                self.assertAlmostEqual(native.best_found_rc, python.best_found_rc, places=8)
                python_negative_task_sets = {
                    frozenset(column.task_set)
                    for column in python.columns
                    if manual_journey_reduced_cost(
                        column,
                        duals,
                        cut_coefficients=cut_context.coefficients_for(column),
                    )
                    < -1.0e-6
                }
                self.assertEqual(
                    {frozenset(column.task_set) for column in native.columns},
                    python_negative_task_sets,
                )

    def test_phase_one_with_nonempty_cut_fails_closed(self) -> None:
        cut_context = CutContext(
            cuts=(subset_row_cut("sri-1", self.data.task_ids[:3]),)
        )
        result = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=JourneyDuals(cover={}),
                objective_mode=BACKEND_OBJECTIVE_PHASE_ONE,
                cut_context=cut_context,
            )
        )

        self.assertEqual(result.engine_status, "UNSUPPORTED_FEATURE")
        self.assertIn(
            "native_phase_one_nonempty_cut_context_unsupported",
            result.certificate_blockers,
        )

    def test_nonempty_cut_state_requires_explicit_promotion_flag(self) -> None:
        cut_context = CutContext(
            cuts=(subset_row_cut("sri-1", self.data.task_ids[:3]),)
        )
        result = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=JourneyDuals(cover={}),
                cut_context=cut_context,
            )
        )

        self.assertEqual(result.engine_status, "UNSUPPORTED_FEATURE")
        self.assertIn(
            "native_nonempty_cut_context_not_promoted",
            result.certificate_blockers,
        )

    def test_branch_tree_shares_audited_columns_and_propagates_remaining_deadline(self) -> None:
        from lunar_ice_bpc.exact.bpc.solver import branch_tree_solver as tree_module

        priced = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=JourneyDuals(
                    cover={task_id: 10.0 for task_id in self.data.task_ids}
                ),
            )
        ).columns
        self.assertGreaterEqual(len(priced), 2)
        initial, discovered = priced[:2]

        def fake_node(*args, **kwargs):
            queued = args[2]
            root = queued.depth == 0
            return {
                "node_id": queued.node_id,
                "node_status": "NODE_LP_CERTIFIED",
                "node_lp_bound": 0.0,
                "integer_incumbent": {
                    "matches_node_lp_bound": not root,
                    "objective": 0.0 if not root else None,
                    "_columns": (initial,) if not root else tuple(),
                },
                "fractional_branch_probe": {
                    "candidates": (
                        []
                        if not root
                        else [
                            {
                                "task_a": self.data.task_ids[0],
                                "task_b": self.data.task_ids[1],
                            }
                        ]
                    )
                },
                "child_node_ids": [],
                "_all_priced_columns": (discovered,) if root else tuple(),
            }

        fake_b0 = SimpleNamespace(objective=100.0, journeys=(initial,), note="test")
        with (
            patch.object(tree_module, "_solve_b3_node", side_effect=fake_node) as solve_node,
            patch.object(
                tree_module,
                "_tree_payload",
                side_effect=lambda **kwargs: {"nodes": kwargs["nodes"]},
            ),
        ):
            result = tree_module.solve_b3_branch_price_tree_baseline(
                self.data,
                initial_columns=(initial,),
                b0_direct=fake_b0,
                max_direct_tasks=5,
                max_tree_nodes=7,
                max_branch_depth=2,
                wall_time_limit_sec=5.0,
                run_b2_root_diagnostic=False,
                solve_b0_direct_first=False,
            )

        self.assertEqual(solve_node.call_count, 3)
        self.assertEqual(
            [call.args[2].node_id for call in solve_node.call_args_list],
            ["node_000", "node_001", "node_002"],
        )
        sibling_input = solve_node.call_args_list[1].args[1]
        self.assertIn(discovered, sibling_input)
        limits = [call.kwargs["wall_time_limit_sec"] for call in solve_node.call_args_list]
        self.assertTrue(all(0.0 < value <= 5.0 for value in limits))
        self.assertLessEqual(limits[-1], limits[0])
        self.assertEqual(result["tree_globally_shared_new_column_count"], 1)
        self.assertEqual(result["tree_global_initial_column_count"], 1)
        self.assertEqual(result["tree_global_final_column_count"], 2)
        self.assertEqual(
            result["tree_node_selection"], "best_bound_depth_tiebreak"
        )
        self.assertEqual(result["restricted_column_mip_attempt_count"], 2)
        self.assertEqual(
            result["restricted_column_mip_attempts"][1]["trigger"],
            "after_node:node_000",
        )

    def test_restricted_column_mip_is_feasible_upper_bound_only(self) -> None:
        from lunar_ice_bpc.exact.bpc.solver.branch_tree_solver import (
            _restricted_column_mip_incumbent,
        )

        universe = enumerate_direct_journey_columns(self.data, max_exact_tasks=5)
        result = _restricted_column_mip_incumbent(
            self.data,
            universe.columns,
            wall_time_limit_sec=5.0,
        )

        self.assertTrue(str(result["status"]).endswith("_FEASIBLE"))
        self.assertTrue(result["used_as_upper_bound_only"])
        selected = tuple(result["_columns"])
        self.assertTrue(selected)
        self.assertLessEqual(len(selected), self.data.fleet_size)
        cover = {task_id: 0 for task_id in self.data.task_ids}
        for column in selected:
            for task_id in column.task_set:
                cover[str(task_id)] += 1
        self.assertEqual(set(cover.values()), {1})
        self.assertAlmostEqual(
            result["objective"],
            sum(column.objective for column in selected),
            places=8,
        )

    def test_tree_global_lower_bound_includes_open_and_incomplete_subtrees(self) -> None:
        from lunar_ice_bpc.exact.bpc.certificates.proof_debt_queue import ProofDebtQueue
        from lunar_ice_bpc.exact.bpc.solver.branch_tree_solver import (
            _QueuedNode,
            _tree_payload,
        )

        nodes = [
            {
                "node_id": "node_000",
                "parent_node_id": None,
                "node_status": "BRANCHED",
                "child_node_ids": ["node_001", "node_002"],
                "node_lp_bound": 1.0,
                "node_lp_bound_official": True,
                "final_judge_certifying_proof_kind": True,
                "certificate_ledger": {"valid": True},
                "integer_incumbent": {"matches_node_lp_bound": False},
            },
            {
                "node_id": "node_002",
                "parent_node_id": "node_000",
                "node_status": "INCOMPLETE",
                "child_node_ids": [],
                # This last restricted-master value is not an official bound.
                "node_lp_bound": 1.4,
                "node_lp_bound_official": False,
                "inherited_parent_lower_bound": 1.0,
                "final_judge_certifying_proof_kind": False,
                "certificate_ledger": {"valid": True},
            },
        ]
        result = _tree_payload(
            data=self.data,
            b2={},
            b0_direct=SimpleNamespace(
                objective=None,
                status="NOT_RUN",
                certificate_scope="DIAGNOSTIC_PRICING_FRONTIER",
            ),
            nodes=nodes,
            open_nodes=(
                _QueuedNode(
                    "node_001",
                    "node_000",
                    1,
                    BranchContext(),
                    inherited_lower_bound=1.0,
                ),
            ),
            incumbent_objective=1.5,
            incumbent_source="TEST_FEASIBLE_INCUMBENT",
            incumbent_columns=tuple(),
            proof_debt=ProofDebtQueue(),
            node_limit_hit=False,
            max_tree_nodes=7,
            max_branch_depth=3,
            negative_eps=1.0e-6,
        )

        self.assertEqual(result["global_lower_bound"], 1.0)
        self.assertEqual(result["global_gap"], 0.5)
        self.assertEqual(result["open_node_count"], 1)
        self.assertEqual(result["incomplete_node_count"], 1)
        self.assertEqual(result["algorithm_status"], "BPC_GAP_AVAILABLE")

    def test_labels_dropped_blocks_certificate_even_if_engine_says_complete(self) -> None:
        raw = {
            "status": "COMPLETE",
            "search_exhaustive": True,
            "frontier_empty": True,
            "labels_dropped": True,
            "routes": [],
        }
        with patch("lunar_spprc_native.solve", return_value=raw):
            result = NativeRcsppInprocessBackend().solve(
                BackendPricingRequest(data=self.data, true_duals=JourneyDuals(cover={}))
            )

        self.assertTrue(result.labels_dropped)
        self.assertIn("native_labels_dropped", result.certificate_blockers)
        self.assertIsNone(result.proved_no_rc_below)
        self.assertFalse(result.can_enter_certificate_audit)

    def test_incomplete_exact_search_keeps_audited_negative_columns_without_rc_redline(self) -> None:
        import lunar_spprc_native
        from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
            _native_request_payload,
        )
        from lunar_ice_bpc.exact.bpc.pricing.labeling_pricer import (
            EXACT_ELEMENTARY_MODE,
            LabelingPricingConfig,
            run_bpc_labeling_pricer,
        )

        duals = JourneyDuals(cover={task_id: 10.0 for task_id in self.data.task_ids})
        request = BackendPricingRequest(data=self.data, true_duals=duals)
        raw = dict(lunar_spprc_native.solve(_native_request_payload(request)))
        raw.update(
            {
                "status": "TIMEOUT",
                "search_exhaustive": False,
                "frontier_empty": False,
                "routes": list(raw["routes"][:2]),
            }
        )
        with (
            patch("lunar_spprc_native.solve", return_value=raw),
            patch.dict(
                os.environ,
                {"LUNAR_ICE_SPPRC_EXACT_BACKEND": "native_rcspp_inprocess"},
            ),
        ):
            payload, columns = run_bpc_labeling_pricer(
                self.data,
                duals,
                config=LabelingPricingConfig(
                    mode=EXACT_ELEMENTARY_MODE,
                    max_exact_tasks=5,
                ),
            )

        self.assertTrue(columns)
        self.assertEqual(payload["pricing_state"], "FOUND_NEGATIVE")
        self.assertTrue(payload["pricing_rc_audit_pass"])
        self.assertTrue(payload["manual_rc_audit_pass"])
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertIn(
            "native_exact_search_incomplete",
            payload["native_backend_result"]["certificate_blockers"],
        )

    def test_shadow_backend_cannot_mutate_python_official_result(self) -> None:
        from lunar_ice_bpc.exact.bpc.pricing.labeling_pricer import (
            EXACT_ELEMENTARY_MODE,
            LabelingPricingConfig,
            run_bpc_labeling_pricer,
        )

        config = LabelingPricingConfig(mode=EXACT_ELEMENTARY_MODE, max_exact_tasks=5)
        duals = JourneyDuals(cover={})
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("LUNAR_ICE_SPPRC_EXACT_BACKEND", None)
            os.environ.pop("LUNAR_ICE_SPPRC_SHADOW_BACKEND", None)
            official_payload, official_columns = run_bpc_labeling_pricer(
                self.data, duals, config=config
            )
        with patch.dict(
            os.environ,
            {"LUNAR_ICE_SPPRC_SHADOW_BACKEND": "native_rcspp_inprocess"},
        ):
            shadow_payload, shadow_columns = run_bpc_labeling_pricer(
                self.data, duals, config=config
            )

        self.assertEqual(shadow_payload["pricing_state"], official_payload["pricing_state"])
        self.assertEqual(shadow_payload["can_certify_no_negative"], official_payload["can_certify_no_negative"])
        self.assertEqual(shadow_columns, official_columns)
        self.assertTrue(shadow_payload["native_shadow_enabled"])
        self.assertFalse(shadow_payload["native_shadow_mutates_official_result"])

    def test_facade_uses_native_for_nonempty_branch(self) -> None:
        branch = BranchContext(
            pair_decisions=(
                PairBranchDecision(self.data.task_ids[0], self.data.task_ids[1], SAME_JOURNEY),
            )
        )
        request = build_spprc_request(
            self.data,
            mode=SPPRC_EXACT_MODE,
            config_hash="native-fallback",
            backend_id="native_rcspp_inprocess",
            max_exact_tasks=5,
            branch_context=branch,
        )
        result = run_spprc_pricer(
            self.data,
            JourneyDuals(cover={}),
            request,
            branch_context=branch,
        )

        self.assertNotIn("native_backend_fallback_to_python", result.payload)
        self.assertEqual(result.engine_source, "native_rcspp_inprocess")
        self.assertTrue(result.search_exhaustive)
        self.assertTrue(
            all(journey_satisfies_branch_context(column, branch) for column in result.columns)
        )

    def test_host_backend_uses_same_contract(self) -> None:
        result = NativeRcsppHostBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=JourneyDuals(cover={}),
                wall_time_limit_sec=10.0,
                memory_limit_gb=1.0,
            )
        )

        self.assertEqual(result.backend_id, "native_rcspp_host")
        self.assertEqual(result.engine_status, "COMPLETE")
        self.assertTrue(result.can_enter_certificate_audit)

    def test_host_ipc_normalizes_read_only_dual_mappings(self) -> None:
        NativeRcsppHostBackend.close()
        try:
            result = NativeRcsppHostBackend().solve(
                BackendPricingRequest(
                    data=self.data,
                    true_duals=JourneyDuals(
                        cover=MappingProxyType(
                            {task_id: 0.0 for task_id in self.data.task_ids}
                        ),
                        cuts=MappingProxyType({}),
                    ),
                    wall_time_limit_sec=10.0,
                    memory_limit_gb=1.0,
                )
            )
        finally:
            NativeRcsppHostBackend.close()

        self.assertEqual(result.engine_status, "COMPLETE")
        self.assertTrue(result.can_enter_certificate_audit)

    def test_persistent_host_reuses_process_and_sends_same_instance_delta(self) -> None:
        NativeRcsppHostBackend.close()
        backend = NativeRcsppHostBackend()
        request = BackendPricingRequest(
            data=self.data,
            true_duals=JourneyDuals(cover={}),
            wall_time_limit_sec=10.0,
            memory_limit_gb=1.0,
        )
        try:
            first = backend.solve(request)
            second = backend.solve(request)
        finally:
            NativeRcsppHostBackend.close()

        self.assertEqual(first.engine_status, "COMPLETE")
        self.assertEqual(second.engine_status, "COMPLETE")
        self.assertEqual(first.telemetry["host_pid"], second.telemetry["host_pid"])
        self.assertFalse(first.telemetry["host_same_instance_delta"])
        self.assertTrue(second.telemetry["host_reused"])
        self.assertTrue(second.telemetry["host_same_instance_delta"])
        self.assertEqual(second.telemetry["host_request_kind"], "solve_delta")
        self.assertTrue(second.telemetry["graph_cache_hit"])

    def test_persistent_host_restarts_stale_build_before_solving(self) -> None:
        NativeRcsppHostBackend.close()
        backend = NativeRcsppHostBackend()
        request = BackendPricingRequest(
            data=self.data,
            true_duals=JourneyDuals(cover={}),
            wall_time_limit_sec=10.0,
            memory_limit_gb=1.0,
        )
        try:
            first = backend.solve(request)
            runtime = NativeRcsppHostBackend._runtime
            self.assertIsNotNone(runtime)
            runtime.build_hash = "deliberately-stale"
            second = backend.solve(request)
        finally:
            NativeRcsppHostBackend.close()

        self.assertEqual(first.engine_status, "COMPLETE")
        self.assertEqual(second.engine_status, "COMPLETE")
        self.assertNotEqual(first.telemetry["host_pid"], second.telemetry["host_pid"])
        self.assertTrue(second.telemetry["host_stale_restarted"])

    def test_host_memory_kill_discards_proof_and_restarts_cleanly(self) -> None:
        NativeRcsppHostBackend.close()
        backend = NativeRcsppHostBackend()
        limited = backend.solve(
            BackendPricingRequest(
                data=self.data10,
                true_duals=JourneyDuals(
                    cover={task_id: 1.0 for task_id in self.data10.task_ids}
                ),
                wall_time_limit_sec=10.0,
                memory_limit_gb=0.001,
            )
        )
        recovered = backend.solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=JourneyDuals(cover={}),
                wall_time_limit_sec=10.0,
                memory_limit_gb=1.0,
            )
        )
        NativeRcsppHostBackend.close()

        self.assertEqual(limited.engine_status, "MEMORY_LIMIT")
        self.assertFalse(limited.can_enter_certificate_audit)
        self.assertTrue(limited.telemetry["host_proof_state_discarded"])
        self.assertTrue(limited.telemetry["host_partial_result_received"])
        self.assertTrue(limited.partial_columns_valid)
        self.assertEqual(recovered.engine_status, "COMPLETE")
        self.assertTrue(recovered.can_enter_certificate_audit)

    def test_native_spprc_facade_certifies_only_after_backend_audit(self) -> None:
        request = build_spprc_request(
            self.data,
            mode=SPPRC_EXACT_MODE,
            config_hash="native-facade",
            backend_id="native_rcspp_inprocess",
            max_exact_tasks=5,
        )
        result = run_spprc_pricer(self.data, JourneyDuals(cover={}), request)

        self.assertTrue(result.can_certify_no_negative)
        self.assertTrue(result.search_exhaustive)
        self.assertEqual(result.proved_no_rc_below, -1.0e-6)
        self.assertIsNone(result.global_min_rc)

    def test_full_instance_hash_changes_with_arc_data(self) -> None:
        original = spprc_instance_hash(self.data)
        first_key = sorted(self.data.arcs)[0]
        first_type = sorted(self.data.arcs[first_key])[0]
        changed_arcs = {key: dict(value) for key, value in self.data.arcs.items()}
        changed_arcs[first_key][first_type] = replace(
            changed_arcs[first_key][first_type],
            travel_time_min=changed_arcs[first_key][first_type].travel_time_min + 0.5,
        )
        changed = replace(self.data, arcs=changed_arcs)

        self.assertNotEqual(original, spprc_instance_hash(changed))

    def test_supplied_instance_hash_mismatch_fails_closed_before_native_call(self) -> None:
        result = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=JourneyDuals(cover={}),
                instance_hash="stale-instance-hash",
            )
        )

        self.assertEqual(result.engine_status, "HASH_MISMATCH")
        self.assertIn("native_instance_hash_mismatch", result.certificate_blockers)
        self.assertFalse(result.can_enter_certificate_audit)


class NativeSpprcScaleProfileTests(unittest.TestCase):
    def test_all_six_scales_have_independent_profiles(self) -> None:
        profiles = [native_spprc_scale_profile(scale) for scale in (5, 10, 20, 30, 50, 100)]

        self.assertEqual([profile.scale for profile in profiles], [5, 10, 20, 30, 50, 100])
        self.assertEqual(profiles[0].ng_sizes, (3, 5))
        self.assertEqual(profiles[3].ng_sizes, (6, 10, 14, 30))
        self.assertEqual(profiles[-1].backend_id, "native_rcspp_host")
        self.assertTrue(all(profile.proof_time_limit_sec > 0 for profile in profiles))
        self.assertEqual(profiles[2].remaining_proof_time_sec(worker_elapsed_sec=17.5), 882.5)
        self.assertEqual(profiles[2].tree_max_nodes, 127)
        self.assertEqual(profiles[2].tree_max_branch_depth, 8)
        self.assertEqual(profiles[3].tree_max_branch_depth, 12)

    def test_acceptance_runner_dry_run_parameterizes_available_scales(self) -> None:
        from lunar_ice_bpc.runners.native_spprc_acceptance import run_native_spprc_acceptance

        project_root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            summary = run_native_spprc_acceptance(
                project_root=project_root,
                config={},
                scales=(5, 10, 20, 30, 50, 100),
                limit=1,
                output_dir=directory,
                dry_run=True,
            )

        by_scale = {row["scale"]: row for row in summary["rows"]}
        self.assertEqual(by_scale[5]["status"], "DRY_RUN")
        self.assertIn("--labeling-worker-max-task-cap", by_scale[30]["command"])
        depth_index = by_scale[30]["command"].index("--tree-closure-max-branch-depth")
        self.assertEqual(by_scale[30]["command"][depth_index + 1], "12")
        self.assertEqual(
            by_scale[50]["status"],
            "DRY_RUN" if by_scale[50]["instance_count"] else "NO_INSTANCES_AVAILABLE",
        )

    def test_tree_subprocess_timeout_is_a_legal_fail_closed_row(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        spec = importlib.util.spec_from_file_location(
            "native_spprc_b42_timeout_test",
            project_root / "scripts/run_lunar_ice_b4_2_cold_exact.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        args = module._build_parser().parse_args([])
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "tree"
            source_probe = Path(directory) / "probe.json"
            source_probe.write_text("{}", encoding="utf-8")
            timeout = subprocess.TimeoutExpired(
                cmd=["tree"],
                timeout=15.0,
                output=b"partial progress",
                stderr=b"",
            )
            with patch.object(module.subprocess, "run", side_effect=timeout):
                row = module._run_tree_closure(
                    args,
                    instance_index=1,
                    instance_path=Path(directory) / "instance.json",
                    source_probe=source_probe,
                    output_dir=output_dir,
                    time_limit_sec=10.0,
                )

        self.assertEqual(row["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(row["pricing_state"], "INCOMPLETE_LIMIT")
        self.assertFalse(row["exact_certificate"])
        self.assertTrue(row["tree_subprocess_timeout"])
        self.assertTrue(row["tree_subprocess_partial_stdout_present"])
        self.assertIn("no certificate", row["fail_reason"])

    def test_exact_first_skipped_worker_is_vacuously_true_dual_audited(self) -> None:
        from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (
            _exact_final_judge_first_skipped_worker_result,
            _worker_round_diagnostic_fields,
        )

        skipped = _exact_final_judge_first_skipped_worker_result(
            worker_pricer_kind="relaxed_labeling",
            remaining_wall_time_sec=10.0,
        )
        telemetry = _worker_round_diagnostic_fields(skipped.payload)

        self.assertTrue(telemetry["worker_dual_only"])
        self.assertTrue(telemetry["worker_true_dual_candidate_audit_pass"])
        self.assertTrue(telemetry["true_dual_rc_recomputed"])
        self.assertFalse(telemetry["tail_dual_no_column_can_certify"])


if __name__ == "__main__":
    unittest.main()
