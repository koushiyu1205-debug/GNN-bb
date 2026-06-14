from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_gat_target_priority_worker_ab_results import audit_results


def _write_result(path: Path, *, status: str, primal: float, dual: str = "", columns: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "instance",
                "status",
                "primal_bound",
                "dual_bound",
                "columns",
                "exact_pricing_calls",
                "generated_sequences",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "instance": "toy.json",
                "status": status,
                "primal_bound": f"{primal:.6f}",
                "dual_bound": dual,
                "columns": str(columns),
                "exact_pricing_calls": "6",
                "generated_sequences": "100",
            }
        )


class GATTargetPriorityWorkerABResultAuditTests(unittest.TestCase):
    def test_audit_classifies_positive_and_no_roi_without_certificate_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            positive_base = tmp / "pos_base.csv"
            positive_worker = tmp / "pos_worker.csv"
            flat_base = tmp / "flat_base.csv"
            flat_worker = tmp / "flat_worker.csv"
            _write_result(positive_base, status="TIME_LIMIT", primal=740.0, columns=10)
            _write_result(positive_worker, status="TIME_LIMIT", primal=739.0, columns=12)
            _write_result(flat_base, status="TIME_LIMIT", primal=752.0, columns=20)
            _write_result(flat_worker, status="TIME_LIMIT", primal=752.0, columns=20)
            runbook = tmp / "runbook.json"
            runbook.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "candidate_runs": [
                            {
                                "name": "positive",
                                "instance": "toy.json",
                                "expected_context_hash": "ctx-pos",
                                "target_sequence": [1, 2],
                                "target_arc_option_sequence": ["0->1:a", "1->2:a", "2->0:a"],
                                "baseline_csv": str(positive_base),
                                "worker_csv": str(positive_worker),
                            },
                            {
                                "name": "flat",
                                "instance": "toy.json",
                                "expected_context_hash": "ctx-flat",
                                "target_sequence": [3],
                                "target_arc_option_sequence": ["0->3:a", "3->0:a"],
                                "baseline_csv": str(flat_base),
                                "worker_csv": str(flat_worker),
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = audit_results(
                runbook_summaries=[runbook],
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["default_enabled"])
            self.assertFalse(summary["certificate_ready"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(summary["roi_class_counts"]["positive_primal_roi"], 1)
            self.assertEqual(summary["roi_class_counts"]["no_observed_roi"], 1)
            self.assertEqual(summary["records"][0]["primal_improvement"], 1.0)
            self.assertEqual(summary["records"][0]["columns_delta"], 2)
            self.assertEqual(summary["next_decision"], "keep_worker_opt_in_and_expand_ab")
            self.assertTrue((tmp / "out" / "summary.json").exists())
            self.assertTrue((tmp / "report.md").exists())

    def test_audit_reuses_instance_baseline_for_multiple_candidate_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            shared_base = tmp / "shared_base.csv"
            worker = tmp / "worker.csv"
            missing_base = tmp / "missing_base.csv"
            _write_result(shared_base, status="TIME_LIMIT", primal=740.0, columns=10)
            _write_result(worker, status="TIME_LIMIT", primal=740.0, columns=10)
            runbook = tmp / "runbook.json"
            runbook.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "candidate_runs": [
                            {
                                "name": "baseline_provider",
                                "instance": "same_instance.json",
                                "expected_context_hash": "ctx-provider",
                                "target_sequence": [1],
                                "target_arc_option_sequence": ["0->1:a", "1->0:a"],
                                "baseline_csv": str(shared_base),
                                "worker_csv": str(shared_base),
                            },
                            {
                                "name": "needs_fallback",
                                "instance": "same_instance.json",
                                "expected_context_hash": "ctx-fallback",
                                "target_sequence": [2],
                                "target_arc_option_sequence": ["0->2:a", "2->0:a"],
                                "baseline_csv": str(missing_base),
                                "worker_csv": str(worker),
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = audit_results(
                runbook_summaries=[runbook],
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            by_name = {record["name"]: record for record in summary["records"]}
            self.assertTrue(by_name["needs_fallback"]["baseline_fallback_used"])
            self.assertEqual(by_name["needs_fallback"]["roi_class"], "no_observed_roi")
            self.assertTrue(by_name["needs_fallback"]["baseline_csv_exists"])


if __name__ == "__main__":
    unittest.main()
