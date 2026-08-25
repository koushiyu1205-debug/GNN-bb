from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/maintain_p0v5_qg2_live_markdown.py"
SPEC = importlib.util.spec_from_file_location("qg2_live_markdown", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_live_pipeline_tracks_independent_formal_ordering_safety() -> None:
    assert MODULE.CONTROLLER_STATES["Formal ordering safety"] == (
        "qg2_formal_ordering_safety_controller_state.json"
    )
    assert MODULE.PIPELINE_ARTIFACTS["Formal ordering safety freeze"] == (
        "qg2_formal_ordering_safety_controller_freeze.json"
    )
    assert MODULE.PIPELINE_ARTIFACTS["Formal ordering safety audit"] == (
        "p0v5_qg2_formal_ordering_safety_audit.json"
    )
    assert MODULE.PIPELINE_ARTIFACTS["Candidate safety extension"] == (
        "P0V5_QG2_ACTION_SURFACE_V2_candidate_safety_extension.json"
    )
    assert MODULE.CONTROLLER_STATES["Training-only V2"] == (
        "qg2_action_surface_v2_training_only_v2_state.json"
    )
    assert MODULE.PIPELINE_ARTIFACTS["Calibration risk V2 freeze"] == (
        "qg2_calibration_risk_v2_freeze.json"
    )
    assert MODULE.CONTROLLER_STATES["Training-only V2 candidate finalizer"] == (
        "qg2_training_only_v2_candidate_finalizer_state.json"
    )
    assert MODULE.PIPELINE_ARTIFACTS["Training-only V2 completion audit"] == (
        "qg2_training_only_v2_completion_audit.json"
    )
    assert MODULE.PIPELINE_ARTIFACTS["Training-only V2 candidate"] == (
        "P0V5_QG2_LABEL_STATE_GAT_TRAINING_ONLY_V2_candidate_freeze.json"
    )
    assert MODULE.CONTROLLER_STATES[
        "Training-only V2 formal ordering safety"
    ] == "qg2_training_only_v2_formal_ordering_safety_state.json"
    assert MODULE.PIPELINE_ARTIFACTS[
        "Training-only V2 candidate safety extension"
    ] == (
        "P0V5_QG2_LABEL_STATE_GAT_TRAINING_ONLY_V2_candidate_safety_extension.json"
    )


def test_live_pipeline_tracks_selective_runtime_candidate_path() -> None:
    assert MODULE.CONTROLLER_STATES["Selective runtime binding"] == (
        "qg2_training_only_v2_selective_runtime_binding_state.json"
    )
    assert MODULE.CONTROLLER_STATES["Selective runtime E2E"] == (
        "qg2_selective_runtime_e2e_state.json"
    )
    assert MODULE.CONTROLLER_STATES[
        "Selective runtime formal full20"
    ] == "qg2_selective_runtime_formal_state.json"
    assert MODULE.CONTROLLER_STATES[
        "Selective runtime candidate finalizer"
    ] == "qg2_selective_runtime_candidate_finalizer_state.json"
    assert MODULE.PIPELINE_ARTIFACTS["Selective runtime manifest"] == (
        "qg2_training_only_v2_selective_runtime_manifest.json"
    )
    assert MODULE.PIPELINE_ARTIFACTS["Selective runtime authority"] == (
        "qg2_training_only_v2_selective_runtime_authority.json"
    )
    assert MODULE.PIPELINE_ARTIFACTS[
        "Selective runtime completion audit"
    ] == "qg2_selective_runtime_completion_audit.json"
    assert MODULE.COMPLETION_AUDIT_CANDIDATES[0] == (
        "qg2_selective_runtime_completion_audit.json"
    )


def test_latest_completion_audit_prefers_final_then_refreshed_live(
    tmp_path: Path,
) -> None:
    import json

    live = tmp_path / "qg2_training_only_v2_completion_audit_live.json"
    live.write_text(
        json.dumps({"track": "live", "passed_check_count": 1}),
        encoding="utf-8",
    )
    assert MODULE._latest_completion_audit(
        tmp_path, MODULE.ProjectionCache()
    )["track"] == "live"

    final = tmp_path / "qg2_training_only_v2_completion_audit.json"
    final.write_text(
        json.dumps({"track": "final", "complete": True}),
        encoding="utf-8",
    )
    assert MODULE._latest_completion_audit(
        tmp_path, MODULE.ProjectionCache()
    )["track"] == "final"


def test_current_arm_name_uses_experiment_arm_not_low_level_policy() -> None:
    for arm, filename in MODULE.ARM_FILES.items():
        assert MODULE._current_arm_name(
            f"/tmp/30_state/{filename}",
            "QG2",
        ) == arm

    assert MODULE._current_arm_name(
        "/tmp/30_state/q0_trace.json",
        "Q0",
    ) == "Q0 trace"
    assert MODULE._current_arm_name(
        "/tmp/30_state/unknown.json",
        "QG2",
    ) == "QG2"


def test_oracle_phase_does_not_treat_last_started_context_as_complete() -> None:
    active_initial = {
        "pid": 123,
        "output": "/tmp/50_state/q0_trace.json",
        "policy": "Q0",
    }
    assert MODULE._oracle_phase(
        oracle_summary=None,
        replicate_started=False,
        current_child=active_initial,
        initial_started=200,
        bounded_limit=200,
    ) == "INITIAL_SCREEN"
    assert MODULE._oracle_phase(
        oracle_summary=None,
        replicate_started=False,
        current_child=None,
        initial_started=200,
        bounded_limit=200,
    ) == "INITIAL_SCREEN_COMPLETE_PENDING_REPLICATES"


def test_oracle_phase_prioritizes_replicates_and_frozen_summary() -> None:
    active_replicate = {
        "pid": 456,
        "output": "/tmp/50_state/q0_0.001_rep1.json",
        "policy": "Q0",
    }
    assert MODULE._oracle_phase(
        oracle_summary=None,
        replicate_started=False,
        current_child=active_replicate,
        initial_started=200,
        bounded_limit=200,
    ) == "BLOCKED_REPLICATES"
    assert MODULE._oracle_phase(
        oracle_summary={"status": "PASSED"},
        replicate_started=True,
        current_child=active_replicate,
        initial_started=200,
        bounded_limit=200,
    ) == "ORACLE_SUMMARY_FROZEN"


def test_replicate_bucket_arm_uses_summary_then_active_or_completed_paths() -> None:
    assert MODULE._replicate_bucket_arm(
        replicate_q0=(),
        current_child=None,
        frozen_bucket=0.0003,
    ) == "QO2-3e-4"
    assert MODULE._replicate_bucket_arm(
        replicate_q0=(),
        current_child={"output": "/tmp/state/q0_0.001_rep1.json"},
        frozen_bucket=None,
    ) == "QO2-1e-3"
    assert MODULE._replicate_bucket_arm(
        replicate_q0=(Path("/tmp/state/q0_0.0001_rep2.json"),),
        current_child=None,
        frozen_bucket=None,
    ) == "QO2-1e-4"
    assert MODULE._replicate_bucket_arm(
        replicate_q0=(),
        current_child={"output": "/tmp/state/q0_initial.json"},
        frozen_bucket=None,
    ) is None


def test_instance_progress_maps_started_state_to_unique_instance() -> None:
    payload = {
        "rows": [
            {
                "scale": 30,
                "state_hash": "a" * 64,
                "instance_id": "instance_001",
            },
            {
                "scale": 30,
                "state_hash": "b" * 64,
                "instance_id": "instance_001",
            },
            {
                "scale": 50,
                "state_hash": "c" * 64,
                "instance_id": "instance_002",
            },
        ]
    }
    mapping = MODULE._index_instance_by_state(payload)
    assert mapping[(30, "a" * 16)] == "instance_001"
    assert mapping[(30, "b" * 16)] == "instance_001"
    assert mapping[(50, "c" * 16)] == "instance_002"


def test_started_context_precedes_q0_trace_completion() -> None:
    progress = {
        50: {
            "started": 0,
            "trace": 0,
            "future": 0,
            "full": 0,
            "instance_ids": set(),
        }
    }
    state = "a" * 16
    MODULE._record_started_context(
        progress,
        scale=50,
        state_prefix=state,
        instance_by_state={(50, state): "instance_090"},
        q0_trace_exists=False,
    )

    assert progress[50]["started"] == 1
    assert progress[50]["trace"] == 0
    assert progress[50]["instance_ids"] == {"instance_090"}


def test_fresh_calibration_progress_counts_only_complete_matched_pairs(
    tmp_path: Path,
) -> None:
    import json

    manifest = {
        "combined_counts": {
            "scale30_calibration_context_count": 1,
            "scale30_heldout_context_count": 0,
            "scale50_calibration_context_count": 0,
            "scale50_heldout_context_count": 0,
        }
    }
    (tmp_path / MODULE.FRESH_CALIBRATION_MANIFEST).write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    context = (
        tmp_path
        / MODULE.FRESH_CALIBRATION_DIR
        / "linear"
        / "calibration"
        / "30_state"
    )
    context.mkdir(parents=True)
    (context / "potential.json").write_text(
        json.dumps({"runtime_prethreshold_veto": False}), encoding="utf-8"
    )
    for repeat in (1, 2, 3):
        (context / f"q0_0.001_rep{repeat}.json").write_text(
            "{}", encoding="utf-8"
        )
    for repeat in (1, 2):
        (context / f"qg2_0.001_rep{repeat}.json").write_text(
            "{}", encoding="utf-8"
        )

    progress = MODULE._collect_fresh_calibration_progress(
        run_root=tmp_path,
        cache=MODULE.ProjectionCache(),
    )
    assert progress["expected_contexts"] == 3
    assert progress["started_contexts"] == 1
    assert progress["completed_pairs"] == 2
    assert progress["finalized_contexts"] == 0

    (context / "qg2_0.001_rep3.json").write_text("{}", encoding="utf-8")
    refreshed = MODULE._collect_fresh_calibration_progress(
        run_root=tmp_path,
        cache=MODULE.ProjectionCache(),
    )
    assert refreshed["completed_pairs"] == 3
    assert refreshed["finalized_contexts"] == 1


def test_snapshot_binding_census_preserves_missingness_and_runtime_context(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(__import__("json").dumps({
        "scale": 30,
        "pricing_lifecycle_scope": "tree_node",
        "trajectory_feature_semantics_version": (
            "p0v5_qg2_preaction_trajectory_missingness.v2"
        ),
        "base_proof_queue_policy_id": "Q0",
        "config_hash": "config",
        "engine_hash": "engine",
        "exact_action_policy_hash": "policy",
        "round": 4,
        "active_column_count": 2,
        "active_column_signature_hashes": ["a", "b"],
        "active_task_sets": [["t1"], ["t2"]],
        "branch_context": {
            "pair_decision_count": 1,
            "pair_decisions": [{}],
        },
        "cut_context": {"cut_count": 1, "cuts": [{}]},
        "true_duals": {
            "task_duals": {f"t{i}": float(i) for i in range(30)},
            "fleet_dual": 1.0,
            "cut_duals": {"c1": 2.0},
        },
        "trajectory_features": {
            "previous_proof_pass_wall_time": None,
            "previous_proof_processed_labels": None,
            "dual_l1_delta_from_previous": 0.5,
            "v5_midpoint_wall_sec": 1.5,
        },
    }), encoding="utf-8")
    state = "a" * 64
    census = MODULE._snapshot_binding_census(
        {"rows": [{
            "scale": 30,
            "state_hash": state,
            "snapshot_path": str(snapshot),
        }]},
        selected_state_prefixes={(30, state[:16])},
        cache=MODULE.ProjectionCache(),
    )[30]

    assert census["snapshot_count"] == 1
    assert census["structural_binding_complete_count"] == 1
    assert census["active_column_binding_complete_count"] == 1
    assert census["previous_proof_present_count"] == 0
    assert census["previous_proof_missing_count"] == 1
    assert census["previous_proof_pair_inconsistent_count"] == 0
    assert census["dual_delta_present_count"] == 1
    assert census["root_count"] == 0
    assert census["tree_count"] == 1
    assert census["active_branch_count"] == 1
    assert census["active_cut_count"] == 1


def test_live_budget_filters_retained_contexts_with_oracle_selection() -> None:
    rows = []
    for scale, prefix in ((30, "a"), (50, "b")):
        for index in range(3):
            rows.append({
                "scale": scale,
                "state_hash": prefix * 15 + str(index) + "0" * 48,
                "instance_hash": f"instance_{scale}_{index}",
                "pricing_lifecycle_scope": "root_cg",
                "round": 35,
                "previous_q0_wall_stratum": "missing",
            })

    selected = MODULE._bounded_selected_state_prefixes(
        {"rows": rows},
        maximum=4,
        per_scale=2,
    )

    assert selected is not None
    assert len(selected) == 4
    assert sum(scale == 30 for scale, _state in selected) == 2
    assert sum(scale == 50 for scale, _state in selected) == 2


def test_measured_portfolio_render_keeps_diagnostic_training_boundary() -> None:
    report = {
        "measured_portfolio": {
            "training_authority": False,
            "aggregate": {
                "all": {
                    "context_count": 2,
                    "qg2_gm": 0.9,
                    "portfolio_gm": 0.5,
                    "captured_savings_fraction": 0.4,
                    "qg2_action_surface_gap_sec": 12.0,
                }
            },
        }
    }

    rendered = "\n".join(MODULE._render_measured_portfolio(report))

    assert "不提供训练授权" in rendered
    assert "包含leaked future trace和事后选bucket的乐观偏差" in rendered
    assert "不是GAT预测准确率" in rendered
    assert "它是当前QG2动作能力的缺口，不是模型误差" in rendered
    assert "QD1/QB1赢家不能直接转换" in rendered
    assert "| all | 2 | 0.9000 | 0.5000 | 40.00% | +12.00s |" in rendered


def test_right_censored_live_arm_cannot_look_faster_than_q0() -> None:
    arm = {
        "milestone_reached": False,
        "milestone_wall_sec": 80.0,
        "requested_wall_time_limit_sec": 180.0,
    }

    assert MODULE._comparison_wall(arm, q0_wall=120.0) == 180.0

    arm["requested_wall_time_limit_sec"] = None
    assert MODULE._comparison_wall(arm, q0_wall=120.0) == 120.0

    arm["milestone_reached"] = True
    assert MODULE._comparison_wall(arm, q0_wall=120.0) == 80.0


def test_scale50_fixed_arm_pilot_is_not_portfolio_selection() -> None:
    report = {
        "contexts": [{
            "scale": 50,
            "ratios": {
                "QD1": 3.0,
                "QB1": 0.1,
                "Random61635": 1.5,
                "Random91267": 1.4,
                "Random170141": 1.3,
                "QO2-1e-4": 1.0,
                "QO2-3e-4": 0.95,
                "QO2-1e-3": 0.9,
            },
            "right_censored_arms": ["QD1"],
        }]
    }

    rendered = "\n".join(MODULE._render_scale50_fixed_arm_pilot(report))

    assert "非事后选择" in rendered
    assert "| QD1 | 1 | 0/1 | 3.0000" in rendered
    assert "| QB1 | 1 | 1/1 | 0.1000" in rendered
    assert "不会逐context选择最快arm" in rendered


def test_partial_context_is_visible_without_entering_aggregate() -> None:
    rendered = "\n".join(MODULE._render_partial_context({
        "partial_context": {
            "scale": 50,
            "state": "abc123",
            "completed": [
                {
                    "arm": "Q0",
                    "milestone": "ADMISSION_BATCH_READY",
                    "milestone_reached": True,
                    "wall": 154.0,
                    "ratio": 1.0,
                    "raw_negative": 512,
                    "master_ready": 128,
                    "processed_labels": 2_000_000,
                    "extended_labels": 300_000_000,
                    "safe": True,
                },
                {
                    "arm": "QD1",
                    "milestone": "RIGHT_CENSORED",
                    "milestone_reached": False,
                    "wall": 303.0,
                    "ratio": 303.0 / 154.0,
                    "raw_negative": 0,
                    "master_ready": 0,
                    "processed_labels": 8_000_000,
                    "extended_labels": 1_200_000_000,
                    "safe": True,
                },
            ],
        }
    }))

    assert "尚未进入累计统计" in rendered
    assert "只有全部initial arms结束后才进入GM和gate" in rendered
    assert (
        "| Q0 | ADMISSION_BATCH_READY | 154.00s | 1.0000 | 512 | 128 | "
        "2,000,000 | 300,000,000 | yes |"
    ) in rendered
    assert (
        "| QD1 | RIGHT_CENSORED | 303.00s | 1.9675 | 0 | 0 | "
        "8,000,000 | 1,200,000,000 | yes |"
    ) in rendered


def test_partial_arm_safe_requires_same_universe_and_zero_drop_authority() -> None:
    telemetry = {
        "legal_action_universe_hash_before_sort": "actions",
        "legal_arc_universe_hash_before_sort": "arcs",
        "guidance_filter_count": 0,
        "guidance_arc_drop_count": 0,
        "guidance_label_drop_count": 0,
        "guidance_branch_pair_drop_count": 0,
    }
    control = {"proof_telemetry": dict(telemetry)}
    arm = {
        "proof_telemetry": dict(telemetry),
        "labels_dropped": False,
        "can_filter": False,
        "can_prune": False,
        "can_change_reduced_cost": False,
        "can_certify_from_guidance": False,
    }

    assert MODULE._partial_arm_safe(control, arm)
    arm["proof_telemetry"]["guidance_label_drop_count"] = 1
    assert not MODULE._partial_arm_safe(control, arm)
    arm["proof_telemetry"] = {
        **telemetry,
        "legal_action_universe_hash_before_sort": "drift",
    }
    assert not MODULE._partial_arm_safe(control, arm)


def test_relaxed_gate_is_reported_per_scale_not_from_pooled_metrics() -> None:
    passing = {
        "context_count": 20,
        "gain_5pct_context_count": 5,
        "gain_5pct_instance_count": 5,
        "gm": 0.90,
        "bootstrap_upper": 0.95,
        "all_safe": True,
    }
    failing = {**passing, "context_count": 6, "gm": 1.05}
    rendered = "\n".join(MODULE._render_relaxed_gate({
        "bucket_metrics_by_scale": {
            30: {"QO2-1e-3": passing},
            50: {"QO2-1e-3": failing},
        },
        "concentration": 0.20,
    }))

    assert "| 30 | 20/20 | 5/5 | 5/5 | 0.9000/0.9500" in rendered
    assert "| 50 | 6/20 | 5/5 | 5/5 | 1.0500/0.9500" in rendered
    assert rendered.count("| PASS |") == 1
    assert "当前预览数字组合：`NOT YET`" in rendered
    assert "尚未冻结bucket" in rendered


def test_relaxed_gate_switches_to_oracle_frozen_bucket() -> None:
    passing = {
        "context_count": 20,
        "gain_5pct_context_count": 5,
        "gain_5pct_instance_count": 5,
        "gm": 0.90,
        "bootstrap_upper": 0.95,
        "all_safe": True,
    }
    rendered = "\n".join(MODULE._render_relaxed_gate({
        "bucket_metrics_by_scale": {
            30: {"QO2-3e-4": passing},
            50: {"QO2-3e-4": passing},
        },
        "relaxed_gate_arm": "QO2-3e-4",
        "relaxed_gate_frozen": True,
        "concentration": 0.20,
    }))

    assert "`3e-4` frozen relaxed training gate" in rendered
    assert "当前冻结数字组合：`PASS`" in rendered
    assert "尚未冻结bucket" not in rendered
    assert MODULE._bucket_arm_from_width(0.0003) == "QO2-3e-4"
    assert MODULE._bucket_arm_from_width(None) is None


def test_training_only_v2_preview_ignores_fixed_arm_gm_and_bootstrap() -> None:
    passing = {
        "context_count": 20,
        "instance_count": 20,
        "gain_5pct_context_count": 5,
        "gain_5pct_instance_count": 5,
        "nonpositive_context_count": 15,
        "harmful_instance_count": 12,
        "gm": 1.10,
        "bootstrap_upper": 1.30,
        "all_safe": True,
    }
    rendered = "\n".join(MODULE._render_training_only_v2_gate({
        "bucket_metrics_by_scale": {
            30: {"QO2-1e-3": passing},
            50: {"QO2-1e-3": passing},
        },
        "relaxed_gate_arm": "QO2-1e-3",
        "relaxed_gate_frozen": False,
        "concentration": 0.20,
    }))

    assert rendered.count("| PASS |") == 2
    assert "固定arm GM和bootstrap仅报告" in rendered
    assert "training-only V2 数据组合：`PASS`" in rendered
    assert "不授权calibration、部署或论文结论" in rendered


def test_training_only_v2_preview_requires_harmful_support() -> None:
    failing = {
        "context_count": 20,
        "instance_count": 20,
        "gain_5pct_context_count": 5,
        "gain_5pct_instance_count": 5,
        "nonpositive_context_count": 5,
        "harmful_instance_count": 0,
        "all_safe": True,
    }

    assert not MODULE._training_only_v2_scale_gate(failing)


def test_instance_split_projection_matches_frozen_trainer_and_exposes_shortfall() -> None:
    contexts = []
    for scale in (30, 50):
        for index in range(10):
            contexts.append({
                "scale": scale,
                "instance_hash": f"instance_{scale}_{index}",
            })

    projection = MODULE._instance_split_projection(contexts)

    assert projection["scale30"]["train_context_count"] == 6
    assert projection["scale30"]["calibration_context_count"] == 2
    assert projection["scale30"]["heldout_context_count"] == 2
    assert projection["scale50"]["train_context_count"] == 6
    assert projection["scale50"]["calibration_context_count"] == 2
    assert projection["scale50"]["heldout_context_count"] == 2
    assert projection["calibration_context_count"] == 4
    assert projection["calibration_shortfall"] == 48

    rendered = "\n".join(MODULE._render_split_projection({
        "split_projection": projection,
    }))
    assert "60/20/20实例级划分" in rendered
    assert "`4/52`" in rendered
    assert "relaxed gate只允许先训练" in rendered


def test_supplemental_pool_projection_keeps_training_instances_out() -> None:
    contexts = [
        {"scale": 30, "instance_hash": f"known30_{index}", "state": f"c{index}"}
        for index in range(10)
    ] + [
        {"scale": 50, "instance_hash": f"known50_{index}", "state": f"d{index}"}
        for index in range(10)
    ]
    rows = []
    for scale in (30, 50):
        for index in range(400):
            rows.append({
                "scale": scale,
                "instance_content_hash": f"unseen_{scale}_{index}",
                "state_hash": f"{scale:02d}{index:014d}" + "0" * 48,
            })

    projection = MODULE._supplemental_pool_projection(
        contexts, {"rows": rows}
    )

    assert projection["calibration_context_count"] >= 52
    assert projection["heldout_context_count"] >= 20
    assert projection["sufficient"]
    assert projection["status"] == "PROJECTED_SUFFICIENT"
