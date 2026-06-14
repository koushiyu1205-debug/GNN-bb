#!/usr/bin/env python3
"""Extract target-priority worker candidates from GAT kNN/OOD decisions.

This is a bridge from the offline GAT safety shell to explicit opt-in worker
A/B runs.  It is read-only: it consumes decision records, a validation dataset
manifest, and capture JSONL logs; it never runs BPC, pricing, RMP, workers, or
certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from typing import Any


DEFAULT_DECISION_RECORDS = Path(
    "BPC_future/results/gat_embedding_knn_ood_sector_wave_capture_validation_20260614/"
    "gat_embedding_external_validation/decision_records.jsonl"
)
DEFAULT_VALIDATION_MANIFEST = Path(
    "BPC_future/results/gat_embedding_knn_ood_sector_wave_capture_validation_20260614/"
    "gat_validation_dataset/manifest.json"
)
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_target_priority_candidates_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_gat_target_priority_candidates_zh.md"
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _capture_events_by_context(path: Path) -> dict[str, dict[str, Any]]:
    events: dict[str, dict[str, Any]] = {}
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            event = json.loads(text)
            if event.get("event") != "journey_counterfactual_replay_capture":
                continue
            context_hash = str(event.get("context_hash") or "")
            if context_hash:
                events[context_hash] = event
    return events


def _true_reduced_cost(journey: dict[str, Any]) -> float | None:
    for key in ("true_reduced_cost", "reduced_cost", "manual_true_reduced_cost"):
        value = journey.get(key)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _first_sortie_target(journey: dict[str, Any]) -> tuple[tuple[int, ...], tuple[str, ...]]:
    signature = journey.get("signature")
    if isinstance(signature, list) and signature:
        first = signature[0]
        if isinstance(first, (list, tuple)) and len(first) >= 2:
            sequence = tuple(int(task) for task in (first[0] or []))
            arcs = tuple(str(arc) for arc in (first[1] or []))
            if sequence and arcs:
                return sequence, arcs
    sequence_payload = journey.get("sequence")
    if isinstance(sequence_payload, list) and sequence_payload:
        sequence = tuple(int(task) for task in (sequence_payload[0] or []))
        trips = journey.get("trips")
        if isinstance(trips, list) and trips:
            arcs = tuple(str(arc) for arc in (trips[0].get("arc_option_ids") or []))
            if sequence and arcs:
                return sequence, arcs
    return tuple(), tuple()


def _safe_name(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")
    return text[:160] or "candidate"


def _best_negative_journey(event: dict[str, Any]) -> dict[str, Any] | None:
    negatives: list[tuple[float, dict[str, Any]]] = []
    for journey in event.get("returned_journeys") or []:
        if not isinstance(journey, dict):
            continue
        true_rc = _true_reduced_cost(journey)
        if true_rc is None or true_rc >= 0.0:
            continue
        sequence, arcs = _first_sortie_target(journey)
        if not sequence or not arcs:
            continue
        negatives.append((true_rc, journey))
    if not negatives:
        return None
    negatives.sort(key=lambda item: item[0])
    return negatives[0][1]


def extract_candidates(
    *,
    decision_records_path: Path = DEFAULT_DECISION_RECORDS,
    validation_manifest: Path = DEFAULT_VALIDATION_MANIFEST,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    max_candidates: int = 8,
    min_probability: float = 0.0,
    decision_name: str = "HIGH_PRIORITY",
) -> dict[str, Any]:
    decisions = _read_jsonl(Path(decision_records_path))
    manifest = json.loads(Path(validation_manifest).read_text(encoding="utf-8"))
    samples = list(manifest.get("samples") or [])
    capture_cache: dict[str, dict[str, dict[str, Any]]] = {}
    skipped: Counter[str] = Counter()
    candidates: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, tuple[int, ...], tuple[str, ...]]] = set()

    for index, (sample, decision) in enumerate(zip(samples, decisions)):
        if len(candidates) >= int(max_candidates):
            break
        if str(decision.get("decision_name") or "") != str(decision_name):
            skipped["decision_not_selected"] += 1
            continue
        if float(decision.get("probability") or 0.0) < float(min_probability):
            skipped["probability_below_min"] += 1
            continue
        source_file = Path(str(sample.get("source_file") or decision.get("source_file") or ""))
        if not source_file.exists():
            skipped["missing_source_file"] += 1
            continue
        context_hash = str(sample.get("context_hash") or decision.get("context_hash") or "")
        if not context_hash:
            skipped["missing_context_hash"] += 1
            continue
        events = capture_cache.get(str(source_file))
        if events is None:
            events = _capture_events_by_context(source_file)
            capture_cache[str(source_file)] = events
        event = events.get(context_hash)
        if event is None:
            skipped["missing_capture_event"] += 1
            continue
        journey = _best_negative_journey(event)
        if journey is None:
            skipped["no_negative_journey_with_materialized_signature"] += 1
            continue
        sequence, arcs = _first_sortie_target(journey)
        instance_path = str(event.get("instance_path") or "")
        if not instance_path or not Path(instance_path).exists():
            skipped["missing_instance_path"] += 1
            continue
        true_rc = _true_reduced_cost(journey)
        key = (instance_path, context_hash, sequence, arcs)
        if key in seen_keys:
            skipped["duplicate_candidate"] += 1
            continue
        seen_keys.add(key)
        instance_name = str(sample.get("instance") or event.get("instance") or Path(instance_path).stem)
        name = _safe_name(
            f"{instance_name}_{context_hash}_{'_'.join(str(task) for task in sequence)}"
        )
        candidates.append(
            {
                "name": name,
                "instance": instance_path,
                "expected_context_hash": context_hash,
                "target_sequence": list(sequence),
                "target_arc_option_sequence": list(arcs),
                "best_true_reduced_cost": true_rc,
                "decision_name": str(decision.get("decision_name") or ""),
                "decision_probability": float(decision.get("probability") or 0.0),
                "decision_reason": str(decision.get("decision_reason") or ""),
                "source_file": str(source_file),
                "manifest_sample_index": index,
                "manifest_row_index": int(sample.get("row_index", -1)),
                "capture_cg_iter": int(event.get("cg_iter") or -1),
                "capture_returned_journey_count": int(event.get("returned_journey_count") or 0),
                "gate_role": "gat_embedding_knn_ood_safety_shell",
                "worker_role": "explicit_opt_in_target_priority_roi_probe",
                "certificate_effect": False,
            }
        )

    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "no_certificate_effect": True,
        "has_candidate": bool(candidates),
        "all_candidates_high_priority": all(
            item["decision_name"] == str(decision_name) for item in candidates
        ),
        "all_candidates_true_rc_negative": all(
            float(item["best_true_reduced_cost"]) < 0.0 for item in candidates
        ),
        "all_candidate_instances_exist": all(
            Path(str(item["instance"])).exists() for item in candidates
        ),
        "all_candidates_have_arc_targets": all(
            bool(item["target_arc_option_sequence"]) for item in candidates
        ),
    }
    summary = {
        "schema_version": "gat_target_priority_candidates_v1",
        "status": "ready" if candidates else "no_candidates",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "decision_records_path": str(decision_records_path),
        "validation_manifest": str(validation_manifest),
        "decision_count": len(decisions),
        "manifest_sample_count": len(samples),
        "candidate_count": len(candidates),
        "skipped_counts": dict(sorted(skipped.items())),
        "candidates": candidates,
        "output_candidates_json": str(output_dir / "candidates.json"),
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "candidates.json").write_text(
        json.dumps({"candidates": candidates}, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Target-Priority Candidates 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "从 GAT embedding + kNN/OOD 的 HIGH_PRIORITY 决策中抽取 target-priority worker",
        "候选。该脚本只读离线记录，不运行 BPC / pricing / RMP，不启用 worker，不产生",
        "certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_target_priority_candidates = current",
        f"status = {summary['status']}",
        f"candidate_count = {summary['candidate_count']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## Candidates",
        "",
        "```json",
        json.dumps(summary["candidates"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Skipped Counts",
        "",
        "```json",
        json.dumps(summary["skipped_counts"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 边界",
        "",
        "- GAT/kNN/OOD 只决定 target-priority 候选，不是 pricing oracle；",
        "- true-RC negative 不允许永久丢弃；",
        "- 这些候选只能喂给显式 opt-in worker A/B；",
        "- 不能用于 no-negative certificate 或 official lower bound。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-records", type=Path, default=DEFAULT_DECISION_RECORDS)
    parser.add_argument("--validation-manifest", type=Path, default=DEFAULT_VALIDATION_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-candidates", type=int, default=8)
    parser.add_argument("--min-probability", type=float, default=0.0)
    parser.add_argument("--decision-name", default="HIGH_PRIORITY")
    args = parser.parse_args(argv)
    summary = extract_candidates(
        decision_records_path=args.decision_records,
        validation_manifest=args.validation_manifest,
        output_dir=args.output_dir,
        report=args.report,
        max_candidates=int(args.max_candidates),
        min_probability=float(args.min_probability),
        decision_name=str(args.decision_name),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
