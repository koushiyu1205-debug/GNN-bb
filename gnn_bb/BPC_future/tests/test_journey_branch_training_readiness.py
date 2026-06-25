from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_branch_training_readiness import (
    build_training_readiness,
)


class JourneyBranchTrainingReadinessTests(unittest.TestCase):
    def test_separates_target_200_positive_from_weak_full_replay_positive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            delta_dir = tmp_path / "delta"
            delta_dir.mkdir()
            rows = []
            for idx in range(10):
                family = "greedy-anchor" if idx < 5 else "sector-wave"
                instance_id = idx % 3
                rows.append(
                    _row(
                        f"pos_{idx}",
                        instance=(
                            "BPC_future/logical_graph/tasks_020/"
                            f"{family}/case_{instance_id}/seed_{idx}.json"
                        ),
                        label_type="strong_positive",
                        baseline_status="OPTIMAL",
                        alternative_status="OPTIMAL",
                        baseline_wall=260.0,
                        alternative_wall=180.0 if idx < 4 else 225.0,
                        alternative_pair=[1, idx + 2],
                        wall_improved=True,
                    )
                )
            for idx in range(5):
                rows.append(
                    _row(
                        f"reg_{idx}",
                        instance=(
                            "BPC_future/logical_graph/tasks_020/"
                            f"sector-wave/regression/seed_{idx}.json"
                        ),
                        label_type="regression",
                        baseline_status="OPTIMAL",
                        alternative_status="TIME_LIMIT",
                        baseline_wall=220.0,
                        alternative_wall=300.0,
                        alternative_pair=[2, idx + 3],
                        regression=True,
                    )
                )
            rows.append(
                _row(
                    "local_only",
                    label_type="local_only_hard_negative",
                    baseline_status="EXTERNAL_TIME_LIMIT",
                    alternative_status="EXTERNAL_TIME_LIMIT",
                    baseline_wall=220.0,
                    alternative_wall=220.0,
                    alternative_pair=[8, 9],
                    local_only=True,
                    right_censored=True,
                )
            )
            _write_jsonl(delta_dir / "branch_counterfactual_delta_rows.jsonl", rows)

            summary = build_training_readiness(
                [delta_dir],
                tmp_path / "out",
                tmp_path / "report.md",
                target_wall=200.0,
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertEqual(summary["strict_full_replay_positive_count"], 10)
            self.assertEqual(summary["target_200_positive_count"], 4)
            self.assertEqual(summary["weak_positive_not_target_count"], 6)
            self.assertEqual(summary["regression_count"], 5)
            self.assertEqual(summary["hard_negative_count"], 5)
            self.assertEqual(summary["local_only_hard_negative_count"], 1)
            self.assertTrue(summary["pipeline_debug_training_ready"])
            self.assertTrue(summary["sanity_training_ready"])
            self.assertFalse(summary["serious_training_ready"])
            self.assertTrue(
                all(value == 0 for value in summary["missing_for_pipeline_debug_training"].values())
            )
            self.assertEqual(summary["serious_training_requirements"]["target_200_positive_min"], 20)
            self.assertEqual(summary["missing_for_serious_training"]["target_200_positive_min"], 16)
            self.assertEqual(summary["missing_for_serious_training"]["hard_negative_min"], 25)
            self.assertEqual(summary["remaining_for_serious_training"]["target_200_positive_min"], 16)
            self.assertEqual(summary["remaining_for_serious_training"]["hard_negative_min"], 25)
            self.assertTrue((tmp_path / "out" / "summary.json").exists())
            self.assertTrue((tmp_path / "out" / "branch_training_readiness_rows.jsonl").exists())
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("target_200_positive_count = 4", report)
            self.assertIn("pipeline_debug_training_ready = true", report)
            self.assertIn("remaining_for_serious_training", report)
            self.assertIn("official_bound_effect = false", report)

    def test_target_positive_requires_alternative_optimal_and_baseline_over_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            rows = [
                _row(
                    "already_fast",
                    label_type="strong_positive",
                    baseline_status="OPTIMAL",
                    alternative_status="OPTIMAL",
                    baseline_wall=190.0,
                    alternative_wall=150.0,
                    wall_improved=True,
                ),
                _row(
                    "nonoptimal_fast_wall",
                    label_type="strong_positive",
                    baseline_status="OPTIMAL",
                    alternative_status="TIME_LIMIT",
                    baseline_wall=260.0,
                    alternative_wall=150.0,
                    wall_improved=True,
                ),
                _row(
                    "crossed",
                    label_type="strong_positive",
                    baseline_status="OPTIMAL",
                    alternative_status="OPTIMAL",
                    baseline_wall=260.0,
                    alternative_wall=150.0,
                    wall_improved=True,
                    alternative_pair=[3, 4],
                ),
            ]
            delta_file = tmp_path / "rows.jsonl"
            _write_jsonl(delta_file, rows)

            summary = build_training_readiness(
                [delta_file],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertEqual(summary["strict_full_replay_positive_count"], 2)
            self.assertEqual(summary["target_200_positive_count"], 1)
            self.assertFalse(summary["pipeline_debug_training_ready"])
            self.assertEqual(summary["missing_for_pipeline_debug_training"]["strict_full_replay_positive_min"], 3)
            normalized = _read_jsonl(tmp_path / "out" / "branch_training_readiness_rows.jsonl")
            by_experiment = {row["experiment"]: row for row in normalized}
            self.assertFalse(by_experiment["already_fast"]["target_200_positive"])
            self.assertFalse(by_experiment["nonoptimal_fast_wall"]["target_200_positive"])
            self.assertTrue(by_experiment["crossed"]["target_200_positive"])


def _row(
    experiment: str,
    *,
    instance: str = "BPC_future/logical_graph/tasks_020/greedy-anchor/demo/demo.json",
    label_type: str,
    baseline_status: str,
    alternative_status: str,
    baseline_wall: float,
    alternative_wall: float,
    baseline_pair: list[int] | None = None,
    alternative_pair: list[int] | None = None,
    wall_improved: bool = False,
    regression: bool = False,
    local_only: bool = False,
    right_censored: bool = False,
) -> dict[str, object]:
    labels = {
        "y_counterfactual_wall_improved": 1.0 if wall_improved else 0.0,
        "y_counterfactual_regression": 1.0 if regression else 0.0,
        "y_counterfactual_local_improved_but_whole_run_not": 1.0 if local_only else 0.0,
        "y_counterfactual_right_censored": 1.0 if right_censored else 0.0,
    }
    return {
        "schema_version": "journey_branch_counterfactual_delta_v4",
        "experiment": experiment,
        "instance": instance,
        "node_id": 0,
        "depth": 0,
        "baseline_pair": baseline_pair or [1, 2],
        "alternative_pair": alternative_pair or [1, 3],
        "baseline_status": baseline_status,
        "alternative_status": alternative_status,
        "baseline_wall_time": baseline_wall,
        "alternative_wall_time": alternative_wall,
        "alternative_forced_pair_matched": True,
        "right_censored_counterfactual": right_censored,
        "timeout_resolved": False,
        "timeout_regression": bool(regression and alternative_status != "OPTIMAL"),
        "usable_for_counterfactual_training": not right_censored,
        "counterfactual_label_type": label_type,
        "labels": labels,
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


if __name__ == "__main__":
    unittest.main()
