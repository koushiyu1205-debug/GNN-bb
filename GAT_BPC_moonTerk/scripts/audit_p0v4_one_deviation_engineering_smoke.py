#!/usr/bin/env python3
"""Audit a bounded, non-trainable one-deviation signal pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean, median
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.one_deviation_oracle import (  # noqa: E402
    materialize_one_deviation_time_labels,
)


REDLINE_KEYS = (
    "correctness_redline_count",
    "hash_redline_count",
    "leakage_redline_count",
    "candidate_filter_redline_count",
    "certificate_redline_count",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite-manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--minimum-contexts", type=int, default=5)
    parser.add_argument("--minimum-instances", type=int, default=5)
    parser.add_argument(
        "--minimum-strong-contexts", type=int, default=2
    )
    parser.add_argument(
        "--minimum-relative-gain", type=float, default=0.05
    )
    args = parser.parse_args()
    suite_path = _resolve(args.suite_manifest)
    output = _resolve(args.output)
    suite = _load_json(suite_path)
    if str(suite.get("schema_version") or "") != (
        "lunar_ice_bpc.p0v4_one_deviation_oracle_suite.v1"
    ):
        raise SystemExit("engineering smoke suite schema mismatch")
    if (
        not bool(suite.get("engineering_smoke_only"))
        or bool(suite.get("gat_training_authorized"))
        or bool(suite.get("formal_claim_authorized"))
    ):
        raise SystemExit(
            "engineering smoke suite is not safely isolated"
        )
    context_rows = []
    rejected = []
    seen_contexts: set[str] = set()
    for suite_row in suite.get("rows", ()):
        try:
            row = dict(suite_row)
            if str(row.get("status")) not in {"COMPLETED", "REUSED"}:
                raise ValueError("suite context did not complete")
            package_path = Path(str(row["package"])).resolve()
            if _sha256(package_path) != str(row["package_sha256"]):
                raise ValueError("suite package hash drift")
            package = _load_json(package_path)
            context = dict(package["context"])
            context_hash = str(context.get("context_hash") or "")
            if not context_hash or context_hash in seen_contexts:
                raise ValueError("duplicate or missing context hash")
            seen_contexts.add(context_hash)
            if (
                not bool(package.get("engineering_smoke_only"))
                or bool(package.get("gat_training_authorized"))
                or bool(package.get("formal_claim_authorized"))
                or package.get("training_row") is not None
            ):
                raise ValueError(
                    "smoke package could leak into formal training"
                )
            if not bool(
                dict(package.get("validation") or {}).get(
                    "validation_pass"
                )
            ):
                raise ValueError("matched rollout validation failed")
            redline_count = sum(
                int(package.get(key) or 0) for key in REDLINE_KEYS
            )
            labels = materialize_one_deviation_time_labels(
                context, tuple(package["rollouts"])
            )
            context_rows.append(
                _summarize_context_labels(
                    context,
                    labels,
                    package_path=package_path,
                    package_sha256=str(row["package_sha256"]),
                    redline_count=redline_count,
                    minimum_relative_gain=float(
                        args.minimum_relative_gain
                    ),
                )
            )
        except Exception as exc:
            rejected.append(
                {
                    "suite_row": dict(suite_row),
                    "reason": repr(exc),
                }
            )
    gate = _signal_gate(
        context_rows,
        rejected_count=len(rejected),
        minimum_contexts=max(1, int(args.minimum_contexts)),
        minimum_instances=max(1, int(args.minimum_instances)),
        minimum_strong_contexts=max(
            1, int(args.minimum_strong_contexts)
        ),
        minimum_relative_gain=float(args.minimum_relative_gain),
    )
    report = {
        "schema_version": (
            "lunar_ice_bpc.one_deviation_engineering_smoke_gate.v1"
        ),
        "status": (
            "BOUNDED_EXPANSION_RECOMMENDED"
            if bool(gate["signal_gate_pass"])
            else "STOP_OR_REVISE_ACTION_DEFINITION"
        ),
        "suite_manifest": str(suite_path.resolve()),
        "suite_manifest_sha256": _sha256(suite_path),
        "execution_scope": "engineering_smoke_scale_gate_only",
        "gat_training_authorized": False,
        "formal_claim_authorized": False,
        "right_censored_actions_forced_negative": False,
        "context_rows": context_rows,
        "rejected_packages": rejected,
        **gate,
    }
    _write_json(output, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if bool(report["signal_gate_pass"]) else 3


def _summarize_context_labels(
    context: dict,
    labels: dict,
    *,
    package_path: Path,
    package_sha256: str,
    redline_count: int,
    minimum_relative_gain: float,
) -> dict:
    rows = [dict(value) for value in labels.get("labels", ())]
    observed = [
        row
        for row in rows
        if row.get("relative_time_gain") is not None
        and int(row.get("observed_replicate_count") or 0) == 3
        and int(row.get("right_censored_replicate_count") or 0) == 0
        and not bool(row.get("memory_adverse_event"))
    ]
    best_gain = max(
        [0.0]
        + [float(row["relative_time_gain"]) for row in observed]
    )
    best_action = next(
        (
            str(row["action_id"])
            for row in observed
            if float(row["relative_time_gain"]) == best_gain
            and best_gain > 0.0
        ),
        "ONE_DEVIATION_NOOP",
    )
    return {
        "context_hash": str(context["context_hash"]),
        "scale": int(context["scale"]),
        "instance_content_hash": str(
            context["instance_content_hash"]
        ),
        "package": str(package_path.resolve()),
        "package_sha256": str(package_sha256),
        "promotion_arm_count": len(rows),
        "observed_action_count": len(observed),
        "right_censored_action_count": sum(
            int(row.get("right_censored_replicate_count") or 0) > 0
            for row in rows
        ),
        "best_observed_action_id": best_action,
        "best_observed_relative_gain": best_gain,
        "strong_signal": bool(best_gain >= minimum_relative_gain),
        "redline_count": int(redline_count),
        "labels": rows,
    }


def _signal_gate(
    rows: list[dict],
    *,
    rejected_count: int,
    minimum_contexts: int,
    minimum_instances: int,
    minimum_strong_contexts: int,
    minimum_relative_gain: float,
) -> dict:
    gains = [float(row["best_observed_relative_gain"]) for row in rows]
    strong = [
        row
        for row in rows
        if float(row["best_observed_relative_gain"])
        >= float(minimum_relative_gain)
    ]
    instances = {str(row["instance_content_hash"]) for row in rows}
    redlines = sum(int(row.get("redline_count") or 0) for row in rows)
    structural_pass = bool(
        len(rows) >= int(minimum_contexts)
        and len(instances) >= int(minimum_instances)
        and int(rejected_count) == 0
        and redlines == 0
    )
    signal_pass = bool(
        structural_pass
        and len(strong) >= int(minimum_strong_contexts)
    )
    return {
        "structural_gate_pass": structural_pass,
        "signal_gate_pass": signal_pass,
        "context_count": len(rows),
        "instance_count": len(instances),
        "rejected_package_count": int(rejected_count),
        "redline_count": redlines,
        "minimum_contexts": int(minimum_contexts),
        "minimum_instances": int(minimum_instances),
        "minimum_strong_contexts": int(minimum_strong_contexts),
        "minimum_relative_gain": float(minimum_relative_gain),
        "strong_signal_context_count": len(strong),
        "positive_observed_context_count": sum(gain > 0.0 for gain in gains),
        "best_gain_mean": 0.0 if not gains else mean(gains),
        "best_gain_median": 0.0 if not gains else median(gains),
        "best_gain_max": 0.0 if not gains else max(gains),
        "bounded_expansion_recommended": signal_pass,
        "stop_or_revise_action_definition": not signal_pass,
        "decision_basis": (
            "at_least_two_independent_contexts_need_a_5pct_"
            "observed_matched_milestone_gain_v1"
        ),
    }


def _resolve(value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def _load_json(path: Path) -> dict:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
