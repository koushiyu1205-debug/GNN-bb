from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import runpy
from types import SimpleNamespace

import pytest
import torch
import lunar_ice_bpc.exact.bpc.pricing.labeling_pricer as labeling_pricer

from lunar_ice_bpc.exact.bpc.guidance.contracts import (
    CanonicalSolveBindingV2,
    PricingOrderingHintsV2,
    QG2_LABEL_STATE_SCHEMA_V1,
    validate_pricing_ordering_hints,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.base import BackendPricingRequest
from lunar_ice_bpc.exact.core.branching import (
    BranchContext,
    PairBranchDecision,
    SAME_JOURNEY,
)
from lunar_ice_bpc.exact.core.cuts import CutContext, subset_row_cut
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
    QG2_CONTEXT_FEATURES,
    QG2Linear,
    QG2MLP,
    QG2TinyGAT,
    build_qg2_features,
    checkpoint_payload,
    normalize_qg2_potential_groups,
    qg2_training_loss,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
    QG2_EXACT_ACTION_POLICY_SCHEMA_V1,
    QG2_TRAJECTORY_FEATURE_SEMANTICS_V2,
    QG2_RUNTIME_POLICY_ID,
    prepare_qg2_request_from_environment,
    qg2_exact_action_policy_hash_from_request,
    qg2_exact_action_policy_hash_from_snapshot,
    qg2_runtime_implementation_hash,
    record_qg2_fallback_snapshot,
    _qg2_snapshot_storage_caps,
)
from lunar_ice_bpc.exact.bpc.solver.pricing_tail_solver import (
    _proof_tail_round_fields,
)
from lunar_ice_bpc.guidance.qg2_admission_supervision import (
    QG2_QUEUE_ACTION_SURFACE_V1,
    QG2_SUPERVISION_SCHEMA_V2,
    build_admission_aware_preference_pairs,
)
ROOT = Path(__file__).resolve().parents[1]
_wilson = runpy.run_path(
    str(ROOT / "scripts/calibrate_p0v5_qg2_models.py")
)["_wilson"]
_oracle_helpers = runpy.run_path(
    str(ROOT / "scripts/run_p0v5_qg2_bounded_oracle.py")
)
_aggregate_contexts = _oracle_helpers["_aggregate_contexts"]
_bounded_selection = _oracle_helpers["_bounded_selection"]
_complete_future_trace = _oracle_helpers["_complete_future_trace"]
_effective_wall = _oracle_helpers["_effective_wall"]
_oracle_gate = _oracle_helpers["_gate"]
_select_oracle_bucket = _oracle_helpers["_select_bucket"]
_queue_action_headroom = _oracle_helpers["_queue_action_headroom"]
_summarize_queue_action_headroom = _oracle_helpers[
    "_summarize_queue_action_headroom"
]
_oracle_identity = _oracle_helpers["_identity"]
_oracle_state_rows = _oracle_helpers["_state_rows"]
_oracle_stable_hash = _oracle_helpers["_stable_hash"]
_oracle_replay = _oracle_helpers["_replay"]
_oracle_preflight_coverage_passes = _oracle_helpers[
    "_preflight_coverage_passes"
]
_index_helpers = runpy.run_path(
    str(ROOT / "scripts/build_p0v5_qg2_fallback_snapshot_index.py")
)
_snapshot_exclusion = _index_helpers["_snapshot_exclusion"]
_expected_exact_action_policy_hashes_by_scale = _index_helpers[
    "_expected_exact_action_policy_hashes_by_scale"
]
_calibration_helpers = runpy.run_path(
    str(ROOT / "scripts/calibrate_p0v5_qg2_models.py")
)
_calibration_effective_wall = _calibration_helpers["_effective_wall"]
_activation_metrics = _calibration_helpers["_activation_metrics"]
_matched_calibration_milestone = _calibration_helpers[
    "_matched_milestone_outcome"
]
_calibration_manifest = _calibration_helpers["_manifest"]
_minimum_zero_harm_sample_size = _calibration_helpers[
    "_minimum_zero_harm_sample_size"
]
_replay_helpers = runpy.run_path(
    str(ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py")
)
_replay_guidance = _replay_helpers["_guidance"]
_diversity_milestone_audit = _replay_helpers[
    "_diversity_milestone_audit"
]
_qg2_replay_schema = _replay_helpers["OUTPUT_SCHEMA"]
_acceptance_helpers = runpy.run_path(
    str(ROOT / "scripts/analyze_p0v5_qg2_paired_acceptance.py")
)
_paired_acceptance_violations = _acceptance_helpers["_violations"]
_paired_qg2_telemetry = _acceptance_helpers["_qg2_telemetry"]
_v4_acceptance_helpers = runpy.run_path(
    str(ROOT / "scripts/analyze_p0v5_qg2_realmap_v4_acceptance.py")
)
_paired_v4_selector_telemetry = _v4_acceptance_helpers[
    "_v4_selector_telemetry"
]
_paired_v4_acceptance_violations = _v4_acceptance_helpers["_violations"]
_acceptance_zeroish = _acceptance_helpers["_zeroish"]
_positive_acceptance_helpers = runpy.run_path(
    str(ROOT / "scripts/analyze_p0v5_qg2_positive_net_acceptance.py")
)
_positive_net_acceptance_violations = _positive_acceptance_helpers[
    "_positive_net_violations"
]
_e2e_helpers = runpy.run_path(
    str(ROOT / "scripts/run_p0v5_qg2_e2e_after_calibration.py")
)
_e2e_environment = _e2e_helpers["_environment"]
_trainer_helpers = runpy.run_path(
    str(ROOT / "scripts/train_p0v5_qg2_model_comparison.py"),
    run_name="qg2_training_smoke_module",
)


def _data(scale: int):
    path = (
        ROOT
        / f"data/instances/lunar_ice_sp50_{scale:03d}"
        / "instance_001_logical_graph.json"
    )
    return load_lunar_ice_data(json.loads(path.read_text(encoding="utf-8")))


def _request(scale: int = 30) -> BackendPricingRequest:
    data = _data(scale)
    return BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(
            cover={
                task_id: float((index % 7) - 2)
                for index, task_id in enumerate(data.task_ids)
            },
            fleet_limit=0.25,
        ),
        mode="exact_proof",
        objective_mode="official",
        pricing_lifecycle_scope="root_cg",
        proof_queue_policy_id="Q0",
        instance_hash=data.instance_content_hash,
        config_hash="exact-config-hash",
        engine_hash="exact-engine-hash",
        proof_tail_fallback_context=True,
        proof_tail_active_column_count=87,
        proof_tail_active_task_sets=(
            (data.task_ids[0],),
            (data.task_ids[1], data.task_ids[2]),
        ),
        proof_tail_active_column_signature_hashes=tuple(
            f"{index:064x}" for index in range(87)
        ),
        proof_tail_round_index=4,
        proof_tail_previous_proof_wall_sec=13.5,
        proof_tail_previous_processed_labels=125_000,
        proof_tail_dual_delta_l1=2.25,
        proof_tail_v5_midpoint_wall_sec=0.4,
        proof_tail_v5_midpoint_reason="midpoint_no_audited_negative",
    )


