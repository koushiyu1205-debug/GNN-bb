#!/usr/bin/env python3
"""Create a candidate, then activate it only after an immutable canary PASS."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.p0v5_temporal_gat_common import ensure_not_terminal  # noqa: E402
BASELINE_REGISTRY = ROOT / "runs/native_bpc_baseline_registry.json"
PRODUCTION_REGISTRY = ROOT / "runs/production_policy_registry_v2.json"


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_once(path, payload):
    path = Path(path)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable production artifact drift:{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(encoded, encoding="utf-8")


def _atomic(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _require_pass(path, *, formal=False):
    payload = _load(path)
    if formal:
        passed = bool(
            payload.get("final_candidate_gate_pass") and
            payload.get("all_required_evidence_available")
        )
    else:
        passed = str(payload.get("decision") or payload.get("status")) == "PASS"
    if not passed:
        raise SystemExit(f"required promotion evidence is not PASS:{path}")
    return payload


def _require_artifact_bindings(payload, *, label):
    bindings = dict(payload.get("artifact_bindings") or {})
    if not bindings:
        raise SystemExit(f"{label} has no immutable artifact bindings")
    for name, row in bindings.items():
        path = Path(str(dict(row).get("path") or ""))
        expected = str(dict(row).get("sha256") or "")
        if not path.is_file() or _sha(path) != expected:
            raise SystemExit(f"{label} artifact drift:{name}")


def _require_e2e_binding(audit_path, outcomes_path, stage):
    audit = _require_pass(audit_path)
    if str(audit.get("stage")) != stage:
        raise SystemExit(f"{stage} audit stage binding mismatch")
    if str(Path(audit.get("source_outcomes") or "").resolve()) != str(
        outcomes_path.resolve()
    ) or str(audit.get("source_outcomes_sha256") or "") != _sha(outcomes_path):
        raise SystemExit(f"{stage} audit/outcomes hash binding mismatch")
    outcomes = _load(outcomes_path)
    if str(outcomes.get("partition")) != stage:
        raise SystemExit(f"{stage} outcomes partition mismatch")
    return audit, outcomes


def _require_runtime_execution_binding(outcomes, expected_manifest):
    freeze_path = Path(str(outcomes.get("execution_freeze") or "")).resolve()
    if not freeze_path.is_file() or _sha(freeze_path) != str(
        outcomes.get("execution_freeze_sha256") or ""
    ):
        raise SystemExit("E2E execution freeze hash binding mismatch")
    freeze = _load(freeze_path)
    if str(Path(freeze.get("manifest") or "").resolve()) != str(
        expected_manifest.resolve()
    ) or str(freeze.get("manifest_sha256") or "") != _sha(expected_manifest):
        raise SystemExit("E2E runtime manifest binding mismatch")


def _require_process_resource_bindings(payload, *, label):
    rows = list(payload.get("rows") or ())
    if not rows:
        raise SystemExit(f"{label} has no canonical resource rows")
    for row in rows:
        path = Path(str(row.get("process_resource_telemetry") or ""))
        if (
            not path.is_file()
            or _sha(path)
                != str(row.get("process_resource_telemetry_sha256") or "")
            or int(row.get("process_tree_rss_sample_count") or 0) <= 0
            or float(row.get("process_tree_peak_rss_gb") or 0.0) <= 0.0
        ):
            raise SystemExit(f"{label} process-resource telemetry drift")


def _fixed_canary_instances(corpus, development_outcomes):
    corpus_rows = {
        str(row["instance_content_hash"]): dict(row)
        for row in corpus.get("rows") or ()
        if str(row.get("partition")) == "development_e2e"
    }
    selected = {}
    for scale in (30, 50):
        candidates = sorted({
            str(row["instance_hash"])
            for row in development_outcomes.get("rows") or ()
            if int(row.get("scale") or 0) == scale
            and str(row.get("arm")) == "MODEL"
            and bool(row.get("inference_ms_values"))
            and sum(int(value) for value in dict(
                row.get("selected_action_counts") or {}
            ).values()) > 0
        })
        if not candidates:
            raise SystemExit(
                f"scale{scale} has no boundary-reaching development canary"
            )
        instance_hash = candidates[0]
        if instance_hash not in corpus_rows:
            raise SystemExit("development canary is outside frozen corpus")
        row = corpus_rows[instance_hash]
        path = (ROOT / row["path"]).resolve()
        if not path.is_file() or _sha(path) != str(row["file_sha256"]):
            raise SystemExit("fixed canary instance file hash drift")
        selected[str(scale)] = {
            "scale": scale,
            "instance_hash": instance_hash,
            "instance_path": str(path),
            "instance_file_sha256": str(row["file_sha256"]),
            "selection": (
                "lexicographically_first_development_instance_with_model_trial"
            ),
        }
    return selected


def _candidate(args):
    baseline = _load(BASELINE_REGISTRY)
    if baseline.get("production_default_policy") != "no_cut":
        raise SystemExit("historical no_cut production baseline already changed")
    _, development_outcomes = _require_e2e_binding(
        args.development_audit, args.development_outcomes, "development_e2e"
    )
    _, sealed_outcomes = _require_e2e_binding(
        args.sealed_audit, args.sealed_outcomes, "sealed_final"
    )
    _require_process_resource_bindings(
        development_outcomes, label="development_e2e"
    )
    _require_process_resource_bindings(
        sealed_outcomes, label="sealed_final"
    )
    development = _load(args.development_manifest)
    if development.get("deployment_authorized") or development.get(
        "production_switch_authorized"
    ):
        raise SystemExit("development manifest already has unsafe authority")
    bundle = (args.development_manifest.parent /
              development["portable_bundle_path"]).resolve()
    if _sha(bundle) != development["portable_bundle_file_sha256"]:
        raise SystemExit("candidate bundle hash drift")
    _require_runtime_execution_binding(
        development_outcomes, args.development_manifest
    )
    _require_runtime_execution_binding(sealed_outcomes, args.development_manifest)
    formal = _require_pass(args.formal_acceptance, formal=True)
    baseline_sources = list(dict(
        formal.get("baseline_evidence_audit") or {}
    ).get("source_files") or ())
    if not baseline_sources:
        raise SystemExit("formal no_cut baseline bindings are missing")
    for row in baseline_sources:
        path = Path(str(dict(row).get("path") or ""))
        if not path.is_file() or _sha(path) != str(
            dict(row).get("sha256") or ""
        ):
            raise SystemExit("formal no_cut baseline evidence drift")
    if str(formal.get("runtime_manifest_sha256") or "") != _sha(
        args.development_manifest
    ):
        raise SystemExit("formal/runtime manifest binding mismatch")
    formal_execution = Path(str(formal.get("execution_freeze") or ""))
    formal_rows = args.formal_acceptance.resolve().parent / "rows.json"
    if (
        not formal_execution.is_file()
        or _sha(formal_execution)
            != str(formal.get("execution_freeze_sha256") or "")
        or not formal_rows.is_file()
        or _sha(formal_rows) != str(formal.get("formal_rows_sha256") or "")
    ):
        raise SystemExit("formal execution/rows evidence binding mismatch")
    _require_process_resource_bindings(
        _load(formal_rows), label="formal_acceptance"
    )
    source_audit = _require_pass(args.source_binary_bundle_audit)
    _require_artifact_bindings(
        source_audit, label="source_binary_bundle_audit"
    )
    if (
        source_audit.get("bundle_file_sha256") != _sha(bundle)
        or source_audit.get("runtime_manifest_sha256")
            != _sha(args.development_manifest)
    ):
        raise SystemExit("source audit candidate binding mismatch")
    portable = _require_pass(args.portable_parity_audit)
    if (
        portable.get("bundle_file_sha256") != _sha(bundle)
        or portable.get("native_binary_sha256")
            != source_audit.get("native_binary_sha256")
        or int(portable.get("synthetic_graph_count") or -1) != 500
        or int(portable.get("action_mismatch_count") or -1) != 0
        or float(portable.get("maximum_absolute_error") or 0.0) > 1.0e-9
        or float(portable.get("native_inference_p99_ms") or 1.0e100) > 10.0
    ):
        raise SystemExit("portable parity candidate bundle binding mismatch")
    run_root = args.run_root.resolve()
    corpus = _load(args.corpus)
    if str(corpus.get("status")) != "FROZEN_BEFORE_QUEUE_OUTCOMES":
        raise SystemExit("candidate corpus freeze status mismatch")
    canary_instances = _fixed_canary_instances(corpus, development_outcomes)
    production_manifest = dict(development)
    production_manifest.update({
        # This manifest is written in run_root rather than beside the
        # development bundle, so retain an unambiguous immutable path.
        "portable_bundle_path": str(bundle),
        "development_e2e_authorized": True,
        "deployment_authorized": True,
        "production_switch_authorized": False,
        "promotion_stage": "IMMUTABLE_CANDIDATE_AWAITING_CANARY",
    })
    manifest_path = run_root / "runtime_manifest.production_candidate.json"
    _write_once(manifest_path, production_manifest)
    evidence = {
        "development_e2e": {"path": str(args.development_audit.resolve()),
                            "sha256": _sha(args.development_audit)},
        "development_outcomes": {
            "path": str(args.development_outcomes.resolve()),
            "sha256": _sha(args.development_outcomes),
        },
        "sealed_final": {"path": str(args.sealed_audit.resolve()),
                         "sha256": _sha(args.sealed_audit)},
        "sealed_outcomes": {
            "path": str(args.sealed_outcomes.resolve()),
            "sha256": _sha(args.sealed_outcomes),
        },
        "fresh_corpus": {"path": str(args.corpus.resolve()),
                         "sha256": _sha(args.corpus)},
        "formal_acceptance": {"path": str(args.formal_acceptance.resolve()),
                              "sha256": _sha(args.formal_acceptance)},
        "source_binary_bundle": {
            "path": str(args.source_binary_bundle_audit.resolve()),
            "sha256": _sha(args.source_binary_bundle_audit),
        },
        "portable_parity": {"path": str(args.portable_parity_audit.resolve()),
                            "sha256": _sha(args.portable_parity_audit)},
    }
    candidate = {
        "schema_version": "lunar_ice_bpc.production_candidate.v2",
        "candidate_id": (
            "P0V4+V5_TEMPORAL_GAT_V1::" + str(corpus["experiment_id"])
        ),
        "policy_id": "P0V4+V5_TEMPORAL_GAT_V1",
        "status": "CANDIDATE_AWAITING_CANARY",
        "runtime_manifest": str(manifest_path),
        "runtime_manifest_sha256": _sha(manifest_path),
        "bundle": str(bundle), "bundle_sha256": _sha(bundle),
        "evidence": evidence,
        "historical_baseline_registry": str(BASELINE_REGISTRY),
        "historical_baseline_registry_sha256": _sha(BASELINE_REGISTRY),
        "rollback_policy": "no_cut",
        "production_default_changed": False,
    }
    _write_once(run_root / "production_candidate.manifest.json", candidate)
    _write_once(run_root / "canary.execution.freeze.json", {
        "schema_version": "lunar_ice_bpc.temporal_gat_canary_execution.v1",
        "candidate_id": candidate["candidate_id"],
        "runtime_manifest": str(manifest_path),
        "runtime_manifest_sha256": _sha(manifest_path),
        "fixed_instances_by_scale": canary_instances,
        "checks": [
            "bundle_load_hash_binding", "scale30_continue_path",
            "scale50_revert_path", "ood_fail_closed_q0",
            "bundle_mismatch_literal_q0", "monitoring_fields_complete",
        ],
        "production_default_changed": False,
    })
    previous = _load(PRODUCTION_REGISTRY) if PRODUCTION_REGISTRY.is_file() else {
        "schema_version": "lunar_ice_bpc.production_policy_registry.v2",
        "historical_baseline_registry": str(BASELINE_REGISTRY),
        "historical_baseline_registry_sha256": _sha(BASELINE_REGISTRY),
        "active_policy": "no_cut",
        "active_runtime_manifest": "",
        "active_runtime_manifest_sha256": "",
        "rollback_policy": "no_cut",
        "candidates": [],
    }
    if (
        previous.get("schema_version")
            != "lunar_ice_bpc.production_policy_registry.v2"
        or previous.get("historical_baseline_registry_sha256")
            != _sha(BASELINE_REGISTRY)
        or str(previous.get("active_policy") or "no_cut") != "no_cut"
    ):
        raise SystemExit("candidate registration requires the bound no_cut registry")
    registry_entry = {
        "candidate_id": candidate["candidate_id"],
        "status": "AWAITING_CANARY",
        "manifest_path": str(manifest_path),
        "manifest_sha256": _sha(manifest_path),
        "candidate_manifest_path": str(
            run_root / "production_candidate.manifest.json"
        ),
        "candidate_manifest_sha256": _sha(
            run_root / "production_candidate.manifest.json"
        ),
    }
    candidates = list(previous.get("candidates") or ())
    existing = [
        row for row in candidates
        if row.get("candidate_id") == candidate["candidate_id"]
    ]
    if existing and existing != [registry_entry]:
        raise SystemExit("immutable production candidate registry entry drift")
    if not existing:
        candidates.append(registry_entry)
    previous.update({
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "active_policy": "no_cut",
        "active_runtime_manifest": "",
        "active_runtime_manifest_sha256": "",
        "rollback_policy": "no_cut",
        "candidates": candidates,
    })
    _atomic(PRODUCTION_REGISTRY, previous)
    print(json.dumps(candidate, indent=2, sort_keys=True))


def _activate(args):
    run_root = args.run_root.resolve()
    candidate_path = run_root / "production_candidate.manifest.json"
    candidate = _load(candidate_path)
    if (
        candidate.get("historical_baseline_registry_sha256")
        != _sha(BASELINE_REGISTRY)
        or _load(BASELINE_REGISTRY).get("production_default_policy") != "no_cut"
    ):
        raise SystemExit("historical no_cut baseline drift before activation")
    if _sha(Path(candidate["runtime_manifest"])) != candidate[
        "runtime_manifest_sha256"
    ] or _sha(Path(candidate["bundle"])) != candidate["bundle_sha256"]:
        raise SystemExit("candidate runtime/bundle drift before activation")
    for label, evidence in dict(candidate.get("evidence") or {}).items():
        path = Path(str(evidence.get("path") or ""))
        if not path.is_file() or _sha(path) != str(evidence.get("sha256") or ""):
            raise SystemExit(f"candidate evidence drift before activation:{label}")
    source_binding = dict(candidate["evidence"])["source_binary_bundle"]
    _require_artifact_bindings(
        _load(Path(source_binding["path"])),
        label="source_binary_bundle_audit",
    )
    canary = _require_pass(args.canary_audit)
    _require_process_resource_bindings(canary, label="activation_canary")
    expected_canary_path = run_root / "canary/canary.audit.json"
    canary_freeze_path = run_root / "canary.execution.freeze.json"
    if (
        args.canary_audit.resolve() != expected_canary_path
        or not canary_freeze_path.is_file()
        or canary.get("canary_execution_freeze_sha256")
            != _sha(canary_freeze_path)
    ):
        raise SystemExit("canary immutable execution binding mismatch")
    if str(canary.get("candidate_id")) != candidate["candidate_id"]:
        raise SystemExit("canary candidate binding mismatch")
    if str(canary.get("runtime_manifest_sha256")) != candidate[
        "runtime_manifest_sha256"
    ]:
        raise SystemExit("canary runtime manifest binding mismatch")
    candidate_manifest = Path(candidate["runtime_manifest"])
    active_manifest = _load(candidate_manifest)
    active_manifest.update({
        "production_switch_authorized": True,
        "promotion_stage": "PRODUCTION_ACTIVE_WITH_NO_CUT_ROLLBACK",
    })
    active_path = run_root / "runtime_manifest.production_active.json"
    _write_once(active_path, active_manifest)
    if not PRODUCTION_REGISTRY.is_file():
        raise SystemExit("production candidate registry is missing")
    previous = _load(PRODUCTION_REGISTRY)
    if str(previous.get("active_policy") or "no_cut") != "no_cut":
        raise SystemExit("activation refuses to replace a non-no_cut policy")
    candidates = list(previous.get("candidates") or ())
    matches = [
        row for row in candidates
        if row.get("candidate_id") == candidate["candidate_id"]
    ]
    if len(matches) != 1 or matches[0].get("status") != "AWAITING_CANARY":
        raise SystemExit("registered AWAITING_CANARY candidate is missing")
    if (
        matches[0].get("candidate_manifest_sha256") != _sha(candidate_path)
        or matches[0].get("manifest_sha256")
            != candidate["runtime_manifest_sha256"]
    ):
        raise SystemExit("registered candidate binding drift before activation")
    matches[0].update({
        "status": "ACTIVE",
        "manifest_path": str(active_path),
        "manifest_sha256": _sha(active_path),
        "canary_audit_path": str(args.canary_audit.resolve()),
        "canary_audit_sha256": _sha(args.canary_audit),
    })
    previous.update({
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "active_policy": candidate["policy_id"],
        "active_runtime_manifest": str(active_path),
        "active_runtime_manifest_sha256": _sha(active_path),
        "rollback_policy": "no_cut",
        "rollback_historical_registry": str(BASELINE_REGISTRY),
        "rollback_historical_registry_sha256": _sha(BASELINE_REGISTRY),
        "candidates": candidates,
    })
    _atomic(PRODUCTION_REGISTRY, previous)
    print(json.dumps({
        "status": "ACTIVATED", "active_policy": candidate["policy_id"],
        "registry": str(PRODUCTION_REGISTRY), "rollback_policy": "no_cut",
    }, indent=2, sort_keys=True))


def _rollback() -> None:
    if not PRODUCTION_REGISTRY.is_file():
        raise SystemExit("production policy registry does not exist")
    registry = _load(PRODUCTION_REGISTRY)
    if registry.get("historical_baseline_registry_sha256") != _sha(
        BASELINE_REGISTRY
    ):
        raise SystemExit("historical no_cut rollback binding drift")
    candidates = list(registry.get("candidates") or ())
    for row in candidates:
        if row.get("status") == "ACTIVE":
            row["status"] = "ROLLED_BACK_TO_NO_CUT"
    registry.update({
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "active_policy": "no_cut",
        "active_runtime_manifest": "",
        "active_runtime_manifest_sha256": "",
        "rollback_executed": True,
        "candidates": candidates,
    })
    _atomic(PRODUCTION_REGISTRY, registry)
    print(json.dumps({
        "status": "ROLLED_BACK", "active_policy": "no_cut",
        "registry": str(PRODUCTION_REGISTRY),
    }, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("candidate", "activate", "rollback"))
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--development-manifest", type=Path)
    parser.add_argument("--development-audit", type=Path)
    parser.add_argument("--development-outcomes", type=Path)
    parser.add_argument("--sealed-audit", type=Path)
    parser.add_argument("--sealed-outcomes", type=Path)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--formal-acceptance", type=Path)
    parser.add_argument("--source-binary-bundle-audit", type=Path)
    parser.add_argument("--portable-parity-audit", type=Path)
    parser.add_argument("--canary-audit", type=Path)
    args = parser.parse_args()
    if args.mode == "rollback":
        _rollback()
    elif args.mode == "candidate":
        if args.run_root is None:
            raise SystemExit("candidate mode requires --run-root")
        required = (
            args.development_manifest, args.development_audit,
            args.development_outcomes, args.sealed_audit,
            args.sealed_outcomes, args.corpus, args.formal_acceptance,
            args.source_binary_bundle_audit, args.portable_parity_audit,
        )
        if any(value is None for value in required):
            raise SystemExit("candidate mode requires all promotion evidence")
        try:
            ensure_not_terminal(args.run_root)
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc
        _candidate(args)
    else:
        if args.run_root is None:
            raise SystemExit("activate mode requires --run-root")
        if args.canary_audit is None:
            raise SystemExit("activate mode requires immutable canary PASS")
        try:
            ensure_not_terminal(args.run_root)
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc
        _activate(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
