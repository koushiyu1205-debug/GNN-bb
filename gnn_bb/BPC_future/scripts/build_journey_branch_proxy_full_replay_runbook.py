#!/usr/bin/env python3
"""Build full-replay runbooks from child-probe proxy branch rows.

This helper is diagnostic-only.  It reads offline child-probe proxy rows and
emits forced-pair replay commands for root branch candidates.  It does not run
BPC, pricing, or RMP, and it does not produce certificates or official bounds.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import shlex
from typing import Any, Iterable


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/journey_branch_proxy_full_replay_runbook_20260624")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260624_bpc_future_journey_branch_proxy_full_replay_runbook_zh.md"
)
DEFAULT_CONFIG = Path("BPC_future/configs/moon_trek_20_smoke.yaml")
DEFAULT_PYTHON = "/home/kai/miniconda3/bin/python"


def _safe_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")
    return slug[:180] or "item"


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


def _int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return int(default)
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


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


def _proxy_branch_file(path: Path) -> Path:
    if path.is_dir():
        candidate = path / "child_probe_proxy_branch_rows.jsonl"
        if candidate.exists():
            return candidate
    return path


def _load_proxy_rows(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.extend(_read_jsonl(_proxy_branch_file(path)))
    return rows


def _pair(row: dict[str, Any]) -> list[int] | None:
    pair = row.get("pair") or row.get("forced_pair")
    if isinstance(pair, (list, tuple)) and len(pair) == 2:
        try:
            return sorted((int(pair[0]), int(pair[1])))
        except (TypeError, ValueError):
            return None
    if row.get("task_i") is not None and row.get("task_j") is not None:
        try:
            return sorted((int(row["task_i"]), int(row["task_j"])))
        except (TypeError, ValueError):
            return None
    return None


def _shell_join(command: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in command)


def _command(
    *,
    python: str,
    config: Path,
    instance: str,
    time_limit: int,
    result_dir: Path,
    pair: list[int],
    candidate_log_top_n: int,
) -> list[str]:
    i, j = int(pair[0]), int(pair[1])
    return [
        python,
        "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
        "--config",
        str(config),
        "--instances",
        instance,
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
        python,
        "--timeout-kill-after",
        "30s",
        "--max-workers",
        "1",
        "--quiet",
        "--set",
        f"journey_branch_candidate_priority=force_pair_path:0:{i},{j}",
        "--set",
        f"journey_branch_candidate_log_top_n={int(candidate_log_top_n)}",
        "--set",
        "journey_tail_action_audit_enabled=True",
        "--set",
        "journey_corrected_node_bound_audit_enabled=True",
        "--set",
        "journey_corrected_node_bound_fathom_enabled=False",
        "--set",
        "journey_tail_action_early_branch_enabled=False",
        "--set",
        "journey_tail_action_no_column_early_branch_enabled=False",
    ]


def build_runbook(
    proxy_inputs: list[Path],
    output_dir: Path,
    report: Path,
    *,
    config: Path = DEFAULT_CONFIG,
    python: str = DEFAULT_PYTHON,
    time_limit: int = 260,
    limit: int = 8,
    max_per_instance: int = 1,
    min_proxy_score: float | None = 0.0,
    min_fathom_count: float | None = None,
    min_corrected_bound_gain: float | None = None,
    max_completion_bound_retry_count: float | None = None,
    max_negative_pricing_event_count: float | None = None,
    require_label_observation_complete: bool = False,
    require_promotion_ready: bool = True,
    candidate_log_top_n: int = 200,
) -> dict[str, Any]:
    raw_rows = _load_proxy_rows(proxy_inputs)
    candidates: list[dict[str, Any]] = []
    skipped_missing_instance = 0
    skipped_missing_pair = 0
    skipped_non_root_depth = 0
    skipped_score_threshold = 0
    skipped_fathom_threshold = 0
    skipped_corrected_gain_threshold = 0
    skipped_completion_retry_threshold = 0
    skipped_negative_pricing_threshold = 0
    skipped_incomplete_label = 0
    skipped_promotion_unready = 0
    for row in raw_rows:
        instance = str(row.get("instance") or row.get("instance_path") or "")
        if not instance:
            skipped_missing_instance += 1
            continue
        depth = _int(row.get("depth"), -1)
        if depth != 0:
            skipped_non_root_depth += 1
            continue
        pair = _pair(row)
        if pair is None:
            skipped_missing_pair += 1
            continue
        proxy_score = _float(row.get("proxy_score"), default=float("-inf"))
        if min_proxy_score is not None and proxy_score < float(min_proxy_score):
            skipped_score_threshold += 1
            continue
        fathom_count = _float(row.get("fathom_count"))
        if min_fathom_count is not None and fathom_count < float(min_fathom_count):
            skipped_fathom_threshold += 1
            continue
        corrected_gain = _float(row.get("max_corrected_bound_gain"))
        if (
            min_corrected_bound_gain is not None
            and corrected_gain < float(min_corrected_bound_gain)
        ):
            skipped_corrected_gain_threshold += 1
            continue
        completion_retries = _float(row.get("completion_bound_retry_count"))
        if (
            max_completion_bound_retry_count is not None
            and completion_retries > float(max_completion_bound_retry_count)
        ):
            skipped_completion_retry_threshold += 1
            continue
        negative_pricing_events = _float(row.get("negative_pricing_event_count"))
        if (
            max_negative_pricing_event_count is not None
            and negative_pricing_events > float(max_negative_pricing_event_count)
        ):
            skipped_negative_pricing_threshold += 1
            continue
        if require_label_observation_complete and not bool(row.get("label_observation_complete")):
            skipped_incomplete_label += 1
            continue
        if require_promotion_ready and row.get("promotion_ready") is False:
            skipped_promotion_unready += 1
            continue
        candidates.append(
            {
                "row": row,
                "instance": instance,
                "pair": pair,
                "proxy_score": proxy_score,
                "fathom_count": fathom_count,
                "max_corrected_bound_gain": corrected_gain,
                "completion_bound_retry_count": completion_retries,
                "negative_pricing_event_count": negative_pricing_events,
            }
        )
    candidates.sort(
        key=lambda item: (
            -float(item["proxy_score"]),
            item["instance"],
            int(item["pair"][0]),
            int(item["pair"][1]),
        )
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    run_root = output_dir / "runs"
    per_instance: dict[str, int] = {}
    seen: set[tuple[str, int, int]] = set()
    entries: list[dict[str, Any]] = []
    skipped_duplicate = 0
    skipped_max_per_instance = 0
    for item in candidates:
        if len(entries) >= int(limit):
            break
        instance = str(item["instance"])
        pair = [int(item["pair"][0]), int(item["pair"][1])]
        key = (instance, pair[0], pair[1])
        if key in seen:
            skipped_duplicate += 1
            continue
        seen.add(key)
        if int(max_per_instance) > 0 and per_instance.get(instance, 0) >= int(max_per_instance):
            skipped_max_per_instance += 1
            continue
        per_instance[instance] = per_instance.get(instance, 0) + 1
        experiment = (
            f"{len(entries) + 1:03d}_proxy_full_replay_"
            f"{pair[0]}_{pair[1]}_{_safe_slug(Path(instance).stem)}"
        )
        result_dir = run_root / experiment
        command = _command(
            python=python,
            config=config,
            instance=instance,
            time_limit=time_limit,
            result_dir=result_dir,
            pair=pair,
            candidate_log_top_n=candidate_log_top_n,
        )
        row = item["row"]
        entries.append(
            {
                "experiment": experiment,
                "instance": instance,
                "source_node_id": _int(row.get("source_node_id"), _int(row.get("node_id"), 0)),
                "source_depth": _int(row.get("source_depth"), _int(row.get("depth"), 0)),
                "source_selected_pair": row.get("source_selected_pair"),
                "forced_pair": pair,
                "forced_pair_path_rule": f"force_pair_path:0:{pair[0]},{pair[1]}",
                "source": "child_probe_proxy_branch_row",
                "proxy_score": item["proxy_score"],
                "right_censored": bool(row.get("right_censored", True)),
                "run_statuses": row.get("run_statuses"),
                "max_corrected_bound_gain": row.get("max_corrected_bound_gain"),
                "fathom_count": row.get("fathom_count"),
                "exact_pricing_event_count": row.get("exact_pricing_event_count"),
                "negative_pricing_event_count": row.get("negative_pricing_event_count"),
                "completion_bound_retry_count": row.get("completion_bound_retry_count"),
                "proof_cpu": row.get("proof_cpu"),
                "command": command,
                "shell_command": _shell_join(command),
            }
        )

    commands_path = output_dir / "commands.sh"
    commands_path.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n\n"
        + "\n\n".join(entry["shell_command"] for entry in entries)
        + ("\n" if entries else ""),
        encoding="utf-8",
    )
    payload = {
        "schema_version": "journey_branch_proxy_full_replay_runbook_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "stage4_candidate_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "proxy_input_paths": [str(path) for path in proxy_inputs],
        "config": str(config),
        "time_limit": int(time_limit),
        "limit": int(limit),
        "max_per_instance": int(max_per_instance),
        "min_proxy_score": min_proxy_score,
        "min_fathom_count": min_fathom_count,
        "min_corrected_bound_gain": min_corrected_bound_gain,
        "max_completion_bound_retry_count": max_completion_bound_retry_count,
        "max_negative_pricing_event_count": max_negative_pricing_event_count,
        "require_label_observation_complete": bool(require_label_observation_complete),
        "require_promotion_ready": bool(require_promotion_ready),
        "candidate_log_top_n": int(candidate_log_top_n),
        "raw_proxy_row_count": len(raw_rows),
        "candidate_row_count": len(candidates),
        "entry_count": len(entries),
        "commands_path": str(commands_path),
        "skipped_missing_instance": int(skipped_missing_instance),
        "skipped_missing_pair": int(skipped_missing_pair),
        "skipped_non_root_depth": int(skipped_non_root_depth),
        "skipped_score_threshold": int(skipped_score_threshold),
        "skipped_fathom_threshold": int(skipped_fathom_threshold),
        "skipped_corrected_gain_threshold": int(skipped_corrected_gain_threshold),
        "skipped_completion_retry_threshold": int(skipped_completion_retry_threshold),
        "skipped_negative_pricing_threshold": int(skipped_negative_pricing_threshold),
        "skipped_incomplete_label": int(skipped_incomplete_label),
        "skipped_promotion_unready": int(skipped_promotion_unready),
        "skipped_duplicate": int(skipped_duplicate),
        "skipped_max_per_instance": int(skipped_max_per_instance),
        "entries": entries,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(payload, report)
    return payload


def _write_report(payload: dict[str, Any], report: Path) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Journey Branch Proxy Full-Replay Runbook",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 目的",
        "",
        "从 child-probe proxy branch rows 选择 root forced-pair，生成 full replay 命令。该脚本只生成命令，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        f"commands_path = {payload.get('commands_path', '')}",
        f"raw_proxy_row_count = {payload.get('raw_proxy_row_count')}",
        f"candidate_row_count = {payload.get('candidate_row_count')}",
        f"entry_count = {payload.get('entry_count')}",
        f"time_limit = {payload.get('time_limit')}",
        f"max_per_instance = {payload.get('max_per_instance')}",
        f"min_proxy_score = {payload.get('min_proxy_score')}",
        f"min_fathom_count = {payload.get('min_fathom_count')}",
        f"min_corrected_bound_gain = {payload.get('min_corrected_bound_gain')}",
        f"max_completion_bound_retry_count = {payload.get('max_completion_bound_retry_count')}",
        f"max_negative_pricing_event_count = {payload.get('max_negative_pricing_event_count')}",
        f"require_label_observation_complete = {str(payload.get('require_label_observation_complete')).lower()}",
        f"require_promotion_ready = {str(payload.get('require_promotion_ready')).lower()}",
        f"candidate_log_top_n = {payload.get('candidate_log_top_n')}",
        f"skipped_non_root_depth = {payload.get('skipped_non_root_depth')}",
        f"skipped_score_threshold = {payload.get('skipped_score_threshold')}",
        f"skipped_fathom_threshold = {payload.get('skipped_fathom_threshold')}",
        f"skipped_corrected_gain_threshold = {payload.get('skipped_corrected_gain_threshold')}",
        f"skipped_completion_retry_threshold = {payload.get('skipped_completion_retry_threshold')}",
        f"skipped_negative_pricing_threshold = {payload.get('skipped_negative_pricing_threshold')}",
        f"skipped_incomplete_label = {payload.get('skipped_incomplete_label')}",
        f"skipped_promotion_unready = {payload.get('skipped_promotion_unready')}",
        f"skipped_max_per_instance = {payload.get('skipped_max_per_instance')}",
        f"runs_bpc_or_pricing = {str(payload.get('runs_bpc_or_pricing')).lower()}",
        f"official_bound_effect = {str(payload.get('official_bound_effect')).lower()}",
        f"certificate_effect = {str(payload.get('certificate_effect')).lower()}",
        "```",
        "",
        "## Entries",
        "",
    ]
    for entry in payload.get("entries", []):
        lines.extend(
            [
                f"- {entry['experiment']}: pair={entry['forced_pair']}, "
                f"proxy_score={entry['proxy_score']}, instance={entry['instance']}",
            ]
        )
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "这些命令用于验证 proxy top pair 是否能在 full replay 中转成 target-200 positive 或 hard negative。执行结果必须再经过 branch-impact / counterfactual delta 审计，不能直接作为训练标签或 solver opt-in 证据。",
        ]
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build root forced-pair full-replay commands from child-probe proxy rows. "
            "The script only creates a runbook; it does not run BPC/pricing/RMP."
        )
    )
    parser.add_argument("proxy_input", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--python", default=DEFAULT_PYTHON)
    parser.add_argument("--time-limit", type=int, default=260)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--max-per-instance", type=int, default=1)
    parser.add_argument("--min-proxy-score", type=float, default=0.0)
    parser.add_argument("--min-fathom-count", type=float, default=None)
    parser.add_argument("--min-corrected-bound-gain", type=float, default=None)
    parser.add_argument("--max-completion-bound-retry-count", type=float, default=None)
    parser.add_argument("--max-negative-pricing-event-count", type=float, default=None)
    parser.add_argument("--require-label-observation-complete", action="store_true")
    parser.add_argument("--allow-promotion-unready", action="store_true")
    parser.add_argument("--candidate-log-top-n", type=int, default=200)
    args = parser.parse_args()
    payload = build_runbook(
        list(args.proxy_input),
        args.output_dir,
        args.report,
        config=args.config,
        python=args.python,
        time_limit=args.time_limit,
        limit=args.limit,
        max_per_instance=args.max_per_instance,
        min_proxy_score=args.min_proxy_score,
        min_fathom_count=args.min_fathom_count,
        min_corrected_bound_gain=args.min_corrected_bound_gain,
        max_completion_bound_retry_count=args.max_completion_bound_retry_count,
        max_negative_pricing_event_count=args.max_negative_pricing_event_count,
        require_label_observation_complete=args.require_label_observation_complete,
        require_promotion_ready=not args.allow_promotion_unready,
        candidate_log_top_n=args.candidate_log_top_n,
    )
    print(json.dumps({k: v for k, v in payload.items() if k != "entries"}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
