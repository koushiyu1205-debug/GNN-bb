from __future__ import annotations

import numpy as np

from lunar_ice_bpc.domain import real_maps


def test_real_map_edge_checkpoint_reuses_complete_source_groups(monkeypatch, tmp_path) -> None:
    surfaces = {
        "resource": np.zeros((5, 5), dtype=float),
        "elevation_m": np.zeros((5, 5), dtype=float),
        "elevation_available": True,
    }
    monkeypatch.setattr(
        real_maps,
        "build_real_map_surface_context",
        lambda **_: {"status": "REAL_MAP_SURFACES_READY", "surfaces": surfaces},
    )
    monkeypatch.setattr(real_maps, "_preview_cost_surfaces", lambda _: {"low_time": np.zeros((5, 5), dtype=float)})
    monkeypatch.setattr(
        real_maps,
        "_dijkstra_grid_paths_to_goals",
        lambda _surface, _start, goals, **_: {goal: [goal] for goal in goals},
    )
    calls: list[tuple[tuple[int, int], tuple[int, int]]] = []

    def build_options(*, start, goal, **_):
        calls.append((start, goal))
        return [{"path_type": path_type, "cells": [list(start), list(goal)]} for path_type in real_maps.PATH_TYPES]

    monkeypatch.setattr(real_maps, "_build_directed_path_options", build_options)
    nodes = {"depot": (0.0, 0.0), "task_1": (1.0, 1.0), "task_2": (2.0, 2.0)}
    checkpoint_dir = tmp_path / "checkpoint"

    first = real_maps.build_real_map_edge_options(
        raw_map_dir=tmp_path,
        nodes=nodes,
        extent_km=5.0,
        output_cells=5,
        checkpoint_dir=checkpoint_dir,
    )

    assert len(first) == 6
    assert len(calls) == 6
    assert len(list(checkpoint_dir.glob("source_*.json"))) == 3

    monkeypatch.setattr(
        real_maps,
        "_build_directed_path_options",
        lambda **_: (_ for _ in ()).throw(AssertionError("completed source checkpoint was not reused")),
    )
    second = real_maps.build_real_map_edge_options(
        raw_map_dir=tmp_path,
        nodes=nodes,
        extent_km=5.0,
        output_cells=5,
        checkpoint_dir=checkpoint_dir,
    )

    assert second == first


def test_batched_edge_generation_runs_one_multigoal_search_per_source_and_type(
    monkeypatch, tmp_path,
) -> None:
    surfaces = {
        "resource": np.zeros((5, 5), dtype=float),
        "elevation_m": np.zeros((5, 5), dtype=float),
        "elevation_available": True,
    }
    monkeypatch.setattr(
        real_maps,
        "build_real_map_surface_context",
        lambda **_: {"status": "REAL_MAP_SURFACES_READY", "surfaces": surfaces},
    )
    monkeypatch.setattr(
        real_maps, "_preview_cost_surfaces",
        lambda _: {
            path_type: np.zeros((5, 5), dtype=float)
            for path_type in real_maps.PATH_TYPES
        },
    )
    searches = []

    def paths(_surface, start, goals, *, path_type, **_):
        searches.append((start, path_type, tuple(goals)))
        return {goal: [start, goal] for goal in goals}

    monkeypatch.setattr(real_maps, "_dijkstra_grid_paths_to_goals", paths)
    builds = []

    def build_options(*, path_overrides, apply_diversity_penalty, **_):
        builds.append((set(path_overrides), apply_diversity_penalty))
        return [
            {"path_type": path_type, "path_options": []}
            for path_type in real_maps.PATH_TYPES
        ]

    monkeypatch.setattr(real_maps, "_build_directed_path_options", build_options)
    nodes = {
        "depot": (0.0, 0.0), "task_1": (1.0, 1.0),
        "task_2": (2.0, 2.0),
    }
    edges = real_maps.build_real_map_edge_options(
        raw_map_dir=tmp_path, nodes=nodes, extent_km=5.0,
        output_cells=5, edge_generation_mode="batched_cost_surface_v1",
    )
    assert len(edges) == 6
    assert len(searches) == len(nodes) * len(real_maps.PATH_TYPES)
    assert {row[1] for row in searches} == set(real_maps.PATH_TYPES)
    assert builds == [(set(real_maps.PATH_TYPES), False)] * 6
