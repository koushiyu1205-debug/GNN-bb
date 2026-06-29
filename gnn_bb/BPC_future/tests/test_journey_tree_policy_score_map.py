import csv
import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_tree_policy_score_map import build_tree_policy_score_map


class JourneyTreePolicyScoreMapTests(unittest.TestCase):
    def test_aggregates_depth_scoped_branch_and_child_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = (
                root
                / "logs"
                / "BPC_future"
                / "logical_graph"
                / "tasks_020"
                / "random-wave"
                / "apollo15_20km"
                / "case.json.jsonl"
            )
            log.parent.mkdir(parents=True)
            events = [
                {
                    "event": "journey_branch",
                    "node_id": 4,
                    "depth": 2,
                    "left": "RF(3,9)=same_vehicle",
                    "right": "RF(3,9)=separate_vehicle",
                    "time": 20.0,
                },
                {
                    "event": "journey_child_queued",
                    "parent_node_id": 4,
                    "child_node_id": 5,
                    "depth": 3,
                    "constraint": "RF(3,9)=separate_vehicle",
                },
                {
                    "event": "journey_child_queued",
                    "parent_node_id": 4,
                    "child_node_id": 6,
                    "depth": 3,
                    "constraint": "RF(3,9)=same_vehicle",
                },
            ]
            log.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")

            output_dir = root / "out"
            report = root / "report.md"
            summary = build_tree_policy_score_map(
                [log],
                output_dir,
                report,
                key_scope="depth",
                context_scope="family_site",
            )

            self.assertEqual(summary["branch_score_row_count"], 1)
            self.assertEqual(summary["child_score_row_count"], 2)
            self.assertFalse(summary["official_bound_effect"])
            self.assertFalse(summary["certificate_effect"])
            branch_rows = json.loads((output_dir / "journey_branch_tree_policy_score_rows.json").read_text())
            child_rows = json.loads((output_dir / "journey_child_tree_policy_score_rows.json").read_text())
            self.assertEqual(branch_rows[0]["scope"], "random-wave/apollo15_20km")
            self.assertEqual(branch_rows[0]["depth"], 2)
            self.assertNotIn("node_id", branch_rows[0])
            self.assertEqual(branch_rows[0]["pair"], [3, 9])
            self.assertEqual(child_rows[0]["child_constraint_kind"], "separate_vehicle")
            self.assertGreater(child_rows[0]["score"], child_rows[1]["score"])


if __name__ == "__main__":
    unittest.main()
