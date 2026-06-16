from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from BPC_future.scripts.audit_gat_batch_impact_cross_checkpoint_selector import (
    audit_cross_checkpoint_selector,
)


class GATBatchImpactCrossCheckpointSelectorTests(unittest.TestCase):
    def test_audit_evaluates_fixed_hybrid_rules_without_pricing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            v18_summary = _write_source(
                tmp,
                "v18",
                [
                    _record("sector-wave", "ctx-a", roi=2.0, accepted=True),
                    _record("random-wave", "ctx-b", roi=1.0, accepted=True),
                    _record("greedy-anchor", "ctx-c", roi=0.1, accepted=True),
                    _record("sector-wave", "ctx-d", roi=0.0, accepted=False, delay=True),
                ],
            )
            v19_summary = _write_source(
                tmp,
                "v19",
                [
                    _record("sector-wave", "ctx-a", roi=2.0, accepted=True),
                    _record("random-wave", "ctx-b", roi=1.0, accepted=True),
                    _record("greedy-anchor", "ctx-c", roi=0.1, accepted=False),
                    _record("sector-wave", "ctx-d", roi=0.0, accepted=False, delay=True),
                ],
            )

            summary = audit_cross_checkpoint_selector(
                sources=[("v18", v18_summary), ("v19", v19_summary)],
                output_dir=tmp / "out",
                report=tmp / "report.md",
            )
            self.assertTrue(Path(summary["rule_metrics_path"]).exists())
            rules = {
                row["rule"]: row
                for row in _read_jsonl(Path(summary["rule_metrics_path"]))
            }

        self.assertTrue(summary["all_checks_pass"])
        self.assertFalse(summary["runs_bpc_or_pricing"])
        self.assertFalse(summary["selector_can_certificate"])
        self.assertEqual(summary["validation_record_count"], 4)
        self.assertEqual(rules["v18_selected"]["accepted_batch_count"], 3)
        self.assertEqual(rules["v18_no_greedy_anchor"]["accepted_batch_count"], 2)
        self.assertEqual(
            rules["v18_sector_plus_v19_random"]["accepted_high_roi_opportunities"],
            2,
        )

    def test_key_mismatch_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            v18_summary = _write_source(
                tmp,
                "v18",
                [_record("sector-wave", "ctx-a", roi=2.0, accepted=True)],
            )
            v19_summary = _write_source(
                tmp,
                "v19",
                [_record("sector-wave", "ctx-b", roi=2.0, accepted=True)],
            )
            with self.assertRaisesRegex(ValueError, "key mismatch"):
                audit_cross_checkpoint_selector(
                    sources=[("v18", v18_summary), ("v19", v19_summary)],
                    output_dir=tmp / "out",
                    report=tmp / "report.md",
                )


def _write_source(
    tmp: Path,
    label: str,
    records: list[dict[str, object]],
) -> Path:
    source_dir = tmp / label
    source_dir.mkdir()
    records_path = source_dir / "validation_opportunities.jsonl"
    _write_jsonl(records_path, records)
    summary_path = source_dir / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "schema_version": "gat_batch_impact_opportunity_mining_v1",
                "validation_opportunities_path": str(records_path),
                "gate_config": {
                    "confidence_z": 1.96,
                    "min_safe_precision_ci_low": 0.5,
                    "min_accepted_batch_roi": 0.65,
                    "min_accepted_batch_roi_ci_low": 0.0,
                    "max_false_safe_union_rate": 0.02,
                },
                "production_ready": False,
                "runs_bpc_or_pricing": False,
                "selector_can_certificate": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return summary_path


def _record(
    family: str,
    context: str,
    *,
    roi: float,
    accepted: bool,
    delay: bool = False,
) -> dict[str, object]:
    return {
        "accepted": accepted,
        "accepted_batch_roi_label": roi,
        "bad_mode_switch": 0,
        "context_hash": context,
        "delay_candidate_label_count": int(delay),
        "family": family,
        "instance_path": f"{family}/{context}.json",
        "is_high_roi_opportunity": roi >= 0.65,
        "predicted_delay_candidate_count": int(delay and accepted),
        "region": "region",
        "task_count": 20,
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


if __name__ == "__main__":
    unittest.main()
