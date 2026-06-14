# Worker Negative Column ROI Blocker 报告

日期：2026-06-14

## 目的

本报告只读已有 Phase 7O / 8Q summary，回答一个窄问题：
worker 已经能加入 true-RC negative columns，为什么仍不能证明 5/10 不退化与 20 加速？
它不运行 BPC / pricing / RMP / Pulse，也不改变 worker 或 certificate 行为。

## 结论

负列发现能力已经不是充分条件。Phase 7O expanded 中 worker 加入了列，包括 new task-set 和 support-changing replacement，但所有 non-baseline rows 都 worsened；Phase 8Q 中 worker-added rows 也没有成为 improved rows。当前阻塞点是 returned-batch impact 与低开销 addition-before selector，而不是继续扩大 worker 或只追求更负 RC。

```text
worker_negative_column_roi_blocker = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = worker_negative_columns_not_sufficient_for_roi
all_checks_pass = true
```

## Phase 7O Expanded 证据

```json
{
  "by_scale": {
    "10": {
      "baseline_rows": 7,
      "improvement_class_counts": {
        "baseline": 7,
        "worsened": 56
      },
      "nonbaseline_improved_rows": 0,
      "nonbaseline_rows": 56,
      "nonbaseline_worsened_rows": 56,
      "row_count": 63,
      "time_limit_rows": 63,
      "worker_added_journeys": 45,
      "worker_added_new_task_sets": 20,
      "worker_added_rows": 15,
      "worker_added_support_changing": 9,
      "worker_triggered_rows": 20
    },
    "20": {
      "baseline_rows": 3,
      "improvement_class_counts": {
        "baseline": 3,
        "worsened": 24
      },
      "nonbaseline_improved_rows": 0,
      "nonbaseline_rows": 24,
      "nonbaseline_worsened_rows": 24,
      "row_count": 27,
      "time_limit_rows": 27,
      "worker_added_journeys": 18,
      "worker_added_new_task_sets": 10,
      "worker_added_rows": 5,
      "worker_added_support_changing": 4,
      "worker_triggered_rows": 5
    },
    "5": {
      "baseline_rows": 2,
      "improvement_class_counts": {
        "baseline": 2,
        "worsened": 16
      },
      "nonbaseline_improved_rows": 0,
      "nonbaseline_rows": 16,
      "nonbaseline_worsened_rows": 16,
      "row_count": 18,
      "time_limit_rows": 18,
      "worker_added_journeys": 0,
      "worker_added_new_task_sets": 0,
      "worker_added_rows": 0,
      "worker_added_support_changing": 0,
      "worker_triggered_rows": 0
    }
  },
  "critical_disagreement_rows": 0,
  "nonbaseline_rows": 96,
  "nonbaseline_worsened_rows": 96,
  "row_count": 108,
  "worker_added_journeys": 63,
  "worker_added_new_task_sets": 30,
  "worker_added_support_changing": 13,
  "worker_triggered_rows": 25
}
```

解释：5-task、10-task、20-task 都存在 non-baseline worsening；20-task 即使有 worker-added journeys，也没有形成 wall-time / status 改善证据。

## Phase 8Q Validation 证据

```json
{
  "critical_disagreement_rows": 0,
  "improvement_class_counts": {
    "baseline": 7,
    "improved": 1,
    "no_regression": 27
  },
  "phase8q_improved_without_worker_added_count": 1,
  "row_count": 35,
  "worker_added_journeys": 10,
  "worker_added_new_task_sets": 8,
  "worker_added_rows": 3,
  "worker_added_support_changing": 2,
  "worker_triggered_rows": 3
}
```

解释：8Q 中确有 worker-added columns，但 improved row 不是 worker-added row。passed-source 可重复加列仍没有证明 tail ROI。

## Worker-added Samples

### Phase 7O

