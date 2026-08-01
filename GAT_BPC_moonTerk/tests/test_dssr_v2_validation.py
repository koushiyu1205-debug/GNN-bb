from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dssr_v2_split_manifest_is_content_hash_disjoint() -> None:
    manifest = json.loads(
        (
            ROOT
            / "data"
            / "manifests"
            / "dssr_v2_validation_split_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["status"] == "LOCKED"
    assert manifest["assignment_unit"] == "instance_content_hash"
    development = manifest["development"]
    locked = manifest["locked_test"]
    development_hashes = {
        row["instance_content_hash"] for row in development
    }
    locked_hashes = {
        row["instance_content_hash"] for row in locked
    }
    assert len(development) == 54
    assert len(locked) == 36
    assert len(development_hashes) == len(development)
    assert len(locked_hashes) == len(locked)
    assert development_hashes.isdisjoint(locked_hashes)
    assert manifest["audit"]["formal_or_prior_protected_overlap_count"] == 0
    assert manifest["audit"]["locked_test_used_for_selection"] is False


def test_dssr_v2_candidate_keeps_tree_round_cap_and_all_scale_policy() -> None:
    config = yaml.safe_load(
        (
            ROOT / "configs" / "dssr_v2_candidate_base.yaml"
        ).read_text(encoding="utf-8")
    )
    assert config["model_id"] == "DSSR_V2_DETERMINISTIC_CANDIDATE"
    assert (
        config["dssr_policy_version"]
        == "multi_sortie_counterexample_pressure_refinement_v2"
    )
    assert config["dssr_pressure_refinement_enabled"] is True
    assert set(map(int, config["profiles"])) == {5, 10, 20, 30, 50, 100}
    assert all(
        int(profile["tree_max_rounds"]) == 16
        for profile in config["profiles"].values()
    )
    assert float(config["profiles"]["50"]["memory_limit_gb"]) <= 8.0
    assert float(config["profiles"]["100"]["memory_limit_gb"]) <= 8.0


def test_snapshot_grid_hard_regression_gate_blocks_slow_scale20() -> None:
    module = _load_script("run_dssr_v2_snapshot_grid.py")
    row = {
        "scale": 20,
        "instance_id": "lunar_ice_sp50_020_011_seed829011",
        "dssr_success": True,
        "extra_incomplete": False,
        "safety_pass": True,
        "wall_ratio": 1.11,
        "dssr_max_bucket_size": 5_853,
        "dssr_dominance_candidate_checks": 4_640_141_693,
    }
    assert module._scale20_011_gate([row]) is False
    row["wall_ratio"] = 1.10
    assert module._scale20_011_gate([row]) is True


def test_snapshot_grid_selection_is_lexicographic_and_freeze_fail_closed() -> None:
    module = _load_script("run_dssr_v2_snapshot_grid.py")
    rows = []
    for config_id, ratio in (("fast_unsafe", 0.5), ("safe", 0.9)):
        rows.append(
            {
                "config_id": config_id,
                "bucket_limit": 4096,
                "candidate_check_limit": 50_000_000,
                "scale": 20,
                "instance_id": "lunar_ice_sp50_020_011_seed829011",
                "status": "PASS",
                "p0_success": True,
                "dssr_success": True,
                "extra_incomplete": False,
                "safety_pass": config_id == "safe",
                "p0_wall_sec": 10.0,
                "dssr_wall_sec": 10.0 * ratio,
                "wall_ratio": ratio,
                "peak_rss_bytes": 100,
                "dssr_pressure_refinement_count": 1,
                "dssr_max_bucket_size": 100,
                "dssr_dominance_candidate_checks": 100,
            }
        )
    summary = module._summarize(
        rows,
        expected=1,
        expected_configurations=2,
    )
    assert summary["status"] == "COMPLETE"
    assert summary["selected_configuration"]["config_id"] == "safe"
    # A partial scale20-only screen cannot authorize a freeze because all five
    # scale30 sentinels have not exact-closed under the same configuration.
    assert summary["regression_gate_pass"] is False
    assert summary["freeze_allowed"] is False
    assert math.isfinite(
        summary["selected_configuration"]["worst_scale_geometric_mean"]
    )


def test_paired_gate_authorizes_gat_only_after_locked_six_scale_pass() -> None:
    module = _load_script("run_dssr_v2_paired_validation.py")
    rows = []
    expected = []
    for scale in (5, 10, 20, 30, 50, 100):
        spec = {
            "scale": scale,
            "instance_content_hash": f"hash{scale}",
        }
        expected.append(spec)
        rows.append(
            {
                **spec,
                "pair_id": module._pair_id(spec),
                "safety_pass": True,
                "extra_incomplete": False,
                "objective_match": True,
                "wall_ratio": 1.0,
                "control": {
                    "status": "EXACT_CLOSED",
                    "cold_start_total_sec": 10.0,
                },
                "candidate": {
                    "status": "EXACT_CLOSED",
                    "cold_start_total_sec": 10.0,
                    "peak_process_tree_rss_gb": 1.0,
                    "root_exact_closed": True,
                },
            }
        )
    development = module._summarize(
        rows,
        expected=expected,
        partition="development",
        full_design=True,
        elapsed_sec=1.0,
        pregrid_smoke=False,
    )
    assert development["status"] == "PASS"
    assert development["freeze_allowed"] is True
    assert development["gat_oracle_allowed"] is False
    locked = module._summarize(
        rows,
        expected=expected,
        partition="locked_test",
        full_design=True,
        elapsed_sec=1.0,
        pregrid_smoke=False,
    )
    assert locked["status"] == "PASS"
    assert locked["promotion_allowed"] is True
    assert locked["gat_oracle_allowed"] is True


def test_candidate_freeze_rejects_locked_data_leak_and_hash_drift(
    tmp_path: Path,
) -> None:
    module = _load_script("freeze_dssr_v2_candidate.py")
    config = tmp_path / "config.yaml"
    native = tmp_path / "native.so"
    grid_path = tmp_path / "grid.json"
    split_path = tmp_path / "split.json"
    for path, content in (
        (config, "config"),
        (native, "native"),
        (grid_path, "{}"),
        (split_path, "{}"),
    ):
        path.write_text(content, encoding="utf-8")
    issues = module._freeze_issues(
        grid={"freeze_allowed": True},
        development={
            "schema_version": (
                "lunar_ice_bpc.dssr_v2_paired_validation.v1"
            ),
            "partition": "development",
            "freeze_allowed": True,
        },
        development_preflight={},
        split={
            "status": "LOCKED",
            "audit": {"locked_test_used_for_selection": True},
        },
        config=config,
        native_module=native,
        grid_path=grid_path,
        split_path=split_path,
    )
    assert "locked_test_leak" in issues
    assert any(issue.endswith("_mismatch") for issue in issues)
