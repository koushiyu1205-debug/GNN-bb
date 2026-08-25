#!/usr/bin/env python3
"""Build the instance-balanced Frontier-GAT V7 train/calibration dataset."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.frontier_gat_qd1_v7 import (  # noqa: E402
    FRONTIER_DATASET_SCHEMA_V1,
    FrontierGraph,
)
from scripts.p0v5_native_frontier_gat_qd1_v7_common import (  # noqa: E402
    DEFAULT_RUN_ROOT,
    assert_active,
    load,
    sha256,
    write_once,
    write_terminal,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    assert_active(run_root, "TRAINING")
    corpus = load(run_root / "main_corpus.freeze.json")
    outcomes = load(run_root / "main_matrix.collapsed.json")
    by_context = {row["context_id"]: row for row in outcomes["rows"]}
    source_rows = [row for row in corpus["rows"]
                   if row["partition"] in {"train", "calibration"}]
    eligible_counts = defaultdict(int)
    for context in source_rows:
        outcome = by_context.get(context["context_id"])
        if outcome and outcome["determined"]:
            eligible_counts[context["instance_content_hash"]] += 1
    train_instances = sorted({
        (int(row["scale"]), row["instance_content_hash"])
        for row in source_rows if row["partition"] == "train"
        and eligible_counts[row["instance_content_hash"]] > 0
    })
    folds = _folds(train_instances)
    rows = []
    for context in source_rows:
        outcome = by_context.get(context["context_id"])
        if not outcome or not outcome["determined"]:
            continue
        graph_payload = outcome.get("qpf0_graph")
        if not graph_payload:
            raise SystemExit("V7 determined outcome lacks QPF0 pre-action graph")
        FrontierGraph.from_native_telemetry(graph_payload)
        instance_hash = context["instance_content_hash"]
        ratio = float(outcome["ratio"])
        rows.append({
            "context_id": context["context_id"], "scale": int(context["scale"]),
            "partition": context["partition"], "instance_hash": instance_hash,
            "state_hash": context["state_hash"],
            "context_weight": 1.0 / eligible_counts[instance_hash],
            "instance_total_weight": 1.0,
            "fold": folds.get(instance_hash),
            "graph": graph_payload,
            "target": {
                "ratio": ratio, "net_ratio": float(outcome["net_ratio"]),
                "benefit": int(ratio <= .98),
                "positive_gain": max(0.0, 1.0 - ratio),
                "adverse": int(bool(outcome["adverse"]) or ratio >= 1.05),
            },
        })
    support = _label_support(rows)
    failures = []
    for scale in (30, 50):
        values = support[str(scale)]
        for field, minimum in (("benefit_positive_instances", 5),
                               ("benefit_negative_instances", 4),
                               ("adverse_or_neutral_instances", 4)):
            if values[field] < minimum:
                failures.append(f"scale{scale}:{field}:{values[field]}<{minimum}")
    if failures:
        write_terminal(run_root, reason="INSUFFICIENT_FRONTIER_GAT_TRAINING_SUPPORT",
                       stage="TRAINING", detail={"label_support": support,
                                                  "failures": failures})
        raise SystemExit("V7 label support gate failed")
    dataset = {
        "schema_version": FRONTIER_DATASET_SCHEMA_V1,
        "source_corpus_sha256": sha256(run_root / "main_corpus.freeze.json"),
        "source_outcomes_sha256": sha256(run_root / "main_matrix.collapsed.json"),
        "instance_balanced": True, "calibration_in_representation_training": False,
        "heldout_e2e_formal_rows": 0, "rows": rows,
        "label_support": support,
    }
    dataset_path = run_root / "frontier_gat_training_dataset.freeze.json"
    write_once(dataset_path, dataset)
    write_once(run_root / "grouped_cv_folds.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_gat_grouped_cv.v1",
        "fold_count": 5, "instance_grouped": True,
        "fold_by_instance": folds,
    })
    write_once(run_root / "training_input.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_gat_training_input.v1",
        "dataset_sha256": sha256(dataset_path),
        "folds_sha256": sha256(run_root / "grouped_cv_folds.freeze.json"),
        "train_instance_count": len(train_instances),
        "calibration_instance_count": len({row["instance_hash"] for row in rows
                                           if row["partition"] == "calibration"}),
    })
    print(json.dumps({"rows": len(rows), "support": support,
                      "status": "READY_FOR_TRAINING"}, ensure_ascii=False, indent=2))
    return 0


def _folds(instances):
    by_scale = defaultdict(list)
    for scale, instance_hash in instances:
        by_scale[scale].append(instance_hash)
    result = {}
    for scale in (30, 50):
        ordered = sorted(by_scale[scale], key=lambda value: hashlib.sha256(
            f"v7-fold:{scale}:{value}".encode()).hexdigest())
        for index, instance_hash in enumerate(ordered):
            result[instance_hash] = index % 5
    return result


def _label_support(rows):
    output = {}
    for scale in (30, 50):
        selected = [row for row in rows if row["partition"] == "train"
                    and int(row["scale"]) == scale]
        by_instance = defaultdict(list)
        for row in selected:
            by_instance[row["instance_hash"]].append(row)
        output[str(scale)] = {
            "train_instances": len(by_instance),
            "benefit_positive_instances": sum(any(row["target"]["benefit"] for row in values)
                                               for values in by_instance.values()),
            "benefit_negative_instances": sum(any(not row["target"]["benefit"] for row in values)
                                               for values in by_instance.values()),
            "adverse_positive_instances": sum(any(row["target"]["adverse"] for row in values)
                                               for values in by_instance.values()),
            "adverse_or_neutral_instances": sum(any(row["target"]["ratio"] > .98 for row in values)
                                                 for values in by_instance.values()),
        }
    return output


if __name__ == "__main__":
    raise SystemExit(main())
