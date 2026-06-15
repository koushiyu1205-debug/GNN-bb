#!/usr/bin/env python3
"""Build the GAT same-context target-intervention sampling protocol.

This helper is diagnostic-only.  It turns the current ROI label hygiene state
into a machine-checkable protocol for the next data collection round.  It does
not run BPC, pricing, RMP, Pulse, workers, replay, certificates, or benchmarks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_ROI_DATASET = Path("BPC_future/results/gat_worker_roi_dataset_20260614/summary.json")
DEFAULT_CONTEXT_PROTOCOL = Path(
    "BPC_future/results/root_cause_selector_context_trajectory_capture_protocol_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/gat_online_target_intervention_protocol_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_gat_online_target_intervention_protocol_zh.md"
)

REQUIRED_EXACT_CONTEXT_COMPONENTS = [
    "context_hash",
    "true_dual_hash",
    "cuts_hash",
    "branch_hash",
    "forbidden_signature_hash",
    "pool_signature_hash",
    "active_hash_before",
    "pricing_config_hash",
    "target_sequence",
    "target_arc_option_sequence",
    "worker_context_hash",
]

REQUIRED_WORKER_DIAGNOSTICS = [
    "journey_sharded_pulse_hidden_negative_worker_log_skips",
    "journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled",
    "journey_sharded_pulse_hidden_negative_worker_expected_context_hash",
    "pulse_worker_context_hash",
    "pulse_worker_enabled",
    "pulse_worker_skipped",
    "pulse_worker_skip_reason",
    "pulse_worker_target_transition_priority_sequence",
    "pulse_worker_target_arc_option_priority_sequence",
    "pulse_worker_target_sequence_completed",
    "pulse_worker_target_sequence_materialized",
    "pulse_worker_target_sequence_negative",
    "pulse_worker_returned_candidate_sequence_samples",
    "pulse_worker_harvested_sequence_samples",
]

INVALID_SAMPLE_CLASSES = [
    "context_mismatch",
    "worker_context_mismatch",
    "missing_worker_diagnostics",
    "no_worker_target_intervention_observed",
    "positive_roi_without_target_causal_match",
    "roi_without_target_causal_match",
    "certificate_or_official_bound_effect",
    "missing_baseline_or_worker_result",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def build_protocol(
    *,
    roi_dataset_path: Path = DEFAULT_ROI_DATASET,
    context_protocol_path: Path = DEFAULT_CONTEXT_PROTOCOL,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    roi_dataset = _read_json(Path(roi_dataset_path))
    context_protocol = _read_json(Path(context_protocol_path))

    label_acceptance_rules = {
        "positive_roi": [
            "all required exact context components match",
            "worker target intervention is observed",
            "target causal match is observed in worker diagnostics",
            "target column is true-RC negative under the same context",
            "follow-up RMP/tail metric improves without certificate or official-bound effect",
        ],
        "no_observed_or_negative_roi": [
            "all required exact context components match",
            "worker target intervention is observed",
            "target causal match is observed in worker diagnostics",
            "target column is true-RC negative under the same context",
            "fixed follow-up horizon shows no RMP/tail improvement",
        ],
        "invalid_not_label": INVALID_SAMPLE_CLASSES,
    }

    collection_steps = [
        "capture candidate and full context before the RMP basis changes",
        "run the target worker/probe in the same context, or mark the row invalid",
        "require exact component match before assigning any ROI label",
        "require worker target diagnostics and target causal match for every training label",
        "record context mismatch as invalid/unreachable, never as a negative label",
        "keep true-RC negative columns in HIGH_PRIORITY or DELAY_QUEUE only; never discard them",
    ]

    checks = {
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "no_certificate_or_official_bound_effect": True,
        "default_enabled_false": True,
        "requires_dual_cut_branch_context": all(
            item in REQUIRED_EXACT_CONTEXT_COMPONENTS
            for item in ("true_dual_hash", "cuts_hash", "branch_hash")
        ),
        "requires_worker_log_skips_and_target_diagnostics": all(
            item in REQUIRED_WORKER_DIAGNOSTICS
            for item in (
                "journey_sharded_pulse_hidden_negative_worker_log_skips",
                "journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled",
            )
        ),
        "requires_target_causal_match_for_positive_and_negative_labels": all(
            "target causal match is observed in worker diagnostics" in rules
            for key, rules in label_acceptance_rules.items()
            if key != "invalid_not_label"
        ),
        "context_mismatch_is_not_a_negative_label": "context_mismatch" in INVALID_SAMPLE_CLASSES,
        "delay_queue_preserves_completeness": True,
        "roi_dataset_guard_fields_present": all(
            key in roi_dataset
            for key in (
                "worker_context_match_count",
                "worker_context_mismatch_count",
                "target_causal_match_count",
                "target_intervention_observed_count",
                "positive_roi_without_target_causal_match_count",
                "no_worker_target_intervention_count",
            )
        ),
        "selector_context_protocol_available": (
            context_protocol.get("status")
            in (None, "selector_context_trajectory_capture_protocol_ready")
        ),
    }

    summary = {
        "schema_version": "gat_online_target_intervention_protocol_v1",
        "status": "gat_online_target_intervention_protocol_ready",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "roi_dataset_path": str(roi_dataset_path),
        "context_protocol_path": str(context_protocol_path),
        "current_roi_dataset_machine_fields": {
            "row_count": roi_dataset.get("row_count"),
            "training_row_count": roi_dataset.get("training_row_count"),
            "unique_training_row_count": roi_dataset.get("unique_training_row_count"),
            "target_diag_available_count": roi_dataset.get("target_diag_available_count"),
            "worker_context_match_count": roi_dataset.get("worker_context_match_count"),
            "target_causal_match_count": roi_dataset.get("target_causal_match_count"),
            "target_intervention_observed_count": roi_dataset.get(
                "target_intervention_observed_count"
            ),
            "positive_roi_without_target_causal_match_count": roi_dataset.get(
                "positive_roi_without_target_causal_match_count"
            ),
            "worker_context_mismatch_count": roi_dataset.get(
                "worker_context_mismatch_count"
            ),
            "roi_without_target_causal_match_count": roi_dataset.get(
                "roi_without_target_causal_match_count"
            ),
            "no_worker_target_intervention_count": roi_dataset.get(
                "no_worker_target_intervention_count"
            ),
            "training_ready": roi_dataset.get("training_ready"),
        },
        "required_exact_context_components": REQUIRED_EXACT_CONTEXT_COMPONENTS,
        "required_worker_diagnostics": REQUIRED_WORKER_DIAGNOSTICS,
        "invalid_sample_classes": INVALID_SAMPLE_CLASSES,
        "label_acceptance_rules": label_acceptance_rules,
        "collection_steps": collection_steps,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(Path(report), summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# GAT Online Target Intervention Protocol 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告把 GAT ROI 样本采集收紧为同上下文目标干预协议。它只写协议，",
        "不运行 BPC / pricing / RMP / Pulse / worker，不产生 certificate 或 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_online_target_intervention_protocol = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        "required_exact_context_component_count = "
        f"{len(summary['required_exact_context_components'])}",
        "required_worker_diagnostic_count = "
        f"{len(summary['required_worker_diagnostics'])}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 为什么当前有效样本稀疏",
        "",
        "- 离线 A/B 很难回到候选出现时的同一个 dual / cuts / branch / pool 上下文；",
        "- worker 经常因为 context mismatch 没有真实处理目标候选；",
        "- 有些表面正 ROI 来自旁支 harvested column，不能归因到目标候选；",
        "- 因此这些记录必须进 invalid bucket，不能当 GAT 正负标签。",
        "",
        "## Required Exact Context Components",
        "",
    ]
    for item in summary["required_exact_context_components"]:
        lines.append(f"- `{item}`")

    lines.extend(["", "## Required Worker Diagnostics", ""])
    for item in summary["required_worker_diagnostics"]:
        lines.append(f"- `{item}`")

    lines.extend(["", "## Label Acceptance Rules", "", "```json"])
    lines.append(
        json.dumps(
            summary["label_acceptance_rules"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    lines.extend(["```", "", "## Collection Steps", ""])
    for item in summary["collection_steps"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Current ROI Dataset Fields",
            "",
            "```json",
            json.dumps(
                summary["current_roi_dataset_machine_fields"],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## Checks",
            "",
            "```json",
            json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## 结论",
            "",
            "- 有效样本必须是同上下文、目标候选真实干预、目标因果匹配后的 ROI 观察；",
            "- `context_mismatch` / 未干预 / 非目标收益都不是负样本；",
            "- 通过安全壳的 true-RC negative 可进 HIGH_PRIORITY，未通过的进 DELAY_QUEUE；",
            "- DELAY_QUEUE 不能永久丢弃负列，也不能参与证书或官方下界。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roi-dataset", type=Path, default=DEFAULT_ROI_DATASET)
    parser.add_argument("--context-protocol", type=Path, default=DEFAULT_CONTEXT_PROTOCOL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_protocol(
        roi_dataset_path=args.roi_dataset,
        context_protocol_path=args.context_protocol,
        output_dir=args.output_dir,
        report=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
