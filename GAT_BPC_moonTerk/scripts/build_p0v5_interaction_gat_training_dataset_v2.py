#!/usr/bin/env python3
"""Bind collapsed fresh arm outcomes to V2 pre-action interaction graphs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import scripts.build_p0v5_context_queue_portfolio_training_dataset as v1  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import verify_portfolio_freezes  # noqa: E402
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    MatchedContextOutcome,
    collapse_matched_matrix,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_v1 import PORTFOLIO_ARMS  # noqa: E402
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import build_interaction_graph  # noqa: E402


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_interaction_gat_queue_selector_v2_20260807"
DATASET_SCHEMA = "lunar_ice_bpc.p0v5_interaction_gat_training_dataset.v2"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    state = _load(run_root / "state.json")
    if bool(state.get("terminal")):
        raise SystemExit("terminal chain forbids training dataset writer")
    config = _load(run_root / "config.freeze.json")
    corpus = _load(run_root / "corpus.freeze.json")
    admission = _load(run_root / "qgr1_force_on.decision.json")["decision"]
    masks = {
        str(arm): {int(value) for value in scales}
        for arm, scales in dict(admission["arm_scale_mask"]).items()
    }
    outcome_path = args.outcomes.resolve()
    outcome_payload = _load(outcome_path)
    if outcome_payload.get("schema_version") == (
        "lunar_ice_bpc.p0v5_interaction_gat_collapsed_outcome_bundle.v2"
    ):
        values = []
        for raw in outcome_payload["rows"]:
            row = dict(raw)
            row["correctness_redlines"] = tuple(row.get("correctness_redlines") or ())
            values.append(MatchedContextOutcome(**row))
        outcomes = tuple(values)
    else:
        outcomes = collapse_matched_matrix(
            outcome_payload["rows"],
            caps_by_scale=config["execution"]["replay_caps_sec"],
            required_repeats=config["execution"]["blocked_fresh_process_repeats"],
        )
    by_context_arm = {(row.context_id, row.arm): row for row in outcomes}
    rows = []
    for context in corpus["rows"]:
        if context["partition"] not in {"train", "calibration"}:
            continue
        snapshot = _load(Path(context["snapshot_path"]))
        request = v1._request(context, snapshot)
        if request.pricing_lifecycle_scope != "root_cg":
            raise SystemExit("V2 training corpus contains non-root context")
        features = build_interaction_graph(request)
        targets = {}
        for arm in PORTFOLIO_ARMS:
            outcome = by_context_arm.get((context["context_id"], arm))
            admitted = int(context["scale"]) in masks.get(arm, set())
            determined = bool(admitted and outcome is not None and outcome.determined)
            ratio = float(outcome.ratio) if determined else None
            targets[arm] = {
                "admitted_for_scale": admitted,
                "determined": determined,
                "ratio": ratio,
                "benefit": bool(determined and ratio <= 0.98),
                "positive_gain": max(0.0, 1.0 - ratio) if determined else 0.0,
                "adverse": bool(outcome is not None and outcome.adverse),
                "correctness_redlines": list(outcome.correctness_redlines) if outcome else [],
            }
        rows.append({
            "context_id": context["context_id"],
            "instance_hash": context["instance_content_hash"],
            "scale": context["scale"],
            "partition": context["partition"],
            "state_hash": context["state_hash"],
            "features": features.audit_payload(),
            "targets": targets,
        })
    payload = {
        "schema_version": DATASET_SCHEMA,
        "unit": "context_with_three_repeats_already_collapsed",
        "instance_balanced_required": True,
        "selector_heldout_outcomes_included": False,
        "formal_outcomes_included": False,
        "outcome_fields_in_graph": False,
        "corpus_freeze_sha256": _sha256(run_root / "corpus.freeze.json"),
        "source_outcomes": str(outcome_path),
        "source_outcomes_sha256": _sha256(outcome_path),
        "arm_scale_mask": {arm: sorted(scales) for arm, scales in masks.items()},
        "rows": rows,
    }
    output = args.output.resolve() if args.output else run_root / "interaction_gat_training_dataset.freeze.json"
    _write_once(output, payload)
    print(json.dumps({
        "output": str(output), "context_count": len(rows),
        "instance_count": len({row["instance_hash"] for row in rows}),
    }, ensure_ascii=False, indent=2))
    return 0


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable V2 dataset drift:{path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
