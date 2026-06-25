#!/usr/bin/env python3
"""Audit whether branch counterfactual rows are ready for GAT training.

This script is diagnostic-only. It reads completed
``branch_counterfactual_delta_rows.jsonl`` files and separates weak full-replay
improvements from target-200 positives. It does not run BPC, pricing, RMP, or
produce official bounds/certificates.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_training_readiness_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_branch_training_readiness_zh.md"
)

ROW_FILENAME = "branch_counterfactual_delta_rows.jsonl"


PIPELINE_DEBUG_REQUIREMENTS = {
    "strict_full_replay_positive_min": 5,
    "positive_context_min": 2,
    "positive_instance_min": 2,
    "positive_time_window_family_min": 2,
}


SANITY_REQUIREMENTS = {
    "strict_full_replay_positive_min": 10,
    "hard_negative_min": 5,
    "positive_context_min": 3,
    "positive_instance_min": 3,
    "positive_time_window_family_min": 2,
}

SERIOUS_REQUIREMENTS = {
    "target_200_positive_min": 20,
    "hard_negative_min": 30,
    "target_200_context_min": 8,
    "target_200_instance_min": 8,
    "target_200_time_window_family_min": 3,
    "holdout_context_min": 2,
}

OPTIN_REQUIREMENTS = {
    "target_200_positive_min": 40,
    "hard_negative_min": 60,
    "target_200_context_min": 15,
    "target_200_instance_min": 15,
    "target_200_time_window_family_min": 3,
    "holdout_context_min": 3,
}


def _float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _label(row: dict[str, Any], name: str) -> float:
    labels = row.get("labels")
    if not isinstance(labels, dict):
        return 0.0
    return _float(labels.get(name))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _row_file(path: Path) -> Path:
    if path.is_dir():
        return path / ROW_FILENAME
    if path.name == ROW_FILENAME:
        return path
    if path.name == "summary.json":
        return path.parent / ROW_FILENAME
    return path


def _load_rows(paths: Iterable[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    resolved: list[str] = []
    for path in paths:
        row_path = _row_file(path)
        resolved.append(str(row_path))
        rows.extend(_read_jsonl(row_path))
    return rows, resolved


def _pair_text(value: Any) -> str:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return f"{value[0]}-{value[1]}"
    return str(value or "")


def _context_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("instance") or ""),
            str(row.get("node_id") if row.get("node_id") is not None else ""),
            str(row.get("depth") if row.get("depth") is not None else ""),
            _pair_text(row.get("baseline_pair")),
        ]
    )


def _time_window_family(value: Any) -> str:
    text = str(value or "")
    for token in ("greedy-anchor", "random-wave", "sector-wave"):
        if token in text:
            return token
    return ""


def _is_strict_full_replay_positive(row: dict[str, Any]) -> bool:
    if str(row.get("counterfactual_label_type") or "") != "strong_positive":
        return False
    if row.get("alternative_forced_pair_matched") is False:
        return False
    if bool(row.get("right_censored_counterfactual")):
        return False
    return str(row.get("alternative_status") or "") == "OPTIMAL"


def _is_target_wall_positive(row: dict[str, Any], *, target_wall: float) -> bool:
    if row.get("alternative_forced_pair_matched") is False:
        return False
    if bool(row.get("right_censored_counterfactual")):
        return False
    return bool(
        str(row.get("alternative_status") or "") == "OPTIMAL"
        and _float(row.get("alternative_wall_time")) <= float(target_wall)
        and _float(row.get("baseline_wall_time")) > float(target_wall)
    )


def _is_regression(row: dict[str, Any]) -> bool:
    return bool(
        str(row.get("counterfactual_label_type") or "") == "regression"
        or _label(row, "y_counterfactual_regression") > 0.5
        or _label(row, "y_counterfactual_timeout_regression") > 0.5
    )


def _is_local_only_hard_negative(row: dict[str, Any]) -> bool:
    return str(row.get("counterfactual_label_type") or "") == "local_only_hard_negative"


def _marked_holdout(row: dict[str, Any]) -> bool:
    baseline_raw = row.get("baseline_raw_row") if isinstance(row.get("baseline_raw_row"), dict) else {}
    alternative_raw = (
        row.get("alternative_raw_row") if isinstance(row.get("alternative_raw_row"), dict) else {}
    )
    return bool(
        row.get("holdout_context")
        or row.get("is_holdout")
        or row.get("positive_holdout_context")
        or baseline_raw.get("holdout_context")
        or baseline_raw.get("is_holdout")
        or baseline_raw.get("positive_holdout_context")
        or alternative_raw.get("holdout_context")
        or alternative_raw.get("is_holdout")
        or alternative_raw.get("positive_holdout_context")
    )


def _count_distinct(rows: Iterable[dict[str, Any]], key: str) -> int:
    if key == "context":
        return len({_context_key(row) for row in rows})
    if key == "instance":
        return len({str(row.get("instance") or "") for row in rows if row.get("instance")})
    if key == "family":
        return len(
            {
                family
                for family in (_time_window_family(row.get("instance")) for row in rows)
                if family
            }
        )
    raise ValueError(f"unknown distinct key: {key}")


def _missing(requirements: dict[str, int], actuals: dict[str, int]) -> dict[str, int]:
    return {
        key: max(0, int(required) - int(actuals.get(key, 0)))
        for key, required in requirements.items()
    }


def _ready(requirements: dict[str, int], actuals: dict[str, int]) -> bool:
    return all(int(actuals.get(key, 0)) >= int(required) for key, required in requirements.items())


def _normalized_row(row: dict[str, Any], *, target_wall: float) -> dict[str, Any]:
    strict_positive = _is_strict_full_replay_positive(row)
    target_positive = _is_target_wall_positive(row, target_wall=target_wall)
    regression = _is_regression(row)
    local_only = _is_local_only_hard_negative(row)
    return {
        "schema_version": "journey_branch_training_readiness_row_v1",
        "experiment": row.get("experiment"),
        "instance": row.get("instance"),
        "time_window_family": _time_window_family(row.get("instance")),
        "context_key": _context_key(row),
        "node_id": row.get("node_id"),
        "depth": row.get("depth"),
        "baseline_pair": row.get("baseline_pair"),
        "alternative_pair": row.get("alternative_pair"),
        "baseline_status": row.get("baseline_status"),
        "alternative_status": row.get("alternative_status"),
        "baseline_wall_time": _float(row.get("baseline_wall_time")),
        "alternative_wall_time": _float(row.get("alternative_wall_time")),
        "counterfactual_label_type": row.get("counterfactual_label_type"),
        "strict_full_replay_positive": strict_positive,
        "target_200_positive": target_positive,
        "weak_positive_not_target": bool(strict_positive and not target_positive),
        "regression": regression,
        "local_only_hard_negative": local_only,
        "usable_for_counterfactual_training": bool(row.get("usable_for_counterfactual_training")),
        "right_censored_counterfactual": bool(row.get("right_censored_counterfactual")),
        "timeout_resolved": bool(row.get("timeout_resolved")),
        "timeout_regression": bool(row.get("timeout_regression")),
        "positive_holdout_context": bool(_marked_holdout(row)),
    }


def build_training_readiness(
    inputs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    target_wall: float = 200.0,
) -> dict[str, Any]:
    rows, resolved_inputs = _load_rows(inputs)
    normalized_rows = [_normalized_row(row, target_wall=target_wall) for row in rows]

    strict_positive_rows = [row for row in normalized_rows if row["strict_full_replay_positive"]]
    target_positive_rows = [row for row in normalized_rows if row["target_200_positive"]]
    weak_positive_rows = [row for row in normalized_rows if row["weak_positive_not_target"]]
    regression_rows = [row for row in normalized_rows if row["regression"]]
    local_only_rows = [row for row in normalized_rows if row["local_only_hard_negative"]]
    hard_negative_rows = regression_rows
    target_holdout_contexts = {
        row["context_key"] for row in target_positive_rows if row["positive_holdout_context"]
    }
    strict_holdout_contexts = {
        row["context_key"] for row in strict_positive_rows if row["positive_holdout_context"]
    }

    label_type_counts = Counter(str(row.get("counterfactual_label_type") or "") for row in normalized_rows)
    status_pair_counts = Counter(
        f"{row.get('baseline_status')}->{row.get('alternative_status')}"
        for row in normalized_rows
    )
    actuals = {
        "strict_full_replay_positive_min": len(strict_positive_rows),
        "target_200_positive_min": len(target_positive_rows),
        "hard_negative_min": len(hard_negative_rows),
        "positive_context_min": _count_distinct(strict_positive_rows, "context"),
        "positive_instance_min": _count_distinct(strict_positive_rows, "instance"),
        "positive_time_window_family_min": _count_distinct(strict_positive_rows, "family"),
        "target_200_context_min": _count_distinct(target_positive_rows, "context"),
        "target_200_instance_min": _count_distinct(target_positive_rows, "instance"),
        "target_200_time_window_family_min": _count_distinct(target_positive_rows, "family"),
        "holdout_context_min": len(target_holdout_contexts),
    }

    remaining_for_pipeline_debug = _missing(PIPELINE_DEBUG_REQUIREMENTS, actuals)
    remaining_for_sanity = _missing(SANITY_REQUIREMENTS, actuals)
    remaining_for_serious = _missing(SERIOUS_REQUIREMENTS, actuals)
    remaining_for_optin = _missing(OPTIN_REQUIREMENTS, actuals)

    summary = {
        "schema_version": "journey_branch_training_readiness_v3",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "production_ready": False,
        "target_wall": float(target_wall),
        "input_paths": [str(path) for path in inputs],
        "resolved_row_paths": resolved_inputs,
        "output_dir": str(output_dir),
        "row_count": len(normalized_rows),
        "usable_counterfactual_training_count": int(
            sum(1 for row in normalized_rows if row["usable_for_counterfactual_training"])
        ),
        "strict_full_replay_positive_count": len(strict_positive_rows),
        "strict_full_replay_positive_context_count": _count_distinct(strict_positive_rows, "context"),
        "strict_full_replay_positive_instance_count": _count_distinct(strict_positive_rows, "instance"),
        "strict_full_replay_positive_time_window_family_count": _count_distinct(
            strict_positive_rows,
            "family",
        ),
        "target_200_positive_count": len(target_positive_rows),
        "target_200_positive_context_count": _count_distinct(target_positive_rows, "context"),
        "target_200_positive_instance_count": _count_distinct(target_positive_rows, "instance"),
        "target_200_positive_time_window_family_count": _count_distinct(
            target_positive_rows,
            "family",
        ),
        "weak_positive_not_target_count": len(weak_positive_rows),
        "regression_count": len(regression_rows),
        "local_only_hard_negative_count": len(local_only_rows),
        "hard_negative_count": len(hard_negative_rows),
        "right_censored_counterfactual_count": int(
            sum(1 for row in normalized_rows if row["right_censored_counterfactual"])
        ),
        "timeout_resolved_count": int(sum(1 for row in normalized_rows if row["timeout_resolved"])),
        "timeout_regression_count": int(sum(1 for row in normalized_rows if row["timeout_regression"])),
        "strict_positive_holdout_context_count": len(strict_holdout_contexts),
        "target_200_positive_holdout_context_count": len(target_holdout_contexts),
        "distinct_instance_count": _count_distinct(normalized_rows, "instance"),
        "distinct_time_window_family_count": _count_distinct(normalized_rows, "family"),
        "counterfactual_label_type_counts": dict(sorted(label_type_counts.items())),
        "status_pair_counts": dict(sorted(status_pair_counts.items())),
        "pipeline_debug_training_requirements": PIPELINE_DEBUG_REQUIREMENTS,
        "sanity_training_requirements": SANITY_REQUIREMENTS,
        "serious_training_requirements": SERIOUS_REQUIREMENTS,
        "optin_training_requirements": OPTIN_REQUIREMENTS,
        "training_readiness_actuals": actuals,
        "pipeline_debug_training_ready": _ready(PIPELINE_DEBUG_REQUIREMENTS, actuals),
        "sanity_training_ready": _ready(SANITY_REQUIREMENTS, actuals),
        "serious_training_ready": _ready(SERIOUS_REQUIREMENTS, actuals),
        "optin_training_ready": _ready(OPTIN_REQUIREMENTS, actuals),
        "remaining_for_pipeline_debug_training": remaining_for_pipeline_debug,
        "remaining_for_sanity_training": remaining_for_sanity,
        "remaining_for_serious_training": remaining_for_serious,
        "remaining_for_optin_training": remaining_for_optin,
        "missing_for_pipeline_debug_training": remaining_for_pipeline_debug,
        "missing_for_sanity_training": remaining_for_sanity,
        "missing_for_serious_training": remaining_for_serious,
        "missing_for_optin_training": remaining_for_optin,
        "rows": normalized_rows,
    }
    write_outputs(summary, output_dir, report)
    return summary


def write_outputs(summary: dict[str, Any], output_dir: Path, report: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = list(summary.get("rows", []))
    summary_without_rows = dict(summary)
    summary_without_rows.pop("rows", None)
    (output_dir / "summary.json").write_text(
        json.dumps(summary_without_rows, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "branch_training_readiness_rows.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    _write_report(report, summary_without_rows)


def _format_missing(missing: dict[str, int]) -> str:
    nonzero = {key: value for key, value in missing.items() if value > 0}
    if not nonzero:
        return "{}"
    return str(nonzero)


def _write_report(report: Path, summary: dict[str, Any]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Branch Training Readiness Audit",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "汇总已完成 branch counterfactual replay，区分 strict full-replay positive 和真正进入 200 秒目标的 target-200 positive。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不改变 official bound 或 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"target_wall = {summary['target_wall']}",
        f"row_count = {summary['row_count']}",
        f"usable_counterfactual_training_count = {summary['usable_counterfactual_training_count']}",
        f"strict_full_replay_positive_count = {summary['strict_full_replay_positive_count']}",
        "strict_full_replay_positive_context_count = "
        f"{summary['strict_full_replay_positive_context_count']}",
        "strict_full_replay_positive_instance_count = "
        f"{summary['strict_full_replay_positive_instance_count']}",
        "strict_full_replay_positive_time_window_family_count = "
        f"{summary['strict_full_replay_positive_time_window_family_count']}",
        f"target_200_positive_count = {summary['target_200_positive_count']}",
        "target_200_positive_context_count = "
        f"{summary['target_200_positive_context_count']}",
        "target_200_positive_instance_count = "
        f"{summary['target_200_positive_instance_count']}",
        "target_200_positive_time_window_family_count = "
        f"{summary['target_200_positive_time_window_family_count']}",
        f"weak_positive_not_target_count = {summary['weak_positive_not_target_count']}",
        f"regression_count = {summary['regression_count']}",
        f"local_only_hard_negative_count = {summary['local_only_hard_negative_count']}",
        f"hard_negative_count = {summary['hard_negative_count']}",
        f"right_censored_counterfactual_count = {summary['right_censored_counterfactual_count']}",
        f"timeout_resolved_count = {summary['timeout_resolved_count']}",
        f"timeout_regression_count = {summary['timeout_regression_count']}",
        "target_200_positive_holdout_context_count = "
        f"{summary['target_200_positive_holdout_context_count']}",
        f"counterfactual_label_type_counts = {summary['counterfactual_label_type_counts']}",
        f"status_pair_counts = {summary['status_pair_counts']}",
        f"pipeline_debug_training_ready = {str(summary['pipeline_debug_training_ready']).lower()}",
        f"sanity_training_ready = {str(summary['sanity_training_ready']).lower()}",
        f"serious_training_ready = {str(summary['serious_training_ready']).lower()}",
        f"optin_training_ready = {str(summary['optin_training_ready']).lower()}",
        f"serious_training_requirements = {summary['serious_training_requirements']}",
        f"optin_training_requirements = {summary['optin_training_requirements']}",
        "remaining_for_pipeline_debug_training = "
        f"{_format_missing(summary['remaining_for_pipeline_debug_training'])}",
        "remaining_for_sanity_training = "
        f"{_format_missing(summary['remaining_for_sanity_training'])}",
        "remaining_for_serious_training = "
        f"{_format_missing(summary['remaining_for_serious_training'])}",
        f"remaining_for_optin_training = {_format_missing(summary['remaining_for_optin_training'])}",
        "missing_for_pipeline_debug_training = "
        f"{_format_missing(summary['missing_for_pipeline_debug_training'])}",
        f"missing_for_sanity_training = {_format_missing(summary['missing_for_sanity_training'])}",
        f"missing_for_serious_training = {_format_missing(summary['missing_for_serious_training'])}",
        f"missing_for_optin_training = {_format_missing(summary['missing_for_optin_training'])}",
        "runs_bpc_or_pricing = false",
        "official_bound_effect = false",
        "certificate_effect = false",
        "```",
        "",
        "## 解释",
        "",
        "- `strict_full_replay_positive` 表示 forced branch 闭环跑完且相对 baseline 改善；它可以用于试训练和排序信号，但不等价于 20 规模达标。",
        "- `target_200_positive` 表示 baseline 超过目标墙钟、alternative 在目标墙钟内 OPTIMAL；这是 20 规模 200 秒目标的高权重标签。",
        "- `hard_negative_count` 当前只计入 full-run regression；`local_only_hard_negative` 作为弱负例单列，避免把右删失局部 proxy 当成严格反例。",
        "- `pipeline_debug_training_ready=true` 只表示可以调通数据加载、图构造、loss 和 checkpoint，不表示模型已有足够跨 context 泛化证据。",
        "- `sanity_training_ready=true` 只说明可以试训模型管线；`serious_training_ready=true` 才表示数据量接近可以认真训练 branch/action head；`optin_training_ready=true` 才接近上线 opt-in 评估门槛。",
        "- `remaining_for_*` 是距离对应 requirements 还差多少；`missing_for_*` 是保留给旧下游的同义字段，不是最低门槛本身。",
        "",
        "## 当前判断",
        "",
    ]
    if summary["pipeline_debug_training_ready"]:
        lines.append("当前 strict/full-replay 信号已经足够跑一次 pipeline/debug 训练。")
    else:
        lines.append("当前 strict/full-replay 信号连 pipeline/debug 训练都偏薄，应先补最小闭环正例。")
    if summary["sanity_training_ready"]:
        lines.append("当前 strict/full-replay 信号已经足够做一次小规模试训练。")
    else:
        lines.append("当前 strict/full-replay 信号还不足以支撑试训练，应继续补最小正负例。")
    if not summary["serious_training_ready"]:
        lines.append(
            "当前还不适合把 branch/action GAT 当作正式训练目标；主要缺口见 remaining_for_serious_training。"
        )
    if int(summary["weak_positive_not_target_count"]) > 0:
        lines.append(
            "存在相对变快但仍未进入 200 秒的弱正例，训练时应降权或单独作为 proof-cost/ranking 辅助标签。"
        )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--target-wall", type=float, default=200.0)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_training_readiness(
        list(args.inputs),
        args.output_dir,
        args.report,
        target_wall=args.target_wall,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
