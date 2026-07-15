from __future__ import annotations

import random

from lunar_ice_bpc.domain import real_instance


def _candidate(index: int, role: str) -> dict[str, object]:
    return {
        "id": f"candidate_{index:03d}",
        "candidate_role": role,
        "hotspot_id": f"hotspot_{index:03d}",
        "hotspot_rank": index,
        "direction_sector": index % 8,
        "xy_km": [float(index % 10), float(index // 10)],
        "selection_score": 0.8 if role != "exploration" else 0.45,
        "resource_score": 0.75 if role != "exploration" else 0.38,
        "psr_interior_score": 0.7 if role == "hotspot_core" else 0.25,
        "psr_boundary_score": 0.8 if role == "hotspot_edge" else 0.3,
        "local_terrain_risk": 0.2,
        "local_shadow_score": 0.5,
    }


def test_hotspot_directional_sample_keeps_literal_exploration_role() -> None:
    targets = (
        [_candidate(index, "hotspot_core") for index in range(16)]
        + [_candidate(100 + index, "hotspot_edge") for index in range(4)]
        + [_candidate(200 + index, "exploration") for index in range(4)]
    )

    for seed in range(20):
        sampled = real_instance._hotspot_directional_sample(targets, 10, random.Random(seed), (0.0, 0.0))
        roles = {str(target.get("candidate_role", "")) for target in sampled}
        assert len(sampled) == 10
        assert "exploration" in roles


def test_missing_role_guard_runs_before_expensive_edge_build(monkeypatch) -> None:
    targets = [_candidate(index, "hotspot_core") for index in range(5)]
    preview = {
        "status": "REAL_MAP_PREVIEW_READY",
        "targets": targets,
        "depot": {"xy_km": [0.0, 0.0]},
    }
    monkeypatch.setattr(real_instance, "build_real_map_preview", lambda **_: preview)

    def fail_if_called(**_: object) -> list[dict[str, object]]:
        raise AssertionError("edge generation must not run when required candidate roles are missing")

    monkeypatch.setattr(real_instance, "build_real_map_edge_options", fail_if_called)

    instance = real_instance.generate_real_map_instance(5, raw_map_dir="data/raw_maps", seed=7)

    assert instance["validation"]["accepted"] is False
    assert instance["validation"]["reason"] == "sampled_candidate_roles_missing"
    assert instance["validation"]["missing_candidate_roles"] == ["hotspot_edge", "exploration"]
