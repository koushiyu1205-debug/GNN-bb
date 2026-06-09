from __future__ import annotations

from types import SimpleNamespace
import unittest

from BPC_future.master.journey_rmp import JourneyDuals
from BPC_future.pricing.journey_harvesting import harvest_support_aware_negative_journeys


def _journey(signature: str, tasks: tuple[int, ...], cost: float) -> SimpleNamespace:
    return SimpleNamespace(
        signature=(signature,),
        task_set=frozenset(tasks),
        cost=float(cost),
    )


class SupportAwareJourneyHarvestingTests(unittest.TestCase):
    def test_true_rc_filter_excludes_nonnegative_near_zero_and_forbidden(self):
        journeys = [
            _journey("negative", (1,), -2.0),
            _journey("near_zero", (2,), -1.0e-7),
            _journey("positive", (3,), 1.0),
            _journey("forbidden", (4,), -5.0),
        ]

        result = harvest_support_aware_negative_journeys(
            journeys,
            true_duals=JourneyDuals(cover={}, fleet_limit=0.0),
            cuts=tuple(),
            active_masks=set(),
            pool_masks=set(),
            forbidden_signatures={("forbidden",)},
            eps=1.0e-6,
            max_columns=4,
            min_new_masks=0,
            replacement_cap=4,
            top_k_strongest=4,
            max_jaccard_selected=0.5,
            max_jaccard_active=0.1,
            max_containment=0.8,
        )

        self.assertEqual([journey.signature for journey in result.selected], [("negative",)])
        self.assertEqual(result.diagnostics["candidate_negative_count"], 1)
        self.assertEqual(result.diagnostics["selected_count"], 1)
        self.assertEqual(result.diagnostics["best_true_rc"], -2.0)
        self.assertNotIn(("forbidden",), result.true_reduced_costs_by_signature)

    def test_support_aware_priority_keeps_new_and_support_changing_masks(self):
        journeys = [
            _journey("weak_replacement", (1, 2), -100.0),
            _journey("support_change", (9, 10), -10.0),
            _journey("new_mask", (11,), -8.0),
        ]

        result = harvest_support_aware_negative_journeys(
            journeys,
            true_duals=JourneyDuals(cover={}, fleet_limit=0.0),
            cuts=tuple(),
            active_masks={frozenset((1, 2)), frozenset((3, 4))},
            pool_masks={frozenset((1, 2)), frozenset((3, 4)), frozenset((9, 10))},
            forbidden_signatures=set(),
            eps=1.0e-6,
            max_columns=2,
            min_new_masks=1,
            replacement_cap=0,
            top_k_strongest=0,
            max_jaccard_selected=0.5,
            max_jaccard_active=0.1,
            max_containment=0.8,
        )

        signatures = {journey.signature for journey in result.selected}
        self.assertEqual(signatures, {("new_mask",), ("support_change",)})
        self.assertEqual(result.diagnostics["selected_new_mask_count"], 1)
        self.assertEqual(result.diagnostics["selected_support_changing_count"], 2)
        self.assertEqual(result.diagnostics["selected_weak_replacement_count"], 0)

    def test_replacement_cap_is_soft_for_configured_batch_fill(self):
        journeys = [
            _journey("weak_a", (1, 2), -10.0),
            _journey("weak_b", (3, 4), -9.0),
            _journey("weak_c", (5, 6), -8.0),
        ]

        result = harvest_support_aware_negative_journeys(
            journeys,
            true_duals=JourneyDuals(cover={}, fleet_limit=0.0),
            cuts=tuple(),
            active_masks=set(),
            pool_masks={frozenset((1, 2)), frozenset((3, 4)), frozenset((5, 6))},
            forbidden_signatures=set(),
            eps=1.0e-6,
            max_columns=3,
            min_new_masks=0,
            replacement_cap=1,
            top_k_strongest=0,
            max_jaccard_selected=0.5,
            max_jaccard_active=0.0,
            max_containment=0.8,
        )

        self.assertEqual(result.diagnostics["selected_count"], 3)
        self.assertEqual(result.diagnostics["selected_weak_replacement_count"], 3)
        self.assertEqual(result.diagnostics["fallback_fill_count"], 2)
        self.assertEqual(result.diagnostics["fallback_fill_replacement_count"], 2)
        self.assertEqual(result.diagnostics["fallback_fill_weak_replacement_count"], 2)
        self.assertEqual(result.diagnostics["fallback_fill_new_mask_count"], 0)

    def test_active_support_is_distinct_from_pool_masks(self):
        journeys = [
            _journey("active_replacement", (1, 2), -10.0),
            _journey("inactive_pool_direction", (7, 8), -9.0),
        ]

        result = harvest_support_aware_negative_journeys(
            journeys,
            true_duals=JourneyDuals(cover={}, fleet_limit=0.0),
            cuts=tuple(),
            active_masks={frozenset((1, 2))},
            pool_masks={frozenset((1, 2)), frozenset((7, 8))},
            forbidden_signatures=set(),
            eps=1.0e-6,
            max_columns=1,
            min_new_masks=0,
            replacement_cap=0,
            top_k_strongest=0,
            max_jaccard_selected=0.5,
            max_jaccard_active=0.1,
            max_containment=0.8,
        )

        signatures = {journey.signature for journey in result.selected}
        self.assertIn(("inactive_pool_direction",), signatures)
        self.assertNotIn(("active_replacement",), signatures)
        self.assertEqual(result.diagnostics["selected_support_changing_count"], 1)
        self.assertEqual(result.diagnostics["selected_weak_replacement_count"], 0)

    def test_diversity_rejection_and_fallback_diagnostics_are_consistent(self):
        journeys = [
            _journey("base", (1, 2, 3), -10.0),
            _journey("overlap", (1, 2, 4), -9.0),
            _journey("orthogonal", (8, 9), -8.0),
        ]

        result = harvest_support_aware_negative_journeys(
            journeys,
            true_duals=JourneyDuals(cover={}, fleet_limit=0.0),
            cuts=tuple(),
            active_masks=set(),
            pool_masks=set(),
            forbidden_signatures=set(),
            eps=1.0e-6,
            max_columns=3,
            min_new_masks=0,
            replacement_cap=3,
            top_k_strongest=0,
            max_jaccard_selected=0.2,
            max_jaccard_active=0.1,
            max_containment=0.8,
        )

        self.assertEqual(result.diagnostics["candidate_negative_count"], 3)
        self.assertEqual(result.diagnostics["selected_count"], len(result.selected))
        self.assertGreaterEqual(result.diagnostics["rejected_overlap_count"], 1)
        self.assertGreaterEqual(result.diagnostics["fallback_fill_count"], 1)
        self.assertEqual(result.diagnostics["best_true_rc"], -10.0)
        self.assertEqual(result.diagnostics["worst_selected_true_rc"], -8.0)
        self.assertIsNotNone(result.diagnostics["avg_pairwise_jaccard"])


if __name__ == "__main__":
    unittest.main()
