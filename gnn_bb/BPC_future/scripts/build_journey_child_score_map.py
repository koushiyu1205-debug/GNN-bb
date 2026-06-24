#!/usr/bin/env python3
"""Build an opt-in child-ordering score map from Journey child-probe rows.

The script is offline and diagnostic-only. It reads existing
``child_probe_rows.jsonl`` artifacts and emits a map for
``journey_child_priority_mode=child_score``. It never runs BPC, pricing, RMP,
or creates official bounds/certificates.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_child_score_map_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/20260624_bpc_future_journey_child_score_map_zh.md"
)


@dataclass
class _ChildScoreAccumulator:
    score_sum: float = 0.0
    observation_count: int = 0
    complete_count: int = 0
    right_censored_count: int = 0
    fathom_sum: float = 0.0
    corrected_gain_max: float = 0.0
    proof_cpu_sum: float = 0.0
    completion_retry_sum: float = 0.0
    negative_pricing_sum: float = 0.0
    instance: str = ""
    node_id: int | None = None
    depth: int | None = None
    pair: tuple[int, int] = (0, 0)
    kind: str = ""


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _load_child_probe_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_iter_jsonl(path / "child_probe_rows.jsonl"))
            continue
        if path.name == "summary.json":
            rows.extend(_iter_jsonl(path.parent / "child_probe_rows.jsonl"))
            continue
        if path.name == "child_probe_rows.jsonl" or path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
    return rows


def _float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if parsed != parsed:
        return float(default)
    return float(parsed)


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _pair_from_row(row: dict[str, Any]) -> tuple[int, int] | None:
    pair = row.get("forced_pair") or row.get("pair")
    if isinstance(pair, str):
        pieces = [piece.strip() for piece in pair.replace(";", ",").split(",") if piece.strip()]
        if len(pieces) == 2:
            try:
                i, j = int(pieces[0]), int(pieces[1])
            except ValueError:
                return None
            return None if i == j else tuple(sorted((i, j)))
    if isinstance(pair, (list, tuple)) and len(pair) == 2:
        try:
            i, j = int(pair[0]), int(pair[1])
        except (TypeError, ValueError):
            return None
        return None if i == j else tuple(sorted((i, j)))
    task_i = row.get("task_i")
    task_j = row.get("task_j")
    if task_i is None or task_j is None:
        return None
    try:
        i, j = int(task_i), int(task_j)
    except (TypeError, ValueError):
        return None
    return None if i == j else tuple(sorted((i, j)))


def _child_kind(row: dict[str, Any]) -> str | None:
    kind = row.get("child_constraint_kind") or row.get("constraint_kind") or row.get("kind")
    if kind in {"same_vehicle", "separate_vehicle"}:
        return str(kind)
    constraint = str(row.get("child_constraint") or row.get("constraint") or "")
    for candidate in ("same_vehicle", "separate_vehicle"):
        if constraint.endswith(f"={candidate}") or f"={candidate}" in constraint:
            return candidate
    return None


def _score_key(
    pair: tuple[int, int],
    kind: str,
    *,
    key_scope: str,
    node_id: int | None,
    depth: int | None,
) -> str:
    pair_text = f"{int(pair[0])},{int(pair[1])}"
    suffix = f"{pair_text}:{kind}"
    if key_scope == "node_depth":
        if node_id is None or depth is None:
            raise ValueError("node_depth key scope requires node_id and depth")
        return f"node:{int(node_id)}:depth:{int(depth)}:{suffix}"
    if key_scope == "depth":
        if depth is None:
            raise ValueError("depth key scope requires depth")
        return f"depth:{int(depth)}:{suffix}"
    if key_scope == "pair":
        return suffix
    raise ValueError(f"unsupported key_scope: {key_scope}")


def _child_score(
    row: dict[str, Any],
    *,
    complete_bonus: float,
    right_censored_penalty: float,
    fathom_bonus: float,
    corrected_gain_scale: float,
    corrected_gain_cap: float,
    completion_retry_penalty: float,
    proof_cpu_scale: float,
    negative_pricing_penalty: float,
) -> float:
    labels = row.get("child_labels") if isinstance(row.get("child_labels"), dict) else {}
    score = 0.0
    if bool(row.get("label_observation_complete")):
        score += float(complete_bonus)
    if bool(row.get("right_censored")):
        score -= float(right_censored_penalty)
    fathomed = _float(labels.get("child_fathomed"))
    corrected_gain = min(
        max(0.0, _float(labels.get("child_max_corrected_bound_gain"))),
        float(corrected_gain_cap),
    )
    score += float(fathom_bonus) * fathomed
    score += corrected_gain / max(1.0e-9, float(corrected_gain_scale))
    score -= float(completion_retry_penalty) * _float(labels.get("child_completion_bound_retry_count"))
    score -= _float(labels.get("child_proof_cpu")) / max(1.0e-9, float(proof_cpu_scale))
    score -= float(negative_pricing_penalty) * _float(labels.get("child_negative_pricing_event_count"))
    return float(score)


def build_child_score_map(
    inputs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    key_scope: str = "node_depth",
    include_log_contains: tuple[str, ...] = (),
    exclude_log_contains: tuple[str, ...] = (),
    include_unstarted: bool = False,
    complete_bonus: float = 5.0,
    right_censored_penalty: float = 8.0,
    fathom_bonus: float = 2.0,
    corrected_gain_scale: float = 5.0,
    corrected_gain_cap: float = 25.0,
    completion_retry_penalty: float = 0.1,
    proof_cpu_scale: float = 120.0,
    negative_pricing_penalty: float = 0.0,
) -> dict[str, Any]:
    if key_scope not in {"node_depth", "depth", "pair"}:
        raise ValueError(f"unsupported key_scope: {key_scope}")
    raw_rows = _load_child_probe_rows(inputs)
    rows: list[dict[str, Any]] = []
    skipped_rows = 0
    for row in raw_rows:
        log_file = str(row.get("log_file") or "")
        if include_log_contains and not any(token in log_file for token in include_log_contains):
            continue
        if exclude_log_contains and any(token in log_file for token in exclude_log_contains):
            continue
        if not include_unstarted and not bool(row.get("child_started")):
            continue
        pair = _pair_from_row(row)
        kind = _child_kind(row)
        node_id = _int_or_none(row.get("branch_node_id"))
        depth = _int_or_none(row.get("branch_depth"))
        if pair is None or kind is None:
            skipped_rows += 1
            continue
        try:
            _score_key(pair, kind, key_scope=key_scope, node_id=node_id, depth=depth)
        except ValueError:
            skipped_rows += 1
            continue
        rows.append(row)

    accumulators: dict[str, _ChildScoreAccumulator] = {}
    for row in rows:
        pair = _pair_from_row(row)
        kind = _child_kind(row)
        node_id = _int_or_none(row.get("branch_node_id"))
        depth = _int_or_none(row.get("branch_depth"))
        if pair is None or kind is None:
            continue
        key = _score_key(pair, kind, key_scope=key_scope, node_id=node_id, depth=depth)
        labels = row.get("child_labels") if isinstance(row.get("child_labels"), dict) else {}
        score = _child_score(
            row,
            complete_bonus=complete_bonus,
            right_censored_penalty=right_censored_penalty,
            fathom_bonus=fathom_bonus,
            corrected_gain_scale=corrected_gain_scale,
            corrected_gain_cap=corrected_gain_cap,
            completion_retry_penalty=completion_retry_penalty,
            proof_cpu_scale=proof_cpu_scale,
            negative_pricing_penalty=negative_pricing_penalty,
        )
        acc = accumulators.setdefault(
            key,
            _ChildScoreAccumulator(
                instance=str(row.get("log_file") or ""),
                node_id=node_id,
                depth=depth,
                pair=pair,
                kind=str(kind),
            ),
        )
        acc.score_sum += float(score)
        acc.observation_count += 1
        acc.complete_count += 1 if bool(row.get("label_observation_complete")) else 0
        acc.right_censored_count += 1 if bool(row.get("right_censored")) else 0
        acc.fathom_sum += _float(labels.get("child_fathomed"))
        acc.corrected_gain_max = max(
            float(acc.corrected_gain_max),
            _float(labels.get("child_max_corrected_bound_gain")),
        )
        acc.proof_cpu_sum += _float(labels.get("child_proof_cpu"))
        acc.completion_retry_sum += _float(labels.get("child_completion_bound_retry_count"))
        acc.negative_pricing_sum += _float(labels.get("child_negative_pricing_event_count"))

    score_rows = []
    for key, acc in sorted(accumulators.items()):
        score = float(acc.score_sum) / float(max(1, acc.observation_count))
        score_rows.append(
            {
                "schema_version": "journey_child_score_row_v1",
                "diagnostic_only": True,
                "runs_bpc_or_pricing": False,
                "production_ready": False,
                "certificate_effect": False,
                "official_bound_effect": False,
                "key": key,
                "child_score": round(score, 9),
                "score": round(score, 9),
                "node_id": acc.node_id,
                "depth": acc.depth,
                "pair": [int(acc.pair[0]), int(acc.pair[1])],
                "task_i": int(acc.pair[0]),
                "task_j": int(acc.pair[1]),
                "child_constraint_kind": acc.kind,
                "observation_count": int(acc.observation_count),
                "complete_count": int(acc.complete_count),
                "right_censored_count": int(acc.right_censored_count),
                "fathom_sum": round(float(acc.fathom_sum), 9),
                "max_corrected_bound_gain": round(float(acc.corrected_gain_max), 9),
                "proof_cpu_sum": round(float(acc.proof_cpu_sum), 9),
                "completion_bound_retry_sum": round(float(acc.completion_retry_sum), 9),
                "negative_pricing_sum": round(float(acc.negative_pricing_sum), 9),
            }
        )
    score_rows.sort(key=lambda row: (-float(row["score"]), str(row["key"])))
    score_map = {str(row["key"]): float(row["score"]) for row in score_rows}

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "journey_child_score_rows.json").write_text(
        json.dumps(score_rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "journey_child_score_rows.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in score_rows),
        encoding="utf-8",
    )
    (output_dir / "journey_child_score_map.json").write_text(
        json.dumps(score_map, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "schema_version": "journey_child_score_map_summary_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "input_paths": [str(path) for path in inputs],
        "output_dir": str(output_dir),
        "key_scope": key_scope,
        "raw_child_probe_row_count": len(raw_rows),
        "child_probe_row_count": len(rows),
        "filtered_out_child_probe_row_count": len(raw_rows) - len(rows),
        "skipped_row_count": int(skipped_rows),
        "child_score_row_count": len(score_rows),
        "child_score_map_entry_count": len(score_map),
        "include_log_contains": list(include_log_contains),
        "exclude_log_contains": list(exclude_log_contains),
        "include_unstarted": bool(include_unstarted),
        "complete_bonus": float(complete_bonus),
        "right_censored_penalty": float(right_censored_penalty),
        "fathom_bonus": float(fathom_bonus),
        "corrected_gain_scale": float(corrected_gain_scale),
        "corrected_gain_cap": float(corrected_gain_cap),
        "completion_retry_penalty": float(completion_retry_penalty),
        "proof_cpu_scale": float(proof_cpu_scale),
        "negative_pricing_penalty": float(negative_pricing_penalty),
        "solver_child_priority_mode": "child_score",
        "solver_score_map_path": str(output_dir / "journey_child_score_map.json"),
        "usable_as_certificate": False,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    _write_report(report, summary, score_rows)
    return summary


def _write_report(report: Path, summary: dict[str, Any], score_rows: list[dict[str, Any]]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Child Score Map",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "把 child-probe rows 转成 solver 的 `journey_child_priority_mode=child_score` 输入。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
    ]
    for key in [
        "raw_child_probe_row_count",
        "child_probe_row_count",
        "filtered_out_child_probe_row_count",
        "skipped_row_count",
        "child_score_row_count",
        "child_score_map_entry_count",
        "key_scope",
        "include_log_contains",
        "exclude_log_contains",
        "include_unstarted",
        "solver_child_priority_mode",
        "solver_score_map_path",
        "production_ready",
        "certificate_effect",
        "official_bound_effect",
    ]:
        lines.append(f"{key} = {summary.get(key)}")
    lines.extend(["```", "", "## Top Child Score Rows", ""])
    for row in score_rows[:12]:
        lines.append(
            "- "
            f"key={row['key']} pair={row['pair']} kind={row['child_constraint_kind']} "
            f"score={row['score']} obs={row['observation_count']} fathom={row['fathom_sum']} "
            f"gain={row['max_corrected_bound_gain']} cpu={row['proof_cpu_sum']}"
        )
    lines.extend(["", "## 使用边界", ""])
    lines.append(
        "使用方式：`journey_child_priority_mode=child_score`，并把 `journey_child_priority_score_path` 指向 `journey_child_score_map.json`。"
    )
    lines.append(
        "`child_score` 只改变同一个 Ryan-Foster branch 下 same/separate child 的入队顺序；它不改变 lower bound、分支约束、剪枝或 certificate。"
    )
    lines.append(
        "当前输出仍是 diagnostic-only；right-censored 数据可用于采样导航和 shadow/opt-in，不应直接视为 production-ready 模型。"
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--key-scope", choices=("node_depth", "depth", "pair"), default="node_depth")
    parser.add_argument("--include-log-contains", action="append", default=[])
    parser.add_argument("--exclude-log-contains", action="append", default=[])
    parser.add_argument("--include-unstarted", action="store_true")
    parser.add_argument("--complete-bonus", type=float, default=5.0)
    parser.add_argument("--right-censored-penalty", type=float, default=8.0)
    parser.add_argument("--fathom-bonus", type=float, default=2.0)
    parser.add_argument("--corrected-gain-scale", type=float, default=5.0)
    parser.add_argument("--corrected-gain-cap", type=float, default=25.0)
    parser.add_argument("--completion-retry-penalty", type=float, default=0.1)
    parser.add_argument("--proof-cpu-scale", type=float, default=120.0)
    parser.add_argument("--negative-pricing-penalty", type=float, default=0.0)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = build_child_score_map(
        list(args.paths),
        args.output_dir,
        args.report,
        key_scope=args.key_scope,
        include_log_contains=tuple(args.include_log_contains or ()),
        exclude_log_contains=tuple(args.exclude_log_contains or ()),
        include_unstarted=bool(args.include_unstarted),
        complete_bonus=args.complete_bonus,
        right_censored_penalty=args.right_censored_penalty,
        fathom_bonus=args.fathom_bonus,
        corrected_gain_scale=args.corrected_gain_scale,
        corrected_gain_cap=args.corrected_gain_cap,
        completion_retry_penalty=args.completion_retry_penalty,
        proof_cpu_scale=args.proof_cpu_scale,
        negative_pricing_penalty=args.negative_pricing_penalty,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
