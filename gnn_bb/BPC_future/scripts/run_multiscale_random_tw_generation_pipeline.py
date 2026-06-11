#!/usr/bin/env python3
"""Generate, deduplicate, validate, and report random-TW multiscale instances.

This is an orchestration layer around
``generate_moon_trek_multiscale_random_tw_benchmark.py``.  It does not change
the instance generation model.  It runs one group per terrain/mode, moves the
solver-facing logical graph JSONs into ``BPC_future/logical_graph``, rewrites
manifests/tensor metadata to that canonical path, validates the generated
instances, and writes Chinese reports.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from BPC_future.core.data import load_future_data  # noqa: E402
from BPC_future.learning.graph_builder import FutureGraphBuilder  # noqa: E402
from BPC_future.scripts.generate_moon_trek_balanced_benchmark import DEFAULT_TERRAINS  # noqa: E402


MODES: tuple[str, ...] = ("greedy-anchor", "random-wave", "sector-wave")
DEFAULT_DATE_TAG = "20260610"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the multiscale random-TW generation pipeline.")
    parser.add_argument("--task-counts", default="20,30,50,100", help="Comma-separated task counts.")
    parser.add_argument("--instances-per-terrain-size", type=int, default=10)
    parser.add_argument("--jobs", type=int, default=6)
    parser.add_argument("--max-seed-attempts", type=int, default=2500)
    parser.add_argument("--tensor-format", choices=("both", "pt", "npz", "none"), default="both")
    parser.add_argument("--date-tag", default=DEFAULT_DATE_TAG)
    parser.add_argument("--logical-root", default="BPC_future/logical_graph")
    parser.add_argument("--data-root", default="BPC_future/data/generated")
    parser.add_argument("--figure-root-base", default="BPC_future/draw")
    parser.add_argument("--results-root", default="BPC_future/results")
    parser.add_argument("--terrain-dir", action="append", default=None)
    parser.add_argument("--force", action="store_true", help="Regenerate scales even if canonical files exist.")
    parser.add_argument("--skip-generation", action="store_true", help="Only combine/dedup/validate/report existing parts.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    task_counts = [int(part.strip()) for part in str(args.task_counts).split(",") if part.strip()]
    terrain_dirs = tuple(args.terrain_dir or DEFAULT_TERRAINS)
    for task_count in task_counts:
        run_scale_pipeline(task_count, args=args, terrain_dirs=terrain_dirs)


def run_scale_pipeline(task_count: int, *, args: argparse.Namespace, terrain_dirs: Sequence[str]) -> None:
    logical_root = Path(args.logical_root)
    data_root = Path(args.data_root)
    figure_base = Path(args.figure_root_base)
    results_root = Path(args.results_root)
    scale_tag = f"tasks{task_count}"
    combined_root = data_root / f"moon_trek_multiscale_random_tw_{scale_tag}_ablation_{args.date_tag}"
    parts_root = data_root / f"moon_trek_multiscale_random_tw_{scale_tag}_ablation_{args.date_tag}_parts"
    figure_root = figure_base / f"moon_trek_multiscale_random_tw_{scale_tag}_ablation_{args.date_tag}_parts"
    log_root = results_root / "multiscale_generation_logs" / f"tasks_{task_count:03d}"

    existing = list((logical_root / f"tasks_{task_count:03d}").glob("**/*_logical_graph.json"))
    expected = int(args.instances_per_terrain_size) * len(terrain_dirs) * len(MODES)
    if existing and len(existing) == expected and not args.force and not args.skip_generation:
        print(
            json.dumps(
                {
                    "event": "skip_generation_existing_scale",
                    "task_count": task_count,
                    "canonical_count": len(existing),
                    "expected": expected,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
    elif not args.skip_generation:
        _run_generation_groups(
            task_count,
            terrain_dirs=terrain_dirs,
            parts_root=parts_root,
            figure_root=figure_root,
            log_root=log_root,
            jobs=max(1, int(args.jobs)),
            instances_per_terrain_size=int(args.instances_per_terrain_size),
            max_seed_attempts=int(args.max_seed_attempts),
            tensor_format=str(args.tensor_format),
        )

    manifest_path, manifest_paths = _combine_part_manifests(
        task_count,
        terrain_dirs=terrain_dirs,
        combined_root=combined_root,
        parts_root=parts_root,
        figure_root=figure_root,
        instances_per_terrain_size=int(args.instances_per_terrain_size),
    )
    _deduplicate_to_logical_root(
        task_count,
        manifest_paths=manifest_paths,
        combined_manifest_path=manifest_path,
        logical_root=logical_root,
        force=bool(args.force),
    )
    validation_path = _validate_scale(
        task_count,
        manifest_path=manifest_path,
        logical_root=logical_root,
        results_root=results_root,
        date_tag=str(args.date_tag),
    )
    report_path = _write_scale_report(
        task_count,
        manifest_path=manifest_path,
        validation_path=validation_path,
        results_root=results_root,
        date_tag=str(args.date_tag),
        log_root=log_root,
    )
    print(
        json.dumps(
            {
                "event": "scale_complete",
                "task_count": task_count,
                "manifest": str(manifest_path),
                "validation": str(validation_path),
                "report": str(report_path),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


def _run_generation_groups(
    task_count: int,
    *,
    terrain_dirs: Sequence[str],
    parts_root: Path,
    figure_root: Path,
    log_root: Path,
    jobs: int,
    instances_per_terrain_size: int,
    max_seed_attempts: int,
    tensor_format: str,
) -> None:
    log_root.mkdir(parents=True, exist_ok=True)
    commands: list[tuple[str, list[str], Path]] = []
    generator = ROOT / "BPC_future/scripts/generate_moon_trek_multiscale_random_tw_benchmark.py"
    for terrain in terrain_dirs:
        terrain_name = Path(terrain).name
        for mode in MODES:
            slug = _mode_slug(mode)
            group = f"{terrain_name}_{slug}"
            out = parts_root / group
            figs = figure_root / group
            log_path = log_root / f"{group}.log"
            cmd = [
                sys.executable,
                str(generator),
                "--task-counts",
                str(task_count),
                "--terrain-dir",
                str(terrain),
                "--time-window-modes",
                mode,
                "--instances-per-terrain-size",
                str(instances_per_terrain_size),
                "--output-root",
                str(out),
                "--figure-root",
                str(figs),
                "--tensor-format",
                tensor_format,
                "--max-seed-attempts",
                str(max_seed_attempts),
                "--no-draw-one-per-size",
                "--no-draw-terrain-atlas",
            ]
            commands.append((group, cmd, log_path))

    active: list[tuple[str, subprocess.Popen[bytes], Any, Path, float]] = []
    remaining = list(commands)
    failures: list[dict[str, Any]] = []
    while remaining or active:
        while remaining and len(active) < jobs:
            group, cmd, log_path = remaining.pop(0)
            handle = log_path.open("wb")
            handle.write(("COMMAND: " + " ".join(cmd) + "\n").encode("utf-8"))
            handle.flush()
            proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=handle, stderr=subprocess.STDOUT)
            active.append((group, proc, handle, log_path, time.time()))
            print(json.dumps({"event": "group_started", "task_count": task_count, "group": group, "log": str(log_path)}, ensure_ascii=False), flush=True)
        time.sleep(5.0)
        still_active: list[tuple[str, subprocess.Popen[bytes], Any, Path, float]] = []
        for group, proc, handle, log_path, started in active:
            code = proc.poll()
            if code is None:
                still_active.append((group, proc, handle, log_path, started))
                continue
            handle.close()
            elapsed = round(time.time() - started, 3)
            if code != 0:
                failures.append({"group": group, "returncode": code, "log": str(log_path), "elapsed": elapsed})
            print(
                json.dumps(
                    {
                        "event": "group_finished",
                        "task_count": task_count,
                        "group": group,
                        "returncode": code,
                        "elapsed": elapsed,
                        "log": str(log_path),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
        active = still_active
    if failures:
        raise RuntimeError(f"generation group failures: {failures}")


def _combine_part_manifests(
    task_count: int,
    *,
    terrain_dirs: Sequence[str],
    combined_root: Path,
    parts_root: Path,
    figure_root: Path,
    instances_per_terrain_size: int,
) -> tuple[Path, list[Path]]:
    manifest_paths = sorted(parts_root.glob("*/manifest.json"))
    expected_groups = len(terrain_dirs) * len(MODES)
    if len(manifest_paths) != expected_groups:
        raise RuntimeError(f"expected {expected_groups} part manifests for task_count={task_count}, found {len(manifest_paths)} under {parts_root}")
    combined: dict[str, Any] | None = None
    instances: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    skip_summary: Counter[str] = Counter()
    part_roots: list[str] = []
    for path in manifest_paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        if combined is None:
            combined = {key: value for key, value in data.items() if key not in {"instances", "attempts", "skip_summary", "generation_summary"}}
        instances.extend(data.get("instances", []))
        attempts.extend(data.get("attempts", []))
        skip_summary.update(data.get("skip_summary", {}))
        part_roots.append(str(Path(data.get("output_root", path.parent))))
    assert combined is not None
    combined.update(
        {
            "output_root": str(combined_root),
            "figure_root": str(figure_root),
            "terrain_dirs": list(terrain_dirs),
            "part_output_roots": sorted(part_roots),
            "task_counts": [int(task_count)],
            "time_window_modes": list(MODES),
            "time_window_mode_count": len(MODES),
            "instances_per_terrain_size": int(instances_per_terrain_size),
            "instances_per_size_total": int(instances_per_terrain_size) * len(terrain_dirs) * len(MODES),
            "instances": sorted(instances, key=lambda item: (str(item.get("terrain")), str(item.get("time_window_mode")), int(item.get("sample_index", 0)), str(item.get("instance_id")))),
            "attempts": attempts,
            "skip_summary": dict(sorted(skip_summary.items())),
        }
    )
    combined["generation_summary"] = _generation_summary(combined)
    manifest_path = combined_root / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(combined, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path, [manifest_path, *manifest_paths]


def _deduplicate_to_logical_root(
    task_count: int,
    *,
    manifest_paths: Sequence[Path],
    combined_manifest_path: Path,
    logical_root: Path,
    force: bool,
) -> None:
    combined = json.loads(combined_manifest_path.read_text(encoding="utf-8"))
    canonical_by_id: dict[str, str] = {}
    for inst in combined["instances"]:
        src = Path(inst["logical_graph"])
        canonical = logical_root / f"tasks_{task_count:03d}" / str(inst["time_window_mode"]) / str(inst["terrain"]) / src.name
        canonical.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            if force or not canonical.exists():
                shutil.copy2(src, canonical)
        if not canonical.exists():
            raise FileNotFoundError(f"canonical logical graph missing after copy: {canonical}")
        canonical_by_id[str(inst["instance_id"])] = str(canonical)

    for manifest_path in manifest_paths:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for inst in data.get("instances", []):
            instance_id = str(inst["instance_id"])
            canonical = canonical_by_id[instance_id]
            old = str(inst.get("logical_graph", ""))
            if old != canonical:
                inst["logical_graph_original_removed_from_generated_root"] = old
                inst["logical_graph"] = canonical
            _rewrite_tensor_paths(inst, canonical)
        data["logical_graph_storage"] = {
            "canonical_root": str(logical_root),
            "generated_root_logical_graph_copies_removed": True,
            "note": "仅在 BPC_future/logical_graph 保留 solver-facing logical graph JSON；scenario 与 GNN tensor 文件保留在 generated 输出目录。",
        }
        manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _update_logical_index(task_count, combined_manifest_path=combined_manifest_path, logical_root=logical_root)

    for manifest_path in manifest_paths:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for inst in data.get("instances", []):
            old = inst.get("logical_graph_original_removed_from_generated_root")
            if old:
                path = Path(old)
                if path.exists():
                    path.unlink()
    for manifest_path in manifest_paths:
        root = Path(json.loads(manifest_path.read_text(encoding="utf-8")).get("output_root", manifest_path.parent))
        if root.exists():
            for path in root.glob("**/*_logical_graph.json"):
                if logical_root not in path.parents:
                    path.unlink()


def _rewrite_tensor_paths(inst: dict[str, Any], canonical_logical_graph: str) -> None:
    tensors = inst.get("gnn_tensors")
    if not isinstance(tensors, dict):
        return
    meta_path = Path(str(tensors.get("meta", "")))
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        old = meta.get("logical_graph_path")
        if old != canonical_logical_graph:
            if old:
                meta["logical_graph_original_removed_from_generated_root"] = old
            meta["logical_graph_path"] = canonical_logical_graph
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pt_path = Path(str(tensors.get("pt", "")))
    if pt_path.exists():
        import torch

        obj = torch.load(pt_path, map_location="cpu", weights_only=False)
        if isinstance(obj, dict) and obj.get("logical_graph_path") != canonical_logical_graph:
            old = obj.get("logical_graph_path")
            if old:
                obj["logical_graph_original_removed_from_generated_root"] = old
            obj["logical_graph_path"] = canonical_logical_graph
            torch.save(obj, pt_path)


def _update_logical_index(task_count: int, *, combined_manifest_path: Path, logical_root: Path) -> None:
    index_path = logical_root / "index.json"
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        index = {"version": "logical_graph_canonical_collection_v1", "files": []}
    existing = [entry for entry in index.get("files", []) if int(entry.get("task_count", -1)) != int(task_count)]
    combined = json.loads(combined_manifest_path.read_text(encoding="utf-8"))
    new_entries: list[dict[str, Any]] = []
    for inst in combined["instances"]:
        new_entries.append(
            {
                "instance_id": inst["instance_id"],
                "task_count": int(inst["task_count"]),
                "terrain": inst["terrain"],
                "time_window_mode": inst["time_window_mode"],
                "logical_graph": inst["logical_graph"],
                "source": inst["logical_graph"],
                "original_generated_logical_graph_removed": inst.get("logical_graph_original_removed_from_generated_root"),
                "scenario": inst.get("scenario"),
                "tensor_meta": (inst.get("gnn_tensors") or {}).get("meta"),
            }
        )
    index["files"] = sorted(existing + new_entries, key=lambda entry: (int(entry["task_count"]), str(entry["time_window_mode"]), str(entry["terrain"]), str(entry["instance_id"])))
    index["scales"] = sorted({int(entry["task_count"]) for entry in index["files"]})
    index["note"] = "Canonical logical graph collection. Generated-root logical_graph copies are removed after ingestion."
    index["logical_graph_storage"] = {
        "canonical_root": str(logical_root),
        "generated_root_logical_graph_copies_removed": True,
    }
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_scale(
    task_count: int,
    *,
    manifest_path: Path,
    logical_root: Path,
    results_root: Path,
    date_tag: str,
) -> Path:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    builder = FutureGraphBuilder()
    issues: list[dict[str, Any]] = []
    option_counts: list[int] = []
    expected_nodes = int(task_count) + 1
    expected_edges = expected_nodes * (expected_nodes - 1)
    for inst in manifest["instances"]:
        instance_id = str(inst["instance_id"])
        path = Path(inst["logical_graph"])
        if not path.exists():
            issues.append({"instance_id": instance_id, "issue": "missing logical_graph", "path": str(path)})
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        scenario_path = Path(payload.get("scenario", {}).get("scenario_path") or payload.get("scenario", {}).get("path") or inst.get("scenario", ""))
        if not scenario_path.exists():
            issues.append({"instance_id": instance_id, "issue": "missing scenario", "path": str(scenario_path)})
        logical = payload.get("logical_graph", {})
        if len(logical.get("nodes", [])) != expected_nodes:
            issues.append({"instance_id": instance_id, "issue": "node_count mismatch", "actual": len(logical.get("nodes", [])), "expected": expected_nodes})
        if len(logical.get("edges", [])) != expected_edges:
            issues.append({"instance_id": instance_id, "issue": "edge_count mismatch", "actual": len(logical.get("edges", [])), "expected": expected_edges})
        data = load_future_data(str(path))
        if len(data.tasks) != int(task_count):
            issues.append({"instance_id": instance_id, "issue": "loader task_count mismatch", "actual": len(data.tasks), "expected": int(task_count)})
        if len(data.arc_options) != expected_edges:
            issues.append({"instance_id": instance_id, "issue": "loader arc_options mismatch", "actual": len(data.arc_options), "expected": expected_edges})
        graph = builder.build_from_json(path)
        if tuple(graph.x.shape) != (expected_nodes, 9):
            issues.append({"instance_id": instance_id, "issue": "x shape mismatch", "actual": list(graph.x.shape), "expected": [expected_nodes, 9]})
        if tuple(graph.pair_edge_index.shape) != (2, expected_edges):
            issues.append({"instance_id": instance_id, "issue": "pair_edge_index shape mismatch", "actual": list(graph.pair_edge_index.shape), "expected": [2, expected_edges]})
        option_counts.append(int(graph.option_feat.shape[0]))
        audit = inst.get("balanced_audit", {})
        if float(audit.get("minimum_task_spacing_km", 0.0)) < 1.0 - 1.0e-9:
            issues.append({"instance_id": instance_id, "issue": "minimum_task_spacing_km below 1.0", "actual": audit.get("minimum_task_spacing_km")})
        tensors = inst.get("gnn_tensors") or {}
        meta_path = Path(str(tensors.get("meta", "")))
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("logical_graph_path") != str(path):
                issues.append({"instance_id": instance_id, "issue": "tensor meta logical_graph_path mismatch"})
        pt_path = Path(str(tensors.get("pt", "")))
        if pt_path.exists():
            import torch

            obj = torch.load(pt_path, map_location="cpu", weights_only=False)
            if isinstance(obj, dict) and obj.get("logical_graph_path") != str(path):
                issues.append({"instance_id": instance_id, "issue": "pt logical_graph_path mismatch"})

    generated_roots = [Path(root) for root in manifest.get("part_output_roots", [])] + [Path(manifest.get("output_root", ""))]
    generated_leftovers = 0
    for root in generated_roots:
        if root.exists():
            generated_leftovers += sum(1 for _ in root.glob("**/*_logical_graph.json"))
    canonical_count = sum(1 for _ in (logical_root / f"tasks_{task_count:03d}").glob("**/*_logical_graph.json"))
    summary = {
        "task_count": int(task_count),
        "validated_count": len(manifest["instances"]),
        "issue_count": len(issues),
        "issues": issues[:100],
        "canonical_logical_graph_json_count": canonical_count,
        "generated_root_logical_graph_json_count": generated_leftovers,
        "expected_nodes": expected_nodes,
        "expected_directed_edges": expected_edges,
        "option_count_min": min(option_counts) if option_counts else None,
        "option_count_max": max(option_counts) if option_counts else None,
    }
    out = results_root / f"{date_tag}_tasks{task_count}_generation_validation.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if issues:
        raise RuntimeError(f"validation failed for task_count={task_count}; see {out}")
    return out


def _write_scale_report(
    task_count: int,
    *,
    manifest_path: Path,
    validation_path: Path,
    results_root: Path,
    date_tag: str,
    log_root: Path,
) -> Path:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    instances = manifest["instances"]
    attempts = manifest.get("attempts", [])
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for inst in instances:
        groups[(str(inst["terrain"]), str(inst["time_window_mode"]))].append(inst)
    attempts_by_group: Counter[tuple[str, str]] = Counter()
    skipped_by_group: Counter[tuple[str, str]] = Counter()
    skip_reasons: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for attempt in attempts:
        key = (str(attempt.get("terrain")), str(attempt.get("time_window_mode")))
        attempts_by_group[key] += 1
        if attempt.get("status") == "skipped":
            skipped_by_group[key] += 1
            skip_reasons[key][str(attempt.get("reason_bucket", "unknown"))] += 1

    total_attempts = len(attempts)
    total_skips = sum(1 for item in attempts if item.get("status") == "skipped")
    lines: list[str] = []
    lines.append(f"# {task_count}规模随机时间窗实例生成报告")
    lines.append("")
    lines.append("生成日期：2026-06-10。报告语言：中文。")
    lines.append("")
    lines.append("## 产物位置")
    lines.append("")
    lines.append(f"- 合并 manifest：`{manifest_path}`")
    lines.append(f"- canonical logical graph：`BPC_future/logical_graph/tasks_{task_count:03d}/`")
    lines.append(f"- 校验 JSON：`{validation_path}`")
    lines.append(f"- 分组生成日志目录：`{log_root}`")
    lines.append("- scenario、`.pt`、`.npz` tensor 仍保留在 generated part 输出目录；solver-facing logical graph JSON 只保留在 `BPC_future/logical_graph`。")
    lines.append("")
    lines.append("## 生成与校验总览")
    lines.append("")
    lines.append(f"- accepted 实例数：`{len(instances)}`")
    lines.append(f"- attempts：`{total_attempts}`")
    lines.append(f"- skips：`{total_skips}`")
    lines.append(f"- post-dedup 校验问题数：`{validation['issue_count']}`")
    lines.append(f"- canonical logical graph JSON 数：`{validation['canonical_logical_graph_json_count']}`")
    lines.append(f"- generated 源目录残留 logical graph JSON 数：`{validation['generated_root_logical_graph_json_count']}`")
    lines.append(f"- 每个实例图规模：`{validation['expected_nodes']}` nodes / `{validation['expected_directed_edges']}` directed pair edges。")
    lines.append(f"- option 数范围：`{validation['option_count_min']}` 到 `{validation['option_count_max']}`。")
    lines.append("")
    lines.append("## 分组接受率与关键分布")
    lines.append("")
    lines.append("| 地形 | 时间窗模式 | accepted/attempts | 接受率 | skip | time pair中位数 | time triple中位数 | energy pair中位数 | energy triple中位数 | window/horizon中位数 | spread/window中位数 | 最小点距中位数 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for key in sorted(groups):
        terrain, mode = key
        group = groups[key]
        accepted = len(group)
        attempts_count = attempts_by_group[key]
        skips = skipped_by_group[key]
        acceptance = accepted / attempts_count if attempts_count else 0.0
        lines.append(
            "| "
            + " | ".join(
                [
                    terrain,
                    mode,
                    f"{accepted}/{attempts_count}",
                    _fmt(acceptance),
                    str(skips),
                    _fmt(_median_metric(group, "time_pair_feasible_ratio")),
                    _fmt(_median_metric(group, "time_triple_feasible_ratio")),
                    _fmt(_median_metric(group, "energy_pair_feasible_ratio")),
                    _fmt(_median_metric(group, "energy_triple_feasible_ratio")),
                    _fmt(_median_metric(group, "window_width_median_ratio")),
                    _fmt(_median_metric(group, "multi_path_spread_to_window_width_median")),
                    _fmt(_median_metric(group, "minimum_task_spacing_km")),
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("## skip 原因")
    lines.append("")
    lines.append("| 地形 | 时间窗模式 | skip原因计数 |")
    lines.append("| --- | --- | --- |")
    for key in sorted(groups):
        terrain, mode = key
        reasons = skip_reasons.get(key, Counter())
        reason_text = "; ".join(f"{reason}: {count}" for reason, count in reasons.most_common()) if reasons else "无"
        lines.append(f"| {terrain} | {mode} | {reason_text} |")
    lines.append("")
    lines.append("## 审计解释")
    lines.append("")
    lines.append("- `pair/triple feasible ratio`、Wilson interval 和抽样方差只用于生成筛选，不进入求解器证明逻辑。")
    lines.append("- 正式 benchmark 默认保留完整 directed pair logical graph；没有在生成阶段剪边。")
    lines.append("- `spread/window` 使用多路径时间差与时间窗宽度的比例，数值过高表示多路径替换空间偏窄；本报告用于后续诊断而不是过滤证明。")
    lines.append("")
    lines.append("## 结论")
    lines.append("")
    if validation["issue_count"] == 0 and len(instances) == 60:
        lines.append(f"- {task_count}规模 60 个实例已生成、去重并通过读取校验，可以进入后续汇总。")
    else:
        lines.append(f"- {task_count}规模仍需复查：accepted={len(instances)}，issue_count={validation['issue_count']}。")
    report = results_root / f"{date_tag}_tasks{task_count}_generation_report_zh.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def _generation_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    attempts: Counter[str] = Counter()
    for inst in manifest.get("instances", []):
        key = f"tasks={int(inst['task_count']):03d}|mode={inst['time_window_mode']}|terrain={inst['terrain']}"
        groups[key].append(inst)
    for attempt in manifest.get("attempts", []):
        key = f"tasks={int(attempt['task_count']):03d}|mode={attempt['time_window_mode']}|terrain={attempt['terrain']}"
        attempts[key] += 1
    out: dict[str, Any] = {"group_by_task_mode_terrain": {}}
    for key, items in sorted(groups.items()):
        accepted = len(items)
        attempt_count = attempts[key]
        out["group_by_task_mode_terrain"][key] = {
            "accepted_count": accepted,
            "attempt_count": attempt_count,
            "acceptance_rate": round(accepted / attempt_count, 6) if attempt_count else 0.0,
            "metric_distributions": {
                metric: _dist([_metric(item, metric) for item in items])
                for metric in (
                    "time_pair_feasible_ratio",
                    "time_triple_feasible_ratio",
                    "energy_pair_feasible_ratio",
                    "energy_triple_feasible_ratio",
                    "energy_quad_feasible_ratio",
                    "energy_large_feasible_ratio",
                    "window_width_median_ratio",
                    "multi_path_spread_to_window_width_median",
                    "minimum_task_spacing_km",
                )
            },
        }
    return out


def _metric(inst: dict[str, Any], name: str) -> float:
    audit = inst.get("balanced_audit", {})
    if name == "multi_path_spread_to_window_width_median":
        return float((audit.get("multi_path_spread_to_window_width_distribution") or {}).get("median", math.nan))
    return float(audit.get(name, math.nan))


def _median_metric(items: Sequence[dict[str, Any]], name: str) -> float:
    return _percentile([_metric(item, name) for item in items], 0.5)


def _dist(values: Iterable[float]) -> dict[str, Any]:
    vals = sorted(float(v) for v in values if math.isfinite(float(v)))
    if not vals:
        return {"count": 0}
    return {
        "count": len(vals),
        "min": round(vals[0], 6),
        "median": round(_percentile(vals, 0.5), 6),
        "mean": round(sum(vals) / len(vals), 6),
        "max": round(vals[-1], 6),
    }


def _percentile(values: Sequence[float], pct: float) -> float:
    vals = sorted(float(v) for v in values if math.isfinite(float(v)))
    if not vals:
        return math.nan
    pos = (len(vals) - 1) * float(pct)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return vals[lo]
    return vals[lo] * (hi - pos) + vals[hi] * (pos - lo)


def _fmt(value: float) -> str:
    if not math.isfinite(float(value)):
        return "nan"
    return f"{float(value):.3f}"


def _mode_slug(mode: str) -> str:
    return str(mode).replace("-", "_")


if __name__ == "__main__":
    main()
