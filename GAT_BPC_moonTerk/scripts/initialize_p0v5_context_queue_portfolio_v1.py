#!/usr/bin/env python3
"""Create the independent immutable P0V5 portfolio experiment chain."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_runtime import (  # noqa: E402
    PORTFOLIO_RUNTIME_POLICY_V1,
    context_queue_portfolio_runtime_implementation_hash,
)


CONFIG = ROOT / "configs/experiments/p0v5_context_queue_portfolio_v1.json"
SEED = 61635
SOURCE_PATHS = (
    "native/lunar_spprc/include/lunar_spprc/native_pricer.hpp",
    "native/lunar_spprc/src/native_pricer.cpp",
    "native/lunar_spprc/src/pybind_module.cpp",
    "native/lunar_spprc/tests/test_native_pricer.cpp",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/base.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/native_rcspp.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/backends/native_bidirectional_hybrid.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/final_judge.py",
    "src/lunar_ice_bpc/exact/bpc/pricing/labeling_pricer.py",
    "src/lunar_ice_bpc/exact/bpc/solver/pricing_tail_solver.py",
    "src/lunar_ice_bpc/guidance/context_queue_portfolio_v1.py",
    "src/lunar_ice_bpc/guidance/context_queue_portfolio_runtime.py",
    "src/lunar_ice_bpc/guidance/context_queue_portfolio_gates.py",
    "src/lunar_ice_bpc/guidance/context_queue_portfolio_freeze.py",
    "src/lunar_ice_bpc/guidance/context_queue_portfolio_snapshot.py",
    "src/lunar_ice_bpc/guidance/qgr1_supervision.py",
    "scripts/initialize_p0v5_context_queue_portfolio_v1.py",
    "scripts/freeze_p0v5_context_queue_portfolio_corpus.py",
    "scripts/collect_p0v5_context_queue_portfolio_contexts.py",
    "scripts/finalize_p0v5_context_queue_portfolio_stage.py",
    "scripts/build_p0v5_context_queue_portfolio_training_dataset.py",
    "scripts/train_p0v5_context_queue_portfolio_selector.py",
    "scripts/replay_p0v5_qg2_label_state_snapshot.py",
    "scripts/predict_p0v5_qgr1_potential.py",
    "scripts/train_p0v5_qgr1_label_gat.py",
    "scripts/run_p0v5_context_queue_portfolio_matrix.py",
    "scripts/freeze_p0v5_qgr1_execution.py",
    "scripts/merge_p0v5_context_queue_portfolio_rows.py",
    "scripts/analyze_p0v5_context_queue_portfolio_outcomes.py",
    "scripts/predict_p0v5_context_queue_portfolio_action.py",
    "scripts/freeze_p0v5_context_queue_portfolio_heldout.py",
    "scripts/run_p0v5_context_queue_portfolio_full_bpc.py",
    "scripts/analyze_p0v5_qg2_paired_acceptance.py",
    "scripts/build_p0v5_qg2_fallback_snapshot_index.py",
    "scripts/run_lunar_ice_native_spprc_acceptance.py",
    "src/lunar_ice_bpc/runners/native_spprc_acceptance.py",
    "configs/experiments/p0v5_context_queue_portfolio_v1.json",
    "tests/test_p0v5_context_queue_portfolio_v1.py",
    "plan/GAT/P0V5_CONTEXT_QUEUE_PORTFOLIO_V1_IMPLEMENTATION_20260807_ZH.md",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--run-root", type=Path)
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("schema_version") != (
        "lunar_ice_bpc.p0v5_context_queue_portfolio_experiment_config.v1"
    ):
        raise SystemExit("experiment config schema mismatch")
    run_root = (
        args.run_root.resolve()
        if args.run_root else (ROOT / str(config["run_root"])).resolve()
    )
    run_root.mkdir(parents=True, exist_ok=True)

    split = _instance_split(config)
    formal_hashes = _formal_hashes(config)
    development_hashes = {row["instance_content_hash"] for row in split["rows"]}
    overlap = sorted(development_hashes.intersection(formal_hashes))
    if overlap:
        _terminal(run_root, "INSTANCE_OR_FEATURE_LEAKAGE", {"overlap": overlap})
        raise SystemExit("development/formal content-hash overlap")

    native_binary = _single_native_binary(config)
    sys.path.insert(0, str(native_binary.parent))
    from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (
        spprc_engine_build_hash,
    )
    exact_engine_backend_id = (
        "native_rcspp_bidirectional_root_partial_hybrid_v3"
    )
    exact_engine_hash = spprc_engine_build_hash(exact_engine_backend_id)
    selected_config = (ROOT / str(config["selected_exact_config"])).resolve()
    if not selected_config.is_file():
        raise SystemExit(f"selected exact config missing: {selected_config}")
    missing_sources = [path for path in SOURCE_PATHS if not (ROOT / path).is_file()]
    if missing_sources:
        raise SystemExit("implementation sources missing: " + ",".join(missing_sources))

    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        text=True, stdout=subprocess.PIPE,
    ).stdout.strip()
    source_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_source_freeze.v1",
        "status": "FROZEN_BEFORE_ANY_PORTFOLIO_OUTCOME",
        "git_commit": git_commit,
        "worktree_may_be_dirty": True,
        "source_sha256": {
            path: _sha256(ROOT / path) for path in SOURCE_PATHS
        },
        "selected_exact_config": str(selected_config),
        "selected_exact_config_sha256": _sha256(selected_config),
        "native_binary": str(native_binary),
        "native_binary_sha256": _sha256(native_binary),
        "exact_engine_backend_id": exact_engine_backend_id,
        "exact_engine_hash": exact_engine_hash,
        "native_source_hash": _combined_hash(
            ROOT / path for path in SOURCE_PATHS if path.startswith("native/")
        ),
        "exact_execution_source_sha256": {
            str(path.relative_to(ROOT)): _sha256(path)
            for path in _exact_execution_sources()
        },
        "portfolio_runtime_policy_id": PORTFOLIO_RUNTIME_POLICY_V1,
        "portfolio_runtime_implementation_hash": (
            context_queue_portfolio_runtime_implementation_hash()
        ),
    }
    config_freeze = {
        **config,
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_config_freeze.v1",
        "source_config": str(config_path),
        "source_config_sha256": _sha256(config_path),
        "status": "FROZEN_BEFORE_ANY_PORTFOLIO_OUTCOME",
    }
    execution_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_execution_freeze.v1",
        "status": "FROZEN_BEFORE_ANY_PORTFOLIO_OUTCOME",
        "action_universe": config["action_universe"],
        "qgr1_bucket_width": config["qgr1_bucket_width"],
        "execution": config["execution"],
        "threshold_grid": config["threshold_grid"],
        "selector_seeds": config["selector_training"]["seeds"],
        "selector_tiebreak_order": config["selector_tiebreak_order"],
        "historical_inputs": config["historical_inputs"],
        "formal_outcomes_may_not_reenter_training": True,
    }
    acceptance_freeze = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_acceptance_freeze.v1",
        "status": "FROZEN_BEFORE_ANY_PORTFOLIO_OUTCOME",
        "context_coverage": config["context_coverage"],
        "arm_admission": config["arm_admission"],
        "qgr1_smoke_gate": config["qgr1_smoke_gate"],
        "portfolio_headroom_gate": config["portfolio_headroom_gate"],
        "heldout_gate": config["heldout_gate"],
        "development_e2e_gate": config["development_e2e_gate"],
        "formal_gate": config["formal_gate"],
        "stop_reasons": config["stop_reasons"],
    }
    split.update({
        "formal_benchmark_hash_count": len(formal_hashes),
        "formal_benchmark_hash_blacklist": sorted(formal_hashes),
        "development_formal_overlap": [],
        "status": "FROZEN_BEFORE_ANY_PORTFOLIO_OUTCOME",
    })
    artifacts = {
        "config.freeze.json": config_freeze,
        "source.freeze.json": source_freeze,
        "instance_split.freeze.json": split,
        "execution.freeze.json": execution_freeze,
        "acceptance.freeze.json": acceptance_freeze,
    }
    for name, payload in artifacts.items():
        _write_once(run_root / name, payload)
    registry = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_freeze_registry.v1",
        "immutable": True,
        "historical_registry_modified": False,
        "artifact_sha256": {
            name: _sha256(run_root / name) for name in sorted(artifacts)
        },
    }
    _write_once(run_root / "freeze.registry.json", registry)
    state = {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_state.v1",
        "experiment_id": config["experiment_id"],
        "current_stage": "CONTEXT_COLLECTION",
        "status": "READY",
        "terminal": False,
        "terminal_decision": None,
        "development_only": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    }
    _write_once(run_root / "state.initial.json", state)
    _write_once(run_root / "state.json", state)
    print(json.dumps({
        "run_root": str(run_root),
        "freeze_registry": str(run_root / "freeze.registry.json"),
        "development_instance_count": len(split["rows"]),
        "formal_hash_blacklist_count": len(formal_hashes),
        "overlap_count": 0,
        "status": "READY_FOR_CONTEXT_COLLECTION",
    }, ensure_ascii=False, indent=2))
    return 0


def _instance_split(config: dict) -> dict:
    root = (ROOT / str(config["development_instance_root"])).resolve()
    counts = dict(config["instance_split_per_scale"])
    ordered_partitions = ("train", "calibration", "selector_heldout", "development_e2e")
    rows = []
    assignments = {}
    counts_by_scale = {}
    for scale in (30, 50):
        paths = sorted((root / f"lunar_ice_sp50_{scale:03d}").glob(
            "instance_*_logical_graph.json"
        ))
        if len(paths) != 20:
            raise SystemExit(f"scale{scale} development instances != 20")
        candidates = []
        for path in paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            data = load_lunar_ice_data(payload)
            content_hash = str(data.instance_content_hash)
            order_key = hashlib.sha256(
                f"{SEED}:{scale}:{content_hash}".encode("utf-8")
            ).hexdigest()
            candidates.append((order_key, content_hash, data.instance_id, path))
        candidates.sort()
        cursor = 0
        scale_counts = {}
        for partition in ordered_partitions:
            count = int(counts[partition])
            for _key, content_hash, instance_id, path in candidates[cursor:cursor + count]:
                if content_hash in assignments:
                    raise SystemExit("development content hash is duplicated")
                assignments[content_hash] = partition
                rows.append({
                    "instance_content_hash": content_hash,
                    "instance_id": instance_id,
                    "instance_path": str(path.resolve()),
                    "partition": partition,
                    "scale": scale,
                })
            cursor += count
            scale_counts[partition] = count
        if cursor != 20:
            raise SystemExit("instance split counts do not sum to 20")
        counts_by_scale[str(scale)] = scale_counts
    return {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_instance_split.v1",
        "seed": SEED,
        "unit": "instance_content_hash",
        "frozen_before_outcomes": True,
        "partition_counts_by_scale": counts_by_scale,
        "assignments": dict(sorted(assignments.items())),
        "rows": sorted(rows, key=lambda row: (row["scale"], row["partition"], row["instance_content_hash"])),
    }


def _formal_hashes(config: dict) -> set[str]:
    root = (ROOT / str(config["formal_instance_root"])).resolve()
    hashes = set()
    for scale in (5, 10, 20, 30, 50):
        paths = sorted((root / f"lunar_ice_sp50_{scale:03d}").glob(
            "instance_*_logical_graph.json"
        ))
        if len(paths) < 20:
            raise SystemExit(f"formal scale{scale} instances < 20")
        for path in paths[:20]:
            data = load_lunar_ice_data(json.loads(path.read_text(encoding="utf-8")))
            hashes.add(str(data.instance_content_hash))
    return hashes


def _single_native_binary(config: dict) -> Path:
    build_dir = (ROOT / str(config["native_build_dir"])).resolve()
    paths = sorted(build_dir.glob("lunar_spprc_native*.so"))
    if len(paths) != 1:
        raise SystemExit(f"expected one portfolio Native binary, found {len(paths)}")
    return paths[0]


def _exact_execution_sources() -> tuple[Path, ...]:
    values = {
        *tuple((ROOT / "src/lunar_ice_bpc/exact").rglob("*.py")),
        ROOT / "src/lunar_ice_bpc/runners/native_spprc_acceptance.py",
        ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py",
        ROOT / "scripts/run_lunar_ice_b4_2_cold_exact.py",
        ROOT / "scripts/run_lunar_ice_compact_pricing_staged_resume.py",
        ROOT / "scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py",
    }
    missing = [path for path in values if not path.is_file()]
    if missing:
        raise SystemExit("exact execution source missing:" + ",".join(map(str, missing)))
    return tuple(sorted(values))


def _terminal(run_root: Path, reason: str, detail: dict) -> None:
    _write_once(run_root / "terminal_decision.json", {
        "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_terminal.v1",
        "decision": "FAIL",
        "reason": reason,
        "detail": detail,
        "deployment_authorized": False,
        "production_switch_authorized": False,
    })


def _write_once(path: Path, payload: object) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise SystemExit(f"immutable artifact drift: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _combined_hash(paths) -> str:
    digest = hashlib.sha256()
    for path in sorted(Path(value) for value in paths):
        digest.update(str(path.relative_to(ROOT)).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
