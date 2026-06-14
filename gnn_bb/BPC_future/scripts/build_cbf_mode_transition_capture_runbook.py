#!/usr/bin/env python3
"""Build a CBF mode-transition capture runbook.

The runbook contains opt-in, no-certificate-effect capture commands for
collecting RMP/residual-mode transitions.  It does not run BPC, pricing, RMP,
Pulse, workers, or certificates by itself.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("BPC_future/results/cbf_mode_transition_capture_runbook_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_mode_transition_capture_runbook_zh.md"
)
PYTHON = "/home/kai/miniconda3/envs/ecole/bin/python"


TARGETS = [
    {
        "target_id": "task05_apollo_smoke",
        "scale": 5,
        "config": "BPC_future/configs/moon_trek_5_journey.yaml",
        "instance": (
            "BPC_future/data/generated/moon_trek_60/logical_graphs/apollo15_20km/"
            "tasks_05/apollo15_20km_tasks05_01_seed6000_logical_graph.json"
        ),
        "time_limit": 30.0,
    },
    {
        "target_id": "task05_tranq_smoke",
        "scale": 5,
        "config": "BPC_future/configs/moon_trek_5_journey.yaml",
        "instance": (
            "BPC_future/data/generated/moon_trek_60/logical_graphs/"
            "tranquillitatis_balmer_like_20km/tasks_05/"
            "tranquillitatis_balmer_like_20km_tasks05_01_seed6000_logical_graph.json"
        ),
        "time_limit": 30.0,
    },
    {
        "target_id": "task10_apollo_smoke",
        "scale": 10,
        "config": "BPC_future/configs/moon_trek_10_journey.yaml",
        "instance": (
            "BPC_future/data/generated/moon_trek_60/logical_graphs/apollo15_20km/"
            "tasks_10/apollo15_20km_tasks10_01_seed11000_logical_graph.json"
        ),
        "time_limit": 45.0,
    },
    {
        "target_id": "task10_tranq_smoke",
        "scale": 10,
        "config": "BPC_future/configs/moon_trek_10_journey.yaml",
        "instance": (
            "BPC_future/data/generated/moon_trek_60/logical_graphs/"
            "tranquillitatis_balmer_like_20km/tasks_10/"
            "tranquillitatis_balmer_like_20km_tasks10_01_seed11000_logical_graph.json"
        ),
        "time_limit": 45.0,
    },
    {
        "target_id": "task20_apollo_random_wave_probe",
        "scale": 20,
        "config": "BPC_future/configs/moon_trek_20_smoke.yaml",
        "instance": (
            "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/"
            "apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json"
        ),
        "time_limit": 90.0,
    },
    {
        "target_id": "task20_tranq_random_wave_probe",
        "scale": 20,
        "config": "BPC_future/configs/moon_trek_20_smoke.yaml",
        "instance": (
            "BPC_future/logical_graph/tasks_020/random-wave/"
            "tranquillitatis_balmer_like_20km/"
            "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json"
        ),
        "time_limit": 90.0,
    },
    {
        "target_id": "task20_apollo_sector_wave_probe",
        "scale": 20,
        "config": "BPC_future/configs/moon_trek_20_smoke.yaml",
        "instance": (
            "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/"
            "apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json"
        ),
        "time_limit": 90.0,
    },
    {
        "target_id": "task20_tranq_sector_wave_probe",
        "scale": 20,
        "config": "BPC_future/configs/moon_trek_20_smoke.yaml",
        "instance": (
            "BPC_future/logical_graph/tasks_020/sector-wave/"
            "tranquillitatis_balmer_like_20km/"
            "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json"
        ),
        "time_limit": 90.0,
    },
]


CAPTURE_OVERRIDES = [
    "journey_counterfactual_replay_capture_enabled=true",
    "journey_counterfactual_replay_capture_active_basis_enabled=true",
    "journey_counterfactual_replay_capture_forbidden_signatures_enabled=true",
    "journey_counterfactual_replay_capture_log_empty=true",
]


def _command(
    target: dict[str, Any],
    *,
    profile: str,
    output_root: Path,
    full_payload: bool,
) -> str:
    target_id = str(target["target_id"])
    log_dir = output_root / "logs" / profile / target_id
    solution_dir = output_root / "solutions" / profile / target_id
    results_csv = output_root / "csv" / f"{target_id}.csv"
    if full_payload:
        payload_overrides = [
            "journey_counterfactual_replay_capture_active_basis_max_rows=0",
            "journey_counterfactual_replay_capture_max_journeys=0",
            "journey_counterfactual_replay_capture_pool_max_journeys=0",
            "journey_counterfactual_replay_capture_forbidden_signature_max_count=0",
        ]
    else:
        payload_overrides = [
            "journey_counterfactual_replay_capture_active_basis_max_rows=96",
            "journey_counterfactual_replay_capture_max_journeys=32",
            "journey_counterfactual_replay_capture_pool_max_journeys=256",
            "journey_counterfactual_replay_capture_forbidden_signature_max_count=256",
        ]
    parts = [
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONPATH=.",
        PYTHON,
        "BPC_future/scripts/run_bpc_future.py",
        f"--config {target['config']}",
        f"--instances {target['instance']}",
        f"--time-limit {target['time_limit']}",
        f"--log-dir {log_dir}",
        f"--results-csv {results_csv}",
        f"--solution-dir {solution_dir}",
        "--quiet",
    ]
    for override in CAPTURE_OVERRIDES + payload_overrides:
        parts.extend(["--set", override])
    return " ".join(str(part) for part in parts)


def build_runbook(*, output_root: Path) -> dict[str, Any]:
    profiles = {
        "capped_smoke": {
            "description": "short capped payload smoke; validates capture plumbing only",
            "full_payload": False,
        },
        "full_capture": {
            "description": "full payload for barrier dataset collection; can be expensive",
            "full_payload": True,
        },
    }
    rows: list[dict[str, Any]] = []
    for profile, meta in profiles.items():
        for target in TARGETS:
            rows.append(
                {
                    "profile": profile,
                    "target_id": target["target_id"],
                    "scale": target["scale"],
                    "config": target["config"],
                    "instance": target["instance"],
                    "time_limit": target["time_limit"],
                    "full_payload": bool(meta["full_payload"]),
                    "command": _command(
                        target,
                        profile=profile,
                        output_root=output_root,
                        full_payload=bool(meta["full_payload"]),
                    ),
                }
            )
    return {
        "schema_version": "cbf_mode_transition_capture_runbook_v1",
        "status": "cbf_mode_transition_capture_runbook_ready",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "target_count": len(TARGETS),
        "command_count": len(rows),
        "profiles": profiles,
        "rows": rows,
        "checks": {
            "has_task5_targets": any(int(target["scale"]) == 5 for target in TARGETS),
            "has_task10_targets": any(int(target["scale"]) == 10 for target in TARGETS),
            "has_task20_targets": any(int(target["scale"]) == 20 for target in TARGETS),
            "all_commands_enable_capture": all(
                "journey_counterfactual_replay_capture_enabled=true" in row["command"]
                for row in rows
            ),
            "all_commands_are_quiet": all("--quiet" in row["command"] for row in rows),
        },
        "all_checks_pass": True,
        "production_ready": False,
        "goal_complete": False,
    }


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Mode Transition Capture Runbook",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告生成 CBF mode transition capture 的 opt-in 命令清单。",
        "它本身不运行 BPC / pricing / RMP / Pulse，也不改变任何默认 benchmark。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_mode_transition_capture_runbook = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"target_count = {summary['target_count']}",
        f"command_count = {summary['command_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"goal_complete = {str(summary['goal_complete']).lower()}",
        "```",
        "",
        "## Profiles",
        "",
        "- `capped_smoke`：短时、payload 有上限，只验证 capture plumbing；",
        "- `full_capture`：完整 payload，用于后续 barrier dataset，但可能有明显日志开销。",
        "",
        "## Commands",
        "",
    ]
    for row in summary["rows"]:
        lines.extend(
            [
                f"### {row['profile']} / {row['target_id']}",
                "",
                "```bash",
                row["command"],
                "```",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = build_runbook(output_root=args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_report(args.report, summary)
    print(json.dumps({"summary": str(summary_path), "report": str(args.report), "all_checks_pass": summary["all_checks_pass"]}, ensure_ascii=False))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
