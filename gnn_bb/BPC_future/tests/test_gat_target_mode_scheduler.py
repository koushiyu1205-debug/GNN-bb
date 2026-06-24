from __future__ import annotations

import unittest

from BPC_future.solver.gat_admission_queue import (
    GAT_DELAY_QUEUE,
    GAT_HIGH_PRIORITY,
    GAT_REJECT_NONNEGATIVE_ONLY,
    GATAdmissionCandidate,
    GATAdmissionQueue,
)
from BPC_future.core.journey import JourneyColumn
from BPC_future.master.journey_rmp import JourneyDuals
from BPC_future.solver.journey_driver import (
    _journey_gat_shadow_candidate_id,
    _journey_gat_target_mode_admission_schedule,
    _log_journey_gat_target_mode_shadow,
    _make_journey_gat_admission_runtime,
)


class _ListLogger:
    def __init__(self) -> None:
        self.records = []

    def log(self, event: str, **payload):
        self.records.append({"event": event, **payload})


class GATTargetModeSchedulerTests(unittest.TestCase):
    def test_true_rc_negative_is_high_priority_or_delayed_never_rejected(self):
        queue = GATAdmissionQueue(max_delay_rounds=2)
        decisions = queue.decide_many(
            [
                GATAdmissionCandidate("safe-neg", -0.4, safe_and_in_distribution=True),
                GATAdmissionCandidate("unsafe-neg", -0.2, safe_and_in_distribution=False),
                GATAdmissionCandidate("nonnegative", 0.0, safe_and_in_distribution=True),
            ],
            current_round=3,
        )

        self.assertEqual(
            [decision.decision for decision in decisions],
            [GAT_HIGH_PRIORITY, GAT_DELAY_QUEUE, GAT_REJECT_NONNEGATIVE_ONLY],
        )
        for decision in decisions:
            if decision.is_true_rc_negative:
                self.assertNotEqual(decision.decision, GAT_REJECT_NONNEGATIVE_ONLY)
        self.assertEqual(len(queue), 1)

    def test_delay_queue_releases_by_round_without_discarding(self):
        queue = GATAdmissionQueue(max_delay_rounds=2)
        queue.decide(
            GATAdmissionCandidate("delayed", -1.0, safe_and_in_distribution=False),
            current_round=5,
        )

        self.assertEqual(queue.due_for_release(current_round=6), [])
        due = queue.due_for_release(current_round=7)

        self.assertEqual([entry.candidate.candidate_id for entry in due], ["delayed"])
        released = queue.pop_released(due)
        self.assertEqual([candidate.candidate_id for candidate in released], ["delayed"])
        self.assertEqual(len(queue), 0)

    def test_capacity_pressure_releases_oldest_instead_of_discarding(self):
        queue = GATAdmissionQueue(max_delay_rounds=10, max_queue_size=1)
        queue.decide(GATAdmissionCandidate("old", -1.0), current_round=1)
        queue.decide(GATAdmissionCandidate("new", -1.0), current_round=2)

        self.assertEqual(len(queue), 2)
        due = queue.due_for_release(current_round=2)

        self.assertEqual([entry.candidate.candidate_id for entry in due], ["old"])
        self.assertEqual(len(queue), 2)

    def test_journey_shadow_logging_is_default_off(self):
        logger = _ListLogger()

        _log_journey_gat_target_mode_shadow(
            logger,
            [_journey("j1", task_set={1}, cost=1.0)],
            JourneyDuals(cover={1: 2.0}, fleet_limit=0.0),
            tuple(),
            {},
            cg_iter=1,
            node_id=0,
            depth=0,
            pricing_kind="exact",
            certificate_candidate=False,
        )

        self.assertEqual(logger.records, [])

    def test_journey_shadow_logging_never_certifies_or_rejects_negative(self):
        logger = _ListLogger()

        _log_journey_gat_target_mode_shadow(
            logger,
            [
                _journey("negative", task_set={1}, cost=1.0),
                _journey("nonnegative", task_set={2}, cost=3.0),
            ],
            JourneyDuals(cover={1: 2.0, 2: 1.0}, fleet_limit=0.0),
            tuple(),
            {"journey_gat_target_mode_shadow_enabled": True},
            cg_iter=4,
            node_id=7,
            depth=1,
            pricing_kind="exact",
            certificate_candidate=True,
        )

        self.assertEqual(len(logger.records), 1)
        record = logger.records[0]
        self.assertEqual(record["event"], "journey_gat_target_mode_shadow")
        self.assertEqual(record["true_negative_journeys"], 1)
        self.assertEqual(record["delay_queue_journeys"], 1)
        self.assertEqual(record["reject_nonnegative_only_journeys"], 1)
        self.assertFalse(record["selector_can_certificate"])
        self.assertFalse(record["selector_is_pricing_oracle"])
        self.assertFalse(record["official_bound_effect"])
        self.assertTrue(record["certificate_blocked_by_delayed_negative"])

    def test_admission_scheduler_is_default_off(self):
        logger = _ListLogger()
        journey = _journey("j1", task_set={1}, cost=1.0)

        scheduled = _journey_gat_target_mode_admission_schedule(
            logger,
            _make_journey_gat_admission_runtime({}),
            [journey],
            JourneyDuals(cover={1: 2.0}, fleet_limit=0.0),
            tuple(),
            {},
            cg_iter=1,
            node_id=0,
            depth=0,
            pricing_kind="heuristic",
            certificate_candidate=False,
        )

        self.assertEqual(scheduled, [journey])
        self.assertEqual(logger.records, [])

    def test_admission_scheduler_delays_then_releases_on_exact_path(self):
        logger = _ListLogger()
        config = {
            "journey_gat_admission_scheduler_enabled": True,
            "journey_gat_admission_allow_unsourced_delay": True,
            "journey_gat_admission_max_delay_rounds": 1,
            "pricing_eps": 1.0e-9,
        }
        runtime = _make_journey_gat_admission_runtime(config)
        journey = _journey("delayed", task_set={1}, cost=1.0)
        duals = JourneyDuals(cover={1: 2.0}, fleet_limit=0.0)

        first = _journey_gat_target_mode_admission_schedule(
            logger,
            runtime,
            [journey],
            duals,
            tuple(),
            config,
            cg_iter=1,
            node_id=0,
            depth=0,
            pricing_kind="heuristic",
            certificate_candidate=False,
        )
        second = _journey_gat_target_mode_admission_schedule(
            logger,
            runtime,
            [],
            duals,
            tuple(),
            config,
            cg_iter=2,
            node_id=0,
            depth=0,
            pricing_kind="exact",
            certificate_candidate=False,
        )

        self.assertEqual(first, [])
        self.assertEqual(second, [journey])
        self.assertEqual(len(runtime.queue), 0)
        self.assertEqual(logger.records[0]["delay_queue_journeys"], 1)
        self.assertEqual(logger.records[1]["released_journeys"], 1)
        self.assertTrue(logger.records[1]["exact_path_preserved"])

    def test_admission_scheduler_without_safe_source_preserves_heuristic_path(self):
        logger = _ListLogger()
        config = {
            "journey_gat_admission_scheduler_enabled": True,
            "journey_gat_admission_max_delay_rounds": 1,
            "pricing_eps": 1.0e-9,
        }
        runtime = _make_journey_gat_admission_runtime(config)
        journey = _journey("unsourced", task_set={1}, cost=1.0)

        scheduled = _journey_gat_target_mode_admission_schedule(
            logger,
            runtime,
            [journey],
            JourneyDuals(cover={1: 2.0}, fleet_limit=0.0),
            tuple(),
            config,
            cg_iter=1,
            node_id=0,
            depth=0,
            pricing_kind="heuristic",
            certificate_candidate=False,
        )

        self.assertEqual(scheduled, [journey])
        self.assertEqual(len(runtime.queue), 0)
        self.assertEqual(logger.records[0]["status"], "bypassed")
        self.assertEqual(logger.records[0]["reason"], "missing_safe_source")
        self.assertEqual(logger.records[0]["delay_queue_journeys"], 0)

    def test_admission_scheduler_safe_source_without_online_hit_preserves_heuristic_path(self):
        logger = _ListLogger()
        config = {
            "journey_gat_admission_scheduler_enabled": True,
            "journey_gat_safe_candidate_ids": ["offline-safe-but-not-this-journey"],
            "journey_gat_admission_max_delay_rounds": 1,
            "pricing_eps": 1.0e-9,
        }
        runtime = _make_journey_gat_admission_runtime(config)
        journey = _journey("online-unmatched", task_set={1}, cost=1.0)

        scheduled = _journey_gat_target_mode_admission_schedule(
            logger,
            runtime,
            [journey],
            JourneyDuals(cover={1: 2.0}, fleet_limit=0.0),
            tuple(),
            config,
            cg_iter=1,
            node_id=0,
            depth=0,
            pricing_kind="heuristic",
            certificate_candidate=False,
        )

        self.assertEqual(scheduled, [journey])
        self.assertEqual(len(runtime.queue), 0)
        self.assertEqual(logger.records[0]["status"], "bypassed")
        self.assertEqual(logger.records[0]["reason"], "no_online_safe_hit")
        self.assertEqual(logger.records[0]["safe_source_candidate_count"], 1)
        self.assertEqual(logger.records[0]["online_safe_hit_journeys"], 0)
        self.assertEqual(logger.records[0]["delay_queue_journeys"], 0)

    def test_admission_scheduler_can_opt_out_of_online_hit_guard(self):
        logger = _ListLogger()
        config = {
            "journey_gat_admission_scheduler_enabled": True,
            "journey_gat_safe_candidate_ids": ["offline-safe-but-not-this-journey"],
            "journey_gat_admission_require_online_safe_hit_for_delay": False,
            "journey_gat_admission_max_delay_rounds": 1,
            "pricing_eps": 1.0e-9,
        }
        runtime = _make_journey_gat_admission_runtime(config)
        journey = _journey("online-unmatched", task_set={1}, cost=1.0)

        scheduled = _journey_gat_target_mode_admission_schedule(
            logger,
            runtime,
            [journey],
            JourneyDuals(cover={1: 2.0}, fleet_limit=0.0),
            tuple(),
            config,
            cg_iter=1,
            node_id=0,
            depth=0,
            pricing_kind="heuristic",
            certificate_candidate=False,
        )

        self.assertEqual(scheduled, [])
        self.assertEqual(len(runtime.queue), 1)
        self.assertEqual(logger.records[0]["status"], "scheduled")
        self.assertEqual(logger.records[0]["reason"], "opt_in_admission_scheduler")
        self.assertEqual(logger.records[0]["safe_source_candidate_count"], 1)
        self.assertEqual(logger.records[0]["online_safe_hit_journeys"], 0)
        self.assertEqual(logger.records[0]["delay_queue_journeys"], 1)

    def test_admission_scheduler_releases_immediately_before_certificate(self):
        logger = _ListLogger()
        config = {
            "journey_gat_admission_scheduler_enabled": True,
            "journey_gat_admission_allow_unsourced_delay": True,
            "journey_gat_admission_max_delay_rounds": 100,
            "pricing_eps": 1.0e-9,
        }
        runtime = _make_journey_gat_admission_runtime(config)
        journey = _journey("certificate-release", task_set={1}, cost=1.0)
        duals = JourneyDuals(cover={1: 2.0}, fleet_limit=0.0)

        delayed = _journey_gat_target_mode_admission_schedule(
            logger,
            runtime,
            [journey],
            duals,
            tuple(),
            config,
            cg_iter=1,
            node_id=0,
            depth=0,
            pricing_kind="heuristic",
            certificate_candidate=False,
        )
        released = _journey_gat_target_mode_admission_schedule(
            logger,
            runtime,
            [],
            duals,
            tuple(),
            config,
            cg_iter=1,
            node_id=0,
            depth=0,
            pricing_kind="exact",
            certificate_candidate=True,
        )

        self.assertEqual(delayed, [])
        self.assertEqual(released, [journey])
        self.assertEqual(len(runtime.queue), 0)
        self.assertEqual(logger.records[-1]["reason"], "certificate_candidate_release")
        self.assertEqual(logger.records[-1]["released_journeys"], 1)

    def test_admission_scheduler_safe_candidate_is_high_priority(self):
        logger = _ListLogger()
        journey = _journey("safe", task_set={1}, cost=1.0)
        config = {
            "journey_gat_admission_scheduler_enabled": True,
            "journey_gat_safe_candidate_ids": [_journey_gat_shadow_candidate_id(journey)],
            "pricing_eps": 1.0e-9,
        }
        runtime = _make_journey_gat_admission_runtime(config)

        scheduled = _journey_gat_target_mode_admission_schedule(
            logger,
            runtime,
            [journey],
            JourneyDuals(cover={1: 2.0}, fleet_limit=0.0),
            tuple(),
            config,
            cg_iter=1,
            node_id=0,
            depth=0,
            pricing_kind="heuristic",
            certificate_candidate=False,
        )

        self.assertEqual(scheduled, [journey])
        self.assertEqual(len(runtime.queue), 0)
        self.assertEqual(logger.records[0]["high_priority_journeys"], 1)
        self.assertEqual(logger.records[0]["online_safe_hit_journeys"], 1)

    def test_support_aware_admission_prioritizes_active_and_new_true_negatives(self):
        logger = _ListLogger()
        config = {
            "journey_gat_admission_scheduler_enabled": True,
            "journey_gat_admission_support_aware_enabled": True,
            "journey_gat_admission_allow_unsourced_delay": True,
            "journey_gat_admission_max_delay_rounds": 100,
            "journey_gat_admission_support_delay_min_depth": 0,
            "pricing_eps": 1.0e-9,
        }
        runtime = _make_journey_gat_admission_runtime(config)
        active = _journey("active-replacement", task_set={1}, cost=1.0)
        new = _journey("new-task-set", task_set={2}, cost=1.0)
        inactive = _journey("inactive-replacement", task_set={3}, cost=1.0)
        duals = JourneyDuals(cover={1: 2.0, 2: 2.0, 3: 2.0}, fleet_limit=0.0)

        scheduled = _journey_gat_target_mode_admission_schedule(
            logger,
            runtime,
            [inactive, active, new],
            duals,
            tuple(),
            config,
            cg_iter=1,
            node_id=0,
            depth=0,
            pricing_kind="heuristic",
            certificate_candidate=False,
            active_task_sets={frozenset({1})},
            dominant_task_set_costs={frozenset({1}): 5.0, frozenset({3}): 5.0},
        )
        released = _journey_gat_target_mode_admission_schedule(
            logger,
            runtime,
            [],
            duals,
            tuple(),
            config,
            cg_iter=1,
            node_id=0,
            depth=0,
            pricing_kind="exact",
            certificate_candidate=True,
            active_task_sets={frozenset({1})},
            dominant_task_set_costs={frozenset({1}): 5.0, frozenset({3}): 5.0},
        )

        self.assertEqual(scheduled, [active, new])
        self.assertEqual(released, [inactive])
        self.assertEqual(len(runtime.queue), 0)
        record = logger.records[0]
        self.assertTrue(record["support_aware_admission_enabled"])
        self.assertEqual(record["support_candidate_active_support_changing_journeys"], 1)
        self.assertEqual(record["support_candidate_new_task_set_journeys"], 1)
        self.assertEqual(record["support_candidate_inactive_only_journeys"], 1)
        self.assertEqual(record["support_high_priority_journeys"], 2)
        self.assertEqual(record["support_delayed_inactive_only_journeys"], 1)
        self.assertEqual(logger.records[-1]["reason"], "certificate_candidate_release")
        self.assertEqual(logger.records[-1]["released_journeys"], 1)

    def test_support_aware_admission_can_demote_inactive_safe_hit_to_delay(self):
        logger = _ListLogger()
        inactive = _journey("inactive-safe-hit", task_set={3}, cost=1.0)
        config = {
            "journey_gat_admission_scheduler_enabled": True,
            "journey_gat_admission_support_aware_enabled": True,
            "journey_gat_safe_candidate_ids": [_journey_gat_shadow_candidate_id(inactive)],
            "journey_gat_admission_max_delay_rounds": 1,
            "journey_gat_admission_support_delay_min_depth": 0,
            "pricing_eps": 1.0e-9,
        }
        runtime = _make_journey_gat_admission_runtime(config)

        scheduled = _journey_gat_target_mode_admission_schedule(
            logger,
            runtime,
            [inactive],
            JourneyDuals(cover={3: 2.0}, fleet_limit=0.0),
            tuple(),
            config,
            cg_iter=1,
            node_id=0,
            depth=0,
            pricing_kind="heuristic",
            certificate_candidate=False,
            active_task_sets={frozenset({1})},
            dominant_task_set_costs={frozenset({3}): 5.0},
        )

        self.assertEqual(scheduled, [])
        self.assertEqual(len(runtime.queue), 1)
        self.assertEqual(logger.records[0]["online_safe_hit_journeys"], 1)
        self.assertEqual(logger.records[0]["support_demoted_safe_hit_journeys"], 1)
        self.assertEqual(logger.records[0]["support_delayed_inactive_only_journeys"], 1)

    def test_support_aware_admission_does_not_delay_root_inactive_by_default(self):
        logger = _ListLogger()
        config = {
            "journey_gat_admission_scheduler_enabled": True,
            "journey_gat_admission_support_aware_enabled": True,
            "journey_gat_admission_allow_unsourced_delay": True,
            "journey_gat_admission_max_delay_rounds": 100,
            "pricing_eps": 1.0e-9,
        }
        runtime = _make_journey_gat_admission_runtime(config)
        inactive = _journey("root-inactive", task_set={3}, cost=1.0)

        scheduled = _journey_gat_target_mode_admission_schedule(
            logger,
            runtime,
            [inactive],
            JourneyDuals(cover={3: 2.0}, fleet_limit=0.0),
            tuple(),
            config,
            cg_iter=1,
            node_id=0,
            depth=0,
            pricing_kind="heuristic",
            certificate_candidate=False,
            active_task_sets={frozenset({1})},
            dominant_task_set_costs={frozenset({3}): 5.0},
        )

        self.assertEqual(scheduled, [inactive])
        self.assertEqual(len(runtime.queue), 0)
        self.assertEqual(logger.records[0]["support_delayed_inactive_only_journeys"], 0)
        self.assertEqual(logger.records[0]["support_delay_depth_blocked_journeys"], 1)

    def test_support_aware_admission_delays_branch_inactive_by_default(self):
        logger = _ListLogger()
        config = {
            "journey_gat_admission_scheduler_enabled": True,
            "journey_gat_admission_support_aware_enabled": True,
            "journey_gat_admission_allow_unsourced_delay": True,
            "journey_gat_admission_max_delay_rounds": 100,
            "pricing_eps": 1.0e-9,
        }
        runtime = _make_journey_gat_admission_runtime(config)
        inactive = _journey("branch-inactive", task_set={3}, cost=1.0)

        scheduled = _journey_gat_target_mode_admission_schedule(
            logger,
            runtime,
            [inactive],
            JourneyDuals(cover={3: 2.0}, fleet_limit=0.0),
            tuple(),
            config,
            cg_iter=1,
            node_id=3,
            depth=1,
            pricing_kind="heuristic",
            certificate_candidate=False,
            active_task_sets={frozenset({1})},
            dominant_task_set_costs={frozenset({3}): 5.0},
        )

        self.assertEqual(scheduled, [])
        self.assertEqual(len(runtime.queue), 1)
        self.assertEqual(logger.records[0]["support_delayed_inactive_only_journeys"], 1)
        self.assertEqual(logger.records[0]["support_delay_depth_blocked_journeys"], 0)

    def test_support_aware_admission_logs_counts_when_exact_is_not_mutating(self):
        logger = _ListLogger()
        config = {
            "journey_gat_admission_scheduler_enabled": True,
            "journey_gat_admission_support_aware_enabled": True,
            "journey_gat_admission_allow_unsourced_delay": True,
            "pricing_eps": 1.0e-9,
        }
        runtime = _make_journey_gat_admission_runtime(config)
        active = _journey("active-replacement", task_set={1}, cost=1.0)
        new = _journey("new-task-set", task_set={2}, cost=1.0)
        inactive = _journey("inactive-replacement", task_set={3}, cost=1.0)

        scheduled = _journey_gat_target_mode_admission_schedule(
            logger,
            runtime,
            [inactive, active, new],
            JourneyDuals(cover={1: 2.0, 2: 2.0, 3: 2.0}, fleet_limit=0.0),
            tuple(),
            config,
            cg_iter=1,
            node_id=3,
            depth=1,
            pricing_kind="exact",
            certificate_candidate=False,
            active_task_sets={frozenset({1})},
            dominant_task_set_costs={frozenset({1}): 5.0, frozenset({3}): 5.0},
        )

        self.assertEqual(scheduled, [inactive, active, new])
        self.assertEqual(len(runtime.queue), 0)
        record = logger.records[0]
        self.assertEqual(record["status"], "bypassed")
        self.assertEqual(record["reason"], "pricing_kind_not_mutated")
        self.assertTrue(record["support_aware_admission_enabled"])
        self.assertEqual(record["support_candidate_active_support_changing_journeys"], 1)
        self.assertEqual(record["support_candidate_new_task_set_journeys"], 1)
        self.assertEqual(record["support_candidate_inactive_only_journeys"], 1)
        self.assertEqual(record["support_online_high_priority_journeys"], 2)
        self.assertEqual(record["support_delayed_inactive_only_journeys"], 0)
        self.assertEqual(record["delay_queue_journeys"], 0)


def _journey(name: str, *, task_set: set[int], cost: float) -> JourneyColumn:
    tasks = tuple(sorted(int(task) for task in task_set))
    return JourneyColumn(
        id=-1,
        trips=tuple(),
        task_set=frozenset(task_set),
        start_time=0.0,
        end_time=1.0,
        travel_cost=float(cost),
        fixed_vehicle_cost=0.0,
        cost=float(cost),
        signature=((tasks, (name,), 0.0),),
    )


if __name__ == "__main__":
    unittest.main()
