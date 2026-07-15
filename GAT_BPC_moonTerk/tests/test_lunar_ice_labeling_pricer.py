from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.exact.bpc.master.reduced_cost import ReducedCostContext
from lunar_ice_bpc.exact.bpc.pricing.final_judge import (
    FinalJudgeResult,
    LABELING_FINAL_JUDGE_PASS_PROOF_ONLY,
    _labeling_final_judge_exact_harvest_target,
    _smaller_optional_time_limit,
    run_true_dual_root_final_judge,
)
from lunar_ice_bpc.exact.bpc.pricing.hidden_negative_audit import build_hidden_negative_audit
from lunar_ice_bpc.exact.bpc.pricing.labeling_pricer import (
    EXACT_ELEMENTARY_MODE,
    PROOF_KIND_EXHAUSTIVE_FOUND_NEGATIVE,
    PROOF_KIND_EXHAUSTIVE_INCOMPLETE,
    PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE,
    PROOF_KIND_RELAXED_WORKER_UNCERTIFIED,
    RELAXED_NG_ROUTE_MODE,
    STATUS_SEMANTICS_CONTRACT_VERSION,
    LabelingPricingConfig,
    _audit_columns_with_true_dual,
    _seed_source_lookup,
    _select_diverse_negative_rows,
    _sources_for_task_set,
    _status_semantics_contract,
    run_bpc_labeling_pricer,
)
from lunar_ice_bpc.exact.bpc.pricing.resource_label_core import (
    CORE_EXACT_ELEMENTARY_FULL_SPACE,
    ResourceLabelCoreConfig,
    _RESOURCE_EXTENSION_MAX_PATH_VARIANTS_PER_SEQUENCE,
    _RESOURCE_EXTENSION_PROXY_PROFILES,
    _add_resource_extension_label,
    _bounded_portfolio_seed_sets,
    _protected_extra_seed_task_sets,
    _resource_extension_path_type_assignments,
    _resource_extension_ng_seed_task_sets,
    _resource_extension_ng_seed_task_sets_with_stats,
    _seed_source_task_count_counts,
    run_resource_label_core,
)
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (
    SPPRC_ENGINE_SOURCE,
    SPPRC_EXACT_MODE,
    SPPRC_WORKER_MODE,
    build_spprc_request,
    run_spprc_pricer,
    spprc_request_hash,
)
from lunar_ice_bpc.exact.bpc.pricing.status import PricingState
from lunar_ice_bpc.exact.bpc.pricing.worker_seed_catalog import WorkerSeedCatalog
from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.solver.branch_tree_solver import solve_b3_branch_price_tree_baseline
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (
    B2B_R2_MODE,
    DIRECT_LABEL_WORKER,
    LARGE_TASK_DIRECT_WORKER_MAX_CANDIDATE_SETS_ENV,
    LARGE_TASK_DIRECT_WORKER_MAX_TASKS_ENV,
    LARGE_TASK_DIRECT_WORKER_TIME_CAP_SEC_ENV,
    LABELING_WORKER_MAX_TASK_CAP_ENV,
    LABELING_FINAL_JUDGE_PASS_POLICY_ADAPTIVE,
    LABELING_FINAL_JUDGE_PASS_POLICY_BRANCH_ADAPTIVE,
    LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC_ENV,
    RELAXED_LABELING_WORKER,
    _catalog_physical_seed_columns,
    _catalog_refinement_neighborhood_seed_task_sets,
    _catalog_refinement_seed_portfolio,
    _catalog_refinement_seed_task_sets,
    _hidden_negative_refinement_summary,
    _effective_labeling_final_judge_pass_policy,
    _adaptive_final_judge_harvest_cap_sec,
    _large_task_direct_worker_seed_task_sets,
    _negative_worker_seed_task_sets,
    _next_labeling_final_judge_pass_strategy,
    _refinement_seed_source_rows,
    _run_large_task_direct_worker,
    _worker_task_cap,
    _adaptive_labeling_final_judge_exact_harvest_target,
    _worker_generated_task_sets,
    solve_node_pricing_with_b2b_r3,
    solve_b2_pricing_tail_baseline,
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
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals, manual_journey_reduced_cost, solve_restricted_journey_rmp
import lunar_ice_bpc.exact.pricing.journey_pricing as journey_pricing_module
from lunar_ice_bpc.exact.pricing.journey_pricing import (
    price_direct_journey_columns,
    price_direct_journey_columns_incremental,
    price_exhaustive_direct_journey_columns,
    price_full_universe_incremental_journey_columns,
)
from lunar_ice_bpc.exact.solver.journey_driver import (
    DirectBaselineTimeLimitExceeded,
    enumerate_direct_journey_columns,
)
from lunar_ice_bpc.runners.b4_1_true_dual_proof_tail import run_b4_1_tree_closure_from_probe
from lunar_ice_bpc.runners.labeling_worker_diagnostic import run_labeling_worker_diagnostic


class LunarIceLabelingPricerTests(unittest.TestCase):
    def setUp(self) -> None:
        # This legacy suite audits the Python reference pricer's detailed payload
        # and monkey-patches its resource-label core.  Keep that implementation
        # explicit now that the production exact default is native; native-default,
        # rollback, and fallback contracts have dedicated backend tests.
        self._reference_backend_env = patch.dict(
            os.environ,
            {"LUNAR_ICE_SPPRC_EXACT_BACKEND": "python_reference"},
        )
        self._reference_backend_env.start()
        self.addCleanup(self._reference_backend_env.stop)

    def test_status_semantics_contract_rejects_worker_certificate_leak(self) -> None:
        contract = _status_semantics_contract(
            {
                "pricing_state": PricingState.LOCAL_NO_COLUMN_UNCERTIFIED.value,
                "pricing_proof_kind": PROOF_KIND_RELAXED_WORKER_UNCERTIFIED,
                "can_certify_no_negative": True,
                "uses_true_dual_bpc_certificate": True,
                "global_remaining_rc_lb_valid": True,
            },
            exact_mode=False,
        )

        self.assertFalse(contract["certificate_semantics_pass"])
        self.assertTrue(contract["worker_no_column_can_certify"])
        self.assertIn("worker_mode_cannot_certify_no_negative", contract["certificate_semantics_issues"])
        self.assertIn(
            "local_no_column_uncertified_cannot_certify",
            contract["certificate_semantics_issues"],
        )
        self.assertIn(
            "relaxed_worker_proof_kind_cannot_certify",
            contract["certificate_semantics_issues"],
        )

    def test_status_semantics_contract_rejects_stabilized_dual_certificate_leak(self) -> None:
        contract = _status_semantics_contract(
            {
                "pricing_state": PricingState.CERTIFIED_NO_NEGATIVE.value,
                "pricing_proof_kind": PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE,
                "can_certify_no_negative": True,
                "uses_true_dual_bpc_certificate": True,
                "global_remaining_rc_lb_valid": True,
                "dual_stabilization_used_for_official_certificate": True,
                "official_pricing_dual_source": "tail_dual_stabilized_worker_dual",
            },
            exact_mode=True,
        )

        self.assertFalse(contract["certificate_semantics_pass"])
        self.assertIn(
            "certifying_payload_cannot_use_stabilized_dual",
            contract["certificate_semantics_issues"],
        )
        self.assertIn(
            "certifying_payload_requires_current_true_rmp_dual",
            contract["certificate_semantics_issues"],
        )

    def test_spprc_worker_mode_is_candidate_search_only(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: -100.0 for task_id in data.task_ids}, fleet_limit=0.0)
        request = build_spprc_request(
            data,
            mode=SPPRC_WORKER_MODE,
            config_hash="test-config",
            max_label_task_count=5,
            max_candidate_sets=8,
            harvest_target=4,
            ng_neighborhood_sizes=(3, 5),
        )

        result = run_spprc_pricer(data, duals, request)
        payload = result.to_payload()

        self.assertEqual(result.mode, SPPRC_WORKER_MODE)
        self.assertEqual(result.engine_source, SPPRC_ENGINE_SOURCE)
        self.assertFalse(result.can_certify_no_negative)
        self.assertFalse(result.no_column_can_certify)
        self.assertFalse(payload["spprc_can_certify_no_negative"])
        self.assertFalse(payload["spprc_no_column_can_certify"])
        self.assertEqual(result.exact_sec, 0.0)
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_RELAXED_WORKER_UNCERTIFIED)
        self.assertEqual(payload["spprc_ng_size_final"], 5)

    def test_incremental_worker_negative_harvest_target_stops_without_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 100.0 for task_id in data.task_ids}, fleet_limit=0.0)

        payload, columns = price_direct_journey_columns_incremental(
            data,
            duals,
            max_direct_tasks=5,
            seed_task_sets=tuple((task_id,) for task_id in data.task_ids),
            max_candidate_sets=10,
            completion_bound_enabled=False,
            stop_at_first_negative=True,
            negative_harvest_target=2,
        )

        self.assertEqual(payload["negative_harvest_target"], 2)
        self.assertTrue(payload["negative_harvest_early_stop_enabled"])
        self.assertTrue(payload["negative_harvest_early_stop_triggered"])
        self.assertEqual(payload["negative_column_count"], 2)
        self.assertEqual(len(columns), 2)
        self.assertLess(payload["candidate_round_count"], 10)
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["uses_true_dual_bpc_certificate"])

    def test_labeling_final_judge_adaptive_harvest_schedule_env_is_used(self) -> None:
        with patch.dict(
            os.environ,
            {"LUNAR_ICE_LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE": "4000:128,2000:256"},
            clear=False,
        ):
            self.assertEqual(
                _adaptive_labeling_final_judge_exact_harvest_target(
                    1024,
                    active_task_set_count=1999,
                ),
                1024,
            )
            self.assertEqual(
                _adaptive_labeling_final_judge_exact_harvest_target(
                    1024,
                    active_task_set_count=2000,
                ),
                256,
            )
            self.assertEqual(
                _adaptive_labeling_final_judge_exact_harvest_target(
                    1024,
                    active_task_set_count=4000,
                ),
                128,
            )
        with patch.dict(
            os.environ,
            {"LUNAR_ICE_LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_SCHEDULE": "disabled"},
            clear=False,
        ):
            self.assertEqual(
                _adaptive_labeling_final_judge_exact_harvest_target(
                    1024,
                    active_task_set_count=100000,
                ),
                1024,
            )
        self.assertEqual(
            _labeling_final_judge_exact_harvest_target(exact_harvest_target_override=2048),
            2048,
        )
        self.assertEqual(
            _labeling_final_judge_exact_harvest_target(exact_harvest_target_override=10000),
            4096,
        )

    def test_spprc_exact_mode_can_certify_small_full_space(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        self.assertEqual(rmp.status, "RESTRICTED_RMP_OPTIMAL")
        request = build_spprc_request(
            data,
            mode=SPPRC_EXACT_MODE,
            config_hash="test-config",
            max_exact_tasks=5,
            harvest_target=8,
            exact_negative_harvest_target=4,
        )

        result = run_spprc_pricer(data, rmp.duals, request)
        payload = result.to_payload()

        self.assertEqual(result.mode, SPPRC_EXACT_MODE)
        self.assertTrue(result.can_certify_no_negative)
        self.assertTrue(result.uses_true_dual_bpc_certificate)
        self.assertTrue(result.exact_coverage_complete)
        self.assertFalse(result.no_column_can_certify)
        self.assertEqual(payload["pricing_state"], PricingState.CERTIFIED_NO_NEGATIVE.value)
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE)
        self.assertEqual(payload["spprc_pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE)
        self.assertGreaterEqual(result.exact_sec, 0.0)

    def test_journey_rmp_highs_fast_path_matches_simplex_invariants(self) -> None:
        try:
            import highspy  # type: ignore[import-not-found]  # noqa: F401
        except Exception:
            self.skipTest("highspy is not installed")

        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)

        with patch.dict(os.environ, {"LUNAR_ICE_RMP_SOLVER": "simplex"}, clear=False):
            simplex_rmp = solve_restricted_journey_rmp(
                data.task_ids,
                universe.columns,
                fleet_size=data.fleet_size,
            )
        with patch.dict(
            os.environ,
            {"LUNAR_ICE_RMP_SOLVER": "highs", "LUNAR_ICE_RMP_HIGHS_THREADS": "1"},
            clear=False,
        ):
            highs_rmp = solve_restricted_journey_rmp(
                data.task_ids,
                universe.columns,
                fleet_size=data.fleet_size,
            )

        self.assertEqual(simplex_rmp.status, "RESTRICTED_RMP_OPTIMAL")
        self.assertEqual(highs_rmp.status, "RESTRICTED_RMP_OPTIMAL")
        self.assertAlmostEqual(simplex_rmp.objective_bound, highs_rmp.objective_bound, places=6)
        self.assertEqual(simplex_rmp.active_column_count, highs_rmp.active_column_count)
        self.assertLessEqual(highs_rmp.primal_cover_residual_max or 0.0, 1.0e-6)
        self.assertLessEqual(highs_rmp.primal_fleet_usage or 0.0, float(data.fleet_size) + 1.0e-6)
        highs_min_rc = min(manual_journey_reduced_cost(column, highs_rmp.duals) for column in universe.columns)
        self.assertGreaterEqual(highs_min_rc, -1.0e-6)

    def test_spprc_request_hash_includes_branch_and_cut_identity(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_a, task_b = data.task_ids[:2]
        base = build_spprc_request(
            data,
            mode=SPPRC_WORKER_MODE,
            config_hash="test-config",
            max_label_task_count=5,
            ng_neighborhood_sizes=(3, 5),
        )
        branched = build_spprc_request(
            data,
            mode=SPPRC_WORKER_MODE,
            config_hash="test-config",
            branch_context=BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),)),
            max_label_task_count=5,
            ng_neighborhood_sizes=(3, 5),
        )
        different_ng = build_spprc_request(
            data,
            mode=SPPRC_WORKER_MODE,
            config_hash="test-config",
            max_label_task_count=5,
            ng_neighborhood_sizes=(2, 5),
        )

        self.assertNotEqual(spprc_request_hash(base), spprc_request_hash(branched))
        self.assertNotEqual(spprc_request_hash(base), spprc_request_hash(different_ng))

    def test_true_dual_audit_filters_branch_infeasible_negative_candidates(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        columns = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
        task_a, task_b = data.task_ids[:2]
        one_only = next(
            column
            for column in columns
            if str(task_a) in set(column.task_set) and str(task_b) not in set(column.task_set)
        )
        context = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))
        self.assertFalse(journey_satisfies_branch_context(one_only, context))
        duals = JourneyDuals(
            cover={task_id: 0.0 for task_id in data.task_ids},
            fleet_limit=0.0,
        )
        duals.cover[str(task_a)] = float(one_only.objective) + 100.0

        audit = _audit_columns_with_true_dual(
            (one_only,),
            duals,
            branch_context=context,
            cut_context=CutContext(),
            task_set_sources={},
            negative_eps=1.0e-6,
            harvest_target=5,
        )

        self.assertFalse(audit["branch_context_audit_pass"])
        self.assertEqual(audit["branch_invalid_column_count"], 1)
        self.assertLess(audit["true_best_reduced_cost"], 0.0)
        self.assertEqual(audit["true_negative_column_count"], 0)
        self.assertEqual(audit["true_selected_negative_count"], 0)
        self.assertFalse(audit["audit_sample_rows"][0]["is_allowed_by_branch"])

    def test_negative_harvest_prefers_distinct_task_sets_before_replacements(self) -> None:
        rows = [
            {"task_set": ("a", "b"), "signature": "ab-1", "true_reduced_cost": -10.0},
            {"task_set": ("a", "b"), "signature": "ab-2", "true_reduced_cost": -9.0},
            {"task_set": ("c",), "signature": "c-1", "true_reduced_cost": -8.0},
            {"task_set": ("d",), "signature": "d-1", "true_reduced_cost": -7.0},
        ]

        selected = _select_diverse_negative_rows(rows, harvest_target=3)

        self.assertEqual([row["signature"] for row in selected], ["ab-1", "c-1", "d-1"])

        selected = _select_diverse_negative_rows(rows, harvest_target=4)

        self.assertEqual([row["signature"] for row in selected], ["ab-1", "c-1", "d-1", "ab-2"])

    def test_negative_harvest_prefers_rmp_new_task_sets_before_replacements(self) -> None:
        rows = [
            {"task_set": ("a", "b"), "signature": "ab-1", "true_reduced_cost": -10.0},
            {"task_set": ("a", "b"), "signature": "ab-2", "true_reduced_cost": -9.0},
            {"task_set": ("c",), "signature": "c-1", "true_reduced_cost": -8.0},
            {"task_set": ("d",), "signature": "d-1", "true_reduced_cost": -7.0},
        ]

        selected = _select_diverse_negative_rows(
            rows,
            harvest_target=2,
            existing_task_sets={("a", "b")},
        )

        self.assertEqual([row["signature"] for row in selected], ["c-1", "d-1"])

        selected = _select_diverse_negative_rows(
            rows,
            harvest_target=3,
            existing_task_sets={("a", "b")},
        )

        self.assertEqual([row["signature"] for row in selected], ["c-1", "d-1", "ab-1"])

    def test_negative_harvest_prefers_low_overlap_after_best_true_rc(self) -> None:
        rows = [
            {"task_set": ("a", "b", "c"), "signature": "abc", "true_reduced_cost": -10.0},
            {"task_set": ("a", "b", "d"), "signature": "abd", "true_reduced_cost": -9.0},
            {"task_set": ("e",), "signature": "e", "true_reduced_cost": -8.0},
            {"task_set": ("f",), "signature": "f", "true_reduced_cost": -7.0},
        ]

        selected = _select_diverse_negative_rows(rows, harvest_target=3)

        self.assertEqual([row["signature"] for row in selected], ["abc", "e", "f"])

    def test_true_dual_audit_selected_rows_match_diverse_selection_not_sample_prefix(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        columns = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
        first_singleton = next(column for column in columns if len(column.task_set) == 1)
        second_singleton = next(
            column
            for column in columns
            if len(column.task_set) == 1 and column.task_set != first_singleton.task_set
        )
        duplicate_task_set_column = replace(
            first_singleton,
            objective=round(float(first_singleton.objective) + 0.1, 6),
        )
        less_negative_distinct_column = replace(
            second_singleton,
            objective=round(float(first_singleton.objective) + 0.2, 6),
        )
        duals = JourneyDuals(
            cover={task_id: 100.0 for task_id in data.task_ids},
            fleet_limit=0.0,
        )

        audit = _audit_columns_with_true_dual(
            (first_singleton, duplicate_task_set_column, less_negative_distinct_column),
            duals,
            branch_context=BranchContext(),
            cut_context=CutContext(),
            task_set_sources={},
            negative_eps=1.0e-6,
            harvest_target=2,
        )

        selected_task_sets = [tuple(row["task_set"]) for row in audit["selected_negative_rows"]]
        sample_prefix_task_sets = [tuple(row["task_set"]) for row in audit["audit_sample_rows"][:2]]
        self.assertEqual(len(selected_task_sets), 2)
        self.assertEqual(len(set(selected_task_sets)), 2)
        self.assertNotEqual(selected_task_sets, sample_prefix_task_sets)
        self.assertEqual(audit["harvest_selected_replacement_task_set_count"], 0)
        self.assertEqual(
            audit["harvest_selection_policy"],
            "support_aware_new_then_support_changing_then_strong_replacement_then_capped_weak_replacement",
        )
        self.assertIsNotNone(audit["harvest_avg_pairwise_jaccard"])
        self.assertIsNotNone(audit["harvest_max_pairwise_jaccard"])

    def test_negative_harvest_prefers_support_changing_before_weak_replacements(self) -> None:
        rows = [
            {
                "task_set": ("a", "b"),
                "signature": "ab-weak",
                "true_reduced_cost": -1.0e-5,
                "task_set_harvest_bucket": "weak_replacement",
            },
            {
                "task_set": ("c", "d"),
                "signature": "cd-support",
                "true_reduced_cost": -2.0e-5,
                "task_set_harvest_bucket": "support_changing",
            },
            {
                "task_set": ("e",),
                "signature": "e-new",
                "true_reduced_cost": -3.0e-5,
                "task_set_harvest_bucket": "new_task_set",
            },
        ]

        selected = _select_diverse_negative_rows(
            rows,
            harvest_target=2,
            existing_task_sets={("a", "b"), ("c", "d")},
            support_task_sets={("a", "b")},
        )

        self.assertEqual([row["signature"] for row in selected], ["e-new", "cd-support"])

    def test_true_dual_audit_marks_new_vs_replacement_against_existing_master_task_sets(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        singleton_columns = [
            column
            for column in enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
            if len(column.task_set) == 1
        ]
        existing_column = singleton_columns[0]
        new_column = next(
            column for column in singleton_columns if column.task_set != existing_column.task_set
        )
        duals = JourneyDuals(
            cover={task_id: 100.0 for task_id in data.task_ids},
            fleet_limit=0.0,
        )

        audit = _audit_columns_with_true_dual(
            (existing_column, new_column),
            duals,
            branch_context=BranchContext(),
            cut_context=CutContext(),
            task_set_sources={},
            existing_task_sets=(tuple(sorted(str(task_id) for task_id in existing_column.task_set)),),
            negative_eps=1.0e-6,
            harvest_target=2,
        )

        self.assertEqual(audit["harvest_existing_master_task_set_count"], 1)
        self.assertEqual(audit["harvest_candidate_new_task_set_count"], 1)
        self.assertEqual(audit["harvest_candidate_replacement_task_set_count"], 1)
        self.assertEqual(audit["harvest_selected_new_task_set_count"], 1)
        self.assertEqual(audit["harvest_selected_replacement_task_set_count"], 1)
        self.assertEqual(audit["selected_negative_rows"][0]["task_set_relation_to_existing"], "new_task_set")
        self.assertEqual(audit["selected_negative_rows"][1]["task_set_relation_to_existing"], "replacement")

    def test_true_dual_audit_marks_support_changing_and_strong_replacements(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        singleton_columns = [
            column
            for column in enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
            if len(column.task_set) == 1
        ]
        support_column = singleton_columns[0]
        off_support_column = next(
            column for column in singleton_columns if column.task_set != support_column.task_set
        )
        existing_sets = (
            tuple(sorted(str(task_id) for task_id in support_column.task_set)),
            tuple(sorted(str(task_id) for task_id in off_support_column.task_set)),
        )
        support_sets = (tuple(sorted(str(task_id) for task_id in support_column.task_set)),)
        duals = JourneyDuals(
            cover={task_id: 100.0 for task_id in data.task_ids},
            fleet_limit=0.0,
        )

        audit = _audit_columns_with_true_dual(
            (support_column, off_support_column),
            duals,
            branch_context=BranchContext(),
            cut_context=CutContext(),
            task_set_sources={},
            existing_task_sets=existing_sets,
            support_task_sets=support_sets,
            negative_eps=1.0e-6,
            harvest_target=2,
        )

        self.assertEqual(audit["harvest_support_task_set_count"], 1)
        self.assertEqual(audit["harvest_candidate_support_changing_count"], 1)
        self.assertEqual(audit["harvest_candidate_strong_replacement_count"], 1)
        self.assertEqual(audit["harvest_selected_support_changing_count"], 1)
        self.assertEqual(audit["harvest_selected_strong_replacement_count"], 1)
        self.assertEqual(audit["selected_negative_rows"][0]["task_set_harvest_bucket"], "support_changing")
        self.assertEqual(audit["selected_negative_rows"][1]["task_set_harvest_bucket"], "strong_replacement")

    def test_true_dual_audit_reports_worker_dual_false_positive_and_miss_rows(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        singleton_columns = [
            column
            for column in enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
            if len(column.task_set) == 1
        ]
        true_negative_column = singleton_columns[0]
        search_false_positive_column = singleton_columns[1]
        true_negative_task = next(iter(true_negative_column.task_set))
        false_positive_task = next(iter(search_false_positive_column.task_set))
        true_duals = JourneyDuals(
            cover={task_id: 0.0 for task_id in data.task_ids},
            fleet_limit=0.0,
        )
        true_duals.cover[str(true_negative_task)] = float(true_negative_column.objective) + 10.0
        search_duals = JourneyDuals(
            cover={task_id: 0.0 for task_id in data.task_ids},
            fleet_limit=0.0,
        )
        search_duals.cover[str(false_positive_task)] = (
            float(search_false_positive_column.objective) + 10.0
        )

        audit = _audit_columns_with_true_dual(
            (true_negative_column, search_false_positive_column),
            true_duals,
            branch_context=BranchContext(),
            cut_context=CutContext(),
            task_set_sources={},
            candidate_search_duals=search_duals,
            negative_eps=1.0e-6,
            harvest_target=4,
        )

        self.assertEqual(audit["candidate_search_negative_column_count"], 1)
        self.assertEqual(audit["candidate_search_negative_true_negative_count"], 0)
        self.assertEqual(audit["candidate_search_negative_true_nonnegative_count"], 1)
        self.assertEqual(audit["true_negative_candidate_search_nonnegative_count"], 1)
        self.assertEqual(audit["candidate_search_false_positive_rate"], 1.0)
        self.assertEqual(audit["true_negative_candidate_search_miss_rate"], 1.0)
        self.assertEqual(
            audit["candidate_search_false_positive_rows"][0]["task_set"],
            sorted(str(task_id) for task_id in search_false_positive_column.task_set),
        )
        self.assertEqual(
            audit["true_negative_candidate_search_miss_rows"][0]["task_set"],
            sorted(str(task_id) for task_id in true_negative_column.task_set),
        )
        selected_task_sets = [tuple(row["task_set"]) for row in audit["selected_negative_rows"]]
        self.assertEqual(
            selected_task_sets,
            [tuple(sorted(str(task_id) for task_id in true_negative_column.task_set))],
        )
        self.assertTrue(all(row["is_true_negative"] for row in audit["selected_negative_rows"]))

    def test_hidden_negative_audit_requires_seen_task_set_for_prune_reason(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        column = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns[0]
        task_set = tuple(sorted(column.task_set))

        not_seen = build_hidden_negative_audit(
            worker_payload={
                "pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
                "worker_kind": "relaxed_labeling",
                "task_bound_pruned_count": 7,
                "worker_seen_task_sets": [],
            },
            final_judge_payload={"pricing_state": "FOUND_NEGATIVE"},
            negative_candidates=((-1.0, column),),
        )
        seen = build_hidden_negative_audit(
            worker_payload={
                "pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
                "worker_kind": "relaxed_labeling",
                "task_bound_pruned_count": 7,
                "worker_seen_task_sets": (task_set,),
            },
            final_judge_payload={"pricing_state": "FOUND_NEGATIVE"},
            negative_candidates=((-1.0, column),),
        )

        self.assertEqual(not_seen["rows"][0]["miss_reason"], "worker_not_generated")
        self.assertEqual(not_seen["rows"][0]["replacement_or_new_task_set"], "new_task_set")
        self.assertEqual(seen["rows"][0]["miss_reason"], "pruned_by_task_bound")
        self.assertEqual(seen["rows"][0]["replacement_or_new_task_set"], "replacement")

    def test_hidden_negative_audit_does_not_treat_new_seed_telemetry_as_seen_column(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        column = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns[0]
        task_set = tuple(sorted(column.task_set))

        new_payload = {
            "pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
            "worker_kind": "relaxed_labeling",
            "task_bound_pruned_count": 7,
            "worker_seen_task_sets": [],
            "generated_task_sets": (task_set,),
            "active_seed_task_sets": (task_set,),
            "worker_candidate_universe_task_sets": (task_set,),
        }
        legacy_payload = {
            "pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
            "worker_kind": "relaxed_labeling",
            "task_bound_pruned_count": 7,
            "generated_task_sets": (task_set,),
        }

        new_audit = build_hidden_negative_audit(
            worker_payload=new_payload,
            final_judge_payload={"pricing_state": "FOUND_NEGATIVE"},
            negative_candidates=((-1.0, column),),
        )
        legacy_audit = build_hidden_negative_audit(
            worker_payload=legacy_payload,
            final_judge_payload={"pricing_state": "FOUND_NEGATIVE"},
            negative_candidates=((-1.0, column),),
        )

        self.assertEqual(new_audit["rows"][0]["miss_reason"], "worker_not_generated")
        self.assertEqual(new_audit["rows"][0]["replacement_or_new_task_set"], "new_task_set")
        self.assertEqual(legacy_audit["rows"][0]["miss_reason"], "pruned_by_task_bound")
        self.assertEqual(legacy_audit["rows"][0]["replacement_or_new_task_set"], "replacement")

    def test_hidden_negative_audit_records_priced_candidate_source_match(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        columns = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
        singleton = next(column for column in columns if len(column.task_set) == 1)
        task_set = tuple(sorted(str(task_id) for task_id in singleton.task_set))
        other_task = next(task_id for task_id in data.task_ids if str(task_id) not in set(task_set))
        superset_task_set = tuple(sorted((*task_set, str(other_task))))

        exact = build_hidden_negative_audit(
            worker_payload={
                "pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
                "worker_kind": "relaxed_labeling",
                "priced_candidate_task_set_sources": [
                    {"task_set": list(task_set), "sources": ["resource_extension"]},
                ],
            },
            final_judge_payload={"pricing_state": "FOUND_NEGATIVE"},
            negative_candidates=((-1.0, singleton),),
        )
        superset = build_hidden_negative_audit(
            worker_payload={
                "pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
                "worker_kind": "relaxed_labeling",
                "priced_candidate_task_set_sources": [
                    {"task_set": list(superset_task_set), "sources": ["ng_route", "direct_candidate"]},
                ],
            },
            final_judge_payload={"pricing_state": "FOUND_NEGATIVE"},
            negative_candidates=((-1.0, singleton),),
        )
        none = build_hidden_negative_audit(
            worker_payload={
                "pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
                "worker_kind": "relaxed_labeling",
                "priced_candidate_task_set_sources": [
                    {"task_set": [str(other_task)], "sources": ["input_seed"]},
                ],
            },
            final_judge_payload={"pricing_state": "FOUND_NEGATIVE"},
            negative_candidates=((-1.0, singleton),),
        )
        priced_rows_take_precedence = build_hidden_negative_audit(
            worker_payload={
                "pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
                "worker_kind": "relaxed_labeling",
                "priced_candidate_task_set_sources": [
                    {"task_set": [str(other_task)], "sources": ["direct_candidate"]},
                ],
                "active_seed_task_set_sources": [
                    {"task_set": list(task_set), "sources": ["resource_extension"]},
                ],
            },
            final_judge_payload={"pricing_state": "FOUND_NEGATIVE"},
            negative_candidates=((-1.0, singleton),),
        )
        active_seed_fallback = build_hidden_negative_audit(
            worker_payload={
                "pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
                "worker_kind": "relaxed_labeling",
                "active_seed_task_set_sources": [
                    {"task_set": list(task_set), "sources": ["resource_extension"]},
                ],
            },
            final_judge_payload={"pricing_state": "FOUND_NEGATIVE"},
            negative_candidates=((-1.0, singleton),),
        )

        exact_row = exact["rows"][0]
        self.assertTrue(exact_row["worker_priced_candidate_seen_same_task_set"])
        self.assertFalse(exact_row["worker_priced_candidate_seen_superset_task_set"])
        self.assertEqual(exact_row["worker_priced_candidate_source_match"], "exact")
        self.assertEqual(exact_row["worker_priced_candidate_seed_sources"], ["resource_extension"])
        self.assertEqual(exact["hidden_negative_priced_candidate_exact_count"], 1)
        self.assertEqual(exact["hidden_negative_priced_candidate_source_counts"], {"resource_extension": 1})
        self.assertEqual(exact["hidden_negative_refinement_uncovered_count"], 1)
        self.assertEqual(exact_row["miss_reason"], "worker_not_generated")

        superset_row = superset["rows"][0]
        self.assertFalse(superset_row["worker_priced_candidate_seen_same_task_set"])
        self.assertTrue(superset_row["worker_priced_candidate_seen_superset_task_set"])
        self.assertEqual(superset_row["worker_priced_candidate_source_match"], "superset")
        self.assertEqual(
            superset_row["worker_priced_candidate_seed_sources"],
            ["direct_candidate", "ng_route"],
        )
        self.assertEqual(superset["hidden_negative_priced_candidate_superset_count"], 1)
        self.assertEqual(superset["hidden_negative_refinement_uncovered_count"], 1)

        none_row = none["rows"][0]
        self.assertFalse(none_row["worker_priced_candidate_seen_same_task_set"])
        self.assertFalse(none_row["worker_priced_candidate_seen_superset_task_set"])
        self.assertEqual(none_row["worker_priced_candidate_source_match"], "none")
        self.assertEqual(none["hidden_negative_priced_candidate_unseen_count"], 1)
        self.assertEqual(none_row["miss_reason"], "worker_not_generated")

        self.assertEqual(
            priced_rows_take_precedence["rows"][0]["worker_priced_candidate_source_match"],
            "none",
        )
        self.assertEqual(
            active_seed_fallback["rows"][0]["worker_priced_candidate_source_match"],
            "exact",
        )

    def test_hidden_negative_audit_reports_refinement_coverage(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        columns = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
        singleton = next(column for column in columns if len(column.task_set) == 1)
        task_set = tuple(sorted(str(task_id) for task_id in singleton.task_set))
        other_task = next(task_id for task_id in data.task_ids if str(task_id) not in set(task_set))
        superset_task_set = tuple(sorted((*task_set, str(other_task))))

        exact = build_hidden_negative_audit(
            worker_payload={
                "pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
                "worker_kind": "relaxed_labeling",
                "priced_candidate_task_set_sources": [
                    {"task_set": list(task_set), "sources": ["hidden_negative_refinement"]},
                ],
            },
            final_judge_payload={"pricing_state": "FOUND_NEGATIVE"},
            negative_candidates=((-1.0, singleton),),
        )
        superset = build_hidden_negative_audit(
            worker_payload={
                "pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
                "worker_kind": "relaxed_labeling",
                "priced_candidate_task_set_sources": [
                    {
                        "task_set": list(superset_task_set),
                        "sources": ["hidden_negative_refinement_expansion"],
                    },
                ],
            },
            final_judge_payload={"pricing_state": "FOUND_NEGATIVE"},
            negative_candidates=((-1.0, singleton),),
        )

        self.assertTrue(exact["rows"][0]["worker_priced_candidate_refinement_source"])
        self.assertEqual(exact["rows"][0]["worker_priced_candidate_refinement_coverage"], "exact")
        self.assertEqual(exact["hidden_negative_refinement_exact_count"], 1)
        self.assertEqual(exact["hidden_negative_refinement_covered_count"], 1)
        self.assertEqual(exact["hidden_negative_refinement_coverage_counts"], {"exact": 1})

        self.assertTrue(superset["rows"][0]["worker_priced_candidate_refinement_source"])
        self.assertEqual(superset["rows"][0]["worker_priced_candidate_refinement_coverage"], "superset")
        self.assertEqual(superset["hidden_negative_refinement_superset_count"], 1)
        self.assertEqual(superset["hidden_negative_refinement_covered_count"], 1)
        self.assertEqual(superset["hidden_negative_refinement_coverage_counts"], {"superset": 1})

    def test_hidden_negative_catalog_seed_has_worker_budget_priority(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        catalog = WorkerSeedCatalog()
        catalog_task_set = tuple(sorted(data.task_ids[-2:]))
        catalog.rows.append(
            {
                "task_set": catalog_task_set,
                "path_signature": tuple(),
                "source": "hidden_negative_audit",
                "true_reduced_cost": -1.0,
            }
        )
        zero_duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)

        refinement = _catalog_refinement_seed_task_sets(
            data,
            seed_catalog=catalog,
            max_direct_tasks=3,
        )
        expanded = _catalog_refinement_neighborhood_seed_task_sets(
            data,
            duals=zero_duals,
            seed_catalog=catalog,
            max_direct_tasks=3,
            expansion_width=2,
        )
        seeds = _negative_worker_seed_task_sets(
            data,
            duals=zero_duals,
            master_columns=tuple(),
            b0_direct=object(),
            seed_catalog=catalog,
            max_direct_tasks=3,
            max_seed_sets=1,
        )

        self.assertEqual(refinement, (catalog_task_set,))
        self.assertEqual(seeds, (catalog_task_set,))
        self.assertGreater(len(expanded), 0)
        self.assertEqual(len(expanded[0]), 3)
        self.assertTrue(set(catalog_task_set).issubset(set(expanded[0])))

        seeds_with_expansion = _negative_worker_seed_task_sets(
            data,
            duals=zero_duals,
            master_columns=tuple(),
            b0_direct=object(),
            seed_catalog=catalog,
            max_direct_tasks=3,
            max_seed_sets=2,
        )
        self.assertEqual(seeds_with_expansion[0], catalog_task_set)
        self.assertEqual(seeds_with_expansion[1], expanded[0])

    def test_hidden_negative_physical_seed_rebuilds_worker_only_candidate_column(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        column = next(
            candidate
            for candidate in enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
            if len(candidate.sorties) == 1
        )
        signature = column_signature_from_journey(column)
        catalog = WorkerSeedCatalog()
        catalog.rows.append(
            {
                "task_set": tuple(signature.task_set),
                "ordered_task_sequences": signature.ordered_task_sequences,
                "path_signature": signature.path_option_signature,
                "source": "hidden_negative_audit",
                "true_reduced_cost": -1.0,
                "miss_reason": "worker_not_generated",
                "worker_priced_candidate_source_match": "none",
            }
        )

        rebuilt, payload = _catalog_physical_seed_columns(
            data,
            seed_catalog=catalog,
            max_columns=4,
        )

        self.assertEqual(len(rebuilt), 1)
        rebuilt_signature = column_signature_from_journey(rebuilt[0])
        self.assertEqual(rebuilt_signature.ordered_task_sequences, signature.ordered_task_sequences)
        self.assertEqual(rebuilt_signature.path_option_signature, signature.path_option_signature)
        self.assertEqual(rebuilt_signature.task_set, signature.task_set)
        self.assertEqual(payload["hidden_negative_physical_seed_column_count"], 1)
        self.assertEqual(payload["hidden_negative_physical_seed_invalid_count"], 0)
        self.assertFalse(payload["hidden_negative_physical_seed_mutates_certificate"])
        self.assertFalse(payload["hidden_negative_physical_seed_can_certify_no_negative"])
        self.assertEqual(
            payload["hidden_negative_physical_seed_certificate_role"],
            "worker_candidate_search_only",
        )

    def test_worker_seed_catalog_preserves_hidden_negative_physical_signature(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        column = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns[0]
        audit = build_hidden_negative_audit(
            worker_payload={
                "pricing_state": "LOCAL_NO_COLUMN_UNCERTIFIED",
                "worker_kind": "relaxed_labeling",
            },
            final_judge_payload={"pricing_state": "FOUND_NEGATIVE"},
            negative_candidates=((-1.0, column),),
        )
        catalog = WorkerSeedCatalog()
        catalog.record_hidden_negative_audit(audit)
        signature = column_signature_from_journey(column)

        self.assertEqual(catalog.rows[0]["ordered_task_sequences"], signature.ordered_task_sequences)
        self.assertEqual(catalog.rows[0]["path_signature"], signature.path_option_signature)
        payload = catalog.to_payload()
        self.assertEqual(
            payload["rows"][0]["ordered_task_sequences"],
            [list(row) for row in signature.ordered_task_sequences],
        )
        self.assertEqual(
            payload["rows"][0]["path_signature"],
            [list(row) for row in signature.path_option_signature],
        )
        self.assertFalse(payload["mutates_certificate"])

    def test_hidden_negative_refinement_portfolio_reserves_first_expansion_under_tight_budget(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        zero_duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)
        first_base = tuple(sorted(str(task_id) for task_id in data.task_ids[:2]))
        second_base = tuple(sorted(str(task_id) for task_id in data.task_ids[2:4]))
        catalog = WorkerSeedCatalog()
        catalog.rows.extend(
            [
                {
                    "task_set": first_base,
                    "path_signature": tuple(),
                    "source": "hidden_negative_audit",
                    "true_reduced_cost": -10.0,
                    "miss_reason": "worker_not_generated",
                    "worker_priced_candidate_source_match": "none",
                },
                {
                    "task_set": second_base,
                    "path_signature": tuple(),
                    "source": "hidden_negative_audit",
                    "true_reduced_cost": -9.0,
                    "miss_reason": "worker_not_generated",
                    "worker_priced_candidate_source_match": "none",
                },
            ]
        )

        expanded = _catalog_refinement_neighborhood_seed_task_sets(
            data,
            duals=zero_duals,
            seed_catalog=catalog,
            max_direct_tasks=3,
            expansion_width=2,
        )
        portfolio = _catalog_refinement_seed_portfolio(
            data,
            duals=zero_duals,
            seed_catalog=catalog,
            max_direct_tasks=3,
            max_seed_sets=3,
        )
        first_expansion = next(row for row in expanded if set(first_base).issubset(set(row)))

        self.assertEqual(portfolio[0], first_base)
        self.assertEqual(portfolio[1], first_expansion)
        self.assertIn(second_base, portfolio)

    def test_hidden_negative_catalog_prioritizes_unseen_pricing_regions(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        exact_seen = (str(data.task_ids[0]),)
        unseen = (str(data.task_ids[1]),)
        catalog = WorkerSeedCatalog()
        catalog.rows.extend(
            [
                {
                    "task_set": exact_seen,
                    "path_signature": tuple(),
                    "source": "hidden_negative_audit",
                    "true_reduced_cost": -100.0,
                    "miss_reason": "worker_not_generated",
                    "worker_priced_candidate_source_match": "exact",
                    "worker_priced_candidate_seed_sources": ("resource_extension",),
                },
                {
                    "task_set": unseen,
                    "path_signature": tuple(),
                    "source": "hidden_negative_audit",
                    "true_reduced_cost": -1.0,
                    "miss_reason": "worker_not_generated",
                    "worker_priced_candidate_source_match": "none",
                    "worker_priced_candidate_seed_sources": ("unknown",),
                },
            ]
        )
        zero_duals = JourneyDuals(cover={task_id: 0.0 for task_id in data.task_ids}, fleet_limit=0.0)

        refinement = _catalog_refinement_seed_task_sets(
            data,
            seed_catalog=catalog,
            max_direct_tasks=3,
        )
        seeds = _negative_worker_seed_task_sets(
            data,
            duals=zero_duals,
            master_columns=tuple(),
            b0_direct=object(),
            seed_catalog=catalog,
            max_direct_tasks=3,
            max_seed_sets=1,
        )
        payload = catalog.to_payload()

        self.assertEqual(refinement[0], unseen)
        self.assertEqual(seeds, (unseen,))
        self.assertEqual(payload["task_count_counts"], {"1": 2})
        self.assertEqual(payload["miss_reason_counts"], {"worker_not_generated": 2})
        self.assertEqual(payload["source_match_counts"], {"exact": 1, "none": 1})
        self.assertEqual(payload["seed_source_counts"], {"resource_extension": 1, "unknown": 1})
        self.assertEqual(payload["refinement_coverage_counts"], {"uncovered": 2})
        self.assertEqual(payload["refinement_exact_count"], 0)
        self.assertEqual(payload["refinement_superset_count"], 0)
        self.assertEqual(payload["refinement_covered_count"], 0)
        self.assertEqual(payload["refinement_uncovered_count"], 2)
        self.assertFalse(payload["mutates_certificate"])
        self.assertEqual(payload["rows"][0]["worker_priced_candidate_source_match"], "exact")
        self.assertEqual(
            payload["rows"][0]["worker_priced_candidate_seed_sources"],
            ["resource_extension"],
        )
        self.assertFalse(payload["mutates_certificate"])

    def test_hidden_negative_refinement_seed_source_rows_distinguish_base_and_expansion(self) -> None:
        base = (("a", "b"),)
        expanded = (("a", "b", "c"), ("a", "b"))

        rows = _refinement_seed_source_rows(
            refinement_seed_task_sets=base,
            refinement_expanded_seed_task_sets=expanded,
        )
        source_by_task_set = {tuple(row["task_set"]): row["sources"] for row in rows}

        self.assertEqual(
            source_by_task_set[("a", "b")],
            ["hidden_negative_refinement", "hidden_negative_refinement_expansion"],
        )
        self.assertEqual(
            source_by_task_set[("a", "b", "c")],
            ["hidden_negative_refinement_expansion"],
        )

    def test_hidden_negative_refinement_summary_exposes_last_and_catalog_coverage(self) -> None:
        catalog = WorkerSeedCatalog()
        catalog.rows.extend(
            [
                {
                    "task_set": ("a",),
                    "path_signature": tuple(),
                    "source": "hidden_negative_audit",
                    "true_reduced_cost": -1.0,
                    "worker_priced_candidate_source_match": "exact",
                    "worker_priced_candidate_seed_sources": ("hidden_negative_refinement",),
                },
                {
                    "task_set": ("a", "b"),
                    "path_signature": tuple(),
                    "source": "hidden_negative_audit",
                    "true_reduced_cost": -0.5,
                    "worker_priced_candidate_source_match": "superset",
                    "worker_priced_candidate_seed_sources": ("hidden_negative_refinement_expansion",),
                },
                {
                    "task_set": ("c",),
                    "path_signature": tuple(),
                    "source": "hidden_negative_audit",
                    "true_reduced_cost": -0.1,
                    "worker_priced_candidate_source_match": "none",
                    "worker_priced_candidate_seed_sources": ("unknown",),
                },
            ]
        )
        summary = _hidden_negative_refinement_summary(
            {
                "hidden_negative_refinement_coverage_counts": {"exact": 1},
                "hidden_negative_refinement_exact_count": 1,
                "hidden_negative_refinement_superset_count": 0,
                "hidden_negative_refinement_covered_count": 1,
                "hidden_negative_refinement_uncovered_count": 0,
            },
            catalog,
        )

        self.assertEqual(summary["hidden_negative_refinement_coverage_counts"], {"exact": 1})
        self.assertEqual(summary["hidden_negative_refinement_exact_count"], 1)
        self.assertEqual(
            summary["hidden_negative_refinement_catalog_coverage_counts"],
            {"exact": 1, "superset": 1, "uncovered": 1},
        )
        self.assertEqual(summary["hidden_negative_refinement_catalog_covered_count"], 2)
        self.assertEqual(summary["hidden_negative_refinement_catalog_uncovered_count"], 1)
        self.assertEqual(summary["hidden_negative_refinement_catalog_seed_count"], 3)
        self.assertTrue(summary["hidden_negative_refinement_coverage_diagnostic_only"])

    def test_resource_extension_ng_seed_generator_respects_budget_and_task_cap(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 5.0 + index for index, task_id in enumerate(data.task_ids)},
            fleet_limit=0.0,
        )

        rows = _resource_extension_ng_seed_task_sets(
            data,
            duals,
            ng_neighborhood_size=3,
            max_task_count=3,
            max_candidate_sets=8,
            max_labels_per_task=2,
        )

        self.assertGreater(len(rows), 0)
        self.assertLessEqual(len(rows), 8)
        self.assertTrue(all(1 <= len(row) <= 3 for row in rows))
        self.assertTrue(all(set(row).issubset(set(data.task_ids)) for row in rows))
        self.assertTrue(any(len(row) > 1 for row in rows))

    def test_resource_extension_ng_seed_generator_reports_worker_only_dominance_stats(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 5.0 + index for index, task_id in enumerate(data.task_ids)},
            fleet_limit=0.0,
        )

        rows, stats = _resource_extension_ng_seed_task_sets_with_stats(
            data,
            duals,
            ng_neighborhood_size=3,
            max_task_count=3,
            max_candidate_sets=8,
            max_labels_per_task=1,
        )

        self.assertGreater(len(rows), 0)
        self.assertGreater(stats["label_attempt_count"], 0)
        self.assertGreater(stats["label_feasible_count"], 0)
        self.assertEqual(stats["label_returned_seed_count"], len(rows))
        self.assertGreaterEqual(stats["label_dominance_rejected_count"], 0)
        self.assertGreaterEqual(stats["label_capacity_truncated_count"], 0)

    def test_resource_extension_ng_seed_generator_respects_expired_deadline(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 5.0 + index for index, task_id in enumerate(data.task_ids)},
            fleet_limit=0.0,
        )

        rows, stats = _resource_extension_ng_seed_task_sets_with_stats(
            data,
            duals,
            ng_neighborhood_size=3,
            max_task_count=3,
            max_candidate_sets=8,
            max_labels_per_task=2,
            deadline=0.0,
        )

        self.assertEqual(rows, tuple())
        self.assertEqual(stats["label_attempt_count"], 0)
        self.assertGreater(stats["label_time_limit_hit_count"], 0)

    def test_relaxed_labeling_worker_deadline_hit_is_incomplete_not_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: -100.0 for task_id in data.task_ids},
            fleet_limit=0.0,
        )

        payload, columns = run_bpc_labeling_pricer(
            data,
            duals,
            config=LabelingPricingConfig(
                mode=RELAXED_NG_ROUTE_MODE,
                max_label_task_count=3,
                max_candidate_sets=8,
                wall_time_limit_sec=0.0,
            ),
        )

        self.assertEqual(columns, tuple())
        self.assertEqual(payload["pricing_state"], PricingState.INCOMPLETE_LIMIT.value)
        self.assertTrue(payload["resource_extension_time_limit_hit"])
        self.assertGreater(payload["resource_extension_label_time_limit_hit_count"], 0)
        self.assertTrue(payload["worker_pricing_limit_hit"])
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["uses_true_dual_bpc_certificate"])
        self.assertFalse(payload["certificate_semantics_issues"])

    def test_resource_extension_label_bucket_preserves_task_count_bands(self) -> None:
        def label(task_set, reduced_proxy, end_time):
            return SimpleNamespace(
                task_set=tuple(task_set),
                sortie=SimpleNamespace(
                    end_time=float(end_time),
                    energy_proxy=1.0,
                    shadow_exposure_min=1.0,
                ),
                reduced_proxy=float(reduced_proxy),
            )

        labels = []
        one_task = label(("ice_site_001",), -10.0, 10.0)
        one_task_replacement = label(("ice_site_002",), -9.0, 11.0)
        two_task = label(("ice_site_001", "ice_site_002"), -1.0, 30.0)

        accepted, _reason, _replaced, truncated = _add_resource_extension_label(
            labels,
            one_task,
            max_labels_per_task=1,
        )
        self.assertTrue(accepted)
        self.assertEqual(truncated, 0)
        accepted, _reason, _replaced, truncated = _add_resource_extension_label(
            labels,
            one_task_replacement,
            max_labels_per_task=1,
        )
        self.assertFalse(accepted)
        self.assertEqual(truncated, 1)
        accepted, _reason, _replaced, truncated = _add_resource_extension_label(
            labels,
            two_task,
            max_labels_per_task=1,
        )

        self.assertTrue(accepted)
        self.assertEqual(truncated, 0)
        self.assertEqual({len(row.task_set) for row in labels}, {1, 2})
        self.assertIn(two_task, labels)
        self.assertIn(one_task, labels)
        self.assertNotIn(one_task_replacement, labels)

    def test_resource_extension_path_variants_are_bounded_and_deduped(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        sequence = tuple(data.task_ids[:2])

        assignments, duplicate_count = _resource_extension_path_type_assignments(
            data,
            sequence,
            proxy_profile="balanced",
        )

        self.assertGreater(len(assignments), 0)
        self.assertLessEqual(len(assignments), _RESOURCE_EXTENSION_MAX_PATH_VARIANTS_PER_SEQUENCE)
        self.assertGreaterEqual(duplicate_count, 0)
        self.assertEqual(len(assignments), len(set(assignments)))
        self.assertTrue(all(len(row) == len(sequence) + 1 for row in assignments))

    def test_relaxed_worker_reports_multi_profile_resource_extension_portfolio(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: -100.0 for task_id in data.task_ids},
            fleet_limit=0.0,
        )

        payload, columns = run_bpc_labeling_pricer(
            data,
            duals,
            config=LabelingPricingConfig(
                mode=RELAXED_NG_ROUTE_MODE,
                max_label_task_count=3,
                max_candidate_sets=8,
                harvest_target=4,
            ),
        )

        self.assertEqual(
            payload["resource_extension_proxy_profiles"],
            list(_RESOURCE_EXTENSION_PROXY_PROFILES),
        )
        self.assertEqual(
            payload["resource_extension_proxy_profile_count"],
            len(_RESOURCE_EXTENSION_PROXY_PROFILES),
        )
        self.assertGreater(payload["resource_extension_seed_task_set_count"], 0)
        self.assertGreater(payload["resource_extension_label_attempt_count"], 0)
        self.assertGreater(payload["resource_extension_label_stats"]["label_feasible_count"], 0)
        self.assertGreaterEqual(
            payload["resource_extension_label_stats"]["label_returned_seed_count"],
            payload["raw_resource_extension_seed_task_set_count"],
        )
        self.assertTrue(payload["resource_extension_label_column_worker_enabled"])
        self.assertGreater(payload["resource_extension_label_column_count"], 0)
        self.assertGreater(payload["resource_extension_label_column_task_set_count"], 0)
        self.assertGreater(payload["resource_extension_label_path_variant_candidate_count"], 0)
        self.assertGreater(payload["resource_extension_label_path_variant_feasible_count"], 0)
        self.assertGreaterEqual(
            payload["resource_extension_label_path_variant_candidate_count"],
            payload["resource_extension_label_path_variant_feasible_count"],
        )
        self.assertEqual(
            payload["resource_extension_label_column_policy"],
            "feasible_resource_extension_physical_representatives_worker_only",
        )
        self.assertFalse(payload["resource_extension_label_columns_can_certify_no_negative"])
        self.assertIn("resource_extension", payload["active_seed_task_set_source_task_count_counts"])
        self.assertIn("ng_route", payload["active_seed_task_set_source_task_count_counts"])
        self.assertTrue(
            any(
                int(task_count) >= 1
                for task_count in payload["active_seed_task_set_source_task_count_counts"][
                    "resource_extension"
                ]
            )
        )
        self.assertIn(
            "priced_candidate_task_set_source_task_count_counts",
            payload,
        )
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_RELAXED_WORKER_UNCERTIFIED)
        self.assertEqual(payload["status_semantics_contract_version"], STATUS_SEMANTICS_CONTRACT_VERSION)
        self.assertTrue(payload["certificate_semantics_pass"])
        self.assertEqual(payload["certificate_semantics_issues"], [])
        self.assertFalse(payload["worker_no_column_can_certify"])
        self.assertFalse(payload["limit_result_can_certify"])
        self.assertFalse(payload["worker_mode_certificate_allowed"])
        self.assertEqual(columns, tuple())

    def test_resource_extension_physical_labels_can_find_worker_columns_without_direct_pricer(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 1000.0 for task_id in data.task_ids},
            fleet_limit=0.0,
        )
        empty_direct_payload = {
            "status": "NO_DIRECT_LABEL_FOUND",
            "candidate_sets": [],
            "candidate_round_count": 0,
            "sortie_attempt_count": 0,
            "feasible_sortie_template_count": 0,
            "pareto_label_count": 0,
        }

        with patch(
            "lunar_ice_bpc.exact.bpc.pricing.resource_label_core.price_direct_journey_columns_incremental",
            return_value=(dict(empty_direct_payload), tuple()),
        ), patch(
            "lunar_ice_bpc.exact.bpc.pricing.resource_label_core.price_direct_journey_columns",
            return_value=(dict(empty_direct_payload), tuple()),
        ):
            payload, columns = run_bpc_labeling_pricer(
                data,
                duals,
                config=LabelingPricingConfig(
                    mode=RELAXED_NG_ROUTE_MODE,
                    max_label_task_count=3,
                    max_candidate_sets=8,
                    harvest_target=4,
                ),
            )

        self.assertTrue(payload["resource_extension_label_column_worker_enabled"])
        self.assertGreater(payload["resource_extension_label_column_count"], 0)
        self.assertGreater(payload["resource_extension_label_path_variant_candidate_count"], 0)
        self.assertGreater(payload["resource_extension_label_path_variant_feasible_count"], 0)
        self.assertGreater(payload["true_audited_column_count"], 0)
        self.assertEqual(payload["direct_seed_portfolio_column_count"], 0)
        self.assertEqual(payload["pricing_state"], PricingState.FOUND_NEGATIVE.value)
        self.assertGreater(payload["harvest_candidate_negative_count"], 0)
        self.assertGreater(payload["harvest_selected_count"], 0)
        self.assertGreater(len(columns), 0)
        self.assertIn("resource_extension", payload["harvest_selected_seed_source_counts"])
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["uses_true_dual_bpc_certificate"])
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_RELAXED_WORKER_UNCERTIFIED)
        self.assertFalse(payload["resource_extension_label_columns_can_certify_no_negative"])
        self.assertTrue(payload["certificate_semantics_pass"])

    def test_relaxed_worker_reports_hidden_negative_refinement_seed_source(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_a, task_b = data.task_ids[:2]
        seed = (task_a, task_b)
        duals = JourneyDuals(cover={task_id: -100.0 for task_id in data.task_ids}, fleet_limit=0.0)

        payload, columns = run_bpc_labeling_pricer(
            data,
            duals,
            config=LabelingPricingConfig(
                mode=RELAXED_NG_ROUTE_MODE,
                max_label_task_count=3,
                max_candidate_sets=8,
                harvest_target=4,
            ),
            seed_task_sets=(seed,),
            seed_source_rows=(
                {
                    "task_set": list(seed),
                    "sources": ["hidden_negative_refinement"],
                },
            ),
        )

        matching_rows = [
            row
            for row in payload["active_seed_task_set_sources"]
            if tuple(row["task_set"]) == tuple(sorted(seed))
        ]
        self.assertTrue(matching_rows)
        self.assertIn("hidden_negative_refinement", matching_rows[0]["sources"])
        self.assertIn("hidden_negative_refinement", payload["active_seed_task_set_source_counts"])
        self.assertEqual(payload["protected_refinement_seed_task_set_count"], 1)
        self.assertEqual(payload["active_protected_refinement_seed_task_set_count"], 1)
        self.assertEqual(payload["protected_refinement_seed_task_set_count_by_size"], {"2": 1})
        self.assertEqual(payload["protected_refinement_seed_budget_truncated_count"], 0)
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_RELAXED_WORKER_UNCERTIFIED)
        self.assertEqual(columns, tuple())

    def test_worker_generated_task_sets_prefers_actual_columns_over_candidate_universes(self) -> None:
        payload = {
            "worker_generated_column_task_sets": [["actual_a"]],
            "worker_seen_task_sets": [["actual_a"]],
            "generated_task_sets": [["seed_b"]],
            "active_seed_task_sets": [["seed_c"]],
            "candidate_sets": [["candidate_d"]],
        }
        legacy_payload = {
            "generated_task_sets": [["seed_b"]],
            "active_seed_task_sets": [["seed_c"]],
            "candidate_sets": [["candidate_d"]],
        }

        self.assertEqual(_worker_generated_task_sets(payload), [["actual_a"]])
        self.assertEqual(
            _worker_generated_task_sets(legacy_payload),
            [["seed_b"], ["seed_c"], ["candidate_d"]],
        )

    def test_worker_seed_portfolio_preserves_source_and_task_count_diversity(self) -> None:
        selected = _bounded_portfolio_seed_sets(
            input_seed_sets=(("a",), ("a", "b"), ("a", "b", "c"), ("a", "b", "c", "d")),
            resource_extension_seed_sets=(("r1",), ("r1", "r2"), ("r1", "r2", "r3")),
            ng_seed_sets=(("n1",), ("n1", "n2"), ("n1", "n2", "n3")),
            max_candidate_sets=6,
        )

        self.assertLessEqual(len(selected), 6)
        self.assertIn(("r1",), selected)
        self.assertIn(("n1",), selected)
        self.assertIn(("r1", "r2"), selected)
        self.assertIn(("n1", "n2"), selected)
        self.assertGreaterEqual(len({len(row) for row in selected}), 2)

        source_payload_rows = []
        for row in selected:
            if row[0] == "a":
                source = "input_seed"
            elif row[0] == "r1":
                source = "resource_extension"
            else:
                source = "ng_route"
            source_payload_rows.append({"task_set": list(row), "sources": [source]})
        source_rows = _seed_source_task_count_counts(source_payload_rows)
        self.assertIn("1", source_rows["input_seed"])
        self.assertIn("1", source_rows["resource_extension"])
        self.assertIn("1", source_rows["ng_route"])
        self.assertIn("2", source_rows["input_seed"])
        self.assertIn("2", source_rows["resource_extension"])
        self.assertIn("2", source_rows["ng_route"])

    def test_worker_seed_portfolio_fills_remaining_budget_with_low_overlap_sets(self) -> None:
        selected = _bounded_portfolio_seed_sets(
            input_seed_sets=(("a",), ("a", "b"), ("a", "c"), ("x", "y")),
            resource_extension_seed_sets=(("r",),),
            ng_seed_sets=(("n",),),
            max_candidate_sets=5,
        )

        self.assertEqual(selected[:3], (("a",), ("r",), ("n",)))
        self.assertIn(("x", "y"), selected)
        self.assertEqual(selected[3], ("a", "b"))
        self.assertEqual(selected[4], ("x", "y"))
        self.assertNotIn(("a", "c"), selected)

    def test_worker_seed_portfolio_protects_hidden_negative_refinement_budget(self) -> None:
        protected = (("a", "b", "c"),)
        selected = _bounded_portfolio_seed_sets(
            input_seed_sets=(("a", "b", "c"), ("seed",)),
            resource_extension_seed_sets=(("r1",), ("r1", "r2")),
            ng_seed_sets=(("n1",), ("n1", "n2")),
            protected_seed_sets=protected,
            max_candidate_sets=1,
        )

        self.assertEqual(selected, protected)

    def test_worker_seed_portfolio_protects_bounded_support_continuation_budget(self) -> None:
        source_rows = (
            {"task_set": ["s1", "s2"], "sources": ["support_continuation"]},
            {"task_set": ["s1", "s3"], "sources": ["support_continuation"]},
            {"task_set": ["s1", "s4"], "sources": ["support_continuation"]},
        )
        protected = _protected_extra_seed_task_sets(
            source_rows,
            (("s1", "s2"), ("s1", "s3"), ("s1", "s4"), ("seed",)),
            source_prefix="support_continuation",
            limit=2,
        )
        selected = _bounded_portfolio_seed_sets(
            input_seed_sets=(("seed",), ("s1", "s2"), ("s1", "s3"), ("s1", "s4")),
            resource_extension_seed_sets=(("r1",), ("r1", "r2")),
            ng_seed_sets=(("n1",), ("n1", "n2")),
            protected_seed_sets=protected,
            max_candidate_sets=2,
        )

        self.assertEqual(protected, (("s1", "s2"), ("s1", "s3")))
        self.assertEqual(selected, protected)

    def test_worker_task_cap_is_fixed_env_config_for_large_instances(self) -> None:
        instance = generate_instance(30, seed=929001, index=1)
        data = load_lunar_ice_data(instance)
        self.assertGreaterEqual(data.max_tasks_per_trip, 4)

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(LABELING_WORKER_MAX_TASK_CAP_ENV, None)
            self.assertEqual(_worker_task_cap(data, max_direct_tasks=30), 3)
        with patch.dict(os.environ, {LABELING_WORKER_MAX_TASK_CAP_ENV: "4"}, clear=False):
            self.assertEqual(_worker_task_cap(data, max_direct_tasks=30), 4)
        with patch.dict(os.environ, {LABELING_WORKER_MAX_TASK_CAP_ENV: "999"}, clear=False):
            self.assertEqual(_worker_task_cap(data, max_direct_tasks=30), data.max_tasks_per_trip)
        with patch.dict(os.environ, {LABELING_WORKER_MAX_TASK_CAP_ENV: "4"}, clear=False):
            self.assertEqual(_worker_task_cap(data, max_direct_tasks=3), 3)

    def test_large_task_direct_worker_seeds_general_large_clusters(self) -> None:
        instance = generate_instance(30, seed=929011, index=1)
        data = load_lunar_ice_data(instance)
        task_ids = tuple(data.task_ids)
        duals = JourneyDuals(
            cover={task_id: 30.0 - index for index, task_id in enumerate(task_ids)},
            fleet_limit=0.0,
        )

        seeds, source_rows = _large_task_direct_worker_seed_task_sets(
            data,
            duals=duals,
            master_columns=tuple(),
            b0_direct=SimpleNamespace(journeys=tuple()),
            support_task_sets=(task_ids[:8], task_ids[8:16]),
            min_task_count=5,
            max_task_count=12,
            max_seed_sets=40,
            neighborhood_width=3,
        )

        self.assertGreater(len(seeds), 0)
        self.assertTrue(any(len(row) > 4 for row in seeds))
        self.assertTrue(all(5 <= len(row) <= 12 for row in seeds))
        self.assertEqual(len(seeds), len(source_rows))
        self.assertTrue(
            any(
                any(str(source).startswith("large_task_") for source in row["sources"])
                for row in source_rows
            )
        )

    def test_large_task_direct_worker_is_candidate_search_only(self) -> None:
        instance = generate_instance(10, seed=929012, index=1)
        data = load_lunar_ice_data(instance)
        task_ids = tuple(data.task_ids)
        duals = JourneyDuals(
            cover={task_id: 20.0 - index for index, task_id in enumerate(task_ids)},
            fleet_limit=0.0,
        )
        env = {
            "LUNAR_ICE_LARGE_TASK_DIRECT_WORKER": "1",
            LARGE_TASK_DIRECT_WORKER_MAX_TASKS_ENV: "6",
            LARGE_TASK_DIRECT_WORKER_MAX_CANDIDATE_SETS_ENV: "12",
            LARGE_TASK_DIRECT_WORKER_TIME_CAP_SEC_ENV: "5",
        }

        with patch.dict(os.environ, env, clear=False):
            payload, _columns = _run_large_task_direct_worker(
                data,
                worker_duals=duals,
                true_duals=duals,
                master_columns=tuple(),
                b0_direct=SimpleNamespace(journeys=tuple()),
                support_task_sets=(task_ids[:6],),
                worker_task_cap=3,
                max_direct_tasks=10,
                max_candidate_sets=32,
                negative_eps=1.0e-6,
                branch_context=BranchContext(),
                cut_context=CutContext(),
                deadline=None,
            )

        self.assertTrue(payload["large_task_direct_worker_enabled"])
        self.assertFalse(payload["large_task_direct_worker_can_certify_no_negative"])
        self.assertFalse(payload["large_task_direct_worker_no_column_can_certify"])
        self.assertFalse(payload["large_task_direct_worker_mutates_certificate"])
        self.assertEqual(
            payload["large_task_direct_worker_pricing_proof_kind"],
            "DIRECT_LARGE_TASK_WORKER_UNCERTIFIED",
        )
        self.assertGreater(payload["large_task_direct_worker_seed_count"], 0)

    def test_protected_extra_seed_task_sets_only_accepts_refinement_sources_in_candidates(self) -> None:
        protected = _protected_extra_seed_task_sets(
            (
                {"task_set": ["a", "b"], "sources": ["hidden_negative_refinement"]},
                {"task_set": ["b", "c"], "sources": ["hidden_negative_refinement_expansion"]},
                {"task_set": ["c", "d"], "sources": ["ng_route"]},
                {"task_set": ["not", "candidate"], "sources": ["hidden_negative_refinement"]},
            ),
            candidate_seed_sets=(("a", "b"), ("b", "c"), ("c", "d")),
            source_prefix="hidden_negative_refinement",
        )

        self.assertEqual(protected, (("a", "b"), ("b", "c")))

    def test_relaxed_worker_seed_portfolio_filters_branch_infeasible_task_sets(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_a, task_b, task_c = data.task_ids[:3]
        context = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))
        duals = JourneyDuals(
            cover={task_id: -100.0 for task_id in data.task_ids},
            fleet_limit=0.0,
        )

        payload, _columns = run_bpc_labeling_pricer(
            data,
            duals,
            config=LabelingPricingConfig(
                mode=RELAXED_NG_ROUTE_MODE,
                max_label_task_count=3,
                max_candidate_sets=12,
                harvest_target=4,
            ),
            branch_context=context,
            seed_task_sets=((task_a,), (task_a, task_b), (task_c,)),
        )

        active_sets = [set(row) for row in payload["active_seed_task_sets"]]
        self.assertTrue(payload["branch_seed_filter_enabled"])
        self.assertGreater(payload["branch_seed_filtered_input_count"], 0)
        self.assertGreater(payload["branch_seed_filtered_ng_count"], 0)
        self.assertIn({task_a, task_b}, active_sets)
        self.assertIn({task_c}, active_sets)
        self.assertTrue(
            all(
                {task_a, task_b}.issubset(row)
                or row.isdisjoint({task_a, task_b})
                or bool(row - {task_a, task_b})
                for row in active_sets
            )
        )
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_RELAXED_WORKER_UNCERTIFIED)

    def test_relaxed_worker_branch_invalid_column_fails_candidate_audit_flags(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_a, task_b = data.task_ids[:2]
        branch_context = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))
        invalid_column = next(
            column for column in enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
            if column.task_set == frozenset((task_a,))
        )
        duals = JourneyDuals(cover={str(task_a): float(invalid_column.objective) + 10.0}, fleet_limit=0.0)
        mocked_core_payload = {
            "resource_label_algorithm": "ng_route_relaxed_resource_labeling",
            "resource_label_core_mode": "relaxed_ng_route_worker",
            "resource_dimensions": ["time_window", "energy"],
            "dominance_policy": "ng_route_relaxed_dominance_worker_only",
            "elementarity_policy": "ng_route_relaxed_elementarity_worker_only",
            "priced_candidate_task_set_sources": [
                {"task_set": [task_a], "sources": ["ng_route"]},
            ],
            "worker_candidate_universe_task_sets": [[task_a]],
            "worker_generated_column_task_sets": [[task_a]],
            "worker_generated_column_task_set_count": 1,
        }

        with patch(
            "lunar_ice_bpc.exact.bpc.pricing.labeling_pricer.run_resource_label_core",
            return_value=(mocked_core_payload, (invalid_column,)),
        ):
            payload, selected = run_bpc_labeling_pricer(
                data,
                duals,
                config=LabelingPricingConfig(
                    mode=RELAXED_NG_ROUTE_MODE,
                    max_label_task_count=5,
                    max_candidate_sets=4,
                    harvest_target=2,
                ),
                branch_context=branch_context,
            )

        self.assertEqual(selected, ())
        self.assertEqual(payload["pricing_state"], PricingState.LOCAL_NO_COLUMN_UNCERTIFIED.value)
        self.assertFalse(payload["branch_context_audit_pass"])
        self.assertEqual(payload["branch_invalid_column_count"], 1)
        self.assertFalse(payload["worker_true_dual_candidate_audit_pass"])
        self.assertFalse(payload["manual_rc_audit_pass"])
        self.assertFalse(payload["pricing_rc_audit_pass"])
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_RELAXED_WORKER_UNCERTIFIED)

    def test_relaxed_worker_timeout_is_incomplete_not_local_no_column(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: -100.0 for task_id in data.task_ids}, fleet_limit=0.0)
        mocked_core_payload = {
            "status": "DIRECT_LABEL_PRICING_TIME_LIMIT",
            "timeout_stage": "candidate_loop",
            "resource_label_algorithm": "ng_route_relaxed_resource_labeling",
            "resource_label_core_mode": "relaxed_ng_route_worker",
            "resource_dimensions": ["time_window", "energy"],
            "dominance_policy": "ng_route_relaxed_dominance_worker_only",
            "elementarity_policy": "ng_route_relaxed_elementarity_worker_only",
            "priced_candidate_task_set_sources": [],
            "worker_candidate_universe_task_sets": [],
            "worker_generated_column_task_sets": [],
            "worker_generated_column_task_set_count": 0,
        }

        with patch(
            "lunar_ice_bpc.exact.bpc.pricing.labeling_pricer.run_resource_label_core",
            return_value=(mocked_core_payload, tuple()),
        ):
            payload, selected = run_bpc_labeling_pricer(
                data,
                duals,
                config=LabelingPricingConfig(
                    mode=RELAXED_NG_ROUTE_MODE,
                    max_label_task_count=5,
                    max_candidate_sets=4,
                    harvest_target=2,
                ),
            )

        self.assertEqual(selected, tuple())
        self.assertEqual(payload["pricing_state"], PricingState.INCOMPLETE_LIMIT.value)
        self.assertTrue(payload["worker_pricing_limit_hit"])
        self.assertEqual(payload["worker_timeout_stage"], "candidate_loop")
        self.assertFalse(payload["no_column_uncertified"])
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["worker_no_column_can_certify"])
        self.assertTrue(payload["limit_result"])
        self.assertFalse(payload["limit_result_can_certify"])
        self.assertTrue(payload["certificate_semantics_pass"])
        self.assertEqual(payload["certificate_semantics_issues"], [])

    def test_direct_pricing_branch_candidate_filter_is_conservative_for_subset_pricing(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_a, task_b, task_c = data.task_ids[:3]
        duals = JourneyDuals(cover={task_id: -100.0 for task_id in data.task_ids}, fleet_limit=0.0)

        same_payload, _ = price_direct_journey_columns_incremental(
            data,
            duals,
            max_direct_tasks=3,
            seed_task_sets=((task_a,), (task_a, task_b), (task_a, task_c)),
            max_candidate_sets=6,
            stop_at_first_negative=False,
            branch_context=BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),)),
        )
        same_candidate_sets = [set(row) for row in same_payload["candidate_sets"]]

        self.assertGreater(same_payload["branch_filtered_candidate_set_count"], 0)
        self.assertNotIn({task_a}, same_candidate_sets)
        self.assertIn({task_a, task_b}, same_candidate_sets)
        self.assertIn({task_a, task_c}, same_candidate_sets)
        self.assertFalse(same_payload["can_certify_no_negative"])

        different_payload, _ = price_direct_journey_columns(
            data,
            duals,
            max_direct_tasks=3,
            seed_task_sets=((task_a, task_b),),
            max_candidate_sets=1,
            branch_context=BranchContext((PairBranchDecision(task_a, task_b, DIFFERENT_JOURNEY),)),
        )
        different_candidate_sets = [set(row) for row in different_payload["candidate_sets"]]

        self.assertEqual(different_payload["branch_filtered_candidate_set_count"], 0)
        self.assertTrue(any({task_a, task_b}.issubset(row) for row in different_candidate_sets))
        self.assertFalse(different_payload["can_certify_no_negative"])

    def test_seed_source_lookup_prefers_exact_then_subset_match(self) -> None:
        rows = [
            {"task_set": ["a", "b"], "sources": ["resource_extension"]},
            {"task_set": ["a", "b", "c"], "sources": ["ng_route"]},
            {"task_set": ["d", "e"], "sources": ["direct_candidate"]},
        ]
        lookup = _seed_source_lookup(rows)

        self.assertEqual(_sources_for_task_set(("b", "a"), lookup), (("resource_extension",), "exact"))
        self.assertEqual(_sources_for_task_set(("c",), lookup), (("ng_route",), "subset"))
        self.assertEqual(_sources_for_task_set(("e", "d"), lookup), (("direct_candidate",), "exact"))
        self.assertEqual(_sources_for_task_set(("z",), lookup), (("unknown",), "none"))

    def test_incremental_pricing_completion_bound_preserves_best_reduced_cost(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 20.0 - index for index, task_id in enumerate(data.task_ids)},
            fleet_limit=3.0,
        )
        seed = (tuple(data.task_ids),)

        pruned, _ = price_direct_journey_columns_incremental(
            data,
            duals,
            max_direct_tasks=5,
            seed_task_sets=seed,
            max_candidate_sets=1,
            completion_bound_enabled=True,
            stop_at_first_negative=False,
        )
        unpruned, _ = price_direct_journey_columns_incremental(
            data,
            duals,
            max_direct_tasks=5,
            seed_task_sets=seed,
            max_candidate_sets=1,
            completion_bound_enabled=False,
            stop_at_first_negative=False,
        )

        self.assertEqual(pruned["best_reduced_cost"], unpruned["best_reduced_cost"])
        self.assertTrue(pruned["completion_bound"]["enabled"])
        self.assertFalse(unpruned["completion_bound"]["enabled"])
        self.assertFalse(pruned["completion_bound"]["can_certify_no_negative"])
        self.assertFalse(pruned["completion_bound"]["includes_fleet_dual"])
        self.assertGreater(pruned["completion_bound"]["evaluated_label_count"], 0)
        self.assertFalse(pruned["can_certify_no_negative"])

    def test_incremental_pricing_completion_bound_disabled_under_active_cut(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        context = CutContext((fleet_lower_bound_cut("fleet_lb_active", min_vehicles=1),))
        duals = JourneyDuals(cover={}, fleet_limit=0.0, cuts={"fleet_lb_active": 25.0})

        priced, _ = price_direct_journey_columns_incremental(
            data,
            duals,
            max_direct_tasks=5,
            seed_task_sets=(tuple(data.task_ids),),
            max_candidate_sets=1,
            completion_bound_enabled=True,
            cut_context=context,
            stop_at_first_negative=False,
        )

        self.assertTrue(priced["cut_context_active"])
        self.assertFalse(priced["completion_bound"]["enabled"])
        self.assertEqual(priced["completion_bound"]["pruned_label_count"], 0)
        self.assertFalse(priced["completion_bound"]["can_certify_no_negative"])

    def test_full_universe_incremental_pricing_matches_exhaustive_best_rc(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 20.0 - index for index, task_id in enumerate(data.task_ids)},
            fleet_limit=3.0,
        )

        full, full_columns = price_full_universe_incremental_journey_columns(
            data,
            duals,
            max_direct_tasks=5,
            completion_bound_enabled=False,
        )
        exhaustive, exhaustive_columns = price_exhaustive_direct_journey_columns(
            data,
            duals,
            max_direct_tasks=5,
            completion_bound_enabled=False,
        )
        exhaustive_best = min(manual_journey_reduced_cost(column, duals) for column in exhaustive_columns)

        self.assertEqual(full["status"], "FULL_UNIVERSE_INCREMENTAL_LABEL_PRICED")
        self.assertTrue(full["pricing_complete_for_all_task_subsets"])
        self.assertEqual(full["pricing_coverage_algorithm"], "full_universe_incremental_label")
        self.assertEqual(full["candidate_round_count"], 1)
        self.assertEqual(full["search_region_count"], 31)
        self.assertEqual(
            full["search_region_count_semantics"],
            "all_nonempty_task_subsets_covered_by_one_incremental_label_dp",
        )
        self.assertEqual(full["returned_column_count"], 1)
        self.assertEqual(full["returned_column_policy"], "single_global_min_column")
        self.assertEqual(full["returned_column_semantics"], "single_best_column_from_full_space_labeling")
        self.assertFalse(full["returned_columns_are_complete_universe"])
        self.assertTrue(full["global_min_proof_complete"])
        self.assertEqual(full["global_min_reduced_cost_source"], "full_universe_incremental_label_dp")
        self.assertEqual(full["global_min_reduced_cost_scope"], "all_nonempty_task_subsets")
        self.assertTrue(full["global_min_proof_requires_true_dual_reaudit"])
        self.assertTrue(full["sortie_candidate_cache_enabled"])
        self.assertIn("sortie_candidate_cache_hit_count", full)
        self.assertGreater(full["sortie_candidate_cache_miss_count"], 0)
        self.assertGreaterEqual(full["sortie_candidate_cache_entry_count"], 1)
        self.assertEqual(full["priced_candidate_set_count_by_task_count"], exhaustive["priced_candidate_set_count_by_task_count"])
        self.assertAlmostEqual(full["best_reduced_cost"], exhaustive["best_reduced_cost"], places=6)
        self.assertAlmostEqual(full["global_min_reduced_cost"], exhaustive["best_reduced_cost"], places=6)
        self.assertAlmostEqual(full["best_reduced_cost"], exhaustive_best, places=6)
        self.assertEqual(len(full_columns), 1)
        self.assertFalse(full["can_certify_no_negative"])
        self.assertFalse(full["uses_true_dual_bpc_certificate"])

    def test_full_universe_incremental_can_harvest_diverse_negative_columns(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 100.0 for task_id in data.task_ids},
            fleet_limit=0.0,
        )

        full, full_columns = price_full_universe_incremental_journey_columns(
            data,
            duals,
            max_direct_tasks=5,
            max_returned_columns=4,
            completion_bound_enabled=False,
        )
        exhaustive, exhaustive_columns = price_exhaustive_direct_journey_columns(
            data,
            duals,
            max_direct_tasks=5,
            completion_bound_enabled=False,
        )
        exhaustive_best = min(manual_journey_reduced_cost(column, duals) for column in exhaustive_columns)
        returned_rc = [manual_journey_reduced_cost(column, duals) for column in full_columns]

        self.assertEqual(full["status"], "FULL_UNIVERSE_INCREMENTAL_LABEL_PRICED")
        self.assertTrue(full["pricing_complete_for_all_task_subsets"])
        self.assertTrue(full["global_min_proof_complete"])
        self.assertEqual(full["exact_negative_harvest_target"], 4)
        self.assertGreater(full["exact_negative_harvest_candidate_count"], 1)
        self.assertGreater(full["exact_negative_harvest_selected_count"], 1)
        self.assertLessEqual(len(full_columns), 4)
        self.assertEqual(full["returned_column_count"], len(full_columns))
        self.assertEqual(
            full["returned_column_policy"],
            "global_min_plus_diverse_negative_harvest",
        )
        self.assertEqual(
            full["returned_column_semantics"],
            "global_min_column_plus_diverse_negative_columns_from_full_space_labeling",
        )
        self.assertAlmostEqual(min(returned_rc), exhaustive_best, places=6)
        self.assertAlmostEqual(full["best_reduced_cost"], exhaustive["best_reduced_cost"], places=6)
        self.assertTrue(all(rc < -1.0e-6 for rc in returned_rc))
        self.assertFalse(full["can_certify_no_negative"])
        self.assertFalse(full["uses_true_dual_bpc_certificate"])

        active_task_sets = tuple(tuple(sorted(column.task_set)) for column in full_columns)
        active_aware, active_aware_columns = price_full_universe_incremental_journey_columns(
            data,
            duals,
            max_direct_tasks=5,
            max_returned_columns=4,
            completion_bound_enabled=False,
            active_task_sets_for_harvest=active_task_sets,
        )

        self.assertEqual(active_aware["status"], "FULL_UNIVERSE_INCREMENTAL_LABEL_PRICED")
        self.assertEqual(active_aware["exact_negative_harvest_active_task_set_reference_count"], len(active_task_sets))
        self.assertEqual(active_aware["early_negative_active_task_set_reference_count"], len(active_task_sets))
        self.assertGreater(active_aware["exact_negative_harvest_non_active_task_set_count"], 0)
        self.assertIn("non_active_distinct_task_sets", active_aware["exact_negative_harvest_selection_policy"])
        self.assertTrue(
            any(tuple(sorted(column.task_set)) not in set(active_task_sets) for column in active_aware_columns)
        )
        self.assertFalse(active_aware["can_certify_no_negative"])
        self.assertFalse(active_aware["uses_true_dual_bpc_certificate"])

    def test_full_universe_incremental_negative_early_stop_is_not_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 100.0 for task_id in data.task_ids},
            fleet_limit=0.0,
        )

        full, full_columns = price_full_universe_incremental_journey_columns(
            data,
            duals,
            max_direct_tasks=5,
            max_returned_columns=2,
            completion_bound_enabled=False,
            stop_at_first_negative=True,
            active_task_sets_for_harvest=(tuple(sorted(data.task_ids[:1])),),
        )
        returned_rc = [manual_journey_reduced_cost(column, duals) for column in full_columns]

        self.assertEqual(full["status"], "FULL_UNIVERSE_INCREMENTAL_LABEL_FOUND_NEGATIVE_EARLY")
        self.assertTrue(full["early_negative_stop"])
        self.assertFalse(full["early_negative_stop_can_certify_no_negative"])
        self.assertGreaterEqual(full["early_negative_stop_trigger_count"], 1)
        self.assertTrue(full["early_negative_distinct_task_set_stop_enabled"])
        self.assertGreaterEqual(full["early_negative_distinct_task_set_count"], 1)
        self.assertGreaterEqual(full["early_negative_preferred_task_set_count"], 1)
        self.assertEqual(full["early_negative_active_task_set_reference_count"], 1)
        self.assertTrue(full["early_negative_active_preference_required"])
        self.assertEqual(full["early_negative_raw_stop_cap"], 16)
        self.assertFalse(full["pricing_complete_for_all_tasks"])
        self.assertFalse(full["pricing_complete_for_all_task_subsets"])
        self.assertFalse(full["pricing_complete_for_branch_context"])
        self.assertFalse(full["global_min_proof_complete"])
        self.assertIsNone(full["global_min_reduced_cost"])
        self.assertEqual(full["global_min_reduced_cost_source"], "partial_incremental_label_dp_found_negative")
        self.assertFalse(full["can_certify_no_negative"])
        self.assertFalse(full["uses_true_dual_bpc_certificate"])
        self.assertGreaterEqual(len(full_columns), 1)
        self.assertTrue(all(rc < -1.0e-6 for rc in returned_rc))

    def test_full_universe_incremental_pricing_is_branch_aware_and_cut_fail_closed(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_a, task_b = data.task_ids[:2]
        duals = JourneyDuals(cover={}, fleet_limit=0.0)
        branch_context = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))

        branch_payload, branch_columns = price_full_universe_incremental_journey_columns(
            data,
            duals,
            max_direct_tasks=5,
            branch_context=branch_context,
        )
        cut_payload, cut_columns = price_full_universe_incremental_journey_columns(
            data,
            JourneyDuals(cover={}, fleet_limit=0.0, cuts={"fleet_lb_active": 25.0}),
            max_direct_tasks=5,
            cut_context=CutContext((fleet_lower_bound_cut("fleet_lb_active", min_vehicles=1),)),
        )

        self.assertEqual(
            branch_payload["status"],
            "FULL_UNIVERSE_INCREMENTAL_LABEL_PRICED",
        )
        self.assertTrue(branch_payload["branch_context_active"])
        self.assertTrue(branch_payload["pricing_complete_for_branch_context"])
        self.assertTrue(branch_payload["pricing_complete_for_all_task_subsets"])
        self.assertEqual(
            branch_payload["global_min_reduced_cost_scope"],
            "branch_feasible_nonempty_task_subsets",
        )
        self.assertEqual(branch_payload["returned_column_policy"], "single_global_min_column")
        self.assertFalse(branch_payload["can_certify_no_negative"])
        self.assertGreaterEqual(len(branch_columns), 1)
        for column in branch_columns:
            self.assertTrue(journey_satisfies_branch_context(column, branch_context))
        self.assertEqual(
            cut_payload["status"],
            "SKIPPED_CUT_CONTEXT_FOR_FULL_UNIVERSE_INCREMENTAL_LABEL_PRICING",
        )
        self.assertFalse(cut_payload["pricing_complete_for_all_task_subsets"])
        self.assertFalse(cut_payload["can_certify_no_negative"])
        self.assertEqual(cut_columns, tuple())

    def test_exact_resource_core_uses_full_universe_incremental_for_branch_context(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_a, task_b = data.task_ids[:2]
        branch_context = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))

        payload, columns = run_resource_label_core(
            data,
            JourneyDuals(cover={}, fleet_limit=0.0),
            config=ResourceLabelCoreConfig(
                mode=CORE_EXACT_ELEMENTARY_FULL_SPACE,
                max_task_count=5,
                completion_bound_enabled=True,
            ),
            branch_context=branch_context,
            cut_context=CutContext(),
        )

        self.assertEqual(payload["exact_pricing_engine_preference"], "full_universe_incremental_label")
        self.assertTrue(payload["branch_context_active"])
        self.assertTrue(payload["pricing_complete_for_branch_context"])
        self.assertTrue(payload["pricing_complete_for_all_task_subsets"])
        self.assertTrue(payload["certificate_eligible_after_true_dual_audit"])
        self.assertEqual(payload["pricing_engine_role"], "exact_full_space_oracle")
        self.assertFalse(payload["candidate_search_only"])
        self.assertFalse(payload["no_column_certificate_allowed"])
        self.assertEqual(payload["ng_route_relaxation_kind"], "none")
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["uses_true_dual_bpc_certificate"])
        self.assertFalse(payload["completion_bound"]["enabled"])
        self.assertGreaterEqual(len(columns), 1)
        for column in columns:
            self.assertTrue(journey_satisfies_branch_context(column, branch_context))

    def test_exact_elementary_labeling_records_branch_feasible_coverage_scope(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_a, task_b = data.task_ids[:2]
        branch_context = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))

        payload, columns = run_bpc_labeling_pricer(
            data,
            JourneyDuals(cover={}, fleet_limit=0.0),
            config=LabelingPricingConfig(mode=EXACT_ELEMENTARY_MODE, max_exact_tasks=5),
            branch_context=branch_context,
        )

        ledger = payload["elementary_coverage_ledger"]
        self.assertTrue(ledger["branch_context_active"])
        self.assertEqual(ledger["branch_decision_count"], 1)
        self.assertEqual(
            ledger["coverage_scope"],
            "branch_feasible_nonempty_task_subsets_up_to_max_tasks_per_trip",
        )
        self.assertTrue(ledger["pricing_complete_for_branch_context"])
        self.assertTrue(ledger["coverage_complete"])
        self.assertGreater(ledger["search_region_count"], ledger["returned_column_count"])
        self.assertEqual(
            ledger["returned_column_semantics"],
            "single_best_column_from_full_space_labeling",
        )
        self.assertTrue(payload["global_remaining_rc_lb_coverage_complete"])
        for column in columns:
            self.assertTrue(journey_satisfies_branch_context(column, branch_context))

    def test_exact_elementary_labeling_requires_branch_coverage_claim_when_branch_active(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_a, task_b = data.task_ids[:2]
        branch_context = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))
        base_payload, base_columns = price_full_universe_incremental_journey_columns(
            data,
            JourneyDuals(cover={}, fleet_limit=0.0),
            max_direct_tasks=5,
            branch_context=branch_context,
        )
        incomplete_payload = dict(base_payload)
        incomplete_payload["pricing_complete_for_branch_context"] = False

        with patch(
            "lunar_ice_bpc.exact.bpc.pricing.labeling_pricer.run_resource_label_core",
            return_value=(incomplete_payload, base_columns),
        ):
            payload, _columns = run_bpc_labeling_pricer(
                data,
                JourneyDuals(cover={}, fleet_limit=0.0),
                config=LabelingPricingConfig(mode=EXACT_ELEMENTARY_MODE, max_exact_tasks=5),
                branch_context=branch_context,
            )

        ledger = payload["elementary_coverage_ledger"]
        self.assertEqual(payload["pricing_state"], PricingState.INCOMPLETE_LIMIT.value)
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["uses_true_dual_bpc_certificate"])
        self.assertFalse(ledger["pricing_complete_for_branch_context"])
        self.assertFalse(ledger["coverage_complete"])
        self.assertGreater(ledger["unsupported_region_count"], 0)

    def test_exact_elementary_labeling_requires_global_min_proof_for_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        base_payload, base_columns = price_full_universe_incremental_journey_columns(
            data,
            rmp.duals,
            max_direct_tasks=5,
            completion_bound_enabled=True,
        )
        incomplete_payload = dict(base_payload)
        incomplete_payload["global_min_proof_complete"] = False
        incomplete_payload["global_min_reduced_cost_source"] = ""

        with patch(
            "lunar_ice_bpc.exact.bpc.pricing.labeling_pricer.run_resource_label_core",
            return_value=(incomplete_payload, base_columns),
        ):
            payload, columns = run_bpc_labeling_pricer(
                data,
                rmp.duals,
                config=LabelingPricingConfig(mode=EXACT_ELEMENTARY_MODE, max_exact_tasks=5),
            )

        ledger = payload["elementary_coverage_ledger"]
        self.assertEqual(payload["pricing_state"], PricingState.INCOMPLETE_LIMIT.value)
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["uses_true_dual_bpc_certificate"])
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_INCOMPLETE)
        self.assertTrue(ledger["search_coverage_complete"])
        self.assertFalse(ledger["coverage_complete"])
        self.assertFalse(ledger["global_min_proof_complete"])
        self.assertFalse(payload["global_remaining_rc_lb_valid"])
        self.assertFalse(payload["global_remaining_rc_lb_coverage_complete"])
        self.assertGreater(payload["frontier_unsupported_region_count"], 0)
        self.assertIn("global_min_proof_incomplete", ledger["unsupported_task_count_regions"])
        self.assertEqual(columns, tuple(base_columns))

    def test_exact_elementary_branch_invalid_column_fails_manual_audit_flag(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_a, task_b = data.task_ids[:2]
        branch_context = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))
        base_payload, base_columns = price_full_universe_incremental_journey_columns(
            data,
            JourneyDuals(cover={}, fleet_limit=0.0),
            max_direct_tasks=5,
            branch_context=branch_context,
        )
        invalid_column = next(
            column for column in enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
            if column.task_set == frozenset((task_a,))
        )

        with patch(
            "lunar_ice_bpc.exact.bpc.pricing.labeling_pricer.run_resource_label_core",
            return_value=(base_payload, (*base_columns, invalid_column)),
        ):
            payload, _columns = run_bpc_labeling_pricer(
                data,
                JourneyDuals(cover={}, fleet_limit=0.0),
                config=LabelingPricingConfig(mode=EXACT_ELEMENTARY_MODE, max_exact_tasks=5),
                branch_context=branch_context,
            )

        self.assertFalse(payload["branch_context_audit_pass"])
        self.assertEqual(payload["branch_invalid_column_count"], 1)
        self.assertFalse(payload["manual_rc_audit_pass"])
        self.assertFalse(payload["true_dual_candidate_audit_pass"])
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertNotEqual(payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE)

    def test_exact_elementary_negative_early_stop_is_found_negative_only(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(
            cover={task_id: 100.0 for task_id in data.task_ids},
            fleet_limit=0.0,
        )

        payload, columns = run_bpc_labeling_pricer(
            data,
            duals,
            config=LabelingPricingConfig(
                mode=EXACT_ELEMENTARY_MODE,
                max_exact_tasks=5,
                exact_negative_harvest_target=2,
                completion_bound_enabled=False,
                stop_at_first_negative=True,
            ),
        )

        self.assertEqual(payload["pricing_state"], PricingState.FOUND_NEGATIVE.value)
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_FOUND_NEGATIVE)
        self.assertTrue(payload["early_negative_stop"])
        self.assertFalse(payload["pricing_complete_for_all_task_subsets"])
        self.assertFalse(payload["global_min_proof_complete"])
        self.assertFalse(payload["global_remaining_rc_lb_valid"])
        self.assertFalse(payload["global_remaining_rc_lb_coverage_complete"])
        self.assertGreater(payload["frontier_unsupported_region_count"], 0)
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["uses_true_dual_bpc_certificate"])
        self.assertTrue(payload["manual_rc_audit_pass"])
        self.assertTrue(payload["pricing_rc_audit_pass"])
        self.assertGreaterEqual(len(columns), 1)
        self.assertTrue(
            all(manual_journey_reduced_cost(column, duals) < -1.0e-6 for column in columns)
        )

    def test_exact_elementary_labeling_can_certify_small_full_space(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        self.assertEqual(rmp.status, "RESTRICTED_RMP_OPTIMAL")

        payload, columns = run_bpc_labeling_pricer(
            data,
            rmp.duals,
            config=LabelingPricingConfig(mode=EXACT_ELEMENTARY_MODE, max_exact_tasks=5),
        )

        expected, expected_columns = price_exhaustive_direct_journey_columns(
            data,
            rmp.duals,
            max_direct_tasks=5,
            completion_bound_enabled=False,
        )
        expected_best = min(manual_journey_reduced_cost(column, rmp.duals) for column in expected_columns)
        self.assertEqual(payload["schema_version"], "lunar_ice_bpc.bpc_labeling_pricer.v1")
        self.assertEqual(payload["resource_label_core_mode"], "exact_elementary_full_space")
        self.assertEqual(payload["resource_label_algorithm"], "elementary_resource_labeling_exhaustive_task_subsets")
        self.assertEqual(payload["pricing_coverage_algorithm"], "full_universe_incremental_label")
        self.assertEqual(payload["exact_pricing_engine_preference"], "full_universe_incremental_label")
        self.assertTrue(payload["full_universe_incremental_label"])
        self.assertEqual(
            payload["label_expansion_order_policy"],
            "topological_task_count_then_best_bound_mask_priority",
        )
        self.assertTrue(payload["label_best_bound_order_enabled"])
        self.assertGreater(payload["label_queue_push_count"], 0)
        self.assertGreaterEqual(payload["label_queue_max_pending_count"], 1)
        self.assertIn("energy", payload["resource_dimensions"])
        self.assertEqual(payload["elementarity_policy"], "elementary_full_space")
        self.assertEqual(payload["pricing_state"], PricingState.CERTIFIED_NO_NEGATIVE.value)
        self.assertTrue(payload["can_certify_no_negative"])
        self.assertTrue(payload["uses_true_dual_bpc_certificate"])
        self.assertFalse(payload["dual_stabilization_requested"])
        self.assertEqual(payload["dual_stabilization_scope"], "worker_candidate_search_only")
        self.assertFalse(payload["dual_stabilization_used_for_official_certificate"])
        self.assertFalse(payload["dual_stabilization_ignored_for_exact_mode"])
        self.assertEqual(payload["official_pricing_dual_source"], "current_true_rmp_dual")
        self.assertFalse(payload["stabilized_dual_no_column_can_certify"])
        self.assertEqual(payload["status_semantics_contract_version"], STATUS_SEMANTICS_CONTRACT_VERSION)
        self.assertTrue(payload["certificate_semantics_pass"])
        self.assertEqual(payload["certificate_semantics_issues"], [])
        self.assertFalse(payload["worker_no_column_can_certify"])
        self.assertFalse(payload["limit_result_can_certify"])
        self.assertTrue(payload["worker_mode_certificate_allowed"])
        self.assertEqual(payload["only_certifying_pricing_state"], PricingState.CERTIFIED_NO_NEGATIVE.value)
        self.assertIn(PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE, payload["certifying_pricing_proof_kinds"])
        self.assertTrue(payload["pricing_rc_audit_pass"])
        self.assertTrue(payload["pricing_complete_for_all_task_subsets"])
        self.assertTrue(payload["cut_aware_signature_used"])
        self.assertFalse(payload["cut_aware_signature_cut_context_active"])
        self.assertEqual(payload["cut_aware_signature_cut_hash_column_count"], 0)
        self.assertTrue(payload["completion_bound"]["enabled"])
        self.assertFalse(payload["completion_bound"]["can_certify_no_negative"])
        self.assertTrue(payload["completion_bound_certificate_safe"])
        self.assertFalse(
            payload["completion_bound_certificate_support"][
                "completion_bound_can_certify_no_negative"
            ]
        )
        self.assertGreater(payload["completion_bound"]["evaluated_label_count"], 0)
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE)
        self.assertTrue(payload["global_remaining_rc_lb_valid"])
        self.assertTrue(payload["global_remaining_rc_lb_coverage_complete"])
        self.assertEqual(payload["frontier_unsupported_region_count"], 0)
        ledger = payload["elementary_coverage_ledger"]
        self.assertTrue(ledger["coverage_complete"])
        self.assertTrue(ledger["search_coverage_complete"])
        self.assertEqual(ledger["unsupported_region_count"], 0)
        self.assertEqual(ledger["expected_region_count"], 31)
        self.assertEqual(ledger["observed_region_count"], 31)
        self.assertEqual(ledger["search_region_count"], 31)
        self.assertEqual(
            ledger["search_region_count_semantics"],
            "pricing search coverage regions; not necessarily returned columns",
        )
        self.assertEqual(ledger["returned_column_count"], payload["true_audited_column_count"])
        self.assertEqual(ledger["returned_column_count"], 1)
        self.assertEqual(
            ledger["returned_column_semantics"],
            "single_best_column_from_full_space_labeling",
        )
        self.assertEqual(ledger["returned_column_policy"], "single_global_min_column")
        self.assertFalse(ledger["returned_columns_are_complete_universe"])
        self.assertTrue(ledger["single_global_min_column_proof"])
        self.assertTrue(ledger["global_min_proof_complete"])
        self.assertEqual(ledger["global_min_reduced_cost_source"], "full_universe_incremental_label_dp")
        self.assertEqual(ledger["global_min_reduced_cost_scope"], "all_nonempty_task_subsets")
        self.assertTrue(ledger["global_min_proof_requires_true_dual_reaudit"])
        self.assertEqual(
            ledger["global_remaining_rc_lb_source"],
            "global_min_column_reaudited_under_true_dual",
        )
        self.assertEqual(ledger["true_dual_audit_scope"], "all columns returned by pricing engine")
        expected_by_task_count = {"1": 5, "2": 10, "3": 10, "4": 5, "5": 1}
        self.assertEqual(ledger["expected_region_count_by_task_count"], expected_by_task_count)
        self.assertEqual(ledger["observed_region_count_by_task_count"], expected_by_task_count)
        self.assertEqual(
            ledger["coverage_complete_by_task_count"],
            {key: True for key in expected_by_task_count},
        )
        self.assertEqual(ledger["unsupported_task_count_regions"], [])
        self.assertEqual(payload["frontier_region_count"], 5)
        self.assertEqual(payload["frontier_unsupported_task_count_regions"], [])
        self.assertEqual(
            expected["exhaustive_candidate_set_count_by_task_count"],
            expected_by_task_count,
        )
        self.assertEqual(expected["priced_candidate_set_count_by_task_count"], expected_by_task_count)
        self.assertAlmostEqual(payload["true_best_reduced_cost"], expected_best, places=6)
        self.assertAlmostEqual(payload["pricing_best_reduced_cost"], expected["best_reduced_cost"], places=6)
        self.assertGreater(len(columns), 0)

    def test_exact_elementary_labeling_ignores_requested_dual_stabilization_for_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        self.assertEqual(rmp.status, "RESTRICTED_RMP_OPTIMAL")

        payload, _columns = run_bpc_labeling_pricer(
            data,
            rmp.duals,
            config=LabelingPricingConfig(
                mode=EXACT_ELEMENTARY_MODE,
                max_exact_tasks=5,
                dual_stabilization_enabled=True,
                dual_stabilization_alpha=0.1,
            ),
            dual_history=(JourneyDuals(cover={task_id: -50.0 for task_id in data.task_ids}),),
        )

        self.assertEqual(payload["pricing_state"], PricingState.CERTIFIED_NO_NEGATIVE.value)
        self.assertTrue(payload["can_certify_no_negative"])
        self.assertTrue(payload["uses_true_dual_bpc_certificate"])
        self.assertTrue(payload["dual_stabilization_requested"])
        self.assertTrue(payload["dual_stabilization_ignored_for_exact_mode"])
        self.assertFalse(payload["dual_stabilization_used_for_official_certificate"])
        self.assertEqual(payload["official_pricing_dual_source"], "current_true_rmp_dual")
        self.assertFalse(payload["stabilized_dual_no_column_can_certify"])
        self.assertTrue(payload["certificate_semantics_pass"])
        self.assertEqual(payload["certificate_semantics_issues"], [])

    def test_exact_elementary_labeling_fails_closed_when_completion_bound_claims_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        base_payload, base_columns = price_full_universe_incremental_journey_columns(
            data,
            rmp.duals,
            max_direct_tasks=5,
            completion_bound_enabled=True,
        )
        unsafe_payload = dict(base_payload)
        unsafe_completion_bound = dict(unsafe_payload["completion_bound"])
        unsafe_completion_bound["can_certify_no_negative"] = True
        unsafe_payload["completion_bound"] = unsafe_completion_bound

        with patch(
            "lunar_ice_bpc.exact.bpc.pricing.labeling_pricer.run_resource_label_core",
            return_value=(unsafe_payload, base_columns),
        ):
            payload, columns = run_bpc_labeling_pricer(
                data,
                rmp.duals,
                config=LabelingPricingConfig(mode=EXACT_ELEMENTARY_MODE, max_exact_tasks=5),
            )

        self.assertEqual(payload["pricing_state"], PricingState.INCOMPLETE_LIMIT.value)
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["uses_true_dual_bpc_certificate"])
        self.assertFalse(payload["completion_bound_certificate_safe"])
        self.assertTrue(
            payload["completion_bound_certificate_support"][
                "completion_bound_can_certify_no_negative"
            ]
        )
        self.assertFalse(payload["global_remaining_rc_lb_valid"])
        self.assertIn(
            "completion_bound_certificate_unsafe",
            payload["elementary_coverage_ledger"]["unsupported_task_count_regions"],
        )
        self.assertEqual(columns, tuple(base_columns))

    def test_exact_elementary_completion_bound_on_off_preserves_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)

        pruned, _ = run_bpc_labeling_pricer(
            data,
            rmp.duals,
            config=LabelingPricingConfig(
                mode=EXACT_ELEMENTARY_MODE,
                max_exact_tasks=5,
                completion_bound_enabled=True,
            ),
        )
        unpruned, _ = run_bpc_labeling_pricer(
            data,
            rmp.duals,
            config=LabelingPricingConfig(
                mode=EXACT_ELEMENTARY_MODE,
                max_exact_tasks=5,
                completion_bound_enabled=False,
            ),
        )

        self.assertEqual(pruned["pricing_state"], PricingState.CERTIFIED_NO_NEGATIVE.value)
        self.assertEqual(unpruned["pricing_state"], PricingState.CERTIFIED_NO_NEGATIVE.value)
        self.assertEqual(pruned["pricing_best_reduced_cost"], unpruned["pricing_best_reduced_cost"])
        self.assertEqual(pruned["true_best_reduced_cost"], unpruned["true_best_reduced_cost"])
        self.assertTrue(pruned["completion_bound"]["enabled"])
        self.assertFalse(unpruned["completion_bound"]["enabled"])
        self.assertFalse(pruned["completion_bound"]["can_certify_no_negative"])
        self.assertTrue(pruned["uses_true_dual_bpc_certificate"])
        self.assertTrue(unpruned["uses_true_dual_bpc_certificate"])

    def test_exact_elementary_wall_time_limit_fails_closed_without_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={}, fleet_limit=0.0)

        payload, columns = run_bpc_labeling_pricer(
            data,
            duals,
            config=LabelingPricingConfig(
                mode=EXACT_ELEMENTARY_MODE,
                max_exact_tasks=5,
                wall_time_limit_sec=0.0,
            ),
        )

        self.assertEqual(payload["pricing_state"], PricingState.INCOMPLETE_LIMIT.value)
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_INCOMPLETE)
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["uses_true_dual_bpc_certificate"])
        self.assertFalse(payload["pricing_complete_for_all_task_subsets"])
        self.assertFalse(payload["global_remaining_rc_lb_valid"])
        self.assertGreater(payload["frontier_unsupported_region_count"], 0)
        ledger = payload["elementary_coverage_ledger"]
        expected_by_task_count = {"1": 5, "2": 10, "3": 10, "4": 5, "5": 1}
        self.assertEqual(ledger["expected_region_count_by_task_count"], expected_by_task_count)
        self.assertEqual(ledger["observed_region_count_by_task_count"], {})
        self.assertEqual(
            ledger["coverage_complete_by_task_count"],
            {key: False for key in expected_by_task_count},
        )
        self.assertEqual(ledger["unsupported_task_count_regions"], ["1", "2", "3", "4", "5"])
        self.assertEqual(
            payload["frontier_unsupported_task_count_regions"],
            ["1", "2", "3", "4", "5"],
        )
        self.assertEqual(ledger["timeout_stage"], "incremental_journey_label_dp")
        self.assertIn("TIME_LIMIT", payload["status"])
        self.assertEqual(columns, tuple())

    def test_full_universe_incremental_timeout_can_return_partial_negatives_without_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 10.0 for task_id in data.task_ids}, fleet_limit=0.0)
        original = journey_pricing_module._best_direct_label_incremental

        def fake_best_direct_label_incremental(*args, **kwargs):
            safe_kwargs = dict(kwargs)
            safe_kwargs["deadline"] = None
            label, stats = original(*args, **safe_kwargs)
            raise DirectBaselineTimeLimitExceeded(
                stage="incremental_candidate_extension",
                generated_sortie_count=int(stats.get("sortie_attempt_count") or 0),
                route_template_count=int(stats.get("feasible_sortie_template_count") or 0),
                pareto_label_count=int(stats.get("pareto_label_count") or 0),
                partial_label=label,
                partial_stats=stats,
            )

        with patch.object(
            journey_pricing_module,
            "_best_direct_label_incremental",
            side_effect=fake_best_direct_label_incremental,
        ):
            payload, columns = price_full_universe_incremental_journey_columns(
                data,
                duals,
                max_direct_tasks=5,
                max_returned_columns=3,
            )

        self.assertIn("TIME_LIMIT", payload["status"])
        self.assertFalse(payload["pricing_complete_for_all_task_subsets"])
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["uses_true_dual_bpc_certificate"])
        self.assertTrue(payload["partial_timeout_negative_harvest_enabled"])
        self.assertGreater(payload["partial_timeout_returned_column_count"], 0)
        self.assertGreater(len(columns), 0)
        self.assertTrue(
            any(manual_journey_reduced_cost(column, duals) < -1.0e-6 for column in columns)
        )

    def test_exact_elementary_found_negative_is_not_no_negative_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 10.0 for task_id in data.task_ids}, fleet_limit=0.0)

        payload, columns = run_bpc_labeling_pricer(
            data,
            duals,
            config=LabelingPricingConfig(mode=EXACT_ELEMENTARY_MODE, max_exact_tasks=5),
        )

        self.assertEqual(payload["pricing_state"], PricingState.FOUND_NEGATIVE.value)
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_FOUND_NEGATIVE)
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["uses_true_dual_bpc_certificate"])
        self.assertTrue(payload["global_remaining_rc_lb_valid"])
        self.assertTrue(payload["global_remaining_rc_lb_coverage_complete"])
        self.assertEqual(payload["frontier_unsupported_region_count"], 0)
        self.assertGreater(payload["true_negative_column_count"], 0)
        self.assertGreater(len(columns), 0)

    def test_exact_elementary_opt_in_negative_harvest_preserves_global_min_audit(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: 100.0 for task_id in data.task_ids}, fleet_limit=0.0)

        payload, columns = run_bpc_labeling_pricer(
            data,
            duals,
            config=LabelingPricingConfig(
                mode=EXACT_ELEMENTARY_MODE,
                max_exact_tasks=5,
                exact_negative_harvest_target=4,
                completion_bound_enabled=False,
            ),
        )

        returned_rc = [manual_journey_reduced_cost(column, duals) for column in columns]
        self.assertEqual(payload["pricing_state"], PricingState.FOUND_NEGATIVE.value)
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_FOUND_NEGATIVE)
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["uses_true_dual_bpc_certificate"])
        self.assertEqual(payload["exact_negative_harvest_target"], 4)
        self.assertGreater(payload["exact_negative_harvest_selected_count"], 1)
        self.assertEqual(payload["returned_column_count"], len(columns))
        self.assertEqual(payload["true_audited_column_count"], len(columns))
        self.assertTrue(payload["pricing_rc_audit_pass"])
        self.assertTrue(payload["global_remaining_rc_lb_valid"])
        self.assertTrue(payload["global_remaining_rc_lb_coverage_complete"])
        self.assertAlmostEqual(payload["pricing_best_reduced_cost"], min(returned_rc), places=6)
        self.assertAlmostEqual(payload["true_best_reduced_cost"], min(returned_rc), places=6)
        ledger = payload["elementary_coverage_ledger"]
        self.assertTrue(ledger["coverage_complete"])
        self.assertEqual(
            ledger["returned_column_policy"],
            "global_min_plus_diverse_negative_harvest",
        )
        self.assertFalse(ledger["returned_columns_are_complete_universe"])

    def test_relaxed_ng_route_no_column_is_uncertified(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        duals = JourneyDuals(cover={task_id: -100.0 for task_id in data.task_ids}, fleet_limit=0.0)

        payload, columns = run_bpc_labeling_pricer(
            data,
            duals,
            config=LabelingPricingConfig(
                mode=RELAXED_NG_ROUTE_MODE,
                max_label_task_count=3,
                max_candidate_sets=8,
                harvest_target=4,
            ),
        )

        self.assertEqual(payload["pricing_state"], PricingState.LOCAL_NO_COLUMN_UNCERTIFIED.value)
        self.assertEqual(payload["resource_label_core_mode"], "relaxed_ng_route_worker")
        self.assertEqual(payload["resource_label_algorithm"], "ng_route_relaxed_resource_labeling")
        self.assertEqual(payload["pricing_engine_role"], "worker_candidate_search")
        self.assertTrue(payload["candidate_search_only"])
        self.assertFalse(payload["relaxed_candidate_search_can_certify_no_negative"])
        self.assertFalse(payload["no_column_certificate_allowed"])
        self.assertEqual(payload["ng_route_relaxation_kind"], "seed_portfolio_task_set_neighborhood")
        self.assertFalse(payload["ng_route_relaxation_is_certificate_relaxation"])
        self.assertFalse(payload["relaxed_route_elementarity_proof_supported"])
        self.assertEqual(payload["dssr_refinement_status"], "hidden_negative_seed_refinement_only")
        self.assertTrue(payload["exact_final_proof_required_after_worker"])
        self.assertEqual(payload["exact_final_proof_expected_mode"], "exact_elementary_full_space")
        self.assertIn("time_window", payload["resource_dimensions"])
        self.assertEqual(payload["elementarity_policy"], "selected_elementary_candidate_sets_ng_route_worker")
        self.assertEqual(payload["ng_neighborhood_size"], 8)
        self.assertEqual(payload["ng_neighborhood_sizes"], [3, 5, 8])
        self.assertEqual(payload["ng_neighborhood_stage_count"], 3)
        self.assertIn("3", payload["ng_seed_task_set_count_by_size"])
        self.assertIn("5", payload["ng_seed_task_set_count_by_size"])
        self.assertIn("8", payload["ng_seed_task_set_count_by_size"])
        self.assertGreater(payload["ng_seed_task_set_count"], 0)
        self.assertGreater(payload["resource_extension_seed_task_set_count"], 0)
        self.assertEqual(
            payload["resource_extension_proxy_profiles"],
            list(_RESOURCE_EXTENSION_PROXY_PROFILES),
        )
        self.assertEqual(
            payload["resource_extension_proxy_profile_count"],
            len(_RESOURCE_EXTENSION_PROXY_PROFILES),
        )
        self.assertGreaterEqual(payload["merged_seed_task_set_count"], payload["ng_seed_task_set_count"])
        self.assertGreater(payload["active_seed_task_set_count"], 0)
        self.assertEqual(
            payload["active_seed_selection_policy"],
            "protected_refinement_then_source_task_count_coverage_then_low_overlap_fill",
        )
        self.assertEqual(payload["protected_refinement_seed_task_set_count"], 0)
        self.assertEqual(payload["active_protected_refinement_seed_task_set_count"], 0)
        self.assertEqual(payload["protected_refinement_seed_task_set_count_by_size"], {})
        self.assertEqual(payload["protected_refinement_seed_budget_truncated_count"], 0)
        self.assertTrue(payload["active_seed_task_set_count_by_size"])
        self.assertGreater(payload["active_ng_seed_task_set_count"], 0)
        self.assertGreater(payload["active_resource_extension_seed_task_set_count"], 0)
        self.assertIn("resource_extension", payload["active_seed_task_set_source_counts"])
        self.assertIn("direct_candidate", payload["candidate_seed_source_precedence"])
        self.assertEqual(payload["active_input_seed_task_set_count"], 0)
        self.assertTrue(payload["candidate_search_dual_matches_true_dual"])
        self.assertTrue(payload["candidate_search_rc_recomputed_under_true_dual"])
        self.assertEqual(payload["candidate_search_negative_column_count"], 0)
        self.assertEqual(payload["harvest_selected_seed_source_counts"], {})
        self.assertEqual(payload["harvest_candidate_negative_count"], 0)
        self.assertEqual(payload["harvest_selected_count"], 0)
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["uses_true_dual_bpc_certificate"])
        self.assertTrue(payload["no_column_uncertified"])
        self.assertFalse(payload["pricing_complete_for_all_task_subsets"])
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_RELAXED_WORKER_UNCERTIFIED)
        self.assertFalse(payload["global_remaining_rc_lb_valid"])
        self.assertFalse(payload["global_remaining_rc_lb_coverage_complete"])
        self.assertGreater(payload["frontier_unsupported_region_count"], 0)
        self.assertEqual(columns, tuple())

    def test_stabilized_worker_columns_are_reaudited_with_true_dual(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        true_duals = JourneyDuals(cover={task_id: 10.0 for task_id in data.task_ids}, fleet_limit=0.0)
        old_duals = JourneyDuals(cover={task_id: -50.0 for task_id in data.task_ids}, fleet_limit=0.0)

        payload, columns = run_bpc_labeling_pricer(
            data,
            true_duals,
            config=LabelingPricingConfig(
                mode=RELAXED_NG_ROUTE_MODE,
                max_label_task_count=3,
                max_candidate_sets=16,
                harvest_target=4,
                dual_stabilization_enabled=True,
                dual_stabilization_alpha=0.7,
            ),
            dual_history=(old_duals, true_duals),
        )

        self.assertTrue(payload["worker_dual_stabilization_enabled"])
        self.assertTrue(payload["worker_dual_used_for_candidate_search"])
        self.assertFalse(payload["candidate_search_dual_matches_true_dual"])
        self.assertTrue(payload["candidate_search_rc_recomputed_under_true_dual"])
        self.assertEqual(payload["pricing_state"], PricingState.FOUND_NEGATIVE.value)
        self.assertGreater(len(columns), 0)
        self.assertGreater(payload["true_selected_negative_count"], 0)
        self.assertGreaterEqual(payload["candidate_search_negative_column_count"], 0)
        self.assertGreaterEqual(payload["candidate_search_negative_true_negative_count"], 0)
        self.assertGreaterEqual(payload["candidate_search_negative_true_nonnegative_count"], 0)
        self.assertGreaterEqual(payload["true_negative_candidate_search_nonnegative_count"], 0)
        for column in columns:
            self.assertLess(manual_journey_reduced_cost(column, true_duals), -1.0e-6)

    def test_relaxed_worker_support_continuation_seeds_are_worker_only(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_ids = tuple(data.task_ids)
        support = (task_ids[:3],)
        duals = JourneyDuals(
            cover={task_id: 12.0 - index for index, task_id in enumerate(task_ids)},
            fleet_limit=0.0,
        )

        payload, _columns = run_bpc_labeling_pricer(
            data,
            duals,
            config=LabelingPricingConfig(
                mode=RELAXED_NG_ROUTE_MODE,
                max_label_task_count=3,
                max_candidate_sets=24,
                harvest_target=4,
                support_continuation_seed_enabled=True,
                support_continuation_max_seed_sets=12,
                support_continuation_max_neighbors=2,
                support_continuation_protected_seed_count=3,
            ),
            support_task_sets=support,
        )

        self.assertGreater(payload["support_continuation_seed_count"], 0)
        self.assertGreater(payload["support_continuation_active_seed_count"], 0)
        self.assertIn("support_continuation", payload["active_seed_task_set_source_counts"])
        self.assertIn("support_continuation", payload["priced_candidate_task_set_source_counts"])
        self.assertEqual(
            payload["support_continuation_seed_policy"],
            "rmp_support_add_drop_swap_by_worker_dual_worker_only_with_protected_front_budget",
        )
        self.assertEqual(payload["support_continuation_protected_seed_count"], 3)
        self.assertGreater(payload["support_continuation_active_protected_seed_count"], 0)
        self.assertFalse(payload["support_continuation_can_certify_no_negative"])
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_RELAXED_WORKER_UNCERTIFIED)
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["uses_true_dual_bpc_certificate"])
        self.assertTrue(payload["candidate_search_rc_recomputed_under_true_dual"])

    def test_relaxed_worker_projects_large_support_continuation_under_task_cap(self) -> None:
        instance = generate_instance(10, seed=629002, index=1)
        data = load_lunar_ice_data(instance)
        task_ids = tuple(data.task_ids)
        support = (task_ids[:5],)
        duals = JourneyDuals(
            cover={task_id: 20.0 - index for index, task_id in enumerate(task_ids)},
            fleet_limit=0.0,
        )

        payload, _columns = run_bpc_labeling_pricer(
            data,
            duals,
            config=LabelingPricingConfig(
                mode=RELAXED_NG_ROUTE_MODE,
                max_label_task_count=3,
                max_candidate_sets=12,
                harvest_target=4,
                support_continuation_seed_enabled=True,
                support_continuation_max_seed_sets=10,
                support_continuation_max_neighbors=2,
                support_continuation_protected_seed_count=4,
            ),
            support_task_sets=support,
        )

        support_rows = [
            row
            for row in payload["active_seed_task_set_sources"]
            if "support_continuation" in set(row.get("sources") or ())
        ]
        self.assertGreater(payload["support_continuation_seed_count"], 0)
        self.assertGreater(payload["support_continuation_active_seed_count"], 0)
        self.assertGreater(len(support_rows), 0)
        self.assertTrue(all(len(row["task_set"]) <= 3 for row in support_rows))
        self.assertFalse(payload["support_continuation_can_certify_no_negative"])
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_RELAXED_WORKER_UNCERTIFIED)

    def test_labeling_pricer_final_judge_opt_in_certifies_small_full_space(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        context = ReducedCostContext(
            task_duals=rmp.duals.cover,
            fleet_dual=rmp.duals.fleet_limit,
            cut_duals=rmp.duals.cuts or {},
            dual_fingerprint="labeling-test",
            rmp_iteration_id="root-1",
        )

        env = {
            **os.environ,
            "LUNAR_ICE_LABELING_FINAL_JUDGE": "1",
            "LUNAR_ICE_LABELING_FINAL_JUDGE_MAX_TASKS": "5",
        }
        with patch.dict(os.environ, env, clear=True):
            result = run_true_dual_root_final_judge(data, context, max_direct_tasks=5)

        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)
        self.assertTrue(result.pricing_payload["labeling_final_judge_enabled"])
        self.assertEqual(result.pricing_payload["status"], "LABELING_FINAL_JUDGE_PRICED")
        self.assertEqual(result.pricing_payload["exact_status"], "BPC_NO_NEGATIVE_CERTIFIED")
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE)
        self.assertTrue(result.pricing_payload["can_certify_no_negative"])
        self.assertTrue(result.pricing_payload["uses_true_dual_bpc_certificate"])
        self.assertTrue(result.pricing_payload["completion_bound_pruning_enabled"])
        self.assertFalse(result.pricing_payload["completion_bound"]["can_certify_no_negative"])
        self.assertEqual(result.pricing_payload["dual_fingerprint"], "labeling-test")
        self.assertEqual(result.pricing_payload["labeling_final_judge_selection_reason"], "environment_enabled")
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_certificate_role"],
            "true_dual_exact_elementary_final_proof",
        )
        self.assertTrue(result.pricing_payload["labeling_final_judge_can_certify"])
        self.assertEqual(result.pricing_payload["labeling_final_judge_downgrade_reason"], "")
        self.assertEqual(result.pricing_payload["labeling_final_judge_task_count"], 5)
        self.assertTrue(result.pricing_payload["labeling_final_judge_early_negative_stop_enabled"])
        self.assertFalse(
            result.pricing_payload["labeling_final_judge_early_negative_stop_can_certify_no_negative"]
        )
        self.assertFalse(result.pricing_payload["early_negative_stop"])

    def test_labeling_pricer_final_judge_explicit_opt_in_overrides_env(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        context = ReducedCostContext(
            task_duals=rmp.duals.cover,
            fleet_dual=rmp.duals.fleet_limit,
            cut_duals=rmp.duals.cuts or {},
            dual_fingerprint="labeling-explicit-test",
            rmp_iteration_id="root-1",
        )

        env = {
            **os.environ,
            "LUNAR_ICE_LABELING_FINAL_JUDGE": "0",
            "LUNAR_ICE_LABELING_FINAL_JUDGE_MAX_TASKS": "1",
        }
        with patch.dict(os.environ, env, clear=True):
            result = run_true_dual_root_final_judge(
                data,
                context,
                max_direct_tasks=5,
                labeling_final_judge_enabled=True,
                labeling_final_judge_max_exact_tasks=5,
            )

        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)
        self.assertTrue(result.pricing_payload["labeling_final_judge_enabled"])
        self.assertEqual(result.pricing_payload["labeling_final_judge_opt_in_source"], "explicit_parameter")
        self.assertEqual(result.pricing_payload["labeling_final_judge_max_exact_tasks"], 5)
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_max_exact_tasks_source"],
            "explicit_parameter",
        )
        self.assertEqual(result.pricing_payload["labeling_final_judge_selection_reason"], "explicit_enabled")
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_certificate_role"],
            "true_dual_exact_elementary_final_proof",
        )
        self.assertTrue(result.pricing_payload["labeling_final_judge_can_certify"])
        self.assertEqual(result.pricing_payload["labeling_final_judge_downgrade_reason"], "")
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE)
        self.assertTrue(result.pricing_payload["uses_true_dual_bpc_certificate"])

    def test_labeling_pricer_final_judge_opt_in_harvests_multiple_true_negative_columns(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        context = ReducedCostContext(
            task_duals={task_id: 100.0 for task_id in data.task_ids},
            fleet_dual=0.0,
            cut_duals={},
            dual_fingerprint="labeling-harvest-test",
            rmp_iteration_id="root-1",
        )

        result = run_true_dual_root_final_judge(
            data,
            context,
            max_direct_tasks=5,
            labeling_final_judge_enabled=True,
            labeling_final_judge_max_exact_tasks=5,
            labeling_final_judge_exact_harvest_target=4,
        )

        payload = result.pricing_payload
        self.assertEqual(result.pricing_state, PricingState.FOUND_NEGATIVE)
        self.assertEqual(payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_FOUND_NEGATIVE)
        self.assertFalse(payload["can_certify_no_negative"])
        self.assertFalse(payload["uses_true_dual_bpc_certificate"])
        self.assertEqual(payload["labeling_final_judge_exact_harvest_target"], 4)
        self.assertEqual(payload["labeling_final_judge_exact_harvest_target_source"], "explicit_parameter")
        self.assertTrue(payload["labeling_final_judge_early_negative_stop_enabled"])
        self.assertFalse(payload["labeling_final_judge_early_negative_stop_can_certify_no_negative"])
        self.assertTrue(payload["early_negative_stop"])
        self.assertFalse(payload["pricing_complete_for_all_task_subsets"])
        self.assertFalse(payload["global_min_proof_complete"])
        self.assertFalse(payload["global_remaining_rc_lb_valid"])
        self.assertEqual(payload["exact_negative_harvest_target"], 4)
        self.assertGreater(payload["exact_negative_harvest_candidate_count"], 1)
        self.assertGreater(payload["exact_negative_harvest_selected_count"], 1)
        self.assertEqual(payload["returned_column_count"], len(result.negative_columns))
        self.assertEqual(len(result.negative_columns), 4)
        self.assertTrue(
            all(
                manual_journey_reduced_cost(column, JourneyDuals(cover=context.task_duals, fleet_limit=0.0))
                < -1.0e-6
                for column in result.negative_columns
            )
        )

    def test_labeling_pricer_final_judge_auto_selects_exact_small_space(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        context = ReducedCostContext(
            task_duals=rmp.duals.cover,
            fleet_dual=rmp.duals.fleet_limit,
            cut_duals=rmp.duals.cuts or {},
            dual_fingerprint="labeling-auto-test",
            rmp_iteration_id="root-1",
        )

        env = {
            **os.environ,
            "LUNAR_ICE_LABELING_FINAL_JUDGE": "auto",
            "LUNAR_ICE_LABELING_FINAL_JUDGE_MAX_TASKS": "5",
        }
        with patch.dict(os.environ, env, clear=True):
            result = run_true_dual_root_final_judge(data, context, max_direct_tasks=5)

        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)
        self.assertEqual(result.pricing_payload["status"], "LABELING_FINAL_JUDGE_PRICED")
        self.assertEqual(result.pricing_payload["pricing_coverage_algorithm"], "full_universe_incremental_label")
        self.assertTrue(result.pricing_payload["full_universe_incremental_label"])
        self.assertTrue(result.pricing_payload["labeling_final_judge_enabled"])
        self.assertTrue(result.pricing_payload["labeling_final_judge_auto_mode"])
        self.assertTrue(result.pricing_payload["labeling_final_judge_auto_selected"])
        self.assertEqual(result.pricing_payload["labeling_final_judge_auto_skip_reason"], "")
        self.assertEqual(result.pricing_payload["labeling_final_judge_opt_in_source"], "environment_auto")
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_selection_reason"],
            "auto_task_count_within_max_exact_tasks",
        )
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_certificate_role"],
            "true_dual_exact_elementary_final_proof",
        )
        self.assertTrue(result.pricing_payload["labeling_final_judge_can_certify"])
        self.assertEqual(result.pricing_payload["labeling_final_judge_downgrade_reason"], "")
        self.assertEqual(result.pricing_payload["labeling_final_judge_task_count"], 5)
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE)
        self.assertTrue(result.pricing_payload["uses_true_dual_bpc_certificate"])
        self.assertTrue(result.pricing_payload["labeling_final_judge_two_phase_enabled"])
        self.assertIn("labeling_final_judge_proof_pass_attempted", result.pricing_payload)
        self.assertFalse(
            result.pricing_payload["labeling_final_judge_early_negative_stop_can_certify_no_negative"]
        )

    def test_labeling_pricer_final_judge_auto_skips_when_task_count_exceeds_limit(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        context = ReducedCostContext(
            task_duals=rmp.duals.cover,
            fleet_dual=rmp.duals.fleet_limit,
            cut_duals=rmp.duals.cuts or {},
            dual_fingerprint="labeling-auto-skip-test",
            rmp_iteration_id="root-1",
        )

        env = {
            **os.environ,
            "LUNAR_ICE_LABELING_FINAL_JUDGE": "auto",
            "LUNAR_ICE_LABELING_FINAL_JUDGE_MAX_TASKS": "1",
        }
        with patch.dict(os.environ, env, clear=True):
            result = run_true_dual_root_final_judge(data, context, max_direct_tasks=5)

        self.assertNotEqual(result.pricing_payload.get("status"), "LABELING_FINAL_JUDGE_PRICED")
        self.assertFalse(result.pricing_payload["labeling_final_judge_enabled"])
        self.assertTrue(result.pricing_payload["labeling_final_judge_auto_mode"])
        self.assertFalse(result.pricing_payload["labeling_final_judge_auto_selected"])
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_auto_skip_reason"],
            "task_count_exceeds_max_exact_tasks",
        )
        self.assertEqual(result.pricing_payload["labeling_final_judge_opt_in_source"], "environment_auto")
        self.assertEqual(result.pricing_payload["labeling_final_judge_max_exact_tasks"], 1)
        self.assertEqual(result.pricing_payload["labeling_final_judge_task_count"], 5)
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_selection_reason"],
            "task_count_exceeds_max_exact_tasks",
        )
        self.assertEqual(result.pricing_payload["labeling_final_judge_certificate_role"], "not_selected")
        self.assertFalse(result.pricing_payload["labeling_final_judge_can_certify"])
        self.assertEqual(result.pricing_payload["labeling_final_judge_downgrade_reason"], "")

    def test_labeling_final_judge_runs_proof_pass_after_empty_harvest(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        context = ReducedCostContext(
            task_duals=rmp.duals.cover,
            fleet_dual=rmp.duals.fleet_limit,
            cut_duals=rmp.duals.cuts or {},
            dual_fingerprint="labeling-proof-pass-test",
            rmp_iteration_id="root-1",
        )
        proof_column = min(
            universe.columns,
            key=lambda column: manual_journey_reduced_cost(column, rmp.duals),
        )
        proof_rc = manual_journey_reduced_cost(proof_column, rmp.duals)
        self.assertGreaterEqual(proof_rc, -1.0e-6)
        incomplete_payload = {
            "status": "FULL_UNIVERSE_INCREMENTAL_LABEL_FOUND_NO_NEW_COLUMN_UNCERTIFIED",
            "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
            "pricing_proof_kind": PROOF_KIND_EXHAUSTIVE_INCOMPLETE,
            "can_certify_no_negative": False,
            "uses_true_dual_bpc_certificate": False,
            "true_best_reduced_cost": None,
            "pricing_best_reduced_cost": None,
            "returned_column_count": 0,
            "true_audited_column_count": 0,
            "completion_bound": {"enabled": False, "can_certify_no_negative": False},
        }
        proof_payload = {
            "status": "FULL_UNIVERSE_INCREMENTAL_LABEL_PRICED",
            "pricing_state": PricingState.CERTIFIED_NO_NEGATIVE.value,
            "pricing_proof_kind": PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE,
            "can_certify_no_negative": True,
            "uses_true_dual_bpc_certificate": True,
            "true_best_reduced_cost": proof_rc,
            "pricing_best_reduced_cost": proof_rc,
            "returned_column_count": 1,
            "true_audited_column_count": 1,
            "pricing_complete_for_all_task_subsets": True,
            "global_remaining_rc_lb": proof_rc,
            "global_remaining_rc_lb_valid": True,
            "global_remaining_rc_lb_coverage_complete": True,
            "completion_bound": {"enabled": False, "can_certify_no_negative": False},
        }

        with patch(
            "lunar_ice_bpc.exact.bpc.pricing.final_judge.run_bpc_labeling_pricer",
            side_effect=((incomplete_payload, tuple()), (proof_payload, (proof_column,))),
        ) as mocked:
            result = run_true_dual_root_final_judge(
                data,
                context,
                max_direct_tasks=5,
                labeling_final_judge_enabled=True,
                labeling_final_judge_max_exact_tasks=5,
                labeling_final_judge_exact_harvest_target=4,
            )

        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)
        self.assertTrue(result.pricing_payload["can_certify_no_negative"])
        self.assertTrue(result.pricing_payload["labeling_final_judge_proof_pass_attempted"])
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_harvest_pass_pricing_proof_kind"],
            PROOF_KIND_EXHAUSTIVE_INCOMPLETE,
        )
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_proof_pass_pricing_proof_kind"],
            PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE,
        )

    def test_labeling_final_judge_proof_only_skips_harvest_and_can_certify(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(
            data.task_ids,
            universe.columns,
            fleet_size=data.fleet_size,
        )
        context = ReducedCostContext(
            task_duals=rmp.duals.cover,
            fleet_dual=rmp.duals.fleet_limit,
            cut_duals=rmp.duals.cuts or {},
            dual_fingerprint="labeling-proof-only-test",
            rmp_iteration_id="root-1",
        )
        proof_payload = {
            "status": "FULL_UNIVERSE_INCREMENTAL_LABEL_PRICED",
            "pricing_state": PricingState.CERTIFIED_NO_NEGATIVE.value,
            "pricing_proof_kind": PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE,
            "can_certify_no_negative": True,
            "uses_true_dual_bpc_certificate": True,
            "true_best_reduced_cost": None,
            "pricing_best_reduced_cost": None,
            "returned_column_count": 0,
            "true_audited_column_count": 0,
            "pricing_complete_for_all_task_subsets": True,
            "global_remaining_rc_lb": -1.0e-6,
            "global_remaining_rc_lb_valid": True,
            "global_remaining_rc_lb_coverage_complete": True,
            "completion_bound": {"enabled": False, "can_certify_no_negative": False},
        }

        with patch(
            "lunar_ice_bpc.exact.bpc.pricing.final_judge.run_bpc_labeling_pricer",
            return_value=(proof_payload, tuple()),
        ) as mocked:
            result = run_true_dual_root_final_judge(
                data,
                context,
                max_direct_tasks=5,
                labeling_final_judge_enabled=True,
                labeling_final_judge_max_exact_tasks=5,
                labeling_final_judge_pass_strategy=LABELING_FINAL_JUDGE_PASS_PROOF_ONLY,
            )

        self.assertEqual(mocked.call_count, 1)
        self.assertFalse(mocked.call_args.kwargs["config"].stop_at_first_negative)
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)
        self.assertTrue(result.pricing_payload["can_certify_no_negative"])
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_pass_strategy"],
            LABELING_FINAL_JUDGE_PASS_PROOF_ONLY,
        )
        self.assertFalse(result.pricing_payload["labeling_final_judge_two_phase_enabled"])
        self.assertFalse(result.pricing_payload["labeling_final_judge_harvest_pass_attempted"])
        self.assertTrue(result.pricing_payload["labeling_final_judge_proof_pass_attempted"])

    def test_adaptive_final_judge_pass_policy_switches_only_on_sparse_results(self) -> None:
        policy = LABELING_FINAL_JUDGE_PASS_POLICY_ADAPTIVE
        self.assertEqual(
            _next_labeling_final_judge_pass_strategy(
                policy,
                {
                    "labeling_final_judge_proof_pass_attempted": False,
                    "labeling_final_judge_harvest_pass_column_count": 64,
                },
                max_columns_per_round=128,
                effective_harvest_target=64,
            ),
            "harvest_then_proof",
        )
        self.assertEqual(
            _next_labeling_final_judge_pass_strategy(
                policy,
                {
                    "labeling_final_judge_proof_pass_attempted": False,
                    "labeling_final_judge_harvest_pass_column_count": 7,
                },
                max_columns_per_round=128,
                effective_harvest_target=64,
            ),
            "proof_only",
        )
        self.assertEqual(
            _effective_labeling_final_judge_pass_policy(
                LABELING_FINAL_JUDGE_PASS_POLICY_BRANCH_ADAPTIVE,
                branch_context_active=False,
            ),
            "harvest_then_proof",
        )
        self.assertEqual(
            _effective_labeling_final_judge_pass_policy(
                LABELING_FINAL_JUDGE_PASS_POLICY_BRANCH_ADAPTIVE,
                branch_context_active=True,
            ),
            "adaptive_sparse_harvest_v1",
        )
        self.assertEqual(
            _next_labeling_final_judge_pass_strategy(
                policy,
                {
                    "labeling_final_judge_proof_pass_attempted": True,
                    "manual_branch_feasible_negative_count": 128,
                },
                max_columns_per_round=128,
                effective_harvest_target=64,
            ),
            "harvest_then_proof",
        )
        self.assertEqual(
            _next_labeling_final_judge_pass_strategy(
                policy,
                {
                    "labeling_final_judge_proof_pass_attempted": True,
                    "manual_branch_feasible_negative_count": 3,
                },
                max_columns_per_round=128,
                effective_harvest_target=64,
            ),
            "proof_only",
        )

    def test_adaptive_final_judge_harvest_cap_is_policy_scoped_and_fails_closed(self) -> None:
        env_name = LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC_ENV
        with patch.dict(os.environ, {env_name: "2.5"}, clear=False):
            self.assertEqual(
                _adaptive_final_judge_harvest_cap_sec(
                    LABELING_FINAL_JUDGE_PASS_POLICY_ADAPTIVE
                ),
                2.5,
            )
            self.assertIsNone(
                _adaptive_final_judge_harvest_cap_sec("harvest_then_proof")
            )

        for invalid in ("0", "-1", "nan", "inf", "not-a-number"):
            with self.subTest(invalid=invalid):
                with patch.dict(os.environ, {env_name: invalid}, clear=False):
                    with self.assertRaises(ValueError):
                        _adaptive_final_judge_harvest_cap_sec(
                            LABELING_FINAL_JUDGE_PASS_POLICY_ADAPTIVE
                        )

    def test_labeling_final_judge_harvest_cap_preserves_total_proof_budget(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        context = ReducedCostContext(
            task_duals={task_id: 0.0 for task_id in data.task_ids},
            fleet_dual=0.0,
            cut_duals={},
            dual_fingerprint="labeling-harvest-cap-test",
            rmp_iteration_id="branch-1",
        )
        incomplete_payload = {
            "status": "TIME_LIMIT",
            "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
            "pricing_proof_kind": PROOF_KIND_EXHAUSTIVE_INCOMPLETE,
            "can_certify_no_negative": False,
            "true_best_reduced_cost": None,
            "returned_column_count": 0,
            "true_audited_column_count": 0,
        }
        proof_payload = {
            "status": "FULL_UNIVERSE_INCREMENTAL_LABEL_PRICED",
            "pricing_state": PricingState.CERTIFIED_NO_NEGATIVE.value,
            "pricing_proof_kind": PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE,
            "can_certify_no_negative": True,
            "uses_true_dual_bpc_certificate": True,
            "true_best_reduced_cost": None,
            "returned_column_count": 0,
            "true_audited_column_count": 0,
            "pricing_complete_for_all_task_subsets": True,
            "global_remaining_rc_lb": -1.0e-6,
            "global_remaining_rc_lb_valid": True,
            "global_remaining_rc_lb_coverage_complete": True,
            "completion_bound": {"enabled": False, "can_certify_no_negative": False},
        }

        with (
            patch(
                "lunar_ice_bpc.exact.bpc.pricing.final_judge.run_bpc_labeling_pricer",
                side_effect=((incomplete_payload, tuple()), (proof_payload, tuple())),
            ) as mocked,
            patch(
                "lunar_ice_bpc.exact.bpc.pricing.final_judge.perf_counter",
                side_effect=(100.0, 100.0, 102.0, 102.0, 102.0, 105.0, 105.0),
            ),
        ):
            result = run_true_dual_root_final_judge(
                data,
                context,
                max_direct_tasks=5,
                wall_time_limit_sec=10.0,
                labeling_final_judge_enabled=True,
                labeling_final_judge_max_exact_tasks=5,
                labeling_final_judge_harvest_time_cap_sec=2.0,
            )

        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(mocked.call_args_list[0].kwargs["config"].wall_time_limit_sec, 2.0)
        self.assertEqual(mocked.call_args_list[1].kwargs["config"].wall_time_limit_sec, 8.0)
        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)
        self.assertEqual(result.pricing_payload["labeling_final_judge_harvest_time_cap_sec"], 2.0)
        self.assertTrue(result.pricing_payload["labeling_final_judge_proof_pass_attempted"])
        self.assertEqual(_smaller_optional_time_limit(None, 2.0), 2.0)
        self.assertEqual(_smaller_optional_time_limit(1.5, 2.0), 1.5)
        with self.assertRaises(ValueError):
            run_true_dual_root_final_judge(
                data,
                context,
                max_direct_tasks=5,
                labeling_final_judge_enabled=True,
                labeling_final_judge_harvest_time_cap_sec=float("nan"),
            )

    def test_labeling_pricer_final_judge_wall_time_limit_fails_closed(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        context = ReducedCostContext(
            task_duals=rmp.duals.cover,
            fleet_dual=rmp.duals.fleet_limit,
            cut_duals=rmp.duals.cuts or {},
            dual_fingerprint="labeling-timeout-test",
            rmp_iteration_id="root-1",
        )

        env = {
            **os.environ,
            "LUNAR_ICE_LABELING_FINAL_JUDGE": "1",
            "LUNAR_ICE_LABELING_FINAL_JUDGE_MAX_TASKS": "5",
        }
        with patch.dict(os.environ, env, clear=True):
            result = run_true_dual_root_final_judge(
                data,
                context,
                max_direct_tasks=5,
                wall_time_limit_sec=0.0,
            )

        self.assertEqual(result.pricing_state, PricingState.INCOMPLETE_LIMIT)
        self.assertEqual(result.pricing_payload["status"], "LABELING_FINAL_JUDGE_PRICED")
        self.assertEqual(result.pricing_payload["exact_status"], "NOT_SOLVED")
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_INCOMPLETE)
        self.assertFalse(result.pricing_payload["can_certify_no_negative"])
        self.assertFalse(result.pricing_payload["uses_true_dual_bpc_certificate"])
        self.assertFalse(result.pricing_payload["global_remaining_rc_lb_valid"])
        self.assertFalse(result.pricing_payload["global_remaining_rc_lb_coverage_complete"])
        self.assertGreater(result.pricing_payload["frontier_unsupported_region_count"], 0)
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_downgrade_reason"],
            "coverage_incomplete_or_timeout",
        )

    def test_labeling_pricer_final_judge_with_unsupported_fleet_cut_fails_closed(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        rmp = solve_restricted_journey_rmp(data.task_ids, universe.columns, fleet_size=data.fleet_size)
        cut = fleet_lower_bound_cut("fleet_lb_active", min_vehicles=1)
        context = ReducedCostContext(
            task_duals=rmp.duals.cover,
            fleet_dual=rmp.duals.fleet_limit,
            cut_duals={"fleet_lb_active": 0.0},
            dual_fingerprint="labeling-live-cut-test",
            rmp_iteration_id="root-cut",
        )

        env = {
            **os.environ,
            "LUNAR_ICE_LABELING_FINAL_JUDGE": "1",
            "LUNAR_ICE_LABELING_FINAL_JUDGE_MAX_TASKS": "5",
        }
        with patch.dict(os.environ, env, clear=True):
            result = run_true_dual_root_final_judge(
                data,
                context,
                max_direct_tasks=5,
                cut_context=CutContext((cut,)),
            )

        self.assertEqual(result.pricing_state, PricingState.INCOMPLETE_LIMIT)
        self.assertEqual(result.pricing_payload["status"], "LABELING_FINAL_JUDGE_PRICED")
        self.assertTrue(result.pricing_payload["cut_context_active"])
        self.assertFalse(result.pricing_payload["pricing_complete_for_all_task_subsets"])
        self.assertFalse(result.pricing_payload["can_certify_no_negative"])
        self.assertFalse(result.pricing_payload["uses_true_dual_bpc_certificate"])
        self.assertFalse(result.pricing_payload["global_remaining_rc_lb_valid"])
        self.assertGreater(result.pricing_payload["frontier_unsupported_region_count"], 0)
        self.assertFalse(result.pricing_payload["live_cut_certificate_supported"])
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_downgrade_reason"],
            "coverage_incomplete_or_timeout",
        )
        self.assertFalse(
            result.pricing_payload["cut_certificate_support"]["live_cut_certificate_supported"]
        )

    def test_labeling_pricer_final_judge_certifies_supported_subset_row_cut(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        universe = enumerate_direct_journey_columns(data, max_exact_tasks=5)
        cut = subset_row_cut("sri_live", data.task_ids[:3], divisor=2)
        rmp = solve_restricted_journey_rmp(
            data.task_ids,
            universe.columns,
            fleet_size=data.fleet_size,
            cut_context=CutContext((cut,)),
        )
        context = ReducedCostContext(
            task_duals=rmp.duals.cover,
            fleet_dual=rmp.duals.fleet_limit,
            cut_duals=rmp.duals.cuts or {},
            dual_fingerprint="labeling-subset-row-cut-test",
            rmp_iteration_id="root-sri",
        )

        env = {
            **os.environ,
            "LUNAR_ICE_LABELING_FINAL_JUDGE": "1",
            "LUNAR_ICE_LABELING_FINAL_JUDGE_MAX_TASKS": "5",
        }
        with patch.dict(os.environ, env, clear=True):
            result = run_true_dual_root_final_judge(
                data,
                context,
                max_direct_tasks=5,
                cut_context=CutContext((cut,)),
            )

        self.assertEqual(result.pricing_state, PricingState.CERTIFIED_NO_NEGATIVE)
        self.assertEqual(result.pricing_payload["status"], "LABELING_FINAL_JUDGE_PRICED")
        self.assertTrue(result.pricing_payload["cut_context_active"])
        self.assertTrue(result.pricing_payload["pricing_complete_for_all_task_subsets"])
        self.assertTrue(result.pricing_payload["can_certify_no_negative"])
        self.assertTrue(result.pricing_payload["uses_true_dual_bpc_certificate"])
        self.assertTrue(result.pricing_payload["global_remaining_rc_lb_valid"])
        self.assertTrue(result.pricing_payload["live_cut_certificate_supported"])
        self.assertTrue(result.pricing_payload["cut_aware_signature_used"])
        self.assertTrue(result.pricing_payload["cut_aware_signature_cut_context_active"])
        self.assertGreater(result.pricing_payload["cut_aware_signature_cut_hash_column_count"], 0)
        self.assertTrue(
            any(
                row["cut_coefficient_vector_hash"]
                for row in result.pricing_payload["audit_sample_rows"]
            )
        )
        support = result.pricing_payload["cut_certificate_support"]
        self.assertTrue(support["live_cut_certificate_supported"])
        self.assertTrue(
            support["cut_reduced_cost_audit"]["manual_rc_with_cuts_matches_pricing_rc"]
        )
        self.assertTrue(support["cut_reduced_cost_audit"]["cut_dual_sign_audit_pass"])

    def test_labeling_final_judge_ignores_branch_infeasible_negative_columns(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        task_a, task_b = data.task_ids[:2]
        one_only = next(
            column
            for column in enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
            if str(task_a) in set(column.task_set) and str(task_b) not in set(column.task_set)
        )
        branch_context = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))
        self.assertFalse(journey_satisfies_branch_context(one_only, branch_context))
        cover_duals = {task_id: 0.0 for task_id in data.task_ids}
        cover_duals[str(task_a)] = float(one_only.objective) + 10.0
        context = ReducedCostContext(
            task_duals=cover_duals,
            fleet_dual=0.0,
            cut_duals={},
            dual_fingerprint="labeling-branch-filter-test",
            rmp_iteration_id="root-branch",
        )
        mocked_payload = {
            "pricing_state": PricingState.FOUND_NEGATIVE.value,
            "can_certify_no_negative": False,
            "uses_true_dual_bpc_certificate": False,
            "pricing_proof_kind": PROOF_KIND_EXHAUSTIVE_FOUND_NEGATIVE,
            "true_best_reduced_cost": -10.0,
            "pricing_best_reduced_cost": -10.0,
            "true_audited_column_count": 1,
            "completion_bound": {"enabled": False, "can_certify_no_negative": False},
        }

        env = {
            **os.environ,
            "LUNAR_ICE_LABELING_FINAL_JUDGE": "1",
            "LUNAR_ICE_LABELING_FINAL_JUDGE_MAX_TASKS": "5",
        }
        with patch.dict(os.environ, env, clear=True), patch(
            "lunar_ice_bpc.exact.bpc.pricing.final_judge.run_bpc_labeling_pricer",
            return_value=(mocked_payload, (one_only,)),
        ):
            result = run_true_dual_root_final_judge(
                data,
                context,
                max_direct_tasks=5,
                branch_context=branch_context,
            )

        self.assertEqual(result.pricing_state, PricingState.INCOMPLETE_LIMIT)
        self.assertEqual(result.negative_columns, tuple())
        self.assertEqual(result.pricing_payload["manual_branch_feasible_negative_count"], 0)
        self.assertEqual(result.pricing_payload["manual_branch_filtered_negative_count"], 1)
        self.assertEqual(result.pricing_payload["labeling_final_judge_branch_filtered_negative_count"], 1)
        self.assertFalse(result.pricing_payload["all_priced_columns_satisfy_branch_context"])
        self.assertFalse(result.pricing_payload["uses_true_dual_bpc_certificate"])
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_INCOMPLETE)
        self.assertEqual(
            result.pricing_payload["underlying_pricing_proof_kind"],
            PROOF_KIND_EXHAUSTIVE_FOUND_NEGATIVE,
        )
        self.assertEqual(
            result.pricing_payload["pricing_proof_kind_source"],
            "labeling_final_judge_true_dual_reaudit",
        )
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_downgrade_reason"],
            "branch_filtered_negative",
        )

    def test_labeling_final_judge_downgrades_when_manual_rc_reaudit_disagrees(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        column = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns[0]
        context = ReducedCostContext(
            task_duals={task_id: 0.0 for task_id in data.task_ids},
            fleet_dual=0.0,
            cut_duals={},
            dual_fingerprint="labeling-manual-rc-mismatch-test",
            rmp_iteration_id="root-rc-mismatch",
        )
        true_manual_rc = manual_journey_reduced_cost(
            column,
            JourneyDuals(cover=context.task_duals, fleet_limit=0.0),
        )
        mocked_payload = {
            "pricing_state": PricingState.CERTIFIED_NO_NEGATIVE.value,
            "can_certify_no_negative": True,
            "uses_true_dual_bpc_certificate": True,
            "pricing_proof_kind": PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE,
            "true_best_reduced_cost": true_manual_rc + 1.0,
            "pricing_best_reduced_cost": true_manual_rc + 1.0,
            "true_audited_column_count": 1,
            "completion_bound": {"enabled": False, "can_certify_no_negative": False},
        }

        env = {
            **os.environ,
            "LUNAR_ICE_LABELING_FINAL_JUDGE": "1",
            "LUNAR_ICE_LABELING_FINAL_JUDGE_MAX_TASKS": "5",
        }
        with patch.dict(os.environ, env, clear=True), patch(
            "lunar_ice_bpc.exact.bpc.pricing.final_judge.run_bpc_labeling_pricer",
            return_value=(mocked_payload, (column,)),
        ):
            result = run_true_dual_root_final_judge(data, context, max_direct_tasks=5)

        self.assertEqual(result.pricing_state, PricingState.INCOMPLETE_LIMIT)
        self.assertEqual(result.pricing_payload["pricing_state"], PricingState.INCOMPLETE_LIMIT.value)
        self.assertFalse(result.pricing_payload["can_certify_no_negative"])
        self.assertFalse(result.pricing_payload["uses_true_dual_bpc_certificate"])
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_INCOMPLETE)
        self.assertEqual(
            result.pricing_payload["underlying_pricing_proof_kind"],
            PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE,
        )
        self.assertEqual(
            result.pricing_payload["pricing_proof_kind_source"],
            "labeling_final_judge_true_dual_reaudit",
        )
        self.assertFalse(result.pricing_payload["labeling_final_judge_manual_rc_consistency_pass"])
        self.assertAlmostEqual(
            result.pricing_payload["manual_branch_feasible_best_reduced_cost"],
            true_manual_rc,
            places=6,
        )
        self.assertAlmostEqual(
            result.pricing_payload["labeling_final_judge_payload_true_best_reduced_cost"],
            true_manual_rc + 1.0,
            places=6,
        )
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_downgrade_reason"],
            "manual_rc_mismatch",
        )

    def test_labeling_final_judge_downgrades_noncertifying_underlying_proof_kind(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        column = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns[0]
        context = ReducedCostContext(
            task_duals={task_id: 0.0 for task_id in data.task_ids},
            fleet_dual=0.0,
            cut_duals={},
            dual_fingerprint="labeling-noncertifying-proof-kind-test",
            rmp_iteration_id="root-proof-kind",
        )
        true_manual_rc = manual_journey_reduced_cost(
            column,
            JourneyDuals(cover=context.task_duals, fleet_limit=0.0),
        )
        mocked_payload = {
            "pricing_state": PricingState.CERTIFIED_NO_NEGATIVE.value,
            "can_certify_no_negative": True,
            "uses_true_dual_bpc_certificate": True,
            "pricing_proof_kind": PROOF_KIND_RELAXED_WORKER_UNCERTIFIED,
            "true_best_reduced_cost": true_manual_rc,
            "pricing_best_reduced_cost": true_manual_rc,
            "true_audited_column_count": 1,
            "completion_bound": {"enabled": False, "can_certify_no_negative": False},
        }

        env = {
            **os.environ,
            "LUNAR_ICE_LABELING_FINAL_JUDGE": "1",
            "LUNAR_ICE_LABELING_FINAL_JUDGE_MAX_TASKS": "5",
        }
        with patch.dict(os.environ, env, clear=True), patch(
            "lunar_ice_bpc.exact.bpc.pricing.final_judge.run_bpc_labeling_pricer",
            return_value=(mocked_payload, (column,)),
        ):
            result = run_true_dual_root_final_judge(data, context, max_direct_tasks=5)

        self.assertEqual(result.pricing_state, PricingState.INCOMPLETE_LIMIT)
        self.assertEqual(result.pricing_payload["pricing_state"], PricingState.INCOMPLETE_LIMIT.value)
        self.assertFalse(result.pricing_payload["can_certify_no_negative"])
        self.assertFalse(result.pricing_payload["uses_true_dual_bpc_certificate"])
        self.assertEqual(result.pricing_payload["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_INCOMPLETE)
        self.assertEqual(
            result.pricing_payload["underlying_pricing_proof_kind"],
            PROOF_KIND_RELAXED_WORKER_UNCERTIFIED,
        )
        self.assertFalse(result.pricing_payload["underlying_pricing_proof_kind_certifying"])
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_downgrade_reason"],
            "noncertifying_underlying_proof_kind",
        )
        self.assertEqual(
            result.pricing_payload["labeling_final_judge_certificate_role"],
            "true_dual_exact_elementary_final_proof",
        )
        self.assertFalse(result.pricing_payload["labeling_final_judge_can_certify"])

    def test_b3_node_solver_passes_explicit_labeling_final_judge_options(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        initial_columns = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
        mock_payload = {
            "pricing_state": PricingState.CERTIFIED_NO_NEGATIVE.value,
            "status": "LABELING_FINAL_JUDGE_PRICED",
            "exact_status": "BPC_NO_NEGATIVE_CERTIFIED",
            "can_certify_no_negative": True,
            "uses_true_dual_bpc_certificate": True,
            "pricing_rc_audit_pass": True,
            "manual_rc_audit_pass": True,
            "all_priced_columns_satisfy_branch_context": True,
            "pricing_proof_kind": PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE,
            "labeling_final_judge_enabled": True,
            "labeling_final_judge_opt_in_source": "explicit_parameter",
            "labeling_final_judge_selection_reason": "explicit_enabled",
            "labeling_final_judge_certificate_role": "true_dual_exact_elementary_final_proof",
            "labeling_final_judge_can_certify": True,
            "labeling_final_judge_downgrade_reason": "",
            "labeling_final_judge_task_count": 5,
            "labeling_final_judge_exact_harvest_target": 4,
            "labeling_final_judge_exact_harvest_target_source": "explicit_parameter",
            "labeling_final_judge_harvest_time_cap_sec": 2.0,
            "exact_negative_harvest_target": 4,
            "exact_negative_harvest_candidate_count": 0,
            "exact_negative_harvest_selected_count": 0,
            "exact_negative_harvest_selected_new_task_set_count": 0,
            "exact_negative_harvest_selected_replacement_task_set_count": 0,
            "exact_negative_harvest_selection_policy": "global_min_first_then_distinct_task_sets_then_replacements",
        }
        mock_result = FinalJudgeResult(
            pricing_state=PricingState.CERTIFIED_NO_NEGATIVE,
            pricing_payload=mock_payload,
            negative_columns=tuple(),
            all_priced_columns=tuple(initial_columns),
        )

        with (
            patch(
                "lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver.run_true_dual_root_final_judge",
                return_value=mock_result,
            ) as mocked_judge,
            patch.dict(
                os.environ,
                {
                    "LUNAR_ICE_LABELING_FINAL_JUDGE_PASS_POLICY": (
                        LABELING_FINAL_JUDGE_PASS_POLICY_ADAPTIVE
                    ),
                    LABELING_FINAL_JUDGE_ADAPTIVE_HARVEST_CAP_SEC_ENV: "2.0",
                },
                clear=False,
            ),
        ):
            result = solve_node_pricing_with_b2b_r3(
                data,
                initial_columns=initial_columns,
                max_direct_tasks=5,
                max_rounds=1,
                max_columns_per_round=0,
                labeling_final_judge_enabled=True,
                labeling_final_judge_max_exact_tasks=5,
                labeling_final_judge_exact_harvest_target=4,
            )

        self.assertTrue(mocked_judge.called)
        self.assertTrue(mocked_judge.call_args.kwargs["labeling_final_judge_enabled"])
        self.assertEqual(mocked_judge.call_args.kwargs["labeling_final_judge_max_exact_tasks"], 5)
        self.assertEqual(mocked_judge.call_args.kwargs["labeling_final_judge_exact_harvest_target"], 4)
        self.assertEqual(
            mocked_judge.call_args.kwargs["labeling_final_judge_harvest_time_cap_sec"],
            2.0,
        )
        self.assertEqual(
            result["history"][0]["labeling_final_judge_harvest_time_cap_sec"],
            2.0,
        )
        self.assertEqual(result["final_judge"]["labeling_final_judge_opt_in_source"], "explicit_parameter")
        self.assertEqual(result["final_judge_status"], "LABELING_FINAL_JUDGE_PRICED")
        self.assertEqual(result["final_judge_exact_status"], "BPC_NO_NEGATIVE_CERTIFIED")
        self.assertEqual(result["pricing_proof_kind"], PROOF_KIND_EXHAUSTIVE_NO_NEGATIVE)
        self.assertTrue(result["final_judge_can_certify_no_negative"])
        self.assertTrue(result["final_judge_uses_true_dual_bpc_certificate"])
        self.assertTrue(result["final_judge_pricing_rc_audit_pass"])
        self.assertTrue(result["final_judge_manual_rc_audit_pass"])
        self.assertTrue(result["labeling_final_judge_enabled"])
        self.assertEqual(result["labeling_final_judge_opt_in_source"], "explicit_parameter")
        self.assertEqual(result["labeling_final_judge_selection_reason"], "explicit_enabled")
        self.assertEqual(
            result["labeling_final_judge_certificate_role"],
            "true_dual_exact_elementary_final_proof",
        )
        self.assertTrue(result["labeling_final_judge_can_certify"])
        self.assertEqual(result["labeling_final_judge_downgrade_reason"], "")
        self.assertEqual(result["labeling_final_judge_exact_harvest_target"], 4)
        self.assertEqual(result["exact_negative_harvest_target"], 4)
        self.assertEqual(result["exact_negative_harvest_selected_count"], 0)
        self.assertEqual(result["labeling_final_judge_task_count"], 5)
        self.assertTrue(result["uses_true_dual_bpc_certificate"])

    def test_b3_node_solver_rejects_uncertified_final_judge_proof_kind(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        initial_columns = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
        mock_payload = {
            "pricing_state": PricingState.CERTIFIED_NO_NEGATIVE.value,
            "status": "RELAXED_WORKER_NO_COLUMN",
            "exact_status": "NOT_SOLVED",
            "can_certify_no_negative": True,
            "uses_true_dual_bpc_certificate": True,
            "pricing_rc_audit_pass": True,
            "manual_rc_audit_pass": True,
            "all_priced_columns_satisfy_branch_context": True,
            "pricing_proof_kind": PROOF_KIND_RELAXED_WORKER_UNCERTIFIED,
            "labeling_final_judge_enabled": True,
        }
        mock_result = FinalJudgeResult(
            pricing_state=PricingState.CERTIFIED_NO_NEGATIVE,
            pricing_payload=mock_payload,
            negative_columns=tuple(),
            all_priced_columns=tuple(initial_columns),
        )

        with patch(
            "lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver.run_true_dual_root_final_judge",
            return_value=mock_result,
        ):
            result = solve_node_pricing_with_b2b_r3(
                data,
                initial_columns=initial_columns,
                max_direct_tasks=5,
                max_rounds=1,
                max_columns_per_round=0,
                labeling_final_judge_enabled=True,
                labeling_final_judge_max_exact_tasks=5,
            )

        self.assertEqual(result["requested_certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertEqual(result["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
        self.assertEqual(result["pricing_state"], "INCOMPLETE_LIMIT")
        self.assertEqual(result["exact_status"], "NOT_SOLVED")
        self.assertFalse(result["node_lp_bound_official"])
        self.assertFalse(result["certificate_ledger"]["valid"])
        self.assertIn("pricing_proof_kind_not_certifying", result["certificate_ledger"]["issues"])
        self.assertFalse(result["final_judge_certifying_proof_kind"])
        self.assertEqual(result["pricing_proof_kind"], PROOF_KIND_RELAXED_WORKER_UNCERTIFIED)

    def test_b3_node_solver_threads_subset_row_cut_context_to_final_judge(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        initial_columns = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
        cut_context = CutContext((subset_row_cut("sr_ab", data.task_ids[:3], divisor=2),))

        result = solve_node_pricing_with_b2b_r3(
            data,
            initial_columns=initial_columns,
            max_direct_tasks=5,
            max_rounds=1,
            max_columns_per_round=0,
            labeling_final_judge_enabled=True,
            labeling_final_judge_max_exact_tasks=5,
            cut_context=cut_context,
        )

        self.assertEqual(result["certificate_scope"], "BPC_NODE_LP_CERTIFIED")
        self.assertEqual(result["pricing_state"], "CERTIFIED_NO_NEGATIVE")
        self.assertTrue(result["uses_true_dual_bpc_certificate"])
        self.assertTrue(result["certificate_ledger"]["valid"])
        self.assertTrue(result["cut_context_active"])
        self.assertEqual(result["cut_count"], 1)
        self.assertTrue(result["completion_bound_policy"]["cut_context_active"])
        self.assertTrue(result["manual_rc_audit_pass"])
        self.assertTrue(result["pricing_rc_audit_pass"])
        self.assertTrue(result["cut_pricing_audit_pass"])
        self.assertTrue(result["final_judge"]["cut_context_active"])
        self.assertEqual(result["final_judge"]["cut_count"], 1)
        self.assertTrue(result["final_judge_live_cut_certificate_supported"])
        self.assertTrue(result["final_judge"]["cut_aware_signature_cut_context_active"])

    def test_relaxed_labeling_worker_adds_columns_without_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)

        result = solve_b2_pricing_tail_baseline(
            data,
            max_direct_tasks=5,
            max_rounds=1,
            mode=B2B_R2_MODE,
            worker_pricer_kind=RELAXED_LABELING_WORKER,
        )

        self.assertEqual(result["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(result["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
        self.assertEqual(result["pricing_state"], "INCOMPLETE_LIMIT")
        self.assertFalse(result["uses_true_dual_bpc_certificate"])
        self.assertEqual(result["final_judge_call_count"], 0)
        self.assertEqual(result["hidden_negative_refinement_coverage_counts"], {})
        self.assertEqual(result["hidden_negative_refinement_catalog_coverage_counts"], {})
        self.assertEqual(result["hidden_negative_refinement_catalog_seed_count"], 0)
        self.assertTrue(result["hidden_negative_refinement_coverage_diagnostic_only"])
        self.assertGreater(result["worker_found_addable_negative_count"], 0)
        self.assertGreater(result["added_to_master_count"], 0)
        row = result["history"][0]
        self.assertEqual(row["worker_pricer_kind"], RELAXED_LABELING_WORKER)
        self.assertTrue(row["labeling_worker_enabled"])
        self.assertEqual(row["labeling_algorithm"], "ng_route_relaxed_resource_labeling_plus_direct_seed_portfolio")
        self.assertEqual(row["resource_label_core_mode"], "relaxed_ng_route_worker")
        self.assertEqual(row["resource_label_algorithm"], "ng_route_relaxed_resource_labeling")
        self.assertIn("energy", row["resource_dimensions"])
        self.assertEqual(row["pricing_proof_kind"], PROOF_KIND_RELAXED_WORKER_UNCERTIFIED)
        self.assertTrue(row["branch_context_audit_pass"])
        self.assertEqual(row["branch_invalid_column_count"], 0)
        self.assertTrue(row["completion_bound_pruning_enabled"])
        self.assertGreater(row["completion_bound_evaluated_label_count"], 0)
        self.assertFalse(row["completion_bound_can_certify_no_negative"])
        self.assertGreater(row["worker_generated_count"], 0)
        self.assertGreater(row["worker_candidate_budget"], 0)
        self.assertGreater(len(row["generated_task_sets"]), 0)
        self.assertGreater(len(row["worker_seen_task_sets"]), 0)
        self.assertGreaterEqual(row["task_bound_pruned_count"], 0)
        self.assertGreaterEqual(row["resource_bound_pruned_count"], 0)
        self.assertGreaterEqual(row["dominance_filtered_count"], 0)
        self.assertGreaterEqual(row["duplicate_filtered_count"], 0)
        self.assertFalse(row["pricing_timeout"])
        self.assertEqual(row["refinement_seed_count"], 0)
        self.assertEqual(row["active_refinement_seed_count"], 0)
        self.assertEqual(row["refinement_seed_task_count_counts"], {})
        self.assertEqual(row["refinement_expanded_seed_count"], 0)
        self.assertEqual(row["active_refinement_expanded_seed_count"], 0)
        self.assertEqual(row["refinement_expanded_seed_task_count_counts"], {})
        self.assertEqual(
            row["refinement_seed_policy"],
            "hidden_negative_unseen_first_then_superset_then_exact_with_first_expansion_reserve",
        )
        self.assertGreater(row["refinement_seed_budget_limit"], 0)
        self.assertTrue(row["refinement_seed_budget_reserves_first_expansion"])
        self.assertEqual(row["refinement_seed_catalog_payload"]["seed_count"], 0)
        self.assertFalse(row["refinement_seed_mutates_certificate"])
        self.assertGreater(row["ng_seed_task_set_count"], 0)
        self.assertTrue(row["resource_extension_seed_enabled"])
        self.assertGreater(row["resource_extension_seed_task_set_count"], 0)
        self.assertGreater(row["active_resource_extension_seed_task_set_count"], 0)
        self.assertIn("3", row["resource_extension_seed_task_set_count_by_size"])
        self.assertGreater(row["resource_extension_label_attempt_count"], 0)
        self.assertTrue(row["resource_extension_label_stats"])
        self.assertGreaterEqual(row["resource_extension_label_dominance_rejected_count"], 0)
        self.assertGreaterEqual(row["resource_extension_label_capacity_truncated_count"], 0)
        self.assertTrue(row["resource_extension_label_column_worker_enabled"])
        self.assertGreater(row["resource_extension_label_column_count"], 0)
        self.assertGreater(row["resource_extension_label_column_task_set_count"], 0)
        self.assertGreater(row["resource_extension_label_path_variant_candidate_count"], 0)
        self.assertGreater(row["resource_extension_label_path_variant_feasible_count"], 0)
        self.assertGreaterEqual(
            row["resource_extension_label_path_variant_candidate_count"],
            row["resource_extension_label_path_variant_feasible_count"],
        )
        self.assertEqual(
            row["resource_extension_label_column_policy"],
            "feasible_resource_extension_physical_representatives_worker_only",
        )
        self.assertFalse(row["resource_extension_label_columns_can_certify_no_negative"])
        self.assertIn("resource_extension", row["active_seed_task_set_source_counts"])
        self.assertIn("resource_extension", row["active_seed_task_set_source_task_count_counts"])
        self.assertIn("resource_extension", row["candidate_seed_source_precedence"])
        self.assertIn("hidden_negative_refinement", row["candidate_seed_source_precedence"])
        self.assertIn("direct_candidate", row["candidate_seed_source_precedence"])
        self.assertGreaterEqual(row["direct_candidate_task_set_count"], 0)
        self.assertTrue(row["priced_candidate_task_set_source_counts"])
        self.assertTrue(row["priced_candidate_task_set_source_task_count_counts"])
        self.assertEqual(row["ng_neighborhood_sizes"], [3, 5, 8])
        self.assertEqual(row["ng_neighborhood_stage_count"], 3)
        self.assertIn("3", row["ng_seed_task_set_count_by_size"])
        self.assertIn("5", row["ng_seed_task_set_count_by_size"])
        self.assertIn("8", row["ng_seed_task_set_count_by_size"])
        self.assertGreaterEqual(row["merged_seed_task_set_count"], row["ng_seed_task_set_count"])
        self.assertGreater(row["active_seed_task_set_count"], 0)
        self.assertEqual(
            row["active_seed_selection_policy"],
            "protected_refinement_then_source_task_count_coverage_then_low_overlap_fill",
        )
        self.assertEqual(row["protected_refinement_seed_task_set_count"], 0)
        self.assertEqual(row["active_protected_refinement_seed_task_set_count"], 0)
        self.assertEqual(row["protected_refinement_seed_task_set_count_by_size"], {})
        self.assertEqual(row["protected_refinement_seed_budget_truncated_count"], 0)
        self.assertTrue(row["active_seed_task_set_count_by_size"])
        self.assertGreater(row["active_ng_seed_task_set_count"], 0)
        self.assertGreater(row["active_input_seed_task_set_count"], 0)
        self.assertGreater(row["true_dual_audited_column_count"], 0)
        self.assertGreater(row["true_dual_selected_negative_count"], 0)
        self.assertTrue(row["candidate_search_dual_matches_true_dual"])
        self.assertTrue(row["candidate_search_rc_recomputed_under_true_dual"])
        self.assertTrue(row["worker_true_dual_candidate_audit_pass"])
        self.assertGreaterEqual(row["candidate_search_false_positive_rate"], 0.0)
        self.assertGreaterEqual(row["true_negative_candidate_search_miss_rate"], 0.0)
        self.assertIsInstance(row["candidate_search_false_positive_rows"], list)
        self.assertIsInstance(row["true_negative_candidate_search_miss_rows"], list)
        self.assertGreaterEqual(row["worker_generated_column_task_set_count"], 0)
        self.assertIsInstance(row["worker_candidate_universe_task_sets"], list)
        self.assertIsInstance(row["worker_generated_column_task_sets"], list)
        self.assertGreater(row["labeling_harvest_candidate_negative_count"], 0)
        self.assertGreaterEqual(row["labeling_harvest_candidate_new_task_set_count"], 0)
        self.assertGreaterEqual(row["labeling_harvest_candidate_replacement_task_set_count"], 0)
        self.assertGreater(row["labeling_harvest_selected_count"], 0)
        self.assertTrue(row["labeling_harvest_selected_seed_source_counts"])
        self.assertGreaterEqual(row["labeling_harvest_selected_new_task_set_count"], 0)
        self.assertGreaterEqual(row["labeling_harvest_selected_replacement_task_set_count"], 0)
        self.assertEqual(
            row["labeling_harvest_selected_new_task_set_count"]
            + row["labeling_harvest_selected_replacement_task_set_count"],
            row["labeling_harvest_selected_count"],
        )
        self.assertGreaterEqual(row["labeling_harvest_existing_master_task_set_count"], 0)
        self.assertGreaterEqual(row["labeling_harvest_selected_distinct_task_set_count"], 0)
        self.assertGreaterEqual(row["labeling_harvest_selected_duplicate_task_set_count"], 0)
        self.assertEqual(
            row["labeling_harvest_selection_policy"],
            "support_aware_new_then_support_changing_then_strong_replacement_then_capped_weak_replacement",
        )
        self.assertTrue(row["labeling_harvest_support_aware_enabled"])
        self.assertGreaterEqual(row["labeling_harvest_support_task_set_count"], 0)
        self.assertGreaterEqual(row["labeling_harvest_selected_support_changing_count"], 0)
        self.assertGreaterEqual(row["labeling_harvest_selected_strong_replacement_count"], 0)
        self.assertGreaterEqual(row["labeling_harvest_selected_weak_replacement_count"], 0)
        self.assertEqual(row["labeling_harvest_weak_replacement_cap"], 8)
        self.assertIn("labeling_harvest_max_pairwise_jaccard", row)
        self.assertEqual(
            row["worker_harvest_priority"],
            "prefer_new_task_set_then_true_rc_then_replacements",
        )
        self.assertGreaterEqual(row["worker_harvest_selected_new_task_set_count"], 0)
        self.assertGreaterEqual(row["worker_harvest_selected_replacement_task_set_count"], 0)
        self.assertEqual(
            row["worker_harvest_selected_new_task_set_count"]
            + row["worker_harvest_selected_replacement_task_set_count"],
            row["labeling_harvest_selected_count"],
        )
        self.assertIsNotNone(row["worker_harvest_best_true_rc"])
        self.assertIsNotNone(row["worker_harvest_worst_selected_true_rc"])
        self.assertEqual(
            row["selected_count_before_entry_audit"],
            row["labeling_harvest_selected_count"],
        )
        self.assertEqual(row["entry_audit_rejected_selected_count"], 0)
        self.assertEqual(
            row["selected_would_enter_master_count"],
            row["labeling_harvest_selected_count"],
        )
        self.assertTrue(row["selected_all_would_enter_master"])
        self.assertFalse(row["rmp_dual_diagnostic"]["can_certify_no_negative"])

    def test_direct_label_worker_uses_resource_label_core_without_certificate(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)

        result = solve_b2_pricing_tail_baseline(
            data,
            max_direct_tasks=5,
            max_rounds=1,
            mode=B2B_R2_MODE,
            worker_pricer_kind=DIRECT_LABEL_WORKER,
        )

        self.assertEqual(result["algorithm_status"], "BPC_INCOMPLETE_PRICING")
        self.assertEqual(result["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
        self.assertFalse(result["uses_true_dual_bpc_certificate"])
        row = result["history"][0]
        self.assertEqual(row["worker_pricer_kind"], DIRECT_LABEL_WORKER)
        self.assertEqual(row["resource_label_core_mode"], "direct_selected_set_worker")
        self.assertEqual(row["resource_label_algorithm"], "direct_selected_set_resource_labeling")
        self.assertEqual(row["pricing_proof_kind"], "DIRECT_WORKER_UNCERTIFIED")
        self.assertFalse(row["completion_bound_pruning_enabled"])
        self.assertEqual(row["completion_bound_pruned_label_count"], 0)
        self.assertFalse(row["completion_bound_can_certify_no_negative"])
        self.assertEqual(row["ng_seed_task_set_count"], 0)
        self.assertEqual(row["ng_neighborhood_size"], 0)
        self.assertEqual(row["ng_neighborhood_sizes"], [])
        self.assertEqual(row["ng_neighborhood_stage_count"], 0)
        self.assertEqual(row["ng_seed_task_set_count_by_size"], {})
        self.assertEqual(row["active_seed_task_set_count"], 0)
        self.assertEqual(row["active_ng_seed_task_set_count"], 0)
        self.assertEqual(row["active_input_seed_task_set_count"], 0)
        self.assertTrue(row["candidate_search_dual_matches_true_dual"])
        self.assertTrue(row["candidate_search_rc_recomputed_under_true_dual"])
        self.assertTrue(row["worker_true_dual_candidate_audit_pass"])
        self.assertGreaterEqual(row["candidate_search_negative_column_count"], 0)
        self.assertGreaterEqual(row["candidate_search_negative_true_negative_count"], 0)
        self.assertGreaterEqual(row["candidate_search_negative_true_nonnegative_count"], 0)
        self.assertGreaterEqual(row["true_negative_candidate_search_nonnegative_count"], 0)
        self.assertGreaterEqual(row["candidate_search_false_positive_rate"], 0.0)
        self.assertGreaterEqual(row["true_negative_candidate_search_miss_rate"], 0.0)
        self.assertIn("time_window", row["resource_dimensions"])
        self.assertFalse(row["rmp_dual_diagnostic"]["can_certify_no_negative"])

    def test_relaxed_labeling_worker_dual_stabilization_remains_worker_only(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)

        result = solve_b2_pricing_tail_baseline(
            data,
            max_direct_tasks=5,
            max_rounds=1,
            mode=B2B_R2_MODE,
            worker_pricer_kind=RELAXED_LABELING_WORKER,
            tail_dual_stabilization_enabled=True,
            tail_dual_stabilization_alpha=0.7,
        )

        row = result["history"][0]
        self.assertEqual(row["diagnostic_dual_source"], "tail_dual_stabilized_worker_dual")
        self.assertEqual(row["worker_dual_source"], "tail_dual_stabilized_worker_dual")
        self.assertEqual(row["official_dual_source"], "current_true_rmp_dual")
        self.assertTrue(row["worker_dual_only"])
        self.assertTrue(row["true_dual_rc_recomputed"])
        self.assertIn(row["candidate_search_dual_matches_true_dual"], {True, False})
        self.assertTrue(row["candidate_search_rc_recomputed_under_true_dual"])
        self.assertGreaterEqual(row["candidate_search_negative_true_nonnegative_count"], 0)
        self.assertGreaterEqual(row["true_negative_candidate_search_nonnegative_count"], 0)
        self.assertGreaterEqual(row["candidate_search_false_positive_rate"], 0.0)
        self.assertGreaterEqual(row["true_negative_candidate_search_miss_rate"], 0.0)
        self.assertIsInstance(row["candidate_search_false_positive_rows"], list)
        self.assertIsInstance(row["true_negative_candidate_search_miss_rows"], list)
        self.assertFalse(row["tail_dual_no_column_can_certify"])
        self.assertTrue(row["tail_dual_stabilization"]["tail_dual_stabilization_enabled"])
        self.assertFalse(row["tail_dual_stabilization"]["can_certify_no_negative"])
        self.assertFalse(result["uses_true_dual_bpc_certificate"])

    def test_labeling_worker_diagnostic_exports_dual_search_error_metrics(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            instance_path = project_root / "instance_001_logical_graph.json"
            instance_path.write_text(json.dumps(instance), encoding="utf-8")

            report = run_labeling_worker_diagnostic(
                [instance_path],
                project_root=project_root,
                workers=(RELAXED_LABELING_WORKER,),
                max_rounds=1,
                max_columns_per_round=4,
                row_time_limit_sec=30.0,
                tail_dual_stabilization_enabled=True,
            )

        row = report["rows"][0]
        summary = report["summary_rows"][0]
        relaxed_config = report["config"]["relaxed_ng_route_worker_config"]
        self.assertTrue(relaxed_config["support_aware_harvest_enabled"])
        self.assertEqual(relaxed_config["support_overlap_threshold"], 0.6)
        self.assertEqual(relaxed_config["max_selected_jaccard"], 0.5)
        self.assertEqual(relaxed_config["max_selected_containment"], 0.8)
        self.assertEqual(relaxed_config["weak_replacement_cap"], 8)
        self.assertEqual(relaxed_config["strong_replacement_threshold"], -1.0e-4)
        self.assertEqual(row["worker_pricer_kind"], RELAXED_LABELING_WORKER)
        self.assertTrue(row["tail_dual_stabilization_enabled"])
        self.assertFalse(row["worker_certificate_leak"])
        self.assertFalse(row["tail_dual_certificate_leak"])
        self.assertFalse(row["true_dual_rc_recompute_missing"])
        self.assertFalse(row["worker_can_certify_no_negative"])
        self.assertFalse(row["worker_uses_true_dual_bpc_certificate"])
        self.assertFalse(row["worker_root_lp_bound_official"])
        self.assertIn("candidate_search_false_positive_rate", row)
        self.assertIn("true_negative_candidate_search_miss_rate", row)
        self.assertIsInstance(row["candidate_search_false_positive_rows"], list)
        self.assertIsInstance(row["true_negative_candidate_search_miss_rows"], list)
        self.assertIn("worker_candidate_universe_task_set_count", row)
        self.assertIn("worker_generated_column_task_set_count", row)
        self.assertIn("resource_extension_label_path_variant_candidate_count", row)
        self.assertIn("resource_extension_label_path_variant_feasible_count", row)
        self.assertGreater(row["resource_extension_label_path_variant_candidate_count"], 0)
        self.assertGreater(row["resource_extension_label_path_variant_feasible_count"], 0)
        self.assertTrue(row["worker_true_dual_candidate_audit_pass"])
        self.assertEqual(
            row["active_seed_selection_policy"],
            "protected_refinement_then_source_task_count_coverage_then_low_overlap_fill",
        )
        self.assertEqual(
            row["labeling_harvest_selection_policy"],
            "support_aware_new_then_support_changing_then_strong_replacement_then_capped_weak_replacement",
        )
        self.assertIn("active_seed_task_set_count_by_size", row)
        self.assertIn("labeling_harvest_max_pairwise_jaccard", row)
        self.assertIn("labeling_harvest_selected_support_changing_count", row)
        self.assertIn("labeling_harvest_selected_strong_replacement_count", row)
        self.assertIn("labeling_harvest_selected_weak_replacement_count", row)
        self.assertGreaterEqual(row["labeling_harvest_selected_count"], 0)
        self.assertGreaterEqual(row["labeling_harvest_selected_new_task_set_count"], 0)
        self.assertEqual(summary["worker_certificate_leak_count"], 0)
        self.assertEqual(summary["tail_dual_certificate_leak_count"], 0)
        self.assertEqual(summary["true_dual_rc_recompute_missing_count"], 0)
        self.assertGreaterEqual(summary["mean_labeling_harvest_selected_count"], 0.0)
        self.assertGreaterEqual(summary["mean_labeling_harvest_selected_new_task_set_count"], 0.0)
        self.assertGreater(
            summary["mean_resource_extension_label_path_variant_candidate_count"],
            0.0,
        )
        self.assertIn(
            "protected_refinement_then_source_task_count_coverage_then_low_overlap_fill",
            summary["active_seed_selection_policies"],
        )
        self.assertIn(
            "support_aware_new_then_support_changing_then_strong_replacement_then_capped_weak_replacement",
            summary["labeling_harvest_selection_policies"],
        )
        self.assertGreaterEqual(summary["mean_candidate_search_false_positive_rate"], 0.0)
        self.assertGreaterEqual(summary["mean_true_negative_candidate_search_miss_rate"], 0.0)
        self.assertGreaterEqual(summary["candidate_search_false_positive_row_count"], 0)
        self.assertGreaterEqual(summary["true_negative_candidate_search_miss_row_count"], 0)

    def test_b3_node_relaxed_worker_exports_active_columns_for_same_run_resume(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)

        result = solve_node_pricing_with_b2b_r3(
            data,
            max_direct_tasks=5,
            max_rounds=1,
            max_columns_per_round=3,
            worker_pricer_kind=RELAXED_LABELING_WORKER,
            return_active_columns_payload=True,
        )

        self.assertEqual(result["certificate_scope"], "DIAGNOSTIC_PRICING_FRONTIER")
        self.assertFalse(result["uses_true_dual_bpc_certificate"])
        self.assertEqual(result["active_columns_payload_version"], "journey_solution_payload.v1")
        self.assertGreater(len(result["active_columns"]), result["initial_column_count"])
        self.assertEqual(result["history"][0]["worker_pricer_kind"], RELAXED_LABELING_WORKER)
        self.assertEqual(result["history"][0]["pricing_proof_kind"], PROOF_KIND_RELAXED_WORKER_UNCERTIFIED)

    def test_b3_node_relaxed_worker_timeout_remains_incomplete_not_local_no_column(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        initial_columns = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
        timeout_payload = {
            "status": "RELAXED_WORKER_TIME_LIMIT",
            "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
            "timeout_stage": "candidate_loop",
            "pricing_timeout": True,
            "pricing_proof_kind": PROOF_KIND_RELAXED_WORKER_UNCERTIFIED,
            "resource_label_algorithm": "ng_route_relaxed_resource_labeling",
            "resource_label_core_mode": "relaxed_ng_route_worker",
            "resource_dimensions": ["time_window", "energy"],
            "dominance_policy": "ng_route_relaxed_dominance_worker_only",
            "elementarity_policy": "ng_route_relaxed_elementarity_worker_only",
            "worker_candidate_universe_task_sets": [],
            "worker_generated_column_task_sets": [],
            "worker_generated_column_task_set_count": 0,
            "candidate_search_rc_recomputed_under_true_dual": True,
            "worker_true_dual_candidate_audit_pass": True,
            "selected_column_true_dual_rc_audit_pass": True,
        }
        final_judge_result = FinalJudgeResult(
            pricing_state=PricingState.INCOMPLETE_LIMIT,
            pricing_payload={
                "status": "MOCK_FINAL_JUDGE_INCOMPLETE",
                "exact_status": "NOT_SOLVED",
                "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
                "can_certify_no_negative": False,
                "uses_true_dual_bpc_certificate": False,
                "pricing_rc_audit_pass": False,
                "manual_rc_audit_pass": False,
                "all_priced_columns_satisfy_branch_context": True,
                "pricing_proof_kind": PROOF_KIND_EXHAUSTIVE_INCOMPLETE,
            },
            negative_columns=tuple(),
            all_priced_columns=tuple(),
        )

        with patch(
            "lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver.run_bpc_labeling_pricer",
            return_value=(timeout_payload, tuple()),
        ), patch(
            "lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver.run_true_dual_root_final_judge",
            return_value=final_judge_result,
        ):
            result = solve_node_pricing_with_b2b_r3(
                data,
                initial_columns=initial_columns,
                max_direct_tasks=5,
                max_rounds=1,
                max_columns_per_round=3,
                worker_pricer_kind=RELAXED_LABELING_WORKER,
            )

        first_round = result["history"][0]
        self.assertEqual(first_round["worker_status"], PricingState.INCOMPLETE_LIMIT.value)
        self.assertEqual(first_round["pricing_state"], PricingState.INCOMPLETE_LIMIT.value)
        self.assertEqual(first_round["worker_exit_reason"], "WORKER_INCOMPLETE_LIMIT")
        self.assertTrue(first_round["pricing_timeout"])
        self.assertTrue(first_round["worker_underlying_incomplete"])
        self.assertEqual(
            first_round["worker_underlying_pricing_state"],
            PricingState.INCOMPLETE_LIMIT.value,
        )
        self.assertEqual(first_round["worker_underlying_status"], "RELAXED_WORKER_TIME_LIMIT")
        self.assertFalse(first_round["relaxed_candidate_search_can_certify_no_negative"])
        self.assertFalse(first_round["no_column_certificate_allowed"])
        self.assertFalse(first_round["tail_dual_no_column_can_certify"])

    def test_b3_tree_passes_relaxed_worker_and_tail_dual_to_node_solver(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)

        result = solve_b3_branch_price_tree_baseline(
            data,
            max_direct_tasks=5,
            max_rounds_per_node=1,
            max_columns_per_round=0,
            max_tree_nodes=1,
            max_branch_depth=0,
            use_complete_universe_audit=False,
            run_b2_root_diagnostic=False,
            worker_pricer_kind=RELAXED_LABELING_WORKER,
            tail_dual_stabilization_enabled=True,
            tail_dual_stabilization_alpha=0.7,
            tail_dual_stabilization_window=5,
            labeling_final_judge_enabled=True,
            labeling_final_judge_max_exact_tasks=5,
        )

        root = result["nodes"][0]
        first_round = root["history"][0]
        self.assertEqual(result["worker_pricer_kind"], RELAXED_LABELING_WORKER)
        self.assertTrue(result["tail_dual_stabilization_enabled"])
        self.assertTrue(result["labeling_final_judge_enabled"])
        self.assertEqual(result["labeling_final_judge_max_exact_tasks"], 5)
        self.assertEqual(first_round["worker_pricer_kind"], RELAXED_LABELING_WORKER)
        self.assertTrue(first_round["tail_dual_stabilization"]["tail_dual_stabilization_enabled"])
        self.assertEqual(first_round["pricing_proof_kind"], PROOF_KIND_RELAXED_WORKER_UNCERTIFIED)
        self.assertEqual(first_round["pricing_engine_role"], "worker_candidate_search")
        self.assertTrue(first_round["candidate_search_only"])
        self.assertFalse(first_round["relaxed_candidate_search_can_certify_no_negative"])
        self.assertFalse(first_round["no_column_certificate_allowed"])
        self.assertEqual(first_round["ng_route_relaxation_kind"], "seed_portfolio_task_set_neighborhood")
        self.assertFalse(first_round["ng_route_relaxation_is_certificate_relaxation"])
        self.assertFalse(first_round["relaxed_route_elementarity_proof_supported"])
        self.assertEqual(first_round["dssr_refinement_status"], "hidden_negative_seed_refinement_only")
        self.assertTrue(first_round["exact_final_proof_required_after_worker"])
        self.assertEqual(first_round["exact_final_proof_expected_mode"], "exact_elementary_full_space")
        self.assertFalse(first_round["tail_dual_no_column_can_certify"])
        self.assertTrue(root["final_judge"]["labeling_final_judge_enabled"])
        self.assertEqual(root["final_judge"]["labeling_final_judge_max_exact_tasks"], 5)

    def test_b4_1_tree_closure_from_probe_accepts_relaxed_worker_config(self) -> None:
        instance = generate_instance(5, seed=629001, index=1)
        data = load_lunar_ice_data(instance)
        columns = enumerate_direct_journey_columns(data, max_exact_tasks=5).columns
        singleton_by_task = {}
        for column in columns:
            if len(column.task_set) == 1:
                singleton_by_task.setdefault(next(iter(column.task_set)), column)
        initial_columns = tuple(singleton_by_task[task_id] for task_id in data.task_ids)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance_path = tmp_path / "instance_001_logical_graph.json"
            instance_path.write_text(json.dumps(instance), encoding="utf-8")
            probe_path = tmp_path / "probe.json"
            probe_path.write_text(
                json.dumps(
                    {
                        "instance_path": str(instance_path),
                        "instance_id": data.instance_id,
                        "active_columns": [
                            column.to_solution_payload(vehicle_id=f"seed_{index:03d}")
                            for index, column in enumerate(initial_columns, start=1)
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = run_b4_1_tree_closure_from_probe(
                probe_path,
                max_rounds=1,
                max_columns_per_round=3,
                max_tree_nodes=1,
                max_branch_depth=0,
                worker_pricer_kind=RELAXED_LABELING_WORKER,
                tail_dual_stabilization_enabled=True,
                tail_dual_stabilization_alpha=0.7,
                tail_dual_stabilization_window=5,
                labeling_final_judge_enabled=True,
                labeling_final_judge_max_exact_tasks=5,
                labeling_final_judge_exact_harvest_target=4,
            )

        row = report["rows"][0]
        raw = report["tree_closure_raw_results"][0]
        self.assertEqual(row["worker_pricer_kind"], RELAXED_LABELING_WORKER)
        self.assertTrue(row["tail_dual_stabilization_enabled"])
        self.assertEqual(raw["worker_pricer_kind"], RELAXED_LABELING_WORKER)
        self.assertTrue(raw["tail_dual_stabilization_enabled"])
        self.assertTrue(raw["labeling_final_judge_enabled"])
        self.assertEqual(raw["labeling_final_judge_max_exact_tasks"], 5)
        self.assertEqual(raw["labeling_final_judge_exact_harvest_target"], 4)
        self.assertEqual(row["labeling_final_judge_exact_harvest_target"], 4)
        self.assertFalse(raw["uses_true_dual_bpc_certificate"])


if __name__ == "__main__":
    unittest.main()