def test_qg2_linear_mlp_gat_training_pipeline_smoke(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _data(5)
    features = build_qg2_features(
        data,
        cover_duals={task_id: 0.0 for task_id in data.task_ids},
        fleet_dual=0.0,
        active_column_count=1,
        active_task_sets=((data.task_ids[0],),),
        round_index=1,
        previous_proof_wall_sec=1.0,
        previous_processed_labels=1,
        dual_l1_delta_from_previous=0.0,
        branch_decisions=(),
        cut_duals={},
        v5_midpoint_wall_sec=0.1,
        root_lifecycle_scope=True,
    )
    examples = []
    for scale in (30, 50):
        for index in range(5):
            labels = {
                1: {
                    "node_id": 1,
                    "incoming_arc_index": 0,
                    "parent_label_id": 2**64 - 1,
                    "features": [1.0, *([0.0] * 14)],
                    "terminal": False,
                    "reduced_cost_bucket": 0,
                },
                2: {
                    "node_id": 1,
                    "incoming_arc_index": 0,
                    "parent_label_id": 2**64 - 1,
                    "features": [0.0] * 15,
                    "terminal": False,
                    "reduced_cost_bucket": 0,
                },
            }
            examples.append({
                "state_hash": f"state-{scale}-{index}",
                "instance_hash": f"instance-{scale}-{index}",
                "scale": scale,
                "features": features,
                "labels": labels,
                "pairs": ((1, 2),),
                "supervision": {},
                "outcome_determined": True,
                "saved_wall_sec": 1.0,
            })
    main = _trainer_helpers["main"]
    monkeypatch.setitem(main.__globals__, "_load_examples", lambda _oracle: examples)
    monkeypatch.setitem(
        main.__globals__,
        "MINIMUM_CALIBRATION_CONTEXTS_FOR_HARMFUL_GATE",
        1,
    )
    oracle = tmp_path / "oracle.json"
    oracle.write_text(json.dumps({
        "schema_version": _trainer_helpers["ORACLE_SCHEMA"],
        "oracle_gate": {"passed": True},
        "training_permitted": True,
    }), encoding="utf-8")
    output = tmp_path / "training"
    monkeypatch.setattr(
        "sys.argv",
        [
            str(ROOT / "scripts/train_p0v5_qg2_model_comparison.py"),
            "--oracle-summary", str(oracle),
            "--output-dir", str(output),
            "--epochs", "1",
            "--max-pairs-per-context", "1",
        ],
    )

    assert main() == 0
    report = json.loads(
        (output / "training_report.json").read_text(encoding="utf-8")
    )
    assert [row["model_kind"] for row in report["models"]] == [
        "linear", "mlp", "gat",
    ]
    assert report["loss"] == (
        "label_rank_plus_0.1_benefit_plus_0.1_positive_gain"
    )
    assert all(
        Path(row["checkpoint_path"]).is_file()
        for row in report["models"]
    )


def _features(request: BackendPricingRequest):
    return build_qg2_features(
        request.data,
        cover_duals=request.true_duals.cover,
        fleet_dual=request.true_duals.fleet_limit,
        active_column_count=request.proof_tail_active_column_count,
        active_task_sets=request.proof_tail_active_task_sets,
        round_index=request.proof_tail_round_index,
        previous_proof_wall_sec=request.proof_tail_previous_proof_wall_sec,
        previous_processed_labels=(
            request.proof_tail_previous_processed_labels
        ),
        dual_l1_delta_from_previous=request.proof_tail_dual_delta_l1,
        branch_decisions=tuple(request.branch_context.pair_decisions),
        cut_duals=dict(request.true_duals.cuts or {}),
        v5_midpoint_wall_sec=request.proof_tail_v5_midpoint_wall_sec,
        root_lifecycle_scope=(request.pricing_lifecycle_scope == "root_cg"),
    )


def _manifest(tmp_path: Path, request: BackendPricingRequest) -> Path:
    model = QG2TinyGAT()
    checkpoint = tmp_path / "qg2.pt"
    torch.save(
        checkpoint_payload(
            model,
            metadata={"training_data_hash": "qg2-training-hash"},
        ),
        checkpoint,
    )
    features = _features(request)
    context = list(features.context_features)
    payload = {
        "runtime_policy_id": QG2_RUNTIME_POLICY_ID,
        "runtime_implementation_hash": qg2_runtime_implementation_hash(),
        "feature_schema_version": features.schema_version,
        "label_state_schema_version": QG2_LABEL_STATE_SCHEMA_V1,
        "guidance_bucket_width": 0.001,
        "checkpoint_path": str(checkpoint),
        "checkpoint_sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        "training_data_hash": "qg2-training-hash",
        "allowed_scales": [30, 50],
        "allowed_exact_engine_hashes": [request.engine_hash],
        "allowed_exact_action_policy_hashes": [
            qg2_exact_action_policy_hash_from_request(request)
        ],
        "source_exact_config_hashes_observed_diagnostic_only": [
            request.config_hash
        ],
        "evaluation_authorized": True,
        "evaluation_force_qg2": True,
        "deployment_authorized": False,
        "torch_num_threads": 1,
        "oracle_gate": {
            "passed": True,
            "context_count": 100,
            "net_gain_5pct_context_count": 50,
            "max_instance_saved_wall_fraction": 0.30,
            "scale30": {
                "context_count": 50,
                "determined_context_count": 50,
                "positive_context_count": 25,
                "positive_instance_count": 5,
                "paired_geomean_ratio": 0.84,
                "bootstrap_95_upper": 0.89,
                "positive_fraction": 0.50,
            },
            "scale50": {
                "context_count": 50,
                "determined_context_count": 50,
                "positive_context_count": 25,
                "positive_instance_count": 5,
                "paired_geomean_ratio": 0.84,
                "bootstrap_95_upper": 0.89,
                "positive_fraction": 0.50,
            },
        },
        "feature_envelope": {
            "context_min": context,
            "context_max": context,
            "node_max_abs": max(
                abs(value)
                for row in features.node_features
                for value in row
            ),
            "edge_max_abs": max(
                abs(value)
                for row in features.edge_features
                for value in row
            ),
            "relative_margin": 0.01,
        },
        "calibration": {
            "gate_pass": True,
            "harmful_rate_95_upper": 0.05,
            "beneficial_precision_95_lower": 0.80,
            "heldout_tail_ratio": 0.90,
            "gat_vs_best_non_gat_ratio": 0.98,
            "probability_threshold": 0.0,
            "expected_gain_threshold": 0.0,
        },
    }
    path = tmp_path / "qg2_manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.mark.parametrize("model_class", [QG2Linear, QG2MLP, QG2TinyGAT])
def test_qg2_models_have_the_same_action_surface(model_class) -> None:
    features = _features(_request())
    output = model_class()(**features.to_tensors())
    assert output["node_scores"].shape == (len(features.task_ids) + 1,)
    assert output["arc_scores"].shape == (len(features.arc_candidate_ids),)
    assert output["label_state_coefficients"].shape == (15,)
    assert torch.isfinite(output["label_state_coefficients"]).all()
    assert 0.0 <= float(output["benefit_probability"].detach()) <= 1.0
    assert float(output["conditional_positive_gain"].detach()) >= 0.0


def test_qg2_global_normalization_preserves_cross_group_rank_score() -> None:
    node = torch.tensor([2.0, -1.0])
    arc = torch.tensor([4.0, -2.0, 1.0])
    state = torch.tensor([0.5, -0.25])
    normalized = normalize_qg2_potential_groups(node, arc, state)
    assert torch.equal(normalized[0], node / 4.0)
    assert torch.equal(normalized[1], arc / 4.0)
    assert torch.equal(normalized[2], state / 4.0)


def test_qg2_features_preserve_missingness_instead_of_zero_imputation() -> None:
    request = _request()
    features = build_qg2_features(
        request.data,
        cover_duals=request.true_duals.cover,
        fleet_dual=request.true_duals.fleet_limit,
        active_column_count=None,
        active_task_sets=None,
        round_index=None,
        previous_proof_wall_sec=None,
        previous_processed_labels=None,
        dual_l1_delta_from_previous=None,
        branch_decisions=tuple(),
        cut_duals={},
        v5_midpoint_wall_sec=None,
        root_lifecycle_scope=False,
    )
    context = features.context_features
    for feature_name in (
        "active_column_count_present",
        "active_task_sets_present",
        "round_present",
        "previous_proof_wall_present",
        "previous_processed_labels_present",
        "dual_l1_delta_present",
        "v5_midpoint_wall_present",
    ):
        assert context[QG2_CONTEXT_FEATURES.index(feature_name)] == 0.0


def test_qg2_fallback_snapshot_is_bounded_pre_action_and_hash_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "snapshots"
    monkeypatch.setenv(
        "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR", str(root)
    )
    request = _request()
    telemetry = record_qg2_fallback_snapshot(request)
    assert telemetry["proof_tail_qg2_snapshot_written"]
    path = Path(telemetry["proof_tail_qg2_snapshot_path"])
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == (
        "lunar_ice_bpc.p0v5_proof_tail_fallback_snapshot.v2"
    )
    assert payload["trajectory_feature_semantics_version"] == (
        QG2_TRAJECTORY_FEATURE_SEMANTICS_V2
    )
    assert payload["development_only"]
    assert not payload["deployable"]
    assert not payload["can_certify"]
    assert payload["exact_admission_batch_size"] == 16
    assert payload["exact_raw_negative_pool_size"] == 64
    assert not payload["exact_negative_escape_enabled"]
    assert payload["exact_negative_escape_policy_id"]
    assert len(payload["active_column_signature_hashes"]) == 87
    state_hash = payload.pop("state_hash")
    assert state_hash == hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()
    duplicate = record_qg2_fallback_snapshot(request)
    assert not duplicate["proof_tail_qg2_snapshot_written"]
    assert duplicate["proof_tail_qg2_snapshot_reason"] == "duplicate_state"

    scale20 = record_qg2_fallback_snapshot(_request(20))
    assert not scale20["proof_tail_qg2_snapshot_written"]
    assert scale20["proof_tail_qg2_snapshot_reason"] == "context_not_eligible"


def test_qg2_snapshot_physical_storage_cap_is_separate_and_hard_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "snapshots"
    monkeypatch.setenv(
        "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR", str(root)
    )
    for scale in (30, 50):
        for index in range(150):
            path = root / f"scale{scale}" / f"dummy-{index}" / "state.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n", encoding="utf-8")

    bounded = record_qg2_fallback_snapshot(_request(30))
    assert not bounded["proof_tail_qg2_snapshot_written"]
    assert bounded["proof_tail_qg2_snapshot_reason"] == (
        "global_300_context_cap"
    )
    assert bounded["proof_tail_qg2_snapshot_global_storage_cap"] == 300

    monkeypatch.setenv(
        "LUNAR_ICE_P0V5_QG2_SNAPSHOT_GLOBAL_STORAGE_CAP", "450"
    )
    monkeypatch.setenv(
        "LUNAR_ICE_P0V5_QG2_SNAPSHOT_PER_SCALE_STORAGE_CAP", "225"
    )
    expanded = record_qg2_fallback_snapshot(_request(30))
    assert expanded["proof_tail_qg2_snapshot_written"]
    assert expanded["proof_tail_qg2_snapshot_global_storage_count"] == 301
    assert expanded["proof_tail_qg2_snapshot_global_storage_cap"] == 450
    assert expanded["proof_tail_qg2_snapshot_scale_storage_count"] == 151
    assert expanded["proof_tail_qg2_snapshot_scale_storage_cap"] == 225

    monkeypatch.setenv(
        "LUNAR_ICE_P0V5_QG2_SNAPSHOT_GLOBAL_STORAGE_CAP", "999"
    )
    monkeypatch.setenv(
        "LUNAR_ICE_P0V5_QG2_SNAPSHOT_PER_SCALE_STORAGE_CAP", "999"
    )
    assert _qg2_snapshot_storage_caps() == (450, 225)


def test_qg2_formal_index_binds_composite_source_engine() -> None:
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_proof_tail_fallback_snapshot.v2",
        "development_only": True,
        "deployable": False,
        "can_certify": False,
        "mutates_p0": False,
        "proof_tail_fallback_context": True,
        "trajectory_feature_semantics_version": (
            QG2_TRAJECTORY_FEATURE_SEMANTICS_V2
        ),
        "engine_hash": "composite-engine",
        "active_task_sets": [],
        "active_column_signature_hashes": [],
        "active_column_count": 0,
        "scale": 30,
        "pricing_mode": "exact_proof",
        "objective_mode": "official",
    }
    assert _snapshot_exclusion(
        payload, expected_engine_hash="composite-engine"
    ) == ""
    assert _snapshot_exclusion(
        payload, expected_engine_hash="fallback-engine"
    ) == "engine_hash_mismatch"
    assert _snapshot_exclusion(
        payload,
        expected_engine_hash="composite-engine",
        require_exact_action_policy_hash=True,
    ) == "base_proof_queue_policy_not_explicit_q0"
    payload["base_proof_queue_policy_id"] = "Q0"
    assert _snapshot_exclusion(
        payload,
        expected_engine_hash="composite-engine",
        require_exact_action_policy_hash=True,
    ) == "exact_action_policy_hash_missing"
    payload["exact_action_policy_hash"] = "policy-hash"
    assert _snapshot_exclusion(
        payload,
        expected_engine_hash="composite-engine",
        require_exact_action_policy_hash=True,
        expected_exact_action_policy_hash="policy-hash",
    ) == ""
    assert _snapshot_exclusion(
        payload,
        expected_engine_hash="composite-engine",
        require_exact_action_policy_hash=True,
        expected_exact_action_policy_hash="other-policy-hash",
    ) == "exact_action_policy_hash_not_frozen_value"


def test_qg2_index_freezes_scale_specific_admission_policy_hashes() -> None:
    scale30 = "3" * 64
    scale50 = "5" * 64
    assert _expected_exact_action_policy_hashes_by_scale({
        "required_exact_action_policy_hashes_by_scale": {
            "30": scale30,
            "50": scale50,
        }
    }) == {30: scale30, 50: scale50}
    assert _expected_exact_action_policy_hashes_by_scale({
        "required_exact_action_policy_hash": scale30,
    }) == {30: scale30, 50: scale30}

    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_proof_tail_fallback_snapshot.v2"
        ),
        "development_only": True,
        "deployable": False,
        "can_certify": False,
        "mutates_p0": False,
        "proof_tail_fallback_context": True,
        "trajectory_feature_semantics_version": (
            QG2_TRAJECTORY_FEATURE_SEMANTICS_V2
        ),
        "engine_hash": "composite-engine",
        "active_task_sets": [],
        "active_column_signature_hashes": [],
        "active_column_count": 0,
        "scale": 50,
        "pricing_mode": "exact_proof",
        "objective_mode": "official",
        "base_proof_queue_policy_id": "Q0",
        "exact_action_policy_hash": scale50,
    }
    assert _snapshot_exclusion(
        payload,
        expected_engine_hash="composite-engine",
        require_exact_action_policy_hash=True,
        expected_exact_action_policy_hash=scale50,
    ) == ""
    assert _snapshot_exclusion(
        payload,
        expected_engine_hash="composite-engine",
        require_exact_action_policy_hash=True,
        expected_exact_action_policy_hash=scale30,
    ) == "exact_action_policy_hash_not_frozen_value"


