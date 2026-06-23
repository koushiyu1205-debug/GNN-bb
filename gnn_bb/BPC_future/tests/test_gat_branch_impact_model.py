from __future__ import annotations

import unittest

try:
    import torch

    from BPC_future.learning.branch_impact_model import (
        BRANCH_IMPACT_EXACTNESS_CONTRACT,
        BRANCH_IMPACT_HEAD_NAMES,
        GATBranchImpactModel,
        branch_impact_exactness_contract,
    )
    from BPC_future.learning.graph_builder import FutureGraphBuilder
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATBranchImpactModelTests(unittest.TestCase):
    def test_forward_backward_and_contract(self):
        torch.manual_seed(23)
        data = FutureGraphBuilder().build_from_logical_graph(_toy_payload())
        model = GATBranchImpactModel(
            node_dim=data.x.size(1),
            option_dim=data.option_feat.size(1),
            branch_feature_dim=7,
            context_feature_dim=6,
            hidden_dim=16,
            option_hidden_dim=16,
            pair_edge_dim=16,
            num_gnn_layers=1,
            heads=4,
            dropout=0.0,
            branch_hidden_dim=20,
            context_hidden_dim=12,
            impact_hidden_dim=18,
        )
        branch_pair_indices = torch.tensor([[0, 1], [1, 2], [0, 2]], dtype=torch.long)
        branch_pair_features = torch.tensor(
            [
                [0.5, 1.0, 2.0, 3.0, 4.0, 0.0, 0.2],
                [0.4, 2.0, 1.0, 5.0, 3.0, 1.0, 0.1],
                [0.3, 1.0, 1.0, 2.0, 2.0, 0.0, 0.5],
            ],
            dtype=torch.float32,
        )
        context_features = torch.tensor([0.0, 1.0, 56.0, 3.0, 7.0, 5.0], dtype=torch.float32)

        output = model(data, branch_pair_indices, branch_pair_features, context_features)

        self.assertEqual(tuple(output["branch_pair_embedding"].shape), (3, 20))
        self.assertEqual(tuple(output["context_embedding"].shape), (12,))
        self.assertEqual(tuple(output["branch_decision_embedding"].shape), (3, 32))
        for head in BRANCH_IMPACT_HEAD_NAMES:
            if head.startswith("predicted_"):
                self.assertEqual(tuple(output[head].shape), (3,))
            else:
                self.assertEqual(tuple(output[f"{head}_logit"].shape), (3,))
                self.assertTrue(
                    bool(
                        torch.all(
                            (output[f"{head}_probability"] >= 0.0)
                            & (output[f"{head}_probability"] <= 1.0)
                        )
                    ),
                    msg=head,
                )
        for name, value in output.items():
            self.assertTrue(torch.all(torch.isfinite(value)), msg=name)

        loss = (
            output["branch_priority_logit"].sum()
            + output["tail_improved_logit"].sum()
            + output["predicted_child_negative_pricing_events"].sum()
            + output["predicted_child_completion_bound_retries"].sum()
        )
        loss.backward()
        grad_norm = sum(
            float(param.grad.detach().abs().sum())
            for param in model.parameters()
            if param.grad is not None
        )
        self.assertGreater(grad_norm, 0.0)
        self.assertFalse(model.exactness_contract["production_ready"])
        self.assertFalse(model.exactness_contract["branching_oracle"])
        self.assertFalse(model.exactness_contract["certificate_source"])
        self.assertEqual(branch_impact_exactness_contract(), BRANCH_IMPACT_EXACTNESS_CONTRACT)

    def test_predictions_depend_on_context(self):
        torch.manual_seed(29)
        data = FutureGraphBuilder().build_from_logical_graph(_toy_payload())
        model = GATBranchImpactModel(
            node_dim=data.x.size(1),
            option_dim=data.option_feat.size(1),
            branch_feature_dim=3,
            context_feature_dim=4,
            hidden_dim=16,
            option_hidden_dim=16,
            pair_edge_dim=16,
            num_gnn_layers=1,
            heads=4,
            dropout=0.0,
            branch_hidden_dim=20,
            context_hidden_dim=12,
            impact_hidden_dim=18,
        )
        branch_pair_indices = torch.tensor([[0, 1], [1, 2]], dtype=torch.long)
        branch_pair_features = torch.tensor(
            [[0.5, 240.0, 264.0], [0.42, 146.0, 219.0]],
            dtype=torch.float32,
        )
        context_a = torch.tensor([0.0, 56.0, 7.0, 5.0], dtype=torch.float32)
        context_b = torch.tensor([3.0, 4.0, 0.0, 1.0], dtype=torch.float32)

        output_a = model(data, branch_pair_indices, branch_pair_features, context_a)
        output_b = model(data, branch_pair_indices, branch_pair_features, context_b)

        self.assertFalse(torch.allclose(output_a["branch_priority_logit"], output_b["branch_priority_logit"]))

    def test_invalid_branch_pairs_are_rejected(self):
        data = FutureGraphBuilder().build_from_logical_graph(_toy_payload())
        model = GATBranchImpactModel(
            node_dim=data.x.size(1),
            option_dim=data.option_feat.size(1),
            branch_feature_dim=3,
            context_feature_dim=4,
            hidden_dim=16,
            option_hidden_dim=16,
            pair_edge_dim=16,
            num_gnn_layers=1,
            heads=4,
            dropout=0.0,
            branch_hidden_dim=20,
            context_hidden_dim=12,
            impact_hidden_dim=18,
        )
        with self.assertRaisesRegex(ValueError, "distinct task"):
            model(
                data,
                torch.tensor([[0, 0]], dtype=torch.long),
                torch.tensor([[0.5, 1.0, 2.0]], dtype=torch.float32),
                torch.tensor([0.0, 56.0, 7.0, 5.0], dtype=torch.float32),
            )


if __name__ == "__main__":
    unittest.main()
