#!/usr/bin/env python3
"""Cross-binary exact differential for the V8 telemetry-only Native repair."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _stable_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


def _worker(case_count: int) -> dict:
    import lunar_spprc_native
    from lunar_ice_bpc.exact.bpc.pricing.backends.base import BackendPricingRequest
    from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import _native_request_payload
    from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
    from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals

    path = ROOT / "data/instances/lunar_ice_sp50_005/instance_001_logical_graph.json"
    data = load_lunar_ice_data(json.loads(path.read_text(encoding="utf-8")))
    generator = random.Random(260818500)
    hashes = []
    summaries = []
    counter_names = (
        "processed_labels", "extended_labels", "dominated_labels",
        "dominance_candidate_checks", "subset_dominance_candidate_checks",
        "subset_dominance_rejected_labels", "max_visited_bucket_size",
        "solution_count", "raw_unique_negative_count",
        "proof_queue_guidance_order_decisions",
        "proof_queue_guidance_reordered_label_hash_count",
    )
    for case_index in range(case_count):
        cover = {
            task_id: generator.uniform(-5.0, 45.0)
            for task_id in data.task_ids
        }
        request = BackendPricingRequest(
            data=data,
            true_duals=JourneyDuals(
                cover=cover, fleet_limit=generator.uniform(-3.0, 8.0)
            ),
            mode="exact_proof", objective_mode="official",
            proof_queue_policy_id="Q0",
            completion_bound_enabled=bool(case_index % 2),
            subset_dominance_enabled=bool((case_index // 2) % 2),
            exact_negative_escape_enabled=False,
            instance_hash=data.instance_content_hash,
            config_hash=f"v8-cross-binary-case-{case_index}",
            engine_hash="cross-binary-audit",
        )
        raw = dict(lunar_spprc_native.solve(_native_request_payload(request)))
        telemetry = dict(raw.get("telemetry") or {})
        canonical = {
            "status": raw.get("status"),
            "routes": raw.get("routes") or [],
            "search_exhaustive": bool(raw.get("search_exhaustive")),
            "frontier_empty": bool(raw.get("frontier_empty")),
            "labels_dropped": bool(raw.get("labels_dropped")),
            "best_found_rc": raw.get("best_found_rc"),
            "unexplored_rc_lower_bound": raw.get("unexplored_rc_lower_bound"),
            "certificate_blockers": raw.get("certificate_blockers") or [],
            "truncated_diagnostic": bool(raw.get("truncated_diagnostic")),
            "exact": bool(raw.get("exact")),
            "certificate": raw.get("certificate"),
            "queue_counters": {
                name: telemetry.get(name) for name in counter_names
            },
        }
        digest = _stable_hash(canonical)
        hashes.append(digest)
        summaries.append({
            "case_index": case_index,
            "digest": digest,
            "status": canonical["status"],
            "route_count": len(canonical["routes"]),
            "processed_labels": telemetry.get("processed_labels"),
        })
    return {
        "module_path": str(Path(lunar_spprc_native.__file__).resolve()),
        "build_info_hash": _stable_hash(dict(lunar_spprc_native.build_info())),
        "case_count": case_count,
        "case_hashes": hashes,
        "case_summaries": summaries,
    }


def _run_build(build_dir: Path, case_count: int) -> dict:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((str(build_dir), str(ROOT / "src")))
    completed = subprocess.run(
        [sys.executable, __file__, "--worker", "--cases", str(case_count)],
        cwd=ROOT, env=environment, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return json.loads(completed.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--cases", type=int, default=500)
    parser.add_argument("--old-build", type=Path)
    parser.add_argument("--new-build", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(_worker(int(args.cases)), sort_keys=True))
        return 0
    if args.old_build is None or args.new_build is None or args.output is None:
        parser.error("controller mode requires --old-build, --new-build, and --output")
    old = _run_build(args.old_build.resolve(), int(args.cases))
    new = _run_build(args.new_build.resolve(), int(args.cases))
    mismatches = [
        index for index, (left, right) in enumerate(
            zip(old["case_hashes"], new["case_hashes"])
        ) if left != right
    ]
    report = {
        "schema_version": "lunar_ice_bpc.p0v5_counterfactual_native_cross_binary_differential.v1",
        "decision": "PASS" if not mismatches else "FAIL",
        "case_count": int(args.cases),
        "old_module_path": old["module_path"],
        "new_module_path": new["module_path"],
        "old_build_info_hash": old["build_info_hash"],
        "new_build_info_hash": new["build_info_hash"],
        "mismatch_count": len(mismatches),
        "mismatch_case_indices": mismatches,
        "checks": [
            "Q0 pop-derived counters", "legal route payload", "minimum RC",
            "RC reconstruction inputs", "exact status", "certificate fields",
        ],
        "old_case_hashes_sha256": _stable_hash(old["case_hashes"]),
        "new_case_hashes_sha256": _stable_hash(new["case_hashes"]),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if not mismatches else 2


if __name__ == "__main__":
    raise SystemExit(main())
