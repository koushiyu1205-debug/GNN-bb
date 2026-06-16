from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_gat_accepted_bad_mode_gate import (
    audit_accepted_bad_mode_gate,
)


class GATAcceptedBadModeGateAuditTests(unittest.TestCase):
    def test_rejects_high_priority_bad_mode_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "decision_records.jsonl"
            records.write_text(
                "\n".join(
                    json.dumps(record, sort_keys=True)
                    for record in [
                        {
                            "decision_name": "HIGH_PRIORITY",
                            "bad_mode_switch": 0,
                            "decision_split": "validation",
                            "instance_family": "sector-wave",
                        },
                        {
                            "decision_name": "HIGH_PRIORITY",
                            "bad_mode_switch": 1,
                            "decision_split": "validation",
                            "instance_family": "sector-wave",
                            "accepted_batch_roi_label": 1.0,
                        },
                        {
                            "decision_name": "DELAY_QUEUE",
                            "bad_mode_switch": 1,
                            "decision_split": "validation",
                            "instance_family": "random-wave",
                        },
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = audit_accepted_bad_mode_gate(
                decision_records=records,
                output_dir=root / "out",
                report=root / "report.md",
            )

            self.assertFalse(summary["all_checks_pass"])
            self.assertFalse(summary["accepted_bad_mode_gate_pass"])
            self.assertEqual(summary["decision_record_count"], 3)
            self.assertEqual(summary["high_priority_decision_count"], 2)
            self.assertEqual(summary["bad_mode_record_count"], 2)
            self.assertEqual(summary["accepted_bad_mode_count"], 1)
            self.assertEqual(summary["accepted_bad_mode_by_family"], {"sector-wave": 1})
            self.assertTrue((root / "out" / "summary.json").exists())
            self.assertTrue((root / "report.md").exists())

    def test_passes_when_bad_mode_records_are_delayed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = root / "decision_records.jsonl"
            records.write_text(
                "\n".join(
                    json.dumps(record, sort_keys=True)
                    for record in [
                        {
                            "decision_name": "HIGH_PRIORITY",
                            "bad_mode_switch": 0,
                            "decision_split": "validation",
                            "instance_family": "sector-wave",
                        },
                        {
                            "decision_name": "DELAY_QUEUE",
                            "bad_mode_switch": 1,
                            "decision_split": "validation",
                            "instance_family": "sector-wave",
                        },
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = audit_accepted_bad_mode_gate(
                decision_records=records,
                output_dir=root / "out",
                report=root / "report.md",
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertTrue(summary["accepted_bad_mode_gate_pass"])
            self.assertEqual(summary["accepted_bad_mode_count"], 0)
            self.assertEqual(summary["bad_mode_record_count"], 1)


if __name__ == "__main__":
    unittest.main()
