from __future__ import annotations

import itertools
import math
import unittest
from dataclasses import replace

from BPC_future.core.data import load_future_data
from BPC_future.master.journey_rmp import JourneyDuals
from BPC_future.pricing.available_mask_completion_bound import AvailableMaskCompletionBound


def _task_to_bit(tasks):
    return {int(task): index for index, task in enumerate(tasks)}


def _arc_rc(data, duals, origin, destination):
    if int(origin) == 0 and int(destination) == 0:
        return 0.0
    options = data.options(int(origin), int(destination))
    value = min(float(option.cost) for option in options)
    if int(destination) in data.tasks:
        value += float(data.task_value(int(destination), "c_srv"))
        value -= float(duals.cover.get(int(destination), 0.0))
    return value


def _best_open_bruteforce(data, duals, last, tasks):
    tasks = tuple(int(task) for task in tasks)
    if not tasks:
        return _arc_rc(data, duals, int(last), 0)
    best = float("inf")
    for order in itertools.permutations(tasks):
        total = 0.0
        current = int(last)
        for task in order:
            total += _arc_rc(data, duals, current, int(task))
            current = int(task)
        total += _arc_rc(data, duals, current, 0)
        best = min(best, total)
    return best


def _best_tail_bruteforce(data, duals, tasks, sorties, max_tasks_per_sortie):
    tasks = tuple(int(task) for task in tasks)
    if int(sorties) <= 0 or not tasks:
        return 0.0
    best = 0.0
    for size in range(1, min(len(tasks), int(max_tasks_per_sortie)) + 1):
        for subset in itertools.combinations(tasks, size):
            remaining = tuple(task for task in tasks if task not in set(subset))
            candidate = _best_open_bruteforce(data, duals, 0, subset) + _best_tail_bruteforce(
                data,
                duals,
                remaining,
                int(sorties) - 1,
                int(max_tasks_per_sortie),
            )
            best = min(best, candidate)
    return best


