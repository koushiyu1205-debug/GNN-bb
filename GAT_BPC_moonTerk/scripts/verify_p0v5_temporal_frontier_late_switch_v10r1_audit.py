#!/usr/bin/env python3
"""Verify the read-only V10R1 analyzer-correction evidence chain."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT_ROOT = (
    ROOT / "runs/p0v5_temporal_frontier_late_switch_oracle_v10r1_audit_20260818"
)

AUDIT_FILES = (
    "v10_source_import.freeze.json",
    "corrected_collapsed.json",
    "corrected_oracle.decision.json",
    "terminal_decision.json",
    "state.json",
)
IMPLEMENTATION_FILES = (
    "scripts/audit_p0v5_temporal_frontier_late_switch_v10r1.py",
    "scripts/verify_p0v5_temporal_frontier_late_switch_v10r1_audit.py",
    "tests/test_p0v5_temporal_frontier_late_switch_v10r1_audit.py",
    "plan/GAT/P0V5_TEMPORAL_FRONTIER_LATE_SWITCH_V10R1_AUDIT_20260818_ZH.md",
    "plan/GAT/P0V5_TEMPORAL_FRONTIER_LATE_SWITCH_V10R1_CLOSEOUT_20260818_ZH.md",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(audit_root: Path) -> dict:
    audit_root = audit_root.resolve()
    missing = [name for name in AUDIT_FILES if not (audit_root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"missing audit artifact:{missing}")

    imported = load(audit_root / "v10_source_import.freeze.json")
    source_root = Path(imported["source_run_root"])
    for name, expected in imported["source_artifact_sha256"].items():
        path = source_root / name
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"V10 source hash drift:{name}")

    rows = load(audit_root / "corrected_collapsed.json")["rows"]
    decision = load(audit_root / "corrected_oracle.decision.json")
    terminal = load(audit_root / "terminal_decision.json")
    state = load(audit_root / "state.json")
    if len(rows) != 32:
        raise ValueError("corrected collapsed row count drift")
    if any(not row.get("instance_hash") for row in rows):
        raise ValueError("corrected instance identity missing")
    if len({
        row["instance_hash"] for row in rows if int(row["scale"]) == 30
    }) != 8:
        raise ValueError("scale30 instance coverage drift")
    if len({
        row["instance_hash"] for row in rows if int(row["scale"]) == 50
    }) != 8:
        raise ValueError("scale50 instance coverage drift")
    if decision["passing_boundaries"]["30"] != [4096]:
        raise ValueError("scale30 corrected gate drift")
    if decision["passing_boundaries"]["50"] != []:
        raise ValueError("scale50 corrected gate drift")
    if decision["failed_conditions"]["50"]["16384"] != [
        "minimum_strong_benefit_instances"
    ]:
        raise ValueError("scale50 closest-boundary failure drift")
    if not (
        decision["decision"] == "FAIL"
        and decision["reason"] == "SCALE50_LATE_SWITCH_SUPPORT_GATE_FAILED"
        and decision["temporal_gat_training_authorized"] is False
        and terminal["decision"] == "FAIL"
        and terminal["v10_source_terminal_rewritten"] is False
        and state["terminal"] is True
    ):
        raise ValueError("audit terminal contract drift")

    implementation_hashes = {}
    for name in IMPLEMENTATION_FILES:
        path = ROOT / name
        if not path.is_file():
            raise FileNotFoundError(f"missing audit implementation:{name}")
        implementation_hashes[name] = sha256(path)
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_audit_verification.v10r1"
        ),
        "status": "PASS",
        "v10_source_hashes_verified": len(
            imported["source_artifact_sha256"]
        ),
        "audit_artifact_sha256": {
            name: sha256(audit_root / name) for name in AUDIT_FILES
        },
        "audit_implementation_sha256": implementation_hashes,
        "corrected_row_count": len(rows),
        "scale30_instances": 8,
        "scale50_instances": 8,
        "corrected_decision": decision["decision"],
        "corrected_reason": decision["reason"],
        "temporal_gat_training_authorized": False,
        "v10_source_terminal_rewritten": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-root", type=Path, default=DEFAULT_AUDIT_ROOT)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    report = verify(args.audit_root)
    if args.write_report:
        path = args.audit_root / "verification.report.json"
        serialized = json.dumps(
            report, ensure_ascii=False, indent=2, sort_keys=True,
        ) + "\n"
        if path.exists():
            if path.read_text(encoding="utf-8") != serialized:
                raise ValueError("existing verification report drift")
        else:
            path.write_text(serialized, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
