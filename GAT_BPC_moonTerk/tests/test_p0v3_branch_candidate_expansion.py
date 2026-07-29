from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
BASE = (
    ROOT
    / "data/gat_v3_branch_candidate_pool_20260725_content_manifest.json"
)
EXPANDED = (
    ROOT
    / "data/gat_v3_branch_candidate_pool_expanded_20260726_content_manifest.json"
)
SPLIT = (
    ROOT
    / (
        "data/gat_v3_branch_candidate_pool_expanded_20260726_"
        "grouped_split_manifest.json"
    )
)
SCHEDULER = (
    ROOT / "scripts/run_p0v3_branch_expansion_priority_census.py"
)
SPEC = importlib.util.spec_from_file_location(
    "p0v3_branch_expansion_priority_census",
    SCHEDULER,
)
assert SPEC is not None and SPEC.loader is not None
SCHEDULER_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCHEDULER_MODULE)
OPPORTUNITY = (
    ROOT / "scripts/run_p0_no_task_wait_v3_branch_opportunity_census.py"
)
OPPORTUNITY_SPEC = importlib.util.spec_from_file_location(
    "p0v3_branch_opportunity_census",
    OPPORTUNITY,
)
assert (
    OPPORTUNITY_SPEC is not None
    and OPPORTUNITY_SPEC.loader is not None
)
OPPORTUNITY_MODULE = importlib.util.module_from_spec(OPPORTUNITY_SPEC)
OPPORTUNITY_SPEC.loader.exec_module(OPPORTUNITY_MODULE)


