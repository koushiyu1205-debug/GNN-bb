#!/usr/bin/env python3
"""Build auditable model-rung metrics from five-fold replay and Stage-B runs.

The candidate-spec JSONL contains one row per consecutively evaluated model:

    {
      "model_kind": "linear",
      "checkpoint_family": "p0v2-linear-cv",
      "stage_b_report": "...json",
      "ha_results_jsonl": "...jsonl",
      "replay_reports": ["fold0...report.json", ..., "fold4...report.json"],
      "parameter_count": 1234,
      "pcgrad_enabled": false
    }

Rows must follow MODEL_LADDER order without skipping a smaller rung.
"""

from __future__ import annotations

import argparse
import json
from math import log
from pathlib import Path
import random
from statistics import mean

from lunar_ice_bpc.guidance.evaluation import paired_runtime_summary
from lunar_ice_bpc.guidance.models import MODEL_LADDER


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-specs-jsonl", required=True)
    parser.add_argument("--p0-results-jsonl", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=5000)
    parser.add_argument("--permutation-samples", type=int, default=20000)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument(
        "--max-replay-inference-mean-sec",
        type=float,
        default=0.05,
    )
    args = parser.parse_args()

    split = _read_json(args.split_manifest)
    if not bool((split.get("audit") or {}).get("passed")):
        raise SystemExit("split manifest audit did not pass")
    split_hash = str(split.get("manifest_hash") or "")
    if not split_hash:
        raise SystemExit("split manifest has no immutable manifest hash")
    development = {
        str(row["instance_content_hash"]): int(row["fold"])
        for row in split.get("development", ())
    }
    if not development:
        raise SystemExit("split manifest has no development rows")
    control = _load_ledger(
        args.p0_results_jsonl, selected_hashes=set(development)
    )
    if set(control) != set(development):
        raise SystemExit("P0 ledger does not cover the full development pool")

    specs = [
        json.loads(line)
        for line in Path(args.candidate_specs_jsonl)
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    if not specs:
        raise SystemExit("no candidate specs")
    kinds = [str(row["model_kind"]) for row in specs]
    expected = list(MODEL_LADDER[: len(kinds)])
    if kinds != expected:
        raise SystemExit(
            "candidate specs must be consecutive smallest-first rungs: "
            + ",".join(expected)
        )

    output_rows = []
    previous_guided = None
    for spec in specs:
        kind = str(spec["model_kind"])
        stage_b = _read_json(spec["stage_b_report"])
        if str(stage_b.get("split_manifest_hash") or "") != split_hash:
            raise SystemExit(f"{kind}: Stage-B split manifest mismatch")
        ha = dict((stage_b.get("variants") or {}).get("HA") or {})
        gate = dict(ha.get("gate") or {})
        checks = dict(gate.get("checks") or {})
        if not checks:
            raise SystemExit(f"{kind}: Stage-B HA gate is missing")
        guided = _load_ledger(
            spec["ha_results_jsonl"], selected_hashes=set(development)
        )
        _audit_guided_ledger(
            guided,
            development=development,
            split_hash=split_hash,
            model_kind=kind,
        )
        if set(guided) != set(control):
            raise SystemExit(f"{kind}: HA/P0 ledgers are not fully paired")
        replay = _audit_replay_reports(
            spec.get("replay_reports") or (),
            split_hash=split_hash,
            fold_count=int(split["fold_count"]),
        )
        inference_mean_max = max(replay["inference_mean_sec_by_fold"].values())
        per_scale = {}
        for scale in (5, 10, 20, 30):
            hashes = [
                content_hash
                for content_hash in sorted(development)
                if int(control[content_hash]["scale"]) == scale
            ]
            per_scale[str(scale)] = paired_runtime_summary(
                [float(control[key]["cold_start_total_sec"]) for key in hashes],
                [float(guided[key]["cold_start_total_sec"]) for key in hashes],
                bootstrap_samples=max(1, int(args.bootstrap_samples)),
                seed=20260723 + scale,
            )
        worst_lcb = min(
            1.0
            - float(
                per_scale[str(scale)][
                    "bootstrap_geometric_mean_ratio_ci95"
                ][1]
            )
            for scale in (5, 10, 20, 30)
        )
        medium_hashes = [
            key
            for key in sorted(development)
            if int(control[key]["scale"]) in {20, 30}
        ]
        medium = paired_runtime_summary(
            [float(control[key]["cold_start_total_sec"]) for key in medium_hashes],
            [float(guided[key]["cold_start_total_sec"]) for key in medium_hashes],
            bootstrap_samples=max(1, int(args.bootstrap_samples)),
            seed=20260743,
        )
        p_value = None
        significantly_better = False
        comparison_mean_log_ratio = None
        if previous_guided is not None:
            deltas = [
                log(
                    float(guided[key]["cold_start_total_sec"])
                    / float(previous_guided[key]["cold_start_total_sec"])
                )
                for key in sorted(development)
            ]
            comparison_mean_log_ratio = mean(deltas)
            p_value = _paired_sign_flip_pvalue(
                deltas,
                samples=max(1, int(args.permutation_samples)),
                seed=20260723 + MODEL_LADDER.index(kind),
            )
            significantly_better = bool(
                comparison_mean_log_ratio < 0.0
                and p_value <= float(args.alpha)
            )
        safety_gate_pass = bool(checks.get("safety_gate"))
        small_scale_pass = bool(
            checks.get("small_p50") and checks.get("small_mean")
        )
        output_rows.append(
            {
                "schema_version": (
                    "lunar_ice_bpc.gat_candidate_metrics.v1"
                ),
                "model_kind": kind,
                "checkpoint_family": str(spec["checkpoint_family"]),
                "split_manifest_hash": split_hash,
                "safety_gate_pass": safety_gate_pass,
                "scale5_10_non_degradation": small_scale_pass,
                "stage_b_gate_pass": bool(gate.get("passed")),
                "inference_overhead_gate_pass": bool(
                    replay["all_legal_universes_preserved"]
                    and inference_mean_max
                    <= float(args.max_replay_inference_mean_sec)
                ),
                "worst_scale_bootstrap_lcb": worst_lcb,
                "scale20_30_end_to_end_gain": (
                    1.0 - float(medium["paired_geometric_mean_ratio"])
                ),
                "guidance_total_wall_sec": float(
                    ha.get("guidance_total_wall_sec_sum") or 0.0
                ),
                "parameter_count": int(spec["parameter_count"]),
                "pcgrad_enabled": bool(spec.get("pcgrad_enabled")),
                "p_value_vs_next_smaller": p_value,
                "significantly_better_than_next_smaller": (
                    significantly_better
                ),
                "mean_log_runtime_ratio_vs_next_smaller": (
                    comparison_mean_log_ratio
                ),
                "runtime_by_scale": per_scale,
                "medium_runtime": medium,
                "replay_inference_mean_sec_by_fold": replay[
                    "inference_mean_sec_by_fold"
                ],
                "stage_b_report": str(
                    Path(spec["stage_b_report"]).resolve()
                ),
                "ha_results_jsonl": str(
                    Path(spec["ha_results_jsonl"]).resolve()
                ),
                "calibration_used": False,
                "protected_final_test_used": False,
            }
        )
        previous_guided = guided

    target = Path(args.output_jsonl)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in output_rows
        ),
        encoding="utf-8",
    )
    report = {
        "schema_version": (
            "lunar_ice_bpc.gat_candidate_metrics_build.v1"
        ),
        "candidate_count": len(output_rows),
        "model_kinds": kinds,
        "split_manifest_hash": split_hash,
        "development_pair_count": len(development),
        "five_fold_replay_required": True,
        "smallest_first_no_skipped_rung": True,
        "calibration_used": False,
        "protected_final_test_used": False,
        "output_jsonl": str(target.resolve()),
    }
    report_path = target.with_suffix(target.suffix + ".report.json")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(str(report_path.resolve()))
    return 0


