#!/usr/bin/env python3
"""Promote a calibrated GAT only after paired held-out Exact evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
from math import ceil, exp, isfinite, log
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-manifest", required=True)
    parser.add_argument("--paired-results", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--minimum-instances-per-scale", type=int, default=10
    )
    parser.add_argument(
        "--minimum-paired-speedup", type=float, default=0.05
    )
    args = parser.parse_args()

    training_path = _resolve(args.training_manifest)
    results_path = _resolve(args.paired_results)
    output = _resolve(args.output_dir)
    training = _load_json(training_path)
    rows = _load_jsonl(results_path)
    if not bool(training.get("evaluation_authorized")):
        raise SystemExit("training manifest did not authorize evaluation")
    if bool(training.get("deployment_authorized")):
        raise SystemExit("training manifest is already deployment-authorized")
    report = audit_heldout_paired_results(
        rows,
        training_manifest=training,
        expected_training_manifest_sha256=_sha256(training_path),
        require_runtime_binding=True,
        minimum_instances_per_scale=max(
            1, int(args.minimum_instances_per_scale)
        ),
        minimum_paired_speedup=float(args.minimum_paired_speedup),
    )
    promoted = {
        **training,
        "schema_version": (
            "lunar_ice_bpc.two_head_one_deviation_deployment_manifest.v1"
        ),
        "source_training_manifest": str(training_path.resolve()),
        "source_training_manifest_sha256": _sha256(training_path),
        "heldout_paired_results": str(results_path.resolve()),
        "heldout_paired_results_sha256": _sha256(results_path),
        "heldout_evaluation": report,
        "deployment_authorized": bool(report["gate_pass"]),
        "deployment_gate_status": (
            "HELDOUT_END_TO_END_PASS"
            if report["gate_pass"]
            else "HELDOUT_END_TO_END_FAILED"
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    target = output / "deployment_manifest.json"
    _write_json(target, promoted)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["gate_pass"] else 3


def audit_heldout_paired_results(
    rows: list[dict],
    *,
    training_manifest: dict,
    required_scales: tuple[int, ...] = (30, 50),
    minimum_instances_per_scale: int = 10,
    minimum_paired_speedup: float = 0.05,
    maximum_inference_p99_ms: float = 10.0,
    expected_training_manifest_sha256: str = "",
    require_runtime_binding: bool = False,
) -> dict:
    train_or_calibration = {
        str(value)
        for key in (
            "train_instance_hashes",
            "calibration_instance_hashes",
        )
        for value in training_manifest.get(key, ())
    }
    seen: set[tuple[int, str]] = set()
    normalized = []
    for row in rows:
        scale = int(row["scale"])
        instance_hash = str(row["instance_content_hash"])
        key = (scale, instance_hash)
        if key in seen:
            raise ValueError("duplicate held-out scale/instance row")
        seen.add(key)
        if instance_hash in train_or_calibration:
            raise ValueError("held-out instance leaked from model development")
        if require_runtime_binding:
            expected_runtime = dict(
                dict(
                    training_manifest.get(
                        "exact_runtime_bindings_by_scale"
                    )
                    or {}
                ).get(str(scale))
                or {}
            )
            expected_runtime_hash = str(
                expected_runtime.get("runtime_binding_hash") or ""
            )
            if (
                not expected_runtime_hash
                or str(row.get("exact_runtime_binding_hash") or "")
                != expected_runtime_hash
                or str(row.get("fixed_k_selection_sha256") or "")
                != str(
                    training_manifest.get("fixed_k_selection_sha256")
                    or ""
                )
                or str(row.get("training_manifest_sha256") or "")
                != str(expected_training_manifest_sha256)
                or not bool(row.get("candidate_evaluation_mode"))
                or int(row.get("candidate_runtime_error_count") or 0) != 0
            ):
                raise ValueError("held-out Exact/GAT runtime binding mismatch")
        control_time = float(row["control_time_sec"])
        candidate_time = float(row["candidate_time_sec"])
        latencies = [
            float(value)
            for value in row.get("candidate_inference_latencies_ms", ())
        ]
        if any(
            not isfinite(value) or value < 0.0 for value in latencies
        ):
            raise ValueError("invalid held-out inference latency")
        if (
            not isfinite(control_time)
            or not isfinite(candidate_time)
            or control_time <= 0.0
            or candidate_time <= 0.0
        ):
            raise ValueError("invalid held-out solve time")
        normalized.append(
            {
                "scale": scale,
                "instance": instance_hash,
                "control_exact": bool(row["control_exact"]),
                "candidate_exact": bool(row["candidate_exact"]),
                "control_time": control_time,
                "candidate_time": candidate_time,
                "redline_count": int(row.get("redline_count") or 0),
                "inference_latencies_ms": latencies,
            }
        )

    reports = {}
    gate = True
    for scale in required_scales:
        scale_rows = [row for row in normalized if row["scale"] == scale]
        control_exact_count = sum(row["control_exact"] for row in scale_rows)
        candidate_exact_count = sum(
            row["candidate_exact"] for row in scale_rows
        )
        common = [
            row
            for row in scale_rows
            if row["control_exact"] and row["candidate_exact"]
        ]
        geometric_ratio = (
            float("inf")
            if not common
            else exp(
                sum(
                    log(row["candidate_time"] / row["control_time"])
                    for row in common
                )
                / len(common)
            )
        )
        speedup = 1.0 - geometric_ratio
        redlines = sum(row["redline_count"] for row in scale_rows)
        scale_gate = bool(
            len(scale_rows) >= minimum_instances_per_scale
            and len(common) >= minimum_instances_per_scale
            and candidate_exact_count >= control_exact_count
            and speedup >= minimum_paired_speedup
            and redlines == 0
        )
        gate = gate and scale_gate
        reports[str(scale)] = {
            "instance_count": len(scale_rows),
            "commonly_exact_count": len(common),
            "control_exact_count": control_exact_count,
            "candidate_exact_count": candidate_exact_count,
            "paired_geometric_mean_ratio": geometric_ratio,
            "paired_speedup": speedup,
            "correctness_redline_count": redlines,
            "gate_pass": scale_gate,
        }
    ordered_latencies = sorted(
        value
        for row in normalized
        for value in row["inference_latencies_ms"]
    )
    inference_p99_ms = (
        float("inf")
        if not ordered_latencies
        else ordered_latencies[
            max(
                0,
                min(
                    len(ordered_latencies) - 1,
                    ceil(0.99 * len(ordered_latencies)) - 1,
                ),
            )
        ]
    )
    latency_gate = inference_p99_ms <= float(maximum_inference_p99_ms)
    gate = gate and latency_gate
    return {
        "schema_version": (
            "lunar_ice_bpc.one_deviation_heldout_gate.v1"
        ),
        "gate_pass": gate,
        "required_scales": list(required_scales),
        "minimum_instances_per_scale": minimum_instances_per_scale,
        "minimum_paired_speedup": minimum_paired_speedup,
        "maximum_inference_p99_ms": float(maximum_inference_p99_ms),
        "inference_p99_ms": inference_p99_ms,
        "inference_latency_sample_count": len(ordered_latencies),
        "inference_p99_gate_pass": latency_gate,
        "scale_reports": reports,
        "failure_policy": "do_not_authorize_deployment",
    }


def _resolve(value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def _load_json(path: Path) -> dict:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _load_jsonl(path: Path) -> list[dict]:
    return [
        dict(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())
