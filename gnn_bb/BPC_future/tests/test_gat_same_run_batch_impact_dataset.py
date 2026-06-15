from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_gat_same_run_batch_impact_dataset import build_dataset


def _write_jsonl(path: Path, events: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n",
        encoding="utf-8",
    )


def _rmp(cg_iter: int, objective: float) -> dict[str, object]:
    return {
        "event": "journey_rmp",
        "cg_iter": cg_iter,
        "node_id": 0,
        "depth": 0,
        "objective": objective,
        "journeys": 10 + cg_iter,
    }


def _capture(cg_iter: int) -> dict[str, object]:
    return {
        "event": "journey_counterfactual_replay_capture",
        "cg_iter": cg_iter,
        "node_id": 0,
        "depth": 0,
        "pricing_kind": "exact",
        "instance": "toy",
        "instance_path": "toy.json",
        "context_hash": f"ctx-{cg_iter}",
        "true_dual_hash": "dual",
        "cut_hash": "cuts",
        "branch_hash": "branch",
        "forbidden_signature_hash": "forbidden",
        "returned_journey_count": 2,
        "returned_journeys": [
            {
                "task_set": [1, 2],
                "true_reduced_cost": -3.0,
                "sequence": [[1, 2]],
            },
            {
                "task_set": [3],
                "true_reduced_cost": -1.0,
                "sequence": [[3]],
            },
        ],
    }


def _addition(cg_iter: int) -> dict[str, object]:
    return {
        "event": "journey_column_addition",
        "cg_iter": cg_iter,
        "node_id": 0,
        "depth": 0,
        "pricing_kind": "exact",
        "added_journeys": 2,
        "new_journeys": 1,
        "replacement_journeys": 1,
        "new_task_set_count": 1,
        "replacement_task_set_count": 1,
        "active_changed_task_set_count": 1,
        "addition_productivity_class": "active_new_task_set",
    }


class GATSameRunBatchImpactDatasetTests(unittest.TestCase):
    def test_builds_valid_same_run_batch_impact_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            log = tmp / "logs" / "toy.jsonl"
            _write_jsonl(
                log,
                [
                    _rmp(4, 100.0),
                    _capture(4),
                    _addition(4),
                    _rmp(5, 96.5),
                    _capture(5),
                    _addition(5),
                    _rmp(6, 96.5),
                ],
            )

            summary = build_dataset(
                log_roots=[tmp / "logs"],
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            rows = [
                json.loads(line)
                for line in (tmp / "out" / "same_run_batch_impact_rows.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["certificate_ready"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(summary["row_count"], 2)
            self.assertEqual(summary["positive_objective_improvement_count"], 1)
            self.assertEqual(summary["non_improving_objective_count"], 1)
            self.assertEqual(summary["objective_positive_rate"], 0.5)
            self.assertEqual(summary["objective_non_improving_rate"], 0.5)
            self.assertEqual(summary["active_support_changing_count"], 2)
            self.assertEqual(summary["new_task_set_added_count"], 2)
            self.assertEqual(summary["rows_needed_for_training"], 48)
            self.assertEqual(summary["positive_rows_needed_for_training"], 9)
            self.assertEqual(summary["non_improving_rows_needed_for_training"], 9)
            self.assertIn("need_more_same_run_rows", summary["training_blockers"])
            self.assertIn(
                "need_more_non_improving_objective_rows",
                summary["training_blockers"],
            )
            self.assertEqual(
                summary["addition_productivity_class_counts"],
                {"active_new_task_set": 2},
            )
            self.assertFalse(summary["training_ready"])
            self.assertFalse(summary["label_distribution_ready"])
            row = rows[0]
            self.assertTrue(row["same_run_intervention_observed"])
            self.assertTrue(row["training_label_allowed"])
            self.assertEqual(row["label_objective_improved"], 1)
            self.assertEqual(row["label_active_support_changing"], 1)
            self.assertEqual(row["best_true_reduced_cost"], -3.0)
            self.assertEqual(row["candidate_task_set_samples"], [[1, 2], [3]])
            self.assertEqual(row["training_label_scope"], "same_run_returned_batch")

    def test_missing_addition_or_next_rmp_does_not_create_training_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            log = tmp / "logs" / "toy.jsonl"
            _write_jsonl(log, [_rmp(4, 100.0), _capture(4)])

            summary = build_dataset(
                log_roots=[tmp / "logs"],
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            self.assertFalse(summary["all_checks_pass"])
            self.assertEqual(summary["row_count"], 0)
            self.assertEqual(
                summary["skipped_counts"],
                {"missing_matching_column_addition": 1},
            )


if __name__ == "__main__":
    unittest.main()