def test_qg2_oracle_cache_binds_bucket_budget_and_potential(
    tmp_path: Path,
) -> None:
    row = {
        "state_hash": "state",
        "source_backend_id": "hybrid",
        "source_engine_hash": "engine",
        "source_config_hash": "config",
        "source_exact_action_policy_hash": "action",
        "instance_path": "unused",
        "snapshot_path": "unused",
    }
    potential = tmp_path / "potential.json"
    potential.write_text('{"potential_id":"p1"}\n', encoding="utf-8")
    target = tmp_path / "replay.json"
    target.write_text(json.dumps({
        "schema_version": _qg2_replay_schema,
        "source_state_hash": "state",
        "policy": "QG2",
        "repeat_index": 2,
        "source_backend_id": "hybrid",
        "source_engine_hash": "engine",
        "source_config_hash": "config",
        "source_exact_action_policy_hash": "action",
        "guidance_bucket_width": 3.0e-4,
        "requested_wall_time_limit_sec": 180.0,
        "requested_memory_limit_gb": 10.867,
        "requested_label_trace": False,
        "potential_file_sha256": hashlib.sha256(
            potential.read_bytes()
        ).hexdigest(),
        "random_seed": None,
        "proof_telemetry": {},
    }), encoding="utf-8")
    _oracle_replay(
        row=row,
        target=target,
        policy="QG2",
        wall_limit=180.0,
        memory_limit=10.867,
        env={},
        potential=potential,
        bucket=3.0e-4,
        repeat=2,
    )
    with pytest.raises(SystemExit, match="stale or mismatched"):
        _oracle_replay(
            row=row,
            target=target,
            policy="QG2",
            wall_limit=180.0,
            memory_limit=10.867,
            env={},
            potential=potential,
            bucket=1.0e-3,
            repeat=2,
        )
    potential.write_text('{"potential_id":"p2"}\n', encoding="utf-8")
    with pytest.raises(SystemExit, match="stale or mismatched"):
        _oracle_replay(
            row=row,
            target=target,
            policy="QG2",
            wall_limit=180.0,
            memory_limit=10.867,
            env={},
            potential=potential,
            bucket=3.0e-4,
            repeat=2,
        )


def test_qg2_paired_acceptance_recomputes_formal_gates() -> None:
    def metrics(scale: int) -> dict:
        exact = 15 if scale == 50 else 20
        return {
            "instance_count": 20,
            "control_exact_count": exact,
            "guided_exact_count": exact,
            "common_exact_count": exact,
            "paired_geomean_wall_ratio": (
                1.01 if scale in {5, 10, 20} else 0.95
            ),
            "objective_mismatch_count": 0,
            "control_redline_count": 0,
            "guided_redline_count": 0,
            "guided_qg2_inference_event_count": 0,
            "guided_qg2_action_count": 0,
        }

    by_scale = {str(scale): metrics(scale) for scale in (5, 10, 20, 30, 50)}
    pairs = [{
        "objective_match": True,
        "control": {"redlines_zero": True},
        "guided": {"redlines_zero": True},
    }]
    assert _paired_acceptance_violations(
        mode="formal", pairs=pairs, by_scale=by_scale
    ) == []
    by_scale["30"]["paired_geomean_wall_ratio"] = 0.951
    by_scale["10"]["guided_qg2_inference_event_count"] = 1
    violations = _paired_acceptance_violations(
        mode="formal", pairs=pairs, by_scale=by_scale
    )
    assert "scale30_speedup_below_5pct" in violations
    assert "scale10_qg2_inference_not_zero" in violations


def test_qg2_positive_net_development_replaces_only_five_percent_gate() -> None:
    by_scale = {
        "30": {
            "instance_count": 5,
            "control_exact_count": 5,
            "guided_exact_count": 5,
            "common_exact_count": 5,
            "paired_geomean_wall_ratio": 0.99,
            "guided_qg2_inference_event_count": 3,
            "guided_qg2_action_count": 2,
        },
        "50": {
            "instance_count": 5,
            "control_exact_count": 4,
            "guided_exact_count": 4,
            "common_exact_count": 4,
            "paired_geomean_wall_ratio": 1.01,
            "guided_qg2_inference_event_count": 2,
            "guided_qg2_action_count": 1,
        },
    }
    pairs = [
        {
            "scale": 30,
            "common_exact": True,
            "wall_ratio": 0.98,
            "objective_match": True,
            "control": {"redlines_zero": True},
            "guided": {"redlines_zero": True},
        },
        {
            "scale": 50,
            "common_exact": True,
            "wall_ratio": 1.01,
            "objective_match": True,
            "control": {"redlines_zero": True},
            "guided": {"redlines_zero": True},
        },
    ]

    assert _positive_net_acceptance_violations(
        mode="development", pairs=pairs, by_scale=by_scale
    ) == []

    pairs[0]["wall_ratio"] = 1.02
    violations = _positive_net_acceptance_violations(
        mode="development", pairs=pairs, by_scale=by_scale
    )
    assert "scale30_50_combined_positive_net_not_observed" in violations

    pairs[0]["wall_ratio"] = 0.98
    by_scale["30"]["guided_qg2_action_count"] = 0
    by_scale["50"]["guided_qg2_action_count"] = 0
    violations = _positive_net_acceptance_violations(
        mode="development", pairs=pairs, by_scale=by_scale
    )
    assert "qg2_action_not_observed" in violations


def test_qg2_paired_acceptance_detects_nested_inference_and_zeroish() -> None:
    telemetry = _paired_qg2_telemetry({
        "children": [
            {"proof_tail_gat_action": "Q0", "proof_tail_gat_inference_wall_ms": 0.0},
            {"proof_tail_gat_action": "QG2", "proof_tail_gat_inference_wall_ms": 1.25},
        ]
    })
    assert telemetry == {
        "inference_event_count": 1,
        "qg2_action_count": 1,
        "total_inference_wall_ms": 1.25,
    }
    assert all(_acceptance_zeroish(value) for value in (None, "", "0", "False"))
    assert not _acceptance_zeroish("1")


def test_qg2_v4_positive_net_gate_uses_selector_actions_and_p99() -> None:
    telemetry = _paired_v4_selector_telemetry({
        "children": [
            {
                "proof_tail_selector_action": "QG2",
                "proof_tail_selector_inference_wall_ms": 2.0,
                "proof_tail_selector_qg2_ranker_inference_wall_ms": 3.0,
            },
            {
                "proof_tail_selector_action": "QD1",
                "proof_tail_selector_inference_wall_ms": 1.0,
            },
        ]
    })
    assert telemetry["action_counts"] == {"QG2": 1, "QD1": 1}
    assert telemetry["non_q0_action_count"] == 2
    assert telemetry["inference_wall_ms_values"] == [5.0, 1.0]

    def metrics() -> dict:
        return {
            "instance_count": 4,
            "control_exact_count": 4,
            "guided_exact_count": 4,
            "common_exact_count": 4,
            "paired_geomean_wall_ratio": 0.99,
            "guided_selector_non_q0_action_count": 1,
            "guided_selector_inference_p99_ms": 5.0,
        }

    by_scale = {"30": metrics(), "50": metrics()}
    pairs = [{
        "objective_match": True,
        "control": {"redlines_zero": True},
        "guided": {"redlines_zero": True},
    }]
    assert _paired_v4_acceptance_violations(
        mode="development",
        pairs=pairs,
        by_scale=by_scale,
        gate_profile="v4_positive_net",
    ) == []
    by_scale["30"]["paired_geomean_wall_ratio"] = 1.0
    by_scale["50"]["guided_selector_inference_p99_ms"] = 10.01
    violations = _paired_v4_acceptance_violations(
        mode="development",
        pairs=pairs,
        by_scale=by_scale,
        gate_profile="v4_positive_net",
    )
    assert "scale30_not_net_positive" in violations
    assert "scale50_selector_inference_p99_above_10ms" in violations


def test_qg2_e2e_environment_separates_literal_q0_from_guided(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv(
        "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR", "/stale/snapshots"
    )
    monkeypatch.setenv("LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE", "15")
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", "/stale/model.json")
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", "1")

    control = _e2e_environment(manifest=None)
    for key in (
        "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR",
        "LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE",
        "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
        "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
    ):
        assert key not in control

    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}\n", encoding="utf-8")
    guided = _e2e_environment(manifest=manifest)
    assert guided["LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST"] == str(manifest)
    assert "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE" not in guided
    assert "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR" not in guided


def test_qg2_clean_v2_collection_strips_all_guidance_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    helpers = runpy.run_path(
        str(ROOT / "scripts/continue_p0v5_qg2_clean_v2_collection.py")
    )
    keys = helpers["GUIDANCE_ENV_KEYS"]
    for key in keys:
        monkeypatch.setenv(key, "stale-value")
    helpers["_sanitize_environment"]()
    assert all(key not in os.environ for key in keys)


def test_qg2_clean_v2_downstream_controllers_are_namespace_isolated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    for key in (
        "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
        "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
        "LUNAR_ICE_GAT_DEPLOYMENT_MANIFEST",
        "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR",
        "LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE",
    ):
        monkeypatch.setenv(key, "stale-clean-v1-value")

    tree = runpy.run_path(
        str(ROOT / "scripts/run_p0v5_qg2_clean_v2_tree_supplement.py")
    )
    tree["_bind_clean_v2_namespace"]()
    tree_controller = tree["controller"]
    assert "qg2_clean_v2" in str(tree_controller.PLAN)
    assert "qg2_clean_v2" in str(tree_controller.SNAPSHOT_DIR)
    tree_env = tree["_environment"]()
    assert tree_env["LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR"].endswith(
        "fallback_snapshots_qg2_clean_v2"
    )
    assert tree_env[
        "LUNAR_ICE_P0V5_QG2_SNAPSHOT_GLOBAL_STORAGE_CAP"
    ] == "450"
    assert tree_env[
        "LUNAR_ICE_P0V5_QG2_SNAPSHOT_PER_SCALE_STORAGE_CAP"
    ] == "225"
    assert "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST" not in tree_env

    oracle = runpy.run_path(
        str(ROOT / "scripts/run_p0v5_qg2_clean_v2_oracle_after_collection.py")
    )
    oracle["_bind_clean_v2_namespace"]()
    oracle_controller = oracle["controller"]
    assert "qg2_clean_v2" in str(oracle_controller.INDEX)
    assert oracle_controller.ORACLE_SUMMARY.name == (
        "oracle_qg2_clean_v2_storage_cap_v2_stage1.json"
    )
    assert oracle_controller.STATE.name == (
        "qg2_clean_v2_oracle_storage_cap_v2_controller_state.json"
    )
    oracle_env = oracle["_python_env"]()
    assert "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST" not in oracle_env
    assert "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR" not in oracle_env

    training = runpy.run_path(
        str(ROOT / "scripts/run_p0v5_qg2_clean_v2_training_after_oracle.py")
    )
    training["_bind_clean_v2_namespace"]()
    training_controller = training["controller"]
    assert training_controller.ORACLE_SUMMARY == oracle_controller.ORACLE_SUMMARY
    assert training_controller.ORACLE_STATE == oracle_controller.STATE
    assert training["FREEZE"].name == (
        "qg2_clean_v2_post_oracle_controller_freeze_storage_cap_v3.json"
    )
    assert "qg2_clean_v2" in str(training_controller.CALIBRATION_REPORT)
    training_env = training["_python_env"]()
    assert "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST" not in training_env
    assert "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR" not in training_env

    e2e = runpy.run_path(
        str(ROOT / "scripts/run_p0v5_qg2_clean_v2_e2e_after_calibration.py")
    )
    e2e["_bind_clean_v2_namespace"]()
    e2e_controller = e2e["controller"]
    assert "qg2_clean_v2" in str(e2e_controller.TRAINING_REPORT)
    assert "qg2_clean_v2" in str(e2e_controller.RESULT)
    assert e2e["FREEZE"].name == (
        "qg2_clean_v2_e2e_controller_freeze_storage_cap_v3.json"
    )

    formal = runpy.run_path(
        str(ROOT / "scripts/run_p0v5_qg2_clean_v2_formal_after_e2e.py")
    )
    assert formal["FREEZE"].name == (
        "qg2_clean_v2_formal_controller_freeze_storage_cap_v3.json"
    )

    finalizer = runpy.run_path(
        str(ROOT / "scripts/finalize_p0v5_qg2_clean_v2_candidate.py")
    )
    assert finalizer["COLLECTION_FREEZE"].name == (
        "qg2_clean_v2_collection_freeze_storage_cap_v4.json"
    )
    assert finalizer["ORACLE_FREEZE"].name == (
        "qg2_clean_v2_oracle_execution_freeze_storage_cap_v3.json"
    )
    assert finalizer["POST_ORACLE_FREEZE"] == training["FREEZE"]
    assert finalizer["E2E_FREEZE"] == e2e["FREEZE"]
    assert finalizer["FORMAL_FREEZE"] == formal["FREEZE"]


