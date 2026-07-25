from __future__ import annotations

import pytest

from lunar_ice_bpc.exact.bpc.solver.branch_tree_solver import (
    _branch_candidate_id,
    _selected_fractional_candidate,
)


def _node(candidate_count: int) -> dict:
    return {
        "fractional_branch_probe": {
            "candidates": [
                {
                    "task_a": f"task_{index:02d}",
                    "task_b": f"task_{index + 1:02d}",
                }
                for index in range(candidate_count)
            ]
        }
    }


def test_development_branch_rank_selects_only_inside_existing_shortlist() -> None:
    candidate, selected_rank, fallback = _selected_fractional_candidate(
        _node(3),
        requested_rank_index=2,
    )
    assert candidate == {"task_a": "task_02", "task_b": "task_03"}
    assert selected_rank == 2
    assert fallback is False


def test_development_branch_rank_falls_back_to_p0_when_rank_is_missing() -> None:
    candidate, selected_rank, fallback = _selected_fractional_candidate(
        _node(1),
        requested_rank_index=2,
    )
    assert candidate == {"task_a": "task_00", "task_b": "task_01"}
    assert selected_rank == 0
    assert fallback is True

    missing, missing_rank, missing_fallback = (
        _selected_fractional_candidate(
            _node(0),
            requested_rank_index=2,
        )
    )
    assert missing is None
    assert missing_rank is None
    assert missing_fallback is False


def test_development_branch_rank_rejects_out_of_universe_rank() -> None:
    with pytest.raises(ValueError, match="one of 0, 1, or 2"):
        _selected_fractional_candidate(
            _node(3),
            requested_rank_index=3,
        )


def test_branch_candidate_id_is_pair_symmetric() -> None:
    assert _branch_candidate_id(
        {"task_a": "right", "task_b": "left"}
    ) == _branch_candidate_id(
        {"task_a": "left", "task_b": "right"}
    )
    with pytest.raises(ValueError, match="invalid task pair"):
        _branch_candidate_id({"task_a": "same", "task_b": "same"})
