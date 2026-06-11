from __future__ import annotations

import unittest
from dataclasses import replace

import numpy as np

from BPC_future.core.data import ArcOption, load_future_data
from BPC_future.master.journey_rmp import JourneyDuals
from BPC_future.pricing.journey_pricing import (
    PRICING_STATE_CERTIFIED_NO_NEGATIVE,
    JourneyPricingConfig,
    price_journeys,
)
from BPC_future.pricing.resource_pareto_completion import (
    ResourceParetoCompletionEnvelope,
    filter_pareto_vectors,
)
from BPC_future.solver.journey_driver import (
    _journey_certificate_pricing_config,
    _validate_journey_required_components,
)


class ResourceParetoCompletionTests(unittest.TestCase):
    def test_pareto_filter_removes_strictly_dominated_and_keeps_tradeoff(self):
        vectors = np.asarray(
            [
                [1.0, 5.0, 1.0, 8.0],
                [2.0, 6.0, 1.0, 9.0],
                [1.5, 4.0, 1.0, 8.0],
            ],
            dtype=float,
        )

        front, disabled = filter_pareto_vectors(vectors)

        self.assertFalse(disabled)
        self.assertEqual(front.shape[0], 2)
        self.assertFalse(any(np.isclose(row[0], 2.0) for row in front))
        self.assertTrue(any(np.isclose(row[0], 1.0) for row in front))
        self.assertTrue(any(np.isclose(row[0], 1.5) for row in front))

    def test_relaxed_dominance_returns_optimistic_bound_under_matching_query_eps(self):
        vectors = np.asarray(
            [
                [1.0, 1.0, 0.0, 10.0],
                [0.5, 1.0, 0.0, 10.004],
            ],
            dtype=float,
        )

        front, disabled = filter_pareto_vectors(
            vectors,
            resource_eps=(0.0, 0.0, 0.01),
            rc_eps=1.0e-9,
        )

        self.assertFalse(disabled)
        self.assertEqual(front.shape[0], 1)
        self.assertLessEqual(float(front[0, 0]), 0.5)
        self.assertLessEqual(float(front[0, 3]), 10.01)

    def test_overflow_front_is_disabled_without_truncation(self):
        vectors = np.asarray(
            [
                [0.0, 3.0, 0.0, 1.0],
                [0.0, 1.0, 0.0, 3.0],
            ],
            dtype=float,
        )

        front, disabled = filter_pareto_vectors(vectors, max_front_size=1)

        self.assertTrue(disabled)
        self.assertEqual(front.shape[0], 0)

    def test_lazy_envelope_only_builds_queried_fronts(self):
        data = replace(load_future_data("very_small"), tasks=(1, 2), sortie_limit=2)
        envelope = ResourceParetoCompletionEnvelope(
            data,
            JourneyDuals(cover={1: 10.0, 2: 8.0}, fleet_limit=0.0),
            max_tasks_per_sortie=1,
            sortie_limit=2,
            max_front_size=5000,
        )

        self.assertEqual(envelope.sortie_front_count, 0)
        self.assertEqual(envelope.tail_front_count, 0)

        result = envelope.partial_value(
            0,
            remaining_slots_in_sortie=1,
            future_sorties=0,
            current_time=0.0,
            current_energy=0.0,
            current_load=0.0,
        )

        self.assertFalse(result.disabled)
        self.assertFalse(result.infeasible)
        self.assertIsNotNone(result.value)
        self.assertGreater(envelope.sortie_front_count, 0)
        self.assertIn(0, envelope._tail_front_cache)
        self.assertNotIn(1, envelope._tail_front_cache)

    def test_envelope_overflow_returns_disabled_no_bound(self):
        data = replace(load_future_data("very_small"), tasks=(1, 2), sortie_limit=1)
        slow_cheap = ArcOption(
            "slow-cheap",
            "test",
            tuple(),
            tau=10.0,
            energy=1.0,
            risk=0.0,
            distance=1.0,
            cost=1.0,
        )
        fast_expensive = ArcOption(
            "fast-expensive",
            "test",
            tuple(),
            tau=1.0,
            energy=10.0,
            risk=0.0,
            distance=1.0,
            cost=10.0,
        )
        data = replace(
            data,
            arc_options={
                **data.arc_options,
                (0, 1): (slow_cheap, fast_expensive),
            },
        )
        envelope = ResourceParetoCompletionEnvelope(
            data,
            JourneyDuals(cover={1: 0.0, 2: 0.0}, fleet_limit=0.0),
            max_tasks_per_sortie=1,
            sortie_limit=1,
            max_front_size=1,
        )

        result = envelope.partial_value(
            0,
            remaining_slots_in_sortie=1,
            future_sorties=0,
            current_time=0.0,
            current_energy=0.0,
            current_load=0.0,
        )

        self.assertTrue(result.disabled)
        self.assertGreater(envelope.overflow_state_count, 0)
        self.assertFalse(envelope.is_available)
        self.assertIn(envelope.disable_reason, {"front_overflow", "candidate_overflow"})

        query_count = envelope.query_count
        second = envelope.partial_value(
            0,
            remaining_slots_in_sortie=1,
            future_sorties=0,
            current_time=0.0,
            current_energy=0.0,
            current_load=0.0,
        )

        self.assertTrue(second.disabled)
        self.assertEqual(envelope.query_count, query_count + 1)

    def test_certificate_config_quarantines_rpce_outside_explicit_modes(self):
        base = JourneyPricingConfig()
        default_updated, default_mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_after_retry_enabled": True,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=1,
            certificate_no_column_rounds=1,
            completion_bound_phase="after_retry",
        )
        self.assertEqual(default_updated.direct_journey_label_completion_bound_mode, "bucket")
        self.assertFalse(default_updated.direct_journey_label_resource_pareto_completion_enabled)
        self.assertEqual(default_mode["completion_bound_mode"], "bucket")
        self.assertFalse(default_mode["resource_pareto_completion"])

        hybrid_updated, hybrid_mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_after_retry_enabled": True,
                "journey_certificate_completion_bound_mode": "hybrid",
                "journey_resource_pareto_completion_max_front_size": 123,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=1,
            certificate_no_column_rounds=1,
            completion_bound_phase="after_retry",
        )
        self.assertEqual(hybrid_updated.direct_journey_label_completion_bound_mode, "hybrid")
        self.assertFalse(hybrid_updated.direct_journey_label_resource_pareto_completion_enabled)
        self.assertEqual(hybrid_updated.direct_journey_label_resource_pareto_completion_max_front_size, 123)
        self.assertFalse(hybrid_mode["resource_pareto_completion"])

        resource_pareto_updated, resource_pareto_mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_after_retry_enabled": True,
                "journey_certificate_completion_bound_mode": "resource_pareto",
                "journey_resource_pareto_completion_max_front_size": 321,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=1,
            certificate_no_column_rounds=1,
            completion_bound_phase="after_retry",
        )
        self.assertEqual(resource_pareto_updated.direct_journey_label_completion_bound_mode, "resource_pareto")
        self.assertTrue(resource_pareto_updated.direct_journey_label_resource_pareto_completion_enabled)
        self.assertEqual(resource_pareto_updated.direct_journey_label_resource_pareto_completion_max_front_size, 321)
        self.assertTrue(resource_pareto_mode["resource_pareto_completion"])

        explicit_updated, explicit_mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_after_retry_enabled": True,
                "journey_certificate_completion_bound_mode": "bucket",
                "journey_resource_pareto_completion_enabled": True,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=1,
            certificate_no_column_rounds=1,
            completion_bound_phase="after_retry",
        )
        self.assertEqual(explicit_updated.direct_journey_label_completion_bound_mode, "bucket")
        self.assertTrue(explicit_updated.direct_journey_label_resource_pareto_completion_enabled)
        self.assertTrue(explicit_mode["resource_pareto_completion"])

    def test_invalid_rpce_config_fails_validation(self):
        with self.assertRaisesRegex(ValueError, "completion_bound_mode"):
            _validate_journey_required_components({"journey_certificate_completion_bound_mode": "invalid"})
        with self.assertRaisesRegex(ValueError, "max_front_size"):
            _validate_journey_required_components({"journey_resource_pareto_completion_max_front_size": -1})
        with self.assertRaisesRegex(ValueError, "time_eps"):
            _validate_journey_required_components({"journey_resource_pareto_completion_time_eps": -1.0})

    def test_certificate_config_maps_available_mask_bound_only_when_explicit(self):
        base = JourneyPricingConfig(max_tasks_per_trip=4)

        disabled, disabled_mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_after_retry_enabled": True,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=1,
            certificate_no_column_rounds=1,
            completion_bound_phase="after_retry",
        )
        self.assertFalse(disabled.direct_journey_label_available_mask_completion_bound_enabled)
        self.assertFalse(disabled_mode["available_mask_completion_bound"])

        enabled, enabled_mode = _journey_certificate_pricing_config(
            {
                "journey_certificate_completion_bound_enabled": True,
                "journey_certificate_completion_bound_after_retry_enabled": True,
                "journey_available_mask_completion_bound_enabled": True,
                "journey_available_mask_completion_bound_max_subset_size": 4,
                "journey_available_mask_completion_bound_max_states": 77,
            },
            base,
            certificate_candidate=True,
            certificate_flat_rounds=1,
            certificate_no_column_rounds=1,
            completion_bound_phase="after_retry",
        )
        self.assertTrue(enabled.direct_journey_label_available_mask_completion_bound_enabled)
        self.assertEqual(enabled.direct_journey_label_available_mask_completion_bound_max_subset_size, 4)
        self.assertEqual(enabled.direct_journey_label_available_mask_completion_bound_max_states, 77)
        self.assertTrue(enabled_mode["available_mask_completion_bound"])
        self.assertEqual(enabled_mode["available_mask_completion_bound_max_subset_size"], 4)
        self.assertEqual(enabled_mode["available_mask_completion_bound_max_states"], 77)

        with self.assertRaisesRegex(ValueError, "available_mask_completion_bound_max_subset_size"):
            _validate_journey_required_components(
                {"journey_available_mask_completion_bound_max_subset_size": -1}
            )
        with self.assertRaisesRegex(ValueError, "available_mask_completion_bound_max_states"):
            _validate_journey_required_components({"journey_available_mask_completion_bound_max_states": -1})

    def test_default_worker_pricing_does_not_build_rpce(self):
        data = replace(load_future_data("very_small"), tasks=(1,), sortie_limit=1)
        result = price_journeys(
            data,
            JourneyDuals(cover={1: 100.0}, fleet_limit=0.0),
            tuple(),
            config=JourneyPricingConfig(
                direct_journey_label_pricing_enabled=True,
                direct_journey_label_completion_bound_enabled=False,
                direct_journey_label_completion_bound_mode="hybrid",
                direct_journey_label_resource_pareto_completion_enabled=True,
                direct_journey_label_available_mask_completion_bound_enabled=True,
                max_returned_journeys=1,
            ),
        )

        self.assertFalse(result.completion_bound_enabled)
        self.assertFalse(result.rpce_enabled)
        self.assertEqual(result.rpce_query_count, 0)
        self.assertFalse(result.amcb_enabled)
        self.assertEqual(result.amcb_query_count, 0)

    def test_hybrid_final_judge_can_certificate_with_safe_rpce_enabled(self):
        data = replace(load_future_data("very_small"), tasks=(1,), sortie_limit=1)
        scheduling = dict(data.instance.get("scheduling", {}))
        data = replace(
            data,
            instance={**data.instance, "scheduling": {**scheduling, "task_waiting_allowed": False}},
        )
        result = price_journeys(
            data,
            JourneyDuals(cover={1: 0.0}, fleet_limit=0.0),
            tuple(),
            config=JourneyPricingConfig(
                profile_pricing_enabled=False,
                direct_journey_label_pricing_enabled=True,
                direct_journey_label_global_certificate_enabled=True,
                direct_journey_label_completion_bound_enabled=True,
                direct_journey_label_completion_bound_mode="hybrid",
                direct_journey_label_resource_pareto_completion_enabled=True,
                max_returned_journeys=1,
            ),
        )

        self.assertTrue(result.exhausted)
        self.assertEqual(result.status, "OPTIMAL")
        self.assertEqual(result.pricing_state, PRICING_STATE_CERTIFIED_NO_NEGATIVE)
        self.assertTrue(result.completion_bound_enabled)
        self.assertTrue(result.rpce_enabled)
        self.assertEqual(result.rpce_query_disabled_count, 0)


if __name__ == "__main__":
    unittest.main()
