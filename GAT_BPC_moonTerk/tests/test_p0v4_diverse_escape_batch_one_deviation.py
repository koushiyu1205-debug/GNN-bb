from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import torch

from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.exact.bpc.core.column_pool import (
    BpcColumn,
    ColumnPool,
)
from lunar_ice_bpc.exact.bpc.core.column_signature import (
    ColumnSemanticSignature,
    column_signature_from_journey,
)
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.core.cuts import (
    CutContext,
    CutLineage,
    canonical_subset_row_cut,
    stable_payload_hash,
)
from lunar_ice_bpc.exact.core.branching import (
    BranchContext,
    PairBranchDecision,
    SAME_JOURNEY,
)
from lunar_ice_bpc.exact.master.journey_rmp import (
    JourneyDuals,
    manual_journey_reduced_cost,
)
from lunar_ice_bpc.exact.bpc.pricing.labeling_pricer import (
    LabelingPricingConfig,
    _select_diverse_negative_rows,
    run_bpc_labeling_pricer,
)
from lunar_ice_bpc.exact.bpc.pricing.backends import (
    PRICING_LIFECYCLE_SCOPE_ROOT_CG,
    PRICING_LIFECYCLE_SCOPE_TREE_NODE,
)
from lunar_ice_bpc.exact.bpc.master.reduced_cost import (
    ReducedCostContext,
)
from lunar_ice_bpc.exact.bpc.pricing.final_judge import (
    run_true_dual_root_final_judge,
)
from lunar_ice_bpc.exact.bpc.pricing.harvest import (
    harvest_addable_negative_columns,
)
from lunar_ice_bpc.exact.bpc.pricing.bidirectional_feasibility import (
    BIDIRECTIONAL_FEASIBILITY_POLICY_ID,
    build_static_sortie_transform,
    split_and_rejoin_journey,
    summarize_backward_suffix,
)
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (
    _apply_full_audited_one_deviation,
    _add_selected_to_pool_and_master,
    _batch_master_admission_round_fields,
    _one_deviation_memory_adverse_event,
    _record_full_audited_route_opportunity,
    _resolve_sparse_tail_deviation_decision,
    _sparse_tail_policy_payload,
    solve_node_pricing_with_b2b_r3,
)
from lunar_ice_bpc.exact.solver.journey_driver import (
    enumerate_direct_journey_columns,
)
from lunar_ice_bpc.guidance.one_deviation import (
    OneDeviationLedger,
    TwoHeadOneDeviationGAT,
    calibrate_one_deviation_thresholds,
    one_deviation_hurdle_loss,
    select_one_deviation,
)
from lunar_ice_bpc.guidance.sparse_tail_action import (
    SPARSE_TAIL_ACTIONS,
    SPARSE_TAIL_GAT_MANIFEST_SCHEMA,
    SPARSE_TAIL_GAT_MODEL_SCHEMA,
    SparseTailGatPolicy,
    TwoHeadSparseTailActionGAT,
    build_sparse_tail_action_features,
    choose_sparse_tail_action,
    sparse_tail_feature_schema,
    sparse_tail_two_head_loss,
    tensorize_sparse_tail_action_features,
)
from lunar_ice_bpc.guidance.one_deviation_oracle import (
    REQUIRED_STATE_HASHES,
    audit_one_deviation_oracle,
    build_one_deviation_oracle_context,
    materialize_one_deviation_time_labels,
    validate_one_deviation_rollouts,
)
from lunar_ice_bpc.guidance.one_deviation_rollout import (
    _matched_cut_lineage,
    _public_exact_result,
    action_initial_columns,
    build_matched_rollout_context,
    materialize_matched_rollout_rows,
    selected_exact_runtime_binding,
)
from lunar_ice_bpc.guidance.route_admission import (
    ONE_DEVIATION_NOOP_ACTION_ID,
    audit_route_opportunity_census,
    build_one_deviation_actions,
    build_route_admission_snapshot,
    fixed_exact_admission_batch_size,
    validate_route_admission_snapshot,
    validate_route_opportunity_census_binding,
)


def _columns(count: int = 8):
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    columns = enumerate_direct_journey_columns(
        data, max_exact_tasks=5
    ).columns
    return tuple(columns[:count])


def _bpc_columns():
    return tuple(
        BpcColumn(
            signature=column_signature_from_journey(column),
            objective=column.objective,
            payload=column,
        )
        for column in _columns()
    )


def _training_runtime_binding(scale: int) -> dict:
    scale_value = int(scale)
    payload = {
        "schema_version": (
            "lunar_ice_bpc.one_deviation_exact_runtime_binding.v1"
        ),
        "selected_config": "/tmp/selected-v5.yaml",
        "selected_config_sha256": "selected-v5-config-hash",
        "scale": scale_value,
        "backend_id": (
            "native_rcspp_bidirectional_root_partial_hybrid_v3"
        ),
        "graph_cache_entries": 1,
        "completion_bound_enabled": False,
        "subset_dominance_enabled": True,
        "cut_state_enabled": True,
        "negative_escape_enabled": True,
        "batch_master_admission_enabled": True,
        "admission_batch_size": 64 if scale_value == 30 else 128,
        "raw_negative_pool_multiplier": 4,
        "negative_escape_policy_id": (
            "diverse_raw_4x_then_p0v4_selector_v1"
        ),
        "worker_ng_sizes": (
            [6, 10, 14, 30]
            if scale_value == 30
            else [8, 16, 32, 50]
        ),
        "worker_hard_time_cap_sec": (
            180.0 if scale_value == 30 else 300.0
        ),
        "exact_final_judge_first": True,
        "final_judge_pass_policy": (
            "branch_adaptive_sparse_harvest_v1"
            if scale_value == 30
            else "harvest_then_proof"
        ),
        "adaptive_harvest_cap_sec": (
            2.0 if scale_value == 30 else None
        ),
        "live_sri_policy": "P0_GROUP_SCREEN_V1",
    }
    payload["runtime_binding_hash"] = stable_payload_hash(payload)
    return payload


