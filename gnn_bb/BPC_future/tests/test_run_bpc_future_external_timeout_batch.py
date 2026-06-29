from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.run_bpc_future_external_timeout_batch import augment_gap_fields


class RunBPCFutureExternalTimeoutBatchGapTests(unittest.TestCase):
    def test_preserves_solver_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            log_path = log_dir / "demo.jsonl"
            log_path.parent.mkdir(parents=True)
            log_path.write_text("", encoding="utf-8")
            row = {
                "instance": "demo",
                "status": "TIME_LIMIT",
                "primal_bound": "120.0",
                "dual_bound": "100.0",
                "gap": "0.166667",
            }

            augmented = augment_gap_fields(row, log_dir=log_dir, instance="demo")

            self.assertEqual(augmented["gap"], "0.166667")
            self.assertEqual(augmented["gap_available"], "true")
            self.assertEqual(augmented["gap_source"], "solver_result")
            self.assertEqual(augmented["gap_unavailable_reason"], "")
            self.assertEqual(augmented["best_primal_bound"], "120.0")
            self.assertEqual(augmented["best_dual_bound"], "100.0")

    def test_external_timeout_with_only_incumbent_reports_unavailable_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            instance = "BPC_future/logical_graph/tasks_020/demo.json"
            log_path = log_dir / f"{instance}.jsonl"
            log_path.parent.mkdir(parents=True)
            log_path.write_text(
                json.dumps(
                    {
                        "event": "journey_corrected_node_bound_audit",
                        "incumbent": 642.291219,
                        "rmp_objective": 624.572984944,
                        "corrected_node_lb": None,
                        "valid": False,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            augmented = augment_gap_fields(
                {"instance": instance, "status": "EXTERNAL_TIME_LIMIT"},
                log_dir=log_dir,
                instance=instance,
            )

            self.assertEqual(augmented["gap_available"], "false")
            self.assertEqual(
                augmented["gap_unavailable_reason"],
                "no_exact_dual_bound_external_timeout_no_finish",
            )
            self.assertEqual(augmented["best_primal_bound"], "642.291219")
            self.assertEqual(augmented["best_dual_bound"], "")
            self.assertNotIn("gap", augmented)

    def test_external_timeout_with_valid_root_corrected_bound_computes_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            instance = "demo"
            log_path = log_dir / "demo.jsonl"
            log_path.parent.mkdir(parents=True)
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"event": "incumbent", "objective": 120.0}, sort_keys=True),
                        json.dumps(
                            {
                                "event": "journey_corrected_node_bound_audit",
                                "corrected_node_lb": 100.0,
                                "valid": True,
                            },
                            sort_keys=True,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            augmented = augment_gap_fields(
                {"instance": instance, "status": "EXTERNAL_TIME_LIMIT"},
                log_dir=log_dir,
                instance=instance,
            )

            self.assertEqual(augmented["gap_available"], "true")
            self.assertEqual(augmented["gap_source"], "root_corrected_node_bound")
            self.assertEqual(augmented["best_primal_bound"], "120.0")
            self.assertEqual(augmented["best_dual_bound"], "100.0")
            self.assertEqual(augmented["dual_bound"], "100.0")
            self.assertEqual(augmented["gap"], "0.166667")


if __name__ == "__main__":
    unittest.main()
