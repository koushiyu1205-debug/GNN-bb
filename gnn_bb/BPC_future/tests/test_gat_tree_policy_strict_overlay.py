from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.apply_gat_tree_policy_strict_overlay import apply_strict_overlay


class GATTreePolicyStrictOverlayTests(unittest.TestCase):
    def test_overlay_adds_state_scoped_positive_and_negative_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = root / "instance.json"
            base_rows = root / "base_rows.json"
            base_rows.write_text(
                json.dumps(
                    [
                        _row(instance, 1, 1, [8, 12], 0.10),
                        _row(instance, 1, 1, [2, 5], 0.80),
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            event_rows = root / "tree_policy_event_rows.jsonl"
            event_rows.write_text(
                "\n".join(
                    json.dumps(row, sort_keys=True)
                    for row in [
                        _event(instance, [8, 12], "controlled_replay_positive", 90.0, 1.0, 0.0),
                        _event(instance, [2, 5], "controlled_replay_hard_negative", -1.0, 0.0, 1.0),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = apply_strict_overlay(
                base_score_rows=base_rows,
                event_rows=[event_rows],
                output_dir=root / "out",
                report=root / "report.md",
                boost_score=0.91,
                suppress_score=0.01,
                min_positive_gain=30.0,
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertFalse(summary["certificate_effect"])
            self.assertFalse(summary["production_ready"])
            self.assertEqual(summary["overlay_counts"]["boost_positive"], 1)
            self.assertEqual(summary["overlay_counts"]["suppress_negative"], 1)
            self.assertEqual(summary["overlay_counts"]["appended_overlay_row"], 2)

            rows = json.loads((root / "out" / "journey_branch_score_rows.json").read_text(encoding="utf-8"))
            state_rows = [row for row in rows if row.get("branch_state_key") == "RF(5,19)=same_vehicle"]
            self.assertEqual(len(state_rows), 2)
            by_pair = {tuple(row["pair"]): row for row in state_rows}
            self.assertEqual(float(by_pair[(8, 12)]["score"]), 0.91)
            self.assertEqual(float(by_pair[(2, 5)]["score"]), 0.01)
            self.assertEqual(
                by_pair[(8, 12)]["state_key"],
                "state:RF(5,19)=same_vehicle::node:1:depth:1:8,12",
            )

    def test_overlay_rehydrates_deep_state_from_source_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = root / "instance.json"
            base_rows = root / "base_rows.json"
            base_rows.write_text("[]\n", encoding="utf-8")
            source_log = root / "source.jsonl"
            source_log.write_text(
                json.dumps(
                    {
                        "event": "journey_node_start",
                        "node_id": 4,
                        "depth": 2,
                        "branch_constraints": [
                            "RF(2,5)=same_vehicle",
                            "RF(17,20)=separate_vehicle",
                        ],
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            event_rows = root / "tree_policy_event_rows.jsonl"
            row = _event(instance, [12, 18], "strong_positive", 120.0, 1.0, 0.0)
            row.pop("ancestor_forced_path")
            row["node_id"] = 4
            row["depth"] = 2
            row["source_log_file"] = str(source_log)
            event_rows.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

            summary = apply_strict_overlay(
                base_score_rows=base_rows,
                event_rows=[event_rows],
                output_dir=root / "out",
                report=root / "report.md",
            )

            self.assertEqual(summary["overlay_counts"]["boost_positive"], 1)
            self.assertNotIn("skipped_missing_state_for_deep_event", summary["overlay_counts"])
            rows = json.loads((root / "out" / "journey_branch_score_rows.json").read_text(encoding="utf-8"))
            self.assertEqual(len(rows), 1)
            self.assertEqual(
                rows[0]["branch_state_key"],
                "RF(2,5)=same_vehicle;RF(17,20)=separate_vehicle",
            )
            self.assertEqual(
                rows[0]["state_key"],
                "state:RF(2,5)=same_vehicle;RF(17,20)=separate_vehicle::node:4:depth:2:12,18",
            )


def _row(instance: Path, node_id: int, depth: int, pair: list[int], score: float) -> dict[str, object]:
    key = f"node:{node_id}:depth:{depth}:{min(pair)},{max(pair)}"
    return {
        "schema_version": "gat_branch_action_score_row_v1",
        "instance": str(instance),
        "instance_key": str(instance),
        "node_id": node_id,
        "depth": depth,
        "pair": [min(pair), max(pair)],
        "task_i": min(pair),
        "task_j": max(pair),
        "key": key,
        "scoped_key": f"{instance}|{key}",
        "score": score,
        "branch_score": score,
    }


def _event(
    instance: Path,
    pair: list[int],
    label_type: str,
    gain: float,
    positive: float,
    hard_negative: float,
) -> dict[str, object]:
    return {
        "schema_version": "journey_tree_policy_event_row_v2",
        "instance": str(instance),
        "node_id": 1,
        "depth": 1,
        "selected_pair": [min(pair), max(pair)],
        "ancestor_forced_path": "force_pair_path:0:5,19=same_vehicle",
        "tree_policy_label_type": label_type,
        "capped_wall_time_gain": gain,
        "full_replay_status": "OPTIMAL" if positive else "EXTERNAL_TIME_LIMIT",
        "y_tree_policy_positive": positive,
        "y_tree_policy_hard_negative": hard_negative,
        "policy_run": f"test_{label_type}",
    }


if __name__ == "__main__":
    unittest.main()