def test_qg2_clean_v2_formal_controller_uses_full20_and_safe_environments(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    formal = runpy.run_path(
        str(ROOT / "scripts/run_p0v5_qg2_clean_v2_formal_after_e2e.py")
    )
    command = formal["_acceptance_command"](output=tmp_path / "formal")
    assert command[command.index("--scales") + 1:command.index("--limit")] == [
        "5", "10", "20", "30", "50"
    ]
    assert command[command.index("--limit") + 1] == "20"
    assert "--no-resume" in command
    assert "--instance" not in command

    for key in formal["GUIDANCE_ENV_KEYS"]:
        monkeypatch.setenv(key, "stale-value")
    monkeypatch.setenv(
        "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR", "/stale/snapshots"
    )
    control = formal["_environment"](manifest=None)
    assert all(key not in control for key in formal["GUIDANCE_ENV_KEYS"])
    assert "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR" not in control

    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}\n", encoding="utf-8")
    guided = formal["_environment"](manifest=manifest)
    assert guided["LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST"] == str(manifest)
    assert "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE" not in guided


def test_qg2_candidate_finalizer_requires_exact_acceptance_universe_and_safe_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    finalizer = runpy.run_path(
        str(ROOT / "scripts/finalize_p0v5_qg2_clean_v2_candidate.py")
    )
    result = tmp_path / "acceptance.json"
    result.write_text("{}\n", encoding="utf-8")
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1",
        "mode": "formal",
        "passed": True,
        "violation_count": 0,
        "by_scale": {str(scale): {} for scale in (5, 10, 20, 30, 50)},
    }
    digest = hashlib.sha256(result.read_bytes()).hexdigest()
    assert finalizer["_valid_acceptance"](
        payload,
        mode="formal",
        scales={5, 10, 20, 30, 50},
        path=result,
        expected_sha256=digest,
    )
    payload["by_scale"].pop("50")
    assert not finalizer["_valid_acceptance"](
        payload,
        mode="formal",
        scales={5, 10, 20, 30, 50},
        path=result,
        expected_sha256=digest,
    )

    for key in finalizer["GUIDANCE_ENV_KEYS"]:
        monkeypatch.setenv(key, "stale-value")
    monkeypatch.setenv(
        "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR", "/stale/snapshots"
    )
    env = finalizer["_python_env"]()
    assert all(key not in env for key in finalizer["GUIDANCE_ENV_KEYS"])
    assert "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR" not in env


def test_qg2_oracle_identity_preserves_source_engine_and_config() -> None:
    identity = _oracle_identity({
        "scale": 30,
        "instance_id": "instance",
        "instance_hash": "instance-hash",
        "state_hash": "state-hash",
        "source_backend_id": "hybrid-v5",
        "source_engine_hash": "engine-hash",
        "source_config_hash": "config-hash",
        "source_exact_action_policy_hash": "policy-hash",
    })
    assert identity["source_backend_id"] == "hybrid-v5"
    assert identity["source_engine_hash"] == "engine-hash"
    assert identity["source_config_hash"] == "config-hash"
    assert identity["source_exact_action_policy_hash"] == "policy-hash"


def test_qg2_oracle_state_rows_preserve_all_source_bindings(
    tmp_path: Path,
) -> None:
    freeze = tmp_path / "freeze.json"
    frozen_action_hashes = {
        "30": "policy-hash",
        "50": "scale50-policy-hash",
    }
    freeze.write_text(json.dumps({
        "required_exact_action_policy_hashes_by_scale": (
            frozen_action_hashes
        ),
    }), encoding="utf-8")
    snapshot_payload = {
        "schema_version": "lunar_ice_bpc.p0v5_proof_tail_fallback_snapshot.v2",
        "proof_tail_fallback_context": True,
        "active_task_sets": [],
        "active_column_signature_hashes": [],
        "active_column_count": 0,
        "instance_content_hash": "instance-hash",
        "engine_hash": "engine-hash",
        "config_hash": "dynamic-config-hash",
        "base_proof_queue_policy_id": "Q0",
        "exact_action_policy_hash": "policy-hash",
    }
    state_hash = _oracle_stable_hash(snapshot_payload)
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(
        json.dumps({**snapshot_payload, "state_hash": state_hash}),
        encoding="utf-8",
    )
    scale50_payload = {
        **snapshot_payload,
        "instance_content_hash": "scale50-instance-hash",
        "config_hash": "scale50-dynamic-config-hash",
        "exact_action_policy_hash": "scale50-policy-hash",
    }
    scale50_state_hash = _oracle_stable_hash(scale50_payload)
    scale50_snapshot = tmp_path / "scale50_snapshot.json"
    scale50_snapshot.write_text(
        json.dumps({
            **scale50_payload,
            "state_hash": scale50_state_hash,
        }),
        encoding="utf-8",
    )
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_fallback_snapshot_index.v2",
        "development_only": True,
        "deployable": False,
        "excluded_count": 0,
        "exact_action_policy_hash_required": True,
        "expected_exact_action_policy_hashes_by_scale": (
            frozen_action_hashes
        ),
        "observed_exact_action_policy_hashes": sorted(
            frozen_action_hashes.values()
        ),
        "collection_freeze": str(freeze),
        "collection_freeze_sha256": hashlib.sha256(
            freeze.read_bytes()
        ).hexdigest(),
        "rows": [{
            "scale": 30,
            "instance_id": "instance",
            "instance_content_hash": "instance-hash",
            "instance_path": str(tmp_path / "instance.json"),
            "snapshot_path": str(snapshot),
            "snapshot_sha256": hashlib.sha256(
                snapshot.read_bytes()
            ).hexdigest(),
            "source_state_hash": state_hash,
            "source_backend_id": "hybrid-v5",
            "source_engine_hash": "engine-hash",
            "source_config_hash": "dynamic-config-hash",
            "source_exact_action_policy_hash": "policy-hash",
        }, {
            "scale": 50,
            "instance_id": "scale50-instance",
            "instance_content_hash": "scale50-instance-hash",
            "instance_path": str(tmp_path / "scale50_instance.json"),
            "snapshot_path": str(scale50_snapshot),
            "snapshot_sha256": hashlib.sha256(
                scale50_snapshot.read_bytes()
            ).hexdigest(),
            "source_state_hash": scale50_state_hash,
            "source_backend_id": "hybrid-v5",
            "source_engine_hash": "engine-hash",
            "source_config_hash": "scale50-dynamic-config-hash",
            "source_exact_action_policy_hash": "scale50-policy-hash",
        }],
    }
    rows = _oracle_state_rows(payload)
    assert len(rows) == 2
    assert rows[0]["source_backend_id"] == "hybrid-v5"
    assert rows[0]["source_engine_hash"] == "engine-hash"
    assert rows[0]["source_config_hash"] == "dynamic-config-hash"
    assert rows[0]["source_exact_action_policy_hash"] == "policy-hash"

    payload["rows"][0]["source_exact_action_policy_hash"] = "wrong"
    with pytest.raises(ValueError, match="binding mismatch"):
        _oracle_state_rows(payload)


def test_qg2_oracle_preflight_rejects_logically_impossible_total() -> None:
    coverage = {
        "30": {"context_count": 20, "instance_count": 10},
        "50": {"context_count": 20, "instance_count": 10},
    }
    assert not _oracle_preflight_coverage_passes(coverage)
    coverage["30"]["context_count"] = 25
    coverage["50"]["context_count"] = 25
    assert _oracle_preflight_coverage_passes(coverage)


def test_qg2_oracle_preflight_requires_frozen_partition_coverage() -> None:
    coverage = {
        str(scale): {
            "context_count": 25,
            "instance_count": 10,
            "partition_context_counts": {
                "train": 15, "calibration": 5, "heldout": 5,
            },
            "partition_instance_counts": {
                "train": 6, "calibration": 2, "heldout": 2,
            },
        }
        for scale in (30, 50)
    }
    assert _oracle_preflight_coverage_passes(
        coverage, require_partitions=True
    )
    coverage["50"]["partition_instance_counts"]["heldout"] = 1
    assert not _oracle_preflight_coverage_passes(
        coverage, require_partitions=True
    )


def test_qg2_exact_action_policy_hash_ignores_dynamic_request_state() -> None:
    request = _request()
    changed = replace(
        request,
        config_hash="different-dynamic-config-hash",
        rmp_iteration_id="different-round-id",
        proof_tail_round_index=99,
        proof_tail_active_column_count=1,
        proof_tail_active_task_sets=((request.data.task_ids[-1],),),
        proof_tail_active_column_signature_hashes=("f" * 64,),
        proof_tail_previous_proof_wall_sec=999.0,
        proof_tail_previous_processed_labels=999_999,
        proof_tail_dual_delta_l1=999.0,
    )
    assert (
        qg2_exact_action_policy_hash_from_request(changed)
        == qg2_exact_action_policy_hash_from_request(request)
    )


def test_qg2_exact_action_policy_hash_binds_admission_contract() -> None:
    request = _request()
    assert (
        qg2_exact_action_policy_hash_from_request(replace(
            request,
            exact_admission_batch_size=128,
            exact_raw_negative_pool_size=512,
        ))
        != qg2_exact_action_policy_hash_from_request(request)
    )
    snapshot = {
        "scale": 30,
        "pricing_mode": request.mode,
        "objective_mode": request.objective_mode,
        "exact_negative_escape_enabled": (
            request.exact_negative_escape_enabled
        ),
        "exact_admission_batch_size": request.exact_admission_batch_size,
        "exact_raw_negative_pool_size": request.exact_raw_negative_pool_size,
        "exact_negative_escape_policy_id": (
            request.exact_negative_escape_policy_id
        ),
        "base_proof_queue_policy_id": request.proof_queue_policy_id,
    }
    assert QG2_EXACT_ACTION_POLICY_SCHEMA_V1.endswith(".v1")
    assert (
        qg2_exact_action_policy_hash_from_snapshot(snapshot)
        == qg2_exact_action_policy_hash_from_request(request)
    )


