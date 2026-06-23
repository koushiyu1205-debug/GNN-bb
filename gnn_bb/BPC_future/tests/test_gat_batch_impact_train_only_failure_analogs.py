import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import torch

from BPC_future.scripts import audit_gat_batch_impact_train_only_failure_analogs as analogs


class GATBatchImpactTrainOnlyFailureAnalogsTests(unittest.TestCase):
    def test_row_index_file_accepts_list_and_manifest_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            list_path = root / "list.json"
            dict_path = root / "dict.json"
            list_path.write_text(json.dumps([1, 2, "3"]), encoding="utf-8")
            dict_path.write_text(json.dumps({"row_indices": [4, "5"]}), encoding="utf-8")

            self.assertEqual(analogs._read_row_index_file(list_path), {1, 2, 3})
            self.assertEqual(analogs._read_row_index_file(dict_path), {4, 5})

    def test_split_matching_strips_logical_graph_suffix(self):
        metrics = {
            "split": {
                "train_instances": [
                    "BPC_future/logical_graph/tasks_020/random-wave/"
                    "apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json"
                ],
                "validation_instances": [
                    "BPC_future/logical_graph/tasks_020/greedy-anchor/"
                    "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json"
                ],
            }
        }
        train, validation = analogs._split_instance_sets(metrics)

        self.assertIn("apollo15_20km_random-wave_randomtw_tasks020_01_seed61000", train)
        self.assertIn("apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308", validation)
        self.assertEqual(
            analogs._row_split(
                "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308",
                train,
                validation,
            ),
            "validation",
        )

    def test_train_only_analogs_exclude_target_validation_rows(self):
        records = {
            1: self._record(1, split="train", label_positive=True, roi=2.0, hp=1, delay=0),
            2: self._record(2, split="train", label_positive=False, roi=0.0, hp=0, delay=1),
            100: self._record(100, split="validation", label_positive=True, roi=3.0, hp=1, delay=0),
            101: self._record(101, split="validation", label_positive=False, roi=0.0, hp=0, delay=1),
        }
        train_pairs = analogs._build_train_pair_universe(
            records,
            candidate_std=(1.0, 1.0),
            batch_std=(1.0,),
            min_positive_roi=0.65,
            max_negative_roi=0.0,
        )
        target_pair = analogs._make_pair_record(
            records[100],
            records[101],
            candidate_std=(1.0, 1.0),
            batch_std=(1.0,),
        )
        failed = [
            {
                "target_failure_key": "100>101",
                "context_key": records[100].context_key,
                "family": "random-wave",
                "task_count": 20,
                "positive_row_index": 100,
                "negative_row_index": 101,
                "target_split_class": "validation_gate_only",
                "target_pair_vector": list(target_pair.pair_vector),
                "target_pair_path_tokens": list(target_pair.pair_path_tokens),
                "target_pair_signature_ids": list(target_pair.pair_signature_ids),
            }
        ]

        rows = analogs._find_analogs(failed, train_pairs, row_records=records, top_k=3)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["analog_positive_row_index"], 1)
        self.assertEqual(rows[0]["analog_negative_row_index"], 2)
        self.assertNotIn(100, {rows[0]["analog_positive_row_index"], rows[0]["analog_negative_row_index"]})
        self.assertNotIn(101, {rows[0]["analog_positive_row_index"], rows[0]["analog_negative_row_index"]})

    def test_primary_candidate_prefers_high_priority_then_delay(self):
        high_priority = torch.tensor([0.0, 1.0, 0.0])
        delay = torch.tensor([1.0, 0.0, 0.0])
        self.assertEqual(
            analogs._primary_candidate_index(
                SimpleNamespace(y_candidate_high_priority=high_priority, y_candidate_delay_risk=delay)
            ),
            1,
        )
        self.assertEqual(
            analogs._primary_candidate_index(
                SimpleNamespace(
                    y_candidate_high_priority=torch.zeros(3),
                    y_candidate_delay_risk=delay,
                )
            ),
            0,
        )

    def _record(
        self,
        row_index,
        *,
        split,
        label_positive,
        roi,
        hp,
        delay,
    ):
        return analogs.RowRecord(
            row_index=row_index,
            context_key="instance|ctx",
            context_hash="ctx",
            instance="instance",
            family="random-wave",
            task_count=20,
            split=split,
            label_positive=label_positive,
            roi=roi,
            high_priority_candidate_count=hp,
            delay_candidate_count=delay,
            candidate_vector=(float(row_index), float(row_index + 1)),
            batch_vector=(float(row_index % 3),),
            path_tokens=(row_index, row_index + 10),
            signature_ids=(f"sig-{row_index}",),
            primary_candidate_index=0,
            in_focused_training=False,
            in_existing_boost=False,
        )


if __name__ == "__main__":
    unittest.main()
