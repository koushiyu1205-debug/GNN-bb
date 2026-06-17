from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_gat_batch_impact_false_delay_context_plan import (
    build_false_delay_context_plan,
    build_false_delay_context_priority_rows,
)
from BPC_future.tests.test_gat_batch_impact_multibatch_intervention_plan import (
    _capture_event,
    _graph_path,
    _journey,
    _write_jsonl,
    _write_manifest,
)


class GATBatchImpactFalseDelayContextPlanTests(unittest.TestCase):
    def test_builds_false_delay_context_priority_rows(self):
        rows = build_false_delay_context_priority_rows(
            [
                {
                    "context_hash": "ctx-small",
                    "family": "sector-wave",
                    "task_counts": [20],
                    "false_high_priority_on_delay_count": 2,
                    "candidate_signature_ids": ["a"],
                    "batch_record_count": 4,
                    "accepted_batch_count": 1,
                    "max_accepted_batch_roi_label": -1.0,
                    "max_delay_risk_score": 0.4,
                    "median_delay_risk_score": 0.3,
                    "median_raw_high_priority_score": 0.5,
                },
                {
                    "context_hash": "ctx-large",
                    "family": "sector-wave",
                    "task_counts": [20],
                    "false_high_priority_on_delay_count": 5,
                    "candidate_signature_ids": ["a", "b"],
                    "batch_record_count": 2,
                    "accepted_batch_count": 0,
                    "max_accepted_batch_roi_label": 0.0,
                },
                {
                    "context_hash": "ctx-random",
                    "family": "random-wave",
                    "task_counts": [20],
                    "false_high_priority_on_delay_count": 99,
                },
            ]
        )

        self.assertEqual([row["context_hash"] for row in rows], ["ctx-large", "ctx-small"])
        self.assertEqual(rows[0]["schema_version"], "gat_batch_impact_false_delay_context_priority_v1")
        self.assertEqual(rows[0]["primary_blocker"], "context_local_false_delay_ranking")
        self.assertFalse(rows[0]["is_high_roi_opportunity"])
        self.assertFalse(rows[0]["is_missed_high_roi_opportunity"])
        self.assertFalse(rows[0]["runs_bpc_or_pricing"])
        self.assertFalse(rows[0]["selector_can_certificate"])
        self.assertFalse(rows[0]["gate_can_permanently_discard_negative_columns"])
        self.assertEqual(
            rows[0]["context_false_delay_false_high_priority_on_delay_count"],
            5,
        )

    def test_builds_context_local_intervention_plan_from_false_delay_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph_path = _graph_path(root)
            source_log = root / "capture.jsonl"
            dataset_dir = root / "dataset"
            false_summary_path = root / "false_summary.json"
            context_summary_path = root / "context_summary.jsonl"
            output_dir = root / "plan"
            report = root / "report.md"
            context_hash = "ctx-false-delay"

            _write_jsonl(
                source_log,
                [
                    _capture_event(
                        graph_path=graph_path,
                        context_hash=context_hash,
                        returned=[
                            _journey([1], -4.0, "low_risk"),
                            _journey([2, 3], -2.5, "low_time"),
                            _journey([4], 0.5, "low_energy"),
                        ],
                    )
                ],
            )
            _write_manifest(
                dataset_dir,
                source_log=source_log,
                graph_path=graph_path,
                context_hash=context_hash,
                candidate_count=3,
                accepted_batch_roi=0.0,
            )
            false_summary_path.write_text(
                json.dumps(
                    {
                        "schema_version": "gat_batch_impact_false_positive_catalog_v1",
                        "diagnostic_only": True,
                        "runs_bpc_or_pricing": False,
                        "false_high_priority_on_delay_count": 2,
                        "false_high_priority_on_delay": 0.4,
                        "context_false_positive_count": 1,
                        "family_task_counts": {"sector-wave|20": 2},
                        "candidate_threshold_zero": True,
                        "diagnosis": {
                            "primary": "raise_candidate_threshold_or_make_candidate_head_usable_before_delay_gate"
                        },
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            _write_jsonl(
                context_summary_path,
                [
                    {
                        "context_hash": context_hash,
                        "family": "sector-wave",
                        "task_counts": [20],
                        "false_high_priority_on_delay_count": 2,
                        "candidate_signature_ids": ["sig-a", "sig-b"],
                        "batch_record_count": 3,
                        "accepted_batch_count": 1,
                        "instances": [graph_path.stem],
                        "max_accepted_batch_roi_label": 0.0,
                        "max_delay_risk_score": 0.44,
                        "median_delay_risk_score": 0.41,
                        "median_raw_high_priority_score": 0.53,
                    }
                ],
            )

            summary = build_false_delay_context_plan(
                false_positive_summary=false_summary_path,
                context_summary_jsonl=context_summary_path,
                dataset_dir=dataset_dir,
                output_dir=output_dir,
                report=report,
                max_contexts=1,
                targets_per_context=2,
                min_negative_targets_per_context=2,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["status"], "ready")
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["certificate_ready"])
            self.assertEqual(summary["context_priority_row_count"], 1)
            self.assertEqual(summary["intervention_selected_context_count"], 1)
            self.assertEqual(summary["intervention_pairwise_context_target_count"], 1)
            self.assertEqual(summary["intervention_candidate_count"], 2)
            self.assertTrue((output_dir / "false_delay_context_priority.jsonl").exists())
            self.assertTrue((output_dir / "multibatch_intervention_plan" / "candidates.json").exists())
            self.assertTrue(report.exists())

            priority_rows = [
                json.loads(line)
                for line in (output_dir / "false_delay_context_priority.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            self.assertEqual(priority_rows[0]["context_hash"], context_hash)
            self.assertEqual(
                priority_rows[0]["primary_action"],
                "collect_same_context_false_delay_hard_negative_contrast",
            )
            candidates = json.loads(
                (output_dir / "multibatch_intervention_plan" / "candidates.json").read_text(
                    encoding="utf-8"
                )
            )["candidates"]
            self.assertEqual({candidate["expected_context_hash"] for candidate in candidates}, {context_hash})
            self.assertTrue(all(float(candidate["best_true_reduced_cost"]) < 0.0 for candidate in candidates))
            self.assertTrue(
                all(
                    candidate["context_false_delay_false_high_priority_on_delay_count"] == 2
                    for candidate in candidates
                )
            )


if __name__ == "__main__":
    unittest.main()
