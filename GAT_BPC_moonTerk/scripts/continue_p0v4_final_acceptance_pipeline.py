#!/usr/bin/env python3
"""Serially continue the already-prepared P0V4 final acceptance pipeline.

This is an outer orchestration helper only.  It never edits candidate configs,
does not run two large-scale stages concurrently, and does not freeze a
candidate.  The helper waits for the separately launched scale50 held-out
stage, validates its terminal state and launch binding, then executes the
remaining registered stages in order.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_p0v4_final_acceptance.py"
SCHEMA = "lunar_ice_bpc.p0v4_final_acceptance_pipeline.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--wait-timeout-sec", type=float, default=86_400.0)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    config = _resolve(args.config)
    output = _resolve(args.output_dir)
    if not config.is_file():
        raise SystemExit(f"acceptance config is missing: {config}")
    if float(args.poll_sec) <= 0.0 or float(args.poll_sec) > 60.0:
        parser.error("--poll-sec must be in (0, 60]")
    if float(args.wait_timeout_sec) <= 0.0:
        parser.error("--wait-timeout-sec must be positive")

    manifest_path = output / "pipeline_manifest.json"
    if manifest_path.exists():
        raise SystemExit(
            "pipeline manifest already exists; refusing a second orchestrator"
        )
    binding = {
        "config": str(config),
        "config_sha256": _sha256(config),
        "runner": str(RUNNER.resolve()),
        "runner_sha256": _sha256(RUNNER),
        "output_dir": str(output),
        "stages": [
            "wait-exact-scale50-heldout",
            "exact-scale50-001",
            "exact-small30",
            "scale100",
            "summarize",
        ],
        "large_scale_concurrency": 1,
        "automatic_freeze": False,
    }
    manifest = {
        "schema_version": SCHEMA,
        "status": "WAITING_FOR_HELDOUT",
        "created_at_utc": _now(),
        "binding": binding,
        "binding_hash": _payload_hash(binding),
        "rows": [],
        "freeze_attempted": False,
    }
    _write_json(manifest_path, manifest)

    heldout_root = output / "official/Exact/scale50_heldout"
    heldout_launch = heldout_root / "p0v4_launch_manifest.json"
    started = time.monotonic()
    last_heartbeat = 0.0
    while not heldout_launch.is_file():
        elapsed = time.monotonic() - started
        if elapsed >= float(args.wait_timeout_sec):
            return _stop(
                manifest_path,
                manifest,
                status="HELDOUT_WAIT_TIMEOUT",
                issue="heldout_launch_manifest_not_created",
            )
        if elapsed - last_heartbeat >= 600.0 or last_heartbeat == 0.0:
            print(
                f"waiting for heldout launch manifest elapsed={elapsed:.1f}s",
                flush=True,
            )
            last_heartbeat = elapsed
        time.sleep(float(args.poll_sec))

    heldout_issues = _completed_stage_issues(
        heldout_root,
        expected_rows=19,
        expected_runner_sha=binding["runner_sha256"],
    )
    manifest["rows"].append(
        {
            "stage": "wait-exact-scale50-heldout",
            "status": "PASS" if not heldout_issues else "FAIL",
            "issues": heldout_issues,
            "launch_manifest": str(heldout_launch.resolve()),
            "launch_manifest_sha256": _sha256(heldout_launch),
        }
    )
    if heldout_issues:
        return _stop(
            manifest_path,
            manifest,
            status="HELDOUT_EVIDENCE_INVALID",
            issue=";".join(heldout_issues),
        )

    stages = (
        ("exact-scale50-001", output / "official/Exact/scale50_001", 1),
        ("exact-small30", output / "official/Exact/small30", 80),
        ("scale100", output / "diagnostic/scale100", 10),
        ("summarize", output, None),
    )
    for stage, stage_root, expected_rows in stages:
        if _sha256(RUNNER) != binding["runner_sha256"]:
            return _stop(
                manifest_path,
                manifest,
                status="IMPLEMENTATION_BINDING_DRIFT",
                issue=f"runner_changed_before_{stage}",
            )
        command = [
            sys.executable,
            str(RUNNER),
            "--config",
            str(config),
            "--output-dir",
            str(output),
            "--stage",
            stage,
            "--resume",
        ]
        print(f"starting stage={stage}", flush=True)
        stage_started = time.monotonic()
        completed = subprocess.run(command, cwd=ROOT, check=False)
        elapsed = time.monotonic() - stage_started
        issues = []
        if int(completed.returncode) != 0:
            issues.append(f"stage_returncode_{completed.returncode}")
        if expected_rows is not None:
            if stage == "scale100":
                issues.extend(
                    _completed_stage_issues(
                        stage_root / "P0V4",
                        expected_rows=5,
                        expected_runner_sha=binding["runner_sha256"],
                    )
                )
                issues.extend(
                    "final_candidate:" + issue
                    for issue in _completed_stage_issues(
                        stage_root / "FinalCandidate",
                        expected_rows=5,
                        expected_runner_sha=binding["runner_sha256"],
                    )
                )
            else:
                issues.extend(
                    _completed_stage_issues(
                        stage_root,
                        expected_rows=int(expected_rows),
                        expected_runner_sha=binding["runner_sha256"],
                    )
                )
        else:
            summary = output / "final_acceptance_summary.json"
            if not summary.is_file():
                issues.append("final_acceptance_summary_missing")
            elif not bool(
                _load_json(summary).get("all_required_evidence_available")
            ):
                issues.append("formal_evidence_incomplete_after_summarize")
        manifest["rows"].append(
            {
                "stage": stage,
                "status": "PASS" if not issues else "FAIL",
                "issues": issues,
                "returncode": int(completed.returncode),
                "wall_time_sec": elapsed,
                "command": command,
            }
        )
        manifest["status"] = (
            "RUNNING" if not issues else f"STOPPED_AFTER_{stage}"
        )
        _write_json(manifest_path, manifest)
        if issues:
            return 2

    manifest["status"] = "PIPELINE_EVIDENCE_COMPLETE_NOT_FROZEN"
    manifest["completed_at_utc"] = _now()
    manifest["freeze_attempted"] = False
    _write_json(manifest_path, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True), flush=True)
    return 0


def _completed_stage_issues(
    root: Path,
    *,
    expected_rows: int,
    expected_runner_sha: str,
) -> list[str]:
    issues = []
    launch_path = root / "p0v4_launch_manifest.json"
    if not launch_path.is_file():
        return ["launch_manifest_missing"]
    launch = _load_json(launch_path)
    if not bool(launch.get("evidence_usable")):
        issues.append("launch_evidence_not_usable")
    if not bool(launch.get("implementation_stable_during_launch")):
        issues.append("implementation_changed_during_launch")
    before = str(launch.get("implementation_binding_hash_before") or "")
    after = str(launch.get("implementation_binding_hash_after") or "")
    if not before or before != after:
        issues.append("implementation_binding_mismatch")
    if _sha256(RUNNER) != expected_runner_sha:
        issues.append("runner_hash_drift")
    states = sorted(root.rglob("b4_2_cold_exact_state.json"))
    rows = []
    for state in states:
        payload = _load_json(state)
        rows.extend(dict(row) for row in payload.get("rows") or ())
    identities = {
        (int(row.get("scale") or 0), str(row.get("instance_key") or ""))
        for row in rows
    }
    if len(rows) != expected_rows or len(identities) != expected_rows:
        issues.append(
            f"terminal_row_count_{len(rows)}_identity_count_"
            f"{len(identities)}_expected_{expected_rows}"
        )
    if any(not bool(row.get("row_terminal")) for row in rows):
        issues.append("nonterminal_state_row")
    return issues


def _stop(
    manifest_path: Path,
    manifest: dict,
    *,
    status: str,
    issue: str,
) -> int:
    manifest["status"] = status
    manifest["stopped_at_utc"] = _now()
    manifest.setdefault("issues", []).append(issue)
    manifest["freeze_attempted"] = False
    _write_json(manifest_path, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True), flush=True)
    return 2


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _payload_hash(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
