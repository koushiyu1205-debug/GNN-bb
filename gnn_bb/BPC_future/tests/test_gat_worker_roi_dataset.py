from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.build_gat_worker_roi_dataset import build_roi_dataset


def _write_worker_stub(
    worker_csv: Path,
    *,
    target_sequence: list[int],
    context_hash: str,
    returned_sequence_samples: list[list[list[int]]] | None = None,
    materialized: bool = False,
    append_context_mismatch: bool = False,
) -> None:
    worker_csv.parent.mkdir(parents=True, exist_ok=True)
    worker_csv.write_text("status\nTIME_LIMIT\n", encoding="utf-8")
    log_dir = worker_csv.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    event = {
        "pulse_worker_enabled": True,
        "pulse_worker_target_transition_priority_enabled": True,
        "pulse_worker_target_transition_priority_sequence": target_sequence,
        "pulse_worker_target_sequence_completed": bool(materialized),
        "pulse_worker_target_sequence_materialized": bool(materialized),
        "pulse_worker_target_sequence_negative": bool(materialized),
        "pulse_worker_target_sequence_reached_prefix_len": len(target_sequence),
        "pulse_worker_returned_candidate_sequence_samples": returned_sequence_samples or [],
        "pulse_worker_harvested_sequence_samples": returned_sequence_samples or [],
        "pulse_worker_context_hash": context_hash,
    }
    rows = [json.dumps(event, sort_keys=True)]
    if append_context_mismatch:
        mismatch = dict(event)
        mismatch["pulse_worker_context_hash"] = "different-context"
        mismatch["pulse_worker_skipped"] = True
        mismatch["pulse_worker_skip_reason"] = "residual_target_context_mismatch"
        mismatch["pulse_worker_returned_candidate_sequence_samples"] = []
        mismatch["pulse_worker_harvested_sequence_samples"] = []
        rows.append(json.dumps(mismatch, sort_keys=True))
    (log_dir / "worker.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")


