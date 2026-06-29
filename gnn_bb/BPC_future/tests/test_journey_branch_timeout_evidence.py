from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_branch_timeout_evidence import build_timeout_evidence


class JourneyBranchTimeoutEvidenceTest(unittest.TestCase):
    def test_root_timeout_change_becomes_hard_negative_and_deep_missing_is_exported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = "BPC_future/logical_graph/tasks_020/fam/demo.json"
            baseline_dir = root / "baseline"
            alt_dir = root / "alt"
            _write_results(
                baseline_dir / "results.csv",
                [
                    _result_row(
                        instance,
                        status="EXTERNAL_TIME_LIMIT",
                        wall_time=600.0,
                        primal=120.0,
                        dual=100.0,
                        gap=0.166667,
                    )
                ],
            )
            _write_results(
                alt_dir / "results.csv",
                [
                    _result_row(
                        instance,
                        status="EXTERNAL_TIME_LIMIT",
                        wall_time=600.0,
                        primal=121.0,
                        dual=100.0,
                        gap=0.173554,
                    )
                ],
            )
            _write_log(
                alt_dir / "logs",
                instance,
                [
                    _branch(
                        depth=0,
                        baseline_pair=[1, 2],
                        selected_pair=[4, 8],
                        changed=True,
                        reason="ok",
                        score=0.41,
                        source="state:root::node:0:depth:0:4,8",
                    ),
                    _branch(
                        depth=1,
                        baseline_pair=[2, 3],
                        selected_pair=[2, 3],
                        changed=False,
                        reason="missing_score_source",
                        constraints=["RF(4,8)=same_vehicle"],
                    ),
                ],
            )
            _write_log(
                baseline_dir / "logs",
                instance,
                [
                    _branch(
                        depth=0,
                        baseline_pair=[1, 2],
                        selected_pair=[1, 2],
                        changed=False,
                        reason="score_below_min",
                        score=0.2,
                        source="state:root::node:0:depth:0:1,2",
                    ),
                    _branch(
                        depth=2,
                        baseline_pair=[5, 6],
                        selected_pair=[5, 6],
                        changed=False,
                        reason="missing_score_source",
                        constraints=["RF(1,2)=same_vehicle", "RF(5,7)=separate_vehicle"],
                    ),
                ],
            )

            summary = build_timeout_evidence(
                baseline_dir=baseline_dir,
                alternative_dir=alt_dir,
                output_dir=root / "out",
                baseline_label="baseline",
                alternative_label="alt",
            )

            self.assertEqual(summary["root_hard_negative_rows"], 1)
            self.assertEqual(summary["root_hard_negative_label_count"], 1)
            self.assertEqual(summary["deep_missing_context_rows"], 2)
            root_rows = _read_jsonl(root / "out" / "root_timeout_hard_negative_rows.jsonl")
            self.assertEqual(root_rows[0]["label_type"], "root_score_timeout_no_effect_hard_negative")
            self.assertEqual(root_rows[0]["selected_pair"], [4, 8])
            self.assertEqual(root_rows[0]["baseline_pair"], [1, 2])
            self.assertEqual(root_rows[0]["y_branch_score_hard_negative"], 1.0)
            missing_rows = _read_jsonl(root / "out" / "deep_missing_context_rows.jsonl")
            self.assertEqual({row["source_experiment"] for row in missing_rows}, {"baseline", "alt"})
            self.assertTrue(all(row["sampling_priority"] == "DEEP_CONTEXT_SCORE_MISSING" for row in missing_rows))
            self.assertTrue(all(row["log_path"] == row["log_file"] for row in missing_rows))
            self.assertTrue(all(row["scored_candidate_count"] == 0 for row in missing_rows))
            self.assertTrue(all(row["eligible_scored_candidate_count"] == 0 for row in missing_rows))
            self.assertTrue(all(row["selected_is_unscored"] for row in missing_rows))


def _result_row(
    instance: str,
    *,
    status: str,
    wall_time: float,
    primal: float,
    dual: float,
    gap: float,
) -> dict[str, object]:
    return {
        "instance": instance,
        "status": status,
        "wall_time": wall_time,
        "primal_bound": primal,
        "dual_bound": dual,
        "gap": gap,
        "gap_available": "true",
        "gap_source": "root_corrected_node_bound",
    }


def _write_results(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "instance",
        "status",
        "wall_time",
        "primal_bound",
        "dual_bound",
        "gap",
        "gap_available",
        "gap_source",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _branch(
    *,
    depth: int,
    baseline_pair: list[int],
    selected_pair: list[int],
    changed: bool,
    reason: str,
    score: float | None = None,
    source: str | None = None,
    constraints: list[str] | None = None,
) -> dict[str, object]:
    return {
        "event": "journey_branch",
        "node_id": depth,
        "depth": depth,
        "branch_state_key": "root" if depth == 0 else ";".join(constraints or []),
        "branch_constraints": constraints or [],
        "candidate_count": 12,
        "baseline_pair": baseline_pair,
        "baseline_rank": 3,
        "selected_pair": selected_pair,
        "selected_pair_changed": changed,
        "selected_score": score,
        "selected_score_source": source,
        "branch_score_selection_gate_passed": reason == "ok",
        "branch_score_selection_gate_reason": reason,
        "branch_score_require_state_key": True,
    }


def _write_log(log_dir: Path, instance: str, events: list[dict[str, object]]) -> None:
    path = log_dir / f"{instance}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


if __name__ == "__main__":
    unittest.main()
