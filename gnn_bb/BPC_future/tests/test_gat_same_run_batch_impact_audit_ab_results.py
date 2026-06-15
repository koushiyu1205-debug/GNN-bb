from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_gat_same_run_batch_impact_audit_ab_results import (
    audit_results,
)


class GATSameRunBatchImpactAuditABResultsTests(unittest.TestCase):
    def test_analysis_accepts_same_run_metrics_and_keeps_production_off(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            runbook = tmp / "runbook.json"
            validation = tmp / "validation" / "summary.json"
            pairs = []
            for scale in (5, 10, 20):
                base = tmp / f"task{scale:03d}_baseline.csv"
                cap = tmp / f"task{scale:03d}_capture.csv"
                _write_results(base, scale)
                _write_results(cap, scale)
                pairs.append(
                    {
                        "task_count": scale,
                        "baseline_csv": str(base),
                        "capture_csv": str(cap),
                    }
                )
            validation.parent.mkdir(parents=True)
            validation.write_text(
                json.dumps(
                    {
                        "all_checks_pass": True,
                        "selector_can_certificate": False,
                        "official_bound_effect": False,
                        "gate_can_permanently_discard_negative_columns": False,
                        "negative_columns_must_remain_eventually_reachable": True,
                        "validation_metrics": {
                            "predicted_high_priority": 3,
                            "fp_high_priority_on_delay": 0,
                            "negative_recall_delay_queue": 1.0,
                        },
                    }
                ),
                encoding="utf-8",
            )
            runbook.write_text(
                json.dumps(
                    {
                        "all_checks_pass": True,
                        "certificate_ready": False,
                        "active_worker_ready": False,
                        "gat_validation_summary": str(validation),
                        "result_pairs": pairs,
                        "productionization_standard": {
                            "task5_10_no_regression_required": True,
                            "task20_wall_time_roi_required": True,
                        },
                    }
                ),
                encoding="utf-8",
            )

            summary = audit_results(
                runbook_summary=runbook,
                output_dir=tmp / "analysis",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertTrue(summary["five_ten_no_regression_pass"])
            self.assertTrue(summary["same_run_gat_offline_gate_ready"])
            self.assertTrue(summary["twenty_capture_pair_completed"])
            self.assertEqual(
                summary["task20_target_status"]["baseline_optimal_count"],
                0,
            )
            self.assertEqual(
                summary["task20_target_status"]["baseline_time_limit_count"],
                2,
            )
            self.assertFalse(summary["task20_target_status"]["baseline_all_optimal"])
            self.assertEqual(
                summary["effective_sample_collection_rule"]["positive_label"],
                "trajectory_improves_objective_dual_or_tail",
            )
            self.assertIn(
                "rc_negative_only",
                summary["effective_sample_collection_rule"]["invalid_sources"],
            )
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["wall_time_roi_proven"])
            self.assertFalse(summary["gate_can_permanently_discard_negative_columns"])
            self.assertTrue(summary["negative_columns_must_remain_eventually_reachable"])
            self.assertTrue((tmp / "analysis" / "summary.json").exists())
            self.assertTrue((tmp / "report.md").exists())


def _write_results(path: Path, scale: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "instance",
        "status",
        "primal_bound",
        "dual_bound",
        "gap",
        "node_count",
        "external_timeout",
        "wall_time",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for idx in (1, 2):
            writer.writerow(
                {
                    "instance": f"task{scale}_{idx}.json",
                    "status": "OPTIMAL" if scale < 20 else "TIME_LIMIT",
                    "primal_bound": 100.0 + scale + idx,
                    "dual_bound": 100.0 + scale + idx if scale < 20 else "",
                    "gap": 0.0 if scale < 20 else "",
                    "node_count": 1,
                    "external_timeout": "false",
                    "wall_time": 1.0 + idx,
                }
            )


if __name__ == "__main__":
    unittest.main()
