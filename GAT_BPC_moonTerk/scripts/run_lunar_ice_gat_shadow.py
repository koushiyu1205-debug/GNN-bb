#!/usr/bin/env python3
"""Write a shadow-only guidance report for a lunar-ice instance."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.shadow_policy import build_shadow_report
from lunar_ice_bpc.io.config import apply_overrides, load_config
from lunar_ice_bpc.io.instance_io import read_json, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--instance", default=None)
    parser.add_argument("--instances", nargs="*", default=None)
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--scales", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--summary-json", default=None)
    parser.add_argument("--set", dest="overrides", action="append", default=[])
    args = parser.parse_args()
    config = apply_overrides(load_config(ROOT / args.config), args.overrides) if args.config else apply_overrides({}, args.overrides)
    _validate_shadow_only_config(config, parser)
    instance_paths = _resolve_instance_paths(args, config, parser)
    output_dir = _root_path(args.output_dir or config.get("output_dir", "runs/logs"))
    explicit_output = args.output or config.get("output")
    if explicit_output and len(instance_paths) != 1:
        parser.error("--output is only valid for a single shadow instance")

    rows = []
    for instance_path in instance_paths:
        report = build_shadow_report(read_json(instance_path))
        _validate_report_schema(report, config, parser)
        if explicit_output:
            output = _root_path(explicit_output)
        else:
            output = output_dir / instance_path.parent.name / f"{instance_path.stem}_gat_shadow.json"
        write_json(output, report)
        rows.append(
            {
                "instance_path": str(instance_path),
                "report_path": str(output),
                "instance_id": report["instance_id"],
                "mode": report["mode"],
                "mutates_solver": report["mutates_solver"],
                "can_certify": report["can_certify"],
                "exact_status_effect": report["exact_status_effect"],
                "node_count": report["node_count"],
                "edge_count": report["edge_count"],
            }
        )
    summary = _summary(rows)
    summary_json = args.summary_json or config.get("summary_json")
    if summary_json:
        write_json(_root_path(summary_json), summary)
    print(
        "wrote {run_count} shadow reports; mode=shadow_only; "
        "mode_counts={mode_counts}; mutates_solver_count={mutates_solver_count}".format(
            **summary
        )
    )
    return 0


def _validate_shadow_only_config(config: dict, parser: argparse.ArgumentParser) -> None:
    if not config:
        return
    guidance_mode = str(config.get("guidance_mode", "shadow_only"))
    if guidance_mode != "shadow_only":
        parser.error(f"run_lunar_ice_gat_shadow.py only accepts guidance_mode='shadow_only', got {guidance_mode!r}")
    if bool(config.get("journey_gat_optin_enabled", False)):
        parser.error("shadow runner refuses journey_gat_optin_enabled=true")
    if bool(config.get("mutates_solver", False)):
        parser.error("shadow runner refuses mutating guidance configs")
    if bool(config.get("can_certify", False)):
        parser.error("guidance configs cannot certify")
    if config.get("journey_gat_shadow_enabled") is False:
        parser.error("shadow config must set journey_gat_shadow_enabled=true")


def _resolve_instance_paths(args: argparse.Namespace, config: dict, parser: argparse.ArgumentParser) -> list[Path]:
    raw_instances: list[str] = []
    if args.instance:
        raw_instances.append(str(args.instance))
    if args.instances:
        raw_instances.extend(str(item) for item in args.instances)
    if config.get("instance"):
        raw_instances.append(str(config["instance"]))
    if isinstance(config.get("instances"), list):
        raw_instances.extend(str(item) for item in config["instances"])
    manifest_value = args.manifest or config.get("manifest") or config.get("manifest_path")
    if not raw_instances and manifest_value:
        return _manifest_instance_paths(_root_path(manifest_value), scales=_parse_scales(args.scales or config.get("scales")))
    if not raw_instances:
        parser.error("provide --instance, --instances, or a manifest with optional --scales")
    return [_root_path(raw) for raw in raw_instances]


def _manifest_instance_paths(manifest_path: Path, *, scales: list[int] | None) -> list[Path]:
    manifest = read_json(manifest_path)
    allowed = {f"{int(scale):03d}" for scale in scales} if scales else None
    paths: list[Path] = []
    for row in manifest.get("instances", []):
        label = _manifest_row_scale_label(row)
        if allowed is not None and label not in allowed:
            continue
        raw = Path(str(row["path"]))
        paths.append(raw if raw.is_absolute() else ROOT / raw)
    return paths


def _manifest_row_scale_label(row: dict) -> str:
    if row.get("scale_label") is not None:
        return f"{int(str(row['scale_label']).strip()):03d}"
    if row.get("scale") is not None:
        return f"{int(row['scale']):03d}"
    path = str(row.get("path", ""))
    for scale in (5, 10, 20, 30, 50, 100):
        if f"lunar_ice_{scale:03d}" in path:
            return f"{scale:03d}"
    return ""


def _parse_scales(value) -> list[int] | None:
    if value is None or value == "":
        return None
    if isinstance(value, (list, tuple)):
        return [int(item) for item in value]
    return [int(item.strip()) for item in str(value).split(",") if item.strip()]


def _root_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _validate_report_schema(report: dict, config: dict, parser: argparse.ArgumentParser) -> None:
    expected_report_schema = config.get("expected_shadow_report_schema_version")
    if expected_report_schema and report.get("schema_version") != expected_report_schema:
        parser.error(
            f"shadow report schema mismatch: got {report.get('schema_version')!r}, expected {expected_report_schema!r}"
        )
    expected_graph_schema = config.get("expected_guidance_graph_schema_version")
    if expected_graph_schema and report.get("guidance_graph_schema_version") != expected_graph_schema:
        parser.error(
            "guidance graph schema mismatch: "
            f"got {report.get('guidance_graph_schema_version')!r}, expected {expected_graph_schema!r}"
        )


def _summary(rows: list[dict]) -> dict:
    mode_counts: dict[str, int] = {}
    exact_effect_counts: dict[str, int] = {}
    for row in rows:
        mode = str(row.get("mode") or "missing")
        exact_effect = str(row.get("exact_status_effect") or "missing")
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
        exact_effect_counts[exact_effect] = exact_effect_counts.get(exact_effect, 0) + 1
    return {
        "schema_version": "lunar_ice_bpc.gat_shadow_summary.v1",
        "run_count": len(rows),
        "mode_counts": dict(sorted(mode_counts.items())),
        "exact_status_effect_counts": dict(sorted(exact_effect_counts.items())),
        "mutates_solver_count": sum(1 for row in rows if row.get("mutates_solver")),
        "can_certify_count": sum(1 for row in rows if row.get("can_certify")),
        "report_count": len(rows),
        "reports": rows,
        "note": "Shadow-only diagnostic guidance; reports are not solver mutations, lower bounds, or certificates.",
    }


if __name__ == "__main__":
    raise SystemExit(main())
