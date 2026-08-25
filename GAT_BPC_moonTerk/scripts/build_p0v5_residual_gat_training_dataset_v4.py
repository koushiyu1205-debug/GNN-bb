#!/usr/bin/env python3
"""Bind censor-aware V4 outcomes to pre-action interaction graphs."""

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
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_gates_v4 import (  # noqa: E402
    CensorAwareContextOutcome,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (  # noqa: E402
    build_interaction_graph,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v4 import (  # noqa: E402
    INTERACTION_DATASET_SCHEMA_V4, V4_ARMS,
)


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_residual_gat_censor_aware_selector_v4_20260815"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    _verify_active(run_root)
    oracle = _load(run_root / "portfolio_oracle.decision.json")
    if not bool(oracle.get("passed")):
        raise SystemExit("V4 portfolio did not authorize selector training")
    outcome_path = args.outcomes.resolve()
    values = []
    for raw in _load(outcome_path)["rows"]:
        row = dict(raw)
        row["correctness_redlines"] = tuple(row.get("correctness_redlines") or ())
        values.append(CensorAwareContextOutcome(**row))
    by_context_arm = {(row.context_id, row.arm): row for row in values}
    masks = _arm_scale_mask(run_root)
    corpus = _load(run_root / "corpus.freeze.json")
    folds = {str(row["instance_hash"]): int(row["fold"])
             for row in _load(run_root / "grouped_cv_folds.freeze.json")["rows"]}
    rows = []
    for context in corpus["rows"]:
        if context["partition"] not in {"train", "calibration"}:
            continue
        snapshot = _load(context["snapshot_path"])
        request = v1._request(context, snapshot)
        features = build_interaction_graph(request)
        targets = {}
        for arm in V4_ARMS:
            outcome = by_context_arm.get((context["context_id"], arm))
            admitted = int(context["scale"]) in masks[arm]
            determined = bool(admitted and outcome is not None and outcome.determined)
            ratio = float(outcome.ratio) if determined else None
            targets[arm] = {
                "admitted_for_scale": admitted, "determined": determined,
                "ratio": ratio, "benefit": bool(determined and ratio <= 0.98),
                "positive_gain": max(0.0, 1.0 - ratio) if determined else 0.0,
                "adverse": bool(outcome is not None and outcome.adverse),
                "resource_censor": bool(
                    outcome is not None and outcome.resource_censor_positive
                ),
                "resource_observed": bool(admitted and outcome is not None),
                "correctness_redlines": list(
                    outcome.correctness_redlines if outcome else ()
                ),
            }
        instance_hash = str(context["instance_content_hash"])
        rows.append({
            "context_id": context["context_id"], "instance_hash": instance_hash,
            "scale": int(context["scale"]), "partition": context["partition"],
            "state_hash": context["state_hash"],
            "context_weight": float(context["context_weight"]),
            "instance_total_weight": 1.0,
            "cv_fold": folds.get(instance_hash) if context["partition"] == "train" else None,
            "features": features.audit_payload(), "targets": targets,
        })
    _validate_weights(rows)
    dataset = {
        "schema_version": INTERACTION_DATASET_SCHEMA_V4,
        "unit": "context_censor_aware_repeats_collapsed_before_instance_fold",
        "instance_balanced_required": True, "instance_total_weight": 1.0,
        "double_censored_excluded_from_benefit_gain_rank": True,
        "double_censored_is_resource_positive": True,
        "selector_heldout_instances_included": False,
        "development_e2e_instances_included": False,
        "formal_outcomes_included": False, "outcome_fields_in_graph": False,
        "probability_calibration_source": "train_oof_predictions_only",
        "corpus_freeze_sha256": _sha256(run_root / "corpus.freeze.json"),
        "split_freeze_sha256": _sha256(run_root / "instance_split.freeze.json"),
        "cv_folds_freeze_sha256": _sha256(run_root / "grouped_cv_folds.freeze.json"),
        "source_outcomes": str(outcome_path),
        "source_outcomes_sha256": _sha256(outcome_path),
        "arm_scale_mask": {arm: sorted(scales) for arm, scales in masks.items()},
        "rows": rows,
    }
    output = args.output.resolve() if args.output else (
        run_root / "interaction_gat_training_dataset.freeze.json"
    )
    _write_once(output, dataset)
    print(json.dumps({
        "output": str(output), "contexts": len(rows),
        "instances": len({row["instance_hash"] for row in rows}),
    }, ensure_ascii=False, indent=2))
    return 0


def _arm_scale_mask(run_root):
    admission = _load(run_root / "qd1_admission.decision.json")
    masks = {"QGR1": set(), "QD1": set()}
    for scale, row in admission["scales"].items():
        if bool(row["admitted"]):
            masks["QD1"].add(int(scale))
    qgr1 = run_root / "qgr1_force_on.decision.json"
    if qgr1.is_file():
        for scale, row in _load(qgr1)["scales"].items():
            if bool(row["admitted"]):
                masks["QGR1"].add(int(scale))
    return masks


def _validate_weights(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(row["instance_hash"], []).append(row)
    for instance, values in grouped.items():
        if abs(sum(float(row["context_weight"]) for row in values) - 1.0) > 1.0e-12:
            raise SystemExit(f"V4 instance weight drift:{instance}")
        if len({row["partition"] for row in values}) != 1:
            raise SystemExit("V4 instance crossed partitions")


def _verify_active(run_root):
    verify_portfolio_freezes(run_root, ROOT)
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal V4 chain forbids dataset writer")


def _write_once(path, payload):
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V4 dataset drift:{path}")
    if not path.exists():
        path.write_text(encoded, encoding="utf-8")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
