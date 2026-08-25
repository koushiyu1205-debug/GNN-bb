from __future__ import annotations

from copy import deepcopy

import pytest

from lunar_ice_bpc.guidance.qg2_calibration_authority import (
    validate_qg2_calibration_performance_authority,
)


def _payloads() -> tuple[dict, dict]:
    thresholds = {
        "probability_threshold": 0.70,
        "expected_gain_threshold": 0.10,
    }
    calibration_metrics = {
        "passes_risk_precision_gate": True,
        "harmful_rate_95_upper": 0.01,
        "beneficial_precision_95_lower": 0.90,
    }
    heldout = {"net_geomean_ratio": 0.85}
    report = {
        "gate_pass": True,
        "deployment_authorized": True,
        "models": [
            {
                "model_kind": kind,
                "checkpoint_sha256": "checkpoint",
                "thresholds": dict(thresholds),
                "calibration": dict(calibration_metrics),
                "heldout": dict(heldout),
            }
            for kind in ("linear", "mlp", "gat")
        ],
        "gat_vs_best_non_gat_ratio": 0.97,
        "gat_inference_p99_ms": 5.0,
    }
    manifest = {
        "evaluation_authorized": True,
        "deployment_authorized": True,
        "checkpoint_sha256": "checkpoint",
        "calibration": {
            "gate_pass": True,
            **thresholds,
            "harmful_rate_95_upper": 0.01,
            "beneficial_precision_95_lower": 0.90,
            "heldout_tail_ratio": 0.85,
            "gat_vs_best_non_gat_ratio": 0.97,
        },
    }
    return report, manifest


def _gat(report: dict) -> dict:
    return next(row for row in report["models"] if row["model_kind"] == "gat")


def test_calibration_authority_accepts_all_frozen_numerical_gates() -> None:
    report, manifest = _payloads()
    validate_qg2_calibration_performance_authority(report, manifest)


@pytest.mark.parametrize(
    ("mutation", "error"),
    (
        (
            lambda report, _manifest: report.update(
                {"gat_inference_p99_ms": 10.01}
            ),
            "gat_inference_p99_exceeded",
        ),
        (
            lambda report, _manifest: _gat(report)["calibration"].update(
                {"harmful_rate_95_upper": 0.051}
            ),
            "gat_harmful_rate_95_upper_exceeded",
        ),
        (
            lambda report, _manifest: _gat(report)["calibration"].update(
                {"beneficial_precision_95_lower": 0.79}
            ),
            "gat_beneficial_precision_95_lower_not_met",
        ),
        (
            lambda report, _manifest: _gat(report)["heldout"].update(
                {"net_geomean_ratio": 0.901}
            ),
            "gat_heldout_tail_ratio_not_met",
        ),
        (
            lambda report, _manifest: report.update(
                {"gat_vs_best_non_gat_ratio": 0.981}
            ),
            "gat_advantage_over_non_gat_not_met",
        ),
        (
            lambda report, _manifest: report.update(
                {
                    "models": [
                        row for row in report["models"]
                        if row["model_kind"] != "linear"
                    ]
                }
            ),
            "model_comparison_universe_mismatch",
        ),
        (
            lambda _report, manifest: manifest["calibration"].update(
                {"beneficial_precision_95_lower": 0.81}
            ),
            "manifest_beneficial_precision_mismatch",
        ),
    ),
)
def test_calibration_authority_fails_closed_on_each_gate(
    mutation,
    error: str,
) -> None:
    report, manifest = _payloads()
    mutation(report, manifest)
    with pytest.raises(ValueError, match=error):
        validate_qg2_calibration_performance_authority(
            deepcopy(report),
            deepcopy(manifest),
        )

