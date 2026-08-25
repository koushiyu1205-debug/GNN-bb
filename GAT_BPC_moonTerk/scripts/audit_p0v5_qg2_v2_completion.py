#!/usr/bin/env python3
"""Requirement-by-requirement completion audit for P0V5 QG2 V2."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
COLLECTION_FREEZE = (
    RUN_ROOT / "qg2_clean_v2_collection_freeze_storage_cap_v4.json"
)
ORACLE_EXECUTION_FREEZE = (
    RUN_ROOT / "qg2_clean_v2_oracle_execution_freeze_storage_cap_v3.json"
)
POST_ORACLE_FREEZE = (
    RUN_ROOT
    / "qg2_clean_v2_post_oracle_controller_freeze_storage_cap_v3.json"
)
E2E_FREEZE = (
    RUN_ROOT / "qg2_clean_v2_e2e_controller_freeze_storage_cap_v3.json"
)
FORMAL_FREEZE = (
    RUN_ROOT / "qg2_clean_v2_formal_controller_freeze_storage_cap_v3.json"
)
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(BUILD))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=str(RUN_ROOT / "p0v5_qg2_v2_completion_audit.json"),
    )
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument(
        "--pre-final-freeze",
        action="store_true",
        help="Audit every requirement except the final candidate freeze itself.",
    )
    args = parser.parse_args()
    checks = {
        "exact_control_and_collection_freeze": _audit_freeze(),
        "frozen400_candidate_corpus": _audit_corpus(),
        "oracle_execution_freeze": _audit_oracle_execution_freeze(),
        "post_oracle_controller_freeze": _audit_post_oracle_freeze(),
        "development_e2e_controller_freeze": _audit_e2e_freeze(),
        "formal_full20_controller_freeze": _audit_formal_freeze(),
        "qg2_exact_safe_implementation": _audit_implementation(),
        "clean_snapshot_coverage": _audit_collection(),
        "real_branch_cut_snapshot_coverage": _audit_tree_supplement(),
        "bounded_qo2_oracle_gate": _audit_oracle(),
        "model_comparison_training": _audit_training(),
        "fresh_process_calibration": _audit_calibration(),
        "heldout_snapshot_replay": _audit_heldout(),
        "development_end_to_end": _audit_e2e(),
        "formal_scale5_to_50_full20": _audit_formal(),
    }
    if not args.pre_final_freeze:
        checks["frozen_experiment_candidate"] = _audit_candidate_freeze()
    if args.run_tests:
        checks["automated_regression_tests"] = _run_tests()
    else:
        checks["automated_regression_tests"] = _check(
            "INCOMPLETE",
            "not executed by this audit invocation",
        )
    required = tuple(checks)
    complete = all(checks[key]["status"] == "PASS" for key in required)
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_v2_completion_audit.v1",
        "objective": "P0V5 Proof-Tail GAT V2 Q0-Anchored Label-State Guidance",
        "complete": complete,
        "checks": checks,
        "required_check_count": len(required),
        "passed_check_count": sum(
            checks[key]["status"] == "PASS" for key in required
        ),
        "failed_check_count": sum(
            checks[key]["status"] == "FAIL" for key in required
        ),
        "incomplete_check_count": sum(
            checks[key]["status"] == "INCOMPLETE" for key in required
        ),
        "completion_rule": "all_required_checks_must_pass",
        "pre_final_freeze": bool(args.pre_final_freeze),
    }
    output = _resolve(args.output)
    _write(output, payload)
    print(json.dumps({
        "complete": complete,
        "passed": payload["passed_check_count"],
        "failed": payload["failed_check_count"],
        "incomplete": payload["incomplete_check_count"],
        "output": str(output),
    }, sort_keys=True))
    return 0 if complete else 2


def _audit_freeze() -> dict:
    freeze_path = COLLECTION_FREEZE
    if not freeze_path.is_file():
        return _check("INCOMPLETE", "clean-v2 collection freeze missing")
    freeze = _load(freeze_path)
    issues = []
    expected = (
        (ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_runtime.py", "qg2_runtime_source_sha256"),
        (ROOT / "src/lunar_ice_bpc/guidance/proof_queue_label_state_gat.py", "qg2_model_source_sha256"),
        (_resolve(freeze.get("selected_exact_config", "")), "selected_exact_config_sha256"),
        (_resolve(freeze.get("development_corpus_manifest", "")), "development_corpus_manifest_sha256"),
    )
    for path, key in expected:
        if not path.is_file() or _sha256(path) != str(freeze.get(key) or ""):
            issues.append(f"{key}_drift")
    extensions = tuple(BUILD.glob("lunar_spprc_native*.so"))
    if len(extensions) != 1 or _sha256(extensions[0]) != str(
        freeze.get("native_extension_sha256") or ""
    ):
        issues.append("native_extension_drift")
    return _check(
        "FAIL" if issues else "PASS",
        "freeze hash audit",
        freeze=str(freeze_path),
        issues=issues,
    )


def _audit_corpus() -> dict:
    path = ROOT / "data/p0v5_qg2_oracle_development_v3/manifest.json"
    if not path.is_file():
        return _check("INCOMPLETE", "frozen400 candidate corpus manifest missing")
    payload = _load(path)
    valid = bool(
        payload.get("status") == "FROZEN_BEFORE_ANY_QO2_OUTCOME"
        and int(payload.get("row_count") or 0) == 400
        and int(payload.get("unique_content_hash_count") or 0) == 400
        and int(payload.get("official_evaluation_corpus_overlap_count") or 0) == 0
        and int(payload.get("protected_content_overlap_count") or 0) == 0
    )
    return _check(
        "PASS" if valid else "FAIL",
        "400 unique pre-oracle candidates with zero protected overlap",
        manifest=str(path),
    )


def _audit_implementation() -> dict:
    try:
        from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (
            spprc_engine_build_hash,
        )
        from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
            qg2_runtime_implementation_hash,
        )
        import lunar_spprc_native

        build_info = dict(lunar_spprc_native.build_info())
        engine = spprc_engine_build_hash(
            "native_rcspp_bidirectional_root_partial_hybrid_v3"
        )
        runtime = qg2_runtime_implementation_hash()
    except Exception as exc:
        return _check("FAIL", "implementation import failed", error=repr(exc))
    freeze = _load(COLLECTION_FREEZE)
    valid = bool(
        engine == str(freeze.get("source_engine_hash") or "")
        and runtime == str(freeze.get("qg2_runtime_implementation_hash") or "")
        and str(build_info.get("label_state_bytes") or "") == "176"
    )
    return _check(
        "PASS" if valid else "FAIL",
        "engine/runtime binding and 176-byte State",
        source_engine_hash=engine,
        runtime_implementation_hash=runtime,
        label_state_bytes=build_info.get("label_state_bytes"),
    )


def _audit_oracle_execution_freeze() -> dict:
    path = ORACLE_EXECUTION_FREEZE
    if not path.is_file():
        return _check("INCOMPLETE", "oracle execution freeze missing")
    payload = _load(path)
    issues = []
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_oracle_execution_freeze.v1"
    ):
        issues.append("schema_mismatch")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        target = _resolve(raw_path)
        if not target.is_file() or _sha256(target) != str(expected):
            issues.append(f"drift:{raw_path}")
    return _check(
        "FAIL" if issues else "PASS",
        "replay/oracle/training/calibration cache identity freeze",
        freeze=str(path),
        issues=issues,
    )


def _audit_post_oracle_freeze() -> dict:
    path = POST_ORACLE_FREEZE
    if not path.is_file():
        return _check("INCOMPLETE", "post-oracle controller freeze missing")
    payload = _load(path)
    issues = []
    if payload.get("schema_version") not in {
        "lunar_ice_bpc.p0v5_qg2_post_oracle_controller_freeze.v1",
        "lunar_ice_bpc.p0v5_qg2_post_oracle_controller_freeze.v2",
    }:
        issues.append("schema_mismatch")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        target = _resolve(raw_path)
        if not target.is_file() or _sha256(target) != str(expected):
            issues.append(f"drift:{raw_path}")
    return _check(
        "FAIL" if issues else "PASS",
        "oracle-pass-only training and calibration controller freeze",
        freeze=str(path),
        issues=issues,
    )


def _audit_e2e_freeze() -> dict:
    path = E2E_FREEZE
    if not path.is_file():
        return _check("INCOMPLETE", "development E2E controller freeze missing")
    payload = _load(path)
    issues = []
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_e2e_controller_freeze.v1"
    ):
        issues.append("schema_mismatch")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        target = _resolve(raw_path)
        if not target.is_file() or _sha256(target) != str(expected):
            issues.append(f"drift:{raw_path}")
    return _check(
        "FAIL" if issues else "PASS",
        "calibration-pass-only development E2E controller freeze",
        freeze=str(path),
        issues=issues,
    )


def _audit_formal_freeze() -> dict:
    path = FORMAL_FREEZE
    if not path.is_file():
        return _check("INCOMPLETE", "formal full20 controller freeze missing")
    payload = _load(path)
    issues = []
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_formal_controller_freeze.v1"
    ):
        issues.append("schema_mismatch")
    if bool(payload.get("production_default")):
        issues.append("unsafe_production_default")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        target = _resolve(raw_path)
        if not target.is_file() or _sha256(target) != str(expected):
            issues.append(f"drift:{raw_path}")
    return _check(
        "FAIL" if issues else "PASS",
        "development-E2E-pass-only formal full20 controller freeze",
        freeze=str(path),
        issues=issues,
    )


def _audit_collection() -> dict:
    path = RUN_ROOT / "qg2_clean_v2_live_snapshot_index.json"
    if not path.is_file():
        return _check("INCOMPLETE", "clean snapshot index missing")
    payload = _load(path)
    collection_freeze = _load(COLLECTION_FREEZE)
    required_action_hashes = dict(
        collection_freeze.get(
            "required_exact_action_policy_hashes_by_scale"
        ) or {}
    )
    observed_action_hashes = {
        str(value)
        for value in payload.get(
            "observed_exact_action_policy_hashes"
        ) or ()
    }
    coverage = dict(payload.get("coverage") or {})
    ready = bool(
        int(payload.get("excluded_count") or 0) == 0
        and str(payload.get("collection_freeze_sha256") or "")
        == _sha256(COLLECTION_FREEZE)
        and set(required_action_hashes) == {"30", "50"}
        and observed_action_hashes == set(required_action_hashes.values())
        and dict(payload.get(
            "expected_exact_action_policy_hashes_by_scale"
        ) or {}) == required_action_hashes
        and all(
            int((coverage.get(str(scale)) or {}).get("context_count") or 0) >= 150
            and int((coverage.get(str(scale)) or {}).get("instance_count") or 0) >= 10
            for scale in (30, 50)
        )
        and sum(
            int((coverage.get(str(scale)) or {}).get("context_count") or 0)
            for scale in (30, 50)
        ) >= 300
    )
    return _check(
        "PASS" if ready else "INCOMPLETE",
        "strict clean snapshot coverage gate",
        index=str(path),
        coverage=coverage,
        excluded_count=payload.get("excluded_count"),
        collection_freeze_sha256=payload.get("collection_freeze_sha256"),
        required_action_hashes_by_scale=required_action_hashes,
        observed_action_hashes=sorted(observed_action_hashes),
    )


def _audit_oracle() -> dict:
    path = RUN_ROOT / "oracle_qg2_clean_v2_storage_cap_v2_stage1.json"
    if not path.is_file():
        return _check("INCOMPLETE", "bounded QO2 oracle has not completed")
    payload = _load(path)
    passed = bool(
        (payload.get("oracle_gate") or {}).get("passed")
        and payload.get("training_permitted")
    )
    return _check(
        "PASS" if passed else "FAIL",
        "scale30/50 bounded QO2 oracle gate",
        summary=str(path),
        oracle_gate=payload.get("oracle_gate"),
    )


def _audit_tree_supplement() -> dict:
    state_path = (
        RUN_ROOT
        / "qg2_clean_v2_tree_supplement_storage_cap_v2_state.json"
    )
    index_path = RUN_ROOT / "qg2_clean_v2_live_snapshot_index.json"
    if not state_path.is_file():
        return _check(
            "INCOMPLETE",
            "bounded real-tree supplement has not run",
        )
    if not index_path.is_file():
        return _check("INCOMPLETE", "strict snapshot index missing")
    state = _load(state_path)
    index = _load(index_path)
    coverage = dict(index.get("coverage") or {})
    branch_cut = sum(
        int(
            (coverage.get(str(scale)) or {}).get(
                "branch_or_cut_context_count"
            )
            or 0
        )
        for scale in (30, 50)
    )
    passed = bool(
        state.get("status") == "COMPLETED_WITH_BRANCH_CUT_CONTEXT"
        and branch_cut >= 1
        and int(index.get("excluded_count") or 0) == 0
    )
    return _check(
        "PASS" if passed else "INCOMPLETE",
        "real branch/cut snapshot binding coverage",
        state=str(state_path),
        index=str(index_path),
        branch_cut_context_count=branch_cut,
        supplement_status=state.get("status"),
    )


def _audit_training() -> dict:
    path = RUN_ROOT / "training_qg2_clean_v2/training_report.json"
    if not path.is_file():
        return _check("INCOMPLETE", "Linear/MLP/GAT training report missing")
    payload = _load(path)
    kinds = {str(row.get("model_kind") or "") for row in payload.get("models") or ()}
    valid = bool(
        payload.get("oracle_gate_passed")
        and kinds == {"linear", "mlp", "gat"}
        and int(payload.get("calibration_context_count") or 0) >= 52
    )
    return _check(
        "PASS" if valid else "FAIL",
        "single authorized Linear/MLP/TinyGAT comparison",
        report=str(path),
        model_kinds=sorted(kinds),
    )


def _audit_calibration() -> dict:
    path = RUN_ROOT / "calibration_qg2_clean_v2/calibration_report.json"
    if not path.is_file():
        return _check("INCOMPLETE", "fresh-process calibration report missing")
    payload = _load(path)
    valid = bool(payload.get("gate_pass") and payload.get("deployment_authorized"))
    return _check(
        "PASS" if valid else "FAIL",
        "risk/precision/OOD/inference/GAT-advantage calibration",
        report=str(path),
        manifest=payload.get("manifest_path"),
    )


def _audit_heldout() -> dict:
    path = RUN_ROOT / "calibration_qg2_clean_v2/calibration_report.json"
    if not path.is_file():
        return _check("INCOMPLETE", "heldout fresh-process replay missing")
    payload = _load(path)
    gat = next(
        (row for row in payload.get("models") or () if row.get("model_kind") == "gat"),
        {},
    )
    heldout = dict(gat.get("heldout") or {})
    valid = bool(
        heldout.get("all_safe")
        and float(heldout.get("net_geomean_ratio", 1.0)) <= 0.90
    )
    return _check(
        "PASS" if valid else "FAIL",
        "unseen snapshot Q0/GAT three-repeat heldout gate",
        heldout=heldout,
    )


def _audit_e2e() -> dict:
    path = RUN_ROOT / "e2e_development_acceptance_qg2_clean_v2.json"
    if not path.is_file():
        return _check("INCOMPLETE", "scale30/50 development E2E evidence missing")
    payload = _load(path)
    valid = _paired_acceptance_valid(
        payload, mode="development", required_scales={30, 50}
    )
    return _check(
        "PASS" if valid else "FAIL",
        "scale30/50 development E2E acceptance",
        evidence=str(path),
    )


def _audit_formal() -> dict:
    path = RUN_ROOT / "formal_full20_acceptance_qg2_clean_v2.json"
    if not path.is_file():
        return _check("INCOMPLETE", "formal scale5-to-50 full20 evidence missing")
    payload = _load(path)
    valid = _paired_acceptance_valid(
        payload, mode="formal", required_scales={5, 10, 20, 30, 50}
    )
    return _check(
        "PASS" if valid else "FAIL",
        "scale5/10/20/30/50 full20 acceptance",
        evidence=str(path),
    )


def _audit_candidate_freeze() -> dict:
    path = RUN_ROOT / "P0V5_QG2_LABEL_STATE_GAT_candidate_freeze.json"
    if not path.is_file():
        return _check("INCOMPLETE", "independent experiment candidate freeze missing")
    payload = _load(path)
    issues = []
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_candidate_freeze.v1"
    ):
        issues.append("schema_mismatch")
    if payload.get("status") != "FROZEN_EXPERIMENT_CANDIDATE":
        issues.append("status_mismatch")
    if bool(payload.get("production_default")):
        issues.append("production_default_changed")
    if not bool(payload.get("historical_baselines_unchanged")):
        issues.append("historical_baseline_safety_missing")
    if not bool(
        payload.get("deployment_authorized")
        and payload.get("development_e2e_passed")
        and payload.get("formal_full20_passed")
    ):
        issues.append("acceptance_or_deployment_gate_missing")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        target = _resolve(raw_path)
        if not target.is_file() or _sha256(target) != str(expected):
            issues.append(f"drift:{raw_path}")
    return _check(
        "FAIL" if issues else "PASS",
        "independent P0V5 QG2 experiment candidate freeze",
        freeze=str(path),
        issues=issues,
    )


def _paired_acceptance_valid(
    payload: dict,
    *,
    mode: str,
    required_scales: set[int],
) -> bool:
    if (
        payload.get("schema_version")
        != "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1"
        or payload.get("mode") != mode
        or not bool(payload.get("passed"))
        or int(payload.get("violation_count") or 0) != 0
        or {int(value) for value in (payload.get("by_scale") or {})}
        != required_scales
    ):
        return False
    for prefix in ("control", "guided"):
        root = _resolve(payload.get(f"{prefix}_root") or "")
        if (
            not root.is_dir()
            or _acceptance_artifact_hash(root)
            != str(payload.get(f"{prefix}_root_hash") or "")
        ):
            return False
    return True


def _acceptance_artifact_hash(root: Path) -> str:
    digest = hashlib.sha256()
    paths = set()
    for pattern in (
        "**/b4_2_cold_exact_rows.csv",
        "**/b4_2_cold_exact_state.json",
        "**/b4_2_cold_exact_summary.json",
        "**/tree_closure_001.json",
    ):
        paths.update(root.glob(pattern))
    if not paths:
        return ""
    for path in sorted(paths):
        digest.update(str(path.relative_to(root)).encode("utf-8"))
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _run_tests() -> dict:
    commands = (
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_p0v5_bidirectional_gate_gat.py",
            "tests/test_p0v5_qg2_label_state_gat.py",
        ],
        ["ctest", "--test-dir", str(BUILD), "--output-on-failure"],
        ["git", "diff", "--check"],
    )
    rows = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        rows.append({
            "command": command,
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
        })
    return _check(
        "PASS" if all(row["returncode"] == 0 for row in rows) else "FAIL",
        "QG2 Python, Native CTest, and diff checks",
        commands=rows,
    )


def _check(status: str, note: str, **evidence) -> dict:
    if status not in {"PASS", "FAIL", "INCOMPLETE"}:
        raise ValueError(f"invalid audit status {status}")
    return {"status": status, "note": note, "evidence": evidence}


def _resolve(value) -> Path:
    path = Path(str(value))
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
