from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "scripts/run_p0_no_task_wait_v3_branch_priority_screen.py"
)
SPEC = importlib.util.spec_from_file_location(
    "p0_no_task_wait_v3_branch_priority_screen",
    SCRIPT,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_priority_key_prefers_top3_then_fractionality_without_scalar_mix() -> None:
    top3 = [
        {"fractionality": 0.4},
        {"fractionality": 0.3},
        {"fractionality": 0.2},
    ]
    top2 = [
        {"fractionality": 0.5},
        {"fractionality": 0.5},
    ]

    key_top3 = MODULE._priority_key(
        candidates=top3,
        active_column_count=100,
        final_round_added_column_count=4,
        instance_content_hash="b",
    )
    key_top2 = MODULE._priority_key(
        candidates=top2,
        active_column_count=1000,
        final_round_added_column_count=0,
        instance_content_hash="a",
    )

    assert key_top3 < key_top2
    assert key_top3 == (0, -0.9, 4, -100, "b")


def test_priority_key_is_content_hash_deterministic_on_tie() -> None:
    common = {
        "candidates": [],
        "active_column_count": 10,
        "final_round_added_column_count": 1,
    }

    assert MODULE._priority_key(
        **common,
        instance_content_hash="a",
    ) < MODULE._priority_key(
        **common,
        instance_content_hash="b",
    )


def test_exploration_quota_is_nonzero() -> None:
    assert 0.0 < MODULE.DEFAULT_EXPLORATION_QUOTA < 1.0


def test_priority_key_keeps_frontier_saturation_as_explicit_field() -> None:
    key = MODULE._priority_key(
        candidates=[{"fractionality": 0.5}] * 3,
        active_column_count=100,
        final_round_added_column_count=5,
        instance_content_hash="a",
    )

    assert key[2] == 5


def test_active_baseline_binding_requires_unique_engine_hash() -> None:
    registry = {
        "active_experiment_baseline_id": MODULE.BASELINE_ID,
        "baselines": [
            {
                "freeze_id": MODULE.BASELINE_ID,
                "engine_hash": "engine",
            }
        ],
    }

    binding = MODULE._active_baseline_binding(registry)

    assert binding["baseline_id"] == MODULE.BASELINE_ID
    assert binding["engine_hash"] == "engine"
