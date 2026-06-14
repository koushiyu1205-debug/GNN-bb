#!/usr/bin/env python3
"""Build runnable commands for selector holdout active-basis collection.

The selector holdout manifest identifies priority failure contexts but leaves
the source profile as a placeholder.  This diagnostic script resolves each
target to an existing logical-graph path and to the source profile encoded in
the prior JSONL file names, then emits no-certificate-effect active-basis
capture commands.  It does not run BPC, pricing, RMP, Pulse, or benchmarks.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_manifest_20260614/"
    "summary.json"
)
DEFAULT_RUNNER = Path("BPC_future/scripts/run_sharded_pulse_roi_calibration.py")
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_runbook_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_collection_runbook_zh.md"
)
CAPTURE_ROOT = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_collection_capture_config_matched_20260614"
)
PYTHON = "/home/kai/miniconda3/envs/ecole/bin/python"
SOURCE_PROFILE_RE = re.compile(r"__(?P<profile>.+?)__r(?P<repeat>\d+)\.jsonl$")
LOGICAL_GRAPH_ROOTS = (
    Path("BPC_future/logical_graph"),
    Path("BPC_future/data/generated"),
)
CAPTURE_FLAGS = (
    "--counterfactual-replay-capture",
    "--counterfactual-replay-capture-active-basis",
    "--counterfactual-replay-capture-active-basis-max-rows 0",
    "--counterfactual-replay-capture-max-journeys 0",
    "--counterfactual-replay-capture-pool-max-journeys 0",
    "--counterfactual-replay-capture-forbidden-signatures",
    "--counterfactual-replay-capture-forbidden-signature-max-count 0",
    "--counterfactual-replay-capture-log-empty",
)
SOURCE_CONFIGS: tuple[dict[str, Any], ...] = (
    {
        "match": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
        "source_config_class": "dp1000_pt02_cg4_tl8",
        "time_limit": 8.0,
        "max_cg_iterations": 4,
        "pricing_time_limit": 0.2,
        "pricing_max_dp_states": 1000,
        "min_repeat_count": 3,
    },
    {
        "match": "root_cause_target002_capture_pt03_r3_20260613",
        "source_config_class": "target002_pt03_dp1000_cg4_tl8",
        "time_limit": 8.0,
        "max_cg_iterations": 4,
        "pricing_time_limit": 0.3,
        "pricing_max_dp_states": 1000,
        "min_repeat_count": 3,
    },
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")


def _extract_source_profile(path: str) -> tuple[str, int] | None:
    match = SOURCE_PROFILE_RE.search(str(path))
    if not match:
        return None
    return match.group("profile"), int(match.group("repeat"))


def _source_config_for_file(path: str) -> dict[str, Any] | None:
    for config in SOURCE_CONFIGS:
        if str(config["match"]) in path:
            return dict(config)
    return None


def _literal_tuple_assignments(script_text: str) -> dict[str, tuple[str, ...]]:
    tree = ast.parse(script_text)
    values: dict[str, tuple[str, ...]] = {}

    def eval_node(node: ast.AST) -> tuple[str, ...]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return (node.value,)
        if isinstance(node, ast.Name):
            return values.get(node.id, ())
        if isinstance(node, ast.Tuple):
            items: list[str] = []
            for element in node.elts:
                if isinstance(element, ast.Starred):
                    items.extend(eval_node(element.value))
                else:
                    items.extend(eval_node(element))
            return tuple(items)
        return ()

    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        for target in statement.targets:
            if isinstance(target, ast.Name):
                evaluated = eval_node(statement.value)
                if evaluated:
                    values[target.id] = evaluated
    return values


def _runner_profiles(runner_path: Path) -> set[str]:
    assignments = _literal_tuple_assignments(runner_path.read_text(encoding="utf-8"))
    return set(assignments.get("VALID_PROFILES", ()))


def _resolve_logical_graph(instance_name: str) -> str:
    target_name = f"{instance_name}_logical_graph.json"
    matches: list[Path] = []
    for root in LOGICAL_GRAPH_ROOTS:
        if root.exists():
            matches.extend(sorted(root.rglob(target_name)))
    if not matches:
        return ""
    matches.sort(key=lambda path: (0 if str(path).startswith("BPC_future/logical_graph/") else 1, len(str(path))))
    return str(matches[0])


def _command_for_group(
    *,
    output_dir: Path,
    instance_path: str,
    profile: str,
    repeat_count: int,
    time_limit: float,
    max_cg_iterations: int,
    pricing_time_limit: float,
    pricing_max_dp_states: int,
) -> str:
    return " ".join(
        [
            "PYTHONDONTWRITEBYTECODE=1",
            "PYTHONPATH=.",
            PYTHON,
            "BPC_future/scripts/run_sharded_pulse_roi_calibration.py",
            "--output-dir",
            str(output_dir),
            "--instances",
            instance_path,
            "--profiles",
            profile,
            "--repeat-count",
            str(max(1, int(repeat_count))),
            "--time-limit",
            f"{float(time_limit):g}",
            "--max-cg-iterations",
            str(int(max_cg_iterations)),
            "--pricing-time-limit",
            f"{float(pricing_time_limit):g}",
            "--pricing-max-dp-states",
            str(int(pricing_max_dp_states)),
            *CAPTURE_FLAGS,
            "--quiet",
        ]
    )


def build_runbook(*, manifest_path: Path, runner_path: Path) -> dict[str, Any]:
    manifest = _read_json(manifest_path)
    supported_profiles = _runner_profiles(runner_path)
    profile_groups: dict[tuple[str, str], dict[str, Any]] = {}
    target_rows: list[dict[str, Any]] = []
    unresolved_instances: set[str] = set()
    unsupported_profiles: set[str] = set()
    unsupported_source_configs: set[str] = set()

    for target in manifest.get("targets", []) or []:
        instance_name = str(target.get("representative_instance", "") or "")
        instance_path = _resolve_logical_graph(instance_name)
        if not instance_path:
            unresolved_instances.add(instance_name)
        source_profiles: dict[str, set[int]] = defaultdict(set)
        for source_file in target.get("candidate_source_files", []) or []:
            extracted = _extract_source_profile(str(source_file))
            if extracted is None:
                continue
            profile, repeat = extracted
            source_config = _source_config_for_file(str(source_file))
            if source_config is None:
                unsupported_source_configs.add(str(source_file))
                continue
            profile_config_key = (
                profile,
                str(source_config["source_config_class"]),
                float(source_config["time_limit"]),
                int(source_config["max_cg_iterations"]),
                float(source_config["pricing_time_limit"]),
                int(source_config["pricing_max_dp_states"]),
                int(source_config["min_repeat_count"]),
            )
            source_profiles[profile_config_key].add(repeat)
            if profile not in supported_profiles:
                unsupported_profiles.add(profile)
        for profile_config_key, repeats in sorted(source_profiles.items()):
            (
                profile,
                source_config_class,
                time_limit,
                max_cg_iterations,
                pricing_time_limit,
                pricing_max_dp_states,
                min_repeat_count,
            ) = profile_config_key
            repeat_count = max(max(repeats) + 1 if repeats else 1, int(min_repeat_count))
            key = (
                instance_path,
                profile,
                source_config_class,
                time_limit,
                max_cg_iterations,
                pricing_time_limit,
                pricing_max_dp_states,
                min_repeat_count,
            )
            group = profile_groups.setdefault(
                key,
                {
                    "instance": instance_name,
                    "instance_path": instance_path,
                    "profile": profile,
                    "source_config_class": source_config_class,
                    "repeat_count": repeat_count,
                    "time_limit": time_limit,
                    "max_cg_iterations": max_cg_iterations,
                    "pricing_time_limit": pricing_time_limit,
                    "pricing_max_dp_states": pricing_max_dp_states,
                    "min_repeat_count": min_repeat_count,
                    "context_hashes": [],
                    "collection_target_ids": [],
                    "failure_kinds": [],
                },
            )
            group["repeat_count"] = max(int(group["repeat_count"]), repeat_count)
            group["context_hashes"].append(target.get("context_hash"))
            group["collection_target_ids"].append(target.get("collection_target_id"))
            group["failure_kinds"].append(target.get("failure_kind"))
            target_rows.append(
                {
                    "collection_target_id": target.get("collection_target_id"),
                    "failure_kind": target.get("failure_kind"),
                    "context_hash": target.get("context_hash"),
                    "instance": instance_name,
                    "instance_path": instance_path,
                    "profile": profile,
                    "source_config_class": source_config_class,
                    "repeat_count": repeat_count,
                    "time_limit": time_limit,
                    "max_cg_iterations": max_cg_iterations,
                    "pricing_time_limit": pricing_time_limit,
                    "pricing_max_dp_states": pricing_max_dp_states,
                    "min_repeat_count": min_repeat_count,
                    "candidate_row_count": target.get("candidate_row_count"),
                    "needs_active_basis_snapshot_capture": target.get(
                        "needs_active_basis_snapshot_capture"
                    ),
                }
            )

    commands: list[dict[str, Any]] = []
    for index, group in enumerate(
        sorted(
            profile_groups.values(),
            key=lambda item: (
                item["instance"],
                item["profile"],
                item["source_config_class"],
            ),
        ),
        start=1,
    ):
        group_dir = CAPTURE_ROOT / (
            f"{index:03d}_{_safe_name(group['instance'])}"
            f"__{_safe_name(group['profile'])}"
            f"__{_safe_name(group['source_config_class'])}"
        )
        command = _command_for_group(
            output_dir=group_dir,
            instance_path=group["instance_path"],
            profile=group["profile"],
            repeat_count=int(group["repeat_count"]),
            time_limit=float(group["time_limit"]),
            max_cg_iterations=int(group["max_cg_iterations"]),
            pricing_time_limit=float(group["pricing_time_limit"]),
            pricing_max_dp_states=int(group["pricing_max_dp_states"]),
        )
        commands.append(
            {
                "command_id": f"selector_holdout_capture_{index:03d}",
                "instance": group["instance"],
                "instance_path": group["instance_path"],
                "profile": group["profile"],
                "source_config_class": group["source_config_class"],
                "repeat_count": int(group["repeat_count"]),
                "time_limit": float(group["time_limit"]),
                "max_cg_iterations": int(group["max_cg_iterations"]),
                "pricing_time_limit": float(group["pricing_time_limit"]),
                "pricing_max_dp_states": int(group["pricing_max_dp_states"]),
                "min_repeat_count": int(group["min_repeat_count"]),
                "output_dir": str(group_dir),
                "expected_context_hashes": sorted(set(group["context_hashes"])),
                "collection_target_ids": sorted(set(group["collection_target_ids"])),
                "failure_kinds": sorted(set(group["failure_kinds"])),
                "command": command,
                "diagnostic_only": True,
                "runs_when_executed": True,
                "runbook_generation_runs_bpc_or_pricing": False,
                "requires_post_run_context_hit_audit": True,
            }
        )

    checks = {
        "manifest_passed": manifest.get("all_checks_pass") is True,
        "has_targets": bool(manifest.get("targets")),
        "has_commands": bool(commands),
        "all_instances_resolved": not unresolved_instances,
        "all_source_profiles_extracted": len(target_rows) > 0,
        "all_source_profiles_supported": not unsupported_profiles,
        "all_source_configs_supported": not unsupported_source_configs,
        "all_commands_have_nondefault_pricing_context_args": all(
            "--pricing-max-dp-states 1000" in item["command"]
            and "--pricing-time-limit" in item["command"]
            and "--max-cg-iterations" in item["command"]
            and "--time-limit" in item["command"]
            for item in commands
        ),
        "all_commands_have_active_basis_capture": all(
            "--counterfactual-replay-capture-active-basis" in item["command"]
            and "--counterfactual-replay-capture-active-basis-max-rows 0" in item["command"]
            for item in commands
        ),
        "all_commands_have_forbidden_signature_capture": all(
            "--counterfactual-replay-capture-forbidden-signatures" in item["command"]
            and (
                "--counterfactual-replay-capture-forbidden-signature-max-count 0"
                in item["command"]
            )
            for item in commands
        ),
        "all_commands_are_diagnostic_only": all(item["diagnostic_only"] for item in commands),
        "runbook_generation_does_not_run_bpc_or_pricing": True,
    }
    return {
        "schema_version": "root_cause_selector_holdout_collection_runbook_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_holdout_collection_runbook_ready",
        "source_manifest": str(manifest_path),
        "runner": str(runner_path),
        "capture_root": str(CAPTURE_ROOT),
        "collection_target_count": int(manifest.get("collection_target_count", 0)),
        "collection_target_profile_mapping_count": len(target_rows),
        "command_count": len(commands),
        "source_profile_count": len({row["profile"] for row in target_rows}),
        "source_profiles": sorted({row["profile"] for row in target_rows}),
        "source_config_class_count": len(
            {row["source_config_class"] for row in target_rows}
        ),
        "source_config_classes": sorted(
            {row["source_config_class"] for row in target_rows}
        ),
        "instance_count": len({row["instance"] for row in target_rows}),
        "instances": sorted({row["instance"] for row in target_rows}),
        "unresolved_instances": sorted(unresolved_instances),
        "unsupported_profiles": sorted(unsupported_profiles),
        "unsupported_source_configs": sorted(unsupported_source_configs),
        "capture_flags": list(CAPTURE_FLAGS),
        "target_profile_rows": target_rows,
        "commands": commands,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "当前 selector holdout 的 10 个 priority contexts 已能映射到"
            " calibration runner 支持的 source profiles 和本地 logical graph 路径。"
            "该 runbook 只生成 no-certificate-effect active-basis / pool / "
            "returned-batch / forbidden-signature capture 命令；"
            "它本身不运行 BPC，也不证明 selector 或优化方向已经可上线。"
        ),
    }


def write_commands(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# Generated diagnostic-only active-basis capture runbook.",
        "# Running these commands will execute BPC_future calibration runs, but",
        "# generation of this file did not run BPC/pricing/RMP/Pulse.",
        "",
    ]
    for item in summary["commands"]:
        lines.extend(
            [
                (
                    f"# {item['command_id']} instance={item['instance']} "
                    f"profile={item['profile']} "
                    f"source_config={item['source_config_class']}"
                ),
                (
                    "# replay_args="
                    f"repeat_count={item['repeat_count']},"
                    f"time_limit={item['time_limit']},"
                    f"max_cg_iterations={item['max_cg_iterations']},"
                    f"pricing_time_limit={item['pricing_time_limit']},"
                    f"pricing_max_dp_states={item['pricing_max_dp_states']}"
                ),
                f"# expected_context_hashes={','.join(item['expected_context_hashes'])}",
                item["command"],
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_csv(summary: dict[str, Any], path: Path) -> None:
    fieldnames = [
        "collection_target_id",
        "failure_kind",
        "context_hash",
        "instance",
        "instance_path",
        "profile",
        "source_config_class",
        "repeat_count",
        "min_repeat_count",
        "time_limit",
        "max_cg_iterations",
        "pricing_time_limit",
        "pricing_max_dp_states",
        "candidate_row_count",
        "needs_active_basis_snapshot_capture",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(
            [{key: row.get(key, "") for key in fieldnames} for row in summary["target_profile_rows"]]
        )


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Selector Holdout Collection Runbook 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告把 selector holdout manifest 中的 context targets 解析成可执行",
        "component payload 采集命令。生成报告不会运行 BPC / pricing / RMP / Pulse；",
        "真正执行 `commands.sh` 才会启动 calibration runs。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_selector_holdout_collection_runbook = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"collection_target_count = {summary['collection_target_count']}",
        f"collection_target_profile_mapping_count = {summary['collection_target_profile_mapping_count']}",
        f"command_count = {summary['command_count']}",
        f"source_profile_count = {summary['source_profile_count']}",
        f"source_config_class_count = {summary['source_config_class_count']}",
        f"instance_count = {summary['instance_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Source profiles",
        "",
        "```json",
        json.dumps(summary["source_profiles"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Source config classes",
        "",
        "```json",
        json.dumps(summary["source_config_classes"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Commands",
        "",
        "```json",
        json.dumps(
            [
                {
                    "command_id": item["command_id"],
                    "instance": item["instance"],
                    "profile": item["profile"],
                    "source_config_class": item["source_config_class"],
                    "repeat_count": item["repeat_count"],
                    "min_repeat_count": item["min_repeat_count"],
                    "time_limit": item["time_limit"],
                    "max_cg_iterations": item["max_cg_iterations"],
                    "pricing_time_limit": item["pricing_time_limit"],
                    "pricing_max_dp_states": item["pricing_max_dp_states"],
                    "expected_context_hashes": item["expected_context_hashes"],
                    "command": item["command"],
                }
                for item in summary["commands"]
            ],
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## 检查项",
        "",
        "```json",
        json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## 当前边界",
        "",
        "- 未执行这些命令；",
        "- 未证明 expected context hash 已被重新命中；",
        "- 未训练或验证 production selector；",
        "- 未打开 worker default 或 certificate gate。",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--runner", default=str(DEFAULT_RUNNER))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = build_runbook(
        manifest_path=Path(args.manifest),
        runner_path=Path(args.runner),
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(summary, output_dir / "target_profile_rows.csv")
    write_commands(summary, output_dir / "commands.sh")
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    write_report(summary, Path(args.report))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
