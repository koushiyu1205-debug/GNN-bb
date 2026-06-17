from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

try:
    import torch

    from BPC_future.learning.batch_impact_model import GATBatchImpactModel
    from BPC_future.scripts.build_gat_batch_impact_dataset import (
        BATCH_IMPACT_BATCH_FEATURE_SCHEMA,
        BATCH_IMPACT_CANDIDATE_FEATURE_SCHEMA,
        BATCH_IMPACT_CONTEXT_FEATURE_SCHEMA,
        build_dataset,
    )
    from BPC_future.solver.gat_candidate_id import journey_gat_candidate_id_from_signature
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATBatchImpactDatasetTests(unittest.TestCase):
    def test_builds_batch_impact_samples_with_sequence_and_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph_pos = root / "graph_pos.json"
            graph_neg = root / "graph_neg.json"
            graph_pos.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            graph_neg.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            source_log = root / "events.jsonl"
            rows_jsonl = root / "same_run_rows.jsonl"
            output_dir = root / "dataset"
            report = root / "report.md"

            _write_jsonl(
                source_log,
                [
                    _capture_event(
                        graph_path=graph_pos,
                        context_hash="ctx-pos",
                        cg_iter=1,
                        instance="inst-pos",
                        returned=[
                            _journey("jp1", [1, 3], -2.0, [[1, 3]]),
                            _journey("jp2", [2], 0.5, [[2]]),
                        ],
                    ),
                    _capture_event(
                        graph_path=graph_neg,
                        context_hash="ctx-neg",
                        cg_iter=2,
                        instance="inst-neg",
                        returned=[
                            _journey("jn1", [1, 2], -1.0, [[2, 1]]),
                            _journey("jn2", [3], 0.2, [[3]]),
                        ],
                    ),
                ],
            )
            _write_jsonl(
                rows_jsonl,
                [
                    _row(
                        source_file=source_log,
                        graph_path=graph_pos,
                        context_hash="ctx-pos",
                        cg_iter=1,
                        instance="inst-pos",
                        region="apollo15_20km",
                        objective_improvement=5.0,
                        label_objective_improved=1,
                        active_changed_task_set_count=1,
                        new_task_set_count=1,
                        replacement_journeys=0,
                    ),
                    _row(
                        source_file=source_log,
                        graph_path=graph_neg,
                        context_hash="ctx-neg",
                        cg_iter=2,
                        instance="inst-neg",
                        region="tranquillitatis_balmer_like_20km",
                        objective_improvement=0.0,
                        label_objective_improved=0,
                        active_changed_task_set_count=1,
                        new_task_set_count=0,
                        replacement_journeys=1,
                    ),
                ],
            )

            summary = build_dataset(
                input_jsonl=rows_jsonl,
                output_dir=output_dir,
                report=report,
                min_samples_for_training=2,
                min_positive_batches_for_training=1,
                min_delay_candidates_for_training=1,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertTrue(summary["training_ready"])
            self.assertEqual(summary["sample_count"], 2)
            self.assertEqual(summary["candidate_count"], 4)
            self.assertEqual(summary["context_match_rate"], 1.0)
            self.assertFalse(summary["ranking_ready"])
            self.assertEqual(summary["ranking_blockers"], ["need_same_context_batch_pairs_for_pairwise_ranking"])
            self.assertEqual(summary["pairwise_context_stats"]["same_context_pair_count"], 0)
            self.assertEqual(summary["pairwise_context_stats"]["multi_context_count"], 0)
            self.assertEqual(summary["batch_label_counts"], {"non_improving": 1, "roi_positive": 1})
            self.assertEqual(
                summary["candidate_label_counts"],
                {
                    "delay_queue": 1,
                    "high_priority": 1,
                    "nonnegative_reject_only": 2,
                },
            )

            manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertFalse(manifest["production_ready"])
            self.assertFalse(manifest["runs_bpc_or_pricing"])
            self.assertFalse(manifest["exactness_contract"]["pricing_oracle"])
            self.assertFalse(manifest["exactness_contract"]["certificate_source"])
            self.assertFalse(manifest["exactness_contract"]["official_bound_effect"])
            self.assertFalse(manifest["exactness_contract"]["can_permanently_discard_true_rc_negative"])
            self.assertFalse(manifest["ranking_ready"])
            self.assertEqual(manifest["ranking_blockers"], ["need_same_context_batch_pairs_for_pairwise_ranking"])
            self.assertEqual(manifest["pairwise_context_stats"]["same_context_pair_count"], 0)
            self.assertEqual(manifest["candidate_feature_schema"], list(BATCH_IMPACT_CANDIDATE_FEATURE_SCHEMA))
            self.assertEqual(manifest["context_feature_schema"], list(BATCH_IMPACT_CONTEXT_FEATURE_SCHEMA))
            self.assertEqual(manifest["batch_feature_schema"], list(BATCH_IMPACT_BATCH_FEATURE_SCHEMA))
            self.assertEqual(manifest["candidate_path_token_schema"]["token_hash_bucket_count"], 4096)
            self.assertEqual(manifest["candidate_path_token_schema"]["pair_hash_bucket_count"], 4096)
            self.assertEqual(manifest["candidate_signature_source_coverage"], 1.0)
            self.assertEqual(
                manifest["samples"][0]["candidate_signature_ids"][0],
                journey_gat_candidate_id_from_signature(["jp1"]),
            )

            sample = torch.load(output_dir / "samples" / "sample_000000.pt", map_location="cpu", weights_only=False)
            self.assertEqual(tuple(sample.candidate_task_membership.shape), (2, 3))
            self.assertEqual(tuple(sample.candidate_sequence_positions.shape), (2, 3))
            self.assertEqual(sample.candidate_sequence_positions[0].tolist(), [1.0, 0.0, 2.0])
            self.assertEqual(tuple(sample.candidate_features.shape), (2, len(BATCH_IMPACT_CANDIDATE_FEATURE_SCHEMA)))
            schema = list(BATCH_IMPACT_CANDIDATE_FEATURE_SCHEMA)
            self.assertIn("trace_arc_option_count", schema)
            self.assertIn("trace_total_energy", schema)
            self.assertIn("trace_service_start_span", schema)
            self.assertIn("trace_occupancy_bucket_count", schema)
            self.assertIn("slack_min_late_time", schema)
            self.assertIn("slack_min_early_time", schema)
            self.assertEqual(
                sample.candidate_features[0, schema.index("trace_arc_option_count")].item(),
                3.0,
            )
            self.assertEqual(
                sample.candidate_features[0, schema.index("trace_low_time_arc_count")].item(),
                2.0,
            )
            self.assertEqual(
                sample.candidate_features[0, schema.index("trace_low_energy_arc_count")].item(),
                1.0,
            )
            self.assertAlmostEqual(
                sample.candidate_features[0, schema.index("trace_total_energy")].item(),
                7.0,
            )
            self.assertAlmostEqual(
                sample.candidate_features[0, schema.index("trace_service_start_span")].item(),
                8.0,
            )
            self.assertEqual(
                sample.candidate_features[0, schema.index("trace_occupancy_bucket_count")].item(),
                1.0,
            )
            self.assertAlmostEqual(
                sample.candidate_features[0, schema.index("slack_min_late_time")].item(),
                190.0,
            )
            self.assertAlmostEqual(
                sample.candidate_features[0, schema.index("slack_min_early_time")].item(),
                -2.0,
            )
            self.assertEqual(tuple(sample.candidate_path_token_ids.shape), (2, 3))
            self.assertEqual(tuple(sample.candidate_path_pair_ids.shape), (2, 3))
            self.assertEqual(tuple(sample.candidate_path_type_ids.shape), (2, 3))
            self.assertEqual(tuple(sample.candidate_path_token_mask.shape), (2, 3))
            self.assertTrue(bool(torch.all(sample.candidate_path_token_ids[0] > 0)))
            self.assertEqual(sample.candidate_path_type_ids[0].tolist(), [1, 2, 1])
            self.assertEqual(sample.candidate_path_token_mask[0].tolist(), [True, True, True])
            self.assertEqual(tuple(sample.context_features.shape), (len(BATCH_IMPACT_CONTEXT_FEATURE_SCHEMA),))
            self.assertEqual(tuple(sample.batch_features.shape), (len(BATCH_IMPACT_BATCH_FEATURE_SCHEMA),))
            self.assertEqual(sample.y_candidate_high_priority.tolist(), [1.0, 0.0])
            self.assertEqual(sample.y_candidate_delay_risk.tolist(), [0.0, 0.0])
            self.assertEqual(sample.y_candidate_true_rc_negative.tolist(), [1.0, 0.0])
            self.assertEqual(sample.y_batch_roi_positive.tolist(), [1.0])
            self.assertEqual(sample.y_accepted_batch_roi.tolist(), [2.5])
            self.assertEqual(
                sample.batch_impact_candidate_signature_ids[0],
                journey_gat_candidate_id_from_signature(["jp1"]),
            )
            self.assertEqual(sample.batch_impact_candidate_signature_source_present, [True, True])
            self.assertTrue(report.exists())

            model = GATBatchImpactModel(
                node_dim=sample.x.size(1),
                option_dim=sample.option_feat.size(1),
                candidate_feature_dim=sample.candidate_features.size(1),
                context_feature_dim=sample.context_features.numel(),
                batch_feature_dim=sample.batch_features.numel(),
                hidden_dim=16,
                option_hidden_dim=16,
                pair_edge_dim=16,
                num_gnn_layers=1,
                heads=4,
                dropout=0.0,
                candidate_hidden_dim=16,
                context_hidden_dim=8,
                batch_hidden_dim=12,
                impact_hidden_dim=10,
                path_token_vocab_size=manifest["candidate_path_token_schema"]["token_hash_bucket_count"],
                path_pair_vocab_size=manifest["candidate_path_token_schema"]["pair_hash_bucket_count"],
                path_type_vocab_size=3,
                path_token_dim=8,
                path_hidden_dim=12,
            )
            output = model(
                sample,
                sample.candidate_task_membership,
                sample.candidate_sequence_positions,
                sample.candidate_features,
                sample.context_features,
                batch_features=sample.batch_features,
                candidate_path_token_ids=sample.candidate_path_token_ids,
                candidate_path_pair_ids=sample.candidate_path_pair_ids,
                candidate_path_type_ids=sample.candidate_path_type_ids,
                candidate_path_token_mask=sample.candidate_path_token_mask,
            )
            self.assertEqual(tuple(output["candidate_embedding"].shape), (2, 16))
            self.assertEqual(tuple(output["candidate_path_embedding"].shape), (2, 12))
            self.assertEqual(tuple(output["high_priority_probability"].shape), (2,))
            self.assertEqual(tuple(output["predicted_accepted_batch_roi"].shape), (1,))

    def test_pairwise_ranking_ready_requires_roi_diverse_same_context_pairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph_path = root / "graph.json"
            graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            source_log = root / "events.jsonl"
            rows_jsonl = root / "same_run_rows.jsonl"
            output_dir = root / "dataset"

            _write_jsonl(
                source_log,
                [
                    _capture_event(
                        graph_path=graph_path,
                        context_hash="ctx-shared",
                        cg_iter=1,
                        instance="inst-shared",
                        returned=[_journey("j1", [1, 3], -2.0, [[1, 3]])],
                    )
                ],
            )
            _write_jsonl(
                rows_jsonl,
                [
                    _row(
                        source_file=source_log,
                        graph_path=graph_path,
                        context_hash="ctx-shared",
                        cg_iter=1,
                        instance="inst-shared",
                        region="apollo15_20km",
                        objective_improvement=5.0,
                        label_objective_improved=1,
                        active_changed_task_set_count=1,
                        new_task_set_count=1,
                        replacement_journeys=0,
                    ),
                    _row(
                        source_file=source_log,
                        graph_path=graph_path,
                        context_hash="ctx-shared",
                        cg_iter=1,
                        instance="inst-shared",
                        region="apollo15_20km",
                        objective_improvement=0.0,
                        label_objective_improved=0,
                        active_changed_task_set_count=1,
                        new_task_set_count=0,
                        replacement_journeys=1,
                    ),
                ],
            )

            summary = build_dataset(
                input_jsonl=rows_jsonl,
                output_dir=output_dir,
                report=root / "report.md",
                min_samples_for_training=1,
                min_positive_batches_for_training=1,
                min_delay_candidates_for_training=1,
                min_same_context_pairs_for_ranking=1,
            )

            self.assertTrue(summary["ranking_ready"])
            self.assertEqual(summary["ranking_blockers"], [])
            self.assertEqual(summary["pairwise_context_stats"]["same_context_pair_count"], 1)
            self.assertEqual(summary["pairwise_context_stats"]["same_context_comparable_pair_count"], 1)
            self.assertEqual(summary["pairwise_context_stats"]["positive_negative_label_pair_count"], 1)

    def test_explicit_long_horizon_labels_override_immediate_objective_gain(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph_path = root / "graph.json"
            graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            source_log = root / "events.jsonl"
            rows_jsonl = root / "same_run_rows.jsonl"
            output_dir = root / "dataset"

            _write_jsonl(
                source_log,
                [
                    _capture_event(
                        graph_path=graph_path,
                        context_hash="ctx-long",
                        cg_iter=1,
                        instance="inst-long",
                        returned=[_journey("j1", [1, 2], -2.0, [[1, 2]])],
                    )
                ],
            )
            row = _row(
                source_file=source_log,
                graph_path=graph_path,
                context_hash="ctx-long",
                cg_iter=1,
                instance="inst-long",
                region="apollo15_20km",
                objective_improvement=3.0,
                label_objective_improved=1,
                active_changed_task_set_count=1,
                new_task_set_count=0,
                replacement_journeys=1,
            )
            row.update(
                {
                    "label_batch_roi_positive": 0,
                    "accepted_batch_roi_label": -4.25,
                    "label_bad_mode_switch": 1,
                    "label_support_changed_good": 0,
                    "delta_v_label": 4.25,
                    "barrier_slack_label": -4.25,
                }
            )
            _write_jsonl(rows_jsonl, [row])

            summary = build_dataset(
                input_jsonl=rows_jsonl,
                output_dir=output_dir,
                report=root / "report.md",
                min_samples_for_training=1,
                min_positive_batches_for_training=0,
                min_delay_candidates_for_training=1,
            )

            self.assertEqual(summary["batch_label_counts"], {"non_improving": 1})
            self.assertEqual(summary["candidate_label_counts"], {"delay_queue": 1})
            manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["samples"][0]["high_priority_candidate_count"], 0)
            self.assertEqual(manifest["samples"][0]["delay_candidate_count"], 1)
            self.assertEqual(manifest["samples"][0]["label_batch_roi_positive"], 0)
            self.assertAlmostEqual(manifest["samples"][0]["accepted_batch_roi"], -4.25)
            sample = torch.load(
                output_dir / "samples" / "sample_000000.pt",
                map_location="cpu",
                weights_only=False,
            )
            self.assertEqual(sample.y_candidate_high_priority.tolist(), [0.0])
            self.assertEqual(sample.y_candidate_delay_risk.tolist(), [1.0])
            self.assertEqual(sample.y_batch_roi_positive.tolist(), [0.0])
            self.assertEqual(sample.y_bad_mode_switch.tolist(), [1.0])
            self.assertEqual(sample.y_support_changed_good.tolist(), [0.0])
            self.assertEqual(sample.y_accepted_batch_roi.tolist(), [-4.25])
            self.assertEqual(sample.y_delta_v.tolist(), [4.25])
            self.assertEqual(sample.y_barrier_slack.tolist(), [-4.25])

    def test_repeated_input_jsonl_paths_are_merged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph_pos = root / "graph_pos.json"
            graph_neg = root / "graph_neg.json"
            graph_pos.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            graph_neg.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            source_log = root / "events.jsonl"
            rows_pos = root / "rows_pos.jsonl"
            rows_neg = root / "rows_neg.jsonl"
            output_dir = root / "dataset"

            _write_jsonl(
                source_log,
                [
                    _capture_event(
                        graph_path=graph_pos,
                        context_hash="ctx-pos",
                        cg_iter=1,
                        instance="inst-pos",
                        returned=[_journey("jp", [1], -1.0, [[1]])],
                    ),
                    _capture_event(
                        graph_path=graph_neg,
                        context_hash="ctx-neg",
                        cg_iter=2,
                        instance="inst-neg",
                        returned=[_journey("jn", [2], -1.0, [[2]])],
                    ),
                ],
            )
            _write_jsonl(
                rows_pos,
                [
                    _row(
                        source_file=source_log,
                        graph_path=graph_pos,
                        context_hash="ctx-pos",
                        cg_iter=1,
                        instance="inst-pos",
                        region="apollo15_20km",
                        objective_improvement=5.0,
                        label_objective_improved=1,
                        active_changed_task_set_count=1,
                        new_task_set_count=1,
                        replacement_journeys=0,
                    )
                ],
            )
            _write_jsonl(
                rows_neg,
                [
                    _row(
                        source_file=source_log,
                        graph_path=graph_neg,
                        context_hash="ctx-neg",
                        cg_iter=2,
                        instance="inst-neg",
                        region="tranquillitatis_balmer_like_20km",
                        objective_improvement=0.0,
                        label_objective_improved=0,
                        active_changed_task_set_count=1,
                        new_task_set_count=0,
                        replacement_journeys=1,
                    )
                ],
            )

            summary = build_dataset(
                input_jsonl=[rows_pos, rows_neg],
                output_dir=output_dir,
                report=root / "report.md",
                min_samples_for_training=2,
                min_positive_batches_for_training=1,
                min_delay_candidates_for_training=1,
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["sample_count"], 2)
            self.assertEqual(summary["source_jsonl_paths"], [str(rows_pos), str(rows_neg)])
            self.assertEqual(summary["source_jsonl"], "")

            manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["source_jsonl_paths"], [str(rows_pos), str(rows_neg)])
            self.assertEqual(manifest["source_jsonl"], "")

    def test_unsafe_rows_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            graph_path = root / "graph.json"
            graph_path.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            source_log = root / "events.jsonl"
            rows_jsonl = root / "same_run_rows.jsonl"
            _write_jsonl(
                source_log,
                [
                    _capture_event(
                        graph_path=graph_path,
                        context_hash="ctx",
                        cg_iter=1,
                        instance="inst",
                        returned=[_journey("j", [1], -1.0, [[1]])],
                    )
                ],
            )
            unsafe = _row(
                source_file=source_log,
                graph_path=graph_path,
                context_hash="ctx",
                cg_iter=1,
                instance="inst",
                region="apollo15_20km",
                objective_improvement=1.0,
                label_objective_improved=1,
                active_changed_task_set_count=0,
                new_task_set_count=1,
                replacement_journeys=0,
            )
            unsafe["official_bound_effect"] = True
            _write_jsonl(rows_jsonl, [unsafe])

            summary = build_dataset(input_jsonl=rows_jsonl, output_dir=root / "dataset", report=root / "report.md")

            self.assertFalse(summary["all_checks_pass"])
            self.assertEqual(summary["sample_count"], 0)
            self.assertEqual(summary["skipped_counts"], {"non_diagnostic_or_official_effect": 1})


