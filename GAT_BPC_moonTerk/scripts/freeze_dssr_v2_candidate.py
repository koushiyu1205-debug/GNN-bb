#!/usr/bin/env python3
"""Freeze a development-qualified DSSR V2 candidate for locked testing."""

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


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (  # noqa: E402
    spprc_engine_build_hash,
)
from lunar_ice_bpc.exact.core.cuts import stable_payload_hash  # noqa: E402


CANDIDATE_ID = "DSSR_V2_DETERMINISTIC_CANDIDATE"
POLICY_VERSION = "multi_sortie_counterexample_pressure_refinement_v2"
DEFAULT_BUILD = ROOT / "build" / "native-spprc-dssr-v2"
DEFAULT_CONFIG = ROOT / "configs" / "dssr_v2_selected.yaml"
DEFAULT_GRID = (
    ROOT
    / "runs"
    / "dssr_v2_development_20260729"
    / "sentinel_grid"
    / "summary.json"
)
DEFAULT_DEVELOPMENT = (
    ROOT
    / "runs"
    / "dssr_v2_development_20260729"
    / "paired_development"
    / "summary.json"
)
DEFAULT_SPLIT = (
    ROOT
    / "data"
    / "manifests"
    / "dssr_v2_validation_split_manifest.json"
)
DEFAULT_OUTPUT = (
    ROOT / "runs" / "frozen_dssr_v2_locked_test_candidate"
)
SOURCE_FILES = (
    "scripts/run_dssr_v2_snapshot_grid.py",
    "scripts/replay_large_exact_pricer_tail.py",
    "scripts/run_dssr_v2_paired_validation.py",
    "scripts/materialize_dssr_v2_selected_config.py",
    "scripts/freeze_dssr_v2_candidate.py",
    "scripts/generate_dssr_v2_validation_instances.py",
    "scripts/run_lunar_ice_native_spprc_acceptance.py",
    "tests/native/test_native_spprc_backend.py",
    "tests/test_dssr_v2_validation.py",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--native-build", type=Path, default=DEFAULT_BUILD)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--grid-summary", type=Path, default=DEFAULT_GRID)
    parser.add_argument(
        "--development-summary",
        type=Path,
        default=DEFAULT_DEVELOPMENT,
    )
    parser.add_argument("--split-manifest", type=Path, default=DEFAULT_SPLIT)
    args = parser.parse_args()

    output = args.output_dir.resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"refusing to overwrite nonempty freeze: {output}")
    config = args.config.resolve()
    grid_path = args.grid_summary.resolve()
    development_path = args.development_summary.resolve()
    split_path = args.split_manifest.resolve()
    build = args.native_build.resolve()
    for path in (config, grid_path, development_path, split_path):
        if not path.is_file():
            raise SystemExit(f"required freeze input missing: {path}")
    modules = sorted(build.glob("lunar_spprc_native*.so"))
    if len(modules) != 1:
        raise SystemExit("isolated native build must contain one module")
    native_module = modules[0]

    grid = _read_json(grid_path)
    development = _read_json(development_path)
    split = _read_json(split_path)
    development_preflight_path = development_path.parent / "preflight.json"
    development_preflight = (
        _read_json(development_preflight_path)
        if development_preflight_path.is_file()
        else {}
    )
    issues = _freeze_issues(
        grid=grid,
        development=development,
        development_preflight=development_preflight,
        split=split,
        config=config,
        native_module=native_module,
        grid_path=grid_path,
        split_path=split_path,
    )
    if issues:
        raise SystemExit("DSSR V2 freeze refused: " + ",".join(issues))

    output.mkdir(parents=True, exist_ok=True)
    test_results = _run_tests(build=build, output=output)
    _write_json(output / "test_results.json", test_results)
    if not test_results["all_passed"]:
        raise SystemExit("DSSR V2 freeze refused: tests failed")

    frozen_native_dir = output / "native"
    frozen_native_dir.mkdir(parents=True, exist_ok=False)
    frozen_native = frozen_native_dir / native_module.name
    shutil.copy2(native_module, frozen_native)
    frozen_config = output / "frozen_config.yaml"
    frozen_grid = output / "sentinel_grid_summary.json"
    frozen_development = output / "development_summary.json"
    frozen_split = output / "split_manifest.json"
    for source, target in (
        (config, frozen_config),
        (grid_path, frozen_grid),
        (development_path, frozen_development),
        (split_path, frozen_split),
    ):
        shutil.copy2(source, target)

    if str(build) not in sys.path:
        sys.path.insert(0, str(build))
    import lunar_spprc_native

    source_bundle = _source_bundle(
        extra=(config, grid_path, development_path, split_path)
    )
    engine_backends = (
        "native_rcspp_inprocess",
        "native_rcspp_host",
        "native_rcspp_dssr_v2_inprocess",
        "native_rcspp_dssr_v2_host",
    )
    manifest = {
        "schema_version": "lunar_ice_bpc.dssr_v2_candidate_freeze.v1",
        "candidate_id": CANDIDATE_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_git_commit": _git_commit(),
        "historical_control_id": (
            "FROZEN_NATIVE_LIVE_SRI_P0_NO_TASK_WAIT_BASELINE_V3"
        ),
        "failed_predecessor_archived": "DSSR_V1",
        "production_default_unchanged": "no_cut",
        "promotion_status": "LOCKED_TEST_AUTHORIZED",
        "algorithm": {
            "policy_version": POLICY_VERSION,
            "negative_batch_enabled": True,
            "pressure_refinement_enabled": True,
            "same_algorithm_all_scales": True,
            "tree_max_rounds_unchanged": 16,
            "gat_enabled": False,
            "critical_task_gat_enabled": False,
            "learned_p0_dssr_selector_enabled": False,
        },
        "frozen_config": _artifact(frozen_config),
        "frozen_native_module": _artifact(frozen_native),
        "sentinel_grid_summary": _artifact(frozen_grid),
        "development_summary": _artifact(frozen_development),
        "split_manifest": _artifact(frozen_split),
        "native_build_info": dict(lunar_spprc_native.build_info()),
        "engine_hashes": {
            backend: spprc_engine_build_hash(backend)
            for backend in engine_backends
        },
        "source_bundle": source_bundle,
        "content_bundle_hash": stable_payload_hash(source_bundle),
        "test_results": _artifact(output / "test_results.json"),
        "locked_test_started": False,
        "locked_test_single_use": True,
        "formal_promotion_authorized": False,
        "gat_oracle_authorized": False,
    }
    _write_json(output / "candidate_freeze_manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _freeze_issues(
    *,
    grid: dict,
    development: dict,
    development_preflight: dict,
    split: dict,
    config: Path,
    native_module: Path,
    grid_path: Path,
    split_path: Path,
) -> list[str]:
    issues: list[str] = []
    if not grid.get("freeze_allowed"):
        issues.append("sentinel_grid_not_passed")
    if (
        development.get("schema_version")
        != "lunar_ice_bpc.dssr_v2_paired_validation.v1"
        or development.get("partition") != "development"
        or not development.get("freeze_allowed")
    ):
        issues.append("development_gate_not_passed")
    if split.get("status") != "LOCKED":
        issues.append("split_manifest_not_locked")
    if split.get("audit", {}).get("locked_test_used_for_selection"):
        issues.append("locked_test_leak")
    expected = {
        "config_sha256": sha256_file(config),
        "native_module_sha256": sha256_file(native_module),
        "grid_summary_sha256": sha256_file(grid_path),
        "split_manifest_sha256": sha256_file(split_path),
    }
    for field, value in expected.items():
        if development_preflight.get(field) != value:
            issues.append(f"development_{field}_mismatch")
    return sorted(set(issues))


