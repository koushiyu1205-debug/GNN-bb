from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_paired_probe_delta_rows import build_delta_rows


class JourneyPairedProbeDeltaRowsTests(unittest.TestCase):
    def test_converts_hard_negative_proxy_to_right_censored_delta_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_dir = tmp_path / "paired"
            input_dir.mkdir()
            instance = "BPC_future/logical_graph/tasks_020/sector-wave/case.json"
            _write_jsonl(
                input_dir / "paired_probe_rows.jsonl",
                [
                    _paired_row(
                        instance,
                        experiment="alt_bad",
                        label_type="hard_negative_proxy",
                        forced_pair=[5, 18],
                        selected_pair=[4, 8],
                        wall=102.90111,
                        wall_gain=-9.259593,
                        gap_improvement=-0.002354,
                    ),
                    _paired_row(
                        instance,
                        experiment="alt_neutral",
                        label_type="neutral_proxy",
                        forced_pair=[1, 18],
                        selected_pair=[4, 8],
                        wall=90.0,
                        wall_gain=3.0,
                        gap_improvement=0.0,
                    ),
                    {"pair_role": "selected_baseline", "paired_label_type": "baseline"},
                ],
            )

            summary = build_delta_rows(
                [input_dir],
                tmp_path / "out",
                tmp_path / "report.md",
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertFalse(summary["certificate_effect"])
            self.assertFalse(summary["production_ready"])
            self.assertEqual(summary["output_row_count"], 1)
            self.assertEqual(
                summary["output_counterfactual_label_counts"],
                {"paired_probe_hard_negative_proxy": 1},
            )
            self.assertEqual(summary["skipped_counts"]["neutral_proxy_excluded"], 1)

            rows = _read_jsonl(tmp_path / "out" / "branch_counterfactual_delta_rows.jsonl")
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertTrue(row["proxy_only"])
            self.assertTrue(row["right_censored_counterfactual"])
            self.assertEqual(row["counterfactual_label_type"], "paired_probe_hard_negative_proxy")
            self.assertEqual(row["baseline_pair"], [4, 8])
            self.assertEqual(row["alternative_pair"], [5, 18])
            self.assertEqual(row["baseline_wall_time"], 93.641517)
            self.assertEqual(row["alternative_wall_time"], 102.90111)
            self.assertGreater(row["hard_negative_loss_weight"], 1.0)
            self.assertEqual(row["labels"]["y_counterfactual_no_effect_hard_negative"], 1.0)
            self.assertEqual(row["alternative_raw_row"]["source_alt_routeopt_bkf_score"], 12.5)
            self.assertEqual(
                row["alternative_raw_row"]["source_alt_routeopt_bkf_reason"],
                "phase1_min_child_lp_gain=2",
            )
            self.assertEqual(row["alternative_raw_row"]["source_alt_routeopt_bkf_stage"], "accepted")
            self.assertEqual(row["alternative_raw_row"]["phase1_min_child_lp_gain"], 2.0)
            self.assertEqual(row["alternative_raw_row"]["phase2_negative_child_count"], 1.0)
            self.assertIn("production_ready = false", (tmp_path / "report.md").read_text(encoding="utf-8"))


def _paired_row(
    instance: str,
    *,
    experiment: str,
    label_type: str,
    forced_pair: list[int],
    selected_pair: list[int],
    wall: float,
    wall_gain: float,
    gap_improvement: float,
) -> dict[str, object]:
    return {
        "schema_version": "journey_paired_probe_entry_v1",
        "diagnostic_only": True,
        "production_ready": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "experiment": experiment,
        "pair_role": "alternative",
        "pair_group_id": "case__d0__n0__sel_4,8",
        "instance": instance,
        "source_node_id": 0,
        "source_depth": 0,
        "source_selected_pair": selected_pair,
        "forced_pair": forced_pair,
        "paired_label_type": label_type,
        "paired_baseline_experiment": "baseline",
        "status": "TIME_LIMIT",
        "wall_time": wall,
        "paired_wall_time_gain": wall_gain,
        "paired_completion_profile_gain": 0.0,
        "paired_child_cb_retry_gain": 0.0,
        "paired_status_rank_delta": 0,
        "paired_gap_improvement": gap_improvement,
        "gap": 0.007,
        "gap_available": True,
        "child_completion_bound_retry_count": 6.0,
        "child_exact_pricing_event_count": 8.0,
        "child_negative_pricing_event_count": 7.0,
        "child_fathomed_count": 0.0,
        "child_proof_cpu": 62.143576,
        "source_alt_routeopt_bkf_score": 12.5,
        "source_alt_routeopt_bkf_reason": "phase1_min_child_lp_gain=2",
        "source_alt_routeopt_bkf_stage": "accepted",
        "source_alt_routeopt_bkf_dynamic_k": 3,
        "source_alt_routeopt_bkf_stage_rank": 0,
        "source_alt_routeopt_bkf_filtered_count": 1,
        "phase1_min_child_lp_gain": 2.0,
        "phase1_child_lp_gain_product": 8.0,
        "phase2_negative_child_count": 1.0,
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


if __name__ == "__main__":
    unittest.main()
