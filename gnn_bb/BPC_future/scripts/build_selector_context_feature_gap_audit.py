"""Audit which context proxies still fail for the addition-before selector.

This diagnostic-only script reads existing root-cause summaries and records the
gap between local column features, simple context proxies, and the stronger
context/RMP-trajectory information needed before a production selector can be
claimed.  It does not run BPC, pricing, RMP, Pulse, or benchmarks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_CONTEXT_DISAMBIGUATION = Path(
    "BPC_future/results/root_cause_selector_context_disambiguation_20260613/"
    "summary.json"
)
DEFAULT_CONTEXT_SCALAR_CANDIDATES = Path(
    "BPC_future/results/root_cause_selector_context_scalar_candidates_20260613/"
    "summary.json"
)
DEFAULT_CONTEXT_SCALAR_HOLDOUT = Path(
    "BPC_future/results/root_cause_selector_context_scalar_holdout_20260613/"
    "summary.json"
)
DEFAULT_CONTEXT_FEATURE = Path(
    "BPC_future/results/root_cause_selector_context_feature_anatomy_20260614/"
    "summary.json"
)
DEFAULT_FAILURE_MECHANISM = Path(
    "BPC_future/results/root_cause_selector_failure_mechanism_audit_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_context_feature_gap_audit_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_context_feature_gap_audit_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ladder_entry(summary: dict[str, Any], name: str) -> dict[str, Any]:
    entry = summary.get("ladder", {}).get(name, {})
    return {
        "name": name,
        "fields": entry.get("fields", []),
        "mixed_group_count": int(entry.get("mixed_group_count", 0) or 0),
        "mixed_row_count": int(entry.get("mixed_row_count", 0) or 0),
        "group_count": int(entry.get("group_count", 0) or 0),
    }


def _group_entry(summary: dict[str, Any], name: str) -> dict[str, Any]:
    entry = summary.get("groups", {}).get(name, {})
    return {
        "name": name,
        "mixed_group_count": int(entry.get("mixed_group_count", 0) or 0),
        "mixed_row_count": int(entry.get("mixed_row_count", 0) or 0),
        "group_count": int(entry.get("group_count", 0) or 0),
    }


def _model_holdout_metrics(
    scalar_holdout: dict[str, Any], model_name: str, holdout_name: str
) -> dict[str, Any]:
    holdout = (
        scalar_holdout.get("model_results", {})
        .get(model_name, {})
        .get("holdouts", {})
        .get(holdout_name, {})
    )
    aggregate = holdout.get("aggregate_metrics", {})
    return {
        "passes_strict": holdout.get("passes_strict"),
        "precision": aggregate.get("precision"),
        "recall": aggregate.get("recall"),
        "tp": aggregate.get("tp"),
        "fp": aggregate.get("fp"),
        "fn": aggregate.get("fn"),
        "tn": aggregate.get("tn"),
    }


def build_audit(
    *,
    context_disambiguation_path: Path,
    context_scalar_candidates_path: Path,
    context_scalar_holdout_path: Path,
    context_feature_path: Path,
    failure_mechanism_path: Path,
) -> dict[str, Any]:
    context_disambiguation = _read_json(context_disambiguation_path)
    scalar_candidates = _read_json(context_scalar_candidates_path)
    scalar_holdout = _read_json(context_scalar_holdout_path)
    context_feature = _read_json(context_feature_path)
    failure_mechanism = _read_json(failure_mechanism_path)

    proxy_results = [
        {
            "proxy_id": "local_sequence",
            "status": "insufficient",
            "evidence": _ladder_entry(context_disambiguation, "local_sequence"),
            "reason": "task_set/sequence 相同仍会跨 context 出现 improved/noop 混合。",
        },
        {
            "proxy_id": "online_flags_and_cg_iter",
            "status": "insufficient",
            "evidence": _ladder_entry(
                context_disambiguation, "local_sequence_online_cg_iter"
            ),
            "reason": (
                "加入 new_task_set、replacement/support flags、cg_iter 后仍有混合组。"
            ),
        },
        {
            "proxy_id": "instance_identity",
            "status": "insufficient",
            "evidence": _ladder_entry(
                context_disambiguation, "local_sequence_online_instance"
            ),
            "reason": "同一 instance 内仍存在 high-impact 与 low/noop context。",
        },
        {
            "proxy_id": "dataset_identity",
            "status": "reduces_but_insufficient",
            "evidence": _ladder_entry(
                context_disambiguation, "local_sequence_online_dataset"
            ),
            "reason": "dataset 能减少混合，但不能消除混合，也不能解释同一 dataset 内差异。",
        },
        {
            "proxy_id": "exact_context_hash",
            "status": "diagnostic_only_too_specific",
            "evidence": _ladder_entry(
                context_disambiguation, "local_sequence_online_context_hash"
            ),
            "reason": (
                "context_hash 在当前样本上消除混合，说明根因在 context/RMP 轨迹；"
                "但 hash 是身份特征，不能直接作为可泛化生产 selector。"
            ),
        },
        {
            "proxy_id": "control_objective_bin_100",
            "status": "calibration_signal_not_holdout_stable",
            "evidence": {
                "current_sample_grouping": _group_entry(
                    scalar_candidates, "base_control_objective_bin_100"
                ),
                "context_holdout": _model_holdout_metrics(
                    scalar_holdout, "bin100_majority75", "context_hash"
                ),
                "instance_holdout": _model_holdout_metrics(
                    scalar_holdout, "bin100_majority75", "instance"
                ),
            },
            "reason": (
                "control_objective bin 在当前样本能消除混合，但 holdout recall 失败，"
                "仍只能作为 calibration lead。"
            ),
        },
        {
            "proxy_id": "threshold_context_scalar",
            "status": "calibration_signal_not_holdout_stable",
            "evidence": {
                "context_holdout": _model_holdout_metrics(
                    scalar_holdout, "threshold_context_scalar", "context_hash"
                ),
                "instance_holdout": _model_holdout_metrics(
                    scalar_holdout, "threshold_context_scalar", "instance"
                ),
                "passing_models": scalar_holdout.get("passing_models", []),
            },
            "reason": (
                "简单 scalar 阈值要么高 recall 但低 precision，要么高 precision "
                "但漏 context；没有模型通过全部 holdout。"
            ),
        },
    ]

    required_feature_properties = [
        {
            "property_id": "addition_before_observable",
            "requirement": (
                "必须在加列前可观测；不能用 objective_delta、dual_after、"
                "active_after 或 replay label。"
            ),
        },
        {
            "property_id": "rmp_trajectory_context",
            "requirement": (
                "必须编码当前 RMP / active-basis / dual / pool saturation 轨迹信息，"
                "不能只依赖 task_set、sequence、true_rc 或 new_task_set。"
            ),
        },
        {
            "property_id": "less_specific_than_hash",
            "requirement": (
                "必须比 exact context_hash 更可泛化；hash 可做诊断分层，不能直接"
                "作为生产规则。"
            ),
        },
        {
            "property_id": "stronger_than_scalar_context",
            "requirement": (
                "必须比 control_objective 单 scalar 或粗 bin 更强，因为这些代理"
                "当前样本有信号但 holdout 不稳。"
            ),
        },
        {
            "property_id": "holdout_stable",
            "requirement": (
                "必须同时通过 context、instance、dataset holdout，再进入 5/10 "
                "no-regression 与 selected 20 hard-repeat BPC A/B。"
            ),
        },
    ]

    checks = {
        "sources_pass": all(
            item.get("all_checks_pass") is True
            for item in [
                context_disambiguation,
                scalar_candidates,
                scalar_holdout,
                context_feature,
                failure_mechanism,
            ]
        ),
        "local_sequence_mixed": (
            proxy_results[0]["evidence"]["mixed_group_count"] > 0
        ),
        "online_flags_still_mixed": (
            proxy_results[1]["evidence"]["mixed_group_count"] > 0
        ),
        "instance_still_mixed": (
            proxy_results[2]["evidence"]["mixed_group_count"] > 0
        ),
        "dataset_reduces_but_not_eliminates": (
            proxy_results[3]["evidence"]["mixed_group_count"] > 0
        ),
        "context_hash_disambiguates_current_sample": (
            proxy_results[4]["evidence"]["mixed_group_count"] == 0
        ),
        "control_objective_current_signal": (
            proxy_results[5]["evidence"]["current_sample_grouping"][
                "mixed_group_count"
            ]
            == 0
        ),
        "control_objective_holdout_fails": (
            proxy_results[5]["evidence"]["context_holdout"]["passes_strict"]
            is False
        ),
        "no_scalar_model_passes": not scalar_holdout.get("passing_models"),
        "same_instance_and_dataset_have_mixed_contexts": (
            int(context_feature.get("mixed_instance_group_count", 0)) > 0
            and int(context_feature.get("mixed_dataset_group_count", 0)) > 0
        ),
    }
    return {
        "schema_version": "selector_context_feature_gap_audit_v1",
        "sources": {
            "context_disambiguation": str(context_disambiguation_path),
            "context_scalar_candidates": str(context_scalar_candidates_path),
            "context_scalar_holdout": str(context_scalar_holdout_path),
            "context_feature": str(context_feature_path),
            "failure_mechanism": str(failure_mechanism_path),
        },
        "proxy_count": len(proxy_results),
        "proxy_results": proxy_results,
        "required_feature_properties": required_feature_properties,
        "current_status": "feature_gap_identified_not_production_selector",
        "current_allowed_work": "calibration_only_feature_design_and_holdout",
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "当前缺的不是更多局部列指标，而是可泛化的 RMP/context trajectory "
            "表示：它必须加列前可观测，比 instance/dataset/online flags 更强，"
            "又不能像 exact context hash 那样只记身份。control_objective 是线索，"
            "但单 scalar / bin 还没有通过 holdout。"
        ),
    }


def write_report(audit: dict[str, Any], path: Path) -> None:
    lines = [
        "# Selector Context Feature Gap Audit 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告审计当前 addition-before selector 缺哪类上下文信息。它只读既有",
        "summary，不运行 solver，不改变 pricing / worker / certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "selector_context_feature_gap_audit = current",
        f"proxy_count = {audit['proxy_count']}",
        f"current_status = {audit['current_status']}",
        f"current_allowed_work = {audit['current_allowed_work']}",
        f"all_checks_pass = {str(audit['all_checks_pass']).lower()}",
        "```",
        "",
        "## 代理特征审计",
        "",
        "| 代理 | 状态 | 结论 |",
        "|---|---|---|",
    ]
    for item in audit["proxy_results"]:
        lines.append(f"| `{item['proxy_id']}` | `{item['status']}` | {item['reason']} |")
    lines.extend(["", "## 下一步特征必须满足", ""])
    for item in audit["required_feature_properties"]:
        lines.append(f"- `{item['property_id']}`：{item['requirement']}")
    lines.extend(["", "## 结论", "", audit["interpretation"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--context-disambiguation", default=str(DEFAULT_CONTEXT_DISAMBIGUATION)
    )
    parser.add_argument(
        "--context-scalar-candidates", default=str(DEFAULT_CONTEXT_SCALAR_CANDIDATES)
    )
    parser.add_argument(
        "--context-scalar-holdout", default=str(DEFAULT_CONTEXT_SCALAR_HOLDOUT)
    )
    parser.add_argument("--context-feature", default=str(DEFAULT_CONTEXT_FEATURE))
    parser.add_argument("--failure-mechanism", default=str(DEFAULT_FAILURE_MECHANISM))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    audit = build_audit(
        context_disambiguation_path=Path(args.context_disambiguation),
        context_scalar_candidates_path=Path(args.context_scalar_candidates),
        context_scalar_holdout_path=Path(args.context_scalar_holdout),
        context_feature_path=Path(args.context_feature),
        failure_mechanism_path=Path(args.failure_mechanism),
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(audit, Path(args.report))
    print(json.dumps(audit, ensure_ascii=False, sort_keys=True))
    return 0 if audit["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
