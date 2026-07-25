from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from lunar_ice_bpc.domain.scheduling import generate_instance
from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import (
    column_signature_from_journey,
)
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
from lunar_ice_bpc.exact.bpc.guidance.contracts import (
    CanonicalSolveBindingV2,
)
from lunar_ice_bpc.exact.bpc.pricing.backends import (
    BACKEND_MODE_NEGATIVE_HARVEST,
    BackendPricingRequest,
)
from lunar_ice_bpc.exact.bpc.pricing.harvest import (
    harvest_addable_negative_columns,
)
from lunar_ice_bpc.exact.core.branching import BranchContext
from lunar_ice_bpc.exact.core.cuts import CutContext, true_dual_binding_hash
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.exact.solver.journey_driver import (
    enumerate_direct_journey_columns,
)
from lunar_ice_bpc.guidance.route_admission import (
    P0_KEEP_BATCH_ACTION_ID,
    ROUTE_ADMISSION_LEXICOGRAPHIC_OBJECTIVE_SPEC_V2,
    ROUTE_ADMISSION_OBJECTIVE_SPEC_V1,
    build_boundary_swap_actions,
    build_route_admission_snapshot,
    materialize_next_rmp_pairwise_targets,
)


def _pure_snapshot() -> dict:
    instance_hash = "instance-hash"
    binding = {
        "binding_hash": "binding-hash",
        "instance_hash": instance_hash,
        "objective_mode": "official",
    }
    return build_route_admission_snapshot(
        canonical_solve_binding=binding,
        instance_content_hash=instance_hash,
        scale=30,
        node_id="root",
        candidate_rows=[
            {
                "candidate_id": f"candidate-{index}",
                "true_reduced_cost": -10.0 + index,
                "task_set": [f"T{index}"],
                "column_payload": {"sorties": [{"tasks": [f"T{index}"]}]},
            }
            for index in range(6)
        ],
        p0_ordered_candidate_ids=[
            f"candidate-{index}" for index in range(6)
        ],
        p0_selected_candidate_ids=[
            f"candidate-{index}" for index in range(4)
        ],
        selection_limit=4,
        active_column_payloads=[{"sorties": [{"tasks": ["T0"]}]}],
        branch_context={},
        full_cut_context={},
        source_phase="test",
        executed_objective_spec_id="normalized-objective.v1",
    )


def test_boundary_swap_contest_never_redefines_legal_universe() -> None:
    snapshot = _pure_snapshot()
    manifest = build_boundary_swap_actions(
        snapshot,
        selected_boundary_width=2,
        omitted_contest_cap=2,
        max_swap_actions=4,
    )
    assert manifest["actions"][0]["action_id"] == P0_KEEP_BATCH_ACTION_ID
    assert len(manifest["actions"]) == 5
    assert manifest["measurement_contest_is_legal_universe"] is False
    assert manifest["guidance_filter_count"] == 0
    assert manifest["permanent_drop_count"] == 0
    assert set(manifest["deferred_candidate_ids"]) == {
        "candidate-4",
        "candidate-5",
    }
    for action in manifest["actions"]:
        assert len(action["admitted_candidate_ids"]) == 4
        assert set(action["admitted_candidate_ids"]).issubset(
            set(snapshot["legal_candidate_ids"])
        )


def test_next_rmp_target_is_raw_within_context_and_censoring_is_masked() -> None:
    snapshot = _pure_snapshot()
    action_id = build_boundary_swap_actions(snapshot)["actions"][1][
        "action_id"
    ]
    measurements = [
        {
            "snapshot_hash": snapshot["snapshot_hash"],
            "objective_spec_id": (
                ROUTE_ADMISSION_LEXICOGRAPHIC_OBJECTIVE_SPEC_V2
            ),
            "action_id": P0_KEEP_BATCH_ACTION_ID,
            "swap_out_candidate_id": None,
            "swap_in_candidate_id": None,
            "status": "RMP_OPTIMAL",
            "next_rmp_objective": 10.0,
            "deferred_negative_count": 2,
            "deferred_negative_mass": 3.0,
            "deferred_best_true_rc": -2.0,
            "censored": False,
        },
        {
            "snapshot_hash": snapshot["snapshot_hash"],
            "objective_spec_id": (
                ROUTE_ADMISSION_LEXICOGRAPHIC_OBJECTIVE_SPEC_V2
            ),
            "action_id": action_id,
            "swap_out_candidate_id": "candidate-3",
            "swap_in_candidate_id": "candidate-4",
            "status": "RMP_OPTIMAL",
            "next_rmp_objective": 8.5,
            "deferred_negative_count": 2,
            "deferred_negative_mass": 2.0,
            "deferred_best_true_rc": -1.5,
            "censored": False,
        },
        {
            "snapshot_hash": snapshot["snapshot_hash"],
            "objective_spec_id": (
                ROUTE_ADMISSION_LEXICOGRAPHIC_OBJECTIVE_SPEC_V2
            ),
            "action_id": "unmeasured-action",
            "swap_out_candidate_id": "candidate-2",
            "swap_in_candidate_id": "candidate-5",
            "status": "RMP_INCOMPLETE",
            "next_rmp_objective": None,
            "deferred_negative_count": None,
            "deferred_negative_mass": None,
            "deferred_best_true_rc": None,
            "censored": True,
        },
    ]
    targets = materialize_next_rmp_pairwise_targets(
        snapshot, measurements
    )
    assert targets["targets"][0][
        "raw_next_rmp_objective_advantage"
    ] == pytest.approx(1.5)
    assert targets["targets"][0]["pairwise_label"] == 1
    assert targets["targets"][0]["swap_out_candidate_id"] == "candidate-3"
    assert targets["targets"][0]["swap_in_candidate_id"] == "candidate-4"
    assert targets["unlabelled_action_ids"] == ["unmeasured-action"]
    assert not targets["cross_context_normalization_applied"]
    assert not targets["legacy_four_coefficient_cost_used"]
    assert not targets["fixed_censoring_penalty_used"]
    assert not targets["linear_training_authorized"]


