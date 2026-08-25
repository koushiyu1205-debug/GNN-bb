from __future__ import annotations

import copy

import pytest

from scripts.audit_p0v5_temporal_frontier_late_switch_v10r1 import (
    boundary_failures,
    corrected_gate,
    corrected_metrics,
    restore_instance_identity,
)


def _row(context: str, scale: int, boundary: int, ratio: float) -> dict:
    return {
        "context_id": context,
        "scale": scale,
        "decision_boundary": boundary,
        "instance_hash": None,
        "determined": True,
        "probe_ratio": 1.0,
        "net_ratio": ratio,
        "resource_censor_positive": False,
        "correctness_redlines": [],
    }


def _config() -> dict:
    return {
        "decision_boundaries": {"30": [4096], "50": [16384]},
        "probe_overhead_gate": {
            "gm_at_most": 1.01,
            "worst_ratio_at_most": 1.05,
        },
        "scale30_gate": {
            "fixed_qpd1_net_gm_at_most": 0.98,
            "minimum_determined_instances": 2,
            "minimum_qpd1_winner_instances": 2,
            "net_oracle_gm_at_most": 0.95,
        },
        "scale50_boundary_gate": {
            "minimum_determined_instances": 3,
            "minimum_neutral_or_harm_instances": 1,
            "minimum_qpd1_winner_instances": 2,
            "minimum_strong_benefit_instances": 2,
            "net_oracle_gm_at_most": 0.95,
        },
    }


def test_restore_identity_uses_preoutcome_corpus_not_missing_metadata() -> None:
    rows = [_row("c1", 30, 4096, 0.8), _row("c2", 30, 4096, 0.9)]
    corpus = [
        {"context_id": "c1", "scale": 30, "instance_content_hash": "i1"},
        {"context_id": "c2", "scale": 30, "instance_content_hash": "i2"},
    ]
    restored = restore_instance_identity(rows, corpus)
    assert [row["instance_hash"] for row in restored] == ["i1", "i2"]
    assert corrected_metrics(restored)["determined_instances"] == 2


def test_context_replication_does_not_increase_instance_counts() -> None:
    rows = [
        {**_row("c1", 50, 16384, 0.90), "instance_hash": "i1"},
        {**_row("c2", 50, 16384, 0.99), "instance_hash": "i1"},
        {**_row("c3", 50, 16384, 1.10), "instance_hash": "i2"},
    ]
    metrics = corrected_metrics(rows)
    assert metrics["determined_contexts"] == 3
    assert metrics["determined_instances"] == 2
    assert metrics["qpd1_winner_instances"] == 1
    assert metrics["harm_instances"] == 1


def test_scale50_oracle_headroom_does_not_bypass_support_gate() -> None:
    config = _config()
    rows = [
        {**_row("a", 50, 16384, 0.40), "instance_hash": "a"},
        {**_row("b", 50, 16384, 0.97), "instance_hash": "b"},
        {**_row("c", 50, 16384, 1.10), "instance_hash": "c"},
    ]
    metrics = corrected_metrics(rows)
    assert metrics["net_oracle_gm"] < 0.95
    failures = boundary_failures(50, metrics, config)
    assert failures == ["minimum_strong_benefit_instances"]


def test_corrected_gate_requires_both_scales() -> None:
    config = _config()
    rows = [
        {**_row("s30a", 30, 4096, 0.80), "instance_hash": "s30a"},
        {**_row("s30b", 30, 4096, 0.90), "instance_hash": "s30b"},
        {**_row("s50a", 50, 16384, 0.40), "instance_hash": "s50a"},
        {**_row("s50b", 50, 16384, 0.97), "instance_hash": "s50b"},
        {**_row("s50c", 50, 16384, 1.10), "instance_hash": "s50c"},
    ]
    decision = corrected_gate(config, rows)
    assert decision["passing_boundaries"]["30"] == [4096]
    assert decision["passing_boundaries"]["50"] == []
    assert decision["decision"] == "FAIL"
    assert decision["reason"] == "SCALE50_LATE_SWITCH_SUPPORT_GATE_FAILED"
    assert decision["temporal_gat_training_authorized"] is False


def test_restore_identity_rejects_partition_drift() -> None:
    row = _row("c1", 30, 4096, 0.8)
    corpus = [{
        "context_id": "c1", "scale": 50, "instance_content_hash": "i1",
    }]
    with pytest.raises(ValueError, match="scale drift"):
        restore_instance_identity([copy.deepcopy(row)], corpus)
