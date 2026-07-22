#!/usr/bin/env python3
"""Freeze the exact source/config/binary binding for formal Live SRI promotion."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

import yaml

from lunar_ice_bpc.exact.bpc.cuts.live_sri import LiveSriPolicy
from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_engine_build_hash


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy-config", type=Path, required=True)
    parser.add_argument("--no-cut-config", type=Path, required=True)
    parser.add_argument("--baseline-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    policy_config_path = args.policy_config.resolve()
    no_cut_config_path = args.no_cut_config.resolve()
    baseline_manifest_path = args.baseline_manifest.resolve()
    output_path = args.output.resolve()
    policy_config = yaml.safe_load(policy_config_path.read_text(encoding="utf-8"))
    no_cut_config = yaml.safe_load(no_cut_config_path.read_text(encoding="utf-8"))
    baseline_manifest = read_json(baseline_manifest_path)
    policy = LiveSriPolicy.named(str(policy_config.get("live_sri_policy")))
    no_cut_policy = LiveSriPolicy.named("no_cut")

    issues = []
    if policy.name != "P0":
        issues.append("formal candidate policy must be P0")
    if str(no_cut_config.get("live_sri_policy", "no_cut")) != "no_cut":
        issues.append("control config must be no_cut")
    if baseline_manifest.get("freeze_id") != "FROZEN_NATIVE_NO_CUT_BASELINE_V1":
        issues.append("baseline manifest freeze_id mismatch")
    no_cut_sha = sha256_file(no_cut_config_path)
    if no_cut_sha != baseline_manifest.get("config_sha256"):
        issues.append("control config does not match frozen baseline manifest")
    module_paths = sorted((ROOT / "build/native-spprc").glob("lunar_spprc_native*.so"))
    if len(module_paths) != 1:
        issues.append(f"expected exactly one native module, found {len(module_paths)}")
    if issues:
        raise SystemExit("; ".join(issues))

    module_path = module_paths[0]
    import lunar_spprc_native

    bundle_files = candidate_bundle_files()
    bundle_rows = [
        {"path": str(path.relative_to(ROOT)), "sha256": sha256_file(path)}
        for path in bundle_files
    ]
    dependencies = sorted(
        {
            f"{distribution.metadata.get('Name') or distribution.name}=={distribution.version}"
            for distribution in importlib.metadata.distributions()
        },
        key=str.lower,
    )
    manifest = {
        "schema_version": "lunar_ice_bpc.live_sri_candidate_freeze.v2",
        "candidate_id": "FROZEN_NATIVE_LIVE_SRI_P0_CANDIDATE_V1",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(ROOT),
        "base_git_commit": git_output("rev-parse", "HEAD"),
        "git_status_short_for_bundle": git_status_for_bundle(bundle_files),
        "source_bundle": {
            "file_count": len(bundle_rows),
            "sha256": stable_payload_hash(bundle_rows),
            "files": bundle_rows,
        },
        "policy_name": policy.name,
        "policy_hash": policy.policy_hash,
        "policy": policy.to_payload(),
        "no_cut_policy_hash": no_cut_policy.policy_hash,
        "no_cut_policy": no_cut_policy.to_payload(),
        "config_path": str(policy_config_path.relative_to(ROOT)),
        "config_sha256": sha256_file(policy_config_path),
        "no_cut_config_path": str(no_cut_config_path.relative_to(ROOT)),
        "no_cut_config_sha256": no_cut_sha,
        "frozen_control_id": baseline_manifest["freeze_id"],
        "frozen_baseline_manifest_path": str(baseline_manifest_path.relative_to(ROOT)),
        "frozen_baseline_manifest_sha256": sha256_file(baseline_manifest_path),
        "native_module_path": str(module_path.relative_to(ROOT)),
        "native_module_sha256": sha256_file(module_path),
        "native_inprocess_engine_hash": spprc_engine_build_hash(
            "native_rcspp_inprocess"
        ),
        "native_host_engine_hash": spprc_engine_build_hash("native_rcspp_host"),
        "native_build_info": dict(lunar_spprc_native.build_info()),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "dependencies_sha256": stable_payload_hash(dependencies),
        "dependencies": dependencies,
        "screening_evidence_role": "candidate_selection_only_not_promotion",
        "promotion_status": "FROZEN_NOT_RUN",
        "production_default": "no_cut",
        "default_switch_authorized": False,
    }
    atomic_write_json(output_path, manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def candidate_bundle_files() -> tuple[Path, ...]:
    files: set[Path] = set()
    for base, suffixes in (
        (ROOT / "src/lunar_ice_bpc", {".py"}),
        (ROOT / "native/lunar_spprc", {".cpp", ".cc", ".c", ".hpp", ".h", ".cmake", ".txt"}),
        (ROOT / "tests", {".py", ".cpp", ".hpp"}),
    ):
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in suffixes and "__pycache__" not in path.parts:
                files.add(path.resolve())
    for relative in (
        "scripts/freeze_live_sri_candidate.py",
        "scripts/run_live_sri_paired_promotion.py",
        "scripts/run_live_sri_readiness.py",
        "scripts/run_lunar_ice_native_spprc_acceptance.py",
        "scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py",
        "scripts/run_lunar_ice_b4_2_cold_exact.py",
        "configs/native_live_sri_p0_pilot_v1.yaml",
        "configs/native_live_sri_p1_pilot_v1.yaml",
        "configs/native_live_sri_p2_pilot_v1.yaml",
        "configs/native_no_cut_50_100_bounded_regression_v1.yaml",
    ):
        path = (ROOT / relative).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        files.add(path)
    return tuple(sorted(files, key=lambda path: str(path.relative_to(ROOT))))


def git_status_for_bundle(files: tuple[Path, ...]) -> str:
    relative = [str(path.relative_to(ROOT)) for path in files]
    completed = subprocess.run(
        ["git", "status", "--short", "--", *relative],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.rstrip()


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_payload_hash(payload: object) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())
