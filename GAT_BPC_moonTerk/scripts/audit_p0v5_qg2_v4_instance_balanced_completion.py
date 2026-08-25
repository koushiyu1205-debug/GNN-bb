#!/usr/bin/env python3
"""Audit the instance-balanced layer after the frozen V4 completion audit."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.instance_balanced_learning import (  # noqa: E402
    INSTANCE_BALANCING_POLICY_V1,
)
from lunar_ice_bpc.guidance.qg2_v4_training_freeze import (  # noqa: E402
    validate_training_freeze,
)


RUN = ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
TRAINING_FREEZE = RUN / "realmap_v4_instance_balanced_training_freeze.json"
UPSTREAM_CANDIDATE = RUN / "P0V5_QG2_LABEL_STATE_GAT_V4_FINAL_candidate_freeze.json"
ADDENDUM = RUN / "gat_mlp_linear_instance_balanced_addendum_v4.json"
OUTPUT = RUN / "realmap_v4_instance_balanced_completion_audit.json"
TEST_LOG = RUN / "instance_balanced_completion_test.log"
FORCE_REPORTS = {
    "train": RUN / "force_on_train_screen_v4/force_on_train.json",
    "calibration": RUN / "force_on_calibration_v4/force_on_calibration.json",
    "heldout": RUN / "force_on_heldout_v4/force_on_heldout.json",
}
MODEL_REPORTS = (
    RUN / "ranker_gat_v4/training_report.json",
    RUN / "selector_gat_v4/training_report.json",
    RUN / "ranker_controls_v4/training_report.json",
    RUN / "selector_mlp_control_v4/training_report.json",
    RUN / "selector_linear_control_v4/training_report.json",
)
ATTRIBUTIONS = (
    RUN / "ranker_gat_v4_attribution.json",
    RUN / "selector_gat_v4_attribution.json",
)
FRESH_REPORTS = tuple(
    RUN / f"selector_{kind}_fresh_{partition}_v4"
    / f"fresh_{partition}.json"
    for kind in ("gat", "mlp", "linear")
    for partition in ("calibration", "heldout")
)
CURVES = (
    RUN / "ranker_gat_v4/training_curve.jsonl",
    RUN / "selector_gat_v4/training_curve.jsonl",
    RUN / "ranker_controls_v4/training_curve.jsonl",
    RUN / "selector_mlp_control_v4/training_curve.jsonl",
    RUN / "selector_linear_control_v4/training_curve.jsonl",
)
TESTS = (
    ROOT / "tests/test_p0v5_qg2_instance_balanced_learning.py",
    ROOT / "tests/test_p0v5_qg2_realmap_v4_post_gat_controllers.py",
)


def main() -> int:
    errors = []
    try:
        validate_training_freeze(TRAINING_FREEZE)
    except (OSError, ValueError, TypeError) as exc:
        errors.append(f"training_freeze_invalid:{exc}")
    required = (
        TRAINING_FREEZE, UPSTREAM_CANDIDATE, ADDENDUM,
        *MODEL_REPORTS, *ATTRIBUTIONS, *FRESH_REPORTS, *CURVES,
        FORCE_REPORTS["train"],
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        errors.append("missing_artifacts:" + ",".join(missing))
        return _finish(errors, test=None, audited=required)

    upstream = _load(UPSTREAM_CANDIDATE)
    action_universe = set(upstream.get("learned_action_surface") or ())
    if action_universe not in (
        {"Q0", "QD1", "QB1"},
        {"Q0", "QG2", "QD1", "QB1"},
    ):
        errors.append("upstream_action_universe_invalid")
    errors.extend(_model_requirements(action_universe=action_universe))
    errors.extend(_attribution_requirements())
    errors.extend(_fresh_requirements())
    errors.extend(_curve_requirements())
    errors.extend(_force_requirements(qg2_enabled="QG2" in action_universe))

    test = _run_tests()
    if test["returncode"] != 0:
        errors.append("instance_balanced_completion_tests_failed")
    audited = (
        *required,
        *(path for path in FORCE_REPORTS.values() if path.is_file()),
        *TESTS,
        Path(__file__).resolve(),
    )
    return _finish(errors, test=test, audited=audited)


def _model_requirements(*, action_universe: set[str]) -> list[str]:
    errors = []
    expected_metrics = (
        "mean_instance_pair_accuracy",
        "instance_balanced_total_loss",
        "mean_instance_pair_accuracy",
        "instance_balanced_total_loss",
        "instance_balanced_total_loss",
    )
    for path, metric in zip(MODEL_REPORTS, expected_metrics, strict=True):
        payload = _load(path)
        if (
            str(payload.get("instance_balancing_policy") or "")
            != INSTANCE_BALANCING_POLICY_V1
            or str(payload.get("checkpoint_selection_metric") or "")
            != metric
        ):
            errors.append(f"instance_balanced_model_invalid:{path}")
    expected_trainable = (
        {"QG2", "QD1", "QB1"}
        if "QG2" in action_universe else {"QD1", "QB1"}
    )
    for path in (MODEL_REPORTS[1], MODEL_REPORTS[3], MODEL_REPORTS[4]):
        payload = _load(path)
        if (
            set(payload.get("trainable_arms") or ()) != expected_trainable
            or str(dict(payload.get("qg2_force_on_screen") or {}).get(
                "instance_balancing_policy"
            ) or "") != INSTANCE_BALANCING_POLICY_V1
        ):
            errors.append(f"selector_action_surface_authority_invalid:{path}")
    return errors


def _attribution_requirements() -> list[str]:
    errors = []
    for path in ATTRIBUTIONS:
        payload = _load(path)
        if (
            str(payload.get("instance_balancing_policy") or "")
            != INSTANCE_BALANCING_POLICY_V1
            or not payload.get("single_feature_dominance_diagnostic")
        ):
            errors.append(f"instance_balanced_attribution_invalid:{path}")
    return errors


def _fresh_requirements() -> list[str]:
    errors = []
    for path in FRESH_REPORTS:
        payload = _load(path)
        overall = dict((payload.get("summary") or {}).get("overall") or {})
        if (
            str(payload.get("instance_balancing_policy") or "")
            != INSTANCE_BALANCING_POLICY_V1
            or str(payload.get("summary_experimental_unit") or "")
            != "instance"
            or not bool(overall.get("all_safe"))
        ):
            errors.append(f"instance_balanced_fresh_invalid:{path}")
    return errors


def _curve_requirements() -> list[str]:
    required = {
        "model", "epoch", "total_loss", "rank_loss", "benefit_loss",
        "positive_gain_loss", "epoch_wall_sec",
    }
    errors = []
    for path in CURVES:
        rows = [
            json.loads(line) for line in path.read_text(
                encoding="utf-8"
            ).splitlines() if line.strip()
        ]
        if not rows or any(not required.issubset(row) for row in rows):
            errors.append(f"instance_balanced_curve_invalid:{path}")
    return errors


def _force_requirements(*, qg2_enabled: bool) -> list[str]:
    errors = []
    train = _load(FORCE_REPORTS["train"])
    if not _force_report_is_instance_balanced(train):
        errors.append("force_train_not_instance_balanced")
    supported = _qg2_support(train)
    if qg2_enabled != supported:
        errors.append("qg2_action_surface_force_support_mismatch")
    for partition in ("calibration", "heldout"):
        path = FORCE_REPORTS[partition]
        if qg2_enabled:
            if not path.is_file() or not _force_report_is_instance_balanced(
                _load(path)
            ):
                errors.append(f"force_{partition}_missing_or_invalid")
        elif path.is_file():
            errors.append(f"force_{partition}_exists_while_qg2_vetoed")
    return errors


def _force_report_is_instance_balanced(payload: dict) -> bool:
    return bool(
        str(payload.get("instance_balancing_policy") or "")
        == INSTANCE_BALANCING_POLICY_V1
        and str(payload.get("selection_experimental_unit") or "")
        == "instance"
        and str(payload.get("context_selection_policy") or "")
        == "instance_round_robin_then_frozen_state_order.v1"
    )


def _qg2_support(payload: dict) -> bool:
    rows = [
        row for row in payload.get("records") or ()
        if str(row.get("partition") or "") == "train"
        and bool(row.get("safe"))
        and bool(row.get("action_eligible"))
        and str(row.get("comparison_class") or "") not in {
            "both_censored", "literal_q0_veto",
            "replicate_class_disagreement",
        }
    ]
    instances = {str(row.get("instance_hash") or "") for row in rows}
    beneficial = [
        row for row in rows
        if bool(row.get("beneficial"))
        or str(row.get("comparison_class") or "")
        == "gat_beneficial_censor"
    ]
    beneficial_instances = {
        str(row.get("instance_hash") or "") for row in beneficial
    }
    by_scale = {
        scale: {
            str(row.get("instance_hash") or "") for row in rows
            if int(row.get("scale") or 0) == scale
        }
        for scale in (30, 50)
    }
    return bool(
        len(rows) >= 5 and len(instances) >= 5
        and all(len(by_scale[scale]) >= 2 for scale in (30, 50))
        and len(beneficial) >= 2 and len(beneficial_instances) >= 2
    )


def _run_tests() -> dict:
    command = [
        sys.executable, "-m", "pytest", "-q", *(str(path) for path in TESTS),
    ]
    env = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    completed = subprocess.run(
        command, cwd=ROOT, env=env, check=False,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    TEST_LOG.write_text(completed.stdout, encoding="utf-8")
    return {
        "command": command,
        "returncode": int(completed.returncode),
        "log": str(TEST_LOG),
        "log_sha256": _sha256(TEST_LOG),
    }


def _finish(errors, *, test, audited) -> int:
    paths = sorted({Path(path).resolve() for path in audited if Path(path).is_file()})
    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_v4_instance_balanced_completion.v1"
        ),
        "passed": not errors,
        "error_count": len(errors),
        "errors": errors,
        "test": test,
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "audited_artifact_sha256": {
            str(path.relative_to(ROOT)): _sha256(path) for path in paths
        },
        "production_switch_performed": False,
    }
    _write(OUTPUT, payload)
    print(json.dumps(payload, sort_keys=True), flush=True)
    return 0 if not errors else 2


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