def test_qg2_frozen_action_hashes_are_scale_specific() -> None:
    common = {
        "pricing_mode": "exact_proof",
        "objective_mode": "official",
        "exact_negative_escape_enabled": True,
        "exact_negative_escape_policy_id": (
            "diverse_raw_4x_then_p0v4_selector_v1"
        ),
        "base_proof_queue_policy_id": "Q0",
    }
    scale30 = {
        **common,
        "scale": 30,
        "exact_admission_batch_size": 64,
        "exact_raw_negative_pool_size": 256,
    }
    scale50 = {
        **common,
        "scale": 50,
        "exact_admission_batch_size": 128,
        "exact_raw_negative_pool_size": 512,
    }
    assert qg2_exact_action_policy_hash_from_snapshot(scale30) == (
        "9dcedb7b74c0a9c20a3a64484067b87300b9267e8bd450fcfff74d2a8c7406ca"
    )
    assert qg2_exact_action_policy_hash_from_snapshot(scale50) == (
        "b2f9eab6bd01d12a0f4319342550733ddb0510e559d5e6a6abc119765d2203e2"
    )


def test_qg2_manifest_uses_static_policy_not_dynamic_config_allowlist() -> None:
    manifest = _calibration_manifest(
        training={
            "training_data_hash": "training-hash",
            "feature_envelope": {},
        },
        oracle={
            "frozen_guidance_bucket_width": 0.001,
            "oracle_gate": {"passed": True},
        },
        gat={
            "checkpoint_path": "",
            "thresholds": {},
            "calibration": {},
            "heldout": {},
        },
        gate_pass=False,
        deployment_authorized=False,
        allowed_engines=["engine-hash"],
        allowed_action_policies=["policy-hash"],
        observed_configs=["dynamic-config-a", "dynamic-config-b"],
        gat_advantage_ratio=1.0,
    )
    assert manifest["allowed_exact_action_policy_hashes"] == [
        "policy-hash"
    ]
    assert "allowed_exact_config_hashes" not in manifest
    assert manifest[
        "source_exact_config_hashes_observed_diagnostic_only"
    ] == ["dynamic-config-a", "dynamic-config-b"]


def test_qg2_harmful_rate_gate_has_explicit_sample_feasibility() -> None:
    minimum = _minimum_zero_harm_sample_size(0.05)
    assert minimum == 52
    assert _wilson(0, minimum - 1)[1] > 0.05
    assert _wilson(0, minimum)[1] <= 0.05


def test_qg2_potential_is_bound_to_exact_source_policy(
    tmp_path: Path,
) -> None:
    data = _data(30)
    snapshot = {
        "state_hash": "state-hash",
        "engine_hash": "engine-hash",
        "config_hash": "dynamic-config-hash",
        "exact_action_policy_hash": "policy-hash",
    }
    _task, _arc, _state, payload = _replay_guidance(
        data=data,
        snapshot=snapshot,
        path=None,
        random_seed=61635,
    )
    assert payload["source_engine_hash"] == "engine-hash"
    assert payload["source_config_hash"] == "dynamic-config-hash"
    assert payload["source_exact_action_policy_hash"] == "policy-hash"
    payload["source_exact_action_policy_hash"] = "wrong-policy"
    path = tmp_path / "potential.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SystemExit, match="action_policy_hash mismatch"):
        _replay_guidance(
            data=data,
            snapshot=snapshot,
            path=path,
            random_seed=None,
        )


def test_qg2_previous_proof_missingness_is_not_encoded_as_zero() -> None:
    missing = _proof_tail_round_fields({
        "labeling_final_judge_proof_pass_attempted": False,
        "labeling_final_judge_proof_pass_wall_time": 0.0,
        "labeling_final_judge_proof_pass_processed_labels": 0,
    })
    assert missing["proof_tail_previous_proof_wall_sec"] is None
    assert missing["proof_tail_previous_processed_labels"] is None
    assert missing["proof_tail_previous_queue_policy_id"] == ""
    assert missing["proof_tail_previous_dominance_candidate_checks"] is None
    assert missing["proof_tail_previous_dominance_wall_sec"] is None
    assert missing["proof_tail_previous_max_visited_bucket_size"] is None

    observed = _proof_tail_round_fields({
        "labeling_final_judge_proof_pass_attempted": True,
        "labeling_final_judge_proof_pass_wall_time": 12.5,
        "labeling_final_judge_proof_pass_processed_labels": 1234,
    })
    assert observed == {
        "proof_tail_previous_queue_policy_id": "Q0",
        "proof_tail_previous_proof_wall_sec": 12.5,
        "proof_tail_previous_processed_labels": 1234,
        "proof_tail_previous_dominance_candidate_checks": None,
        "proof_tail_previous_dominance_wall_sec": None,
        "proof_tail_previous_max_visited_bucket_size": None,
    }


def test_qg2_loss_masks_censored_and_nonpositive_gain_rows() -> None:
    preferred = torch.tensor([1.0, 0.5, -0.5])
    other = torch.tensor([0.0, 0.0, 0.0])
    loss = qg2_training_loss(
        preferred_scores=preferred,
        other_scores=other,
        benefit_probability=torch.tensor([0.8, 0.2, 0.5]),
        benefit_target=torch.tensor([1.0, 0.0, 0.0]),
        conditional_positive_gain=torch.tensor([2.0, 3.0, 4.0]),
        positive_gain_target=torch.tensor([1.5, 0.0, 0.0]),
        outcome_mask=torch.tensor([True, True, False]),
        positive_mask=torch.tensor([True, False, False]),
    )
    assert torch.isfinite(loss)


def test_qg2_masked_activation_values_cannot_change_training_loss() -> None:
    common = {
        "preferred_scores": torch.tensor([1.0, 0.5, -0.5]),
        "other_scores": torch.tensor([0.0, 0.0, 0.0]),
        "benefit_target": torch.tensor([1.0, 0.0, 0.0]),
        "positive_gain_target": torch.tensor([1.5, 0.0, 0.0]),
        "outcome_mask": torch.tensor([True, True, False]),
        "positive_mask": torch.tensor([True, False, False]),
    }
    baseline = qg2_training_loss(
        **common,
        benefit_probability=torch.tensor([0.8, 0.2, 0.5]),
        conditional_positive_gain=torch.tensor([2.0, 3.0, 4.0]),
    )
    masked_values_changed = qg2_training_loss(
        **common,
        # Row 2 is censored for benefit; rows 1 and 2 are masked for gain.
        benefit_probability=torch.tensor([0.8, 0.2, 0.999999]),
        conditional_positive_gain=torch.tensor([2.0, 3.0e6, 4.0e6]),
    )

    torch.testing.assert_close(baseline, masked_values_changed)


def test_qg2_one_sided_risk_bound_is_attainable_with_bounded_oracle() -> None:
    assert _wilson(0, 60)[1] < 0.05
    assert _wilson(60, 60)[0] > 0.80


def test_qg2_oracle_keeps_nonbeneficial_initial_contexts() -> None:
    rows = _aggregate_contexts(
        [{
            "scale": 30,
            "instance_id": "instance",
            "instance_hash": "instance-hash",
            "state_hash": "state-hash",
            "compliant_context": True,
            "all_initial_arms_safe": True,
            "q0_wall_sec": 10.0,
            "q0_search_exhaustive": True,
            "q0_milestone_reached": True,
            "q0_milestone_kind": "EXACT_PROOF_COMPLETION",
            "qo2_wall_sec_by_bucket": {"0.001": 12.0},
            "qo2_search_exhaustive_by_bucket": {"0.001": True},
            "qo2_milestone_reached_by_bucket": {"0.001": True},
            "qo2_milestone_kind_by_bucket": {
                "0.001": "EXACT_PROOF_COMPLETION"
            },
        }],
        [],
        0.001,
    )
    assert len(rows) == 1
    assert rows[0]["ratio"] == pytest.approx(1.2)
    assert rows[0]["outcome_source"] == "single_initial_screen"
    assert rows[0]["outcome_determined"]


def test_qg2_oracle_aggregates_blocked_replicates_before_training(
    tmp_path: Path,
) -> None:
    replay = tmp_path / "replay.json"
    replay.write_text(
        json.dumps({"search_exhaustive": True}),
        encoding="utf-8",
    )
    initial = {
        "scale": 50,
        "instance_id": "instance",
        "instance_hash": "instance-hash",
        "state_hash": "state-hash",
        "compliant_context": True,
        "all_initial_arms_safe": True,
        "q0_wall_sec": 1.0,
        "q0_search_exhaustive": True,
        "q0_milestone_reached": True,
        "q0_milestone_kind": "ADMISSION_BATCH_READY",
        "qo2_wall_sec_by_bucket": {"0.001": 100.0},
        "qo2_search_exhaustive_by_bucket": {"0.001": True},
        "qo2_milestone_reached_by_bucket": {"0.001": True},
        "qo2_milestone_kind_by_bucket": {
            "0.001": "ADMISSION_BATCH_READY"
        },
    }
    replicates = [
        {
            "scale": 50,
            "instance_id": "instance",
            "instance_hash": "instance-hash",
            "state_hash": "state-hash",
            "q0_wall_sec": q0_wall,
            "qo2_wall_sec": qo2_wall,
            "q0_milestone_reached": True,
            "qo2_milestone_reached": True,
            "q0_milestone_kind": "ADMISSION_BATCH_READY",
            "qo2_milestone_kind": "ADMISSION_BATCH_READY",
            "q0_path": str(replay),
            "qo2_path": str(replay),
            "safe": True,
        }
        for q0_wall, qo2_wall in ((10.0, 8.0), (20.0, 18.0), (30.0, 40.0))
    ]

    rows = _aggregate_contexts([initial], replicates, 0.001)

    assert len(rows) == 1
    assert rows[0]["repeat_count"] == 3
    assert rows[0]["outcome_source"] == "three_blocked_replicates"
    assert rows[0]["q0_median_wall_sec"] == pytest.approx(20.0)
    assert rows[0]["qo2_median_wall_sec"] == pytest.approx(18.0)
    assert rows[0]["ratio"] == pytest.approx(0.9)
    assert rows[0]["saved_wall_sec"] == pytest.approx(2.0)
    assert rows[0]["outcome_determined"]


def test_qg2_oracle_does_not_compare_different_milestones() -> None:
    rows = _aggregate_contexts(
        [{
            "scale": 30,
            "instance_id": "instance",
            "instance_hash": "instance-hash",
            "state_hash": "state-hash",
            "compliant_context": True,
            "all_initial_arms_safe": True,
            "q0_wall_sec": 10.0,
            "q0_search_exhaustive": False,
            "q0_milestone_reached": True,
            "q0_milestone_kind": "ADMISSION_BATCH_READY",
            "qo2_wall_sec_by_bucket": {"0.001": 9.0},
            "qo2_search_exhaustive_by_bucket": {"0.001": True},
            "qo2_milestone_reached_by_bucket": {"0.001": True},
            "qo2_milestone_kind_by_bucket": {
                "0.001": "EXACT_PROOF_COMPLETION"
            },
        }],
        [],
        0.001,
    )
    assert len(rows) == 1
    assert not rows[0]["outcome_determined"]


