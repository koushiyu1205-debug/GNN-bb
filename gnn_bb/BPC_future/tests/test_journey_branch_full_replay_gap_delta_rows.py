from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_branch_full_replay_gap_delta_rows import (
    build_gap_delta_rows,
)


class JourneyBranchFullReplayGapDeltaRowsTest(unittest.TestCase):
    def test_right_censored_gap_and_fathom_positive_is_auxiliary_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = "BPC_future/logical_graph/tasks_020/greedy-anchor/a.json"
            baseline_csv = root / "baseline.csv"
            alternative_csv = root / "alternative.csv"
            baseline_log = root / "baseline.jsonl"
            alternative_log = root / "alternative.jsonl"
            _write_result_csv(
                baseline_csv,
                instance=instance,
                status="EXTERNAL_TIME_LIMIT",
                wall_time=600.0,
                gap=0.050,
                primal=573.0,
                dual=547.0,
            )
            _write_result_csv(
                alternative_csv,
                instance=instance,
                status="EXTERNAL_TIME_LIMIT",
                wall_time=600.0,
                gap=0.045,
                primal=570.0,
                dual=547.0,
            )
            _write_log(baseline_log, selected_pair=[17, 20], fathom_count=0, completion_retries=4)
            _write_log(alternative_log, selected_pair=[16, 17], fathom_count=3, completion_retries=5)

            summary = build_gap_delta_rows(
                baseline_results=baseline_csv,
                baseline_log=baseline_log,
                baseline_pair=(17, 20),
                alternatives=[("alt_16_17", (16, 17), alternative_csv, alternative_log)],
                output_dir=root / "out",
                report=root / "report.md",
            )

            self.assertEqual(summary["row_count"], 1)
            self.assertEqual(summary["label_type_counts"], {"weak_gap_fathom_positive": 1})
            rows = _read_jsonl(root / "out" / "branch_counterfactual_delta_rows.jsonl")
            row = rows[0]
            self.assertFalse(row["usable_for_counterfactual_training"])
            self.assertTrue(row["usable_for_gap_aux_training"])
            self.assertTrue(row["right_censored_counterfactual"])
            self.assertEqual(row["counterfactual_label_type"], "weak_gap_fathom_positive")
            self.assertAlmostEqual(row["deltas"]["gap_improvement"], 0.005)
            self.assertAlmostEqual(row["deltas"]["primal_improvement"], 3.0)
            self.assertEqual(row["deltas"]["fathom_gain"], 3.0)
            self.assertEqual(row["deltas"]["completion_bound_final_judge_retry_gain"], -1.0)
            self.assertEqual(row["baseline_raw_row"]["phase2_negative_severity_sum"], 0.45)
            self.assertEqual(row["alternative_raw_row"]["phase2_negative_severity_sum"], 0.45)
            self.assertEqual(row["baseline_raw_row"]["phase2_negative_child_presence_balance_gap"], 0)
            self.assertEqual(row["alternative_raw_row"]["phase2_negative_child_presence_balance_gap"], 0)

    def test_forced_pair_mismatch_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = "BPC_future/logical_graph/tasks_020/greedy-anchor/a.json"
            baseline_csv = root / "baseline.csv"
            alternative_csv = root / "alternative.csv"
            baseline_log = root / "baseline.jsonl"
            alternative_log = root / "alternative.jsonl"
            _write_result_csv(baseline_csv, instance=instance)
            _write_result_csv(alternative_csv, instance=instance)
            _write_log(baseline_log, selected_pair=[17, 20])
            _write_log(alternative_log, selected_pair=[16, 20])

            summary = build_gap_delta_rows(
                baseline_results=baseline_csv,
                baseline_log=baseline_log,
                baseline_pair=(17, 20),
                alternatives=[("alt_16_17", (16, 17), alternative_csv, alternative_log)],
                output_dir=root / "out",
                report=root / "report.md",
            )

            self.assertEqual(summary["row_count"], 0)
            self.assertEqual(summary["skipped_counts"], {"alternative_forced_pair_not_matched": 1})

    def test_both_optimal_wall_gain_becomes_strict_positive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = "BPC_future/logical_graph/tasks_020/random-wave/a.json"
            baseline_csv = root / "baseline.csv"
            alternative_csv = root / "alternative.csv"
            baseline_log = root / "baseline.jsonl"
            alternative_log = root / "alternative.jsonl"
            _write_result_csv(
                baseline_csv,
                instance=instance,
                status="OPTIMAL",
                wall_time=345.182173,
                gap=0.0,
                primal=641.659225,
                dual=641.659225,
                node_count=31,
            )
            _write_result_csv(
                alternative_csv,
                instance=instance,
                status="OPTIMAL",
                wall_time=50.186441,
                gap=0.0,
                primal=641.659225,
                dual=641.659225,
                node_count=3,
            )
            _write_log(
                baseline_log,
                selected_pair=[2, 10],
                branch_count=15,
                fathom_count=16,
                completion_retries=31,
            )
            _write_log(
                alternative_log,
                selected_pair=[3, 10],
                branch_count=1,
                fathom_count=2,
                completion_retries=3,
            )

            summary = build_gap_delta_rows(
                baseline_results=baseline_csv,
                baseline_log=baseline_log,
                baseline_pair=(2, 10),
                alternatives=[("alt_3_10", (3, 10), alternative_csv, alternative_log)],
                output_dir=root / "out",
                report=root / "report.md",
            )

            self.assertEqual(summary["row_count"], 1)
            self.assertEqual(summary["label_type_counts"], {"strong_positive": 1})
            self.assertEqual(summary["strict_full_replay_positive_count"], 1)
            self.assertEqual(summary["counterfactual_training_count"], 1)
            rows = _read_jsonl(root / "out" / "branch_counterfactual_delta_rows.jsonl")
            row = rows[0]
            self.assertEqual(row["counterfactual_label_type"], "strong_positive")
            self.assertTrue(row["usable_for_counterfactual_training"])
            self.assertFalse(row["usable_for_gap_aux_training"])
            self.assertFalse(row["right_censored_counterfactual"])
            self.assertTrue(row["both_optimal"])
            self.assertTrue(row["optimal_objective_match"])
            self.assertAlmostEqual(row["deltas"]["wall_time_gain"], 294.995732)
            self.assertEqual(row["deltas"]["branch_count_delta"], -14.0)
            self.assertEqual(row["deltas"]["completion_bound_final_judge_retry_gain"], 28.0)
            self.assertEqual(row["labels"]["y_counterfactual_wall_improved"], 1.0)


