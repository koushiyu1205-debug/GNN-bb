from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_gat_batch_impact_focused_tranche_mining import (
    mine_focused_tranche,
)


class GATBatchImpactFocusedTrancheMiningTests(unittest.TestCase):
    def test_mines_same_context_positive_negative_pairs_and_selector_gap(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            dataset_dir = root / "dataset"
            dataset_dir.mkdir()
            manifest = {
                "diagnostic_only": True,
                "runs_bpc_or_pricing": False,
                "production_ready": False,
                "certificate_source": False,
                "sample_count": 5,
                "candidate_count": 5,
                "samples": [
                    _sample(
                        row_index=0,
                        context_hash="ctx-a",
                        family="sector-wave",
                        roi=1.2,
                        label_positive=1,
                        high_priority=1,
                        delay=0,
                    ),
                    _sample(
                        row_index=1,
                        context_hash="ctx-a",
                        family="sector-wave",
                        roi=-2.0,
                        label_positive=0,
                        high_priority=0,
                        delay=1,
                    ),
                    _sample(
                        row_index=2,
                        context_hash="ctx-b",
                        family="random-wave",
                        roi=-1.0,
                        label_positive=0,
                        high_priority=0,
                        delay=1,
                    ),
                    _sample(
                        row_index=3,
                        context_hash="ctx-c",
                        family="random-wave",
                        roi=2.0,
                        label_positive=1,
                        high_priority=1,
                        delay=0,
                    ),
                    _sample(
                        row_index=4,
                        context_hash="ctx-d",
                        family="greedy-anchor",
                        roi=0.2,
                        label_positive=1,
                        high_priority=1,
                        delay=0,
                    ),
                ],
            }
            (dataset_dir / "manifest.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )

            summary = mine_focused_tranche(
                dataset_dir=dataset_dir,
                output_dir=root / "out",
                report=root / "report.md",
                min_positive_roi=0.65,
                max_hard_negative_roi=0.0,
                min_roi_gap=1.0e-6,
                top_contexts=5,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertTrue(summary["stage3_focused_tranche_ready"])
            self.assertEqual(summary["trainable_context_count"], 1)
            self.assertEqual(summary["focused_pair_count"], 1)
            self.assertEqual(summary["focused_row_indices"], [0, 1])
            self.assertEqual(summary["focused_family_counts"], {"sector-wave": 2})
            self.assertEqual(summary["negative_only_context_count"], 1)
            self.assertEqual(summary["positive_only_context_count"], 1)
            self.assertEqual(summary["recommended_selector"], "explicit_row_indices")
            self.assertEqual(summary["row_index_min_selector"]["extra_nonfocused_count"], 3)
            self.assertTrue(Path(summary["focused_pairs_path"]).exists())
            self.assertTrue(Path(summary["focused_row_indices_path"]).exists())


def _sample(
    *,
    row_index: int,
    context_hash: str,
    family: str,
    roi: float,
    label_positive: int,
    high_priority: int,
    delay: int,
) -> dict[str, object]:
    return {
        "path": f"samples/sample_{row_index:06d}.pt",
        "instance": f"inst-{context_hash}",
        "instance_region": "apollo15_20km",
        "instance_family": family,
        "task_count": 20,
        "context_hash": context_hash,
        "source_file": "toy.jsonl",
        "row_index": row_index,
        "candidate_count": 1,
        "candidate_ids": [f"cand-{row_index}"],
        "candidate_signature_ids": [f"sig-{row_index}"],
        "negative_candidate_count": 1,
        "high_priority_candidate_count": high_priority,
        "delay_candidate_count": delay,
        "batch_type": "new_task_set",
        "label_batch_roi_positive": label_positive,
        "objective_improvement": roi,
        "accepted_batch_roi": roi,
    }


if __name__ == "__main__":
    unittest.main()