def _read_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_ledger(
    path: str | Path, *, selected_hashes: set[str]
) -> dict[str, dict]:
    rows = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        content_hash = str(row["instance_content_hash"])
        if content_hash not in selected_hashes:
            continue
        if content_hash in rows:
            raise SystemExit(f"duplicate ledger row: {content_hash}")
        if float(row.get("cold_start_total_sec") or 0.0) <= 0.0:
            raise SystemExit(f"nonpositive runtime: {content_hash}")
        rows[content_hash] = row
    return rows


def _audit_guided_ledger(
    rows: dict[str, dict],
    *,
    development: dict[str, int],
    split_hash: str,
    model_kind: str,
) -> None:
    for content_hash, row in rows.items():
        if str(row.get("split_manifest_hash") or "") != split_hash:
            raise SystemExit(f"{model_kind}: guided split hash mismatch")
        if str(row.get("partition") or "") != "development":
            raise SystemExit(f"{model_kind}: guided non-development row")
        if int(row.get("fold", -1)) != development[content_hash]:
            raise SystemExit(f"{model_kind}: guided fold mismatch")
        if str(row.get("guidance_model_kind") or "") != model_kind:
            raise SystemExit(f"{model_kind}: guided model kind mismatch")
        if not str(row.get("guidance_checkpoint_id") or ""):
            raise SystemExit(f"{model_kind}: guided checkpoint ID missing")


def _audit_replay_reports(
    paths: list[str] | tuple[str, ...],
    *,
    split_hash: str,
    fold_count: int,
) -> dict:
    reports = [_read_json(path) for path in paths]
    folds = {int(row.get("fold", -1)) for row in reports}
    if folds != set(range(fold_count)) or len(reports) != fold_count:
        raise SystemExit("replay reports must cover every fold exactly once")
    inference = {}
    all_legal = True
    for row in reports:
        if str(row.get("split_manifest_hash") or "") != split_hash:
            raise SystemExit("replay split manifest mismatch")
        if bool(row.get("calibration_used")) or bool(
            row.get("protected_final_test_used")
        ):
            raise SystemExit("replay illegally used calibration/protected data")
        all_legal = all_legal and bool(
            row.get("all_legal_universes_preserved")
        )
        rankers = [
            metrics
            for name, metrics in (row.get("ranker_summary") or {}).items()
            if name != "P0_deterministic"
        ]
        if len(rankers) != 1:
            raise SystemExit(
                "each candidate replay report must contain one learned ranker"
            )
        inference[str(int(row["fold"]))] = float(
            rankers[0]["inference_sec_mean"]
        )
    return {
        "all_legal_universes_preserved": all_legal,
        "inference_mean_sec_by_fold": inference,
    }


def _paired_sign_flip_pvalue(
    differences: list[float],
    *,
    samples: int,
    seed: int,
) -> float:
    """One-sided paired randomization p-value for a negative mean."""

    if not differences:
        raise ValueError("paired sign-flip test needs observations")
    observed = mean(float(value) for value in differences)
    rng = random.Random(seed)
    extreme = 0
    for _ in range(max(1, int(samples))):
        permuted = mean(
            value if rng.randrange(2) else -value
            for value in differences
        )
        extreme += permuted <= observed
    return (extreme + 1.0) / (max(1, int(samples)) + 1.0)


if __name__ == "__main__":
    raise SystemExit(main())
