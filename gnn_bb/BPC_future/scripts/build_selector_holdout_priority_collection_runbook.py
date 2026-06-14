#!/usr/bin/env python3
"""Build collection commands for uncovered priority selector contexts.

The target priority matrix identifies contexts that are important for the
next selector holdout but are not yet covered by the existing collection
manifest.  This script converts commandable uncovered contexts into capture
commands and records uncommandable contexts explicitly.  It only builds a
runbook; it does not run BPC, pricing, RMP, Pulse, replay, workers, or
benchmarks.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_PRIORITY_MATRIX = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_target_priority_matrix_20260614/summary.json"
)
DEFAULT_RUNNER = Path("BPC_future/scripts/run_sharded_pulse_roi_calibration.py")
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_priority_collection_runbook_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_priority_collection_runbook_zh.md"
)
DEFAULT_CSV_GLOB = "BPC_future/results/**/*candidate*impact*rows.csv"
CAPTURE_ROOT = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_priority_collection_capture_20260614"
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


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


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
    matches.sort(
        key=lambda path: (
            0 if str(path).startswith("BPC_future/logical_graph/") else 1,
            len(str(path)),
        )
    )
    return str(matches[0])


def _read_candidate_rows(csv_glob: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(Path().glob(csv_glob)):
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                copied = dict(row)
                copied["_source_csv"] = str(path)
                rows.append(copied)
    return rows


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


def _label_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    return dict(Counter(row.get("single_impact_class", "") for row in rows))


def _target_rows_for_context(
    rows_by_context: dict[str, list[dict[str, str]]], context_hash: str
) -> list[dict[str, str]]:
    return rows_by_context.get(context_hash, [])


def build_runbook(
    *,
    priority_matrix_path: Path,
    runner_path: Path,
    csv_glob: str,
) -> dict[str, Any]:
    priority_matrix = _read_json(priority_matrix_path)
    supported_profiles = _runner_profiles(runner_path)
    rows = _read_candidate_rows(csv_glob)
    rows_by_context: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        context_hash = str(row.get("context_hash", "")).strip()
        if context_hash:
            rows_by_context[context_hash].append(row)

    target_contexts = list(priority_matrix.get("uncovered_priority_contexts", []))
    target_rows: list[dict[str, Any]] = []
    profile_groups: dict[tuple[Any, ...], dict[str, Any]] = {}
    unsupported_contexts: list[dict[str, Any]] = []
    unresolved_instances: set[str] = set()
    unsupported_profiles: set[str] = set()
    unsupported_source_configs: set[str] = set()

    for context_hash in target_contexts:
        context_rows = _target_rows_for_context(rows_by_context, str(context_hash))
        source_files = sorted(
            {row.get("source_file", "") for row in context_rows if row.get("source_file")}
        )
        instance_counts = Counter(
            row.get("instance", "") for row in context_rows if row.get("instance")
        )
        representative_instance = (
            instance_counts.most_common(1)[0][0] if instance_counts else ""
        )
        instance_path = _resolve_logical_graph(representative_instance)
        if representative_instance and not instance_path:
            unresolved_instances.add(representative_instance)

        context_profile_rows: list[dict[str, Any]] = []
        unsupported_reasons: Counter[str] = Counter()
        for source_file in source_files:
            extracted = _extract_source_profile(source_file)
            if extracted is None:
                unsupported_reasons["source_profile_not_encoded"] += 1
                continue
            profile, repeat = extracted
            source_config = _source_config_for_file(source_file)
            if source_config is None:
                unsupported_reasons["source_config_not_mapped"] += 1
                unsupported_source_configs.add(source_file)
                continue
            if profile not in supported_profiles:
                unsupported_reasons["runner_profile_not_supported"] += 1
                unsupported_profiles.add(profile)
                continue
            if not instance_path:
                unsupported_reasons["logical_graph_not_resolved"] += 1
                continue

            key = (
                instance_path,
                profile,
                str(source_config["source_config_class"]),
                float(source_config["time_limit"]),
                int(source_config["max_cg_iterations"]),
                float(source_config["pricing_time_limit"]),
                int(source_config["pricing_max_dp_states"]),
                int(source_config["min_repeat_count"]),
            )
            group = profile_groups.setdefault(
                key,
                {
                    "instance": representative_instance,
                    "instance_path": instance_path,
                    "profile": profile,
                    "source_config_class": source_config["source_config_class"],
                    "repeat_count": int(source_config["min_repeat_count"]),
                    "time_limit": float(source_config["time_limit"]),
                    "max_cg_iterations": int(source_config["max_cg_iterations"]),
                    "pricing_time_limit": float(source_config["pricing_time_limit"]),
                    "pricing_max_dp_states": int(
                        source_config["pricing_max_dp_states"]
                    ),
                    "min_repeat_count": int(source_config["min_repeat_count"]),
                    "context_hashes": [],
                    "source_files": [],
                },
            )
            group["repeat_count"] = max(group["repeat_count"], int(repeat) + 1)
            group["context_hashes"].append(str(context_hash))
            group["source_files"].append(source_file)
            context_profile_rows.append(
                {
                    "context_hash": context_hash,
                    "source_file": source_file,
                    "profile": profile,
                    "repeat": repeat,
                    "source_config_class": source_config["source_config_class"],
                }
            )

        compact = {
            "context_hash": context_hash,
            "row_count": len(context_rows),
            "label_counts": _label_counts(context_rows),
            "instance_counts": dict(instance_counts),
            "source_file_count": len(source_files),
            "commandable_source_file_count": len(context_profile_rows),
            "unsupported_reason_counts": dict(unsupported_reasons),
            "sample_source_files": source_files[:5],
            "needs_active_basis_snapshot_capture": True,
            "needs_explicit_forbidden_payload": True,
        }
        target_rows.append({**compact, "profile_rows": context_profile_rows})
        if not context_profile_rows:
            unsupported_contexts.append(compact)

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
        output_dir = CAPTURE_ROOT / (
            f"{index:03d}_{_safe_name(group['instance'])}"
            f"__{_safe_name(group['profile'])}"
            f"__{_safe_name(group['source_config_class'])}"
        )
        command = _command_for_group(
            output_dir=output_dir,
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
                "command_id": f"selector_priority_capture_{index:03d}",
                "instance": group["instance"],
                "instance_path": group["instance_path"],
                "profile": group["profile"],
                "source_config_class": group["source_config_class"],
                "repeat_count": int(group["repeat_count"]),
                "time_limit": float(group["time_limit"]),
                "max_cg_iterations": int(group["max_cg_iterations"]),
                "pricing_time_limit": float(group["pricing_time_limit"]),
                "pricing_max_dp_states": int(group["pricing_max_dp_states"]),
                "output_dir": str(output_dir),
                "expected_context_hashes": sorted(set(group["context_hashes"])),
                "source_files": sorted(set(group["source_files"])),
                "command": command,
                "diagnostic_only": True,
                "runbook_generation_runs_bpc_or_pricing": False,
                "requires_post_run_context_hit_audit": True,
            }
        )

    commandable_contexts = sorted(
        {
            context_hash
            for item in target_rows
            if item.get("commandable_source_file_count", 0) > 0
            for context_hash in [str(item["context_hash"])]
        }
    )
    unsupported_context_hashes = sorted(
        {str(item["context_hash"]) for item in unsupported_contexts}
    )
    checks = {
        "priority_matrix_passed": priority_matrix.get("all_checks_pass") is True,
        "uncovered_contexts_present": bool(target_contexts),
        "has_commandable_contexts": bool(commandable_contexts),
        "has_commands": bool(commands),
        "unsupported_contexts_explicitly_listed": bool(unsupported_context_hashes),
        "all_commands_have_nondefault_pricing_context_args": all(
            "--pricing-max-dp-states 1000" in item["command"]
            and "--pricing-time-limit" in item["command"]
            and "--max-cg-iterations" in item["command"]
            and "--time-limit" in item["command"]
            for item in commands
        ),
        "all_commands_have_active_basis_capture": all(
            "--counterfactual-replay-capture-active-basis" in item["command"]
            and "--counterfactual-replay-capture-active-basis-max-rows 0"
            in item["command"]
            for item in commands
        ),
        "all_commands_have_forbidden_signature_capture": all(
            "--counterfactual-replay-capture-forbidden-signatures" in item["command"]
            and "--counterfactual-replay-capture-forbidden-signature-max-count 0"
            in item["command"]
            for item in commands
        ),
        "all_instances_resolved_for_commands": all(
            item.get("instance_path") for item in commands
        ),
        "diagnostic_not_solver_run": True,
    }
    return {
        "schema_version": "selector_holdout_priority_collection_runbook_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_holdout_priority_collection_runbook_ready",
        "target_context_count": len(target_contexts),
        "commandable_context_count": len(commandable_contexts),
        "unsupported_context_count": len(unsupported_context_hashes),
        "command_count": len(commands),
        "commandable_contexts": commandable_contexts,
        "unsupported_contexts": unsupported_context_hashes,
        "unsupported_profiles": sorted(unsupported_profiles),
        "unsupported_source_configs": sorted(unsupported_source_configs),
        "unresolved_instances": sorted(unresolved_instances),
        "targets": target_rows,
        "commands": commands,
        "forbidden_next_actions": [
            "production_bpc_ab_before_selector_holdout",
            "default_worker_or_audit_enable",
            "official_certificate_gate",
            "treat_priority_runbook_as_selector_validation",
        ],
        "sources": {
            "priority_matrix": str(priority_matrix_path),
            "runner": str(runner_path),
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "未覆盖 priority contexts 中，一部分可以直接用现有 profile/config "
            "生成 no-certificate-effect active-basis/forbidden capture 命令；"
            "其余 context 被显式列为 unsupported，不能当作已补采。该 runbook "
            "只是补采入口，不是 production selector 或求解加速证据。"
        ),
    }


def write_outputs(summary: dict[str, Any], output_dir: Path, report_path: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "commands.sh").write_text(
        "\n".join(item["command"] for item in summary["commands"]) + "\n",
        encoding="utf-8",
    )
    with (output_dir / "target_profile_rows.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        fieldnames = [
            "context_hash",
            "row_count",
            "label_counts",
            "instance_counts",
            "commandable_source_file_count",
            "unsupported_reason_counts",
            "needs_active_basis_snapshot_capture",
            "needs_explicit_forbidden_payload",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary["targets"]:
            writer.writerow(
                {
                    key: json.dumps(row.get(key), ensure_ascii=False, sort_keys=True)
                    if isinstance(row.get(key), (dict, list))
                    else row.get(key)
                    for key in fieldnames
                }
            )
    lines = [
        "# Selector Holdout Priority Collection Runbook 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告把未覆盖 priority contexts 转成补采 runbook。它只生成命令，"
        "不运行 BPC / pricing / RMP / Pulse。",
        "",
        "## 机器字段",
        "",
        "```text",
        "selector_holdout_priority_collection_runbook = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"target_context_count = {summary['target_context_count']}",
        f"commandable_context_count = {summary['commandable_context_count']}",
        f"unsupported_context_count = {summary['unsupported_context_count']}",
        f"command_count = {summary['command_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Commandable contexts",
        "",
        "```json",
        json.dumps(
            summary["commandable_contexts"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Unsupported contexts",
        "",
        "```json",
        json.dumps(
            summary["unsupported_contexts"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Commands",
        "",
        "```json",
        json.dumps(summary["commands"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Target rows",
        "",
        "```json",
        json.dumps(summary["targets"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Checks",
        "",
        "```json",
        json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--priority-matrix", default=str(DEFAULT_PRIORITY_MATRIX))
    parser.add_argument("--runner", default=str(DEFAULT_RUNNER))
    parser.add_argument("--csv-glob", default=DEFAULT_CSV_GLOB)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = build_runbook(
        priority_matrix_path=Path(args.priority_matrix),
        runner_path=Path(args.runner),
        csv_glob=str(args.csv_glob),
    )
    write_outputs(summary, Path(args.output_dir), Path(args.report))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
