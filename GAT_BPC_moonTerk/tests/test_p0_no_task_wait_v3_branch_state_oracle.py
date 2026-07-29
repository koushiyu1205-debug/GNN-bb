from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT / "scripts/run_p0_no_task_wait_v3_branch_state_oracle.py"
)
SPEC = importlib.util.spec_from_file_location(
    "p0_no_task_wait_v3_branch_state_oracle",
    SCRIPT,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

CENSUS_SCRIPT = (
    ROOT / "scripts/run_p0_no_task_wait_v3_branch_opportunity_census.py"
)
CENSUS_SPEC = importlib.util.spec_from_file_location(
    "p0_no_task_wait_v3_branch_opportunity_census",
    CENSUS_SCRIPT,
)
assert CENSUS_SPEC is not None and CENSUS_SPEC.loader is not None
CENSUS_MODULE = importlib.util.module_from_spec(CENSUS_SPEC)
CENSUS_SPEC.loader.exec_module(CENSUS_MODULE)


def _branch_node(*, path: list[str], selected_rank: int = 0) -> dict:
    return {
        "node_id": "node_007",
        "node_status": "BRANCHED",
        "depth": len(path),
        "development_branch_path_signature": path,
        "development_branch_selected_rank_index": selected_rank,
        "legal_branch_shortlist_hash_before_sort": "same",
        "legal_branch_shortlist_hash_after_sort": "same",
        "guidance_branch_pair_drop_count": 0,
        "tree_elapsed_sec_at_exit": 4.0,
        "fractional_branch_probe": {
            "candidate_count": 7,
            "candidates": [
                {"task_a": "a", "task_b": "b"},
                {"task_a": "b", "task_b": "c"},
                {"task_a": "c", "task_b": "a"},
            ],
        },
    }


def test_actionable_states_require_unchanged_top3_universe() -> None:
    accepted = _branch_node(path=["a:b:same_journey"])
    hash_mismatch = {
        **_branch_node(path=["a:c:different_journey"]),
        "legal_branch_shortlist_hash_after_sort": "different",
    }
    already_deviated = _branch_node(
        path=["b:c:same_journey"],
        selected_rank=1,
    )
    rows = MODULE._actionable_states(
        {"nodes": [hash_mismatch, accepted, already_deviated]}
    )
    assert len(rows) == 1
    assert rows[0]["node_id"] == "node_007"
    assert rows[0]["top3_candidate_ids"] == [
        "branch_pair:a|b",
        "branch_pair:b|c",
        "branch_pair:a|c",
    ]


def _exact_tail_node(*, elapsed: float, node_id: str) -> dict:
    return {
        **_branch_node(path=[]),
        "node_id": node_id,
        "pricing_state": "CERTIFIED_NO_NEGATIVE",
        "node_lp_bound_official": True,
        "development_branch_rank_fallback_to_p0": False,
        "guidance_filter_count": 0,
        "tree_elapsed_sec_at_exit": elapsed,
    }


def test_tail_trigger_is_fixed_one_shot_and_torch_free() -> None:
    from lunar_ice_bpc.guidance import branch_tail_trigger as trigger

    rows = trigger.annotate_branch_tail_events(
        nodes=[
            _exact_tail_node(elapsed=9.0, node_id="early"),
            _exact_tail_node(elapsed=25.0, node_id="first-tail"),
            _exact_tail_node(elapsed=30.0, node_id="later-tail"),
        ],
        root_wall_sec=0.0,
        scale=20,
    )
    assert [row["tail_triggered"] for row in rows] == [
        False,
        True,
        False,
    ]
    assert rows[0]["tail_trigger_reason"] == (
        "BELOW_FIXED_TAIL_THRESHOLD"
    )
    assert rows[2]["tail_trigger_reason"] == (
        "ONE_SHOT_ALREADY_CONSUMED"
    )
    assert "torch" not in trigger.__dict__


def test_tail_trigger_rejects_changed_legal_universe() -> None:
    from lunar_ice_bpc.guidance.branch_tail_trigger import (
        evaluate_branch_tail_trigger,
    )

    node = _exact_tail_node(elapsed=100.0, node_id="unsafe")
    node["legal_branch_shortlist_hash_after_sort"] = "changed"
    decision = evaluate_branch_tail_trigger(
        node=node,
        root_wall_sec=0.0,
        scale=20,
        already_triggered=False,
    )
    assert decision.triggered is False
    assert decision.reason == "LEGAL_SHORTLIST_HASH_MISMATCH"


def test_tail_trigger_fresh_process_does_not_import_torch() -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys;"
                "import lunar_ice_bpc.guidance.branch_tail_trigger;"
                "assert 'torch' not in sys.modules"
            ),
        ],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_fresh_exact_zero_tail_trigger_terminates_landing() -> None:
    script = ROOT / "scripts/audit_p0v3_tail_selective_oracle.py"
    spec = importlib.util.spec_from_file_location(
        "p0v3_tail_selective_oracle",
        script,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    decision = module._tail_stop_loss_decision(
        evidence_role="FRESH_VALIDATION",
        pilot_threshold_reached=True,
        all_census_exact=True,
        tail_trigger_count=0,
        missing_trigger_gold_count=0,
        oracle_upper=0.0,
        oracle_gold_ready=False,
        instance_cap_reached=False,
    )
    assert decision["terminate_tail_selective_landing"] is True
    assert decision["decision_reason_code"] == (
        "FRESH_EXACT_PILOT_ZERO_TAIL_TRIGGER"
    )


def test_universe_safe_rejects_guidance_drop() -> None:
    node = _branch_node(path=[])
    assert MODULE._universe_safe({"nodes": [node]})
    node["guidance_branch_pair_drop_count"] = 1
    assert not MODULE._universe_safe({"nodes": [node]})


def test_node_lp_exact_safe_requires_certificate_and_both_rc_audits() -> None:
    node = {
        "requested_node_status": "NODE_LP_CERTIFIED",
        "certificate_scope": "BPC_NODE_LP_CERTIFIED",
        "pricing_state": "CERTIFIED_NO_NEGATIVE",
        "node_lp_bound_official": True,
        "uses_true_dual_bpc_certificate": True,
        "manual_rc_audit_pass": True,
        "pricing_rc_audit_pass": True,
        "final_judge_certifying_proof_kind": True,
        "certificate_ledger": {"valid": True},
    }
    assert MODULE._node_lp_exact_safe(node)
    node["pricing_rc_audit_pass"] = False
    assert not MODULE._node_lp_exact_safe(node)


def test_path_hash_is_deterministic_and_order_sensitive() -> None:
    assert MODULE._path_hash(("a", "b")) == MODULE._path_hash(("a", "b"))
    assert MODULE._path_hash(("a", "b")) != MODULE._path_hash(("b", "a"))


def test_warm_start_reuses_columns_but_never_certificate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "root_source.json"
    source.write_text(
        json.dumps(
            {
                "instance_content_hash": "content",
                "split_manifest_hash": "split",
                "root_wall_sec": 12.0,
                "root_exact_safe": False,
                "solver_binding": {
                    "baseline_id": MODULE.BASELINE_ID,
                    "engine_hash": "engine",
                    "service_timing_policy_id": "timing",
                },
                "result": {
                    "pricing_state": "INCOMPLETE_LIMIT",
                    "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                    "active_columns": [{"column": 1}],
                },
            }
        ),
        encoding="utf-8",
    )

    class Data:
        instance_content_hash = "content"
        service_timing_policy_id = "timing"

    monkeypatch.setattr(
        MODULE,
        "journey_column_from_solution_payload",
        lambda data, row: ("column", row["column"]),
    )
    columns, metadata = MODULE._warm_start_from_root_source(
        path=source,
        data=Data(),
        split_manifest_hash="split",
        solver_binding={"engine_hash": "engine"},
    )

    assert columns == (("column", 1),)
    assert metadata["certificate_reused"] is False
    assert metadata["columns_only"] is True
    assert metadata["source_root_wall_sec"] == 12.0


def test_arm_summary_root_path_ignores_leaves_without_path_field() -> None:
    result = {
        "nodes": [
            {
                "node_id": "node_000",
                "development_branch_path_signature": [],
                "development_branch_selected_rank_index": 1,
                "development_branch_rank_fallback_to_p0": False,
            },
            {"node_id": "node_001"},
            {"node_id": "node_002"},
        ]
    }

    summary = MODULE._arm_summary(
        result=result,
        tree_wall_sec=1.0,
        root_wall_sec=2.0,
        lifecycle_overhead_sec=0.02,
        target_path=tuple(),
        requested_rank=1,
    )

    assert summary["target_path_reached_once"] is True
    assert summary["target_node_id"] == "node_000"
    assert summary["target_selected_rank_index"] == 1


def test_arm_summary_binds_target_candidate_identity() -> None:
    node = _branch_node(path=[], selected_rank=1)
    result = {"nodes": [node]}

    summary = MODULE._arm_summary(
        result=result,
        tree_wall_sec=1.0,
        root_wall_sec=2.0,
        lifecycle_overhead_sec=0.02,
        target_path=tuple(),
        requested_rank=1,
    )

    assert summary["target_top3_candidate_ids"] == [
        "branch_pair:a|b",
        "branch_pair:b|c",
        "branch_pair:a|c",
    ]
    assert summary["target_selected_candidate_id"] == "branch_pair:b|c"
    assert (
        summary["target_legal_branch_shortlist_hash_before_sort"]
        == "same"
    )


def test_opportunity_parent_uses_master_primal_for_branch_probe(
    monkeypatch,
) -> None:
    primal = (
        {
            "column_id": "c1",
            "lambda_value": 0.5,
            "tasks": ["a", "b"],
        },
    )
    raw = {
        "_active_columns": ("column",),
        "_master": SimpleNamespace(
            rmp=SimpleNamespace(primal_columns=primal)
        ),
        "node_status": "NODE_LP_CERTIFIED",
    }
    observed = {}
    monkeypatch.setattr(
        MODULE,
        "solve_node_pricing_with_live_sri",
        lambda *args, **kwargs: raw,
    )
    monkeypatch.setattr(
        MODULE,
        "_diagnostic_b0_placeholder",
        lambda data: None,
    )

    def fake_probe(task_ids, received_primal, columns, **kwargs):
        observed["primal"] = tuple(received_primal)
        return {
            "status": "FRACTIONAL",
            "candidates": [{"task_a": "a"}],
        }

    monkeypatch.setattr(MODULE, "build_fractional_branch_probe", fake_probe)

    class Data:
        task_ids = ("a", "b")

    result, control, _ = MODULE._opportunity_parent_call(
        data=Data(),
        initial_columns=("seed",),
        profile={"root_harvest_target": 2},
        wall_time_limit_sec=1.0,
        max_rounds=1,
        max_columns_per_round=2,
    )

    assert observed["primal"] == primal
    assert tuple(result["primal_columns"]) == primal
    assert control["nodes"][0]["primal_columns"] == primal
    assert len(
        control["nodes"][0]["fractional_branch_probe"]["candidates"]
    ) == 1


def test_census_classifies_exact_root_incomplete_tree_as_censored(
    tmp_path: Path,
) -> None:
    (tmp_path / "root_source.json").write_text(
        json.dumps(
            {
                "root_exact_safe": True,
                "root_wall_sec": 12.0,
                "result": {},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "control_rank0_summary.json").write_text(
        json.dumps({"exact_safe": False, "tree_wall_sec": 30.0}),
        encoding="utf-8",
    )
    (tmp_path / "control_rank0_tree.json").write_text(
        json.dumps(
            {
                "pricing_state": "INCOMPLETE_LIMIT",
                "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
                "node_count": 1,
                "incomplete_node_count": 1,
            }
        ),
        encoding="utf-8",
    )

    status = CENSUS_MODULE._existing_status(tmp_path)

    assert status is not None
    assert status["status"] == "TREE_CENSORED"
    assert status["root_exact_safe"] is True
    assert status["control_exact_safe"] is False


def test_census_reads_exact_actionable_opportunity_report(
    tmp_path: Path,
) -> None:
    (tmp_path / "branch_opportunity_report.json").write_text(
        json.dumps(
            {
                "opportunity_status": "EXACT_ACTIONABLE_ROOT",
                "root_source_exact_safe": True,
                "p0_root_node_exact_safe": True,
                "root_wall_sec": 10.0,
                "p0_root_node_wall_sec": 20.0,
                "candidate_count": 3,
            }
        ),
        encoding="utf-8",
    )

    status = CENSUS_MODULE._existing_status(tmp_path)

    assert status is not None
    assert status["status"] == "EXACT_ACTIONABLE"
    assert status["actionable_state_count"] == 1
    assert status["tree_result_is_exact_bpc"] is False
