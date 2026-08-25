#!/usr/bin/env python3
"""Map distinct heldout arm replays back to all five frozen V2 models."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from math import isfinite
from pathlib import Path
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    geometric_mean,
    percentile,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"
VARIANTS = ("gat", "mlp", "linear", "no_message", "shuffled_topology")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal chain forbids heldout analysis")
    schedule_path = run_root / "heldout_execution.freeze.json"
    schedule = _load(schedule_path)
    if not bool(schedule.get("all_models_frozen_before_heldout")):
        raise SystemExit("heldout schedule did not freeze all models")
    rows_path = args.rows.resolve()
    rows = list(_load(rows_path)["rows"])
    grouped = defaultdict(list)
    for row in rows:
        grouped[(str(row["context_id"]), str(row["arm"]))].append(dict(row))
    decisions = {str(row["context_id"]): dict(row) for row in schedule["decisions"]}
    if {context for context, _arm in grouped} != set(decisions):
        raise SystemExit("heldout replay/decision context universe mismatch")
    model_rows = {variant: [] for variant in VARIANTS}
    for context_id, decision in decisions.items():
        q0_rows = grouped.get((context_id, "Q0"), ())
        if len(q0_rows) != 3:
            raise SystemExit("heldout context does not have three Q0 repeats")
        for variant in VARIANTS:
            prediction = dict(decision["variants"][variant])
            action = str(prediction["selected_action"])
            arm_rows = q0_rows if action == "Q0" else grouped.get((context_id, action), ())
            if len(arm_rows) != 3:
                raise SystemExit("heldout selected action lacks three distinct-arm repeats")
            ratio, determined, censored = _ratio(
                q0_rows, arm_rows,
                preparation=float(prediction["preparation_wall_sec"]),
                cap=float(_cap(run_root, int(decision["scale"]))),
                q0_selected=action == "Q0",
            )
            redlines = sorted({
                value for row in (*q0_rows, *arm_rows)
                for value in row.get("correctness_redlines") or ()
            })
            model_rows[variant].append({
                "context_id": context_id,
                "instance_hash": decision["instance_content_hash"],
                "scale": int(decision["scale"]),
                "variant": variant,
                "action": action,
                "ratio": ratio,
                "determined": determined,
                "censored": censored,
                "activated": action != "Q0",
                "harmful": bool(action != "Q0" and ratio is not None and ratio >= 1.05),
                "adverse": bool(action != "Q0" and (censored or (ratio is not None and ratio >= 1.05))),
                "ood": bool(prediction.get("ood")),
                "preparation_wall_sec": float(prediction["preparation_wall_sec"]),
                "correctness_redlines": redlines,
            })
    summaries = {
        variant: _summary(model_rows[variant]) for variant in VARIANTS
    }
    gat_warm = [
        float(row["variants"]["gat"]["warm_graph_tensorization_inference_wall_ms"])
        for row in decisions.values()
    ]
    first_import = all(
        bool(row["variants"][variant].get("first_import_load_included"))
        for row in decisions.values() for variant in VARIANTS
    )
    action_disagreement = _disagreement(decisions, model_rows)
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_heldout_analysis.v2",
        "source_rows": str(rows_path),
        "source_rows_sha256": _sha256(rows_path),
        "execution_freeze": str(schedule_path),
        "execution_freeze_sha256": _sha256(schedule_path),
        "all_models_frozen_before_heldout": True,
        "first_import_load_included": first_import,
        "warm_graph_tensorization_inference_p99_ms": percentile(gat_warm, 0.99),
        "summaries": summaries,
        "action_disagreement": action_disagreement,
        "model_rows": model_rows,
    }
    output = args.output.resolve() if args.output else run_root / "heldout_analysis.json"
    _write_once(output, payload)
    print(json.dumps({
        "output": str(output),
        "gat_combined_gm": summaries["gat"]["combined_gm"],
        "warm_p99_ms": payload["warm_graph_tensorization_inference_p99_ms"],
    }, ensure_ascii=False, indent=2))
    return 0


def _ratio(q0_rows, arm_rows, *, preparation, cap, q0_selected):
    q0_complete = all(_complete(row) for row in q0_rows)
    arm_complete = q0_complete if q0_selected else all(_complete(row) for row in arm_rows)
    q0_censored = all(_censored(row) for row in q0_rows)
    arm_censored = q0_censored if q0_selected else all(_censored(row) for row in arm_rows)
    q0_wall = statistics.median(float(row["solver_wall_sec"]) for row in q0_rows)
    arm_wall = statistics.median(float(row["solver_wall_sec"]) for row in arm_rows)
    if q0_complete and arm_complete:
        ratio = (arm_wall + preparation) / q0_wall
        return ratio, True, False
    if q0_complete and arm_censored:
        return (cap + preparation) / q0_wall, True, True
    if q0_censored and arm_complete:
        return (arm_wall + preparation) / cap, True, False
    if q0_censored and arm_censored:
        return None, False, True
    raise SystemExit("mixed heldout censor state inside repeat block")


def _complete(row):
    return bool(row.get("milestone_reached")) and str(row.get("status")) == "COMPLETED"


def _censored(row):
    return str(row.get("status")) in {"TIMEOUT", "MEMORY_LIMIT", "CENSORED"}


def _summary(rows):
    scales = {}
    redlines = sorted({
        value for row in rows for value in row["correctness_redlines"]
    })
    for scale in (30, 50):
        selected = [row for row in rows if row["scale"] == scale]
        determined = [row for row in selected if row["determined"]]
        ratios = [float(row["ratio"]) for row in determined]
        scales[str(scale)] = {
            "context_count": len(selected),
            "determined_contexts": len(determined),
            "activation_instances": len({
                row["instance_hash"] for row in selected if row["activated"]
            }),
            "net_gm": geometric_mean(ratios) if len(determined) == len(selected) else None,
            "harmful_activations": sum(row["harmful"] for row in selected),
            "adverse_activations": sum(row["adverse"] for row in selected),
            "censored_activations": sum(row["activated"] and row["censored"] for row in selected),
            "ood_contexts": sum(row["ood"] for row in selected),
            "action_counts": dict(Counter(row["action"] for row in selected)),
        }
    values = [float(row["ratio"]) for row in rows if row["determined"]]
    combined = geometric_mean(values) if len(values) == len(rows) else None
    scale_gms = [scales[str(scale)]["net_gm"] for scale in (30, 50)]
    return {
        "scales": scales,
        "combined_gm": combined,
        "worst_scale_gm": max(scale_gms) if all(value is not None for value in scale_gms) else None,
        "correctness_redlines": redlines,
    }


def _disagreement(decisions, model_rows):
    by_model = {
        variant: {row["context_id"]: row for row in rows}
        for variant, rows in model_rows.items()
    }
    rows = []
    for context_id in sorted(decisions):
        actions = {variant: by_model[variant][context_id]["action"] for variant in VARIANTS}
        rows.append({
            "context_id": context_id,
            "actions": actions,
            "disagrees": len(set(actions.values())) > 1,
            "real_wall_ratio_by_variant": {
                variant: by_model[variant][context_id]["ratio"] for variant in VARIANTS
            },
        })
    return {
        "context_count": len(rows),
        "disagreement_count": sum(row["disagrees"] for row in rows),
        "rows": rows,
    }


def _cap(run_root, scale):
    return _load(run_root / "config.freeze.json")["execution"]["replay_caps_sec"][str(scale)]


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable V2 heldout analysis drift:{path}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
