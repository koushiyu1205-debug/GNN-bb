#!/usr/bin/env python3
"""Verify the immutable P0 V4 memory-compact experiment baseline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


FREEZE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = FREEZE_DIR.parents[1]
MANIFEST_PATH = FREEZE_DIR / "baseline_freeze_manifest.json"
REGISTRY_PATH = PROJECT_ROOT / "runs" / "native_bpc_baseline_registry.json"
EXPECTED_ID = "FROZEN_NATIVE_LIVE_SRI_P0_MEMORY_COMPACT_BASELINE_V4"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    issues: list[str] = []
    if manifest.get("freeze_id") != EXPECTED_ID:
        issues.append("freeze_id_mismatch")
    for relative, artifact in manifest.get("artifacts", {}).items():
        path = PROJECT_ROOT / relative
        if not path.is_file():
            issues.append(f"missing:{relative}")
        elif sha256_file(path) != artifact.get("sha256"):
            issues.append(f"sha256:{relative}")

    validation = manifest.get("performance", {})
    scale30 = validation.get("scale30", {})
    scale50 = validation.get("scale50_instance001", {})
    if (
        scale30.get("row_count") != 20
        or scale30.get("exact_count") != 20
        or scale30.get("incomplete_count") != 0
        or scale30.get("redline_count") != 0
        or scale30.get("mean_ratio", 2.0) > 1.0
        or scale30.get("paired_geometric_mean_ratio", 2.0) > 1.0
    ):
        issues.append("scale30_validation_mismatch")
    if (
        scale50.get("status") != "FAIL_CLOSED"
        or scale50.get("exact_count") != 0
        or scale50.get("redlines_zero") is not True
        or scale50.get("exact_root_closure") is not False
    ):
        issues.append("scale50_boundary_mismatch")
    scope = manifest.get("validation_scope", {})
    if (
        scope.get("scale50_full") != "NOT_RUN_BY_USER_DIRECTION"
        or scope.get("six_scale_promotion_complete") is not False
        or manifest.get("formal_full120_complete") is not False
    ):
        issues.append("validation_scope_overclaim")

    native_dir = FREEZE_DIR / "native"
    modules = sorted(native_dir.glob("lunar_spprc_native*.so"))
    if len(modules) != 1:
        issues.append("native_module_count")
        build_info = {}
    else:
        sys.path.insert(0, str(native_dir))
        try:
            import lunar_spprc_native  # type: ignore

            build_info = dict(lunar_spprc_native.build_info())
            if build_info != manifest.get("native_build_info"):
                issues.append("native_build_info_mismatch")
        except Exception as exc:
            build_info = {}
            issues.append(f"native_import:{type(exc).__name__}:{exc}")

    if not REGISTRY_PATH.is_file():
        issues.append("baseline_registry_missing")
    else:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        if registry.get("active_experiment_baseline_id") != EXPECTED_ID:
            issues.append("baseline_registry_active_id_mismatch")
        rows = {
            row.get("freeze_id"): row for row in registry.get("baselines", [])
        }
        row = rows.get(EXPECTED_ID)
        if row is None:
            issues.append("baseline_registry_row_missing")
        elif row.get("manifest_sha256") != sha256_file(MANIFEST_PATH):
            issues.append("baseline_registry_manifest_hash_mismatch")
        old = rows.get(manifest.get("historical_control_id"))
        if (
            old is None
            or old.get("status")
            != "preserved_historical_experiment_baseline"
            or old.get("superseded_as_active_by") != EXPECTED_ID
        ):
            issues.append("historical_control_not_preserved")
        if registry.get("production_default_policy") != "no_cut":
            issues.append("production_default_changed")

    result = {
        "schema_version": "lunar_ice_bpc.baseline_freeze_verification.v4",
        "freeze_id": EXPECTED_ID,
        "valid": not issues,
        "issues": issues,
        "artifact_count": len(manifest.get("artifacts", {})),
        "native_build_info": build_info,
        "known_scale50_boundary_preserved": (
            scale50.get("exact_root_closure") is False
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
