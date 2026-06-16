from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_gat_batch_impact_score_margins import (
    audit_score_margins,
)


class GATBatchImpactScoreMarginAuditTests(unittest.TestCase):
    def test_audit_summarizes_missed_margin_and_context_contrast(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            opportunities = tmp / "validation_opportunities.jsonl"
            summary_path = tmp / "opportunity_summary.json"
            output_dir = tmp / "out"
            report = tmp / "report.md"
            _write_jsonl(
                opportunities,
                [
                    _record(
                        family="random-wave",
                        context="ctx-deep",
                        roi=4.0,
                        max_safe_margin=-0.25,
                        missed=True,
                        high_roi=True,
                    ),
                    _record(
                        family="random-wave",
                        context="ctx-deep",
                        roi=0.1,
                        max_safe_margin=-0.01,
                        missed=False,
                        high_roi=False,
                    ),
                    _record(
                        family="random-wave",
                        context="ctx-near",
                        roi=2.0,
                        max_safe_margin=-0.02,
                        missed=True,
                        high_roi=True,
                    ),
                    _record(
                        family="sector-wave",
                        context="ctx-accepted",
                        roi=3.0,
                        max_safe_margin=0.10,
                        missed=False,
                        high_roi=True,
                        accepted=True,
                    ),
                ],
            )
            summary_path.write_text(
                json.dumps(
                    {
                        "schema_version": "gat_batch_impact_opportunity_mining_v1",
                        "validation_opportunities_path": str(opportunities),
                        "selected_threshold": {
                            "threshold_scope": "family_delay_fallback",
                            "threshold_mode": "context_delay_fallback",
                            "batch_threshold": 0.45,
                            "candidate_threshold": 0.60,
                        },
                        "production_ready": False,
                        "runs_bpc_or_pricing": False,
                        "selector_can_certificate": False,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = audit_score_margins(
                opportunity_summary=summary_path,
                output_dir=output_dir,
                report=report,
                near_miss_window=0.05,
                deep_miss_margin=-0.20,
            )
            self.assertTrue(Path(summary["missed_high_roi_score_margins_path"]).exists())
            self.assertTrue(Path(summary["context_score_margin_summary_path"]).exists())

        margin = summary["margin_summary"]
        self.assertEqual(margin["missed_high_roi_opportunities"], 2)
        self.assertEqual(margin["accepted_high_roi_opportunities"], 1)
        self.assertEqual(
            margin["candidate_margin_bucket_counts"],
            {"deep_candidate_score_gap": 1, "near_candidate_threshold": 1},
        )
        self.assertEqual(margin["missed_without_same_context_contrast_count"], 1)
        self.assertEqual(
            margin["family"]["random-wave"]["missed_without_same_context_contrast_count"],
            1,
        )
        self.assertEqual(
            summary["recommended_next_step"]["primary"],
            "collect_same_context_positive_negative_pairs_for_missed_high_roi_contexts",
        )
        self.assertFalse(summary["runs_bpc_or_pricing"])
        self.assertFalse(summary["selector_can_certificate"])


def _record(
    *,
    family: str,
    context: str,
    roi: float,
    max_safe_margin: float,
    missed: bool,
    high_roi: bool,
    accepted: bool = False,
) -> dict[str, object]:
    return {
        "family": family,
        "context_hash": context,
        "instance": f"{family}-{context}",
        "instance_path": f"{family}/{context}.json",
        "region": "region",
        "task_count": 50 if family == "random-wave" else 20,
        "accepted": accepted,
        "is_high_roi_opportunity": high_roi,
        "is_missed_high_roi_opportunity": missed,
        "is_accepted_high_roi_opportunity": accepted and high_roi,
        "accepted_batch_roi_label": roi,
        "batch_score": 0.50,
        "batch_score_margin": 0.05,
        "candidate_threshold": 0.60,
        "candidate_count": 1,
        "predicted_candidate_count": 0 if missed else 1,
        "delay_candidate_label_count": 0,
        "bad_mode_switch": 0,
        "max_safe_candidate_score": 0.60 + max_safe_margin,
        "max_safe_candidate_score_margin": max_safe_margin,
        "max_candidate_score": 0.60 + max_safe_margin,
        "max_candidate_score_margin": max_safe_margin,
        "missed_reasons": ["no_candidate_above_threshold"] if missed else [],
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
