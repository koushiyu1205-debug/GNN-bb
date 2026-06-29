from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.summarize_journey_child_order_paired_runbook import (
    summarize_child_order_paired,
)


class JourneyChildOrderPairedSummaryTests(unittest.TestCase):
    def test_summarizes_child_order_pairs_and_prefers_valid_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runbook_dir = root / "runbook"
            runs = runbook_dir / "runs"
            extra = root / "extra"
            entries = [
                _entry("same_old", "same_vehicle"),
                _entry("separate", "separate_vehicle"),
            ]
            runbook_dir.mkdir(parents=True)
            (runbook_dir / "runbook.json").write_text(
                json.dumps({"entries": entries}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            _write_result(runs / "same_old" / "results.csv", wall=20.0, gap_available=False)
            _write_log(runs / "same_old" / "logs" / "instance.json.jsonl", target_seen=False)
            _write_result(extra / "same_replay" / "results.csv", wall=90.0, gap_available=True)
            _write_log(extra / "same_replay" / "logs" / "instance.json.jsonl", target_seen=True, first="same_vehicle")
            _write_result(runs / "separate" / "results.csv", wall=75.0, gap_available=True)
            _write_log(runs / "separate" / "logs" / "instance.json.jsonl", target_seen=True, first="separate_vehicle")

            summary = summarize_child_order_paired(
                runbook_dir / "runbook.json",
                root / "out",
                root / "report.md",
                extra_run_roots=[extra],
            )

            self.assertEqual(summary["paired_group_count"], 1)
            self.assertEqual(summary["valid_paired_group_count"], 1)
            rows = [
                json.loads(line)
                for line in (root / "out" / "child_order_paired_rows.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            by_kind = {row["target_child_kind"]: row for row in rows}
            self.assertEqual(by_kind["same_vehicle"]["experiment"], "same_replay")
            self.assertTrue(by_kind["same_vehicle"]["target_branch_seen"])
            self.assertAlmostEqual(by_kind["separate_vehicle"]["paired_wall_time_gain"], 15.0)
            self.assertEqual(
                by_kind["separate_vehicle"]["paired_label_type"],
                "positive_child_order_proxy",
            )
            self.assertEqual(
                by_kind["same_vehicle"]["paired_label_type"],
                "hard_negative_child_order_proxy",
            )
            report = (root / "report.md").read_text(encoding="utf-8")
            self.assertIn("valid_paired_group_count", report)


def _entry(experiment: str, target_kind: str) -> dict[str, object]:
    return {
        "experiment": experiment,
        "instance": "instance.json",
        "source_depth": 1,
        "source_pair": [1, 2],
        "target_child_kind": target_kind,
        "pair_group_id": "instance__d1__n1__1_2",
        "pair_role": f"{target_kind}_first",
        "source_first_child_kind": "same_vehicle",
    }


def _write_result(path: Path, *, wall: float, gap_available: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "instance,status,wall_time,solving_time,gap_available,gap,node_count,columns,pricing_calls,exact_pricing_calls,generated_sequences\n"
        f"instance.json,TIME_LIMIT,{wall},{wall - 1.0},{str(gap_available).lower()},0.1,1,2,3,4,5\n",
        encoding="utf-8",
    )


def _write_log(path: Path, *, target_seen: bool, first: str = "same_vehicle") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    other = "separate_vehicle" if first == "same_vehicle" else "same_vehicle"
    rows: list[dict[str, object]] = [
        {"event": "journey_branch_candidates", "depth": 0, "forced_pair": [3, 4]},
        {"event": "journey_branch", "depth": 0, "selected_pair": [3, 4], "branch_constraints": []},
    ]
    if target_seen:
        rows.extend(
            [
                {"event": "journey_branch_candidates", "depth": 1, "forced_pair": [1, 2]},
                {"event": "journey_branch", "depth": 1, "selected_pair": [1, 2], "branch_constraints": ["RF(3,4)=same_vehicle"]},
                {"event": "journey_exact_pricing_completion_bound_retry", "depth": 1, "node_id": 1},
                {"event": "journey_branch", "depth": 2, "selected_pair": [1, 3], "branch_constraints": [f"RF(1,2)={first}"], "time": 10.0},
                {"event": "journey_branch", "depth": 2, "selected_pair": [1, 4], "branch_constraints": [f"RF(1,2)={other}"], "time": 20.0},
            ]
        )
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
