#!/usr/bin/env python3
"""Train MLP/Linear controls only after the real-map GAT fresh test passes.

Two comparisons are kept separate so an architecture claim has a clear
meaning:

* label-ranker controls use the same admission-ancestor pairs as label GAT;
* context-selector controls use the same GAT-QG2/QD1/QB1 matched outcomes as
  context GAT, thereby changing only graph message passing in the selector.

The controls never authorize deployment and cannot replace the frozen GAT
candidate. Their fresh-process results are required for the paper comparison,
but their speed need not beat GAT for the GAT candidate to continue to E2E.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
GAT_RANKER = RUN / "ranker_gat_v4/training_report.json"
GAT_SELECTOR = RUN / "selector_gat_v4/training_report.json"
GAT_FRESH = RUN / "selector_gat_fresh_heldout_v4/fresh_heldout.json"
LABEL_CONTROLS_DIR = RUN / "ranker_controls_v4"
LABEL_CONTROLS = LABEL_CONTROLS_DIR / "training_report.json"
SUMMARY = RUN / "gat_mlp_linear_comparison_v4.json"
STATE = RUN / "realmap_v4_controls_state.json"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
MODEL_ORDER = ("mlp", "linear")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale30-wall-sec", type=float, default=300.0)
    parser.add_argument("--scale50-wall-sec", type=float, default=600.0)
    parser.add_argument("--memory-limit-gb", type=float, default=10.867)
    args = parser.parse_args()
    gat_ranker = _load_required(GAT_RANKER)
    gat_selector = _load_required(GAT_SELECTOR)
    gat_fresh = _load_required(GAT_FRESH)
    _validate_gat_authority(gat_ranker, gat_selector, gat_fresh)
    env = _environment()

    _state("TRAINING_LABEL_MLP_LINEAR_CONTROLS")
    if not LABEL_CONTROLS.is_file():
        code = _run([
            sys.executable,
            str(ROOT / "scripts/train_p0v5_qg2_v3_rankers.py"),
            "--oracle-summary", str(gat_ranker["oracle_summary"]),
            "--instance-split", str(gat_ranker["split_path"]),
            "--output-dir", str(LABEL_CONTROLS_DIR),
            "--models", "mlp,linear",
            "--epochs", "40",
            "--early-stopping-patience", "8",
        ], env=env)
        if code != 0 or not LABEL_CONTROLS.is_file():
            return _stop("LABEL_CONTROL_TRAINING_FAILED", code)

    force_reports = [
        str(_resolve(path))
        for path in gat_selector.get("qg2_force_on_reports") or ()
    ]
    if not force_reports:
        return _stop("GAT_SELECTOR_FORCE_BINDING_MISSING", 2)
    for kind in MODEL_ORDER:
        selector_dir = RUN / f"selector_{kind}_control_v4"
        selector_report = selector_dir / "training_report.json"
        _state(f"TRAINING_CONTEXT_{kind.upper()}_CONTROL")
        if not selector_report.is_file():
            command = [
                sys.executable,
                str(ROOT / "scripts/train_p0v5_qg2_v3_gat_arm_selector.py"),
                "--oracle-summary", str(gat_selector["oracle_summary"]),
                "--ranker-training-report", str(GAT_RANKER),
                "--matched-arm-report", str(gat_selector["matched_arm_report"]),
                "--output-dir", str(selector_dir),
                "--model-kind", kind,
                "--epochs", "200",
                "--early-stopping-patience", "25",
            ]
            for report in force_reports:
                command.extend(("--qg2-force-on-report", report))
            code = _run(command, env=env)
            if code != 0 or not selector_report.is_file():
                return _stop(f"CONTEXT_{kind.upper()}_TRAINING_FAILED", code)

        for partition in ("calibration", "heldout"):
            output_dir = RUN / f"selector_{kind}_fresh_{partition}_v4"
            output = output_dir / f"fresh_{partition}.json"
            _state(
                f"RUNNING_CONTEXT_{kind.upper()}_FRESH_{partition.upper()}"
            )
            if output.is_file():
                continue
            code = _run([
                sys.executable,
                str(ROOT / "scripts/evaluate_p0v5_qg2_v3_gat_selector_fresh.py"),
                "--selector-training-report", str(selector_report),
                "--output-dir", str(output_dir),
                "--output", str(output),
                "--partition", partition,
                "--repeats", "3",
                "--scale30-wall-sec", str(float(args.scale30_wall_sec)),
                "--scale50-wall-sec", str(float(args.scale50_wall_sec)),
                "--memory-limit-gb", str(float(args.memory_limit_gb)),
            ], env=env)
            if code not in {0, 3} or not output.is_file():
                return _stop(
                    f"CONTEXT_{kind.upper()}_FRESH_{partition.upper()}_FAILED",
                    code,
                )
            if not bool(
                dict((_load(output).get("summary") or {}).get("overall") or {}).get(
                    "all_safe"
                )
            ):
                return _stop(
                    f"CONTEXT_{kind.upper()}_FRESH_{partition.upper()}_UNSAFE",
                    3,
                )

    payload = _comparison(gat_ranker, gat_selector, gat_fresh)
    _write(SUMMARY, payload)
    _state(
        "CONTROLS_COMPLETE_GAT_E2E_MAY_START",
        comparison=str(SUMMARY),
        comparison_sha256=_sha256(SUMMARY),
        graph_advantage_supported=payload["graph_advantage_supported"],
    )
    print(json.dumps(payload, sort_keys=True), flush=True)
    return 0


def _validate_gat_authority(ranker, selector, fresh) -> None:
    overall = dict((fresh.get("summary") or {}).get("overall") or {})
    scale30 = dict((fresh.get("summary") or {}).get("scale30") or {})
    scale50 = dict((fresh.get("summary") or {}).get("scale50") or {})
    errors = []
    if str(selector.get("trained_model") or "") != "gat":
        errors.append("selector_not_gat")
    if str(fresh.get("trained_model") or "") != "gat":
        errors.append("fresh_not_gat")
    if str(fresh.get("partition") or "") != "heldout":
        errors.append("fresh_not_heldout")
    if str(fresh.get("selector_training_report_sha256") or "") != _sha256(
        GAT_SELECTOR
    ):
        errors.append("fresh_selector_hash_drift")
    if _resolve(selector.get("ranker_training_report") or "") != GAT_RANKER:
        errors.append("selector_ranker_binding")
    if str(selector.get("ranker_training_report_sha256") or "") != _sha256(
        GAT_RANKER
    ):
        errors.append("selector_ranker_hash_drift")
    if not any(
        str(row.get("model_kind") or "") == "gat"
        for row in ranker.get("models") or ()
    ):
        errors.append("label_gat_missing")
    if not (
        bool(overall.get("all_safe"))
        and int(overall.get("activated_count") or 0) > 0
        and 0.0 < float(overall.get("net_geomean_ratio") or 1.0) < 1.0
        and float(scale30.get("net_geomean_ratio") or 1.0) <= 1.0
        and float(scale50.get("net_geomean_ratio") or 1.0) <= 1.0
    ):
        errors.append("gat_fresh_not_net_positive")
    if errors:
        raise SystemExit("real-map V4 GAT control authority invalid:" + ",".join(errors))


def _comparison(gat_ranker, gat_selector, gat_fresh) -> dict:
    label_controls = _load_required(LABEL_CONTROLS)
    parity_fields = (
        "oracle_summary_sha256", "training_data_hash", "split_sha256",
        "normalization_sha256", "supervision_schema_version",
    )
    if any(
        str(label_controls.get(field) or "")
        != str(gat_ranker.get(field) or "")
        for field in parity_fields
    ):
        raise SystemExit("label GAT/MLP/Linear data or input parity drift")
    label_models = {
        str(row["model_kind"]): dict(row)
        for row in (*gat_ranker.get("models", ()), *label_controls.get("models", ()))
    }
    label_metrics = {}
    for kind in ("gat", "mlp", "linear"):
        row = label_models.get(kind)
        if row is None:
            raise SystemExit(f"label control missing model {kind}")
        label_metrics[kind] = {
            "parameter_count": int(row["parameter_count"]),
            "best_epoch": int(row["best_epoch"]),
            "epochs_completed": int(row["epochs_completed"]),
            "partition_metrics": row["partition_metrics"],
        }
    selector_reports = {"gat": gat_selector}
    fresh_reports = {"gat": gat_fresh}
    for kind in MODEL_ORDER:
        selector_reports[kind] = _load_required(
            RUN / f"selector_{kind}_control_v4/training_report.json"
        )
        fresh_reports[kind] = _load_required(
            RUN / f"selector_{kind}_fresh_heldout_v4/fresh_heldout.json"
        )
        if any(
            str(selector_reports[kind].get(field) or "")
            != str(gat_selector.get(field) or "")
            for field in (
                "oracle_summary_sha256", "ranker_training_report_sha256",
                "matched_arm_report_sha256",
            )
        ):
            raise SystemExit(f"context {kind} control matched-data parity drift")
        if str(fresh_reports[kind].get(
            "selector_training_report_sha256"
        ) or "") != _sha256(
            RUN / f"selector_{kind}_control_v4/training_report.json"
        ):
            raise SystemExit(f"context {kind} fresh report binding drift")
    context_metrics = {}
    for kind in ("gat", "mlp", "linear"):
        overall = dict(
            (fresh_reports[kind].get("summary") or {}).get("overall") or {}
        )
        context_metrics[kind] = {
            "parameter_count": int(selector_reports[kind]["parameter_count"]),
            "classification": selector_reports[kind].get(
                "classification_metrics"
            ),
            "arm_rank": selector_reports[kind].get("arm_rank_metrics"),
            "heldout_fresh": fresh_reports[kind].get("summary"),
            "heldout_net_geomean_ratio": float(
                overall.get("net_geomean_ratio") or 1.0
            ),
            "heldout_activated_count": int(
                overall.get("activated_count") or 0
            ),
            "heldout_harmful_count": int(overall.get("harmful_count") or 0),
            "all_safe": bool(overall.get("all_safe")),
        }
    gat_ratio = context_metrics["gat"]["heldout_net_geomean_ratio"]
    best_control = min(
        context_metrics[kind]["heldout_net_geomean_ratio"]
        for kind in MODEL_ORDER
    )
    return {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_realmap_v4_model_comparison.v1",
        "development_only": True,
        "deployable": False,
        "comparison_contract": {
            "label_ranker": "same_admission_ancestor_pairs_split_loss",
            "context_selector": (
                "same_label_gat_qg2_qd1_qb1_outcomes_split_loss_inputs;"
                "topology_message_passing_only_architecture_difference"
            ),
            "execution_order": ["gat", "mlp", "linear"],
            "gat_candidate_selection_precedes_controls": True,
        },
        "label_ranker_metrics": label_metrics,
        "context_selector_metrics": context_metrics,
        "gat_to_best_control_net_ratio": gat_ratio / max(1.0e-12, best_control),
        "graph_advantage_supported": bool(gat_ratio <= 0.98 * best_control),
        "claim_rule": (
            "if_false_report_learned_ordering_only_not_graph_architecture_advantage"
        ),
        "all_controls_safe": all(
            context_metrics[kind]["all_safe"] for kind in MODEL_ORDER
        ),
        "deployment_authorized": False,
    }


def _run(command, *, env) -> int:
    return subprocess.run(command, cwd=ROOT, env=env, check=False).returncode


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    for key in (
        "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
        "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
        "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST",
        "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_EVALUATION_MODE",
        "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR",
    ):
        env.pop(key, None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{BUILD}"
    return env


def _stop(status, returncode) -> int:
    _state(status, returncode=int(returncode or 2))
    return int(returncode or 2)


def _state(status, **extra) -> None:
    _write(STATE, {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_realmap_v4_controls_state.v1",
        "status": str(status),
        **extra,
    })


def _load_required(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"required V4 artifact missing: {path}")
    return _load(path)


def _resolve(value) -> Path:
    path = Path(str(value))
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


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
