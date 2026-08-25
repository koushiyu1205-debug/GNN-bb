#!/usr/bin/env python3
"""Freeze the production-v1 research contract after the fresh corpus exists."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.generate_p0v5_temporal_gat_production_corpus_v1 import (  # noqa: E402
    _generation_retry_policy,
    _generation_seed,
    _generation_seed_attempt,
)

DEFAULT_CONFIG = ROOT / "configs/experiments/p0v5_temporal_gat_production_v1.json"
SOURCE_STATIC_PATHS = (
    "native/lunar_spprc/CMakeLists.txt",
    "native/lunar_spprc/include/lunar_spprc/bidirectional_feasibility.hpp",
    "native/lunar_spprc/src/bidirectional_feasibility.cpp",
    "src/lunar_ice_bpc/domain/real_instance.py",
    "src/lunar_ice_bpc/domain/real_maps.py",
    "src/lunar_ice_bpc/exact/bpc/core/column_signature.py",
    "src/lunar_ice_bpc/exact/bpc/guidance/contracts.py",
    "native/lunar_spprc/include/lunar_spprc/native_pricer.hpp",
    "native/lunar_spprc/src/native_pricer.cpp",
    "native/lunar_spprc/src/pybind_module.cpp",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/base.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/native_rcspp.py",
    "src/lunar_ice_bpc/runners/native_spprc_acceptance.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/native_bidirectional_hybrid.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/bidirectional_feasibility.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/final_judge.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/labeling_pricer.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/spprc_pricer.py",
    "src/lunar_ice_bpc/exact/bpc/solver/cut_formulation_solver.py",
    "src/lunar_ice_bpc/exact/bpc/solver/pricing_tail_solver.py",
    "src/lunar_ice_bpc/exact/bpc/solver/root_node_solver.py",
    "src/lunar_ice_bpc/guidance/temporal_frontier_gat_v1.py",
    "src/lunar_ice_bpc/guidance/temporal_frontier_gat_runtime_v1.py",
    "src/lunar_ice_bpc/guidance/frontier_gat_qd1_v7.py",
    "src/lunar_ice_bpc/guidance/counterfactual_prefix_gat_qd1_v8.py",
    "src/lunar_ice_bpc/guidance/proof_queue_label_state_runtime.py",
    "scripts/generate_p0v5_temporal_gat_production_corpus_v1.py",
    "scripts/p0v5_temporal_gat_common.py",
    "scripts/replay_p0v5_qg2_label_state_snapshot.py",
    "scripts/audit_p0v5_counterfactual_native_differential_v8.py",
    "scripts/audit_p0v5_temporal_gat_native_differential_v1.py",
    "scripts/run_lunar_ice_native_spprc_acceptance.py",
    "scripts/run_p0v4_final_acceptance.py",
    "scripts/analyze_p0v5_qg2_paired_acceptance.py",
    "scripts/collect_p0v5_temporal_gat_root_contexts_v1.py",
    "scripts/freeze_p0v5_temporal_gat_trial_schedule_v1.py",
    "scripts/run_p0v5_temporal_gat_trial_schedule_v1.py",
    "scripts/select_p0v5_temporal_gat_trial_k_v1.py",
    "scripts/build_p0v5_temporal_gat_dataset_v1.py",
    "scripts/train_p0v5_temporal_gat_production_v1.py",
    "scripts/verify_p0v5_temporal_gat_portable_v1.py",
    "scripts/run_p0v5_temporal_gat_full_bpc_v1.py",
    "scripts/run_p0v5_temporal_gat_formal_acceptance_v1.py",
    "scripts/run_p0v5_temporal_gat_canary_v1.py",
    "scripts/audit_p0v5_temporal_gat_source_bundle_v1.py",
    "scripts/audit_p0v5_temporal_gat_e2e_v1.py",
    "scripts/finalize_p0v5_temporal_gat_production_v1.py",
    "tests/test_p0v5_temporal_gat_production_v1.py",
    "tests/test_real_map_edge_checkpoint.py",
    "native/lunar_spprc/tests/test_native_pricer.cpp",
    "scripts/check_rcspp_patch_queue.py",
    "scripts/run_lunar_ice_b4_2_cold_exact.py",
)

SOURCE_GLOBS = (
    "src/lunar_ice_bpc/**/*.py",
    "native/lunar_spprc/include/**/*.hpp",
    "native/lunar_spprc/src/**/*.cpp",
    "scripts/*p0v5_temporal_gat*.py",
    "tests/test_p0v5_temporal_gat*.py",
)

PYTHON_CONTRACT_TEST_PATHS = (
    "tests/test_p0v5_temporal_gat_production_v1.py",
    "tests/test_real_map_edge_checkpoint.py",
)
MINIMUM_PYTHON_CONTRACT_TEST_COUNT = 16


def source_inventory_paths() -> tuple[str, ...]:
    paths = set(SOURCE_STATIC_PATHS)
    for pattern in SOURCE_GLOBS:
        paths.update(
            str(path.relative_to(ROOT))
            for path in ROOT.glob(pattern)
            if path.is_file()
        )
    return tuple(sorted(paths))


SOURCE_PATHS = source_inventory_paths()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = _load(config_path)
    run_root = (ROOT / config["run_root"]).resolve()
    if run_root.exists() and any(run_root.iterdir()):
        raise SystemExit("immutable temporal production run root is not empty")
    corpus = (ROOT / config["corpus_root"] / "corpus.freeze.json").resolve()
    if not corpus.is_file():
        raise SystemExit("fresh corpus must be frozen before bootstrap")
    corpus_payload = _load(corpus)
    rows = list(corpus_payload.get("rows") or ())
    expected_rows = len(config["scales"]) * int(config["instances_per_scale"])
    protected_audit = dict(
        corpus_payload.get("protected_history_audit") or {}
    )
    protected_cache = ROOT / str(protected_audit.get("cache_path") or "")
    protected_cache_payload = (
        _load(protected_cache) if protected_cache.is_file() else {}
    )
    protected_paths = sorted({
        path
        for base in (ROOT / "data", ROOT / "runs")
        for path in base.rglob("*logical_graph.json")
        if (ROOT / config["corpus_root"]).resolve() not in path.parents
    })
    protected_inventory = [{
        "path": str(path.relative_to(ROOT)),
        "size": int(path.stat().st_size),
        "mtime_ns": int(path.stat().st_mtime_ns),
    } for path in protected_paths]
    protected_inventory_sha256 = hashlib.sha256(json.dumps(
        protected_inventory, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    protected_hashes = {
        str(row.get("instance_content_hash") or "")
        for row in protected_cache_payload.get("rows") or ()
    }
    if (
        corpus_payload.get("status") != "FROZEN_BEFORE_QUEUE_OUTCOMES"
        or corpus_payload.get("source_config_sha256") != _sha(config_path)
        or corpus_payload.get("driver_source_sha256") != _sha(
            ROOT / "scripts/generate_p0v5_temporal_gat_production_corpus_v1.py"
        )
        or corpus_payload.get("generator_source_sha256")
            != _sha(ROOT / "src/lunar_ice_bpc/domain/real_instance.py")
        or corpus_payload.get("real_map_source_sha256")
            != _sha(ROOT / "src/lunar_ice_bpc/domain/real_maps.py")
        or int(corpus_payload.get("row_count") or -1) != expected_rows
        or len(rows) != expected_rows
        # Zero is the only acceptable overlap count.  Do not use
        # ``value or -1`` here: zero is falsey and would make every valid
        # frozen corpus fail bootstrap.
        or int(corpus_payload.get(
            "official_or_historical_overlap_count", -1
        )) != 0
        or len({str(row.get("instance_content_hash") or "") for row in rows})
            != expected_rows
        or any(not str(row.get("instance_content_hash") or "") for row in rows)
        or not protected_cache.is_file()
        or _sha(protected_cache) != protected_audit.get("cache_sha256")
        or protected_audit.get("inventory_roots") != ["data", "runs"]
        or int(protected_audit.get("file_count") or -1)
            != len(protected_paths)
        or protected_audit.get("inventory_sha256")
            != protected_inventory_sha256
        or protected_cache_payload.get("inventory_sha256")
            != protected_inventory_sha256
        or len(protected_cache_payload.get("rows") or ())
            != len(protected_paths)
        or {
            str(row.get("path") or "")
            for row in protected_cache_payload.get("rows") or ()
        } != {str(row["path"]) for row in protected_inventory}
        or int(protected_audit.get("unique_content_hash_count") or -1)
            != len(protected_hashes)
        or any(
            str(row.get("instance_content_hash") or "") in protected_hashes
            for row in rows
        )
    ):
        raise SystemExit("fresh corpus freeze/generator/history binding drift")
    expected_splits = dict(config["split_counts_by_scale"])
    for scale in map(int, config["scales"]):
        selected_rows = [row for row in rows if int(row.get("scale") or 0) == scale]
        counts = {
            partition: sum(
                str(row.get("partition") or "") == partition
                for row in selected_rows
            )
            for partition in expected_splits
        }
        if len(selected_rows) != int(config["instances_per_scale"]) or counts != {
            key: int(value) for key, value in expected_splits.items()
        }:
            raise SystemExit(f"fresh corpus scale/split drift:scale{scale}")
        for row in selected_rows:
            index = int(row["index"])
            path = ROOT / str(row["path"])
            seed = int(row["seed"])
            try:
                seed_attempt = _generation_seed_attempt(
                    config, scale, index, seed
                )
            except (SystemExit, ValueError) as exc:
                raise SystemExit(
                    "fresh corpus row seed retry binding drift"
                ) from exc
            rejection_audit = (
                ROOT / config["corpus_root"] / "generation_checkpoints"
                / f"scale_{scale:03d}" / f"instance_{index:03d}"
                / "rejected_attempts.audit.json"
            )
            row_audit_path = row.get("generation_rejection_audit_path")
            row_audit_sha256 = row.get(
                "generation_rejection_audit_sha256"
            )
            rejection_binding_ok = (
                int(row.get("seed_attempt", -1)) == seed_attempt
            )
            if seed_attempt > 0:
                rejection_payload = (
                    _load(rejection_audit)
                    if rejection_audit.is_file() else {}
                )
                rejection_binding_ok = rejection_binding_ok and (
                    rejection_audit.is_file()
                    and row_audit_path
                        == str(rejection_audit.relative_to(ROOT))
                    and row_audit_sha256 == _sha(rejection_audit)
                    and rejection_payload.get("retry_policy")
                        == _generation_retry_policy(config)
                    and int(rejection_payload.get(
                        "accepted_attempt", -1
                    )) == seed_attempt
                    and int(rejection_payload.get(
                        "accepted_seed", -1
                    )) == seed
                    and len(rejection_payload.get(
                        "rejected_attempts"
                    ) or ()) == seed_attempt
                )
            else:
                rejection_binding_ok = rejection_binding_ok and (
                    row_audit_path is None
                    and row_audit_sha256 is None
                    and not rejection_audit.exists()
                )
            if (
                seed != _generation_seed(
                    config, scale, index, seed_attempt
                )
                or not rejection_binding_ok
                or not path.is_file()
                or _sha(path) != str(row["file_sha256"])
            ):
                raise SystemExit("fresh corpus row seed/file binding drift")
    selected = (ROOT / config["selected_exact_config"]).resolve()
    if not selected.is_file():
        raise SystemExit("selected exact comparator is missing")
    formal_contract = (ROOT / config["formal_acceptance_contract"]).resolve()
    if not formal_contract.is_file():
        raise SystemExit("formal acceptance contract is missing")
    native_build = (ROOT / config["native_build_dir"]).resolve()
    # Make source/binary freezing fail-safe: an incremental rebuild must
    # complete before any extension or test-executable hash is recorded.
    subprocess.run(
        ["cmake", "--build", str(native_build), "--parallel", "2"],
        cwd=ROOT, check=True,
    )
    binaries = sorted(native_build.glob("lunar_spprc_native*.so"))
    if len(binaries) != 1:
        raise SystemExit("Temporal Native build must contain exactly one extension")
    native_test_binary = native_build / "lunar_spprc_native_tests"
    if not native_test_binary.is_file():
        raise SystemExit("Temporal Native contract-test binary is missing")
    reference_build = (ROOT / config["reference_native_build_dir"]).resolve()
    reference_binaries = sorted(reference_build.glob("lunar_spprc_native*.so"))
    if len(reference_binaries) != 1:
        raise SystemExit("reference Native build must contain exactly one extension")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((
        str(native_build), str(ROOT / "src"),
    ))
    python_contract_collection = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q",
         *PYTHON_CONTRACT_TEST_PATHS],
        cwd=ROOT, env=environment, check=False, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    python_contract_test_count = _pytest_collected_count(
        python_contract_collection.stdout
    )
    if (
        python_contract_collection.returncode
        or python_contract_test_count < MINIMUM_PYTHON_CONTRACT_TEST_COUNT
    ):
        raise SystemExit(
            "Temporal Python contract test collection failed or shrank: "
            + python_contract_collection.stdout[-4000:]
        )
    native_build_info = json.loads(subprocess.run(
        [sys.executable, "-c", (
            "import json,lunar_spprc_native as n;"
            "print(json.dumps(n.build_info(),sort_keys=True))"
        )], cwd=ROOT, env=environment, check=True, text=True,
        stdout=subprocess.PIPE,
    ).stdout)
    required_build_info = dict(config["required_native_build_info"])
    build_info_mismatches = {
        key: {
            "expected": expected,
            "observed": native_build_info.get(key),
        }
        for key, expected in required_build_info.items()
        if native_build_info.get(key) != expected
    }
    if build_info_mismatches:
        raise SystemExit(
            "Temporal Native build does not preserve the frozen P0V4+V5 "
            f"feature contract: {json.dumps(build_info_mismatches, sort_keys=True)}"
        )
    exact_engine_hash = subprocess.run(
        [sys.executable, "-c", (
            "from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import "
            "spprc_engine_build_hash;"
            "from lunar_ice_bpc.exact.bpc.pricing.backends import "
            "NATIVE_BIDIRECTIONAL_ROOT_PARTIAL_HYBRID_BACKEND_ID as B;"
            "print(spprc_engine_build_hash(B))"
        )], cwd=ROOT, env=environment, check=True, text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    run_root.mkdir(parents=True, exist_ok=False)
    source = {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_gat_source_freeze.v1",
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
            text=True, stdout=subprocess.PIPE,
        ).stdout.strip(),
        "worktree_may_be_dirty": True,
        "source_sha256": {name: _sha(ROOT / name) for name in SOURCE_PATHS},
        "source_inventory_contract": {
            "static_paths": list(SOURCE_STATIC_PATHS),
            "globs": list(SOURCE_GLOBS),
            "resolved_paths": list(SOURCE_PATHS),
        },
        "selected_exact_config": str(selected),
        "selected_exact_config_sha256": _sha(selected),
        "formal_acceptance_contract": str(formal_contract),
        "formal_acceptance_contract_sha256": _sha(formal_contract),
        "corpus_manifest": str(corpus),
        "corpus_manifest_sha256": _sha(corpus),
        "protected_history_cache": str(protected_cache.resolve()),
        "protected_history_cache_sha256": _sha(protected_cache),
        "native_build_dir": str(native_build),
        "native_binary": str(binaries[0]),
        "native_binary_sha256": _sha(binaries[0]),
        "native_test_binary": str(native_test_binary),
        "native_test_binary_sha256": _sha(native_test_binary),
        "python_contract_test_paths": list(PYTHON_CONTRACT_TEST_PATHS),
        "python_contract_test_count": python_contract_test_count,
        "python_contract_collection_output_sha256": hashlib.sha256(
            python_contract_collection.stdout.encode("utf-8")
        ).hexdigest(),
        "reference_native_build_dir": str(reference_build),
        "reference_native_binary": str(reference_binaries[0]),
        "reference_native_binary_sha256": _sha(reference_binaries[0]),
        "native_differential_cases": int(config["native_differential_cases"]),
        "native_build_info": native_build_info,
        "required_native_build_info": required_build_info,
        "exact_engine_hash": exact_engine_hash,
    }
    contract = {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_gat_contract.v1",
        "action_scope": "scale30_50_root_cg_p0v4_fallback_only",
        "actions": ["CONTINUE_QD1", "MIGRATE_BACK_TO_Q0"],
        "boundary_by_scale": config["boundary_by_scale"],
        "trial_k_candidates": config["trial_k_candidates"],
        "gat_may_delete_or_prune_labels": False,
        "gat_has_certificate_authority": False,
        "production_default_change_before_all_gates": False,
        "old_outcomes_allowed_for_training": False,
    }
    state = {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_gat_state.v1",
        "experiment_id": config["experiment_id"],
        "current_stage": "CONTEXT_COLLECTION",
        "status": "READY",
        "terminal": False,
        "candidate_trained": False,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    artifacts = {
        "config.freeze.json": config,
        "source.freeze.json": source,
        "research_contract.freeze.json": contract,
        "state.initial.json": state,
    }
    for name, payload in artifacts.items():
        _write_once(run_root / name, payload)
    # state.json is the only mutable stage pointer.  Its immutable initial
    # value is state.initial.json; do not advertise the mutable copy as a
    # permanently hash-frozen bootstrap artifact.
    _write_once(run_root / "state.json", state)
    _write_once(run_root / "bootstrap.freeze.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_gat_bootstrap.v1",
        "immutable": True,
        "artifact_sha256": {name: _sha(run_root / name) for name in artifacts},
    })
    print(json.dumps({"status": "READY_FOR_CONTEXT_COLLECTION",
                      "run_root": str(run_root)}, sort_keys=True))
    return 0


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pytest_collected_count(output: str) -> int:
    match = re.search(r"(\d+) tests? collected", output)
    return int(match.group(1)) if match is not None else 0


def _write_once(path: Path, payload) -> None:
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable artifact drift:{path}")
    if not path.exists():
        path.write_text(encoded, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