class AvailableMaskCompletionBoundTests(unittest.TestCase):
    def test_tail_uses_each_task_dual_at_most_once(self):
        data = replace(load_future_data("very_small"), tasks=(1,), sortie_limit=2)
        duals = JourneyDuals(cover={1: 100.0}, fleet_limit=0.0)
        bound = AvailableMaskCompletionBound(
            data,
            duals,
            _task_to_bit(data.tasks),
            max_tasks_per_sortie=1,
            sortie_limit=2,
        )
        bit = 1 << _task_to_bit(data.tasks)[1]

        result = bound.lower_bound_for_suffix(available_mask=bit, remaining_sorties=2)
        closed_once = bound._closed_value(bit)

        self.assertIsNotNone(result.value)
        self.assertAlmostEqual(result.value, min(0.0, closed_once), places=9)
        self.assertGreater(result.value, 2.0 * closed_once - 1.0e-9)

    def test_lower_bound_is_not_above_bruteforce_relaxed_completion(self):
        data = replace(load_future_data("very_small"), tasks=(1, 2), sortie_limit=2)
        duals = JourneyDuals(cover={1: 12.0, 2: 9.0}, fleet_limit=0.0)
        task_to_bit = _task_to_bit(data.tasks)
        bound = AvailableMaskCompletionBound(
            data,
            duals,
            task_to_bit,
            max_tasks_per_sortie=2,
            sortie_limit=2,
        )
        available = sum(1 << task_to_bit[task] for task in data.tasks)

        result = bound.lower_bound_for_partial(
            last=0,
            available_mask=available,
            remaining_slots_current_sortie=2,
            remaining_sorties_after_current=1,
        )
        exact = _best_tail_bruteforce(data, duals, data.tasks, sorties=2, max_tasks_per_sortie=2)

        self.assertIsNotNone(result.value)
        self.assertLessEqual(float(result.value), float(exact) + 1.0e-9)

    def test_negative_completion_is_not_pruned_by_bound(self):
        data = replace(load_future_data("very_small"), tasks=(1,), sortie_limit=1)
        duals = JourneyDuals(cover={1: 100.0}, fleet_limit=0.0)
        task_to_bit = _task_to_bit(data.tasks)
        bound = AvailableMaskCompletionBound(
            data,
            duals,
            task_to_bit,
            max_tasks_per_sortie=1,
            sortie_limit=1,
        )
        available = 1 << task_to_bit[1]

        result = bound.lower_bound_for_partial(
            last=0,
            available_mask=available,
            remaining_slots_current_sortie=1,
            remaining_sorties_after_current=0,
        )

        self.assertIsNotNone(result.value)
        self.assertLess(float(result.value), -1.0e-6)

    def test_nonnegative_completion_can_support_prune(self):
        data = replace(load_future_data("very_small"), tasks=(1,), sortie_limit=1)
        duals = JourneyDuals(cover={1: -100.0}, fleet_limit=0.0)
        task_to_bit = _task_to_bit(data.tasks)
        bound = AvailableMaskCompletionBound(
            data,
            duals,
            task_to_bit,
            max_tasks_per_sortie=1,
            sortie_limit=1,
        )
        available = 1 << task_to_bit[1]

        result = bound.lower_bound_for_partial(
            last=0,
            available_mask=available,
            remaining_slots_current_sortie=1,
            remaining_sorties_after_current=0,
        )

        self.assertIsNotNone(result.value)
        self.assertGreaterEqual(float(result.value), -1.0e-6)

    def test_resource_optimistic_infeasible_subset_is_filtered(self):
        data = replace(load_future_data("very_small"), tasks=(1, 2), sortie_limit=1, capacity=0.0)
        duals = JourneyDuals(cover={1: 100.0, 2: 100.0}, fleet_limit=0.0)
        task_to_bit = _task_to_bit(data.tasks)
        bound = AvailableMaskCompletionBound(
            data,
            duals,
            task_to_bit,
            max_tasks_per_sortie=2,
            sortie_limit=1,
        )
        available = sum(1 << task_to_bit[task] for task in data.tasks)

        result = bound.lower_bound_for_partial(
            last=0,
            available_mask=available,
            remaining_slots_current_sortie=2,
            remaining_sorties_after_current=0,
            remaining_capacity=0.0,
        )

        self.assertFalse(result.disabled)
        self.assertGreater(bound.resource_filtered_subsets, 0)

    def test_state_budget_disables_without_truncation(self):
        data = replace(load_future_data("very_small"), tasks=(1, 2), sortie_limit=2)
        duals = JourneyDuals(cover={1: 10.0, 2: 8.0}, fleet_limit=0.0)
        task_to_bit = _task_to_bit(data.tasks)
        bound = AvailableMaskCompletionBound(
            data,
            duals,
            task_to_bit,
            max_tasks_per_sortie=2,
            sortie_limit=2,
            max_states=1,
        )
        available = sum(1 << task_to_bit[task] for task in data.tasks)

        result = bound.lower_bound_for_partial(
            last=0,
            available_mask=available,
            remaining_slots_current_sortie=2,
            remaining_sorties_after_current=1,
        )

        self.assertTrue(result.disabled)
        self.assertTrue(bound.disabled)
        self.assertEqual(bound.disable_reason, "state_budget")

    def test_subset_budget_below_sortie_capacity_disables_no_bound(self):
        data = replace(load_future_data("very_small"), tasks=(1, 2), sortie_limit=1)
        duals = JourneyDuals(cover={1: 100.0, 2: 100.0}, fleet_limit=0.0)
        task_to_bit = _task_to_bit(data.tasks)
        bound = AvailableMaskCompletionBound(
            data,
            duals,
            task_to_bit,
            max_tasks_per_sortie=2,
            sortie_limit=1,
            max_subset_size=1,
        )
        available = sum(1 << task_to_bit[task] for task in data.tasks)

        result = bound.lower_bound_for_partial(
            last=0,
            available_mask=available,
            remaining_slots_current_sortie=2,
            remaining_sorties_after_current=0,
        )

        self.assertTrue(result.disabled)
        self.assertTrue(bound.disabled)
        self.assertEqual(bound.disable_reason, "subset_budget_below_sortie_capacity")


if __name__ == "__main__":
    unittest.main()
