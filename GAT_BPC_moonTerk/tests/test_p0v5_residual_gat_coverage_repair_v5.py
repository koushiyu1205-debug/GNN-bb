from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.manage_p0v5_residual_gat_coverage_census_v5 import (  # noqa: E402
    _build_corpus_rows, _split_payload, coverage_decision,
    select_eligible_new_candidates,
)
from scripts.p0v5_residual_gat_coverage_repair_v5_common import (  # noqa: E402
    assert_active, load, terminal, validate_v4_import,
)


CONFIG_PATH = (
    ROOT / "configs/experiments/"
    "p0v5_residual_gat_censor_aware_selector_v5.json"
)


def _candidate(index: int, eligible: bool) -> dict:
    return {
        "accepted_instance_index": index,
        "instance_content_hash": f"candidate-{index}",
        "screen_status": "ELIGIBLE" if eligible else "INELIGIBLE",
        "legal_snapshot_count": 1 if eligible else 0,
        "arm_outcomes_read": 0,
    }


def test_v5_real_v4_import_is_q0_only_and_has_frozen_counts():
    config = load(CONFIG_PATH)
    imported = validate_v4_import(config)
    assert imported["observed_counts"] == {
        "fixed_instances": 42,
        "fixed_snapshots": 94,
        "eligible_candidate_instances": 5,
        "eligible_candidate_snapshots": 11,
        "scale30_v4_eligible_instances": 1,
        "scale50_v4_eligible_instances": 4,
        "scale30_v4_screened_ineligible_instances": 3,
    }
    assert len(imported["snapshot_rows"]) == 105
    assert all(
        not ({"arm_outcome", "wall_ratio", "winner", "selected_action"} & set(load(
            row["source_snapshot_path"]
        )))
        for row in imported["snapshot_rows"]
    )
    assert load(imported["terminal_path"])["reason"] == (
        "INSUFFICIENT_FRESH_ROOT_COVERAGE"
    )


def test_v5_three_zero_context_v4_scale30_candidates_are_never_eligible():
    imported = validate_v4_import(load(CONFIG_PATH))
    ineligible = imported["screened_ineligible_instances"]
    assert len(ineligible) == 3
    assert {int(row["scale"]) for row in ineligible} == {30}
    eligible = imported["eligible_candidate_instances"]
    assert sum(int(row["scale"]) == 30 for row in eligible) == 1
    assert sum(int(row["scale"]) == 50 for row in eligible) == 4


def test_v5_selects_first_three_eligible_by_accepted_index_only():
    rows = [
        _candidate(5, True), _candidate(1, False), _candidate(3, True),
        _candidate(2, True), _candidate(4, True),
    ]
    selected = select_eligible_new_candidates(rows)
    assert [row["accepted_instance_index"] for row in selected] == [2, 3, 4]
    assert coverage_decision(rows) == "READY"
    # Fields forbidden as selection signals cannot change the deterministic result.
    for index, row in enumerate(reversed(rows)):
        row["wall_sec"] = 10_000 - index
        row["round"] = index
        row["active_column_density"] = index / 10
    assert [
        row["accepted_instance_index"]
        for row in select_eligible_new_candidates(list(reversed(rows)))
    ] == [2, 3, 4]


def test_v5_coverage_terminal_is_only_authorized_after_all_26_screened():
    rows = [_candidate(index, index in {2, 8}) for index in range(1, 26)]
    assert coverage_decision(rows) == "CONTINUE"
    rows.append(_candidate(26, False))
    assert coverage_decision(rows) == "EXHAUSTED"
    rows[-1] = _candidate(26, True)
    assert coverage_decision(rows) == "READY"


def test_v5_context_weight_is_one_per_instance_and_order_invariant():
    imported = validate_v4_import(load(CONFIG_PATH))
    task = imported["fixed_instances"][0]
    snapshots = [
        {**row, "snapshot_path": row["source_snapshot_path"]}
        for row in imported["snapshot_rows"]
        if row["instance_content_hash"] == task["instance_content_hash"]
    ]
    assert snapshots
    rows_a = _build_corpus_rows([("train", task, snapshots)])
    rows_b = _build_corpus_rows([("train", task, list(reversed(snapshots)))])
    assert sum(row["context_weight"] for row in rows_a) == pytest.approx(1.0)
    assert [(row["state_hash"], row["context_weight"]) for row in rows_a] == [
        (row["state_hash"], row["context_weight"]) for row in rows_b
    ]


def test_v5_split_rejects_cross_partition_instance():
    corpus = {
        "rows": [
            {"scale": 30, "partition": "train", "instance_content_hash": "same"},
            {"scale": 30, "partition": "calibration", "instance_content_hash": "same"},
        ]
    }
    with pytest.raises(SystemExit, match="split"):
        _split_payload(corpus)


def test_v5_terminal_guard_blocks_later_writers(tmp_path):
    state = {
        "schema_version": "test", "current_stage": "SCALE30_CANDIDATE_CENSUS",
        "status": "READY", "terminal": False, "terminal_decision": None,
    }
    (tmp_path / "state.json").write_text(json.dumps(state), encoding="utf-8")
    terminal(tmp_path, "INSUFFICIENT_SCALE30_HELDOUT_COVERAGE", {"observed": 2})
    with pytest.raises(SystemExit, match="terminal V5 chain"):
        assert_active(tmp_path)
    decision = load(tmp_path / "terminal_decision.json")
    assert decision["development_only"] is True
    assert decision["deployment_authorized"] is False


def test_v5_config_freezes_only_scale30_census_and_unchanged_runtime():
    config = load(CONFIG_PATH)
    assert config["candidate_scale"] == 30
    assert config["maximum_new_candidates"] == 26
    assert config["required_new_eligible_candidates"] == 3
    assert config["runtime_policy"] == "P0V5_ROOT_INTERACTION_GAT_SELECTOR_V4"
    assert config["expected_engine_hash"] == "3a2c89d88ca5b431"
    assert config["development_only"] is True
    assert config["deployment_authorized"] is False
    source = (ROOT / "scripts/manage_p0v5_residual_gat_coverage_census_v5.py").read_text()
    assert "--policy" not in source
    assert "arm_outcomes_read\": 0" in source
    assert "--route-opportunity-collection-only-root-pool" in source
