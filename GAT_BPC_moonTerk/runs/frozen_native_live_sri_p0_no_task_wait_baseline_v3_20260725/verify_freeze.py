#!/usr/bin/env python3
"""Verify the immutable P0 no-task-wait experimental baseline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


FREEZE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FREEZE_DIR.parents[1]
MANIFEST_PATH = FREEZE_DIR / "baseline_freeze_manifest.json"
REGISTRY_PATH = PROJECT_ROOT / "runs/native_bpc_baseline_registry.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_file(issues: list[str], *, path: str, expected_sha256: str) -> None:
    target = PROJECT_ROOT / path
    if not target.is_file():
        issues.append(f"missing:{path}")
        return
    actual = sha256_file(target)
    if actual != expected_sha256:
        issues.append(f"sha256:{path}:{actual}")


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    issues: list[str] = []

    for key in ("config_snapshot", "native_binary_snapshot", "candidate_snapshot"):
        row = manifest[key]
        check_file(issues, path=row["path"], expected_sha256=row["sha256"])

    for key in (
        "summary",
        "rows_json",
        "rows_csv",
        "report",
        "schedule",
        "resource_heartbeat",
    ):
        row = manifest["performance_evidence"][key]
        check_file(issues, path=row["path"], expected_sha256=row["sha256"])

    check_file(
        issues,
        path=manifest["verification"]["script"],
        expected_sha256=manifest["verification"]["script_sha256"],
    )

    candidate_path = PROJECT_ROOT / manifest["candidate_snapshot"]["path"]
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    source_mismatches: list[str] = []
    for row in candidate["source_bundle"]:
        path = PROJECT_ROOT / row["path"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            source_mismatches.append(row["path"])
    if source_mismatches:
        issues.append(f"source_bundle_mismatch_count:{len(source_mismatches)}")
    if candidate["source_bundle_hash"] != manifest["git_binding"]["source_bundle_sha256"]:
        issues.append("source_bundle_hash_manifest_mismatch")

    summary_path = PROJECT_ROOT / manifest["performance_evidence"]["summary"]["path"]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    expected_summary = {
        "status": "COMPLETE",
        "formal_full80": True,
        "strict_cold_start": True,
        "fresh_python_native_runtime_per_slot": True,
        "solver_resume": False,
        "completed_slot_count": 80,
        "expected_slot_count": 80,
        "exact_count": 80,
        "correctness_pass_count": 80,
        "new_baseline_freeze_authorized": True,
        "source_bundle_stable": True,
        "service_timing_policy_id": manifest["algorithm"]["service_timing_policy_id"],
        "engine_hash": manifest["native_binary_snapshot"]["engine_hash"],
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            issues.append(f"summary:{key}:{summary.get(key)!r}")

    rows_path = PROJECT_ROOT / manifest["performance_evidence"]["rows_json"]["path"]
    rows = json.loads(rows_path.read_text(encoding="utf-8"))
    if len(rows) != 80:
        issues.append(f"rows_count:{len(rows)}")
    required_scales = {5: 20, 10: 20, 20: 20, 30: 20}
    observed_scales = {
        scale: sum(int(row.get("scale", -1)) == scale for row in rows)
        for scale in required_scales
    }
    if observed_scales != required_scales:
        issues.append(f"scale_counts:{observed_scales}")
    for index, row in enumerate(rows):
        row_valid = (
            row.get("status") == "EXACT_CLOSED"
            and row.get("exact") is True
            and row.get("correctness_pass") is True
            and row.get("redlines_zero") is True
            and row.get("no_cheat_pass") is True
            and row.get("certificate_leak") == 0
            and row.get("manual_rc_fail") == 0
            and row.get("pricing_rc_fail") == 0
            and row.get("external_probe_used") is False
            and row.get("mature_pool_used") is False
            and row.get("manual_columns_used") is False
            and row.get("same_run_checkpoint_resume_used") is False
            and row.get("row_budget_exhausted") is False
            and row.get("service_timing_policy_id")
            == manifest["algorithm"]["service_timing_policy_id"]
            and row.get("observed_service_timing_policy_id")
            == manifest["algorithm"]["service_timing_policy_id"]
            and row.get("engine_build_hash")
            == manifest["native_binary_snapshot"]["engine_hash"]
            and row.get("live_cut_policy_hash")
            == manifest["algorithm"]["policy_hash"]
        )
        if not row_valid:
            issues.append(f"invalid_result_row:{index}")

    native_dir = FREEZE_DIR / "native"
    sys.path.insert(0, str(native_dir))
    try:
        import lunar_spprc_native

        build_info = dict(lunar_spprc_native.build_info())
        if build_info != candidate["native_build_info"]:
            issues.append("native_build_info_mismatch")
    except Exception as exc:
        build_info = {}
        issues.append(f"native_import:{type(exc).__name__}:{exc}")

    if not REGISTRY_PATH.is_file():
        issues.append("baseline_registry_missing")
    else:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        if registry.get("active_experiment_baseline_id") != manifest["freeze_id"]:
            issues.append("baseline_registry_active_id_mismatch")
        registry_rows = {
            row["freeze_id"]: row for row in registry.get("baselines", [])
        }
        registry_row = registry_rows.get(manifest["freeze_id"])
        if registry_row is None:
            issues.append("baseline_registry_row_missing")
        else:
            if registry_row.get("manifest_sha256") != sha256_file(MANIFEST_PATH):
                issues.append("baseline_registry_manifest_hash_mismatch")

    result = {
        "schema_version": "lunar_ice_bpc.baseline_freeze_verification.v2",
        "freeze_id": manifest["freeze_id"],
        "valid": not issues,
        "issues": issues,
        "source_bundle_checked_count": len(candidate["source_bundle"]),
        "source_bundle_mismatch_count": len(source_mismatches),
        "source_bundle_mismatches": source_mismatches,
        "result_row_count": len(rows),
        "result_scale_counts": observed_scales,
        "native_build_info": build_info,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
