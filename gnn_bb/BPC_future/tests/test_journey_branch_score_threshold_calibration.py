from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_branch_score_threshold_calibration import (
    build_threshold_calibration,
)


class JourneyBranchScoreThresholdCalibrationTests(unittest.TestCase):
    def test_threshold_calibration_filters_low_score_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            rows = [
                self._row("a", score=3.0, baseline_wall=250.0, optin_wall=180.0),
                self._row("b", score=2.0, baseline_wall=220.0, optin_wall=190.0),
                self._row("c", score=0.1, baseline_wall=280.0, optin_wall=310.0),
            ]
            source = tmp_path / "rows.jsonl"
            source.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_threshold_calibration(
                inputs=[source],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                thresholds=[0.0, 1.0, 2.5],
                target_wall=200.0,
            )

            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(summary["raw_ab_row_count"], 3)
            by_threshold = {row["threshold"]: row for row in summary["threshold_rows"]}
            self.assertEqual(by_threshold[0.0]["admitted_count"], 3)
            self.assertEqual(by_threshold[0.0]["wall_regressed_count"], 1)
            self.assertEqual(by_threshold[1.0]["admitted_count"], 2)
            self.assertEqual(by_threshold[1.0]["wall_regressed_count"], 0)
            self.assertEqual(by_threshold[1.0]["crossed_into_target_count"], 2)
            self.assertEqual(by_threshold[2.5]["admitted_count"], 1)
            self.assertEqual(summary["recommended_min_score"], 1.0)
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("recommended_min_score = 1.0", report)
            self.assertTrue((tmp_path / "out" / "threshold_calibration_rows.jsonl").exists())

    @staticmethod
    def _row(
        instance: str,
        *,
        score: float,
        baseline_wall: float,
        optin_wall: float,
    ) -> dict[str, object]:
        return {
            "instance": instance,
            "baseline": {"status": "OPTIMAL", "wall_time": baseline_wall},
            "optin": {"status": "OPTIMAL", "wall_time": optin_wall, "branch_score": score},
            "deltas": {"wall_time": round(float(optin_wall) - float(baseline_wall), 6)},
        }


if __name__ == "__main__":
    unittest.main()
