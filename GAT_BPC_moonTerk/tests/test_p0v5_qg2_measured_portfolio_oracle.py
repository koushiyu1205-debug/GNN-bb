from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/summarize_p0v5_qg2_measured_portfolio_oracle.py"
SPEC = importlib.util.spec_from_file_location("qg2_portfolio_oracle", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _replay(*, wall: float, reached: bool = True, milestone: str = "ADMISSION_BATCH_READY") -> dict:
    return {
        "schema_version": "replay.v1",
        "source_state_hash": "a" * 64,
        "instance_content_hash": "instance-hash",
        "source_backend_id": "backend",
        "source_config_hash": "config",
        "source_engine_hash": "engine",
        "source_exact_action_policy_hash": "policy",
        "replay_engine_hash": "replay",
        "milestone_kind": milestone if reached else "RIGHT_CENSORED",
        "milestone_reached": reached,
        "milestone_wall_sec": wall,
        "admission_milestone_wall_sec": wall if reached else None,
        "total_fresh_process_wall_sec": wall,
        "search_exhaustive": False,
        "labels_dropped": False,
        "proof_telemetry": {
            "legal_action_universe_hash_before_sort": "actions",
            "legal_arc_universe_hash_before_sort": "arcs",
            "guidance_filter_count": 0,
            "guidance_arc_drop_count": 0,
            "guidance_label_drop_count": 0,
            "guidance_branch_pair_drop_count": 0,
        },
    }


def test_best_of_arms_separates_qg2_reachable_from_broader_portfolio(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    oracle_dir = run_root / "oracle"
    state = "a" * 16
    context = oracle_dir / f"30_{state}"
    context.mkdir(parents=True)
    (run_root / "qg2_clean_v2_live_snapshot_index.json").write_text(
        __import__("json").dumps({"rows": [{
            "scale": 30,
            "state_hash": "a" * 64,
            "instance_hash": "instance-hash",
            "instance_id": "instance-001",
            "pricing_lifecycle_scope": "root_cg",
            "round": 30,
            "previous_q0_wall_stratum": "60to300",
        }]}), encoding="utf-8"
    )
    walls = {
        "Q0": 100.0,
        "QD1": 90.0,
        "QB1": 10.0,
        "QO2-1e-4": 95.0,
        "QO2-3e-4": 93.0,
        "QO2-1e-3": 80.0,
    }
    import json
    for arm, wall in walls.items():
        (context / MODULE.live.ARM_FILES[arm]).write_text(
            json.dumps(_replay(wall=wall)), encoding="utf-8"
        )

    report = MODULE.collect(
        run_root=run_root,
        oracle_dir=oracle_dir,
        maximum_contexts=2,
        maximum_contexts_per_scale=1,
    )

    assert report["context_count"] == 1
    row = report["contexts"][0]
    assert row["qg2_reachable_best_arm"] == "QO2-1e-3"
    assert row["qg2_reachable_ratio"] == 0.8
    assert row["portfolio_best_arm"] == "QB1"
    assert row["portfolio_ratio"] == 0.1
    assert row["qg2_captured_portfolio_savings_fraction"] == 2.0 / 9.0


def test_right_censored_and_unsafe_arms_cannot_win() -> None:
    control = _replay(wall=100.0)
    censored = _replay(wall=5.0, reached=False)
    unsafe = _replay(wall=1.0)
    unsafe["proof_telemetry"]["guidance_label_drop_count"] = 1

    assert MODULE._arm_ineligible_reason(control, censored) == (
        "right_censored_or_milestone_not_reached"
    )
    assert MODULE._arm_ineligible_reason(control, unsafe) == (
        "exact_safe_audit_failed"
    )

    drifted = _replay(wall=1.0)
    drifted["source_config_hash"] = "different"
    assert MODULE._arm_ineligible_reason(control, drifted) == (
        "execution_binding_mismatch"
    )


def test_aggregate_reports_action_surface_gap_and_winner_counts() -> None:
    rows = [{
        "scale": 50,
        "milestone": "ADMISSION_BATCH_READY",
        "instance_hash": "i1",
        "q0_wall_sec": 100.0,
        "qg2_reachable_best_wall_sec": 80.0,
        "portfolio_best_wall_sec": 10.0,
        "qg2_reachable_ratio": 0.8,
        "portfolio_ratio": 0.1,
        "qg2_reachable_best_arm": "QO2-1e-3",
        "portfolio_best_arm": "QB1",
    }]

    aggregate = MODULE._aggregate_rows(rows)

    assert aggregate["qg2_action_surface_gap_sec"] == 70.0
    assert aggregate["captured_savings_fraction"] == 2.0 / 9.0
    assert aggregate["qg2_reachable_winner_counts"] == {"QO2-1e-3": 1}
    assert aggregate["portfolio_winner_counts"] == {"QB1": 1}
