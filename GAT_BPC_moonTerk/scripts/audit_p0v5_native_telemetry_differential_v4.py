#!/usr/bin/env python3
"""Compare the frozen pre-V4 Native binary with the telemetry-only V4 build.

The worker mode deliberately uses literal Q0 exact-proof requests.  The parent
runs each binary in a separate interpreter so the same pybind module name can
never resolve to the wrong shared object.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OLD_BUILD = ROOT / "build/native-spprc-context-queue-portfolio-v1"
DEFAULT_NEW_BUILD = ROOT / "build/native-spprc-residual-gat-v4"
DEFAULT_OUTPUT = ROOT / "output/p0v5_native_telemetry_differential_v4.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-build", type=Path, default=DEFAULT_OLD_BUILD)
    parser.add_argument("--new-build", type=Path, default=DEFAULT_NEW_BUILD)
    parser.add_argument("--cases", type=int, default=500)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--worker-output", type=Path)
    args = parser.parse_args()
    if args.worker:
        if args.worker_output is None:
            raise SystemExit("worker output is required")
        return _worker(args.cases, args.worker_output.resolve())
    if args.cases != 500:
        raise SystemExit("V4 frozen differential requires exactly 500 cases")
    old_build = args.old_build.resolve()
    new_build = args.new_build.resolve()
    old_binary = _single_binary(old_build)
    new_binary = _single_binary(new_build)
    with tempfile.TemporaryDirectory(prefix="p0v5_v4_native_diff_") as directory:
        temporary = Path(directory)
        old_rows = _run_worker(old_build, args.cases, temporary / "old.json")
        new_rows = _run_worker(new_build, args.cases, temporary / "new.json")
    redlines = _compare(old_rows, new_rows)
    report = {
        "schema_version": "lunar_ice_bpc.p0v5_native_telemetry_differential.v4",
        "status": "PASS" if not redlines else "FAIL",
        "case_count": args.cases,
        "literal_q0_exact_proof_only": True,
        "old_build": str(old_build),
        "old_binary": str(old_binary),
        "old_binary_sha256": _sha256(old_binary),
        "new_build": str(new_build),
        "new_binary": str(new_binary),
        "new_binary_sha256": _sha256(new_binary),
        "old_result_digest": _digest(old_rows),
        "new_result_digest": _digest(new_rows),
        "compared_fields": [
            "status", "search_exhaustive", "frontier_empty", "labels_dropped",
            "best_found_rc", "unexplored_rc_lower_bound", "certificate_blockers",
            "canonical_route_universe_with_reduced_cost",
        ],
        "redline_count": len(redlines),
        "redlines": redlines[:20],
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not redlines else 2


def _worker(cases: int, output: Path) -> int:
    from lunar_ice_bpc.domain.scheduling import generate_instance
    from lunar_ice_bpc.exact.bpc.pricing.backends.base import BackendPricingRequest
    from lunar_ice_bpc.exact.bpc.pricing.backends.native_rcspp import (
        _native_request_payload,
    )
    from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
    from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
    import lunar_spprc_native

    rows = []
    for index in range(cases):
        seed = 410_815_000 + index
        data = load_lunar_ice_data(generate_instance(5, seed=seed, index=index + 1))
        cover = {
            task_id: 3.0 + float((index * 17 + task_index * 11) % 37) / 3.0
            for task_index, task_id in enumerate(data.task_ids)
        }
        request = BackendPricingRequest(
            data=data,
            true_duals=JourneyDuals(cover=cover),
            mode="exact_proof",
            proof_queue_policy_id="Q0",
            proof_tail_label_trace_enabled=False,
        )
        raw = dict(lunar_spprc_native.solve(_native_request_payload(request)))
        routes = []
        for route in raw.get("routes") or ():
            sorties = tuple(
                (
                    tuple(str(value) for value in sortie.get("tasks") or ()),
                    tuple(str(value) for value in sortie.get("path_types") or ()),
                )
                for sortie in route.get("sorties") or ()
            )
            routes.append({
                "sorties": sorties,
                "reduced_cost": round(float(route["reduced_cost"]), 10),
            })
        routes.sort(key=lambda row: (row["sorties"], row["reduced_cost"]))
        rows.append({
            "case": index,
            "instance_content_hash": str(data.instance_content_hash),
            "status": str(raw.get("status") or ""),
            "search_exhaustive": bool(raw.get("search_exhaustive")),
            "frontier_empty": bool(raw.get("frontier_empty")),
            "labels_dropped": bool(raw.get("labels_dropped")),
            "best_found_rc": _finite_or_none(raw.get("best_found_rc")),
            "unexplored_rc_lower_bound": _finite_or_none(
                raw.get("unexplored_rc_lower_bound")
            ),
            "certificate_blockers": sorted(
                str(value) for value in raw.get("certificate_blockers") or ()
            ),
            "routes": routes,
        })
    output.write_text(json.dumps(rows, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def _run_worker(build: Path, cases: int, output: Path):
    _single_binary(build)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((str(build), str(ROOT / "src")))
    completed = subprocess.run(
        [
            sys.executable, str(Path(__file__).resolve()), "--worker",
            "--cases", str(cases), "--worker-output", str(output),
        ],
        cwd=ROOT,
        env=environment,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"Native differential worker failed for {build}")
    return json.loads(output.read_text(encoding="utf-8"))


def _compare(old_rows, new_rows):
    if len(old_rows) != len(new_rows):
        return [{"reason": "case_count_mismatch"}]
    redlines = []
    scalar_fields = (
        "case", "instance_content_hash", "status", "search_exhaustive",
        "frontier_empty", "labels_dropped", "certificate_blockers", "routes",
    )
    for old, new in zip(old_rows, new_rows, strict=True):
        differing = [field for field in scalar_fields if old[field] != new[field]]
        for field in ("best_found_rc", "unexplored_rc_lower_bound"):
            if not _same_optional_float(old[field], new[field]):
                differing.append(field)
        if differing:
            redlines.append({"case": old["case"], "fields": sorted(differing)})
    return redlines


def _finite_or_none(value):
    if value is None:
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _same_optional_float(left, right):
    if left is None or right is None:
        return left is right
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1.0e-9)


def _single_binary(build: Path):
    paths = list(build.glob("lunar_spprc_native*.so"))
    if len(paths) != 1:
        raise SystemExit(f"expected one Native extension in {build}")
    return paths[0].resolve()


def _sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
