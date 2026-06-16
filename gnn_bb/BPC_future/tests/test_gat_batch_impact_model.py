from __future__ import annotations

import unittest

try:
    import torch

    from BPC_future.learning.batch_impact_model import (
        BATCH_IMPACT_EXACTNESS_CONTRACT,
        BATCH_IMPACT_HEAD_NAMES,
        GATBatchImpactModel,
        JourneyCandidateEncoder,
        batch_impact_exactness_contract,
    )
    from BPC_future.learning.graph_builder import FutureGraphBuilder
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATBatchImpactModelTests(unittest.TestCase):
    def test_forward_backward_and_head_shapes(self):
        data = FutureGraphBuilder().build_from_logical_graph(_toy_payload())
        model = GATBatchImpactModel(
            node_dim=data.x.size(1),
            option_dim=data.option_feat.size(1),
            candidate_feature_dim=6,
            context_feature_dim=5,
            batch_feature_dim=3,
            hidden_dim=16,
            option_hidden_dim=16,
            pair_edge_dim=16,
            num_gnn_layers=1,
            heads=4,
            dropout=0.0,
            candidate_hidden_dim=24,
            context_hidden_dim=12,
            batch_hidden_dim=20,
            impact_hidden_dim=18,
        )
        membership = torch.tensor(
            [
                [1.0, 0.0, 1.0],
                [0.0, 1.0, 1.0],
                [1.0, 1.0, 0.0],
            ]
        )
        sequence_positions = torch.tensor(
            [
                [1.0, 0.0, 2.0],
                [0.0, 1.0, 2.0],
                [2.0, 1.0, 0.0],
            ]
        )
        candidate_features = torch.tensor(
            [
                [-20.0, 2.0, 1.0, 0.1, 0.0, 3.0],
                [-9.0, 2.0, 0.0, 0.4, 1.0, 2.0],
                [-13.0, 2.0, 1.0, 0.2, 0.0, 4.0],
            ]
        )
        context_features = torch.tensor([0.3, 0.0, 2.0, 10.0, 1.0])
        batch_features = torch.tensor([3.0, 0.7, 0.2])
        candidate_mask = torch.tensor([True, True, False])

        output = model(
            data,
            membership,
            sequence_positions,
            candidate_features,
            context_features,
            candidate_mask=candidate_mask,
            batch_features=batch_features,
        )

        self.assertEqual(tuple(output["candidate_embedding"].shape), (3, 24))
        self.assertEqual(tuple(output["batch_embedding"].shape), (20,))
        self.assertEqual(tuple(output["context_embedding"].shape), (12,))
        self.assertEqual(tuple(output["high_priority_logit"].shape), (3,))
        self.assertEqual(tuple(output["delay_risk_logit"].shape), (3,))
        self.assertEqual(tuple(output["batch_roi_positive_logit"].shape), (1,))
        self.assertEqual(tuple(output["predicted_delta_v"].shape), (1,))
        self.assertEqual(float(output["batch_candidate_count"]), 2.0)
        for name, value in output.items():
            self.assertTrue(torch.all(torch.isfinite(value)), msg=name)
        for key in (
            "high_priority_probability",
            "delay_risk_probability",
            "batch_roi_positive_probability",
            "objective_progress_probability",
            "tail_improved_probability",
            "bad_mode_switch_probability",
            "support_changed_good_probability",
        ):
            self.assertTrue(bool(torch.all((output[key] >= 0.0) & (output[key] <= 1.0))), msg=key)

        loss = (
            output["predicted_delta_v"].sum()
            + output["predicted_barrier_slack"].sum()
            + output["predicted_accepted_batch_roi"].sum()
            + output["high_priority_logit"].sum()
            + output["bad_mode_switch_logit"].sum()
        )
        loss.backward()
        grad_norm = sum(
            float(param.grad.detach().abs().sum())
            for param in model.parameters()
            if param.grad is not None
        )
        self.assertGreater(grad_norm, 0.0)

    def test_candidate_encoder_distinguishes_order_with_same_task_set(self):
        torch.manual_seed(7)
        encoder = JourneyCandidateEncoder(
            graph_hidden_dim=4,
            candidate_feature_dim=2,
            candidate_hidden_dim=8,
            dropout=0.0,
        )
        task_h = torch.tensor(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
            ]
        )
        initial_task_h = torch.tensor(
            [
                [0.5, 0.0, 0.0, 0.0],
                [0.0, 0.5, 0.0, 0.0],
                [0.0, 0.0, 0.5, 0.0],
            ]
        )
        membership = torch.tensor([[1.0, 1.0, 0.0], [1.0, 1.0, 0.0]])
        positions = torch.tensor([[1.0, 2.0, 0.0], [2.0, 1.0, 0.0]])
        candidate_features = torch.tensor([[0.1, 0.2], [0.1, 0.2]])

        output = encoder(task_h, initial_task_h, membership, positions, candidate_features)

        self.assertEqual(tuple(output["candidate_embedding"].shape), (2, 8))
        self.assertFalse(torch.allclose(output["order_pool"][0], output["order_pool"][1]))
        self.assertFalse(torch.allclose(output["first_pool"][0], output["first_pool"][1]))
        self.assertFalse(torch.allclose(output["last_pool"][0], output["last_pool"][1]))

    def test_candidate_priority_head_depends_on_context_and_batch(self):
        torch.manual_seed(11)
        data = FutureGraphBuilder().build_from_logical_graph(_toy_payload())
        model = GATBatchImpactModel(
            node_dim=data.x.size(1),
            option_dim=data.option_feat.size(1),
            candidate_feature_dim=6,
            context_feature_dim=5,
            batch_feature_dim=3,
            hidden_dim=16,
            option_hidden_dim=16,
            pair_edge_dim=16,
            num_gnn_layers=1,
            heads=4,
            dropout=0.0,
            candidate_hidden_dim=24,
            context_hidden_dim=12,
            batch_hidden_dim=20,
            impact_hidden_dim=18,
        )
        model.eval()
        membership = torch.tensor(
            [
                [1.0, 0.0, 1.0],
                [0.0, 1.0, 1.0],
                [1.0, 1.0, 0.0],
            ]
        )
        sequence_positions = torch.tensor(
            [
                [1.0, 0.0, 2.0],
                [0.0, 1.0, 2.0],
                [2.0, 1.0, 0.0],
            ]
        )
        candidate_features = torch.tensor(
            [
                [-20.0, 2.0, 1.0, 0.1, 0.0, 3.0],
                [-9.0, 2.0, 0.0, 0.4, 1.0, 2.0],
                [-13.0, 2.0, 1.0, 0.2, 0.0, 4.0],
            ]
        )
        context_features = torch.tensor([0.3, 0.0, 2.0, 10.0, 1.0])
        shifted_context_features = torch.tensor([3.0, 1.0, 0.0, -8.0, 4.0])
        batch_features = torch.tensor([3.0, 0.7, 0.2])
        shifted_batch_features = torch.tensor([0.0, 5.0, -2.0])

        with torch.no_grad():
            baseline = model(
                data,
                membership,
                sequence_positions,
                candidate_features,
                context_features,
                batch_features=batch_features,
            )
            context_shifted = model(
                data,
                membership,
                sequence_positions,
                candidate_features,
                shifted_context_features,
                batch_features=batch_features,
            )
            batch_shifted = model(
                data,
                membership,
                sequence_positions,
                candidate_features,
                context_features,
                batch_features=shifted_batch_features,
            )

        self.assertEqual(
            model.high_priority_head[0].in_features,
            model.candidate_hidden_dim + model.batch_hidden_dim + model.context_hidden_dim,
        )
        self.assertFalse(
            torch.allclose(baseline["high_priority_logit"], context_shifted["high_priority_logit"])
        )
        self.assertFalse(
            torch.allclose(baseline["high_priority_logit"], batch_shifted["high_priority_logit"])
        )

    def test_single_candidate_and_single_option_std_backward_is_finite(self):
        data = FutureGraphBuilder().build_from_logical_graph(_toy_payload())
        model = GATBatchImpactModel(
            node_dim=data.x.size(1),
            option_dim=data.option_feat.size(1),
            candidate_feature_dim=4,
            context_feature_dim=3,
            batch_feature_dim=2,
            hidden_dim=16,
            option_hidden_dim=16,
            pair_edge_dim=16,
            num_gnn_layers=1,
            heads=4,
            dropout=0.0,
            candidate_hidden_dim=12,
            context_hidden_dim=8,
            batch_hidden_dim=12,
            impact_hidden_dim=10,
        )
        membership = torch.tensor([[1.0, 0.0, 1.0]])
        sequence_positions = torch.tensor([[1.0, 0.0, 2.0]])
        candidate_features = torch.tensor([[-7.0, 2.0, 0.0, 1.0]])
        context_features = torch.tensor([0.2, 1.0, 4.0])
        batch_features = torch.tensor([1.0, 0.5])

        output = model(
            data,
            membership,
            sequence_positions,
            candidate_features,
            context_features,
            batch_features=batch_features,
        )
        loss = (
            output["batch_roi_positive_logit"].sum()
            + output["predicted_accepted_batch_roi"].sum()
            + output["high_priority_logit"].sum()
        )
        loss.backward()

        for name, parameter in model.named_parameters():
            if parameter.grad is not None:
                self.assertTrue(torch.all(torch.isfinite(parameter.grad)), msg=name)

    def test_exactness_contract_is_audit_only(self):
        contract = batch_impact_exactness_contract()

        self.assertEqual(contract, BATCH_IMPACT_EXACTNESS_CONTRACT)
        self.assertIsNot(contract, BATCH_IMPACT_EXACTNESS_CONTRACT)
        self.assertFalse(contract["production_ready"])
        self.assertFalse(contract["pricing_oracle"])
        self.assertFalse(contract["certificate_source"])
        self.assertFalse(contract["official_bound_effect"])
        self.assertFalse(contract["can_permanently_discard_true_rc_negative"])
        self.assertFalse(contract["delay_queue_replaces_exact_pricing"])
        self.assertIn("predicted_accepted_batch_roi", BATCH_IMPACT_HEAD_NAMES)
        self.assertIn("candidate_high_priority", BATCH_IMPACT_HEAD_NAMES)

    def test_rejects_invalid_sequence_positions(self):
        encoder = JourneyCandidateEncoder(
            graph_hidden_dim=4,
            candidate_feature_dim=2,
            candidate_hidden_dim=8,
            dropout=0.0,
        )
        task_h = torch.ones((2, 4))
        initial_task_h = torch.ones((2, 4))
        membership = torch.tensor([[1.0, 0.0]])
        features = torch.tensor([[0.0, 1.0]])

        with self.assertRaisesRegex(ValueError, "positive sequence positions"):
            encoder(task_h, initial_task_h, membership, torch.tensor([[0.0, 0.0]]), features)
        with self.assertRaisesRegex(ValueError, "absent tasks must have zero"):
            encoder(task_h, initial_task_h, membership, torch.tensor([[1.0, 2.0]]), features)


if __name__ == "__main__":
    unittest.main()
