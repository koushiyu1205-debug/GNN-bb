#!/usr/bin/env python3
"""Freeze the tested all-scale DSSR candidate before formal evaluation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (  # noqa: E402
    spprc_engine_build_hash,
)
from lunar_ice_bpc.exact.core.cuts import stable_payload_hash  # noqa: E402


CANDIDATE_ID = "LARGE_EXACT_DSSR_ALL_SCALE_CANDIDATE_V1_20260727"
DEFAULT_OUTPUT = (
    ROOT
    / "runs"
    / "frozen_large_exact_dssr_all_scale_candidate_v1_20260727"
)
DEFAULT_BUILD = ROOT / "build" / "native-spprc-large-exact"
DEFAULT_CONFIG = ROOT / "configs" / "native_live_sri_p0_full120_v1.yaml"
P0_REGISTRY = ROOT / "runs" / "native_bpc_baseline_registry.json"
FORMAL_MANIFEST = (
    ROOT
    / "data"
    / "manifests"
    / "lunar_ice_sp50_real_benchmark_manifest.json"
)
RUNTIME_SCRIPTS = (
    "scripts/run_dssr_all_scale_full100_validation.py",
    "scripts/run_lunar_ice_native_spprc_acceptance.py",
    "scripts/run_lunar_ice_b4_2_cold_exact.py",
    "scripts/run_lunar_ice_compact_pricing_staged_resume.py",
    "scripts/run_lunar_ice_compact_pricing_batch_probe.py",
    "scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--native-build-dir", type=Path, default=DEFAULT_BUILD)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    output = args.output_dir.resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"refusing to overwrite nonempty freeze: {output}")
    output.mkdir(parents=True, exist_ok=True)
    build = args.native_build_dir.resolve()
    config = args.config.resolve()
    native_modules = sorted(build.glob("lunar_spprc_native*.so"))
    if len(native_modules) != 1:
        raise SystemExit(
            f"expected exactly one native module under {build}, "
            f"found {len(native_modules)}"
        )
    native_source = native_modules[0]

    test_results = (
        {"skipped": True, "all_passed": False, "commands": []}
        if args.skip_tests
        else run_tests(build, output)
    )
    if not test_results["all_passed"]:
        atomic_write_json(output / "test_results.json", test_results)
        raise SystemExit("candidate tests did not all pass; freeze refused")
    atomic_write_json(output / "test_results.json", test_results)

    frozen_native_dir = output / "native"
    frozen_native_dir.mkdir(parents=True, exist_ok=False)
    frozen_native = frozen_native_dir / native_source.name
    shutil.copy2(native_source, frozen_native)
    frozen_config = output / "frozen_config.yaml"
    shutil.copy2(config, frozen_config)

    if str(build) not in sys.path:
        sys.path.insert(0, str(build))
    import lunar_spprc_native

    source_rows = collect_source_rows(config)
    manifest = {
        "schema_version": "lunar_ice_bpc.large_exact_dssr_candidate_freeze.v1",
        "candidate_id": CANDIDATE_ID,
        "created_at_utc": utc_now(),
        "base_git_commit": git_commit(),
        "historical_control_id": (
            "FROZEN_NATIVE_LIVE_SRI_P0_NO_TASK_WAIT_BASELINE_V3"
        ),
        "production_default_unchanged": "no_cut",
        "algorithm": {
            "exact_pricer": "DSSR_COUNTEREXAMPLE_REFINEMENT",
            "dssr_policy_version": (
                "multi_sortie_counterexample_refinement_v1"
            ),
            "applies_to_scales": [5, 10, 20, 30, 50],
            "same_algorithm_all_scales": True,
            "backend_by_scale": {
                "5": "native_rcspp_dssr_inprocess",
                "10": "native_rcspp_dssr_inprocess",
                "20": "native_rcspp_dssr_inprocess",
                "30": "native_rcspp_dssr_inprocess",
                "50": "native_rcspp_dssr_host",
            },
            "negative_harvest_preserves_p0": True,
            "proof_and_certificate_semantics_unchanged": True,
        },
        "config_path": str(config.relative_to(ROOT)),
        "config_sha256": sha256_file(config),
        "frozen_config": str(frozen_config.relative_to(ROOT)),
        "frozen_config_sha256": sha256_file(frozen_config),
        "native_build_source": str(native_source.relative_to(ROOT)),
        "frozen_native_module": str(frozen_native.relative_to(ROOT)),
        "native_module_sha256": sha256_file(frozen_native),
        "native_build_info": dict(lunar_spprc_native.build_info()),
        "engine_hashes": {
            backend: spprc_engine_build_hash(backend)
            for backend in (
                "native_rcspp_dssr_inprocess",
                "native_rcspp_dssr_host",
            )
        },
        "source_bundle": source_rows,
        "content_bundle_hash": stable_payload_hash(source_rows),
        "test_results": {
            "path": str((output / "test_results.json").relative_to(ROOT)),
            "sha256": sha256_file(output / "test_results.json"),
            "all_passed": True,
        },
        "formal_instance_manifest": {
            "path": str(FORMAL_MANIFEST.relative_to(ROOT)),
            "sha256": sha256_file(FORMAL_MANIFEST),
        },
        "p0_registry": {
            "path": str(P0_REGISTRY.relative_to(ROOT)),
            "sha256": sha256_file(P0_REGISTRY),
        },
        "formal_evaluation_started": False,
        "promotion_status": "CANDIDATE_ONLY",
    }
    manifest_path = output / "candidate_freeze_manifest.json"
    atomic_write_json(manifest_path, manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def collect_source_rows(config: Path) -> list[dict[str, str]]:
    files: set[Path] = set()
    files.update(
        path
        for path in (ROOT / "src" / "lunar_ice_bpc").rglob("*.py")
        if "__pycache__" not in path.parts
    )
    files.update(
        path
        for path in (ROOT / "native" / "lunar_spprc").rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    )
    files.update(ROOT / relative for relative in RUNTIME_SCRIPTS)
    files.update(
        {
            config,
            ROOT / "pyproject.toml",
        }
    )
    missing = [path for path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing)
    return [
        {
            "path": str(path.resolve().relative_to(ROOT)),
            "sha256": sha256_file(path),
        }
        for path in sorted(files, key=lambda value: str(value))
    ]


def run_tests(build: Path, output: Path) -> dict:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(ROOT / "src"), str(build))
    )
    commands = (
        [
            "ctest",
            "--test-dir",
            str(build),
            "--output-on-failure",
        ],
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/native/test_native_spprc_backend.py",
        ],
    )
    rows = []
    for index, command in enumerate(commands, start=1):
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        stdout_path = output / f"test_{index:02d}_stdout.txt"
        stderr_path = output / f"test_{index:02d}_stderr.txt"
        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        rows.append(
            {
                "command": command,
                "returncode": int(completed.returncode),
                "stdout": str(stdout_path.relative_to(ROOT)),
                "stdout_sha256": sha256_file(stdout_path),
                "stderr": str(stderr_path.relative_to(ROOT)),
                "stderr_sha256": sha256_file(stderr_path),
            }
        )
    return {
        "skipped": False,
        "all_passed": all(row["returncode"] == 0 for row in rows),
        "commands": rows,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def atomic_write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
