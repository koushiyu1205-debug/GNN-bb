#!/usr/bin/env python3
"""Audit the complete real-map V4 GAT-first evidence before candidate freeze."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
ACCEPTANCE_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_realmap_v4_paired_acceptance.v1"
)
FORMAL_STATE = RUN / "realmap_v4_formal_full20_state.json"
FORMAL_RESULT = RUN / "formal_full20_v4_acceptance.json"
E2E_RESULT = RUN / "development_e2e_v4_acceptance.json"
ORACLE_EXECUTION_FREEZE = RUN / "realmap_v4_oracle_execution_freeze.json"
E2E_FREEZE = RUN / "realmap_v4_development_e2e_freeze.json"
FORMAL_FREEZE = RUN / "realmap_v4_formal_full20_freeze.json"
MANIFEST = RUN / "p0v5_qg2_v4_gat_development_manifest.json"
COMPARISON = RUN / "gat_mlp_linear_comparison_v4.json"
LABEL_ATTRIBUTION = RUN / "ranker_gat_v4_attribution.json"
SELECTOR_ATTRIBUTION = RUN / "selector_gat_v4_attribution.json"
EVENTS = RUN / "realmap_v4_pipeline_events.jsonl"
OUTPUT = RUN / "realmap_v4_completion_audit.json"
NATIVE_TEST = (
    ROOT / "build/native-spprc-bidirectional-feasibility-v1/"
    "lunar_spprc_native_tests"
)

PYTHON_TESTS = (
    "tests/test_p0v5_qg2_realmap_v4_post_gat_controllers.py",
    "tests/test_p0v5_qg2_v3_rankers.py",
    "tests/test_p0v5_qg2_v3_selector_runtime.py",
    "tests/test_p0v5_bidirectional_gate_gat.py",
    "tests/test_p0v5_qg2_label_state_gat.py",
)
CURVES = (
    RUN / "ranker_gat_v4/training_curve.jsonl",
    RUN / "selector_gat_v4/training_curve.jsonl",
    RUN / "ranker_controls_v4/training_curve.jsonl",
    RUN / "selector_mlp_control_v4/training_curve.jsonl",
    RUN / "selector_linear_control_v4/training_curve.jsonl",
)
REPORTS = (
    RUN / "ranker_gat_v4/training_report.json",
    RUN / "ranker_controls_v4/training_report.json",
    RUN / "selector_gat_v4/training_report.json",
    RUN / "selector_mlp_control_v4/training_report.json",
    RUN / "selector_linear_control_v4/training_report.json",
)


def main() -> int:
    errors = []
    required = (
        FORMAL_STATE, FORMAL_RESULT, E2E_RESULT, MANIFEST, COMPARISON,
        ORACLE_EXECUTION_FREEZE, E2E_FREEZE, FORMAL_FREEZE,
        LABEL_ATTRIBUTION, SELECTOR_ATTRIBUTION, EVENTS, *CURVES, *REPORTS,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        errors.append("missing_artifacts:" + ",".join(missing))
    if errors:
        return _finish(errors, tests={})

    formal_state = _load(FORMAL_STATE)
    formal = _load(FORMAL_RESULT)
    e2e = _load(E2E_RESULT)
    manifest = _load(MANIFEST)
    comparison = _load(COMPARISON)
    action_universe = set(manifest.get("action_universe") or ())
    forced_veto = set(manifest.get("forced_veto_arms") or ())
    if not (
        str(formal_state.get("status") or "")
        == "FORMAL_FULL20_PASSED_CANDIDATE_MAY_FREEZE"
        and str(formal.get("schema_version") or "") == ACCEPTANCE_SCHEMA
        and bool(formal.get("passed"))
        and str(formal.get("mode") or "") == "formal"
        and str(formal.get("gate_profile") or "") == "v4_positive_net"
        and int(formal.get("violation_count") or 0) == 0
        and str(formal_state.get("result_sha256") or "")
        == _sha256(FORMAL_RESULT)
    ):
        errors.append("formal_full20_authority_invalid")
    if not (
        str(e2e.get("schema_version") or "") == ACCEPTANCE_SCHEMA
        and bool(e2e.get("passed"))
        and str(e2e.get("mode") or "") == "development"
        and str(e2e.get("gate_profile") or "") == "v4_positive_net"
    ):
        errors.append("development_e2e_authority_invalid")
    if not (
        bool(manifest.get("development_only"))
        and not bool(manifest.get("deployable"))
        and str(manifest.get("fallback_action") or "") == "Q0"
        and set(manifest.get("allowed_scales") or ()) == {30, 50}
        and action_universe in (
            {"Q0", "QD1", "QB1"},
            {"Q0", "QG2", "QD1", "QB1"},
        )
        and forced_veto == (set() if "QG2" in action_universe else {"QG2"})
        and not bool(manifest.get("production_switch_authorized"))
    ):
        errors.append("runtime_manifest_safety_invalid")
    if not (
        bool(comparison.get("all_controls_safe"))
        and not bool(comparison.get("deployment_authorized"))
        and list((comparison.get("comparison_contract") or {}).get(
            "execution_order", ()
        )) == ["gat", "mlp", "linear"]
    ):
        errors.append("model_comparison_invalid")

    errors.extend(_formal_requirements(formal))
    errors.extend(_execution_freeze_requirements())
    errors.extend(_curve_requirements())
    errors.extend(_report_requirements())
    errors.extend(_attribution_requirements())
    errors.extend(_event_order_requirements())
    source = (
        ROOT / "native/lunar_spprc/tests/test_native_pricer.cpp"
    ).read_text(encoding="utf-8")
    if not (
        "verify_qg2_500_randomized_exact_differentials" in source
        and "trial < 500U" in source
        and 'label_state_bytes") == "176"' in source
    ):
        errors.append("native_500_differential_or_state176_test_missing")

    tests = {
        "native": _test([str(NATIVE_TEST)], "native_completion_test.log"),
        "python": _test([
            sys.executable, "-m", "pytest", "-q", *PYTHON_TESTS,
        ], "python_completion_test.log", env={
            **os.environ,
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        }),
    }
    if tests["native"]["returncode"] != 0:
        errors.append("native_completion_tests_failed")
    if tests["python"]["returncode"] != 0:
        errors.append("python_completion_tests_failed")
    return _finish(errors, tests=tests)


def _formal_requirements(payload) -> list[str]:
    errors = []
    by_scale = dict(payload.get("by_scale") or {})
    if set(by_scale) != {"5", "10", "20", "30", "50"}:
        return ["formal_scale_universe_invalid"]
    for scale in (5, 10, 20):
        row = dict(by_scale[str(scale)])
        if not (
            int(row.get("instance_count") or 0) == 20
            and int(row.get("guided_exact_count") or 0) == 20
            and float(row.get("paired_geomean_wall_ratio") or 99.0) <= 1.01
            and int(row.get("guided_selector_inference_event_count") or 0) == 0
        ):
            errors.append(f"scale{scale}_formal_requirement_failed")
    row30 = dict(by_scale["30"])
    if not (
        int(row30.get("instance_count") or 0) == 20
        and int(row30.get("guided_exact_count") or 0) == 20
        and float(row30.get("paired_geomean_wall_ratio") or 99.0) < 1.0
    ):
        errors.append("scale30_formal_requirement_failed")
    row50 = dict(by_scale["50"])
    if not (
        int(row50.get("instance_count") or 0) == 20
        and int(row50.get("guided_exact_count") or 0)
        >= int(row50.get("control_exact_count") or 0)
        and int(row50.get("guided_exact_count") or 0) >= 15
        and float(row50.get("paired_geomean_wall_ratio") or 99.0) < 1.0
    ):
        errors.append("scale50_formal_requirement_failed")
    for scale in (30, 50):
        p99 = by_scale[str(scale)].get("guided_selector_inference_p99_ms")
        if p99 is None or float(p99) > 10.0:
            errors.append(f"scale{scale}_inference_p99_failed")
    return errors


def _curve_requirements() -> list[str]:
    required = {
        "model", "epoch", "total_loss", "rank_loss", "benefit_loss",
        "positive_gain_loss", "epoch_wall_sec",
    }
    errors = []
    for path in CURVES:
        rows = [json.loads(line) for line in path.read_text(
            encoding="utf-8"
        ).splitlines() if line.strip()]
        if not rows or any(not required.issubset(row) for row in rows):
            errors.append(f"training_curve_invalid:{path}")
    return errors


def _report_requirements() -> list[str]:
    observed = set()
    errors = []
    for path in REPORTS:
        report = _load(path)
        if "models" in report:
            for row in report.get("models") or ():
                observed.add(str(row.get("model_kind") or ""))
                if int(row.get("parameter_count") or 0) <= 0:
                    errors.append(f"ranker_parameter_count_invalid:{path}")
                if set((row.get("partition_metrics") or {})) != {
                    "train", "calibration", "heldout"
                }:
                    errors.append(f"ranker_partition_metrics_invalid:{path}")
        else:
            observed.add(str(report.get("trained_model") or ""))
            if int(report.get("parameter_count") or 0) <= 0:
                errors.append(f"selector_parameter_count_invalid:{path}")
            if set(report.get("classification_metrics") or {}) != {
                "train", "calibration", "heldout"
            }:
                errors.append(f"selector_partition_metrics_invalid:{path}")
            if set(report.get("arm_rank_metrics") or {}) != {
                "train", "calibration", "heldout"
            }:
                errors.append(f"selector_arm_rank_metrics_invalid:{path}")
    if observed != {"gat", "mlp", "linear"}:
        errors.append("three_model_coverage_invalid")
    return errors


def _event_order_requirements() -> list[str]:
    events = [
        json.loads(line) for line in EVENTS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    statuses = [str(row.get("status") or "") for row in events]
    expected = (
        "TRAINING_LABEL_GAT",
        "TRAINING_CONTEXT_GAT",
        "GAT_FRESH_POSITIVE_RUNNING_POST_GAT_CONTROLS",
        "GAT_AND_CONTROLS_COMPLETE_RUNNING_DEVELOPMENT_E2E",
        "DEVELOPMENT_E2E_PASSED_RUNNING_FORMAL_FULL20",
    )
    cursor = -1
    for status in expected:
        try:
            cursor = statuses.index(status, cursor + 1)
        except ValueError:
            return ["gat_first_event_order_invalid"]
    return []


def _attribution_requirements() -> list[str]:
    label = _load(LABEL_ATTRIBUTION)
    selector = _load(SELECTOR_ATTRIBUTION)
    label_groups = {
        str(row.get("ablation") or "")
        for row in label.get("group_ablations") or ()
    }
    selector_groups = {
        str(row.get("ablation") or "")
        for row in selector.get("group_ablations") or ()
    }
    errors = []
    required = {
        "node_to_train_mean", "edge_to_train_mean", "context_to_train_mean",
        "no_message_passing", "shuffled_message_topology",
    }
    if (
        list(label.get("partitions") or ()) != ["calibration"]
        or not required.issubset(label_groups)
        or not label.get("single_feature_ablations")
    ):
        errors.append("label_gat_attribution_incomplete")
    if (
        list(selector.get("partitions") or ()) != ["calibration"]
        or not required.issubset(selector_groups)
        or not selector.get("context_feature_ablations")
    ):
        errors.append("context_gat_attribution_incomplete")
    return errors


def _test(command, log_name, env=None) -> dict:
    completed = subprocess.run(
        command, cwd=ROOT, env=env, check=False,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    log = RUN / log_name
    log.write_text(completed.stdout, encoding="utf-8")
    return {
        "command": command,
        "returncode": int(completed.returncode),
        "log": str(log),
        "log_sha256": _sha256(log),
    }


def _finish(errors, *, tests) -> int:
    tested_paths = (
        *(ROOT / path for path in PYTHON_TESTS),
        ROOT / "native/lunar_spprc/tests/test_native_pricer.cpp",
        ROOT / "src/lunar_ice_bpc/guidance/qg2_v3_selector_runtime.py",
        ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_gat_v3.py",
        ROOT / "src/lunar_ice_bpc/guidance/qg2_unified_arm_selector_v3.py",
        NATIVE_TEST,
    )
    audited_evidence = (
        FORMAL_RESULT, E2E_RESULT, MANIFEST, COMPARISON,
        ORACLE_EXECUTION_FREEZE, E2E_FREEZE, FORMAL_FREEZE,
        LABEL_ATTRIBUTION, SELECTOR_ATTRIBUTION, EVENTS,
        *CURVES, *REPORTS,
    )
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_realmap_v4_completion_audit.v1",
        "passed": not errors,
        "error_count": len(errors),
        "errors": errors,
        "tests": tests,
        "tested_file_sha256": {
            str(path.relative_to(ROOT)): _sha256(path)
            for path in tested_paths if path.is_file()
        },
        "audited_evidence_sha256": {
            str(path.relative_to(ROOT)): _sha256(path)
            for path in audited_evidence if path.is_file()
        },
        "formal_result": str(FORMAL_RESULT),
        "formal_result_sha256": _sha256(FORMAL_RESULT) if FORMAL_RESULT.is_file() else "",
        "manifest": str(MANIFEST),
        "manifest_sha256": _sha256(MANIFEST) if MANIFEST.is_file() else "",
        "production_switch_performed": False,
    }
    _write(OUTPUT, payload)
    print(json.dumps(payload, sort_keys=True), flush=True)
    return 0 if not errors else 2


def _execution_freeze_requirements() -> list[str]:
    payload = _load(ORACLE_EXECUTION_FREEZE)
    errors = []
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_oracle_execution_freeze.v2"
    ):
        return ["oracle_execution_freeze_schema_invalid"]
    if not (
        int(payload.get("scheduled_oracle_contexts") or 0) == 120
        and int(payload.get("scheduled_oracle_contexts_per_scale") or 0) == 60
        and bool(payload.get("oracle_schedule_must_match_exactly"))
    ):
        errors.append("oracle_execution_schedule_invalid")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        path = Path(str(raw_path))
        path = path if path.is_absolute() else ROOT / path
        if not path.is_file() or _sha256(path) != str(expected):
            errors.append(f"oracle_execution_source_drift:{path}")
    e2e = _load(E2E_FREEZE)
    formal = _load(FORMAL_FREEZE)
    if str(e2e.get("oracle_execution_freeze_sha256") or "") != _sha256(
        ORACLE_EXECUTION_FREEZE
    ):
        errors.append("development_e2e_oracle_freeze_binding_invalid")
    if str(formal.get("oracle_execution_freeze_sha256") or "") != _sha256(
        ORACLE_EXECUTION_FREEZE
    ):
        errors.append("formal_oracle_freeze_binding_invalid")
    if str(formal.get("development_e2e_freeze_sha256") or "") != _sha256(
        E2E_FREEZE
    ):
        errors.append("formal_development_freeze_binding_invalid")
    return errors


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
