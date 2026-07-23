from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def _module():
    path = ROOT / "scripts/run_live_sri_paired_promotion.py"
    spec = importlib.util.spec_from_file_location("live_sri_promotion_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bootstrap_uses_exactly_requested_sample_count() -> None:
    module = _module()
    original = module.geometric_mean
    with patch.object(module, "geometric_mean", wraps=original) as wrapped:
        lower, upper = module.bootstrap_geometric_mean_ci(
            [0.8, 0.9, 1.0], samples=137, seed=1
        )
    assert wrapped.call_count == 137
    assert lower is not None and upper is not None and lower <= upper


def _formal_fixture(module):
    schedule = []
    rows = []
    references = {}
    engine_hash = "engine-v1"
    policy_hash = "policy-v1"
    no_cut_policy_hash = "no-cut-policy-v1"
    for scale in module.FORMAL_SCALES:
        repeats = (
            module.SMALL_SCALE_REPEATS
            if scale in {5, 10}
            else module.LARGE_SCALE_REPEATS
        )
        live_ratio = 0.99 if scale in {5, 10} else 0.8
        for instance_index in range(module.EXPECTED_INSTANCE_COUNT):
            instance_key = f"instance_{instance_index + 1:03d}"
            references[(scale, instance_key)] = float(scale + instance_index)
            for repetition in range(1, repeats + 1):
                order = (
                    ("no_cut", "live")
                    if (instance_index + repetition) % 2 == 1
                    else ("live", "no_cut")
                )
                for order_index, mode in enumerate(order, start=1):
                    slot_id = (
                        f"s{scale:03d}:{instance_key}:r{repetition:02d}:"
                        f"o{order_index}:{mode}"
                    )
                    base = {
                        "slot_id": slot_id,
                        "scale": scale,
                        "instance_key": instance_key,
                        "repetition": repetition,
                        "order": "/".join(order),
                        "order_index": order_index,
                        "mode": mode,
                    }
                    schedule.append(dict(base))
                    rows.append(
                        {
                            **base,
                            "exact": True,
                            "redlines_zero": True,
                            "engine_hash_valid": True,
                            "engine_build_hash": engine_hash,
                            "certificate_scope": "BPC_TREE_OPTIMAL",
                            "all_certificate_ledgers_valid": True,
                            "all_node_lower_bounds_official": True,
                            "all_node_pricing_proofs_certifying": True,
                            "tree_certificate_gate_issues": [],
                            "live_sri_policy_name": "P0" if mode == "live" else "no_cut",
                            "live_cut_policy_hash": (
                                policy_hash if mode == "live" else no_cut_policy_hash
                            ),
                            "certificate_leak": 0,
                            "pricing_rc_fail": 0,
                            "manual_rc_fail": 0,
                            "no_cheat_pass": True,
                            "same_run_checkpoint_resume_used": False,
                            "external_probe_used": False,
                            "mature_pool_used": False,
                            "manual_columns_used": False,
                            "row_budget_exhausted": False,
                            "launcher_termination_reason": "",
                            "objective": references[(scale, instance_key)],
                            "cold_start_total_sec": (
                                1.0 if mode == "no_cut" else live_ratio
                            ),
                        }
                    )
    return schedule, rows, references, engine_hash, policy_hash, no_cut_policy_hash


def test_formal_summary_requires_every_slot_and_every_correctness_binding() -> None:
    module = _module()
    (
        schedule,
        rows,
        references,
        engine_hash,
        policy_hash,
        no_cut_policy_hash,
    ) = _formal_fixture(module)
    assert len(schedule) == 1040

    passed = module.summarize_promotion(
        rows,
        schedule=schedule,
        reference_objectives=references,
        expected_engine_hash=engine_hash,
        expected_policy_hash=policy_hash,
        expected_no_cut_policy_hash=no_cut_policy_hash,
        bootstrap_samples=100,
        dry_run=False,
    )
    assert passed["formal_design_complete"]
    assert passed["all_scales_promoted"]
    assert all(
        scale_row["correctness_gate"]
        for scale_row in passed["scale_summary"].values()
    )

    missing = module.summarize_promotion(
        rows[:-1],
        schedule=schedule,
        reference_objectives=references,
        expected_engine_hash=engine_hash,
        expected_policy_hash=policy_hash,
        expected_no_cut_policy_hash=no_cut_policy_hash,
        bootstrap_samples=100,
        dry_run=False,
    )
    assert not missing["formal_design_complete"]
    assert not missing["default_switch_allowed"]

    rows[0]["same_run_checkpoint_resume_used"] = True
    invalid = module.summarize_promotion(
        rows,
        schedule=schedule,
        reference_objectives=references,
        expected_engine_hash=engine_hash,
        expected_policy_hash=policy_hash,
        expected_no_cut_policy_hash=no_cut_policy_hash,
        bootstrap_samples=100,
        dry_run=False,
    )
    assert invalid["formal_design_complete"]
    assert not invalid["scale_summary"]["5"]["correctness_gate"]
    assert not invalid["default_switch_allowed"]


def test_objective_audit_matches_six_decimal_frozen_references() -> None:
    module = _module()
    (
        _schedule,
        rows,
        _references,
        engine_hash,
        policy_hash,
        no_cut_policy_hash,
    ) = _formal_fixture(module)
    row = dict(rows[0])
    row["objective"] = 1.636391

    assert module.row_correctness_basics(
        row,
        expected_engine_hash=engine_hash,
        expected_policy_hash=policy_hash,
        expected_no_cut_policy_hash=no_cut_policy_hash,
        reference_objective=1.636390,
    )

    row["objective"] = 1.6363911
    assert not module.row_correctness_basics(
        row,
        expected_engine_hash=engine_hash,
        expected_policy_hash=policy_hash,
        expected_no_cut_policy_hash=no_cut_policy_hash,
        reference_objective=1.636390,
    )


def test_single_repeat_benchmark_is_complete_but_cannot_promote() -> None:
    module = _module()
    (
        formal_schedule,
        formal_rows,
        references,
        engine_hash,
        policy_hash,
        no_cut_policy_hash,
    ) = _formal_fixture(module)
    schedule = [
        row for row in formal_schedule if int(row["repetition"]) == 1
    ]
    slot_ids = {str(row["slot_id"]) for row in schedule}
    rows = [row for row in formal_rows if str(row["slot_id"]) in slot_ids]

    summary = module.summarize_promotion(
        rows,
        schedule=schedule,
        reference_objectives=references,
        expected_engine_hash=engine_hash,
        expected_policy_hash=policy_hash,
        expected_no_cut_policy_hash=no_cut_policy_hash,
        bootstrap_samples=100,
        repeats_small=1,
        repeats_large=1,
        benchmark_only=True,
        dry_run=False,
    )

    assert summary["status"] == "BENCHMARK_COMPLETE"
    assert summary["paired_design_complete"]
    assert summary["benchmark_complete"]
    assert not summary["formal_design_complete"]
    assert not summary["all_scales_promoted"]
    assert not summary["default_switch_allowed"]