class GATWorkerROIDatasetTests(unittest.TestCase):
    def test_builds_positive_and_noop_roi_labels_with_candidate_features(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            audit = tmp / "audit_summary.json"
            candidate_summary = tmp / "candidate_summary.json"
            instance = "toy_instance.json"
            positive_worker_csv = tmp / "positive_worker" / "results.csv"
            noop_worker_csv = tmp / "noop_worker" / "results.csv"
            audit.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "records": [
                            {
                                "name": "positive",
                                "instance": instance,
                                "expected_context_hash": "ctx-pos",
                                "target_sequence": [1, 2],
                                "target_arc_option_sequence": ["0->1:a", "1->2:a", "2->0:a"],
                                "baseline_csv_exists": True,
                                "worker_csv_exists": True,
                                "worker_csv": str(positive_worker_csv),
                                "official_bound_effect": False,
                                "certificate_effect": False,
                                "baseline_status": "TIME_LIMIT",
                                "worker_status": "TIME_LIMIT",
                                "baseline_primal": 10.0,
                                "worker_primal": 9.0,
                                "primal_improvement": 1.0,
                                "baseline_columns": 10,
                                "worker_columns": 12,
                                "columns_delta": 2,
                                "exact_pricing_calls_delta": 1,
                                "generated_sequences_delta": 7,
                                "roi_class": "positive_primal_roi",
                            },
                            {
                                "name": "noop",
                                "instance": instance,
                                "expected_context_hash": "ctx-flat",
                                "target_sequence": [3],
                                "target_arc_option_sequence": ["0->3:a", "3->0:a"],
                                "baseline_csv_exists": True,
                                "worker_csv_exists": True,
                                "worker_csv": str(noop_worker_csv),
                                "official_bound_effect": False,
                                "certificate_effect": False,
                                "baseline_status": "TIME_LIMIT",
                                "worker_status": "TIME_LIMIT",
                                "baseline_primal": 10.0,
                                "worker_primal": 10.0,
                                "primal_improvement": 0.0,
                                "baseline_columns": 10,
                                "worker_columns": 10,
                                "columns_delta": 0,
                                "exact_pricing_calls_delta": 0,
                                "generated_sequences_delta": 0,
                                "roi_class": "no_observed_roi",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            _write_worker_stub(
                positive_worker_csv,
                target_sequence=[1, 2],
                context_hash="ctx-pos",
                returned_sequence_samples=[[[1, 2]]],
                append_context_mismatch=True,
            )
            _write_worker_stub(
                noop_worker_csv,
                target_sequence=[3],
                context_hash="ctx-flat",
                returned_sequence_samples=[[[3]]],
            )
            candidate_summary.write_text(
                json.dumps(
                    {
                        "candidates": [
                            {
                                "name": "positive",
                                "instance": instance,
                                "expected_context_hash": "ctx-pos",
                                "target_sequence": [1, 2],
                                "target_arc_option_sequence": ["0->1:a", "1->2:a", "2->0:a"],
                                "decision_name": "HIGH_PRIORITY",
                                "decision_probability": 0.91,
                                "decision_reason": "high_priority",
                                "best_true_reduced_cost": -8.5,
                                "capture_cg_iter": 4,
                                "capture_returned_journey_count": 3,
                                "source_file": "capture.jsonl",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            summary = build_roi_dataset(
                audit_summary_path=audit,
                candidate_summary_paths=[candidate_summary],
                output_dir=tmp / "out",
                report=tmp / "report.md",
                min_positive_for_training=1,
                min_negative_for_training=1,
                min_positive_instances_for_training=1,
                min_negative_instances_for_training=1,
                min_positive_families_for_training=1,
                min_negative_families_for_training=1,
                min_positive_regions_for_training=1,
                min_negative_regions_for_training=1,
                max_label_instance_fraction=1.0,
            )

            rows = [
                json.loads(line)
                for line in (tmp / "out" / "gat_worker_roi_rows.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            by_name = {row["name"]: row for row in rows}
            self.assertTrue(summary["all_checks_pass"])
            self.assertTrue(summary["training_ready"])
            self.assertEqual(summary["label_counts"], {"0": 1, "1": 1})
            self.assertEqual(summary["unique_label_counts"], {"0": 1, "1": 1})
            self.assertEqual(summary["unique_training_row_count"], 2)
            self.assertEqual(summary["positive_region_count"], 1)
            self.assertEqual(summary["negative_region_count"], 1)
            self.assertEqual(summary["positive_region_counts"], {"unknown": 1})
            self.assertEqual(summary["negative_region_counts"], {"unknown": 1})
            self.assertEqual(summary["training_exclusion_reason_counts"], {})
            self.assertEqual(summary["sample_collection_gaps"], [])
            self.assertTrue(all(summary["label_distribution_ready_details"].values()))
            self.assertEqual(summary["duplicate_candidate_count"], 0)
            self.assertEqual(summary["target_diag_available_count"], 2)
            self.assertEqual(summary["worker_context_match_count"], 2)
            self.assertEqual(summary["target_causal_match_count"], 2)
            self.assertEqual(summary["target_intervention_observed_count"], 2)
            self.assertEqual(summary["positive_roi_without_target_causal_match_count"], 0)
            self.assertTrue(summary["label_distribution_ready"])
            self.assertEqual(by_name["positive"]["label_worker_roi_positive"], 1)
            self.assertEqual(by_name["positive"]["label_worker_adds_columns"], 1)
            self.assertEqual(by_name["positive"]["decision_probability"], 0.91)
            self.assertEqual(by_name["positive"]["best_true_reduced_cost"], -8.5)
            self.assertTrue(by_name["positive"]["candidate_feature_joined"])
            self.assertTrue(by_name["positive"]["worker_target_diag_available"])
            self.assertTrue(by_name["positive"]["worker_context_match"])
            self.assertTrue(by_name["positive"]["worker_target_causal_match"])
            self.assertEqual(by_name["noop"]["label_worker_roi_positive"], 0)
            self.assertEqual(by_name["noop"]["label_worker_adds_columns"], 0)
            self.assertFalse(by_name["noop"]["candidate_feature_joined"])
            self.assertTrue(by_name["noop"]["worker_target_intervention_observed"])
            self.assertTrue((tmp / "out" / "gat_worker_roi_rows.csv").exists())
            self.assertTrue((tmp / "report.md").exists())

    def test_missing_result_is_not_training_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            audit = tmp / "audit_summary.json"
            audit.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "records": [
                            {
                                "name": "missing",
                                "instance": "toy_instance.json",
                                "expected_context_hash": "ctx",
                                "target_sequence": [1],
                                "target_arc_option_sequence": ["0->1:a", "1->0:a"],
                                "baseline_csv_exists": True,
                                "worker_csv_exists": False,
                                "official_bound_effect": False,
                                "certificate_effect": False,
                                "primal_improvement": None,
                                "columns_delta": None,
                                "roi_class": "missing_result",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = build_roi_dataset(
                audit_summary_path=audit,
                candidate_summary_paths=[],
                output_dir=tmp / "out",
                report=tmp / "report.md",
                min_positive_for_training=1,
                min_negative_for_training=1,
            )

            rows = [
                json.loads(line)
                for line in (tmp / "out" / "gat_worker_roi_rows.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertFalse(summary["all_checks_pass"])
            self.assertFalse(summary["training_ready"])
            self.assertEqual(summary["training_row_count"], 0)
            self.assertFalse(rows[0]["training_eligible"])
            self.assertEqual(rows[0]["training_exclusion_reason"], "missing_ab_result")
            self.assertIsNone(rows[0]["label_worker_roi_positive"])
            self.assertFalse(summary["certificate_ready"])
            self.assertFalse(summary["official_bound_effect"])

    def test_duplicate_candidate_does_not_inflate_unique_training_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            audit = tmp / "audit_summary.json"
            worker_csv = tmp / "duplicate_worker" / "results.csv"
            duplicate_record = {
                "instance": "toy_instance.json",
                "expected_context_hash": "ctx-pos",
                "target_sequence": [1, 2],
                "target_arc_option_sequence": ["0->1:a", "1->2:a", "2->0:a"],
                "baseline_csv_exists": True,
                "worker_csv_exists": True,
                "worker_csv": str(worker_csv),
                "official_bound_effect": False,
                "certificate_effect": False,
                "baseline_status": "TIME_LIMIT",
                "worker_status": "TIME_LIMIT",
                "baseline_primal": 10.0,
                "worker_primal": 9.0,
                "primal_improvement": 1.0,
                "baseline_columns": 10,
                "worker_columns": 12,
                "columns_delta": 2,
                "roi_class": "positive_primal_roi",
            }
            audit.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "records": [
                            {"name": "positive_a", **duplicate_record},
                            {"name": "positive_b", **duplicate_record},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            _write_worker_stub(
                worker_csv,
                target_sequence=[1, 2],
                context_hash="ctx-pos",
                returned_sequence_samples=[[[1, 2]]],
            )

            summary = build_roi_dataset(
                audit_summary_path=audit,
                candidate_summary_paths=[],
                output_dir=tmp / "out",
                report=tmp / "report.md",
                min_positive_for_training=2,
                min_negative_for_training=1,
            )

            rows = [
                json.loads(line)
                for line in (tmp / "out" / "gat_worker_roi_rows.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(summary["label_counts"], {"1": 2})
            self.assertEqual(summary["unique_label_counts"], {"1": 1})
            self.assertEqual(summary["training_row_count"], 2)
            self.assertEqual(summary["unique_training_row_count"], 1)
            self.assertEqual(summary["duplicate_candidate_count"], 1)
            self.assertFalse(summary["label_distribution_ready"])
            self.assertFalse(summary["training_ready"])
            self.assertEqual(rows[0]["duplicate_group_size"], 2)
            self.assertEqual(rows[1]["duplicate_group_size"], 2)

    def test_training_not_ready_when_positive_labels_are_instance_concentrated(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            audit = tmp / "audit_summary.json"
            records = []
            for idx in range(3):
                worker_csv = tmp / f"positive_worker_{idx}" / "results.csv"
                target_sequence = [idx + 1]
                _write_worker_stub(
                    worker_csv,
                    target_sequence=target_sequence,
                    context_hash=f"ctx-pos-{idx}",
                    returned_sequence_samples=[[target_sequence]],
                )
                records.append(
                    {
                        "name": f"positive_{idx}",
                        "instance": (
                            "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/"
                            "apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json"
                        ),
                        "expected_context_hash": f"ctx-pos-{idx}",
                        "target_sequence": target_sequence,
                        "target_arc_option_sequence": [f"0->{idx + 1}:a", f"{idx + 1}->0:a"],
                        "baseline_csv_exists": True,
                        "worker_csv_exists": True,
                        "worker_csv": str(worker_csv),
                        "official_bound_effect": False,
                        "certificate_effect": False,
                        "baseline_primal": 10.0,
                        "worker_primal": 9.0,
                        "primal_improvement": 1.0,
                        "baseline_columns": 10,
                        "worker_columns": 11,
                        "columns_delta": 1,
                        "roi_class": "positive_primal_roi",
                    }
                )
            for idx in range(3):
                worker_csv = tmp / f"negative_worker_{idx}" / "results.csv"
                target_sequence = [idx + 4]
                _write_worker_stub(
                    worker_csv,
                    target_sequence=target_sequence,
                    context_hash=f"ctx-neg-{idx}",
                    returned_sequence_samples=[[target_sequence]],
                )
                records.append(
                    {
                        "name": f"negative_{idx}",
                        "instance": (
                            "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/"
                            f"tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_0{idx + 1}_seed6100{idx}_logical_graph.json"
                        ),
                        "expected_context_hash": f"ctx-neg-{idx}",
                        "target_sequence": target_sequence,
                        "target_arc_option_sequence": [f"0->{idx + 4}:a", f"{idx + 4}->0:a"],
                        "baseline_csv_exists": True,
                        "worker_csv_exists": True,
                        "worker_csv": str(worker_csv),
                        "official_bound_effect": False,
                        "certificate_effect": False,
                        "baseline_primal": 10.0,
                        "worker_primal": 10.0,
                        "primal_improvement": 0.0,
                        "baseline_columns": 10,
                        "worker_columns": 10,
                        "columns_delta": 0,
                        "roi_class": "no_observed_roi",
                    }
                )
            audit.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "records": records,
                    }
                ),
                encoding="utf-8",
            )

            summary = build_roi_dataset(
                audit_summary_path=audit,
                candidate_summary_paths=[],
                output_dir=tmp / "out",
                report=tmp / "report.md",
                min_positive_for_training=3,
                min_negative_for_training=3,
                min_positive_instances_for_training=2,
                min_negative_instances_for_training=2,
                min_positive_families_for_training=1,
                min_negative_families_for_training=1,
                min_positive_regions_for_training=1,
                min_negative_regions_for_training=1,
                max_label_instance_fraction=0.75,
            )

            self.assertEqual(summary["unique_label_counts"], {"0": 3, "1": 3})
            self.assertEqual(summary["positive_instance_count"], 1)
            self.assertEqual(summary["negative_instance_count"], 3)
            self.assertIn(
                {"name": "positive_instance_count", "observed": 1, "required": 2, "missing": 1},
                summary["sample_collection_gaps"],
            )
            self.assertFalse(summary["label_distribution_ready"])
            self.assertFalse(summary["training_ready"])

    def test_positive_roi_without_target_causal_match_is_not_training_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            audit = tmp / "audit_summary.json"
            worker_csv = tmp / "mismatch_worker" / "results.csv"
            _write_worker_stub(
                worker_csv,
                target_sequence=[1, 2],
                context_hash="ctx-pos",
                returned_sequence_samples=[[[9], [8]]],
            )
            audit.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "records": [
                            {
                                "name": "mismatch_positive",
                                "instance": "toy_instance.json",
                                "expected_context_hash": "ctx-pos",
                                "target_sequence": [1, 2],
                                "target_arc_option_sequence": ["0->1:a", "1->2:a", "2->0:a"],
                                "baseline_csv_exists": True,
                                "worker_csv_exists": True,
                                "worker_csv": str(worker_csv),
                                "official_bound_effect": False,
                                "certificate_effect": False,
                                "baseline_status": "TIME_LIMIT",
                                "worker_status": "TIME_LIMIT",
                                "baseline_primal": 10.0,
                                "worker_primal": 9.0,
                                "primal_improvement": 1.0,
                                "baseline_columns": 10,
                                "worker_columns": 12,
                                "columns_delta": 2,
                                "roi_class": "positive_primal_roi",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = build_roi_dataset(
                audit_summary_path=audit,
                candidate_summary_paths=[],
                output_dir=tmp / "out",
                report=tmp / "report.md",
                min_positive_for_training=1,
                min_negative_for_training=1,
            )

            rows = [
                json.loads(line)
                for line in (tmp / "out" / "gat_worker_roi_rows.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertFalse(summary["all_checks_pass"])
            self.assertEqual(summary["training_row_count"], 0)
            self.assertEqual(summary["label_counts"], {})
            self.assertEqual(summary["target_diag_available_count"], 1)
            self.assertEqual(summary["target_causal_match_count"], 0)
            self.assertEqual(summary["positive_roi_without_target_causal_match_count"], 1)
            self.assertEqual(
                summary["training_exclusion_reason_counts"],
                {"positive_roi_without_target_causal_match": 1},
            )
            self.assertTrue(rows[0]["worker_target_diag_available"])
            self.assertFalse(rows[0]["worker_target_causal_match"])
            self.assertFalse(rows[0]["training_eligible"])
            self.assertEqual(
                rows[0]["training_exclusion_reason"],
                "positive_roi_without_target_causal_match",
            )

    def test_no_observed_roi_without_target_causal_match_is_not_training_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            audit = tmp / "audit_summary.json"
            worker_csv = tmp / "mismatch_noop_worker" / "results.csv"
            _write_worker_stub(
                worker_csv,
                target_sequence=[5],
                context_hash="ctx-flat",
                returned_sequence_samples=[[[7]]],
            )
            audit.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "records": [
                            {
                                "name": "mismatch_noop",
                                "instance": "toy_instance.json",
                                "expected_context_hash": "ctx-flat",
                                "target_sequence": [5],
                                "target_arc_option_sequence": ["0->5:a", "5->0:a"],
                                "baseline_csv_exists": True,
                                "worker_csv_exists": True,
                                "worker_csv": str(worker_csv),
                                "official_bound_effect": False,
                                "certificate_effect": False,
                                "baseline_status": "TIME_LIMIT",
                                "worker_status": "TIME_LIMIT",
                                "baseline_primal": 10.0,
                                "worker_primal": 10.0,
                                "primal_improvement": 0.0,
                                "baseline_columns": 10,
                                "worker_columns": 10,
                                "columns_delta": 0,
                                "roi_class": "no_observed_roi",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = build_roi_dataset(
                audit_summary_path=audit,
                candidate_summary_paths=[],
                output_dir=tmp / "out",
                report=tmp / "report.md",
                min_positive_for_training=1,
                min_negative_for_training=1,
            )

            rows = [
                json.loads(line)
                for line in (tmp / "out" / "gat_worker_roi_rows.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertFalse(summary["all_checks_pass"])
            self.assertEqual(summary["training_row_count"], 0)
            self.assertEqual(summary["label_counts"], {})
            self.assertEqual(summary["roi_without_target_causal_match_count"], 1)
            self.assertTrue(rows[0]["worker_target_intervention_observed"])
            self.assertFalse(rows[0]["worker_target_causal_match"])
            self.assertFalse(rows[0]["training_eligible"])
            self.assertEqual(
                rows[0]["training_exclusion_reason"],
                "roi_without_target_causal_match",
            )

    def test_matching_target_in_wrong_context_is_not_training_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            audit = tmp / "audit_summary.json"
            worker_csv = tmp / "wrong_context_worker" / "results.csv"
            _write_worker_stub(
                worker_csv,
                target_sequence=[6],
                context_hash="ctx-observed-other",
                returned_sequence_samples=[[[6]]],
            )
            audit.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "records": [
                            {
                                "name": "wrong_context_noop",
                                "instance": "toy_instance.json",
                                "expected_context_hash": "ctx-expected",
                                "target_sequence": [6],
                                "target_arc_option_sequence": ["0->6:a", "6->0:a"],
                                "baseline_csv_exists": True,
                                "worker_csv_exists": True,
                                "worker_csv": str(worker_csv),
                                "official_bound_effect": False,
                                "certificate_effect": False,
                                "baseline_status": "TIME_LIMIT",
                                "worker_status": "TIME_LIMIT",
                                "baseline_primal": 10.0,
                                "worker_primal": 10.0,
                                "primal_improvement": 0.0,
                                "baseline_columns": 10,
                                "worker_columns": 10,
                                "columns_delta": 0,
                                "roi_class": "no_observed_roi",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = build_roi_dataset(
                audit_summary_path=audit,
                candidate_summary_paths=[],
                output_dir=tmp / "out",
                report=tmp / "report.md",
                min_positive_for_training=1,
                min_negative_for_training=1,
            )

            rows = [
                json.loads(line)
                for line in (tmp / "out" / "gat_worker_roi_rows.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertFalse(summary["all_checks_pass"])
            self.assertEqual(summary["training_row_count"], 0)
            self.assertEqual(summary["worker_context_mismatch_count"], 1)
            self.assertEqual(summary["worker_context_match_count"], 0)
            self.assertTrue(rows[0]["worker_target_causal_match"])
            self.assertFalse(rows[0]["worker_context_match"])
            self.assertFalse(rows[0]["training_eligible"])
            self.assertEqual(rows[0]["training_exclusion_reason"], "worker_context_mismatch")

    def test_no_observed_roi_without_worker_intervention_is_not_training_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            audit = tmp / "audit_summary.json"
            audit.write_text(
                json.dumps(
                    {
                        "certificate_ready": False,
                        "official_bound_effect": False,
                        "records": [
                            {
                                "name": "no_intervention_noop",
                                "instance": "toy_instance.json",
                                "expected_context_hash": "ctx-flat",
                                "target_sequence": [5],
                                "target_arc_option_sequence": ["0->5:a", "5->0:a"],
                                "baseline_csv_exists": True,
                                "worker_csv_exists": True,
                                "worker_csv": str(tmp / "missing_worker_log" / "results.csv"),
                                "official_bound_effect": False,
                                "certificate_effect": False,
                                "baseline_status": "TIME_LIMIT",
                                "worker_status": "TIME_LIMIT",
                                "baseline_primal": 10.0,
                                "worker_primal": 10.0,
                                "primal_improvement": 0.0,
                                "baseline_columns": 10,
                                "worker_columns": 10,
                                "columns_delta": 0,
                                "roi_class": "no_observed_roi",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = build_roi_dataset(
                audit_summary_path=audit,
                candidate_summary_paths=[],
                output_dir=tmp / "out",
                report=tmp / "report.md",
                min_positive_for_training=1,
                min_negative_for_training=1,
            )

            rows = [
                json.loads(line)
                for line in (tmp / "out" / "gat_worker_roi_rows.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertFalse(summary["all_checks_pass"])
            self.assertEqual(summary["training_row_count"], 0)
            self.assertEqual(summary["label_counts"], {})
            self.assertEqual(summary["no_worker_target_intervention_count"], 1)
            self.assertFalse(rows[0]["worker_target_intervention_observed"])
            self.assertFalse(rows[0]["training_eligible"])
            self.assertEqual(
                rows[0]["training_exclusion_reason"],
                "no_worker_target_intervention_observed",
            )


if __name__ == "__main__":
    unittest.main()
