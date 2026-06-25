#!/usr/bin/env python3
"""Build audit-only profile runbooks for Journey tail low-min-fill mining.

The runbook executes canonical random-TW instances with low-min-fill audit
enabled but behavior disabled.  It is the precursor to A/B replay: first collect
V337-style candidate fields on unprofiled instances, then feed the resulting
logs into ``audit_journey_completion_tail_profile.py`` and
``build_journey_tail_minfill_ab_runbook.py``.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import shlex
from typing import Any, Iterable


DEFAULT_INSTANCES_ROOT = Path("BPC_future/logical_graph/tasks_020")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_tail_minfill_profile_runbook_20260625")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260625_bpc_future_journey_tail_minfill_profile_runbook_zh.md"
)
DEFAULT_CONFIG = Path("BPC_future/configs/moon_trek_20_smoke.yaml")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


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


def _safe_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")
    return slug[:180] or "instance"


def _shell_join(items: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(item)) for item in items)


def _summary_file(path: Path) -> Path:
    if path.is_dir():
        return path / "summary.json"
    return path


def _instance_from_log_file(log_file: Any) -> str | None:
    text = str(log_file or "")
    marker = "BPC_future/logical_graph/"
    if marker in text:
        instance = marker + text.split(marker, 1)[1]
        if instance.endswith(".jsonl"):
            instance = instance[: -len(".jsonl")]
        return instance
    return None


def _instances_from_known_artifact(path: Path) -> set[str]:
    candidates: set[str] = set()
    if path.is_dir():
        candidates.update(_instances_from_known_artifact(path / "summary.json"))
        for name in (
            "tail_minfill_training_rows.jsonl",
            "tail_minfill_ab_rows.jsonl",
            "branch_training_rows.jsonl",
        ):
            candidates.update(_instances_from_known_artifact(path / name))
        return candidates
    if not path.exists():
        return candidates
    if path.suffix == ".jsonl":
        for row in _iter_jsonl(path):
            value = row.get("instance") or row.get("instance_path")
            if value:
                candidates.add(str(value))
            log_instance = _instance_from_log_file(row.get("log_file"))
            if log_instance:
                candidates.add(log_instance)
        return candidates
    payload = _read_json(path)
    for key in ("training_rows", "rows", "records", "entries", "branch_training_rows"):
        raw_rows = payload.get(key)
        if not isinstance(raw_rows, list):
            continue
        for row in raw_rows:
            if not isinstance(row, dict):
                continue
            value = row.get("instance") or row.get("instance_path")
            if value:
                candidates.add(str(value))
            log_instance = _instance_from_log_file(row.get("log_file"))
            if log_instance:
                candidates.add(log_instance)
    return candidates


def _load_training_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            rows.extend(_load_training_rows([path / "summary.json"]))
            rows.extend(_iter_jsonl(path / "tail_minfill_training_rows.jsonl"))
            continue
        if path.suffix == ".jsonl":
            rows.extend(_iter_jsonl(path))
            continue
        payload = _read_json(path)
        raw_rows = payload.get("training_rows")
        if isinstance(raw_rows, list):
            rows.extend(row for row in raw_rows if isinstance(row, dict))
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
        label_key = ",".join(f"{name}:{labels.get(name)}" for name in sorted(labels))
        key = (str(row.get("instance") or ""), label_key)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _path_features(instance: str) -> dict[str, Any]:
    path = Path(instance)
    parts = path.parts
    family = ""
    scenario = ""
    if "tasks_020" in parts:
        idx = parts.index("tasks_020")
        if idx + 1 < len(parts):
            family = parts[idx + 1]
        if idx + 2 < len(parts):
            scenario = parts[idx + 2]
    match = re.search(r"_tasks020_(\d+)_seed(\d+)_", path.name)
    return {
        "family": family,
        "scenario": scenario,
        "task_index": int(match.group(1)) if match else -1,
        "seed": int(match.group(2)) if match else -1,
        "stem": path.stem,
    }


def _float_label(row: dict[str, Any], name: str) -> float:
    labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
    try:
        return float(labels.get(name) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _score_instance(
    instance: str,
    *,
    positive_features: list[dict[str, Any]],
    negative_features: list[dict[str, Any]],
    guard_features: list[dict[str, Any]],
) -> tuple[float, str]:
    features = _path_features(instance)
    score = 0.0
    reasons: list[str] = []
    for positive in positive_features:
        if features["family"] and features["family"] == positive.get("family"):
            score += 100.0
            reasons.append("same_positive_family")
        if features["scenario"] and features["scenario"] == positive.get("scenario"):
            score += 20.0
            reasons.append("same_positive_scenario")
        distance = abs(int(features["task_index"]) - int(positive.get("task_index", -99)))
        if features["task_index"] >= 0 and positive.get("task_index", -1) >= 0:
            score += max(0.0, 20.0 - 2.0 * float(distance))
            if distance <= 2:
                reasons.append("near_positive_task_index")
    for negative in negative_features:
        if (
            features["family"] == negative.get("family")
            and features["task_index"] == negative.get("task_index")
        ):
            score -= 50.0
            reasons.append("same_hard_negative_bucket")
        elif features["family"] == negative.get("family"):
            score -= 5.0
    for guard in guard_features:
        if (
            features["family"] == guard.get("family")
            and features["task_index"] == guard.get("task_index")
        ):
            score -= 10.0
            reasons.append("same_no_effect_guard_bucket")
    if not reasons:
        reasons.append("fallback_unseen_context")
    return score, ",".join(sorted(set(reasons)))


def _command(
    *,
    config: Path,
    instance: str,
    result_dir: Path,
    time_limit: int,
    python: str,
    max_workers: int,
    timeout_kill_after: str,
    tail_min_fill: int,
    max_depth: int,
    final_probe_only: bool,
) -> list[str]:
    return [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        python,
        "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
        "--config",
        str(config),
        "--instances",
        str(instance),
        "--time-limit",
        str(int(time_limit)),
        "--results-csv",
        str(result_dir / "results.csv"),
        "--log-dir",
        str(result_dir / "logs"),
        "--solution-dir",
        str(result_dir / "solutions"),
        "--run-log-dir",
        str(result_dir / "run_logs"),
        "--python",
        str(python),
        "--timeout-kill-after",
        str(timeout_kill_after),
        "--max-workers",
        str(int(max_workers)),
        "--quiet",
        "--set",
        "journey_tail_action_audit_enabled=True",
        "--set",
        "journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True",
        "--set",
        "journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False",
        "--set",
        f"journey_certificate_completion_bound_diverse_harvest_tail_min_fill={int(tail_min_fill)}",
        "--set",
        f"journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth={int(max_depth)}",
        "--set",
        (
            "journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only="
            f"{bool(final_probe_only)}"
        ),
    ]


def build_profile_runbook(
    *,
    instances_root: Path = DEFAULT_INSTANCES_ROOT,
    training_rows: list[Path] | None = None,
    exclude_from: list[Path] | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    config: Path = DEFAULT_CONFIG,
    time_limit: int = 260,
    limit: int = 24,
    python: str = "/home/kai/miniconda3/bin/python",
    max_workers: int = 1,
    timeout_kill_after: str = "30s",
    tail_min_fill: int = 4,
    tail_min_fill_max_depth: int = 0,
    tail_min_fill_final_probe_only: bool = True,
) -> dict[str, Any]:
    training_rows = training_rows or []
    exclude_from = exclude_from or []
    all_instances = sorted(str(path) for path in instances_root.rglob("*_logical_graph.json"))
    excluded: set[str] = set()
    for path in exclude_from:
        excluded.update(_instances_from_known_artifact(path))
    rows = _load_training_rows(training_rows)
    positive_features = [
        _path_features(str(row.get("instance") or ""))
        for row in rows
        if _float_label(row, "y_strict_positive") > 0.0 and row.get("instance")
    ]
    negative_features = [
        _path_features(str(row.get("instance") or ""))
        for row in rows
        if _float_label(row, "y_hard_negative") > 0.0 and row.get("instance")
    ]
    guard_features = [
        _path_features(str(row.get("instance") or ""))
        for row in rows
        if _float_label(row, "y_no_effect_guard") > 0.0 and row.get("instance")
    ]
    scored: list[dict[str, Any]] = []
    for instance in all_instances:
        if instance in excluded:
            continue
        score, reason = _score_instance(
            instance,
            positive_features=positive_features,
            negative_features=negative_features,
            guard_features=guard_features,
        )
        features = _path_features(instance)
        scored.append(
            {
                "instance": instance,
                "priority_score": round(score, 6),
                "priority_reason": reason,
                "family": features["family"],
                "scenario": features["scenario"],
                "task_index": features["task_index"],
                "seed": features["seed"],
            }
        )
    selected = sorted(
        scored,
        key=lambda row: (-float(row["priority_score"]), row["family"], row["task_index"], row["instance"]),
    )[: max(0, int(limit))]
    entries: list[dict[str, Any]] = []
    command_lines: list[str] = []
    for index, row in enumerate(selected, start=1):
        instance = str(row["instance"])
        result_dir = output_dir / f"{index:03d}_{_safe_slug(Path(instance).stem)}"
        command = _shell_join(
            _command(
                config=config,
                instance=instance,
                result_dir=result_dir,
                time_limit=time_limit,
                python=python,
                max_workers=max_workers,
                timeout_kill_after=timeout_kill_after,
                tail_min_fill=tail_min_fill,
                max_depth=tail_min_fill_max_depth,
                final_probe_only=tail_min_fill_final_probe_only,
            )
        )
        entry = {
            "entry_id": index,
            **row,
            "result_dir": str(result_dir),
            "command": command,
        }
        entries.append(entry)
        command_lines.append(command)
    summary = {
        "schema_version": "journey_tail_minfill_profile_runbook_v1",
        "status": "ready" if entries else "empty",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "instances_root": str(instances_root),
        "training_row_inputs": [str(path) for path in training_rows],
        "exclude_inputs": [str(path) for path in exclude_from],
        "raw_instance_count": len(all_instances),
        "excluded_instance_count": len(excluded),
        "candidate_pool_count": len(scored),
        "entry_count": len(entries),
        "command_count": len(command_lines),
        "time_limit": int(time_limit),
        "tail_min_fill": int(tail_min_fill),
        "tail_min_fill_enabled": False,
        "positive_template_count": len(positive_features),
        "negative_template_count": len(negative_features),
        "guard_template_count": len(guard_features),
        "entries": entries,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "commands.sh").write_text("\n".join(command_lines) + ("\n" if command_lines else ""), encoding="utf-8")
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Journey Tail Min-Fill Profile Runbook",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "为 canonical random-TW 20-scale 未覆盖实例生成 audit-only profile 命令。"
        "这些命令只采集 low min-fill candidate 字段，行为保持 disabled；后续再用"
        " completion-tail profile 筛出真正需要 paired replay 的候选。",
        "",
        "## 机器字段",
        "",
        "```text",
        "journey_tail_minfill_profile_runbook = current",
        f"raw_instance_count = {summary['raw_instance_count']}",
        f"excluded_instance_count = {summary['excluded_instance_count']}",
        f"candidate_pool_count = {summary['candidate_pool_count']}",
        f"entry_count = {summary['entry_count']}",
        f"command_count = {summary['command_count']}",
        f"time_limit = {summary['time_limit']}",
        f"tail_min_fill = {summary['tail_min_fill']}",
        "tail_min_fill_enabled = false",
        f"positive_template_count = {summary['positive_template_count']}",
        f"negative_template_count = {summary['negative_template_count']}",
        f"guard_template_count = {summary['guard_template_count']}",
        "runs_bpc_or_pricing = false",
        "certificate_effect = false",
        "official_bound_effect = false",
        "```",
        "",
        "## Entries",
        "",
        "```json",
        json.dumps(summary["entries"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances-root", type=Path, default=DEFAULT_INSTANCES_ROOT)
    parser.add_argument("--training-rows", type=Path, nargs="*", default=[])
    parser.add_argument("--exclude-from", type=Path, nargs="*", default=[])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--time-limit", type=int, default=260)
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--python", default="/home/kai/miniconda3/bin/python")
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--timeout-kill-after", default="30s")
    parser.add_argument("--tail-min-fill", type=int, default=4)
    parser.add_argument("--tail-min-fill-max-depth", type=int, default=0)
    parser.add_argument("--tail-min-fill-final-probe-only", action="store_true", default=True)
    args = parser.parse_args()
    build_profile_runbook(
        instances_root=args.instances_root,
        training_rows=args.training_rows,
        exclude_from=args.exclude_from,
        output_dir=args.output_dir,
        report=args.report,
        config=args.config,
        time_limit=args.time_limit,
        limit=args.limit,
        python=args.python,
        max_workers=args.max_workers,
        timeout_kill_after=args.timeout_kill_after,
        tail_min_fill=args.tail_min_fill,
        tail_min_fill_max_depth=args.tail_min_fill_max_depth,
        tail_min_fill_final_probe_only=args.tail_min_fill_final_probe_only,
    )


if __name__ == "__main__":
    main()
