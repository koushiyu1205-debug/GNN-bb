from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

try:
    import torch

    from BPC_future.scripts.merge_gat_worker_roi_graph_datasets import merge_datasets
    from BPC_future.tests.test_learning_components import _toy_payload
    from BPC_future.learning.graph_builder import FutureGraphBuilder

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATWorkerROIGraphDatasetMergeTests(unittest.TestCase):
    def test_merge_copies_samples_and_preserves_delay_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            first = tmp / "first"
            second = tmp / "second"
            _write_dataset(first, label_name="add", roi_class="positive_retry_roi")
            _write_dataset(second, label_name="abstain", roi_class="negative_exact_roi")

            summary = merge_datasets(
                input_datasets=[first, second],
                output_dir=tmp / "merged",
                report=tmp / "report.md",
            )

            manifest = json.loads((tmp / "merged" / "manifest.json").read_text())
            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["candidate_label_counts"], {"abstain": 1, "add": 1})
            self.assertEqual(summary["delay_queue_label_count"], 1)
            self.assertEqual(summary["sample_count"], 2)
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["certificate_ready"])
            self.assertEqual(len(manifest["samples"]), 2)
            self.assertTrue((tmp / "merged" / "samples" / "sample_000000.pt").exists())
            self.assertTrue((tmp / "merged" / "samples" / "sample_000001.pt").exists())
            self.assertEqual(
                {item["selector_source_dataset"] for item in manifest["samples"]},
                {str(first), str(second)},
            )


def _write_dataset(path: Path, *, label_name: str, roi_class: str) -> None:
    sample_dir = path / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    graph = FutureGraphBuilder().build_from_logical_graph(_toy_payload())
    graph.candidate_features = torch.tensor([[1.0, 2.0]], dtype=torch.float32)
    graph.context_features = torch.tensor([3.0, 4.0], dtype=torch.float32)
    torch.save(graph, sample_dir / "sample_000000.pt")
    manifest = {
        "schema_version": "gat_worker_roi_graph_dataset_manifest_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "source_jsonl": str(path / "rows.jsonl"),
        "sample_count": 1,
        "candidate_count": 1,
        "candidate_label_counts": {label_name: 1},
        "roi_class_counts": {roi_class: 1},
        "instance_counts": {"instance": 1},
        "family_counts": {"family": 1},
        "region_counts": {"region": 1},
        "skipped_counts": {},
        "candidate_feature_schema": ["a", "b"],
        "context_feature_schema": ["c", "d"],
        "candidate_feature_mean": [1.0, 2.0],
        "candidate_feature_std": [1.0, 1.0],
        "context_feature_mean": [3.0, 4.0],
        "context_feature_std": [1.0, 1.0],
        "selector_class_names": ["skip", "add", "abstain"],
        "label_semantics": {"abstain": "delay_queue"},
        "samples": [
            {
                "path": "samples/sample_000000.pt",
                "name": f"{label_name}-sample",
                "instance": "instance",
                "instance_family": "family",
                "instance_region": "region",
                "context_hash": "ctx",
                "source_file": "capture.jsonl",
                "row_index": 0,
                "candidate_count": 1,
                "roi_class": roi_class,
                "label_worker_roi_positive": 1 if label_name == "add" else 0,
                "selector_label": label_name,
            }
        ],
    }
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
