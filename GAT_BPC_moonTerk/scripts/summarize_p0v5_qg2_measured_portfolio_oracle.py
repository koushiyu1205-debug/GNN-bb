#!/usr/bin/env python3
"""Summarize the measured P0V5 QG2 arm portfolio without solver replays.

This is a read-only, development-only diagnostic.  It computes two empirical
post-hoc ceilings from replay JSON files that already exist:

* reachable QG2: best of Q0 and the three leaked-potential bucket arms;
* measured portfolio: best of Q0, QD1, QB1, and the three QG2 bucket arms.

The result is not a perfect queue oracle and has no training authority.  In
particular, QD1/QB1 operate on a broader ordering surface than frozen QG2, so
their winning outcomes must not be converted into QG2 label-level targets.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import json
import math
import os
from pathlib import Path
import random
import sys
import time
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import maintain_p0v5_qg2_live_markdown as live  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
DEFAULT_ORACLE_DIR = DEFAULT_RUN_ROOT / "oracle_qg2_action_surface_v2_stage1"
DEFAULT_JSON = DEFAULT_RUN_ROOT / "qg2_measured_portfolio_oracle_live.json"
DEFAULT_MARKDOWN = DEFAULT_RUN_ROOT / "P0V5_QG2_MEASURED_PORTFOLIO_ORACLE.md"

QG2_REACHABLE_ARMS = (
    "Q0",
    "QO2-1e-4",
    "QO2-3e-4",
    "QO2-1e-3",
)
MEASURED_PORTFOLIO_ARMS = (
    "Q0",
    "QD1",
    "QB1",
    "QO2-1e-4",
    "QO2-3e-4",
    "QO2-1e-3",
)
MILESTONES = {"ADMISSION_BATCH_READY", "EXACT_PROOF_COMPLETION"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    parser.add_argument("--oracle-dir")
    parser.add_argument("--json-output")
    parser.add_argument("--markdown-output")
    parser.add_argument("--max-contexts", type=int, default=200)
    parser.add_argument("--max-contexts-per-scale", type=int, default=100)
    parser.add_argument("--watch-pid", action="append", type=int, default=[])
    parser.add_argument("--poll-sec", type=float, default=30.0)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    run_root = _resolve(args.run_root)
    oracle_dir = (
        _resolve(args.oracle_dir)
        if args.oracle_dir
        else run_root / "oracle_qg2_action_surface_v2_stage1"
    )
    json_output = (
        _resolve(args.json_output)
        if args.json_output
        else run_root / DEFAULT_JSON.name
    )
    markdown_output = (
        _resolve(args.markdown_output)
        if args.markdown_output
        else run_root / DEFAULT_MARKDOWN.name
    )
    watched = tuple(dict.fromkeys(int(pid) for pid in args.watch_pid))
    poll = max(5.0, min(300.0, float(args.poll_sec)))

    while True:
        report = collect(
            run_root=run_root,
            oracle_dir=oracle_dir,
            maximum_contexts=args.max_contexts,
            maximum_contexts_per_scale=args.max_contexts_per_scale,
        )
        report["watch_pids"] = list(watched)
        report["watch_pids_alive"] = [pid for pid in watched if _pid_alive(pid)]
        _atomic_write(json_output, json.dumps(
            report, indent=2, sort_keys=True, ensure_ascii=False
        ) + "\n")
        _atomic_write(markdown_output, render_markdown(report))
        print(json.dumps({
            "status": "updated",
            "context_count": report["context_count"],
            "json_output": str(json_output),
            "markdown_output": str(markdown_output),
            "watch_pids_alive": report["watch_pids_alive"],
        }, sort_keys=True), flush=True)
        if args.once:
            return 0
        if watched and not report["watch_pids_alive"]:
            return 0
        time.sleep(poll)


def collect(
    *,
    run_root: Path,
    oracle_dir: Path,
    maximum_contexts: int,
    maximum_contexts_per_scale: int,
) -> dict[str, Any]:
    index_path = run_root / "qg2_clean_v2_live_snapshot_index.json"
    index = _load(index_path) or {}
    selected = live._bounded_selected_state_prefixes(
        index,
        maximum=maximum_contexts,
        per_scale=maximum_contexts_per_scale,
    )
    instance_by_state = live._index_instance_by_state(index)
    rows: list[dict[str, Any]] = []
    rejection_counts: Counter[str] = Counter()

    for context_dir in sorted(oracle_dir.glob("[0-9][0-9]_*")):
        try:
            scale_text, state = context_dir.name.split("_", 1)
            scale = int(scale_text)
        except (ValueError, IndexError):
            continue
        if scale not in (30, 50):
            continue
        if selected is not None and (scale, state) not in selected:
            continue
        control = _load(context_dir / live.ARM_FILES["Q0"])
        if control is None:
            continue
        control_reason = _control_ineligible_reason(control)
        if control_reason:
            rejection_counts[f"control:{control_reason}"] += 1
            continue
        q0_wall = live._wall(control)
        assert q0_wall is not None

        arm_payloads = {
            arm: _load(context_dir / live.ARM_FILES[arm])
            for arm in MEASURED_PORTFOLIO_ARMS
            if arm != "Q0"
        }
        # Do not let a context currently being written enter the aggregate as
        # a Q0-only tie.  A censored arm is a valid observed outcome, but every
        # declared initial arm must at least have produced its replay record.
        if any(payload is None for payload in arm_payloads.values()):
            rejection_counts["context:initial_arm_set_incomplete"] += 1
            continue

        eligible: dict[str, float] = {"Q0": q0_wall}
        arm_rejections: dict[str, str] = {}
        for arm in MEASURED_PORTFOLIO_ARMS:
            if arm == "Q0":
                continue
            replay = arm_payloads[arm]
            reason = _arm_ineligible_reason(control, replay)
            if reason:
                arm_rejections[arm] = reason
                rejection_counts[f"arm:{reason}"] += 1
                continue
            wall = live._wall(replay)
            assert wall is not None
            eligible[arm] = wall

        qg2_arm, qg2_wall = _best(eligible, QG2_REACHABLE_ARMS)
        portfolio_arm, portfolio_wall = _best(
            eligible, MEASURED_PORTFOLIO_ARMS
        )
        rows.append({
            "scale": scale,
            "state": state,
            "instance_id": str(
                control.get("instance_id")
                or instance_by_state.get((scale, state))
                or ""
            ),
            "instance_hash": str(
                control.get("instance_content_hash")
                or control.get("instance_hash")
                or instance_by_state.get((scale, state))
                or ""
            ),
            "milestone": str(control["milestone_kind"]),
            "q0_wall_sec": q0_wall,
            "eligible_arm_walls_sec": eligible,
            "arm_rejections": arm_rejections,
            "qg2_reachable_best_arm": qg2_arm,
            "qg2_reachable_best_wall_sec": qg2_wall,
            "qg2_reachable_ratio": qg2_wall / q0_wall,
            "portfolio_best_arm": portfolio_arm,
            "portfolio_best_wall_sec": portfolio_wall,
            "portfolio_ratio": portfolio_wall / q0_wall,
            "qg2_vs_portfolio_wall_gap_sec": qg2_wall - portfolio_wall,
            "qg2_captured_portfolio_savings_fraction": _captured_fraction(
                q0_wall, qg2_wall, portfolio_wall
            ),
        })

    rows.sort(key=lambda row: (row["scale"], row["state"]))
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_measured_portfolio_oracle.v1"
        ),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "development_only": True,
        "deployable": False,
        "training_authority": False,
        "starts_no_solver_process": True,
        "interpretation": (
            "post_hoc_empirical_ceiling_over_completed_exact_safe_measured_arms"
        ),
        "not_a_perfect_queue_oracle": True,
        "qg2_label_supervision_authority": (
            "none_heterogeneous_arm_winners_are_not_qg2_label_targets"
        ),
        "qg2_reachable_arms": list(QG2_REACHABLE_ARMS),
        "measured_portfolio_arms": list(MEASURED_PORTFOLIO_ARMS),
        "random_arms_excluded": [
            "Random61635", "Random91267", "Random170141"
        ],
        "context_budget": {
            "maximum": maximum_contexts,
            "per_scale": maximum_contexts_per_scale,
        },
        "context_count": len(rows),
        "rejection_counts": dict(sorted(rejection_counts.items())),
        "aggregate": _aggregate(rows),
        "contexts": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P0V5 QG2 Measured Portfolio Oracle",
        "",
        "> 这是对已完成、exact-safe、同里程碑 arm 的事后经验上界；不启动新求解。",
        "> 它不是完美 queue oracle，也不授权训练或部署。QD1/QB1 的赢家不能直接变成 QG2 label 标签。",
        "",
        f"- 更新时间：`{report['generated_at']}`",
        f"- 可比较 context：`{report['context_count']}`",
        f"- 训练授权：`{str(report['training_authority']).lower()}`",
        "",
        "## 汇总",
        "",
        "| Scale/里程碑 | Context | QG2可达GM | Portfolio GM | QG2捕获收益 | QG2动作面损失 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    aggregate = report["aggregate"]
    for key in ("all", "scale30", "scale50", "admission", "proof"):
        row = aggregate[key]
        lines.append(
            f"| {key} | {row['context_count']} | {_fmt(row['qg2_gm'])} | "
            f"{_fmt(row['portfolio_gm'])} | {_pct(row['captured_savings_fraction'])} | "
            f"{row['qg2_action_surface_gap_sec']:.2f}s |"
        )
    lines.extend([
        "",
        "### 事后赢家分布",
        "",
        "| 范围 | Arm | 次数 |",
        "|---|---|---:|",
    ])
    for scope in ("qg2_reachable", "portfolio"):
        counts = aggregate["all"][f"{scope}_winner_counts"]
        for arm, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"| {scope} | {arm} | {count} |")
    lines.extend([
        "",
        "## 逐 context",
        "",
        "| Scale | 实例 | State | 里程碑 | Q0(s) | QG2最佳/ratio | Portfolio最佳/ratio | 动作面差(s) |",
        "|---:|---|---|---|---:|---|---|---:|",
    ])
    for row in report["contexts"]:
        lines.append(
            f"| {row['scale']} | {row['instance_id']} | {row['state'][:8]} | "
            f"{row['milestone']} | {row['q0_wall_sec']:.2f} | "
            f"{row['qg2_reachable_best_arm']}/{row['qg2_reachable_ratio']:.3f} | "
            f"{row['portfolio_best_arm']}/{row['portfolio_ratio']:.3f} | "
            f"{row['qg2_vs_portfolio_wall_gap_sec']:.2f} |"
        )
    lines.extend([
        "",
        "## 使用边界",
        "",
        "- `QG2 reachable` 是 Q0 与三个 QO2 bucket 的逐 context 事后最小值，仍包含 future-trace 与多重选择乐观偏差。",
        "- `Portfolio` 额外纳入 QD1/QB1，只用于判断更宽 ordering action surface 的潜力。",
        "- Random arms 不进入上界；右删失、里程碑不一致、exact-safe 失败的 arm 不进入最小值。",
        "- 当前 Linear/MLP/GAT 继续使用 action-reachable admission/proof pairwise supervision；本文件不能生成逐 label 训练标签。",
        "",
    ])
    return "\n".join(lines)


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups = {
        "all": rows,
        "scale30": [row for row in rows if row["scale"] == 30],
        "scale50": [row for row in rows if row["scale"] == 50],
        "admission": [
            row for row in rows if row["milestone"] == "ADMISSION_BATCH_READY"
        ],
        "proof": [
            row for row in rows if row["milestone"] == "EXACT_PROOF_COMPLETION"
        ],
    }
    return {name: _aggregate_rows(values) for name, values in groups.items()}


def _aggregate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    qg2_ratios = [float(row["qg2_reachable_ratio"]) for row in rows]
    portfolio_ratios = [float(row["portfolio_ratio"]) for row in rows]
    q0_total = sum(float(row["q0_wall_sec"]) for row in rows)
    qg2_total = sum(float(row["qg2_reachable_best_wall_sec"]) for row in rows)
    portfolio_total = sum(float(row["portfolio_best_wall_sec"]) for row in rows)
    possible_savings = q0_total - portfolio_total
    captured_savings = q0_total - qg2_total
    return {
        "context_count": len(rows),
        "qg2_gm": _geomean(qg2_ratios),
        "portfolio_gm": _geomean(portfolio_ratios),
        "qg2_instance_bootstrap_95_upper": _instance_bootstrap_upper(
            rows, "qg2_reachable_ratio"
        ),
        "portfolio_instance_bootstrap_95_upper": _instance_bootstrap_upper(
            rows, "portfolio_ratio"
        ),
        "q0_total_wall_sec": q0_total,
        "qg2_total_wall_sec": qg2_total,
        "portfolio_total_wall_sec": portfolio_total,
        "qg2_action_surface_gap_sec": qg2_total - portfolio_total,
        "captured_savings_fraction": (
            captured_savings / possible_savings
            if possible_savings > 1.0e-12
            else None
        ),
        "qg2_reachable_winner_counts": dict(Counter(
            row["qg2_reachable_best_arm"] for row in rows
        )),
        "portfolio_winner_counts": dict(Counter(
            row["portfolio_best_arm"] for row in rows
        )),
    }


def _control_ineligible_reason(control: dict[str, Any]) -> str | None:
    if not bool(control.get("milestone_reached")):
        return "milestone_not_reached"
    if str(control.get("milestone_kind") or "") not in MILESTONES:
        return "unsupported_milestone"
    if live._wall(control) is None:
        return "invalid_wall"
    return None


def _arm_ineligible_reason(
    control: dict[str, Any], arm: dict[str, Any] | None
) -> str | None:
    if arm is None:
        return "missing"
    if not bool(arm.get("milestone_reached")):
        return "right_censored_or_milestone_not_reached"
    if arm.get("milestone_kind") != control.get("milestone_kind"):
        return "milestone_mismatch"
    if not _binding_match(control, arm):
        return "execution_binding_mismatch"
    if live._wall(arm) is None:
        return "invalid_wall"
    if not live._ordering_safe(control, arm):
        return "exact_safe_audit_failed"
    return None


def _binding_match(control: dict[str, Any], arm: dict[str, Any]) -> bool:
    return all(
        control.get(key) is not None and control.get(key) == arm.get(key)
        for key in (
            "schema_version",
            "source_state_hash",
            "instance_content_hash",
            "source_backend_id",
            "source_config_hash",
            "source_engine_hash",
            "source_exact_action_policy_hash",
            "replay_engine_hash",
        )
    )


def _best(
    eligible: dict[str, float], allowed: Iterable[str]
) -> tuple[str, float]:
    candidates = [
        (arm, eligible[arm]) for arm in allowed if arm in eligible
    ]
    return min(candidates, key=lambda item: (item[1], item[0]))


def _captured_fraction(
    q0_wall: float, qg2_wall: float, portfolio_wall: float
) -> float | None:
    possible = q0_wall - portfolio_wall
    return (q0_wall - qg2_wall) / possible if possible > 1.0e-12 else None


def _instance_bootstrap_upper(
    rows: list[dict[str, Any]], ratio_key: str
) -> float | None:
    if not rows:
        return None
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        groups[str(row["instance_hash"])].append(float(row[ratio_key]))
    instances = sorted(groups)
    rng = random.Random(20260803)
    draws = []
    for _ in range(10_000):
        sampled = [instances[rng.randrange(len(instances))] for _ in instances]
        draws.append(_geomean([
            ratio for instance in sampled for ratio in groups[instance]
        ]))
    draws.sort()
    return draws[9750]


def _geomean(values: list[float]) -> float | None:
    return (
        math.exp(sum(math.log(value) for value in values) / len(values))
        if values
        else None
    )


def _load(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def _fmt(value: float | None) -> str:
    return "—" if value is None else f"{value:.4f}"


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{100.0 * value:.1f}%"


if __name__ == "__main__":
    raise SystemExit(main())
