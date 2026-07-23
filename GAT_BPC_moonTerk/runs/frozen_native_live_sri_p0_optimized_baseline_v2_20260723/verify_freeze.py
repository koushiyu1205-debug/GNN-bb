#!/usr/bin/env python3
"""Verify the frozen P0 baseline without mutating any artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


FREEZE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FREEZE_DIR.parents[1]
MANIFEST_PATH = FREEZE_DIR / "baseline_freeze_manifest.json"


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

    for key in (
        "config_snapshot",
        "native_binary_snapshot",
        "candidate_snapshot",
    ):
        row = manifest[key]
        check_file(issues, path=row["path"], expected_sha256=row["sha256"])

    for key in ("summary", "rows_json", "rows_csv", "report"):
        row = manifest["performance_evidence"][key]
        check_file(issues, path=row["path"], expected_sha256=row["sha256"])

    check_file(
        issues,
        path=manifest["verification"]["script"],
        expected_sha256=manifest["verification"]["script_sha256"],
    )
    check_file(
        issues,
        path=manifest["instance_binding"]["hash_manifest_path"],
        expected_sha256=manifest["instance_binding"]["hash_manifest_sha256"],
    )
    check_file(
        issues,
        path=manifest["legacy_baseline"]["summary_path"],
        expected_sha256=manifest["legacy_baseline"]["summary_sha256"],
    )

    candidate_path = PROJECT_ROOT / manifest["candidate_snapshot"]["path"]
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    source_mismatches: list[str] = []
    for row in candidate["source_bundle"]["files"]:
        path = PROJECT_ROOT / row["path"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            source_mismatches.append(row["path"])
    if source_mismatches:
        issues.append(f"source_bundle_mismatch_count:{len(source_mismatches)}")

    native_dir = FREEZE_DIR / "native"
    sys.path.insert(0, str(native_dir))
    try:
        import lunar_spprc_native

        build_info = dict(lunar_spprc_native.build_info())
        expected_info = candidate["native_build_info"]
        if build_info != expected_info:
            issues.append("native_build_info_mismatch")
    except Exception as exc:
        build_info = {}
        issues.append(f"native_import:{type(exc).__name__}:{exc}")

    result = {
        "schema_version": "lunar_ice_bpc.baseline_freeze_verification.v1",
        "freeze_id": manifest["freeze_id"],
        "valid": not issues,
        "issues": issues,
        "source_bundle_checked_count": len(candidate["source_bundle"]["files"]),
        "source_bundle_mismatch_count": len(source_mismatches),
        "source_bundle_mismatches": source_mismatches,
        "native_build_info": build_info,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
