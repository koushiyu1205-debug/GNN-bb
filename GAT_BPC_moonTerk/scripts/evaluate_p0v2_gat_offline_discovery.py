#!/usr/bin/env python3
"""Fail-closed offline gate before any P0 V2 online H/HA experiment."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from statistics import mean

from lunar_ice_bpc.guidance.tensorization import (
    HARVEST_MODEL_CONTEXT_SCHEMA_V2,
    learned_harvest_context,
)


EXPECTED_FOLDS = frozenset(range(5))
EXPECTED_KINDS = ("linear", "mlp2x32")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pricing-replay-dir", required=True)
    parser.add_argument("--harvest-replay-dir", required=True)
    parser.add_argument("--records-jsonl", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    split = json.loads(
        Path(args.split_manifest).read_text(encoding="utf-8")
    )
    if not bool((split.get("audit") or {}).get("passed")):
        raise SystemExit("split manifest audit did not pass")
    manifest_hash = str(split.get("manifest_hash") or "")
    development_hashes = {
        str(row["instance_content_hash"])
        for row in split.get("development", ())
    }
    forbidden_hashes = {
        str(row["instance_content_hash"])
        for partition in ("calibration", "protected_final_test")
        for row in split.get(partition, ())
    }

    pricing = _load_report_matrix(
        Path(args.pricing_replay_dir),
        expected_schema="lunar_ice_bpc.gat_snapshot_model_replay.v1",
        manifest_hash=manifest_hash,
    )
    harvest = _load_report_matrix(
        Path(args.harvest_replay_dir),
        expected_schema="lunar_ice_bpc.gat_harvest_row_replay.v1",
        manifest_hash=manifest_hash,
    )
    leakage = _audit_harvest_target_leakage(
        Path(args.records_jsonl),
        development_hashes=development_hashes,
        forbidden_hashes=forbidden_hashes,
    )

    by_kind = {}
    eligible = []
    for kind in EXPECTED_KINDS:
        pricing_reports = [pricing[(kind, fold)] for fold in range(5)]
        harvest_reports = [harvest[(kind, fold)] for fold in range(5)]
        pricing_aggregate = _aggregate_pricing(pricing_reports)
        harvest_aggregate = _aggregate_harvest(harvest_reports)
        blockers = []
        if not all(
            bool(row.get("all_legal_universes_preserved"))
            for row in (*pricing_reports, *harvest_reports)
        ):
            blockers.append("legal_universe_mismatch")
        if not all(
            bool(row.get("selector_exact_replay"))
            for row in harvest_reports
        ):
            blockers.append("legacy_v1_harvest_selector_context")
        if bool(leakage["learned_input_direct_target_leakage"]):
            blockers.append("harvest_target_is_direct_input_feature")
        if not all(
            str(
                report.get("harvest_model_context_schema_version") or ""
            )
            == HARVEST_MODEL_CONTEXT_SCHEMA_V2
            for report in harvest_reports
        ):
            blockers.append("obsolete_harvest_model_context_schema")
        if (
            pricing_aggregate["learned_top5_recall_weighted_mean"]
            <= pricing_aggregate["p0_top5_recall_weighted_mean"]
        ):
            blockers.append("task_arc_top5_recall_not_better_than_p0")
        if any(
            learned > p0
            for learned, p0 in zip(
                pricing_aggregate["learned_first_rank_p50_by_fold"],
                pricing_aggregate["p0_first_rank_p50_by_fold"],
                strict=True,
            )
        ):
            blockers.append("task_arc_first_rank_regressed")
        if blockers:
            decision = "blocked"
        else:
            decision = "offline_signal_only_requires_online_stage_b"
            eligible.append(kind)
        by_kind[kind] = {
            "decision": decision,
            "blockers": blockers,
            "pricing_preordering": pricing_aggregate,
            "harvest_preordering": harvest_aggregate,
        }

    report = {
        "schema_version": "lunar_ice_bpc.gat_offline_discovery_gate.v1",
        "split_manifest_hash": manifest_hash,
        "partition": "development_cross_validation_only",
        "calibration_used": False,
        "protected_final_test_used": False,
        "target_leakage_audit": leakage,
        "model_results": by_kind,
        "eligible_model_kinds": eligible,
        "passed": bool(eligible),
        "online_h_authorized": False,
        "online_ha_authorized": False,
        "gat_training_authorized": False,
        "proof_queue_online_authorized": False,
        "branch_online_authorized": False,
        "decision": (
            "BLOCKED_OFFLINE_SIGNAL_NO_ONLINE_STAGE_B"
            if not eligible
            else "OFFLINE_SIGNAL_REQUIRES_SEPARATE_ONLINE_STAGE_B"
        ),
        "required_next_actions": (
            [
                (
                    "Use v2 harvest rows whose context records "
                    "is_new_task_set consistently online and offline."
                ),
                (
                    "Keep deterministic selector facts masked from learned "
                    "input; redesign the harvest target around a downstream "
                    "outcome if further discovery is attempted."
                ),
                (
                    "Do not train a GAT or run online H/HA while linear and "
                    "MLP remain below P0 on fivefold task/arc replay."
                ),
            ]
            if not eligible
            else []
        ),
        "notes": [
            (
                "The raw factual context contains the grade-4 rule, but "
                "composite feature v3 masks it before every model forward."
            ),
            (
                "No online run, deployment manifest, full80 evaluation, or "
                "protected scale50/100 evaluation is authorized by this file."
            ),
        ],
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(str(target.resolve()))
    return 0


def _load_report_matrix(
    root: Path, *, expected_schema: str, manifest_hash: str
) -> dict[tuple[str, int], dict]:
    matrix = {}
    for path in sorted(root.glob("*.report.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        if str(report.get("schema_version") or "") != expected_schema:
            continue
        if str(report.get("split_manifest_hash") or "") != manifest_hash:
            raise SystemExit(f"replay split mismatch: {path}")
        if bool(report.get("calibration_used")) or bool(
            report.get("protected_final_test_used")
        ):
            raise SystemExit(f"forbidden partition used by replay: {path}")
        learned_rankers = [
            key
            for key in (report.get("ranker_summary") or {})
            if key != "P0_deterministic"
        ]
        if len(learned_rankers) != 1:
            raise SystemExit(
                f"replay report must contain one learned ranker: {path}"
            )
        learned_ranker = learned_rankers[0]
        kind = str(report.get("model_kind") or "")
        if not kind:
            if "-linear-" in learned_ranker:
                kind = "linear"
            elif "-mlp2x32-" in learned_ranker:
                kind = "mlp2x32"
        fold = int(report.get("fold", -1))
        key = (kind, fold)
        if kind not in EXPECTED_KINDS or fold not in EXPECTED_FOLDS:
            continue
        if key in matrix:
            raise SystemExit(f"duplicate replay report for {key}")
        matrix[key] = report
    expected = {
        (kind, fold)
        for kind in EXPECTED_KINDS
        for fold in EXPECTED_FOLDS
    }
    if set(matrix) != expected:
        raise SystemExit(
            f"incomplete replay matrix: missing={sorted(expected - set(matrix))}"
        )
    return matrix


def _audit_harvest_target_leakage(
    path: Path,
    *,
    development_hashes: set[str],
    forbidden_hashes: set[str],
) -> dict:
    candidate_count = 0
    raw_mismatch_count = 0
    learned_input_mismatch_count = 0
    context_count = 0
    v1_context_count = 0
    v2_context_count = 0
    for line in path.open(encoding="utf-8"):
        if not line.strip():
            continue
        row = json.loads(line)
        if str(row.get("head") or "") != "harvest":
            continue
        content_hash = str(row["instance_content_hash"])
        if content_hash in forbidden_hashes:
            raise SystemExit(
                f"forbidden harvest training row present: {content_hash}"
            )
        if content_hash not in development_hashes:
            raise SystemExit(
                f"non-development harvest row present: {content_hash}"
            )
        context_count += 1
        if str(row.get("schema_version") or "").endswith(".v2"):
            v2_context_count += 1
        else:
            v1_context_count += 1
        grades = list(row.get("harvest_grades") or ())
        contexts = list(row.get("harvest_context") or ())
        if len(grades) != len(contexts):
            raise SystemExit("harvest grade/context length mismatch")
        for grade, context in zip(grades, contexts, strict=True):
            candidate_count += 1
            direct_prediction = (
                float(grade) >= 3.0
                and len(context) > 1
                and float(context[1]) > 0.5
            )
            if direct_prediction != (float(grade) >= 4.0):
                raw_mismatch_count += 1
            learned = learned_harvest_context(context)
            learned_input_prediction = (
                float(grade) >= 3.0 and learned[1] > 0.5
            )
            if learned_input_prediction != (float(grade) >= 4.0):
                learned_input_mismatch_count += 1
    if candidate_count == 0:
        raise SystemExit("no harvest candidates for leakage audit")
    return {
        "context_count": context_count,
        "candidate_count": candidate_count,
        "v1_context_count": v1_context_count,
        "v2_context_count": v2_context_count,
        "rule": (
            "grade>=4 iff grade>=3 and "
            "harvest_context[1]=would_change_active_support"
        ),
        "raw_context_mismatch_count": raw_mismatch_count,
        "raw_context_match_rate": (
            1.0 - raw_mismatch_count / candidate_count
        ),
        "raw_context_direct_target_leakage": raw_mismatch_count == 0,
        "learned_model_context_schema_version": (
            HARVEST_MODEL_CONTEXT_SCHEMA_V2
        ),
        "learned_input_mismatch_count": learned_input_mismatch_count,
        "learned_input_match_rate": (
            1.0 - learned_input_mismatch_count / candidate_count
        ),
        "learned_input_direct_target_leakage": (
            learned_input_mismatch_count == 0
        ),
    }


def _aggregate_pricing(reports: list[dict]) -> dict:
    p0 = [
        report["ranker_summary"]["P0_deterministic"]
        for report in reports
    ]
    learned = [
        _learned_summary(report)
        for report in reports
    ]
    return {
        "context_count": sum(int(row["context_count"]) for row in learned),
        "p0_first_rank_p50_by_fold": [
            float(row["first_observed_negative_candidate_rank_p50"])
            for row in p0
        ],
        "learned_first_rank_p50_by_fold": [
            float(row["first_observed_negative_candidate_rank_p50"])
            for row in learned
        ],
        "p0_top5_recall_weighted_mean": _weighted_mean(
            p0, "observed_top5_recall_mean"
        ),
        "learned_top5_recall_weighted_mean": _weighted_mean(
            learned, "observed_top5_recall_mean"
        ),
        "learned_inference_sec_weighted_mean": _weighted_mean(
            learned, "inference_sec_mean"
        ),
    }


def _aggregate_harvest(reports: list[dict]) -> dict:
    p0 = [
        report["ranker_summary"]["P0_deterministic"]
        for report in reports
    ]
    learned = [
        _learned_summary(report)
        for report in reports
    ]
    return {
        "context_count": sum(int(row["context_count"]) for row in learned),
        "informative_context_count": sum(
            int(row["informative_grade_context_count"])
            for row in learned
        ),
        "selector_exact_replay": all(
            bool(report["selector_exact_replay"]) for report in reports
        ),
        "p0_informative_first_useful_rank_mean": _weighted_mean(
            p0,
            "informative_first_useful_rank_mean",
            weight_key="informative_grade_context_count",
        ),
        "learned_informative_first_useful_rank_mean": _weighted_mean(
            learned,
            "informative_first_useful_rank_mean",
            weight_key="informative_grade_context_count",
        ),
        "p0_graded_ndcg_at_5_weighted_mean": _weighted_mean(
            p0, "graded_ndcg_at_5_mean"
        ),
        "learned_graded_ndcg_at_5_weighted_mean": _weighted_mean(
            learned, "graded_ndcg_at_5_mean"
        ),
        "learned_inference_sec_weighted_mean": _weighted_mean(
            learned, "inference_sec_mean"
        ),
    }


def _weighted_mean(
    rows: list[dict], value_key: str, *, weight_key: str = "context_count"
) -> float:
    weighted = [
        (
            float(row[value_key]),
            int(row[weight_key]),
        )
        for row in rows
        if row.get(value_key) is not None and int(row[weight_key]) > 0
    ]
    if not weighted:
        raise ValueError(f"no weighted values for {value_key}")
    return sum(value * weight for value, weight in weighted) / sum(
        weight for _, weight in weighted
    )


def _learned_summary(report: dict) -> dict:
    learned = [
        row
        for ranker, row in report["ranker_summary"].items()
        if ranker != "P0_deterministic"
    ]
    if len(learned) != 1:
        raise ValueError("expected exactly one learned ranker summary")
    return learned[0]


if __name__ == "__main__":
    raise SystemExit(main())
