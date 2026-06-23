from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import torch

from BPC_future.scripts.audit_gat_batch_impact_unresolved_context_label_action import (
    audit_unresolved_context_label_action,
)


class GATBatchImpactUnresolvedContextLabelActionAuditTests(unittest.TestCase):
    def test_supported_labels_recommend_action_consequence_contrast(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "dataset"
            pair_rows = root / "pairs.jsonl"
            _write_dataset(
                dataset,
                source_rows=[
                    _source_row(row_index=0, roi=2.5, causal=True),
                    _source_row(row_index=1, roi=0.0, causal=True),
                ],
            )
            _write_jsonl(
                pair_rows,
                [
                    {
                        "context_hash": "ctx",
                        "context_key": "inst|ctx",
                        "family": "random-wave",
                        "positive_row_index": 0,
                        "negative_row_index": 1,
                        "positive_roi": 2.5,
                        "negative_roi": 0.0,
                        "pair_pass": False,
                        "existing_pair_pass": False,
                        "comparator_pair_pass": False,
                        "comparator_unresolved_existing_failure": True,
                        "comparator_conflicts_existing_pass": False,
                        "positive_lower_delay_risk": True,
                    }
                ],
            )

            summary = audit_unresolved_context_label_action(
                dataset_dir=dataset,
                pair_rows_path=pair_rows,
                output_dir=root / "out",
                report=root / "report.md",
            )

            self.assertEqual(summary["audited_pair_count"], 1)
            self.assertEqual(summary["summary"]["causal_pair_supported_rate"], 1.0)
            self.assertEqual(summary["summary"]["label_polarity_valid_pair_rate"], 1.0)
            self.assertEqual(
                summary["summary"]["primary"],
                "supported_labels_need_action_consequence_visible_contrast",
            )
            self.assertEqual(
                summary["recommended_next_step"],
                "add_model_visible_action_consequence_contrast_then_retrain_focused_gate",
            )
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["selector_can_certificate"])

    def test_missing_causal_support_recommends_label_repair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "dataset"
            pair_rows = root / "pairs.jsonl"
            _write_dataset(
                dataset,
                source_rows=[
                    _source_row(row_index=0, roi=2.5, causal=False),
                    _source_row(row_index=1, roi=0.0, causal=True),
                ],
            )
            _write_jsonl(
                pair_rows,
                [
                    {
                        "context_hash": "ctx",
                        "context_key": "inst|ctx",
                        "family": "random-wave",
                        "positive_row_index": 0,
                        "negative_row_index": 1,
                        "positive_roi": 2.5,
                        "negative_roi": 0.0,
                        "pair_pass": False,
                        "existing_pair_pass": False,
                        "comparator_pair_pass": False,
                        "comparator_unresolved_existing_failure": True,
                    }
                ],
            )

            summary = audit_unresolved_context_label_action(
                dataset_dir=dataset,
                pair_rows_path=pair_rows,
                output_dir=root / "out",
                report=root / "report.md",
            )

            self.assertEqual(
                summary["summary"]["primary"],
                "some_unresolved_pairs_have_causal_provenance_gap",
            )
            self.assertEqual(
                summary["recommended_next_step"],
                "repair_or_filter_unresolved_pair_labels_before_more_training",
            )


def _write_dataset(dataset: Path, *, source_rows: list[dict[str, object]]) -> None:
    (dataset / "samples").mkdir(parents=True)
    source_path = dataset / "source.jsonl"
    _write_jsonl(source_path, source_rows)
    samples = []
    for row in source_rows:
        row_index = int(row["row_index"])
        roi = float(row["objective_improvement"])
        path = f"samples/sample_{row_index:06d}.pt"
        torch.save(
            {
                "context_features": torch.tensor([1.0, 2.0], dtype=torch.float32),
                "batch_features": torch.tensor([1.0, roi], dtype=torch.float32),
                "candidate_features": torch.tensor(
                    [[-3.0 + float(row_index), roi]],
                    dtype=torch.float32,
                ),
                "y_batch_roi_positive": torch.tensor([1.0 if roi > 0.0 else 0.0]),
                "y_accepted_batch_roi": torch.tensor([roi], dtype=torch.float32),
                "y_candidate_high_priority": torch.tensor([1.0 if roi > 0.0 else 0.0]),
                "y_candidate_delay_risk": torch.tensor([0.0 if roi > 0.0 else 1.0]),
                "y_candidate_true_rc_negative": torch.tensor([1.0]),
            },
            dataset / path,
        )
        samples.append(
            {
                "row_index": row_index,
                "path": path,
                "instance": "inst",
                "instance_family": "random-wave",
                "task_count": 20,
                "context_hash": "ctx",
                "accepted_batch_roi": roi,
                "label_batch_roi_positive": 1 if roi > 0.0 else 0,
                "candidate_signature_ids": [f"sig-{row_index}"],
            }
        )
    manifest = {
        "sample_count": len(samples),
        "samples": samples,
        "source_jsonl_paths": [str(source_path)],
        "context_feature_schema": ["context_a", "context_b"],
        "batch_feature_schema": ["added_journeys", "accepted_roi_proxy"],
        "candidate_feature_schema": ["true_reduced_cost", "candidate_roi_proxy"],
    }
    (dataset / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _source_row(*, row_index: int, roi: float, causal: bool) -> dict[str, object]:
    return {
        "row_index": row_index,
        "context_hash": "ctx",
        "instance": "inst",
        "training_label_allowed": causal,
        "same_context_target_intervention_observed": causal,
        "worker_target_causal_match": causal,
        "objective_improvement": roi,
        "label_objective_improved": roi > 0.0,
        "added_journeys": 1,
        "replacement_journeys": 0,
        "active_changed_task_set_count": 0,
        "pricing_kind": "exact",
        "target_signature_samples": [f"target-{row_index}"],
        "worker_returned_candidate_signature_samples": [f"target-{row_index}"],
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


if __name__ == "__main__":
    unittest.main()
