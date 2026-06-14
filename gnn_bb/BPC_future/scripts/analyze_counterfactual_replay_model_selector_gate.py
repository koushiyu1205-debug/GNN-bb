#!/usr/bin/env python3
"""Audit simple multifeature selector models on exact replay impact rows.

The script is read-only with respect to solver state.  It reuses the small
calibration models from ``analyze_candidate_selector_models.py`` but applies
them to exact replay impact rows with only addition-before features.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from BPC_future.scripts import analyze_candidate_selector_models as model_lib
from BPC_future.scripts.analyze_counterfactual_replay_selector_gate import (
    DEFAULT_INPUTS,
    _candidate_csv,
    _dataset_name,
)


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_counterfactual_replay_model_selector_gate_20260613"
)
FEATURES = (
    "true_reduced_cost",
    "cost",
    "task_count",
    "vehicle_count",
    "new_task_set_numeric",
    "duplicate_signature_numeric",
    "active_support_changing_numeric",
    "strict_replacement_by_cost_numeric",
    "weak_replacement_or_duplicate_numeric",
)


def _as_bool_number(value: Any) -> str:
    text = str(value).strip().lower()
    return "1.0" if text in {"1", "true", "yes"} else "0.0"


def _read_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw_path in paths:
        path = _candidate_csv(raw_path)
        dataset = _dataset_name(path)
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                if str(row.get("single_treatment_found", "")).lower() not in {
                    "1",
                    "true",
                    "yes",
                }:
                    continue
                row = dict(row)
                row["impact_dataset"] = dataset
                row["new_task_set_numeric"] = _as_bool_number(row.get("new_task_set"))
                row["duplicate_signature_numeric"] = _as_bool_number(
                    row.get("duplicate_signature")
                )
                row["active_support_changing_numeric"] = _as_bool_number(
                    row.get("active_support_changing")
                )
                row["strict_replacement_by_cost_numeric"] = _as_bool_number(
                    row.get("strict_replacement_by_cost")
                )
                row["weak_replacement_or_duplicate_numeric"] = _as_bool_number(
                    row.get("weak_replacement_or_duplicate")
                )
                rows.append(row)
    return rows


def _label(row: dict[str, str]) -> int:
    return 1 if row.get("single_impact_class") == "improved" else 0


def _patch_model_library() -> None:
    model_lib.FEATURES = FEATURES
    model_lib._label = _label


def _strict_gate(models: dict[str, dict[str, Any]]) -> dict[str, Any]:
    passing = {
        name: payload
        for name, payload in models.items()
        if (payload.get("precision") or 0.0) >= 0.75
        and (payload.get("recall") or 0.0) >= 0.5
    }
    return {
        "precision_min": 0.75,
        "recall_min": 0.5,
        "passing_models": sorted(passing),
    }


def _group_summary(rows: list[dict[str, str]], group_key: str) -> dict[str, Any]:
    payload = model_lib._leave_one_group(rows, group_key)
    payload["strict_selector_gate"] = _strict_gate(payload["models"])
    return payload


def analyze_model_selector_gate(paths: list[Path]) -> dict[str, Any]:
    _patch_model_library()
    rows = _read_rows(paths)
    label_counts = dict(Counter(row["single_impact_class"] for row in rows))
    result = {
        "schema_version": "counterfactual_replay_model_selector_gate_v1",
        "input_paths": [str(_candidate_csv(path)) for path in paths],
        "features": {
            "numeric": list(FEATURES),
            "excluded_post_treatment": [
                "single_objective_delta",
                "single_dual_l1_delta",
                "single_changed_journey_count",
            ],
        },
        "row_count": len(rows),
        "label_counts": label_counts,
        "context_count": len({row["context_hash"] for row in rows}),
        "instance_count": len({row["instance"] for row in rows}),
        "impact_dataset_count": len({row["impact_dataset"] for row in rows}),
        "leave_one_context": _group_summary(rows, "context_hash"),
        "leave_one_instance": _group_summary(rows, "instance"),
        "leave_one_dataset": _group_summary(rows, "impact_dataset"),
    }
    lod = result["leave_one_dataset"]["strict_selector_gate"]["passing_models"]
    loi = result["leave_one_instance"]["strict_selector_gate"]["passing_models"]
    loc = result["leave_one_context"]["strict_selector_gate"]["passing_models"]
    result["checks"] = {
        "has_exact_replay_rows": len(rows) >= 200,
        "has_improved_and_noop_labels": (
            int(label_counts.get("improved", 0)) > 0
            and int(label_counts.get("noop", 0)) > 0
        ),
        "context_models_have_passing_candidates": bool(loc),
        "instance_models_have_passing_candidates": bool(loi),
        "dataset_models_fail_strict_gate": not lod,
        "no_model_passes_all_holdout_gates": not (
            set(loc).intersection(loi).intersection(lod)
        ),
        "post_treatment_features_excluded": True,
    }
    result["all_checks_pass"] = (
        result["checks"]["has_exact_replay_rows"]
        and result["checks"]["has_improved_and_noop_labels"]
        and result["checks"]["context_models_have_passing_candidates"]
        and result["checks"]["instance_models_have_passing_candidates"]
        and result["checks"]["dataset_models_fail_strict_gate"]
        and result["checks"]["no_model_passes_all_holdout_gates"]
        and result["checks"]["post_treatment_features_excluded"]
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        default=list(DEFAULT_INPUTS),
        help="candidate_impact_rows.csv files or directories containing them.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    result = analyze_model_selector_gate(list(args.inputs or DEFAULT_INPUTS))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
