from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from time import sleep
from types import MappingProxyType, SimpleNamespace
import unittest
from unittest.mock import patch

from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.exact.bpc.pricing.backends import (
    BACKEND_MODE_EXACT_PROOF,
    BACKEND_MODE_NEGATIVE_HARVEST,
    BACKEND_OBJECTIVE_PHASE_ONE,
    NATIVE_BIDIRECTIONAL_MIDPOINT_HYBRID_BACKEND_ID,
    NATIVE_BIDIRECTIONAL_MIDPOINT_PARTIAL_HYBRID_BACKEND_ID,
    NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID,
    PRICING_LIFECYCLE_SCOPE_ROOT_CG,
    PRICING_LIFECYCLE_SCOPE_TREE_NODE,
    BackendPricingRequest,
    BackendRegistry,
    NativeBidirectionalMidpointHybridBackend,
    NativeBidirectionalMidpointPartialHybridBackend,
    NativeBidirectionalRootPartialHybridBackend,
    NativeDssrHostBackend,
    NativeDssrInprocessBackend,
    NativeDssrV2HostBackend,
    NativeDssrV2InprocessBackend,
    NativeNgDssrV3HostBackend,
    NativeNgDssrV3InprocessBackend,
    NativeRcsppInprocessBackend,
    NativeRcsppHostBackend,
    native_spprc_scale_profile,
)
from lunar_ice_bpc.exact.bpc.pricing.backends import native_rcspp as native_rcspp_module
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (
    SPPRC_EXACT_MODE,
    build_spprc_request,
    run_spprc_pricer,
    spprc_instance_hash,
)
from lunar_ice_bpc.exact.bpc.pricing.labeling_pricer import (
    EXACT_ELEMENTARY_MODE,
    LabelingPricingConfig,
    run_bpc_labeling_pricer,
)
from lunar_ice_bpc.exact.bpc.guidance.replay import load_pricing_snapshot
from lunar_ice_bpc.exact.bpc.core.column_signature import (
    column_signature_from_journey,
)
from lunar_ice_bpc.exact.core.branching import (
    DIFFERENT_JOURNEY,
    SAME_JOURNEY,
    BranchContext,
    PairBranchDecision,
    journey_satisfies_branch_context,
)
from lunar_ice_bpc.exact.core.cuts import (
    CutContext,
    fleet_lower_bound_cut,
    subset_row_cut,
    true_dual_binding_hash,
)
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
        cls.data20 = load_lunar_ice_data(
            json.loads(
                (
                    project_root
                    / "data/instances/lunar_ice_sp50_020/instance_001_logical_graph.json"
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

    def test_processed_label_budget_is_harvest_only(self) -> None:
        request = BackendPricingRequest(
            data=self.data,
            true_duals=JourneyDuals(cover={}),
            mode=BACKEND_MODE_NEGATIVE_HARVEST,
            harvest_max_processed_labels=17,
        )
        self.assertEqual(request.harvest_max_processed_labels, 17)
        with self.assertRaisesRegex(
            ValueError,
            "cannot truncate exact proof",
        ):
            BackendPricingRequest(
                data=self.data,
                true_duals=JourneyDuals(cover={}),
                mode=BACKEND_MODE_EXACT_PROOF,
                harvest_max_processed_labels=17,
            )

    def test_exact_negative_escape_is_partial_and_never_certifies(self) -> None:
        duals = JourneyDuals(
            cover={task_id: 100.0 for task_id in self.data.task_ids}
        )
        request = BackendPricingRequest(
            data=self.data,
            true_duals=duals,
            exact_negative_escape_enabled=True,
            exact_admission_batch_size=1,
            exact_raw_negative_pool_size=4,
        )
        result = NativeRcsppInprocessBackend().solve(request)
        self.assertEqual(result.engine_status, "FOUND_NEGATIVE_PARTIAL")
        self.assertFalse(result.search_exhaustive)
        self.assertFalse(result.frontier_empty)
        self.assertFalse(result.can_enter_certificate_audit)
        self.assertEqual(len(result.columns), 4)
        semantic_signatures = tuple(
            column_signature_from_journey(column)
            for column in result.columns
        )
        self.assertEqual(
            len(set(semantic_signatures)),
            len(semantic_signatures),
        )
        self.assertTrue(
            all(
                manual_journey_reduced_cost(column, duals)
                < -request.negative_eps
                for column in result.columns
            )
        )
        self.assertTrue(result.partial_columns_valid)
        self.assertTrue(result.telemetry["negative_escape_triggered"])
        self.assertEqual(
            result.telemetry["raw_unique_negative_count"], 4
        )
        self.assertIn(
            "native_exact_negative_escape_partial",
            result.certificate_blockers,
        )

    def test_proof_queue_policies_preserve_exact_result_and_report_policy(self) -> None:
        results = {}
        for policy_id in ("Q0", "QC0", "QD1", "QB1"):
            results[policy_id] = NativeRcsppInprocessBackend().solve(
                BackendPricingRequest(
                    data=self.data20,
                    true_duals=JourneyDuals(cover={}),
                    proof_queue_policy_id=policy_id,
                )
            )

        for policy_id, result in results.items():
            self.assertEqual(result.engine_status, "COMPLETE")
            self.assertTrue(result.search_exhaustive)
            self.assertTrue(result.frontier_empty)
            self.assertFalse(result.labels_dropped)
            self.assertEqual(result.proved_no_rc_below, -1.0e-6)
            self.assertEqual(
                result.telemetry["proof_queue_policy_id"],
                policy_id,
            )
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

    def test_bidirectional_feasibility_probe_matches_frozen_native_route(self) -> None:
        import lunar_spprc_native
        from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
            _manual_backend_reduced_cost,
            _native_request_payload,
            _reconstruct_column,
        )

        if (
            lunar_spprc_native.build_info().get(
                "bidirectional_feasibility_compiled"
            )
            != "true"
        ):
            self.skipTest(
                "isolated bidirectional feasibility build is not active"
            )
        duals = JourneyDuals(
            cover={task_id: 100.0 for task_id in self.data.task_ids}
        )
        request = BackendPricingRequest(
            data=self.data,
            true_duals=duals,
        )
        payload = _native_request_payload(request)
        raw = dict(lunar_spprc_native.solve(payload))
        route = next(
            row
            for row in raw["routes"]
            if len(row["sorties"]) >= 2
        )
        audit = dict(
            lunar_spprc_native.bidirectional_feasibility_probe(
                {
                    **payload,
                    "forward_sorties": route["sorties"][:1],
                    "backward_sorties": route["sorties"][1:],
                }
            )
        )
        self.assertEqual(
            audit["status"],
            "FEASIBLE_JOIN_DIAGNOSTIC_ONLY",
        )
        self.assertTrue(audit["feasible"])
        self.assertTrue(audit["task_sets_disjoint"])
        self.assertTrue(audit["suffix_boundary_feasible"])
        self.assertTrue(audit["branch_feasible"])
        self.assertFalse(audit["can_certify_no_negative"])
        self.assertEqual(
            audit["certificate_scope"],
            "DIAGNOSTIC_BIDIRECTIONAL_FEASIBILITY_ONLY",
        )
        self.assertAlmostEqual(
            audit["true_reduced_cost"],
            route["reduced_cost"],
            places=10,
        )
        task_meet = dict(
            lunar_spprc_native.bidirectional_task_meet_frontier_probe(
                {
                    **payload,
                    "bidirectional_max_partial_states_per_direction": (
                        1_000_000
                    ),
                    "bidirectional_max_join_checks": 5_000_000,
                    "bidirectional_wall_time_limit_sec": 30.0,
                }
            )
        )
        self.assertEqual(
            task_meet["status"],
            "TASK_MEET_SORTIE_ENUMERATION_COMPLETE",
        )
        self.assertTrue(task_meet["join_exhaustive"])
        self.assertGreater(
            task_meet["feasible_joined_sorties"],
            task_meet["nondominated_sortie_count"],
        )
        self.assertFalse(task_meet["can_certify_no_negative"])

        journey = dict(
            lunar_spprc_native.bidirectional_journey_frontier_probe(
                {
                    **payload,
                    "bidirectional_max_partial_states_per_direction": (
                        1_000_000
                    ),
                    "bidirectional_max_join_checks": 5_000_000,
                    "bidirectional_sortie_wall_time_limit_sec": 30.0,
                    "bidirectional_max_journey_labels": 1_000_000,
                    "bidirectional_max_journey_extension_checks": (
                        10_000_000
                    ),
                    "bidirectional_journey_wall_time_limit_sec": 30.0,
                }
            )
        )
        self.assertEqual(
            journey["status"],
            "JOURNEY_FRONTIER_COMPLETE_DIAGNOSTIC_ONLY",
        )
        self.assertTrue(journey["search_exhaustive"])
        self.assertTrue(journey["frontier_empty"])
        self.assertFalse(journey["can_certify_no_negative"])
        self.assertAlmostEqual(
            journey["best_true_reduced_cost"],
            raw["best_found_rc"],
            places=9,
        )
        midpoint = dict(
            lunar_spprc_native.bidirectional_midpoint_journey_meet(
                {
                    **payload,
                    "bidirectional_max_partial_states_per_direction": (
                        1_000_000
                    ),
                    "bidirectional_max_join_checks": 5_000_000,
                    "bidirectional_sortie_wall_time_limit_sec": 30.0,
                    "bidirectional_midpoint_split_fraction": 0.02,
                    "bidirectional_midpoint_max_forward_labels": 100_000,
                    "bidirectional_midpoint_max_backward_labels": 100_000,
                    "bidirectional_midpoint_max_crossing_labels": 100_000,
                    "bidirectional_midpoint_max_extension_checks": (
                        10_000_000
                    ),
                    "bidirectional_midpoint_max_join_checks": 5_000_000,
                    "bidirectional_midpoint_wall_time_limit_sec": 30.0,
                }
            )
        )
        self.assertEqual(
            midpoint["status"],
            "MIDPOINT_MEET_COMPLETE_DIAGNOSTIC_ONLY",
        )
        self.assertTrue(midpoint["search_exhaustive"])
        self.assertTrue(midpoint["forward_exhaustive"])
        self.assertTrue(midpoint["backward_exhaustive"])
        self.assertTrue(midpoint["crossing_exhaustive"])
        self.assertTrue(midpoint["join_exhaustive"])
        self.assertFalse(midpoint["can_certify_no_negative"])
        self.assertGreater(midpoint["backward_generated_labels"], 1)
        self.assertGreater(midpoint["crossing_generated_labels"], 0)
        self.assertEqual(
            midpoint["join_checks"],
            midpoint["time_index_candidate_join_pairs"],
        )
        self.assertEqual(
            midpoint["unindexed_active_join_pairs"],
            midpoint["time_index_candidate_join_pairs"]
            + midpoint["time_index_pruned_join_pairs"],
        )
        self.assertAlmostEqual(
            midpoint["best_true_reduced_cost"],
            raw["best_found_rc"],
            places=9,
        )
        self.assertEqual(
            midpoint["returned_negative_route_count"],
            len(midpoint["routes"]),
        )
        self.assertGreater(midpoint["returned_negative_route_count"], 0)
        self.assertAlmostEqual(
            midpoint["routes"][0]["reduced_cost"],
            midpoint["best_true_reduced_cost"],
            places=9,
        )
        returned_task_sets = set()
        for native_route in midpoint["routes"]:
            column = _reconstruct_column(request, native_route)
            returned_task_sets.add(frozenset(column.task_set))
            self.assertAlmostEqual(
                native_route["reduced_cost"],
                _manual_backend_reduced_cost(column, request),
                delta=2.0e-6,
            )
        self.assertEqual(
            len(returned_task_sets),
            midpoint["returned_negative_route_count"],
        )

    def test_bidirectional_hybrid_runs_midpoint_on_scale5(
        self,
    ) -> None:
        backend = BackendRegistry.create(
            NATIVE_BIDIRECTIONAL_MIDPOINT_HYBRID_BACKEND_ID
        )
        self.assertIsInstance(
            backend,
            NativeBidirectionalMidpointHybridBackend,
        )
        request = BackendPricingRequest(
            data=self.data,
            true_duals=JourneyDuals(
                cover={
                    task_id: 100.0
                    for task_id in self.data.task_ids
                }
            ),
            mode=BACKEND_MODE_NEGATIVE_HARVEST,
        )
        try:
            result = backend.solve(request)
        finally:
            NativeRcsppHostBackend.close()
        self.assertEqual(
            result.backend_id,
            NATIVE_BIDIRECTIONAL_MIDPOINT_HYBRID_BACKEND_ID,
        )
        self.assertTrue(result.columns)
        self.assertFalse(
            result.telemetry[
                "bidirectional_midpoint_hybrid_fallback_used"
            ]
        )
        self.assertTrue(
            result.telemetry[
                "bidirectional_midpoint_hybrid_attempted"
            ]
        )
        self.assertTrue(
            result.telemetry[
                "bidirectional_midpoint_hybrid_accepted"
            ]
        )
        self.assertEqual(
            result.engine_status,
            "FOUND_NEGATIVE_PARTIAL",
        )
        self.assertFalse(result.can_enter_certificate_audit)

    def test_bidirectional_hybrid_scale5_no_negative_falls_back_inprocess(
        self,
    ) -> None:
        request = BackendPricingRequest(
            data=self.data,
            true_duals=JourneyDuals(cover={}),
        )
        expected = NativeRcsppInprocessBackend().solve(request)
        actual = (
            NativeBidirectionalMidpointHybridBackend()
            .solve(request)
        )
        self.assertEqual(
            actual.telemetry[
                "bidirectional_midpoint_fallback_backend_id"
            ],
            "native_rcspp_inprocess",
        )
        self.assertTrue(
            actual.telemetry[
                "bidirectional_midpoint_hybrid_fallback_used"
            ]
        )
        self.assertEqual(
            actual.engine_status,
            expected.engine_status,
        )
        self.assertEqual(
            actual.can_enter_certificate_audit,
            expected.can_enter_certificate_audit,
        )
        self.assertEqual(
            actual.proved_no_rc_below,
            expected.proved_no_rc_below,
        )
        self.assertEqual(actual.columns, expected.columns)

    def test_bidirectional_partial_hybrid_retains_audited_incomplete_witnesses(
        self,
    ) -> None:
        import lunar_spprc_native
        from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
            _native_request_payload,
        )

        backend = BackendRegistry.create(
            NATIVE_BIDIRECTIONAL_MIDPOINT_PARTIAL_HYBRID_BACKEND_ID
        )
        self.assertIsInstance(
            backend,
            NativeBidirectionalMidpointPartialHybridBackend,
        )
        request = BackendPricingRequest(
            data=self.data,
            true_duals=JourneyDuals(
                cover={
                    task_id: 100.0
                    for task_id in self.data.task_ids
                }
            ),
            mode=BACKEND_MODE_NEGATIVE_HARVEST,
        )
        payload = _native_request_payload(request)
        payload.update(backend._midpoint_parameters(request))
        raw = dict(
            lunar_spprc_native.bidirectional_midpoint_journey_meet(
                payload
            )
        )
        self.assertTrue(raw["routes"])
        raw.update(
            {
                "status": "MIDPOINT_MEET_LABEL_LIMIT",
                "search_exhaustive": False,
                "forward_exhaustive": False,
                "join_exhaustive": False,
                "can_certify_no_negative": False,
            }
        )
        old_result = (
            NativeBidirectionalMidpointHybridBackend()
            ._audit_midpoint_result(
                request,
                raw,
                build_info=dict(lunar_spprc_native.build_info()),
                elapsed_sec=0.25,
            )
        )
        result = backend._audit_midpoint_result(
            request,
            raw,
            build_info=dict(lunar_spprc_native.build_info()),
            elapsed_sec=0.25,
        )

        self.assertIsNone(old_result)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertTrue(result.columns)
        self.assertEqual(result.engine_status, "FOUND_NEGATIVE_PARTIAL")
        self.assertFalse(result.search_exhaustive)
        self.assertFalse(result.can_enter_certificate_audit)
        self.assertTrue(
            result.telemetry[
                "bidirectional_midpoint_partial_witness_accepted"
            ]
        )
        self.assertEqual(
            result.telemetry[
                "negative_escape_termination_reason"
            ],
            "BIDIRECTIONAL_MIDPOINT_PARTIAL_NEGATIVE_POOL",
        )

    def test_bidirectional_root_partial_hybrid_is_tree_conservative(
        self,
    ) -> None:
        import lunar_spprc_native
        from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
            _native_request_payload,
        )

        backend = BackendRegistry.create(
            NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID
        )
        self.assertIsInstance(
            backend,
            NativeBidirectionalRootPartialHybridBackend,
        )
        base_request = BackendPricingRequest(
            data=self.data,
            true_duals=JourneyDuals(
                cover={
                    task_id: 100.0
                    for task_id in self.data.task_ids
                }
            ),
            mode=BACKEND_MODE_NEGATIVE_HARVEST,
            pricing_lifecycle_scope=(
                PRICING_LIFECYCLE_SCOPE_ROOT_CG
            ),
        )
        payload = _native_request_payload(base_request)
        payload.update(backend._midpoint_parameters(base_request))
        raw = dict(
            lunar_spprc_native.bidirectional_midpoint_journey_meet(
                payload
            )
        )
        self.assertTrue(raw["routes"])
        raw.update(
            {
                "status": "MIDPOINT_MEET_LABEL_LIMIT",
                "search_exhaustive": False,
                "forward_exhaustive": False,
                "join_exhaustive": False,
                "can_certify_no_negative": False,
            }
        )

        root_result = backend._audit_midpoint_result(
            base_request,
            raw,
            build_info=dict(lunar_spprc_native.build_info()),
            elapsed_sec=0.25,
        )
        tree_result = backend._audit_midpoint_result(
            replace(
                base_request,
                pricing_lifecycle_scope=(
                    PRICING_LIFECYCLE_SCOPE_TREE_NODE
                ),
            ),
            raw,
            build_info=dict(lunar_spprc_native.build_info()),
            elapsed_sec=0.25,
        )
        unspecified_result = backend._audit_midpoint_result(
            replace(
                base_request,
                pricing_lifecycle_scope="unspecified",
            ),
            raw,
            build_info=dict(lunar_spprc_native.build_info()),
            elapsed_sec=0.25,
        )

        self.assertIsNotNone(root_result)
        assert root_result is not None
        self.assertFalse(root_result.can_enter_certificate_audit)
        self.assertEqual(
            root_result.telemetry["pricing_lifecycle_scope"],
            PRICING_LIFECYCLE_SCOPE_ROOT_CG,
        )
        self.assertTrue(
            root_result.telemetry[
                "bidirectional_midpoint_partial_allowed_for_scope"
            ]
        )
        self.assertEqual(
            root_result.telemetry[
                "bidirectional_midpoint_partial_scope_policy"
            ],
            "root_cg_only_tree_conservative",
        )
        self.assertIsNone(tree_result)
        self.assertIsNone(unspecified_result)

    def test_bidirectional_partial_hybrid_empty_incomplete_result_falls_back(
        self,
    ) -> None:
        request = BackendPricingRequest(
            data=self.data,
            true_duals=JourneyDuals(cover={}),
        )
        raw = {
            "status": "MIDPOINT_SORTIE_POOL_INCOMPLETE",
            "policy_id": "p0v4_frozen_dual_depot_midpoint_meet_v1",
            "search_exhaustive": False,
            "can_certify_no_negative": False,
            "routes": [],
        }
        backend = NativeBidirectionalMidpointPartialHybridBackend()

        self.assertIsNone(
            backend._audit_midpoint_result(
                request,
                raw,
                build_info={},
                elapsed_sec=0.5,
            )
        )
        telemetry = backend._fallback_prepass_telemetry(raw)
        self.assertEqual(
            telemetry["bidirectional_midpoint_raw_status"],
            "MIDPOINT_SORTIE_POOL_INCOMPLETE",
        )
        self.assertEqual(
            telemetry["bidirectional_midpoint_raw_route_count"],
            0,
        )

    def test_bidirectional_hybrid_default_wall_limit_is_bounded(self) -> None:
        request = BackendPricingRequest(
            data=self.data,
            true_duals=JourneyDuals(cover={}),
        )
        parameters = (
            NativeBidirectionalMidpointHybridBackend
            ._midpoint_parameters(request)
        )
        self.assertEqual(
            parameters[
                "bidirectional_midpoint_wall_time_limit_sec"
            ],
            30.0,
        )
        self.assertEqual(
            parameters[
                "bidirectional_sortie_wall_time_limit_sec"
            ],
            30.0,
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
                    self.assertGreaterEqual(
                        accelerated.telemetry["subset_dominance_key_lookups"],
                        accelerated.telemetry["subset_dominance_nonempty_buckets"],
                    )
                    self.assertGreaterEqual(
                        accelerated.telemetry["subset_dominance_nonempty_buckets"],
                        accelerated.telemetry[
                            "subset_dominance_summary_skipped_buckets"
                        ],
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

    def test_subset_row_cut_reduced_costs_match_python(self) -> None:
        for cut in (
            subset_row_cut("sri-3", self.data.task_ids[:3]),
            subset_row_cut("sri-5", self.data.task_ids[:5]),
        ):
            with self.subTest(cut_id=cut.cut_id):
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
                build_info = native.telemetry["native_build_info"]
                self.assertEqual(
                    build_info["cut_state_schema"],
                    "packed_exact_overlap_u64_sri3_2bit_sri5_3bit_v2",
                )
                self.assertEqual(int(build_info["cut_state_bytes"]), 8)
                self.assertEqual(int(build_info["cut_state_max_bits"]), 48)
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

    def test_branch_plus_subset_row_cut_matches_python_reference(self) -> None:
        branch = BranchContext(
            pair_decisions=(
                PairBranchDecision(
                    self.data.task_ids[0],
                    self.data.task_ids[1],
                    DIFFERENT_JOURNEY,
                ),
            )
        )
        cut = subset_row_cut("sri-branch-cut", self.data.task_ids[:3])
        cut_context = CutContext(cuts=(cut,))
        duals = JourneyDuals(
            cover={task_id: 10.0 for task_id in self.data.task_ids},
            cuts={cut.cut_id: 0.3},
        )
        native = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=duals,
                branch_context=branch,
                cut_context=cut_context,
            )
        )
        request = build_spprc_request(
            self.data,
            mode=SPPRC_EXACT_MODE,
            config_hash="native-branch-plus-cut",
            backend_id="python_reference",
            max_exact_tasks=5,
            harvest_target=1000,
            exact_negative_harvest_target=1000,
            branch_context=branch,
            cut_context=cut_context,
        )
        python = run_spprc_pricer(
            self.data,
            duals,
            request,
            branch_context=branch,
            cut_context=cut_context,
        )

        self.assertEqual(native.engine_status, "COMPLETE")
        self.assertTrue(native.search_exhaustive)
        self.assertTrue(native.frontier_empty)
        self.assertFalse(native.certificate_blockers)
        self.assertEqual(native.telemetry["rc_mismatch_count"], 0)
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

    def test_phase_one_with_nonempty_cut_matches_manual_rc(self) -> None:
        cut_context = CutContext(
            cuts=(subset_row_cut("sri-1", self.data.task_ids[:3]),)
        )
        phase_one = solve_phase_one_journey_rmp(
            self.data.task_ids,
            tuple(),
            fleet_size=self.data.fleet_size,
            cut_context=cut_context,
        )
        result = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=phase_one.duals,
                objective_mode=BACKEND_OBJECTIVE_PHASE_ONE,
                cut_context=cut_context,
            )
        )

        self.assertEqual(result.engine_status, "COMPLETE")
        self.assertFalse(result.certificate_blockers)
        self.assertTrue(result.columns)
        self.assertEqual(result.telemetry["rc_mismatch_count"], 0)
        self.assertTrue(result.telemetry["cut_state_required"])

    def test_zero_dual_active_cut_requires_no_native_cut_state(self) -> None:
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

        self.assertEqual(result.engine_status, "COMPLETE")
        self.assertFalse(result.certificate_blockers)
        self.assertTrue(result.telemetry["cut_state_required"])
        self.assertFalse(result.telemetry["cut_state_effective"])
        self.assertEqual(result.telemetry["active_cut_count"], 1)
        self.assertEqual(result.telemetry["pricing_cut_count"], 0)
        self.assertEqual(result.telemetry["projected_zero_dual_cut_count"], 1)

    def test_exact_nonzero_dual_cut_projection_matches_full_cut_pricing(self) -> None:
        task_ids = self.data.task_ids
        cuts = (
            subset_row_cut("sri-zero", (task_ids[0], task_ids[1], task_ids[2])),
            subset_row_cut("sri-neg-zero", (task_ids[0], task_ids[1], task_ids[3])),
            subset_row_cut("sri-tiny", (task_ids[0], task_ids[1], task_ids[4])),
            subset_row_cut("sri-positive", (task_ids[0], task_ids[2], task_ids[3])),
        )
        cut_context = CutContext(cuts=cuts)
        duals = JourneyDuals(
            cover={task_id: 10.0 for task_id in task_ids},
            cuts={
                "sri-zero": 0.0,
                "sri-neg-zero": -0.0,
                "sri-tiny": -1.0e-15,
                "sri-positive": -0.3,
            },
        )
        projected = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=duals,
                cut_context=cut_context,
            )
        )
        full = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=duals,
                cut_context=cut_context,
                cut_dual_projection_enabled=False,
            )
        )

        self.assertEqual(projected.engine_status, "COMPLETE")
        self.assertEqual(full.engine_status, "COMPLETE")
        self.assertFalse(projected.certificate_blockers)
        self.assertFalse(full.certificate_blockers)
        self.assertAlmostEqual(projected.best_found_rc, full.best_found_rc, places=8)
        self.assertEqual(
            {frozenset(column.task_set) for column in projected.columns},
            {frozenset(column.task_set) for column in full.columns},
        )
        self.assertEqual(projected.telemetry["active_cut_count"], 4)
        self.assertEqual(projected.telemetry["pricing_cut_count"], 2)
        self.assertEqual(projected.telemetry["projected_zero_dual_cut_count"], 2)
        self.assertTrue(projected.telemetry["cut_state_effective"])
        self.assertEqual(full.telemetry["pricing_cut_count"], 4)
        self.assertEqual(full.telemetry["projected_zero_dual_cut_count"], 0)
        self.assertNotEqual(
            projected.telemetry["active_cut_context_hash"],
            projected.telemetry["pricing_cut_context_hash"],
        )
        self.assertEqual(
            full.telemetry["active_cut_context_hash"],
            full.telemetry["pricing_cut_context_hash"],
        )

        phase_one_projected = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=duals,
                objective_mode=BACKEND_OBJECTIVE_PHASE_ONE,
                cut_context=cut_context,
            )
        )
        phase_one_full = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=duals,
                objective_mode=BACKEND_OBJECTIVE_PHASE_ONE,
                cut_context=cut_context,
                cut_dual_projection_enabled=False,
            )
        )
        self.assertEqual(phase_one_projected.engine_status, "COMPLETE")
        self.assertEqual(phase_one_full.engine_status, "COMPLETE")
        self.assertAlmostEqual(
            phase_one_projected.best_found_rc,
            phase_one_full.best_found_rc,
            places=8,
        )
        self.assertEqual(
            {frozenset(column.task_set) for column in phase_one_projected.columns},
            {frozenset(column.task_set) for column in phase_one_full.columns},
        )
        self.assertEqual(phase_one_projected.telemetry["rc_mismatch_count"], 0)

    def test_native_projection_is_bound_into_final_cut_certificate(self) -> None:
        cut = subset_row_cut("sri-projection-certificate", self.data.task_ids[:3])
        cut_context = CutContext(cuts=(cut,))
        payload, columns = run_bpc_labeling_pricer(
            self.data,
            JourneyDuals(
                cover={task_id: 0.0 for task_id in self.data.task_ids},
                cuts={cut.cut_id: -0.0},
            ),
            config=LabelingPricingConfig(
                mode=EXACT_ELEMENTARY_MODE,
                max_exact_tasks=5,
                completion_bound_enabled=False,
            ),
            cut_context=cut_context,
        )

        self.assertFalse(columns)
        self.assertTrue(payload["can_certify_no_negative"])
        self.assertTrue(payload["live_cut_certificate_supported"])
        self.assertEqual(payload["cut_count"], 1)
        self.assertEqual(payload["pricing_cut_count"], 0)
        self.assertEqual(payload["projected_zero_dual_cut_count"], 1)
        projection = payload["cut_certificate_support"][
            "cut_dual_projection_audit"
        ]
        self.assertTrue(projection["binding_required"])
        self.assertTrue(projection["binding_present"])
        self.assertTrue(projection["projection_enabled"])
        self.assertTrue(projection["valid"])

    def test_fleet_cut_is_diagnostic_only_for_native_live_v1(self) -> None:
        cut_context = CutContext(
            cuts=(fleet_lower_bound_cut("fleet-1", min_vehicles=2),)
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
            "unsupported_live_cut_type:fleet_lower_bound",
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

    def test_failed_route_audit_blocks_exact_global_min_semantics(self) -> None:
        import lunar_spprc_native
        from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
            _native_request_payload,
        )

        request = BackendPricingRequest(
            data=self.data,
            true_duals=JourneyDuals(
                cover={task_id: 10.0 for task_id in self.data.task_ids}
            ),
        )
        raw = dict(lunar_spprc_native.solve(_native_request_payload(request)))
        self.assertTrue(raw["routes"])
        raw["routes"] = [
            raw["routes"][0],
            {
                "reduced_cost": -999.0,
                "sorties": [{"tasks": [], "path_types": []}],
            },
        ]
        raw.update(
            {
                "status": "COMPLETE",
                "search_exhaustive": True,
                "frontier_empty": True,
                "labels_dropped": False,
            }
        )

        with patch("lunar_spprc_native.solve", return_value=raw):
            result = NativeRcsppInprocessBackend().solve(request)

        self.assertIsNotNone(result.best_found_rc)
        self.assertIsNone(result.global_min_rc)
        self.assertFalse(result.global_min_rc_is_exact)
        self.assertIn(
            "native_route_reconstruction_failed",
            result.certificate_blockers,
        )
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
        with patch.dict(
            os.environ,
            {"LUNAR_ICE_SPPRC_EXACT_BACKEND": "python_reference"},
        ):
            os.environ.pop("LUNAR_ICE_SPPRC_SHADOW_BACKEND", None)
            official_payload, official_columns = run_bpc_labeling_pricer(
                self.data, duals, config=config
            )
        with patch.dict(
            os.environ,
            {
                "LUNAR_ICE_SPPRC_EXACT_BACKEND": "python_reference",
                "LUNAR_ICE_SPPRC_SHADOW_BACKEND": "native_rcspp_inprocess",
            },
        ):
            shadow_payload, shadow_columns = run_bpc_labeling_pricer(
                self.data, duals, config=config
            )

        self.assertEqual(shadow_payload["pricing_state"], official_payload["pricing_state"])
        self.assertEqual(shadow_payload["can_certify_no_negative"], official_payload["can_certify_no_negative"])
        self.assertEqual(shadow_columns, official_columns)
        self.assertTrue(shadow_payload["native_shadow_enabled"])
        self.assertFalse(shadow_payload["native_shadow_mutates_official_result"])

    def test_default_native_backend_and_explicit_python_rollback_match(self) -> None:
        from lunar_ice_bpc.exact.bpc.pricing.labeling_pricer import (
            EXACT_ELEMENTARY_MODE,
            LabelingPricingConfig,
            run_bpc_labeling_pricer,
        )

        config = LabelingPricingConfig(mode=EXACT_ELEMENTARY_MODE, max_exact_tasks=5)
        duals = JourneyDuals(cover={})
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("LUNAR_ICE_SPPRC_EXACT_BACKEND", None)
            default_payload, default_columns = run_bpc_labeling_pricer(
                self.data, duals, config=config
            )
        with patch.dict(
            os.environ,
            {"LUNAR_ICE_SPPRC_EXACT_BACKEND": "python_reference"},
        ):
            rollback_payload, rollback_columns = run_bpc_labeling_pricer(
                self.data, duals, config=config
            )

        self.assertEqual(default_payload["native_backend_id"], "native_rcspp_inprocess")
        self.assertTrue(default_payload["can_certify_no_negative"])
        self.assertTrue(rollback_payload["can_certify_no_negative"])
        self.assertNotIn("native_backend_result", rollback_payload)
        self.assertEqual(default_payload["pricing_state"], rollback_payload["pricing_state"])
        default_negative = {
            frozenset(column.task_set)
            for column in default_columns
            if manual_journey_reduced_cost(column, duals) < -1.0e-6
        }
        rollback_negative = {
            frozenset(column.task_set)
            for column in rollback_columns
            if manual_journey_reduced_cost(column, duals) < -1.0e-6
        }
        self.assertEqual(default_negative, rollback_negative)
        self.assertFalse(default_negative)

    def test_unsupported_native_cut_falls_back_to_python_fail_closed_safe(self) -> None:
        from lunar_ice_bpc.exact.bpc.pricing.labeling_pricer import (
            EXACT_ELEMENTARY_MODE,
            LabelingPricingConfig,
            run_bpc_labeling_pricer,
        )

        # Fleet lower-bound cuts remain diagnostic-only in Live SRI V1, so
        # asking the Native V1 backend to price one must fail closed and use
        # the exact Python reference rollback path.
        cut_context = CutContext(
            cuts=(fleet_lower_bound_cut("fallback-fleet", min_vehicles=2),)
        )
        with patch.dict(
            os.environ,
            {
                "LUNAR_ICE_SPPRC_EXACT_BACKEND": "native_rcspp_inprocess",
            },
        ):
            payload, _ = run_bpc_labeling_pricer(
                self.data,
                JourneyDuals(cover={}),
                config=LabelingPricingConfig(
                    mode=EXACT_ELEMENTARY_MODE,
                    max_exact_tasks=5,
                ),
                cut_context=cut_context,
            )

        self.assertTrue(payload["native_backend_fallback_to_python"])
        self.assertEqual(payload["native_backend_fallback_status"], "UNSUPPORTED_FEATURE")
        self.assertIn(
            "unsupported_live_cut_type:fleet_lower_bound",
            payload["native_backend_fallback_blockers"],
        )
        # The diagnostic-only family is not allowed to manufacture a proof on
        # rollback; it stays explicitly incomplete/fail-closed.
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertEqual(payload["pricing_state"], "INCOMPLETE_LIMIT")

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

    def test_dssr_host_is_independent_and_certifies_relaxed_no_negative(self) -> None:
        NativeDssrHostBackend.close()
        try:
            result = NativeDssrHostBackend().solve(
                BackendPricingRequest(
                    data=self.data20,
                    true_duals=JourneyDuals(cover={}),
                    wall_time_limit_sec=10.0,
                    memory_limit_gb=1.0,
                    completion_bound_enabled=True,
                    subset_dominance_enabled=True,
                )
            )
        finally:
            NativeDssrHostBackend.close()

        self.assertEqual(result.backend_id, "native_rcspp_dssr_host")
        self.assertEqual(result.engine_status, "COMPLETE")
        self.assertTrue(result.can_enter_certificate_audit)
        self.assertEqual(result.proved_no_rc_below, -1.0e-6)
        self.assertTrue(result.telemetry["dssr_enabled"])
        self.assertEqual(
            result.telemetry["dssr_policy_version"],
            "multi_sortie_counterexample_refinement_v1",
        )
        self.assertTrue(
            result.telemetry[
                "dssr_relaxation_no_negative_certificate"
            ]
        )
        self.assertEqual(
            result.telemetry["completion_bound_evaluated_labels"], 0
        )
        self.assertEqual(
            result.telemetry["subset_dominance_candidate_checks"], 0
        )
        self.assertTrue(result.telemetry["request_bindings_match"])

    def test_dssr_exact_negative_returns_only_audited_elementary_column(self) -> None:
        for data in (self.data, self.data10, self.data20):
            with self.subTest(scale=data.scale):
                NativeDssrHostBackend.close()
                try:
                    result = NativeDssrHostBackend().solve(
                        BackendPricingRequest(
                            data=data,
                            true_duals=JourneyDuals(
                                cover={
                                    task_id: 10.0
                                    for task_id in data.task_ids
                                }
                            ),
                            wall_time_limit_sec=10.0,
                            memory_limit_gb=1.0,
                        )
                    )
                finally:
                    NativeDssrHostBackend.close()

                self.assertEqual(result.engine_status, "MAX_SOLUTIONS")
                self.assertFalse(result.search_exhaustive)
                self.assertTrue(result.partial_columns_valid)
                self.assertTrue(result.columns)
                self.assertLess(result.best_found_rc, -1.0e-6)
                self.assertTrue(
                    result.telemetry["dssr_elementary_witness_returned"]
                )
                for column in result.columns:
                    task_ids = [
                        task_id
                        for sortie in column.sorties
                        for task_id in sortie.tasks
                    ]
                    self.assertEqual(len(task_ids), len(set(task_ids)))
                self.assertIn(
                    "native_exact_search_incomplete",
                    result.certificate_blockers,
                )

    def test_old_native_backend_keeps_dssr_off(self) -> None:
        result = NativeRcsppInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=JourneyDuals(cover={}),
            )
        )
        self.assertFalse(result.telemetry["dssr_enabled"])
        self.assertFalse(
            result.telemetry[
                "dssr_relaxation_no_negative_certificate"
            ]
        )

    def test_dssr_backend_runs_on_small_scales(self) -> None:
        NativeDssrHostBackend.close()
        try:
            result = NativeDssrHostBackend().solve(
                BackendPricingRequest(
                    data=self.data,
                    true_duals=JourneyDuals(cover={}),
                    wall_time_limit_sec=10.0,
                    memory_limit_gb=1.0,
                )
            )
        finally:
            NativeDssrHostBackend.close()
        self.assertTrue(result.can_enter_certificate_audit)
        self.assertTrue(result.telemetry["dssr_enabled"])
        self.assertTrue(result.telemetry["dssr_exact_proof_eligible"])
        self.assertFalse(result.telemetry["dssr_non_exact_bypassed"])
        self.assertEqual(result.telemetry["dssr_bypass_reason"], "")
        self.assertTrue(
            result.telemetry["dssr_relaxation_no_negative_certificate"]
        )

    def test_dssr_inprocess_backend_runs_same_policy_without_host(self) -> None:
        result = NativeDssrInprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=JourneyDuals(cover={}),
                wall_time_limit_sec=10.0,
                memory_limit_gb=1.0,
            )
        )
        self.assertEqual(
            result.backend_id,
            "native_rcspp_dssr_inprocess",
        )
        self.assertTrue(result.can_enter_certificate_audit)
        self.assertTrue(result.telemetry["dssr_enabled"])
        self.assertTrue(result.telemetry["dssr_exact_proof_eligible"])
        self.assertTrue(
            result.telemetry["dssr_relaxation_no_negative_certificate"]
        )

    def test_dssr_v2_batch_and_policy_binding_are_independent(self) -> None:
        request = BackendPricingRequest(
            data=self.data,
            true_duals=JourneyDuals(
                cover={
                    task_id: 10.0
                    for task_id in self.data.task_ids
                }
            ),
            harvest_target=4,
            config_hash="source-config",
            engine_hash="dssr-v2-engine",
            dssr_pressure_max_bucket_size=16_384,
            dssr_pressure_max_candidate_checks=800_000_000,
        )
        result = NativeDssrV2InprocessBackend().solve(request)

        self.assertEqual(
            result.backend_id,
            "native_rcspp_dssr_v2_inprocess",
        )
        self.assertTrue(result.columns)
        self.assertLessEqual(len(result.columns), 4)
        self.assertTrue(result.partial_columns_valid)
        self.assertFalse(result.can_enter_certificate_audit)
        self.assertEqual(
            result.telemetry["dssr_policy_version"],
            "multi_sortie_counterexample_pressure_refinement_v2",
        )
        self.assertEqual(
            result.telemetry["dssr_elementary_batch_count"],
            len(result.columns),
        )
        self.assertGreaterEqual(
            result.telemetry["dssr_raw_solution_count"],
            len(result.columns),
        )
        bindings = result.telemetry["request_bindings"]
        self.assertNotEqual(bindings["config_hash"], "source-config")
        self.assertEqual(bindings["dssr_negative_batch_target"], 4)
        self.assertTrue(
            bindings["dssr_pressure_refinement_enabled"]
        )
        canonical = bindings["canonical_solve_binding_v2"]
        self.assertEqual(
            canonical["dssr_policy_version"],
            "multi_sortie_counterexample_pressure_refinement_v2",
        )
        self.assertEqual(
            canonical["dssr_pressure_max_bucket_size"],
            16_384,
        )
        self.assertTrue(result.telemetry["request_bindings_match"])

    def test_dssr_v2_pressure_abort_has_zero_certificate_leak(self) -> None:
        result = NativeDssrV2InprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=JourneyDuals(
                    cover={
                        task_id: 10.0
                        for task_id in self.data.task_ids
                    }
                ),
                harvest_target=4,
                dssr_pressure_max_bucket_size=1,
                dssr_pressure_max_candidate_checks=800_000_000,
            )
        )

        self.assertTrue(result.columns)
        self.assertTrue(result.partial_columns_valid)
        self.assertFalse(result.can_enter_certificate_audit)
        self.assertIsNone(result.proved_no_rc_below)
        self.assertGreater(
            result.telemetry["dssr_pressure_refinement_count"],
            0,
        )
        self.assertGreaterEqual(
            result.telemetry[
                "dssr_pressure_abandoned_iteration_count"
            ],
            result.telemetry["dssr_pressure_refinement_count"],
        )
        pressure_rows = [
            row
            for row in result.telemetry["dssr_iteration_trace"]
            if row["pressure_refinement_triggered"]
        ]
        self.assertTrue(pressure_rows)
        self.assertTrue(
            all(
                int(row["raw_solution_count"]) == 0
                and int(row["elementary_solution_count"]) == 0
                and int(row["non_elementary_solution_count"]) == 0
                for row in pressure_rows
            )
        )

    def test_dssr_v2_host_ipc_preserves_policy_and_exact_certificate(
        self,
    ) -> None:
        NativeDssrV2HostBackend.close()
        try:
            result = NativeDssrV2HostBackend().solve(
                BackendPricingRequest(
                    data=self.data,
                    true_duals=JourneyDuals(cover={}),
                    wall_time_limit_sec=10.0,
                    memory_limit_gb=1.0,
                    dssr_pressure_max_bucket_size=16_384,
                    dssr_pressure_max_candidate_checks=800_000_000,
                )
            )
        finally:
            NativeDssrV2HostBackend.close()

        self.assertEqual(
            result.backend_id,
            "native_rcspp_dssr_v2_host",
        )
        self.assertTrue(result.can_enter_certificate_audit)
        self.assertEqual(result.proved_no_rc_below, -1.0e-6)
        self.assertEqual(
            result.telemetry["dssr_policy_version"],
            "multi_sortie_counterexample_pressure_refinement_v2",
        )
        self.assertTrue(result.telemetry["request_bindings_match"])

    def test_dssr_v2_branch_and_cut_context_certifies_exactly(
        self,
    ) -> None:
        task_a, task_b, task_c = self.data.task_ids[:3]
        branch = BranchContext(
            pair_decisions=(
                PairBranchDecision(
                    task_a,
                    task_b,
                    SAME_JOURNEY,
                ),
            )
        )
        cut = subset_row_cut(
            "dssr-v2-sri",
            (task_a, task_b, task_c),
        )
        result = NativeDssrV2InprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=JourneyDuals(
                    cover={},
                    cuts={cut.cut_id: 0.0},
                ),
                branch_context=branch,
                cut_context=CutContext(cuts=(cut,)),
                dssr_pressure_max_bucket_size=16_384,
                dssr_pressure_max_candidate_checks=800_000_000,
            )
        )

        self.assertTrue(result.can_enter_certificate_audit)
        self.assertTrue(result.search_exhaustive)
        self.assertTrue(result.frontier_empty)
        self.assertFalse(result.labels_dropped)
        self.assertEqual(result.proved_no_rc_below, -1.0e-6)
        self.assertTrue(result.telemetry["cut_state_required"])
        self.assertTrue(result.telemetry["request_bindings_match"])

    def test_dssr_v2_timeout_and_memory_fail_closed(self) -> None:
        cases = (
            {
                "wall_time_limit_sec": 0.0,
                "memory_limit_gb": 1.0,
            },
            {
                "wall_time_limit_sec": 10.0,
                "memory_limit_gb": 0.000_001,
            },
        )
        for limits in cases:
            with self.subTest(limits=limits):
                result = NativeDssrV2InprocessBackend().solve(
                    BackendPricingRequest(
                        data=self.data20,
                        true_duals=JourneyDuals(cover={}),
                        dssr_pressure_max_bucket_size=16_384,
                        dssr_pressure_max_candidate_checks=(
                            800_000_000
                        ),
                        **limits,
                    )
                )

                self.assertIn(
                    result.engine_status,
                    {"TIMEOUT", "MEMORY_LIMIT"},
                )
                self.assertFalse(result.search_exhaustive)
                self.assertFalse(result.frontier_empty)
                self.assertFalse(result.can_enter_certificate_audit)
                self.assertIsNone(result.proved_no_rc_below)
                self.assertIn(
                    "native_exact_search_incomplete",
                    result.certificate_blockers,
                )

    def test_ng_dssr_v3_binding_and_elementary_batch(self) -> None:
        result = NativeNgDssrV3InprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=JourneyDuals(
                    cover={
                        task_id: 10.0
                        for task_id in self.data.task_ids
                    }
                ),
                harvest_target=4,
                config_hash="source-ng-config",
                engine_hash="ng-dssr-v3-engine",
                ng_dssr_initial_neighborhood_size=3,
                completion_bound_enabled=True,
                subset_dominance_enabled=True,
                proof_queue_policy_id="QD1",
            )
        )

        self.assertEqual(
            result.backend_id,
            "native_rcspp_ng_dssr_v3_inprocess",
        )
        self.assertTrue(result.columns)
        self.assertLessEqual(len(result.columns), 4)
        self.assertTrue(result.partial_columns_valid)
        self.assertFalse(result.can_enter_certificate_audit)
        self.assertTrue(result.telemetry["ng_dssr_enabled"])
        self.assertEqual(
            result.telemetry["dssr_policy_version"],
            "multi_sortie_ng_memory_counterexample_refinement_v3",
        )
        self.assertEqual(
            result.telemetry["ng_dssr_initial_neighborhood_size"],
            3,
        )
        self.assertGreaterEqual(
            result.telemetry["ng_dssr_final_relation_count"],
            result.telemetry["ng_dssr_initial_relation_count"],
        )
        self.assertEqual(
            result.telemetry["completion_bound_evaluated_labels"],
            0,
        )
        self.assertEqual(
            result.telemetry["subset_dominance_candidate_checks"],
            0,
        )
        self.assertEqual(
            result.telemetry["proof_queue_policy_id"],
            "Q0",
        )
        bindings = result.telemetry["request_bindings"]
        self.assertEqual(
            bindings["ng_dssr_initial_neighborhood_size"],
            3,
        )
        self.assertEqual(
            bindings["canonical_solve_binding_v2"][
                "ng_dssr_initial_neighborhood_size"
            ],
            3,
        )
        self.assertTrue(result.telemetry["request_bindings_match"])
        for column in result.columns:
            task_ids = [
                task_id
                for sortie in column.sorties
                for task_id in sortie.tasks
            ]
            self.assertEqual(len(task_ids), len(set(task_ids)))

    def test_ng_dssr_v3_host_ipc_and_zero_dual_certificate(self) -> None:
        NativeNgDssrV3HostBackend.close()
        try:
            result = NativeNgDssrV3HostBackend().solve(
                BackendPricingRequest(
                    data=self.data,
                    true_duals=JourneyDuals(cover={}),
                    wall_time_limit_sec=10.0,
                    memory_limit_gb=1.0,
                    ng_dssr_initial_neighborhood_size=3,
                )
            )
        finally:
            NativeNgDssrV3HostBackend.close()

        self.assertEqual(
            result.backend_id,
            "native_rcspp_ng_dssr_v3_host",
        )
        self.assertTrue(result.can_enter_certificate_audit)
        self.assertEqual(result.proved_no_rc_below, -1.0e-6)
        self.assertTrue(result.telemetry["ng_dssr_enabled"])
        self.assertTrue(
            result.telemetry[
                "dssr_relaxation_no_negative_certificate"
            ]
        )
        self.assertTrue(result.telemetry["request_bindings_match"])

    def test_ng_dssr_v3_branch_cut_and_resource_limits_fail_closed(
        self,
    ) -> None:
        task_a, task_b, task_c = self.data.task_ids[:3]
        branch = BranchContext(
            pair_decisions=(
                PairBranchDecision(
                    task_a,
                    task_b,
                    SAME_JOURNEY,
                ),
            )
        )
        cut = subset_row_cut(
            "ng-dssr-v3-sri",
            (task_a, task_b, task_c),
        )
        exact = NativeNgDssrV3InprocessBackend().solve(
            BackendPricingRequest(
                data=self.data,
                true_duals=JourneyDuals(
                    cover={},
                    cuts={cut.cut_id: 0.0},
                ),
                branch_context=branch,
                cut_context=CutContext(cuts=(cut,)),
                ng_dssr_initial_neighborhood_size=3,
            )
        )
        self.assertTrue(exact.can_enter_certificate_audit)
        self.assertTrue(exact.search_exhaustive)
        self.assertTrue(exact.frontier_empty)
        self.assertFalse(exact.labels_dropped)
        self.assertTrue(exact.telemetry["cut_state_required"])

        for limits in (
            {"wall_time_limit_sec": 0.0, "memory_limit_gb": 1.0},
            {"wall_time_limit_sec": 10.0, "memory_limit_gb": 0.000_001},
        ):
            with self.subTest(limits=limits):
                incomplete = NativeNgDssrV3InprocessBackend().solve(
                    BackendPricingRequest(
                        data=self.data20,
                        true_duals=JourneyDuals(cover={}),
                        ng_dssr_initial_neighborhood_size=6,
                        **limits,
                    )
                )
                self.assertIn(
                    incomplete.engine_status,
                    {"TIMEOUT", "MEMORY_LIMIT"},
                )
                self.assertFalse(incomplete.search_exhaustive)
                self.assertFalse(incomplete.frontier_empty)
                self.assertFalse(
                    incomplete.can_enter_certificate_audit
                )
                self.assertIsNone(incomplete.proved_no_rc_below)
                self.assertIn(
                    "native_exact_search_incomplete",
                    incomplete.certificate_blockers,
                )

    def test_pre_solve_exact_snapshot_survives_without_result(self) -> None:
        request = BackendPricingRequest(
            data=self.data,
            true_duals=JourneyDuals(
                cover={
                    task_id: 0.0
                    for task_id in self.data.task_ids
                }
            ),
            wall_time_limit_sec=10.0,
            memory_limit_gb=1.0,
            config_hash="pre-solve-snapshot-config",
            engine_hash="pre-solve-snapshot-engine",
        )
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {"LUNAR_ICE_PRE_SOLVE_EXACT_SNAPSHOT_DIR": directory},
            ):
                result = NativeDssrInprocessBackend().solve(request)

            snapshot_paths = sorted(Path(directory).glob("**/*.json"))
            self.assertEqual(len(snapshot_paths), 1)
            snapshot = load_pricing_snapshot(snapshot_paths[0])

        self.assertEqual(result.engine_status, "COMPLETE")
        self.assertEqual(
            snapshot.instance_content_hash,
            self.data.instance_content_hash,
        )
        self.assertEqual(
            snapshot.true_duals["cover"],
            dict(request.true_duals.cover),
        )
        self.assertEqual(
            snapshot.result_summary["status"],
            "NOT_OBSERVED",
        )
        self.assertFalse(snapshot.result_summary["search_exhaustive"])
        self.assertFalse(snapshot.censored)
        self.assertEqual(
            snapshot.binding.config_hash,
            request.config_hash,
        )

    def test_pre_solve_pricing_snapshot_includes_negative_harvest(
        self,
    ) -> None:
        request = BackendPricingRequest(
            data=self.data,
            true_duals=JourneyDuals(
                cover={
                    task_id: 0.0
                    for task_id in self.data.task_ids
                }
            ),
            mode=BACKEND_MODE_NEGATIVE_HARVEST,
            wall_time_limit_sec=10.0,
            memory_limit_gb=1.0,
            config_hash="pre-solve-pricing-snapshot-config",
            engine_hash="pre-solve-pricing-snapshot-engine",
        )
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "LUNAR_ICE_PRE_SOLVE_PRICING_SNAPSHOT_DIR": (
                        directory
                    )
                },
            ):
                NativeRcsppInprocessBackend().solve(request)

            snapshot_paths = sorted(Path(directory).glob("**/*.json"))
            self.assertEqual(len(snapshot_paths), 1)
            snapshot = load_pricing_snapshot(snapshot_paths[0])

        self.assertEqual(
            snapshot.pricing_mode,
            BACKEND_MODE_NEGATIVE_HARVEST,
        )
        self.assertEqual(
            snapshot.binding.config_hash,
            request.config_hash,
        )
        self.assertEqual(
            snapshot.binding.engine_hash,
            request.engine_hash,
        )
        self.assertFalse(
            snapshot.to_payload()["can_certify"],
        )

    def test_dssr_backend_integrates_with_official_labeling_pricer(self) -> None:
        NativeDssrHostBackend.close()
        try:
            with patch.dict(
                os.environ,
                {
                    "LUNAR_ICE_SPPRC_EXACT_BACKEND": (
                        "native_rcspp_dssr_host"
                    ),
                    "LUNAR_ICE_SPPRC_MEMORY_LIMIT_GB": "1",
                },
            ):
                payload, columns = run_bpc_labeling_pricer(
                    self.data20,
                    JourneyDuals(cover={}),
                    config=LabelingPricingConfig(
                        mode=EXACT_ELEMENTARY_MODE,
                        max_exact_tasks=20,
                        wall_time_limit_sec=10.0,
                    ),
                )
        finally:
            NativeDssrHostBackend.close()

        self.assertFalse(columns)
        self.assertEqual(
            payload["native_backend_id"],
            "native_rcspp_dssr_host",
        )
        self.assertEqual(
            payload["pricing_state"],
            "CERTIFIED_NO_NEGATIVE",
        )
        self.assertTrue(payload["can_certify_no_negative"])
        self.assertEqual(
            payload["exact_pricing_certificate_method"],
            "DSSR_RELAXATION_LOWER_BOUND",
        )
        self.assertEqual(
            payload["resource_label_core_mode"],
            "native_exact_dssr_counterexample_refinement",
        )

    def test_dssr_v2_integrates_with_official_labeling_pricer(
        self,
    ) -> None:
        with patch.dict(
            os.environ,
            {
                "LUNAR_ICE_SPPRC_EXACT_BACKEND": (
                    "native_rcspp_dssr_v2_inprocess"
                ),
                "LUNAR_ICE_SPPRC_MEMORY_LIMIT_GB": "1",
                "LUNAR_ICE_SPPRC_DSSR_NEGATIVE_BATCH_TARGET": "16",
                "LUNAR_ICE_SPPRC_DSSR_PRESSURE_MAX_BUCKET_SIZE": (
                    "16384"
                ),
                "LUNAR_ICE_SPPRC_DSSR_PRESSURE_MAX_CANDIDATE_CHECKS": (
                    "800000000"
                ),
            },
        ):
            payload, columns = run_bpc_labeling_pricer(
                self.data,
                JourneyDuals(cover={}),
                config=LabelingPricingConfig(
                    mode=EXACT_ELEMENTARY_MODE,
                    max_exact_tasks=5,
                    wall_time_limit_sec=10.0,
                ),
            )

        self.assertFalse(columns)
        self.assertEqual(
            payload["native_backend_id"],
            "native_rcspp_dssr_v2_inprocess",
        )
        self.assertEqual(
            payload["pricing_state"],
            "CERTIFIED_NO_NEGATIVE",
        )
        self.assertTrue(payload["can_certify_no_negative"])
        self.assertEqual(
            payload["exact_pricing_certificate_method"],
            "DSSR_RELAXATION_LOWER_BOUND",
        )
        self.assertEqual(
            payload["resource_label_core_mode"],
            "native_exact_dssr_batch_pressure_refinement_v2",
        )

    def test_ng_dssr_v3_integrates_with_official_labeling_pricer(
        self,
    ) -> None:
        with patch.dict(
            os.environ,
            {
                "LUNAR_ICE_SPPRC_EXACT_BACKEND": (
                    "native_rcspp_ng_dssr_v3_inprocess"
                ),
                "LUNAR_ICE_SPPRC_MEMORY_LIMIT_GB": "1",
                "LUNAR_ICE_SPPRC_DSSR_NEGATIVE_BATCH_TARGET": "16",
                "LUNAR_ICE_SPPRC_NG_DSSR_INITIAL_NEIGHBORHOOD_SIZE": (
                    "3"
                ),
            },
        ):
            payload, columns = run_bpc_labeling_pricer(
                self.data,
                JourneyDuals(cover={}),
                config=LabelingPricingConfig(
                    mode=EXACT_ELEMENTARY_MODE,
                    max_exact_tasks=5,
                    wall_time_limit_sec=10.0,
                ),
            )

        self.assertFalse(columns)
        self.assertEqual(
            payload["native_backend_id"],
            "native_rcspp_ng_dssr_v3_inprocess",
        )
        self.assertEqual(
            payload["pricing_state"],
            "CERTIFIED_NO_NEGATIVE",
        )
        self.assertTrue(payload["can_certify_no_negative"])
        self.assertEqual(
            payload["exact_pricing_certificate_method"],
            "DSSR_RELAXATION_LOWER_BOUND",
        )
        self.assertEqual(
            payload["resource_label_core_mode"],
            "native_exact_ng_dssr_local_memory_refinement_v3",
        )
        self.assertEqual(
            payload["elementarity_policy"],
            "ng_dssr_nearest_memory_local_cycle_refinement_v3",
        )

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

    def test_host_ipc_preserves_signed_zero_dual_binding(self) -> None:
        NativeRcsppHostBackend.close()
        duals = JourneyDuals(
            cover={task_id: 0.0 for task_id in self.data.task_ids},
            fleet_limit=-0.0,
            cuts={},
        )
        try:
            result = NativeRcsppHostBackend().solve(
                BackendPricingRequest(
                    data=self.data,
                    true_duals=duals,
                    dual_binding_hash=true_dual_binding_hash(
                        duals.cover,
                        fleet_limit=duals.fleet_limit,
                        cuts=duals.cuts,
                    ),
                    wall_time_limit_sec=10.0,
                    memory_limit_gb=1.0,
                )
            )
        finally:
            NativeRcsppHostBackend.close()

        self.assertEqual(result.engine_status, "COMPLETE")
        self.assertNotIn(
            "native_dual_binding_hash_mismatch",
            result.certificate_blockers,
        )
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

    def test_host_native_memory_limit_returns_without_watchdog_kill(self) -> None:
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
        self.assertGreater(
            limited.telemetry["host_memory_watchdog_limit_bytes"],
            limited.telemetry["native_memory_limit_bytes"],
        )
        self.assertNotIn("host_exitcode", limited.telemetry)
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
    def test_parent_aware_host_memory_budget_preserves_reserve(self) -> None:
        gib = 1024**3
        budget = native_rcspp_module._dynamic_host_memory_budget(
            configured_native_limit_bytes=11 * gib,
            host_rss_bytes=300 * 1024**2,
            available_memory_bytes=8 * gib,
        )

        self.assertTrue(budget["clamped"])
        self.assertFalse(budget["preflight_rejected"])
        self.assertLess(
            budget["native_limit_bytes"],
            11 * gib,
        )
        self.assertLessEqual(
            budget["watchdog_limit_bytes"],
            300 * 1024**2 + 6 * gib,
        )

    def test_parent_aware_host_memory_budget_rejects_no_headroom(
        self,
    ) -> None:
        gib = 1024**3
        budget = native_rcspp_module._dynamic_host_memory_budget(
            configured_native_limit_bytes=11 * gib,
            host_rss_bytes=500 * 1024**2,
            available_memory_bytes=2 * gib,
        )

        self.assertTrue(budget["clamped"])
        self.assertTrue(budget["preflight_rejected"])
        self.assertEqual(budget["native_limit_bytes"], 0)

    def test_parent_aware_host_memory_budget_keeps_small_limit(
        self,
    ) -> None:
        gib = 1024**3
        budget = native_rcspp_module._dynamic_host_memory_budget(
            configured_native_limit_bytes=1 * gib,
            host_rss_bytes=200 * 1024**2,
            available_memory_bytes=12 * gib,
        )

        self.assertFalse(budget["clamped"])
        self.assertFalse(budget["preflight_rejected"])
        self.assertEqual(budget["native_limit_bytes"], 1 * gib)

    def test_heavy_host_recycle_policy_is_large_scale_only(self) -> None:
        limit_bytes = 10 * 1024**3
        threshold = native_rcspp_module._host_recycle_threshold_bytes(limit_bytes)

        self.assertEqual(threshold, int(0.25 * limit_bytes))
        self.assertFalse(
            native_rcspp_module._should_recycle_host_after_response(
                task_count=30,
                peak_rss_bytes=threshold,
                native_memory_limit_bytes=limit_bytes,
            )
        )
        self.assertFalse(
            native_rcspp_module._should_recycle_host_after_response(
                task_count=50,
                peak_rss_bytes=threshold - 1,
                native_memory_limit_bytes=limit_bytes,
            )
        )
        self.assertTrue(
            native_rcspp_module._should_recycle_host_after_response(
                task_count=50,
                peak_rss_bytes=threshold,
                native_memory_limit_bytes=limit_bytes,
            )
        )

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
        from lunar_ice_bpc.runners.native_spprc_acceptance import (
            _acceptance_metrics,
            _adaptive_harvest_cap_for_scale,
            _adaptive_harvest_schedule_for_scale,
            _configure_one_deviation_environment,
            _engine_binding_audit,
            _final_judge_pass_policy_for_scale,
            _profile_gate_metrics,
            run_native_spprc_acceptance,
        )

        project_root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "deployment.json"
            manifest.write_text(
                (
                    '{"allowed_scales":[30,50],'
                    '"deployment_authorized":true}'
                ),
                encoding="utf-8",
            )
            environment = {
                "LUNAR_ICE_ONE_DEVIATION_MANIFEST": "stale"
            }
            _configure_one_deviation_environment(
                environment,
                config={
                    "one_deviation_gat_deployment_manifest": str(
                        manifest
                    )
                },
                root=project_root,
                scale=30,
            )
            self.assertEqual(
                environment["LUNAR_ICE_ONE_DEVIATION_MANIFEST"],
                str(manifest.resolve()),
            )
            _configure_one_deviation_environment(
                environment,
                config={
                    "one_deviation_gat_deployment_manifest": str(
                        manifest
                    )
                },
                root=project_root,
                scale=20,
            )
            self.assertNotIn(
                "LUNAR_ICE_ONE_DEVIATION_MANIFEST", environment
            )
            evaluation_manifest = Path(directory) / "evaluation.json"
            evaluation_manifest.write_text(
                (
                    '{"allowed_scales":[30,50],'
                    '"evaluation_authorized":true,'
                    '"deployment_authorized":false}'
                ),
                encoding="utf-8",
            )
            _configure_one_deviation_environment(
                environment,
                config={
                    "one_deviation_gat_deployment_manifest": str(
                        evaluation_manifest
                    ),
                    "one_deviation_gat_evaluation_mode": True,
                },
                root=project_root,
                scale=30,
            )
            self.assertEqual(
                environment[
                    "LUNAR_ICE_ONE_DEVIATION_EVALUATION_MODE"
                ],
                "1",
            )
            with self.assertRaisesRegex(
                ValueError, "manifest hash mismatch"
            ):
                _configure_one_deviation_environment(
                    environment,
                    config={
                        "one_deviation_gat_deployment_manifest": str(
                            manifest
                        ),
                        "one_deviation_gat_deployment_manifest_sha256": (
                            "wrong"
                        ),
                    },
                    root=project_root,
                    scale=30,
                )
            summary = run_native_spprc_acceptance(
                project_root=project_root,
                config={},
                scales=(5, 10, 20, 30, 50, 100),
                limit=1,
                output_dir=directory,
                dry_run=True,
                route_opportunity_collection_only_root_pool=True,
                route_opportunity_collection_root_pool_time_cap_sec=300.0,
            )

        by_scale = {row["scale"]: row for row in summary["rows"]}
        self.assertEqual(by_scale[5]["status"], "DRY_RUN")
        self.assertEqual(by_scale[5]["final_judge_pass_policy"], "harvest_then_proof")
        self.assertIsNone(by_scale[5]["adaptive_harvest_cap_sec"])
        self.assertIn("--labeling-worker-max-task-cap", by_scale[30]["command"])
        self.assertIn(
            "--route-opportunity-collection-only-root-pool",
            by_scale[30]["command"],
        )
        self.assertTrue(
            by_scale[30][
                "route_opportunity_collection_only_root_pool"
            ]
        )
        cap_index = by_scale[30]["command"].index(
            "--route-opportunity-collection-root-pool-time-cap-sec"
        )
        self.assertEqual(by_scale[30]["command"][cap_index + 1], "300.0")
        depth_index = by_scale[30]["command"].index("--tree-closure-max-branch-depth")
        self.assertEqual(by_scale[30]["command"][depth_index + 1], "12")
        self.assertEqual(
            by_scale[50]["status"],
            "DRY_RUN" if by_scale[50]["instance_count"] else "NO_INSTANCES_AVAILABLE",
        )
        configured = {
            "native_final_judge_pass_policy": "harvest_then_proof",
            "native_final_judge_pass_policy_by_scale": {
                "30": "branch_adaptive_sparse_harvest_v1"
            },
            "native_adaptive_harvest_cap_sec_by_scale": {"30": 2.0},
        }
        self.assertEqual(
            _final_judge_pass_policy_for_scale(configured, 20),
            "harvest_then_proof",
        )
        self.assertEqual(
            _final_judge_pass_policy_for_scale(configured, 30),
            "branch_adaptive_sparse_harvest_v1",
        )
        self.assertIsNone(_adaptive_harvest_cap_for_scale(configured, 20))
        self.assertEqual(_adaptive_harvest_cap_for_scale(configured, 30), 2.0)
        self.assertIsNone(
            _adaptive_harvest_schedule_for_scale(configured, 30)
        )
        self.assertEqual(
            _adaptive_harvest_schedule_for_scale(
                {
                    "native_adaptive_harvest_schedule": "disabled",
                    "native_adaptive_harvest_schedule_by_scale": {
                        "30": "2000:256,4000:128"
                    },
                },
                30,
            ),
            "4000:128,2000:256",
        )
        self.assertEqual(
            _adaptive_harvest_schedule_for_scale(
                {"native_adaptive_harvest_schedule": "off"},
                50,
            ),
            "disabled",
        )
        for invalid_schedule in ("", "4000", "x:128", "4000:0"):
            with self.subTest(invalid_schedule=invalid_schedule):
                with self.assertRaises(ValueError):
                    _adaptive_harvest_schedule_for_scale(
                        {
                            "native_adaptive_harvest_schedule": (
                                invalid_schedule
                            )
                        },
                        50,
                    )
        for invalid in (0, -1, float("nan"), float("inf"), "invalid"):
            with self.subTest(invalid_cap=invalid):
                with self.assertRaises(ValueError):
                    _adaptive_harvest_cap_for_scale(
                        {"native_adaptive_harvest_cap_sec_by_scale": {"30": invalid}},
                        30,
                    )
        binding = _engine_binding_audit(
            expected_hash="engine-a",
            end_hash="engine-a",
            b42_summary={
                "config": {
                    "native_runtime_binding": {"engine_build_hash": "engine-a"}
                }
            },
        )
        self.assertTrue(binding["valid"])

        profile = native_spprc_scale_profile(30)
        state = {
            "rows": [
                {
                    "algorithm_status": "BPC_OPTIMAL",
                    "bpc_tree_optimal": True,
                    "no_cheat_pass": True,
                    "cold_start_total_sec": float(100 + index),
                }
                for index in range(20)
            ]
        }
        profile_gate = _profile_gate_metrics(
            profile,
            b42_state=state,
            expected_count=20,
        )
        self.assertTrue(profile_gate["all_exact"])
        self.assertTrue(profile_gate["all_no_cheat"])
        self.assertTrue(profile_gate["all_under_profile_time_limit"])
        self.assertEqual(profile_gate["p50_cold_start_total_sec"], 109.5)
        acceptance = _acceptance_metrics(
            [
                {
                    "scale": 30,
                    "instance_count": 20,
                    "status": "EXACT_CLOSED",
                    "profile_gate": profile_gate,
                    "redlines_zero": True,
                    "engine_binding": {"valid": True},
                }
            ]
        )
        self.assertTrue(acceptance["scale30_full20_exact"])
        self.assertTrue(acceptance["scale30_all_under_1800"])
        self.assertTrue(acceptance["scale30_phase11_release_gate"])

    def test_acceptance_engine_binding_detects_mid_run_source_drift(self) -> None:
        from lunar_ice_bpc.runners.native_spprc_acceptance import (
            _engine_binding_audit,
        )

        binding = _engine_binding_audit(
            expected_hash="engine-at-start",
            end_hash="engine-after-edit",
            b42_summary={
                "config": {
                    "native_runtime_binding": {
                        "engine_build_hash": "engine-at-start"
                    }
                }
            },
        )

        self.assertFalse(binding["valid"])
        self.assertIn("engine_build_hash_changed_during_run", binding["issues"])

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
            with patch.object(
                module,
                "_run_process_tree",
                side_effect=timeout,
            ):
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

    def test_b4_2_timeout_kills_the_entire_process_group(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        spec = importlib.util.spec_from_file_location(
            "native_spprc_b42_process_group_test",
            project_root / "scripts/run_lunar_ice_b4_2_cold_exact.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            child_pid_path = Path(directory) / "child.pid"
            command = [
                sys.executable,
                "-c",
                (
                    "import pathlib,subprocess,sys,time;"
                    "p=subprocess.Popen([sys.executable,'-c','import time;"
                    "time.sleep(60)']);"
                    f"pathlib.Path({str(child_pid_path)!r}).write_text(str(p.pid));"
                    "time.sleep(60)"
                ),
            ]
            with self.assertRaises(subprocess.TimeoutExpired):
                module._run_process_tree(
                    command,
                    cwd=str(project_root),
                    env=dict(os.environ),
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=0.5,
                )
            child_pid = int(
                child_pid_path.read_text(encoding="utf-8")
            )
            for _ in range(20):
                if not Path(f"/proc/{child_pid}").exists():
                    break
                sleep(0.05)
            self.assertFalse(Path(f"/proc/{child_pid}").exists())

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
