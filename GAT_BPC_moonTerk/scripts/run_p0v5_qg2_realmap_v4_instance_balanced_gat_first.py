#!/usr/bin/env python3
"""Resume the real-map GAT-first pipeline with instance-balanced training."""

from __future__ import annotations

from datetime import datetime
import importlib.util
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
    create_training_freeze,
    sha256,
    validate_training_freeze,
)


RUN = ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
ORACLE = RUN / "oracle_realmap_v4.json"
ORACLE_FREEZE = RUN / "realmap_v4_oracle_execution_freeze.json"
SPLIT = RUN / "realmap_v4_instance_split.json"
TRAIN_GATE = RUN / "realmap_v4_training_gate.json"
AUTHORIZED_ORACLE = RUN / "oracle_realmap_v4_training_view.json"
TRAINING_AUTHORIZER = (
    ROOT
    / "scripts/authorize_p0v5_qg2_realmap_v4_instance_balanced_training.py"
)
FITTING_GATE_FREEZE = (
    RUN / "realmap_v4_instance_balanced_fitting_gate_freeze.json"
)
SMOKE_DIR = RUN / "instance_balanced_pretraining_smoke_v4"
SMOKE_REPORT = SMOKE_DIR / "smoke_report.json"
TRAINING_FREEZE = RUN / "realmap_v4_instance_balanced_training_freeze.json"
INSTANCE_BALANCED_AUDIT = (
    RUN / "realmap_v4_instance_balanced_completion_audit.json"
)
INSTANCE_BALANCED_AUDITOR = (
    ROOT / "scripts/audit_p0v5_qg2_v4_instance_balanced_completion.py"
)
FROZEN_CONTROLLER = ROOT / "scripts/run_p0v5_qg2_realmap_v4_gat_first.py"
RANKER_WRAPPER = ROOT / "scripts/train_p0v5_qg2_v4_instance_balanced_rankers.py"
SELECTOR_WRAPPER = (
    ROOT / "scripts/train_p0v5_qg2_v4_instance_balanced_arm_selector.py"
)
CONTROLS_WRAPPER = (
    ROOT / "scripts/run_p0v5_qg2_realmap_v4_instance_balanced_controls.py"
)
LABEL_ATTRIBUTION_WRAPPER = (
    ROOT
    / "scripts/analyze_p0v5_qg2_v4_instance_balanced_gat_attribution.py"
)
SELECTOR_ATTRIBUTION_WRAPPER = (
    ROOT
    / "scripts/analyze_p0v5_qg2_v4_instance_balanced_selector_attribution.py"
)
FRESH_WRAPPER = (
    ROOT
    / "scripts/evaluate_p0v5_qg2_v4_instance_balanced_selector_fresh.py"
)
FORCE_ON_WRAPPER = (
    ROOT
    / "scripts/calibrate_p0v5_qg2_v4_instance_balanced_gat_force_on.py"
)
UPSTREAM_CANDIDATE = (
    RUN / "P0V5_QG2_LABEL_STATE_GAT_V4_FINAL_candidate_freeze.json"
)
FINAL_CANDIDATE = (
    RUN
    / "P0V5_QG2_LABEL_STATE_GAT_V4_INSTANCE_BALANCED_FINAL_candidate_freeze.json"
)
COMPARISON_ADDENDUM = (
    RUN / "gat_mlp_linear_instance_balanced_addendum_v4.json"
)
UPSTREAM_COMPARISON = RUN / "gat_mlp_linear_comparison_v4.json"
TERMINAL = RUN / "realmap_v4_instance_balanced_terminal.json"


