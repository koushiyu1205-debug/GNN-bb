from __future__ import annotations

import json
import shlex
import sys
import tempfile
import unittest
from pathlib import Path

from BPC_future.scripts.run_gat_target_priority_worker_ab_runbook import execute_runbook


class GATTargetPriorityWorkerABRunbookExecutorTests(unittest.TestCase):
    def test_executes_command_and_records_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            csv_path = tmp / "out" / "results.csv"
            runbook = _runbook(
                tmp,
                [
                    {
                        "command_type": "task020_success",
                        "command": _write_csv_command(csv_path),
                    }
                ],
            )

            summary = execute_runbook(
                runbook_summary=runbook,
                execution_log=tmp / "execution.jsonl",
                execution_summary=tmp / "execution_summary.json",
                max_workers=1,
                cwd=Path("."),
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["command_count"], 1)
            self.assertEqual(summary["executed_count"], 1)
            self.assertEqual(summary["failed_command_count"], 0)
            self.assertTrue(csv_path.exists())
            self.assertTrue((tmp / "execution.jsonl").exists())
            self.assertTrue((tmp / "execution_summary.json").exists())

    def test_skips_existing_result_when_requested(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            csv_path = tmp / "results.csv"
            csv_path.write_text("status\nOPTIMAL\n", encoding="utf-8")
            runbook = _runbook(
                tmp,
                [
                    {
                        "command_type": "task020_existing",
                        "command": _fail_command(csv_path),
                    }
                ],
            )

            summary = execute_runbook(
                runbook_summary=runbook,
                execution_log=tmp / "execution.jsonl",
                execution_summary=tmp / "execution_summary.json",
                max_workers=1,
                cwd=Path("."),
            )

            self.assertTrue(summary["all_checks_pass"])
            self.assertEqual(summary["executed_count"], 0)
            self.assertEqual(summary["skipped_existing_count"], 1)
            self.assertEqual(summary["failed_command_count"], 0)

    def test_records_failed_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            csv_path = tmp / "missing.csv"
            runbook = _runbook(
                tmp,
                [
                    {
                        "command_type": "task020_fail",
                        "command": _fail_command(csv_path),
                    }
                ],
            )

            summary = execute_runbook(
                runbook_summary=runbook,
                execution_log=tmp / "execution.jsonl",
                execution_summary=tmp / "execution_summary.json",
                max_workers=1,
                cwd=Path("."),
            )

            self.assertFalse(summary["all_checks_pass"])
            self.assertEqual(summary["executed_count"], 0)
            self.assertEqual(summary["failed_command_count"], 1)
            self.assertEqual(summary["failed_commands"][0]["command_type"], "task020_fail")


def _runbook(tmp: Path, commands: list[dict[str, str]]) -> Path:
    path = tmp / "summary.json"
    path.write_text(json.dumps({"commands": commands}, indent=2) + "\n", encoding="utf-8")
    return path


def _write_csv_command(csv_path: Path) -> str:
    code = (
        "import sys;"
        "from pathlib import Path;"
        "p=Path(sys.argv[sys.argv.index('--results-csv')+1]);"
        "p.parent.mkdir(parents=True, exist_ok=True);"
        "p.write_text('status\\nOPTIMAL\\n', encoding='utf-8')"
    )
    return " ".join(
        [
            shlex.quote(sys.executable),
            "-c",
            shlex.quote(code),
            "--results-csv",
            shlex.quote(str(csv_path)),
        ]
    )


def _fail_command(csv_path: Path) -> str:
    code = "import sys; sys.exit(7)"
    return " ".join(
        [
            shlex.quote(sys.executable),
            "-c",
            shlex.quote(code),
            "--results-csv",
            shlex.quote(str(csv_path)),
        ]
    )


if __name__ == "__main__":
    unittest.main()
