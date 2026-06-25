from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

try:
    import torch

    from BPC_future.scripts.audit_journey_branch_impact import BRANCH_IMPACT_FEATURE_SCHEMA
    from BPC_future.scripts.build_gat_branch_action_sanity_dataset import build_dataset
    from BPC_future.tests.test_learning_components import _toy_payload

    HAS_LEARNING_STACK = True
except Exception:
    HAS_LEARNING_STACK = False


@unittest.skipUnless(HAS_LEARNING_STACK, "learning stack is not installed")
class GATBranchActionSanityDatasetTests(unittest.TestCase):
    def test_builds_graph_samples_with_walltime_gain_as_main_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = tmp_path / "toy.json"
            instance.write_text(json.dumps(_toy_payload(), sort_keys=True), encoding="utf-8")
            delta_dir = tmp_path / "delta"
            delta_dir.mkdir()
            rows = [
                _delta_row(
                    "target",
                    instance=instance,
                    label_type="strong_positive",
                    baseline_status="OPTIMAL",
                    alternative_status="OPTIMAL",
                    baseline_wall=260.0,
                    alternative_wall=150.0,
                    pair=[1, 2],
                    wall_improved=True,
                ),
                _delta_row(
                    "weak",
                    instance=instance,
                    label_type="strong_positive",
                    baseline_status="OPTIMAL",
                    alternative_status="OPTIMAL",
                    baseline_wall=260.0,
                    alternative_wall=230.0,
                    pair=[1, 3],
                    wall_improved=True,
                ),
                _delta_row(
                    "regression",
                    instance=instance,
                    label_type="regression",
                    baseline_status="OPTIMAL",
                    alternative_status="EXTERNAL_TIME_LIMIT",
                    baseline_wall=260.0,
                    alternative_wall=320.0,
                    pair=[2, 3],
                    regression=True,
                ),
                _delta_row(
                    "local_only",
                    instance=instance,
                    label_type="local_only_hard_negative",
                    baseline_status="EXTERNAL_TIME_LIMIT",
                    alternative_status="EXTERNAL_TIME_LIMIT",
                    baseline_wall=220.0,
                    alternative_wall=220.0,
                    pair=[1, 2],
                    right_censored=True,
                ),
            ]
            _write_jsonl(delta_dir / "branch_counterfactual_delta_rows.jsonl", rows)

            summary = build_dataset(
                [delta_dir],
                tmp_path / "dataset",
                tmp_path / "report.md",
                target_wall=200.0,
            )

            self.assertTrue(summary["diagnostic_only"])
            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertEqual(summary["sample_count"], 3)
            self.assertEqual(
                summary["branch_priority_label_counts"],
                {
                    "not_walltime_gain": 1,
                    "walltime_gain_positive": 2,
                },
            )
            self.assertEqual(
                summary["target_wall_crossing_label_counts"],
                {
                    "not_target_wall_crossing": 2,
                    "target_wall_crossing_positive": 1,
                },
            )
            self.assertEqual(summary["row_kind_counts"]["local_only_hard_negative"], 1)
            self.assertIn(
                "not_training_sample:local_only_hard_negative",
                summary["skipped_counts"],
            )
            self.assertTrue(summary["sanity_training_dataset_ready"])
            manifest = json.loads((tmp_path / "dataset" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["sample_count"], 3)
            self.assertEqual(manifest["branch_feature_schema"], list(BRANCH_IMPACT_FEATURE_SCHEMA))
            self.assertEqual(manifest["exactness_contract"]["certificate_source"], False)
            sample = torch.load(
                tmp_path / "dataset" / manifest["samples"][0]["path"],
                map_location="cpu",
                weights_only=False,
            )
            self.assertEqual(tuple(sample.branch_pair_indices.shape), (1, 2))
            self.assertEqual(tuple(sample.branch_pair_features.shape), (1, len(BRANCH_IMPACT_FEATURE_SCHEMA)))
            self.assertEqual(tuple(sample.context_features.shape), (11,))
            self.assertEqual(tuple(sample.branch_action_labels.shape), (1, 12))
            self.assertTrue((tmp_path / "dataset" / "summary.json").exists())
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("sanity_training_dataset_ready = true", report)
            self.assertIn("official_bound_effect = false", report)


def _delta_row(
    experiment: str,
    *,
    instance: Path,
    label_type: str,
    baseline_status: str,
    alternative_status: str,
    baseline_wall: float,
    alternative_wall: float,
    pair: list[int],
    wall_improved: bool = False,
    regression: bool = False,
    right_censored: bool = False,
) -> dict[str, object]:
    labels = {
        "y_counterfactual_wall_improved": 1.0 if wall_improved else 0.0,
        "y_counterfactual_regression": 1.0 if regression else 0.0,
        "y_counterfactual_timeout_regression": 1.0 if regression else 0.0,
    }
    branch_labels = {
        "y_tail_improved": 1.0 if wall_improved else 0.0,
        "y_completion_bound_tail": 0.0,
        "y_early_branch_continues": 0.0,
        "y_negative_chain_continues": 0.0,
        "y_active_touch": 0.0,
        "y_inactive_only": 0.0,
        "y_child_negative_pricing_events": 2.0,
        "y_child_exact_pricing_events": 3.0,
        "y_child_completion_bound_retries": 1.0,
        "y_child_early_branch_triggers": 0.0,
        "y_child_fathom_events": 1.0,
        "y_child_max_safe_bound_gain": 0.0,
        "y_child_max_corrected_bound_gain": 4.0,
    }
    return {
        "schema_version": "journey_branch_counterfactual_delta_v4",
        "experiment": experiment,
        "instance": str(instance),
        "node_id": 0,
        "depth": 0,
        "baseline_pair": [1, 2],
        "alternative_pair": pair,
        "baseline_status": baseline_status,
        "alternative_status": alternative_status,
        "baseline_wall_time": baseline_wall,
        "alternative_wall_time": alternative_wall,
        "alternative_forced_pair_matched": True,
        "right_censored_counterfactual": right_censored,
        "timeout_regression": regression,
        "counterfactual_label_type": label_type,
        "labels": labels,
        "alternative_branch_labels": branch_labels,
        "alternative_raw_row": {
            "branch_feature_vector": [float(idx) for idx in range(len(BRANCH_IMPACT_FEATURE_SCHEMA))],
            "branch_time": 12.0,
            "candidate_count": 10,
            "eligible_count": 8,
            "branch_rank_in_top": 1,
            "branch_rank_in_priority_top": 1,
        },
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
