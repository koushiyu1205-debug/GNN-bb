#!/usr/bin/env python3
"""Freeze the independently audited P0V5 QG2 V4 candidate."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
AUDIT = RUN / "realmap_v4_completion_audit.json"
MANIFEST = RUN / "p0v5_qg2_v4_gat_development_manifest.json"
FORMAL = RUN / "formal_full20_v4_acceptance.json"
E2E = RUN / "development_e2e_v4_acceptance.json"
COMPARISON = RUN / "gat_mlp_linear_comparison_v4.json"
OUTPUT = RUN / "P0V5_QG2_LABEL_STATE_GAT_V4_FINAL_candidate_freeze.json"
ACCEPTANCE_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_realmap_v4_paired_acceptance.v1"
)


def main() -> int:
    evidence = {path: _load_required(path) for path in (
        AUDIT, MANIFEST, FORMAL, E2E, COMPARISON,
    )}
    audit = evidence[AUDIT]
    manifest = evidence[MANIFEST]
    formal = evidence[FORMAL]
    action_universe = _validated_action_universe(manifest)
    audit_binding_errors = _audit_binding_errors(
        audit, (MANIFEST, FORMAL, E2E, COMPARISON)
    )
    if not (
        bool(audit.get("passed"))
        and int(audit.get("error_count") or 0) == 0
        and str(audit.get("formal_result_sha256") or "") == _sha256(FORMAL)
        and str(audit.get("manifest_sha256") or "") == _sha256(MANIFEST)
        and bool(formal.get("passed"))
        and str(formal.get("schema_version") or "") == ACCEPTANCE_SCHEMA
        and str(formal.get("gate_profile") or "") == "v4_positive_net"
        and str(manifest.get("fallback_action") or "") == "Q0"
        and not bool(manifest.get("production_switch_authorized"))
        and not audit_binding_errors
    ):
        raise SystemExit("V4 final candidate evidence is not complete")
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_realmap_v4_final_candidate.v1",
        "candidate_id": "P0V5_QG2_LABEL_STATE_GAT_V4_FINAL",
        "exact_control": "P0V4_V5_BIDIRECTIONAL_EXACT_FINAL_CANDIDATE",
        "learned_action_surface": action_universe,
        "qg2_label_state_arm_status": manifest.get(
            "qg2_label_state_arm_status"
        ),
        "literal_fallback_action": "Q0",
        "allowed_scales": [30, 50],
        "small_scale_model_bypass": [5, 10, 20],
        "ordering_only": True,
        "may_filter_labels": False,
        "may_change_dominance_bound_rc_or_certificate": False,
        "model_order": ["gat", "mlp", "linear"],
        "graph_advantage_supported": bool(
            evidence[COMPARISON].get("graph_advantage_supported")
        ),
        "claim_rule": evidence[COMPARISON].get("claim_rule"),
        "gate_profile": "v4_positive_net",
        "evidence_sha256": {
            str(path.relative_to(ROOT)): _sha256(path) for path in evidence
        },
        "runtime_manifest": str(MANIFEST),
        "runtime_manifest_sha256": _sha256(MANIFEST),
        "production_default_overwritten": False,
        "p0v4_or_p0v5_exact_control_overwritten": False,
        "production_switch_authorized": False,
    }
    if OUTPUT.is_file():
        if _load(OUTPUT) != payload:
            raise SystemExit("V4 final candidate freeze drift")
    else:
        _write(OUTPUT, payload)
    print(json.dumps(payload, sort_keys=True), flush=True)
    return 0


def _validated_action_universe(manifest: dict) -> list[str]:
    actions = list(manifest.get("action_universe") or ())
    if set(actions) not in (
        {"Q0", "QD1", "QB1"},
        {"Q0", "QG2", "QD1", "QB1"},
    ) or len(actions) != len(set(actions)):
        raise SystemExit("V4 final candidate action universe is invalid")
    return actions


def _audit_binding_errors(audit: dict, paths) -> list[str]:
    bindings = dict(audit.get("audited_evidence_sha256") or {})
    tested = dict(audit.get("tested_file_sha256") or {})
    errors = []
    for key, expected in tested.items():
        if key in bindings and str(bindings[key]) != str(expected):
            errors.append(str(key))
        bindings[str(key)] = str(expected)
    for key, expected in sorted(bindings.items()):
        path = ROOT / str(key)
        if not path.is_file() or _sha256(path) != str(expected):
            errors.append(str(key))
    required = {str(Path(path).relative_to(ROOT)) for path in paths}
    errors.extend(sorted(required - set(bindings)))
    return sorted(set(errors))


def _load_required(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"required V4 final evidence missing: {path}")
    return _load(path)


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