def test_active_harvest_boundary_writes_replayable_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_instance = generate_instance(5, seed=629001, index=1)
    data = load_lunar_ice_data(raw_instance)
    universe = enumerate_direct_journey_columns(
        data, max_exact_tasks=5
    ).columns
    active = next(
        column
        for column in universe
        if set(column.task_set) == set(data.task_ids)
    )
    candidates = tuple(
        column for column in universe if column is not active
    )[:3]
    pool = ColumnPool()
    view = MasterColumnView()
    active_bpc = BpcColumn(
        signature=column_signature_from_journey(active),
        objective=active.objective,
        payload=active,
    )
    assert pool.add(active_bpc).added
    assert view.add_from_pool(active_bpc, node_id="root", pool=pool)
    duals = JourneyDuals(
        cover={task_id: 1000.0 for task_id in data.task_ids},
        fleet_limit=0.0,
        cuts={},
    )
    structural_dir = tmp_path / "structural-zero"
    monkeypatch.setenv(
        "LUNAR_ICE_GAT_TRAINING_ROWS_DIR", str(structural_dir)
    )
    structural_selected, structural_telemetry = (
        harvest_addable_negative_columns(
            tuple(
                (-10.0 + index, column)
                for index, column in enumerate(candidates)
            ),
            pool=pool,
            view=view,
            max_selected=3,
            guidance_data=data,
            guidance_duals=duals,
            guidance_rmp_iteration_id="root-structural-zero",
        )
    )
    assert len(structural_selected) == 3
    structural_recording = structural_telemetry[
        "guidance_training_recording"
    ]
    assert structural_recording["written"]
    assert not structural_recording["route_admission_boundary_active"]
    assert not structural_recording["route_admission_snapshot_written"]
    assert not list(structural_dir.rglob("route_admission_snapshot.json"))

    monkeypatch.setenv(
        "LUNAR_ICE_GAT_TRAINING_ROWS_DIR", str(tmp_path / "active")
    )
    selected, telemetry = harvest_addable_negative_columns(
        tuple(
            (-10.0 + index, column)
            for index, column in enumerate(candidates)
        ),
        pool=pool,
        view=view,
        max_selected=1,
        guidance_data=data,
        guidance_duals=duals,
        guidance_rmp_iteration_id="root-test",
    )
    assert len(selected) == 1
    recording = telemetry["guidance_training_recording"]
    assert recording["written"]
    assert recording["route_admission_snapshot_written"]
    snapshot_paths = [
        Path(value)
        for value in recording["paths"]
        if value.endswith("route_admission_snapshot.json")
    ]
    assert len(snapshot_paths) == 1
    snapshot = json.loads(snapshot_paths[0].read_text(encoding="utf-8"))
    assert snapshot["instance_content_hash"] == data.instance_content_hash
    assert len(snapshot["candidate_rows"]) == 3
    assert len(snapshot["active_column_payloads"]) == 1
    assert snapshot["p0_selected_candidate_ids"] == snapshot[
        "p0_ordered_candidate_ids"
    ][:1]
    assert snapshot["guidance_filter_count"] == 0

    instance_path = tmp_path / "instance.json"
    instance_path.write_text(
        json.dumps(raw_instance, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    replay_path = tmp_path / "lookahead.json"
    subprocess.run(
        [
            sys.executable,
            "scripts/replay_p0v2_gat_route_admission_lookahead.py",
            "--instance",
            str(instance_path),
            "--snapshot",
            str(snapshot_paths[0]),
            "--output",
            str(replay_path),
            "--max-swap-actions",
            "2",
        ],
        check=True,
    )
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    assert len(replay["measurements"]) == 3
    assert all(
        row["status"] == "RMP_OPTIMAL"
        for row in replay["measurements"]
    )
    assert replay["legal_universe_preserved"]
    assert replay["guidance_filter_count"] == 0
    assert not replay["legacy_four_coefficient_cost_used"]
    assert not replay["linear_training_authorized"]
