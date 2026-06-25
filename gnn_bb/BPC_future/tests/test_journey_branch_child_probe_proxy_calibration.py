from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_branch_child_probe_proxy_calibration import (
    build_proxy_calibration,
)


class JourneyBranchChildProbeProxyCalibrationTests(unittest.TestCase):
    def test_detects_proxy_top_mismatch_against_full_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            proxy_dir = tmp_path / "proxy"
            delta_dir = tmp_path / "delta"
            proxy_dir.mkdir()
            delta_dir.mkdir()
            instance = "BPC_future/logical_graph/tasks_020/sector-wave/case.json"
            proxy_rows = [
                _proxy_row(instance, pair=[3, 6], proxy_score=-6.0),
                _proxy_row(instance, pair=[6, 16], proxy_score=-7.0),
                _proxy_row(instance, pair=[3, 14], proxy_score=-9.0),
            ]
            delta_rows = [
                _delta_row(instance, pair=[3, 6], wall_delta=-18.0),
                _delta_row(instance, pair=[6, 16], wall_delta=-45.0),
                _delta_row(instance, pair=[3, 14], wall_delta=-17.0),
            ]
            _write_jsonl(proxy_dir / "child_probe_proxy_branch_rows.jsonl", proxy_rows)
            _write_jsonl(delta_dir / "branch_counterfactual_delta_rows.jsonl", delta_rows)

            summary = build_proxy_calibration(
                [proxy_dir],
                [delta_dir],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(summary["matched_pair_count"], 3)
            self.assertEqual(summary["context_count"], 1)
            self.assertEqual(summary["top_pair_match_count"], 0)
            self.assertEqual(summary["top_pair_mismatch_count"], 1)
            self.assertEqual(summary["pairwise_comparison_count"], 3)
            self.assertEqual(summary["discordant_pair_count"], 1)
            self.assertFalse(summary["ranking_training_ready"])

            context_rows = _read_jsonl(
                tmp_path / "out" / "child_probe_proxy_calibration_context_rows.jsonl"
            )
            self.assertEqual(context_rows[0]["top_proxy"]["pair"], [3, 6])
            self.assertEqual(context_rows[0]["top_full"]["pair"], [6, 16])
            self.assertFalse(context_rows[0]["top_pair_match"])
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("top_pair_mismatch_count = 1", report)


def _proxy_row(instance: str, *, pair: list[int], proxy_score: float) -> dict:
    return {
        "schema_version": "journey_branch_child_probe_proxy_branch_row_v1",
        "diagnostic_only": True,
        "instance": instance,
        "node_id": 0,
        "depth": 0,
        "pair": pair,
        "task_i": pair[0],
        "task_j": pair[1],
        "proxy_score": proxy_score,
        "right_censored": True,
        "fathom_count": 1.0,
        "max_corrected_bound_gain": 1.0,
        "completion_bound_retry_count": 3.0,
        "proof_cpu": 40.0,
    }


def _delta_row(instance: str, *, pair: list[int], wall_delta: float) -> dict:
    return {
        "schema_version": "journey_branch_counterfactual_delta_v4",
        "diagnostic_only": True,
        "instance": instance,
        "node_id": 0,
        "depth": 0,
        "baseline_pair": [1, 2],
        "alternative_pair": pair,
        "counterfactual_label_type": "strong_positive",
        "alternative_status": "OPTIMAL",
        "alternative_wall_time": 200.0 + wall_delta,
        "deltas": {
            "wall_time_delta": wall_delta,
            "exact_pricing_calls_delta": 0.0,
        },
        "labels": {"y_counterfactual_wall_improved": 1.0},
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


if __name__ == "__main__":
    unittest.main()
