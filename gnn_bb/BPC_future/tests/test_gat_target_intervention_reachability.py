from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.audit_gat_target_intervention_reachability import (
    audit_reachability,
)


def _worker_csv(root: Path, name: str) -> Path:
    csv = root / name / "results.csv"
    csv.parent.mkdir(parents=True, exist_ok=True)
    csv.write_text("status\nTIME_LIMIT\n", encoding="utf-8")
    return csv


def _write_worker_log(
    worker_csv: Path,
    events: list[dict[str, object]],
    *,
    include_non_worker_line: bool = False,
) -> None:
    log_dir = worker_csv.parent / "logs" / "run"
    log_dir.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if include_non_worker_line:
        lines.append(json.dumps({"event": "journey_pricing"}, sort_keys=True))
    lines.extend(json.dumps(event, sort_keys=True) for event in events)
    (log_dir / "events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _worker_event(
    *,
    context_hash: str,
    target_sequence: list[int] | None = None,
    skipped: bool = False,
    skip_reason: str = "",
    returned_samples: list[object] | None = None,
) -> dict[str, object]:
    sequence = target_sequence or [2, 3]
    return {
        "event": "journey_sharded_pulse_hidden_negative_worker",
        "pulse_worker_context_hash": context_hash,
        "pulse_worker_skipped": skipped,
        "pulse_worker_skip_reason": skip_reason,
        "pulse_worker_status": "FOUND_NEGATIVE",
        "pulse_worker_returned_journeys": 1,
        "pulse_worker_best_rc": -1.25,
        "pulse_worker_target_transition_priority_sequence": sequence,
        "pulse_worker_target_sequence_materialized": not skipped,
        "pulse_worker_returned_candidate_sequence_samples": returned_samples or [],
    }


def _candidate(
    *,
    name: str,
    expected_context: str,
    worker_csv: Path,
    capture_pricing_kind: str = "exact",
    target_sequence: list[int] | None = None,
) -> dict[str, object]:
    return {
        "name": name,
        "instance": f"{name}.json",
        "expected_context_hash": expected_context,
        "capture_pricing_kind": capture_pricing_kind,
        "target_sequence": target_sequence or [2, 3],
        "target_arc_option_sequence": ["0->2:a", "2->3:a", "3->0:a"],
        "worker_csv": str(worker_csv),
    }


def _command(
    *,
    name: str,
    before_heuristic: bool,
    before_exact: bool = False,
    learning_enabled: bool = True,
) -> dict[str, str]:
    tokens = [
        "python",
        "BPC_future/scripts/run_bpc_future.py",
        (
            "journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled="
            f"{str(before_heuristic)}"
        ),
        (
            "journey_sharded_pulse_hidden_negative_worker_before_exact_enabled="
            f"{str(before_exact)}"
        ),
    ]
    if not learning_enabled:
        tokens.append("journey_learning_enabled=False")
    return {
        "command_type": f"task020_{name}_target_priority_worker",
        "command": " ".join(tokens),
    }