def main() -> int:
    if not ORACLE.is_file():
        raise SystemExit("instance-balanced GAT-first waits for Oracle summary")
    _ensure_training_authority()
    _ensure_pretraining_smoke()
    _ensure_training_freeze()
    validate_training_freeze(TRAINING_FREEZE)
    controller = _load_frozen_controller()
    original_run = controller._run
    original_state = controller._state

    def run(command, *, env, accepted={0}):
        validate_training_freeze(TRAINING_FREEZE)
        return original_run(_redirect(command), env=env, accepted=accepted)

    def state(status, **extra):
        return original_state(
            status,
            instance_balancing_policy=INSTANCE_BALANCING_POLICY_V1,
            instance_balanced_training_freeze=str(TRAINING_FREEZE),
            instance_balanced_training_freeze_sha256=sha256(TRAINING_FREEZE),
            **extra,
        )

    controller._run = run
    controller._state = state
    controller._qg2_train_support = _instance_balanced_qg2_train_support
    returncode = int(controller.main())
    validate_training_freeze(TRAINING_FREEZE)
    if returncode == 0:
        completed = subprocess.run(
            [sys.executable, str(INSTANCE_BALANCED_AUDITOR)],
            cwd=ROOT, check=False,
        )
        returncode = int(completed.returncode)
        if returncode == 0:
            validate_training_freeze(TRAINING_FREEZE)
            _freeze_instance_balanced_candidate()
    if returncode != 0:
        _write(TERMINAL, {
            "schema_version": (
                "lunar_ice_bpc.p0v5_qg2_v4_instance_balanced_terminal.v1"
            ),
            "created_at": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "returncode": returncode,
            "training_freeze": str(TRAINING_FREEZE),
            "training_freeze_sha256": sha256(TRAINING_FREEZE),
            "candidate_frozen": False,
            "production_switch_performed": False,
        })
    return returncode


def _ensure_training_freeze() -> None:
    if TRAINING_FREEZE.is_file():
        validate_training_freeze(TRAINING_FREEZE)
        return
    source_paths = (
        Path(__file__).resolve(),
        ROOT / "scripts/run_p0v5_qg2_realmap_v4_instance_balanced_controls.py",
        RANKER_WRAPPER,
        SELECTOR_WRAPPER,
        FROZEN_CONTROLLER,
        ROOT / "scripts/run_p0v5_qg2_realmap_v4_controls_after_gat.py",
        ROOT / "scripts/train_p0v5_qg2_v3_rankers.py",
        ROOT / "scripts/train_p0v5_qg2_v3_gat_arm_selector.py",
        ROOT / "src/lunar_ice_bpc/guidance/instance_balanced_learning.py",
        ROOT / "src/lunar_ice_bpc/guidance/qg2_v4_training_freeze.py",
        ROOT / "scripts/smoke_p0v5_qg2_v4_instance_balanced_training.py",
        ROOT / "scripts/watch_p0v5_qg2_v4_instance_balanced_gat_first.py",
        LABEL_ATTRIBUTION_WRAPPER,
        SELECTOR_ATTRIBUTION_WRAPPER,
        FRESH_WRAPPER,
        FORCE_ON_WRAPPER,
        INSTANCE_BALANCED_AUDITOR,
        TRAINING_AUTHORIZER,
        FITTING_GATE_FREEZE,
        ROOT / "tests/test_p0v5_qg2_instance_balanced_learning.py",
        ROOT / "tests/test_p0v5_qg2_realmap_v4_post_gat_controllers.py",
    )
    create_training_freeze(
        output=TRAINING_FREEZE,
        oracle_summary=AUTHORIZED_ORACLE,
        oracle_execution_freeze=ORACLE_FREEZE,
        instance_split=SPLIT,
        training_gate=TRAIN_GATE,
        source_paths=source_paths,
        forbidden_preexisting_outputs=(
            RUN / "ranker_gat_v4/training_report.json",
            RUN / "selector_gat_v4/training_report.json",
            RUN / "ranker_controls_v4/training_report.json",
        ),
        pretraining_smoke_report=SMOKE_REPORT,
    )


def _ensure_training_authority() -> None:
    if AUTHORIZED_ORACLE.is_file():
        payload = _load(AUTHORIZED_ORACLE)
        if (
            not bool(payload.get("training_permitted"))
            or not bool(dict(payload.get("oracle_gate") or {}).get("passed"))
            or str(payload.get("fitting_gate_profile") or "")
            != "bounded_instance_supported_fitting_only.v2"
        ):
            raise SystemExit("existing real-map training authority is invalid")
        return
    if TRAIN_GATE.exists():
        raise SystemExit(
            "partial real-map training authority exists without authorized view"
        )
    completed = subprocess.run([
        sys.executable,
        str(TRAINING_AUTHORIZER),
        "--oracle-summary", str(ORACLE),
        "--instance-split", str(SPLIT),
        "--gate-output", str(TRAIN_GATE),
        "--authorized-oracle-output", str(AUTHORIZED_ORACLE),
    ], cwd=ROOT, check=False)
    if completed.returncode != 0 or not AUTHORIZED_ORACLE.is_file():
        raise SystemExit(
            "real-map Oracle did not obtain training-only authority"
        )


