#!/usr/bin/env python3
"""Bind frozen V5 QD1 outcomes to pre-action V6 interaction graphs."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import scripts.build_p0v5_context_queue_portfolio_training_dataset as v1  # noqa: E402
from scripts.p0v5_minimal_interaction_gat_qd1_v6_common import (  # noqa: E402
    DEFAULT_RUN_ROOT, assert_active, load, sha256, update_state,
    verify_freezes, write_once,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (  # noqa: E402
    build_interaction_graph,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v6 import (  # noqa: E402
    INTERACTION_DATASET_SCHEMA_V6,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    assert_active(run_root)
    verify_freezes(run_root)
    state = load(run_root / "state.json")
    if state.get("current_stage") != "DATASET_BUILD":
        raise SystemExit("V6 dataset writer is not authorized in current stage")

    evidence = load(run_root / "v5_qd1_evidence_import.freeze.json")
    v5_root = Path(str(evidence["v5_run_root"]))
    outcomes = {
        str(row["context_id"]): dict(row)
        for row in load(v5_root / "matched_qd1_collapsed.json")["rows"]
    }
    milestone = load(v5_root / "q0_milestone.freeze.json")["by_context"]
    folds = {
        str(row["instance_hash"]): int(row["fold"])
        for row in load(run_root / "grouped_cv_folds.freeze.json")["rows"]
    }
    corpus = load(run_root / "corpus.freeze.json")
    eligible = []
    for context in corpus["rows"]:
        if context["partition"] not in {"train", "calibration"}:
            continue
        marker = milestone.get(str(context["context_id"]))
        if not marker or not bool(marker.get("replay_eligible")):
            continue
        outcome = outcomes.get(str(context["context_id"]))
        if not outcome or not bool(outcome.get("determined")):
            raise SystemExit("V6_V5_EVIDENCE_IMPORT_DRIFT:eligible outcome missing")
        eligible.append((dict(context), outcome))

    grouped = defaultdict(list)
    for context, outcome in eligible:
        grouped[(context["partition"], context["instance_content_hash"])].append(
            (context, outcome)
        )
    rows = []
    for (_, instance_hash), values in sorted(grouped.items()):
        v6_weight = 1.0 / len(values)
        for context, outcome in sorted(values, key=lambda value: value[0]["context_id"]):
            snapshot = load(context["snapshot_path"])
            request = v1._request(context, snapshot)
            features = build_interaction_graph(request)
            ratio = float(outcome["ratio"])
            adverse = bool(
                outcome.get("adverse") or ratio >= 1.05
                or int(outcome.get("q0_complete_arm_censored_blocks") or 0) > 0
            )
            rows.append({
                "context_id": context["context_id"],
                "instance_hash": instance_hash,
                "scale": int(context["scale"]),
                "partition": context["partition"],
                "state_hash": context["state_hash"],
                "source_context_weight": float(context["context_weight"]),
                "training_context_weight": v6_weight,
                "instance_total_weight": 1.0,
                "cv_fold": (
                    folds[instance_hash] if context["partition"] == "train" else None
                ),
                "features": features.audit_payload(),
                "target": {
                    "determined": True,
                    "ratio": ratio,
                    "benefit": ratio <= 0.98,
                    "positive_gain": max(0.0, 1.0 - ratio),
                    "adverse": adverse,
                    "resource_censor": bool(
                        outcome.get("resource_censor_positive")
                    ),
                    "resource_failure_folded_into_adverse": bool(
                        outcome.get("resource_censor_positive")
                    ),
                    "q0_complete_qd1_censored_blocks": int(
                        outcome.get("q0_complete_arm_censored_blocks") or 0
                    ),
                    "correctness_redlines": list(
                        outcome.get("correctness_redlines") or ()
                    ),
                },
            })
    _validate_rows(rows)
    label_support = _label_support(rows)
    for scale in (30, 50):
        row = label_support[str(scale)]
        requirements = {
            "benefit_positive_instances": 3,
            "benefit_negative_instances": 3,
            "adverse_positive_instances": 2,
            "adverse_negative_instances": 3,
        }
        failed = {
            key: {"observed": int(row[key]), "required": required}
            for key, required in requirements.items() if int(row[key]) < required
        }
        if failed:
            raise SystemExit(
                "INSUFFICIENT_QD1_LABEL_SUPPORT:"
                + json.dumps({"scale": scale, "failed": failed}, sort_keys=True)
            )
    dataset = {
        "schema_version": INTERACTION_DATASET_SCHEMA_V6,
        "unit": "eligible_context_with_instance_total_weight_one",
        "instance_balanced_required": True,
        "benefit_threshold": 0.98,
        "adverse_threshold": 1.05,
        "resource_censor_head_present": False,
        "resource_censor_folded_into_adverse": True,
        "resource_failure_rows": sum(
            bool(row["target"]["resource_failure_folded_into_adverse"])
            for row in rows
        ),
        "selector_heldout_instances_included": False,
        "development_e2e_instances_included": False,
        "formal_outcomes_included": False,
        "outcome_fields_in_graph": False,
        "probability_calibration_source": "train_oof_predictions_by_scale_only",
        "evidence_import_sha256": sha256(
            run_root / "v5_qd1_evidence_import.freeze.json"
        ),
        "corpus_freeze_sha256": sha256(run_root / "corpus.freeze.json"),
        "split_freeze_sha256": sha256(run_root / "instance_split.freeze.json"),
        "cv_folds_freeze_sha256": sha256(
            run_root / "grouped_cv_folds.freeze.json"
        ),
        "source_outcomes": str(
            (v5_root / "matched_qd1_collapsed.json").resolve()
        ),
        "source_outcomes_sha256": sha256(
            v5_root / "matched_qd1_collapsed.json"
        ),
        "action_universe": ["Q0", "QD1"],
        "label_support": label_support,
        "rows": rows,
    }
    output = (
        args.output.resolve() if args.output
        else run_root / "interaction_gat_qd1_training_dataset.freeze.json"
    )
    write_once(output, dataset)
    write_once(run_root / "training_input.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_interaction_gat_qd1_training_input.v1",
        "dataset_path": str(output), "dataset_sha256": sha256(output),
        "frozen_before_optimizer": True,
        "train_contexts": sum(row["partition"] == "train" for row in rows),
        "calibration_contexts": sum(
            row["partition"] == "calibration" for row in rows
        ),
        "train_instances": len({
            row["instance_hash"] for row in rows if row["partition"] == "train"
        }),
        "calibration_instances": len({
            row["instance_hash"] for row in rows
            if row["partition"] == "calibration"
        }),
    })
    update_state(run_root, "SELECTOR_TRAINING", "READY")
    print(json.dumps({
        "output": str(output), "contexts": len(rows),
        "train_contexts": sum(row["partition"] == "train" for row in rows),
        "calibration_contexts": sum(
            row["partition"] == "calibration" for row in rows
        ),
        "instances": len({row["instance_hash"] for row in rows}),
        "label_support": label_support,
    }, ensure_ascii=False, indent=2))
    return 0


def _validate_rows(rows):
    grouped = defaultdict(list)
    for row in rows:
        if row["target"]["correctness_redlines"]:
            raise SystemExit("V6 correctness redline in imported outcome")
        # V5 has one determined calibration row where Q0 completed and QD1
        # censored in all three blocks.  V6 has no separately calibratable
        # resource head; the frozen contract folds this failure into adverse.
        if bool(row["target"]["resource_censor"]) and (
            not bool(row["target"]["adverse"])
            or int(row["target"]["q0_complete_qd1_censored_blocks"]) <= 0
        ):
            raise SystemExit("V6 resource failure was not folded into adverse")
        grouped[(row["partition"], row["instance_hash"])].append(row)
    if len(rows) != 74:
        raise SystemExit(f"V6 dataset count drift:{len(rows)}")
    partitions = defaultdict(set)
    for (partition, instance), values in grouped.items():
        partitions[instance].add(partition)
        if abs(sum(row["training_context_weight"] for row in values) - 1.0) > 1e-12:
            raise SystemExit(f"V6 instance weight drift:{instance}")
    if any(len(values) != 1 for values in partitions.values()):
        raise SystemExit("V6 instance crossed dataset partitions")


def _label_support(rows):
    result = {}
    for scale in (30, 50):
        selected = [
            row for row in rows
            if row["partition"] == "train" and row["scale"] == scale
        ]
        result[str(scale)] = {
            "contexts": len(selected),
            "instances": len({row["instance_hash"] for row in selected}),
            "benefit_positive_instances": len({
                row["instance_hash"] for row in selected if row["target"]["benefit"]
            }),
            "benefit_negative_instances": len({
                row["instance_hash"] for row in selected if not row["target"]["benefit"]
            }),
            "adverse_positive_instances": len({
                row["instance_hash"] for row in selected if row["target"]["adverse"]
            }),
            "adverse_negative_instances": len({
                row["instance_hash"] for row in selected if not row["target"]["adverse"]
            }),
        }
    return result


if __name__ == "__main__":
    raise SystemExit(main())