def test_qg2_oracle_gate_masks_censored_and_mismatched_outcomes() -> None:
    rows = [{
        "scale": 30,
        "instance_hash": "a",
        "ratio": 0.01,
        "saved_wall_sec": 99.0,
        "all_safe": True,
        "outcome_determined": False,
    }]
    gate = _oracle_gate(rows, [], 0.001)
    assert gate["scale30"]["context_count"] == 1
    assert gate["scale30"]["determined_context_count"] == 0
    assert gate["scale30"]["positive_context_count"] == 0
    assert gate["scale30"]["paired_geomean_ratio"] == float("inf")
    assert gate["net_gain_5pct_context_count"] == 0
    assert not gate["passed"]


def test_qg2_bucket_freeze_uses_only_matched_completed_milestones() -> None:
    row = {
        "compliant_context": True,
        "all_initial_arms_safe": True,
        "q0_milestone_reached": True,
        "q0_milestone_kind": "ADMISSION_BATCH_READY",
        "bucket_ratios": {
            "0.0001": 0.01,
            "0.0003": 0.8,
            "0.001": 0.9,
        },
        "qo2_milestone_reached_by_bucket": {
            "0.0001": True,
            "0.0003": True,
            "0.001": True,
        },
        "qo2_milestone_kind_by_bucket": {
            "0.0001": "EXACT_PROOF_COMPLETION",
            "0.0003": "ADMISSION_BATCH_READY",
            "0.001": "ADMISSION_BATCH_READY",
        },
    }
    assert _select_oracle_bucket([row]) == pytest.approx(0.0003)


def test_qg2_realmap_bucket_is_selected_from_train_partition_only() -> None:
    def row(partition: str, ratios: tuple[float, float, float]) -> dict:
        return {
            "partition": partition,
            "compliant_context": True,
            "all_initial_arms_safe": True,
            "q0_milestone_reached": True,
            "q0_milestone_kind": "ADMISSION_BATCH_READY",
            "bucket_ratios": {
                "0.0001": ratios[0],
                "0.0003": ratios[1],
                "0.001": ratios[2],
            },
            "qo2_milestone_reached_by_bucket": {
                "0.0001": True, "0.0003": True, "0.001": True,
            },
            "qo2_milestone_kind_by_bucket": {
                "0.0001": "ADMISSION_BATCH_READY",
                "0.0003": "ADMISSION_BATCH_READY",
                "0.001": "ADMISSION_BATCH_READY",
            },
        }

    rows = [
        row("train", (0.9, 0.7, 0.8)),
        row("heldout", (0.1, 2.0, 2.0)),
    ]
    assert _select_oracle_bucket(
        rows, partition="train"
    ) == pytest.approx(0.0003)


def test_qg2_bounded_selection_round_robins_preaction_strata() -> None:
    rows = [
        {
            "scale": 30,
            "instance_hash": f"i{index}",
            "state_hash": f"s{index}",
            "pricing_lifecycle_scope": "root_cg",
            "branch_pair_count": index % 2,
            "active_cut_count": 0,
            "round": 5 if index < 2 else 35,
            "previous_q0_wall_stratum": "lt10",
        }
        for index in range(4)
    ]
    selected = _bounded_selection(rows, maximum=3, per_scale=3)
    assert len(selected) == 3
    assert len({row["instance_hash"] for row in selected}) == 3


def test_qg2_bounded_selection_round_robins_frozen_partitions() -> None:
    rows = []
    for partition, count in (("train", 12), ("calibration", 4), ("heldout", 4)):
        rows.extend({
            "scale": 30,
            "instance_hash": f"{partition}-{index}",
            "state_hash": f"{partition}-state-{index}",
            "partition": partition,
            "pricing_lifecycle_scope": "root_cg",
            "branch_pair_count": 0,
            "active_cut_count": 0,
            "round": 5,
            "previous_q0_wall_stratum": "lt10",
        } for index in range(count))
    selected = _bounded_selection(rows, maximum=12, per_scale=12)
    assert {row["partition"] for row in selected} == {
        "train", "calibration", "heldout"
    }


def test_qg2_bounded_selection_keeps_oracle_300_150_with_expanded_tree_pool(
) -> None:
    rows = []
    for scale in (30, 50):
        rows.extend({
            "scale": scale,
            "instance_hash": f"root-{scale}-{index}",
            "state_hash": f"root-state-{scale}-{index}",
            "pricing_lifecycle_scope": "root_cg",
            "branch_pair_count": 0,
            "active_cut_count": 0,
            "round": index,
            "previous_q0_wall_stratum": "10to60",
        } for index in range(150))
        rows.append({
            "scale": scale,
            "instance_hash": f"tree-{scale}",
            "state_hash": f"tree-state-{scale}",
            "pricing_lifecycle_scope": "tree_node",
            "branch_pair_count": 1,
            "active_cut_count": 4,
            "round": 1,
            "previous_q0_wall_stratum": "ge300",
        })

    selected = _bounded_selection(rows, maximum=300, per_scale=150)
    assert len(selected) == 300
    assert sum(row["scale"] == 30 for row in selected) == 150
    assert sum(row["scale"] == 50 for row in selected) == 150
    assert all(any(
        row["scale"] == scale
        and row["pricing_lifecycle_scope"] == "tree_node"
        for row in selected
    ) for scale in (30, 50))


def test_qg2_oracle_accepts_diverse_escape_as_complete_future_trace() -> None:
    row = {
        "milestone_reached": True,
        "milestone_kind": "ADMISSION_BATCH_READY",
        "search_exhaustive": False,
        "frontier_empty": False,
        "labels_dropped": False,
        "proof_telemetry": {
            "proof_queue_label_trace_enabled": True,
            "proof_queue_label_state_trace": [{"label_id": 1}],
        },
    }
    assert _complete_future_trace(row)
    assert _effective_wall({**row, "milestone_wall_sec": 4.0}, 180.0) == 4.0


def test_qg2_oracle_optimizes_admission_not_first_raw_negative() -> None:
    row = {
        "milestone_reached": True,
        "raw_negative_milestone_wall_sec": 2.0,
        "admission_milestone_wall_sec": 9.0,
        "milestone_wall_sec": 10.0,
    }
    assert _effective_wall(row, 180.0) == 9.0
    assert _calibration_effective_wall(row, 180.0) == 9.0


def test_qg2_diversity_milestones_use_selected_master_ready_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    columns = [object(), object(), object()]
    selected = [
        {
            "column": column,
            "signature": f"signature-{index}",
            "task_set": (f"task-{index}",),
            "true_reduced_cost": -float(index + 1),
            "task_set_harvest_bucket": "new_task_set",
        }
        for index, column in enumerate(columns)
    ]
    monkeypatch.setattr(
        labeling_pricer,
        "_audit_columns_with_true_dual",
        lambda *_args, **_kwargs: {
            "_selected_internal": tuple(selected),
            "_ordered_negative_internal": tuple(selected),
        },
    )
    monkeypatch.setitem(
        _diversity_milestone_audit.__globals__,
        "column_semantic_signature_hash",
        lambda signature: str(signature),
    )
    result = SimpleNamespace(
        columns=columns,
        telemetry={
            "proof_queue_label_trace_enabled": True,
            "reconstruction_audit": [
                {
                    "accepted": True,
                    "python_manual_rc": -float(index + 1),
                    "native_route_index": index,
                    "column_signature": f"signature-{index}",
                }
                for index in range(3)
            ],
            "proof_queue_negative_witness_trace": [
                {
                    "solution_index": 0,
                    "elapsed_seconds": 2.0,
                    "ancestor_label_ids": [10],
                },
                {
                    "solution_index": 1,
                    "elapsed_seconds": 7.5,
                    "ancestor_label_ids": [11],
                },
                {
                    "solution_index": 2,
                    "elapsed_seconds": 11.0,
                    "ancestor_label_ids": [12],
                },
            ],
            "proof_queue_label_state_trace": [
                {"label_id": label_id} for label_id in (10, 11, 12)
            ],
        },
    )
    request = SimpleNamespace(
        exact_negative_escape_enabled=True,
        true_duals=object(),
        branch_context=object(),
        cut_context=object(),
        proof_tail_active_task_sets=tuple(),
        proof_tail_active_column_signature_hashes=("signature-0",),
        negative_eps=1.0e-8,
    )

    audit = _diversity_milestone_audit(
        result=result,
        request=request,
        admission_target=2,
    )

    assert audit["selected_master_ready_native_solution_indices"] == [1, 2]
    assert audit["selected_master_rejected_native_solution_indices"] == [0]
    assert audit[
        "first_selected_master_ready_native_discovery_wall_sec"
    ] == pytest.approx(7.5)
    assert audit[
        "selected_master_ready_batch_native_discovery_wall_sec"
    ] == pytest.approx(11.0)
    assert audit["selected_witness_mapping_complete"]

    request.proof_tail_active_column_signature_hashes = None
    unavailable = _diversity_milestone_audit(
        result=result,
        request=request,
        admission_target=2,
    )
    assert not unavailable["selected_master_entry_audit_available"]
    assert unavailable["selected_master_ready_negative_count"] is None
    assert unavailable[
        "first_selected_master_ready_native_discovery_wall_sec"
    ] is None
    assert unavailable[
        "selected_master_ready_batch_native_discovery_wall_sec"
    ] is None


def test_qg2_queue_action_headroom_detects_fixed_pipeline_ceiling() -> None:
    headroom = _queue_action_headroom({
        "milestone_reached": True,
        "milestone_kind": "ADMISSION_BATCH_READY",
        "raw_negative_milestone_wall_sec": 1.0,
        "native_search_wall_sec": 2.0,
        "admission_milestone_wall_sec": 100.0,
    })
    assert headroom["available"]
    assert headroom["post_native_fixed_pipeline_share"] == pytest.approx(0.98)
    assert headroom["queue_zero_search_speedup_ceiling"] == pytest.approx(0.02)
    assert headroom["required_native_search_reduction_for_target"] == pytest.approx(2.5)
    assert not headroom["target_feasible_under_fixed_pipeline_assumption"]


def test_qg2_queue_action_headroom_separates_raw_from_admission_harvest() -> None:
    headroom = _queue_action_headroom({
        "milestone_reached": True,
        "milestone_kind": "ADMISSION_BATCH_READY",
        "raw_negative_milestone_wall_sec": 20.417728995,
        "native_search_wall_sec": 96.317390952,
        "admission_milestone_wall_sec": 97.925891246,
    })
    assert headroom["available"]
    assert headroom["raw_to_native_harvest_sec"] == pytest.approx(75.899661957)
    assert headroom["post_native_fixed_pipeline_sec"] == pytest.approx(1.608500294)
    assert headroom["post_native_fixed_pipeline_share"] == pytest.approx(
        0.016425695,
        rel=1.0e-6,
    )
    assert headroom["required_native_search_reduction_for_target"] == pytest.approx(
        0.050835,
        rel=1.0e-6,
    )
    assert headroom["target_feasible_under_fixed_pipeline_assumption"]


