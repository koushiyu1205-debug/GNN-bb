#!/usr/bin/env python3
"""Merge arm-specific matched controls into one collapsed V2 outcome matrix."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    collapse_matched_matrix,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--qgr1", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal chain forbids outcome merge")
    config = _load(run_root / "config.freeze.json")
    base_path = args.base.resolve()
    qgr1_path = args.qgr1.resolve()
    base_payload = _load(base_path)
    qgr1_payload = _load(qgr1_path)
    kwargs = {
        "caps_by_scale": config["execution"]["replay_caps_sec"],
        "required_repeats": config["execution"]["blocked_fresh_process_repeats"],
    }
    base = collapse_matched_matrix(base_payload["rows"], **kwargs)
    qgr1 = collapse_matched_matrix(qgr1_payload["rows"], **kwargs)
    if {row.arm for row in base} != {"QD1", "QB1"}:
        raise SystemExit("V2 base outcome matrix is not QD1/QB1")
    if {row.arm for row in qgr1} != {"QGR1"}:
        raise SystemExit("V2 residual outcome matrix is not QGR1")
    base_contexts = {row.context_id for row in base}
    qgr1_contexts = {row.context_id for row in qgr1}
    if base_contexts != qgr1_contexts:
        raise SystemExit("V2 QGR1 full matrix context universe mismatch")
    rows = tuple((*base, *qgr1))
    redlines = sorted({
        value for row in rows for value in row.correctness_redlines
    })
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_collapsed_outcome_bundle.v2",
        "unit": "context_arm_with_arm_specific_fresh_q0_control",
        "repeat_rows_are_not_independent_samples": True,
        "base_source": str(base_path),
        "base_source_sha256": _sha256(base_path),
        "qgr1_source": str(qgr1_path),
        "qgr1_source_sha256": _sha256(qgr1_path),
        "correctness_redlines": redlines,
        "rows": [asdict(row) for row in sorted(
            rows, key=lambda row: (row.scale, row.context_id, row.arm)
        )],
        "mechanism_summary": _mechanism_summary(
            (*base_payload["rows"], *qgr1_payload["rows"])
        ),
    }
    output = args.output.resolve() if args.output else run_root / "portfolio_collapsed_outcomes.json"
    _write_once(output, payload)
    _update_state(run_root, "PORTFOLIO_ORACLE", "READY")
    print(json.dumps({
        "output": str(output),
        "collapsed_context_arm_count": len(rows),
        "correctness_redlines": redlines,
    }, ensure_ascii=False, indent=2))
    return 0


def _mechanism_summary(rows):
    result = {}
    for arm in ("Q0", "QD1", "QB1", "QGR1"):
        selected = [row for row in rows if str(row["arm"]) == arm]
        result[arm] = {
            "repeat_rows": len(selected),
            "median_solver_wall_sec": _median(selected, "solver_wall_sec"),
            "median_processed_labels": _median(selected, "processed_labels"),
            "median_dominance_candidate_checks": _median(selected, "dominance_candidate_checks"),
            "median_dominance_wall_sec": _median(selected, "dominance_wall_sec"),
            "median_ordering_decisions": _median(selected, "ordering_decisions"),
            "median_native_scoring_wall_sec": _median(selected, "native_scoring_wall_sec"),
        }
    return result


def _median(rows, field):
    values = [float(row.get(field) or 0.0) for row in rows]
    return statistics.median(values) if values else None


def _update_state(run_root, stage, status):
    path = run_root / "state.json"
    payload = _load(path)
    payload.update({"current_stage": stage, "status": status})
    path.write_text(json.dumps(
        payload, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n", encoding="utf-8")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable V2 outcome merge drift:{path}")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
