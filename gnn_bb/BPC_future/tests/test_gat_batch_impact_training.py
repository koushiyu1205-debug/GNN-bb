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
        _candidate_action_priority_logit_from_output,
        _context_pair_comparator_loss,
        _context_pair_delta_loss,
        _context_pair_stats,
        _candidate_raw_logit_from_output,
        _focused_frontier_context_pair_groups,
        _focused_pair_gate_metrics,
        _focused_pair_gate_reject_reasons,
        _focused_pair_head_loss,
        _focused_training_pairs,
        _gate_config,
        _hard_roi_positive_candidate_boost_loss,
        _loss_options,
        _pairwise_ranking_loss,
        _path_token_model_config,
        _record_candidate_decision_counts,
        _same_context_roi_pairs,
        _targeted_safe_positive_samples,
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

    def test_path_token_model_config_can_be_disabled_for_diagnostic_ablation(self):
        manifest = {
            "candidate_path_token_schema": {
                "token_hash_bucket_count": 4096,
                "pair_hash_bucket_count": 2048,
                "type_ids": {"arc": 1, "sortie": 3},
            }
        }
        enabled = _path_token_model_config(
            manifest,
            SimpleNamespace(
                disable_path_token_encoder=False,
                path_token_dim=8,
                path_hidden_dim=12,
                path_feature_scale=0.5,
                path_feature_dropout=0.25,
                path_context_gate_hidden_dim=7,
            ),
        )
        disabled = _path_token_model_config(
            manifest,
            SimpleNamespace(
                disable_path_token_encoder=True,
                path_token_dim=8,
                path_hidden_dim=12,
                path_feature_scale=0.5,
                path_feature_dropout=0.25,
                path_context_gate_hidden_dim=7,
            ),
        )

        self.assertEqual(enabled["path_token_vocab_size"], 4096)
        self.assertEqual(enabled["path_pair_vocab_size"], 2048)
        self.assertEqual(enabled["path_hidden_dim"], 12)
        self.assertEqual(enabled["path_feature_scale"], 0.5)
        self.assertEqual(enabled["path_feature_dropout"], 0.25)
        self.assertEqual(enabled["path_context_gate_hidden_dim"], 7)
        self.assertEqual(disabled["path_token_vocab_size"], 0)
        self.assertEqual(disabled["path_pair_vocab_size"], 0)
        self.assertEqual(disabled["path_hidden_dim"], 12)
        self.assertEqual(disabled["path_feature_scale"], 0.5)
        self.assertEqual(disabled["path_feature_dropout"], 0.25)
        self.assertEqual(disabled["path_context_gate_hidden_dim"], 7)

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
            pairwise_false_delay_contrast_loss_multiplier=1.75,
            pairwise_delay_risk_contrast_loss_multiplier=2.25,
            context_pair_comparator_loss_multiplier=0.85,
            context_pair_delta_loss_multiplier=0.95,
            focused_pair_loss_multiplier=3.5,
            focused_pair_candidate_loss_multiplier=4.5,
            focused_pair_raw_all_candidate_loss_multiplier=5.0,
            focused_pair_admission_loss_multiplier=5.5,
            focused_pair_delay_risk_loss_multiplier=6.5,
            focused_pair_batch_loss_multiplier=7.5,
            focused_pair_batch_priority_loss_multiplier=8.0,
            focused_pair_action_priority_loss_multiplier=8.25,
            focused_pair_context_comparator_loss_multiplier=8.5,
            focused_pair_delta_loss_multiplier=8.75,
            focused_pair_boost_row_indices_file=None,
            focused_pair_boost_loss_multiplier=2.5,
            targeted_safe_positive_row_indices_file=None,
            targeted_safe_positive_loss_multiplier=1.5,
            focused_pair_gate_row_index_min=383,
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
        self.assertEqual(loss_options["pairwise_false_delay_contrast_loss_multiplier"], 1.75)
        self.assertEqual(loss_options["pairwise_delay_risk_contrast_loss_multiplier"], 2.25)
        self.assertEqual(loss_options["context_pair_comparator_loss_multiplier"], 0.85)
        self.assertEqual(loss_options["context_pair_delta_loss_multiplier"], 0.95)
        self.assertEqual(loss_options["focused_pair_loss_multiplier"], 3.5)
        self.assertEqual(loss_options["focused_pair_candidate_loss_multiplier"], 4.5)
        self.assertEqual(loss_options["focused_pair_raw_all_candidate_loss_multiplier"], 5.0)
        self.assertEqual(loss_options["focused_pair_admission_loss_multiplier"], 5.5)
        self.assertEqual(loss_options["focused_pair_delay_risk_loss_multiplier"], 6.5)
        self.assertEqual(loss_options["focused_pair_batch_loss_multiplier"], 7.5)
        self.assertEqual(loss_options["focused_pair_batch_priority_loss_multiplier"], 8.0)
        self.assertEqual(loss_options["focused_pair_action_priority_loss_multiplier"], 8.25)
        self.assertEqual(loss_options["focused_pair_context_comparator_loss_multiplier"], 8.5)
        self.assertEqual(loss_options["focused_pair_delta_loss_multiplier"], 8.75)
        self.assertEqual(loss_options["focused_pair_boost_row_indices"], [])
        self.assertEqual(loss_options["focused_pair_boost_loss_multiplier"], 2.5)
        self.assertEqual(loss_options["targeted_safe_positive_row_indices"], [])
        self.assertEqual(loss_options["targeted_safe_positive_loss_multiplier"], 1.5)
        self.assertEqual(loss_options["focused_pair_row_index_min"], 383)
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

    def test_pairwise_false_delay_contrast_separates_delay_hard_negative(self):
        class FakeSample(SimpleNamespace):
            def to(self, device):
                return self

        class FakeModel:
            def __call__(self, sample, *args, **kwargs):
                return {
                    "batch_roi_positive_logit": sample.batch_logit,
                    "high_priority_logit": sample.candidate_logits,
                    "delay_risk_logit": sample.delay_logits,
                }

        better = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            candidate_logits=torch.tensor([0.0, 0.1]),
            delay_logits=torch.tensor([0.8, 0.7]),
            y_candidate_high_priority=torch.tensor([0.0, 1.0]),
            y_candidate_delay_risk=torch.tensor([0.0, 0.0]),
        )
        worse = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            candidate_logits=torch.tensor([2.0, 0.0]),
            delay_logits=torch.tensor([-0.5, 0.0]),
            y_candidate_high_priority=torch.tensor([0.0, 0.0]),
            y_candidate_delay_risk=torch.tensor([1.0, 0.0]),
        )

        loss = _pairwise_ranking_loss(
            FakeModel(),
            better,
            worse,
            torch.device("cpu"),
            roi_delta=1.0,
            loss_options={
                "pairwise_ranking_loss_multiplier": 0.0,
                "pairwise_candidate_ranking_loss_multiplier": 0.0,
                "pairwise_false_delay_contrast_loss_multiplier": 1.0,
                "pairwise_roi_margin": 0.5,
            },
        )

        self.assertGreater(float(loss), 1.0)

    def test_pairwise_delay_risk_contrast_separates_after_candidate_head_passes(self):
        class FakeSample(SimpleNamespace):
            def to(self, device):
                return self

        class FakeModel:
            def __call__(self, sample, *args, **kwargs):
                return {
                    "batch_roi_positive_logit": sample.batch_logit,
                    "high_priority_logit": sample.candidate_logits,
                    "delay_risk_logit": sample.delay_logits,
                }

        better = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            candidate_logits=torch.tensor([3.0]),
            delay_logits=torch.tensor([1.5]),
            y_candidate_high_priority=torch.tensor([1.0]),
            y_candidate_delay_risk=torch.tensor([0.0]),
        )
        worse = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            candidate_logits=torch.tensor([0.5]),
            delay_logits=torch.tensor([-0.5]),
            y_candidate_high_priority=torch.tensor([0.0]),
            y_candidate_delay_risk=torch.tensor([1.0]),
        )

        loss = _pairwise_ranking_loss(
            FakeModel(),
            better,
            worse,
            torch.device("cpu"),
            roi_delta=1.0,
            loss_options={
                "pairwise_ranking_loss_multiplier": 0.0,
                "pairwise_candidate_ranking_loss_multiplier": 0.0,
                "pairwise_false_delay_contrast_loss_multiplier": 0.0,
                "pairwise_delay_risk_contrast_loss_multiplier": 1.0,
                "pairwise_roi_margin": 0.5,
            },
        )

        self.assertGreater(float(loss), 2.49)

    def test_context_pair_comparator_loss_requires_enabled_head(self):
        model = SimpleNamespace(context_pair_comparator_head=None)

        with self.assertRaisesRegex(ValueError, "context pair comparator loss requires"):
            _context_pair_comparator_loss(
                model,
                {},
                {},
                base_tensor=torch.tensor([0.0]),
                loss_options={"context_pair_comparator_loss_multiplier": 1.0},
            )

    def test_context_pair_comparator_loss_trains_forward_and_reverse_order(self):
        class FakeModel:
            context_pair_comparator_head = object()

            def context_pair_preference_logit(self, left_output, right_output):
                if left_output["name"] == "better" and right_output["name"] == "worse":
                    return torch.tensor([-2.0])
                return torch.tensor([2.0])

        loss = _context_pair_comparator_loss(
            FakeModel(),
            {"name": "better"},
            {"name": "worse"},
            base_tensor=torch.tensor([0.0]),
            loss_options={"context_pair_comparator_loss_multiplier": 1.0},
        )

        self.assertGreater(float(loss), 2.0)

    def test_context_pair_delta_loss_requires_enabled_head(self):
        model = SimpleNamespace(context_pair_delta_head=None)

        with self.assertRaisesRegex(ValueError, "context pair-delta loss requires"):
            _context_pair_delta_loss(
                model,
                {"context_pair_delta_logit": torch.tensor([0.0])},
                {"context_pair_delta_logit": torch.tensor([0.0])},
                base_tensor=torch.tensor([0.0]),
                loss_options={
                    "context_pair_delta_loss_multiplier": 1.0,
                    "pairwise_roi_margin": 0.5,
                },
                multiplier_name="context_pair_delta_loss_multiplier",
            )

    def test_context_pair_delta_loss_ranks_better_above_worse(self):
        model = SimpleNamespace(context_pair_delta_head=object())

        loss = _context_pair_delta_loss(
            model,
            {"context_pair_delta_logit": torch.tensor([-1.0])},
            {"context_pair_delta_logit": torch.tensor([1.0])},
            base_tensor=torch.tensor([0.0]),
            loss_options={
                "context_pair_delta_loss_multiplier": 1.0,
                "pairwise_roi_margin": 0.5,
            },
            multiplier_name="context_pair_delta_loss_multiplier",
        )

        self.assertGreater(float(loss), 2.49)

    def test_focused_pair_head_loss_can_train_context_pair_comparator_only(self):
        class FakeSample(SimpleNamespace):
            def to(self, device):
                return self

        class FakeModel:
            context_pair_comparator_head = object()

            def __call__(self, sample, *args, **kwargs):
                return {
                    "batch_roi_positive_logit": sample.batch_logit,
                    "high_priority_logit": sample.candidate_logits,
                    "delay_risk_logit": sample.delay_logits,
                }

            def context_pair_preference_logit(self, left_output, right_output):
                if left_output["batch_roi_positive_logit"].item() > right_output[
                    "batch_roi_positive_logit"
                ].item():
                    return torch.tensor([-2.0])
                return torch.tensor([2.0])

        better = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([1.0]),
            candidate_logits=torch.tensor([0.0]),
            delay_logits=torch.tensor([0.0]),
            y_candidate_high_priority=torch.tensor([1.0]),
            y_candidate_delay_risk=torch.tensor([0.0]),
        )
        worse = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            candidate_logits=torch.tensor([0.0]),
            delay_logits=torch.tensor([0.0]),
            y_candidate_high_priority=torch.tensor([0.0]),
            y_candidate_delay_risk=torch.tensor([1.0]),
        )

        loss = _focused_pair_head_loss(
            FakeModel(),
            better,
            worse,
            torch.device("cpu"),
            roi_delta=1.0,
            loss_options={
                "pairwise_roi_margin": 0.5,
                "focused_pair_context_comparator_loss_multiplier": 1.0,
            },
        )

        self.assertGreater(float(loss), 2.0)

    def test_focused_pair_head_loss_can_train_pair_delta_only(self):
        class FakeSample(SimpleNamespace):
            def to(self, device):
                return self

        class FakeModel:
            context_pair_delta_head = object()

            def __call__(self, sample, *args, **kwargs):
                return {
                    "batch_roi_positive_logit": sample.batch_logit,
                    "high_priority_logit": sample.candidate_logits,
                    "delay_risk_logit": sample.delay_logits,
                    "context_pair_delta_logit": sample.pair_delta_logit,
                }

        better = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            pair_delta_logit=torch.tensor([-1.0]),
            candidate_logits=torch.tensor([0.0]),
            delay_logits=torch.tensor([0.0]),
            y_candidate_high_priority=torch.tensor([1.0]),
            y_candidate_delay_risk=torch.tensor([0.0]),
        )
        worse = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            pair_delta_logit=torch.tensor([1.0]),
            candidate_logits=torch.tensor([0.0]),
            delay_logits=torch.tensor([1.0]),
            y_candidate_high_priority=torch.tensor([0.0]),
            y_candidate_delay_risk=torch.tensor([1.0]),
        )

        loss = _focused_pair_head_loss(
            FakeModel(),
            better,
            worse,
            torch.device("cpu"),
            roi_delta=1.0,
            loss_options={
                "pairwise_roi_margin": 0.5,
                "focused_pair_delta_loss_multiplier": 1.0,
            },
        )

        self.assertGreater(float(loss), 2.49)

    def test_record_candidate_decision_counts_caches_same_threshold(self):
        record = {
            "candidate_scores": [0.9, 0.2],
            "candidate_delay_scores": [0.1, 0.9],
            "candidate_delay_labels": [0, 1],
        }
        gate_config = {
            "candidate_admission_score_mode": "risk_adjusted_product",
            "candidate_delay_score_penalty": 1.0,
            "candidate_delay_gate_enabled": True,
            "candidate_delay_risk_threshold": 0.5,
        }

        first = _record_candidate_decision_counts(
            record,
            candidate_threshold=0.5,
            gate_config=gate_config,
        )
        second = _record_candidate_decision_counts(
            record,
            candidate_threshold=0.5,
            gate_config=gate_config,
        )

        self.assertEqual(first, second)
        self.assertIn("_candidate_prediction_cache", record)
        self.assertEqual(len(record["_candidate_prediction_cache"]), 1)

    def test_focused_pair_head_loss_can_train_raw_candidate_head_only(self):
        class FakeSample(SimpleNamespace):
            def to(self, device):
                return self

        class FakeModel:
            def __call__(self, sample, *args, **kwargs):
                return {
                    "batch_roi_positive_logit": sample.batch_logit,
                    "high_priority_logit": sample.candidate_logits,
                    "delay_risk_logit": sample.delay_logits,
                }

        better = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            candidate_logits=torch.tensor([0.1, 0.0]),
            delay_logits=torch.tensor([0.0, 0.0]),
            y_candidate_high_priority=torch.tensor([1.0, 0.0]),
            y_candidate_delay_risk=torch.tensor([0.0, 0.0]),
        )
        worse = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            candidate_logits=torch.tensor([2.0, 0.0]),
            delay_logits=torch.tensor([0.0, 0.0]),
            y_candidate_high_priority=torch.tensor([0.0, 0.0]),
            y_candidate_delay_risk=torch.tensor([1.0, 0.0]),
        )

        loss = _focused_pair_head_loss(
            FakeModel(),
            better,
            worse,
            torch.device("cpu"),
            roi_delta=1.0,
            loss_options={
                "pairwise_roi_margin": 0.5,
                "focused_pair_candidate_loss_multiplier": 1.0,
                "focused_pair_admission_loss_multiplier": 0.0,
                "focused_pair_delay_risk_loss_multiplier": 0.0,
                "focused_pair_batch_loss_multiplier": 0.0,
            },
        )

        self.assertGreater(float(loss), 2.39)

    def test_focused_pair_raw_all_candidate_loss_matches_gate_raw_max(self):
        class FakeSample(SimpleNamespace):
            def to(self, device):
                return self

        class FakeModel:
            def __call__(self, sample, *args, **kwargs):
                return {
                    "batch_roi_positive_logit": sample.batch_logit,
                    "high_priority_logit": sample.candidate_logits,
                    "delay_risk_logit": sample.delay_logits,
                }

        better = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            candidate_logits=torch.tensor([0.1, -1.0]),
            delay_logits=torch.tensor([0.0, 0.0]),
            y_candidate_high_priority=torch.tensor([1.0, 0.0]),
            y_candidate_delay_risk=torch.tensor([0.0, 0.0]),
        )
        worse = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            candidate_logits=torch.tensor([-3.0, 2.0]),
            delay_logits=torch.tensor([0.0, 0.0]),
            y_candidate_high_priority=torch.tensor([0.0, 0.0]),
            y_candidate_delay_risk=torch.tensor([0.0, 0.0]),
        )

        self.assertAlmostEqual(
            float(_candidate_raw_logit_from_output(worse, FakeModel()(worse), labeled_safe_only=False)),
            2.0,
        )
        loss = _focused_pair_head_loss(
            FakeModel(),
            better,
            worse,
            torch.device("cpu"),
            roi_delta=1.0,
            loss_options={
                "pairwise_roi_margin": 0.5,
                "focused_pair_candidate_loss_multiplier": 0.0,
                "focused_pair_raw_all_candidate_loss_multiplier": 1.0,
                "focused_pair_admission_loss_multiplier": 0.0,
                "focused_pair_delay_risk_loss_multiplier": 0.0,
                "focused_pair_batch_loss_multiplier": 0.0,
            },
        )

        self.assertGreater(float(loss), 2.39)

    def test_focused_pair_batch_priority_loss_trains_residual_head(self):
        class FakeSample(SimpleNamespace):
            def to(self, device):
                return self

        class FakeModel:
            candidate_batch_priority_head = object()

            def __call__(self, sample, *args, **kwargs):
                return {
                    "batch_roi_positive_logit": sample.batch_logit,
                    "high_priority_logit": sample.candidate_logits,
                    "delay_risk_logit": sample.delay_logits,
                    "candidate_batch_priority_logit": sample.batch_priority_logit,
                }

        better = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            batch_priority_logit=torch.tensor([0.1]),
            candidate_logits=torch.tensor([0.0]),
            delay_logits=torch.tensor([0.0]),
            y_candidate_high_priority=torch.tensor([1.0]),
            y_candidate_delay_risk=torch.tensor([0.0]),
        )
        worse = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            batch_priority_logit=torch.tensor([2.0]),
            candidate_logits=torch.tensor([0.0]),
            delay_logits=torch.tensor([0.0]),
            y_candidate_high_priority=torch.tensor([0.0]),
            y_candidate_delay_risk=torch.tensor([1.0]),
        )

        loss = _focused_pair_head_loss(
            FakeModel(),
            better,
            worse,
            torch.device("cpu"),
            roi_delta=1.0,
            loss_options={
                "pairwise_roi_margin": 0.5,
                "focused_pair_batch_priority_loss_multiplier": 1.0,
            },
        )

        self.assertGreater(float(loss), 2.39)

    def test_focused_pair_action_priority_loss_trains_candidate_residual_head(self):
        class FakeSample(SimpleNamespace):
            def to(self, device):
                return self

        class FakeModel:
            candidate_action_priority_head = object()

            def __call__(self, sample, *args, **kwargs):
                return {
                    "batch_roi_positive_logit": sample.batch_logit,
                    "high_priority_logit": sample.candidate_logits,
                    "delay_risk_logit": sample.delay_logits,
                    "candidate_action_priority_logit": sample.action_priority_logits,
                }

        better = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            action_priority_logits=torch.tensor([0.1, 0.2, 0.0]),
            candidate_logits=torch.tensor([0.0, 0.0, 0.0]),
            delay_logits=torch.tensor([0.0, 0.0, 0.0]),
            y_candidate_high_priority=torch.tensor([0.0, 1.0, 0.0]),
            y_candidate_delay_risk=torch.tensor([0.0, 0.0, 0.0]),
        )
        worse = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            action_priority_logits=torch.tensor([2.0, 0.3, 0.1]),
            candidate_logits=torch.tensor([0.0, 0.0, 0.0]),
            delay_logits=torch.tensor([0.0, 0.0, 0.0]),
            y_candidate_high_priority=torch.tensor([0.0, 0.0, 0.0]),
            y_candidate_delay_risk=torch.tensor([1.0, 0.0, 0.0]),
        )

        self.assertAlmostEqual(
            float(
                _candidate_action_priority_logit_from_output(
                    better,
                    FakeModel()(better),
                    labeled_safe_only=True,
                )
            ),
            0.2,
            places=6,
        )
        self.assertAlmostEqual(
            float(
                _candidate_action_priority_logit_from_output(
                    worse,
                    FakeModel()(worse),
                    labeled_safe_only=False,
                )
            ),
            2.0,
            places=6,
        )
        loss = _focused_pair_head_loss(
            FakeModel(),
            better,
            worse,
            torch.device("cpu"),
            roi_delta=1.0,
            loss_options={
                "pairwise_roi_margin": 0.5,
                "focused_pair_action_priority_loss_multiplier": 1.0,
            },
        )

        self.assertGreater(float(loss), 2.29)

    def test_focused_pair_head_loss_can_train_delay_risk_head_only(self):
        class FakeSample(SimpleNamespace):
            def to(self, device):
                return self

        class FakeModel:
            def __call__(self, sample, *args, **kwargs):
                return {
                    "batch_roi_positive_logit": sample.batch_logit,
                    "high_priority_logit": sample.candidate_logits,
                    "delay_risk_logit": sample.delay_logits,
                }

        better = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            candidate_logits=torch.tensor([3.0]),
            delay_logits=torch.tensor([1.5]),
            y_candidate_high_priority=torch.tensor([1.0]),
            y_candidate_delay_risk=torch.tensor([0.0]),
        )
        worse = FakeSample(
            candidate_task_membership=torch.empty(0),
            candidate_sequence_positions=torch.empty(0),
            candidate_features=torch.empty(0),
            context_features=torch.empty(0),
            batch_features=torch.empty(0),
            batch_logit=torch.tensor([0.0]),
            candidate_logits=torch.tensor([0.0]),
            delay_logits=torch.tensor([-0.5]),
            y_candidate_high_priority=torch.tensor([0.0]),
            y_candidate_delay_risk=torch.tensor([1.0]),
        )

        loss = _focused_pair_head_loss(
            FakeModel(),
            better,
            worse,
            torch.device("cpu"),
            roi_delta=1.0,
            loss_options={
                "pairwise_roi_margin": 0.5,
                "focused_pair_candidate_loss_multiplier": 0.0,
                "focused_pair_admission_loss_multiplier": 0.0,
                "focused_pair_delay_risk_loss_multiplier": 1.0,
                "focused_pair_batch_loss_multiplier": 0.0,
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

    def test_focused_training_pairs_use_fixed_positive_negative_tranche(self):
        positive = SimpleNamespace(
            batch_impact_source_row_index=torch.tensor(390),
            batch_impact_context_hash="ctx-a",
            y_candidate_high_priority=torch.tensor([1.0]),
            y_candidate_delay_risk=torch.tensor([0.0]),
            y_batch_roi_positive=torch.tensor(1.0),
            y_bad_mode_switch=torch.tensor(0.0),
            y_accepted_batch_roi=torch.tensor(1.2),
        )
        negative = SimpleNamespace(
            batch_impact_source_row_index=torch.tensor(391),
            batch_impact_context_hash="ctx-a",
            y_candidate_high_priority=torch.tensor([0.0]),
            y_candidate_delay_risk=torch.tensor([1.0]),
            y_batch_roi_positive=torch.tensor(0.0),
            y_bad_mode_switch=torch.tensor(0.0),
            y_accepted_batch_roi=torch.tensor(-2.0),
        )
        outside = SimpleNamespace(
            batch_impact_source_row_index=torch.tensor(100),
            batch_impact_context_hash="ctx-a",
            y_candidate_high_priority=torch.tensor([0.0]),
            y_candidate_delay_risk=torch.tensor([1.0]),
            y_batch_roi_positive=torch.tensor(0.0),
            y_bad_mode_switch=torch.tensor(0.0),
            y_accepted_batch_roi=torch.tensor(-3.0),
        )
        other_context = SimpleNamespace(
            batch_impact_source_row_index=torch.tensor(392),
            batch_impact_context_hash="ctx-b",
            y_candidate_high_priority=torch.tensor([0.0]),
            y_candidate_delay_risk=torch.tensor([1.0]),
            y_batch_roi_positive=torch.tensor(0.0),
            y_bad_mode_switch=torch.tensor(0.0),
            y_accepted_batch_roi=torch.tensor(-4.0),
        )

        pairs = _focused_training_pairs(
            [negative, outside, positive, other_context],
            focus_row_index_min=383,
        )

        self.assertEqual(len(pairs), 1)
        self.assertIs(pairs[0][0], positive)
        self.assertIs(pairs[0][1], negative)
        self.assertAlmostEqual(pairs[0][2], 3.2, places=6)

    def test_focused_training_pairs_can_use_explicit_row_indices(self):
        positive = SimpleNamespace(
            batch_impact_source_row_index=torch.tensor(100),
            batch_impact_context_hash="ctx-explicit",
            y_candidate_high_priority=torch.tensor([1.0]),
            y_candidate_delay_risk=torch.tensor([0.0]),
            y_batch_roi_positive=torch.tensor(1.0),
            y_bad_mode_switch=torch.tensor(0.0),
            y_accepted_batch_roi=torch.tensor(2.0),
        )
        negative = SimpleNamespace(
            batch_impact_source_row_index=torch.tensor(101),
            batch_impact_context_hash="ctx-explicit",
            y_candidate_high_priority=torch.tensor([0.0]),
            y_candidate_delay_risk=torch.tensor([1.0]),
            y_batch_roi_positive=torch.tensor(0.0),
            y_bad_mode_switch=torch.tensor(0.0),
            y_accepted_batch_roi=torch.tensor(-1.0),
        )
        extra = SimpleNamespace(
            batch_impact_source_row_index=torch.tensor(102),
            batch_impact_context_hash="ctx-explicit",
            y_candidate_high_priority=torch.tensor([0.0]),
            y_candidate_delay_risk=torch.tensor([1.0]),
            y_batch_roi_positive=torch.tensor(0.0),
            y_bad_mode_switch=torch.tensor(0.0),
            y_accepted_batch_roi=torch.tensor(-5.0),
        )

        pairs = _focused_training_pairs(
            [extra, negative, positive],
            focus_row_index_min=None,
            focus_row_indices=[101, 100],
        )

        self.assertEqual(len(pairs), 1)
        self.assertIs(pairs[0][0], positive)
        self.assertIs(pairs[0][1], negative)
        self.assertAlmostEqual(pairs[0][2], 3.0, places=6)

    def test_focused_frontier_context_pair_groups_match_full_key_suffix(self):
        positive = SimpleNamespace(
            batch_impact_source_row_index=torch.tensor(100),
            batch_impact_context_hash="9f80ae35ea87da5b",
            y_candidate_high_priority=torch.tensor([1.0]),
            y_candidate_delay_risk=torch.tensor([0.0]),
            y_batch_roi_positive=torch.tensor(1.0),
            y_bad_mode_switch=torch.tensor(0.0),
            y_accepted_batch_roi=torch.tensor(53.7),
        )
        negative = SimpleNamespace(
            batch_impact_source_row_index=torch.tensor(101),
            batch_impact_context_hash="9f80ae35ea87da5b",
            y_candidate_high_priority=torch.tensor([0.0]),
            y_candidate_delay_risk=torch.tensor([1.0]),
            y_batch_roi_positive=torch.tensor(0.0),
            y_bad_mode_switch=torch.tensor(0.0),
            y_accepted_batch_roi=torch.tensor(0.0),
        )
        other_context = SimpleNamespace(
            batch_impact_source_row_index=torch.tensor(102),
            batch_impact_context_hash="b36178f6655c5f75",
            y_candidate_high_priority=torch.tensor([0.0]),
            y_candidate_delay_risk=torch.tensor([1.0]),
            y_batch_roi_positive=torch.tensor(0.0),
            y_bad_mode_switch=torch.tensor(0.0),
            y_accepted_batch_roi=torch.tensor(-1.0),
        )

        groups = _focused_frontier_context_pair_groups(
            [negative, other_context, positive],
            context_keys=[
                "apollo15_20km_random-wave_randomtw_tasks030_03_seed71204|9f80ae35ea87da5b"
            ],
        )

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0][0], "9f80ae35ea87da5b")
        self.assertEqual(len(groups[0][1]), 1)
        self.assertIs(groups[0][1][0][0], positive)
        self.assertIs(groups[0][1][0][1], negative)

    def test_targeted_safe_positive_samples_filters_to_selected_positive_rows(self):
        positive = SimpleNamespace(
            batch_impact_source_row_index=torch.tensor(100),
            y_candidate_high_priority=torch.tensor([1.0]),
            y_candidate_delay_risk=torch.tensor([0.0]),
            y_batch_roi_positive=torch.tensor(1.0),
            y_bad_mode_switch=torch.tensor(0.0),
        )
        negative = SimpleNamespace(
            batch_impact_source_row_index=torch.tensor(101),
            y_candidate_high_priority=torch.tensor([0.0]),
            y_candidate_delay_risk=torch.tensor([1.0]),
            y_batch_roi_positive=torch.tensor(0.0),
            y_bad_mode_switch=torch.tensor(0.0),
        )
        unselected_positive = SimpleNamespace(
            batch_impact_source_row_index=torch.tensor(102),
            y_candidate_high_priority=torch.tensor([1.0]),
            y_candidate_delay_risk=torch.tensor([0.0]),
            y_batch_roi_positive=torch.tensor(1.0),
            y_bad_mode_switch=torch.tensor(0.0),
        )

        selected = _targeted_safe_positive_samples(
            [negative, unselected_positive, positive],
            row_indices=[100, 101],
        )

        self.assertEqual(selected, [positive])

    def test_loss_options_reads_explicit_focused_row_indices_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            row_indices_path = Path(tmp) / "focused_row_indices.json"
            training_indices_path = Path(tmp) / "focused_training_row_indices.json"
            boost_indices_path = Path(tmp) / "focused_boost_row_indices.json"
            frontier_contexts_path = Path(tmp) / "frontier_context_keys.json"
            targeted_indices_path = Path(tmp) / "targeted_positive_row_indices.json"
            row_indices_path.write_text(json.dumps([101, 100, 101]), encoding="utf-8")
            training_indices_path.write_text(json.dumps([100, 100]), encoding="utf-8")
            boost_indices_path.write_text(json.dumps({"row_indices": [205, 204, 205]}), encoding="utf-8")
            frontier_contexts_path.write_text(
                json.dumps(
                    {
                        "frontier_context_keys": [
                            "instance-a|9f80ae35ea87da5b",
                            {"context_hash": "b36178f6655c5f75"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            targeted_indices_path.write_text(json.dumps([302, 301, 302]), encoding="utf-8")
            args = SimpleNamespace(
                min_accepted_batch_roi=0.65,
                baseline_accepted_batch_roi=0.55,
                min_roi_margin_over_baseline=0.20,
                hard_roi_threshold=None,
                focused_pair_gate_row_index_min=None,
                focused_pair_row_indices_file=row_indices_path,
                focused_pair_training_row_indices_file=training_indices_path,
                focused_pair_context_comparator_loss_multiplier=1.25,
                focused_pair_boost_row_indices_file=boost_indices_path,
                focused_pair_boost_loss_multiplier=3.0,
                focused_pair_frontier_context_keys_file=frontier_contexts_path,
                focused_pair_frontier_context_loss_multiplier=4.0,
                targeted_safe_positive_row_indices_file=targeted_indices_path,
                targeted_safe_positive_loss_multiplier=2.0,
            )

            loss_options = _loss_options(args)

        self.assertIsNone(loss_options["focused_pair_row_index_min"])
        self.assertEqual(loss_options["focused_pair_row_indices_file"], str(row_indices_path))
        self.assertEqual(loss_options["focused_pair_gate_row_indices"], [100, 101])
        self.assertEqual(
            loss_options["focused_pair_training_row_indices_file"],
            str(training_indices_path),
        )
        self.assertEqual(loss_options["focused_pair_row_indices"], [100])
        self.assertEqual(loss_options["focused_pair_context_comparator_loss_multiplier"], 1.25)
        self.assertEqual(
            loss_options["focused_pair_boost_row_indices_file"],
            str(boost_indices_path),
        )
        self.assertEqual(loss_options["focused_pair_boost_row_indices"], [204, 205])
        self.assertEqual(loss_options["focused_pair_boost_loss_multiplier"], 3.0)
        self.assertEqual(
            loss_options["focused_pair_frontier_context_keys_file"],
            str(frontier_contexts_path),
        )
        self.assertEqual(
            loss_options["focused_pair_frontier_context_keys"],
            [
                "9f80ae35ea87da5b",
                "b36178f6655c5f75",
                "instance-a|9f80ae35ea87da5b",
            ],
        )
        self.assertEqual(loss_options["focused_pair_frontier_context_loss_multiplier"], 4.0)
        self.assertEqual(
            loss_options["targeted_safe_positive_row_indices_file"],
            str(targeted_indices_path),
        )
        self.assertEqual(loss_options["targeted_safe_positive_row_indices"], [301, 302])
        self.assertEqual(loss_options["targeted_safe_positive_loss_multiplier"], 2.0)

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

    def test_threshold_search_risk_adjusted_candidate_score_suppresses_high_delay_risk_candidate(self):
        records = [
            {
                "family": "random-wave",
                "context_hash": "ctx-risk-adjusted",
                "batch_score": 0.95,
                "candidate_scores": [0.95, 0.60],
                "candidate_delay_scores": [0.90, 0.10],
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
            "candidate_admission_score_mode": "risk_adjusted_product",
            "candidate_delay_score_penalty": 1.0,
            "candidate_delay_gate_enabled": False,
            "candidate_delay_risk_threshold": 1.0,
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
        self.assertEqual(selected["false_high_priority_on_delay_count"], 0)
        self.assertEqual(selected["candidate_delay_gate_blocked_count"], 0)
        self.assertEqual(selected["candidate_risk_adjusted_suppressed_count"], 1)
        self.assertEqual(selected["candidate_admission_score_mode"], "risk_adjusted_product")
        self.assertEqual(selected["candidate_delay_score_penalty"], 1.0)

    def test_threshold_search_rescue_window_promotes_raw_safe_candidate(self):
        records = [
            {
                "family": "random-wave",
                "context_hash": "ctx-rescue-window",
                "batch_score": 0.95,
                "candidate_scores": [0.95],
                "candidate_delay_scores": [0.60],
                "candidate_high_priority_labels": [1],
                "candidate_delay_labels": [0],
                "batch_roi_positive": 1,
                "bad_mode_switch": 0,
                "tail_improved": 1,
                "support_changed_good": 1,
                "accepted_batch_roi_label": 1.0,
            }
        ]
        gate_config = _threshold_test_gate_config()
        gate_config.update(
            {
                "candidate_admission_score_mode": "risk_adjusted_rescue_window",
                "candidate_delay_score_penalty": 2.0,
                "candidate_delay_gate_enabled": True,
                "candidate_delay_risk_threshold": 0.5,
                "candidate_rescue_raw_score_threshold": 0.9,
                "candidate_rescue_delay_risk_threshold": 0.75,
                "candidate_rescue_delay_score_penalty": 0.25,
            }
        )

        selected = _threshold_search(
            records,
            gate_config=gate_config,
            fixed_batch_threshold=0.5,
            fixed_candidate_threshold=0.5,
        )["selected_metrics"]

        self.assertEqual(selected["accepted_batch_count"], 1)
        self.assertEqual(selected["high_priority_prediction_count"], 1)
        self.assertEqual(selected["candidate_risk_adjusted_suppressed_count"], 1)
        self.assertEqual(selected["candidate_delay_gate_blocked_count"], 0)
        self.assertEqual(selected["candidate_rescue_window_eligible_count"], 1)
        self.assertEqual(selected["candidate_rescue_window_promoted_count"], 1)

    def test_threshold_search_rescue_window_does_not_promote_high_delay_candidate(self):
        records = [
            {
                "family": "random-wave",
                "context_hash": "ctx-rescue-window-high-delay",
                "batch_score": 0.95,
                "candidate_scores": [0.95],
                "candidate_delay_scores": [0.90],
                "candidate_high_priority_labels": [1],
                "candidate_delay_labels": [0],
                "batch_roi_positive": 1,
                "bad_mode_switch": 0,
                "tail_improved": 1,
                "support_changed_good": 1,
                "accepted_batch_roi_label": 1.0,
            }
        ]
        gate_config = _threshold_test_gate_config()
        gate_config.update(
            {
                "candidate_admission_score_mode": "risk_adjusted_rescue_window",
                "candidate_delay_score_penalty": 2.0,
                "candidate_delay_gate_enabled": True,
                "candidate_delay_risk_threshold": 0.5,
                "candidate_rescue_raw_score_threshold": 0.9,
                "candidate_rescue_delay_risk_threshold": 0.75,
                "candidate_rescue_delay_score_penalty": 0.25,
            }
        )

        selected = _threshold_search(
            records,
            gate_config=gate_config,
            fixed_batch_threshold=0.5,
            fixed_candidate_threshold=0.5,
        )["selected_metrics"]

        self.assertEqual(selected["accepted_batch_count"], 0)
        self.assertEqual(selected["high_priority_prediction_count"], 0)
        self.assertEqual(selected["candidate_risk_adjusted_suppressed_count"], 1)
        self.assertEqual(selected["candidate_rescue_window_eligible_count"], 0)
        self.assertEqual(selected["candidate_rescue_window_promoted_count"], 0)

    def test_threshold_search_rejects_zero_candidate_threshold_as_inactive_filter(self):
        records = [
            {
                "family": "sector-wave",
                "context_hash": "ctx-zero-candidate-threshold",
                "batch_score": 0.95,
                "candidate_scores": [0.95],
                "candidate_high_priority_labels": [1],
                "candidate_delay_labels": [0],
                "batch_roi_positive": 1,
                "bad_mode_switch": 0,
                "tail_improved": 1,
                "support_changed_good": 1,
                "accepted_batch_roi_label": 1.0,
            }
        ]
        gate_config = _threshold_test_gate_config()

        selected = _threshold_search(
            records,
            gate_config=gate_config,
            fixed_batch_threshold=0.5,
            fixed_candidate_threshold=0.0,
        )["selected_metrics"]

        self.assertEqual(selected["evaluated_candidate_count"], 1)
        self.assertEqual(selected["candidate_score_threshold_blocked_count"], 0)
        self.assertEqual(selected["high_priority_prediction_count"], 1)
        self.assertFalse(selected["threshold_local_gate_pass"])
        self.assertIn(
            "candidate_threshold_zero_disables_candidate_head_filter",
            selected["threshold_local_reject_reasons"],
        )
        self.assertIn(
            "candidate_head_filter_inactive",
            selected["threshold_local_hard_reject_reason_categories"],
        )

    def test_threshold_search_counts_candidate_score_threshold_blocks(self):
        records = [
            {
                "family": "sector-wave",
                "context_hash": "ctx-score-threshold-blocks",
                "batch_score": 0.95,
                "candidate_scores": [0.25, 0.95],
                "candidate_high_priority_labels": [1, 1],
                "candidate_delay_labels": [0, 0],
                "batch_roi_positive": 1,
                "bad_mode_switch": 0,
                "tail_improved": 1,
                "support_changed_good": 1,
                "accepted_batch_roi_label": 1.0,
            }
        ]
        gate_config = _threshold_test_gate_config()

        selected = _threshold_search(
            records,
            gate_config=gate_config,
            fixed_batch_threshold=0.5,
            fixed_candidate_threshold=0.5,
        )["selected_metrics"]

        self.assertEqual(selected["evaluated_candidate_count"], 2)
        self.assertEqual(selected["candidate_score_threshold_blocked_count"], 1)
        self.assertEqual(selected["high_priority_prediction_count"], 1)

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

    def test_focused_pair_gate_passes_same_context_safe_vs_delay_order(self):
        gate_config = _threshold_test_gate_config()
        args = SimpleNamespace(
            focused_pair_gate_row_index_min=383,
            min_focused_pair_count=1,
            min_focused_raw_pair_pass_rate=1.0,
            min_focused_admission_pair_pass_rate=1.0,
            min_focused_delay_risk_pair_pass_rate=1.0,
            min_focused_strict_pair_pass_rate=1.0,
        )
        manifest_items = [
            {
                "row_index": 383,
                "instance_path": "inst-a",
                "context_hash": "ctx-a",
                "instance_family": "sector-wave",
                "candidate_signature_ids": ["safe"],
                "accepted_batch_roi": 1.0,
            },
            {
                "row_index": 384,
                "instance_path": "inst-a",
                "context_hash": "ctx-a",
                "instance_family": "sector-wave",
                "candidate_signature_ids": ["delay"],
                "accepted_batch_roi": 0.0,
            },
        ]
        prediction_records = [
            {
                "family": "sector-wave",
                "context_hash": "ctx-a",
                "batch_score": 0.9,
                "candidate_scores": [0.9],
                "candidate_delay_scores": [0.1],
                "candidate_high_priority_labels": [1],
                "candidate_delay_labels": [0],
                "batch_roi_positive": 1,
                "bad_mode_switch": 0,
                "accepted_batch_roi_label": 1.0,
            },
            {
                "family": "sector-wave",
                "context_hash": "ctx-a",
                "batch_score": 0.8,
                "candidate_scores": [0.6],
                "candidate_delay_scores": [0.8],
                "candidate_high_priority_labels": [0],
                "candidate_delay_labels": [1],
                "batch_roi_positive": 0,
                "bad_mode_switch": 1,
                "accepted_batch_roi_label": 0.0,
            },
        ]

        metrics = _focused_pair_gate_metrics(
            manifest_items=manifest_items,
            prediction_records=prediction_records,
            gate_config=gate_config,
            args=args,
        )

        self.assertTrue(metrics["active"])
        self.assertTrue(metrics["gate"]["gate_pass"])
        self.assertEqual(metrics["summary"]["pair_count"], 1)
        self.assertEqual(metrics["summary"]["strict_pair_pass_rate"], 1.0)
        self.assertEqual(_focused_pair_gate_reject_reasons(metrics), [])

    def test_focused_pair_gate_can_use_explicit_row_indices_file(self):
        gate_config = _threshold_test_gate_config()
        manifest_items = [
            {
                "row_index": 10,
                "instance_path": "inst-a",
                "context_hash": "ctx-a",
                "instance_family": "sector-wave",
                "candidate_signature_ids": ["outside"],
                "accepted_batch_roi": -5.0,
            },
            {
                "row_index": 100,
                "instance_path": "inst-a",
                "context_hash": "ctx-a",
                "instance_family": "sector-wave",
                "candidate_signature_ids": ["safe"],
                "accepted_batch_roi": 1.0,
            },
            {
                "row_index": 101,
                "instance_path": "inst-a",
                "context_hash": "ctx-a",
                "instance_family": "sector-wave",
                "candidate_signature_ids": ["delay"],
                "accepted_batch_roi": 0.0,
            },
        ]
        prediction_records = [
            {
                "family": "sector-wave",
                "context_hash": "ctx-a",
                "batch_score": 0.2,
                "candidate_scores": [0.1],
                "candidate_delay_scores": [0.9],
                "candidate_high_priority_labels": [0],
                "candidate_delay_labels": [1],
                "batch_roi_positive": 0,
                "bad_mode_switch": 1,
                "accepted_batch_roi_label": -5.0,
            },
            {
                "family": "sector-wave",
                "context_hash": "ctx-a",
                "batch_score": 0.9,
                "candidate_scores": [0.9],
                "candidate_delay_scores": [0.1],
                "candidate_high_priority_labels": [1],
                "candidate_delay_labels": [0],
                "batch_roi_positive": 1,
                "bad_mode_switch": 0,
                "accepted_batch_roi_label": 1.0,
            },
            {
                "family": "sector-wave",
                "context_hash": "ctx-a",
                "batch_score": 0.8,
                "candidate_scores": [0.6],
                "candidate_delay_scores": [0.8],
                "candidate_high_priority_labels": [0],
                "candidate_delay_labels": [1],
                "batch_roi_positive": 0,
                "bad_mode_switch": 1,
                "accepted_batch_roi_label": 0.0,
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            row_indices_path = Path(tmp) / "focused_row_indices.json"
            row_indices_path.write_text(json.dumps([101, 100]), encoding="utf-8")
            args = SimpleNamespace(
                focused_pair_gate_row_index_min=None,
                focused_pair_row_indices_file=row_indices_path,
                min_focused_pair_count=1,
                min_focused_raw_pair_pass_rate=1.0,
                min_focused_admission_pair_pass_rate=1.0,
                min_focused_delay_risk_pair_pass_rate=1.0,
                min_focused_strict_pair_pass_rate=1.0,
            )

            metrics = _focused_pair_gate_metrics(
                manifest_items=manifest_items,
                prediction_records=prediction_records,
                gate_config=gate_config,
                args=args,
            )

        self.assertTrue(metrics["active"])
        self.assertEqual(metrics["focus_selector"], "explicit_row_indices")
        self.assertEqual(metrics["focus_row_indices_count"], 2)
        self.assertEqual(metrics["summary"]["focused_row_count"], 2)
        self.assertEqual(metrics["summary"]["pair_count"], 1)
        self.assertTrue(metrics["gate"]["gate_pass"])

    def test_focused_pair_gate_rejects_context_pair_ranking_failure(self):
        gate_config = _threshold_test_gate_config()
        args = SimpleNamespace(
            focused_pair_gate_row_index_min=383,
            min_focused_pair_count=1,
            min_focused_raw_pair_pass_rate=1.0,
            min_focused_admission_pair_pass_rate=1.0,
            min_focused_delay_risk_pair_pass_rate=1.0,
            min_focused_strict_pair_pass_rate=1.0,
        )
        manifest_items = [
            {
                "row_index": 383,
                "instance_path": "inst-a",
                "context_hash": "ctx-a",
                "instance_family": "sector-wave",
                "candidate_signature_ids": ["safe"],
                "accepted_batch_roi": 1.0,
            },
            {
                "row_index": 384,
                "instance_path": "inst-a",
                "context_hash": "ctx-a",
                "instance_family": "sector-wave",
                "candidate_signature_ids": ["delay"],
                "accepted_batch_roi": 0.0,
            },
        ]
        prediction_records = [
            {
                "family": "sector-wave",
                "context_hash": "ctx-a",
                "batch_score": 0.9,
                "candidate_scores": [0.55],
                "candidate_delay_scores": [0.8],
                "candidate_high_priority_labels": [1],
                "candidate_delay_labels": [0],
                "batch_roi_positive": 1,
                "bad_mode_switch": 0,
                "accepted_batch_roi_label": 1.0,
            },
            {
                "family": "sector-wave",
                "context_hash": "ctx-a",
                "batch_score": 0.8,
                "candidate_scores": [0.85],
                "candidate_delay_scores": [0.2],
                "candidate_high_priority_labels": [0],
                "candidate_delay_labels": [1],
                "batch_roi_positive": 0,
                "bad_mode_switch": 1,
                "accepted_batch_roi_label": 0.0,
            },
        ]

        metrics = _focused_pair_gate_metrics(
            manifest_items=manifest_items,
            prediction_records=prediction_records,
            gate_config=gate_config,
            args=args,
        )

        self.assertFalse(metrics["gate"]["gate_pass"])
        self.assertEqual(metrics["summary"]["raw_pair_pass_rate"], 0.0)
        self.assertEqual(metrics["summary"]["delay_risk_pair_pass_rate"], 0.0)
        self.assertEqual(
            metrics["gate"]["blocking_primary"],
            "candidate_head_context_ranking_failure",
        )
        self.assertIn(
            "strict_pair_pass_rate_below_threshold",
            _focused_pair_gate_reject_reasons(metrics),
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
                epoch_checkpoint_dir=tmp / "epoch_checkpoints",
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
                context_pair_hidden_dim=0,
                path_token_dim=8,
                path_hidden_dim=12,
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
            epoch_checkpoint = torch.load(
                args.epoch_checkpoint_dir / "epoch_001.pt",
                map_location="cpu",
                weights_only=False,
            )
            epoch_metrics = json.loads(
                (args.epoch_checkpoint_dir / "epoch_001_metrics.json").read_text(
                    encoding="utf-8"
                )
            )
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
            self.assertIn(
                "pairwise_delay_risk_contrast_loss_multiplier",
                summary["loss_options"],
            )
            self.assertIn("context_pair_comparator_loss_multiplier", summary["loss_options"])
            self.assertIn("context_pair_delta_loss_multiplier", summary["loss_options"])
            self.assertIn(
                "focused_pair_candidate_loss_multiplier",
                summary["loss_options"],
            )
            self.assertIn(
                "focused_pair_delay_risk_loss_multiplier",
                summary["loss_options"],
            )
            self.assertIn(
                "focused_pair_context_comparator_loss_multiplier",
                summary["loss_options"],
            )
            self.assertIn("focused_pair_delta_loss_multiplier", summary["loss_options"])
            self.assertIn("focused_pair_boost_loss_multiplier", summary["loss_options"])
            self.assertIn("focused_pair_boost_row_indices", summary["loss_options"])
            self.assertIn("targeted_safe_positive_loss_multiplier", summary["loss_options"])
            self.assertIn("targeted_safe_positive_row_indices", summary["loss_options"])
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
                "evaluated_candidate_count",
                "candidate_score_threshold_blocked_count",
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
            self.assertIn("history", summary)
            self.assertEqual(
                summary["epoch_checkpoint_paths"],
                [str(args.epoch_checkpoint_dir / "epoch_001.pt")],
            )
            self.assertIn("focused_pair_gate", summary)
            self.assertIn("focused_pair_gate_not_run", summary["focused_pair_gate_reject_reasons"])
            self.assertIn("training_run_config", summary)
            self.assertEqual(summary["training_run_config"]["seed"], 13)
            self.assertEqual(summary["training_run_config"]["validation_fraction"], 0.5)
            self.assertEqual(
                summary["training_run_config"]["model_config"]["context_pair_hidden_dim"],
                0,
            )
            self.assertEqual(
                summary["training_run_config"]["model_config"]["context_pair_delta_hidden_dim"],
                0,
            )
            self.assertIsNone(
                summary["training_run_config"]["focused_pair_gate_config"][
                    "focused_pair_gate_row_index_min"
                ]
            )
            self.assertEqual(len(summary["history"]), 1)
            self.assertEqual(summary["history"][0]["epoch"], 1)
            self.assertEqual(summary["training_stability_reject_reasons"], [])
            self.assertEqual(checkpoint["target_label"], "same_context_batch_trajectory_roi")
            self.assertEqual(checkpoint["exactness_contract"], BATCH_IMPACT_EXACTNESS_CONTRACT)
            self.assertEqual(
                epoch_checkpoint["target_label"],
                "same_context_batch_trajectory_roi",
            )
            self.assertEqual(
                epoch_checkpoint["exactness_contract"],
                BATCH_IMPACT_EXACTNESS_CONTRACT,
            )
            self.assertEqual(
                epoch_metrics["schema_version"],
                "gat_batch_impact_training_summary_v1",
            )
            self.assertFalse(epoch_metrics["production_ready"])
            self.assertEqual(epoch_metrics["epoch"], 1)
            self.assertIn("focused_pair_gate", epoch_metrics)
            self.assertIn("validation_deployment_metrics", epoch_metrics)
            self.assertEqual(checkpoint["model_config"]["path_token_vocab_size"], 4096)
            self.assertEqual(checkpoint["model_config"]["path_pair_vocab_size"], 4096)
            self.assertEqual(checkpoint["model_config"]["path_hidden_dim"], 12)
            self.assertEqual(checkpoint["model_config"]["context_pair_hidden_dim"], 0)
            self.assertEqual(checkpoint["model_config"]["context_pair_delta_hidden_dim"], 0)
            self.assertIn("candidate_path_token_schema", checkpoint)
            self.assertEqual(
                checkpoint["training_contract"]["training_objective"],
                "precision_constrained_roi_maximization",
            )
            self.assertIn("hard_roi_threshold", checkpoint["training_contract"])
            self.assertIn(
                "pairwise_delay_risk_contrast_loss_multiplier",
                checkpoint["training_contract"],
            )
            self.assertIn(
                "context_pair_comparator_loss_multiplier",
                checkpoint["training_contract"],
            )
            self.assertIn(
                "context_pair_delta_loss_multiplier",
                checkpoint["training_contract"],
            )
            self.assertEqual(checkpoint["training_contract"]["context_pair_hidden_dim"], 0)
            self.assertEqual(checkpoint["training_contract"]["context_pair_delta_hidden_dim"], 0)
            self.assertIn(
                "focused_pair_candidate_loss_multiplier",
                checkpoint["training_contract"],
            )
            self.assertIn(
                "focused_pair_delay_risk_loss_multiplier",
                checkpoint["training_contract"],
            )
            self.assertIn(
                "focused_pair_context_comparator_loss_multiplier",
                checkpoint["training_contract"],
            )
            self.assertIn(
                "focused_pair_delta_loss_multiplier",
                checkpoint["training_contract"],
            )
            self.assertIn(
                "focused_pair_boost_loss_multiplier",
                checkpoint["training_contract"],
            )
            self.assertIn(
                "targeted_safe_positive_loss_multiplier",
                checkpoint["training_contract"],
            )
            self.assertIn("context_pair_stats", checkpoint["training_contract"])
            self.assertIn("focused_pair_gate", checkpoint["training_contract"])
            self.assertIn("training_run_config", checkpoint["training_contract"])
            self.assertEqual(checkpoint["training_contract"]["training_run_config"]["seed"], 13)
            self.assertFalse(checkpoint["training_contract"]["pairwise_ranking_loss_active"])
            self.assertFalse(checkpoint["training_contract"]["uses_random_row_split"])
            self.assertFalse(checkpoint["training_contract"]["production_ready"])
            self.assertTrue(checkpoint["training_contract"]["requires_knn_ood_shell_before_stage4"])
            self.assertEqual(checkpoint["training"]["training_run_config"]["epochs"], 1)
            self.assertEqual(len(checkpoint["training"]["history"]), 1)
            self.assertTrue(args.metrics_out.exists())
            self.assertTrue(args.report.exists())


def _threshold_test_gate_config() -> dict[str, object]:
    return {
        "min_high_priority_precision": 0.0,
        "min_high_priority_precision_ci_low": None,
        "min_safe_precision": 0.0,
        "min_safe_precision_ci_low": None,
        "confidence_z": 1.96,
        "max_false_high_priority_on_delay": 0.0,
        "max_false_safe_union_rate": 0.02,
        "min_accepted_batch_count": 0,
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
    }


if __name__ == "__main__":
    unittest.main()
