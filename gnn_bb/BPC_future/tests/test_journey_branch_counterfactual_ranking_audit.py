from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_branch_counterfactual_ranking import build_ranking_audit


class JourneyBranchCounterfactualRankingAuditTests(unittest.TestCase):
    def test_builds_same_parent_ranking_pairs_and_proxy_contradictions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            delta_dir = tmp_path / "delta"
            delta_dir.mkdir()
            rows = [
                _delta_row(
                    "01_fast",
                    baseline_pair=[2, 5],
                    alternative_pair=[3, 18],
                    wall_delta=-10.0,
                    exact_delta=-2,
                    child_negative_delta=1,
                    wall_improved=True,
                    proof_improved=True,
                ),
                _delta_row(
                    "02_slow",
                    baseline_pair=[2, 5],
                    alternative_pair=[5, 8],
                    wall_delta=20.0,
                    exact_delta=5,
                    child_negative_delta=-3,
                    regression=True,
                ),
                _delta_row(
                    "03_other",
                    node_id=1,
                    baseline_pair=[4, 7],
                    alternative_pair=[4, 8],
                    wall_delta=0.2,
                    exact_delta=0,
                ),
            ]
            (delta_dir / "branch_counterfactual_delta_rows.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_ranking_audit(
                [delta_dir],
                tmp_path / "out",
                tmp_path / "report.md",
                min_wall_gap=1.0,
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(summary["counterfactual_row_count"], 3)
            self.assertEqual(summary["context_count"], 2)
            self.assertEqual(summary["ranking_pair_count"], 1)
            self.assertTrue(summary["minimal_ranking_signal_ready"])
            self.assertFalse(summary["strict_ranking_training_ready"])
            self.assertFalse(summary["ranking_training_ready"])
            self.assertEqual(summary["strong_positive_count"], 1)
            self.assertEqual(summary["strong_positive_context_count"], 1)
            self.assertEqual(summary["positive_holdout_context_count"], 0)
            self.assertEqual(summary["label_counts"]["wall_improved"], 1)
            self.assertEqual(summary["label_counts"]["regression"], 1)
            self.assertEqual(
                summary["proxy_contradiction_counts"],
                {
                    "fewer_child_negative_but_regressed": 1,
                    "more_child_negative_but_wall_improved": 1,
                },
            )

            ranking_rows = _read_jsonl(tmp_path / "out" / "counterfactual_ranking_pair_rows.jsonl")
            self.assertEqual(len(ranking_rows), 1)
            self.assertEqual(ranking_rows[0]["better"]["entry_id"], "01")
            self.assertEqual(ranking_rows[0]["worse"]["entry_id"], "02")
            self.assertEqual(ranking_rows[0]["preference_reason"], "wall_time_delta")
            self.assertIn("official_bound_effect = False", (tmp_path / "report.md").read_text())

    def test_exact_pricing_gap_can_create_pair_when_wall_gap_is_small(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            delta_file = tmp_path / "rows.jsonl"
            rows = [
                _delta_row("a", alternative_pair=[1, 3], wall_delta=0.1, exact_delta=0),
                _delta_row("b", alternative_pair=[1, 4], wall_delta=0.2, exact_delta=4),
            ]
            delta_file.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_ranking_audit(
                [delta_file],
                tmp_path / "out",
                tmp_path / "report.md",
                min_wall_gap=1.0,
                min_exact_pricing_gap=1,
            )

            self.assertEqual(summary["ranking_pair_count"], 1)
            ranking_rows = _read_jsonl(tmp_path / "out" / "counterfactual_ranking_pair_rows.jsonl")
            self.assertEqual(ranking_rows[0]["preference_reason"], "exact_pricing_calls_delta")
            self.assertEqual(ranking_rows[0]["better"]["entry_id"], "a")

    def test_strict_training_ready_requires_context_instance_family_and_holdout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            delta_file = tmp_path / "rows.jsonl"
            rows = [
                _delta_row(
                    "ga_pos_1",
                    instance="BPC_future/logical_graph/tasks_020/greedy-anchor/a/a.json",
                    alternative_pair=[1, 3],
                    wall_delta=-10.0,
                    exact_delta=-2,
                    wall_improved=True,
                    proof_improved=True,
                    holdout=True,
                ),
                _delta_row(
                    "ga_pos_2",
                    instance="BPC_future/logical_graph/tasks_020/greedy-anchor/a/a.json",
                    alternative_pair=[1, 4],
                    wall_delta=-8.0,
                    exact_delta=-1,
                    wall_improved=True,
                    proof_improved=True,
                ),
                _delta_row(
                    "ga_reg_1",
                    instance="BPC_future/logical_graph/tasks_020/greedy-anchor/a/a.json",
                    alternative_pair=[1, 5],
                    wall_delta=20.0,
                    exact_delta=3,
                    regression=True,
                ),
                _delta_row(
                    "ga_reg_2",
                    instance="BPC_future/logical_graph/tasks_020/greedy-anchor/a/a.json",
                    alternative_pair=[1, 6],
                    wall_delta=22.0,
                    exact_delta=4,
                    regression=True,
                ),
                _delta_row(
                    "rw_pos_1",
                    instance="BPC_future/logical_graph/tasks_020/random-wave/b/b.json",
                    baseline_pair=[2, 6],
                    alternative_pair=[2, 7],
                    wall_delta=-9.0,
                    exact_delta=-2,
                    wall_improved=True,
                    proof_improved=True,
                ),
                _delta_row(
                    "rw_pos_2",
                    instance="BPC_future/logical_graph/tasks_020/random-wave/b/b.json",
                    baseline_pair=[2, 6],
                    alternative_pair=[2, 8],
                    wall_delta=-7.0,
                    exact_delta=-1,
                    wall_improved=True,
                    proof_improved=True,
                ),
                _delta_row(
                    "rw_reg_1",
                    instance="BPC_future/logical_graph/tasks_020/random-wave/b/b.json",
                    baseline_pair=[2, 6],
                    alternative_pair=[2, 9],
                    wall_delta=18.0,
                    exact_delta=3,
                    regression=True,
                ),
                _delta_row(
                    "rw_reg_2",
                    instance="BPC_future/logical_graph/tasks_020/random-wave/b/b.json",
                    baseline_pair=[2, 6],
                    alternative_pair=[2, 10],
                    wall_delta=19.0,
                    exact_delta=4,
                    regression=True,
                ),
                _delta_row(
                    "sw_pos_1",
                    instance="BPC_future/logical_graph/tasks_020/sector-wave/c/c.json",
                    node_id=1,
                    baseline_pair=[3, 7],
                    alternative_pair=[3, 8],
                    wall_delta=-6.0,
                    exact_delta=-1,
                    wall_improved=True,
                    proof_improved=True,
                ),
                _delta_row(
                    "sw_reg_1",
                    instance="BPC_future/logical_graph/tasks_020/sector-wave/c/c.json",
                    node_id=1,
                    baseline_pair=[3, 7],
                    alternative_pair=[3, 9],
                    wall_delta=16.0,
                    exact_delta=2,
                    regression=True,
                ),
            ]
            delta_file.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_ranking_audit(
                [delta_file],
                tmp_path / "out",
                tmp_path / "report.md",
                min_wall_gap=1.0,
            )

            self.assertTrue(summary["minimal_ranking_signal_ready"])
            self.assertTrue(summary["strict_ranking_training_ready"])
            self.assertTrue(summary["ranking_training_ready"])
            self.assertEqual(summary["strong_positive_count"], 5)
            self.assertEqual(summary["strong_positive_context_count"], 3)
            self.assertEqual(summary["strong_positive_instance_count"], 3)
            self.assertEqual(summary["strong_positive_time_window_family_count"], 3)
            self.assertEqual(summary["positive_holdout_context_count"], 1)

    def test_holdout_instance_filter_counts_context_once_and_reports_train_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            delta_file = tmp_path / "rows.jsonl"
            rows = [
                _delta_row(
                    "holdout_pos_1",
                    instance=(
                        "BPC_future/logical_graph/tasks_020/sector-wave/"
                        "holdout_instance/holdout_instance.json"
                    ),
                    alternative_pair=[1, 3],
                    wall_delta=-10.0,
                    exact_delta=-2,
                    wall_improved=True,
                    proof_improved=True,
                ),
                _delta_row(
                    "holdout_pos_2",
                    instance=(
                        "BPC_future/logical_graph/tasks_020/sector-wave/"
                        "holdout_instance/holdout_instance.json"
                    ),
                    alternative_pair=[1, 4],
                    wall_delta=-8.0,
                    exact_delta=-1,
                    wall_improved=True,
                    proof_improved=True,
                ),
                _delta_row(
                    "train_pos",
                    instance=(
                        "BPC_future/logical_graph/tasks_020/greedy-anchor/"
                        "train_instance/train_instance.json"
                    ),
                    baseline_pair=[2, 6],
                    alternative_pair=[2, 7],
                    wall_delta=-7.0,
                    exact_delta=-1,
                    wall_improved=True,
                    proof_improved=True,
                ),
                _delta_row(
                    "train_reg",
                    instance=(
                        "BPC_future/logical_graph/tasks_020/greedy-anchor/"
                        "train_instance/train_instance.json"
                    ),
                    baseline_pair=[2, 6],
                    alternative_pair=[2, 8],
                    wall_delta=9.0,
                    exact_delta=2,
                    regression=True,
                ),
            ]
            delta_file.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_ranking_audit(
                [delta_file],
                tmp_path / "out",
                tmp_path / "report.md",
                min_wall_gap=1.0,
                positive_holdout_instance_contains=("holdout_instance",),
            )

            self.assertEqual(summary["positive_holdout_context_count"], 1)
            self.assertEqual(summary["holdout_strong_positive_count"], 2)
            self.assertEqual(summary["training_strong_positive_count"], 1)
            self.assertEqual(summary["training_strong_positive_context_count"], 1)
            self.assertEqual(summary["training_strong_positive_instance_count"], 1)
            self.assertEqual(summary["training_strong_positive_time_window_family_count"], 1)
            self.assertEqual(summary["training_regression_count"], 1)
            self.assertTrue(summary["training_regression_at_least_positive"])
            self.assertFalse(summary["strict_ranking_training_ready"])


def _delta_row(
    experiment: str,
    *,
    instance: str = "BPC_future/logical_graph/tasks_020/demo/demo.json",
    node_id: int = 0,
    depth: int = 0,
    baseline_pair: list[int] | None = None,
    alternative_pair: list[int] | None = None,
    wall_delta: float = 0.0,
    exact_delta: int = 0,
    node_delta: int = 0,
    pricing_delta: int = 0,
    child_negative_delta: int = 0,
    wall_improved: bool = False,
    proof_improved: bool = False,
    regression: bool = False,
    holdout: bool = False,
) -> dict[str, object]:
    return {
        "schema_version": "journey_branch_counterfactual_delta_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "experiment": experiment,
        "instance": instance,
        "node_id": node_id,
        "depth": depth,
        "baseline_pair": baseline_pair or [2, 5],
        "alternative_pair": alternative_pair or [3, 18],
        "alternative_forced_pair_matched": True,
        "counterfactual_label_type": (
            "strong_positive"
            if wall_improved
            else "regression"
            if regression
            else "observed_neutral"
        ),
        "positive_holdout_context": holdout,
        "deltas": {
            "wall_time_delta": wall_delta,
            "exact_pricing_calls_delta": exact_delta,
            "node_count_delta": node_delta,
            "pricing_calls_delta": pricing_delta,
            "child_negative_pricing_events_delta": child_negative_delta,
        },
        "labels": {
            "y_counterfactual_wall_improved": 1.0 if wall_improved else 0.0,
            "y_counterfactual_proof_cost_improved": 1.0 if proof_improved else 0.0,
            "y_counterfactual_regression": 1.0 if regression else 0.0,
        },
    }


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


if __name__ == "__main__":
    unittest.main()
