from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_branch_forced_replay_delta_rows import build_delta_rows


class JourneyBranchForcedReplayDeltaRowsTest(unittest.TestCase):
    def test_timeout_resolved_and_timeout_no_effect_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance_pos = "BPC_future/logical_graph/tasks_020/fam/a.json"
            instance_neg = "BPC_future/logical_graph/tasks_020/fam/b.json"
            baseline_csv = root / "baseline.csv"
            _write_csv(
                baseline_csv,
                [
                    _result_row(instance_pos, "EXTERNAL_TIME_LIMIT", 600.0),
                    _result_row(instance_neg, "EXTERNAL_TIME_LIMIT", 600.0),
                ],
            )
            pos_csv = root / "pos" / "results.csv"
            neg_csv = root / "neg" / "results.csv"
            _write_csv(pos_csv, [_result_row(instance_pos, "OPTIMAL", 341.0)])
            _write_csv(neg_csv, [_result_row(instance_neg, "EXTERNAL_TIME_LIMIT", 600.0)])
            pos_log_dir = root / "pos" / "logs"
            neg_log_dir = root / "neg" / "logs"
            _write_log(pos_log_dir, instance_pos, selected_pair=[2, 10], baseline_pair=[1, 9])
            _write_log(neg_log_dir, instance_neg, selected_pair=[4, 16], baseline_pair=[1, 2])
            runbook = root / "runbook.json"
            runbook.write_text(
                json.dumps(
                    {
                        "entries": [
                            _entry("pos", instance_pos, [2, 10], pos_csv, pos_log_dir, [1, 9]),
                            _entry("neg", instance_neg, [4, 16], neg_csv, neg_log_dir, [1, 2]),
                        ]
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            summary = build_delta_rows(
                runbook=runbook,
                baseline_csvs=[baseline_csv],
                output_dir=root / "out",
                report=root / "report.md",
            )

            self.assertEqual(summary["row_count"], 2)
            self.assertEqual(
                summary["label_type_counts"],
                {
                    "changed_timeout_no_effect_hard_negative": 1,
                    "strong_positive": 1,
                },
            )
            rows = _read_jsonl(root / "out" / "branch_counterfactual_delta_rows.jsonl")
            by_experiment = {row["experiment"]: row for row in rows}
            self.assertTrue(by_experiment["pos"]["timeout_resolved"])
            self.assertEqual(by_experiment["pos"]["deltas"]["wall_time_gain"], 259.0)
            self.assertEqual(
                by_experiment["neg"]["counterfactual_label_type"],
                "changed_timeout_no_effect_hard_negative",
            )

    def test_forced_pair_mismatch_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = "BPC_future/logical_graph/tasks_020/fam/a.json"
            baseline_csv = root / "baseline.csv"
            result_csv = root / "result.csv"
            _write_csv(baseline_csv, [_result_row(instance, "EXTERNAL_TIME_LIMIT", 600.0)])
            _write_csv(result_csv, [_result_row(instance, "OPTIMAL", 100.0)])
            log_dir = root / "logs"
            _write_log(
                log_dir,
                instance,
                selected_pair=[1, 3],
                baseline_pair=[1, 2],
                extra_candidates=[[2, 10]],
            )
            runbook = root / "runbook.json"
            runbook.write_text(
                json.dumps(
                    {"entries": [_entry("mismatch", instance, [2, 10], result_csv, log_dir, [1, 2])]},
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            summary = build_delta_rows(
                runbook=runbook,
                baseline_csvs=[baseline_csv],
                output_dir=root / "out",
                report=root / "report.md",
            )

            self.assertEqual(summary["row_count"], 0)
            self.assertEqual(summary["skipped_counts"], {"row_not_usable": 1})


def _entry(
    experiment: str,
    instance: str,
    forced_pair: list[int],
    results_csv: Path,
    log_dir: Path,
    source_selected_pair: list[int],
) -> dict[str, object]:
    return {
        "experiment": experiment,
        "instance": instance,
        "forced_pair": forced_pair,
        "source_depth": 0,
        "source_node_id": 0,
        "source_selected_pair": source_selected_pair,
        "command": [
            "python",
            "BPC_future/scripts/run_bpc_future_external_timeout_batch.py",
            "--results-csv",
            str(results_csv),
            "--log-dir",
            str(log_dir),
        ],
    }


def _result_row(instance: str, status: str, wall_time: float) -> dict[str, object]:
    return {
        "instance": instance,
        "status": status,
        "wall_time": wall_time,
        "solving_time": wall_time,
        "node_count": 7,
        "exact_pricing_calls": 11,
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["instance", "status", "wall_time", "solving_time", "node_count", "exact_pricing_calls"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_log(
    log_dir: Path,
    instance: str,
    *,
    selected_pair: list[int],
    baseline_pair: list[int],
    extra_candidates: list[list[int]] | None = None,
) -> None:
    path = log_dir / f"{instance}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    selected = _candidate(*selected_pair)
    top = [selected, _candidate(1, 2)]
    for pair in extra_candidates or []:
        top.append(_candidate(*pair))
    event = {
        "event": "journey_branch_candidates",
        "node_id": 0,
        "depth": 0,
        "time": 12.0,
        "candidate_count": 2,
        "eligible_count": 2,
        "baseline_pair": baseline_pair,
        "selected_pair": selected_pair,
        "selected": selected,
        "top": top,
        "priority_top": [selected],
    }
    branch = {
        "event": "journey_branch",
        "node_id": 0,
        "depth": 0,
        "selected_pair": selected_pair,
        "baseline_pair": baseline_pair,
    }
    path.write_text(
        json.dumps(event, sort_keys=True) + "\n" + json.dumps(branch, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _candidate(task_i: int, task_j: int) -> dict[str, object]:
    return {
        "task_i": task_i,
        "task_j": task_j,
        "same_mass": 0.5,
        "fractionality": 0.5,
        "support_count": 1,
        "incumbent_relation": True,
        "incumbent_disagreement": 0.5,
        "pool_same_allowed": 300,
        "pool_separate_allowed": 350,
        "pool_max_child_width": 350,
        "pool_total_child_width": 650,
        "pool_balance_gap": 50,
    }


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


if __name__ == "__main__":
    unittest.main()
