from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_branch_child_probe_proxy_ranking import build_proxy_ranking


class JourneyBranchChildProbeProxyRankingTests(unittest.TestCase):
    def test_builds_same_parent_proxy_ranking_from_child_probe_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            probe_dir = tmp_path / "probe"
            probe_dir.mkdir()
            rows = [
                _child_probe_row(
                    log_file="run_a/logs/BPC_future/logical_graph/tasks_020/demo/demo.json.jsonl",
                    pair=[2, 9],
                    child_node_id=1,
                    fathomed=True,
                    corrected_gain=3.0,
                    retries=4.0,
                    proof_cpu=40.0,
                    negative_events=4.0,
                ),
                _child_probe_row(
                    log_file="run_a/logs/BPC_future/logical_graph/tasks_020/demo/demo.json.jsonl",
                    pair=[2, 9],
                    child_node_id=2,
                    fathomed=False,
                    corrected_gain=0.0,
                    retries=1.0,
                    proof_cpu=12.0,
                    negative_events=1.0,
                ),
                _child_probe_row(
                    log_file="run_b/logs/BPC_future/logical_graph/tasks_020/demo/demo.json.jsonl",
                    pair=[4, 5],
                    child_node_id=1,
                    fathomed=False,
                    corrected_gain=0.0,
                    retries=8.0,
                    proof_cpu=70.0,
                    negative_events=9.0,
                ),
                _child_probe_row(
                    log_file="run_b/logs/BPC_future/logical_graph/tasks_020/demo/demo.json.jsonl",
                    pair=[4, 5],
                    child_node_id=2,
                    fathomed=False,
                    corrected_gain=0.0,
                    retries=2.0,
                    proof_cpu=20.0,
                    negative_events=2.0,
                ),
            ]
            (probe_dir / "child_probe_rows.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_proxy_ranking(
                [probe_dir],
                tmp_path / "out",
                tmp_path / "report.md",
                min_proxy_score_gap=0.05,
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["ranking_training_ready"])
            self.assertTrue(summary["sampling_navigation_ready"])
            self.assertEqual(summary["raw_child_probe_row_count"], 4)
            self.assertEqual(summary["proxy_branch_row_count"], 2)
            self.assertEqual(summary["proxy_context_count"], 1)
            self.assertEqual(summary["proxy_ranking_pair_count"], 1)
            self.assertEqual(summary["right_censored_proxy_ranking_pair_count"], 1)
            self.assertEqual(summary["promotion_ready_branch_count"], 0)
            self.assertEqual(summary["promotion_blocked_branch_count"], 2)
            self.assertEqual(
                summary["promotion_blocked_reason_counts"],
                {"proxy_score_below_promotion_threshold": 2},
            )

            ranking_rows = _read_jsonl(tmp_path / "out" / "child_probe_proxy_ranking_pair_rows.jsonl")
            self.assertEqual(len(ranking_rows), 1)
            self.assertEqual(ranking_rows[0]["better"]["alternative_pair"], [2, 9])
            self.assertEqual(ranking_rows[0]["worse"]["alternative_pair"], [4, 5])
            self.assertEqual(ranking_rows[0]["preference_reason"], "child_fathom_then_proxy_score")
            self.assertTrue(ranking_rows[0]["right_censored_proxy"])
            self.assertFalse(ranking_rows[0]["better"]["promotion_ready"])
            self.assertEqual(
                ranking_rows[0]["better"]["promotion_blocked_reasons"],
                ["proxy_score_below_promotion_threshold"],
            )
            self.assertIn("right-censored proxy", (tmp_path / "report.md").read_text(encoding="utf-8"))

    def test_min_proxy_score_gap_filters_near_ties(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            probe_file = tmp_path / "child_probe_rows.jsonl"
            rows = [
                _child_probe_row(pair=[1, 2], child_node_id=1, proof_cpu=10.0),
                _child_probe_row(pair=[1, 3], child_node_id=2, proof_cpu=11.0),
                _child_probe_row(pair=[1, 4], child_node_id=3, child_started=False),
            ]
            probe_file.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_proxy_ranking(
                [probe_file],
                tmp_path / "out",
                tmp_path / "report.md",
                min_proxy_score_gap=10.0,
            )

            self.assertEqual(summary["proxy_branch_row_count"], 2)
            self.assertEqual(summary["raw_proxy_branch_row_count"], 3)
            self.assertEqual(summary["filtered_out_proxy_branch_row_count"], 1)
            self.assertEqual(summary["proxy_context_count"], 1)
            self.assertEqual(summary["proxy_ranking_pair_count"], 0)
            self.assertFalse(summary["sampling_navigation_ready"])

    def test_marks_complete_positive_proxy_as_promotion_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            probe_file = tmp_path / "child_probe_rows.jsonl"
            rows = [
                _child_probe_row(
                    pair=[1, 2],
                    child_node_id=1,
                    complete=True,
                    right_censored=False,
                    fathomed=True,
                    corrected_gain=25.0,
                    retries=0.0,
                    proof_cpu=10.0,
                )
            ]
            probe_file.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = build_proxy_ranking(
                [probe_file],
                tmp_path / "out",
                tmp_path / "report.md",
                min_promotion_fathom_count=1.0,
                min_promotion_corrected_bound_gain=10.0,
                max_promotion_completion_bound_retry_count=1.0,
                require_promotion_complete_label=True,
            )

            self.assertEqual(summary["promotion_ready_branch_count"], 1)
            self.assertEqual(summary["promotion_blocked_branch_count"], 0)
            branch_rows = _read_jsonl(tmp_path / "out" / "child_probe_proxy_branch_rows.jsonl")
            self.assertTrue(branch_rows[0]["promotion_ready"])
            self.assertEqual(branch_rows[0]["promotion_blocked_reasons"], [])
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("promotion_ready_branch_count = 1", report)


def _child_probe_row(
    *,
    log_file: str = "logs/BPC_future/logical_graph/tasks_020/demo/demo.json.jsonl",
    branch_node_id: int = 0,
    branch_depth: int = 0,
    pair: list[int],
    child_node_id: int,
    complete: bool = False,
    right_censored: bool = True,
    fathomed: bool = False,
    corrected_gain: float = 0.0,
    retries: float = 0.0,
    proof_cpu: float = 0.0,
    negative_events: float = 0.0,
    exact_events: float = 1.0,
    child_started: bool = True,
) -> dict[str, object]:
    return {
        "schema_version": "journey_branch_child_probe_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "log_file": log_file,
        "run_status": "NO_FINISH",
        "right_censored": bool(right_censored),
        "label_observation_complete": bool(complete),
        "branch_node_id": int(branch_node_id),
        "branch_depth": int(branch_depth),
        "task_i": int(pair[0]),
        "task_j": int(pair[1]),
        "child_node_id": int(child_node_id),
        "child_started": bool(child_started),
        "child_labels": {
            "child_max_corrected_bound_gain": float(corrected_gain),
            "child_exact_pricing_event_count": float(exact_events),
            "child_negative_pricing_event_count": float(negative_events),
            "child_completion_bound_retry_count": float(retries),
            "child_proof_cpu": float(proof_cpu),
            "child_fathomed": 1.0 if fathomed else 0.0,
        },
    }


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


if __name__ == "__main__":
    unittest.main()
