#!/usr/bin/env python3
"""Audit development or sealed-final full-BPC Temporal-GAT outcomes."""

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
    load_frozen_config, mark_terminal_negative,
)


def _gm(values):
    values = [float(value) for value in values]
    return exp(sum(log(value) for value in values) / len(values))


def audit(rows, gates, stage, *, expected_instances_per_scale,
          effective_native_memory_limit_gb):
    grouped = defaultdict(list)
    redlines = set()
    resource_censors = 0
    for row in rows:
        grouped[(int(row["scale"]), row["instance_hash"], row["arm"])].append(row)
        redlines.update(row.get("correctness_redlines") or ())
        if (
            "route_rc_reaudit_pass" in row
            and not bool(row.get("route_rc_reaudit_pass"))
        ):
            redlines.add(
                "route_reduced_cost_reaudit_failed:"
                f"{row['scale']}:{row['instance_hash']}:{row['arm']}"
            )
        resource_censors += int(bool(row.get("resource_censor")))
    collapsed = {}
    for key, values in grouped.items():
        complete = [row for row in values if row.get("status") == "COMPLETE"]
        repeats = {int(row.get("repeat", -1)) for row in values}
        if repeats != {0, 1, 2}:
            redlines.add("blocked_repeat_coverage_mismatch:" + ":".join(
                map(str, key)
            ))
        if any(float(row.get("peak_rss_gb") or 0.0) <= 0.0 for row in values):
            redlines.add("peak_rss_telemetry_missing:" + ":".join(
                map(str, key)
            ))
        collapsed[key] = {
            "determined": len(values) == 3 and len(complete) == 3,
            "wall": statistics.median(float(row["wall_seconds"]) for row in complete)
                if len(complete) == 3 else None,
            "rss": max((float(row.get("peak_rss_gb") or 0.0) for row in values),
                       default=0.0),
            "signatures": {str(row.get("exact_semantics_signature") or "")
                           for row in complete},
            "objectives": [float(row["objective"]) for row in complete
                           if row.get("objective") is not None],
            "graph_wall": statistics.median(
                float(row.get("graph_wall_seconds") or 0.0)
                for row in complete
            ) if len(complete) == 3 else None,
        }
    metrics = {}
    failures = []
    for scale in (30, 50):
        instances = sorted({key[1] for key in collapsed if key[0] == scale})
        if len(instances) != int(expected_instances_per_scale):
            failures.append(f"scale{scale}:instance_count_mismatch")
        for instance in instances:
            if {
                key[2] for key in collapsed
                if key[0] == scale and key[1] == instance
            } != {"Q0", "MODEL", "ALWAYS_CONTINUE", "BEST_CONTROL"}:
                failures.append(f"scale{scale}:arm_coverage_mismatch:{instance}")
        ratios = []
        harm = []
        always = []
        best_control = []
        rss = []
        probe_overhead = []
        for instance in instances:
            arms = {
                arm: collapsed.get((scale, instance, arm))
                for arm in (
                    "Q0", "MODEL", "ALWAYS_CONTINUE", "BEST_CONTROL"
                )
            }
            if any(not row or not row["determined"] for row in arms.values()):
                continue
            q0 = arms["Q0"]
            model = arms["MODEL"]
            signatures = set().union(*(
                row["signatures"] for row in arms.values()
            ))
            if len(signatures) != 1 or "" in signatures:
                redlines.add(f"exact_semantics_mismatch:{scale}:{instance}")
            objectives = [
                value for row in arms.values() for value in row["objectives"]
            ]
            if len(objectives) != 12 or max(objectives) - min(objectives) > 2.0e-6:
                redlines.add(f"exact_objective_mismatch:{scale}:{instance}")
            ratio = model["wall"] / q0["wall"]
            ratios.append(ratio)
            if ratio >= float(gates["harm_ratio"]):
                harm.append(instance)
            rss.append(model["rss"] / max(1e-12, q0["rss"]))
            probe_overhead.append(
                1.0 + float(model["graph_wall"] or 0.0) /
                max(1.0e-12, float(q0["wall"]))
            )
            always.append(model["wall"] / arms["ALWAYS_CONTINUE"]["wall"])
            best_control.append(model["wall"] / arms["BEST_CONTROL"]["wall"])
        metrics[str(scale)] = {
            "determined_instances": len(ratios),
            "q0_ratio_gm": _gm(ratios) if ratios else None,
            "harmful_instances": harm,
            "peak_rss_ratio_worst": max(rss) if rss else None,
            "always_continue_ratio_gm": _gm(always) if always else None,
            "best_control_ratio_gm": (
                _gm(best_control) if best_control else None
            ),
            "probe_graph_overhead_gm": (
                _gm(probe_overhead) if probe_overhead else None
            ),
            "probe_graph_overhead_worst": (
                max(probe_overhead) if probe_overhead else None
            ),
        }
        metric = metrics[str(scale)]
        if metric["q0_ratio_gm"] is None or metric["q0_ratio_gm"] > float(
            gates["per_scale_gm_at_most"]
        ):
            failures.append(f"scale{scale}:q0_incremental_speed_gate")
        if harm:
            failures.append(f"scale{scale}:harmful_instance")
        if metric["peak_rss_ratio_worst"] is None or metric[
            "peak_rss_ratio_worst"
        ] > float(gates["peak_rss_ratio_at_most"]):
            failures.append(f"scale{scale}:peak_rss_gate")
        peak_values = [
            float(row.get("peak_rss_gb") or 0.0) for row in rows
            if int(row["scale"]) == scale
        ]
        if not peak_values or max(peak_values) > float(
            effective_native_memory_limit_gb
        ):
            failures.append(f"scale{scale}:dynamic_memory_cap_gate")
        if scale == 30 and (
            metric["always_continue_ratio_gm"] is None or
            metric["always_continue_ratio_gm"] > float(
                gates["scale30_always_continue_regression_at_most"]
            )
        ):
            failures.append("scale30:always_continue_gate")
        if scale == 50 and (
            metric["best_control_ratio_gm"] is None or
            metric["best_control_ratio_gm"] > float(
                gates["scale50_best_control_ratio_at_most"]
            )
        ):
            failures.append("scale50:best_simple_gate")
    model_rows = [row for row in rows if row["arm"] == "MODEL"]
    inference = sorted(
        float(value) for row in model_rows
        for value in (
            row.get("inference_ms_values")
            or [row.get("inference_ms") or 0.0]
        )
    )
    p99 = inference[min(len(inference) - 1, int(0.99 * len(inference)))] if inference else None
    overhead = [
        value for scale in (30, 50)
        for value in (
            metrics[str(scale)]["probe_graph_overhead_gm"],
        ) if value is not None
    ]
    overhead_worst = max((
        float(metrics[str(scale)]["probe_graph_overhead_worst"])
        for scale in (30, 50)
        if metrics[str(scale)]["probe_graph_overhead_worst"] is not None
    ), default=None)
    if p99 is None or p99 > float(gates["inference_p99_ms_at_most"]):
        failures.append("portable_inference_p99_gate")
    if not overhead or _gm(overhead) > float(gates["probe_overhead_gm_at_most"]) or (
        overhead_worst is None or
        overhead_worst > float(gates["probe_overhead_worst_at_most"])
    ):
        failures.append("probe_graph_overhead_gate")
    if redlines:
        failures.append("correctness_redline")
    if resource_censors:
        failures.append("resource_censor")
    return {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_gat_e2e_audit.v1",
        "stage": stage, "decision": "FAIL" if failures else "PASS",
        "terminal_negative": bool(failures), "failures": failures,
        "correctness_redlines": sorted(redlines),
        "resource_censor_count": resource_censors,
        "inference_p99_ms": p99,
        "probe_overhead_gm": _gm(overhead) if overhead else None,
        "probe_overhead_worst": overhead_worst,
        "metrics_by_scale": metrics,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--stage", choices=("development_e2e", "sealed_final"),
                        required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    candidate = json.loads(args.config.read_text(encoding="utf-8"))
    try:
        config, config_freeze = load_frozen_config(
            args.config, run_root=ROOT / candidate["run_root"]
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    run_root = (ROOT / config["run_root"]).resolve()
    expected_outcomes = run_root / "full_bpc" / args.stage / "outcomes.json"
    expected_output = run_root / "full_bpc" / args.stage / "audit.json"
    if (
        args.outcomes.resolve() != expected_outcomes
        or args.output.resolve() != expected_output
    ):
        raise SystemExit("E2E evidence must use canonical immutable paths")
    outcomes = json.loads(args.outcomes.read_text(encoding="utf-8"))
    if outcomes.get("partition") != args.stage:
        raise SystemExit("E2E partition/stage mismatch")
    execution_path = Path(str(outcomes.get("execution_freeze") or ""))
    if (
        not execution_path.is_file()
        or hashlib.sha256(execution_path.read_bytes()).hexdigest()
            != str(outcomes.get("execution_freeze_sha256") or "")
    ):
        raise SystemExit("E2E execution freeze binding drift")
    execution = json.loads(execution_path.read_text(encoding="utf-8"))
    if (
        execution.get("partition") != args.stage
        or execution.get("source_config_freeze_sha256")
            != hashlib.sha256(config_freeze.read_bytes()).hexdigest()
        or int(outcomes.get("row_count", -1))
            != int(execution.get("task_count", -2))
    ):
        raise SystemExit("E2E outcome/execution/config binding drift")
    for row in outcomes.get("rows") or ():
        resource_path = Path(str(
            row.get("process_resource_telemetry") or ""
        ))
        if (
            not resource_path.is_file()
            or hashlib.sha256(resource_path.read_bytes()).hexdigest()
                != str(row.get("process_resource_telemetry_sha256") or "")
            or int(row.get("process_tree_rss_sample_count") or 0) <= 0
            or float(row.get("process_tree_peak_rss_gb") or 0.0) <= 0.0
        ):
            raise SystemExit("E2E process-resource telemetry binding drift")
    payload = audit(
        outcomes["rows"], config["development_gates"], args.stage,
        expected_instances_per_scale=int(
            config["split_counts_by_scale"][args.stage]
        ),
        effective_native_memory_limit_gb=float(
            config["execution"]["effective_native_memory_limit_gb"]
        ),
    )
    payload["source_outcomes"] = str(args.outcomes.resolve())
    payload["source_outcomes_sha256"] = hashlib.sha256(
        args.outcomes.read_bytes()
    ).hexdigest()
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output.exists() and args.output.read_text(encoding="utf-8") != encoded:
        raise SystemExit("immutable E2E audit drift")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not args.output.exists():
        args.output.write_text(encoded, encoding="utf-8")
    if payload["decision"] != "PASS":
        mark_terminal_negative(
            ROOT / config["run_root"], stage=args.stage.upper(),
            reason=f"{args.stage}_GATE_FAILED", detail=payload,
        )
        raise SystemExit(f"{args.stage} TERMINATED_NEGATIVE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
