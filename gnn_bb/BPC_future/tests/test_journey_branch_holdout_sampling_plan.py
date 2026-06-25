from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.build_journey_branch_holdout_sampling_plan import (
    build_holdout_sampling_plan,
)


class JourneyBranchHoldoutSamplingPlanTests(unittest.TestCase):
    def test_only_target200_positive_instances_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            target_known = (
                "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/"
                "target_seed1_logical_graph.json"
            )
            weak_known = (
                "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/"
                "weak_seed2_logical_graph.json"
            )
            uncovered = (
                "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/"
                "uncovered_seed3_logical_graph.json"
            )
            results = tmp_path / "results.csv"
            self._write_results(
                results,
                [
                    {"instance": target_known, "status": "OPTIMAL", "wall_time": "250", "node_count": "5"},
                    {"instance": weak_known, "status": "OPTIMAL", "wall_time": "230", "node_count": "4"},
                    {"instance": uncovered, "status": "OPTIMAL", "wall_time": "240", "node_count": "4"},
                ],
            )
            positive = tmp_path / "delta"
            positive.mkdir()
            (positive / "branch_counterfactual_delta_rows.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "instance": target_known,
                                "counterfactual_label_type": "strong_positive",
                                "alternative_forced_pair_matched": True,
                                "right_censored_counterfactual": False,
                                "baseline_status": "OPTIMAL",
                                "alternative_status": "OPTIMAL",
                                "baseline_wall_time": 250.0,
                                "alternative_wall_time": 180.0,
                            },
                            sort_keys=True,
                        ),
                        json.dumps(
                            {
                                "instance": weak_known,
                                "counterfactual_label_type": "strong_positive",
                                "alternative_forced_pair_matched": True,
                                "right_censored_counterfactual": False,
                                "baseline_status": "OPTIMAL",
                                "alternative_status": "OPTIMAL",
                                "baseline_wall_time": 230.0,
                                "alternative_wall_time": 215.0,
                            },
                            sort_keys=True,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_holdout_sampling_plan(
                results_csv=[results],
                positive_inputs=[positive],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
                limit=4,
            )

            self.assertFalse(summary["runs_bpc_or_pricing"])
            self.assertFalse(summary["official_bound_effect"])
            self.assertEqual(summary["known_strict_positive_instance_count"], 2)
            self.assertEqual(summary["known_target200_positive_instance_count"], 1)
            self.assertEqual(summary["actionable_context_count"], 2)
            self.assertEqual(summary["selected_context_count"], 2)
            selected_by_instance = {row["instance"]: row for row in summary["rows"]}
            all_rows = _read_jsonl(tmp_path / "out" / "holdout_sampling_all_rows.jsonl")
            by_instance = {row["instance"]: row for row in all_rows}
            self.assertEqual(
                by_instance[target_known]["recommended_action"],
                "ALREADY_HAS_TARGET200_POSITIVE",
            )
            self.assertNotIn(target_known, selected_by_instance)
            self.assertTrue(by_instance[target_known]["known_target200_positive_instance"])
            self.assertTrue(by_instance[weak_known]["known_strict_positive_instance"])
            self.assertFalse(by_instance[weak_known]["known_target200_positive_instance"])
            self.assertEqual(
                selected_by_instance[weak_known]["recommended_action"],
                "COLLECT_TOP200_DIAG_LOG",
            )
            self.assertEqual(
                selected_by_instance[uncovered]["recommended_action"],
                "COLLECT_TOP200_DIAG_LOG",
            )
            self.assertIn(
                "journey_branch_candidate_log_top_n=200",
                selected_by_instance[uncovered]["recommended_command"],
            )
            self.assertTrue((tmp_path / "out" / "commands.sh").exists())

    def test_recommends_child_probe_when_candidate_log_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = (
                "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/"
                "case_seed3_logical_graph.json"
            )
            results = tmp_path / "results.csv"
            self._write_results(
                results,
                [{"instance": instance, "status": "OPTIMAL", "wall_time": "240", "node_count": "6"}],
            )
            log_path = tmp_path / "logs" / f"{instance}.jsonl"
            log_path.parent.mkdir(parents=True)
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"event": "journey_pricing", "cg_iter": 7}, sort_keys=True),
                        json.dumps({"event": "journey_pricing", "cg_iter": 21}, sort_keys=True),
                        json.dumps(
                            {
                                "event": "journey_branch_candidates",
                                "node_id": 0,
                                "depth": 0,
                                "candidate_count": 5,
                                "priority_top": [{"task_i": 1, "task_j": 2}],
                            },
                            sort_keys=True,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_holdout_sampling_plan(
                results_csv=[results],
                log_paths=[log_path],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
            )

            row = summary["rows"][0]
            self.assertEqual(row["recommended_action"], "BUILD_CHILD_PROBE_RUNBOOK")
            self.assertEqual(row["branch_candidate_event_count"], 1)
            self.assertIn("--probe-mode child_probe", row["recommended_command"])
            self.assertEqual(row["cg_iterations_before_first_branch"], 21)
            self.assertEqual(row["probe_max_cg_iterations"], 29)
            self.assertIn("--probe-max-cg-iterations 29", row["recommended_command"])
            self.assertNotIn(" --log ", row["recommended_command"])
            self.assertIn(str(log_path), row["recommended_command"])

    def test_routes_confirmed_no_branch_root_tail_out_of_branch_sampling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = (
                "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/"
                "root_tail_seed9_logical_graph.json"
            )
            results = tmp_path / "results.csv"
            self._write_results(
                results,
                [{"instance": instance, "status": "OPTIMAL", "wall_time": "214", "node_count": "1"}],
            )
            log_path = tmp_path / "logs" / f"{instance}.jsonl"
            log_path.parent.mkdir(parents=True)
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"event": "journey_node_start", "node_id": 0}, sort_keys=True),
                        json.dumps({"event": "journey_pricing", "cg_iter": 46}, sort_keys=True),
                        json.dumps({"event": "finish", "status": "OPTIMAL"}, sort_keys=True),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_holdout_sampling_plan(
                results_csv=[results],
                log_paths=[log_path],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
            )

            all_rows = _read_jsonl(tmp_path / "out" / "holdout_sampling_all_rows.jsonl")
            self.assertEqual(summary["actionable_context_count"], 0)
            self.assertEqual(summary["selected_context_count"], 0)
            self.assertEqual(all_rows[0]["recommended_action"], "ROUTE_TO_ROOT_PRICING_TAIL")
            self.assertEqual(all_rows[0]["branch_event_count"], 0)
            self.assertEqual(all_rows[0]["branch_candidate_event_count"], 0)
            self.assertEqual(all_rows[0]["recommended_command"], "")
            report = (tmp_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("ROUTE_TO_ROOT_PRICING_TAIL", report)

    def test_old_branch_log_without_candidate_features_still_collects_top200(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            instance = (
                "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/"
                "old_branch_seed4_logical_graph.json"
            )
            results = tmp_path / "results.csv"
            self._write_results(
                results,
                [{"instance": instance, "status": "OPTIMAL", "wall_time": "240", "node_count": "3"}],
            )
            log_path = tmp_path / "logs" / f"{instance}.jsonl"
            log_path.parent.mkdir(parents=True)
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"event": "journey_pricing", "cg_iter": 9}, sort_keys=True),
                        json.dumps(
                            {"event": "journey_branch", "node_id": 0, "depth": 0},
                            sort_keys=True,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_holdout_sampling_plan(
                results_csv=[results],
                log_paths=[log_path],
                output_dir=tmp_path / "out",
                report=tmp_path / "report.md",
            )

            row = summary["rows"][0]
            self.assertEqual(row["recommended_action"], "COLLECT_TOP200_DIAG_LOG")
            self.assertEqual(row["branch_event_count"], 1)
            self.assertEqual(row["branch_candidate_event_count"], 0)
            self.assertIn("journey_branch_candidate_log_top_n=200", row["recommended_command"])

    @staticmethod
    def _write_results(path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["instance", "status", "wall_time", "node_count", "exact_pricing_calls"],
            )
            writer.writeheader()
            writer.writerows(rows)


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


if __name__ == "__main__":
    unittest.main()
