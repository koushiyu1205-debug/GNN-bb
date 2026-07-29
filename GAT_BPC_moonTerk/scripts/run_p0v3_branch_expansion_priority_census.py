#!/usr/bin/env python3
"""Resume-safe, development-only S30 census for a precommitted expansion.

Every expansion row is eventually screened.  The resulting priority signal
may schedule expensive exact collection, but it cannot filter a row or become
a branch-training label.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from time import time


ROOT = Path(__file__).resolve().parents[1]
SCREEN_SCRIPT = (
    ROOT / "scripts/run_p0_no_task_wait_v3_branch_priority_screen.py"
)
SCHEMA_VERSION = (
    "lunar_ice_bpc.no_task_wait_v3_branch_expansion_priority_census.v1"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_json(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _row_key(row: dict) -> tuple:
    role = str(row.get("pool_role") or "")
    role_order = (
        0 if role == "UNBIASED_EXPANSION_CENSUS" else 1
    )
    return (
        role_order,
        int(row["scale_hash_order_index"]),
        int(row["scale"]),
        str(row["instance_content_hash"]),
    )


def _result_dir(output_root: Path, row: dict) -> Path:
    safe_id = "".join(
        character
        if character.isalnum() or character in "._-"
        else "_"
        for character in str(row["instance_id"])
    )
    return output_root / f"scale{int(row['scale'])}_{safe_id}_budget30"


def _valid_completed_report(
    *, report_path: Path, row: dict, manifest_hash: str
) -> dict | None:
    if not report_path.exists():
        return None
    report = _load(report_path)
    if (
        str(report.get("instance_content_hash") or "")
        != str(row["instance_content_hash"])
        or str(report.get("split_manifest_hash") or "")
        != manifest_hash
        or report.get("development_only") is not True
        or report.get("is_branch_training_label") is not False
        or report.get("may_permanently_filter_development_instance")
        is not False
    ):
        raise RuntimeError(
            f"stale or incompatible report: {report_path}"
        )
    return report


def _summary(
    *,
    manifest_path: Path,
    manifest: dict,
    rows: list[dict],
    output_root: Path,
    failures: list[dict],
) -> dict:
    completed = []
    pending = []
    manifest_hash = str(manifest["manifest_hash"])
    for row in rows:
        report_path = (
            _result_dir(output_root, row)
            / "branch_priority_screen.json"
        )
        report = _valid_completed_report(
            report_path=report_path,
            row=row,
            manifest_hash=manifest_hash,
        )
        if report is None:
            pending.append(
                {
                    "instance_id": row["instance_id"],
                    "instance_content_hash": row[
                        "instance_content_hash"
                    ],
                    "scale": int(row["scale"]),
                    "pool_role": row["pool_role"],
                }
            )
            continue
        completed.append(
            {
                "instance_id": row["instance_id"],
                "instance_content_hash": row[
                    "instance_content_hash"
                ],
                "scale": int(row["scale"]),
                "pool_role": row["pool_role"],
                "screen_wall_sec": report["screen_wall_sec"],
                "cut_aware_candidate_count": int(
                    report["cut_aware_candidate_count"]
                ),
                "exact_promotion_recommended": bool(
                    report["exact_promotion_recommended"]
                ),
                "report_path": str(report_path),
            }
        )
    counts = {}
    for scale in (20, 30):
        scale_completed = [
            row for row in completed if int(row["scale"]) == scale
        ]
        counts[str(scale)] = {
            "precommitted": sum(
                int(row["scale"]) == scale for row in rows
            ),
            "completed": len(scale_completed),
            "pending": sum(
                int(row["scale"]) == scale for row in pending
            ),
            "priority_hits": sum(
                bool(row["exact_promotion_recommended"])
                for row in scale_completed
            ),
        }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "development_only": True,
        "deployable": False,
        "training_authorized": False,
        "is_branch_training_label": False,
        "is_exact_opportunity_decision": False,
        "may_permanently_filter_development_instance": False,
        "all_precommitted_rows_eventually_screened": True,
        "content_manifest_path": str(manifest_path),
        "content_manifest_hash": manifest_hash,
        "precommitted_row_count": len(rows),
        "completed": completed,
        "pending": pending,
        "counts_by_scale": counts,
        "failures": failures,
        "updated_unix_sec": time(),
    }
    payload["summary_hash"] = _sha256_json(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-manifest", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--screen-budget-sec", type=float, default=30.0)
    parser.add_argument("--max-new-instances", type=int, default=1)
    parser.add_argument(
        "--scale",
        type=int,
        choices=(20, 30),
        action="append",
    )
    args = parser.parse_args()
    if float(args.screen_budget_sec) <= 0:
        raise SystemExit("screen budget must be positive")
    if int(args.max_new_instances) < 0:
        raise SystemExit("max-new-instances must be nonnegative")

    manifest_path = (ROOT / args.content_manifest).resolve()
    output_root = (ROOT / args.output_root).resolve()
    manifest = _load(manifest_path)
    audit = manifest.get("audit") or {}
    if (
        audit.get("passed") is not True
        or audit.get(
            "expansion_precommitted_before_priority_or_exact_screen"
        )
        is not True
        or manifest.get("calibration_read_authorized") is not False
        or manifest.get("training_authorized") is not False
    ):
        raise SystemExit("expanded content manifest is not admissible")
    scales = set(args.scale or (20, 30))
    rows = sorted(
        (
            row
            for row in manifest.get("development") or ()
            if row.get(
                "expansion_precommitted_before_screening"
            )
            is True
            and int(row["scale"]) in scales
        ),
        key=_row_key,
    )
    if not rows:
        raise SystemExit("no precommitted expansion rows selected")

    output_root.mkdir(parents=True, exist_ok=True)
    summary_path = output_root / "expansion_priority_census.json"
    failures: list[dict] = []
    launched = 0
    manifest_hash = str(manifest["manifest_hash"])
    for row in rows:
        result_dir = _result_dir(output_root, row)
        report_path = result_dir / "branch_priority_screen.json"
        if _valid_completed_report(
            report_path=report_path,
            row=row,
            manifest_hash=manifest_hash,
        ) is not None:
            continue
        if launched >= int(args.max_new_instances):
            break
        result_dir.mkdir(parents=True, exist_ok=True)
        command = [
            sys.executable,
            str(SCREEN_SCRIPT),
            "--instance",
            str(row["instance_path"]),
            "--split-manifest",
            str(manifest_path),
            "--output-dir",
            str(result_dir),
            "--screen-budget-sec",
            str(float(args.screen_budget_sec)),
            "--persist-warm-source",
        ]
        environment = os.environ.copy()
        environment["PYTHONPATH"] = os.pathsep.join(
            (
                str(ROOT / "src"),
                str(ROOT / "build/native-spprc"),
                environment.get("PYTHONPATH", ""),
            )
        ).rstrip(os.pathsep)
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            check=False,
            text=True,
            capture_output=True,
        )
        launched += 1
        (result_dir / "screen.stdout.log").write_text(
            completed.stdout,
            encoding="utf-8",
        )
        (result_dir / "screen.stderr.log").write_text(
            completed.stderr,
            encoding="utf-8",
        )
        if completed.returncode != 0:
            failures.append(
                {
                    "instance_id": row["instance_id"],
                    "instance_content_hash": row[
                        "instance_content_hash"
                    ],
                    "returncode": int(completed.returncode),
                    "stderr_tail": completed.stderr[-2000:],
                }
            )
        _write(
            summary_path,
            _summary(
                manifest_path=manifest_path,
                manifest=manifest,
                rows=rows,
                output_root=output_root,
                failures=failures,
            ),
        )
        if completed.returncode != 0:
            break

    summary = _summary(
        manifest_path=manifest_path,
        manifest=manifest,
        rows=rows,
        output_root=output_root,
        failures=failures,
    )
    _write(summary_path, summary)
    print(
        json.dumps(
            {
                "summary_path": str(summary_path),
                "launched": launched,
                "counts_by_scale": summary["counts_by_scale"],
                "failure_count": len(failures),
            },
            sort_keys=True,
        )
    )
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
