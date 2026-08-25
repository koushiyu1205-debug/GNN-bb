#!/usr/bin/env python3
"""Authorize reversible QG2 E2E trials from positive net calibration.

This sidecar does not alter the frozen v4 calibrator or reinterpret exact
safety.  It relaxes only minimum effect-size and confidence-interval gates for
development E2E: calibration and heldout must both have net GM below one after
inference overhead, while selected censored/unsafe actions remain forbidden.
The emitted manifest is evaluation-only and can never authorize production.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (  # noqa: E402
    QG2_POSITIVE_NET_EVALUATION_GATE_V1,
    qg2_runtime_implementation_hash,
)
from lunar_ice_bpc.guidance.qg2_oracle_evidence import (  # noqa: E402
    attach_selective_oracle_evidence_to_manifest,
)


SCHEMA = "lunar_ice_bpc.p0v5_qg2_positive_net_calibration.v1"
MANIFEST_SCHEMA = "lunar_ice_bpc.p0v5_qg2_manifest.v1"
BASE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
SELECTIVE_EVIDENCE_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_runtime_oracle_evidence.v1"
)
EXPECTED_MODELS = ("linear", "mlp", "gat")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calibration-report", required=True)
    parser.add_argument("--selective-oracle-evidence", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest-output", required=True)
    args = parser.parse_args()

    calibration_path = _resolve(args.calibration_report)
    evidence_path = _resolve(args.selective_oracle_evidence)
    output_path = _resolve(args.output)
    manifest_path = _resolve(args.manifest_output)
    if output_path.exists() or manifest_path.exists():
        raise SystemExit("positive-net calibration refuses overwrite")
    base = _load(calibration_path)
    evidence = _load(evidence_path)
    base_manifest_path = _validate_inputs(
        calibration_path, base, evidence_path, evidence
    )
    base_manifest = _load(base_manifest_path)
    records_by_model = {
        kind: [
            dict(row)
            for row in base.get("records") or ()
            if str(row.get("model_kind") or "") == kind
        ]
        for kind in EXPECTED_MODELS
    }
    model_reports = []
    for kind in EXPECTED_MODELS:
        rows = records_by_model[kind]
        calibration_rows = [
            row for row in rows if row.get("partition") == "calibration"
        ]
        heldout_rows = [
            row for row in rows if row.get("partition") == "heldout"
        ]
        thresholds = choose_positive_net_thresholds(calibration_rows)
        calibration_metrics = activation_metrics(calibration_rows, thresholds)
        heldout_metrics = activation_metrics(heldout_rows, thresholds)
        inference_p99 = _quantile(
            [
                float(row.get("inference_wall_ms") or 0.0)
                for row in heldout_rows
            ],
            0.99,
        )
        all_replays_exact_safe = all(bool(row.get("safe")) for row in rows)
        positive_net_gate = bool(
            thresholds["gate_passed"]
            and float(calibration_metrics["net_geomean_ratio"]) < 1.0
            and int(calibration_metrics["selected_right_censored_count"]) == 0
            and int(calibration_metrics["selected_unsafe_count"]) == 0
            and int(heldout_metrics["activation_count"]) > 0
            and float(heldout_metrics["net_geomean_ratio"]) < 1.0
            and int(heldout_metrics["selected_right_censored_count"]) == 0
            and int(heldout_metrics["selected_unsafe_count"]) == 0
            and all(
                float(heldout_metrics["per_scale"][str(scale)][
                    "net_geomean_ratio"
                ])
                <= 1.03
                for scale in (30, 50)
            )
            and inference_p99 <= 10.0
            and all_replays_exact_safe
        )
        base_model = next(
            row
            for row in base.get("models") or ()
            if str(row.get("model_kind") or "") == kind
        )
        model_reports.append({
            "model_kind": kind,
            "checkpoint_path": str(base_model["checkpoint_path"]),
            "checkpoint_sha256": str(base_model["checkpoint_sha256"]),
            "thresholds": {
                "probability_threshold": thresholds[
                    "probability_threshold"
                ],
                "expected_gain_threshold": thresholds[
                    "expected_gain_threshold"
                ],
            },
            "threshold_reason": thresholds["reason"],
            "calibration": calibration_metrics,
            "heldout": heldout_metrics,
            "inference_p99_ms": inference_p99,
            "all_replays_exact_safe": all_replays_exact_safe,
            "positive_net_exact_safe_gate_passed": positive_net_gate,
            "strict_calibration_diagnostic": dict(
                base_model.get("calibration") or {}
            ),
            "strict_heldout_diagnostic": dict(
                base_model.get("heldout") or {}
            ),
        })
    by_kind = {row["model_kind"]: row for row in model_reports}
    gat = by_kind["gat"]
    eligible_models = [
        row
        for row in model_reports
        if row["positive_net_exact_safe_gate_passed"]
    ]
    best_model = (
        min(
            eligible_models,
            key=lambda row: (
                float(row["heldout"]["net_geomean_ratio"]),
                row["model_kind"],
            ),
        )["model_kind"]
        if eligible_models
        else ""
    )
    gat_gate_passed = bool(gat["positive_net_exact_safe_gate_passed"])
    report = {
        "schema_version": SCHEMA,
        "generated_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "development_only": True,
        "deployable": False,
        "deployment_authorized": False,
        "evaluation_gate_policy": QG2_POSITIVE_NET_EVALUATION_GATE_V1,
        "minimum_speedup_gate_enabled": False,
        "harmful_rate_confidence_gate_blocks_e2e": False,
        "strict_metrics_retained_for_reporting": True,
        "selected_censor_or_unsafe_is_hard_veto": True,
        "fallback_action": "Q0",
        "calibration_report": str(calibration_path),
        "calibration_report_sha256": _sha256(calibration_path),
        "base_manifest": str(base_manifest_path),
        "base_manifest_sha256": _sha256(base_manifest_path),
        "selective_oracle_evidence": str(evidence_path),
        "selective_oracle_evidence_sha256": _sha256(evidence_path),
        "models": model_reports,
        "best_positive_net_model_kind": best_model,
        "gat_positive_net_exact_safe_gate_passed": gat_gate_passed,
        "development_e2e_authorized": gat_gate_passed,
        "production_switch_authorized": False,
        "next_action": (
            "bind_evaluation_only_gat_manifest_then_scale30_50_e2e"
            if gat_gate_passed
            else "retain_q0_and_report_no_positive_net_gat"
        ),
    }
    if gat_gate_passed:
        manifest = build_positive_net_evaluation_manifest(
            base_manifest=base_manifest,
            gat_report=gat,
            evidence=evidence,
            calibration_path=calibration_path,
            base_manifest_path=base_manifest_path,
        )
        _write(manifest_path, manifest)
        report.update({
            "evaluation_manifest": str(manifest_path),
            "evaluation_manifest_sha256": _sha256(manifest_path),
        })
    else:
        report.update({
            "evaluation_manifest": "",
            "evaluation_manifest_sha256": "",
        })
    _write(output_path, report)
    print(json.dumps({
        "gat_positive_net_exact_safe_gate_passed": gat_gate_passed,
        "best_positive_net_model_kind": best_model,
        "gat_calibration_ratio": gat["calibration"]["net_geomean_ratio"],
        "gat_heldout_ratio": gat["heldout"]["net_geomean_ratio"],
        "output": str(output_path),
        "manifest": str(manifest_path) if gat_gate_passed else "",
    }, sort_keys=True), flush=True)
    return 0 if gat_gate_passed else 2


def choose_positive_net_thresholds(rows: list[dict]) -> dict[str, Any]:
    eligible = [row for row in rows if row.get("action_eligible", True)]
    probabilities = sorted({
        float(row["benefit_probability"])
        for row in eligible
        if _finite(row.get("benefit_probability"))
    })
    gains = sorted({
        float(row["expected_gain"])
        for row in eligible
        if _finite(row.get("expected_gain"))
    })
    candidates = []
    for probability in probabilities:
        for gain in gains:
            thresholds = {
                "probability_threshold": probability,
                "expected_gain_threshold": gain,
            }
            metrics = activation_metrics(rows, thresholds)
            if not (
                int(metrics["activation_count"]) > 0
                and int(metrics["selected_right_censored_count"]) == 0
                and int(metrics["selected_unsafe_count"]) == 0
                and float(metrics["net_geomean_ratio"]) < 1.0
            ):
                continue
            candidates.append((
                float(metrics["net_geomean_ratio"]),
                -int(metrics["activation_count"]),
                -probability,
                -gain,
                thresholds,
                metrics,
            ))
    if not candidates:
        return {
            "probability_threshold": 2.0,
            "expected_gain_threshold": 1.0e30,
            "gate_passed": False,
            "reason": "no_exact_safe_uncensored_positive_net_threshold",
        }
    selected = min(candidates)
    return {
        **selected[4],
        "gate_passed": True,
        "reason": "best_calibration_positive_net_threshold",
    }


def activation_metrics(rows: list[dict], thresholds: Mapping[str, float]) -> dict[str, Any]:
    selected = [
        row
        for row in rows
        if row.get("action_eligible", True)
        and _finite(row.get("benefit_probability"))
        and _finite(row.get("expected_gain"))
        and float(row["benefit_probability"])
        >= float(thresholds["probability_threshold"])
        and float(row["expected_gain"])
        >= float(thresholds["expected_gain_threshold"])
    ]
    selected_ids = {id(row) for row in selected}
    ratios = [
        float(row.get("ratio") or 1.0) if id(row) in selected_ids else 1.0
        for row in rows
    ]
    per_scale = {}
    for scale in (30, 50):
        scale_rows = [row for row in rows if int(row.get("scale") or 0) == scale]
        scale_selected = [row for row in selected if int(row.get("scale") or 0) == scale]
        scale_ids = {id(row) for row in scale_selected}
        per_scale[str(scale)] = {
            "context_count": len(scale_rows),
            "activation_count": len(scale_selected),
            "net_geomean_ratio": _geomean(
                float(row.get("ratio") or 1.0) if id(row) in scale_ids else 1.0
                for row in scale_rows
            ),
            "selected_right_censored_count": sum(
                bool(row.get("right_censored"))
                or not bool(row.get("outcome_determined"))
                for row in scale_selected
            ),
            "selected_unsafe_count": sum(
                not bool(row.get("safe")) for row in scale_selected
            ),
        }
    harmful = sum(float(row.get("ratio") or 1.0) > 1.0 for row in selected)
    beneficial = sum(float(row.get("ratio") or 1.0) < 1.0 for row in selected)
    return {
        "context_count": len(rows),
        "instance_count": len({str(row.get("instance_hash") or "") for row in rows}),
        "activation_count": len(selected),
        "no_op_count": len(rows) - len(selected),
        "beneficial_count": beneficial,
        "harmful_count": harmful,
        "harmful_rate": harmful / max(1, len(selected)),
        "beneficial_precision": beneficial / max(1, len(selected)),
        "selected_right_censored_count": sum(
            bool(row.get("right_censored"))
            or not bool(row.get("outcome_determined"))
            for row in selected
        ),
        "selected_unsafe_count": sum(not bool(row.get("safe")) for row in selected),
        "net_geomean_ratio": _geomean(ratios),
        "per_scale": per_scale,
        "selected_state_hashes": [str(row.get("state_hash") or "") for row in selected],
    }


def build_positive_net_evaluation_manifest(
    *,
    base_manifest: Mapping[str, Any],
    gat_report: Mapping[str, Any],
    evidence: Mapping[str, Any],
    calibration_path: Path,
    base_manifest_path: Path,
) -> dict[str, Any]:
    if str(base_manifest.get("schema_version") or "") != MANIFEST_SCHEMA:
        raise ValueError("positive-net base manifest schema mismatch")
    calibration = dict(gat_report["calibration"])
    heldout = dict(gat_report["heldout"])
    thresholds = dict(gat_report["thresholds"])
    manifest = dict(base_manifest)
    manifest.update({
        "runtime_implementation_hash": qg2_runtime_implementation_hash(),
        "checkpoint_path": str(Path(gat_report["checkpoint_path"]).resolve()),
        "checkpoint_sha256": str(gat_report["checkpoint_sha256"]),
        "evaluation_gate_policy": QG2_POSITIVE_NET_EVALUATION_GATE_V1,
        "evaluation_authorized": True,
        "evaluation_force_qg2": True,
        "development_e2e_authorized": True,
        "deployment_authorized": False,
        "production_switch_authorized": False,
        "positive_net_source_calibration_report": str(calibration_path),
        "positive_net_source_calibration_report_sha256": _sha256(
            calibration_path
        ),
        "positive_net_source_base_manifest": str(base_manifest_path),
        "positive_net_source_base_manifest_sha256": _sha256(
            base_manifest_path
        ),
        "calibration": {
            "gate_pass": False,
            "strict_gate_report_only": True,
            "positive_net_gate_pass": True,
            "probability_threshold": float(
                thresholds["probability_threshold"]
            ),
            "expected_gain_threshold": float(
                thresholds["expected_gain_threshold"]
            ),
            "calibration_net_ratio": float(
                calibration["net_geomean_ratio"]
            ),
            "heldout_net_ratio": float(heldout["net_geomean_ratio"]),
            "calibration_selected_right_censored_count": int(
                calibration["selected_right_censored_count"]
            ),
            "heldout_selected_right_censored_count": int(
                heldout["selected_right_censored_count"]
            ),
            "calibration_selected_unsafe_count": int(
                calibration["selected_unsafe_count"]
            ),
            "heldout_selected_unsafe_count": int(
                heldout["selected_unsafe_count"]
            ),
            "heldout_per_scale_net_ratio": {
                str(scale): float(
                    heldout["per_scale"][str(scale)]["net_geomean_ratio"]
                )
                for scale in (30, 50)
            },
            "harmful_rate_95_upper": float(
                (base_manifest.get("calibration") or {}).get(
                    "harmful_rate_95_upper", 1.0
                )
            ),
            "beneficial_precision_95_lower": float(
                (base_manifest.get("calibration") or {}).get(
                    "beneficial_precision_95_lower", 0.0
                )
            ),
            "heldout_tail_ratio": float(heldout["net_geomean_ratio"]),
            "gat_vs_best_non_gat_ratio": 1.0,
        },
        "ordering_only": True,
        "can_filter": False,
        "can_prune": False,
        "can_change_bound": False,
        "can_certify": False,
        "fallback": "P0V4_V5_Q0",
    })
    return attach_selective_oracle_evidence_to_manifest(manifest, evidence)


def _validate_inputs(calibration_path, base, evidence_path, evidence) -> Path:
    errors = []
    if base.get("schema_version") != BASE_SCHEMA:
        errors.append("calibration_schema_mismatch")
    if not bool(base.get("development_only")):
        errors.append("calibration_development_contract_missing")
    kinds = {str(row.get("model_kind") or "") for row in base.get("models") or ()}
    if kinds != set(EXPECTED_MODELS):
        errors.append("model_universe_mismatch")
    base_manifest_path = _resolve(base.get("manifest_path") or "")
    if (
        not base_manifest_path.is_file()
        or str(base.get("manifest_sha256") or "") != _sha256(base_manifest_path)
    ):
        errors.append("base_manifest_binding_mismatch")
    if evidence.get("schema_version") != SELECTIVE_EVIDENCE_SCHEMA:
        errors.append("selective_evidence_schema_mismatch")
    if bool(evidence.get("deployment_authorized")):
        errors.append("selective_evidence_deployment_authority_forbidden")
    if not bool(evidence.get("passed")):
        errors.append("selective_evidence_not_passed")
    if errors:
        raise ValueError(
            "positive-net calibration input contract failed:"
            + ",".join(sorted(set(errors)))
        )
    return base_manifest_path


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return math.inf
    ordered = sorted(float(value) for value in values)
    index = min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))
    return ordered[index]


def _geomean(values: Iterable[float]) -> float:
    rows = [max(1.0e-12, float(value)) for value in values]
    return 1.0 if not rows else math.exp(statistics.fmean(math.log(value) for value in rows))


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