def _ensure_pretraining_smoke() -> None:
    completed = subprocess.run([
        sys.executable,
        str(ROOT / "scripts/smoke_p0v5_qg2_v4_instance_balanced_training.py"),
        "--oracle-summary", str(AUTHORIZED_ORACLE),
        "--instance-split", str(SPLIT),
        "--output-dir", str(SMOKE_DIR),
        "--output", str(SMOKE_REPORT),
        "--maximum-contexts-per-partition-scale", "2",
    ], cwd=ROOT, check=False)
    if completed.returncode != 0 or not SMOKE_REPORT.is_file():
        raise SystemExit("instance-balanced pretraining smoke failed")


def _redirect(command):
    result = list(command)
    if len(result) >= 2:
        script = Path(str(result[1])).name
        if script == "train_p0v5_qg2_v3_rankers.py":
            result[1] = str(RANKER_WRAPPER)
        elif script == "train_p0v5_qg2_v3_gat_arm_selector.py":
            result[1] = str(SELECTOR_WRAPPER)
        elif script == "run_p0v5_qg2_realmap_v4_controls_after_gat.py":
            result[1] = str(CONTROLS_WRAPPER)
        elif script == "analyze_p0v5_qg2_v3_gat_attribution.py":
            result[1] = str(LABEL_ATTRIBUTION_WRAPPER)
        elif script == "analyze_p0v5_qg2_v3_selector_attribution.py":
            result[1] = str(SELECTOR_ATTRIBUTION_WRAPPER)
        elif script == "evaluate_p0v5_qg2_v3_gat_selector_fresh.py":
            result[1] = str(FRESH_WRAPPER)
        elif script == "calibrate_p0v5_qg2_v3_gat_force_on.py":
            result[1] = str(FORCE_ON_WRAPPER)
    return result


def _instance_balanced_qg2_train_support(report) -> bool:
    rows = _eligible_qg2_train_rows(report)
    instances = {str(row.get("instance_hash") or "") for row in rows}
    beneficial_rows = [row for row in rows if _qg2_row_is_beneficial(row)]
    beneficial_instances = {
        str(row.get("instance_hash") or "") for row in beneficial_rows
    }
    scale_instances = {
        scale: {
            str(row.get("instance_hash") or "")
            for row in rows
            if int(row.get("scale") or 0) == scale
        }
        for scale in (30, 50)
    }
    return bool(
        len(rows) >= 5
        and len(instances) >= 5
        and all(len(scale_instances[scale]) >= 2 for scale in (30, 50))
        and len(beneficial_rows) >= 2
        and len(beneficial_instances) >= 2
    )


def _eligible_qg2_train_rows(report):
    return [
        row for row in report.get("records") or ()
        if str(row.get("partition") or "") == "train"
        and bool(row.get("safe"))
        and bool(row.get("action_eligible"))
        and str(row.get("comparison_class") or "") not in {
            "both_censored",
            "literal_q0_veto",
            "replicate_class_disagreement",
        }
    ]


def _qg2_row_is_beneficial(row) -> bool:
    return bool(row.get("beneficial")) or str(
        row.get("comparison_class") or ""
    ) == "gat_beneficial_censor"