def _capture_event(
    *,
    graph_path: Path,
    context_hash: str,
    cg_iter: int,
    instance: str,
    returned: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "event": "journey_counterfactual_replay_capture",
        "instance": instance,
        "instance_path": str(graph_path),
        "context_hash": context_hash,
        "cg_iter": cg_iter,
        "pricing_kind": "exact",
        "node_id": 0,
        "depth": 0,
        "pool_journey_count": 8,
        "active_basis_journey_count": 3,
        "active_task_set_count": 3,
        "active_basis_fractional_journey_count": 1,
        "true_dual_vector": [1.0, -2.0, 3.0],
        "true_duals": {"fleet_limit": 4.0},
        "cut_duals": {"cut-a": -0.5, "cut-b": 0.25},
        "branch_constraints": [{"type": "same_vehicle"}],
        "pool_task_sets": [[1, 2]],
        "pool_signatures": [["old"]],
        "state_t_final_judge_retry_count": 2,
        "returned_journeys": returned,
    }


def _row(
    *,
    source_file: Path,
    graph_path: Path,
    context_hash: str,
    cg_iter: int,
    instance: str,
    region: str,
    objective_improvement: float,
    label_objective_improved: int,
    active_changed_task_set_count: int,
    new_task_set_count: int,
    replacement_journeys: int,
) -> dict[str, object]:
    return {
        "schema_version": "gat_same_run_batch_impact_row_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "certificate_effect": False,
        "official_bound_effect": False,
        "source_file": str(source_file),
        "instance": instance,
        "instance_path": str(graph_path),
        "instance_region": region,
        "cg_iter": cg_iter,
        "node_id": 0,
        "depth": 0,
        "pricing_kind": "exact",
        "context_hash": context_hash,
        "true_dual_hash": f"dual-{context_hash}",
        "cut_hash": f"cut-{context_hash}",
        "branch_hash": f"branch-{context_hash}",
        "returned_journey_count": 2,
        "added_journeys": 2,
        "new_journeys": 1,
        "replacement_journeys": replacement_journeys,
        "new_task_set_count": new_task_set_count,
        "replacement_task_set_count": replacement_journeys,
        "active_changed_task_set_count": active_changed_task_set_count,
        "best_true_reduced_cost": -2.0,
        "objective_before": 100.0,
        "objective_after": 100.0 - objective_improvement,
        "objective_delta": -objective_improvement,
        "objective_improvement": objective_improvement,
        "label_objective_improved": label_objective_improved,
        "label_active_support_changing": int(active_changed_task_set_count > 0),
        "label_new_task_set_added": int(new_task_set_count > 0),
        "same_run_intervention_observed": True,
        "training_label_allowed": True,
        "training_label_scope": "same_run_returned_batch",
    }


