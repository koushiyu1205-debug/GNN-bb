#!/usr/bin/env python3
"""Select one immutable trial K per scale from train-only matched outcomes."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
from math import exp, log
import json
from pathlib import Path
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.p0v5_temporal_gat_common import (  # noqa: E402
    load_frozen_config, mark_terminal_negative, write_once,
)


def _gm(values):
    rows = tuple(float(value) for value in values)
    if not rows or any(value <= 0.0 for value in rows):
        raise ValueError("geometric mean requires positive values")
    return exp(sum(log(value) for value in rows) / len(rows))


def _collapsed(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["context_id"], int(row["scale"]), int(row["k"]),
                 row["arm"])].append(row)
    output = {}
    for key, repeats in grouped.items():
        complete = [row for row in repeats if row.get("status") == "COMPLETE"]
        repeat_coverage = {int(row.get("repeat", -1)) for row in repeats}
        action_determined = all(
            bool(row.get("trial_completed_for_action", row["arm"] == "Q0"))
            for row in repeats
        )
        output[key] = {
            "determined": (
                len(complete) == 3 and len(repeats) == 3 and
                action_determined and repeat_coverage == {0, 1, 2}
            ),
            "wall": statistics.median(float(row["wall_seconds"]) for row in complete)
            if len(complete) == 3 else None,
            "instance_hash": str(repeats[0]["instance_hash"]),
            "redlines": sorted({value for row in repeats
                                for value in row.get("correctness_redlines", ())}),
            "censor": any(bool(row.get("resource_censor")) for row in repeats),
        }
    return output


def _metrics(rows, scale, k, gates=None):
    gates = dict(gates or {})
    continue_ratio = float(gates.get("continue_oracle_ratio_below", 1.0))
    adverse_ratio = float(gates.get("adverse_ratio_at_least", 1.05))
    strong_ratio = float(gates.get("strong_benefit_ratio_at_most", 0.95))
    collapsed = _collapsed(rows)
    contexts = sorted({key[0] for key in collapsed if key[1:3] == (scale, k)})
    by_instance = defaultdict(list)
    redlines = set()
    censor = 0
    for context in contexts:
        arms = {arm: collapsed.get((context, scale, k, arm))
                for arm in ("Q0", "CONTINUE_QD1", "MIGRATE_BACK_TO_Q0")}
        for row in arms.values():
            if row:
                redlines.update(row["redlines"])
                censor += int(row["censor"])
        if any(not row or not row["determined"] for row in arms.values()):
            continue
        q0 = float(arms["Q0"]["wall"])
        cont = float(arms["CONTINUE_QD1"]["wall"])
        revert = float(arms["MIGRATE_BACK_TO_Q0"]["wall"])
        by_instance[arms["Q0"]["instance_hash"]].append({
            "continue": cont / q0,
            "revert": revert / q0,
            "continue_vs_revert": cont / revert,
            "oracle": min(cont, revert) / q0,
        })
    instances = []
    for instance_hash, values in by_instance.items():
        instances.append({
            "instance_hash": instance_hash,
            **{name: _gm(row[name] for row in values)
               for name in ("continue", "revert", "continue_vs_revert", "oracle")},
        })
    return {
        "scale": scale, "k": k, "determined_instances": len(instances),
        "oracle_gm": _gm(row["oracle"] for row in instances) if instances else None,
        "revert_gm": _gm(row["revert"] for row in instances) if instances else None,
        "revert_worst": max((row["revert"] for row in instances), default=None),
        "continue_instances": sum(
            row["continue_vs_revert"] < continue_ratio for row in instances
        ),
        "revert_instances": sum(
            row["continue_vs_revert"] >= continue_ratio for row in instances
        ),
        "adverse_instances": sum(
            row["continue_vs_revert"] >= adverse_ratio for row in instances
        ),
        # Strong benefit is evidence for the CONTINUE action itself, not for
        # an oracle that could obtain its gain from the REVERT arm.
        "strong_benefit_instances": sum(
            row["continue_vs_revert"] <= strong_ratio for row in instances
        ),
        "correctness_redlines": sorted(redlines), "resource_censor_count": censor,
        "instances": instances,
    }


def _passes(metric, gates):
    common = (
        metric["determined_instances"] >= gates["minimum_determined_instances"]
        and metric["oracle_gm"] is not None
        and metric["oracle_gm"] <= gates["oracle_gm_at_most"]
        and metric["revert_gm"] <= gates["trial_revert_gm_at_most"]
        and metric["revert_worst"] <= gates["trial_revert_worst_at_most"]
        and len(metric["correctness_redlines"]) <= gates["correctness_redline_max"]
        and metric["resource_censor_count"] <= gates["resource_censor_max"]
    )
    if metric["scale"] == 30:
        return common and (
            metric["continue_instances"] >= gates["scale30_minimum_continue_instances"]
            and metric["revert_instances"] >=
                gates["scale30_minimum_revert_or_adverse_instances"]
        )
    return common and (
        metric["continue_instances"] >= gates["scale50_minimum_continue_instances"]
        and metric["revert_instances"] >= gates["scale50_minimum_revert_instances"]
        and metric["strong_benefit_instances"] >=
            gates["scale50_minimum_strong_benefit_instances"]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    candidate = json.loads(args.config.read_text(encoding="utf-8"))
    try:
        config, config_freeze = load_frozen_config(
            args.config, run_root=ROOT / candidate["run_root"]
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    outcomes = json.loads(args.outcomes.read_text(encoding="utf-8"))
    source_freeze_path = ROOT / config["run_root"] / "source.freeze.json"
    if not source_freeze_path.is_file():
        raise SystemExit("K selection source freeze is missing")
    source = json.loads(source_freeze_path.read_text(encoding="utf-8"))
    if (
        outcomes.get("partition") != "train"
        or outcomes.get("source_config_freeze_sha256")
            != hashlib.sha256(config_freeze.read_bytes()).hexdigest()
        or outcomes.get("source_freeze_sha256")
            != hashlib.sha256(source_freeze_path.read_bytes()).hexdigest()
        or outcomes.get("native_binary_sha256")
            != source.get("native_binary_sha256")
        or bool(outcomes.get("differential_redlines"))
    ):
        raise SystemExit("K selection accepts bound redline-free train outcomes only")
    metrics = [_metrics(outcomes["rows"], scale, k, config["k_selection_gates"])
               for scale in (30, 50) for k in config["trial_k_candidates"]]
    selected = {}
    for scale in (30, 50):
        passing = [row for row in metrics
                   if row["scale"] == scale and _passes(row, config["k_selection_gates"])]
        if not passing:
            payload = {
                "schema_version": (
                    "lunar_ice_bpc.p0v5_temporal_trial_k_selection.v1"
                ),
                "status": "TERMINATED_NEGATIVE",
                "reason": f"NO_PASSING_TEMPORAL_TRIAL_K_SCALE{scale}",
                "source_outcomes_sha256": hashlib.sha256(
                    args.outcomes.read_bytes()
                ).hexdigest(),
                "source_config_freeze_sha256": hashlib.sha256(
                    config_freeze.read_bytes()
                ).hexdigest(),
                "selected_k_by_scale": {}, "metrics": metrics,
            }
            write_once(args.output, payload)
            mark_terminal_negative(
                ROOT / config["run_root"], stage="K_SELECTION",
                reason=payload["reason"], detail=payload,
            )
            raise SystemExit(f"NO_PASSING_TEMPORAL_TRIAL_K_SCALE{scale}")
        selected[str(scale)] = min(
            passing, key=lambda row: (row["oracle_gm"], row["k"])
        )["k"]
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_trial_k_selection.v1",
        "status": "FIXED_BEFORE_CALIBRATION_AND_HELDOUT",
        "source_outcomes_sha256": hashlib.sha256(
            args.outcomes.read_bytes()
        ).hexdigest(),
        "source_config_freeze_sha256": hashlib.sha256(
            config_freeze.read_bytes()
        ).hexdigest(),
        "selected_k_by_scale": selected,
        "metrics": metrics,
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output.exists() and args.output.read_text(encoding="utf-8") != encoded:
        raise SystemExit("immutable K selection drift")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not args.output.exists():
        args.output.write_text(encoded, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