def _freeze_instance_balanced_candidate() -> None:
    validate_training_freeze(TRAINING_FREEZE)
    if not UPSTREAM_CANDIDATE.is_file():
        raise SystemExit("upstream V4 candidate freeze missing")
    _validate_instance_balanced_completion_audit()
    reports = (
        RUN / "ranker_gat_v4/training_report.json",
        RUN / "selector_gat_v4/training_report.json",
        RUN / "ranker_controls_v4/training_report.json",
        RUN / "selector_mlp_control_v4/training_report.json",
        RUN / "selector_linear_control_v4/training_report.json",
    )
    attributions = (
        RUN / "ranker_gat_v4_attribution.json",
        RUN / "selector_gat_v4_attribution.json",
    )
    fresh_reports = tuple(
        RUN / f"selector_{kind}_fresh_{partition}_v4"
        / f"fresh_{partition}.json"
        for kind in ("gat", "mlp", "linear")
        for partition in ("calibration", "heldout")
    )
    for path in reports:
        payload = _load(path)
        if str(payload.get("instance_balancing_policy") or "") != (
            INSTANCE_BALANCING_POLICY_V1
        ):
            raise SystemExit(f"instance-balanced report binding missing:{path}")
    for path in attributions:
        attribution = _load(path)
        if str(attribution.get("instance_balancing_policy") or "") != (
            INSTANCE_BALANCING_POLICY_V1
        ):
            raise SystemExit(
                f"instance-balanced attribution binding missing:{path}"
            )
    for path in fresh_reports:
        fresh = _load(path)
        if (
            str(fresh.get("instance_balancing_policy") or "")
            != INSTANCE_BALANCING_POLICY_V1
            or str(fresh.get("summary_experimental_unit") or "")
            != "instance"
        ):
            raise SystemExit(
                f"instance-balanced fresh binding missing:{path}"
            )
    addendum = _load(COMPARISON_ADDENDUM)
    if (
        str(addendum.get("instance_balancing_policy") or "")
        != INSTANCE_BALANCING_POLICY_V1
        or bool(addendum.get("deployable"))
        or bool(addendum.get("production_switch_authorized"))
    ):
        raise SystemExit("instance-balanced comparison addendum invalid")
    addendum_artifacts = dict(addendum.get("artifact_sha256") or {})
    expected_addendum_artifacts = {
        "label_gat": reports[0],
        "context_gat": reports[1],
        "label_controls": reports[2],
        "context_mlp": reports[3],
        "context_linear": reports[4],
        "upstream_comparison": UPSTREAM_COMPARISON,
        "training_freeze": TRAINING_FREEZE,
        **{
            f"fresh_{kind}_{partition}": (
                RUN / f"selector_{kind}_fresh_{partition}_v4"
                / f"fresh_{partition}.json"
            )
            for kind in ("gat", "mlp", "linear")
            for partition in ("calibration", "heldout")
        },
    }
    if any(
        str(addendum_artifacts.get(key) or "") != sha256(path)
        for key, path in expected_addendum_artifacts.items()
    ):
        raise SystemExit("instance-balanced comparison artifact drift")
    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_realmap_v4_instance_balanced_final.v1"
        ),
        "candidate_id": (
            "P0V5_QG2_LABEL_STATE_GAT_V4_INSTANCE_BALANCED_FINAL"
        ),
        "upstream_v4_candidate": str(UPSTREAM_CANDIDATE),
        "upstream_v4_candidate_sha256": sha256(UPSTREAM_CANDIDATE),
        "training_freeze": str(TRAINING_FREEZE),
        "training_freeze_sha256": sha256(TRAINING_FREEZE),
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "training_report_sha256": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in reports
        },
        "attribution_sha256": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in attributions
        },
        "fresh_report_sha256": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in fresh_reports
        },
        "comparison_addendum": str(COMPARISON_ADDENDUM),
        "comparison_addendum_sha256": sha256(COMPARISON_ADDENDUM),
        "instance_balanced_completion_audit": str(
            INSTANCE_BALANCED_AUDIT
        ),
        "instance_balanced_completion_audit_sha256": sha256(
            INSTANCE_BALANCED_AUDIT
        ),
        "literal_fallback_action": "Q0",
        "ordering_only": True,
        "may_filter_labels": False,
        "may_change_dominance_bound_rc_or_certificate": False,
        "production_default_overwritten": False,
        "p0v4_or_p0v5_exact_control_overwritten": False,
        "production_switch_authorized": False,
    }
    if FINAL_CANDIDATE.is_file():
        if _load(FINAL_CANDIDATE) != payload:
            raise SystemExit("instance-balanced final candidate freeze drift")
    else:
        _write(FINAL_CANDIDATE, payload)


def _validate_instance_balanced_completion_audit() -> dict:
    audit = _load(INSTANCE_BALANCED_AUDIT)
    audit_bindings = dict(audit.get("audited_artifact_sha256") or {})
    if (
        not bool(audit.get("passed"))
        or int(audit.get("error_count") or 0) != 0
        or str(audit.get("instance_balancing_policy") or "")
        != INSTANCE_BALANCING_POLICY_V1
        or not audit_bindings
    ):
        raise SystemExit("instance-balanced completion audit invalid")
    audit_drift = []
    for relative, expected in sorted(audit_bindings.items()):
        path = ROOT / str(relative)
        if not path.is_file() or sha256(path) != str(expected):
            audit_drift.append(str(relative))
    if audit_drift:
        raise SystemExit(
            "instance-balanced audited artifact drift:"
            + ",".join(audit_drift)
        )
    return audit


def _load_frozen_controller():
    spec = importlib.util.spec_from_file_location(
        "p0v5_qg2_v4_frozen_gat_first_controller", FROZEN_CONTROLLER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen GAT-first controller")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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


if __name__ == "__main__":
    raise SystemExit(main())
