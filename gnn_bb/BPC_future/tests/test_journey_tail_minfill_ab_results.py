from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_tail_minfill_ab_results import audit_tail_minfill_ab


class JourneyTailMinfillABResultsTests(unittest.TestCase):
    def test_audit_classifies_strong_positive_and_regression(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runbook = tmp_path / "runbook.json"
            entries = []
            for idx, name in enumerate(("positive", "regression"), start=1):
                baseline_dir = tmp_path / name / "baseline"
                optin_dir = tmp_path / name / "optin"
                entries.append(
                    {
                        "entry_id": idx,
                        "instance": f"{name}.json",
                        "baseline_result_dir": str(baseline_dir),
                        "optin_result_dir": str(optin_dir),
                        "source_completion_retry_class": "completion_bound_time_limit_no_column_uncertified",
                        "source_tail_min_fill_candidate_count": 1,
                    }
                )
            runbook.write_text(json.dumps({"entries": entries}, sort_keys=True) + "\n", encoding="utf-8")

            self._write_result(tmp_path / "positive" / "baseline", status="TIME_LIMIT", wall=151.0)
            self._write_result(tmp_path / "positive" / "optin", status="OPTIMAL", wall=131.0)
            self._write_tail_log(
                tmp_path / "positive" / "baseline" / "logs",
                reason="optin_disabled",
                applied=False,
                min_fill=10,
                state="INCOMPLETE_LIMIT",
            )
            self._write_tail_log(
                tmp_path / "positive" / "optin" / "logs",
                reason="applied",
                applied=True,
                min_fill=4,
                state="CERTIFIED_NO_NEGATIVE",
            )

            self._write_result(tmp_path / "regression" / "baseline", status="OPTIMAL", wall=180.0)
            self._write_result(tmp_path / "regression" / "optin", status="TIME_LIMIT", wall=220.0)

            summary = audit_tail_minfill_ab(
                runbook=runbook,
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                target_wall=200.0,
            )

            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(summary["classification_counts"]["strong_positive"], 1)
            self.assertEqual(summary["classification_counts"]["regression"], 1)
            positive = next(row for row in summary["rows"] if row["instance"] == "positive.json")
            self.assertEqual(positive["classification"], "strong_positive")
            self.assertEqual(positive["baseline"]["tail_minfill_optin_disabled_count"], 1)
            self.assertEqual(positive["optin"]["tail_minfill_applied_count"], 1)
            self.assertEqual(positive["optin"]["direct_label_harvest_min_fill_values"], [4])
            self.assertLess(positive["deltas"]["wall_time"], 0)
            self.assertTrue((tmp_path / "out" / "tail_minfill_ab_rows.jsonl").exists())
            self.assertIn("strong_positive_count = 1", (tmp_path / "report.md").read_text(encoding="utf-8"))

    @staticmethod
    def _write_result(result_dir: Path, *, status: str, wall: float) -> None:
        result_dir.mkdir(parents=True)
        with (result_dir / "results.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "instance",
                    "status",
                    "wall_time",
                    "solving_time",
                    "external_timeout",
                    "node_count",
                    "rmp_solves",
                    "pricing_calls",
                    "exact_pricing_calls",
                    "columns",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "instance": "demo.json",
                    "status": status,
                    "wall_time": wall,
                    "solving_time": wall - 2.0,
                    "external_timeout": "false",
                    "node_count": 1,
                    "rmp_solves": 2,
                    "pricing_calls": 3,
                    "exact_pricing_calls": 1,
                    "columns": 10,
                }
            )

    @staticmethod
    def _write_tail_log(
        log_dir: Path,
        *,
        reason: str,
        applied: bool,
        min_fill: int,
        state: str,
    ) -> None:
        log_dir.mkdir(parents=True)
        rows = [
            {
                "event": "journey_exact_pricing_completion_bound_retry",
                "retry_mode": {
                    "completion_bound_diverse_harvest_tail_min_fill_candidate": True,
                    "completion_bound_diverse_harvest_tail_min_fill_applied": applied,
                    "completion_bound_diverse_harvest_tail_min_fill_reason": reason,
                },
            },
            {
                "event": "journey_pricing",
                "pricing_kind": "exact_completion_bound_retry",
                "pricing_state": state,
                "reason": "direct_label_no_negative_journey",
                "negative_journeys": 0,
                "selected_trips": 0,
                "direct_label_harvest_min_fill": min_fill,
            },
        ]
        (log_dir / "run.jsonl").write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
