#!/usr/bin/env python3
"""Run and audit frozen matched end-to-end proof-tail policy pairs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import subprocess
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SCHEMA = "lunar_ice_bpc.proof_tail_e2e_pair_manifest.v2"
BOOTSTRAP_SEED = 20260724
BOOTSTRAP_REPLICATES = 20_000


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _quantile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("quantile requires at least one value")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * float(probability)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + fraction * (
        ordered[upper] - ordered[lower]
    )


def _validate_manifest(
    manifest_path: Path,
) -> tuple[dict[str, Any], str]:
    payload = _load_json(manifest_path)
    if payload.get("schema_version") != EXPECTED_SCHEMA:
        raise SystemExit("unsupported proof-tail E2E manifest schema")
    if payload.get("allowed_partition") != "development":
        raise SystemExit("proof-tail discovery accepts development only")
    if payload.get("calibration_used") or payload.get(
        "protected_final_test_used"
    ):
        raise SystemExit("calibration/protected evidence is forbidden")
    if payload.get("selection_uses_qc0_qd1_outcomes"):
        raise SystemExit("outcome-selected sentinel manifest is forbidden")
    if not payload.get("selection_frozen_before_this_batch_outcomes"):
        raise SystemExit("sentinel selection must be frozen before outcomes")
    if int(payload.get("workers") or 0) != 1:
        raise SystemExit("proof-tail E2E sentinel must run one worker")

    split_path = ROOT / str(payload["split_manifest"])
    split = _load_json(split_path)
    if not bool((split.get("audit") or {}).get("passed")):
        raise SystemExit("split manifest audit did not pass")
    if split.get("manifest_hash") != payload.get("split_manifest_hash"):
        raise SystemExit("split manifest hash mismatch")
    development_by_hash = {
        str(row["instance_content_hash"]): row
        for row in split.get("development", ())
    }

    source_path = ROOT / str(payload["selection_source_manifest"])
    source = _load_json(source_path)
    if source.get("manifest_hash") != payload.get(
        "selection_source_manifest_hash"
    ):
        raise SystemExit("source sentinel manifest hash mismatch")
    if source.get("split_manifest_hash") != payload.get(
        "split_manifest_hash"
    ):
        raise SystemExit("source sentinel split hash mismatch")
    if source.get("calibration_used"):
        raise SystemExit("source sentinel used calibration")
    source_by_hash = {
        str(row["instance_content_hash"]): row
        for row in source.get("instances", ())
    }

    difficulty_by_hash: dict[str, str] = {}
    records_path = ROOT / (
        "data/gat_p0v2/development_instance_records_with_b0.jsonl"
    )
    for row in _load_jsonl(records_path):
        difficulty_by_hash[str(row["instance_content_hash"])] = str(
            row["p0_difficulty_bin"]
        )

    instance_manifest = _load_json(
        ROOT / "data/gat_p0v2/development_instances_manifest.json"
    )
    instance_by_hash = {
        str(row["instance_content_hash"]): row
        for row in instance_manifest.get("instances", ())
    }

    pairs = list(payload.get("pairs") or ())
    if not pairs:
        raise SystemExit("sentinel manifest contains no pairs")
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    order_counts = {
        ("control", "candidate"): 0,
        ("candidate", "control"): 0,
    }
    excluded = {
        int(value) for value in payload.get("excluded_prior_e2e_indices", ())
    }
    for pair in pairs:
        pair_id = str(pair.get("pair_id") or "")
        content_hash = str(pair.get("instance_content_hash") or "")
        instance_id = str(pair.get("instance_id") or "")
        index = int(pair.get("index") or 0)
        order = tuple(str(value) for value in pair.get("run_order", ()))
        if not pair_id or pair_id in seen_ids:
            raise SystemExit("pair IDs must be non-empty and unique")
        if not content_hash or content_hash in seen_hashes:
            raise SystemExit("pair content hashes must be non-empty and unique")
        if int(pair.get("scale") or 0) != 30:
            raise SystemExit("batch1 proof-tail sentinel accepts scale30 only")
        if index in excluded:
            raise SystemExit("prior inspected E2E instance entered sentinel")
        if order not in order_counts:
            raise SystemExit("invalid matched pair run order")
        order_counts[order] += 1
        seen_ids.add(pair_id)
        seen_hashes.add(content_hash)

        split_row = development_by_hash.get(content_hash)
        source_row = source_by_hash.get(content_hash)
        instance_row = instance_by_hash.get(content_hash)
        if split_row is None or source_row is None or instance_row is None:
            raise SystemExit(f"{pair_id}: instance is not development-backed")
        if not bool(source_row.get("selected")):
            raise SystemExit(f"{pair_id}: source sentinel did not select row")
        if str(source_row.get("instance_id")) != instance_id:
            raise SystemExit(f"{pair_id}: source sentinel instance mismatch")
        if str(split_row.get("instance_id")) != instance_id:
            raise SystemExit(f"{pair_id}: split instance mismatch")
        if int(instance_row.get("index") or 0) != index:
            raise SystemExit(f"{pair_id}: development index mismatch")
        if str(pair.get("p0_difficulty_bin")) != difficulty_by_hash.get(
            content_hash
        ):
            raise SystemExit(f"{pair_id}: frozen difficulty-bin mismatch")
        if not math.isclose(
            float(pair.get("selection_uniform")),
            float(source_row.get("selection_uniform")),
            rel_tol=0.0,
            abs_tol=5e-10,
        ):
            raise SystemExit(f"{pair_id}: selection key mismatch")

    if abs(order_counts[("control", "candidate")] - order_counts[
        ("candidate", "control")
    ]) > 1:
        raise SystemExit("matched run orders are not balanced")

    control_config = _load_yaml(ROOT / str(payload["control_config"]))
    candidate_config = _load_yaml(ROOT / str(payload["candidate_config"]))
    allowed_differences = {
        "model_id",
        "native_proof_queue_experiment_policy",
    }
    all_keys = set(control_config) | set(candidate_config)
    unexpected = [
        key
        for key in sorted(all_keys)
        if key not in allowed_differences
        and control_config.get(key) != candidate_config.get(key)
    ]
    if unexpected:
        raise SystemExit(
            "control/candidate config mismatch outside policy: "
            + ",".join(unexpected)
        )
    if control_config.get("native_proof_queue_experiment_policy") != "off":
        raise SystemExit("control config is not Q0")
    if candidate_config.get(
        "native_proof_queue_experiment_policy"
    ) != payload.get("candidate_rule"):
        raise SystemExit("candidate rule/config mismatch")

    manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    return payload, manifest_hash


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise SystemExit(f"invalid YAML object: {path}")
    return loaded


def _result_for_hash(
    results_path: Path,
    content_hash: str,
) -> dict[str, Any] | None:
    for row in _load_jsonl(results_path):
        if str(row.get("instance_content_hash")) == content_hash:
            return row
    return None


def _safety_passed(row: dict[str, Any]) -> bool:
    safety = row.get("stage_b_safety") or {}
    return bool(row.get("redlines_zero")) and all(
        (
            int(safety.get("binding_mismatch_accepted") or 0) == 0,
            int(safety.get("guidance_induced_permanent_drop") or 0) == 0,
            not bool(safety.get("labels_dropped")),
            int(safety.get("legal_universe_hash_mismatch") or 0) == 0,
            int(safety.get("nonfinite_hint_accepted") or 0) == 0,
        )
    )


def _build_audit(
    manifest: dict[str, Any],
    manifest_hash: str,
    output_root: Path,
) -> dict[str, Any]:
    pair_rows: list[dict[str, Any]] = []
    ratios: list[float] = []
    log_ratios: list[float] = []
    rss_ratios: list[float] = []
    ratios_by_stratum: dict[str, list[float]] = {}
    all_arms_complete = True
    all_exact_equal = True
    safety_failure_count = 0
    extra_incomplete = 0
    candidate_peak_rss_max = 0

    for pair in manifest["pairs"]:
        arms: dict[str, dict[str, Any] | None] = {}
        for arm in ("control", "candidate"):
            results_path = (
                output_root / pair["pair_id"] / arm / "results.jsonl"
            )
            arms[arm] = _result_for_hash(
                results_path,
                str(pair["instance_content_hash"]),
            )
        control = arms["control"]
        candidate = arms["candidate"]
        complete = control is not None and candidate is not None
        all_arms_complete = all_arms_complete and complete
        row: dict[str, Any] = {
            "pair_id": pair["pair_id"],
            "p0_difficulty_bin": pair["p0_difficulty_bin"],
            "index": pair["index"],
            "instance_content_hash": pair["instance_content_hash"],
            "run_order": pair["run_order"],
            "arms_complete": complete,
        }
        if not complete:
            all_exact_equal = False
            pair_rows.append(row)
            continue

        assert control is not None and candidate is not None
        control_exact = (
            control.get("algorithm_status") == "BPC_OPTIMAL"
            and bool(control.get("bpc_tree_optimal"))
        )
        candidate_exact = (
            candidate.get("algorithm_status") == "BPC_OPTIMAL"
            and bool(candidate.get("bpc_tree_optimal"))
        )
        objective_equal = (
            control_exact
            and candidate_exact
            and math.isclose(
                float(control.get("global_ub")),
                float(candidate.get("global_ub")),
                rel_tol=0.0,
                abs_tol=1e-9,
            )
        )
        all_exact_equal = all_exact_equal and objective_equal
        if control_exact and not candidate_exact:
            extra_incomplete += 1
        control_safety = _safety_passed(control)
        candidate_safety = _safety_passed(candidate)
        safety_failure_count += int(not control_safety)
        safety_failure_count += int(not candidate_safety)

        control_wall = float(control["cold_start_total_sec"])
        candidate_wall = float(candidate["cold_start_total_sec"])
        ratio = candidate_wall / control_wall
        if objective_equal:
            ratios.append(ratio)
            log_ratios.append(math.log(ratio))
            ratios_by_stratum.setdefault(
                str(pair["p0_difficulty_bin"]),
                [],
            ).append(ratio)
        control_rss = int(control.get("process_tree_rss_peak_bytes") or 0)
        candidate_rss = int(candidate.get("process_tree_rss_peak_bytes") or 0)
        candidate_peak_rss_max = max(candidate_peak_rss_max, candidate_rss)
        if control_rss > 0:
            rss_ratios.append(candidate_rss / control_rss)
        row.update(
            {
                "control_status": control.get("algorithm_status"),
                "candidate_status": candidate.get("algorithm_status"),
                "exact_objective_equal": objective_equal,
                "global_ub_control": control.get("global_ub"),
                "global_ub_candidate": candidate.get("global_ub"),
                "control_wall_sec": control_wall,
                "candidate_wall_sec": candidate_wall,
                "candidate_over_control_wall_ratio": ratio,
                "control_peak_rss_bytes": control_rss,
                "candidate_peak_rss_bytes": candidate_rss,
                "candidate_over_control_peak_rss_ratio": (
                    None if control_rss <= 0 else candidate_rss / control_rss
                ),
                "control_safety_passed": control_safety,
                "candidate_safety_passed": candidate_safety,
            }
        )
        pair_rows.append(row)

    bootstrap_lcb = None
    bootstrap_ucb = None
    if log_ratios:
        rng = random.Random(BOOTSTRAP_SEED)
        means = [
            statistics.fmean(
                rng.choice(log_ratios) for _ in range(len(log_ratios))
            )
            for _ in range(BOOTSTRAP_REPLICATES)
        ]
        bootstrap_lcb = _quantile(means, 0.025)
        bootstrap_ucb = _quantile(means, 0.975)

    gate = manifest["primary_gate"]
    evaluable = all_arms_complete and len(ratios) == len(pair_rows)
    geometric_mean = (
        None if not log_ratios else math.exp(statistics.fmean(log_ratios))
    )
    median_ratio = None if not ratios else statistics.median(ratios)
    worst_ratio = None if not ratios else max(ratios)
    rss_ratio_p90 = None if not rss_ratios else _quantile(rss_ratios, 0.90)
    stratum_geometric_means = {
        stratum: math.exp(
            statistics.fmean(math.log(value) for value in values)
        )
        for stratum, values in sorted(ratios_by_stratum.items())
        if values
    }
    stratum_limits = {
        str(key): float(value)
        for key, value in (
            gate.get("stratum_geometric_mean_wall_ratio_max") or {}
        ).items()
    }
    checks = {
        "all_arms_complete": all_arms_complete,
        "exact_objective_and_certificate_equal": all_exact_equal,
        "extra_incomplete_passed": extra_incomplete
        <= int(gate["extra_incomplete_allowed"]),
        "geometric_mean_passed": geometric_mean is not None
        and geometric_mean
        <= float(gate["paired_geometric_mean_wall_ratio_max"]),
        "median_passed": median_ratio is not None
        and median_ratio <= float(gate["paired_median_wall_ratio_max"]),
        "bootstrap_ucb_passed": bootstrap_ucb is not None
        and bootstrap_ucb
        <= float(gate["paired_log_ratio_bootstrap_ucb95_max"]),
        "worst_instance_passed": worst_ratio is not None
        and worst_ratio <= float(gate["worst_instance_wall_ratio_max"]),
        "rss_ratio_p90_passed": rss_ratio_p90 is not None
        and rss_ratio_p90 <= float(gate["candidate_peak_rss_ratio_p90_max"]),
        "rss_absolute_passed": candidate_peak_rss_max
        <= int(gate["candidate_peak_rss_absolute_max_bytes"]),
        "safety_passed": safety_failure_count
        <= int(gate["safety_redline_count_max"]),
    }
    if stratum_limits:
        checks["stratum_geometric_means_passed"] = all(
            stratum in stratum_geometric_means
            and stratum_geometric_means[stratum] <= limit
            for stratum, limit in stratum_limits.items()
        )
    return {
        "schema_version": "lunar_ice_bpc.proof_tail_e2e_pair_audit.v1",
        "experiment_id": manifest["experiment_id"],
        "manifest_sha256": manifest_hash,
        "evidence_scope": manifest["evidence_scope"],
        "production_policy_changed": False,
        "pair_count": len(pair_rows),
        "completed_pair_count": sum(
            bool(row["arms_complete"]) for row in pair_rows
        ),
        "exact_comparable_pair_count": len(ratios),
        "extra_incomplete_count": extra_incomplete,
        "safety_failure_count": safety_failure_count,
        "paired_geometric_mean_wall_ratio": geometric_mean,
        "paired_median_wall_ratio": median_ratio,
        "paired_worst_wall_ratio": worst_ratio,
        "paired_log_ratio_bootstrap_lcb95": bootstrap_lcb,
        "paired_log_ratio_bootstrap_ucb95": bootstrap_ucb,
        "candidate_peak_rss_ratio_p90": rss_ratio_p90,
        "candidate_peak_rss_absolute_max_bytes": candidate_peak_rss_max,
        "stratum_geometric_mean_wall_ratios": stratum_geometric_means,
        "promotion_evaluable": evaluable,
        "promotion_passed": evaluable and all(checks.values()),
        "gate_checks": checks,
        "pairs": pair_rows,
    }


def _write_audit(output_root: Path, audit: dict[str, Any]) -> None:
    path = output_root / "paired_gate_audit.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Force recomputation; default resumes completed arms.",
    )
    args = parser.parse_args()

    manifest_path = (ROOT / args.manifest).resolve()
    output_root = (ROOT / args.output_dir).resolve()
    manifest, manifest_hash = _validate_manifest(manifest_path)
    if args.validate_only:
        print(
            json.dumps(
                {
                    "status": "VALID",
                    "manifest_sha256": manifest_hash,
                    "pair_count": len(manifest["pairs"]),
                },
                sort_keys=True,
            )
        )
        return 0

    output_root.mkdir(parents=True, exist_ok=True)
    frozen_copy = output_root / "frozen_pair_manifest.json"
    if frozen_copy.exists():
        frozen_hash = hashlib.sha256(frozen_copy.read_bytes()).hexdigest()
        if frozen_hash != manifest_hash:
            raise SystemExit("output directory is bound to another manifest")
    else:
        frozen_copy.write_bytes(manifest_path.read_bytes())
    _write_audit(
        output_root,
        _build_audit(manifest, manifest_hash, output_root),
    )

    for pair in manifest["pairs"]:
        for arm in pair["run_order"]:
            arm_root = output_root / pair["pair_id"] / arm
            results_path = arm_root / "results.jsonl"
            command = [
                sys.executable,
                str(ROOT / "scripts" / "run_p0v2_gat_b0_development.py"),
                "--config",
                str(ROOT / manifest[f"{arm}_config"]),
                "--output-dir",
                str(arm_root),
                "--results-jsonl",
                str(results_path),
                "--scales",
                "30",
                "--indices",
                str(pair["index"]),
                "--split-manifest",
                str(ROOT / manifest["split_manifest"]),
                "--partition",
                "development",
                "--workers",
                "1",
                "--outer-timeout-sec",
                str(manifest["outer_time_limit_sec"]),
                "--experiment-variant",
                "P0_Q0_3600"
                if arm == "control"
                else "SCALE30_QD1_ELSE_Q0_3600",
            ]
            if args.fresh:
                command.append("--no-resume")
            print(
                f"START pair={pair['pair_id']} index={pair['index']:03d} "
                f"arm={arm}",
                flush=True,
            )
            completed = subprocess.run(command, cwd=ROOT, check=False)
            audit = _build_audit(manifest, manifest_hash, output_root)
            _write_audit(output_root, audit)
            if completed.returncode != 0:
                raise SystemExit(
                    f"arm failed closed with return code "
                    f"{completed.returncode}: {pair['pair_id']} {arm}"
                )
            result = _result_for_hash(
                results_path,
                str(pair["instance_content_hash"]),
            )
            if result is None:
                raise SystemExit(
                    f"arm produced no auditable result: {pair['pair_id']} {arm}"
                )
            if not _safety_passed(result):
                raise SystemExit(
                    f"arm failed safety gate: {pair['pair_id']} {arm}"
                )
            print(
                f"DONE pair={pair['pair_id']} arm={arm} "
                f"status={result.get('algorithm_status')} "
                f"wall={result.get('cold_start_total_sec')}",
                flush=True,
            )

    final_audit = _build_audit(manifest, manifest_hash, output_root)
    _write_audit(output_root, final_audit)
    print(json.dumps(final_audit, sort_keys=True))
    return 0 if final_audit["safety_failure_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
