from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_branch_score_ab import build_branch_score_ab_audit


class JourneyBranchScoreABAuditTests(unittest.TestCase):
    def test_audit_pairs_csv_rows_and_branch_score_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = "BPC_future/logical_graph/tasks_020/demo/demo_logical_graph.json"
            baseline_csv = tmp_path / "baseline.csv"
            optin_csv = tmp_path / "optin.csv"
            _write_csv(
                baseline_csv,
                instance=instance,
                status="OPTIMAL",
                wall_time=100.0,
                solving_time=90.0,
                node_count=7,
                pricing_calls=30,
                exact_pricing_calls=15,
            )
            _write_csv(
                optin_csv,
                instance=instance,
                status="OPTIMAL",
                wall_time=60.0,
                solving_time=55.0,
                node_count=3,
                pricing_calls=20,
                exact_pricing_calls=9,
            )
            baseline_log_dir = tmp_path / "baseline_logs"
            optin_log_dir = tmp_path / "optin_logs"
            _write_log(
                baseline_log_dir / f"{Path(instance).name}.jsonl",
                priority_mode="fractionality",
                task_i=2,
                task_j=5,
                score=None,
                source=None,
            )
            _write_log(
                optin_log_dir / f"{Path(instance).name}.jsonl",
                priority_mode="branch_score",
                task_i=3,
                task_j=18,
                score=10.0,
                source="node:0:depth:0:3,18",
            )

            summary = build_branch_score_ab_audit(
                baseline_csv=baseline_csv,
                optin_csv=optin_csv,
                baseline_log_dir=baseline_log_dir,
                optin_log_dir=optin_log_dir,
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(summary["paired_instance_count"], 1)
            self.assertEqual(summary["both_optimal_count"], 1)
            self.assertEqual(summary["selected_pair_changed_count"], 1)
            self.assertEqual(summary["branch_score_used_count"], 1)
            self.assertEqual(summary["wall_time_delta_sum"], -40.0)
            self.assertEqual(summary["exact_pricing_calls_delta_sum"], -6.0)

            rows = [
                json.loads(line)
                for line in (tmp_path / "out" / "branch_score_ab_rows.jsonl").read_text().splitlines()
            ]
            self.assertEqual(rows[0]["baseline"]["selected_pair"], [2, 5])
            self.assertEqual(rows[0]["optin"]["selected_pair"], [3, 18])
            self.assertEqual(rows[0]["optin"]["branch_score"], 10.0)
            self.assertEqual(rows[0]["optin"]["branch_score_source"], "node:0:depth:0:3,18")
            self.assertEqual(rows[0]["deltas"]["node_count"], -4.0)
            self.assertIn("official_bound_effect = False", (tmp_path / "report.md").read_text())


def _write_csv(
    path: Path,
    *,
    instance: str,
    status: str,
    wall_time: float,
    solving_time: float,
    node_count: int,
    pricing_calls: int,
    exact_pricing_calls: int,
) -> None:
    fieldnames = [
        "instance",
        "status",
        "external_timeout",
        "wall_time",
        "solving_time",
        "node_count",
        "rmp_solves",
        "pricing_calls",
        "exact_pricing_calls",
        "generated_sequences",
        "evaluated_timed_trips",
        "primal_bound",
        "dual_bound",
        "gap",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "instance": instance,
                "status": status,
                "external_timeout": "false",
                "wall_time": wall_time,
                "solving_time": solving_time,
                "node_count": node_count,
                "rmp_solves": 1,
                "pricing_calls": pricing_calls,
                "exact_pricing_calls": exact_pricing_calls,
                "generated_sequences": 100,
                "evaluated_timed_trips": 50,
                "primal_bound": 1.0,
                "dual_bound": 1.0,
                "gap": 0.0,
            }
        )


def _write_log(
    path: Path,
    *,
    priority_mode: str,
    task_i: int,
    task_j: int,
    score: float | None,
    source: str | None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    selected = {
        "task_i": task_i,
        "task_j": task_j,
        "fractionality": 0.5,
        "branch_score": score,
        "branch_score_source": source,
    }
    records = [
        {
            "event": "journey_branch_candidates",
            "node_id": 0,
            "depth": 0,
            "priority_mode": priority_mode,
            "selected": selected,
            "priority_top": [selected],
        },
        {
            "event": "journey_branch",
            "node_id": 0,
            "depth": 0,
            "left": f"RF({task_i},{task_j})=same_vehicle",
            "right": f"RF({task_i},{task_j})=separate_vehicle",
        },
        {"event": "finish", "status": "OPTIMAL"},
    ]
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