```json
[
  {
    "improvement_class": "worsened",
    "instance": "apollo10",
    "next_dual_l1_delta": 0.36586,
    "next_rmp_objective_delta": -0.220167,
    "profile": "strict_worker_current_probe",
    "scale": "10",
    "status": "TIME_LIMIT",
    "worker_added_journeys": 2,
    "worker_added_new_task_sets": 0,
    "worker_added_support_changing": 1
  },
  {
    "improvement_class": "worsened",
    "instance": "apollo10",
    "next_dual_l1_delta": 0.36586,
    "next_rmp_objective_delta": -0.220167,
    "profile": "strict_worker_current_probe_support_aware",
    "scale": "10",
    "status": "TIME_LIMIT",
    "worker_added_journeys": 2,
    "worker_added_new_task_sets": 0,
    "worker_added_support_changing": 1
  },
  {
    "improvement_class": "worsened",
    "instance": "apollo10",
    "next_dual_l1_delta": 0.36586,
    "next_rmp_objective_delta": -0.220167,
    "profile": "strict_worker_current_probe_support_aware_low_budget",
    "scale": "10",
    "status": "TIME_LIMIT",
    "worker_added_journeys": 2,
    "worker_added_new_task_sets": 0,
    "worker_added_support_changing": 1
  },
  {
    "improvement_class": "worsened",
    "instance": "apollo10",
    "next_dual_l1_delta": 0.36586,
    "next_rmp_objective_delta": -0.220167,
    "profile": "strict_worker_current_probe_support_aware_mid_budget",
    "scale": "10",
    "status": "TIME_LIMIT",
    "worker_added_journeys": 2,
    "worker_added_new_task_sets": 0,
    "worker_added_support_changing": 1
  },
  {
    "improvement_class": "worsened",
    "instance": "apollo10",
    "next_dual_l1_delta": 0.36586,
    "next_rmp_objective_delta": -0.220167,
    "profile": "strict_worker_current_probe_support_aware_impact_filter",
    "scale": "10",
    "status": "TIME_LIMIT",
    "worker_added_journeys": 1,
    "worker_added_new_task_sets": 0,
    "worker_added_support_changing": 1
  },
  {
    "improvement_class": "worsened",
    "instance": "tranq10_09",
    "next_dual_l1_delta": 30.524704,
    "next_rmp_objective_delta": -8.209058,
    "profile": "strict_worker_current_probe",
    "scale": "10",
    "status": "TIME_LIMIT",
    "worker_added_journeys": 4,
    "worker_added_new_task_sets": 1,
    "worker_added_support_changing": 1
  },
  {
    "improvement_class": "worsened",
    "instance": "tranq10_09",
    "next_dual_l1_delta": 30.524704,
    "next_rmp_objective_delta": -8.209058,
    "profile": "strict_worker_current_probe_support_aware",
    "scale": "10",
    "status": "TIME_LIMIT",
    "worker_added_journeys": 4,
    "worker_added_new_task_sets": 1,
    "worker_added_support_changing": 1
  },
  {
    "improvement_class": "worsened",
    "instance": "tranq10_09",
    "next_dual_l1_delta": 30.524704,
    "next_rmp_objective_delta": -8.209058,
    "profile": "strict_worker_current_probe_support_aware_low_budget",
    "scale": "10",
    "status": "TIME_LIMIT",
    "worker_added_journeys": 3,
    "worker_added_new_task_sets": 1,
    "worker_added_support_changing": 0
  }
]
```

### Phase 8Q

```json
[
  {
    "improvement_class": "no_regression",
    "instance": "mt20_greedy_apollo_01",
    "next_dual_l1_delta": 204.497989,
    "next_rmp_objective_delta": -204.152729,
    "profile": "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority",
    "scale": "20",
    "status": "TIME_LIMIT",
    "worker_added_journeys": 8,
    "worker_added_new_task_sets": 8,
    "worker_added_support_changing": 0
  },
  {
    "improvement_class": "no_regression",
    "instance": "mt20_greedy_apollo_01",
    "next_dual_l1_delta": 0.760334,
    "next_rmp_objective_delta": -0.760334,
    "profile": "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic",
    "scale": "20",
    "status": "TIME_LIMIT",
    "worker_added_journeys": 1,
    "worker_added_new_task_sets": 0,
    "worker_added_support_changing": 1
  },
  {
    "improvement_class": "no_regression",
    "instance": "mt20_greedy_apollo_01",
    "next_dual_l1_delta": 0.760334,
    "next_rmp_objective_delta": -0.760334,
    "profile": "strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic",
    "scale": "20",
    "status": "TIME_LIMIT",
    "worker_added_journeys": 1,
    "worker_added_new_task_sets": 0,
    "worker_added_support_changing": 1
  }
]
```

## 对根因判断的影响

- 不能再把“Pulse 找不到负列”当成主因；
- 不能把“找到更多 true-RC negative columns”当成充分优化方向；
- 5/10 仍然要求默认完全避开固定开销，而不是只靠 worker min-task gate；
- 20 的下一步必须先证明 returned-batch selector 能改变 RMP/tail trajectory；
- 在 selector 通过 context / instance / dataset holdout 前，不能进入 production A/B 或 certificate gate。

## 检查项

```json
{
  "all_rows_time_limit": true,
  "no_critical_disagreement": true,
  "phase7o_10_task_no_regression_not_met": true,
  "phase7o_20_task_speedup_not_met": true,
  "phase7o_5_task_no_regression_not_met": true,
  "phase7o_all_nonbaseline_worsened": true,
  "phase7o_rows_present": true,
  "phase8q_improved_row_is_not_worker_added": true,
  "phase8q_rows_present": true,
  "phase8q_worker_added_rows_not_improved": true,
  "worker_added_new_task_sets_exist": true,
  "worker_added_support_changing_exists": true,
  "worker_added_true_negative_columns_exist": true
}
```
