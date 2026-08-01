#!/usr/bin/env python3
"""Summarize the frozen scale20/011 ng-DSSR V3 development gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, median


DEFAULT_NEIGHBORHOODS = (6, 10, 14, 20)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path(
            "runs/ng_dssr_v3_development_20260729"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "runs/ng_dssr_v3_development_20260729/"
            "scale20_011_summary.json"
        ),
    )
    parser.add_argument(
        "--neighborhoods",
        nargs="+",
        type=int,
        default=list(DEFAULT_NEIGHBORHOODS),
    )
    parser.add_argument(
        "--max-wall-ratio",
        type=float,
        default=1.10,
    )
    parser.add_argument(
        "--p0-differential-dir",
        type=Path,
        default=Path(
            "runs/ng_dssr_v3_development_20260729/"
            "p0_compile_gate_final_differential"
        ),
    )
    return parser.parse_args()


def _exact_closed(row: dict) -> bool:
    return bool(
        row.get("engine_status") == "COMPLETE"
        and row.get("search_exhaustive")
        and row.get("frontier_empty")
        and not row.get("labels_dropped")
        and row.get("can_enter_certificate_audit")
    )


def main() -> int:
    args = parse_args()
    rows = []
    for neighborhood_size in args.neighborhoods:
        final_path = (
            args.input_dir
            / f"scale20_011_final_k{neighborhood_size}"
            / "replay.json"
        )
        current_path = (
            args.input_dir
            / f"scale20_011_current_k{neighborhood_size}"
            / "replay.json"
        )
        historical_path = (
            args.input_dir
            / f"scale20_011_k{neighborhood_size}"
            / "replay.json"
        )
        if final_path.exists():
            path = final_path
        elif current_path.exists():
            path = current_path
        else:
            path = historical_path
        payload = json.loads(path.read_text(encoding="utf-8"))
        p0 = dict(payload["p0"])
        candidate = dict(payload["dssr"])
        telemetry = dict(candidate.get("telemetry") or {})
        p0_wall = float(p0["elapsed_wall_sec"])
        candidate_wall = float(candidate["elapsed_wall_sec"])
        exact_closed = _exact_closed(candidate)
        relaxation_effective = bool(
            int(
                telemetry.get("ng_dssr_initial_relation_count")
                or 0
            )
            < int(payload["scale"]) ** 2
        )
        wall_ratio = candidate_wall / p0_wall
        safety_pass = bool(
            payload["audit"]["both_bindings_match"]
            and payload["audit"]["both_labels_dropped_zero"]
            and (
                not exact_closed
                or payload["audit"][
                    "dssr_returns_audited_negative_or_exact_certificate"
                ]
            )
        )
        gate_pass = bool(
            safety_pass
            and relaxation_effective
            and exact_closed
            and wall_ratio <= float(args.max_wall_ratio)
        )
        rows.append(
            {
                "neighborhood_size": neighborhood_size,
                "role": (
                    "full_elementary_structural_control"
                    if not relaxation_effective
                    else "ng_dssr_candidate"
                ),
                "relaxation_effective": relaxation_effective,
                "p0_wall_sec": p0_wall,
                "candidate_wall_sec": candidate_wall,
                "wall_ratio_or_censored_lower_bound": wall_ratio,
                "candidate_status": candidate["engine_status"],
                "candidate_exact_closed": exact_closed,
                "candidate_certificate": bool(
                    candidate["can_enter_certificate_audit"]
                ),
                "labels_dropped": bool(
                    candidate["labels_dropped"]
                ),
                "safety_pass": safety_pass,
                "scale20_011_gate_pass": gate_pass,
                "processed_labels": telemetry.get(
                    "processed_labels"
                ),
                "extended_labels": telemetry.get(
                    "extended_labels"
                ),
                "max_bucket_size": telemetry.get(
                    "dssr_max_bucket_size"
                ),
                "dominance_candidate_checks": telemetry.get(
                    "dssr_dominance_candidate_checks"
                ),
                "initial_relation_count": telemetry.get(
                    "ng_dssr_initial_relation_count"
                ),
                "final_relation_count": telemetry.get(
                    "ng_dssr_final_relation_count"
                ),
                "refinement_count": telemetry.get(
                    "dssr_refinement_count"
                ),
                "peak_rss_bytes": telemetry.get(
                    "host_peak_rss_bytes"
                ),
                "source_replay": str(path),
            }
        )

    qualifying = [
        row for row in rows if row["scale20_011_gate_pass"]
    ]
    current_engine_evidence: dict = {
        "status": "UNAVAILABLE",
    }
    try:
        import lunar_spprc_native
        from lunar_ice_bpc.exact.bpc.pricing.spprc_pricer import (
            spprc_engine_build_hash,
        )

        backend_ids = {
            json.loads(
                Path(row["source_replay"]).read_text(
                    encoding="utf-8"
                )
            )[key]["backend_id"]
            for row in rows
            for key in ("p0", "dssr")
        }
        current_engine_evidence = {
            "status": "COMPLETE",
            "engine_hashes": {
                backend_id: spprc_engine_build_hash(backend_id)
                for backend_id in sorted(backend_ids)
            },
            "native_build_info": dict(
                lunar_spprc_native.build_info()
            ),
            "all_final_replay_bindings_match": all(
                json.loads(
                    Path(row["source_replay"]).read_text(
                        encoding="utf-8"
                    )
                )["audit"]["both_bindings_match"]
                for row in rows
            ),
        }
    except (ImportError, OSError, KeyError, ValueError):
        pass

    p0_compile_gate = {
        "status": "NOT_AVAILABLE",
        "pass": False,
    }
    old_paths = sorted(args.p0_differential_dir.glob("old_*.json"))
    off_paths = sorted(args.p0_differential_dir.glob("off_*.json"))
    if old_paths and len(old_paths) == len(off_paths):
        old_payloads = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in old_paths
        ]
        off_payloads = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in off_paths
        ]
        old_host = [
            float(payload["p0"]["elapsed_wall_sec"])
            for payload in old_payloads
        ]
        off_host = [
            float(payload["p0"]["elapsed_wall_sec"])
            for payload in off_payloads
        ]
        old_native = [
            float(
                payload["p0"]["telemetry"]["wall_time_seconds"]
            )
            for payload in old_payloads
        ]
        off_native = [
            float(
                payload["p0"]["telemetry"]["wall_time_seconds"]
            )
            for payload in off_payloads
        ]
        exact_semantics_match = all(
            _exact_closed(old["p0"])
            and _exact_closed(off["p0"])
            and old["p0"]["column_count"]
            == off["p0"]["column_count"]
            and old["p0"]["telemetry"]["processed_labels"]
            == off["p0"]["telemetry"]["processed_labels"]
            and old["p0"]["telemetry"]["extended_labels"]
            == off["p0"]["telemetry"]["extended_labels"]
            for old, off in zip(old_payloads, off_payloads)
        )
        host_ratio = mean(off_host) / mean(old_host)
        native_ratio = mean(off_native) / mean(old_native)
        p0_compile_gate = {
            "status": "COMPLETE",
            "trial_count": len(old_paths),
            "old_build_host_wall_sec": old_host,
            "ng_disabled_build_host_wall_sec": off_host,
            "old_build_native_wall_sec": old_native,
            "ng_disabled_build_native_wall_sec": off_native,
            "old_build_host_mean_sec": mean(old_host),
            "ng_disabled_build_host_mean_sec": mean(off_host),
            "old_build_host_median_sec": median(old_host),
            "ng_disabled_build_host_median_sec": median(off_host),
            "host_mean_ratio": host_ratio,
            "native_mean_ratio": native_ratio,
            "exact_semantics_match": exact_semantics_match,
            "max_non_regression_ratio": 1.02,
            "pass": bool(
                exact_semantics_match
                and host_ratio <= 1.02
                and native_ratio <= 1.02
            ),
            "source_directory": str(args.p0_differential_dir),
        }

    output = {
        "schema_version": (
            "lunar_ice_bpc.ng_dssr_v3_sentinel_gate.v1"
        ),
        "source_instance_id": (
            "lunar_ice_sp50_020_011_seed829011"
        ),
        "source_instance_content_hash": "99fe0d93672e1dc9",
        "max_wall_ratio": float(args.max_wall_ratio),
        "candidate_neighborhoods": [
            value
            for value in args.neighborhoods
            if value < 20
        ],
        "structural_control_neighborhood": 20,
        "rows": rows,
        "qualifying_candidate_count": len(qualifying),
        "promotion_allowed": bool(qualifying),
        "scale30_validation_allowed": bool(qualifying),
        "six_scale_validation_allowed": bool(qualifying),
        "p0_compile_gate": p0_compile_gate,
        "current_engine_evidence": current_engine_evidence,
        "conclusion": (
            "continue_to_scale30"
            if qualifying
            else "terminate_ng_dssr_v3_before_scale30"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
