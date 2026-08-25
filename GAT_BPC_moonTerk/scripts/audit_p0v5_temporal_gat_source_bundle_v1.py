#!/usr/bin/env python3
"""Audit source, Native binary, ABI, bundle, and runtime hash bindings."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.p0v5_temporal_gat_common import (  # noqa: E402
    ensure_not_terminal, mark_terminal_negative,
)
from scripts.initialize_p0v5_temporal_gat_production_v1 import (  # noqa: E402
    MINIMUM_PYTHON_CONTRACT_TEST_COUNT, PYTHON_CONTRACT_TEST_PATHS,
    SOURCE_GLOBS, SOURCE_PATHS, SOURCE_STATIC_PATHS,
)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-freeze", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--runtime-manifest", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--k-selection", type=Path, required=True)
    parser.add_argument("--training-report", type=Path, required=True)
    parser.add_argument(
        "--trial-outcomes", type=Path, required=True, nargs="+"
    )
    parser.add_argument("--native-differential", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        ensure_not_terminal(args.source_freeze.resolve().parent)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    source = json.loads(args.source_freeze.read_text(encoding="utf-8"))
    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    runtime = json.loads(args.runtime_manifest.read_text(encoding="utf-8"))
    differential = json.loads(
        args.native_differential.read_text(encoding="utf-8")
    )
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    k_selection = json.loads(
        args.k_selection.read_text(encoding="utf-8")
    )
    training = json.loads(
        args.training_report.read_text(encoding="utf-8")
    )
    issues = []
    expected_inventory_contract = {
        "static_paths": list(SOURCE_STATIC_PATHS),
        "globs": list(SOURCE_GLOBS),
        "resolved_paths": list(SOURCE_PATHS),
    }
    if source.get("source_inventory_contract") != expected_inventory_contract:
        issues.append("source_inventory_contract_drift")
    if set(source.get("source_sha256") or {}) != set(SOURCE_PATHS):
        issues.append("source_inventory_membership_drift")
    for relative, expected in source["source_sha256"].items():
        if not (ROOT / relative).is_file() or _sha(ROOT / relative) != expected:
            issues.append(f"source_hash_drift:{relative}")
    binary = Path(source["native_binary"])
    if not binary.is_file() or _sha(binary) != source["native_binary_sha256"]:
        issues.append("native_binary_hash_drift")
    native_test_binary = Path(str(source.get("native_test_binary") or ""))
    if (
        not native_test_binary.is_file()
        or _sha(native_test_binary)
            != str(source.get("native_test_binary_sha256") or "")
    ):
        issues.append("native_test_binary_hash_drift")
    for label, path_key, hash_key in (
        ("reference_native_binary", "reference_native_binary",
         "reference_native_binary_sha256"),
        ("selected_exact_config", "selected_exact_config",
         "selected_exact_config_sha256"),
        ("formal_acceptance_contract", "formal_acceptance_contract",
         "formal_acceptance_contract_sha256"),
        ("corpus_manifest", "corpus_manifest", "corpus_manifest_sha256"),
        ("protected_history_cache", "protected_history_cache",
         "protected_history_cache_sha256"),
    ):
        path = Path(str(source.get(path_key) or ""))
        if not path.is_file() or _sha(path) != str(source.get(hash_key) or ""):
            issues.append(f"{label}_hash_drift")
    normalized = dict(bundle)
    internal = normalized.pop("bundle_sha256", "")
    canonical = json.dumps(
        normalized, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != internal:
        issues.append("bundle_internal_hash_drift")
    if runtime.get("portable_bundle_file_sha256") != _sha(args.bundle):
        issues.append("runtime_bundle_file_hash_drift")
    bindings = dict(bundle.get("bindings") or {})
    observed_request_configs = bindings.get(
        "source_request_config_hashes_observed_diagnostic_only"
    )
    if not isinstance(observed_request_configs, list) or not all(
        isinstance(value, str) and value for value in observed_request_configs
    ):
        issues.append("diagnostic_request_config_hash_binding_drift")
    if "config_hashes" in bindings:
        issues.append("dynamic_request_config_hash_used_as_allowlist")
    if bindings.get("selected_exact_config_sha256") != source[
        "selected_exact_config_sha256"
    ]:
        issues.append("selected_exact_config_binding_drift")
    if bindings.get("source_freeze_sha256") != _sha(args.source_freeze):
        issues.append("bundle_source_freeze_binding_drift")
    if bindings.get("native_binary_sha256") != source[
        "native_binary_sha256"
    ]:
        issues.append("bundle_native_binary_binding_drift")
    config_freeze = args.source_freeze.resolve().parent / "config.freeze.json"
    frozen_config = (
        json.loads(config_freeze.read_text(encoding="utf-8"))
        if config_freeze.is_file() else {}
    )
    if not config_freeze.is_file() or bindings.get(
        "experiment_config_sha256"
    ) != _sha(config_freeze):
        issues.append("bundle_experiment_config_binding_drift")
    if bindings.get("dataset_sha256") != _sha(args.dataset):
        issues.append("bundle_dataset_binding_drift")
    if bindings.get("k_selection_sha256") != _sha(args.k_selection):
        issues.append("bundle_k_selection_binding_drift")
    trial_by_partition = {}
    trial_schedule_bindings = {}
    canonical_contexts = args.source_freeze.resolve().parent / "contexts.freeze.json"
    for path in args.trial_outcomes:
        payload = json.loads(path.read_text(encoding="utf-8"))
        partition = str(payload.get("partition") or "")
        if not partition or partition in trial_by_partition:
            issues.append("trial_outcome_partition_binding_drift")
            continue
        trial_by_partition[partition] = {
            "path": str(path.resolve()), "sha256": _sha(path),
        }
        schedule_path = Path(str(payload.get("source_schedule") or ""))
        contexts_path = Path(str(payload.get("source_contexts") or ""))
        if (
            not schedule_path.is_file()
            or _sha(schedule_path)
                != str(payload.get("source_schedule_sha256") or "")
            or contexts_path.resolve() != canonical_contexts.resolve()
            or not contexts_path.is_file()
            or _sha(contexts_path)
                != str(payload.get("source_contexts_sha256") or "")
        ):
            issues.append(f"trial_schedule_context_binding_drift:{partition}")
        else:
            schedule_payload = json.loads(
                schedule_path.read_text(encoding="utf-8")
            )
            contexts_payload = json.loads(
                contexts_path.read_text(encoding="utf-8")
            )
            if (
                schedule_payload.get("partition") != partition
                or schedule_payload.get("source_config_freeze_sha256")
                    != _sha(config_freeze)
                or schedule_payload.get("source_contexts_sha256")
                    != _sha(contexts_path)
                or int(schedule_payload.get("task_count") or -1)
                    != int(payload.get("row_count") or -2)
                or contexts_payload.get("status")
                    != "FROZEN_BEFORE_CONTINUE_REVERT_OUTCOMES"
                or contexts_payload.get("source_config_freeze_sha256")
                    != _sha(config_freeze)
                or contexts_payload.get("source_freeze_sha256")
                    != _sha(args.source_freeze)
            ):
                issues.append(
                    f"trial_schedule_context_contract_drift:{partition}"
                )
            trial_schedule_bindings[partition] = {
                "path": str(schedule_path.resolve()),
                "sha256": _sha(schedule_path),
            }
        if (
            payload.get("source_config_freeze_sha256") != _sha(config_freeze)
            or payload.get("source_freeze_sha256") != _sha(args.source_freeze)
            or payload.get("native_binary_sha256")
                != source.get("native_binary_sha256")
            or bool(payload.get("differential_redlines"))
        ):
            issues.append(f"trial_outcome_immutable_binding_drift:{partition}")
    if trial_by_partition.keys() != {"train", "calibration"}:
        issues.append("trial_outcome_partition_coverage_drift")
    if dict(dataset.get("source_outcome_sha256") or {}) != {
        key: row["sha256"] for key, row in trial_by_partition.items()
    }:
        issues.append("dataset_trial_outcome_binding_drift")
    if k_selection.get("source_outcomes_sha256") != dict(
        trial_by_partition.get("train") or {}
    ).get("sha256"):
        issues.append("k_selection_train_outcome_binding_drift")
    if (
        training.get("status") != "TRAINED_DEVELOPMENT_ONLY_NOT_PROMOTED"
        or not bool(dict(training.get("control_audit") or {}).get(
            "representation_gate_pass"
        ))
        or training.get("bundle_file_sha256") != _sha(args.bundle)
        or training.get("dataset_sha256") != _sha(args.dataset)
        or training.get("k_selection_sha256") != _sha(args.k_selection)
        or training.get("source_freeze_sha256") != _sha(args.source_freeze)
        or training.get("experiment_config_sha256") != _sha(config_freeze)
        or runtime.get("training_report_sha256")
            != _sha(args.training_report)
        or (args.runtime_manifest.resolve().parent / str(
            runtime.get("training_report_path") or ""
        )).resolve() != args.training_report.resolve()
    ):
        issues.append("training_report_evidence_binding_drift")
    if source["exact_engine_hash"] not in runtime.get(
        "allowed_exact_engine_hashes", ()
    ):
        issues.append("runtime_engine_binding_drift")
    if (
        differential.get("decision") != "PASS"
        or not bool(differential.get("native_ctest_pass"))
        or not bool(differential.get("python_contract_tests_pass"))
        or tuple(source.get("python_contract_test_paths") or ())
            != PYTHON_CONTRACT_TEST_PATHS
        or int(source.get("python_contract_test_count") or 0)
            < MINIMUM_PYTHON_CONTRACT_TEST_COUNT
        or tuple(differential.get("python_contract_test_paths") or ())
            != PYTHON_CONTRACT_TEST_PATHS
        or int(differential.get("python_contract_test_count") or 0)
            != int(source.get("python_contract_test_count") or 0)
        or int(differential.get("case_count") or 0) != 500
        or int(differential.get("mismatch_count", -1)) != 0
        or int(differential.get(
            "temporal_action_randomized_exact_case_count"
        ) or 0) != 500
        or int(differential.get(
            "temporal_action_randomized_exact_mismatch_count", -1
        )) != 0
        or differential.get("source_freeze_sha256") != _sha(args.source_freeze)
        or differential.get("reference_native_binary_sha256")
            != source.get("reference_native_binary_sha256")
        or differential.get("temporal_native_binary_sha256")
            != source.get("native_binary_sha256")
        or differential.get("native_test_binary_sha256")
            != source.get("native_test_binary_sha256")
    ):
        issues.append("native_500_case_differential_binding_drift")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((
        source["native_build_dir"], str(ROOT / "src"),
    ))
    live_info = json.loads(subprocess.run(
        [sys.executable, "-c", (
            "import json,lunar_spprc_native as n;"
            "print(json.dumps(n.build_info(),sort_keys=True))"
        )], cwd=ROOT, env=environment, check=True, text=True,
        stdout=subprocess.PIPE,
    ).stdout)
    if live_info != source["native_build_info"]:
        issues.append("native_build_info_drift")
    required_build_info = dict(
        frozen_config.get("required_native_build_info") or {}
    )
    if not required_build_info:
        issues.append("required_native_build_info_missing")
    for key, expected in required_build_info.items():
        if live_info.get(key) != expected:
            issues.append(f"required_native_build_info_drift:{key}")
    if source.get("required_native_build_info") != required_build_info:
        issues.append("source_required_native_build_info_binding_drift")
    if live_info.get("frontier_temporal_gat_bundle_schema") != bundle.get(
        "schema_version"
    ):
        issues.append("native_bundle_schema_binding_drift")
    architecture = dict(bundle.get("architecture_contract") or {})
    if architecture != {
        "hidden_size": 32,
        "attention_heads": 4,
        "message_layers": 2,
        "message_encoder_shared_across_resolution_time_and_scale": True,
        "pooling": "type_wise_mean_max_attention_v1",
        "trunk": [128, 64],
        "dropout": 0.1,
    }:
        issues.append("temporal_architecture_contract_drift")
    if dict(bundle.get("ood_policy") or {}) != {
        "kind": "per_feature_fold_train_mean_std_envelope_v1",
        "standard_deviation_radius": 8.0,
        "zero_variance_epsilon": 1.0e-12,
        "action": "MIGRATE_BACK_TO_Q0",
    }:
        issues.append("temporal_ood_policy_contract_drift")
    if (
        runtime.get("allowed_scales") != [30, 50]
        or runtime.get("boundary_by_scale") != bundle.get("boundary_by_scale")
        or runtime.get("trial_pop_budget_by_scale")
            != bundle.get("trial_pop_budget_by_scale")
        or runtime.get("pricing_lifecycle_authority") != "root_cg_only"
        or runtime.get("native_binary_sha256")
            != source.get("native_binary_sha256")
        or runtime.get("source_freeze_sha256") != _sha(args.source_freeze)
        or runtime.get("experiment_config_sha256") != _sha(config_freeze)
    ):
        issues.append("runtime_action_scope_binding_drift")
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_temporal_source_bundle_audit.v1",
        "decision": "FAIL" if issues else "PASS", "issues": issues,
        "source_freeze_sha256": _sha(args.source_freeze),
        "native_binary_sha256": _sha(binary) if binary.is_file() else None,
        "bundle_file_sha256": _sha(args.bundle),
        "runtime_manifest_sha256": _sha(args.runtime_manifest),
        "dataset_sha256": _sha(args.dataset),
        "k_selection_sha256": _sha(args.k_selection),
        "native_differential_sha256": _sha(args.native_differential),
        "training_report_sha256": _sha(args.training_report),
        "artifact_bindings": {
            "source_freeze": {
                "path": str(args.source_freeze.resolve()),
                "sha256": _sha(args.source_freeze),
            },
            "bundle": {
                "path": str(args.bundle.resolve()),
                "sha256": _sha(args.bundle),
            },
            "runtime_manifest": {
                "path": str(args.runtime_manifest.resolve()),
                "sha256": _sha(args.runtime_manifest),
            },
            "dataset": {
                "path": str(args.dataset.resolve()),
                "sha256": _sha(args.dataset),
            },
            "k_selection": {
                "path": str(args.k_selection.resolve()),
                "sha256": _sha(args.k_selection),
            },
            "training_report": {
                "path": str(args.training_report.resolve()),
                "sha256": _sha(args.training_report),
            },
            "native_differential": {
                "path": str(args.native_differential.resolve()),
                "sha256": _sha(args.native_differential),
            },
            "native_binary": {
                "path": str(binary.resolve()),
                "sha256": source["native_binary_sha256"],
            },
            "native_test_binary": {
                "path": str(native_test_binary.resolve()),
                "sha256": source["native_test_binary_sha256"],
            },
            "reference_native_binary": {
                "path": str(Path(source["reference_native_binary"]).resolve()),
                "sha256": source["reference_native_binary_sha256"],
            },
            "selected_exact_config": {
                "path": str(Path(source["selected_exact_config"]).resolve()),
                "sha256": source["selected_exact_config_sha256"],
            },
            "formal_acceptance_contract": {
                "path": str(Path(
                    source["formal_acceptance_contract"]
                ).resolve()),
                "sha256": source["formal_acceptance_contract_sha256"],
            },
            "config_freeze": {
                "path": str(config_freeze.resolve()),
                "sha256": _sha(config_freeze),
            },
            "corpus_manifest": {
                "path": str(Path(source["corpus_manifest"]).resolve()),
                "sha256": source["corpus_manifest_sha256"],
            },
            "protected_history_cache": {
                "path": str(Path(
                    source["protected_history_cache"]
                ).resolve()),
                "sha256": source["protected_history_cache_sha256"],
            },
            **{
                "source:" + relative: {
                    "path": str((ROOT / relative).resolve()),
                    "sha256": expected,
                }
                for relative, expected in sorted(
                    source["source_sha256"].items()
                )
            },
            **{
                f"{partition}_trial_outcomes": row
                for partition, row in sorted(trial_by_partition.items())
            },
            **{
                f"{partition}_trial_schedule": row
                for partition, row in sorted(
                    trial_schedule_bindings.items()
                )
            },
            **({
                "contexts_freeze": {
                    "path": str(canonical_contexts.resolve()),
                    "sha256": _sha(canonical_contexts),
                }
            } if canonical_contexts.is_file() else {}),
        },
        "state_abi_bytes": live_info.get("label_state_bytes"),
        "deployment_authorized": False,
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output.exists() and args.output.read_text(encoding="utf-8") != encoded:
        raise SystemExit("immutable source/bundle audit drift")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not args.output.exists():
        args.output.write_text(encoded, encoding="utf-8")
    if issues:
        mark_terminal_negative(
            args.source_freeze.resolve().parent, stage="SOURCE_BUNDLE_AUDIT",
            reason="TEMPORAL_SOURCE_BINARY_BUNDLE_AUDIT_FAILED",
            detail=payload,
        )
        raise SystemExit("TEMPORAL_SOURCE_BINARY_BUNDLE_AUDIT_FAILED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