def _run_tests(*, build: Path, output: Path) -> dict:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(ROOT / "src"), str(build))
    )
    commands = (
        ["ctest", "--test-dir", str(build), "--output-on-failure"],
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/native/test_native_spprc_backend.py",
            "tests/test_dssr_v2_validation.py",
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
        stdout = output / f"test_{index:02d}_stdout.txt"
        stderr = output / f"test_{index:02d}_stderr.txt"
        stdout.write_text(completed.stdout, encoding="utf-8")
        stderr.write_text(completed.stderr, encoding="utf-8")
        rows.append(
            {
                "command": command,
                "returncode": completed.returncode,
                "stdout_sha256": sha256_file(stdout),
                "stderr_sha256": sha256_file(stderr),
            }
        )
    return {
        "all_passed": all(row["returncode"] == 0 for row in rows),
        "commands": rows,
    }


def _source_bundle(*, extra: tuple[Path, ...]) -> list[dict]:
    files = {
        *(ROOT / path for path in SOURCE_FILES),
        *extra,
        *(
            path
            for path in (ROOT / "src" / "lunar_ice_bpc").rglob("*.py")
            if "__pycache__" not in path.parts
        ),
        *(
            path
            for path in (ROOT / "native" / "lunar_spprc").rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix not in {".pyc", ".pyo"}
        ),
    }
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing)
    return [
        {
            "path": str(path.resolve().relative_to(ROOT)),
            "sha256": sha256_file(path),
        }
        for path in sorted(files, key=lambda value: str(value))
    ]


def _artifact(path: Path) -> dict:
    return {
        "path": str(path.resolve().relative_to(ROOT)),
        "sha256": sha256_file(path),
    }


def _git_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())
