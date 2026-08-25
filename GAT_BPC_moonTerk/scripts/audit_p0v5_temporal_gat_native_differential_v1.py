#!/usr/bin/env python3
"""Bind a fresh 500-case disabled-Q0 cross-binary differential to this round."""

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

from scripts.audit_p0v5_counterfactual_native_differential_v8 import (  # noqa: E402
    _run_build,
    _stable_hash,
)
from scripts.p0v5_temporal_gat_common import (  # noqa: E402
    ensure_not_terminal, mark_terminal_negative,
    write_once,
)
from scripts.initialize_p0v5_temporal_gat_production_v1 import (  # noqa: E402
    MINIMUM_PYTHON_CONTRACT_TEST_COUNT,
    PYTHON_CONTRACT_TEST_PATHS,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-freeze", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        ensure_not_terminal(args.run_root)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    if args.source_freeze.resolve() != (
        args.run_root.resolve() / "source.freeze.json"
    ):
        raise SystemExit("Native differential source/run binding drift")
    source = json.loads(args.source_freeze.read_text(encoding="utf-8"))
    old_build = Path(source["reference_native_build_dir"])
    new_build = Path(source["native_build_dir"])
    cases = int(source["native_differential_cases"])
    if cases != 500:
        raise SystemExit("production Native differential must contain 500 cases")
    old_binary = Path(source["reference_native_binary"])
    new_binary = Path(source["native_binary"])
    native_test_binary = Path(source["native_test_binary"])
    if _sha(old_binary) != source["reference_native_binary_sha256"] or _sha(
        new_binary
    ) != source["native_binary_sha256"] or not native_test_binary.is_file() or _sha(
        native_test_binary
    ) != source["native_test_binary_sha256"]:
        raise SystemExit("Native differential binary hash binding drift")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((
        str(new_build.resolve()), str(ROOT / "src"),
    ))
    frozen_python_contract_paths = tuple(
        str(path) for path in source.get("python_contract_test_paths") or ()
    )
    expected_python_contract_test_count = int(
        source.get("python_contract_test_count") or 0
    )
    ctest = subprocess.run(
        ["ctest", "--test-dir", str(new_build), "--output-on-failure"],
        cwd=ROOT, check=False, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    python_contract = subprocess.run(
        [sys.executable, "-m", "pytest", "-q",
         *frozen_python_contract_paths],
        cwd=ROOT, env=environment, check=False, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    randomized_exact = subprocess.run(
        [str(native_test_binary)], cwd=ROOT, check=False, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    count_match = re.search(r"(\d+) passed", python_contract.stdout)
    python_contract_test_count = (
        int(count_match.group(1)) if count_match is not None else 0
    )
    randomized_match = re.search(
        r"TEMPORAL_ACTION_RANDOMIZED_EXACT cases=(\d+) mismatches=(\d+)",
        randomized_exact.stdout,
    )
    randomized_case_count = (
        int(randomized_match.group(1)) if randomized_match else 0
    )
    randomized_mismatch_count = (
        int(randomized_match.group(2)) if randomized_match else -1
    )
    if (
        ctest.returncode or python_contract.returncode
        or frozen_python_contract_paths != PYTHON_CONTRACT_TEST_PATHS
        or expected_python_contract_test_count
            < MINIMUM_PYTHON_CONTRACT_TEST_COUNT
        or python_contract_test_count != expected_python_contract_test_count
        or randomized_exact.returncode
        or randomized_case_count != 500
        or randomized_mismatch_count != 0
    ):
        detail = {
            "native_ctest_returncode": ctest.returncode,
            "native_ctest_output": ctest.stdout[-8000:],
            "python_contract_returncode": python_contract.returncode,
            "python_contract_output": python_contract.stdout[-8000:],
            "python_contract_test_count": python_contract_test_count,
            "expected_python_contract_test_count": (
                expected_python_contract_test_count
            ),
            "python_contract_test_paths": list(
                frozen_python_contract_paths
            ),
            "randomized_exact_returncode": randomized_exact.returncode,
            "randomized_exact_output": randomized_exact.stdout[-8000:],
            "randomized_exact_case_count": randomized_case_count,
            "randomized_exact_mismatch_count": randomized_mismatch_count,
        }
        mark_terminal_negative(
            args.run_root, stage="NATIVE_CONTRACT_TESTS",
            reason="TEMPORAL_NATIVE_CONTRACT_TESTS_FAILED", detail=detail,
        )
        raise SystemExit("TEMPORAL_NATIVE_CONTRACT_TESTS_FAILED")
    old = _run_build(old_build, cases)
    new = _run_build(new_build, cases)
    mismatches = [
        index for index, (left, right) in enumerate(zip(
            old["case_hashes"], new["case_hashes"]
        )) if left != right
    ]
    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_gat_native_differential.v1"
        ),
        "decision": "PASS" if not mismatches else "FAIL",
        "case_count": cases,
        "mismatch_count": len(mismatches),
        "mismatch_case_indices": mismatches,
        "reference_native_binary": str(old_binary),
        "reference_native_binary_sha256": _sha(old_binary),
        "temporal_native_binary": str(new_binary),
        "temporal_native_binary_sha256": _sha(new_binary),
        "reference_module_path": old["module_path"],
        "temporal_module_path": new["module_path"],
        "reference_build_info_hash": old["build_info_hash"],
        "temporal_build_info_hash": new["build_info_hash"],
        "reference_case_hashes_sha256": _stable_hash(old["case_hashes"]),
        "temporal_case_hashes_sha256": _stable_hash(new["case_hashes"]),
        "native_ctest_pass": True,
        "temporal_action_randomized_exact_case_count": (
            randomized_case_count
        ),
        "temporal_action_randomized_exact_mismatch_count": (
            randomized_mismatch_count
        ),
        "native_test_binary": str(native_test_binary),
        "native_test_binary_sha256": _sha(native_test_binary),
        "native_ctest_output_sha256": hashlib.sha256(
            ctest.stdout.encode("utf-8")
        ).hexdigest(),
        "python_contract_tests_pass": True,
        "python_contract_test_count": python_contract_test_count,
        "python_contract_test_paths": list(frozen_python_contract_paths),
        "python_contract_output_sha256": hashlib.sha256(
            python_contract.stdout.encode("utf-8")
        ).hexdigest(),
        "source_freeze_sha256": _sha(args.source_freeze),
        "checks": [
            "literal_Q0_disabled_temporal_mode",
            "route_payload_and_reduced_cost_inputs",
            "exact_status_and_certificate_fields",
            "pop_derived_counters",
            "atomic_bidirectional_migration_fault_injection",
            "500_randomized_force_trial_continue_revert_exact_differentials",
            "state_176_byte_abi_and_portable_parity",
            "deterministic_telemetry_hash",
        ],
        "deployment_authorized": False,
    }
    write_once(args.output, payload)
    if mismatches:
        mark_terminal_negative(
            args.run_root, stage="NATIVE_DIFFERENTIAL",
            reason="TEMPORAL_NATIVE_500_CASE_DIFFERENTIAL_FAILED",
            detail=payload,
        )
        raise SystemExit("TEMPORAL_NATIVE_500_CASE_DIFFERENTIAL_FAILED")
    print(json.dumps({"status": "PASS", "case_count": cases}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
