from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_gat_embedding_audit_ab_results import audit_results


FIELDS = [
    "instance",
    "status",
    "solving_time",
    "primal_bound",
    "dual_bound",
    "gap",
    "node_count",
    "external_timeout",
    "wall_time",
]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def _row(instance: str, *, wall_time: float = 1.0) -> dict[str, object]:
    return {
        "instance": instance,
        "status": "OPTIMAL",
        "solving_time": wall_time,
        "primal_bound": 10.0,
        "dual_bound": 10.0,
        "gap": 0.0,
        "node_count": 1,
        "external_timeout": "false",
        "wall_time": wall_time,
    }


class GATEmbeddingAuditABResultsTests(unittest.TestCase):
    def test_analysis_accepts_capture_only_no_regression_and_gat_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            result_pairs = []
            for scale in (5, 10, 20):
                baseline = tmp / f"task{scale:03d}_baseline" / "results.csv"
                capture = tmp / f"task{scale:03d}_capture" / "results.csv"
                rows = [_row(f"instance-{scale}-a"), _row(f"instance-{scale}-b", wall_time=2.0)]
                _write_csv(baseline, rows)
                _write_csv(capture, rows)
                result_pairs.append(
                    {
                        "task_count": scale,
                        "baseline_csv": str(baseline),
                        "capture_csv": str(capture),
                        "instance_count": 2,
                    }
                )
            validation = tmp / "validation" / "summary.json"
            validation.parent.mkdir(parents=True, exist_ok=True)
            validation.write_text(
                json.dumps(
                    {
                        "all_checks_pass": True,
                        "validation_candidate_ready": True,
                        "production_ready": False,
                        "official_bound_effect": False,
                        "active_worker_effect": False,
                        "certificate_effect": False,
                        "external_validation_summary": {
                            "validation_metrics": {
                                "overall": {
                                    "predicted_positive": 4,
                                    "fp": 0,
                                    "tp": 4,
                                }
                            }
                        },
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            runbook = tmp / "runbook.json"
            runbook.write_text(
                json.dumps(
                    {
                        "all_checks_pass": True,
                        "active_worker_ready": False,
                        "certificate_ready": False,
                        "result_pairs": result_pairs,
                        "gat_validation_summary": str(validation),
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            summary = audit_results(
                runbook_summary=runbook,
                output_dir=tmp / "analysis",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertTrue(summary["pre_online_gate_ready"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["online_effect_enabled"])
            self.assertFalse(summary["wall_time_roi_proven"])
            self.assertTrue(summary["checks"]["task5_official_results_match"])
            self.assertTrue(summary["checks"]["task10_official_results_match"])
            self.assertTrue(summary["checks"]["task20_official_results_match_for_capture_only"])
            self.assertTrue(summary["checks"]["gat_validation_has_high_priority_signal"])
            self.assertTrue(summary["checks"]["gat_validation_has_zero_false_positive"])
            self.assertTrue(summary["five_ten_no_regression_pass"])
            self.assertTrue(summary["twenty_roi_audit_ready"])
            self.assertFalse(summary["twenty_wall_time_roi_proven"])
            self.assertEqual(summary["gat_role"], "embedding_and_trajectory_impact_representation")
            self.assertEqual(summary["safety_shell"], "knn_ood_delay_queue")
            self.assertEqual(summary["safe_negative_decision"], "HIGH_PRIORITY")
            self.assertEqual(summary["unsafe_negative_decision"], "DELAY_QUEUE")
            self.assertFalse(summary["gate_can_permanently_discard_negative_columns"])
            self.assertTrue(summary["negative_columns_must_remain_eventually_reachable"])
            self.assertTrue(summary["productionization_standard"]["task5_10_no_regression_required"])
            self.assertTrue(summary["productionization_standard"]["task20_wall_time_roi_required"])
            self.assertFalse(summary["productionization_standard"]["default_enable_allowed"])
            self.assertIn("no_online_wall_time_roi_evidence_yet", summary["remaining_blockers"])
            self.assertTrue((tmp / "analysis" / "summary.json").exists())
            self.assertTrue((tmp / "report.md").exists())

    def test_analysis_blocks_when_capture_changes_official_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            result_pairs = []
            for scale in (5, 10, 20):
                baseline = tmp / f"task{scale:03d}_baseline" / "results.csv"
                capture = tmp / f"task{scale:03d}_capture" / "results.csv"
                _write_csv(baseline, [_row(f"instance-{scale}")])
                changed = _row(f"instance-{scale}")
                if scale == 10:
                    changed["dual_bound"] = 9.0
                _write_csv(capture, [changed])
                result_pairs.append(
                    {
                        "task_count": scale,
                        "baseline_csv": str(baseline),
                        "capture_csv": str(capture),
                        "instance_count": 1,
                    }
                )
            validation = tmp / "validation.json"
            validation.write_text(
                json.dumps(
                    {
                        "all_checks_pass": True,
                        "official_bound_effect": False,
                        "external_validation_summary": {
                            "validation_metrics": {"overall": {"predicted_positive": 1, "fp": 0}}
                        },
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            runbook = tmp / "runbook.json"
            runbook.write_text(
                json.dumps(
                    {
                        "all_checks_pass": True,
                        "active_worker_ready": False,
                        "certificate_ready": False,
                        "result_pairs": result_pairs,
                        "gat_validation_summary": str(validation),
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            summary = audit_results(
                runbook_summary=runbook,
                output_dir=tmp / "analysis",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["pre_online_gate_ready"])
            self.assertFalse(summary["checks"]["task10_official_results_match"])
            task10 = next(pair for pair in summary["pair_results"] if pair["task_count"] == 10)
            self.assertEqual(task10["official_result_mismatch_count"], 1)


if __name__ == "__main__":
    unittest.main()
