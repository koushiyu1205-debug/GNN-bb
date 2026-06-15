# GAT Same-Run Batch Impact Audit A/B Analysis 报告

日期：2026-06-15

## 目的

读取 same-run GAT audit-only A/B 的结果 CSV 和 kNN/OOD summary。
该脚本只读文件，不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate。

## 机器字段

```text
gat_same_run_batch_impact_audit_ab_analysis = current
status = gat_same_run_pre_online_audit_gate_ready
diagnostic_only = true
runs_bpc_or_pricing = false
five_ten_no_regression_pass = true
same_run_gat_offline_gate_ready = true
twenty_capture_pair_completed = true
production_ready = false
wall_time_roi_proven = false
all_checks_pass = true
```

## 摘要

```json
{
  "checks": {
    "gat_knn_ood_checks_pass": true,
    "gat_validation_delay_recall_positive": true,
    "gat_validation_has_high_priority_signal": true,
    "gat_validation_has_zero_delay_false_positive": true,
    "negative_not_discarded": true,
    "no_active_worker_effect": true,
    "no_certificate_effect": true,
    "runbook_checks_pass": true,
    "task10_official_results_match": true,
    "task20_capture_pair_available": true,
    "task5_official_results_match": true
  },
  "effective_sample_collection_rule": {
    "invalid_sources": [
      "rc_negative_only",
      "different_dual_context",
      "appeared_in_positive_batch_without_causal_target_match",
      "replacement_column_without_support_or_tail_change"
    ],
    "negative_true_rc_without_impact": "delay_queue_not_discard",
    "positive_label": "trajectory_improves_objective_dual_or_tail",
    "required_context": "same_context_theta_basis_cuts_branch_pool",
    "required_intervention": "add_candidate_batch_then_re_solve_rmp_or_followup_rounds"
  },
  "gat_validation_metrics": {
    "accuracy": 0.6666666666666666,
    "actual_delay_queue": 4,
    "actual_high_priority": 11,
    "fn_delayed_high_priority": 5,
    "fp_high_priority_on_delay": 0,
    "high_priority_precision": 1.0,
    "high_priority_recall": 0.5454545454545454,
    "negative_recall_delay_queue": 1.0,
    "predicted_high_priority": 6,
    "tn_delay_queue": 4,
    "total": 15,
    "tp_high_priority": 6
  },
  "pair_results": [
    {
      "baseline_csv": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_20260615/task005_baseline/results.csv",
      "baseline_row_count": 2,
      "baseline_summary": {
        "optimal_count": 2,
        "row_count": 2,
        "status_counts": {
          "OPTIMAL": 2
        },
        "time_limit_count": 0,
        "wall_time_avg": 2.177187,
        "wall_time_max": 2.191489
      },
      "capture_csv": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_20260615/task005_capture/results.csv",
      "capture_row_count": 2,
      "capture_summary": {
        "optimal_count": 2,
        "row_count": 2,
        "status_counts": {
          "OPTIMAL": 2
        },
        "time_limit_count": 0,
        "wall_time_avg": 2.164297,
        "wall_time_max": 2.188301
      },
      "common_instance_count": 2,
      "missing_in_baseline": [],
      "missing_in_capture": [],
      "official_result_mismatch_count": 0,
      "official_result_mismatches": [],
      "official_results_match": true,
      "task_count": 5,
      "wall_overhead_avg": -0.005805156952902484,
      "wall_overhead_max": 0.011750971503339236
    },
    {
      "baseline_csv": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_20260615/task010_baseline/results.csv",
      "baseline_row_count": 2,
      "baseline_summary": {
        "optimal_count": 2,
        "row_count": 2,
        "status_counts": {
          "OPTIMAL": 2
        },
        "time_limit_count": 0,
        "wall_time_avg": 4.2900405,
        "wall_time_max": 5.036243
      },
      "capture_csv": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_20260615/task010_capture/results.csv",
      "capture_row_count": 2,
      "capture_summary": {
        "optimal_count": 2,
        "row_count": 2,
        "status_counts": {
          "OPTIMAL": 2
        },
        "time_limit_count": 0,
        "wall_time_avg": 4.329200999999999,
        "wall_time_max": 5.078734
      },
      "common_instance_count": 2,
      "missing_in_baseline": [],
      "missing_in_capture": [],
      "official_result_mismatch_count": 0,
      "official_result_mismatches": [],
      "official_results_match": true,
      "task_count": 10,
      "wall_overhead_avg": 0.009273775278526462,
      "wall_overhead_max": 0.010110507308742614
    },
    {
      "baseline_csv": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_20260615/task020_baseline/results.csv",
      "baseline_row_count": 4,
      "baseline_summary": {
        "optimal_count": 0,
        "row_count": 4,
        "status_counts": {
          "TIME_LIMIT": 4
        },
        "time_limit_count": 4,
        "wall_time_avg": 66.148522,
        "wall_time_max": 77.384512
      },
      "capture_csv": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_20260615/task020_capture/results.csv",
      "capture_row_count": 4,
      "capture_summary": {
        "optimal_count": 0,
        "row_count": 4,
        "status_counts": {
          "TIME_LIMIT": 4
        },
        "time_limit_count": 4,
        "wall_time_avg": 66.27906775,
        "wall_time_max": 77.569516
      },
      "common_instance_count": 4,
      "missing_in_baseline": [],
      "missing_in_capture": [],
      "official_result_mismatch_count": 0,
      "official_result_mismatches": [],
      "official_results_match": true,
      "task_count": 20,
      "wall_overhead_avg": 0.001921235371983293,
      "wall_overhead_max": 0.0029320172556131204
    }
  ],
  "remaining_blockers": [
    "no_online_opt_in_solver_integration_yet",
    "no_online_wall_time_roi_evidence_yet",
    "task20_baseline_not_exact_optimal_on_smoke_matrix"
  ],
  "task20_target_status": {
    "baseline_all_optimal": false,
    "baseline_optimal_count": 0,
    "baseline_time_limit_count": 4,
    "capture_all_optimal": false,
    "capture_optimal_count": 0,
    "capture_time_limit_count": 4
  }
}
```

## 解释

- `five_ten_no_regression_pass=true` 只说明 capture-only 不改变 5/10 official result；
- 20-task smoke 的 baseline/capture official result 一致，但当前仍是 TIME_LIMIT，不是 200 秒内精确闭合；
- `same_run_gat_offline_gate_ready=true` 只说明离线 safety shell 有候选信号；
- `production_ready=false` 是刻意保守，因为还没有 online opt-in ROI；
- true-RC negative 不能被永久丢弃，未放行的只能进入 DELAY_QUEUE。

## 为什么有效样本稀疏

- `rc < 0` 只能说明列在当前 dual 下可加，不说明它会改变 RMP 轨迹；
- 很多负列是 replacement：能进池，但不改变 active support、dual 震荡或 final-judge tail；
- 跨 dual / cuts / branch / pool 上下文贴标签会污染因果关系；
- 因此有效样本必须来自 same-context intervention：固定上下文，加入候选 batch，再观察 objective、dual、support 和 tail 的真实变化。
