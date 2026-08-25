#!/usr/bin/env python3
"""Supplement a completed root-only QG2 census with natural BPC-tree contexts.

The pilot root collection is never discarded or rerun.  This controller is
allowed to start only after all 20+20 pilot rows have completed and the frozen
preflight has reported insufficient natural fallback coverage.  It then runs
the same independent instances, exact config, engine, and pre-outcome split
through the standard branch-price-and-cut tree.  Snapshot capture remains a
pre-action, diagnostic side effect; it cannot alter a request or certificate.
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
sys.path.insert(0, str(ROOT / "scripts"))

import continue_p0v5_qg2_realmap_v4_collection as pilot


STATE = pilot.RUN_ROOT / "realmap_v4_tree_supplement_state.json"
FREEZE = pilot.RUN_ROOT / "realmap_v4_tree_supplement_freeze.json"
SNAPSHOT_MAX_PER_INSTANCE = 15
REQUIRED_CONTEXTS_PER_SCALE = 20
REQUIRED_INSTANCES_PER_SCALE = 10
REQUIRED_TOTAL_CONTEXTS = 50
REQUIRED_PARTITION_CONTEXTS = {
    "train": 10,
    "calibration": 4,
    "heldout": 4,
}
REQUIRED_PARTITION_INSTANCES = {
    "train": 6,
    "calibration": 2,
    "heldout": 2,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-max-per-instance", type=int, default=15)
    args = parser.parse_args()
    maximum = int(args.snapshot_max_per_instance)
    if maximum != SNAPSHOT_MAX_PER_INSTANCE:
        raise SystemExit(
            "tree supplement snapshot cap is frozen to 15 per instance"
    )
    _assert_pilot_incomplete_and_immutable()
    _assert_fresh_namespace()
    supplement_scales, coverage_audit = _select_supplement_scales()
    _freeze_before_tree_outcomes(
        maximum,
        supplement_scales=supplement_scales,
        coverage_audit=coverage_audit,
    )
    for scale in supplement_scales:
        instances = tuple(sorted(
            (pilot.CORPUS_ROOT / f"lunar_ice_sp50_{scale:03d}").glob(
                "instance_*_logical_graph.json"
            )
        ))
        _state(
            "RUNNING_TREE_SUPPLEMENT",
            scale=scale,
            instance_count=len(instances),
        )
        _run_full_tree_acceptance(
            scale=scale,
            instances=instances,
            snapshot_max_per_instance=maximum,
        )
        pilot._build_index()
    index = pilot._build_index()
    if not bool(index.get("oracle_preflight_ready")):
        _state(
            "TREE_SUPPLEMENT_INSUFFICIENT",
            coverage=index.get("coverage"),
        )
        return 2
    preflight = pilot._run_oracle_preflight()
    if preflight != 0:
        _state(
            "TREE_SUPPLEMENT_PREFLIGHT_FAILED",
            coverage=index.get("coverage"),
            preflight_exit_code=preflight,
        )
        return 2
    pilot._freeze_oracle_execution()
    _state(
        "TREE_SUPPLEMENT_PREFLIGHT_READY",
        coverage=index.get("coverage"),
        preflight_exit_code=preflight,
    )
    pilot._state(
        "ORACLE_PREFLIGHT_READY_AFTER_TREE_SUPPLEMENT",
        coverage=index.get("coverage"),
        preflight_exit_code=preflight,
    )
    return 0


def _assert_pilot_incomplete_and_immutable() -> None:
    if not pilot.FREEZE.is_file() or not pilot.STATE.is_file():
        raise SystemExit("root-only pilot freeze/state is missing")
    state = _load(pilot.STATE)
    if str(state.get("status") or "") != "COLLECTION_INCOMPLETE":
        raise SystemExit(
            "tree supplement requires a completed COLLECTION_INCOMPLETE pilot"
        )
    for scale in (30, 50):
        rows = (
            pilot.RUN_ROOT / f"snapshot_collection_realmap_v4_scale{scale}"
            / f"scale_{scale:03d}" / "b4_2_cold_exact_rows.csv"
        )
        if _csv_data_row_count(rows) != 20:
            raise SystemExit(
                f"tree supplement requires 20 completed scale{scale} pilot rows"
            )
    if pilot.ORACLE_EXECUTION_FREEZE.exists():
        raise SystemExit("Oracle execution was already frozen before supplement")
    frozen = _load(pilot.FREEZE)
    if _sha256(pilot.CONFIG) != str(
        frozen.get("selected_exact_config_sha256") or ""
    ):
        raise SystemExit("selected Exact config drifted after root pilot")
    if _sha256(pilot.CORPUS_MANIFEST) != str(
        frozen.get("development_corpus_manifest_sha256") or ""
    ):
        raise SystemExit("development corpus drifted after root pilot")
    if _sha256(pilot.SPLIT) != str(
        frozen.get("instance_split_sha256") or ""
    ):
        raise SystemExit("pre-outcome instance split drifted after root pilot")
    runtime_source = (
        ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_runtime.py"
    )
    model_source = (
        ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_gat.py"
    )
    if _sha256(runtime_source) != str(
        frozen.get("qg2_runtime_source_sha256") or ""
    ):
        raise SystemExit("QG2 snapshot/runtime source drifted after root pilot")
    if _sha256(model_source) != str(
        frozen.get("qg2_model_source_sha256") or ""
    ):
        raise SystemExit("QG2 feature/model source drifted after root pilot")
    for relative, digest in dict(
        frozen.get("exact_execution_source_sha256") or {}
    ).items():
        if _sha256(ROOT / relative) != str(digest):
            raise SystemExit(f"Exact collection source drifted: {relative}")
    extensions = tuple(sorted(pilot.BUILD.glob("lunar_spprc_native*.so")))
    if len(extensions) != 1 or _sha256(extensions[0]) != str(
        frozen.get("native_extension_sha256") or ""
    ):
        raise SystemExit("Native extension drifted after root pilot")
    index = _load(pilot.INDEX)
    if bool(index.get("oracle_preflight_ready")):
        raise SystemExit("root pilot already passed preflight; supplement forbidden")
    if int(index.get("excluded_count") or 0) != 0:
        raise SystemExit("root pilot index has exclusions")


def _assert_fresh_namespace() -> None:
    existing = [path for path in (STATE, FREEZE) if path.exists()]
    existing.extend(
        pilot.RUN_ROOT.glob("snapshot_collection_realmap_v4_tree_scale*")
    )
    if existing:
        raise SystemExit(
            "tree supplement namespace is not empty: "
            + ",".join(str(path) for path in existing)
        )


def _select_supplement_scales() -> tuple[tuple[int, ...], dict]:
    """Select only structurally deficient scales before tree outcomes.

    Selection uses the frozen root-pilot snapshot coverage and the pre-outcome
    instance split. It never reads an Oracle replay, arm wall time, or learned
    outcome. Every selected scale still runs its complete, predeclared set of
    20 development instances exactly once.
    """

    root_index = _load(pilot.INDEX)
    split = dict(_load(pilot.SPLIT).get("assignments") or {})
    rows = [dict(row) for row in root_index.get("rows") or ()]
    by_scale: dict[str, dict] = {}
    ready_by_scale: dict[int, bool] = {}
    for scale in (30, 50):
        scale_rows = [
            row for row in rows if int(row.get("scale") or 0) == scale
        ]
        partition_context_counts = {
            partition: sum(
                str(split.get(str(row.get("instance_hash") or "")) or "")
                == partition
                for row in scale_rows
            )
            for partition in REQUIRED_PARTITION_CONTEXTS
        }
        partition_instance_counts = {
            partition: len({
                str(row.get("instance_hash") or "")
                for row in scale_rows
                if str(split.get(str(row.get("instance_hash") or "")) or "")
                == partition
            })
            for partition in REQUIRED_PARTITION_INSTANCES
        }
        context_count = len(scale_rows)
        instance_count = len({
            str(row.get("instance_hash") or "") for row in scale_rows
        })
        ready = bool(
            context_count >= REQUIRED_CONTEXTS_PER_SCALE
            and instance_count >= REQUIRED_INSTANCES_PER_SCALE
            and all(
                partition_context_counts[partition] >= required
                for partition, required in REQUIRED_PARTITION_CONTEXTS.items()
            )
            and all(
                partition_instance_counts[partition] >= required
                for partition, required in REQUIRED_PARTITION_INSTANCES.items()
            )
        )
        ready_by_scale[scale] = ready
        by_scale[str(scale)] = {
            "context_count": context_count,
            "instance_count": instance_count,
            "partition_context_counts": partition_context_counts,
            "partition_instance_counts": partition_instance_counts,
            "per_scale_preflight_ready": ready,
        }

    selected = tuple(scale for scale in (30, 50) if not ready_by_scale[scale])
    total_contexts = sum(
        int(row["context_count"]) for row in by_scale.values()
    )
    # The global gate additionally requires 50 contexts. If both scales meet
    # their individual structural gates but the combined pool is still short,
    # supplement exactly one deterministically chosen scale. This choice is
    # made from counts only, before any tree or arm outcome exists.
    if not selected and total_contexts < REQUIRED_TOTAL_CONTEXTS:
        selected = (min(
            (30, 50),
            key=lambda scale: (by_scale[str(scale)]["context_count"], scale),
        ),)
    if not selected:
        raise SystemExit(
            "root pilot is marked incomplete but no structural coverage "
            "deficit requires a tree supplement"
        )
    return selected, {
        "selection_input": "frozen_root_snapshot_index_and_preoutcome_split",
        "outcome_fields_used": [],
        "scale_coverage": by_scale,
        "total_context_count": total_contexts,
        "required_total_context_count": REQUIRED_TOTAL_CONTEXTS,
        "selected_scales": list(selected),
    }


def _freeze_before_tree_outcomes(
    snapshot_max_per_instance: int,
    *,
    supplement_scales: tuple[int, ...],
    coverage_audit: dict,
) -> None:
    root_index = _load(pilot.INDEX)
    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_realmap_v4_tree_supplement_freeze.v1"
        ),
        "status": "FROZEN_BEFORE_TREE_SUPPLEMENT_OUTCOMES",
        "development_only": True,
        "deployable": False,
        "trigger": "completed_root_pilot_failed_snapshot_preflight",
        "selection_policy": (
            "coverage_deficient_scales_all20_standard_bpc_tree_fixed_before_run"
        ),
        "supplement_scales": list(supplement_scales),
        "scale_selection_audit": coverage_audit,
        "scale_selection_uses_arm_or_oracle_outcomes": False,
        "formal_benchmark_instances_used": False,
        "root_pilot_freeze": str(pilot.FREEZE),
        "root_pilot_freeze_sha256": _sha256(pilot.FREEZE),
        "root_pilot_index": str(pilot.INDEX),
        "root_pilot_index_sha256": _sha256(pilot.INDEX),
        "root_pilot_coverage": root_index.get("coverage"),
        "instance_split": str(pilot.SPLIT),
        "instance_split_sha256": _sha256(pilot.SPLIT),
        "candidate_instance_count_per_scale": 20,
        "snapshot_max_per_instance": int(snapshot_max_per_instance),
        "row_limit_sec": 3600.0,
        "same_exact_config_and_engine_as_root_pilot": True,
        "snapshot_capture_can_issue_certificate": False,
        "standard_exact_run_certificate_path_unchanged": True,
        "supplement_source_sha256": _sha256(Path(__file__).resolve()),
    }
    _write(FREEZE, payload)


def _run_full_tree_acceptance(
    *,
    scale: int,
    instances: tuple[Path, ...],
    snapshot_max_per_instance: int,
) -> None:
    if len(instances) != 20:
        raise SystemExit(f"scale{scale} tree supplement requires 20 instances")
    output = (
        pilot.RUN_ROOT / f"snapshot_collection_realmap_v4_tree_scale{scale}"
    )
    command = [
        sys.executable,
        str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
        "--config", str(pilot.CONFIG),
        "--scales", str(scale),
    ]
    for path in instances:
        command.extend(("--instance", str(path)))
    command.extend((
        "--limit", str(len(instances)),
        "--output-dir", str(output),
        "--no-resume",
    ))
    env = pilot._environment()
    env["LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE"] = str(
        snapshot_max_per_instance
    )
    env["LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR"] = str(
        pilot.SNAPSHOT_DIR
    )
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
    if completed.returncode not in {0, 1}:
        raise SystemExit(
            f"scale{scale} tree supplement failed: {completed.returncode}"
        )


def _csv_data_row_count(path: Path) -> int:
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines()
                 if line.strip()]
    except OSError:
        return 0
    return max(0, len(lines) - 1)


def _state(status: str, **extra) -> None:
    _write(STATE, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_realmap_v4_tree_supplement_state.v1"
        ),
        "status": str(status),
        **extra,
    })
    pilot._state(str(status), **extra)


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