def test_qg2_queue_action_headroom_summary_is_admission_only() -> None:
    rows = [
        {
            "scale": 30,
            "instance_hash": "a",
            "q0_queue_action_headroom": _queue_action_headroom({
                "milestone_reached": True,
                "milestone_kind": "ADMISSION_BATCH_READY",
                "native_search_wall_sec": 90.0,
                "admission_milestone_wall_sec": 100.0,
            }),
        },
        {
            "scale": 30,
            "instance_hash": "b",
            "q0_queue_action_headroom": _queue_action_headroom({
                "milestone_reached": True,
                "milestone_kind": "EXACT_PROOF_COMPLETION",
                "native_search_wall_sec": 90.0,
                "admission_milestone_wall_sec": 100.0,
            }),
        },
    ]
    summary = _summarize_queue_action_headroom(rows)
    assert summary["available_admission_context_count"] == 1
    assert summary["unavailable_reasons"] == {"not_an_admission_milestone": 1}
    assert summary["scale30"]["admission_context_count"] == 1
    assert summary["scale30"]["median_post_native_fixed_pipeline_share"] == pytest.approx(0.1)


def test_qg2_calibration_requires_the_same_completed_milestone() -> None:
    admission = {
        "milestone_reached": True,
        "milestone_kind": "ADMISSION_BATCH_READY",
    }
    proof = {
        "milestone_reached": True,
        "milestone_kind": "EXACT_PROOF_COMPLETION",
    }
    assert _matched_calibration_milestone(admission, admission)
    assert not _matched_calibration_milestone(admission, proof)


def test_qg2_calibration_treats_ood_and_zero_potential_as_noop() -> None:
    rows = [
        {
            "action_eligible": False,
            "ood": True,
            "outcome_determined": False,
            "benefit_probability": 1.0,
            "expected_gain": 100.0,
            "ratio": 0.01,
            "beneficial": True,
            "harmful": False,
            "safe": True,
        },
        {
            "action_eligible": False,
            "ood": False,
            "outcome_determined": False,
            "benefit_probability": 1.0,
            "expected_gain": 100.0,
            "ratio": 0.01,
            "beneficial": True,
            "harmful": False,
            "safe": True,
        },
    ]
    metrics = _activation_metrics(rows, {
        "probability_threshold": 0.0,
        "expected_gain_threshold": 0.0,
    })
    assert metrics["activation_count"] == 0
    assert metrics["prethreshold_veto_context_count"] == 2
    assert metrics["ood_context_count"] == 1
    assert metrics["right_censored_context_count"] == 0
    assert metrics["net_geomean_ratio"] == pytest.approx(1.0)


def test_qg2_admission_supervision_uses_selected_master_ready_ancestors() -> None:
    labels = {
        1: {"reduced_cost_bucket": 0, "terminal": False},
        2: {"reduced_cost_bucket": 0, "terminal": True},
        3: {"reduced_cost_bucket": 0, "terminal": True},
        4: {"reduced_cost_bucket": 0, "terminal": False},
    }
    replay = {
        "milestone_kind": "ADMISSION_BATCH_READY",
        "diversity_milestone_audit": {
            "label_supervision_target_scope": "master_admission",
            "selected_route_mapping_complete": True,
            "selected_witness_mapping_complete": True,
            "admission_target": 1,
            "selected_master_ready_native_solution_indices": [10],
        },
        "proof_telemetry": {
            "proof_queue_label_preference_trace": [
                {
                    "preferred_label_id": 1,
                    "other_label_id": 4,
                    "kind": "existing_dominator",
                }
            ],
            "proof_queue_negative_witness_trace": [
                {"solution_index": 10, "ancestor_label_ids": [1, 2]},
                {"solution_index": 11, "ancestor_label_ids": [1, 3]},
            ]
        },
    }
    pairs, metadata = build_admission_aware_preference_pairs(
        replay, labels, seed=7
    )
    assert (2, 3, "admission_ancestor_vs_omitted_negative") in pairs
    assert not any(winner == 3 for winner, _loser, _kind in pairs)
    assert metadata["selected_master_ready_solution_count"] == 1
    assert metadata["omitted_raw_negative_solution_count"] == 1
    assert metadata["supervision_schema_version"] == (
        QG2_SUPERVISION_SCHEMA_V2
    )
    assert metadata["queue_action_surface"] == (
        QG2_QUEUE_ACTION_SURFACE_V1
    )
    assert metadata["action_reachable_pair_count"] == len(pairs)
    assert all(
        labels[winner]["terminal"] == labels[loser]["terminal"]
        and labels[winner]["reduced_cost_bucket"]
        == labels[loser]["reduced_cost_bucket"]
        for winner, loser, _kind in pairs
    )


def test_qg2_admission_pairs_are_not_crowded_out_by_dominance_budget() -> None:
    labels = {
        1: {"reduced_cost_bucket": 0, "terminal": False},
        2: {"reduced_cost_bucket": 0, "terminal": True},
        3: {"reduced_cost_bucket": 0, "terminal": True},
        4: {"reduced_cost_bucket": 0, "terminal": False},
    }
    replay = {
        "milestone_kind": "ADMISSION_BATCH_READY",
        "diversity_milestone_audit": {
            "label_supervision_target_scope": "master_admission",
            "selected_route_mapping_complete": True,
            "selected_witness_mapping_complete": True,
            "admission_target": 1,
            "selected_master_ready_native_solution_indices": [10],
        },
        "proof_telemetry": {
            "proof_queue_label_preference_trace": [
                {
                    "preferred_label_id": 4,
                    "other_label_id": 1,
                    "kind": "dominance",
                },
                {
                    "preferred_label_id": 1,
                    "other_label_id": 4,
                    "kind": "dominance",
                },
            ],
            "proof_queue_negative_witness_trace": [
                {"solution_index": 10, "ancestor_label_ids": [1, 2]},
                {"solution_index": 11, "ancestor_label_ids": [1, 3]},
            ],
        },
    }
    pairs, _metadata = build_admission_aware_preference_pairs(
        replay, labels, seed=7, maximum=1
    )
    assert len(pairs) == 1
    assert pairs[0][2] == "admission_ancestor_vs_omitted_negative"
    assert pairs[0][1] == 3


def test_qg2_admission_supervision_rejects_cross_terminal_pairs() -> None:
    labels = {
        1: {"reduced_cost_bucket": 0, "terminal": False},
        2: {"reduced_cost_bucket": 0, "terminal": True},
        3: {"reduced_cost_bucket": 0, "terminal": False},
        4: {"reduced_cost_bucket": 0, "terminal": True},
    }
    replay = {
        "milestone_kind": "ADMISSION_BATCH_READY",
        "diversity_milestone_audit": {
            "label_supervision_target_scope": "master_admission",
            "selected_route_mapping_complete": True,
            "selected_witness_mapping_complete": True,
            "admission_target": 1,
            "selected_master_ready_native_solution_indices": [10],
        },
        "proof_telemetry": {
            "proof_queue_label_preference_trace": [
                {
                    "preferred_label_id": 1,
                    "other_label_id": 4,
                    "kind": "existing_dominator",
                }
            ],
            "proof_queue_negative_witness_trace": [
                {"solution_index": 10, "ancestor_label_ids": [1, 2]},
                {"solution_index": 11, "ancestor_label_ids": [3, 4]},
            ],
        },
    }
    pairs, metadata = build_admission_aware_preference_pairs(
        replay, labels, seed=7
    )
    assert set(pairs) == {
        (1, 3, "admission_ancestor_vs_omitted_negative"),
        (2, 4, "admission_ancestor_vs_omitted_negative"),
    }
    assert metadata["rejected_pair_counts"][
        "different_terminal_class"
    ] == 1


def test_qg2_proof_supervision_uses_only_reachable_progress_pairs() -> None:
    labels = {
        1: {
            "reduced_cost_bucket": 0,
            "terminal": False,
            "parent_label_id": None,
        },
        2: {
            "reduced_cost_bucket": 0,
            "terminal": False,
            "parent_label_id": None,
        },
        3: {
            "reduced_cost_bucket": 0,
            "terminal": False,
            "parent_label_id": None,
        },
        4: {
            "reduced_cost_bucket": 0,
            "terminal": True,
            "parent_label_id": 1,
        },
        5: {
            "reduced_cost_bucket": 1,
            "terminal": False,
            "parent_label_id": None,
        },
    }
    replay = {
        "milestone_kind": "EXACT_PROOF_COMPLETION",
        "proof_telemetry": {
            "proof_queue_label_preference_trace": [
                {
                    "preferred_label_id": 1,
                    "other_label_id": 2,
                    "kind": "existing_dominator",
                },
                {
                    "preferred_label_id": 4,
                    "other_label_id": 3,
                    "kind": "incoming_dominator",
                },
                {
                    "preferred_label_id": 1,
                    "other_label_id": 5,
                    "kind": "existing_dominator",
                },
            ]
        },
    }
    pairs, metadata = build_admission_aware_preference_pairs(
        replay, labels, seed=7
    )
    assert (1, 2, "existing_dominator") in pairs
    assert any(
        winner == 1 and kind == "proof_terminal_parent_progress"
        for winner, _loser, kind in pairs
    )
    assert not any(kind == "proof_terminal_progress" for _, _, kind in pairs)
    assert all(
        labels[winner]["terminal"] == labels[loser]["terminal"]
        and labels[winner]["reduced_cost_bucket"]
        == labels[loser]["reduced_cost_bucket"]
        for winner, loser, _kind in pairs
    )
    assert metadata["proof_terminal_parent_count"] == 1
    assert metadata["action_reachable_pair_count"] == len(pairs)
    assert metadata["rejected_pair_counts"][
        "different_terminal_class"
    ] == 1
    assert metadata["rejected_pair_counts"][
        "different_reduced_cost_bucket"
    ] == 1


def test_qg2_admission_supervision_fails_closed_without_master_binding() -> None:
    replay = {
        "milestone_kind": "ADMISSION_BATCH_READY",
        "diversity_milestone_audit": {
            "label_supervision_target_scope": "selector_selected_only",
        },
        "proof_telemetry": {},
    }
    with pytest.raises(ValueError, match="Master-bound"):
        build_admission_aware_preference_pairs(
            replay,
            {1: {"reduced_cost_bucket": 0}},
            seed=7,
        )


def test_qg2_zero_addable_admission_batch_fails_closed() -> None:
    replay = {
        "milestone_kind": "ADMISSION_BATCH_READY",
        "diversity_milestone_audit": {
            "label_supervision_target_scope": "master_admission",
            "selected_route_mapping_complete": True,
            "selected_witness_mapping_complete": True,
            "admission_target": 1,
            "selected_master_ready_native_solution_indices": [],
        },
        "proof_telemetry": {},
    }
    with pytest.raises(ValueError, match="complete Master-ready batch"):
        build_admission_aware_preference_pairs(
            replay,
            {1: {"reduced_cost_bucket": 0}},
            seed=7,
        )


def test_qg2_oracle_right_censors_unreached_milestone() -> None:
    row = {
        "milestone_reached": False,
        "total_fresh_process_wall_sec": 12.0,
    }
    assert _effective_wall(row, 180.0) == 180.0


@pytest.mark.parametrize(
    "engine_status",
    ["TIMEOUT", "MEMORY_LIMIT", "FRONTIER_LIMIT"],
)
def test_qg2_incomplete_resource_outcomes_are_right_censored(
    engine_status: str,
) -> None:
    row = {
        "engine_status": engine_status,
        "milestone_reached": False,
        "search_exhaustive": False,
        "labels_dropped": False,
        "total_fresh_process_wall_sec": 12.0,
        "proof_telemetry": {
            "proof_queue_label_trace_enabled": True,
            "proof_queue_label_state_trace": [{"label_id": 1}],
        },
    }
    assert _effective_wall(row, 180.0) == 180.0
    assert not _complete_future_trace(row)