def _cross_domain_builder_module():
    script = (
        ROOT
        / "scripts/build_p0v3_branch_cross_domain_content_manifest.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p0v3_branch_cross_domain_content",
        script,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _hashes(rows: list[dict]) -> set[str]:
    return {str(row["instance_content_hash"]) for row in rows}


def test_expansion_is_precommitted_and_preserves_locked_partitions() -> None:
    base = _load(BASE)
    expanded = _load(EXPANDED)
    base_development = list(base["development"])
    new_development = list(expanded["development"])
    expansion = new_development[len(base_development) :]

    assert expanded["audit"]["passed"] is True
    assert expanded["audit"]["collision_count"] == 0
    assert new_development[: len(base_development)] == base_development
    assert expanded["calibration"] == base["calibration"]
    assert expanded["protected_final_test"] == (
        base.get("protected_final_test") or []
    )
    assert len(expansion) == 120
    assert {
        scale: sum(int(row["scale"]) == scale for row in expansion)
        for scale in (20, 30)
    } == {20: 60, 30: 60}
    assert {
        scale: sum(
            int(row["scale"]) == scale
            and row["pool_role"] == "UNBIASED_EXPANSION_CENSUS"
            for row in expansion
        )
        for scale in (20, 30)
    } == {20: 12, 30: 12}
    assert all(
        row["expansion_precommitted_before_screening"] is True
        and row["v3_exact_actionability_status"] == "NOT_RUN"
        for row in expansion
    )


def test_expanded_grouped_split_has_no_partition_leakage() -> None:
    expanded = _load(EXPANDED)
    split = _load(SPLIT)
    development = list(split["development"])
    calibration = list(split["calibration"])
    development_hashes = _hashes(development)
    calibration_hashes = _hashes(calibration)

    assert split["audit"]["passed"] is True
    assert split["schema_version"] == (
        "lunar_ice_bpc.branch_grouped_split_manifest.v2"
    )
    assert split["audit"]["label_fields_used_for_assignment"] == []
    assert split["audit"]["protected_test_content_read"] is False
    assert split["calibration_read_authorized"] is False
    assert split["training_authorized"] is False
    assert split["opportunity_collection_authorized"] is True
    assert split["causal_oracle_collection_authorized"] is True
    assert set(split["authorized_collection_manifest_hashes"]) == {
        str(expanded["manifest_hash"]),
        str(expanded["base_content_manifest_hash"]),
    }
    assert development_hashes == _hashes(expanded["development"])
    assert calibration_hashes == _hashes(expanded["calibration"])
    assert development_hashes.isdisjoint(calibration_hashes)
    assert max(split["audit"]["fold_sizes"]) - min(
        split["audit"]["fold_sizes"]
    ) <= 1
    assert all(row["fold"] in range(5) for row in development)
    assert all(row["fold"] is None for row in calibration)
    assert {
        row["instance_generator_domain"] for row in development
    } == {"synthetic_polar_resource_grid_v1"}


def test_expansion_census_order_interleaves_scales_before_discovery() -> None:
    expanded = _load(EXPANDED)
    expansion = sorted(
        (
            row
            for row in expanded["development"]
            if row.get(
                "expansion_precommitted_before_screening"
            )
            is True
        ),
        key=SCHEDULER_MODULE._row_key,
    )

    assert [int(row["scale"]) for row in expansion[:24]] == [
        value for _ in range(12) for value in (20, 30)
    ]
    assert all(
        row["pool_role"] == "UNBIASED_EXPANSION_CENSUS"
        for row in expansion[:24]
    )
    assert all(
        "DISCOVERY_EXPANSION" in row["pool_role"]
        for row in expansion[24:]
    )


def test_cross_domain_pilot_freezes_three_plus_one_before_labels(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _cross_domain_builder_module()
    synthetic_path = tmp_path / "synthetic.json"
    generation_path = tmp_path / "generation.json"
    protected_path = tmp_path / "protected.json"
    output_path = tmp_path / "combined.json"
    synthetic_path.write_text(
        json.dumps(
            {
                "manifest_hash": "synthetic-current",
                "base_content_manifest_hash": "synthetic-base",
                "development": [
                    {"instance_content_hash": "synthetic-dev"}
                ],
                "calibration": [
                    {"instance_content_hash": "synthetic-cal"}
                ],
            }
        ),
        encoding="utf-8",
    )
    generation_path.write_text("{}", encoding="utf-8")
    protected_path.write_text(
        json.dumps(
            {
                "development": [
                    {"instance_content_hash": "old-dev"}
                ],
                "calibration": [
                    {"instance_content_hash": "old-cal"}
                ],
                "protected_final_test": [
                    {"instance_content_hash": "old-test"}
                ],
            }
        ),
        encoding="utf-8",
    )
    real_rows = {
        scale: [
            {
                "scale": scale,
                "instance_id": f"real-{scale}-{index}",
                "instance_path": f"/tmp/real-{scale}-{index}.json",
                "instance_content_hash": f"{scale}-{index}",
                "raw_file_sha256": f"raw-{scale}-{index}",
                "seed": index,
                "generator_attempt_index": index,
                "service_timing_policy_id": (
                    "no_task_wait_base_departure_shift_v1"
                ),
                "generator_schema_accepted": True,
                "v3_solver_reaccepted": False,
                "v3_exact_actionability_status": "NOT_RUN",
                "instance_generator_domain": (
                    "real_lunar_south_pole_sp50_benchmark_v1"
                ),
            }
            for index in range(4)
        ]
        for scale in (20, 30)
    }
    monkeypatch.setattr(module, "_real_rows", lambda _: real_rows)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(module.__file__),
            "--synthetic-content-manifest",
            str(synthetic_path),
            "--real-generation-manifest",
            str(generation_path),
            "--protected-manifest",
            str(protected_path),
            "--output-manifest",
            str(output_path),
        ],
    )

    assert module.main() == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    real_development = [
        row
        for row in payload["development"]
        if row.get("instance_generator_domain")
        == "real_lunar_south_pole_sp50_benchmark_v1"
    ]
    real_calibration = [
        row
        for row in payload["calibration"]
        if row.get("instance_generator_domain")
        == "real_lunar_south_pole_sp50_benchmark_v1"
    ]
    assert len(real_development) == 6
    assert len(real_calibration) == 2
    assert all(
        row["partition_frozen_before_branch_labels"] is True
        for row in real_development + real_calibration
    )
    without_hash = {
        key: value
        for key, value in payload.items()
        if key != "manifest_hash"
    }
    assert payload["manifest_hash"] == module._payload_sha256(
        without_hash
    )


def test_opportunity_census_can_isolate_real_map_domain() -> None:
    manifest = {
        "development": [
            {
                "scale": 20,
                "instance_content_hash": "b",
                "instance_generator_domain": (
                    "synthetic_polar_resource_grid_v1"
                ),
            },
            {
                "scale": 20,
                "instance_content_hash": "c",
                "instance_generator_domain": (
                    "real_lunar_south_pole_sp50_benchmark_v1"
                ),
            },
            {
                "scale": 20,
                "instance_content_hash": "a",
                "instance_generator_domain": (
                    "real_lunar_south_pole_sp50_benchmark_v1"
                ),
            },
        ]
    }
    rows = OPPORTUNITY_MODULE._development_rows(
        manifest,
        scale=20,
        instance_generator_domain=(
            "real_lunar_south_pole_sp50_benchmark_v1"
        ),
    )
    assert [
        row["instance_content_hash"] for row in rows
    ] == ["a", "c"]