def _summary_file(
    root: Path,
    *,
    candidates: list[dict[str, object]],
    commands: list[dict[str, str]],
) -> Path:
    path = root / "summary.json"
    path.write_text(
        json.dumps(
            {
                "certificate_ready": False,
                "official_bound_effect": False,
                "candidate_runs": candidates,
                "commands": commands,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


class GATTargetInterventionReachabilityTests(unittest.TestCase):
    def test_same_context_executed_target_match_allows_training_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            csv = _worker_csv(tmp, "reachable")
            _write_worker_log(
                csv,
                [_worker_event(context_hash="ctx-hit", target_sequence=[2, 3])],
            )
            summary_file = _summary_file(
                tmp,
                candidates=[
                    _candidate(name="reachable", expected_context="ctx-hit", worker_csv=csv)
                ],
                commands=[_command(name="reachable", before_heuristic=False, before_exact=True)],
            )

            summary = audit_reachability(
                runbook_summaries=[summary_file],
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            record = summary["records"][0]
            self.assertEqual(record["reachability_class"], "target_intervention_reachable")
            self.assertTrue(record["training_label_allowed"])
            self.assertEqual(summary["reachable_target_intervention_count"], 1)
            self.assertFalse(summary["production_ready"])
            self.assertFalse(summary["certificate_ready"])
            self.assertFalse(summary["official_bound_effect"])

    def test_worker_log_without_worker_event_is_not_training_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            csv = _worker_csv(tmp, "hook_miss")
            _write_worker_log(csv, [], include_non_worker_line=True)
            summary_file = _summary_file(
                tmp,
                candidates=[
                    _candidate(name="hook_miss", expected_context="ctx-hit", worker_csv=csv)
                ],
                commands=[_command(name="hook_miss", before_heuristic=False, before_exact=True)],
            )

            summary = audit_reachability(
                runbook_summaries=[summary_file],
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            record = summary["records"][0]
            self.assertEqual(record["reachability_class"], "worker_hook_not_triggered")
            self.assertFalse(record["training_label_allowed"])

    def test_context_miss_is_not_training_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            csv = _worker_csv(tmp, "context_miss")
            _write_worker_log(
                csv,
                [_worker_event(context_hash="ctx-other", target_sequence=[2, 3])],
            )
            summary_file = _summary_file(
                tmp,
                candidates=[
                    _candidate(
                        name="context_miss",
                        expected_context="ctx-expected",
                        worker_csv=csv,
                    )
                ],
                commands=[_command(name="context_miss", before_heuristic=False, before_exact=True)],
            )

            summary = audit_reachability(
                runbook_summaries=[summary_file],
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            record = summary["records"][0]
            self.assertEqual(record["reachability_class"], "worker_context_not_reached")
            self.assertFalse(record["training_label_allowed"])

    def test_executed_without_target_causal_match_is_not_training_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            csv = _worker_csv(tmp, "target_miss")
            _write_worker_log(
                csv,
                [_worker_event(context_hash="ctx-hit", target_sequence=[9, 8])],
            )
            summary_file = _summary_file(
                tmp,
                candidates=[
                    _candidate(name="target_miss", expected_context="ctx-hit", worker_csv=csv)
                ],
                commands=[_command(name="target_miss", before_heuristic=False, before_exact=True)],
            )

            summary = audit_reachability(
                runbook_summaries=[summary_file],
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            record = summary["records"][0]
            self.assertEqual(
                record["reachability_class"],
                "worker_executed_without_target_causal_match",
            )
            self.assertFalse(record["training_label_allowed"])
            self.assertEqual(
                summary["next_decision"],
                "improve_target_reachability_or_budget_before_labeling",
            )

    def test_stage_and_learning_policy_mismatches_block_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            stage_csv = _worker_csv(tmp, "stage_miss")
            learning_csv = _worker_csv(tmp, "learning_miss")
            _write_worker_log(
                stage_csv,
                [_worker_event(context_hash="ctx-stage", target_sequence=[2, 3])],
            )
            _write_worker_log(
                learning_csv,
                [_worker_event(context_hash="ctx-learning", target_sequence=[2, 3])],
            )
            summary_file = _summary_file(
                tmp,
                candidates=[
                    _candidate(
                        name="stage_miss",
                        expected_context="ctx-stage",
                        worker_csv=stage_csv,
                        capture_pricing_kind="exact",
                    ),
                    _candidate(
                        name="learning_miss",
                        expected_context="ctx-learning",
                        worker_csv=learning_csv,
                        capture_pricing_kind="exact",
                    ),
                ],
                commands=[
                    _command(name="stage_miss", before_heuristic=True),
                    _command(
                        name="learning_miss",
                        before_heuristic=False,
                        before_exact=True,
                        learning_enabled=False,
                    ),
                ],
            )

            summary = audit_reachability(
                runbook_summaries=[summary_file],
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )

            by_name = {record["name"]: record for record in summary["records"]}
            self.assertEqual(
                by_name["stage_miss"]["reachability_class"],
                "worker_stage_mismatch",
            )
            self.assertEqual(
                by_name["learning_miss"]["reachability_class"],
                "capture_learning_policy_mismatch",
            )
            self.assertFalse(by_name["stage_miss"]["training_label_allowed"])
            self.assertFalse(by_name["learning_miss"]["training_label_allowed"])


if __name__ == "__main__":
    unittest.main()
