from __future__ import annotations

import unittest
from pathlib import Path

from BPC_future.scripts.build_cbf_mode_transition_capture_runbook import (
    TARGETS,
    build_runbook,
)


class CBFModeTransitionCaptureRunbookTests(unittest.TestCase):
    def test_runbook_uses_existing_instances_and_current_task20_paths(self) -> None:
        summary = build_runbook(output_root=Path("BPC_future/results/unit_cbf_capture_runbook"))

        self.assertTrue(summary["all_checks_pass"])
        self.assertTrue(summary["checks"]["has_task5_targets"])
        self.assertTrue(summary["checks"]["has_task10_targets"])
        self.assertTrue(summary["checks"]["has_task20_targets"])
        self.assertTrue(summary["checks"]["all_commands_enable_capture"])

        for target in TARGETS:
            instance = str(target["instance"])
            self.assertTrue(Path(instance).exists(), instance)
            if int(target["scale"]) == 20:
                self.assertIn("/tasks_020/", instance)
                self.assertNotIn("/tasks_20/", instance)

    def test_runbook_does_not_run_solver_or_claim_production_readiness(self) -> None:
        summary = build_runbook(output_root=Path("BPC_future/results/unit_cbf_capture_runbook"))

        self.assertTrue(summary["diagnostic_only"])
        self.assertFalse(summary["runs_bpc_or_pricing"])
        self.assertFalse(summary["production_ready"])
        self.assertFalse(summary["goal_complete"])


if __name__ == "__main__":
    unittest.main()
