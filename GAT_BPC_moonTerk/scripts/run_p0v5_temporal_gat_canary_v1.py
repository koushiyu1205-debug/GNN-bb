#!/usr/bin/env python3
"""Execute the immutable pre-activation Temporal-GAT canary matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_REGISTRY = ROOT / "runs/production_policy_registry_v2.json"
sys.path.insert(0, str(ROOT))

from scripts.p0v5_temporal_gat_common import (  # noqa: E402
    load_frozen_config, mark_terminal_negative,
)
from scripts.run_p0v5_temporal_gat_full_bpc_v1 import (  # noqa: E402
    _load,
    _mem_available_gb,
    _parse_one,
    _run_one,
    _sha,
    _write_once,
)


def _canonical_hash(payload) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")).hexdigest()


def _mark_registry_canary_negative(candidate: dict, audit_path: Path) -> None:
    if not PRODUCTION_REGISTRY.is_file():
        raise SystemExit("canary candidate registry is missing")
    registry = _load(PRODUCTION_REGISTRY)
    matches = [
        row for row in registry.get("candidates") or ()
        if row.get("candidate_id") == candidate.get("candidate_id")
    ]
    if len(matches) != 1 or matches[0].get("status") != "AWAITING_CANARY":
        raise SystemExit("canary registry candidate binding drift")
    matches[0].update({
        "status": "TERMINATED_NEGATIVE_CANARY",
        "canary_audit_path": str(audit_path.resolve()),
        "canary_audit_sha256": _sha(audit_path),
    })
    temporary = PRODUCTION_REGISTRY.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(registry, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, PRODUCTION_REGISTRY)


def _synthetic_manifests(run_root: Path, candidate: dict):
    manifest_path = Path(candidate["runtime_manifest"]).resolve()
    if _sha(manifest_path) != str(candidate["runtime_manifest_sha256"]):
        raise SystemExit("canary candidate runtime manifest hash drift")
    manifest = _load(manifest_path)
    bundle_path = Path(candidate["bundle"]).resolve()
    if _sha(bundle_path) != str(candidate["bundle_sha256"]):
        raise SystemExit("canary candidate bundle hash drift")

    synthetic = run_root / "canary" / "synthetic"
    bad_hash = dict(manifest)
    bad_hash["portable_bundle_path"] = str(bundle_path)
    bad_hash["portable_bundle_file_sha256"] = "0" * 64
    bad_hash_path = synthetic / "runtime_manifest.bad_bundle_hash.json"
    _write_once(bad_hash_path, bad_hash)

    ood_bundle = _load(bundle_path)
    for group in dict(ood_bundle["normalization"]).values():
        width = len(group["minimum"])
        group["minimum"] = [1.0e100] * width
        group["maximum"] = [1.0e100] * width
    unsigned = dict(ood_bundle)
    unsigned.pop("bundle_sha256", None)
    ood_bundle["bundle_sha256"] = _canonical_hash(unsigned)
    ood_bundle_path = synthetic / "temporal_frontier_gat_bundle.ood.json"
    _write_once(ood_bundle_path, ood_bundle)
    ood_manifest = dict(manifest)
    ood_manifest["portable_bundle_path"] = str(ood_bundle_path)
    ood_manifest["portable_bundle_file_sha256"] = _sha(ood_bundle_path)
    ood_manifest_path = synthetic / "runtime_manifest.ood.json"
    _write_once(ood_manifest_path, ood_manifest)
    return manifest_path, bad_hash_path, ood_manifest_path


def _tasks(freeze, manifests):
    normal, bad_hash, ood = manifests
    instances = dict(freeze["fixed_instances_by_scale"])
    definitions = (
        ("q0_30", 30, "Q0", None, ""),
        ("q0_50", 50, "Q0", None, ""),
        ("model_30", 30, "MODEL", normal, ""),
        ("model_50", 50, "MODEL", normal, ""),
        ("force_continue_30", 30, "FORCE_CONTINUE", normal, "CONTINUE_QD1"),
        ("force_revert_50", 50, "FORCE_REVERT", normal, "MIGRATE_BACK_TO_Q0"),
        ("bundle_hash_mismatch_30", 30, "BUNDLE_HASH_MISMATCH", bad_hash, ""),
        ("ood_fail_closed_50", 50, "OOD_FAIL_CLOSED", ood, ""),
    )
    output = []
    for task_id, scale, arm, manifest, force in definitions:
        row = dict(instances[str(scale)])
        path = Path(row["instance_path"])
        if not path.is_file() or _sha(path) != row["instance_file_sha256"]:
            raise SystemExit("canary instance hash drift")
        output.append({
            "task_id": task_id,
            "scale": scale,
            "instance_hash": row["instance_hash"],
            "instance_path": str(path),
            "arm": arm,
            "partition": "activation_canary",
            "repeat": 0,
            "manifest": str(manifest) if manifest else "",
            "force_action": force,
            "fresh_process": True,
        })
    return output


def _audit(candidate, freeze, rows):
    by_id = {row["task_id"]: row for row in rows}
    failures = []
    if set(by_id) != {
        "q0_30", "q0_50", "model_30", "model_50",
        "force_continue_30", "force_revert_50",
        "bundle_hash_mismatch_30", "ood_fail_closed_50",
    }:
        failures.append("canary_task_coverage")
    for row in rows:
        if row["status"] != "COMPLETE" or row["resource_censor"]:
            failures.append(f"incomplete:{row['task_id']}")
        if row["correctness_redlines"]:
            failures.append(f"redline:{row['task_id']}")
    for scale in (30, 50):
        scale_rows = [row for row in rows if int(row["scale"]) == scale]
        signatures = {row["exact_semantics_signature"] for row in scale_rows}
        objectives = [float(row["objective"]) for row in scale_rows
                      if row.get("objective") is not None]
        if len(signatures) != 1:
            failures.append(f"scale{scale}:exact_semantics")
        if len(objectives) != len(scale_rows) or max(objectives) - min(
            objectives
        ) > 2.0e-6:
            failures.append(f"scale{scale}:objective")

    for task_id in ("model_30", "model_50"):
        row = by_id.get(task_id, {})
        if "temporal_bundle_attached" not in row.get("runtime_reasons", ()):
            failures.append(f"{task_id}:bundle_load")
        if not row.get("inference_ms_values"):
            failures.append(f"{task_id}:model_not_called")
        if (
            int(row.get("runtime_calls") or 0) < 1
            or float(row.get("graph_wall_seconds") or 0.0) <= 0.0
            or float(row.get("trial_wall_seconds") or 0.0) <= 0.0
            or float(row.get("peak_rss_gb") or 0.0) <= 0.0
        ):
            failures.append(f"{task_id}:monitoring_fields_incomplete")
    if int(by_id.get("force_continue_30", {}).get(
        "selected_action_counts", {}
    ).get("CONTINUE_QD1", 0)) < 1:
        failures.append("scale30_force_continue_path")
    if int(by_id.get("force_revert_50", {}).get(
        "selected_action_counts", {}
    ).get("MIGRATE_BACK_TO_Q0", 0)) < 1:
        failures.append("scale50_force_revert_path")
    mismatch = by_id.get("bundle_hash_mismatch_30", {})
    if not any(str(value).startswith("temporal_fail_closed:ValueError")
               for value in mismatch.get("runtime_reasons", ())):
        failures.append("bundle_hash_mismatch_not_fail_closed")
    if mismatch.get("selected_action_counts"):
        failures.append("bundle_hash_mismatch_started_trial")
    ood = by_id.get("ood_fail_closed_50", {})
    if "temporal_frontier_ood" not in ood.get("fail_closed_reasons", ()):
        failures.append("ood_not_fail_closed")
    if int(ood.get("selected_action_counts", {}).get(
        "MIGRATE_BACK_TO_Q0", 0
    )) < 1:
        failures.append("ood_not_migrated_back_to_q0")

    return {
        "schema_version": "lunar_ice_bpc.temporal_gat_canary_audit.v1",
        "decision": "FAIL" if failures else "PASS",
        "candidate_id": candidate["candidate_id"],
        "runtime_manifest_sha256": candidate["runtime_manifest_sha256"],
        "canary_execution_freeze_sha256": _sha(freeze["_path"]),
        "fixed_instances_by_scale": freeze["fixed_instances_by_scale"],
        "failures": sorted(set(failures)),
        "rows": rows,
        "production_default_changed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--task-limit", type=int)
    args = parser.parse_args()
    try:
        config, _ = load_frozen_config(args.config, run_root=args.run_root)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    run_root = args.run_root.resolve()
    candidate_path = run_root / "production_candidate.manifest.json"
    freeze_path = run_root / "canary.execution.freeze.json"
    candidate = _load(candidate_path)
    freeze = _load(freeze_path)
    freeze["_path"] = freeze_path
    if freeze.get("candidate_id") != candidate.get("candidate_id") or str(
        freeze.get("runtime_manifest_sha256")
    ) != str(candidate.get("runtime_manifest_sha256")):
        raise SystemExit("canary execution/candidate binding mismatch")
    manifests = _synthetic_manifests(run_root, candidate)
    tasks = _tasks(freeze, manifests)
    raw = run_root / "canary" / "raw"
    launched = 0
    for task in tasks:
        row_path = raw / task["task_id"] / "canonical_row.json"
        if row_path.is_file():
            continue
        if args.task_limit is not None and launched >= args.task_limit:
            break
        if _mem_available_gb() < float(
            config["execution"]["memavailable_reserve_gb"]
        ):
            raise SystemExit("MemAvailable reserve would be violated")
        manifest = Path(task["manifest"]) if task["manifest"] else None
        _run_one(task, row_path.parent, config, manifest)
        _write_once(row_path, _parse_one(row_path.parent, task))
        launched += 1
    missing = [task["task_id"] for task in tasks if not (
        raw / task["task_id"] / "canonical_row.json"
    ).is_file()]
    if missing:
        print(json.dumps({"status": "PARTIAL", "remaining": missing}))
        return 0
    rows = [_load(raw / task["task_id"] / "canonical_row.json")
            for task in tasks]
    payload = _audit(candidate, freeze, rows)
    audit_path = run_root / "canary" / "canary.audit.json"
    _write_once(audit_path, payload)
    if payload["decision"] != "PASS":
        _mark_registry_canary_negative(candidate, audit_path)
        mark_terminal_negative(
            run_root, stage="ACTIVATION_CANARY",
            reason="ACTIVATION_CANARY_FAILED", detail=payload,
        )
        raise SystemExit("ACTIVATION_CANARY_FAILED")
    print(json.dumps({"status": "PASS", "audit": str(audit_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
