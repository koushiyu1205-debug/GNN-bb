#!/usr/bin/env python3
"""Sequential V3 development census for exact top-3 branch opportunities."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from time import time


ROOT = Path(__file__).resolve().parents[1]
STATE_RUNNER = (
    ROOT / "scripts/run_p0_no_task_wait_v3_branch_state_oracle.py"
)
GENERATOR_DOMAINS = (
    "synthetic_polar_resource_grid_v1",
    "real_lunar_south_pole_sp50_benchmark_v1",
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _existing_status(output_dir: Path) -> dict | None:
    opportunity_path = output_dir / "branch_opportunity_report.json"
    if opportunity_path.is_file():
        report = _load_json(opportunity_path)
        raw_status = str(report.get("opportunity_status") or "")
        status = {
            "EXACT_ACTIONABLE_ROOT": "EXACT_ACTIONABLE",
            "EXACT_NONACTIONABLE_ROOT": "EXACT_NONACTIONABLE",
            "TREE_ROOT_CENSORED": "TREE_CENSORED",
        }.get(raw_status, "INFRASTRUCTURE_CENSORED")
        return {
            "status": status,
            "root_exact_safe": bool(
                report.get("root_source_exact_safe")
            ),
            "control_exact_safe": bool(
                report.get("p0_root_node_exact_safe")
            ),
            "actionable_state_count": (
                1 if status == "EXACT_ACTIONABLE" else 0
            ),
            "root_wall_sec": float(report.get("root_wall_sec") or 0.0),
            "tree_wall_sec": float(
                report.get("p0_root_node_wall_sec") or 0.0
            ),
            "candidate_count": int(report.get("candidate_count") or 0),
            "tree_result_is_exact_bpc": False,
            "opportunity_node_lp_exact_safe": bool(
                report.get("p0_root_node_exact_safe")
            ),
        }
    report_path = output_dir / "state_oracle_report.json"
    if report_path.is_file():
        report = _load_json(report_path)
        return {
            "status": (
                "EXACT_ACTIONABLE"
                if int(report.get("actionable_state_count") or 0) > 0
                else "EXACT_NONACTIONABLE"
            ),
            "root_exact_safe": bool(report.get("root_exact_safe")),
            "control_exact_safe": bool(report.get("control_exact_safe")),
            "actionable_state_count": int(
                report.get("actionable_state_count") or 0
            ),
            "root_wall_sec": float(
                (report.get("control") or {}).get("root_wall_sec") or 0.0
            ),
            "tree_wall_sec": float(
                (report.get("control") or {}).get("tree_wall_sec") or 0.0
            ),
        }
    root_path = output_dir / "root_source.json"
    if root_path.is_file():
        root = _load_json(root_path)
        result = root.get("result") or {}
        if not bool(root.get("root_exact_safe")):
            return {
                "status": "ROOT_CENSORED",
                "root_exact_safe": False,
                "control_exact_safe": False,
                "actionable_state_count": 0,
                "root_wall_sec": float(root.get("root_wall_sec") or 0.0),
                "tree_wall_sec": 0.0,
                "pricing_state": result.get("pricing_state"),
                "certificate_scope": result.get("certificate_scope"),
                "pricing_round_count": int(
                    result.get("pricing_round_count") or 0
                ),
            }
        control_summary_path = output_dir / "control_rank0_summary.json"
        control_tree_path = output_dir / "control_rank0_tree.json"
        if control_summary_path.is_file() and control_tree_path.is_file():
            control_summary = _load_json(control_summary_path)
            control = _load_json(control_tree_path)
            if not bool(control_summary.get("exact_safe")):
                return {
                    "status": "TREE_CENSORED",
                    "root_exact_safe": True,
                    "control_exact_safe": False,
                    "actionable_state_count": 0,
                    "root_wall_sec": float(
                        root.get("root_wall_sec") or 0.0
                    ),
                    "tree_wall_sec": float(
                        control_summary.get("tree_wall_sec") or 0.0
                    ),
                    "pricing_state": control.get("pricing_state"),
                    "certificate_scope": control.get("certificate_scope"),
                    "node_count": int(control.get("node_count") or 0),
                    "incomplete_node_count": int(
                        control.get("incomplete_node_count") or 0
                    ),
                }
    return None


def _summary(rows: list[dict]) -> dict:
    counts = {}
    for row in rows:
        status = str(row["status"])
        counts[status] = counts.get(status, 0) + 1
    exact_count = sum(
        row["status"] in {"EXACT_ACTIONABLE", "EXACT_NONACTIONABLE"}
        for row in rows
    )
    actionable_count = sum(
        row["status"] == "EXACT_ACTIONABLE" for row in rows
    )
    return {
        "attempted_instance_count": len(rows),
        "status_counts": counts,
        "exact_count": exact_count,
        "exact_actionable_instance_count": actionable_count,
        "exact_actionable_rate": (
            actionable_count / exact_count if exact_count else None
        ),
        "actionable_state_count": sum(
            int(row.get("actionable_state_count") or 0) for row in rows
        ),
    }


def _development_rows(
    manifest: dict,
    *,
    scale: int,
    instance_generator_domain: str | None,
    instance_content_hashes: set[str] | None = None,
) -> list[dict]:
    rows = [
        row
        for row in manifest.get("development", ())
        if int(row["scale"]) == int(scale)
        and (
            instance_generator_domain is None
            or str(row.get("instance_generator_domain") or "")
            == str(instance_generator_domain)
        )
        and (
            not instance_content_hashes
            or str(row["instance_content_hash"])
            in instance_content_hashes
        )
    ]
    rows.sort(
        key=lambda row: str(row["instance_content_hash"])
    )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--split-manifest",
        default=(
            "data/gat_p0v2/"
            "p0_no_task_wait_v3_gat_split_rebind_manifest.json"
        ),
    )
    parser.add_argument("--scale", type=int, choices=(20, 30), required=True)
    parser.add_argument(
        "--instance-generator-domain",
        choices=GENERATOR_DOMAINS,
        default=None,
    )
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--max-new-instances", type=int, default=12)
    parser.add_argument(
        "--instance-content-hash",
        action="append",
        default=[],
        help=(
            "Restrict the census to precommitted development hashes; "
            "repeat for multiple instances."
        ),
    )
    parser.add_argument("--stop-after-actionable", type=int, default=4)
    parser.add_argument("--root-wall-time-limit-sec", type=float, default=240.0)
    parser.add_argument("--tree-wall-time-limit-sec", type=float, default=300.0)
    args = parser.parse_args()

    split_path = (ROOT / args.split_manifest).resolve()
    output_root = (ROOT / args.output_root).resolve()
    manifest = _load_json(split_path)
    rows = _development_rows(
        manifest,
        scale=int(args.scale),
        instance_generator_domain=args.instance_generator_domain,
        instance_content_hashes={
            str(value) for value in args.instance_content_hash
        },
    )
    requested_hashes = {
        str(value) for value in args.instance_content_hash
    }
    if requested_hashes != {
        str(row["instance_content_hash"]) for row in rows
    } and requested_hashes:
        raise SystemExit(
            "requested census hash is absent from the selected development "
            "partition/domain/scale"
        )
    if args.instance_generator_domain is not None and not rows:
        raise SystemExit(
            "no development rows match the requested generator domain"
        )
    # V2 difficulty labels are retained only as stale diagnostics.  They must
    # not determine the V3 census sample or stopping point.
    progress_path = output_root / "opportunity_census_progress.json"
    observed = []
    new_attempts = 0
    for row in rows:
        instance_path = Path(str(row["instance_path"]))
        instance_key = instance_path.stem.removesuffix("_logical_graph")
        instance_output = (
            output_root / f"scale{int(args.scale):02d}_{instance_key}"
        )
        status = _existing_status(instance_output)
        if status is None:
            if new_attempts >= max(0, int(args.max_new_instances)):
                continue
            new_attempts += 1
            command = [
                sys.executable,
                str(STATE_RUNNER),
                "--instance",
                str(instance_path),
                "--split-manifest",
                str(split_path),
                "--output-dir",
                str(instance_output),
                "--max-states",
                "0",
                "--opportunity-only",
                "--root-wall-time-limit-sec",
                str(float(args.root_wall_time_limit_sec)),
                "--tree-wall-time-limit-sec",
                str(float(args.tree_wall_time_limit_sec)),
            ]
            env = dict(os.environ)
            env["PYTHONPATH"] = (
                f"{ROOT / 'src'}:{ROOT / 'build/native-spprc'}"
            )
            started = time()
            completed = subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                check=False,
                text=True,
                capture_output=True,
            )
            status = _existing_status(instance_output)
            if status is None:
                status = {
                    "status": "INFRASTRUCTURE_CENSORED",
                    "root_exact_safe": False,
                    "control_exact_safe": False,
                    "actionable_state_count": 0,
                    "root_wall_sec": 0.0,
                    "tree_wall_sec": 0.0,
                    "returncode": int(completed.returncode),
                    "stdout_tail": completed.stdout[-2000:],
                    "stderr_tail": completed.stderr[-2000:],
                }
            status["driver_wall_sec"] = round(time() - started, 6)
            status["returncode"] = int(completed.returncode)
            _write_json(
                instance_output / "census_driver_result.json",
                status,
            )
        observed.append(
            {
                "instance_id": row["instance_id"],
                "instance_content_hash": row["instance_content_hash"],
                "instance_path": str(instance_path),
                "source_p0_difficulty_bin": row.get("p0_difficulty_bin"),
                "source_p0_difficulty_is_stale": True,
                "output_dir": str(instance_output),
                **status,
            }
        )
        payload = {
            "schema_version": (
                "lunar_ice_bpc.no_task_wait_v3_branch_opportunity_census.v1"
            ),
            "scale": int(args.scale),
            "instance_generator_domain": (
                args.instance_generator_domain
            ),
            "split_manifest_hash": manifest.get("manifest_hash"),
            "development_only": True,
            "training_authorized": False,
            "requested_instance_content_hashes": sorted(
                requested_hashes
            ),
            "rows": observed,
            "summary": _summary(observed),
        }
        _write_json(progress_path, payload)
        print(
            json.dumps(
                {
                    "instance_id": row["instance_id"],
                    **status,
                    "summary": payload["summary"],
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            flush=True,
        )
        if (
            int(payload["summary"]["exact_actionable_instance_count"])
            >= max(1, int(args.stop_after_actionable))
        ):
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