def _load_sparse_tail_replay_module():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "replay_p0v4_sparse_tail_deviation.py"
    )
    spec = importlib.util.spec_from_file_location(
        "replay_p0v4_sparse_tail_deviation",
        path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sparse_tail_deviation_targets_are_one_call_and_restore_v5(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_sparse_tail_replay_module()
    assert module._action_targets("P0", frozen_batch_size=64) == (
        64,
        256,
    )
    assert module._action_targets("S1", frozen_batch_size=64) == (1, 1)
    assert module._action_targets("S4", frozen_batch_size=64) == (4, 4)
    with pytest.raises(ValueError, match="unsupported sparse-tail action"):
        module._action_targets("S8", frozen_batch_size=64)

    instance_payload = generate_instance(30, seed=629_930, index=1)
    data = load_lunar_ice_data(instance_payload)
    instance_path = tmp_path / "instance.json"
    instance_path.write_text(json.dumps(instance_payload), encoding="utf-8")
    probe_path = tmp_path / "probe.json"
    probe_path.write_text(
        json.dumps(
            {
                "instance_id": data.instance_id,
                "history": [
                    {
                        "round": 17,
                        "node_id": "root",
                        "branch_context_active": False,
                        "pricing_state": "FOUND_NEGATIVE",
                        "raw_unique_negative_count": 7,
                        "selected_diverse_negative_count": 1,
                        "labeling_final_judge_effective_exact_harvest_target": 64,
                        "labeling_final_judge_proof_pass_wall_time": 212.0,
                        "dual_context": {
                            "dual_fingerprint": "dual-hash",
                            "rmp_iteration_id": "root-17",
                            "fleet_dual": 0.1,
                            "task_duals": {
                                task_id: 0.2 for task_id in data.task_ids
                            },
                            "cut_duals": {},
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    context = module._context_from_probe(
        probe_path=probe_path,
        instance_path=instance_path,
        round_index=17,
        action="S1",
    )
    assert context["frozen_batch_size"] == 64
    assert context["admission_batch_size"] == 1
    assert context["raw_negative_pool_size"] == 1

    from lunar_ice_bpc.exact.bpc.pricing.backends import BackendResult

    class _Backend:
        def solve(self, request):
            assert request.exact_negative_escape_enabled
            assert request.exact_admission_batch_size == 1
            assert request.exact_raw_negative_pool_size == 1
            assert request.pricing_lifecycle_scope == (
                PRICING_LIFECYCLE_SCOPE_ROOT_CG
            )
            return BackendResult(
                backend_id=module.DEFAULT_BACKEND,
                engine_status="FOUND_NEGATIVE_PARTIAL",
                best_found_rc=-0.25,
                global_min_rc=None,
                global_min_rc_is_exact=False,
                proved_no_rc_below=None,
                unexplored_rc_lower_bound=None,
                search_exhaustive=False,
                frontier_empty=False,
                labels_dropped=False,
                partial_columns_valid=True,
                columns=(_columns(1)[0],),
                certificate_blockers=(
                    "native_exact_search_incomplete",
                    "native_frontier_not_empty",
                    "native_exact_negative_escape_partial",
                ),
                telemetry={
                    "negative_escape_triggered": True,
                    "negative_escape_termination_reason": (
                        "RAW_TRUE_NEGATIVE_POOL_REACHED"
                    ),
                    "raw_unique_negative_count": 1,
                    "wall_time_seconds": 0.5,
                },
            )

    monkeypatch.setattr(
        module.BackendRegistry,
        "create",
        lambda _backend_id: _Backend(),
    )
    output_path = tmp_path / "replay.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "replay_p0v4_sparse_tail_deviation.py",
            "--probe",
            str(probe_path),
            "--instance",
            str(instance_path),
            "--round",
            "17",
            "--action",
            "S1",
            "--wall-time-limit-sec",
            "30",
            "--output",
            str(output_path),
        ],
    )
    assert module.main() == 0
    replay = json.loads(output_path.read_text(encoding="utf-8"))
    assert replay["status"] == "SAFE_REPLAY_COMPLETE"
    assert replay["negative_escape_triggered"]
    assert not replay["backend_can_enter_certificate_audit"]
    assert replay["safety"]["issues"] == []
    assert replay["safety"]["replay_certificate_authority"] == "none"
    assert not replay["safety"]["can_certify_from_replay"]
    assert replay["safety"]["next_round_policy"] == "restore_frozen_v5"


def test_sparse_tail_replay_rejects_unbound_branch_or_cut_context() -> None:
    module = _load_sparse_tail_replay_module()
    base = {
        "round": 1,
        "node_id": "root",
        "branch_context_active": False,
        "dual_context": {
            "task_duals": {"task": 1.0},
            "cut_duals": {},
        },
    }
    branch = deepcopy(base)
    branch["branch_context_active"] = True
    with pytest.raises(ValueError, match="active branch context"):
        module._round_row({"history": [branch]}, 1)
    cut = deepcopy(base)
    cut["dual_context"]["cut_duals"] = {"cut": 0.5}
    with pytest.raises(ValueError, match="complete cut context"):
        module._round_row({"history": [cut]}, 1)


def test_one_deviation_runtime_uses_selected_v5_backend(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "selected_v5.yaml"
    config_path.write_text(
        json.dumps(
            {
                "live_sri_policy": "P0_GROUP_SCREEN_V1",
                "native_completion_bound_enabled": False,
                "native_subset_dominance_enabled": True,
                "native_cut_state_enabled": True,
                "native_final_judge_pass_policy": "harvest_then_proof",
                "native_final_judge_pass_policy_by_scale": {
                    "30": "branch_adaptive_sparse_harvest_v1"
                },
                "native_adaptive_harvest_cap_sec_by_scale": {"30": 2.0},
                "exact_negative_escape_enabled": True,
                "exact_raw_negative_pool_multiplier": 4,
                "exact_negative_escape_policy_id": (
                    "diverse_raw_4x_then_p0v4_selector_v1"
                ),
                "batch_master_admission_enabled": True,
                "profiles": {
                    "30": {
                        "backend_id": (
                            "native_rcspp_bidirectional_"
                            "root_partial_hybrid_v3"
                        ),
                        "harvest_target": 64,
                        "ng_sizes": [6, 10, 14, 30],
                        "graph_cache_entries": 1,
                        "worker_time_limit_sec": 180,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    binding = selected_exact_runtime_binding(
        {
            "status": "FIXED_K_SELECTED",
            "selected_config": str(config_path),
            "selected_config_sha256": hashlib.sha256(
                config_path.read_bytes()
            ).hexdigest(),
        },
        scale=30,
    )
    assert binding["backend_id"] == (
        "native_rcspp_bidirectional_root_partial_hybrid_v3"
    )
    assert binding["admission_batch_size"] == 64
    assert binding["raw_negative_pool_multiplier"] == 4
    assert binding["final_judge_pass_policy"] == (
        "branch_adaptive_sparse_harvest_v1"
    )
    assert binding["adaptive_harvest_cap_sec"] == 2.0
    assert binding["runtime_binding_hash"]

    from lunar_ice_bpc.guidance.one_deviation_runtime import (
        _validate_exact_runtime_environment,
    )

    environment = {
        "LUNAR_ICE_SPPRC_EXACT_BACKEND": binding["backend_id"],
        "LUNAR_ICE_SPPRC_GRAPH_CACHE_ENTRIES": "1",
        "LUNAR_ICE_SPPRC_COMPLETION_BOUND": "0",
        "LUNAR_ICE_SPPRC_SUBSET_DOMINANCE": "1",
        "LUNAR_ICE_SPPRC_CUT_STATE": "1",
        "LUNAR_ICE_EXACT_NEGATIVE_ESCAPE_ENABLED": "1",
        "LUNAR_ICE_BATCH_MASTER_ADMISSION_ENABLED": "1",
        "LUNAR_ICE_LABELING_WORKER_NG_SIZES": "6,10,14,30",
        "LUNAR_ICE_LABELING_WORKER_HARD_TIME_CAP_SEC": "180",
        "LUNAR_ICE_EXACT_FINAL_JUDGE_FIRST": "1",
        "LUNAR_ICE_LABELING_FINAL_JUDGE_PASS_POLICY": (
            "branch_adaptive_sparse_harvest_v1"
        ),
        (
            "LUNAR_ICE_LABELING_FINAL_JUDGE_"
            "ADAPTIVE_HARVEST_CAP_SEC"
        ): "2.0",
    }
    _validate_exact_runtime_environment(
        binding, environment=environment
    )
    environment["LUNAR_ICE_SPPRC_SUBSET_DOMINANCE"] = "0"
    with pytest.raises(ValueError, match="runtime environment mismatch"):
        _validate_exact_runtime_environment(
            binding, environment=environment
        )


def test_bidirectional_depot_join_replays_p0v4_route_and_true_rc() -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    universe = enumerate_direct_journey_columns(
        data,
        max_exact_tasks=5,
    )
    cut = canonical_subset_row_cut(data.task_ids[:3])
    cut_context = CutContext(cuts=(cut,))
    duals = JourneyDuals(
        cover={
            task_id: 0.05 * (index + 1)
            for index, task_id in enumerate(data.task_ids)
        },
        fleet_limit=0.17,
        cuts={cut.cut_id: 0.31},
    )
    assert universe.columns
    assert any(len(column.sorties) > 1 for column in universe.columns)
    for column in universe.columns:
        expected_rc = manual_journey_reduced_cost(
            column,
            duals,
            cut_coefficients=cut_context.coefficients_for(column),
        )
        for split in range(len(column.sorties) + 1):
            audit = split_and_rejoin_journey(
                data,
                column,
                split_sortie_index=split,
                true_duals=duals,
                cut_context=cut_context,
            )
            assert audit.feasible, audit
            assert audit.status == "FEASIBLE_JOIN_DIAGNOSTIC_ONLY"
            assert audit.policy_id == BIDIRECTIONAL_FEASIBILITY_POLICY_ID
            assert not audit.can_certify_no_negative
            assert audit.journey is not None
            joined_signature = column_signature_from_journey(audit.journey)
            source_signature = column_signature_from_journey(column)
            assert joined_signature.task_set == source_signature.task_set
            assert joined_signature.sortie_partition == (
                source_signature.sortie_partition
            )
            assert joined_signature.path_option_signature == (
                source_signature.path_option_signature
            )
            assert audit.journey.objective == pytest.approx(
                column.objective,
                abs=2.0e-6,
            )
            assert audit.true_reduced_cost == pytest.approx(
                expected_rc,
                abs=1.0e-9,
            )
            assert audit.objective_drift is not None
            assert audit.objective_drift <= 2.0e-6
            assert audit.weighted_completion_drift is not None
            assert audit.weighted_completion_drift <= 2.0e-5


def test_bidirectional_suffix_boundary_and_branch_fail_closed() -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    columns = enumerate_direct_journey_columns(
        data,
        max_exact_tasks=5,
    ).columns
    multi = next(column for column in columns if len(column.sorties) > 1)
    transforms = tuple(
        build_static_sortie_transform(
            data,
            sortie.tasks,
            tuple(leg.path_type for leg in sortie.legs),
        )
        for sortie in multi.sorties
    )
    suffix = summarize_backward_suffix(transforms[1:])
    assert suffix.structurally_feasible
    assert suffix.accepts(multi.sorties[0].end_time)
    assert not suffix.accepts(suffix.latest_input_time + 1.0e-3)

    singleton = next(
        column for column in columns if len(column.task_set) == 1
    )
    present = next(iter(singleton.task_set))
    absent = next(
        task_id for task_id in data.task_ids if task_id != present
    )
    branch = BranchContext(
        pair_decisions=(
            PairBranchDecision(
                task_a=present,
                task_b=absent,
                sense=SAME_JOURNEY,
            ),
        )
    )
    audit = split_and_rejoin_journey(
        data,
        singleton,
        split_sortie_index=0,
        true_duals=JourneyDuals(cover={}),
        branch_context=branch,
    )
    assert not audit.feasible
    assert not audit.branch_feasible
    assert audit.status == "BRANCH_CONTEXT_INFEASIBLE"
    assert not audit.can_certify_no_negative


def test_batch_pool_and_view_match_ordered_scalar_admission() -> None:
    base_columns = _bpc_columns()
    columns = (
        *base_columns[:3],
        base_columns[1],
        *base_columns[3:],
    )
    scalar_pool = ColumnPool()
    scalar_view = MasterColumnView()
    scalar_results = []
    scalar_view_results = []
    for column in columns:
        scalar_results.append(
            scalar_pool.add(
                column,
                {
                    "master_view": scalar_view,
                    "node_id": "node",
                },
            )
        )
        scalar_view_results.append(
            scalar_view.add_from_pool(
                column, node_id="node", pool=scalar_pool
            )
        )

    batch_pool = ColumnPool()
    batch_view = MasterColumnView()
    batch_results, batch_view_results = (
        batch_view.admit_many_atomically(
            columns, node_id="node", pool=batch_pool
        )
    )
    assert [row.added for row in batch_results] == [
        row.added for row in scalar_results
    ]
    assert [row.reason for row in batch_results] == [
        row.reason for row in scalar_results
    ]
    assert [
        row.addability_report.reject_reason
        for row in batch_results
        if row.addability_report is not None
    ] == [
        row.addability_report.reject_reason
        for row in scalar_results
        if row.addability_report is not None
    ]
    assert batch_view_results == tuple(scalar_view_results)
    assert list(batch_pool.columns_by_signature) == list(
        scalar_pool.columns_by_signature
    )
    assert batch_view.signatures_by_node == (
        scalar_view.signatures_by_node
    )


def test_solver_batch_admission_matches_p0_scalar_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    columns = _columns()
    scalar_pool = ColumnPool()
    scalar_view = MasterColumnView()
    scalar_timing = {}
    monkeypatch.setenv(
        "LUNAR_ICE_BATCH_MASTER_ADMISSION_ENABLED", "0"
    )
    scalar_added = _add_selected_to_pool_and_master(
        scalar_pool,
        scalar_view,
        columns,
        timing_payload=scalar_timing,
    )
    batch_pool = ColumnPool()
    batch_view = MasterColumnView()
    batch_timing = {}
    monkeypatch.setenv(
        "LUNAR_ICE_BATCH_MASTER_ADMISSION_ENABLED", "1"
    )
    batch_added = _add_selected_to_pool_and_master(
        batch_pool,
        batch_view,
        columns,
        timing_payload=batch_timing,
    )
    assert batch_added == scalar_added
    assert batch_pool.columns_by_signature == (
        scalar_pool.columns_by_signature
    )
    assert batch_view.signatures_by_node == (
        scalar_view.signatures_by_node
    )
    assert not scalar_timing["batch_master_admission_enabled"]
    assert batch_timing["batch_master_admission_enabled"]
    assert "batch_pool_wall_time_sec" in batch_timing
    assert "batch_master_view_wall_time_sec" in batch_timing
    persisted_timing = _batch_master_admission_round_fields(
        batch_timing
    )
    assert persisted_timing["batch_master_admission_enabled"]
    assert persisted_timing["batch_master_admission_input_count"] == len(
        columns
    )
    assert "batch_master_total_wall_time_sec" in persisted_timing
    assert "unrelated" not in _batch_master_admission_round_fields(
        {"unrelated": 1}
    )


def test_diverse_negative_escape_selects_k_and_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    monkeypatch.setenv(
        "LUNAR_ICE_SPPRC_EXACT_BACKEND",
        "native_rcspp_inprocess",
    )
    payload, columns, audited_candidate_order = (
        run_bpc_labeling_pricer(
        data,
        JourneyDuals(
            cover={task_id: 100.0 for task_id in data.task_ids}
        ),
        config=LabelingPricingConfig(
            max_exact_tasks=5,
            exact_negative_escape_enabled=True,
            exact_admission_batch_size=2,
            exact_raw_negative_pool_size=8,
        ),
        return_audited_candidate_order=True,
        )
    )
    assert payload["negative_escape_triggered"]
    assert payload["raw_unique_negative_count"] == 8
    assert payload["native_raw_unique_negative_count"] == 8
    assert (
        payload["audited_raw_unique_negative_count"]
        <= payload["native_raw_unique_negative_count"]
    )
    assert payload["selected_diverse_negative_count"] == 2
    assert len(columns) == 2
    assert len(audited_candidate_order) >= len(columns) + 1
    assert tuple(
        column_signature_from_journey(column)
        for column in audited_candidate_order[:2]
    ) == tuple(
        column_signature_from_journey(column)
        for column in columns
    )
    assert not payload["can_certify_no_negative"]
    assert payload["pricing_state"] == "FOUND_NEGATIVE"
    assert payload["harvest_selected_true_rc_distribution"]["count"] == 2
    assert payload["harvest_max_pairwise_containment"] >= 0.0


def test_escape_diversity_keeps_only_best_same_task_set_representative() -> None:
    rows = [
        {
            "signature": f"sig-{index}",
            "task_set": task_set,
            "true_reduced_cost": reduced_cost,
            "objective": objective,
            "task_set_harvest_bucket": "new_task_set",
        }
        for index, (task_set, reduced_cost, objective) in enumerate(
            (
                (("A",), -3.0, 3.0),
                (("A",), -2.0, 2.0),
                (("B",), -1.0, 1.0),
            )
        )
    ]
    selected = _select_diverse_negative_rows(
        rows,
        harvest_target=3,
        unique_task_sets_only=True,
    )
    assert len(selected) == 2
    assert [row["task_set"] for row in selected] == [("A",), ("B",)]
    assert selected[0]["true_reduced_cost"] == -3.0


def test_full_diverse_order_preserves_every_fixed_k_prefix() -> None:
    generator = random.Random(629_045)
    for trial in range(100):
        rows = []
        for index in range(generator.randint(12, 48)):
            task_ids = tuple(
                sorted(
                    {
                        f"T{generator.randrange(12):02d}"
                        for _ in range(generator.randint(1, 5))
                    }
                )
            )
            rows.append(
                {
                    "signature": f"{trial}:{index}",
                    "task_set": task_ids,
                    "true_reduced_cost": -generator.random() - 1.0e-3,
                    "objective": generator.random() * 100.0,
                    "task_set_harvest_bucket": generator.choice(
                        (
                            "new_task_set",
                            "support_changing",
                            "strong_replacement",
                            "weak_replacement",
                        )
                    ),
                }
            )
        full_order = _select_diverse_negative_rows(
            rows,
            harvest_target=len(rows),
            unique_task_sets_only=True,
        )
        for target in (1, 2, 4, 8, 16):
            expected = _select_diverse_negative_rows(
                rows,
                harvest_target=target,
                unique_task_sets_only=True,
            )
            assert full_order[: len(expected)] == expected


def test_full_audited_pool_records_boundary_without_changing_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    columns = _columns(16)
    active, exact_selected, audited_order = (
        columns[0],
        columns[1:3],
        columns[1:14],
    )
    pool = ColumnPool()
    view = MasterColumnView()
    active_bpc = BpcColumn(
        column_signature_from_journey(active),
        active.objective,
        active,
    )
    assert pool.add(active_bpc).added
    assert view.add_from_pool(
        active_bpc, node_id="root", pool=pool
    )
    duals = JourneyDuals(
        cover={task_id: 100.0 for task_id in data.task_ids}
    )
    selected_pairs = tuple(
        (-1.0 - index, column)
        for index, column in enumerate(exact_selected)
    )
    _selected, actual = harvest_addable_negative_columns(
        selected_pairs,
        pool=pool,
        view=view,
        node_id="root",
        max_selected=2,
        active_task_sets={frozenset(active.task_set)},
    )
    monkeypatch.setenv(
        "LUNAR_ICE_GAT_TRAINING_ROWS_DIR", str(tmp_path)
    )
    observation = _record_full_audited_route_opportunity(
        data=data,
        judge=SimpleNamespace(
            all_priced_columns=exact_selected,
            audited_candidate_order=audited_order,
        ),
        actual_harvest_payload=actual,
        pool=pool,
        view=view,
        duals=duals,
        node_id="root",
        negative_eps=1.0e-6,
        max_selected=2,
        active_task_sets={frozenset(active.task_set)},
        rmp_iteration_id="root:1",
    )
    assert observation["recorded"]
    assert observation["addable_negative_count"] >= 10
    snapshot_paths = tuple(
        tmp_path.rglob("route_admission_snapshot.json")
    )
    assert len(snapshot_paths) == 1
    snapshot = validate_route_admission_snapshot(
        json.loads(snapshot_paths[0].read_text(encoding="utf-8"))
    )
    assert snapshot["p0_selected_candidate_ids"] == actual[
        "p0_selected_candidate_ids_in_execution_order"
    ]
    assert len(snapshot["p0_ordered_candidate_ids"]) > 2
    assert (
        column_signature_from_journey(audited_order[-1])
        not in pool.columns_by_signature
    )


def test_full_audited_pool_applies_only_rank_k_promotion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    columns = _columns(16)
    active, exact_selected, audited_order = (
        columns[0],
        columns[1:3],
        columns[1:14],
    )
    pool = ColumnPool()
    view = MasterColumnView()
    active_bpc = BpcColumn(
        column_signature_from_journey(active),
        active.objective,
        active,
    )
    assert pool.add(active_bpc).added
    assert view.add_from_pool(
        active_bpc, node_id="root", pool=pool
    )
    duals = JourneyDuals(
        cover={task_id: 100.0 for task_id in data.task_ids}
    )
    _selected, preliminary = harvest_addable_negative_columns(
        tuple(
            (-1.0 - index, column)
            for index, column in enumerate(exact_selected)
        ),
        pool=pool,
        view=view,
        node_id="root",
        max_selected=2,
        active_task_sets={frozenset(active.task_set)},
    )
    monkeypatch.setenv(
        "LUNAR_ICE_ONE_DEVIATION_MANIFEST",
        "/tmp/calibrated-deployment.json",
    )

    def promote_first_omitted(
        *, ordered_candidates, **_kwargs
    ):
        return (
            SimpleNamespace(
                promotes=True,
                promoted_candidate_id=ordered_candidates[2][
                    "candidate_id"
                ],
            ),
            {"test_runtime": True},
        )

    with patch(
        "lunar_ice_bpc.guidance.one_deviation_runtime."
        "infer_one_deviation_from_environment",
        side_effect=promote_first_omitted,
    ):
        result = _apply_full_audited_one_deviation(
            data=data,
            judge=SimpleNamespace(
                all_priced_columns=exact_selected,
                audited_candidate_order=audited_order,
            ),
            preliminary_harvest_payload=preliminary,
            pool=pool,
            view=view,
            duals=duals,
            node_id="root",
            negative_eps=1.0e-6,
            max_selected=2,
            active_task_sets={frozenset(active.task_set)},
            rmp_iteration_id="root:1",
        )
    assert result is not None
    promoted, payload = result
    assert len(promoted) == 2
    assert column_signature_from_journey(promoted[0]) == (
        column_signature_from_journey(_selected[0])
    )
    assert column_signature_from_journey(promoted[1]) != (
        column_signature_from_journey(_selected[1])
    )
    assert payload["one_deviation_executed"]
    assert payload["full_audited_one_deviation_path"]
    assert len(pool.columns_by_signature) == 1


def test_zero_addable_escape_restarts_exhaustive_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    duplicate = _columns(1)[0]
    pool = ColumnPool()
    view = MasterColumnView()
    stored = BpcColumn(
        column_signature_from_journey(duplicate),
        duplicate.objective,
        duplicate,
    )
    assert pool.add(stored).added
    assert view.add_from_pool(stored, node_id="root", pool=pool)
    dual_values = {
        task_id: 100.0 for task_id in data.task_ids
    }
    context = ReducedCostContext(
        task_duals=dual_values,
        fleet_dual=0.0,
        dual_fingerprint="dual",
        rmp_iteration_id="root-1",
    )
    first_payload = {
        "pricing_state": "FOUND_NEGATIVE",
        "pricing_proof_kind": "EXHAUSTIVE_INCOMPLETE",
        "can_certify_no_negative": False,
        "true_best_reduced_cost": -1.0,
        "pricing_best_reduced_cost": -1.0,
        "true_audited_column_count": 1,
        "negative_escape_triggered": True,
        "negative_escape_termination_reason": "raw_pool_target_reached",
        "raw_unique_negative_count": 4,
        "selected_diverse_negative_count": 1,
    }
    second_payload = {
        "pricing_state": "CERTIFIED_NO_NEGATIVE",
        "pricing_proof_kind": "EXHAUSTIVE_NO_NEGATIVE",
        "can_certify_no_negative": True,
        "true_best_reduced_cost": None,
        "pricing_best_reduced_cost": None,
        "true_audited_column_count": 0,
    }
    monkeypatch.setenv(
        "LUNAR_ICE_EXACT_NEGATIVE_ESCAPE_ENABLED", "1"
    )
    seen_configs = []

    def fake_pricer(*_args, config, **_kwargs):
        seen_configs.append(config)
        if len(seen_configs) == 1:
            return dict(first_payload), (duplicate,)
        return dict(second_payload), tuple()

    with patch(
        "lunar_ice_bpc.exact.bpc.pricing.final_judge."
        "run_bpc_labeling_pricer",
        side_effect=fake_pricer,
    ):
        result = run_true_dual_root_final_judge(
            data,
            context,
            labeling_final_judge_enabled=True,
            labeling_final_judge_max_exact_tasks=5,
            labeling_final_judge_exact_harvest_target=1,
            labeling_final_judge_pass_strategy="proof_only",
            column_pool=pool,
            master_view=view,
            node_id="root",
            active_task_sets={frozenset(duplicate.task_set)},
        )
    assert len(seen_configs) == 2
    assert all(
        config.pricing_lifecycle_scope
        == PRICING_LIFECYCLE_SCOPE_ROOT_CG
        for config in seen_configs
    )
    assert seen_configs[0].exact_negative_escape_enabled
    assert not seen_configs[1].exact_negative_escape_enabled
    assert result.pricing_payload[
        "negative_escape_zero_addable_fallback_used"
    ]
    assert result.pricing_payload["can_certify_no_negative"]


def test_sparse_tail_one_deviation_returns_partial_true_negative_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    column = _columns(1)[0]
    context = ReducedCostContext(
        task_duals={task_id: 100.0 for task_id in data.task_ids},
        fleet_dual=0.0,
        dual_fingerprint="sparse-dual",
        rmp_iteration_id="root-sparse",
    )
    true_rc = manual_journey_reduced_cost(
        column,
        JourneyDuals(
            cover={task_id: 100.0 for task_id in data.task_ids}
        ),
    )
    harvest_payload = {
        "pricing_state": "INCOMPLETE_LIMIT",
        "pricing_proof_kind": "EXHAUSTIVE_INCOMPLETE",
        "can_certify_no_negative": False,
        "true_best_reduced_cost": None,
        "true_audited_column_count": 0,
    }
    sparse_payload = {
        "pricing_state": "FOUND_NEGATIVE",
        "pricing_proof_kind": "EXHAUSTIVE_INCOMPLETE",
        "can_certify_no_negative": False,
        "true_best_reduced_cost": true_rc,
        "pricing_best_reduced_cost": true_rc,
        "true_audited_column_count": 1,
        "negative_escape_triggered": True,
        "negative_escape_termination_reason": (
            "RAW_TRUE_NEGATIVE_POOL_REACHED"
        ),
        "raw_unique_negative_count": 1,
        "selected_diverse_negative_count": 1,
    }
    seen = []

    def fake_pricer(*_args, config, **_kwargs):
        seen.append(config)
        if len(seen) == 1:
            return dict(harvest_payload), tuple()
        return dict(sparse_payload), (column,)

    monkeypatch.setenv(
        "LUNAR_ICE_EXACT_NEGATIVE_ESCAPE_ENABLED", "1"
    )
    with patch(
        "lunar_ice_bpc.exact.bpc.pricing.final_judge."
        "run_bpc_labeling_pricer",
        side_effect=fake_pricer,
    ):
        result = run_true_dual_root_final_judge(
            data,
            context,
            node_id="node_000",
            labeling_final_judge_enabled=True,
            labeling_final_judge_max_exact_tasks=5,
            labeling_final_judge_exact_harvest_target=8,
            labeling_final_judge_pass_strategy="harvest_then_proof",
            one_deviation_sparse_tail_action="S1",
            one_deviation_sparse_tail_negative_eps=3.0e-6,
            one_deviation_sparse_tail_time_cap_sec=7.0,
        )
    assert len(seen) == 2
    assert seen[0].stop_at_first_negative
    assert not seen[0].exact_negative_escape_enabled
    assert not seen[1].stop_at_first_negative
    assert seen[1].exact_negative_escape_enabled
    assert seen[1].exact_admission_batch_size == 1
    assert seen[1].exact_raw_negative_pool_size == 1
    assert seen[1].negative_eps == pytest.approx(3.0e-6)
    assert seen[1].wall_time_limit_sec == pytest.approx(7.0)
    assert result.pricing_state.value == "FOUND_NEGATIVE"
    assert result.negative_columns == (column,)
    assert result.pricing_payload[
        "one_deviation_sparse_tail_attempted"
    ]
    assert result.pricing_payload[
        "one_deviation_sparse_tail_executed"
    ]
    assert not result.pricing_payload[
        "labeling_final_judge_proof_pass_attempted"
    ]
    assert result.pricing_payload[
        "labeling_final_judge_proof_pass_skip_reason"
    ] == "one_deviation_sparse_tail_found_true_negative"
    assert not result.pricing_payload["can_certify_no_negative"]
    assert result.pricing_payload[
        "one_deviation_sparse_tail_certificate_authority"
    ] == "none"
    assert result.pricing_payload[
        "one_deviation_sparse_tail_next_round_policy"
    ] == "restore_frozen_v5"
    assert result.pricing_payload[
        "one_deviation_sparse_tail_time_cap_sec"
    ] == pytest.approx(7.0)
    assert result.pricing_payload[
        "one_deviation_sparse_tail_time_cap_applied"
    ]


def test_sparse_tail_miss_runs_official_frozen_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    context = ReducedCostContext(
        task_duals={task_id: 0.0 for task_id in data.task_ids},
        fleet_dual=0.0,
        dual_fingerprint="sparse-miss-dual",
        rmp_iteration_id="root-sparse-miss",
    )
    incomplete = {
        "pricing_state": "INCOMPLETE_LIMIT",
        "pricing_proof_kind": "EXHAUSTIVE_INCOMPLETE",
        "can_certify_no_negative": False,
        "true_best_reduced_cost": None,
        "true_audited_column_count": 0,
    }
    strict_only_certificate = {
        "pricing_state": "CERTIFIED_NO_NEGATIVE",
        "pricing_proof_kind": "EXHAUSTIVE_NO_NEGATIVE",
        "can_certify_no_negative": True,
        "true_best_reduced_cost": None,
        "true_audited_column_count": 0,
    }
    official_certificate = dict(strict_only_certificate)
    seen = []

    def fake_pricer(*_args, config, **_kwargs):
        seen.append(config)
        if len(seen) == 1:
            return dict(incomplete), tuple()
        if len(seen) == 2:
            return dict(strict_only_certificate), tuple()
        return dict(official_certificate), tuple()

    monkeypatch.setenv(
        "LUNAR_ICE_EXACT_NEGATIVE_ESCAPE_ENABLED", "1"
    )
    with patch(
        "lunar_ice_bpc.exact.bpc.pricing.final_judge."
        "run_bpc_labeling_pricer",
        side_effect=fake_pricer,
    ):
        result = run_true_dual_root_final_judge(
            data,
            context,
            labeling_final_judge_enabled=True,
            labeling_final_judge_max_exact_tasks=5,
            labeling_final_judge_exact_harvest_target=8,
            labeling_final_judge_pass_strategy="harvest_then_proof",
            one_deviation_sparse_tail_action="S1",
            one_deviation_sparse_tail_negative_eps=3.0e-6,
        )
    assert len(seen) == 3
    assert seen[1].negative_eps == pytest.approx(3.0e-6)
    assert seen[1].exact_admission_batch_size == 1
    assert seen[1].exact_raw_negative_pool_size == 1
    assert seen[2].negative_eps == pytest.approx(1.0e-6)
    assert seen[2].exact_admission_batch_size == 8
    assert seen[2].exact_raw_negative_pool_size == 32
    assert result.pricing_state.value == "CERTIFIED_NO_NEGATIVE"
    assert result.pricing_payload["can_certify_no_negative"]
    assert result.pricing_payload[
        "one_deviation_sparse_tail_attempted"
    ]
    assert not result.pricing_payload[
        "one_deviation_sparse_tail_executed"
    ]
    assert result.pricing_payload[
        "one_deviation_sparse_tail_fallback_reason"
    ] == "no_official_true_negative_from_sparse_pass"
    assert result.pricing_payload[
        "labeling_final_judge_proof_pass_attempted"
    ]


def test_sparse_tail_policy_is_invoked_only_after_empty_harvest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    context = ReducedCostContext(
        task_duals={task_id: 1.0 for task_id in data.task_ids},
        fleet_dual=0.0,
        dual_fingerprint="post-harvest-policy-dual",
        rmp_iteration_id="root-post-harvest-policy",
    )
    column = enumerate_direct_journey_columns(
        data,
        max_exact_tasks=5,
    ).columns[0]
    true_rc = manual_journey_reduced_cost(
        column,
        JourneyDuals(
            cover=context.task_duals,
            fleet_limit=context.fleet_dual,
        ),
    )
    assert true_rc < -1.0e-6
    harvest_empty = {
        "pricing_state": "INCOMPLETE_LIMIT",
        "pricing_proof_kind": "EXHAUSTIVE_INCOMPLETE",
        "can_certify_no_negative": False,
        "processed_labels": 123,
        "extended_labels": 456,
        "true_audited_column_count": 0,
    }
    sparse_negative = {
        "pricing_state": "FOUND_NEGATIVE",
        "pricing_proof_kind": "EXHAUSTIVE_INCOMPLETE",
        "can_certify_no_negative": False,
        "negative_escape_triggered": True,
        "negative_escape_termination_reason": (
            "RAW_TRUE_NEGATIVE_POOL_REACHED"
        ),
        "raw_unique_negative_count": 1,
        "true_best_reduced_cost": true_rc,
        "true_audited_column_count": 1,
    }
    seen_configs = []
    seen_contexts = []

    def fake_pricer(*_args, config, **_kwargs):
        seen_configs.append(config)
        if len(seen_configs) == 1:
            return dict(harvest_empty), tuple()
        return dict(sparse_negative), (column,)

    def policy(post_harvest):
        seen_contexts.append(dict(post_harvest))
        return "S1"

    monkeypatch.setenv(
        "LUNAR_ICE_EXACT_NEGATIVE_ESCAPE_ENABLED", "1"
    )
    with patch(
        "lunar_ice_bpc.exact.bpc.pricing.final_judge."
        "run_bpc_labeling_pricer",
        side_effect=fake_pricer,
    ):
        result = run_true_dual_root_final_judge(
            data,
            context,
            node_id="node_000",
            labeling_final_judge_enabled=True,
            labeling_final_judge_max_exact_tasks=5,
            labeling_final_judge_exact_harvest_target=8,
            labeling_final_judge_pass_strategy="harvest_then_proof",
            one_deviation_sparse_tail_action_resolver=policy,
        )
    assert len(seen_configs) == 2
    assert len(seen_contexts) == 1
    assert seen_contexts[0][
        "harvest_pass_processed_labels"
    ] == 123
    assert seen_contexts[0][
        "audited_official_negative_column_count"
    ] == 0
    assert result.pricing_state.value == "FOUND_NEGATIVE"
    assert result.pricing_payload[
        "one_deviation_sparse_tail_action"
    ] == "S1"
    assert result.pricing_payload[
        "one_deviation_sparse_tail_action_resolver_invoked"
    ]
    assert result.pricing_payload[
        "one_deviation_sparse_tail_decision_timing"
    ] == "after_empty_harvest_before_sparse_pass"


def test_sparse_tail_policy_not_invoked_when_harvest_found_negative(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    context = ReducedCostContext(
        task_duals={task_id: 1.0 for task_id in data.task_ids},
        fleet_dual=0.0,
        dual_fingerprint="harvest-hit-policy-dual",
        rmp_iteration_id="root-harvest-hit-policy",
    )
    column = enumerate_direct_journey_columns(
        data,
        max_exact_tasks=5,
    ).columns[0]
    true_rc = manual_journey_reduced_cost(
        column,
        JourneyDuals(
            cover=context.task_duals,
            fleet_limit=context.fleet_dual,
        ),
    )
    harvest_negative = {
        "pricing_state": "FOUND_NEGATIVE",
        "pricing_proof_kind": "EXHAUSTIVE_INCOMPLETE",
        "can_certify_no_negative": False,
        "true_best_reduced_cost": true_rc,
        "true_audited_column_count": 1,
    }
    policy_calls = []

    def policy(post_harvest):
        policy_calls.append(dict(post_harvest))
        return "S1"

    with patch(
        "lunar_ice_bpc.exact.bpc.pricing.final_judge."
        "run_bpc_labeling_pricer",
        return_value=(dict(harvest_negative), (column,)),
    ) as pricer:
        result = run_true_dual_root_final_judge(
            data,
            context,
            node_id="node_000",
            labeling_final_judge_enabled=True,
            labeling_final_judge_max_exact_tasks=5,
            labeling_final_judge_pass_strategy="harvest_then_proof",
            one_deviation_sparse_tail_action_resolver=policy,
        )
    assert pricer.call_count == 1
    assert policy_calls == []
    assert result.pricing_state.value == "FOUND_NEGATIVE"
    assert not result.pricing_payload[
        "one_deviation_sparse_tail_action_resolver_invoked"
    ]
    assert not result.pricing_payload[
        "one_deviation_sparse_tail_attempted"
    ]


def test_sparse_tail_post_harvest_policy_exception_runs_official_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    context = ReducedCostContext(
        task_duals={task_id: 0.0 for task_id in data.task_ids},
        fleet_dual=0.0,
        dual_fingerprint="post-harvest-exception-dual",
        rmp_iteration_id="root-post-harvest-exception",
    )
    incomplete = {
        "pricing_state": "INCOMPLETE_LIMIT",
        "pricing_proof_kind": "EXHAUSTIVE_INCOMPLETE",
        "can_certify_no_negative": False,
        "true_audited_column_count": 0,
    }
    certificate = {
        "pricing_state": "CERTIFIED_NO_NEGATIVE",
        "pricing_proof_kind": "EXHAUSTIVE_NO_NEGATIVE",
        "can_certify_no_negative": True,
        "true_audited_column_count": 0,
    }
    seen = []

    def fake_pricer(*_args, config, **_kwargs):
        seen.append(config)
        return (
            (dict(incomplete), tuple())
            if len(seen) == 1
            else (dict(certificate), tuple())
        )

    def broken_policy(_post_harvest):
        raise RuntimeError("GAT unavailable")

    with patch(
        "lunar_ice_bpc.exact.bpc.pricing.final_judge."
        "run_bpc_labeling_pricer",
        side_effect=fake_pricer,
    ):
        result = run_true_dual_root_final_judge(
            data,
            context,
            node_id="node_000",
            labeling_final_judge_enabled=True,
            labeling_final_judge_max_exact_tasks=5,
            labeling_final_judge_pass_strategy="harvest_then_proof",
            one_deviation_sparse_tail_action_resolver=broken_policy,
        )
    assert len(seen) == 2
    assert result.pricing_state.value == "CERTIFIED_NO_NEGATIVE"
    assert result.pricing_payload["can_certify_no_negative"]
    assert not result.pricing_payload[
        "one_deviation_sparse_tail_attempted"
    ]
    assert "GAT unavailable" in result.pricing_payload[
        "one_deviation_sparse_tail_action_resolver_error"
    ]
    assert result.pricing_payload[
        "labeling_final_judge_proof_pass_attempted"
    ]


def test_sparse_tail_policy_is_once_per_root_and_restores_noop() -> None:
    calls = []

    def fixed_policy(context):
        calls.append(context)
        return "S1"

    first = _resolve_sparse_tail_deviation_decision(
        policy=fixed_policy,
        context={"round": 7},
        expected_input_hash="input-7",
        node_id="root",
        already_used=False,
    )
    assert first["requested_action"] == "S1"
    assert first["effective_action"] == "S1"
    assert first["certificate_authority"] == "none"

    restored = _resolve_sparse_tail_deviation_decision(
        policy=fixed_policy,
        context={"round": 8},
        expected_input_hash="input-8",
        node_id="root",
        already_used=True,
    )
    assert restored["effective_action"] == "NOOP"
    assert restored["decision_reason"] == "one_deviation_already_used"
    assert restored["next_round_policy"] == "restore_frozen_v5"
    assert len(calls) == 1


def test_sparse_tail_gat_policy_hash_ood_and_exception_fail_to_noop() -> None:
    expected_input_hash = "canonical-input"
    valid = _resolve_sparse_tail_deviation_decision(
        policy=lambda _context: {
            "action": "S4",
            "policy_kind": "gat",
            "input_hash": expected_input_hash,
            "manifest_sha256": "a" * 64,
            "checkpoint_sha256": "b" * 64,
            "hash_valid": True,
            "ood": False,
        },
        context={},
        expected_input_hash=expected_input_hash,
        node_id="root",
        already_used=False,
    )
    assert valid["effective_action"] == "S4"
    payload = _sparse_tail_policy_payload(valid)
    assert not payload[
        "one_deviation_sparse_tail_policy_fallback_to_noop"
    ]
    assert payload[
        "one_deviation_sparse_tail_policy_certificate_authority"
    ] == "none"

    ood = _resolve_sparse_tail_deviation_decision(
        policy=lambda _context: {
            "action": "S1",
            "policy_kind": "gat",
            "input_hash": expected_input_hash,
            "manifest_sha256": "a" * 64,
            "checkpoint_sha256": "b" * 64,
            "ood": True,
        },
        context={},
        expected_input_hash=expected_input_hash,
        node_id="root",
        already_used=False,
    )
    assert ood["effective_action"] == "NOOP"
    assert ood["decision_reason"] == "context_ood"

    mismatch = _resolve_sparse_tail_deviation_decision(
        policy=lambda _context: {
            "action": "S1",
            "policy_kind": "gat",
            "input_hash": "wrong-input",
            "manifest_sha256": "a" * 64,
            "checkpoint_sha256": "b" * 64,
        },
        context={},
        expected_input_hash=expected_input_hash,
        node_id="root",
        already_used=False,
    )
    assert mismatch["effective_action"] == "NOOP"
    assert mismatch["decision_reason"] == "input_hash_mismatch"

    def broken_policy(_context):
        raise RuntimeError("model unavailable")

    broken = _resolve_sparse_tail_deviation_decision(
        policy=broken_policy,
        context={},
        expected_input_hash=expected_input_hash,
        node_id="root",
        already_used=False,
    )
    assert broken["effective_action"] == "NOOP"
    assert broken["decision_reason"] == "policy_exception"
    assert "model unavailable" in broken["runtime_error"]


def test_tree_node_threads_conservative_pricing_scope(
    monkeypatch,
) -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    initial_columns = enumerate_direct_journey_columns(
        data,
        max_exact_tasks=5,
    ).columns
    monkeypatch.setenv("LUNAR_ICE_EXACT_FINAL_JUDGE_FIRST", "1")

    def capture_scope(*_args, **kwargs):
        assert (
            kwargs["pricing_lifecycle_scope"]
            == PRICING_LIFECYCLE_SCOPE_TREE_NODE
        )
        raise RuntimeError("scope captured")

    with patch(
        "lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver."
        "run_true_dual_root_final_judge",
        side_effect=capture_scope,
    ), pytest.raises(RuntimeError, match="scope captured"):
        solve_node_pricing_with_b2b_r3(
            data,
            node_id="node_000",
            pricing_lifecycle_scope=(
                PRICING_LIFECYCLE_SCOPE_TREE_NODE
            ),
            initial_columns=initial_columns,
            max_direct_tasks=5,
            max_rounds=1,
            labeling_final_judge_enabled=True,
            labeling_final_judge_max_exact_tasks=5,
        )


def test_batch_interfaces_are_atomic_on_invalid_input() -> None:
    columns = _bpc_columns()
    pool = ColumnPool()
    with pytest.raises(ValueError):
        pool.add_many(columns, node_contexts=({},))
    assert not pool.columns_by_signature
    view = MasterColumnView()
    with pytest.raises(ValueError):
        view.add_many_from_pool(
            columns, node_id="root", pool=pool
        )
    assert not view.signatures_by_node


def test_batch_admission_matches_scalar_on_500_random_instances() -> None:
    generator = random.Random(629_044)
    for trial in range(500):
        signatures = [
            ColumnSemanticSignature(
                task_set=(f"T{generator.randrange(8)}",),
                sortie_partition=((f"S{index}",),),
                ordered_task_sequences=((f"S{index}",),),
                path_option_signature=(("direct",),),
                service_timing_signature=tuple(),
                resource_profile_signature=(
                    ("objective", float(index)),
                ),
            )
            for index in range(generator.randrange(1, 18))
        ]
        columns = tuple(
            BpcColumn(signature, float(index), payload=index)
            for index, signature in enumerate(signatures)
        )
        forbidden = set(
            generator.sample(
                signatures,
                k=generator.randrange(0, min(3, len(signatures)) + 1),
            )
        )
        scalar_pool = ColumnPool()
        scalar_view = MasterColumnView()
        scalar_results = []
        scalar_view_results = []
        for column in columns:
            context = {
                "master_view": scalar_view,
                "node_id": "node",
                "forbidden_signatures": forbidden,
            }
            result = scalar_pool.add(column, context)
            scalar_results.append((result.added, result.reason))
            stored = scalar_pool.get(column.signature)
            scalar_view_results.append(
                False
                if stored is None
                else scalar_view.add_from_pool(
                    stored, node_id="node", pool=scalar_pool
                )
            )

        batch_pool = ColumnPool()
        batch_view = MasterColumnView()
        batch_results, batch_view_results = (
            batch_view.admit_many_atomically(
                columns,
                node_contexts=tuple(
                {
                    "master_view": batch_view,
                    "node_id": "node",
                    "forbidden_signatures": forbidden,
                }
                for _column in columns
                ),
                node_id="node",
                pool=batch_pool,
            )
        )
        assert [(row.added, row.reason) for row in batch_results] == (
            scalar_results
        ), trial
        assert batch_view_results == tuple(scalar_view_results), trial
        assert batch_pool.columns_by_signature == (
            scalar_pool.columns_by_signature
        ), trial
        assert batch_view.signatures_by_node == (
            scalar_view.signatures_by_node
        ), trial


def _snapshot(
    *,
    scale: int = 30,
    instance_index: int = 1,
    context_index: int = 0,
    candidate_count: int = 40,
    batch_size: int = 8,
) -> dict:
    instance_hash = f"instance-{scale}-{instance_index}"
    context_suffix = (
        ""
        if int(context_index) == 0
        else f"-context-{int(context_index)}"
    )
    binding = {
        "binding_hash": (
            f"binding-{scale}-{instance_index}{context_suffix}"
        ),
        "instance_hash": instance_hash,
        "objective_mode": "official",
        "engine_hash": f"engine-{scale}",
        "config_hash": f"config-{scale}",
        "mathematical_dual_hash": (
            f"true-dual-{scale}-{instance_index}{context_suffix}"
        ),
        "rmp_iteration_id": (
            f"root:{instance_index}:{int(context_index)}"
        ),
        "cut_lineage_hash": CutLineage(
            policy_version="explicit_cut_context_v1"
        ).cut_lineage_hash,
    }
    return build_route_admission_snapshot(
        canonical_solve_binding=binding,
        instance_content_hash=instance_hash,
        scale=scale,
        node_id="root",
        candidate_rows=[
            {
                "candidate_id": f"c{index:03d}",
                "true_reduced_cost": -float(candidate_count - index),
                "task_set": [f"T{index % max(1, scale)}"],
                "column_payload": {
                    "sorties": [{"tasks": [f"T{index % max(1, scale)}"]}]
                },
            }
            for index in range(candidate_count)
        ],
        p0_ordered_candidate_ids=[
            f"c{index:03d}" for index in range(candidate_count)
        ],
        p0_selected_candidate_ids=[
            f"c{index:03d}" for index in range(batch_size)
        ],
        selection_limit=batch_size,
        active_column_payloads=[{"sorties": [{"tasks": ["T0"]}]}],
        branch_context={},
        full_cut_context={},
        source_phase="test",
        executed_objective_spec_id="objective.v1",
        remaining_solve_budget_sec=300.0,
        remaining_budget_observation_stage=(
            "post_candidate_generation_pre_admission"
        ),
    )


def test_route_snapshot_counterfactual_state_is_hash_bound() -> None:
    snapshot = _snapshot()
    assert (
        snapshot["counterfactual_state"]["rmp_basis_state"]["kind"]
        == "p0v4_no_persistent_basis_deterministic_rebuild"
    )
    assert snapshot["counterfactual_state"][
        "cut_policy_binding_hash"
    ]
    assert _matched_cut_lineage(snapshot).empty
    legacy_empty_lineage = deepcopy(snapshot)
    legacy_empty_lineage["canonical_solve_binding"][
        "cut_lineage_hash"
    ] = ""
    legacy_empty_lineage["counterfactual_state"][
        "cut_policy_binding_hash"
    ] = stable_payload_hash(
        {
            "cut_lineage_hash": "",
            "live_cut_policy_hash": "",
            "separator_policy_version": "",
        }
    )
    legacy_empty_lineage["snapshot_hash"] = stable_payload_hash(
        {
            key: value
            for key, value in legacy_empty_lineage.items()
            if key != "snapshot_hash"
        }
    )
    assert _matched_cut_lineage(legacy_empty_lineage).empty
    tampered = deepcopy(snapshot)
    tampered["counterfactual_state"]["active_columns_hash"] = "wrong"
    tampered["snapshot_hash"] = stable_payload_hash(
        {
            key: value
            for key, value in tampered.items()
            if key != "snapshot_hash"
        }
    )
    with pytest.raises(ValueError, match="active-column state hash"):
        validate_route_admission_snapshot(tampered)

    tampered = deepcopy(snapshot)
    tampered["counterfactual_state"]["rmp_basis_state"][
        "kind"
    ] = "fabricated_warm_basis"
    tampered["counterfactual_state"]["rmp_basis_hash"] = (
        stable_payload_hash(
            tampered["counterfactual_state"]["rmp_basis_state"]
        )
    )
    tampered["snapshot_hash"] = stable_payload_hash(
        {
            key: value
            for key, value in tampered.items()
            if key != "snapshot_hash"
        }
    )
    with pytest.raises(ValueError, match="basis semantics"):
        validate_route_admission_snapshot(tampered)

    unsupported_lineage = deepcopy(snapshot)
    unsupported_lineage["canonical_solve_binding"][
        "cut_lineage_hash"
    ] = "unreconstructable"
    unsupported_lineage["counterfactual_state"][
        "cut_policy_binding_hash"
    ] = stable_payload_hash(
        {
            "cut_lineage_hash": "unreconstructable",
            "live_cut_policy_hash": "",
            "separator_policy_version": "",
        }
    )
    unsupported_lineage["snapshot_hash"] = stable_payload_hash(
        {
            key: value
            for key, value in unsupported_lineage.items()
            if key != "snapshot_hash"
        }
    )
    with pytest.raises(
        ValueError, match="cannot be reconstructed exactly"
    ):
        _matched_cut_lineage(unsupported_lineage)


def test_one_deviation_arm_persists_only_public_exact_result() -> None:
    marker = object()
    assert _public_exact_result(
        {
            "algorithm_status": "BPC_INCOMPLETE_PRICING",
            "_master": marker,
            "_all_priced_columns": (marker,),
        }
    ) == {"algorithm_status": "BPC_INCOMPLETE_PRICING"}


def test_matched_action_rebuild_changes_only_rank_k() -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    columns = enumerate_direct_journey_columns(
        data, max_exact_tasks=5
    ).columns
    candidates = tuple(columns[:12])
    active = columns[-1]
    binding = {
        "binding_hash": "binding-real-columns",
        "instance_hash": data.instance_content_hash,
        "objective_mode": "official",
        "engine_hash": "engine-hash",
        "config_hash": "config-hash",
        "mathematical_dual_hash": "true-dual-hash",
        "rmp_iteration_id": "root:1",
    }
    snapshot = build_route_admission_snapshot(
        canonical_solve_binding=binding,
        instance_content_hash=data.instance_content_hash,
        scale=30,
        node_id="root",
        candidate_rows=[
            {
                "candidate_id": f"c{index:03d}",
                "true_reduced_cost": -float(12 - index),
                "task_set": sorted(column.task_set),
                "column_payload": column.to_solution_payload(
                    vehicle_id=f"candidate-{index:03d}"
                ),
            }
            for index, column in enumerate(candidates)
        ],
        p0_ordered_candidate_ids=[
            f"c{index:03d}" for index in range(12)
        ],
        p0_selected_candidate_ids=[
            f"c{index:03d}" for index in range(4)
        ],
        selection_limit=4,
        active_column_payloads=[
            active.to_solution_payload(vehicle_id="active")
        ],
        branch_context={},
        full_cut_context={},
        source_phase="test",
        executed_objective_spec_id="objective.v1",
        remaining_solve_budget_sec=300.0,
        remaining_budget_observation_stage=(
            "post_candidate_generation_pre_admission"
        ),
    )
    manifest = build_one_deviation_actions(snapshot)
    noop = manifest["actions"][0]
    promotion = manifest["actions"][1]
    noop_columns = action_initial_columns(data, snapshot, noop)
    promoted_columns = action_initial_columns(
        data, snapshot, promotion
    )
    noop_signatures = [
        column_signature_from_journey(column)
        for column in noop_columns
    ]
    promoted_signatures = [
        column_signature_from_journey(column)
        for column in promoted_columns
    ]
    assert promoted_signatures[:-1] == noop_signatures[:-1]
    assert promoted_signatures[-1] != noop_signatures[-1]
    assert promoted_signatures[-1] == column_signature_from_journey(
        candidates[4]
    )
    assert len(set(promoted_signatures)) == len(promoted_signatures)


def test_matched_rollout_rows_validate_blocked_replicates() -> None:
    snapshot = _snapshot()
    full_manifest = build_one_deviation_actions(snapshot)
    manifest = {
        **full_manifest,
        "actions": [
            full_manifest["actions"][0],
            full_manifest["actions"][1],
            full_manifest["actions"][2],
        ],
    }
    context = build_matched_rollout_context(
        snapshot,
        manifest,
        fixed_k_selection_hash="fixed-k-hash",
    )
    raw_by_replicate = {}
    for replicate in ("r1", "r2", "r3"):
        raw_by_replicate[replicate] = [
            {
                "action_id": ONE_DEVIATION_NOOP_ACTION_ID,
                "action_kind": "noop",
                "root_closed": False,
                "terminal_root_bound": 10.0,
                "terminal_negative_pressure": None,
                "trace": [
                    {"elapsed_sec": 100.0, "root_bound": 10.0}
                ],
                "rollout_horizon_cg_rounds": 1,
                "next_round_exact_order_restored": True,
                "intervention_count": 0,
            },
            {
                "action_id": manifest["actions"][1]["action_id"],
                "action_kind": "promotion",
                "root_closed": False,
                "terminal_root_bound": 9.5,
                "terminal_negative_pressure": None,
                "trace": [
                    {"elapsed_sec": 90.0, "root_bound": 10.0}
                ],
                "rollout_horizon_cg_rounds": 1,
                "next_round_exact_order_restored": True,
                "intervention_count": 1,
            },
            {
                "action_id": manifest["actions"][2]["action_id"],
                "action_kind": "promotion",
                "root_closed": False,
                "terminal_root_bound": 11.0,
                "terminal_negative_pressure": None,
                "trace": [
                    {"elapsed_sec": 120.0, "root_bound": 11.0}
                ],
                "rollout_horizon_cg_rounds": 1,
                "next_round_exact_order_restored": True,
                "intervention_count": 1,
            },
        ]
    rows = materialize_matched_rollout_rows(
        context, raw_by_replicate
    )
    validation = validate_one_deviation_rollouts(context, rows)
    assert validation["validation_pass"]
    labels = materialize_one_deviation_time_labels(context, rows)
    by_action = {
        row["action_id"]: row for row in labels["labels"]
    }
    assert (
        by_action[manifest["actions"][1]["action_id"]][
            "delta_time_sec"
        ]
        == 10.0
    )
    assert (
        by_action[manifest["actions"][2]["action_id"]][
            "delta_time_sec"
        ]
        is None
    )
    assert by_action[manifest["actions"][2]["action_id"]][
        "survival_mask"
    ]
    mixed_rows = deepcopy(rows)
    mixed_action_id = manifest["actions"][1]["action_id"]
    mixed_row = next(
        row
        for row in mixed_rows
        if row["replicate_id"] == "r3"
        and row["action_id"] == mixed_action_id
    )
    mixed_row["right_censored"] = True
    mixed_row["milestone_time_sec"] = mixed_row["budget_sec"]
    mixed_label = next(
        row
        for row in materialize_one_deviation_time_labels(
            context, mixed_rows
        )["labels"]
        if row["action_id"] == mixed_action_id
    )
    assert mixed_label["observed_replicate_count"] == 2
    assert mixed_label["right_censored_replicate_count"] == 1
    assert mixed_label["beneficial"] is None
    assert not mixed_label["probability_head_mask"]
    assert not mixed_label["positive_magnitude_head_mask"]
    assert mixed_label["survival_mask"]

    duplicate_rows = [*rows, deepcopy(rows[0])]
    with pytest.raises(ValueError, match="repeats an action"):
        validate_one_deviation_rollouts(context, duplicate_rows)


def test_matched_rollout_uses_observed_pressure_when_objective_is_flat() -> None:
    snapshot = _snapshot()
    full_manifest = build_one_deviation_actions(snapshot)
    manifest = {
        **full_manifest,
        "actions": [
            full_manifest["actions"][0],
            full_manifest["actions"][1],
            full_manifest["actions"][2],
        ],
    }
    context = build_matched_rollout_context(
        snapshot,
        manifest,
        fixed_k_selection_hash="fixed-k-hash",
    )
    control_pressure = {
        "count": 5,
        "mass": 0.5,
        "best_true_rc": -0.1,
    }
    raw_by_replicate = {}
    for replicate in ("r1", "r2", "r3"):
        raw_by_replicate[replicate] = [
            {
                "action_id": ONE_DEVIATION_NOOP_ACTION_ID,
                "action_kind": "noop",
                "root_closed": False,
                "terminal_root_bound": 10.0,
                "terminal_negative_pressure": control_pressure,
                "trace": [
                    {
                        "elapsed_sec": 20.0,
                        "root_bound": 10.0,
                        "pricing_state": "FOUND_NEGATIVE",
                        "negative_pressure": {
                            "count": 20,
                            "mass": 4.0,
                            "best_true_rc": -0.2,
                        },
                    },
                    {
                        "elapsed_sec": 100.0,
                        "root_bound": 10.0,
                        "pricing_state": "FOUND_NEGATIVE",
                        "negative_pressure": control_pressure,
                    },
                ],
                "rollout_horizon_cg_rounds": 2,
                "next_round_exact_order_restored": True,
                "intervention_count": 0,
            },
            {
                "action_id": manifest["actions"][1]["action_id"],
                "action_kind": "promotion",
                "root_closed": False,
                "terminal_root_bound": 10.0,
                "terminal_negative_pressure": control_pressure,
                "trace": [
                    {
                        "elapsed_sec": 5.0,
                        "root_bound": 10.0,
                        "pricing_state": "INCOMPLETE_LIMIT",
                        "negative_pressure": {
                            "count": 0,
                            "mass": 0.0,
                            "best_true_rc": None,
                        },
                    },
                    {
                        "elapsed_sec": 80.0,
                        "root_bound": 10.0,
                        "pricing_state": "FOUND_NEGATIVE",
                        "negative_pressure": control_pressure,
                    },
                ],
                "rollout_horizon_cg_rounds": 2,
                "next_round_exact_order_restored": True,
                "intervention_count": 1,
            },
            {
                "action_id": manifest["actions"][2]["action_id"],
                "action_kind": "promotion",
                "root_closed": False,
                "terminal_root_bound": 10.0,
                "terminal_negative_pressure": None,
                "trace": [
                    {
                        "elapsed_sec": 5.0,
                        "root_bound": 10.0,
                        "pricing_state": "INCOMPLETE_LIMIT",
                        "negative_pressure": {
                            "count": 0,
                            "mass": 0.0,
                            "best_true_rc": None,
                        },
                    }
                ],
                "rollout_horizon_cg_rounds": 1,
                "next_round_exact_order_restored": True,
                "intervention_count": 1,
            },
        ]
    rows = materialize_matched_rollout_rows(
        context, raw_by_replicate
    )
    assert {
        row["milestone_kind"] for row in rows
    } == {"equal_remaining_negative_pressure"}
    by_action = {
        row["action_id"]: row
        for row in materialize_one_deviation_time_labels(
            context, rows
        )["labels"]
    }
    assert (
        by_action[manifest["actions"][1]["action_id"]][
            "delta_time_sec"
        ]
        == 20.0
    )
    assert (
        by_action[manifest["actions"][2]["action_id"]][
            "delta_time_sec"
        ]
        is None
    )
    assert by_action[manifest["actions"][2]["action_id"]][
        "survival_mask"
    ]


def test_one_deviation_actions_only_replace_rank_k() -> None:
    manifest = build_one_deviation_actions(_snapshot())
    assert manifest["actions"][0]["action_id"] == (
        ONE_DEVIATION_NOOP_ACTION_ID
    )
    assert len(manifest["actions"]) == 33
    for action in manifest["actions"][1:]:
        assert action["replaced_candidate_id"] == "c007"
        assert action["admitted_candidate_ids"][:7] == [
            f"c{index:03d}" for index in range(7)
        ]
        assert 9 <= action["promoted_from_rank"] <= 40
    assert manifest["intervention_count_limit_per_root"] == 1
    assert manifest["next_round_policy"] == (
        "restore_frozen_exact_p0_order"
    )


def test_route_opportunity_gate_requires_both_scales_and_instances() -> None:
    snapshots = [
        _snapshot(
            scale=scale,
            instance_index=instance_index,
            context_index=replicate,
        )
        for scale in (30, 50)
        for instance_index in range(1, 6)
        for replicate in range(1, 5)
    ]
    audit = audit_route_opportunity_census(snapshots)
    assert audit["gate_pass"]
    assert audit["gat_oracle_authorized"]
    assert audit["scales"]["30"]["eligible_context_count"] == 20
    assert audit["scales"]["50"]["eligible_instance_count"] == 5


def test_route_opportunity_gate_does_not_count_duplicate_snapshots() -> None:
    snapshot = _snapshot(scale=30)
    audit = audit_route_opportunity_census(
        [snapshot, deepcopy(snapshot)],
        required_scales=(30,),
        minimum_contexts_per_scale=2,
        minimum_instances_per_scale=1,
    )
    assert not audit["gate_pass"]
    assert audit["scales"]["30"]["eligible_context_count"] == 1
    assert audit["rejected_reasons"] == {
        "duplicate_snapshot_hash": 1
    }


def test_route_opportunity_census_binding_rejects_index_drift() -> None:
    fixed_hash = "fixed-k-hash"
    eligible = [
        {
            "snapshot_hash": "snapshot-hash",
            "source_snapshot": "/tmp/snapshot.json",
            "source_snapshot_sha256": "snapshot-sha256",
            "scale": 30,
            "instance_content_hash": "instance-hash",
            "instance_split": "train",
        }
    ]
    split = {"instance-hash": "train"}
    binding = {
        "schema_version": (
            "lunar_ice_bpc.p0v4_route_opportunity_census_binding.v1"
        ),
        "fixed_k_selection_sha256": fixed_hash,
        "eligibility_policy": (
            "root_true_rc_audited_post_generation_budget_min8_v2"
        ),
        "eligible_snapshots": [
            {
                key: value
                for key, value in eligible[0].items()
                if key != "source_snapshot"
            }
        ],
        "instance_split_by_hash": split,
        "instance_split_policy": (
            "pre_outcome_scale_stratified_sorted_every_fifth_calibration_v1"
        ),
    }
    census = {
        "schema_version": (
            "lunar_ice_bpc.p0v4_route_opportunity_census.v1"
        ),
        "fixed_k_selection_sha256": fixed_hash,
        "eligible_snapshot_count": 1,
        "eligible_snapshots": eligible,
        "action_manifest_count": 1,
        "census_binding_payload": binding,
        "census_content_binding_hash": stable_payload_hash(binding),
        "instance_split_by_hash": split,
        "instance_split_policy": binding["instance_split_policy"],
        "audit": {"gat_oracle_authorized": True},
        "expensive_oracle_authorized": True,
        "candidate_manufacturing_used": False,
    }
    assert validate_route_opportunity_census_binding(
        census, fixed_k_selection_sha256=fixed_hash
    ) == stable_payload_hash(binding)

    tampered = deepcopy(census)
    tampered["eligible_snapshots"][0][
        "source_snapshot_sha256"
    ] = "drifted"
    with pytest.raises(ValueError, match="not hash-bound"):
        validate_route_opportunity_census_binding(
            tampered, fixed_k_selection_sha256=fixed_hash
        )


def test_route_census_writes_only_unique_eligible_action_manifests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_route_opportunity_census.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v4_route_opportunity_census_integration_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    fixed_path = tmp_path / "fixed_k_selection.json"
    fixed_path.write_text(
        json.dumps(
            {
                "status": "FIXED_K_SELECTED",
                "selected_batch_size": 128,
                "admission_batch_size_by_scale": {
                    "30": 8,
                    "50": 128,
                },
            }
        ),
        encoding="utf-8",
    )
    snapshot_root = tmp_path / "snapshots"
    valid = _snapshot(scale=30, context_index=1)
    insufficient = _snapshot(scale=30, context_index=2)
    insufficient["remaining_solve_budget_sec"] = 119.0
    insufficient["snapshot_hash"] = stable_payload_hash(
        {
            key: value
            for key, value in insufficient.items()
            if key != "snapshot_hash"
        }
    )
    for relative, payload in (
        ("a/route_admission_snapshot.json", valid),
        ("b/route_admission_snapshot.json", valid),
        ("c/route_admission_snapshot.json", insufficient),
    ):
        target = snapshot_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "census"
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script),
            "--snapshot-root",
            str(snapshot_root),
            "--fixed-k-selection",
            str(fixed_path),
            "--output-dir",
            str(output),
        ],
    )
    assert module.main() == 3
    census = json.loads(
        (output / "opportunity_census.json").read_text(
            encoding="utf-8"
        )
    )
    assert census["discovered_snapshot_count"] == 3
    assert census["valid_snapshot_path_count"] == 3
    assert census["valid_snapshot_count"] == 2
    assert census["duplicate_snapshot_count"] == 1
    assert census["eligible_snapshot_count"] == 1
    assert census["action_manifest_count"] == 1
    action_paths = list(
        (output / "action_manifests").glob("*.json")
    )
    assert len(action_paths) == 1
    action = json.loads(
        action_paths[0].read_text(encoding="utf-8")
    )
    assert action["snapshot_hash"] == valid["snapshot_hash"]
    assert action["census_content_binding_hash"] == (
        census["census_content_binding_hash"]
    )


def test_route_opportunity_rejects_pre_generation_budget_snapshot() -> None:
    snapshot = _snapshot()
    legacy = {
        **snapshot,
        "schema_version": "lunar_ice_bpc.route_admission_snapshot.v1",
    }
    legacy.pop("remaining_budget_observation_stage")
    legacy["snapshot_hash"] = stable_payload_hash(
        {
            key: value
            for key, value in legacy.items()
            if key != "snapshot_hash"
        }
    )
    audit = audit_route_opportunity_census(
        [legacy],
        required_scales=(50,),
        minimum_contexts_per_scale=1,
        minimum_instances_per_scale=1,
    )
    assert not audit["gate_pass"]
    assert audit["rejected_reasons"] == {"invalid_snapshot": 1}


def test_fixed_escape_k_is_scale50_only() -> None:
    selection = {
        "selected_batch_size": 128,
        "admission_batch_size_by_scale": {
            "30": 64,
            "50": 128,
        },
    }
    assert fixed_exact_admission_batch_size(
        selection, scale=30
    ) == 64
    assert fixed_exact_admission_batch_size(
        selection, scale=50
    ) == 128
    assert fixed_exact_admission_batch_size(
        selection, scale=100
    ) == 128


def test_calibrated_deployment_promotes_once_then_restores_noop() -> None:
    calibration = calibrate_one_deviation_thresholds(
        [
            {
                "positive_probability": 0.99,
                "expected_positive_relative_gain": 0.02,
                "outcome": "beneficial",
            }
            for _index in range(120)
        ]
    )
    assert calibration["gate_pass"]
    ledger = OneDeviationLedger()
    decision = select_one_deviation(
        candidate_ids=("c008", "c009"),
        candidate_ranks=(9, 10),
        positive_probabilities=(0.99, 0.99),
        conditional_positive_relative_gains=(0.03, 0.04),
        batch_size=8,
        probability_threshold=calibration["probability_threshold"],
        expected_relative_gain_threshold=(
            calibration["expected_relative_gain_threshold"]
        ),
        root_key="instance:root",
        ledger=ledger,
        context_hash="context",
        expected_context_hash="context",
        model_hash="model",
        expected_model_hash="model",
        calibration_gate_pass=True,
    )
    assert decision.promotes
    assert decision.promoted_candidate_id == "c009"
    second = select_one_deviation(
        candidate_ids=("c008",),
        candidate_ranks=(9,),
        positive_probabilities=(1.0,),
        conditional_positive_relative_gains=(1.0,),
        batch_size=8,
        probability_threshold=0.0,
        expected_relative_gain_threshold=0.0,
        root_key="instance:root",
        ledger=ledger,
        context_hash="context",
        expected_context_hash="context",
        model_hash="model",
        expected_model_hash="model",
        calibration_gate_pass=True,
    )
    assert not second.promotes
    assert second.reason == "root_intervention_already_used"


def test_calibration_scores_the_deployed_winner_per_context() -> None:
    rows = [
        {
            "positive_probability": 0.99,
            "expected_positive_relative_gain": 0.01,
            "outcome": "beneficial",
            "context_hash": f"safe-{index:03d}",
            "candidate_rank": 1,
            "action_id": f"safe-{index:03d}",
        }
        for index in range(80)
    ]
    rows.extend(
        {
            "positive_probability": 0.99,
            "expected_positive_relative_gain": 0.01,
            "outcome": "beneficial",
            "context_hash": "mixed-context",
            "candidate_rank": index + 2,
            "action_id": f"mixed-safe-{index:03d}",
        }
        for index in range(100)
    )
    rows.append(
        {
            "positive_probability": 0.99,
            "expected_positive_relative_gain": 0.10,
            "outcome": "harmful",
            "context_hash": "mixed-context",
            "candidate_rank": 1,
            "action_id": "mixed-harmful-winner",
        }
    )
    calibration = calibrate_one_deviation_thresholds(rows)
    assert not calibration["gate_pass"]
    assert calibration["calibration_candidate_count"] == 181
    assert calibration["calibration_context_count"] == 81
    assert calibration["calibration_unit"] == (
        "deployed_winner_per_context"
    )


def test_calibration_never_drops_an_unknown_deployed_winner() -> None:
    rows = [
        {
            "positive_probability": 0.99,
            "expected_positive_relative_gain": 0.01,
            "outcome": "beneficial",
            "context_hash": f"safe-{index:03d}",
            "candidate_rank": 1,
            "action_id": f"safe-{index:03d}",
        }
        for index in range(100)
    ]
    rows.extend(
        (
            {
                "positive_probability": 0.99,
                "expected_positive_relative_gain": 0.01,
                "outcome": "beneficial",
                "context_hash": "censored-context",
                "candidate_rank": 2,
                "action_id": "observed-lower-score",
            },
            {
                "positive_probability": 0.99,
                "expected_positive_relative_gain": 0.10,
                "outcome": "unknown",
                "context_hash": "censored-context",
                "candidate_rank": 1,
                "action_id": "unknown-winner",
            },
        )
    )
    calibration = calibrate_one_deviation_thresholds(rows)
    assert not calibration["gate_pass"]


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"ood": True}, "context_ood"),
        ({"adverse_memory_event": True}, "memory_adverse_event_veto"),
        ({"model_hash": "wrong"}, "model_hash_mismatch"),
        ({"context_hash": "wrong"}, "context_hash_mismatch"),
        ({"calibration_gate_pass": False}, "calibration_gate_failed"),
    ],
)
def test_one_deviation_safety_vetoes(override, reason) -> None:
    kwargs = {
        "candidate_ids": ("c008",),
        "candidate_ranks": (9,),
        "positive_probabilities": (1.0,),
        "conditional_positive_relative_gains": (0.10,),
        "batch_size": 8,
        "probability_threshold": 0.8,
        "expected_relative_gain_threshold": 0.01,
        "root_key": "root",
        "ledger": OneDeviationLedger(),
        "context_hash": "context",
        "expected_context_hash": "context",
        "model_hash": "model",
        "expected_model_hash": "model",
        "calibration_gate_pass": True,
    }
    kwargs.update(override)
    decision = select_one_deviation(**kwargs)
    assert not decision.promotes
    assert decision.reason == reason


def test_native_memory_adverse_event_is_automatic_veto_input() -> None:
    assert _one_deviation_memory_adverse_event(
        {
            "native_backend_result": {
                "engine_status": "MEMORY_LIMIT",
                "telemetry": {"host_memory_killed": True},
            }
        }
    )
    assert not _one_deviation_memory_adverse_event(
        {
            "native_backend_result": {
                "engine_status": "FOUND_NEGATIVE_PARTIAL",
                "telemetry": {
                    "host_memory_killed": False,
                    "memory_pressure_triggered": False,
                },
            }
        }
    )


def test_matched_oracle_masks_right_censoring_and_passes_gate() -> None:
    state_hashes = {key: f"hash-{key}" for key in REQUIRED_STATE_HASHES}
    context = build_one_deviation_oracle_context(
        scale=50,
        instance_content_hash="instance",
        node_id="root",
        candidate_count=40,
        batch_size=8,
        remaining_solve_budget_sec=300.0,
        state_hashes=state_hashes,
        action_manifest_hash="actions",
    )
    rollout_rows = []
    for replicate in ("r1", "r2", "r3"):
        common = {
            "schema_version": (
                "lunar_ice_bpc.one_deviation_rollout_row.v1"
            ),
            "context_hash": context["context_hash"],
            "replicate_id": replicate,
            "budget_sec": 300.0,
            "rollout_horizon_cg_rounds": 3,
            "next_round_exact_order_restored": True,
            "intervention_count": 1,
            "certificate_paths_mutated": False,
            "bound_or_pruning_paths_mutated": False,
            "state_hashes": state_hashes,
            "milestone_kind": "p0_terminal_rmp_objective",
        }
        rollout_rows.extend(
            (
                {
                    **common,
                    "action_id": ONE_DEVIATION_NOOP_ACTION_ID,
                    "action_kind": "noop",
                    "milestone_time_sec": 100.0,
                    "right_censored": False,
                },
                {
                    **common,
                    "action_id": "promote-a",
                    "action_kind": "promotion",
                    "milestone_time_sec": 90.0,
                    "right_censored": False,
                },
                {
                    **common,
                    "action_id": "promote-b",
                    "action_kind": "promotion",
                    "milestone_time_sec": 300.0,
                    "right_censored": True,
                },
            )
        )
    labels = materialize_one_deviation_time_labels(
        context, rollout_rows
    )
    by_action = {row["action_id"]: row for row in labels["labels"]}
    assert by_action["promote-a"]["delta_time_sec"] == 10.0
    assert by_action["promote-a"]["relative_time_gain"] == 0.1
    assert by_action["promote-a"]["positive_magnitude_head_mask"]
    assert by_action["promote-b"]["delta_time_sec"] is None
    assert not by_action["promote-b"]["probability_head_mask"]
    assert by_action["promote-b"]["survival_mask"]
    assert by_action["promote-b"]["censor_lower_bound_sec"] == 200.0
    assert by_action["promote-b"]["censor_lower_bound_relative"] == 2.0
    assert labels["right_censored_never_forced_negative"]

    gate_rows = [
        {
            "scale": scale,
            "instance_content_hash": f"instance-{instance}",
            "oracle_gain_fraction": 0.12,
            "redline_count": 0,
        }
        for scale in (30, 50)
        for instance in range(5)
        for _context in range(4)
    ]
    gate = audit_one_deviation_oracle(
        gate_rows, bootstrap_samples=200
    )
    assert gate["gate_pass"]
    assert gate["gat_training_authorized"]


def test_sparse_tail_context_gat_features_loss_and_harm_veto() -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    columns = enumerate_direct_journey_columns(
        data,
        max_exact_tasks=5,
    ).columns[:8]
    reduced = ReducedCostContext(
        task_duals={
            task_id: 0.02 * (index + 1)
            for index, task_id in enumerate(data.task_ids)
        },
        fleet_dual=-0.01,
        dual_fingerprint="sparse-tail-gat-features",
        rmp_iteration_id="root-7",
    )
    context = {
        "data": data,
        "master_columns": columns,
        "master": SimpleNamespace(
            reduced_cost_context=reduced,
            objective=1.25,
        ),
        "round": 7,
        "effective_harvest_target": 8,
        "sparse_tail_time_cap_sec": 60.0,
        "prior_history": (
            {
                "round": 5,
                "added_column_count": 4,
                "selected_diverse_negative_count": 4,
                "raw_unique_negative_count": 12,
                "harvest_best_true_rc": -0.02,
                "labeling_final_judge_harvest_pass_processed_labels": 100,
                "final_judge_wall_time": 1.5,
                "node_lp_bound": 1.20,
                "dual_context": {
                    "task_duals": {
                        task_id: 0.01
                        for task_id in data.task_ids
                    }
                },
            },
            {
                "round": 6,
                "added_column_count": 1,
                "selected_diverse_negative_count": 1,
                "raw_unique_negative_count": 3,
                "harvest_best_true_rc": -0.001,
                "labeling_final_judge_harvest_pass_processed_labels": 300,
                "final_judge_wall_time": 3.0,
                "node_lp_bound": 1.24,
                "dual_context": {
                    "task_duals": {
                        task_id: 0.015
                        for task_id in data.task_ids
                    }
                },
            },
        ),
        "post_harvest": {
            "harvest_pass_pricing_state": "INCOMPLETE_LIMIT",
            "harvest_pass_wall_time_sec": 2.0,
            "harvest_pass_processed_labels": 500,
            "harvest_pass_extended_labels": 2000,
            "harvest_pass_best_true_rc": None,
            "harvest_pass_search_exhaustive": False,
            "harvest_pass_frontier_empty": False,
            "harvest_pass_can_certify_no_negative": False,
            "audited_official_negative_column_count": 0,
        },
        "one_deviation_sparse_tail_decision_timing": (
            "after_empty_harvest_before_sparse_pass"
        ),
        "one_deviation_sparse_tail_input_hash": "a" * 64,
    }
    features = build_sparse_tail_action_features(context)
    assert features.action_ids == SPARSE_TAIL_ACTIONS
    assert len(features.node_features) == len(data.task_ids) + 1
    assert len(features.action_features) == 2
    assert features.feature_hash == build_sparse_tail_action_features(
        context
    ).feature_hash
    tensors = tensorize_sparse_tail_action_features(features)
    model = TwoHeadSparseTailActionGAT(
        node_input_dim=tensors["node_features"].shape[1],
        edge_input_dim=tensors["edge_features"].shape[1],
        global_input_dim=tensors["global_features"].shape[0],
        action_input_dim=tensors["action_features"].shape[1],
    )
    outputs = model(**tensors)
    assert outputs["positive_probability"].shape == (2,)
    losses = sparse_tail_two_head_loss(
        outputs,
        beneficial=torch.tensor([True, False]),
        observed_mask=torch.tensor([True, True]),
        positive_relative_gain=torch.tensor([0.1, 0.0]),
    )
    assert torch.isfinite(losses["loss"])
    losses["loss"].backward()

    vetoed = choose_sparse_tail_action(
        action_ids=SPARSE_TAIL_ACTIONS,
        probabilities=(0.95, 0.90),
        conditional_positive_gains=(0.20, 0.10),
        probability_threshold=0.8,
        expected_gain_threshold=0.05,
        calibration_harm_gate_pass=False,
    )
    assert vetoed.action == "NOOP"
    assert vetoed.reason == "harm_gate_not_passed"
    selected = choose_sparse_tail_action(
        action_ids=SPARSE_TAIL_ACTIONS,
        probabilities=(0.95, 0.90),
        conditional_positive_gains=(0.20, 0.10),
        probability_threshold=0.8,
        expected_gain_threshold=0.05,
        calibration_harm_gate_pass=True,
    )
    assert selected.action == "S1"


def test_sparse_tail_gat_runtime_shadow_is_fail_closed(
    tmp_path: Path,
) -> None:
    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    columns = enumerate_direct_journey_columns(
        data,
        max_exact_tasks=5,
    ).columns[:4]
    reduced = ReducedCostContext(
        task_duals={task_id: 0.01 for task_id in data.task_ids},
        fleet_dual=0.0,
        dual_fingerprint="sparse-tail-runtime",
        rmp_iteration_id="root-runtime",
    )
    context = {
        "data": data,
        "master_columns": columns,
        "master": SimpleNamespace(
            reduced_cost_context=reduced,
            objective=1.0,
        ),
        "round": 3,
        "effective_harvest_target": 8,
        "sparse_tail_time_cap_sec": 60.0,
        "prior_history": tuple(),
        "post_harvest": {
            "harvest_pass_pricing_state": "INCOMPLETE_LIMIT",
            "harvest_pass_wall_time_sec": 1.0,
            "harvest_pass_processed_labels": 10,
            "harvest_pass_extended_labels": 20,
            "harvest_pass_search_exhaustive": False,
            "harvest_pass_frontier_empty": False,
            "harvest_pass_can_certify_no_negative": False,
            "audited_official_negative_column_count": 0,
        },
        "one_deviation_sparse_tail_decision_timing": (
            "after_empty_harvest_before_sparse_pass"
        ),
        "one_deviation_sparse_tail_input_hash": "b" * 64,
    }
    features = build_sparse_tail_action_features(context)
    tensors = tensorize_sparse_tail_action_features(features)
    dimensions = {
        "node_input_dim": tensors["node_features"].shape[1],
        "edge_input_dim": tensors["edge_features"].shape[1],
        "global_input_dim": tensors["global_features"].shape[0],
        "action_input_dim": tensors["action_features"].shape[1],
        "hidden_dim": 32,
        "heads": 2,
        "layers": 2,
    }
    model = TwoHeadSparseTailActionGAT(**dimensions)
    checkpoint_path = tmp_path / "sparse_tail_gat.pt"
    torch.save(
        {
            "schema_version": SPARSE_TAIL_GAT_MODEL_SCHEMA,
            "dimensions": dimensions,
            "state_dict": model.state_dict(),
        },
        checkpoint_path,
    )
    checkpoint_sha = hashlib.sha256(
        checkpoint_path.read_bytes()
    ).hexdigest()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": SPARSE_TAIL_GAT_MANIFEST_SCHEMA,
                "feature_schema_hash": stable_payload_hash(
                    sparse_tail_feature_schema()
                ),
                "action_ids": list(SPARSE_TAIL_ACTIONS),
                "checkpoint": checkpoint_path.name,
                "checkpoint_sha256": checkpoint_sha,
                "evaluation_authorized": False,
                "calibration": {
                    "probability_threshold": 0.0,
                    "expected_gain_threshold": 0.0,
                    "harm_gate_pass": True,
                },
                "feature_envelope": {
                    "allowed_scales": [int(data.scale)],
                    "global_min": list(features.global_features),
                    "global_max": list(features.global_features),
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    policy = SparseTailGatPolicy(
        manifest_path,
        evaluation_mode=True,
    )
    preload = policy.preload(data)
    assert preload["success"], preload
    decision = policy(context)
    assert decision["action"] == "NOOP"
    assert decision["decision_reason"] == (
        "manifest_not_evaluation_authorized"
    )
    assert decision["fallback_to_noop"]
    assert decision["hash_valid"]
    assert not decision["ood"]
    assert set(decision["model_scores"]) == set(SPARSE_TAIL_ACTIONS)


def test_two_head_gat_and_censor_aware_loss_are_finite() -> None:
    model = TwoHeadOneDeviationGAT(
        node_input_dim=3,
        edge_input_dim=2,
        candidate_context_dim=4,
        global_context_dim=4,
    )
    outputs = model(
        node_features=torch.tensor(
            [[1.0, 0.0, 0.5], [0.0, 1.0, 0.25]]
        ),
        edge_index=torch.tensor([[0, 1], [1, 0]]),
        edge_features=torch.tensor([[1.0, 0.0], [0.0, 1.0]]),
        candidate_task_masks=torch.tensor(
            [[1.0, 0.0], [0.0, 1.0]]
        ),
        candidate_context=torch.zeros((2, 4)),
        global_context=torch.zeros(4),
    )
    assert outputs["positive_probability"].shape == (2,)
    assert outputs["conditional_positive_relative_gain"].shape == (2,)
    losses = one_deviation_hurdle_loss(
        outputs,
        beneficial=torch.tensor([True, False]),
        observed_mask=torch.tensor([True, False]),
        positive_relative_gain=torch.tensor([0.02, 0.0]),
        right_censored_positive_mask=torch.tensor([False, True]),
        censor_lower_bound_relative=torch.tensor([0.0, 1.0]),
    )
    assert torch.isfinite(losses["loss"])
    assert torch.isfinite(losses["censored_survival_loss"])
    assert (
        float(losses["censored_survival_loss"].detach()) > 0.0
    )


def test_training_tensorization_and_fixed_k_binding() -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "train_p0v4_one_deviation_gat.py"
    )
    spec = importlib.util.spec_from_file_location(
        "train_p0v4_one_deviation_gat_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    features = {
        "node_features": [[0.0, 1.0], [1.0, 0.0]],
        "edge_index": [[0], [1]],
        "edge_features": [[0.5]],
        "candidate_task_masks": [[1.0, 0.0], [0.0, 1.0]],
        "candidate_context": [
            [-1.0, 1.0, 1.0, 0.2, 0.03125, -0.1, 0.2, 0.1, 0.2, 0.0, 0.0, 0.0],
            [-0.5, 1.0, 1.0, 0.2, 0.0625, 0.4, 0.1, 0.1, 0.2, 0.0, 0.0, 0.0],
        ],
        "global_context": [1.0],
    }
    row = {
        "scale": 30,
        **features,
        "instance_content_hash": "instance-a",
        "context_hash": "context-a",
        "split": "train",
        "action_ids": ["promote-a", "promote-b"],
        "candidate_rank_offsets": [1, 2],
        "beneficial": [True, False],
        "observed_mask": [True, True],
        "positive_gain_sec": [1.0, 0.0],
        "positive_relative_gain": [0.01, 0.0],
        "delta_time_sec": [1.0, -1.0],
        "relative_time_gain": [0.01, -0.01],
        "right_censored_positive_mask": [False, False],
        "censor_lower_bound_sec": [0.0, 0.0],
        "censor_lower_bound_relative": [0.0, 0.0],
        "memory_adverse_event": [False, False],
        "fixed_k_selection_hash": "fixed-k-hash",
        "exact_binary_hash": "engine-hash",
        "exact_config_hash": "config-hash",
        "exact_engine_hash": "engine-hash",
        "exact_runtime_binding": _training_runtime_binding(30),
        "exact_runtime_binding_hash": _training_runtime_binding(30)[
            "runtime_binding_hash"
        ],
        "pre_action_feature_hash": stable_payload_hash(features),
    }
    module._validate_rows(
        [row],
        expected_fixed_k_selection_hash="fixed-k-hash",
    )
    tensors = module._tensorize(row)
    assert tensors["inputs"]["candidate_context"].shape == (2, 12)
    assert tensors["beneficial"].tolist() == [True, False]
    from lunar_ice_bpc.guidance.one_deviation_runtime import (
        _runtime_feature_schema,
    )

    assert stable_payload_hash(module._feature_schema(row)) == (
        stable_payload_hash(
            _runtime_feature_schema(tensors["inputs"])
        )
    )
    with pytest.raises(SystemExit, match="fixed E_K"):
        module._validate_rows(
            [row],
            expected_fixed_k_selection_hash="wrong",
        )


def test_runtime_input_hash_payload_covers_every_model_input() -> None:
    from lunar_ice_bpc.guidance.one_deviation_runtime import (
        _tensorize_request,
    )

    data = load_lunar_ice_data(
        generate_instance(5, seed=629001, index=1)
    )
    request = SimpleNamespace(
        data=data,
        memory_limit_gb=1.0,
        wall_time_limit_sec=120.0,
        mode="exact_proof",
        true_duals=JourneyDuals(
            cover={task_id: 0.0 for task_id in data.task_ids}
        ),
    )
    candidates = [
        {
            "candidate_id": f"candidate-{index}",
            "task_ids": [task_id],
            "context": [-1.0, 1.0, 1.0, 0.2],
        }
        for index, task_id in enumerate(data.task_ids[:2])
    ]
    tensors, payload = _tensorize_request(
        request,
        candidates,
        candidate_rank_offsets=(1, 2),
        selected_candidates=candidates,
    )
    assert payload["edge_index"] == tensors["edge_index"].tolist()
    assert payload["candidate_task_masks"] == tensors[
        "candidate_task_masks"
    ].tolist()
    assert tensors["candidate_context"].shape == (2, 12)
    assert stable_payload_hash(payload)


def test_fixed_k_metrics_are_materialized_without_manual_oracle_file(
    tmp_path: Path,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_diverse_escape_oracle.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_diverse_escape_oracle_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    instances = [
        tmp_path / f"instance_{index:03d}_logical_graph.json"
        for index in range(1, 11)
    ]
    for index, path in enumerate(instances, start=1):
        path.write_text(
            json.dumps({"instance": index}), encoding="utf-8"
        )
    output = tmp_path / "oracle"
    output.mkdir()
    (output / "arm_configs").mkdir()
    control_config = tmp_path / "P0V4.yaml"
    control_config.write_text("model_id: P0V4\n", encoding="utf-8")
    config_paths = {"P0V4": control_config}
    for arm in ("E64", "E128", "E256"):
        arm_path = output / "arm_configs" / f"{arm}.yaml"
        arm_path.write_text(
            f"model_id: {arm}\n", encoding="utf-8"
        )
        config_paths[arm] = arm_path
    config = {
        "frozen_control_config": str(control_config),
        "development_stage": {
            "instance_paths": [str(path) for path in instances]
        },
        "arms": {
            "E64": {
                "admission_batch_size": 64,
                "raw_negative_pool_size": 256,
            },
            "E128": {
                "admission_batch_size": 128,
                "raw_negative_pool_size": 512,
            },
            "E256": {
                "admission_batch_size": 256,
                "raw_negative_pool_size": 1024,
            },
        },
    }
    rows = []
    labels = ("P0V4", "E64", "E128", "E256")
    for label, wall, exact_count in (
        ("P0V4", 100.0, 10),
        ("E64", 90.0, 9),
        ("E128", 70.0, 10),
        ("E256", 80.0, 10),
    ):
        for index in range(1, 11):
            instance_key = f"instance_{index:03d}"
            instance_path = instances[index - 1]
            block_order = module._rotated_block_order(labels, index)
            probe = tmp_path / f"{label}_{instance_key}_probe.json"
            probe.write_text(
                json.dumps(
                    {
                        "root_lp_bound": 1.0,
                        "pricing_round_count": 3,
                        "history": [
                            {
                                "node_lp_bound": 1.2,
                                "final_judge_wall_time": 1.0,
                                "candidate_negative_count": 4,
                                "harvest_best_true_rc": -0.1,
                            },
                            {
                                "node_lp_bound": 1.0,
                                "final_judge_wall_time": 1.0,
                                "candidate_negative_count": 1,
                                "harvest_best_true_rc": -0.01,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            exact = index <= exact_count
            state = tmp_path / f"{label}_{instance_key}_state.json"
            state.write_text(
                json.dumps({"instance_key": instance_key}),
                encoding="utf-8",
            )
            rows.append(
                {
                    "arm": label,
                    "instance_key": instance_key,
                    "instance_path": str(instance_path),
                    "instance_sha256": module._sha256(instance_path),
                    "arm_config_path": str(config_paths[label]),
                    "arm_config_sha256": module._sha256(
                        config_paths[label]
                    ),
                    "development_schedule_id": (
                        "development_instance_rotating_arm_blocks_v1"
                    ),
                    "blocked_arm_order": list(block_order),
                    "blocked_arm_position": (
                        block_order.index(label) + 1
                    ),
                    "returncode": 0,
                    "peak_process_tree_rss_gb": (
                        2.0 if label == "E128" else 3.0
                    ),
                    "result_available": True,
                    "result_state_path": str(state),
                    "result_state_sha256": module._sha256(state),
                    "result_row": {
                        "instance_key": instance_key,
                        "bpc_tree_optimal": exact,
                        "algorithm_status": (
                            "BPC_OPTIMAL"
                            if exact
                            else "BPC_INCOMPLETE_PRICING"
                        ),
                        "root_pool_certified": exact,
                        "cold_start_total_sec": wall + index,
                        "root_pool_final_judge_history_round_count": 3,
                        "root_pool_latest_probe_json": str(probe),
                        "no_cheat_pass": True,
                        "config_hash": f"config-{label}",
                    },
                }
            )
    (output / "development_stage_rows.json").write_text(
        json.dumps(rows), encoding="utf-8"
    )
    metrics = module._materialize_development_metrics(
        config, output
    )
    assert metrics["E128"]["exact_closure_count"] == 10
    assert (
        metrics["E128"][
            "commonly_closed_paired_geometric_mean"
        ]
        < metrics["E256"][
            "commonly_closed_paired_geometric_mean"
        ]
    )
    assert (
        output / "development" / "E128" / "oracle_metrics.json"
    ).is_file()
    assert module._select_fixed_k(config, output) == 0
    selection = json.loads(
        (output / "fixed_k_selection.json").read_text(
            encoding="utf-8"
        )
    )
    assert selection["status"] == "FIXED_K_SELECTED"
    assert selection["selected_arm"] == "E128"


def test_fixed_e256_disables_runtime_batch_shrink_and_rejects_clamped_evidence(
    tmp_path: Path,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_diverse_escape_oracle.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_fixed_batch_contract_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    control = tmp_path / "P0V4.yaml"
    control.write_text(
        "\n".join(
            [
                "model_id: P0V4",
                "profiles:",
                "  '50':",
                "    harvest_target: 128",
                "    tree_max_columns_per_round: 128",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    experiment = {
        "frozen_control_config": str(control),
        "negative_escape_policy_id": (
            "diverse_raw_4x_then_p0v4_selector_v1"
        ),
        "batch_master_admission_enabled": True,
        "effective_native_memory_limit_gb": 10.867,
        "arms": {
            "E64": {
                "admission_batch_size": 64,
                "raw_negative_pool_size": 256,
            },
            "E128": {
                "admission_batch_size": 128,
                "raw_negative_pool_size": 512,
            },
            "E256": {
                "admission_batch_size": 256,
                "raw_negative_pool_size": 1024,
            },
        },
    }
    paths = module._materialize_arm_configs(
        experiment, tmp_path / "oracle"
    )
    e128 = module._load_yaml(paths["E128"])
    e256 = module._load_yaml(paths["E256"])
    assert "native_adaptive_harvest_schedule" not in e128
    assert (
        e256["native_adaptive_harvest_schedule"] == "disabled"
    )
    assert e256["profiles"]["50"]["harvest_target"] == 256
    assert e256["profiles"]["50"]["raw_negative_pool_size"] == 1024

    probe = tmp_path / "probe.json"
    probe.write_text(
        json.dumps(
            {
                "history": [
                    {
                        "batch_master_admission_enabled": True,
                        "labeling_final_judge_effective_exact_harvest_target": 128,
                        "negative_escape_triggered": True,
                        "negative_escape_termination_reason": (
                            "RAW_TRUE_NEGATIVE_POOL_REACHED"
                        ),
                        "raw_unique_negative_count": 512,
                        "selected_diverse_negative_count": 128,
                        "can_certify_no_negative": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    launcher_row = {
        "result_row": {
            "instance_key": "instance_001",
            "labeling_final_judge_exact_harvest_target": 256,
            "root_pool_latest_probe_json": str(probe),
            "no_cheat_pass": True,
        },
        "peak_process_tree_rss_gb": 1.0,
    }
    assert not module._development_fixed_k_runtime_contract_valid(
        launcher_row,
        label="E256",
        config_path=paths["E256"],
    )
    record = module._development_record(launcher_row)
    assert record["fixed_k_contract_violation_count"] == 2
    assert record["redline_count"] == 2

    payload = json.loads(probe.read_text(encoding="utf-8"))
    payload["history"][0].update(
        {
            "labeling_final_judge_effective_exact_harvest_target": 256,
            "raw_unique_negative_count": 1024,
            "native_raw_unique_negative_count": 1024,
            "audited_raw_unique_negative_count": 1016,
            "selected_diverse_negative_count": 256,
        }
    )
    probe.write_text(json.dumps(payload), encoding="utf-8")
    assert module._development_fixed_k_runtime_contract_valid(
        launcher_row,
        label="E256",
        config_path=paths["E256"],
    )


def test_development_auc_is_fixed_horizon_and_memory_fail_closed(
    tmp_path: Path,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_diverse_escape_oracle.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_fixed_horizon_metric_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    probe = tmp_path / "probe.json"
    probe.write_text(
        json.dumps(
            {
                "root_lp_bound": 9.0,
                "pricing_round_count": 2,
                "history": [
                    {
                        "round_elapsed_wall_time_sec": 100.0,
                        "node_lp_bound": 10.0,
                        "pricing_state": "FOUND_NEGATIVE",
                        "candidate_negative_count": 9,
                        "harvest_best_true_rc": -0.5,
                    },
                    {
                        "round_elapsed_wall_time_sec": 200.0,
                        "node_lp_bound": 9.0,
                        "pricing_state": "INCOMPLETE_LIMIT",
                        "candidate_negative_count": 0,
                        "harvest_best_true_rc": None,
                    },
                ],
                "final_judge": {
                    "native_backend_result": {
                        "engine_status": "MEMORY_LIMIT"
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    record = module._development_record(
        {
            "result_row": {
                "instance_key": "instance_001",
                "algorithm_status": "BPC_INCOMPLETE_PRICING",
                "cold_start_total_sec": 200.0,
                "root_pool_latest_probe_json": str(probe),
                "no_cheat_pass": True,
            },
            "peak_process_tree_rss_gb": 11.0,
        },
        metric_horizon_sec=3600.0,
    )
    expected_pressure = module.log(10.0) + 0.5
    assert record["root_bound_trace"] == [
        {"elapsed_sec": 100.0, "root_bound": 10.0},
        {"elapsed_sec": 200.0, "root_bound": 9.0},
    ]
    assert record["pricing_pressure_auc"] == pytest.approx(
        expected_pressure
    )
    assert record["metric_horizon_sec"] == 3600.0
    assert record["native_engine_status"] == "MEMORY_LIMIT"
    assert record["resource_adverse_event"]
    assert module._root_gap_auc(
        record["root_bound_trace"],
        best_bound=9.0,
        metric_horizon_sec=3600.0,
    ) == pytest.approx((100.0 / 9.0) / 3600.0)


def test_snapshot_gate_persists_observed_context_shortfall(
    tmp_path: Path,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_diverse_escape_oracle.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_snapshot_gate_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    snapshots = [
        {
            "path": f"snapshot-{index}.json",
            "role": "heavy" if index < 4 else "ordinary",
        }
        for index in range(6)
    ]
    (tmp_path / "snapshot_registry.json").write_text(
        json.dumps(
            {
                "status": "INSUFFICIENT_UNIQUE_PROOF_CONTEXTS",
                "snapshots": snapshots,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="4 heavy and 12 ordinary"):
        module._run_snapshot_stage(
            {
                "snapshot_stage": {
                    "required_heavy_snapshot_count": 4,
                    "required_ordinary_snapshot_count": 12,
                }
            },
            tmp_path,
            arms=("E64",),
            dry_run=False,
            resume=False,
        )
    gate = json.loads(
        (tmp_path / "snapshot_stage_gate.json").read_text(
            encoding="utf-8"
        )
    )
    assert gate["observed_heavy_snapshot_count"] == 4
    assert gate["observed_ordinary_snapshot_count"] == 2
    assert not gate["downstream_fixed_k_selection_authorized"]


def test_snapshot_selector_separates_heavy_proof_and_ordinary_harvest(
    tmp_path: Path,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_diverse_escape_oracle.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_snapshot_selector_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    candidates = []
    for index in range(6):
        context = f"context-{index}"
        candidates.append(
            {
                "source_pricing_mode": "exact_proof",
                "mathematical_context_hash": context,
                "source_final_judge_wall_time_sec": 100.0 - index,
            }
        )
        candidates.append(
            {
                "source_pricing_mode": "negative_harvest",
                "mathematical_context_hash": context,
                "source_final_judge_wall_time_sec": 1.0 + index,
            }
        )
    for index in range(6, 24):
        candidates.append(
            {
                "source_pricing_mode": "negative_harvest",
                "mathematical_context_hash": f"context-{index}",
                "source_final_judge_wall_time_sec": 1.0 + index,
            }
        )
    heavy, ordinary = module._select_snapshot_rows(
        candidates,
        heavy_count=4,
        ordinary_count=12,
    )
    heavy_contexts = {
        row["mathematical_context_hash"] for row in heavy
    }
    ordinary_contexts = {
        row["mathematical_context_hash"] for row in ordinary
    }
    all_proof_contexts = {
        row["mathematical_context_hash"]
        for row in candidates
        if row["source_pricing_mode"] == "exact_proof"
    }
    assert len(heavy) == 4
    assert len(ordinary) == 12
    assert all(row["source_pricing_mode"] == "exact_proof" for row in heavy)
    assert all(
        row["source_pricing_mode"] == "negative_harvest"
        for row in ordinary
    )
    assert heavy_contexts.isdisjoint(ordinary_contexts)
    assert all_proof_contexts.isdisjoint(ordinary_contexts)


def test_snapshot_replay_schedule_rotates_arms_within_blocks(
    tmp_path: Path,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_diverse_escape_oracle.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_snapshot_block_order_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    labels = ("P0V4", "E64", "E128", "E256")
    assert module._rotated_block_order(labels, 1) == labels
    assert module._rotated_block_order(labels, 2) == (
        "E64",
        "E128",
        "E256",
        "P0V4",
    )
    assert module._rotated_block_order(labels, 3) == (
        "E128",
        "E256",
        "P0V4",
        "E64",
    )


def test_snapshot_summary_audits_complete_4k_fail_closed_contract(
    tmp_path: Path,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_diverse_escape_oracle.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_snapshot_summary_audit_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text('{"immutable": true}\n', encoding="utf-8")
    snapshot_row = {
        "path": str(snapshot),
        "sha256": module._sha256(snapshot),
        "role": "heavy",
    }
    config = {
        "snapshot_stage": {
            "blocked_replicates": 1,
            "required_heavy_snapshot_count": 1,
            "required_ordinary_snapshot_count": 0,
        },
        "arms": {
            "E64": {
                "admission_batch_size": 64,
                "raw_negative_pool_size": 256,
            }
        },
    }
    common = {
        "schema_version": (
            "lunar_ice_bpc.proof_tail_snapshot_replay.v1"
        ),
        "fresh_process_arm": True,
        "total_fresh_process_wall_sec": 1.0,
        "source_snapshot": str(snapshot.resolve()),
        "source_snapshot_hash": module._sha256(snapshot),
        "source_binding_hash": "same-mathematical-source",
        "source_role": "mathematical_context",
        "same_mathematical_request_as_source": {
            "branch_context": True,
            "full_cut_context": True,
            "instance": True,
            "mathematical_dual": True,
            "objective_mode": True,
        },
        "labels_dropped": False,
    }
    control_payload = {
        **common,
        "engine_status": "MEMORY_LIMIT",
        "exact_negative_escape_enabled": False,
        "exact_admission_batch_size": 0,
        "exact_raw_negative_pool_size": 0,
        "proof_telemetry": {
            "native_engine_build_hash": "native-engine",
            "negative_escape_enabled": False,
            "negative_escape_triggered": False,
        },
    }
    escape_payload = {
        **common,
        "engine_status": "FOUND_NEGATIVE_PARTIAL",
        "exact_negative_escape_enabled": True,
        "exact_admission_batch_size": 64,
        "exact_raw_negative_pool_size": 256,
        "column_count": 256,
        "frontier_empty": False,
        "search_exhaustive": False,
        "can_enter_certificate_audit": False,
        "can_certify_another_run": False,
        "certificate_blockers": [
            "native_exact_search_incomplete",
            "native_exact_negative_escape_partial",
            "native_frontier_not_empty",
        ],
        "proof_telemetry": {
            "native_engine_build_hash": "native-engine",
            "negative_escape_enabled": True,
            "negative_escape_triggered": True,
            "negative_escape_termination_reason": (
                "RAW_TRUE_NEGATIVE_POOL_REACHED"
            ),
            "raw_unique_negative_count": 256,
        },
    }
    rows = []
    order = ("P0V4", "E64")
    for position, (arm, payload) in enumerate(
        (("P0V4", control_payload), ("E64", escape_payload)),
        start=1,
    ):
        output = tmp_path / f"{arm}.json"
        output.write_text(json.dumps(payload), encoding="utf-8")
        rows.append(
            {
                "arm": arm,
                "snapshot_index": 1,
                "snapshot_role": "heavy",
                "replicate": 1,
                "blocked_schedule_id": (
                    "snapshot_replicate_rotating_arm_blocks_v1"
                ),
                "blocked_arm_order": list(order),
                "blocked_arm_position": position,
                "returncode": 0,
                "output": str(output),
            }
        )

    summary = module._summarize_snapshot_stage(
        rows,
        config=config,
        snapshots=[snapshot_row],
        schedule_id="snapshot_replicate_rotating_arm_blocks_v1",
    )
    assert summary["status"] == "PASS"
    assert summary["expected_row_count"] == 2
    assert summary["total_audit_failure_count"] == 0
    assert summary["downstream_fixed_k_selection_authorized"]

    escape_payload["can_enter_certificate_audit"] = True
    escape_payload["proof_telemetry"]["raw_unique_negative_count"] = 255
    Path(rows[1]["output"]).write_text(
        json.dumps(escape_payload), encoding="utf-8"
    )
    unsafe = module._summarize_snapshot_stage(
        rows,
        config=config,
        snapshots=[snapshot_row],
        schedule_id="snapshot_replicate_rotating_arm_blocks_v1",
    )
    assert unsafe["status"] == "FAIL"
    assert any(
        "partial_escape_fail_closed_contract_mismatch" in failure
        for failure in unsafe["arms"]["E64"]["audit_failures"]
    )
    assert not unsafe["downstream_fixed_k_selection_authorized"]
    escape_payload["engine_status"] = "MEMORY_LIMIT"
    escape_payload["proof_telemetry"]["negative_escape_triggered"] = False
    escape_payload["can_enter_certificate_audit"] = False
    Path(rows[1]["output"]).write_text(
        json.dumps(escape_payload), encoding="utf-8"
    )
    incomplete = module._summarize_snapshot_stage(
        rows,
        config=config,
        snapshots=[snapshot_row],
        schedule_id="snapshot_replicate_rotating_arm_blocks_v1",
    )
    assert any(
        "escape_neither_4k_partial_nor_exhaustive" in failure
        for failure in incomplete["arms"]["E64"]["audit_failures"]
    )
    duplicate = module._summarize_snapshot_stage(
        [*rows, deepcopy(rows[1])],
        config=config,
        snapshots=[snapshot_row],
        schedule_id="snapshot_replicate_rotating_arm_blocks_v1",
    )
    assert duplicate["duplicate_row_count"] == 1
    assert duplicate["status"] == "FAIL"


def test_development_stage_is_snapshot_gated_rotated_and_hash_bound(
    tmp_path: Path,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_diverse_escape_oracle.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_development_schedule_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    instances = []
    for index in (1, 2):
        path = tmp_path / f"instance_{index:03d}_logical_graph.json"
        path.write_text(f'{{"instance": {index}}}\n', encoding="utf-8")
        instances.append(path)
    control = tmp_path / "P0V4.yaml"
    control.write_text("model_id: P0V4\n", encoding="utf-8")
    arm_configs = {}
    arms = ("E64", "E128", "E256")
    for arm in arms:
        path = tmp_path / f"{arm}.yaml"
        path.write_text(f"model_id: {arm}\n", encoding="utf-8")
        arm_configs[arm] = path
    config = {
        "frozen_control_config": str(control),
        "snapshot_stage": {
            "required_heavy_snapshot_count": 1,
            "required_ordinary_snapshot_count": 0,
            "blocked_replicates": 1,
        },
        "development_stage": {
            "instance_paths": [str(path) for path in instances],
            "wall_time_limit_sec": 3600,
        },
        "arms": {arm: {} for arm in arms},
    }
    with pytest.raises(SystemExit, match="requires completed"):
        module._require_snapshot_stage_authorized(config, tmp_path)
    (tmp_path / "snapshot_stage_summary.json").write_text(
        json.dumps(
            {
                "schema_version": (
                    "lunar_ice_bpc.p0v4_fixed_k_snapshot_summary.v2"
                ),
                "status": "PASS",
                "expected_row_count": 4,
                "observed_row_count": 4,
                "total_audit_failure_count": 0,
                "downstream_fixed_k_selection_authorized": True,
            }
        ),
        encoding="utf-8",
    )
    module._require_snapshot_stage_authorized(config, tmp_path)
    assert (
        module._run_development_stage(
            config,
            tmp_path,
            arm_configs=arm_configs,
            arms=arms,
            limit=0,
            dry_run=True,
            resume=False,
        )
        == 0
    )
    rows = json.loads(
        (tmp_path / "development_stage_dry_run_rows.json").read_text(
            encoding="utf-8"
        )
    )
    assert not (tmp_path / "development_stage_rows.json").exists()
    assert [(row["instance_key"], row["arm"]) for row in rows] == [
        ("instance_001", "P0V4"),
        ("instance_001", "E64"),
        ("instance_001", "E128"),
        ("instance_001", "E256"),
        ("instance_002", "E64"),
        ("instance_002", "E128"),
        ("instance_002", "E256"),
        ("instance_002", "P0V4"),
    ]
    assert all(
        row["development_schedule_id"]
        == "development_instance_rotating_arm_blocks_v1"
        for row in rows
    )

    reusable = rows[0]
    state = tmp_path / "state.json"
    state.write_text('{"complete": true}\n', encoding="utf-8")
    reusable.update(
        {
            "returncode": 0,
            "result_available": True,
            "result_state_path": str(state),
            "result_state_sha256": module._sha256(state),
            "result_row": {"instance_key": "instance_001"},
        }
    )
    assert module._development_row_reusable(
        reusable,
        label="P0V4",
        instance_path=instances[0],
        config_path=control,
        schedule_id=reusable["development_schedule_id"],
        block_order=tuple(reusable["blocked_arm_order"]),
        block_position=reusable["blocked_arm_position"],
    )
    reusable["returncode"] = 1
    assert module._development_row_reusable(
        reusable,
        label="P0V4",
        instance_path=instances[0],
        config_path=control,
        schedule_id=reusable["development_schedule_id"],
        block_order=tuple(reusable["blocked_arm_order"]),
        block_position=reusable["blocked_arm_position"],
    )
    reusable["returncode"] = 2
    assert not module._development_row_reusable(
        reusable,
        label="P0V4",
        instance_path=instances[0],
        config_path=control,
        schedule_id=reusable["development_schedule_id"],
        block_order=tuple(reusable["blocked_arm_order"]),
        block_position=reusable["blocked_arm_position"],
    )
    reusable["returncode"] = 1
    reusable["launcher_termination_reason"] = "OUTER_DEADLINE"
    assert not module._development_row_reusable(
        reusable,
        label="P0V4",
        instance_path=instances[0],
        config_path=control,
        schedule_id=reusable["development_schedule_id"],
        block_order=tuple(reusable["blocked_arm_order"]),
        block_position=reusable["blocked_arm_position"],
    )
    reusable["launcher_termination_reason"] = ""
    control.write_text("model_id: changed\n", encoding="utf-8")
    assert not module._development_row_reusable(
        reusable,
        label="P0V4",
        instance_path=instances[0],
        config_path=control,
        schedule_id=reusable["development_schedule_id"],
        block_order=tuple(reusable["blocked_arm_order"]),
        block_position=reusable["blocked_arm_position"],
    )


def test_snapshot_runner_terminates_fresh_process_group(
    tmp_path: Path,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_diverse_escape_oracle.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_snapshot_termination_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import time; time.sleep(60)",
        ],
        start_new_session=True,
    )
    try:
        module._terminate_process_group(process)
        assert process.poll() is not None
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5.0)


def test_opportunity_collector_terminates_fresh_process_group() -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "collect_p0v4_route_opportunities.py"
    )
    spec = importlib.util.spec_from_file_location(
        "collect_p0v4_route_opportunities_termination_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        start_new_session=True,
    )
    try:
        module._terminate_process_group(process)
        assert process.poll() is not None
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5.0)


def test_root_pool_collection_only_is_fail_closed() -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_lunar_ice_b4_2_cold_exact.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_lunar_ice_b4_2_collection_only_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fields = module._route_opportunity_collection_stop_fields(
        latest_stage={"pricing_state": "CERTIFIED_NO_NEGATIVE"},
        latest_probe=Path("probe.json"),
        root_pool_certified=True,
        time_cap_sec=300.0,
        pool_wall_sec=100.0,
    )
    assert fields["algorithm_status"] == (
        "GAT_COLLECTION_ROOT_TRAJECTORY_PERSISTED"
    )
    assert fields["certificate_scope"] == (
        "DIAGNOSTIC_PRICING_FRONTIER"
    )
    assert not fields["exact_certificate"]
    assert not fields["bpc_tree_optimal"]
    assert fields["route_opportunity_collection_root_pool_certified"]
    assert not fields[
        "route_opportunity_collection_root_pool_time_cap_reached"
    ]
    assert fields["route_opportunity_collection_tree_closure_skipped"]
    assert fields["route_opportunity_collection_certificate_suppressed"]


def test_opportunity_collector_binds_selected_exact_native_family(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "collect_p0v4_route_opportunities.py"
    )
    spec = importlib.util.spec_from_file_location(
        "collect_p0v4_route_opportunities_native_binding_test",
        script,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)

    bidirectional = (
        tmp_path / "build/native-spprc-bidirectional-feasibility-v1"
    )
    bidirectional.mkdir(parents=True)
    (bidirectional / "lunar_spprc_native.test.so").touch()
    memory_opt = tmp_path / "build/native-spprc-memory-opt-v2"
    memory_opt.mkdir(parents=True)
    (memory_opt / "lunar_spprc_native.test.so").touch()

    selected = tmp_path / "selected.yaml"
    selected.write_text(
        "profiles:\n"
        "  '30':\n"
        "    backend_id: native_rcspp_bidirectional_root_partial_hybrid_v3\n",
        encoding="utf-8",
    )
    assert module._resolve_native_build_dir(
        "", selected_config=selected
    ) == bidirectional.resolve()

    selected.write_text(
        "profiles:\n"
        "  '30':\n"
        "    backend_id: native_rcspp_inprocess\n",
        encoding="utf-8",
    )
    assert module._resolve_native_build_dir(
        "", selected_config=selected
    ) == memory_opt.resolve()


def test_final_acceptance_gates_require_exact_and_gat_nonregression(
    tmp_path: Path,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_final_acceptance.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_final_acceptance_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    gates = {
        "exact_count_by_scale": {
            "5": 20,
            "10": 20,
            "20": 20,
            "30": 20,
            "50": 14,
        },
        "scale50_held_out_min_exact": 13,
        "scale_small_ratio_max": {
            "5": 1.03,
            "10": 1.03,
            "20": 1.03,
            "30": 1.03,
        },
        "scale20_30_combined_speedup_min": 0.05,
        "scale5_30_combined_speedup_min": 0.05,
        "gat_common_exact_speedup_min": 0.05,
        "gat_scale50_extra_closure_min": 1,
        "inference_p99_ms_max": 10.0,
        "correctness_redline_max": 0,
    }
    exact_metrics = {
        "by_scale": {
            scale: {"exact_count": count}
            for scale, count in (
                ("5", 20),
                ("10", 20),
                ("20", 20),
                ("30", 20),
                ("50", 14),
            )
        },
        "scale50_held_out_exact_count": 13,
        "paired_exact_count_by_scale": {
            "5": 20,
            "10": 20,
            "20": 20,
            "30": 20,
        },
        "paired_geometric_mean_ratio_by_scale": {
            "5": 0.99,
            "10": 0.99,
            "20": 0.94,
            "30": 0.94,
        },
        "scale20_30_combined_ratio": 0.94,
        "scale5_30_combined_ratio": 0.94,
        "correctness_redline_count": 0,
    }
    assert module._exact_gate(exact_metrics, gates)["pass"]
    manifest_path = tmp_path / "deployment_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "deployment_authorized": True,
                "inference_p99_ms": 1.0,
            }
        ),
        encoding="utf-8",
    )
    gate = module._gat_gate(
        {
            "exact_count": 93,
            "exact_candidate_count": 94,
            "commonly_exact_paired_geometric_mean_ratio": 0.90,
            "paired_geometric_mean_ratio_by_scale": {
                "30": 0.94,
                "50": 0.94,
            },
            "commonly_exact_count_by_scale": {"30": 20, "50": 14},
            "scale50_extra_exact_closure_count": 2,
            "correctness_redline_count": 0,
        },
        gates,
        manifest_path,
    )
    assert not gate["pass"]
    assert "gat_exact_count_regressed" in gate["issues"]


def test_final_acceptance_adds_triggered_bidirectional_ablation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_final_acceptance.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_final_acceptance_ablation_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(
        module, "_verify_frozen_p0v4", lambda _experiment: None
    )

    frozen = tmp_path / "P0V4.yaml"
    frozen.write_text(
        "\n".join(
            (
                "model_id: P0V4",
                "profiles:",
                "  '50':",
                "    harvest_target: 128",
                "    backend_id: native_rcspp_host",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    selected = tmp_path / "selected.yaml"
    selected.write_text(
        "\n".join(
            (
                "model_id: E128",
                "exact_negative_escape_enabled: true",
                "batch_master_admission_enabled: true",
                "profiles:",
                "  '50':",
                "    harvest_target: 128",
                "    raw_negative_pool_size: 512",
                (
                    "    backend_id: native_rcspp_bidirectional_"
                    "root_partial_hybrid_v3"
                ),
            )
        )
        + "\n",
        encoding="utf-8",
    )
    fixed = tmp_path / "fixed_k_selection.json"
    fixed.write_text(
        json.dumps(
            {
                "status": "FIXED_K_SELECTED",
                "selected_config": str(selected),
                "selected_config_sha256": module._sha256(selected),
            }
        ),
        encoding="utf-8",
    )
    experiment = {
        "frozen_p0v4_config": str(frozen),
        "frozen_p0v4_config_sha256": module._sha256(frozen),
        "fixed_k_selection": str(fixed),
        "one_deviation_training_manifest": str(
            tmp_path / "missing_training_manifest.json"
        ),
    }
    exact_path, gat_path = module._materialize_configs(
        experiment, tmp_path / "acceptance", require_gat=False
    )
    manifest = json.loads(
        (
            exact_path.parent / "paper_ablation_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["configuration_count"] == 6
    assert [
        row["ablation_id"]
        for row in manifest["configurations"]
    ] == [
        "P0V4",
        "P0V4_BATCH_ADMISSION",
        "P0V4_DIVERSE_NEGATIVE_ESCAPE",
        "P0V4_ESCAPE_BATCH",
        "P0V4_ESCAPE_BATCH_V5_BIDIRECTIONAL",
        "P0V4_ESCAPE_BATCH_ONE_DEVIATION_GAT",
    ]
    assert manifest["bidirectional_included"]
    batch_only = module._read_yaml(
        exact_path.parent / "BatchAdmissionOnly.yaml"
    )
    escape_only = module._read_yaml(
        exact_path.parent / "DiverseEscapeOnly.yaml"
    )
    assert not batch_only["exact_negative_escape_enabled"]
    assert batch_only["batch_master_admission_enabled"]
    assert escape_only["exact_negative_escape_enabled"]
    assert not escape_only["batch_master_admission_enabled"]
    escape_batch = module._read_yaml(
        exact_path.parent / "EscapeBatchUnidirectional.yaml"
    )
    assert escape_batch["profiles"]["50"]["backend_id"] == (
        "native_rcspp_host"
    )
    assert exact_path.is_file()
    assert gat_path.is_file()


def test_final_acceptance_accepts_hash_bound_terminal_gat_stop(
    tmp_path: Path,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_final_acceptance.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_final_acceptance_gat_stop_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "source_gate.json"
    source.write_text('{"gate_pass": false}\n', encoding="utf-8")
    terminal = tmp_path / "terminal_decision.json"
    terminal.write_text(
        json.dumps(
            {
                "schema_version": (
                    "lunar_ice_bpc.p0v4_one_deviation_"
                    "terminal_decision.v1"
                ),
                "status": "STOPPED_BY_PREDECLARED_GATES",
                "terminal_decision_valid": True,
                "exact_acceptance_may_proceed_without_gat": True,
                "gat_performance_claim_authorized": False,
                "certificate_or_bound_role": "none",
                "baseline_mutated": False,
                "artifacts": [
                    {
                        "path": str(source),
                        "sha256": module._sha256(source),
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    experiment = {
        "one_deviation_deployment_manifest": str(
            tmp_path / "missing_deployment.json"
        ),
        "one_deviation_terminal_decision": str(terminal),
    }
    state = module._one_deviation_branch_state(experiment)
    assert state["mode"] == "stopped"
    assert state["terminal_decision_sha256"] == module._sha256(terminal)

    source.write_text('{"gate_pass": true}\n', encoding="utf-8")
    invalid = module._one_deviation_branch_state(experiment)
    assert invalid["mode"] == "pending"
    assert any(
        "terminal_source_artifact_hash_mismatch" in issue
        for issue in invalid["issues"]
    )


def test_two_head_training_writes_loadable_deployment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "train_p0v4_one_deviation_gat.py"
    )
    spec = importlib.util.spec_from_file_location(
        "train_p0v4_one_deviation_gat_integration_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    adverse_predictions = module._calibration_prediction_rows(
        {
            "instance_content_hash": "memory-adverse-instance",
            "context_hash": "memory-adverse-context",
            "action_ids": ["censored-adverse"],
            "candidate_rank_offsets": [1],
            "observed_mask": [False],
            "memory_adverse_event": [True],
            "delta_time_sec": [0.0],
            "relative_time_gain": [0.0],
        },
        probabilities=[0.99],
        expected_relative_gains=[0.10],
        context_ood=False,
        allowed_rank_offsets=[1],
    )
    assert len(adverse_predictions) == 1
    assert adverse_predictions[0]["outcome"] == "harmful"
    fixed_path = tmp_path / "fixed_k_selection.json"
    fixed_path.write_text(
        json.dumps(
            {
                "status": "FIXED_K_SELECTED",
                "selected_batch_size": 128,
            }
        ),
        encoding="utf-8",
    )
    oracle_path = tmp_path / "oracle_gate.json"
    oracle_path.write_text(
        json.dumps({"gat_training_authorized": True}),
        encoding="utf-8",
    )
    action_ids = [f"promote-{index:03d}" for index in range(32)]
    features = {
        "node_features": [[0.0, 1.0], [1.0, 0.0]],
        "edge_index": [[0], [1]],
        "edge_features": [[0.5]],
        "candidate_task_masks": [
            [1.0, 0.0] if index % 2 == 0 else [0.0, 1.0]
            for index in range(32)
        ],
        "candidate_context": [
            [
                -1.0 + float(index) / 64.0,
                1.0,
                1.0,
                0.2,
                float(index + 1) / 32.0,
                float(index) / 64.0,
                0.2,
                0.1,
                0.2,
                0.0,
                0.0,
                0.0,
            ]
            for index in range(32)
        ],
        "global_context": [1.0],
    }
    fixed_hash = module._sha256(fixed_path)
    rows = [
        {
            **features,
            "scale": 30,
            "instance_content_hash": "train-instance",
            "context_hash": "train-context",
            "split": "train",
            "action_ids": action_ids,
            "candidate_rank_offsets": [
                index + 1 for index in range(32)
            ],
            "beneficial": [True] * 32,
            "observed_mask": [True] * 32,
            "positive_gain_sec": [1.0] * 32,
            "positive_relative_gain": [0.01] * 32,
            "delta_time_sec": [1.0] * 32,
            "relative_time_gain": [0.01] * 32,
            "right_censored_positive_mask": [False] * 32,
            "censor_lower_bound_sec": [0.0] * 32,
            "censor_lower_bound_relative": [0.0] * 32,
            "memory_adverse_event": [False] * 32,
            "fixed_k_selection_hash": fixed_hash,
            "exact_binary_hash": "engine-hash",
            "exact_config_hash": "config-train",
            "exact_engine_hash": "engine-hash",
            "exact_runtime_binding": _training_runtime_binding(30),
            "exact_runtime_binding_hash": _training_runtime_binding(30)[
                "runtime_binding_hash"
            ],
            "pre_action_feature_hash": stable_payload_hash(features),
            "post_action_features_exposed_to_model": False,
            "certificate_paths_mutated": False,
        }
    ]
    for index in range(80):
        candidate_index = index % len(action_ids)
        calibration_features = {
            **features,
            "candidate_task_masks": [
                features["candidate_task_masks"][candidate_index]
            ],
            "candidate_context": [
                features["candidate_context"][candidate_index]
            ],
        }
        rows.append(
            {
                **calibration_features,
                "scale": 50,
                "instance_content_hash": "calibration-instance",
                "context_hash": f"calibration-context-{index:03d}",
                "split": "calibration",
                "action_ids": [action_ids[candidate_index]],
                "candidate_rank_offsets": [1],
                "beneficial": [True],
                "observed_mask": [True],
                "positive_gain_sec": [1.0],
                "positive_relative_gain": [0.01],
                "delta_time_sec": [1.0],
                "relative_time_gain": [0.01],
                "right_censored_positive_mask": [False],
                "censor_lower_bound_sec": [0.0],
                "censor_lower_bound_relative": [0.0],
                "memory_adverse_event": [False],
                "fixed_k_selection_hash": fixed_hash,
                "exact_binary_hash": "engine-hash",
                "exact_config_hash": "config-calibration",
                "exact_engine_hash": "engine-hash",
                "exact_runtime_binding": _training_runtime_binding(50),
                "exact_runtime_binding_hash": (
                    _training_runtime_binding(50)[
                        "runtime_binding_hash"
                    ]
                ),
                "pre_action_feature_hash": stable_payload_hash(
                    calibration_features
                ),
                "post_action_features_exposed_to_model": False,
                "certificate_paths_mutated": False,
            }
        )
    dataset_path = tmp_path / "dataset.jsonl"
    dataset_path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    output = tmp_path / "model"
    monkeypatch.setattr(
        "sys.argv",
        [
            str(script),
            "--dataset",
            str(dataset_path),
            "--oracle-gate",
            str(oracle_path),
            "--fixed-k-selection",
            str(fixed_path),
            "--output-dir",
            str(output),
            "--epochs",
            "1",
        ],
    )
    assert module.main() == 0
    manifest = json.loads(
        (output / "training_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["evaluation_authorized"]
    assert not manifest["deployment_authorized"]
    assert manifest["deployment_gate_status"] == (
        "HELDOUT_END_TO_END_REQUIRED"
    )
    assert manifest["calibration"]["harmful_rate_95_upper"] <= 0.05
    assert (
        manifest["calibration"]["beneficial_precision_95_lower"]
        >= 0.80
    )
    assert manifest["allowed_exact_engine_hashes"] == [
        "engine-hash"
    ]
    assert manifest["allowed_exact_runtime_binding_hashes"] == sorted(
        {
            _training_runtime_binding(30)["runtime_binding_hash"],
            _training_runtime_binding(50)["runtime_binding_hash"],
        }
    )
    assert sorted(
        manifest["exact_runtime_bindings_by_scale"], key=int
    ) == ["30", "50"]
    assert manifest["allowed_scales"] == [30, 50]
    assert manifest["feature_schema_hash"]
    assert manifest["runtime_policy_id"] == (
        "one_deviation_full_audited_p0_prefix_v1"
    )
    assert len(manifest["runtime_implementation_hash"]) == 64
    assert manifest["deployment_rank_offsets"] == [1]
    assert manifest["deployment_candidate_scope"] == (
        "intersection_of_calibration_context_rank_offsets"
    )
    from lunar_ice_bpc.guidance.one_deviation_runtime import (
        _load_model,
    )

    loaded_manifest, loaded_model = _load_model(
        output / "training_manifest.json"
    )
    assert loaded_manifest["checkpoint_sha256"] == (
        manifest["checkpoint_sha256"]
    )
    assert isinstance(loaded_model, TwoHeadOneDeviationGAT)


def test_oracle_suite_context_selection_is_instance_stratified() -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_one_deviation_oracle_suite.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_one_deviation_oracle_suite_selection_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    records = [
        {
            "path": Path(f"/tmp/{instance}-{index}.json"),
            "scale": scale,
            "instance_content_hash": instance,
            "snapshot_hash": f"{index:03d}-{instance}",
        }
        for scale, instance, count in (
            (30, "a", 8),
            (30, "b", 2),
            (30, "c", 2),
            (50, "d", 3),
            (50, "e", 3),
        )
        for index in range(count)
    ]
    selected = module._stratified_manifest_records(
        records,
        limits_by_scale={30: 6, 50: 4},
    )
    scale30 = [row for row in selected if row["scale"] == 30]
    scale50 = [row for row in selected if row["scale"] == 50]
    assert [row["instance_content_hash"] for row in scale30[:3]] == [
        "a",
        "b",
        "c",
    ]
    assert len(scale30) == 6
    assert [row["instance_content_hash"] for row in scale50] == [
        "d",
        "e",
        "d",
        "e",
    ]

    scope = module._suite_authorization_scope(
        {
            "expensive_oracle_authorized": False,
            "audit": {
                "scales": {
                    "30": {"gate_pass": True},
                    "50": {"gate_pass": False},
                }
            },
        },
        requested_scales={30},
        engineering_smoke=True,
    )
    assert scope["engineering_smoke_only"]
    assert not scope["gat_training_authorized"]
    assert not scope["formal_claim_authorized"]
    with pytest.raises(ValueError, match="scale opportunity gate failed"):
        module._suite_authorization_scope(
            {
                "expensive_oracle_authorized": False,
                "audit": {"scales": {"50": {"gate_pass": False}}},
            },
            requested_scales={50},
            engineering_smoke=True,
        )


def test_one_deviation_engineering_smoke_is_scale_gated_and_not_trainable() -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_one_deviation_oracle.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_one_deviation_oracle_smoke_scope_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    census = {
        "expensive_oracle_authorized": False,
        "audit": {
            "scales": {
                "30": {"gate_pass": True},
                "50": {"gate_pass": False},
            }
        },
    }
    scope = module._rollout_authorization_scope(
        census, scale=30, engineering_smoke=True
    )
    assert scope == {
        "execution_scope": "engineering_smoke_scale_gate_only",
        "formal_joint_scale_census_authorized": False,
        "engineering_smoke_only": True,
        "gat_training_authorized": False,
        "formal_claim_authorized": False,
    }
    with pytest.raises(ValueError, match="did not authorize"):
        module._rollout_authorization_scope(
            census, scale=30, engineering_smoke=False
        )
    with pytest.raises(ValueError, match="scale opportunity gate"):
        module._rollout_authorization_scope(
            census, scale=50, engineering_smoke=True
        )


def test_engineering_smoke_gate_requires_material_five_percent_signal() -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "audit_p0v4_one_deviation_engineering_smoke.py"
    )
    spec = importlib.util.spec_from_file_location(
        "audit_p0v4_one_deviation_engineering_smoke_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    weak = [
        {
            "instance_content_hash": f"instance-{index}",
            "best_observed_relative_gain": gain,
            "redline_count": 0,
        }
        for index, gain in enumerate((0.003, 0.012, 0.002, 0.001, 0.013))
    ]
    gate = module._signal_gate(
        weak,
        rejected_count=0,
        minimum_contexts=5,
        minimum_instances=5,
        minimum_strong_contexts=2,
        minimum_relative_gain=0.05,
    )
    assert gate["structural_gate_pass"]
    assert not gate["signal_gate_pass"]
    assert gate["stop_or_revise_action_definition"]
    strong = [dict(row) for row in weak]
    strong[0]["best_observed_relative_gain"] = 0.06
    strong[1]["best_observed_relative_gain"] = 0.08
    gate = module._signal_gate(
        strong,
        rejected_count=0,
        minimum_contexts=5,
        minimum_instances=5,
        minimum_strong_contexts=2,
        minimum_relative_gain=0.05,
    )
    assert gate["signal_gate_pass"]
    assert gate["bounded_expansion_recommended"]


def test_heldout_gate_requires_five_percent_on_each_scale() -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "promote_p0v4_one_deviation_gat.py"
    )
    spec = importlib.util.spec_from_file_location(
        "promote_p0v4_one_deviation_gat_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = [
        {
            "scale": scale,
            "instance_content_hash": f"heldout-{scale}-{index}",
            "control_exact": True,
            "candidate_exact": True,
            "control_time_sec": 100.0,
            "candidate_time_sec": 94.0,
            "redline_count": 0,
            "candidate_inference_latencies_ms": [1.0, 1.2],
        }
        for scale in (30, 50)
        for index in range(10)
    ]
    report = module.audit_heldout_paired_results(
        rows,
        training_manifest={
            "train_instance_hashes": ["train"],
            "calibration_instance_hashes": ["calibration"],
        },
    )
    assert report["gate_pass"]
    training_runtime = {
        str(scale): _training_runtime_binding(scale)
        for scale in (30, 50)
    }
    for row in rows:
        row.update(
            {
                "candidate_evaluation_mode": True,
                "candidate_runtime_error_count": 0,
                "training_manifest_sha256": "training-hash",
                "fixed_k_selection_sha256": "fixed-hash",
                "exact_runtime_binding_hash": training_runtime[
                    str(row["scale"])
                ]["runtime_binding_hash"],
            }
        )
    strict = module.audit_heldout_paired_results(
        rows,
        training_manifest={
            "train_instance_hashes": ["train"],
            "calibration_instance_hashes": ["calibration"],
            "fixed_k_selection_sha256": "fixed-hash",
            "exact_runtime_bindings_by_scale": training_runtime,
        },
        expected_training_manifest_sha256="training-hash",
        require_runtime_binding=True,
    )
    assert strict["gate_pass"]
    rows[-1]["candidate_time_sec"] = 200.0
    failed = module.audit_heldout_paired_results(
        rows,
        training_manifest={
            "train_instance_hashes": ["train"],
            "calibration_instance_hashes": ["calibration"],
        },
    )
    assert not failed["gate_pass"]
    assert not failed["scale_reports"]["50"]["gate_pass"]


def test_heldout_runner_audits_evaluation_runtime_binding() -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_one_deviation_heldout.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_one_deviation_heldout_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    probe = {
        "history": [
            {
                "one_deviation_runtime_enabled": True,
                "one_deviation_evaluation_mode": True,
                "one_deviation_executed": True,
                "one_deviation_runtime_error": "",
                "one_deviation_ood": False,
                "one_deviation_manifest_sha256": "manifest-hash",
                "one_deviation_exact_runtime_binding_hash": (
                    "runtime-hash"
                ),
            },
            {
                "one_deviation_runtime_enabled": False,
                "one_deviation_executed": False,
            },
        ]
    }
    audit = module._audit_probe_history(
        probe,
        expected_manifest_sha256="manifest-hash",
        expected_runtime_binding_hash="runtime-hash",
        candidate=True,
    )
    assert audit["runtime_call_count"] == 1
    assert audit["promotion_count"] == 1
    assert not audit["runtime_error_count"]
    assert not audit["manifest_mismatch_count"]
    probe["history"][0]["one_deviation_evaluation_mode"] = False
    failed = module._audit_probe_history(
        probe,
        expected_manifest_sha256="manifest-hash",
        expected_runtime_binding_hash="runtime-hash",
        candidate=True,
    )
    assert failed["evaluation_mode_mismatch_count"] == 1


def test_blocked_p0v4_v5_nonregression_audit_is_paired_and_gated(
    tmp_path: Path,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "audit_p0v4_v5_paired_nonregression.py"
    )
    spec = importlib.util.spec_from_file_location(
        "audit_p0v4_v5_paired_nonregression_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for block in range(1, 4):
        for arm in ("P0V4", "V5"):
            (tmp_path / f"block{block:02d}_{arm}").mkdir()

    def fake_read_arm(arm_dir, *, scale, expected_instances):
        assert scale == 5
        assert expected_instances == 2
        candidate = arm_dir.name.endswith("_V5")
        timings = {
            "instance_001": 98.0 if candidate else 100.0,
            "instance_002": 196.0 if candidate else 200.0,
        }
        return timings, {"valid": True}, {"summary": str(arm_dir)}

    with patch.object(module, "_read_arm", side_effect=fake_read_arm):
        audit = module.audit_blocked_pairs(
            tmp_path,
            scale=5,
            minimum_blocks=3,
            expected_instances=2,
            ratio_max=1.03,
        )
    assert audit["pass"]
    assert audit["paired_observation_count"] == 6
    assert audit["pooled_geometric_mean_ratio"] == pytest.approx(0.98)
    assert audit["candidate_win_count"] == 6


def test_sparse_tail_replay_suite_discovers_only_natural_root_contexts(
    tmp_path: Path,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_sparse_tail_replay_suite.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_sparse_tail_replay_suite_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    instance = tmp_path / "instance.json"
    instance.write_text("{}\n", encoding="utf-8")
    probe = tmp_path / "probe.json"
    rows = [
        {
            "round": 1,
            "node_id": "root",
            "pricing_state": "FOUND_NEGATIVE",
            "final_judge_called": True,
            "labeling_final_judge_harvest_pass_attempted": True,
            "labeling_final_judge_proof_pass_wall_time": 20.0,
            "dual_context": {
                "task_duals": {"task": 1.0},
                "cut_duals": {},
                "dual_fingerprint": "dual-1",
            },
        },
        {
            "round": 2,
            "node_id": "root",
            "pricing_state": "CERTIFIED_NO_NEGATIVE",
            "final_judge_called": True,
            "labeling_final_judge_harvest_pass_attempted": True,
            "labeling_final_judge_proof_pass_wall_time": 30.0,
            "dual_context": {
                "task_duals": {"task": 2.0},
                "cut_duals": {},
                "dual_fingerprint": "dual-2",
            },
        },
        {
            "round": 3,
            "node_id": "node_007",
            "pricing_state": "FOUND_NEGATIVE",
            "final_judge_called": True,
            "labeling_final_judge_harvest_pass_attempted": True,
            "labeling_final_judge_proof_pass_wall_time": 100.0,
            "dual_context": {
                "task_duals": {"task": 3.0},
                "cut_duals": {},
            },
        },
        {
            "round": 4,
            "node_id": "root",
            "pricing_state": "FOUND_NEGATIVE",
            "final_judge_called": True,
            "labeling_final_judge_harvest_pass_attempted": True,
            "labeling_final_judge_proof_pass_wall_time": 100.0,
            "dual_context": {
                "task_duals": {"task": 4.0},
                "cut_duals": {"cut": 1.0},
            },
        },
    ]
    probe.write_text(
        json.dumps(
            {
                "instance_path": str(instance),
                "instance_content_hash": "instance-a",
                "scale": 30,
                "history": rows,
            }
        ),
        encoding="utf-8",
    )
    discovered = module.discover_contexts(
        (probe,), minimum_source_proof_sec=10.0
    )
    assert [row["round"] for row in discovered] == [1, 2]
    assert {row["source_state"] for row in discovered} == {
        "FOUND_NEGATIVE",
        "CERTIFIED_NO_NEGATIVE",
    }
    assert len({row["context_id"] for row in discovered}) == 2


def test_sparse_tail_replay_suite_freezes_balanced_instance_diverse_prefix() -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_p0v4_sparse_tail_replay_suite.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_p0v4_sparse_tail_replay_suite_selection_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    contexts = [
        {
            "context_id": f"{instance}-{state}-{rank}",
            "instance_content_hash": instance,
            "source_state": state,
            "source_proof_wall_sec": wall,
            "round": rank,
        }
        for instance, wall in (("a", 100.0), ("b", 80.0), ("c", 60.0))
        for state in ("FOUND_NEGATIVE", "CERTIFIED_NO_NEGATIVE")
        for rank in (1, 2)
    ]
    selected = module.select_contexts(
        contexts,
        context_limit=6,
        max_contexts_per_instance=2,
    )
    assert len(selected) == 6
    assert {row["instance_content_hash"] for row in selected} == {
        "a",
        "b",
        "c",
    }
    assert {row["source_state"] for row in selected} == {
        "FOUND_NEGATIVE",
        "CERTIFIED_NO_NEGATIVE",
    }
    assert all(
        sum(
            row["instance_content_hash"] == instance
            for row in selected
        )
        == 2
        for instance in ("a", "b", "c")
    )


def test_sparse_tail_fixed_pilot_label_requires_executable_partial_return(
    tmp_path: Path,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "build_p0v4_sparse_tail_gat_pilot_dataset.py"
    )
    spec = importlib.util.spec_from_file_location(
        "build_p0v4_sparse_tail_gat_pilot_dataset_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    probe = tmp_path / "probe.json"
    probe.write_text("{}\n", encoding="utf-8")
    instance = tmp_path / "instance.json"
    instance.write_text("{}\n", encoding="utf-8")
    instance_sha = hashlib.sha256(instance.read_bytes()).hexdigest()
    context = {
        "round": 7,
        "source_probe_sha256": hashlib.sha256(probe.read_bytes()).hexdigest(),
        "instance_sha256": instance_sha,
        "source_proof_wall_sec": 200.0,
    }
    replay_path = tmp_path / "S4.json"
    replay = {
        "schema_version": (
            "lunar_ice_bpc.p0v4_sparse_tail_deviation_replay.v1"
        ),
        "status": "SAFE_REPLAY_COMPLETE",
        "action": "S4",
        "source_round": 7,
        "source_probe_sha256": context["source_probe_sha256"],
        "instance_sha256": instance_sha,
        "engine_status": "TIMEOUT",
        "negative_escape_triggered": False,
        "partial_columns_valid": True,
        "column_count": 1,
        "fresh_process_wall_sec": 60.0,
        "reconstruction_audit": {"true_negative_column_count": 1},
        "safety": {
            "issues": [],
            "replay_certificate_authority": "none",
        },
    }
    replay_path.write_text(json.dumps(replay), encoding="utf-8")
    suite_row = {
        "status": "COMPLETED",
        "replay": str(replay_path),
        "replay_sha256": hashlib.sha256(replay_path.read_bytes()).hexdigest(),
        "true_negative_column_count": 1,
    }
    timed_out = module._action_label(
        context=context,
        action="S4",
        suite_row=suite_row,
    )
    assert not timed_out["executable_partial_return"]
    assert not timed_out["beneficial"]
    assert timed_out["delta_time_sec"] == pytest.approx(-60.0)

    replay["engine_status"] = "FOUND_NEGATIVE_PARTIAL"
    replay["negative_escape_triggered"] = True
    replay_path.write_text(json.dumps(replay), encoding="utf-8")
    suite_row["replay_sha256"] = hashlib.sha256(
        replay_path.read_bytes()
    ).hexdigest()
    partial = module._action_label(
        context=context,
        action="S4",
        suite_row=suite_row,
    )
    assert partial["executable_partial_return"]
    assert partial["beneficial"]
    assert partial["delta_time_sec"] == pytest.approx(140.0)


def test_sparse_tail_fixed_pilot_split_is_outcome_independent() -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "build_p0v4_sparse_tail_gat_pilot_dataset.py"
    )
    spec = importlib.util.spec_from_file_location(
        "build_p0v4_sparse_tail_gat_pilot_split_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    first = module.split_for_instance(
        binding_hash="binding-a",
        instance_sha256="instance-sha-a",
    )
    second = module.split_for_instance(
        binding_hash="binding-a",
        instance_sha256="instance-sha-a",
    )
    assert first == second
    assert first in {"train", "calibration"}
    with pytest.raises(ValueError, match="must be non-empty"):
        module.split_for_instance(
            binding_hash="",
            instance_sha256="instance-sha-a",
        )


def test_final_acceptance_pipeline_requires_bound_terminal_rows(
    tmp_path: Path,
) -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "continue_p0v4_final_acceptance_pipeline.py"
    )
    spec = importlib.util.spec_from_file_location(
        "continue_p0v4_final_acceptance_pipeline_test", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    binding_hash = "implementation-binding"
    (tmp_path / "p0v4_launch_manifest.json").write_text(
        json.dumps(
            {
                "evidence_usable": True,
                "implementation_stable_during_launch": True,
                "implementation_binding_hash_before": binding_hash,
                "implementation_binding_hash_after": binding_hash,
            }
        ),
        encoding="utf-8",
    )
    state = tmp_path / "scale_050" / "b4_2_cold_exact_state.json"
    state.parent.mkdir()
    state.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "scale": 50,
                        "instance_key": "instance_002",
                        "row_terminal": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    runner_sha = module._sha256(module.RUNNER)
    assert module._completed_stage_issues(
        tmp_path,
        expected_rows=1,
        expected_runner_sha=runner_sha,
    ) == []
    state.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "scale": 50,
                        "instance_key": "instance_002",
                        "row_terminal": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert "nonterminal_state_row" in module._completed_stage_issues(
        tmp_path,
        expected_rows=1,
        expected_runner_sha=runner_sha,
    )