def _write_result_csv(
    path: Path,
    *,
    instance: str,
    status: str = "EXTERNAL_TIME_LIMIT",
    wall_time: float = 600.0,
    gap: float = 0.05,
    primal: float = 573.0,
    dual: float = 547.0,
    node_count: int | str = "",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "instance",
        "status",
        "wall_time",
        "gap",
        "gap_available",
        "gap_source",
        "best_primal_bound",
        "best_dual_bound",
        "primal_bound",
        "dual_bound",
        "node_count",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "instance": instance,
                "status": status,
                "wall_time": wall_time,
                "gap": gap,
                "gap_available": "true",
                "gap_source": "root_corrected_node_bound",
                "best_primal_bound": primal,
                "best_dual_bound": dual,
                "primal_bound": primal,
                "dual_bound": dual,
                "node_count": node_count,
            }
        )


def _write_log(
    path: Path,
    *,
    selected_pair: list[int],
    branch_count: int = 1,
    fathom_count: int = 0,
    completion_retries: int = 0,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    selected = _candidate(*selected_pair)
    records: list[dict[str, object]] = [
        {
            "event": "journey_branch_candidates",
            "node_id": 0,
            "depth": 0,
            "time": 12.0,
            "candidate_count": 3,
            "eligible_count": 3,
            "selected_pair": selected_pair,
            "selected": selected,
            "top": [selected],
            "priority_top": [selected],
        },
        {
            "event": "journey_branch",
            "node_id": 0,
            "depth": 0,
            "selected_pair": selected_pair,
        },
    ]
    records.extend(
        {
            "event": "journey_branch",
            "node_id": index + 1,
            "depth": 1,
            "selected_pair": selected_pair,
        }
        for index in range(max(0, int(branch_count) - 1))
    )
    records.extend({"event": "journey_fathom", "node_id": index + 1, "depth": 1} for index in range(fathom_count))
    records.extend(
        {
            "event": "journey_exact_pricing_completion_bound_retry",
            "node_id": index + 1,
            "depth": 1,
            "retry_class": "completion_bound_final_judge",
        }
        for index in range(completion_retries)
    )
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _candidate(task_i: int, task_j: int) -> dict[str, object]:
    return {
        "task_i": task_i,
        "task_j": task_j,
        "same_mass": 0.5,
        "fractionality": 0.5,
        "support_count": 1,
        "incumbent_relation": True,
        "incumbent_disagreement": 0.5,
        "pool_same_allowed": 300,
        "pool_separate_allowed": 350,
        "pool_max_child_width": 350,
        "pool_total_child_width": 650,
        "pool_balance_gap": 50,
        "phase2_same_child_negative_severity": 0.35,
        "phase2_separate_child_negative_severity": 0.1,
        "phase2_negative_severity_sum": 0.45,
        "phase2_negative_severity_gap": 0.25,
        "phase2_negative_severity_balance_ratio": 0.285714286,
        "phase2_negative_child_presence_balance_gap": 0,
    }


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


if __name__ == "__main__":
    unittest.main()
