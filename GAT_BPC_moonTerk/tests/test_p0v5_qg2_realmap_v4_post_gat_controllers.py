from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _module(name: str, script: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONTROLS = _module(
    "qg2_v4_controls_test",
    "run_p0v5_qg2_realmap_v4_controls_after_gat.py",
)
E2E = _module(
    "qg2_v4_e2e_test",
    "run_p0v5_qg2_realmap_v4_development_e2e.py",
)
FORMAL = _module(
    "qg2_v4_formal_test",
    "run_p0v5_qg2_realmap_v4_formal_full20.py",
)
AUDIT = _module(
    "qg2_v4_completion_audit_test",
    "audit_p0v5_qg2_realmap_v4_completion.py",
)
AUTH = _module(
    "qg2_v4_training_authority_test",
    "authorize_p0v5_qg2_realmap_v4_training.py",
)
FINALIZER = _module(
    "qg2_v4_finalizer_test",
    "finalize_p0v5_qg2_realmap_v4_candidate.py",
)
COLLECTION = _module(
    "qg2_v4_collection_test",
    "continue_p0v5_qg2_realmap_v4_collection.py",
)
GAT_FIRST = _module(
    "qg2_v4_gat_first_test",
    "run_p0v5_qg2_realmap_v4_gat_first.py",
)
TREE_SUPPLEMENT = _module(
    "qg2_v4_tree_supplement_test",
    "continue_p0v5_qg2_realmap_v4_tree_supplement.py",
)
TREE_SUCCESSOR = _module(
    "qg2_v4_tree_successor_test",
    "watch_p0v5_qg2_realmap_v4_tree_then_gat.py",
)
STATUS_MAINTAINER = _module(
    "qg2_v4_status_maintainer_test",
    "maintain_p0v5_qg2_realmap_v4_status.py",
)
SELECTOR_ATTRIBUTION = _module(
    "qg2_v4_selector_attribution_test",
    "analyze_p0v5_qg2_v3_selector_attribution.py",
)
FRESH_EVALUATION = _module(
    "qg2_v4_fresh_evaluation_test",
    "evaluate_p0v5_qg2_v3_gat_selector_fresh.py",
)


def test_qg2_v4_oracle_schedule_is_exactly_frozen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    freeze = tmp_path / "oracle_execution_freeze.json"
    freeze.write_text(json.dumps({
        "scheduled_oracle_contexts": 120,
        "scheduled_oracle_contexts_per_scale": 60,
        "oracle_schedule_must_match_exactly": True,
    }), encoding="utf-8")
    monkeypatch.setattr(GAT_FIRST, "FREEZE", freeze)
    GAT_FIRST._validate_scheduled_oracle_budget(
        contexts=120, contexts_per_scale=60,
    )
    with pytest.raises(SystemExit, match="invocation budget drift"):
        GAT_FIRST._validate_scheduled_oracle_budget(
            contexts=300, contexts_per_scale=150,
        )


@pytest.mark.parametrize("status", [
    "ORACLE_PREFLIGHT_READY",
    "ORACLE_PREFLIGHT_READY_AFTER_TREE_SUPPLEMENT",
])
def test_qg2_v4_gat_first_accepts_both_preflight_paths(
    status: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    collection_state = tmp_path / "collection_state.json"
    collection_state.write_text(
        json.dumps({"status": status}), encoding="utf-8"
    )
    required = {
        "COLLECTION_STATE": collection_state,
        "INDEX": tmp_path / "index.json",
        "FREEZE": tmp_path / "freeze.json",
        "SPLIT": tmp_path / "split.json",
    }
    for name, path in required.items():
        if name != "COLLECTION_STATE":
            path.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(GAT_FIRST, name, path)
    GAT_FIRST._validate_collection()

    collection_state.write_text(
        json.dumps({"status": "COLLECTION_INCOMPLETE"}), encoding="utf-8"
    )
    with pytest.raises(SystemExit, match="has not reached Oracle preflight"):
        GAT_FIRST._validate_collection()


def test_qg2_v4_execution_freeze_covers_actual_v3_supervision_and_predictor() -> None:
    frozen = {
        path.relative_to(ROOT).as_posix()
        for path in COLLECTION.QG2_V4_LEARNING_SOURCES
    }
    assert {
        "src/lunar_ice_bpc/guidance/qg2_admission_supervision_v3.py",
        "scripts/predict_p0v5_qg2_v3_potential.py",
        "scripts/train_p0v5_qg2_v3_rankers.py",
        "scripts/train_p0v5_qg2_v3_gat_arm_selector.py",
        "src/lunar_ice_bpc/guidance/qg2_v3_selector_runtime.py",
    }.issubset(frozen)
    assert len(frozen) == len(COLLECTION.QG2_V4_LEARNING_SOURCES)


def test_qg2_v4_force_screen_one_positive_triggers_one_bounded_expansion() -> None:
    records = [
        {
            "partition": "train",
            "safe": True,
            "action_eligible": True,
            "comparison_class": "matched_milestone",
            "beneficial": index == 0,
        }
        for index in range(10)
    ]
    report = {"records": records}
    assert GAT_FIRST._qg2_train_screen_warrants_expansion(report)
    assert not GAT_FIRST._qg2_train_support(report)
    records[1]["beneficial"] = True
    assert GAT_FIRST._qg2_train_support(report)


def test_qg2_v4_force_screen_zero_positive_stops_without_expansion() -> None:
    report = {"records": [{
        "partition": "train",
        "safe": True,
        "action_eligible": True,
        "comparison_class": "matched_milestone",
        "beneficial": False,
    }]}
    assert not GAT_FIRST._qg2_train_screen_warrants_expansion(report)


def test_qg2_v4_selector_attribution_ablates_matrix_and_vector_features() -> None:
    torch = pytest.importorskip("torch")
    tensors = {
        "node_features": torch.tensor([[1.0, 2.0], [3.0, 4.0]]),
        "edge_features": torch.tensor([[5.0, 6.0]]),
        "context_features": torch.tensor([7.0, 8.0]),
    }
    node = SELECTOR_ATTRIBUTION._single_feature_to_mean("node", 1, -2.0)(
        tensors
    )
    assert node["node_features"].tolist() == [[1.0, -2.0], [3.0, -2.0]]
    assert tensors["node_features"].tolist() == [[1.0, 2.0], [3.0, 4.0]]
    context = SELECTOR_ATTRIBUTION._single_feature_to_mean(
        "context", 0, -3.0
    )(tensors)
    assert context["context_features"].tolist() == [-3.0, 8.0]
    assert tensors["context_features"].tolist() == [7.0, 8.0]


def test_qg2_v4_selector_attribution_reports_arm_rank_drop() -> None:
    baseline = {
        "mean_classification_accuracy": 0.8,
        "mean_context_arm_rank_accuracy": 0.75,
        "actions": ["QD1", "Q0"],
    }
    ablated = {
        "mean_classification_accuracy": 0.7,
        "mean_context_arm_rank_accuracy": 0.50,
        "net_geomean_ratio": 1.0,
        "activated_count": 1,
        "harmful_count": 0,
        "actions": ["Q0", "Q0"],
    }
    row = SELECTOR_ATTRIBUTION._ablation_row(
        "feature", ablated, baseline
    )
    assert row["arm_rank_accuracy_drop"] == pytest.approx(0.25)
    assert row["classification_accuracy_drop"] == pytest.approx(0.1)
    assert row["selected_action_disagreement_rate"] == pytest.approx(0.5)


def test_qg2_v4_status_curve_shows_context_arm_rank_accuracy(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "selector"
    directory.mkdir()
    (directory / "training_curve.jsonl").write_text(json.dumps({
        "model": "gat_arm_selector",
        "epoch": 2,
        "total_loss": 1.0,
        "rank_loss": 0.2,
        "benefit_loss": 0.3,
        "positive_gain_loss": 0.1,
        "adverse_loss": 0.4,
        "epoch_wall_sec": 0.5,
        "is_best_epoch": True,
    }) + "\n", encoding="utf-8")
    (directory / "training_report.json").write_text(json.dumps({
        "trained_model": "gat",
        "parameter_count": 123,
        "arm_rank_metrics": {
            partition: {"mean_context_pair_accuracy": value}
            for partition, value in (
                ("train", 0.8), ("calibration", 0.7), ("heldout", 0.6)
            )
        },
    }), encoding="utf-8")
    text = STATUS_MAINTAINER._curve(directory / "training_curve.jsonl")
    assert "arm-rank accuracy T/C/H 0.800000/0.700000/0.600000" in text
    assert "parameters 123" in text


def test_qg2_v4_status_reports_live_oracle_replay_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = tmp_path / "run"
    context = run / "oracle_realmap_v4/30_state"
    context.mkdir(parents=True)
    (run / "realmap_v4_oracle_execution_freeze.json").write_text(
        json.dumps({
            "scheduled_oracle_contexts": 120,
            "scheduled_oracle_contexts_per_scale": 60,
        }),
        encoding="utf-8",
    )
    (run / "realmap_v4_snapshot_index.json").write_text(
        json.dumps({
            "rows": [
                *({"scale": 30} for _ in range(65)),
                *({"scale": 50} for _ in range(29)),
            ],
        }),
        encoding="utf-8",
    )
    (context / "q0_initial.json").write_text(json.dumps({
        "policy": "Q0",
        "scale": 30,
        "instance_content_hash": "instance_a",
        "engine_status": "COMPLETE",
        "total_fresh_process_wall_sec": 12.5,
    }), encoding="utf-8")
    (context / "qb1_initial.json").write_text(json.dumps({
        "policy": "QB1",
        "scale": 30,
        "instance_content_hash": "instance_a",
        "engine_status": "TIMEOUT",
        "total_fresh_process_wall_sec": 300.0,
    }), encoding="utf-8")
    (context / "qd1_initial.json").write_text(json.dumps({
        "policy": "QD1",
        "scale": 30,
        "instance_content_hash": "instance_a",
        "engine_status": "COMPLETE",
        "total_fresh_process_wall_sec": 10.0,
    }), encoding="utf-8")
    (context / "qo2_leaked_potential.json").write_text(json.dumps({
        "policy": "QO2_LEAKED",
        "status": "COMPLETE",
        "wall_sec": 1.0,
    }), encoding="utf-8")
    (context / "q0_trace.json").write_text(json.dumps({
        "policy": "Q0",
        "scale": 30,
        "instance_content_hash": "instance_a",
        "engine_status": "COMPLETE",
        "total_fresh_process_wall_sec": 13.0,
        "proof_telemetry": {"proof_queue_label_state_trace": [
            {"label_id": value} for value in range(100)
        ]},
    }), encoding="utf-8")
    monkeypatch.setattr(STATUS_MAINTAINER, "RUN", run)
    text = STATUS_MAINTAINER._oracle_progress()
    assert (
        "contexts touched 1/89（s30 1/60@1 instances/"
        "s50 0/29@0 instances）"
    ) in text
    assert "replay outcomes 3" in text
    assert "trace contexts 1" in text
    assert "complete/timeout 2/1" in text
    assert "qb1_initial.json TIMEOUT 300.000000s" in text
    summary = STATUS_MAINTAINER._oracle_initial_arm_summary()
    assert "QD1 0.800000（n=1，censored=0）" in summary
    assert "QB1 24.000000（n=1，censored=1）" in summary
    assert "QO2-1e-4 n=0" in summary


def test_qg2_v4_status_reports_q0_milestone_and_queue_headroom(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = tmp_path / "run"
    oracle = run / "oracle_realmap_v4"
    for name, payload in (
        ("30_admission", {
            "scale": 30,
            "milestone_kind": "ADMISSION_BATCH_READY",
            "total_fresh_process_wall_sec": 10.0,
            "native_search_wall_sec": 8.0,
            "admission_audit_wall_sec": 1.0,
            "admission_selector_wall_sec": 0.5,
        }),
        ("30_proof", {
            "scale": 30,
            "milestone_kind": "EXACT_PROOF_COMPLETION",
            "total_fresh_process_wall_sec": 30.0,
            "native_search_wall_sec": 29.0,
            "admission_audit_wall_sec": 0.5,
            "admission_selector_wall_sec": 0.2,
        }),
    ):
        context = oracle / name
        context.mkdir(parents=True)
        (context / "q0_initial.json").write_text(
            json.dumps(payload), encoding="utf-8",
        )
    monkeypatch.setattr(STATUS_MAINTAINER, "RUN", run)
    summary = STATUS_MAINTAINER._oracle_q0_mechanism_summary()
    assert "s30 n=2 admission/proof/other 1/1/0" in summary
    assert "weighted Native-search 92.500%" in summary
    assert "audit+selector 5.500%" in summary
    assert "s50 n=0" in summary


def test_qg2_v4_status_distinguishes_running_and_stopped_processes() -> None:
    assert STATUS_MAINTAINER._process_state(os.getpid()) == "RUNNING"
    assert STATUS_MAINTAINER._process_state(2**31 - 1) == "STOPPED"


def test_qg2_v4_fresh_thresholds_preserve_calibration_without_override() -> None:
    frozen = {
        "minimum_benefit_probability": 0.6,
        "minimum_expected_gain": 0.0,
        "maximum_adverse_probability": 0.25,
        "risk_penalty": 1.0,
        "forced_veto_arms": ["QG2"],
    }
    unchanged = FRESH_EVALUATION._fresh_thresholds(frozen)
    assert unchanged == frozen
    assert unchanged is not frozen
    tightened = FRESH_EVALUATION._fresh_thresholds(
        frozen,
        minimum_expected_gain_floor=0.01,
        minimum_benefit_probability_floor=0.8,
        maximum_adverse_probability_ceiling=0.1,
    )
    assert tightened["minimum_expected_gain"] == pytest.approx(0.01)
    assert tightened["minimum_benefit_probability"] == pytest.approx(0.8)
    assert tightened["maximum_adverse_probability"] == pytest.approx(0.1)


def test_qg2_v4_resource_censor_is_safe_but_exhaustive_drop_is_redline() -> None:
    telemetry = {
        "legal_action_universe_hash_before_sort": "actions",
        "legal_arc_universe_hash_before_sort": "arcs",
        "guidance_filter_count": 0,
        "guidance_arc_drop_count": 0,
        "guidance_label_drop_count": 0,
        "guidance_branch_pair_drop_count": 0,
    }
    control = {
        "proof_telemetry": dict(telemetry),
        "search_exhaustive": False,
        "labels_dropped": False,
    }
    censored = {
        "proof_telemetry": dict(telemetry),
        "search_exhaustive": False,
        "labels_dropped": True,
    }
    assert FRESH_EVALUATION._safe(control, censored)
    claimed_exact = dict(censored, search_exhaustive=True)
    assert not FRESH_EVALUATION._safe(control, claimed_exact)
    assert FRESH_EVALUATION._safety_violations(
        control, claimed_exact
    ) == ("exhaustive_with_labels_dropped",)


def test_qg2_v4_guidance_filter_remains_hard_safety_redline() -> None:
    left = {
        "legal_action_universe_hash_before_sort": "actions",
        "legal_arc_universe_hash_before_sort": "arcs",
    }
    right = dict(left, guidance_label_drop_count=1)
    violations = FRESH_EVALUATION._safety_violations(
        {"proof_telemetry": left}, {"proof_telemetry": right}
    )
    assert "guidance_label_drop_count" in violations


def test_qg2_v4_gat_authority_precedes_controls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ranker_path = tmp_path / "ranker.json"
    selector_path = tmp_path / "selector.json"
    ranker_path.write_text("{}", encoding="utf-8")
    selector_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(CONTROLS, "GAT_RANKER", ranker_path)
    monkeypatch.setattr(CONTROLS, "GAT_SELECTOR", selector_path)
    ranker = {"models": [{"model_kind": "gat"}]}
    selector = {
        "trained_model": "gat",
        "ranker_training_report": str(ranker_path),
        "ranker_training_report_sha256": CONTROLS._sha256(ranker_path),
    }
    fresh = {
        "trained_model": "gat",
        "partition": "heldout",
        "selector_training_report_sha256": CONTROLS._sha256(selector_path),
        "summary": {"overall": {
            "all_safe": True,
            "activated_count": 2,
            "net_geomean_ratio": 0.99,
        }},
    }
    CONTROLS._validate_gat_authority(ranker, selector, fresh)
    fresh["summary"]["overall"]["net_geomean_ratio"] = 1.0
    with pytest.raises(SystemExit, match="gat_fresh_not_net_positive"):
        CONTROLS._validate_gat_authority(ranker, selector, fresh)


def test_qg2_v4_development_split_is_exactly_four_plus_four(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = []
    for scale in (30, 50):
        for index in range(4):
            path = tmp_path / f"scale{scale}_{index}.json"
            path.write_text("{}", encoding="utf-8")
            rows.append({
                "scale": scale,
                "partition": "heldout",
                "instance_content_hash": f"{scale}-{index}",
                "instance_path": str(path),
            })
    split = tmp_path / "split.json"
    split.write_text(json.dumps({"rows": rows}), encoding="utf-8")
    monkeypatch.setattr(E2E, "SPLIT", split)
    assert len(E2E._heldout_instances()) == 8
    rows.pop()
    split.write_text(json.dumps({"rows": rows}), encoding="utf-8")
    with pytest.raises(SystemExit, match=r"4\+4"):
        E2E._heldout_instances()


@pytest.mark.parametrize("module", [E2E, FORMAL])
def test_qg2_v4_paired_environment_uses_context_selector_manifest(
    module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", "/stale/legacy")
    monkeypatch.setenv(
        "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST", "/stale/selector"
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")

    control = module._environment(None)
    assert "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST" not in control
    assert "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST" not in control

    guided = module._environment(manifest)
    assert "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST" not in guided
    assert guided["LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST"] == str(manifest)
    assert guided["LUNAR_ICE_P0V5_QG2_V3_SELECTOR_EVALUATION_MODE"] == "1"


def test_qg2_v4_completion_audit_accepts_positive_net_not_only_five_percent() -> None:
    by_scale = {}
    for scale in (5, 10, 20, 30, 50):
        exact = 15 if scale == 50 else 20
        by_scale[str(scale)] = {
            "instance_count": 20,
            "control_exact_count": exact,
            "guided_exact_count": exact,
            "paired_geomean_wall_ratio": (
                1.0 if scale in {5, 10, 20} else 0.99
            ),
            "guided_selector_inference_event_count": (
                0 if scale in {5, 10, 20} else 5
            ),
            "guided_selector_inference_p99_ms": (
                None if scale in {5, 10, 20} else 4.0
            ),
        }
    assert AUDIT._formal_requirements({"by_scale": by_scale}) == []
    by_scale["30"]["paired_geomean_wall_ratio"] = 1.0
    assert "scale30_formal_requirement_failed" in (
        AUDIT._formal_requirements({"by_scale": by_scale})
    )


def test_qg2_v4_acceptance_isolated_from_legacy_frozen_analyzer() -> None:
    development = (ROOT / "scripts/run_p0v5_qg2_realmap_v4_development_e2e.py").read_text(
        encoding="utf-8"
    )
    formal = (ROOT / "scripts/run_p0v5_qg2_realmap_v4_formal_full20.py").read_text(
        encoding="utf-8"
    )
    v4_name = "analyze_p0v5_qg2_realmap_v4_acceptance.py"
    legacy_name = "analyze_p0v5_qg2_paired_acceptance.py"
    for source in (development, formal):
        assert f'str(ROOT / "scripts/{v4_name}"),' in source
        assert f'str(ROOT / "scripts/{legacy_name}"),' not in source
        assert f'ROOT / "scripts/{legacy_name}"' in source


def test_qg2_v4_fitting_gate_accepts_small_strict_positive_class_support() -> None:
    class Helper:
        SUPERVISION_SCHEMA = "supervision"
        ACTION_SURFACE = "surface"

        @staticmethod
        def _contract_errors(_oracle):
            return []

        @staticmethod
        def _geomean_or_none(values):
            return sum(values) / len(values)

        @staticmethod
        def _instance_bootstrap_upper(_rows):
            return 1.0

    rows = []
    for scale in (30, 50):
        for index in range(20):
            ratio = 0.99 if index < 3 else (1.06 if index < 5 else 1.0)
            rows.append({
                "scale": scale,
                "instance_hash": f"{scale}-{index % 10}",
                "outcome_determined": True,
                "all_safe": True,
                "ratio": ratio,
                "saved_wall_sec": 1.0 if ratio < 1.0 else 0.0,
            })
    oracle = {
        "context_rows": rows,
        "initial_rows": [{
            "compliant_context": True,
            "all_initial_arms_safe": True,
        }],
        "oracle_gate": {"passed": False},
    }
    result = AUTH._evaluate_v4_training_gate(oracle, helper=Helper)
    assert result["training_authorized"]
    assert result["gate"]["scale30"]["strict_positive_context_count"] == 3
    assert result["gate"]["scale50"]["strict_positive_instance_count"] == 3

    for row in rows:
        if int(row["scale"]) == 50 and float(row["ratio"]) < 1.0:
            row["ratio"] = 1.0
            row["saved_wall_sec"] = 0.0
    assert not AUTH._evaluate_v4_training_gate(
        oracle, helper=Helper
    )["training_authorized"]


def test_qg2_v4_final_freeze_reports_actual_trainable_action_surface() -> None:
    assert FINALIZER._validated_action_universe({
        "action_universe": ["Q0", "QD1", "QB1"],
    }) == ["Q0", "QD1", "QB1"]
    assert FINALIZER._validated_action_universe({
        "action_universe": ["Q0", "QG2", "QD1", "QB1"],
    }) == ["Q0", "QG2", "QD1", "QB1"]
    with pytest.raises(SystemExit, match="action universe"):
        FINALIZER._validated_action_universe({
            "action_universe": ["Q0", "QG2"],
        })


def test_qg2_v4_finalizer_rejects_post_audit_evidence_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence = tmp_path / "evidence.json"
    evidence.write_text('{"version": 1}', encoding="utf-8")
    monkeypatch.setattr(FINALIZER, "ROOT", tmp_path)
    audit = {"audited_evidence_sha256": {
        "evidence.json": FINALIZER._sha256(evidence),
    }}
    assert FINALIZER._audit_binding_errors(audit, (evidence,)) == []
    evidence.write_text('{"version": 2}', encoding="utf-8")
    assert FINALIZER._audit_binding_errors(audit, (evidence,)) == [
        "evidence.json"
    ]


@pytest.mark.parametrize("module", [E2E, FORMAL])
def test_qg2_v4_e2e_refuses_exact_execution_source_drift(
    module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "exact_source.py"
    source.write_text("version = 1\n", encoding="utf-8")
    freeze = tmp_path / "oracle_execution_freeze.json"
    freeze.write_text(json.dumps({
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_oracle_execution_freeze.v2"
        ),
        "frozen_file_sha256": {
            "exact_source.py": module._sha256(source),
        },
    }), encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "ORACLE_EXECUTION_FREEZE", freeze)
    module._validate_execution_freeze()
    source.write_text("version = 2\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="source drift"):
        module._validate_execution_freeze()


def test_qg2_v4_collection_freezes_full_exact_python_execution_surface() -> None:
    relative = {
        str(path.relative_to(ROOT))
        for path in COLLECTION.EXACT_EXECUTION_SOURCES
    }
    assert "scripts/run_lunar_ice_native_spprc_acceptance.py" in relative
    assert "scripts/run_lunar_ice_b4_2_cold_exact.py" in relative
    assert "scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py" in relative
    assert "src/lunar_ice_bpc/exact/bpc/pricing/backends/native_rcspp.py" in relative
    assert "src/lunar_ice_bpc/exact/bpc/solver/pricing_tail_solver.py" in relative
    assert all(path.is_file() for path in COLLECTION.EXACT_EXECUTION_SOURCES)


def test_qg2_v4_tree_supplement_uses_full_tree_and_literal_q0_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = tmp_path / "exact.yaml"
    config.write_text("model_id: exact\n", encoding="utf-8")
    snapshots = tmp_path / "snapshots"
    run_root = tmp_path / "run"
    instances = []
    for index in range(20):
        path = tmp_path / f"instance_{index:03d}.json"
        path.write_text("{}", encoding="utf-8")
        instances.append(path)
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(TREE_SUPPLEMENT.pilot, "CONFIG", config)
    monkeypatch.setattr(TREE_SUPPLEMENT.pilot, "RUN_ROOT", run_root)
    monkeypatch.setattr(TREE_SUPPLEMENT.pilot, "SNAPSHOT_DIR", snapshots)
    monkeypatch.setattr(
        TREE_SUPPLEMENT.pilot,
        "_environment",
        lambda: {"PYTHONPATH": "frozen"},
    )
    monkeypatch.setattr(TREE_SUPPLEMENT.subprocess, "run", fake_run)
    TREE_SUPPLEMENT._run_full_tree_acceptance(
        scale=30,
        instances=tuple(instances),
        snapshot_max_per_instance=15,
    )
    command, kwargs = calls[0]
    assert "--no-resume" in command
    assert "--route-opportunity-collection-only-root-pool" not in command
    assert command.count("--instance") == 20
    assert kwargs["env"][
        "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR"
    ] == str(snapshots)
    assert kwargs["env"][
        "LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE"
    ] == "15"
    assert "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST" not in kwargs["env"]


def test_qg2_v4_tree_supplement_selects_only_preoutcome_deficient_scales(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    index = tmp_path / "index.json"
    split = tmp_path / "split.json"

    def corpus(scale: int, layout: tuple[tuple[str, int, int], ...]):
        rows = []
        assignments = {}
        for partition, context_count, instance_count in layout:
            hashes = [
                f"s{scale}-{partition}-i{value}"
                for value in range(instance_count)
            ]
            assignments.update({value: partition for value in hashes})
            rows.extend({
                "scale": scale,
                "instance_hash": hashes[value % len(hashes)],
                "state_hash": f"s{scale}-{partition}-c{value}",
            } for value in range(context_count))
        return rows, assignments

    # scale30 mirrors the observed root-only structural shortfall. scale50
    # independently satisfies every per-scale and partition requirement.
    rows30, split30 = corpus(30, (
        ("train", 7, 7), ("calibration", 3, 3), ("heldout", 3, 2),
    ))
    rows50, split50 = corpus(50, (
        ("train", 10, 6), ("calibration", 4, 2), ("heldout", 6, 2),
    ))
    index.write_text(json.dumps({"rows": rows30 + rows50}), encoding="utf-8")
    split.write_text(json.dumps({
        "assignments": {**split30, **split50},
    }), encoding="utf-8")
    monkeypatch.setattr(TREE_SUPPLEMENT.pilot, "INDEX", index)
    monkeypatch.setattr(TREE_SUPPLEMENT.pilot, "SPLIT", split)

    selected, audit = TREE_SUPPLEMENT._select_supplement_scales()
    assert selected == (30,)
    assert audit["outcome_fields_used"] == []
    assert audit["scale_coverage"]["30"]["per_scale_preflight_ready"] is False
    assert audit["scale_coverage"]["50"]["per_scale_preflight_ready"] is True


def test_qg2_v4_tree_supplement_global_shortfall_uses_one_fixed_scale(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    index = tmp_path / "index.json"
    split = tmp_path / "split.json"
    rows = []
    assignments = {}
    for scale in (30, 50):
        layout = (("train", 10, 6), ("calibration", 4, 2), ("heldout", 6, 2))
        for partition, context_count, instance_count in layout:
            hashes = [
                f"s{scale}-{partition}-i{value}"
                for value in range(instance_count)
            ]
            assignments.update({value: partition for value in hashes})
            rows.extend({
                "scale": scale,
                "instance_hash": hashes[value % len(hashes)],
                "state_hash": f"s{scale}-{partition}-c{value}",
            } for value in range(context_count))
    index.write_text(json.dumps({"rows": rows}), encoding="utf-8")
    split.write_text(json.dumps({"assignments": assignments}), encoding="utf-8")
    monkeypatch.setattr(TREE_SUPPLEMENT.pilot, "INDEX", index)
    monkeypatch.setattr(TREE_SUPPLEMENT.pilot, "SPLIT", split)

    selected, audit = TREE_SUPPLEMENT._select_supplement_scales()
    assert selected == (30,)
    assert audit["total_context_count"] == 40
    assert audit["required_total_context_count"] == 50


def test_qg2_v4_tree_successor_only_triggers_for_coverage_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = tmp_path / "run"
    run.mkdir()
    (run / "realmap_v4_watch_controller_state.json").write_text(
        json.dumps({"status": "SNAPSHOT_COLLECTION_FAILED"}),
        encoding="utf-8",
    )
    (run / "realmap_v4_collection_state.json").write_text(
        json.dumps({"status": "RUNNING_COLLECTION"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(TREE_SUCCESSOR, "RUN", run)
    monkeypatch.setattr(TREE_SUCCESSOR, "STATE", run / "successor.json")
    monkeypatch.setattr(TREE_SUCCESSOR, "_alive", lambda _pid: False)
    monkeypatch.setattr(
        TREE_SUCCESSOR.sys,
        "argv",
        ["tree-successor", "--wait-for-pid", "123"],
    )
    monkeypatch.setattr(
        TREE_SUCCESSOR.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail(
            "supplement must not start for a non-coverage failure"
        ),
    )
    assert TREE_SUCCESSOR.main() == 2
    state = json.loads((run / "successor.json").read_text(encoding="utf-8"))
    assert state["status"] == "ROOT_PILOT_FAILED_FOR_NON_COVERAGE_REASON"


def test_qg2_v4_tree_successor_runs_supplement_before_gat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = tmp_path / "run"
    run.mkdir()
    (run / "realmap_v4_watch_controller_state.json").write_text(
        json.dumps({"status": "SNAPSHOT_COLLECTION_FAILED"}),
        encoding="utf-8",
    )
    (run / "realmap_v4_collection_state.json").write_text(
        json.dumps({"status": "COLLECTION_INCOMPLETE"}),
        encoding="utf-8",
    )
    calls = []

    def fake_run(command, **_kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(TREE_SUCCESSOR, "RUN", run)
    monkeypatch.setattr(TREE_SUCCESSOR, "STATE", run / "successor.json")
    monkeypatch.setattr(TREE_SUCCESSOR, "_alive", lambda _pid: False)
    monkeypatch.setattr(
        TREE_SUCCESSOR.sys,
        "argv",
        ["tree-successor", "--wait-for-pid", "123"],
    )
    monkeypatch.setattr(TREE_SUCCESSOR.subprocess, "run", fake_run)
    assert TREE_SUCCESSOR.main() == 0
    assert "continue_p0v5_qg2_realmap_v4_tree_supplement.py" in calls[0][1]
    assert "run_p0v5_qg2_realmap_v4_gat_first.py" in calls[1][1]


def test_qg2_v4_live_status_redline_summary_is_fail_closed() -> None:
    safe = {
        "no_cheat_pass": "True",
        "certificate_leak": "0",
        "manual_rc_fail": "0",
        "pricing_rc_fail": "0",
    }
    assert not STATUS_MAINTAINER._row_has_redline(safe)
    unsafe = dict(safe, certificate_leak="1")
    assert STATUS_MAINTAINER._row_has_redline(unsafe)
    malformed = dict(safe, pricing_rc_fail="not-a-number")
    assert STATUS_MAINTAINER._row_has_redline(malformed)
    no_cheat = dict(safe, no_cheat_pass="False")
    assert STATUS_MAINTAINER._row_has_redline(no_cheat)


def test_qg2_v4_live_status_reports_partition_preflight_deficits() -> None:
    progress = {
        "completed_instances": 8,
        "tree_completed_instances": 0,
        "pilot_root_certified_count": 3,
        "pilot_cap_reached_count": 5,
        "pilot_redline_count": 0,
        "tree_exact_count": 0,
        "tree_redline_count": 0,
        "context_count": 9,
        "instance_count": 6,
        "partition_contexts": {"train": 5, "calibration": 3, "heldout": 1},
        "partition_instances": {"train": 3, "calibration": 2, "heldout": 1},
        "overall_context_deficit": 11,
        "overall_instance_deficit": 4,
        "partition_context_deficits": {
            "train": 5, "calibration": 1, "heldout": 3,
        },
        "partition_instance_deficits": {
            "train": 3, "calibration": 0, "heldout": 1,
        },
    }
    text = STATUS_MAINTAINER._collection_progress_text(50, progress)
    assert "preflight deficit total ctx/inst 11/4" in text
    assert "T/C/H ctx 5/1/3" in text
    assert "inst 3/0/1" in text


def test_qg2_v4_live_status_reports_all_training_curve_components(
    tmp_path: Path,
) -> None:
    curve = tmp_path / "training_curve.jsonl"
    curve.write_text(json.dumps({
        "model": "gat_arm_selector",
        "epoch": 3,
        "total_loss": 1.2,
        "rank_loss": 0.0,
        "benefit_loss": 0.4,
        "positive_gain_loss": 0.3,
        "adverse_loss": 0.5,
        "epoch_wall_sec": 2.5,
        "is_best_epoch": True,
        "calibration_instance_balanced_total_loss": 1.1,
        "calibration_raw_context_total_loss": 1.3,
    }) + "\n", encoding="utf-8")
    text = STATUS_MAINTAINER._curve(curve)
    assert "total/rank/benefit/positive-gain/adverse" in text
    assert "1.200000/0.000000/0.400000/0.300000/0.500000" in text
    assert "epoch wall 2.500000s" in text
    assert "calibration loss instance/raw-context 1.100000/1.300000" in text


def test_qg2_v4_live_status_reports_completed_partition_pair_accuracy(
    tmp_path: Path,
) -> None:
    curve = tmp_path / "training_curve.jsonl"
    curve.write_text(json.dumps({
        "model": "gat",
        "epoch": 4,
        "total_loss": 0.5,
        "rank_loss": 0.5,
        "benefit_loss": 0.0,
        "positive_gain_loss": 0.0,
        "adverse_loss": 0.0,
        "epoch_wall_sec": 1.0,
        "is_best_epoch": True,
    }) + "\n", encoding="utf-8")
    (tmp_path / "training_report.json").write_text(json.dumps({
        "models": [{
            "model_kind": "gat",
            "partition_metrics": {
                "train": {"mean_context_pair_accuracy": 0.8},
                "calibration": {"mean_context_pair_accuracy": 0.7},
                "heldout": {"mean_context_pair_accuracy": 0.6},
            },
        }],
    }), encoding="utf-8")
    text = STATUS_MAINTAINER._curve(curve)
    assert "pair accuracy T/C/H 0.800000/0.700000/0.600000" in text


def test_qg2_v4_live_status_distinguishes_instance_and_context_accuracy(
    tmp_path: Path,
) -> None:
    curve = tmp_path / "training_curve.jsonl"
    curve.write_text(json.dumps({
        "model": "gat",
        "epoch": 1,
        "total_loss": 0.5,
        "rank_loss": 0.5,
        "benefit_loss": 0.0,
        "positive_gain_loss": 0.0,
        "adverse_loss": 0.0,
        "epoch_wall_sec": 1.0,
        "is_best_epoch": True,
    }) + "\n", encoding="utf-8")
    partitions = {
        name: {
            "mean_instance_pair_accuracy": instance,
            "raw_mean_context_pair_accuracy": raw,
        }
        for name, instance, raw in (
            ("train", 0.7, 0.9),
            ("calibration", 0.6, 0.8),
            ("heldout", 0.5, 0.7),
        )
    }
    (tmp_path / "training_report.json").write_text(json.dumps({
        "models": [{
            "model_kind": "gat",
            "partition_metrics": partitions,
        }],
    }), encoding="utf-8")
    text = STATUS_MAINTAINER._curve(curve)
    assert "pair accuracy instance T/C/H 0.700000/0.600000/0.500000" in text
    assert "raw-context T/C/H 0.900000/0.800000/0.700000" in text


def test_qg2_v4_live_status_reports_training_provenance_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(STATUS_MAINTAINER, "RUN", tmp_path)
    assert "等待完整 Oracle" in (
        STATUS_MAINTAINER._training_provenance_summary()
    )
    (tmp_path / "realmap_v4_training_gate.json").write_text(json.dumps({
        "training_authorized": True,
        "gate": {"passed": True},
    }), encoding="utf-8")
    (tmp_path / "oracle_realmap_v4_training_view.json").write_text(json.dumps({
        "training_permitted": True,
    }), encoding="utf-8")
    smoke = tmp_path / "instance_balanced_pretraining_smoke_v4"
    smoke.mkdir()
    (smoke / "smoke_report.json").write_text(json.dumps({
        "passed": True,
    }), encoding="utf-8")
    (tmp_path / "realmap_v4_instance_balanced_training_freeze.json").write_text(
        json.dumps({"schema_version": "freeze.v2"}), encoding="utf-8"
    )
    text = STATUS_MAINTAINER._training_provenance_summary()
    assert "gate True" in text
    assert "authorized view True" in text
    assert "1-epoch smoke True" in text
    assert "formal-training freeze freeze.v2" in text


def test_qg2_v4_live_status_reports_preoutcome_fitting_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(STATUS_MAINTAINER, "RUN", tmp_path)
    assert STATUS_MAINTAINER._fitting_gate_freeze_summary() == "缺失"
    (tmp_path / "realmap_v4_instance_balanced_fitting_gate_freeze.json").write_text(
        json.dumps({
            "fitting_gate_profile": "bounded.v2",
            "frozen_before_scale50_oracle_outcomes": True,
            "thresholds": {
                "minimum_determined_contexts_per_scale": 12,
                "minimum_determined_instances_per_scale": 6,
            },
        }),
        encoding="utf-8",
    )
    text = STATUS_MAINTAINER._fitting_gate_freeze_summary()
    assert "profile bounded.v2" in text
    assert "pre-scale50 True" in text
    assert "12/6" in text
