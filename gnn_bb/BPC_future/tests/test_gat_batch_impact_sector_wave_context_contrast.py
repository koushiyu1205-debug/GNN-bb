from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_gat_batch_impact_sector_wave_context_contrast import (
    audit_sector_wave_context_contrast,
    build_context_contrast_pairs,
    classify_contrast_pair,
)


class GATBatchImpactSectorWaveContextContrastTests(unittest.TestCase):
    def test_build_pairs_detects_raw_and_safe_rank_reversal(self) -> None:
        pairs = build_context_contrast_pairs(
            [
                _decision(
                    context="ctx-a",
                    roi=10.0,
                    high_roi=True,
                    accepted=False,
                    raw_score=0.45,
                    safe_score=0.20,
                    batch_score=0.40,
                    missed_reasons=["candidate_risk_adjusted_below_threshold"],
                ),
                _decision(
                    context="ctx-a",
                    roi=0.2,
                    high_roi=False,
                    accepted=True,
                    raw_score=0.55,
                    safe_score=0.25,
                    batch_score=0.41,
                ),
            ],
            run_name="v-test",
        )

        self.assertEqual(len(pairs), 1)
        self.assertTrue(pairs[0]["raw_rank_failure"])
        self.assertTrue(pairs[0]["safe_rank_failure"])
        self.assertEqual(
            pairs[0]["repair_bucket"],
            "missed_high_roi_raw_and_safe_rank_reversal",
        )

    def test_classifies_risk_adjusted_rank_reversal(self) -> None:
        bucket = classify_contrast_pair(
            {
                "positive_was_missed": True,
                "raw_rank_failure": False,
                "safe_rank_failure": True,
                "batch_rank_failure": False,
                "positive_candidate_risk_adjusted_suppressed_count": 1,
                "positive_candidate_delay_gate_blocked_count": 0,
                "positive_raw_candidate_margin": 0.2,
                "positive_safe_candidate_margin": -0.1,
            }
        )

        self.assertEqual(bucket, "missed_high_roi_risk_adjusted_rank_reversal")

    def test_audit_reads_v106_like_summary_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            decisions = tmp / "v-test_sector-wave_validation_decisions.jsonl"
            _write_jsonl(
                decisions,
                [
                    _decision(
                        context="ctx-a",
                        roi=9.0,
                        high_roi=True,
                        accepted=False,
                        raw_score=0.50,
                        safe_score=0.20,
                        batch_score=0.40,
                        missed_reasons=["candidate_risk_adjusted_below_threshold"],
                    ),
                    _decision(
                        context="ctx-a",
                        roi=0.1,
                        high_roi=False,
                        accepted=True,
                        raw_score=0.60,
                        safe_score=0.30,
                        batch_score=0.41,
                    ),
                ],
            )
            repair_summary = tmp / "repair_summary.json"
            report = tmp / "report.md"
            output_dir = tmp / "out"
            repair_summary.write_text(
                json.dumps(
                    {
                        "schema_version": "gat_batch_impact_sector_wave_repair_audit_v1",
                        "diagnostic_only": True,
                        "production_ready": False,
                        "selector_can_certificate": False,
                        "runs": [
                            {
                                "run_name": "v-test",
                                "validation_decisions_path": str(decisions),
                            }
                        ],
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = audit_sector_wave_context_contrast(
                repair_summary=repair_summary,
                output_dir=output_dir,
                report=report,
            )

            self.assertEqual(summary["aggregate"]["missed_high_roi_pair_count"], 1)
            self.assertEqual(summary["aggregate"]["missed_raw_rank_failure_count"], 1)
            self.assertEqual(
                summary["recommended_next_step"],
                "train_sector_wave_same_context_pairwise_ranking_with_trace_features",
            )
            self.assertTrue(Path(summary["runs"][0]["context_contrast_pairs_path"]).exists())
            self.assertTrue(report.exists())
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["selector_can_certificate"])


def _decision(
    *,
    context: str,
    roi: float,
    high_roi: bool,
    accepted: bool,
    raw_score: float,
    safe_score: float,
    batch_score: float,
    missed_reasons: list[str] | None = None,
) -> dict[str, object]:
    candidate_threshold = 0.25
    return {
        "family": "sector-wave",
        "context_hash": context,
        "instance_path": f"{context}.json",
        "task_count": 20,
        "accepted": accepted,
        "is_high_roi_opportunity": high_roi,
        "is_missed_high_roi_opportunity": bool(high_roi and not accepted),
        "is_accepted_high_roi_opportunity": bool(high_roi and accepted),
        "is_accepted_low_roi_or_bad": bool((not high_roi) and accepted),
        "accepted_batch_roi_label": roi,
        "batch_score": batch_score,
        "batch_score_margin": batch_score,
        "max_candidate_score": safe_score,
        "max_safe_candidate_score": safe_score,
        "max_raw_candidate_score": raw_score,
        "max_safe_candidate_score_margin": safe_score - candidate_threshold,
        "max_raw_candidate_score_margin": raw_score - candidate_threshold,
        "candidate_risk_adjusted_suppressed_count": int(high_roi and not accepted),
        "candidate_delay_gate_blocked_count": 0,
        "delay_candidate_label_count": 0,
        "missed_reasons": missed_reasons or [],
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
