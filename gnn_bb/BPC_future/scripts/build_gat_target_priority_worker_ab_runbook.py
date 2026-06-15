#!/usr/bin/env python3
"""Build a guarded GAT target-priority worker A/B runbook.

The generated commands keep the current production boundary:

* 5/10 commands are no-regression checks with the mainline learning path kept.
* 20-task worker commands are explicit opt-in target-priority probes on top
  of the same mainline learning path that produced the captured target context.
* No command enables certificate effect or official lower-bound shortcuts.
* Shell commands are emitted with shlex.join so arc option ids such as
  ``0->20:low_risk:2`` cannot be interpreted as redirection.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
from typing import Any


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/gat_target_priority_worker_ab_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_gat_target_priority_worker_ab_runbook_zh.md"
)
PYTHON = "/home/kai/miniconda3/envs/ecole/bin/python"
DEFAULT_LOGICAL_GRAPH_ROOT = Path("BPC_future/logical_graph")

SCALE_CONFIG = {
    5: "BPC_future/configs/moon_trek_5_journey.yaml",
    10: "BPC_future/configs/moon_trek_10_journey.yaml",
    20: "BPC_future/configs/moon_trek_20_smoke.yaml",
}

NO_LEARNING_OVERRIDES = (
    "journey_learning_enabled=False",
    "journey_learning_required=False",
    "journey_learning_fail_hard=False",
    "journey_learning_force_light_profile_pricing=False",
    "journey_learning_prewarm_enabled=False",
    "journey_learning_pricing_enabled=False",
)

WORKER_BASE_OVERRIDES = (
    "journey_sharded_pulse_hidden_negative_worker_enabled=True",
    "journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe",
    "journey_sharded_pulse_hidden_negative_worker_log_skips=True",
    "journey_sharded_pulse_worker_current_probe_enabled=True",
    "journey_sharded_pulse_worker_current_probe_time_limit=1.0",
    "journey_sharded_pulse_worker_current_probe_max_recursions=50000",
    "journey_sharded_pulse_worker_current_probe_min_tasks=20",
    "journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0",
    "journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16",
    "journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True",
    "journey_sharded_pulse_hidden_negative_worker_archive_enabled=True",
    "journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True",
    "journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True",
    "journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16",
    "journey_sharded_pulse_hidden_negative_worker_max_columns=4",
    "journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True",
    "journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True",
    "journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True",
    "journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True",
    "journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True",
)

TASK20_CONTEXT_CAPTURE_OVERRIDES = (
    "journey_counterfactual_replay_capture_enabled=True",
    "journey_counterfactual_replay_capture_active_basis_enabled=True",
    "journey_counterfactual_replay_capture_forbidden_signatures_enabled=True",
    "journey_counterfactual_replay_capture_log_empty=True",
    "journey_counterfactual_replay_capture_active_basis_max_rows=96",
    "journey_counterfactual_replay_capture_max_journeys=32",
    "journey_counterfactual_replay_capture_pool_max_journeys=256",
    "journey_counterfactual_replay_capture_forbidden_signature_max_count=256",
)

REQUIRED_CANDIDATE_CONTEXT_FIELDS = (
    "expected_context_hash",
    "true_dual_hash",
    "cut_hash",
    "branch_hash",
    "forbidden_signature_hash",
    "active_hash_before",
    "pool_signature_hash",
    "pool_task_set_hash",
)

DEFAULT_CANDIDATES = (
    {
        "name": "apollo20_sector_wave_7e0afd09753effed_target_19",
        "instance": (
            "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/"
            "apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json"
        ),
        "expected_context_hash": "7e0afd09753effed",
        "true_dual_hash": "4fb2dc95e30f31c4",
        "cut_hash": "d653e60106177bb4",
        "branch_hash": "da39a3ee5e6b4b0d",
        "forbidden_signature_hash": "4a0466dbb3cb0ca3",
        "active_hash_before": "f5e56fbba74784b5",
        "pool_signature_hash": "5b033e33a1d57de2",
        "pool_task_set_hash": "07344d8ff99d9697",
        "target_sequence": (19,),
        "target_arc_option_sequence": (
            "0->19:low_risk:2",
            "19->0:low_risk:2",
        ),
    },
)


def _split_csv(value: Any) -> tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    if isinstance(value, (list, tuple)):
        return tuple(str(part).strip() for part in value if str(part).strip())
    return (str(value).strip(),) if str(value).strip() else tuple()


def _target_sequence(value: Any) -> tuple[int, ...]:
    return tuple(int(part) for part in _split_csv(value))


def _target_arc_options(value: Any) -> tuple[str, ...]:
    return _split_csv(value)


def _instance(path: Path | str) -> str:
    return str(Path(path))


def _small_instance_paths(logical_graph_root: Path, scale: int) -> list[str]:
    roots = (
        logical_graph_root / f"tasks_{int(scale):03d}" / "sector-wave" / "apollo15_20km",
        logical_graph_root
        / f"tasks_{int(scale):03d}"
        / "sector-wave"
        / "tranquillitatis_balmer_like_20km",
    )
    paths: list[str] = []
    for root in roots:
        paths.extend(str(path) for path in sorted(root.glob("*_01_seed*_logical_graph.json")))
    if not paths:
        for root in roots:
            paths.extend(str(path) for path in sorted(root.glob("*_logical_graph.json"))[:1])
    return paths[:2]


def _command(parts: list[str]) -> str:
    return shlex.join(parts)


def _single_run_command(
    *,
    config: str,
    instance: str,
    output_dir: Path,
    profile: str,
    time_limit: float,
    overrides: tuple[str, ...] = tuple(),
) -> str:
    run_dir = output_dir / profile
    parts = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        PYTHON,
        "BPC_future/scripts/run_bpc_future.py",
        "--config",
        config,
        "--instance",
        instance,
        "--time-limit",
        f"{float(time_limit):.6f}",
        "--results-csv",
        str(run_dir / "results.csv"),
        "--log-dir",
        str(run_dir / "logs"),
        "--solution-dir",
        str(run_dir / "solutions"),
        "--quiet",
    ]
    for override in overrides:
        parts.extend(["--set", str(override)])
    return _command(parts)


def _batch_run_command(
    *,
    config: str,
    instances: list[str],
    output_dir: Path,
    profile: str,
    time_limit: float,
    max_workers: int,
) -> str:
    run_dir = output_dir / profile
    parts = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        PYTHON,
        "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
        "--config",
        config,
        "--time-limit",
        f"{float(time_limit):.6f}",
        "--timeout-kill-after",
        "30s",
        "--max-workers",
        str(int(max_workers)),
        "--results-csv",
        str(run_dir / "results.csv"),
        "--log-dir",
        str(run_dir / "logs"),
        "--solution-dir",
        str(run_dir / "solutions"),
        "--run-log-dir",
        str(run_dir / "run_logs"),
        "--quiet",
        "--instances",
    ]
    parts.extend(instances)
    return _command(parts)


def _load_candidates(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return [dict(item) for item in DEFAULT_CANDIDATES]
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "candidates" in payload:
        payload = payload["candidates"]
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise ValueError("candidate file must contain an object, a list, or {'candidates': [...]}")
    return [dict(item) for item in payload]


def _normalized_candidate(raw: dict[str, Any], index: int) -> dict[str, Any]:
    sequence = _target_sequence(raw.get("target_sequence") or raw.get("target_tasks"))
    priority_sequence = _target_sequence(raw.get("target_priority_sequence") or sequence)
    arc_options = _target_arc_options(
        raw.get("target_arc_option_sequence") or raw.get("arc_option_sequence")
    )
    if not sequence:
        raise ValueError(f"candidate {index} has no target_sequence")
    if not raw.get("instance"):
        raise ValueError(f"candidate {index} has no instance")
    if not raw.get("expected_context_hash"):
        raise ValueError(f"candidate {index} has no expected_context_hash")
    normalized = {
        "name": str(raw.get("name") or f"candidate_{index:03d}"),
        "instance": _instance(raw["instance"]),
        "expected_context_hash": str(raw["expected_context_hash"]),
        "target_sequence": sequence,
        "target_priority_sequence": priority_sequence,
        "target_arc_option_sequence": arc_options,
        "target_sortie_traces": list(raw.get("target_sortie_traces") or []),
        "capture_pricing_kind": str(raw.get("capture_pricing_kind") or ""),
    }
    for field in (
        "cell",
        "ordinal_cell",
        "recommendation_bucket",
        "reason",
        "score",
        "cell_positive_rate",
        "cell_positive_count",
        "cell_training_negative_count",
        "positive_gap",
        "negative_gap",
    ):
        if field in raw:
            normalized[field] = raw[field]
    for field in REQUIRED_CANDIDATE_CONTEXT_FIELDS:
        if field == "expected_context_hash":
            continue
        normalized[field] = str(raw.get(field) or "")
    normalized["candidate_context_complete"] = all(
        str(normalized.get(field) or "").strip()
        for field in REQUIRED_CANDIDATE_CONTEXT_FIELDS
    )
    return normalized


def _worker_before_heuristic_enabled(candidate: dict[str, Any]) -> bool:
    capture_kind = str(candidate.get("capture_pricing_kind") or "").strip().lower()
    if capture_kind == "exact":
        return False
    if capture_kind == "heuristic":
        return True
    return False


def _worker_before_exact_enabled(candidate: dict[str, Any]) -> bool:
    capture_kind = str(candidate.get("capture_pricing_kind") or "").strip().lower()
    return capture_kind == "exact"


def _worker_overrides(candidate: dict[str, Any]) -> tuple[str, ...]:
    target_sequence = ",".join(str(task) for task in candidate["target_sequence"])
    priority_sequence = ",".join(str(task) for task in candidate["target_priority_sequence"])
    arc_sequence = ",".join(str(option) for option in candidate["target_arc_option_sequence"])
    target_traces = json.dumps(
        candidate.get("target_sortie_traces") or [],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    overrides = [
        *WORKER_BASE_OVERRIDES,
        (
            "journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled="
            f"{_worker_before_heuristic_enabled(candidate)}"
        ),
        (
            "journey_sharded_pulse_hidden_negative_worker_before_exact_enabled="
            f"{_worker_before_exact_enabled(candidate)}"
        ),
        (
            "journey_sharded_pulse_hidden_negative_worker_expected_context_hash="
            f"{candidate['expected_context_hash']}"
        ),
        (
            "journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence="
            f"{priority_sequence}"
        ),
        (
            "journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence="
            f"{priority_sequence}"
        ),
        (
            "journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence="
            f"{target_sequence}"
        ),
        (
            "journey_sharded_pulse_hidden_negative_worker_target_materialization_traces="
            f"{target_traces}"
        ),
    ]
    if arc_sequence:
        overrides.append(
            "journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence="
            f"{arc_sequence}"
        )
    return tuple(overrides)


def _has_certificate_effect(command: str) -> bool:
    forbidden = (
        "journey_final_judge_sharding_enabled=True",
        "journey_pulse_final_judge_enabled=True",
        "journey_sharded_pulse_audit_allow_certificate_effect=True",
        "allow_test_dummy_certificate=True",
        "dummy_certificate=True",
        "certificate_enabled=True",
        "official_bound_effect=True",
    )
    return any(token in command for token in forbidden)


def build_runbook(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report: Path = DEFAULT_REPORT,
    logical_graph_root: Path = DEFAULT_LOGICAL_GRAPH_ROOT,
    candidates_file: Path | None = None,
    small_time_limit: float = 60.0,
    twenty_time_limit: float = 85.0,
    max_workers: int = 1,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates = [
        _normalized_candidate(raw, index)
        for index, raw in enumerate(_load_candidates(candidates_file), start=1)
    ]

    commands: list[dict[str, Any]] = []
    small_checks: list[dict[str, Any]] = []
    for scale in (5, 10):
        instances = _small_instance_paths(Path(logical_graph_root), scale)
        profile = f"task{scale:03d}_mainline_no_regression_gat_kept"
        command = _batch_run_command(
            config=SCALE_CONFIG[scale],
            instances=instances,
            output_dir=output_dir,
            profile=profile,
            time_limit=float(small_time_limit),
            max_workers=int(max_workers),
        )
        commands.append(
            {
                "command_type": profile,
                "description": (
                    f"Run task-{scale} no-regression with mainline GAT/learning kept; "
                    "no new worker or gate is enabled."
                ),
                "command": command,
            }
        )
        small_checks.append(
            {
                "task_count": scale,
                "instances": instances,
                "instance_count": len(instances),
            }
        )

    candidate_runs: list[dict[str, Any]] = []
    for candidate in candidates:
        base_profile = f"task020_{candidate['name']}_mainline_baseline"
        worker_profile = f"task020_{candidate['name']}_target_priority_worker"
        baseline_command = _single_run_command(
            config=SCALE_CONFIG[20],
            instance=candidate["instance"],
            output_dir=output_dir,
            profile=base_profile,
            time_limit=float(twenty_time_limit),
            overrides=TASK20_CONTEXT_CAPTURE_OVERRIDES,
        )
        worker_command = _single_run_command(
            config=SCALE_CONFIG[20],
            instance=candidate["instance"],
            output_dir=output_dir,
            profile=worker_profile,
            time_limit=float(twenty_time_limit),
            overrides=(*TASK20_CONTEXT_CAPTURE_OVERRIDES, *_worker_overrides(candidate)),
        )
        commands.extend(
            [
                {
                    "command_type": base_profile,
                    "description": (
                        "Run task-20 mainline baseline for the same target context. "
                        "Learning/GAT stays enabled so the captured context can be reached."
                    ),
                    "command": baseline_command,
                },
                {
                    "command_type": worker_profile,
                    "description": (
                        "Run explicit opt-in target-priority Pulse worker. This may add "
                        "true-RC negative columns but cannot certify no-negative."
                    ),
                    "command": worker_command,
                },
            ]
        )
        candidate_runs.append(
            {
                **candidate,
                "baseline_csv": str(output_dir / base_profile / "results.csv"),
                "worker_csv": str(output_dir / worker_profile / "results.csv"),
            }
        )

    checks = {
        "all_small_instances_exist": all(
            Path(instance).exists()
            for item in small_checks
            for instance in item["instances"]
        ),
        "all_candidate_instances_exist": all(
            Path(item["instance"]).exists() for item in candidate_runs
        ),
        "all_candidates_have_full_context": all(
            bool(item.get("candidate_context_complete")) for item in candidate_runs
        ),
        "small_commands_keep_mainline_gat": all(
            "journey_learning_enabled=False" not in item["command"]
            and "hidden_negative_worker_enabled=True" not in item["command"]
            for item in commands
            if item["command_type"].startswith(("task005", "task010"))
        ),
        "task20_commands_keep_capture_learning_policy": all(
            "journey_learning_enabled=False" not in item["command"]
            for item in commands
            if item["command_type"].startswith("task020_")
        ),
        "worker_commands_have_expected_context": all(
            item["expected_context_hash"] in next(
                command["command"]
                for command in commands
                if command["command_type"] == f"task020_{item['name']}_target_priority_worker"
            )
            for item in candidate_runs
        ),
        "task20_commands_capture_actual_contexts": all(
            "journey_counterfactual_replay_capture_enabled=True" in item["command"]
            for item in commands
            if item["command_type"].startswith("task020_")
        ),
        "commands_have_no_certificate_effect": not any(
            _has_certificate_effect(item["command"]) for item in commands
        ),
        "arc_option_values_are_shell_quoted": all(
            not item["target_arc_option_sequence"]
            or any(
                "target_arc_option_priority_sequence=" in command["command"]
                and "'" in command["command"]
                and "->" in command["command"]
                for command in commands
                if command["command_type"] == f"task020_{item['name']}_target_priority_worker"
            )
            for item in candidate_runs
        ),
    }
    summary = {
        "schema_version": "gat_target_priority_worker_ab_runbook_v1",
        "status": "ready",
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "default_enabled": False,
        "certificate_ready": False,
        "official_bound_effect": False,
        "online_effect_scope": "explicit_task20_worker_commands_only",
        "mainline_gat_kept_for_5_10": True,
        "mainline_gat_kept_for_20_context_replay": True,
        "candidate_policy": {
            "gat_role": "embedding_and_trajectory_impact_expression",
            "knn_ood_role": "safety_shell",
            "safe_negative_action": "HIGH_PRIORITY",
            "unsafe_negative_action": "DELAY_QUEUE",
            "negative_discard_allowed": False,
            "certificate_effect": False,
            "worker_stage_policy": "match_capture_pricing_kind: heuristic_before_heuristic_exact_before_exact",
            "context_miss_policy": "capture_actual_reached_contexts_for_next_iteration",
        },
        "required_candidate_context_fields": list(REQUIRED_CANDIDATE_CONTEXT_FIELDS),
        "small_no_regression": small_checks,
        "candidate_runs": candidate_runs,
        "commands": commands,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GAT Target-Priority Worker A/B Runbook",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "生成下一轮 5/10 no-regression 与 20-task ROI A/B 命令。GAT 仍只负责 "
        "embedding / trajectory impact 表达，kNN/OOD 只做安全壳；通过安全壳的 "
        "true-RC negative 可优先进入 worker target，不通过的负列进入 DELAY_QUEUE，"
        "不能永久丢弃，也不能参与 certificate。",
        "",
        "## 机器字段",
        "",
        "```text",
        "gat_target_priority_worker_ab_runbook = current",
        f"status = {summary['status']}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"default_enabled = {str(summary['default_enabled']).lower()}",
        f"certificate_ready = {str(summary['certificate_ready']).lower()}",
        f"official_bound_effect = {str(summary['official_bound_effect']).lower()}",
        "required_candidate_context_field_count = "
        f"{len(summary['required_candidate_context_fields'])}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## Candidate Policy",
        "",
        "```json",
        json.dumps(summary["candidate_policy"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Candidate Runs",
        "",
        "```json",
        json.dumps(summary["candidate_runs"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Commands",
        "",
    ]
    for item in summary["commands"]:
        lines.extend(
            [
                f"### {item['command_type']}",
                "",
                item["description"],
                "",
                "```bash",
                item["command"],
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## 边界",
            "",
            "- 5/10 命令不关闭主线 GAT/learning，也不启用新 worker；",
            "- 20 baseline/worker 命令也不关闭主线 GAT/learning，避免候选捕获上下文无法复现；",
            "- 20 baseline/worker 命令开启 counterfactual replay capture；如果旧 target context 没到，仍保留实际到达的 context 供下一轮候选抽取；",
            "- 20 worker 命令是显式 opt-in，只验证 target-priority ROI；",
            "- 20 worker 候选必须带完整 context / dual / cuts / branch / pool hash；",
            "- 所有命令都不启用 sharded Pulse certificate 或 official lower-bound effect；",
            "- 含 `->` 的 arc-option 配置通过 `shlex.join` 自动引用，不能手工去掉引号；",
            "- 该 runbook 不是生产开关，跑完后仍需看 5/10 no-regression 和 20-task ROI。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--logical-graph-root", type=Path, default=DEFAULT_LOGICAL_GRAPH_ROOT)
    parser.add_argument("--candidates-file", type=Path, default=None)
    parser.add_argument("--small-time-limit", type=float, default=60.0)
    parser.add_argument("--twenty-time-limit", type=float, default=85.0)
    parser.add_argument("--max-workers", type=int, default=1)
    args = parser.parse_args(argv)
    summary = build_runbook(
        output_dir=args.output_dir,
        report=args.report,
        logical_graph_root=args.logical_graph_root,
        candidates_file=args.candidates_file,
        small_time_limit=float(args.small_time_limit),
        twenty_time_limit=float(args.twenty_time_limit),
        max_workers=int(args.max_workers),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
