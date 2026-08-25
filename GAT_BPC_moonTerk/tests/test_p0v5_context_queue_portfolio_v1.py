from __future__ import annotations

from dataclasses import replace
import builtins
import hashlib
import json
from pathlib import Path

import pytest
import torch

from lunar_ice_bpc.exact.bpc.guidance.contracts import (
    validate_pricing_ordering_hints,
)
from lunar_ice_bpc.exact.bpc.pricing.backends.base import BackendPricingRequest
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.context_queue_portfolio_runtime import (
    PORTFOLIO_EVALUATION_ENV,
    PORTFOLIO_MANIFEST_ENV,
    PORTFOLIO_MANIFEST_SCHEMA_V1,
    PORTFOLIO_RUNTIME_POLICY_V1,
    QGR1_BUCKET_WIDTH,
    context_queue_portfolio_runtime_implementation_hash,
    prepare_context_queue_portfolio_request_from_environment,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_v1 import (
    PORTFOLIO_ACTION_UNIVERSE,
    PORTFOLIO_ARMS,
    PORTFOLIO_CHECKPOINT_SCHEMA_V1,
    PORTFOLIO_CONTEXT_FEATURES,
    PORTFOLIO_FEATURE_SCHEMA_V1,
    PORTFOLIO_INPUT_PARITY_CONTRACT_V1,
    PortfolioGATSelector,
    PortfolioLinearSelector,
    PortfolioMLPSelector,
    build_portfolio_features,
    fit_portfolio_feature_envelope,
    fit_portfolio_normalization,
    portfolio_parameter_count,
    portfolio_training_loss,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (
    assess_arm_scale_admission,
    assess_formal_full100,
    collapse_matched_matrix,
    measured_portfolio_oracle,
    rotate_blocked_arm_order,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
    QG2V3TinyGAT,
    fit_qg2_v3_normalization,
    qg2_v3_checkpoint_payload,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
    qg2_exact_action_policy_hash_from_request,
)
from lunar_ice_bpc.guidance.qgr1_supervision import (
    QGR1_ACTION_SURFACE_V1,
    QGR1_SUPERVISION_SCHEMA_V1,
)
from lunar_ice_bpc.guidance.qg2_admission_supervision_v3 import (
    QG2V3WeightedPair,
)


ROOT = Path(__file__).resolve().parents[1]


def _request(scale: int = 30) -> BackendPricingRequest:
    path = (
        ROOT / f"data/instances/lunar_ice_sp50_{scale:03d}"
        / "instance_001_logical_graph.json"
    )
    data = load_lunar_ice_data(json.loads(path.read_text(encoding="utf-8")))
    return BackendPricingRequest(
        data=data,
        true_duals=JourneyDuals(
            cover={
                task_id: float(index % 5)
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
        proof_tail_active_column_count=2,
        proof_tail_active_task_sets=(
            (data.task_ids[0],),
            (data.task_ids[1], data.task_ids[2]),
        ),
        proof_tail_active_column_signature_hashes=("0" * 64, "1" * 64),
        proof_tail_round_index=4,
        proof_tail_previous_queue_policy_id="Q0",
        proof_tail_previous_proof_wall_sec=13.5,
        proof_tail_previous_processed_labels=125_000,
        proof_tail_previous_dominance_candidate_checks=2_000_000,
        proof_tail_previous_dominance_wall_sec=4.25,
        proof_tail_previous_max_visited_bucket_size=31_000,
        proof_tail_dual_delta_l1=2.25,
        proof_tail_v5_midpoint_wall_sec=0.4,
        proof_tail_v5_midpoint_reason="midpoint_no_audited_negative",
    )


def _write_manifest(
    tmp_path: Path,
    request: BackendPricingRequest,
    *,
    selected_arm: str = "QD1",
) -> Path:
    features = build_portfolio_features(request)
    normalization = fit_portfolio_normalization([features])
    model = PortfolioLinearSelector(normalization)
    selected_index = PORTFOLIO_ARMS.index(selected_arm)
    with torch.no_grad():
        model.head.weight.zero_()
        model.head.bias.zero_()
        for index in range(len(PORTFOLIO_ARMS)):
            offset = 3 * index
            model.head.bias[offset:offset + 3] = torch.tensor(
                [-10.0, -10.0, 10.0]
            )
        offset = 3 * selected_index
        model.head.bias[offset:offset + 3] = torch.tensor(
            [10.0, 1.0, -10.0]
        )
    checkpoint = tmp_path / "portfolio_selector.pt"
    torch.save({
        "schema_version": PORTFOLIO_CHECKPOINT_SCHEMA_V1,
        "feature_schema_version": PORTFOLIO_FEATURE_SCHEMA_V1,
        "input_parity_contract": PORTFOLIO_INPUT_PARITY_CONTRACT_V1,
        "model_kind": "linear",
        "action_universe": list(PORTFOLIO_ACTION_UNIVERSE),
        "normalization": normalization,
        "state_dict": model.state_dict(),
        "activation_authority": False,
        "deployment_authorized": False,
    }, checkpoint)
    forced_veto = ["QGR1"] if selected_arm != "QGR1" else []
    arm_scale_mask = {
        "QGR1": [] if "QGR1" in forced_veto else [30, 50],
        "QD1": [30, 50],
        "QB1": [30, 50],
    }
    payload = {
        "schema_version": PORTFOLIO_MANIFEST_SCHEMA_V1,
        "runtime_policy_id": PORTFOLIO_RUNTIME_POLICY_V1,
        "runtime_implementation_hash": (
            context_queue_portfolio_runtime_implementation_hash()
        ),
        "action_universe": list(PORTFOLIO_ACTION_UNIVERSE),
        "fallback_action": "Q0",
        "allowed_scales": [30, 50],
        "arm_scale_mask": arm_scale_mask,
        "forced_veto_arms": forced_veto,
        "forced_veto_arms_by_scale": {"30": [], "50": []},
        "model_kind": "linear",
        "selector_checkpoint_path": str(checkpoint),
        "selector_checkpoint_sha256": hashlib.sha256(
            checkpoint.read_bytes()
        ).hexdigest(),
        "feature_schema_version": PORTFOLIO_FEATURE_SCHEMA_V1,
        "feature_envelope": fit_portfolio_feature_envelope([features]),
        "thresholds": {
            "minimum_benefit_probability": 0.8,
            "minimum_expected_gain": 0.01,
            "maximum_adverse_probability": 0.1,
            "risk_penalty": 0.5,
        },
        "allowed_exact_engine_hashes": [request.engine_hash],
        "allowed_exact_action_policy_hashes": [
            qg2_exact_action_policy_hash_from_request(request)
        ],
        "development_e2e_authorized": True,
        "deployment_authorized": False,
        "development_only": True,
        "production_switch_authorized": False,
        "torch_num_threads": 1,
    }
    manifest = tmp_path / "portfolio_manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return manifest


def _enable_qgr1(
    manifest: Path, request: BackendPricingRequest, *, zero: bool = False
) -> None:
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    base_features = build_portfolio_features(request)
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
        QG2Features,
        QG2_CONTEXT_FEATURES,
    )
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
        QG2_V3_INPUT_FEATURE_SCHEMA,
    )
    ranker_features = QG2Features(
        instance_content_hash=base_features.instance_content_hash,
        task_ids=base_features.task_ids,
        arc_candidate_ids=base_features.arc_candidate_ids,
        node_features=base_features.node_features,
        edge_index=base_features.edge_index,
        edge_features=base_features.edge_features,
        context_features=base_features.context_features[:len(QG2_CONTEXT_FEATURES)],
        schema_version=QG2_V3_INPUT_FEATURE_SCHEMA,
    )
    normalization = fit_qg2_v3_normalization([ranker_features])
    torch.manual_seed(61635)
    ranker = QG2V3TinyGAT(normalization, hidden_dim=32, heads=2)
    if zero:
        with torch.no_grad():
            for parameter in ranker.parameters():
                parameter.zero_()
    ranker_path = manifest.parent / "qgr1_ranker.pt"
    torch.save(qg2_v3_checkpoint_payload(
        ranker,
        normalization=normalization,
        metadata={
            "activation_authority": False,
            "supervision_schema_version": QGR1_SUPERVISION_SCHEMA_V1,
            "queue_action_surface": QGR1_ACTION_SURFACE_V1,
        },
    ), ranker_path)
    payload.update({
        "qgr1_ranker_checkpoint_path": str(ranker_path),
        "qgr1_ranker_checkpoint_sha256": hashlib.sha256(
            ranker_path.read_bytes()
        ).hexdigest(),
        "qgr1_guidance_bucket_width": QGR1_BUCKET_WIDTH,
        "qgr1_label_state_schema_version": "lunar_spprc.qg2_label_state.v1",
    })
    manifest.write_text(json.dumps(payload), encoding="utf-8")


def test_small_scale_bypasses_before_manifest_and_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request(20)
    monkeypatch.setenv(PORTFOLIO_MANIFEST_ENV, "/must/not/be/read.json")
    imported: list[str] = []
    original_import = builtins.__import__

    def spy(name, *args, **kwargs):
        imported.append(str(name))
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", spy)
    selected, telemetry = (
        prepare_context_queue_portfolio_request_from_environment(request)
    )
    assert selected is request
    assert telemetry["proof_tail_portfolio_decision_reason"] == (
        "scale_bypasses_selector"
    )
    assert not any(name == "torch" or name.startswith("torch.") for name in imported)
    assert not any("context_queue_portfolio_v1" in name for name in imported)


def test_portfolio_models_have_input_parity_and_are_below_50k() -> None:
    features = build_portfolio_features(_request())
    normalization = fit_portfolio_normalization([features])
    tensors = features.to_tensors()
    for model_class in (
        PortfolioGATSelector,
        PortfolioMLPSelector,
        PortfolioLinearSelector,
    ):
        model = model_class(normalization)
        output = model(**tensors)
        assert output["benefit_probability"].shape == (1, 3)
        assert output["conditional_positive_gain"].shape == (1, 3)
        assert output["adverse_probability"].shape == (1, 3)
        assert portfolio_parameter_count(model) < 50_000


def test_non_q0_previous_trajectory_is_missing_from_selector_features() -> None:
    request = replace(
        _request(),
        proof_tail_previous_queue_policy_id="QD1",
        proof_tail_previous_proof_wall_sec=99.0,
        proof_tail_previous_processed_labels=999,
        proof_tail_previous_dominance_candidate_checks=999,
        proof_tail_previous_dominance_wall_sec=99.0,
        proof_tail_previous_max_visited_bucket_size=999,
    )
    features = build_portfolio_features(request)
    values = dict(zip(
        PORTFOLIO_CONTEXT_FEATURES,
        features.context_features,
        strict=True,
    ))
    assert values["previous_proof_wall_present"] == 0.0
    assert values["previous_processed_labels_present"] == 0.0
    assert values["previous_dominance_candidate_checks_present"] == 0.0
    assert values["previous_dominance_wall_sec_present"] == 0.0
    assert values["previous_max_visited_bucket_size_present"] == 0.0


def test_selector_installs_exactly_one_simple_arm(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    manifest = _write_manifest(tmp_path, request, selected_arm="QD1")
    monkeypatch.setenv(PORTFOLIO_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(PORTFOLIO_EVALUATION_ENV, "1")
    selected, telemetry = (
        prepare_context_queue_portfolio_request_from_environment(request)
    )
    assert telemetry["proof_tail_portfolio_action"] == "QD1"
    assert selected.proof_queue_policy_id == "QD1"
    assert selected.guidance_mode == "off"
    assert selected.guidance_hints is None
    assert not selected.proof_tail_gat_enabled


def test_selector_installs_qgr1_only_after_ranker_contract_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    manifest = _write_manifest(tmp_path, request, selected_arm="QGR1")
    _enable_qgr1(manifest, request)
    monkeypatch.setenv(PORTFOLIO_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(PORTFOLIO_EVALUATION_ENV, "1")
    selected, telemetry = (
        prepare_context_queue_portfolio_request_from_environment(request)
    )
    accepted, audit = validate_pricing_ordering_hints(selected)
    assert telemetry["proof_tail_portfolio_action"] == "QGR1"
    assert selected.proof_queue_policy_id == "QGR1"
    assert selected.proof_queue_guidance_bucket_width == QGR1_BUCKET_WIDTH
    assert selected.proof_tail_queue_policy_id == "QGR1"
    assert accepted is not None and audit["guidance_accepted"]
    assert len(accepted.label_state_coefficients) == 15


def test_zero_qgr1_output_is_literal_q0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    manifest = _write_manifest(tmp_path, request, selected_arm="QGR1")
    _enable_qgr1(manifest, request, zero=True)
    monkeypatch.setenv(PORTFOLIO_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(PORTFOLIO_EVALUATION_ENV, "1")
    selected, telemetry = (
        prepare_context_queue_portfolio_request_from_environment(request)
    )
    assert selected is request
    assert telemetry["proof_tail_portfolio_action"] == "Q0"
    assert telemetry["proof_tail_portfolio_decision_reason"] == (
        "qgr1_ranker_zero_or_invalid_potential"
    )


def test_manifest_hash_drift_is_literal_q0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    manifest = _write_manifest(tmp_path, request)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["runtime_implementation_hash"] = "drift"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(PORTFOLIO_MANIFEST_ENV, str(manifest))
    monkeypatch.setenv(PORTFOLIO_EVALUATION_ENV, "1")
    selected, telemetry = (
        prepare_context_queue_portfolio_request_from_environment(request)
    )
    assert selected is request
    assert telemetry["proof_tail_portfolio_action"] == "Q0"
    assert telemetry["proof_tail_portfolio_decision_reason"] == (
        "portfolio_fail_closed:ValueError"
    )


def test_qgr1_supervision_keeps_only_actionable_equal_mass_families(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import lunar_ice_bpc.guidance.qgr1_supervision as supervision

    base = (
        QG2V3WeightedPair(1, 2, "admission_route_ancestor", 4.0, 0),
        QG2V3WeightedPair(3, 4, "existing_dominator", 2.0, None),
        QG2V3WeightedPair(5, 6, "incoming_dominator", 1.0, None),
        QG2V3WeightedPair(7, 8, "existing_dominator", 9.0, None),
    )
    monkeypatch.setattr(
        supervision,
        "build_qg2_v3_weighted_pairs",
        lambda *args, **kwargs: (base, {"source": "synthetic"}),
    )
    labels = {
        index: {
            "terminal": False,
            "visited_count": 4,
            "reduced_cost_bucket": 9,
        }
        for index in range(1, 9)
    }
    labels[8]["visited_count"] = 5
    replay = {
        "diversity_milestone_audit": {
            "selected_master_ready_native_solution_indices": [0]
        }
    }
    rows, metadata = supervision.build_qgr1_weighted_pairs(
        replay, labels, seed=61635, maximum=3
    )
    assert len(rows) == 3
    assert {row.family for row in rows} == {
        "admitted_ancestor", "existing_dominator", "incoming_dominator"
    }
    masses = metadata["pair_family_weight_mass"]
    assert all(value == pytest.approx(1.0 / 3.0) for value in masses.values())
    assert metadata["rejected_pair_counts"] == {
        "outside_qgr1_action_surface": 1
    }
    assert metadata["all_admitted_routes_represented"]


def test_fixed_training_loss_has_all_four_terms() -> None:
    features = build_portfolio_features(_request())
    normalization = fit_portfolio_normalization([features])
    output = PortfolioLinearSelector(normalization)(**features.to_tensors())
    values = portfolio_training_loss(
        output,
        benefit_target=torch.tensor([1.0, 0.0, 1.0]),
        positive_gain_target=torch.tensor([0.1, 0.0, 0.2]),
        adverse_target=torch.tensor([0.0, 1.0, 0.0]),
        determined_mask=torch.ones(3),
        positive_mask=torch.tensor([1.0, 0.0, 1.0]),
        pairwise_preferences=((-1, 1, 1.0), (2, -1, 1.0)),
    )
    assert set(values) == {
        "loss", "benefit_bce", "positive_gain_huber",
        "adverse_bce", "pairwise_rank",
    }
    expected = (
        values["benefit_bce"] + 0.5 * values["positive_gain_huber"]
        + values["adverse_bce"] + 0.25 * values["pairwise_rank"]
    )
    assert torch.allclose(values["loss"], expected)


def test_blocked_matrix_collapses_repeats_before_arm_admission() -> None:
    rows = []
    for context in range(12):
        instance = f"instance-{context % 6}"
        ratio = 0.94 if context < 2 else 1.0
        for arm, wall in (("Q0", 10.0), ("QD1", 10.0 * ratio)):
            for repeat in range(3):
                rows.append({
                    "context_id": f"context-{context}",
                    "instance_hash": instance,
                    "scale": 30,
                    "partition": "train",
                    "arm": arm,
                    "repeat": repeat,
                    "status": "COMPLETED",
                    "wall_sec": wall,
                    "milestone_reached": True,
                    "correctness_redlines": [],
                })
    outcomes = collapse_matched_matrix(rows, caps_by_scale={30: 300, 50: 600})
    assert len(outcomes) == 12
    decision = assess_arm_scale_admission(outcomes, arm="QD1", scale=30)
    assert decision["admitted"]
    schedule = rotate_blocked_arm_order("a" * 64)
    assert len(schedule) == 3
    assert all(set(block) == {"Q0", "QD1", "QB1"} for block in schedule)


def test_formal_gate_rejects_any_small_scale_model_call() -> None:
    rows = []
    for scale in (5, 10, 20, 30, 50):
        for index in range(20):
            for side in ("Q0", "candidate"):
                rows.append({
                    "scale": scale,
                    "instance_hash": f"{scale}-{index}",
                    "side": side,
                    "exact": True,
                    "wall_sec": 10.0 if side == "Q0" else 9.9,
                    "par2_wall_sec": 10.0 if side == "Q0" else 9.9,
                    "model_calls": int(scale == 10 and index == 0 and side == "candidate"),
                    "selector_calls": 0,
                    "ranker_calls": 0,
                    "correctness_redlines": [],
                })
    decision = assess_formal_full100(rows)
    assert not decision["passed"]
    assert "FORMAL_SMALL_SCALE_MODEL_CALL" in decision["violations"]
    assert not decision["production_switch_authorized"]


def test_portfolio_oracle_keeps_double_censored_context_as_q0() -> None:
    rows = []
    for arm in ("Q0", "QD1"):
        for repeat in range(3):
            rows.append({
                "context_id": "double-censored",
                "instance_hash": "instance-a",
                "scale": 30,
                "partition": "train",
                "arm": arm,
                "repeat": repeat,
                "status": "TIMEOUT",
                "wall_sec": 300.0,
                "milestone_reached": False,
                "correctness_redlines": [],
            })
    outcomes = collapse_matched_matrix(
        rows, caps_by_scale={30: 300, 50: 600}
    )
    decision = measured_portfolio_oracle(
        outcomes, admitted_arms_by_scale={30: ["QD1"], 50: []}
    )
    assert decision["scales"]["30"]["context_count"] == 1
    assert decision["scales"]["30"]["oracle_gm"] == pytest.approx(1.0)


def test_explicit_incomplete_correctness_audit_is_redline() -> None:
    rows = []
    for arm in ("Q0", "QD1"):
        for repeat in range(3):
            rows.append({
                "context_id": "audit-incomplete",
                "instance_hash": "instance-a",
                "scale": 30,
                "partition": "train",
                "arm": arm,
                "repeat": repeat,
                "status": "COMPLETED",
                "wall_sec": 10.0,
                "milestone_reached": True,
                "correctness_audit_complete": arm == "Q0",
                "correctness_redlines": [],
            })
    outcome = collapse_matched_matrix(
        rows, caps_by_scale={30: 300, 50: 600}
    )[0]
    assert "correctness_audit_incomplete" in outcome.correctness_redlines
