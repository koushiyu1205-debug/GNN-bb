#!/usr/bin/env python3
"""Correct the V10 instance-folding audit without rewriting V10 evidence.

V10's frozen analyzer expanded ``metadata`` in ``collapse_matched_blocks`` and
then attempted to read a nested ``metadata`` object.  Consequently every
collapsed ``instance_hash`` was ``null`` and the instance-coverage gate was
evaluated as one instance.  This script binds the immutable V10 artifacts,
restores identity from the pre-outcome corpus freeze, and reapplies the exact
same gates.  It never launches a pricing task or writes into the V10 run root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = (
    ROOT / "runs/p0v5_temporal_frontier_late_switch_oracle_v10_20260818"
)
DEFAULT_AUDIT_ROOT = (
    ROOT / "runs/p0v5_temporal_frontier_late_switch_oracle_v10r1_audit_20260818"
)

SOURCE_FILES = (
    "bootstrap.freeze.registry.json",
    "config.freeze.json",
    "late_switch.execution.freeze.json",
    "late_switch.rows.json",
    "late_switch.collapsed.json",
    "late_switch_oracle.decision.json",
    "native_differential.import.freeze.json",
    "native_differential.report.json",
    "performance.freeze.registry.json",
    "pilot_corpus.freeze.json",
    "research_contract.freeze.json",
    "source.freeze.json",
    "state.json",
    "terminal_decision.json",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def geometric_mean(values: Iterable[float]) -> float:
    materialized = [float(value) for value in values]
    if not materialized or any(value <= 0.0 for value in materialized):
        raise ValueError("geometric mean requires positive non-empty values")
    return math.exp(sum(math.log(value) for value in materialized) / len(materialized))


def restore_instance_identity(
    collapsed_rows: list[dict], corpus_rows: list[dict],
) -> list[dict]:
    """Restore immutable instance identity from the pre-outcome corpus."""

    by_context: dict[str, dict] = {}
    for row in corpus_rows:
        context_id = str(row["context_id"])
        if context_id in by_context:
            raise ValueError(f"duplicate corpus context:{context_id}")
        by_context[context_id] = row

    restored = []
    for source in collapsed_rows:
        row = dict(source)
        context_id = str(row["context_id"])
        corpus = by_context.get(context_id)
        if corpus is None:
            raise ValueError(f"collapsed context absent from corpus:{context_id}")
        if int(row["scale"]) != int(corpus["scale"]):
            raise ValueError(f"scale drift:{context_id}")
        frozen_instance = str(corpus["instance_content_hash"])
        existing = row.get("instance_hash")
        if existing not in (None, "", frozen_instance):
            raise ValueError(f"instance identity drift:{context_id}")
        row["instance_hash"] = frozen_instance
        row["instance_identity_source"] = "pilot_corpus.freeze.json"
        restored.append(row)

    expected_contexts = set(by_context)
    observed_contexts = {str(row["context_id"]) for row in restored}
    if observed_contexts != expected_contexts:
        missing = sorted(expected_contexts - observed_contexts)
        extra = sorted(observed_contexts - expected_contexts)
        raise ValueError(f"context universe drift:missing={missing}:extra={extra}")
    return restored


def instance_fold(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        if not row.get("determined"):
            continue
        grouped.setdefault(str(row["instance_hash"]), []).append(row)
    folded = []
    for instance_hash, instance_rows in sorted(grouped.items()):
        folded.append({
            "instance_hash": instance_hash,
            "context_count": len(instance_rows),
            "probe_ratio": geometric_mean(
                float(row["probe_ratio"]) for row in instance_rows
            ),
            "net_ratio": geometric_mean(
                float(row["net_ratio"]) for row in instance_rows
            ),
        })
    return folded


def corrected_metrics(rows: list[dict]) -> dict:
    determined = [row for row in rows if row.get("determined")]
    folded = instance_fold(rows)
    instance_net = [float(row["net_ratio"]) for row in folded]
    instance_probe = [float(row["probe_ratio"]) for row in folded]
    return {
        "contexts": len(rows),
        "determined_contexts": len(determined),
        "determined_instances": len(folded),
        "probe_overhead_gm": (
            geometric_mean(instance_probe) if instance_probe else None
        ),
        "probe_overhead_worst_context_ratio": (
            max(float(row["probe_ratio"]) for row in determined)
            if determined else None
        ),
        "fixed_qpd1_net_gm": (
            geometric_mean(instance_net) if instance_net else None
        ),
        "net_oracle_gm": (
            geometric_mean(min(1.0, value) for value in instance_net)
            if instance_net else None
        ),
        "qpd1_winner_instances": sum(value < 1.0 for value in instance_net),
        "strong_benefit_instances": sum(value <= 0.95 for value in instance_net),
        "benefit_instances": sum(value <= 0.98 for value in instance_net),
        "neutral_or_harm_instances": sum(value > 0.98 for value in instance_net),
        "harm_instances": sum(value >= 1.05 for value in instance_net),
        "resource_censor_contexts": sum(
            bool(row.get("resource_censor_positive")) for row in rows
        ),
        "resource_censor_instances": len({
            str(row["instance_hash"]) for row in rows
            if row.get("resource_censor_positive")
        }),
        "instance_rows": folded,
    }


def boundary_failures(scale: int, metrics: dict, config: dict) -> list[str]:
    failures = []
    overhead = config["probe_overhead_gate"]
    if metrics["probe_overhead_gm"] is None:
        failures.append("probe_overhead_missing")
    elif metrics["probe_overhead_gm"] > overhead["gm_at_most"]:
        failures.append("probe_overhead_gm")
    if metrics["probe_overhead_worst_context_ratio"] is None:
        failures.append("probe_overhead_worst_missing")
    elif (
        metrics["probe_overhead_worst_context_ratio"]
        > overhead["worst_ratio_at_most"]
    ):
        failures.append("probe_overhead_worst")

    gate = config["scale30_gate"] if scale == 30 else config["scale50_boundary_gate"]
    if metrics["determined_instances"] < gate["minimum_determined_instances"]:
        failures.append("minimum_determined_instances")
    if metrics["qpd1_winner_instances"] < gate["minimum_qpd1_winner_instances"]:
        failures.append("minimum_qpd1_winner_instances")
    if metrics["net_oracle_gm"] is None or (
        metrics["net_oracle_gm"] > gate["net_oracle_gm_at_most"]
    ):
        failures.append("net_oracle_gm")
    if metrics["resource_censor_contexts"]:
        failures.append("resource_censor_contexts")
    if scale == 30:
        if metrics["fixed_qpd1_net_gm"] is None or (
            metrics["fixed_qpd1_net_gm"]
            > gate["fixed_qpd1_net_gm_at_most"]
        ):
            failures.append("fixed_qpd1_net_gm")
    else:
        if (
            metrics["strong_benefit_instances"]
            < gate["minimum_strong_benefit_instances"]
        ):
            failures.append("minimum_strong_benefit_instances")
        if (
            metrics["neutral_or_harm_instances"]
            < gate["minimum_neutral_or_harm_instances"]
        ):
            failures.append("minimum_neutral_or_harm_instances")
    return failures


def corrected_gate(config: dict, rows: list[dict]) -> dict:
    metrics_by_scale: dict[str, dict[str, dict]] = {"30": {}, "50": {}}
    passing: dict[str, list[int]] = {"30": [], "50": []}
    failed_conditions: dict[str, dict[str, list[str]]] = {"30": {}, "50": {}}
    for scale in (30, 50):
        for boundary in config["decision_boundaries"][str(scale)]:
            subset = [
                row for row in rows
                if int(row["scale"]) == scale
                and int(row["decision_boundary"]) == int(boundary)
            ]
            metrics = corrected_metrics(subset)
            failures = boundary_failures(scale, metrics, config)
            metrics_by_scale[str(scale)][str(boundary)] = metrics
            failed_conditions[str(scale)][str(boundary)] = failures
            if not failures:
                passing[str(scale)].append(int(boundary))

    selected_scale50 = None
    if passing["50"]:
        selected_scale50 = min(
            passing["50"],
            key=lambda boundary: (
                metrics_by_scale["50"][str(boundary)]["net_oracle_gm"],
                boundary,
            ),
        )

    decision = "PASS" if passing["30"] and passing["50"] else "FAIL"
    if decision == "PASS":
        reason = "LATE_SWITCH_ORACLE_GATE_PASSED"
    elif passing["30"] and any(
        metrics_by_scale["50"][str(boundary)]["net_oracle_gm"]
        <= config["scale50_boundary_gate"]["net_oracle_gm_at_most"]
        for boundary in config["decision_boundaries"]["50"]
    ):
        reason = "SCALE50_LATE_SWITCH_SUPPORT_GATE_FAILED"
    elif not passing["30"]:
        reason = "SCALE30_QD1_GATE_FAILED"
    else:
        reason = "SCALE50_LATE_SWITCH_ORACLE_HEADROOM_FAILED"

    return {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_oracle_audit.v10r1"
        ),
        "decision": decision,
        "reason": reason,
        "boundary_metrics": metrics_by_scale,
        "failed_conditions": failed_conditions,
        "passing_boundaries": passing,
        "selected_scale30_boundary": 4096 if 4096 in passing["30"] else None,
        "selected_scale50_boundary": selected_scale50,
        "temporal_gat_training_authorized": decision == "PASS",
        "heldout_e2e_formal_authorized": False,
        "correctness_redline_count": sum(
            len(row.get("correctness_redlines") or ()) for row in rows
        ),
    }


def write_once(path: Path, payload: dict) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite:{path}")
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_audit(source_root: Path, audit_root: Path) -> dict:
    source_root = source_root.resolve()
    audit_root = audit_root.resolve()
    if audit_root == source_root or source_root in audit_root.parents:
        raise ValueError("audit root must be independent from V10 source root")
    if audit_root.exists():
        raise FileExistsError(f"audit root already exists:{audit_root}")

    missing = [name for name in SOURCE_FILES if not (source_root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"missing V10 source artifacts:{missing}")
    terminal = load(source_root / "terminal_decision.json")
    state = load(source_root / "state.json")
    if not (
        terminal.get("decision") == "FAIL"
        and terminal.get("reason") == "NO_SCALE50_LATE_SWITCH_ORACLE_HEADROOM"
        and state.get("terminal") is True
    ):
        raise ValueError("unexpected V10 terminal contract")

    source_hashes = {name: sha256(source_root / name) for name in SOURCE_FILES}
    config = load(source_root / "config.freeze.json")
    corpus = load(source_root / "pilot_corpus.freeze.json")
    execution = load(source_root / "late_switch.execution.freeze.json")
    collapsed = load(source_root / "late_switch.collapsed.json")
    if int(execution.get("task_count") or 0) != 240:
        raise ValueError("unexpected V10 task count")
    if len(collapsed.get("rows") or ()) != 32:
        raise ValueError("unexpected V10 collapsed row count")

    restored = restore_instance_identity(
        list(collapsed["rows"]), list(corpus["rows"]),
    )
    decision = corrected_gate(config, restored)
    if decision["correctness_redline_count"]:
        raise ValueError("corrected audit found correctness redline")

    audit_root.mkdir(parents=True)
    import_freeze = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_v10_import.v10r1"
        ),
        "source_run_root": str(source_root),
        "source_artifact_sha256": source_hashes,
        "source_terminal_immutable": True,
        "source_wall_outcomes_reused_without_modification": True,
        "new_wall_outcomes_generated": 0,
        "analyzer_bug": {
            "kind": "expanded_metadata_read_as_nested_metadata",
            "symptom": "all_collapsed_instance_hash_values_were_null",
            "affected_original_metric": "determined_instances",
            "gate_thresholds_changed": False,
        },
    }
    corrected_rows = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_collapsed.v10r1"
        ),
        "rows": restored,
    }
    audit_terminal = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_audit_terminal.v10r1"
        ),
        "decision": decision["decision"],
        "reason": decision["reason"],
        "stage": "POST_TERMINAL_ANALYZER_CORRECTION_AUDIT",
        "development_only": True,
        "diagnostic_only": True,
        "candidate_trained": False,
        "temporal_gat_training_authorized": bool(
            decision["temporal_gat_training_authorized"]
        ),
        "heldout_e2e_formal_authorized": False,
        "deployment_authorized": False,
        "production_switch_authorized": False,
        "v10_source_terminal_rewritten": False,
        "detail": decision,
    }
    audit_state = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_audit_state.v10r1"
        ),
        "current_stage": "TERMINAL",
        "status": decision["decision"],
        "terminal": True,
        "terminal_reason": decision["reason"],
        "candidate_trained": False,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }

    write_once(audit_root / "v10_source_import.freeze.json", import_freeze)
    write_once(audit_root / "corrected_collapsed.json", corrected_rows)
    write_once(audit_root / "corrected_oracle.decision.json", decision)
    write_once(audit_root / "terminal_decision.json", audit_terminal)
    write_once(audit_root / "state.json", audit_state)

    after_hashes = {name: sha256(source_root / name) for name in SOURCE_FILES}
    if after_hashes != source_hashes:
        raise RuntimeError("V10 source artifact changed during read-only audit")
    return decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--audit-root", type=Path, default=DEFAULT_AUDIT_ROOT)
    args = parser.parse_args()
    print(json.dumps(
        run_audit(args.source_root, args.audit_root),
        ensure_ascii=False, indent=2, sort_keys=True,
    ))


if __name__ == "__main__":
    main()
