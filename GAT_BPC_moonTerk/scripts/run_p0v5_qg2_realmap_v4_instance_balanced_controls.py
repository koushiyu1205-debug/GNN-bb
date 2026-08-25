#!/usr/bin/env python3
"""Run post-GAT MLP/Linear controls with the same instance authority."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.instance_balanced_learning import (  # noqa: E402
    INSTANCE_BALANCING_POLICY_V1,
)
from lunar_ice_bpc.guidance.qg2_v4_training_freeze import (  # noqa: E402
    sha256,
    validate_training_freeze,
)


RUN = ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
TRAINING_FREEZE = RUN / "realmap_v4_instance_balanced_training_freeze.json"
FROZEN_CONTROLLER = ROOT / "scripts/run_p0v5_qg2_realmap_v4_controls_after_gat.py"
RANKER_WRAPPER = ROOT / "scripts/train_p0v5_qg2_v4_instance_balanced_rankers.py"
SELECTOR_WRAPPER = (
    ROOT / "scripts/train_p0v5_qg2_v4_instance_balanced_arm_selector.py"
)
FRESH_WRAPPER = (
    ROOT
    / "scripts/evaluate_p0v5_qg2_v4_instance_balanced_selector_fresh.py"
)
COMPARISON = RUN / "gat_mlp_linear_comparison_v4.json"
ADDENDUM = RUN / "gat_mlp_linear_instance_balanced_addendum_v4.json"
LABEL_REPORTS = {
    "gat": RUN / "ranker_gat_v4/training_report.json",
    "controls": RUN / "ranker_controls_v4/training_report.json",
}
SELECTOR_REPORTS = {
    "gat": RUN / "selector_gat_v4/training_report.json",
    "mlp": RUN / "selector_mlp_control_v4/training_report.json",
    "linear": RUN / "selector_linear_control_v4/training_report.json",
}
FRESH_REPORTS = {
    f"{kind}_{partition}": RUN / f"selector_{kind}_fresh_{partition}_v4"
    / f"fresh_{partition}.json"
    for kind in ("gat", "mlp", "linear")
    for partition in ("calibration", "heldout")
}


def main() -> int:
    validate_training_freeze(TRAINING_FREEZE)
    for key in ("gat_calibration", "gat_heldout"):
        _validated_fresh(FRESH_REPORTS[key])
    controller = _load_frozen_controller()
    original_run = controller._run
    original_state = controller._state

    def run(command, *, env):
        validate_training_freeze(TRAINING_FREEZE)
        return original_run(_redirect(command), env=env)

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
    returncode = int(controller.main())
    validate_training_freeze(TRAINING_FREEZE)
    if returncode == 0:
        _freeze_instance_balanced_comparison_addendum()
    return returncode


def _freeze_instance_balanced_comparison_addendum() -> None:
    if not COMPARISON.is_file():
        raise SystemExit("instance-balanced comparison lacks upstream summary")
    reports = {**{
        f"label_{key}": _validated_report(
            path, checkpoint_metric="mean_instance_pair_accuracy"
        )
        for key, path in LABEL_REPORTS.items()
    }, **{
        f"context_{key}": _validated_report(
            path, checkpoint_metric="instance_balanced_total_loss"
        )
        for key, path in SELECTOR_REPORTS.items()
    }}
    label_parity = (
        "oracle_summary_sha256", "training_data_hash", "split_sha256",
        "normalization_sha256", "supervision_schema_version",
    )
    if any(
        str(reports["label_gat"].get(field) or "")
        != str(reports["label_controls"].get(field) or "")
        for field in label_parity
    ):
        raise SystemExit("instance-balanced label comparison parity drift")
    context_parity = (
        "oracle_summary_sha256", "ranker_training_report_sha256",
        "matched_arm_report_sha256",
    )
    if any(
        str(reports["context_gat"].get(field) or "")
        != str(reports[f"context_{kind}"].get(field) or "")
        for kind in ("mlp", "linear") for field in context_parity
    ):
        raise SystemExit("instance-balanced context comparison parity drift")
    fresh_reports = {
        key: _validated_fresh(path) for key, path in FRESH_REPORTS.items()
    }
    artifacts = {
        **{f"label_{key}": path for key, path in LABEL_REPORTS.items()},
        **{f"context_{key}": path for key, path in SELECTOR_REPORTS.items()},
        **{f"fresh_{key}": path for key, path in FRESH_REPORTS.items()},
        "upstream_comparison": COMPARISON,
        "training_freeze": TRAINING_FREEZE,
    }
    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_v4_instance_balanced_comparison.v1"
        ),
        "development_only": True,
        "deployable": False,
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "comparison_contract": {
            "label_ranker": (
                "same_milestone_conditional_action_reachable_pairs_split_loss;"
                "admission_uses_master_admitted_ancestors;"
                "proof_uses_dominance_and_terminal_progress"
            ),
            "context_selector": (
                "same_qg2_qd1_qb1_matched_outcomes_split_loss_inputs;"
                "topology_message_passing_only_architecture_difference"
            ),
            "execution_order": ["gat", "mlp", "linear"],
            "gat_fresh_authority_precedes_controls": True,
            "experimental_unit": "instance",
        },
        "artifact_sha256": {
            key: sha256(path) for key, path in sorted(artifacts.items())
        },
        "production_switch_authorized": False,
    }
    if ADDENDUM.is_file():
        if _load(ADDENDUM) != payload:
            raise SystemExit("instance-balanced comparison addendum drift")
    else:
        _write(ADDENDUM, payload)


def _validated_report(path: Path, *, checkpoint_metric: str) -> dict:
    payload = _load(path)
    if (
        str(payload.get("instance_balancing_policy") or "")
        != INSTANCE_BALANCING_POLICY_V1
        or str(payload.get("checkpoint_selection_metric") or "")
        != checkpoint_metric
    ):
        raise SystemExit(f"instance-balanced model report invalid:{path}")
    return payload


def _validated_fresh(path: Path) -> dict:
    payload = _load(path)
    if (
        str(payload.get("instance_balancing_policy") or "")
        != INSTANCE_BALANCING_POLICY_V1
        or str(payload.get("summary_experimental_unit") or "") != "instance"
        or not bool(
            dict((payload.get("summary") or {}).get("overall") or {}).get(
                "all_safe"
            )
        )
    ):
        raise SystemExit(f"instance-balanced fresh report invalid:{path}")
    return payload


def _redirect(command):
    result = list(command)
    if len(result) >= 2:
        script = Path(str(result[1])).name
        if script == "train_p0v5_qg2_v3_rankers.py":
            result[1] = str(RANKER_WRAPPER)
        elif script == "train_p0v5_qg2_v3_gat_arm_selector.py":
            result[1] = str(SELECTOR_WRAPPER)
        elif script == "evaluate_p0v5_qg2_v3_gat_selector_fresh.py":
            result[1] = str(FRESH_WRAPPER)
    return result


def _load_frozen_controller():
    spec = importlib.util.spec_from_file_location(
        "p0v5_qg2_v4_frozen_controls_controller", FROZEN_CONTROLLER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen post-GAT controls controller")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"instance-balanced model report missing:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


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