def test_qg2_runtime_installs_bound_label_state_guidance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", str(manifest))
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", "1")
    enriched, diagnostics = prepare_qg2_request_from_environment(request)
    accepted, audit = validate_pricing_ordering_hints(enriched)
    assert diagnostics["proof_tail_gat_action"] == "QG2"
    assert enriched.proof_queue_policy_id == "QG2"
    assert enriched.proof_queue_guidance_bucket_width == pytest.approx(0.001)
    assert enriched.config_hash != request.config_hash
    assert accepted is not None
    assert audit["guidance_accepted"]
    assert len(accepted.task_priorities) == 30
    assert len(accepted.arc_priorities) > 0
    assert len(accepted.label_state_coefficients) == 15
    assert accepted.label_state_schema_version == QG2_LABEL_STATE_SCHEMA_V1
    binding = CanonicalSolveBindingV2.from_backend_request(enriched)
    assert accepted.binding_hash == binding.binding_hash


def test_positive_net_manifest_authorizes_evaluation_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload.update({
        "evaluation_gate_policy": "positive_net_exact_safe.v1",
        "development_e2e_authorized": True,
        "evaluation_authorized": True,
        "deployment_authorized": False,
    })
    payload["calibration"] = {
        "gate_pass": False,
        "positive_net_gate_pass": True,
        "calibration_net_ratio": 0.99,
        "heldout_net_ratio": 0.98,
        "calibration_selected_right_censored_count": 0,
        "heldout_selected_right_censored_count": 0,
        "calibration_selected_unsafe_count": 0,
        "heldout_selected_unsafe_count": 0,
        "heldout_per_scale_net_ratio": {"30": 0.99, "50": 0.97},
        "probability_threshold": 0.0,
        "expected_gain_threshold": 0.0,
        # Strict statistical fields remain report-only and deliberately fail.
        "harmful_rate_95_upper": 0.25,
        "beneficial_precision_95_lower": 0.50,
        "heldout_tail_ratio": 0.98,
        "gat_vs_best_non_gat_ratio": 1.0,
    }
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", str(manifest))
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", "1")

    enriched, diagnostics = prepare_qg2_request_from_environment(request)

    assert diagnostics["proof_tail_gat_action"] == "QG2"
    assert diagnostics["proof_tail_gat_decision_reason"] == (
        "positive_net_evaluation_qg2"
    )
    assert enriched.proof_queue_policy_id == "QG2"

    monkeypatch.delenv("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE")
    unchanged, diagnostics = prepare_qg2_request_from_environment(request)
    assert unchanged is request
    assert diagnostics["proof_tail_gat_action"] == "Q0"
    assert diagnostics["proof_tail_gat_fallback_reason"] == (
        "deployment_not_authorized"
    )


def test_positive_net_manifest_keeps_censor_and_unsafe_as_hard_veto(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload.update({
        "evaluation_gate_policy": "positive_net_exact_safe.v1",
        "development_e2e_authorized": True,
        "evaluation_authorized": True,
        "deployment_authorized": False,
    })
    payload["calibration"].update({
        "gate_pass": False,
        "positive_net_gate_pass": True,
        "calibration_net_ratio": 0.99,
        "heldout_net_ratio": 0.98,
        "calibration_selected_right_censored_count": 1,
        "heldout_selected_right_censored_count": 0,
        "calibration_selected_unsafe_count": 0,
        "heldout_selected_unsafe_count": 0,
        "heldout_per_scale_net_ratio": {"30": 0.99, "50": 0.97},
        "probability_threshold": 0.0,
        "expected_gain_threshold": 0.0,
    })
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", str(manifest))
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", "1")

    with pytest.raises(ValueError, match="authority is incomplete"):
        prepare_qg2_request_from_environment(request)


def test_qg2_runtime_allows_new_dynamic_config_binding_for_same_exact_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    heldout_request = replace(
        request,
        config_hash="heldout-request-specific-config-hash",
        rmp_iteration_id="heldout-rmp-iteration",
    )
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", str(manifest))
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", "1")
    enriched, diagnostics = prepare_qg2_request_from_environment(
        heldout_request
    )
    assert diagnostics["proof_tail_gat_action"] == "QG2"
    assert diagnostics["proof_tail_gat_source_exact_config_hash"] == (
        heldout_request.config_hash
    )
    assert enriched.config_hash != heldout_request.config_hash


def test_qg2_runtime_vetoes_changed_exact_action_policy_before_model_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["checkpoint_path"] = "/does/not/exist.pt"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", str(manifest))
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", "1")
    changed = replace(
        request,
        exact_admission_batch_size=128,
        exact_raw_negative_pool_size=512,
    )
    unchanged, diagnostics = prepare_qg2_request_from_environment(changed)
    assert unchanged is changed
    assert diagnostics["proof_tail_gat_action"] == "Q0"
    assert diagnostics["proof_tail_gat_fallback_reason"] == (
        "exact_action_policy_hash_mismatch"
    )


def test_qg2_tree_branch_and_cut_context_are_bound_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = _request()
    tasks = base.data.task_ids
    cut_id = "qg2_sri_001"
    request = replace(
        base,
        true_duals=JourneyDuals(
            cover=base.true_duals.cover,
            fleet_limit=base.true_duals.fleet_limit,
            cuts={cut_id: 0.75},
        ),
        pricing_lifecycle_scope="tree_node",
        branch_context=BranchContext((
            PairBranchDecision(tasks[0], tasks[1], SAME_JOURNEY),
        )),
        cut_context=CutContext((
            subset_row_cut(cut_id, tasks[:3], divisor=2),
        )),
    )
    manifest = _manifest(tmp_path, request)
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", str(manifest))
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", "1")
    enriched, diagnostics = prepare_qg2_request_from_environment(request)
    accepted, audit = validate_pricing_ordering_hints(enriched)
    assert diagnostics["proof_tail_gat_action"] == "QG2"
    assert accepted is not None and audit["guidance_accepted"]
    binding = CanonicalSolveBindingV2.from_backend_request(enriched)
    assert binding.branch_context_hash != CanonicalSolveBindingV2.from_backend_request(
        base
    ).branch_context_hash
    assert binding.full_cut_context_hash != CanonicalSolveBindingV2.from_backend_request(
        base
    ).full_cut_context_hash
    assert accepted.binding_hash == binding.binding_hash


def test_qg2_runtime_rejects_unpassed_oracle_before_checkpoint_load(
    tmp_path: Path,
) -> None:
    request = _request()
    path = tmp_path / "rejected_manifest.json"
    path.write_text(
        json.dumps(
            {
                "runtime_policy_id": QG2_RUNTIME_POLICY_ID,
                "runtime_implementation_hash": qg2_runtime_implementation_hash(),
                "feature_schema_version": "lunar_ice_bpc.p0v5_qg2_features.v1",
                "label_state_schema_version": QG2_LABEL_STATE_SCHEMA_V1,
                "guidance_bucket_width": 0.001,
                "allowed_scales": [30, 50],
                "oracle_gate": {"passed": False},
                "checkpoint_path": "does-not-exist.pt",
            }
        ),
        encoding="utf-8",
    )
    rejected = replace(request, proof_tail_gat_manifest_path=str(path))
    with pytest.raises(ValueError, match="oracle gate"):
        prepare_qg2_request_from_environment(rejected)


def test_scale20_bypasses_qg2_before_manifest_or_model_load() -> None:
    request = replace(
        _request(20),
        proof_tail_gat_manifest_path="/does/not/exist.json",
    )
    unchanged, diagnostics = prepare_qg2_request_from_environment(request)
    assert unchanged is request
    assert diagnostics["proof_tail_gat_action"] == "Q0"
    assert diagnostics["proof_tail_gat_fallback_reason"] == "scale_bypasses_qg2"
    assert not diagnostics["proof_tail_gat_runtime_enabled"]


def test_qg2_calibration_veto_is_literal_q0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["calibration"]["probability_threshold"] = 1.1
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", str(manifest))
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", "1")
    unchanged, diagnostics = prepare_qg2_request_from_environment(request)
    assert unchanged is request
    assert diagnostics["proof_tail_gat_action"] == "Q0"
    assert diagnostics["proof_tail_gat_fallback_reason"] == "calibration_veto"


def test_qg2_ood_veto_happens_before_checkpoint_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["feature_envelope"]["context_min"] = [0.0] * len(
        payload["feature_envelope"]["context_min"]
    )
    payload["feature_envelope"]["context_max"] = [0.0] * len(
        payload["feature_envelope"]["context_max"]
    )
    payload["checkpoint_path"] = "/does/not/exist.pt"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", str(manifest))
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", "1")
    unchanged, diagnostics = prepare_qg2_request_from_environment(request)
    assert unchanged is request
    assert diagnostics["proof_tail_gat_action"] == "Q0"
    assert diagnostics["proof_tail_gat_ood"]
    assert diagnostics["proof_tail_gat_fallback_reason"].endswith(
        "outside_feature_envelope"
    )


def test_qg2_checkpoint_hash_drift_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["checkpoint_sha256"] = "bad-checkpoint-hash"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", str(manifest))
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", "1")
    with pytest.raises(ValueError, match="checkpoint hash"):
        prepare_qg2_request_from_environment(request)


@pytest.mark.parametrize("nonfinite", [False, True])
def test_qg2_zero_and_nonfinite_model_outputs_are_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    nonfinite: bool,
) -> None:
    request = _request()
    manifest = _manifest(tmp_path, request)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    checkpoint = Path(payload["checkpoint_path"])
    model = QG2TinyGAT()
    for parameter in model.parameters():
        parameter.data.fill_(float("nan") if nonfinite else 0.0)
    torch.save(
        checkpoint_payload(
            model,
            metadata={"training_data_hash": "qg2-training-hash"},
        ),
        checkpoint,
    )
    payload["checkpoint_sha256"] = hashlib.sha256(
        checkpoint.read_bytes()
    ).hexdigest()
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", str(manifest))
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", "1")
    enriched, diagnostics = prepare_qg2_request_from_environment(request)
    if nonfinite:
        assert enriched is request
        assert diagnostics["proof_tail_gat_action"] == "Q0"
        assert diagnostics["proof_tail_gat_fallback_reason"] == (
            "nonfinite_model_output"
        )
    else:
        assert enriched is request
        assert diagnostics["proof_tail_gat_action"] == "Q0"
        assert diagnostics["proof_tail_gat_fallback_reason"] == (
            "zero_potential"
        )


def test_label_state_hint_schema_and_finite_values_are_hard_validated() -> None:
    with pytest.raises(ValueError, match="exactly 15"):
        PricingOrderingHintsV2(
            binding_hash="binding",
            label_state_coefficients=(1.0,),
            label_state_schema_version=QG2_LABEL_STATE_SCHEMA_V1,
        )
    with pytest.raises(ValueError, match="finite"):
        PricingOrderingHintsV2(
            binding_hash="binding",
            label_state_coefficients=(0.0,) * 14 + (float("nan"),),
            label_state_schema_version=QG2_LABEL_STATE_SCHEMA_V1,
        )
