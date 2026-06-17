from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_gat_batch_impact_focused_pair_failures import (
    audit_focused_pair_failures,
)


class FocusedPairFailureAuditTests(unittest.TestCase):
    def test_audit_classifies_near_and_deep_pair_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset_dir = root / "dataset"
            dataset_dir.mkdir()
            metrics_path = root / "metrics.json"
            output_dir = root / "out"
            report_path = root / "report.md"
            manifest = {
                "diagnostic_only": True,
                "runs_bpc_or_pricing": False,
                "production_ready": False,
                "sample_count": 4,
                "candidate_feature_schema": [],
                "batch_feature_schema": [],
                "samples": [
                    _sample(1, "ctx-a", ["shared", "p1"]),
                    _sample(2, "ctx-a", ["shared"]),
                    _sample(3, "ctx-b", ["p2"]),
                    _sample(4, "ctx-b", ["n2"]),
                ],
            }
            metrics = {
                "production_ready": False,
                "focused_pair_gate": {
                    "pair_rows": [
                        {
                            "context_key": "inst|ctx-a",
                            "context_hash": "ctx-a",
                            "family": "sector-wave",
                            "positive_row_index": 1,
                            "negative_row_index": 2,
                            "positive_roi": 1.0,
                            "negative_roi": 0.0,
                            "positive_signature_ids": ["shared", "p1"],
                            "negative_signature_ids": ["shared"],
                            "raw_margin": -0.001,
                            "admission_margin": -0.002,
                            "delay_risk_margin": 0.2,
                            "pair_pass": False,
                        },
                        {
                            "context_key": "inst|ctx-b",
                            "context_hash": "ctx-b",
                            "family": "random-wave",
                            "positive_row_index": 3,
                            "negative_row_index": 4,
                            "positive_roi": 2.0,
                            "negative_roi": -1.0,
                            "positive_signature_ids": ["p2"],
                            "negative_signature_ids": ["n2"],
                            "raw_margin": 0.4,
                            "admission_margin": 0.3,
                            "delay_risk_margin": -0.2,
                            "pair_pass": False,
                        },
                        {
                            "context_key": "inst|ctx-b",
                            "context_hash": "ctx-b",
                            "family": "random-wave",
                            "positive_row_index": 3,
                            "negative_row_index": 4,
                            "positive_roi": 2.0,
                            "negative_roi": -1.0,
                            "positive_signature_ids": ["p2"],
                            "negative_signature_ids": ["n2"],
                            "raw_margin": 0.4,
                            "admission_margin": 0.3,
                            "delay_risk_margin": 0.2,
                            "pair_pass": True,
                        },
                    ]
                },
            }
            (dataset_dir / "manifest.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )
            metrics_path.write_text(json.dumps(metrics), encoding="utf-8")

            summary = audit_focused_pair_failures(
                metrics=metrics_path,
                dataset_dir=dataset_dir,
                output_dir=output_dir,
                report=report_path,
                near_margin_abs=0.01,
                deep_margin_abs=0.05,
                top_contexts=5,
            )
            self.assertTrue(Path(summary["focused_pair_failure_rows_path"]).exists())
            self.assertTrue(Path(summary["focused_pair_failure_contexts_path"]).exists())
            self.assertTrue(report_path.exists())

        self.assertTrue(summary["all_checks_pass"])
        stats = summary["summary"]
        self.assertEqual(stats["pair_count"], 3)
        self.assertEqual(stats["failed_pair_count"], 2)
        self.assertEqual(stats["raw_fail_count"], 1)
        self.assertEqual(stats["admission_fail_count"], 1)
        self.assertEqual(stats["delay_risk_fail_count"], 1)
        self.assertEqual(stats["all_failed_heads_near_count"], 1)
        self.assertEqual(stats["any_failed_head_deep_count"], 1)
        self.assertEqual(stats["signature_overlap_pair_count"], 1)
        self.assertEqual(
            summary["recommended_next_step"]["primary"],
            "add_or_repair_context_action_consequence_features_before_more_sweeps",
        )


def _sample(row_index: int, context_hash: str, signature_ids: list[str]) -> dict[str, object]:
    return {
        "row_index": row_index,
        "path": f"samples/sample_{row_index:06d}.pt",
        "instance": "inst",
        "context_hash": context_hash,
        "instance_family": "sector-wave",
        "task_count": 20,
        "candidate_count": len(signature_ids),
        "candidate_signature_ids": signature_ids,
    }


if __name__ == "__main__":
    unittest.main()
