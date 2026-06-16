from __future__ import annotations

import unittest

from BPC_future.solver.gat_admission_queue import (
    GATAdmissionCandidate,
    GATAdmissionQueue,
)


class GATTargetModeCertificateSafetyTests(unittest.TestCase):
    def test_delayed_current_negative_blocks_learned_certificate_preflight(self):
        queue = GATAdmissionQueue(max_delay_rounds=5)
        queue.decide(
            GATAdmissionCandidate("delayed-neg", -0.5, safe_and_in_distribution=False),
            current_round=1,
        )

        preflight = queue.certificate_preflight(
            current_true_reduced_costs={"delayed-neg": -0.25}
        )

        self.assertFalse(preflight.selector_can_certificate)
        self.assertTrue(preflight.requires_exact_pricing_full_scan)
        self.assertTrue(preflight.certificate_blocked_by_delayed_negative)
        self.assertEqual(preflight.delayed_negative_ids, ("delayed-neg",))

    def test_nonnegative_delay_queue_still_cannot_create_certificate(self):
        queue = GATAdmissionQueue(max_delay_rounds=5)
        queue.decide(
            GATAdmissionCandidate("became-nonnegative", -0.5, safe_and_in_distribution=False),
            current_round=1,
        )

        preflight = queue.certificate_preflight(
            current_true_reduced_costs={"became-nonnegative": 0.01}
        )

        self.assertFalse(preflight.selector_can_certificate)
        self.assertTrue(preflight.requires_exact_pricing_full_scan)
        self.assertFalse(preflight.certificate_blocked_by_delayed_negative)
        self.assertEqual(preflight.delayed_negative_ids, ())
        self.assertEqual(preflight.delayed_nonnegative_ids, ("became-nonnegative",))

    def test_before_certificate_all_delayed_candidates_are_due_for_reexposure(self):
        queue = GATAdmissionQueue(max_delay_rounds=100)
        queue.decide(GATAdmissionCandidate("a", -0.1), current_round=1)
        queue.decide(GATAdmissionCandidate("b", -0.2), current_round=2)

        due = queue.due_for_release(current_round=2, before_certificate=True)

        self.assertEqual(
            sorted(entry.candidate.candidate_id for entry in due),
            ["a", "b"],
        )


if __name__ == "__main__":
    unittest.main()