def _journey(
    journey_id: str,
    task_set: list[int],
    true_rc: float,
    sequence: list[list[int]],
) -> dict[str, object]:
    first_sequence = sequence[0]
    arc_option_ids = ["0->start:low_time:0"]
    for left, right in zip(first_sequence, first_sequence[1:]):
        arc_option_ids.append(f"{left}->{right}:low_energy:0")
    arc_option_ids.append("end->0:low_time:0")
    service_start = {
        str(task_id): 10.0 + float(index) * 8.0
        for index, task_id in enumerate(first_sequence)
    }
    return {
        "id": journey_id,
        "task_set": task_set,
        "sequence": sequence,
        "true_reduced_cost": true_rc,
        "cost": 20.0,
        "start_time": 5.0,
        "end_time": 25.0,
        "trips": [
            {
                "task_sequence": first_sequence,
                "arc_option_ids": arc_option_ids,
                "start_time": 5.0,
                "end_time": 25.0,
                "distance": 3.0,
                "energy": 7.0,
                "risk": 0.5,
                "travel_time": 12.0,
                "load": 2.0,
                "survival_energy": 4.0,
                "recharge_time": 1.5,
                "service_start": service_start,
                "occupancy": {"5": 1.0},
            }
        ],
        "signature": [journey_id],
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
