#!/usr/bin/env python3
"""Collect a clean P0V5 QG2 corpus from independent real-map instances.

The controller is intentionally sequential at the Native-pricing level.  It
freezes the completed development corpus before the first snapshot, strips all
learning guidance from child environments, runs every instance once with a
bounded root-pool collection window, and validates the resulting P0V5 snapshot
index.  It never reads or trains on the formal benchmark instances.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

RUN_ROOT = ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
CORPUS_ROOT = ROOT / "data/p0v5_qg2_realmap_development_v4"
CORPUS_MANIFEST = CORPUS_ROOT / "manifest.json"
CONFIG = ROOT / "runs/p0v4_v5_exact_gat_binding_20260731/selected_exact_v5.yaml"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
SNAPSHOT_DIR = RUN_ROOT / "fallback_snapshots_realmap_v4"
INDEX = RUN_ROOT / "realmap_v4_snapshot_index.json"
FREEZE = RUN_ROOT / "realmap_v4_collection_freeze.json"
STATE = RUN_ROOT / "realmap_v4_collection_state.json"
SPLIT = RUN_ROOT / "realmap_v4_instance_split.json"
ORACLE_PREFLIGHT = RUN_ROOT / "realmap_v4_oracle_preflight.json"
ORACLE_EXECUTION_FREEZE = (
    RUN_ROOT / "realmap_v4_oracle_execution_freeze.json"
)
BACKEND_ID = "native_rcspp_bidirectional_root_partial_hybrid_v3"
REQUIRED_ACTION_HASHES = {
    "30": "9dcedb7b74c0a9c20a3a64484067b87300b9267e8bd450fcfff74d2a8c7406ca",
    "50": "b2f9eab6bd01d12a0f4319342550733ddb0510e559d5e6a6abc119765d2203e2",
}
SCHEDULED_ORACLE_CONTEXTS = 120
SCHEDULED_ORACLE_CONTEXTS_PER_SCALE = 60
GUIDANCE_ENV_KEYS = (
    "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
    "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
    "LUNAR_ICE_PROOF_QUEUE_GAT_MANIFEST",
    "LUNAR_ICE_PROOF_QUEUE_GAT_EVALUATION_MODE",
    "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_MANIFEST",
    "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_EVALUATION_MODE",
    "LUNAR_ICE_GAT_DEPLOYMENT_MANIFEST",
    "LUNAR_ICE_GAT_GUIDANCE_MODE",
    "LUNAR_ICE_GAT_TRAINING_ROWS_DIR",
    "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST",
    "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_EVALUATION_MODE",
)
EXACT_EXECUTION_SOURCES = (
    ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py",
    ROOT / "scripts/run_lunar_ice_b4_2_cold_exact.py",
    ROOT / "scripts/run_lunar_ice_compact_pricing_staged_resume.py",
    ROOT / "scripts/run_lunar_ice_b4_1_true_dual_proof_tail.py",
    ROOT / "src/lunar_ice_bpc/runners/native_spprc_acceptance.py",
    *tuple(sorted((ROOT / "src/lunar_ice_bpc/exact").rglob("*.py"))),
)
QG2_V4_LEARNING_SOURCES = (
    ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py",
    ROOT / "scripts/fit_p0v5_qo2_leaked_label_state_oracle.py",
    ROOT / "scripts/run_p0v5_qg2_bounded_oracle.py",
    ROOT / "scripts/authorize_p0v5_qg2_realmap_v4_training.py",
    ROOT / "scripts/evaluate_p0v5_qg2_training_only_gate_v2.py",
    ROOT / "scripts/collect_p0v5_qg2_realmap_v4_matched_arms.py",
    ROOT / "scripts/train_p0v5_qg2_v3_rankers.py",
    ROOT / "scripts/analyze_p0v5_qg2_v3_gat_attribution.py",
    ROOT / "scripts/calibrate_p0v5_qg2_v3_gat_force_on.py",
    ROOT / "scripts/predict_p0v5_qg2_v3_potential.py",
    ROOT / "scripts/train_p0v5_qg2_v3_gat_arm_selector.py",
    ROOT / "scripts/analyze_p0v5_qg2_v3_selector_attribution.py",
    ROOT / "scripts/evaluate_p0v5_qg2_v3_gat_selector_fresh.py",
    ROOT / "scripts/freeze_p0v5_qg2_v3_selector_candidate.py",
    ROOT / "scripts/analyze_p0v5_qg2_realmap_v4_acceptance.py",
    ROOT / "scripts/analyze_p0v5_qg2_paired_acceptance.py",
    ROOT / "scripts/run_p0v5_qg2_realmap_v4_controls_after_gat.py",
    ROOT / "scripts/run_p0v5_qg2_realmap_v4_development_e2e.py",
    ROOT / "scripts/run_p0v5_qg2_realmap_v4_formal_full20.py",
    ROOT / "scripts/audit_p0v5_qg2_realmap_v4_completion.py",
    ROOT / "scripts/finalize_p0v5_qg2_realmap_v4_candidate.py",
    ROOT / "scripts/run_p0v5_qg2_realmap_v4_gat_first.py",
    ROOT / "src/lunar_ice_bpc/guidance/models.py",
    ROOT / "src/lunar_ice_bpc/guidance/tensorization.py",
    ROOT / "src/lunar_ice_bpc/guidance/qg2_context_arm_selector.py",
    ROOT / "src/lunar_ice_bpc/guidance/qg2_runtime_oracle_authority.py",
    ROOT / "src/lunar_ice_bpc/guidance/qg2_admission_supervision.py",
    ROOT / "src/lunar_ice_bpc/guidance/qg2_admission_supervision_v3.py",
    ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_gat.py",
    ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_gat_v3.py",
    ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_runtime.py",
    ROOT / "src/lunar_ice_bpc/guidance/qg2_unified_arm_selector_v3.py",
    ROOT / "src/lunar_ice_bpc/guidance/qg2_v3_selector_runtime.py",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-pool-cap-sec", type=float, default=300.0)
    parser.add_argument("--snapshot-max-per-instance", type=int, default=15)
    args = parser.parse_args()
    _assert_corpus_complete()
    _assert_fresh_namespace()
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    _freeze_collection(
        root_pool_cap_sec=float(args.root_pool_cap_sec),
        snapshot_max_per_instance=int(args.snapshot_max_per_instance),
    )
    for scale in (30, 50):
        instances = tuple(sorted(
            (CORPUS_ROOT / f"lunar_ice_sp50_{scale:03d}").glob(
                "instance_*_logical_graph.json"
            )
        ))
        _state("RUNNING_COLLECTION", scale=scale, instance_count=len(instances))
        _run_acceptance(
            scale=scale,
            instances=instances,
            root_pool_cap_sec=float(args.root_pool_cap_sec),
            snapshot_max_per_instance=int(args.snapshot_max_per_instance),
        )
        _build_index()
    index = _build_index()
    coverage = dict(index.get("coverage") or {})
    ready = bool(index.get("oracle_preflight_ready")) and all(
        int((coverage.get(str(scale)) or {}).get("instance_count") or 0) >= 10
        for scale in (30, 50)
    )
    preflight = _run_oracle_preflight() if ready else 2
    if preflight == 0:
        _freeze_oracle_execution()
    _state(
        "ORACLE_PREFLIGHT_READY" if preflight == 0 else "COLLECTION_INCOMPLETE",
        coverage=coverage,
        preflight_exit_code=preflight,
    )
    return 0 if preflight == 0 else 2


def _assert_corpus_complete() -> None:
    if not CORPUS_MANIFEST.is_file():
        raise SystemExit("real-map development manifest is missing")
    payload = _load(CORPUS_MANIFEST)
    # The shared real-map manifest retains all six formal scales in
    # ``formal_scales`` even when this run requests only 30 and 50, so its
    # top-level status remains ``incomplete``.  Validate the requested corpus
    # directly instead of weakening the check or requiring unrelated scales.
    manifest_counts = {
        scale: sum(
            int(row.get("scale") or 0) == scale
            and str(row.get("status") or "accepted") == "accepted"
            for row in payload.get("instances") or ()
        )
        for scale in (30, 50)
    }
    if manifest_counts != {30: 20, 50: 20}:
        raise SystemExit(
            f"real-map development manifest counts are incomplete: {manifest_counts}"
        )
    formal_hashes = {
        _instance_content_hash(path)
        for scale in (30, 50)
        for path in (ROOT / f"data/instances/lunar_ice_sp50_{scale:03d}").glob(
            "instance_*_logical_graph.json"
        )
    }
    development_by_scale = {
        scale: tuple(sorted(
            (CORPUS_ROOT / f"lunar_ice_sp50_{scale:03d}").glob(
                "instance_*_logical_graph.json"
            )
        ))
        for scale in (30, 50)
    }
    if any(len(rows) != 20 for rows in development_by_scale.values()):
        raise SystemExit(
            "expected 20 real-map development instances per scale: "
            + repr({scale: len(rows) for scale, rows in development_by_scale.items()})
        )
    development = [
        path for rows in development_by_scale.values() for path in rows
    ]
    overlap = formal_hashes & {_instance_content_hash(path) for path in development}
    if overlap:
        raise SystemExit("development corpus overlaps formal benchmark hashes")


def _assert_fresh_namespace() -> None:
    existing = [
        path for path in (
            SNAPSHOT_DIR, INDEX, FREEZE, STATE, SPLIT,
            ORACLE_PREFLIGHT, ORACLE_EXECUTION_FREEZE,
        )
        if path.exists()
    ]
    existing.extend(RUN_ROOT.glob("snapshot_collection_realmap_v4_scale*"))
    if existing:
        raise SystemExit(
            "real-map V4 collection namespace is not empty: "
            + ",".join(str(path) for path in existing)
        )


def _freeze_collection(*, root_pool_cap_sec: float, snapshot_max_per_instance: int) -> None:
    sys.path.insert(0, str(BUILD))
    from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import spprc_engine_build_hash
    from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
        qg2_runtime_implementation_hash,
    )

    extensions = tuple(sorted(BUILD.glob("lunar_spprc_native*.so")))
    if len(extensions) != 1:
        raise SystemExit("real-map V4 collection requires one frozen Native extension")
    split = _freeze_instance_split()
    runtime = ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_runtime.py"
    model = ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_gat.py"
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_clean_collection_freeze.v3",
        "status": "FROZEN_BEFORE_REALMAP_V4_COLLECTION",
        "development_only": True,
        "deployable": False,
        "collection_policy": "independent_realmap_all20_each_scale_sequential_native",
        "formal_benchmark_instances_used": False,
        "candidate_instance_count_per_scale": 20,
        "maximum_oracle_contexts_per_scale": 150,
        "scheduled_oracle_contexts": SCHEDULED_ORACLE_CONTEXTS,
        "scheduled_oracle_contexts_per_scale": (
            SCHEDULED_ORACLE_CONTEXTS_PER_SCALE
        ),
        "root_pool_cap_sec": float(root_pool_cap_sec),
        "snapshot_max_per_instance": int(snapshot_max_per_instance),
        "snapshot_dir": str(SNAPSHOT_DIR),
        "source_backend_id": BACKEND_ID,
        "source_engine_hash": spprc_engine_build_hash(BACKEND_ID),
        "qg2_runtime_implementation_hash": qg2_runtime_implementation_hash(),
        "qg2_runtime_source_sha256": _sha256(runtime),
        "qg2_model_source_sha256": _sha256(model),
        "native_extension_sha256": _sha256(extensions[0]),
        "selected_exact_config": str(CONFIG),
        "selected_exact_config_sha256": _sha256(CONFIG),
        "development_corpus_manifest": str(CORPUS_MANIFEST),
        "development_corpus_manifest_sha256": _sha256(CORPUS_MANIFEST),
        "instance_split": str(SPLIT),
        "instance_split_sha256": _sha256(SPLIT),
        "instance_split_counts": split["partition_counts_by_scale"],
        "exact_execution_source_sha256": {
            str(path.relative_to(ROOT)): _sha256(path)
            for path in EXACT_EXECUTION_SOURCES
        },
        "required_exact_action_policy_hashes_by_scale": REQUIRED_ACTION_HASHES,
        "mutation_rule": "do_not_modify_exact_runtime_native_config_or_corpus_until_collection_finishes",
    }
    _write(FREEZE, payload)


def _freeze_instance_split() -> dict:
    """Freeze 12/4/4 per scale before any action outcome exists."""

    rows = []
    assignments = {}
    counts = {}
    for scale in (30, 50):
        instances = []
        for path in sorted(
            (CORPUS_ROOT / f"lunar_ice_sp50_{scale:03d}").glob(
                "instance_*_logical_graph.json"
            )
        ):
            payload = _load(path)
            digest = _instance_content_hash(path)
            order_key = hashlib.sha256(
                f"p0v5_qg2_realmap_v4_split:{scale}:{digest}".encode("utf-8")
            ).hexdigest()
            instances.append((order_key, digest, path, str(payload["instance_id"])))
        instances.sort()
        if len(instances) != 20:
            raise SystemExit(f"scale{scale} split requires exactly 20 instances")
        scale_counts = {"train": 0, "calibration": 0, "heldout": 0}
        for index, (_key, digest, path, instance_id) in enumerate(instances):
            partition = (
                "train" if index < 12
                else "calibration" if index < 16
                else "heldout"
            )
            assignments[digest] = partition
            scale_counts[partition] += 1
            rows.append({
                "scale": scale,
                "instance_id": instance_id,
                "instance_content_hash": digest,
                "instance_path": str(path.resolve()),
                "partition": partition,
            })
        counts[str(scale)] = scale_counts
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_realmap_v4_instance_split.v1",
        "frozen_before_matched_outcomes": True,
        "unit": "instance_content_hash",
        "ratio": [60, 20, 20],
        "partition_counts_by_scale": counts,
        "assignments": assignments,
        "rows": sorted(rows, key=lambda row: (
            int(row["scale"]), str(row["instance_content_hash"])
        )),
    }
    _write(SPLIT, payload)
    return payload


def _run_acceptance(
    *,
    scale: int,
    instances: tuple[Path, ...],
    root_pool_cap_sec: float,
    snapshot_max_per_instance: int,
) -> None:
    if len(instances) != 20:
        raise SystemExit(f"scale{scale} corpus must contain 20 instances")
    output = RUN_ROOT / f"snapshot_collection_realmap_v4_scale{scale}"
    command = [
        sys.executable,
        str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
        "--config", str(CONFIG),
        "--scales", str(scale),
    ]
    for path in instances:
        command.extend(("--instance", str(path)))
    command.extend((
        "--limit", str(len(instances)),
        "--output-dir", str(output),
        "--no-resume",
        "--route-opportunity-collection-only-root-pool",
        "--route-opportunity-collection-root-pool-time-cap-sec",
        str(root_pool_cap_sec),
    ))
    env = _environment()
    env["LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE"] = str(
        snapshot_max_per_instance
    )
    env["LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR"] = str(SNAPSHOT_DIR)
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
    if completed.returncode not in {0, 1}:
        raise SystemExit(f"scale{scale} real-map collection failed: {completed.returncode}")


def _build_index() -> dict:
    command = [
        sys.executable,
        str(ROOT / "scripts/build_p0v5_qg2_fallback_snapshot_index.py"),
        "--snapshot-dir", str(SNAPSHOT_DIR),
        "--instance-root", str(CORPUS_ROOT),
        "--output", str(INDEX),
        "--collection-freeze", str(FREEZE),
        "--require-exact-action-policy-hash",
    ]
    completed = subprocess.run(command, cwd=ROOT, env=_environment(), check=False)
    if completed.returncode != 0:
        raise SystemExit("real-map V4 snapshot index validation failed")
    payload = _load(INDEX)
    if int(payload.get("excluded_count") or 0) != 0:
        raise SystemExit("real-map V4 snapshot index contains exclusions")
    return payload


def _run_oracle_preflight() -> int:
    command = [
        sys.executable,
        str(ROOT / "scripts/run_p0v5_qg2_bounded_oracle.py"),
        "--state-index", str(INDEX),
        "--instance-split", str(SPLIT),
        "--output-dir", str(RUN_ROOT / "oracle_realmap_v4"),
        "--output", str(ORACLE_PREFLIGHT),
        "--preflight-only",
    ]
    return subprocess.run(command, cwd=ROOT, env=_environment(), check=False).returncode


def _freeze_oracle_execution() -> None:
    """Bind the real-map index and Oracle implementation before outcomes."""

    from lunar_ice_bpc.guidance.qg2_admission_supervision import (
        QG2_QUEUE_ACTION_SURFACE_V1,
        QG2_SUPERVISION_SCHEMA_V2,
    )
    from lunar_ice_bpc.guidance.qg2_admission_supervision_v3 import (
        QG2_V3_SUPERVISION_SCHEMA,
    )

    collection = _load(FREEZE)
    preflight = _load(ORACLE_PREFLIGHT)
    if str(preflight.get("status") or "") != "PREFLIGHT_ONLY":
        raise SystemExit("real-map V4 Oracle preflight did not pass")
    extension = tuple(sorted(BUILD.glob("lunar_spprc_native*.so")))
    if len(extension) != 1:
        raise SystemExit("real-map V4 Oracle freeze requires one Native extension")
    tree_supplement_files = tuple(
        path for path in (
            ROOT / "scripts/continue_p0v5_qg2_realmap_v4_tree_supplement.py",
            ROOT / "scripts/watch_p0v5_qg2_realmap_v4_tree_then_gat.py",
            RUN_ROOT / "realmap_v4_tree_supplement_freeze.json",
        )
        if path.is_file()
    )
    frozen = (
        *EXACT_EXECUTION_SOURCES,
        ROOT / "scripts/continue_p0v5_qg2_realmap_v4_collection.py",
        *tree_supplement_files,
        *QG2_V4_LEARNING_SOURCES,
        INDEX,
        ORACLE_PREFLIGHT,
        FREEZE,
        SPLIT,
        CONFIG,
        extension[0],
    )
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_oracle_execution_freeze.v2",
        "status": "FROZEN_AFTER_REALMAP_V4_PREFLIGHT_BEFORE_ORACLE_OUTCOMES",
        "development_only": True,
        "deployable": False,
        "collection_id": "p0v5_qg2_realmap_v4_gat_first",
        "oracle_schema": "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5",
        "potential_schema": "lunar_ice_bpc.p0v5_qg2_label_state_potential.v2",
        "supervision_schema_version": QG2_SUPERVISION_SCHEMA_V2,
        "ranker_supervision_schema_version": QG2_V3_SUPERVISION_SCHEMA,
        "queue_action_surface": QG2_QUEUE_ACTION_SURFACE_V1,
        "source_state_index": str(INDEX),
        "source_state_index_sha256": _sha256(INDEX),
        "preflight": str(ORACLE_PREFLIGHT),
        "preflight_sha256": _sha256(ORACLE_PREFLIGHT),
        "preflight_coverage": preflight.get("coverage"),
        "required_exact_action_policy_hashes_by_scale": REQUIRED_ACTION_HASHES,
        "source_exact_engine_hash": str(collection["source_engine_hash"]),
        "native_binary_sha256": _sha256(extension[0]),
        "maximum_oracle_contexts": 300,
        "maximum_oracle_contexts_per_scale": 150,
        "scheduled_oracle_contexts": SCHEDULED_ORACLE_CONTEXTS,
        "scheduled_oracle_contexts_per_scale": (
            SCHEDULED_ORACLE_CONTEXTS_PER_SCALE
        ),
        "oracle_schedule_must_match_exactly": True,
        "scale30_wall_time_limit_sec": 300.0,
        "scale50_wall_time_limit_sec": 600.0,
        "memory_limit_gb": 10.867,
        "blocked_repeats": 3,
        "fixed_bucket_candidates": [1.0e-4, 3.0e-4, 1.0e-3],
        "instance_split": str(SPLIT),
        "instance_split_sha256": _sha256(SPLIT),
        "formal_benchmark_instances_used": False,
        "tree_supplement_used": bool(
            (RUN_ROOT / "realmap_v4_tree_supplement_freeze.json").is_file()
        ),
        "frozen_file_sha256": {
            str(path.relative_to(ROOT)): _sha256(path) for path in frozen
        },
        "training_before_oracle_outcomes": False,
        "inherited_guidance_environment_permitted": False,
    }
    _write(ORACLE_EXECUTION_FREEZE, payload)


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    for key in GUIDANCE_ENV_KEYS:
        env.pop(key, None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{BUILD}"
    return env


def _state(status: str, **extra) -> None:
    _write(STATE, {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_realmap_v4_collection_state.v1",
        "status": str(status),
        **extra,
    })


def _instance_content_hash(path: Path) -> str:
    from lunar_ice_bpc.exact.core.data import load_lunar_ice_data

    return load_lunar_ice_data(_load(path)).instance_content_hash


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
