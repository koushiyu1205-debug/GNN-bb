#!/usr/bin/env python3
"""Run the frozen 500-case disabled-mode differential for V10."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_p0v5_counterfactual_native_differential_v8 import (  # noqa: E402
    _run_build, _stable_hash,
)
from scripts.p0v5_temporal_frontier_late_switch_v10_common import (  # noqa: E402
    DEFAULT_RUN_ROOT, assert_active, load, update_state, write_once,
    write_terminal,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    assert_active(run_root, "NATIVE_DIFFERENTIAL")
    config = load(run_root / "config.freeze.json")
    source = load(run_root / "source.freeze.json")
    case_count = int(config["native_differential"]["case_count"])
    old = _run_build(Path(source["reference_native_build"]), case_count)
    new = _run_build(Path(source["temporal_native_build"]), case_count)
    mismatches = [
        index for index, (left, right) in enumerate(
            zip(old["case_hashes"], new["case_hashes"])
        ) if left != right
    ]
    report = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_native_differential.v1"
        ),
        "decision": "PASS" if not mismatches else "FAIL",
        "case_count": case_count,
        "old_module_path": old["module_path"],
        "new_module_path": new["module_path"],
        "old_build_info_hash": old["build_info_hash"],
        "new_build_info_hash": new["build_info_hash"],
        "mismatch_count": len(mismatches),
        "mismatch_case_indices": mismatches,
        "old_case_hashes_sha256": _stable_hash(old["case_hashes"]),
        "new_case_hashes_sha256": _stable_hash(new["case_hashes"]),
        "checks": [
            "disabled-mode Q0 pop-derived counters",
            "legal route payload",
            "minimum RC and reconstruction inputs",
            "exact status",
            "certificate fields",
        ],
    }
    write_once(run_root / "native_differential.report.json", report)
    if mismatches:
        write_terminal(
            run_root, "V10_NATIVE_TEMPORAL_DIFFERENTIAL_REDLINE",
            "NATIVE_DIFFERENTIAL", report,
        )
    else:
        update_state(run_root, "PERFORMANCE_FREEZE")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not mismatches else 2


if __name__ == "__main__":
    raise SystemExit(main())

