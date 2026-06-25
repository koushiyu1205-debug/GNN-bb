from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_journey_branch_probe_training_readiness import (
    build_probe_training_readiness,
)


class JourneyBranchProbeTrainingReadinessTests(unittest.TestCase):
    def test_counts_probe_positive_and_hard_negative_without_production_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            probe_dir = tmp_path / "probe"
            probe_dir.mkdir()
            rows = []
            for idx in range(30):
                rows.append(
                    _row(
                        idx,
                        family="greedy-anchor" if idx < 15 else "random-wave",
                        promotion_ready=True,
                        proxy_score=1.5,
                        complete=True,
                        right_censored=False,
                        retries=0.0,
                    )
                )
            for idx in range(30, 65):
                rows.append(
                    _row(
                        idx,
                        family="random-wave" if idx < 45 else "sector-wave",
                        promotion_ready=False,
                        proxy_score=-2.0,
                        complete=False,
                        right_censored=True,
                        retries=2.0,
                    )
                )
            for idx in range(65, 120):
                rows.append(
                    _row(
                        idx,
                        family="sector-wave",
                        promotion_ready=False,
                        proxy_score=-0.1,
                        complete=True,
                        right_censored=False,
                        retries=0.0,
                    )
                )
            _write_jsonl(probe_dir / "child_probe_proxy_branch_rows.jsonl", rows)

            summary = build_probe_training_readiness(
                [probe_dir],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertTrue(summary["proxy_only"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["optin_training_ready"])
            self.assertEqual(summary["row_count"], 120)
            self.assertEqual(summary["probe_positive_count"], 30)
            self.assertEqual(summary["strict_uncensored_probe_positive_count"], 30)
            self.assertEqual(summary["probe_hard_negative_count"], 35)
            self.assertEqual(summary["probe_time_window_family_count"], 3)
            self.assertTrue(summary["probe_debug_training_ready"])
            self.assertFalse(summary["probe_sanity_training_ready"])
            self.assertEqual(
                summary["missing_for_probe_sanity_training"]["probe_branch_row_min"],
                380,
            )
            self.assertEqual(
                summary["probe_hard_negative_reason_counts"]["right_censored_probe"],
                35,
            )
            self.assertTrue((tmp_path / "out" / "summary.json").exists())
            self.assertTrue(
                (tmp_path / "out" / "branch_probe_training_readiness_rows.jsonl").exists()
            )
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("probe_positive_count = 30", report)
            self.assertIn("production_ready = False", report)
            self.assertIn("optin_training_ready = False", report)

    def test_missing_rows_keep_debug_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            row_file = tmp_path / "child_probe_proxy_branch_rows.jsonl"
            _write_jsonl(
                row_file,
                [
                    _row(0, promotion_ready=True, proxy_score=1.0),
                    _row(1, promotion_ready=False, proxy_score=-2.0, right_censored=True),
                ],
            )

            summary = build_probe_training_readiness(
                [row_file],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertEqual(summary["row_count"], 2)
            self.assertFalse(summary["probe_debug_training_ready"])
            self.assertEqual(
                summary["missing_for_probe_debug_training"]["probe_branch_row_min"],
                98,
            )
            self.assertEqual(
                summary["missing_for_probe_debug_training"]["probe_positive_min"],
                9,
            )
            self.assertEqual(
                summary["missing_for_probe_debug_training"]["probe_hard_negative_min"],
                9,
            )


def _row(
    idx: int,
    *,
    family: str = "greedy-anchor",
    promotion_ready: bool,
    proxy_score: float,
    complete: bool = True,
    right_censored: bool = False,
    retries: float = 0.0,
) -> dict[str, object]:
    context_id = idx % 12
    return {
        "schema_version": "journey_branch_child_probe_proxy_branch_row_v1",
        "instance": (
            "BPC_future/logical_graph/tasks_020/"
            f"{family}/terrain_{idx % 4}/case_seed{idx:05d}.json"
        ),
        "node_id": context_id,
        "depth": context_id % 3,
        "pair": [idx % 20, (idx % 20) + 1],
        "proxy_score": proxy_score,
        "promotion_ready": promotion_ready,
        "promotion_blocked_reasons": [] if promotion_ready else ["unit_block"],
        "label_observation_complete": complete,
        "right_censored": right_censored,
        "child_count": 2,
        "started_child_count": 2,
        "unstarted_child_count": 0,
        "fathom_count": 1.0 if promotion_ready else 0.0,
        "max_corrected_bound_gain": 12.0 if promotion_ready else 0.0,
        "completion_bound_retry_count": retries,
        "negative_pricing_event_count": 0.0,
        "exact_pricing_event_count": 2.0,
        "proof_cpu": 8.0,
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
