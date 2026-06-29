from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.summarize_journey_paired_probe_runbook import summarize_paired_probe


class JourneyPairedProbeSummaryTests(unittest.TestCase):
    def test_summarizes_group_relative_gains(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runbook_dir = root / "runbook"
            runs = runbook_dir / "runs"
            runs.mkdir(parents=True)
            entries = [
                _entry("baseline", "selected_baseline", [1, 2]),
                _entry("fast_alt", "alternative", [1, 3]),
                _entry("slow_alt", "alternative", [1, 4]),
            ]
            (runbook_dir / "runbook.json").write_text(
                json.dumps({"entries": entries}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            _write_result(runs / "baseline" / "results.csv", status="TIME_LIMIT", wall=180.0, gap=0.10)
            _write_result(runs / "fast_alt" / "results.csv", status="TIME_LIMIT", wall=130.0, gap=0.09)
            _write_result(runs / "slow_alt" / "results.csv", status="TIME_LIMIT", wall=220.0, gap=0.11)
            completion_summary = root / "completion.json"
            completion_summary.write_text(
                json.dumps(
                    {
                        "records": [
                            _completion_record("baseline", profile=90.0, retry=7),
                            _completion_record("fast_alt", profile=40.0, retry=3),
                            _completion_record("slow_alt", profile=120.0, retry=9),
                        ]
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            child_rows = root / "child_probe_rows.jsonl"
            child_rows.write_text(
                "\n".join(
                    json.dumps(row, sort_keys=True)
                    for row in [
                        _child_row("baseline", retry=7, proof_cpu=30.0),
                        _child_row("fast_alt", retry=3, proof_cpu=10.0),
                        _child_row("slow_alt", retry=9, proof_cpu=40.0),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = summarize_paired_probe(
                runbook_dir / "runbook.json",
                root / "out",
                root / "report.md",
                completion_tail_summary=completion_summary,
                child_probe_rows=child_rows,
            )

            self.assertEqual(summary["paired_group_count"], 1)
            self.assertEqual(summary["label_counts"], {"hard_negative_proxy": 1, "positive_proxy": 1})
            rows = [
                json.loads(line)
                for line in (root / "out" / "paired_probe_rows.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            by_experiment = {row["experiment"]: row for row in rows}
            self.assertEqual(by_experiment["fast_alt"]["target_replay_status"], "not_audited")
            self.assertEqual(by_experiment["fast_alt"]["paired_label_type"], "positive_proxy")
            self.assertAlmostEqual(by_experiment["fast_alt"]["paired_wall_time_gain"], 50.0)
            self.assertAlmostEqual(by_experiment["fast_alt"]["paired_completion_profile_gain"], 50.0)
            self.assertAlmostEqual(by_experiment["fast_alt"]["paired_child_cb_retry_gain"], 4.0)
            self.assertAlmostEqual(by_experiment["fast_alt"]["source_alt_routeopt_bkf_score"], 7.25)
            self.assertEqual(
                by_experiment["fast_alt"]["source_alt_routeopt_bkf_reason"],
                "phase1_min_child_lp_gain=2",
            )
            self.assertAlmostEqual(by_experiment["fast_alt"]["phase1_min_child_lp_gain"], 2.0)
            self.assertAlmostEqual(by_experiment["fast_alt"]["phase1_child_lp_gain_product"], 8.0)
            self.assertAlmostEqual(by_experiment["fast_alt"]["phase2_negative_child_count"], 0.0)
            self.assertEqual(by_experiment["slow_alt"]["paired_label_type"], "hard_negative_proxy")
            self.assertIn("label_counts", (root / "report.md").read_text(encoding="utf-8"))

    def test_marks_alternative_invalid_when_target_source_node_is_not_replayed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runbook_dir = root / "runbook"
            runs = runbook_dir / "runs"
            runs.mkdir(parents=True)
            entries = [
                _entry("baseline", "selected_baseline", [1, 2]),
                _entry("missed_alt", "alternative", [1, 3]),
            ]
            (runbook_dir / "runbook.json").write_text(
                json.dumps({"entries": entries}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            _write_result(runs / "baseline" / "results.csv", status="TIME_LIMIT", wall=180.0, gap=0.10)
            _write_result(runs / "missed_alt" / "results.csv", status="TIME_LIMIT", wall=120.0, gap=0.08)
            _write_branch_log(runs / "baseline" / "logs" / "instance.jsonl", node=1, depth=1, pair=[1, 2])
            _write_branch_log(runs / "missed_alt" / "logs" / "instance.jsonl", node=9, depth=1, pair=[1, 3])

            summary = summarize_paired_probe(
                runbook_dir / "runbook.json",
                root / "out",
                root / "report.md",
            )

            self.assertEqual(summary["label_counts"], {"target_not_replayed": 1})
            self.assertEqual(summary["valid_observed_alternative_entry_count"], 0)
            rows = [
                json.loads(line)
                for line in (root / "out" / "paired_probe_rows.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            missed = {row["experiment"]: row for row in rows}["missed_alt"]
            self.assertTrue(missed["target_replay_audited"])
            self.assertEqual(missed["target_replay_status"], "target_not_replayed")
            self.assertFalse(missed["target_pair_selected"])
            self.assertEqual(missed["paired_label_type"], "target_not_replayed")


def _entry(experiment: str, role: str, pair: list[int]) -> dict[str, object]:
    entry: dict[str, object] = {
        "experiment": experiment,
        "pair_group_id": "group_a",
        "pair_role": role,
        "instance": "instance.json",
        "source_node_id": 1,
        "source_depth": 1,
        "source_selected_pair": [1, 2],
        "forced_pair": pair,
        "source_alt_selection_reason": role,
    }
    if role == "alternative":
        entry.update(
            {
                "source_alt_routeopt_bkf_score": 7.25 if experiment == "fast_alt" else 1.0,
                "source_alt_routeopt_bkf_reason": "phase1_min_child_lp_gain=2",
                "source_alt_phase1_min_child_lp_gain": 2.0 if experiment == "fast_alt" else 0.1,
                "source_alt_phase1_child_lp_gain_product": 8.0 if experiment == "fast_alt" else 0.1,
                "source_alt_phase2_negative_child_count": 0.0 if experiment == "fast_alt" else 3.0,
            }
        )
    return entry


def _write_result(path: Path, *, status: str, wall: float, gap: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "status,wall_time,gap_available,gap,node_count,columns,pricing_calls,exact_pricing_calls,generated_sequences\n"
        f"{status},{wall},true,{gap},1,2,3,4,5\n",
        encoding="utf-8",
    )


def _completion_record(experiment: str, *, profile: float, retry: int) -> dict[str, object]:
    return {
        "log_file": f"/tmp/runs/{experiment}/logs/instance.json.jsonl",
        "completion_retry_count": retry,
        "completion_retry_total_profile_generation_time": profile,
        "completion_retry_total_generated_sequences": 1000,
        "completion_retry_total_negative_journeys": 1,
    }


def _child_row(experiment: str, *, retry: int, proof_cpu: float) -> dict[str, object]:
    return {
        "log_file": f"/tmp/runs/{experiment}/logs/instance.json.jsonl",
        "child_completion_bound_retry_count": retry,
        "child_exact_pricing_event_count": retry + 1,
        "child_negative_pricing_event_count": retry + 2,
        "child_proof_cpu": proof_cpu,
        "child_fathomed": 0.0,
        "right_censored": True,
    }


def _write_branch_log(path: Path, *, node: int, depth: int, pair: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = [
        {"event": "journey_branch_candidates", "node_id": node, "depth": depth, "selected_pair": pair},
        {"event": "journey_branch", "node_id": node, "depth": depth, "selected_pair": pair},
    ]
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
