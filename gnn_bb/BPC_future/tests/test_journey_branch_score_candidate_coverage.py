from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_branch_score_candidate_coverage import (
    build_branch_score_candidate_coverage,
)


class JourneyBranchScoreCandidateCoverageTests(unittest.TestCase):
    def test_candidate_coverage_counts_hits_and_would_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            score_path = tmp_path / "score_rows.json"
            score_path.write_text(
                json.dumps(
                    [
                        {"key": "node:0:depth:0:3,18", "branch_score": 10.0},
                        {"key": "5,8", "branch_score": -2.0},
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            log_path = tmp_path / "events.jsonl"
            records = [
                {
                    "event": "journey_branch_candidates",
                    "node_id": 0,
                    "depth": 0,
                    "priority_mode": "branch_score",
                    "candidate_count": 2,
                    "eligible_count": 2,
                    "selected": {"task_i": 2, "task_j": 5, "fractionality": 0.5},
                    "priority_top": [
                        {"task_i": 2, "task_j": 5, "fractionality": 0.5},
                        {"task_i": 3, "task_j": 18, "fractionality": 0.5},
                    ],
                },
                {
                    "event": "journey_branch_candidates",
                    "node_id": 1,
                    "depth": 1,
                    "priority_mode": "branch_score",
                    "candidate_count": 1,
                    "selected": {"task_i": 1, "task_j": 2, "fractionality": 0.5},
                    "priority_top": [{"task_i": 1, "task_j": 2, "fractionality": 0.5}],
                },
            ]
            log_path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )

            summary = build_branch_score_candidate_coverage(
                score_path=score_path,
                log_paths=[log_path],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(summary["score_entry_count"], 2)
            self.assertEqual(summary["candidate_event_count"], 2)
            self.assertEqual(summary["candidate_event_with_score_hit_count"], 1)
            self.assertEqual(summary["candidate_event_with_eligible_score_hit_count"], 1)
            self.assertEqual(summary["candidate_event_with_selected_score_count"], 0)
            self.assertEqual(summary["candidate_event_would_change_selected_count"], 1)
            self.assertEqual(summary["candidate_event_would_change_selected_any_logged_count"], 1)
            self.assertEqual(summary["scored_candidate_count_sum"], 1)
            self.assertEqual(summary["eligible_scored_candidate_count_sum"], 1)
            self.assertEqual(summary["unscored_logged_candidate_count_sum"], 2)
            self.assertEqual(summary["selected_unscored_count"], 2)

            rows = [
                json.loads(line)
                for line in (tmp_path / "out" / "branch_score_candidate_coverage_rows.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(rows[0]["selected_pair"], "2,5")
            self.assertEqual(rows[0]["best_scored_pair"], "3,18")
            self.assertEqual(rows[0]["best_scored_source"], "node:0:depth:0:3,18")
            self.assertEqual(rows[0]["best_eligible_scored_pair"], "3,18")
            self.assertTrue(rows[0]["would_change_selected"])
            self.assertTrue(rows[0]["would_change_selected_any_logged"])
            self.assertTrue(rows[0]["selected_is_unscored"])
            self.assertEqual(rows[0]["eligible_scored_candidate_count"], 1)
            self.assertEqual(rows[0]["unscored_logged_candidate_count"], 1)
            self.assertEqual(rows[0]["unscored_candidates"][0]["pair"], [2, 5])
            self.assertEqual(rows[1]["scored_candidate_count"], 0)
            self.assertEqual(rows[1]["eligible_scored_candidate_count"], 0)
            self.assertEqual(rows[1]["unscored_logged_candidate_count"], 1)
            self.assertIn("official_bound_effect = False", (tmp_path / "report.md").read_text())

    def test_candidate_coverage_distinguishes_logged_hit_from_eligible_hit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            score_path = tmp_path / "score_rows.json"
            score_path.write_text(
                json.dumps([{"key": "node:0:depth:0:7,11", "branch_score": 3.0}], sort_keys=True),
                encoding="utf-8",
            )
            log_path = tmp_path / "events.jsonl"
            record = {
                "event": "journey_branch_candidates",
                "node_id": 0,
                "depth": 0,
                "tie_tolerance": 0.0,
                "candidate_count": 2,
                "eligible_count": 1,
                "selected": {"task_i": 2, "task_j": 18, "fractionality": 0.4},
                "priority_top": [
                    {"task_i": 2, "task_j": 18, "fractionality": 0.4},
                    {"task_i": 7, "task_j": 11, "fractionality": 0.2},
                ],
            }
            log_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

            default_summary = build_branch_score_candidate_coverage(
                score_path=score_path,
                log_paths=[log_path],
                output_dir=tmp_path / "default",
                report=tmp_path / "default.md",
            )
            self.assertEqual(default_summary["candidate_event_with_score_hit_count"], 1)
            self.assertEqual(default_summary["candidate_event_with_eligible_score_hit_count"], 0)
            self.assertEqual(default_summary["candidate_event_would_change_selected_count"], 0)
            self.assertEqual(default_summary["candidate_event_would_change_selected_any_logged_count"], 1)
            self.assertEqual(
                default_summary[
                    "candidate_event_with_best_scored_requiring_recorded_horizon_expansion_count"
                ],
                1,
            )
            self.assertEqual(
                default_summary[
                    "candidate_event_with_best_scored_requiring_effective_horizon_expansion_count"
                ],
                1,
            )
            self.assertEqual(default_summary["best_scored_required_tie_tolerance_count"], 1)
            self.assertEqual(default_summary["best_scored_required_tie_tolerance_le_0_count"], 0)
            self.assertEqual(default_summary["best_scored_required_tie_tolerance_le_0_2_count"], 1)
            self.assertEqual(default_summary["best_scored_required_tie_tolerance_gt_0_2_count"], 0)
            self.assertAlmostEqual(default_summary["best_scored_required_tie_tolerance_max"], 0.2)
            default_row = json.loads(
                (tmp_path / "default" / "branch_score_candidate_coverage_rows.jsonl").read_text(encoding="utf-8")
            )
            self.assertEqual(default_row["best_scored_pair"], "7,11")
            self.assertEqual(default_row["max_logged_fractionality"], 0.4)
            self.assertEqual(default_row["best_scored_fractionality"], 0.2)
            self.assertAlmostEqual(default_row["best_scored_required_tie_tolerance"], 0.2)
            self.assertTrue(default_row["best_scored_requires_recorded_horizon_expansion"])
            self.assertTrue(default_row["best_scored_requires_effective_horizon_expansion"])
            self.assertIsNone(default_row["best_eligible_scored_pair"])
            self.assertFalse(default_row["would_change_selected"])
            self.assertTrue(default_row["would_change_selected_any_logged"])

            override_summary = build_branch_score_candidate_coverage(
                score_path=score_path,
                log_paths=[log_path],
                output_dir=tmp_path / "override",
                report=tmp_path / "override.md",
                tie_tolerance_override=0.2,
            )
            self.assertEqual(override_summary["tie_tolerance_override"], 0.2)
            self.assertEqual(override_summary["candidate_event_with_eligible_score_hit_count"], 1)
            self.assertEqual(override_summary["candidate_event_would_change_selected_count"], 1)
            self.assertEqual(
                override_summary[
                    "candidate_event_with_best_scored_requiring_effective_horizon_expansion_count"
                ],
                0,
            )
            override_row = json.loads(
                (tmp_path / "override" / "branch_score_candidate_coverage_rows.jsonl").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(override_row["best_eligible_scored_pair"], "7,11")
            self.assertAlmostEqual(override_row["best_eligible_scored_required_tie_tolerance"], 0.2)
            self.assertTrue(override_row["would_change_selected"])
            self.assertTrue(override_row["tie_tolerance_overridden"])

    def test_candidate_coverage_can_filter_nonpositive_horizon_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            score_path = tmp_path / "score_rows.json"
            score_path.write_text(
                json.dumps([{"key": "node:0:depth:0:7,11", "branch_score": -0.5}], sort_keys=True),
                encoding="utf-8",
            )
            log_path = tmp_path / "events.jsonl"
            record = {
                "event": "journey_branch_candidates",
                "node_id": 0,
                "depth": 0,
                "tie_tolerance": 0.0,
                "candidate_count": 2,
                "eligible_count": 2,
                "selected": {"task_i": 2, "task_j": 3, "fractionality": 0.5},
                "priority_top": [
                    {"task_i": 2, "task_j": 3, "fractionality": 0.5},
                    {"task_i": 7, "task_j": 11, "fractionality": 0.5},
                ],
            }
            log_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

            raw_summary = build_branch_score_candidate_coverage(
                score_path=score_path,
                log_paths=[log_path],
                output_dir=tmp_path / "raw",
                report=tmp_path / "raw.md",
            )
            self.assertEqual(raw_summary["candidate_event_with_eligible_score_hit_count"], 1)
            self.assertEqual(raw_summary["candidate_event_would_change_selected_count"], 1)

            filtered_summary = build_branch_score_candidate_coverage(
                score_path=score_path,
                log_paths=[log_path],
                output_dir=tmp_path / "filtered",
                report=tmp_path / "filtered.md",
                score_min_score=0.0,
            )
            self.assertEqual(filtered_summary["score_min_score"], 0.0)
            self.assertEqual(filtered_summary["candidate_event_with_eligible_score_hit_count"], 0)
            self.assertEqual(filtered_summary["candidate_event_would_change_selected_count"], 0)
            filtered_row = json.loads(
                (tmp_path / "filtered" / "branch_score_candidate_coverage_rows.jsonl").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIsNone(filtered_row["best_eligible_scored_pair"])
            self.assertFalse(filtered_row["would_change_selected"])


if __name__ == "__main__":
    unittest.main()
