from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

try:
    import torch

    from BPC_future.learning.batch_impact_model import BATCH_IMPACT_EXACTNESS_CONTRACT
    from BPC_future.scripts.build_gat_batch_impact_dataset import build_dataset
    from BPC_future.scripts.train_gat_batch_impact import (
        _candidate_acceptance_logit,
        _context_pair_stats,
        _gate_config,
        _hard_roi_positive_candidate_boost_loss,
        _loss_options,
        _pairwise_ranking_loss,
        _same_context_roi_pairs,
        _threshold_search,
        _with_hard_roi_positive_group_balance,
        train_batch_impact,
    )
    from BPC_future.tests.test_gat_batch_impact_dataset import (
        _capture_event,
        _journey,
        _row,
        _write_jsonl,
    )
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATBatchImpactTrainingTests(unittest.TestCase):
    def test_gate_config_defaults_family_roi_to_hard_roi_threshold(self):
        args = SimpleNamespace(
            min_validation_high_priority_precision=0.9,
            min_validation_safe_precision=0.9,
            max_false_high_priority_on_delay=0.01,
            max_false_safe_union_rate=0.02,
            min_accepted_batch_count=1,
            min_accepted_batch_rate=0.02,
            min_accepted_batch_roi=0.65,
            baseline_accepted_batch_roi=0.55,
            min_roi_margin_over_baseline=0.2,
            min_major_families=3,
            stage3_min_samples=200,
        )
        gate = _gate_config(args, {"family_counts": {"a": 1, "b": 1, "c": 1}, "sample_count": 300})

        self.assertEqual(gate["min_accepted_batch_roi"], 0.75)
        self.assertEqual(gate["min_family_holdout_accepted_roi"], 0.75)
        self.assertEqual(gate["min_high_priority_precision_ci_low"], 0.9)
        self.assertEqual(gate["min_safe_precision_ci_low"], 0.9)
        self.assertEqual(gate["min_accepted_batch_roi_ci_low"], 0.75)
        self.assertEqual(gate["min_family_accepted_high_roi_count"], 0)
        self.assertEqual(gate["min_family_high_roi_capture_rate"], 0.0)

    def test_loss_options_default_hard_roi_threshold_matches_deployment_gate(self):
        args = SimpleNamespace(
            min_accepted_batch_roi=0.65,
            baseline_accepted_batch_roi=0.55,
            min_roi_margin_over_baseline=0.20,
            false_high_priority_loss_multiplier=4.0,
            bad_mode_loss_multiplier=2.0,
            regression_loss_multiplier=0.15,
            hard_roi_loss_multiplier=3.0,
            hard_roi_candidate_loss_multiplier=0.75,
            hard_roi_positive_candidate_loss_multiplier=1.5,
            hard_roi_threshold=None,
            pairwise_ranking_loss_multiplier=2.5,
            pairwise_candidate_ranking_loss_multiplier=1.25,
            pairwise_roi_margin=0.15,
            min_pairwise_roi_delta=0.01,
            max_grad_norm=5.0,
        )

        loss_options = _loss_options(args)

        self.assertEqual(loss_options["hard_roi_threshold"], 0.75)
        self.assertEqual(loss_options["hard_roi_loss_multiplier"], 3.0)
        self.assertEqual(loss_options["hard_roi_candidate_loss_multiplier"], 0.75)
        self.assertEqual(loss_options["hard_roi_positive_candidate_loss_multiplier"], 1.5)
        self.assertEqual(loss_options["pairwise_ranking_loss_multiplier"], 2.5)
        self.assertEqual(loss_options["pairwise_candidate_ranking_loss_multiplier"], 1.25)
        self.assertEqual(loss_options["pairwise_roi_margin"], 0.15)
        self.assertEqual(loss_options["min_pairwise_roi_delta"], 0.01)

    def test_hard_roi_positive_candidate_boost_loss_only_boosts_high_roi_safe_candidates(self):
        logits = torch.tensor([-2.0, 0.0, 2.0])
        hp_target = torch.tensor([1.0, 0.0, 1.0])

        active_loss = _hard_roi_positive_candidate_boost_loss(
            logits,
            hp_target,
            torch.tensor(1.0),
        )
        inactive_low_roi_loss = _hard_roi_positive_candidate_boost_loss(
            logits,
            hp_target,
            torch.tensor(0.0),
        )
        inactive_no_positive_loss = _hard_roi_positive_candidate_boost_loss(
            logits,
            torch.zeros_like(hp_target),
            torch.tensor(1.0),
        )

        expected = torch.nn.functional.binary_cross_entropy_with_logits(
            torch.tensor([-2.0, 2.0]),
            torch.ones(2),
        )
        self.assertAlmostEqual(float(active_loss), float(expected), places=6)
        self.assertEqual(float(inactive_low_roi_loss), 0.0)
        self.assertEqual(float(inactive_no_positive_loss), 0.0)

    def test_hard_roi_positive_candidate_boost_loss_applies_group_weight(self):
        logits = torch.tensor([-2.0, 2.0])
        hp_target = torch.tensor([1.0, 1.0])

        unweighted = _hard_roi_positive_candidate_boost_loss(
            logits,
            hp_target,
            torch.tensor(1.0),
        )
        weighted = _hard_roi_positive_candidate_boost_loss(
            logits,
            hp_target,
            torch.tensor(1.0),
            positive_weight=3.0,
        )

        self.assertAlmostEqual(float(weighted), 3.0 * float(unweighted), places=6)

    def test_hard_roi_positive_group_balance_boosts_sparse_family_task_groups(self):
        def sample(family: str, task_count: int, roi: float, bad: float = 0.0) -> SimpleNamespace:
            return SimpleNamespace(
                batch_impact_instance_family=family,
                batch_impact_task_count=task_count,
                y_accepted_batch_roi=torch.tensor(roi),
                y_bad_mode_switch=torch.tensor(bad),
            )

        loss_options = {
            "hard_roi_threshold": 0.65,
            "hard_roi_positive_group_balance": "family_task",
            "hard_roi_positive_group_weight_power": 1.0,
            "max_hard_roi_positive_group_weight": 4.0,
        }

        balanced = _with_hard_roi_positive_group_balance(
            loss_options,
            [
                sample("random-wave", 50, 1.0),
                sample("random-wave", 20, 1.0),
                sample("random-wave", 20, 1.2),
                sample("random-wave", 20, 1.4),
                sample("sector-wave", 20, 1.0),
                sample("sector-wave", 20, 1.2),
                sample("sector-wave", 20, 1.4),
                sample("sector-wave", 20, 1.6),
                sample("sector-wave", 20, 0.2),
                sample("sector-wave", 20, 10.0, bad=1.0),
            ],
        )

        self.assertEqual(
            balanced["hard_roi_positive_group_counts"],
            {"random-wave|20": 3, "random-wave|50": 1, "sector-wave|20": 4},
        )
        self.assertGreater(
            balanced["hard_roi_positive_group_weights"]["random-wave|50"],
            balanced["hard_roi_positive_group_weights"]["random-wave|20"],
        )
        self.assertGreaterEqual(
            balanced["hard_roi_positive_group_weights"]["sector-wave|20"],
            1.0,
        )

    def test_pairwise_candidate_ranking_uses_safe_candidate_against_any_worse_candidate(self):
        class FakeSample(SimpleNamespace):
            def to(self, device):
                return self

        class FakeModel:
            def __call__(self, sample, *args, **kwargs):
                return {
                    "batch_roi_positive_logit": sample.batch_logit,
                    "high_priority_logit": sample.candidate_logits,
                }

        better = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([5.0]),
            candidate_logits=torch.tensor([0.1, 2.0, 0.2]),
            y_candidate_high_priority=torch.tensor([0.0, 1.0, 0.0]),
        )
        worse = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            candidate_logits=torch.tensor([4.0, 0.3, 0.2]),
            y_candidate_high_priority=torch.tensor([1.0, 0.0, 0.0]),
        )

        self.assertAlmostEqual(
            float(_candidate_acceptance_logit(FakeModel(), better, torch.device("cpu"), labeled_safe_only=True)),
            2.0,
        )
        self.assertAlmostEqual(
            float(_candidate_acceptance_logit(FakeModel(), worse, torch.device("cpu"), labeled_safe_only=False)),
            4.0,
        )

        loss = _pairwise_ranking_loss(
            FakeModel(),
            better,
            worse,
            torch.device("cpu"),
            roi_delta=1.0,
            loss_options={
                "pairwise_ranking_loss_multiplier": 0.0,
                "pairwise_candidate_ranking_loss_multiplier": 1.0,
                "pairwise_roi_margin": 0.5,
            },
        )

        self.assertGreater(float(loss), 2.49)

    def test_context_pair_stats_reports_same_context_training_capacity(self):
        samples = [
            SimpleNamespace(
                batch_impact_context_hash="ctx-a",
                y_accepted_batch_roi=torch.tensor(1.2),
                y_batch_roi_positive=torch.tensor(1.0),
            ),
            SimpleNamespace(
                batch_impact_context_hash="ctx-a",
                y_accepted_batch_roi=torch.tensor(0.1),
                y_batch_roi_positive=torch.tensor(0.0),
            ),
            SimpleNamespace(
                batch_impact_context_hash="ctx-a",
                y_accepted_batch_roi=torch.tensor(0.1),
                y_batch_roi_positive=torch.tensor(0.0),
            ),
            SimpleNamespace(
                batch_impact_context_hash="ctx-b",
                y_accepted_batch_roi=torch.tensor(2.0),
                y_batch_roi_positive=torch.tensor(1.0),
            ),
        ]

        stats = _context_pair_stats(samples)

        self.assertEqual(stats["sample_count"], 4)
        self.assertEqual(stats["context_count"], 2)
        self.assertEqual(stats["multi_context_count"], 1)
        self.assertEqual(stats["same_context_pair_count"], 3)
        self.assertEqual(stats["same_context_comparable_pair_count"], 2)
        self.assertEqual(stats["positive_negative_label_pair_count"], 2)
        self.assertEqual(stats["roi_diverse_context_count"], 1)
        self.assertEqual(stats["largest_context_size"], 3)

    def test_same_context_roi_pairs_rank_higher_roi_batches(self):
        high = SimpleNamespace(
            batch_impact_context_hash="ctx-a",
            y_accepted_batch_roi=torch.tensor(1.4),
        )
        low = SimpleNamespace(
            batch_impact_context_hash="ctx-a",
            y_accepted_batch_roi=torch.tensor(0.2),
        )
        other = SimpleNamespace(
            batch_impact_context_hash="ctx-b",
            y_accepted_batch_roi=torch.tensor(3.0),
        )

        pairs = _same_context_roi_pairs([low, other, high], min_roi_delta=0.01)

        self.assertEqual(len(pairs), 1)
        self.assertIs(pairs[0][0], high)
        self.assertIs(pairs[0][1], low)
        self.assertAlmostEqual(pairs[0][2], 1.2)

    def test_threshold_search_rejects_small_sample_point_precision_without_confidence(self):
        def record(idx: int) -> dict[str, object]:
            return {
                "family": "random-wave",
                "context_hash": f"ctx-{idx}",
                "batch_score": 0.95,
                "candidate_scores": [0.95],
                "candidate_high_priority_labels": [1],
                "candidate_delay_labels": [0],
                "batch_roi_positive": 1,
                "bad_mode_switch": 0,
                "tail_improved": 0,
                "support_changed_good": 0,
                "accepted_batch_roi_label": 1.0,
            }

        gate_config = {
            "min_high_priority_precision": 0.9,
            "min_high_priority_precision_ci_low": 0.9,
            "min_safe_precision": 0.9,
            "min_safe_precision_ci_low": 0.9,
            "confidence_z": 1.96,
            "max_false_high_priority_on_delay": 0.0,
            "max_false_safe_union_rate": 0.02,
            "min_accepted_batch_count": 1,
            "min_accepted_batch_rate": 0.0,
            "min_accepted_batch_roi": 0.65,
            "min_accepted_batch_roi_ci_low": 0.65,
            "baseline_accepted_batch_roi": 0.0,
            "min_roi_margin_over_baseline": 0.20,
            "min_family_holdout_precision": 0.0,
            "min_family_holdout_accepted_roi": 0.0,
            "min_major_families": 1,
            "observed_family_count": 1,
            "stage3_min_samples": 1,
            "actual_sample_count": 2,
            "knn_ood_audit_completed": True,
        }

        selected = _threshold_search(
            [record(1), record(2)],
            gate_config=gate_config,
            fixed_batch_threshold=0.5,
            fixed_candidate_threshold=0.5,
        )["selected_metrics"]

        self.assertEqual(selected["high_priority_precision"], 1.0)
        self.assertEqual(selected["safe_precision"], 1.0)
        self.assertLess(selected["high_priority_precision_ci_low"], 0.9)
        self.assertLess(selected["safe_precision_ci_low"], 0.9)
        self.assertFalse(selected["threshold_local_gate_pass"])
        self.assertIn(
            "high_priority_precision_ci_low_below_threshold_or_not_measurable",
            selected["threshold_local_reject_reasons"],
        )
        self.assertIn(
            "safe_precision_ci_low_below_threshold_or_not_measurable",
            selected["threshold_local_reject_reasons"],
        )

    def test_threshold_search_prefers_roi_ci_over_point_utility(self):
        def record(idx: int, *, score: float, roi: float) -> dict[str, object]:
            return {
                "family": "random-wave",
                "context_hash": f"ctx-{idx}",
                "batch_score": score,
                "candidate_scores": [0.9],
                "candidate_high_priority_labels": [1],
                "candidate_delay_labels": [0],
                "batch_roi_positive": 1,
                "bad_mode_switch": 0,
                "tail_improved": 0,
                "support_changed_good": 0,
                "accepted_batch_roi_label": roi,
            }

        stable_records = [record(idx, score=0.9, roi=1.0) for idx in range(30)]
        high_variance_records = stable_records + [record(99, score=0.5, roi=50.0)]
        gate_config = {
            "min_high_priority_precision": 0.0,
            "min_high_priority_precision_ci_low": None,
            "min_safe_precision": 0.0,
            "min_safe_precision_ci_low": None,
            "confidence_z": 1.96,
            "max_false_high_priority_on_delay": 0.0,
            "max_false_safe_union_rate": 0.02,
            "min_accepted_batch_count": 1,
            "min_accepted_batch_rate": 0.0,
            "min_accepted_batch_roi": 0.0,
            "min_accepted_batch_roi_ci_low": None,
            "baseline_accepted_batch_roi": 0.0,
            "baseline_selection_roi": 0.0,
            "baseline_roi_ci_high": 0.0,
            "baseline_roi_ci_high_source": "test",
            "random_baseline_accepted_batch_roi": 0.0,
            "best_rc_baseline_accepted_batch_roi": 0.0,
            "old_gat_baseline_accepted_batch_roi": 0.0,
            "min_roi_margin_over_baseline": 0.0,
            "min_family_holdout_precision": 0.0,
            "min_family_holdout_accepted_roi": 0.0,
            "min_major_families": 1,
            "observed_family_count": 1,
            "stage3_min_samples": 1,
            "actual_sample_count": len(high_variance_records),
            "knn_ood_audit_completed": True,
        }

        selected = _threshold_search(
            high_variance_records,
            gate_config=gate_config,
        )["selected_metrics"]

        self.assertTrue(selected["threshold_local_gate_pass"])
        self.assertEqual(selected["accepted_batch_count"], len(stable_records))
        self.assertAlmostEqual(selected["accepted_batch_roi"], 1.0)
        self.assertGreater(selected["accepted_batch_roi_ci_low"], 0.99)
        self.assertGreater(selected["batch_threshold"], 0.5)

    def test_threshold_search_candidate_delay_gate_blocks_high_delay_risk_candidate(self):
        records = [
            {
                "family": "random-wave",
                "context_hash": "ctx-dual-gate",
                "batch_score": 0.95,
                "candidate_scores": [0.95, 0.90],
                "candidate_delay_scores": [0.95, 0.10],
                "candidate_high_priority_labels": [0, 1],
                "candidate_delay_labels": [1, 0],
                "batch_roi_positive": 1,
                "bad_mode_switch": 0,
                "tail_improved": 0,
                "support_changed_good": 0,
                "accepted_batch_roi_label": 1.0,
            }
        ]
        gate_config = {
            "min_high_priority_precision": 0.0,
            "min_high_priority_precision_ci_low": None,
            "min_safe_precision": 0.0,
            "min_safe_precision_ci_low": None,
            "confidence_z": 1.96,
            "max_false_high_priority_on_delay": 0.0,
            "max_false_safe_union_rate": 0.02,
            "min_accepted_batch_count": 1,
            "min_accepted_batch_rate": 0.0,
            "min_accepted_batch_roi": 0.65,
            "min_accepted_batch_roi_ci_low": None,
            "baseline_accepted_batch_roi": 0.0,
            "baseline_selection_roi": 0.0,
            "baseline_roi_ci_high": 0.0,
            "baseline_roi_ci_high_source": "test",
            "random_baseline_accepted_batch_roi": 0.0,
            "best_rc_baseline_accepted_batch_roi": 0.0,
            "old_gat_baseline_accepted_batch_roi": 0.0,
            "min_roi_margin_over_baseline": 0.0,
            "min_family_holdout_precision": 0.0,
            "min_family_holdout_accepted_roi": 0.0,
            "min_major_families": 1,
            "observed_family_count": 1,
            "stage3_min_samples": 1,
            "actual_sample_count": 1,
            "knn_ood_audit_completed": True,
            "candidate_delay_gate_enabled": True,
            "candidate_delay_risk_threshold": 0.5,
        }

        selected = _threshold_search(
            records,
            gate_config=gate_config,
            fixed_batch_threshold=0.5,
            fixed_candidate_threshold=0.5,
        )["selected_metrics"]

        self.assertEqual(selected["accepted_batch_count"], 1)
        self.assertEqual(selected["high_priority_prediction_count"], 1)
        self.assertEqual(selected["high_priority_true_positive_count"], 1)
        self.assertEqual(selected["candidate_delay_gate_blocked_count"], 1)
        self.assertEqual(selected["false_high_priority_on_delay_count"], 0)
        self.assertTrue(selected["candidate_delay_gate_enabled"])
        self.assertEqual(selected["candidate_delay_risk_threshold"], 0.5)

    def test_threshold_search_rejects_any_accepted_bad_mode_by_default(self):
        def record(idx: int, *, score: float) -> dict[str, object]:
            return {
                "family": "sector-wave",
                "context_hash": f"ctx-bad-{idx}",
                "batch_score": score,
                "candidate_scores": [0.95],
                "candidate_high_priority_labels": [1],
                "candidate_delay_labels": [0],
                "batch_roi_positive": 1,
                "bad_mode_switch": 1,
                "tail_improved": 0,
                "support_changed_good": 1,
                "accepted_batch_roi_label": 1.0,
            }

        records = [record(0, score=0.95)]
        records.extend(record(idx, score=0.10) for idx in range(1, 100))
        gate_config = {
            "min_high_priority_precision": 0.9,
            "min_safe_precision": 0.9,
            "max_false_high_priority_on_delay": 0.0,
            "max_false_safe_union_rate": 0.02,
            "max_accepted_bad_mode_count": 0,
            "min_accepted_batch_count": 1,
            "min_accepted_batch_rate": 0.0,
            "min_accepted_batch_roi": 0.65,
            "min_accepted_batch_roi_ci_low": None,
            "baseline_accepted_batch_roi": 0.0,
            "baseline_selection_roi": 0.0,
            "baseline_roi_ci_high": 0.0,
            "baseline_roi_ci_high_source": "test",
            "random_baseline_accepted_batch_roi": 0.0,
            "best_rc_baseline_accepted_batch_roi": 0.0,
            "old_gat_baseline_accepted_batch_roi": 0.0,
            "min_roi_margin_over_baseline": 0.0,
            "min_family_holdout_precision": 0.0,
            "min_family_holdout_accepted_roi": 0.0,
            "min_major_families": 1,
            "observed_family_count": 1,
            "stage3_min_samples": 1,
            "actual_sample_count": len(records),
            "knn_ood_audit_completed": True,
        }

        selected = _threshold_search(
            records,
            gate_config=gate_config,
            fixed_batch_threshold=0.5,
            fixed_candidate_threshold=0.5,
        )["selected_metrics"]

        self.assertEqual(selected["accepted_batch_count"], 1)
        self.assertEqual(selected["accepted_bad_mode_count"], 1)
        self.assertLessEqual(selected["false_safe_rate_union"], 0.02)
        self.assertFalse(selected["threshold_local_gate_pass"])
        self.assertIn(
            "accepted_bad_mode_count_above_limit",
            selected["threshold_local_reject_reasons"],
        )
        self.assertIn("accepted_bad_mode", selected["hard_reject_reason_categories"])

    def test_threshold_search_delays_low_roi_context_without_high_roi_opportunity(self):
        def record(family: str, score: float, roi: float, *, candidate_score: float = 0.9) -> dict[str, object]:
            return {
                "family": family,
                "context_hash": f"{family}-{score}-{roi}",
                "batch_score": score,
                "candidate_scores": [candidate_score],
                "candidate_high_priority_labels": [1],
                "candidate_delay_labels": [0],
                "batch_roi_positive": 1,
                "bad_mode_switch": 0,
                "tail_improved": 0,
                "support_changed_good": 0,
                "accepted_batch_roi_label": roi,
            }

        records = [record("greedy-anchor", 0.95, 0.05), record("greedy-anchor", 0.94, 1.0)]
        records.extend(record("random-wave", 0.94 - idx * 0.01, 1.0) for idx in range(4))
        records.extend(record("sector-wave", 0.93 - idx * 0.01, 1.0) for idx in range(4))
        gate_config = {
            "min_high_priority_precision": 0.9,
            "min_safe_precision": 0.9,
            "max_false_high_priority_on_delay": 0.0,
            "max_false_safe_union_rate": 0.02,
            "min_accepted_batch_count": 3,
            "min_accepted_batch_rate": 0.0,
            "min_accepted_batch_roi": 0.65,
            "baseline_accepted_batch_roi": 0.0,
            "min_roi_margin_over_baseline": 0.20,
            "min_family_holdout_precision": 0.9,
            "min_family_holdout_accepted_roi": 0.65,
            "min_major_families": 3,
            "observed_family_count": 3,
            "stage3_min_samples": 1,
            "actual_sample_count": len(records),
            "knn_ood_audit_completed": True,
        }

        selected = _threshold_search(
            records,
            gate_config=gate_config,
            fixed_batch_threshold=0.5,
            fixed_candidate_threshold=0.5,
        )["selected_metrics"]

        self.assertGreaterEqual(selected["accepted_batch_roi"], 0.65)
        self.assertTrue(selected["threshold_local_gate_pass"])
        self.assertEqual(selected["family_delay_fallback_families"], [])
        self.assertEqual(selected["context_delay_fallback_contexts"], ["greedy-anchor-0.95-0.05"])
        self.assertEqual(selected["family_specific_delay_fallback_families"], [])
        self.assertNotIn(
            "family_holdout_accepted_roi_below_threshold",
            selected["threshold_local_reject_reasons"],
        )

    def test_threshold_search_distinguishes_delay_fallback_from_missed_opportunity(self):
        def record(family: str, score: float, roi: float) -> dict[str, object]:
            return {
                "family": family,
                "context_hash": f"{family}-{score}-{roi}",
                "batch_score": score,
                "candidate_scores": [0.9],
                "candidate_high_priority_labels": [1],
                "candidate_delay_labels": [0],
                "batch_roi_positive": 1 if roi > 0.0 else 0,
                "bad_mode_switch": 0,
                "tail_improved": 0,
                "support_changed_good": 0,
                "accepted_batch_roi_label": roi,
            }

        gate_config = {
            "min_high_priority_precision": 0.9,
            "min_safe_precision": 0.9,
            "max_false_high_priority_on_delay": 0.0,
            "max_false_safe_union_rate": 0.02,
            "min_accepted_batch_count": 1,
            "min_accepted_batch_rate": 0.0,
            "min_accepted_batch_roi": 0.65,
            "baseline_accepted_batch_roi": 0.0,
            "min_roi_margin_over_baseline": 0.20,
            "min_family_holdout_precision": 0.9,
            "min_family_holdout_accepted_roi": 0.65,
            "min_major_families": 3,
            "observed_family_count": 3,
            "stage3_min_samples": 1,
            "actual_sample_count": 3,
            "knn_ood_audit_completed": True,
        }

        selected = _threshold_search(
            [
                record("greedy-anchor", 0.4, 0.05),
                record("random-wave", 0.9, 1.0),
                record("sector-wave", 0.4, 1.0),
            ],
            gate_config=gate_config,
            fixed_batch_threshold=0.5,
            fixed_candidate_threshold=0.5,
        )["selected_metrics"]

        self.assertEqual(selected["family_specific_delay_fallback_families"], ["greedy-anchor"])
        self.assertEqual(selected["family_holdout_missing_accepted_opportunity_families"], ["sector-wave"])
        self.assertIn("family_holdout_accepted_batch_missing", selected["threshold_local_reject_reasons"])

        selected_with_sector = _threshold_search(
            [
                record("greedy-anchor", 0.4, 0.05),
                record("random-wave", 0.9, 1.0),
                record("sector-wave", 0.9, 1.0),
            ],
            gate_config=gate_config,
            fixed_batch_threshold=0.5,
            fixed_candidate_threshold=0.5,
        )["selected_metrics"]

        self.assertEqual(selected_with_sector["family_specific_delay_fallback_families"], ["greedy-anchor"])
        self.assertEqual(selected_with_sector["family_holdout_missing_accepted_opportunity_families"], [])
        self.assertTrue(selected_with_sector["threshold_local_gate_pass"])

    def test_threshold_search_rejects_family_high_roi_capture_shortfall(self):
        def record(family: str, score: float, roi: float) -> dict[str, object]:
            return {
                "family": family,
                "context_hash": f"{family}-{score}-{roi}",
                "batch_score": score,
                "candidate_scores": [0.9],
                "candidate_high_priority_labels": [1],
                "candidate_delay_labels": [0],
                "batch_roi_positive": 1,
                "bad_mode_switch": 0,
                "tail_improved": 0,
                "support_changed_good": 0,
                "accepted_batch_roi_label": roi,
            }

        records = [record("random-wave", 0.95, 1.0)]
        records.extend(record("random-wave", 0.10 + 0.01 * idx, 1.0) for idx in range(4))
        records.extend(record("sector-wave", 0.90 - 0.01 * idx, 1.0) for idx in range(5))
        gate_config = {
            "min_high_priority_precision": 0.0,
            "min_high_priority_precision_ci_low": None,
            "min_safe_precision": 0.0,
            "min_safe_precision_ci_low": None,
            "confidence_z": 1.96,
            "max_false_high_priority_on_delay": 0.0,
            "max_false_safe_union_rate": 0.02,
            "min_accepted_batch_count": 1,
            "min_accepted_batch_rate": 0.0,
            "min_accepted_batch_roi": 0.65,
            "min_accepted_batch_roi_ci_low": None,
            "baseline_accepted_batch_roi": 0.0,
            "baseline_selection_roi": 0.0,
            "baseline_roi_ci_high": 0.0,
            "baseline_roi_ci_high_source": "test",
            "random_baseline_accepted_batch_roi": 0.0,
            "best_rc_baseline_accepted_batch_roi": 0.0,
            "old_gat_baseline_accepted_batch_roi": 0.0,
            "min_roi_margin_over_baseline": 0.0,
            "min_family_holdout_precision": 0.0,
            "min_family_holdout_accepted_roi": 0.65,
            "min_family_accepted_high_roi_count": 2,
            "min_family_high_roi_capture_rate": 0.5,
            "min_major_families": 2,
            "observed_family_count": 2,
            "stage3_min_samples": 1,
            "actual_sample_count": len(records),
            "knn_ood_audit_completed": True,
        }

        selected = _threshold_search(
            records,
            gate_config=gate_config,
            fixed_batch_threshold=0.5,
            fixed_candidate_threshold=0.5,
        )["selected_metrics"]

        random_metrics = selected["family_holdout_per_family"]["random-wave"]
        self.assertEqual(random_metrics["oracle_high_roi_count"], 5)
        self.assertEqual(random_metrics["accepted_high_roi_count"], 1)
        self.assertAlmostEqual(random_metrics["high_roi_capture_rate"], 0.2)
        self.assertEqual(selected["family_holdout_min_accepted_high_roi_count"], 1)
        self.assertAlmostEqual(selected["family_holdout_min_high_roi_capture_rate"], 0.2)
        self.assertFalse(selected["threshold_local_gate_pass"])
        self.assertIn(
            "family_accepted_high_roi_count_below_threshold",
            selected["threshold_local_reject_reasons"],
        )
        self.assertIn(
            "family_high_roi_capture_rate_below_threshold",
            selected["threshold_local_reject_reasons"],
        )

    def test_threshold_search_can_evaluate_family_local_batch_thresholds(self):
        def record(
            family: str,
            score: float,
            roi: float,
            *,
            label: int = 1,
            candidate_score: float = 0.9,
        ) -> dict[str, object]:
            return {
                "family": family,
                "context_hash": f"{family}-{score}-{roi}-{label}",
                "batch_score": score,
                "candidate_scores": [candidate_score],
                "candidate_high_priority_labels": [label],
                "candidate_delay_labels": [0],
                "batch_roi_positive": label,
                "bad_mode_switch": 0 if label else 1,
                "tail_improved": 0,
                "support_changed_good": 0,
                "accepted_batch_roi_label": roi,
            }

        records = [
            record("greedy-anchor", 0.60, 0.0),
            record("greedy-anchor", 0.57, 0.0, label=0, candidate_score=0.1),
            record("random-wave", 0.95, 1.0),
            record("sector-wave", 0.95, 1.0),
        ]
        for idx in range(4):
            records.append(record("random-wave", 0.55 - 0.001 * idx, 1.0))
            records.append(record("sector-wave", 0.55 - 0.001 * idx, 1.0))
        gate_config = {
            "min_high_priority_precision": 0.95,
            "min_safe_precision": 0.95,
            "max_false_high_priority_on_delay": 0.0,
            "max_false_safe_union_rate": 0.02,
            "min_accepted_batch_count": 3,
            "min_accepted_batch_rate": 0.0,
            "min_accepted_batch_roi": 0.8,
            "baseline_accepted_batch_roi": 0.0,
            "min_roi_margin_over_baseline": 0.0,
            "min_family_holdout_precision": 0.95,
            "min_family_holdout_accepted_roi": 0.0,
            "min_major_families": 3,
            "observed_family_count": 3,
            "stage3_min_samples": 1,
            "actual_sample_count": len(records),
            "knn_ood_audit_completed": True,
        }

        selected = _threshold_search(
            records,
            gate_config=gate_config,
            fixed_batch_threshold=0.6,
            fixed_candidate_threshold=0.9,
            fixed_batch_thresholds_by_family={
                "greedy-anchor": 0.6,
                "random-wave": 0.0,
                "sector-wave": 0.0,
            },
        )["selected_metrics"]

        self.assertEqual(selected["threshold_mode"], "family_local_batch_candidate")
        self.assertTrue(selected["threshold_local_gate_pass"])
        self.assertEqual(selected["family_holdout_missing_accepted_families"], [])
        self.assertGreaterEqual(selected["accepted_batch_roi"], 0.8)
        self.assertIn("greedy-anchor", selected["batch_thresholds_by_family"])

    def test_training_writes_diagnostic_checkpoint_with_hard_gate_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            graph_pos = tmp / "tasks_020" / "sector-wave" / "apollo" / "graph_pos.json"
            graph_neg = tmp / "tasks_020" / "random-wave" / "apollo" / "graph_neg.json"
            graph_pos.parent.mkdir(parents=True, exist_ok=True)
            graph_neg.parent.mkdir(parents=True, exist_ok=True)
            graph_pos.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            graph_neg.write_text(json.dumps(_toy_payload()), encoding="utf-8")
            source_log = tmp / "events.jsonl"
            rows_jsonl = tmp / "same_run_rows.jsonl"
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
                            _journey("jp2", [2], -0.5, [[2]]),
                        ],
                    ),
                    _capture_event(
                        graph_path=graph_neg,
                        context_hash="ctx-neg",
                        cg_iter=2,
                        instance="inst-neg",
                        returned=[
                            _journey("jn1", [1, 2], -1.0, [[2, 1]]),
                            _journey("jn2", [3], -0.2, [[3]]),
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
                        objective_improvement=4.0,
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
                        region="apollo15_20km",
                        objective_improvement=0.0,
                        label_objective_improved=0,
                        active_changed_task_set_count=1,
                        new_task_set_count=0,
                        replacement_journeys=1,
                    ),
                ],
            )
            dataset_dir = tmp / "dataset"
            build_dataset(
                input_jsonl=rows_jsonl,
                output_dir=dataset_dir,
                report=tmp / "dataset_report.md",
                min_samples_for_training=1,
                min_positive_batches_for_training=1,
                min_delay_candidates_for_training=1,
            )

            args = SimpleNamespace(
                dataset_dir=dataset_dir,
                checkpoint_out=tmp / "gat_batch_impact.pt",
                metrics_out=tmp / "metrics.json",
                report=tmp / "report.md",
                device="cpu",
                epochs=1,
                lr=1.0e-3,
                weight_decay=1.0e-5,
                hidden_dim=16,
                option_hidden_dim=16,
                pair_edge_dim=16,
                candidate_hidden_dim=12,
                context_hidden_dim=8,
                batch_hidden_dim=12,
                impact_hidden_dim=10,
                num_gnn_layers=1,
                heads=4,
                dropout=0.0,
                validation_fraction=0.5,
                seed=13,
                min_samples=1,
                stage3_min_samples=200,
                min_roi_positive_batches=1,
                min_delay_candidates=1,
                min_major_families=2,
                min_validation_high_priority_precision=0.0,
                min_validation_safe_precision=0.0,
                max_false_high_priority_on_delay=1.0,
                max_false_safe_union_rate=1.0,
                min_accepted_batch_count=0,
                min_accepted_batch_rate=0.0,
                min_accepted_batch_roi=0.0,
                baseline_accepted_batch_roi=0.0,
                min_roi_margin_over_baseline=0.0,
                false_high_priority_loss_multiplier=2.0,
                bad_mode_loss_multiplier=1.0,
                regression_loss_multiplier=0.05,
                max_nonfinite_skipped_update_rate=1.0,
            )

            summary = train_batch_impact(args)

            checkpoint = torch.load(args.checkpoint_out, map_location="cpu", weights_only=False)
            self.assertTrue(summary["all_checks_pass"])
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["default_enabled"])
            self.assertFalse(summary["selector_is_pricing_oracle"])
            self.assertFalse(summary["selector_can_certificate"])
            self.assertFalse(summary["gate_can_permanently_discard_negative_columns"])
            self.assertFalse(summary["checkpoint_gate_pass"])
            self.assertFalse(summary["stage4_candidate_ready"])
            self.assertIn("stage3_effective_sample_count_below_200", summary["stage4_blockers"])
            self.assertIn("knn_ood_holdout_audit_not_run", summary["stage4_blockers"])
            self.assertEqual(
                summary["checkpoint_selection"],
                "deployment_gate_first_then_roi_ci_baseline_utility_loss",
            )
            self.assertEqual(summary["training_objective"], "precision_constrained_roi_maximization")
            self.assertIn("hard_roi_threshold", summary)
            self.assertIn("loss_options", summary)
            self.assertIn("context_pair_stats", summary)
            self.assertFalse(summary["pairwise_ranking_loss_active"])
            for key in (
                "high_priority_precision",
                "high_priority_precision_ci_low",
                "safe_precision",
                "safe_precision_ci_low",
                "accepted_batch_count",
                "accepted_batch_rate",
                "accepted_batch_roi",
                "accepted_batch_roi_ci_low",
                "accepted_batch_roi_over_baseline_ci_low",
                "accepted_batch_roi_over_random_baseline_ci_low",
                "accepted_batch_roi_over_best_rc_baseline_ci_low",
                "accepted_batch_roi_over_old_gat_baseline_ci_low",
                "baseline_roi_ci_high",
                "batch_threshold",
                "candidate_threshold",
                "false_high_priority_on_delay",
                "false_safe_rate_union",
                "expected_trajectory_utility",
                "family_holdout_min_precision",
                "family_holdout_missing_accepted_families",
                "threshold_local_gate_pass",
                "hard_reject_reason_categories",
            ):
                self.assertIn(key, summary["validation_deployment_metrics"])
            self.assertIn("rejected_checkpoint_reason_categories", summary)
            self.assertIn("attempted_update_count", summary)
            self.assertIn("nonfinite_skipped_update_rate", summary)
            self.assertEqual(summary["training_stability_reject_reasons"], [])
            self.assertEqual(checkpoint["target_label"], "same_context_batch_trajectory_roi")
            self.assertEqual(checkpoint["exactness_contract"], BATCH_IMPACT_EXACTNESS_CONTRACT)
            self.assertEqual(
                checkpoint["training_contract"]["training_objective"],
                "precision_constrained_roi_maximization",
            )
            self.assertIn("hard_roi_threshold", checkpoint["training_contract"])
            self.assertIn("context_pair_stats", checkpoint["training_contract"])
            self.assertFalse(checkpoint["training_contract"]["pairwise_ranking_loss_active"])
            self.assertFalse(checkpoint["training_contract"]["uses_random_row_split"])
            self.assertFalse(checkpoint["training_contract"]["production_ready"])
            self.assertTrue(checkpoint["training_contract"]["requires_knn_ood_shell_before_stage4"])
            self.assertTrue(args.metrics_out.exists())
            self.assertTrue(args.report.exists())


if __name__ == "__main__":
    unittest.main()
