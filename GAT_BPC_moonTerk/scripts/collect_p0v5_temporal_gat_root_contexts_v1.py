#!/usr/bin/env python3
"""Collect fresh root snapshots, screen boundary reach, and freeze contexts."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.p0v5_temporal_gat_common import (  # noqa: E402
    load_frozen_config,
    mark_terminal_negative,
    update_state,
)

SNAPSHOT_ENV = "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR"
SNAPSHOT_CAP_ENV = "LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE"
SNAPSHOT_GLOBAL_CAP_ENV = "LUNAR_ICE_P0V5_QG2_SNAPSHOT_GLOBAL_STORAGE_CAP"
SNAPSHOT_SCALE_CAP_ENV = "LUNAR_ICE_P0V5_QG2_SNAPSHOT_PER_SCALE_STORAGE_CAP"
REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"


class ContextCorrectnessRedline(RuntimeError):
    pass


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _mem_available_gb():
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if line.startswith("MemAvailable:"):
            return float(line.split()[1]) / (1024.0 * 1024.0)
    raise RuntimeError("MemAvailable is unavailable")


def _environment(config, snapshot_dir):
    value = dict(os.environ)
    for key in tuple(value):
        if (
            key.startswith("LUNAR_ICE_P0V5_")
            or key.startswith("LUNAR_ICE_PROOF_TAIL_GAT")
            or key.startswith("LUNAR_ICE_GAT_")
            or key == "LUNAR_ICE_PRODUCTION_POLICY_REGISTRY"
        ):
            value.pop(key, None)
    if snapshot_dir is not None:
        value[SNAPSHOT_ENV] = str(snapshot_dir)
        # Selection is based on the earliest three requests that *reach* the
        # scale boundary.  Preserve every available pre-action root fallback
        # snapshot up to the writer's audited hard caps so a non-reaching
        # early request cannot hide a later eligible one.
        value[SNAPSHOT_CAP_ENV] = "50"
        value[SNAPSHOT_GLOBAL_CAP_ENV] = "450"
        value[SNAPSHOT_SCALE_CAP_ENV] = "225"
    value["PYTHONPATH"] = os.pathsep.join((
        str((ROOT / config["native_build_dir"]).resolve()), str(ROOT / "src"),
    ))
    return value


def _collect_instance(config, row, snapshot_dir, output):
    if output.exists() or snapshot_dir.exists():
        raise SystemExit(
            "partial root context collection requires audit:"
            f"{row['instance_content_hash']}"
        )
    command = [
        sys.executable,
        str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
        "--config", str((ROOT / config["selected_exact_config"]).resolve()),
        "--scales", str(row["scale"]), "--instance",
        str((ROOT / row["path"]).resolve()), "--limit", "1",
        "--output-dir", str(output), "--no-resume",
        "--route-opportunity-collection-only-root-pool",
        "--route-opportunity-collection-root-pool-time-cap-sec",
        str(config["execution"][f"scale{row['scale']}_task_cap_sec"]),
        "--effective-memory-cap-gb",
        str(config["execution"]["effective_native_memory_limit_gb"]),
    ]
    completed = subprocess.run(
        command, cwd=ROOT, env=_environment(config, snapshot_dir), check=False
    )
    if completed.returncode not in {0, 1}:
        raise SystemExit(f"root context collection failed:{row['instance_content_hash']}")
    output.mkdir(parents=True, exist_ok=True)
    (output / "collection.marker.json").write_text(json.dumps({
        "instance_hash": row["instance_content_hash"],
        "returncode": completed.returncode,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _snapshot_rows(corpus, snapshot_dir):
    by_hash = {
        row["instance_content_hash"]: row
        for row in corpus["rows"]
        if str(row["partition"]) in {"train", "calibration"}
    }
    output = []
    # Each acceptance process writes below an instance-isolated storage root;
    # recursive discovery keeps the writer's global/per-scale safety caps from
    # biasing later corpus instances while retaining the same snapshot schema.
    for path in sorted(snapshot_dir.rglob("scale*/*/*.json")):
        payload = _load(path)
        instance_hash = str(payload.get("instance_content_hash") or "")
        if instance_hash not in by_hash:
            raise SystemExit("snapshot is outside frozen fresh corpus")
        if str(payload.get("pricing_lifecycle_scope")) != "root_cg":
            raise SystemExit("non-root snapshot leaked into temporal corpus")
        if (
            not bool(payload.get("proof_tail_fallback_context"))
            or str(payload.get("base_proof_queue_policy_id")) != "Q0"
            or str(payload.get("pricing_mode")) != "exact_proof"
            or str(payload.get("objective_mode")) != "official"
            or bool(payload.get("mutates_p0"))
        ):
            raise SystemExit("snapshot is not an exact P0V4 literal-Q0 fallback")
        if bool(payload.get("labels_dropped")):
            raise ContextCorrectnessRedline(
                "snapshot source reported label drop"
            )
        output.append({
            "instance_hash": instance_hash,
            "scale": int(by_hash[instance_hash]["scale"]),
            "partition": by_hash[instance_hash]["partition"],
            "instance_path": str((ROOT / by_hash[instance_hash]["path"]).resolve()),
            "instance_file_sha256": str(by_hash[instance_hash]["file_sha256"]),
            "snapshot_path": str(path.resolve()), "snapshot_sha256": _sha(path),
            "state_hash": str(payload["state_hash"]),
            "root_request_ordinal": int(payload.get("round") or 0),
            "engine_hash": str(payload.get("engine_hash") or ""),
            "config_hash": str(payload.get("config_hash") or ""),
        })
    return output


def _eligibility(config, row, output):
    staging = output.with_suffix(output.suffix + ".partial")
    if staging.exists():
        raise SystemExit(f"partial eligibility replay requires audit:{staging}")
    boundary = int(config["boundary_by_scale"][str(row["scale"])])
    observation_boundaries = [
        value for value in (4096, 8192, 16384) if value <= boundary
    ]
    command = [
        sys.executable, str(REPLAY), "--instance", row["instance_path"],
        "--snapshot", row["snapshot_path"], "--output", str(staging),
        # Boundary eligibility is measured on literal Q0.  No candidate K or
        # CONTINUE/REVERT outcome exists when contexts are frozen.
        "--policy", "QPF0", "--frontier-probe-boundary",
        str(boundary), "--frontier-observation-boundaries",
        *(str(value) for value in observation_boundaries),
        "--wall-time-limit-sec",
        str(config["execution"][f"scale{row['scale']}_task_cap_sec"]),
        "--memory-limit-gb",
        str(config["execution"]["effective_native_memory_limit_gb"]),
    ]
    completed = subprocess.run(
        command, cwd=ROOT, env=_environment(config, None),
        check=False,
    )
    if completed.returncode or not staging.is_file():
        raise SystemExit(f"boundary eligibility replay failed:{row['state_hash']}")
    _load(staging)
    os.replace(staging, output)


def _freeze(config, corpus, snapshot_dir, eligibility_dir):
    snapshots = _snapshot_rows(corpus, snapshot_dir)
    eligible = []
    census = []
    for row in snapshots:
        path = eligibility_dir / f"{row['state_hash']}.json"
        if not path.is_file():
            raise SystemExit("eligibility matrix is incomplete")
        raw = _load(path)
        if (
            str(raw.get("instance_content_hash") or "")
                != row["instance_hash"]
            or str(raw.get("source_state_hash") or "") != row["state_hash"]
            or str(raw.get("policy") or "") != "QPF0"
        ):
            raise SystemExit("eligibility replay/context binding drift")
        frontier = dict(
            dict(raw.get("proof_telemetry") or {}).get(
                "proof_queue_frontier_probe"
            ) or {}
        )
        if bool(raw.get("labels_dropped")):
            raise ContextCorrectnessRedline(
                "eligibility replay label-drop redline"
            )
        reached = bool(frontier.get("reached"))
        graph_built = bool(frontier.get("graph_built"))
        evidence = {
            **row,
            "eligibility_path": str(path.resolve()),
            "eligibility_sha256": _sha(path),
            "eligibility_policy": "QPF0",
            "eligibility_boundary": int(
                config["boundary_by_scale"][str(row["scale"])]
            ),
            "boundary_reached": reached,
            "boundary_graph_built": graph_built,
        }
        census.append(evidence)
        # Eligibility is only "literal Q0 reached the frozen boundary".
        if reached and graph_built:
            eligible.append(evidence)
    grouped = defaultdict(list)
    for row in eligible:
        grouped[(row["scale"], row["instance_hash"])].append(row)
    output = []
    for key, rows in sorted(grouped.items()):
        ordered = sorted(rows, key=lambda row: (
            row["root_request_ordinal"], row["state_hash"]
        ))[:int(config["maximum_contexts_per_instance"])]
        for rank, row in enumerate(ordered):
            output.append({
                **row,
                "context_id": f"temporal_s{row['scale']}_{row['instance_hash']}_{rank}",
                "selection_rank_within_instance": rank,
                "selection_policy": (
                    "earliest_boundary_reaching_p0v4_fallback_request_v1"
                ),
                "selection_used_queue_performance_outcome": False,
                "pricing_lifecycle_scope": "root_cg",
                "p0v4_fallback_only": True,
            })
    return {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_root_contexts.v1",
        "status": "FROZEN_BEFORE_CONTINUE_REVERT_OUTCOMES",
        "selection_policy": "earliest_three_boundary_reaching_v1",
        "snapshot_census_count": len(census),
        "snapshot_census": census,
        "context_count": len(output), "rows": output,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("collect", "eligibility", "freeze"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--task-limit", type=int)
    args = parser.parse_args()
    try:
        config, config_freeze = load_frozen_config(
            args.config, run_root=args.run_root
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    corpus = _load(args.corpus)
    root = args.run_root.resolve()
    source_path = root / "source.freeze.json"
    if not source_path.is_file():
        raise SystemExit("Temporal-GAT source freeze is missing")
    source = _load(source_path)
    if (
        Path(str(source.get("corpus_manifest") or "")).resolve()
            != args.corpus.resolve()
        or str(source.get("corpus_manifest_sha256") or "") != _sha(args.corpus)
        or corpus.get("status") != "FROZEN_BEFORE_QUEUE_OUTCOMES"
    ):
        raise SystemExit("fresh corpus/source freeze binding drift")
    for row in corpus.get("rows") or ():
        path = ROOT / str(row["path"])
        if not path.is_file() or _sha(path) != str(row["file_sha256"]):
            raise SystemExit("frozen fresh corpus instance drift")
    snapshot_dir = root / "root_snapshots"
    eligibility_dir = root / "boundary_eligibility"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    eligibility_dir.mkdir(parents=True, exist_ok=True)
    completed = 0
    if args.mode == "collect":
        # Development and sealed-final instances must remain untouched until
        # their own E2E stages.  Context supervision is train/calibration only.
        for row in corpus["rows"]:
            if str(row["partition"]) not in {"train", "calibration"}:
                continue
            marker = root / "root_collection" / row["instance_content_hash"]
            if (marker / "collection.marker.json").is_file():
                continue
            if args.task_limit is not None and completed >= args.task_limit:
                update_state(
                    root, stage="CONTEXT_COLLECTION", status="IN_PROGRESS",
                    detail={"context_collection_tasks_launched": completed},
                )
                return 0
            if _mem_available_gb() < float(
                config["execution"]["memavailable_reserve_gb"]
            ):
                raise SystemExit("MemAvailable reserve would be violated")
            _collect_instance(
                config,
                row,
                snapshot_dir / row["instance_content_hash"],
                marker,
            )
            completed += 1
        update_state(
            root, stage="CONTEXT_ELIGIBILITY", status="READY",
            detail={"context_collection_tasks_launched": completed},
        )
        return 0
    try:
        snapshots = _snapshot_rows(corpus, snapshot_dir)
    except ContextCorrectnessRedline as exc:
        mark_terminal_negative(
            root, stage="CONTEXT_ELIGIBILITY",
            reason="CONTEXT_COLLECTION_CORRECTNESS_REDLINE",
            detail={"error": str(exc)},
        )
        raise SystemExit(str(exc)) from exc
    if args.mode == "eligibility":
        for row in snapshots:
            target = eligibility_dir / f"{row['state_hash']}.json"
            if target.is_file():
                continue
            if args.task_limit is not None and completed >= args.task_limit:
                update_state(
                    root, stage="CONTEXT_ELIGIBILITY", status="IN_PROGRESS",
                    detail={"context_eligibility_tasks_launched": completed},
                )
                return 0
            if _mem_available_gb() < float(
                config["execution"]["memavailable_reserve_gb"]
            ):
                raise SystemExit("MemAvailable reserve would be violated")
            _eligibility(config, row, target)
            completed += 1
        update_state(
            root, stage="CONTEXT_FREEZE", status="READY",
            detail={"context_eligibility_tasks_launched": completed},
        )
        return 0
    try:
        payload = _freeze(config, corpus, snapshot_dir, eligibility_dir)
    except ContextCorrectnessRedline as exc:
        mark_terminal_negative(
            root, stage="CONTEXT_FREEZE",
            reason="CONTEXT_COLLECTION_CORRECTNESS_REDLINE",
            detail={"error": str(exc)},
        )
        raise SystemExit(str(exc)) from exc
    payload["source_config_freeze_sha256"] = _sha(config_freeze)
    payload["source_freeze_sha256"] = _sha(source_path)
    payload["source_corpus_sha256"] = _sha(args.corpus)
    target = root / "contexts.freeze.json"
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") != encoded:
        raise SystemExit("immutable context freeze drift")
    if not target.exists():
        target.write_text(encoded, encoding="utf-8")
    update_state(
        root, stage="TRIAL_SCHEDULE_FREEZE", status="READY",
        detail={"frozen_context_count": int(payload["context_count"])},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
