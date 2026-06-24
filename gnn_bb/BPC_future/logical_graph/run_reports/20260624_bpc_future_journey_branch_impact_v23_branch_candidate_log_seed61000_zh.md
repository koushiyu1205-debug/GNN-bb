# Journey Branch-Impact Audit

日期：2026-06-24

## 目的

读取 solver JSONL 日志，聚合每次 Journey 分支后的子节点负列、列添加、active-support 和证明尾段行为。该脚本只读日志，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_branch_impact_audit = current
log_count = 1
branch_count = 1
branch_training_row_count = 1
tail_class_counts = {'unprocessed_children': 1}
priority_mode_counts = {'fractionality': 1}
selected_match_count = 1
top_contains_branch_count = 1
top_first_branch_count = 1
priority_top_first_branch_count = 1
candidate_log_branch_count = 1
right_censored_branch_count = 1
complete_label_branch_count = 0
usable_branch_impact_training_count = 0
run_status_counts = {'NO_FINISH': 1}
active_touch_branch_count = 0
inactive_only_branch_count = 0
unprocessed_child_count = 1
total_child_negative_pricing_events = 0
total_child_column_additions = 0
total_child_added_journeys = 0
total_child_completion_bound_retries = 0
total_child_early_branch_triggers = 0
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## 解释

本批 branch row 存在右删失，子树未完整观测；可以做 hard-negative/风险诊断，但不能把未处理 child 当成稳定 branch-impact 标签。

## Feature / Label Schema

```json
{
  "branch_feature_schema": [
    "depth",
    "candidate_count",
    "eligible_count",
    "has_candidate_log",
    "branch_rank_in_top",
    "branch_rank_in_priority_top",
    "same_mass",
    "fractionality",
    "support_count",
    "incumbent_relation_known",
    "incumbent_relation_same",
    "incumbent_disagreement",
    "pool_same_allowed",
    "pool_separate_allowed",
    "pool_max_child_width",
    "pool_total_child_width",
    "pool_balance_gap"
  ],
  "branch_label_schema": [
    "y_tail_improved",
    "y_completion_bound_tail",
    "y_early_branch_continues",
    "y_negative_chain_continues",
    "y_active_touch",
    "y_inactive_only",
    "y_child_negative_pricing_events",
    "y_child_completion_bound_retries",
    "y_child_early_branch_triggers"
  ]
}
```

## 注意

若 `selected_match_count = 0` 但 `top_contains_branch_count > 0`，通常表示输入日志生成于 `selected` / `priority_top` 字段加入之前；此时只能从 `top` 中反推实际分支候选位置，不能把 `selected_match_count = 0` 解读为分支选择错误。

若 `candidate_log_branch_count = 0`，说明该批日志完全缺少 branch-candidate 特征；这些 rows 只能作为 proof-cost / tail-risk 诊断，不能作为 GAT branch-impact 排序训练 row。

## Records

```json
[
  {
    "all_children_started": false,
    "branch_feature_source": "candidate_log",
    "branch_feature_vector": [
      0.0,
      60.0,
      60.0,
      1.0,
      0.0,
      0.0,
      0.666666667,
      0.333333333,
      1.0,
      1.0,
      0.0,
      0.666666667,
      178.0,
      256.0,
      256.0,
      434.0,
      78.0
    ],
    "branch_labels": {
      "y_active_touch": 0.0,
      "y_child_completion_bound_retries": 0.0,
      "y_child_early_branch_triggers": 0.0,
      "y_child_negative_pricing_events": 0.0,
      "y_completion_bound_tail": 0.0,
      "y_early_branch_continues": 0.0,
      "y_inactive_only": 0.0,
      "y_negative_chain_continues": 0.0,
      "y_tail_improved": 0.0
    },
    "branch_node_id": 0,
    "branch_observation_window": 0.857606,
    "branch_rank_in_priority_top": 0,
    "branch_rank_in_top": 0,
    "branch_time": 124.314955,
    "candidate_count": 60,
    "child_count": 2,
    "child_lower_bound_exact": true,
    "children": [
      {
        "active_new_task_set_count": 0,
        "active_replacement_task_set_count": 0,
        "added_journeys": 0,
        "addition_productivity_class_counts": {},
        "allowed_current_journeys": 178,
        "branch_same_mass": 0.666666667,
        "branch_triggered": false,
        "child_node_id": 1,
        "column_addition_count": 0,
        "completion_bound_retry_count": 0,
        "constraint": "RF(3,7)=same_vehicle",
        "constraint_kind": "same_vehicle",
        "depth": 1,
        "early_branch_trigger_count": 0,
        "inactive_changed_task_set_count": 0,
        "last_time": 125.172561,
        "lower_bound": 580.044467,
        "lower_bound_exact": true,
        "min_best_reduced_cost": 15.982898013,
        "negative_journeys_total": 0,
        "negative_pricing_event_count": 0,
        "new_journeys": 0,
        "node_incomplete_reason": null,
        "pricing_event_count": 1,
        "replacement_journeys": 0,
        "selected_trips_total": 0,
        "start_time": 124.315218,
        "started": true,
        "time_span": 0.857343
      },
      {
        "active_new_task_set_count": 0,
        "active_replacement_task_set_count": 0,
        "added_journeys": 0,
        "addition_productivity_class_counts": {},
        "allowed_current_journeys": 256,
        "branch_same_mass": 0.666666667,
        "branch_triggered": false,
        "child_node_id": 2,
        "column_addition_count": 0,
        "completion_bound_retry_count": 0,
        "constraint": "RF(3,7)=separate_vehicle",
        "constraint_kind": "separate_vehicle",
        "depth": 1,
        "early_branch_trigger_count": 0,
        "inactive_changed_task_set_count": 0,
        "last_time": 124.315198,
        "lower_bound": 580.044467,
        "lower_bound_exact": true,
        "min_best_reduced_cost": null,
        "negative_journeys_total": 0,
        "negative_pricing_event_count": 0,
        "new_journeys": 0,
        "node_incomplete_reason": null,
        "pricing_event_count": 0,
        "replacement_journeys": 0,
        "selected_trips_total": 0,
        "start_time": 124.315198,
        "started": false,
        "time_span": 0.0
      }
    ],
    "depth": 0,
    "eligible_count": 60,
    "exact_bound_available": false,
    "first_child_allowed_current_journeys": 178,
    "first_child_column_additions": 0,
    "first_child_completion_bound_retry_count": 0,
    "first_child_early_branch_trigger_count": 0,
    "first_child_negative_pricing_event_count": 0,
    "first_child_time_span": 0.857343,
    "first_started_child_node_id": 1,
    "label_observation_complete": false,
    "left": "RF(3,7)=same_vehicle",
    "log_end_time": 125.172561,
    "log_file": "BPC_future/results/logs_20260624_v23_branch_candidate_log_130_randomtw20_seed61000/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json.jsonl",
    "log_has_finish": false,
    "max_child_allowed_current_journeys": 256,
    "min_child_allowed_current_journeys": 178,
    "observed_branch_candidate": {
      "fractionality": 0.333333333,
      "incumbent_disagreement": 0.666666667,
      "incumbent_relation": false,
      "pool_balance_gap": 78,
      "pool_max_child_width": 256,
      "pool_same_allowed": 178,
      "pool_separate_allowed": 256,
      "pool_total_child_width": 434,
      "same_mass": 0.666666667,
      "support_count": 1,
      "task_i": 3,
      "task_j": 7
    },
    "priority_mode": "fractionality",
    "priority_top": [
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": false,
        "pool_balance_gap": 78,
        "pool_max_child_width": 256,
        "pool_same_allowed": 178,
        "pool_separate_allowed": 256,
        "pool_total_child_width": 434,
        "same_mass": 0.666666667,
        "support_count": 1,
        "task_i": 3,
        "task_j": 7
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.333333333,
        "incumbent_relation": true,
        "pool_balance_gap": 74,
        "pool_max_child_width": 229,
        "pool_same_allowed": 155,
        "pool_separate_allowed": 229,
        "pool_total_child_width": 384,
        "same_mass": 0.666666667,
        "support_count": 1,
        "task_i": 3,
        "task_j": 10
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": false,
        "pool_balance_gap": 79,
        "pool_max_child_width": 249,
        "pool_same_allowed": 170,
        "pool_separate_allowed": 249,
        "pool_total_child_width": 419,
        "same_mass": 0.666666667,
        "support_count": 1,
        "task_i": 3,
        "task_j": 19
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": false,
        "pool_balance_gap": 49,
        "pool_max_child_width": 253,
        "pool_same_allowed": 204,
        "pool_separate_allowed": 253,
        "pool_total_child_width": 457,
        "same_mass": 0.666666667,
        "support_count": 2,
        "task_i": 6,
        "task_j": 9
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": false,
        "pool_balance_gap": 70,
        "pool_max_child_width": 251,
        "pool_same_allowed": 181,
        "pool_separate_allowed": 251,
        "pool_total_child_width": 432,
        "same_mass": 0.666666667,
        "support_count": 2,
        "task_i": 6,
        "task_j": 13
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": false,
        "pool_balance_gap": 85,
        "pool_max_child_width": 255,
        "pool_same_allowed": 170,
        "pool_separate_allowed": 255,
        "pool_total_child_width": 425,
        "same_mass": 0.666666667,
        "support_count": 1,
        "task_i": 7,
        "task_j": 10
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": false,
        "pool_balance_gap": 83,
        "pool_max_child_width": 247,
        "pool_same_allowed": 164,
        "pool_separate_allowed": 247,
        "pool_total_child_width": 411,
        "same_mass": 0.666666667,
        "support_count": 1,
        "task_i": 10,
        "task_j": 19
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": true,
        "pool_balance_gap": 55,
        "pool_max_child_width": 254,
        "pool_same_allowed": 199,
        "pool_separate_allowed": 254,
        "pool_total_child_width": 453,
        "same_mass": 0.333333333,
        "support_count": 1,
        "task_i": 11,
        "task_j": 12
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": true,
        "pool_balance_gap": 59,
        "pool_max_child_width": 254,
        "pool_same_allowed": 195,
        "pool_separate_allowed": 254,
        "pool_total_child_width": 449,
        "same_mass": 0.333333333,
        "support_count": 1,
        "task_i": 11,
        "task_j": 16
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": true,
        "pool_balance_gap": 56,
        "pool_max_child_width": 254,
        "pool_same_allowed": 198,
        "pool_separate_allowed": 254,
        "pool_total_child_width": 452,
        "same_mass": 0.333333333,
        "support_count": 1,
        "task_i": 11,
        "task_j": 17
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.333333333,
        "incumbent_relation": false,
        "pool_balance_gap": 44,
        "pool_max_child_width": 257,
        "pool_same_allowed": 213,
        "pool_separate_allowed": 257,
        "pool_total_child_width": 470,
        "same_mass": 0.333333333,
        "support_count": 1,
        "task_i": 12,
        "task_j": 14
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.333333333,
        "incumbent_relation": false,
        "pool_balance_gap": 42,
        "pool_max_child_width": 255,
        "pool_same_allowed": 213,
        "pool_separate_allowed": 255,
        "pool_total_child_width": 468,
        "same_mass": 0.333333333,
        "support_count": 1,
        "task_i": 14,
        "task_j": 16
      }
    ],
    "processed_child_count": 1,
    "right": "RF(3,7)=separate_vehicle",
    "right_censored": true,
    "right_kind": "separate_vehicle",
    "run_status": "NO_FINISH",
    "selected": {
      "fractionality": 0.333333333,
      "incumbent_disagreement": 0.666666667,
      "incumbent_relation": false,
      "pool_balance_gap": 78,
      "pool_max_child_width": 256,
      "pool_same_allowed": 178,
      "pool_separate_allowed": 256,
      "pool_total_child_width": 434,
      "same_mass": 0.666666667,
      "support_count": 1,
      "task_i": 3,
      "task_j": 7
    },
    "selected_matches_branch": true,
    "sum_child_active_new_task_set_count": 0,
    "sum_child_active_replacement_task_set_count": 0,
    "sum_child_added_journeys": 0,
    "sum_child_column_additions": 0,
    "sum_child_completion_bound_retry_count": 0,
    "sum_child_early_branch_trigger_count": 0,
    "sum_child_inactive_changed_task_set_count": 0,
    "sum_child_negative_pricing_event_count": 0,
    "tail_class": "unprocessed_children",
    "task_i": 3,
    "task_j": 7,
    "top": [
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": false,
        "pool_balance_gap": 78,
        "pool_max_child_width": 256,
        "pool_same_allowed": 178,
        "pool_separate_allowed": 256,
        "pool_total_child_width": 434,
        "same_mass": 0.666666667,
        "support_count": 1,
        "task_i": 3,
        "task_j": 7
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.333333333,
        "incumbent_relation": true,
        "pool_balance_gap": 74,
        "pool_max_child_width": 229,
        "pool_same_allowed": 155,
        "pool_separate_allowed": 229,
        "pool_total_child_width": 384,
        "same_mass": 0.666666667,
        "support_count": 1,
        "task_i": 3,
        "task_j": 10
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": false,
        "pool_balance_gap": 79,
        "pool_max_child_width": 249,
        "pool_same_allowed": 170,
        "pool_separate_allowed": 249,
        "pool_total_child_width": 419,
        "same_mass": 0.666666667,
        "support_count": 1,
        "task_i": 3,
        "task_j": 19
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": false,
        "pool_balance_gap": 49,
        "pool_max_child_width": 253,
        "pool_same_allowed": 204,
        "pool_separate_allowed": 253,
        "pool_total_child_width": 457,
        "same_mass": 0.666666667,
        "support_count": 2,
        "task_i": 6,
        "task_j": 9
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": false,
        "pool_balance_gap": 70,
        "pool_max_child_width": 251,
        "pool_same_allowed": 181,
        "pool_separate_allowed": 251,
        "pool_total_child_width": 432,
        "same_mass": 0.666666667,
        "support_count": 2,
        "task_i": 6,
        "task_j": 13
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": false,
        "pool_balance_gap": 85,
        "pool_max_child_width": 255,
        "pool_same_allowed": 170,
        "pool_separate_allowed": 255,
        "pool_total_child_width": 425,
        "same_mass": 0.666666667,
        "support_count": 1,
        "task_i": 7,
        "task_j": 10
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": false,
        "pool_balance_gap": 83,
        "pool_max_child_width": 247,
        "pool_same_allowed": 164,
        "pool_separate_allowed": 247,
        "pool_total_child_width": 411,
        "same_mass": 0.666666667,
        "support_count": 1,
        "task_i": 10,
        "task_j": 19
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": true,
        "pool_balance_gap": 55,
        "pool_max_child_width": 254,
        "pool_same_allowed": 199,
        "pool_separate_allowed": 254,
        "pool_total_child_width": 453,
        "same_mass": 0.333333333,
        "support_count": 1,
        "task_i": 11,
        "task_j": 12
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": true,
        "pool_balance_gap": 59,
        "pool_max_child_width": 254,
        "pool_same_allowed": 195,
        "pool_separate_allowed": 254,
        "pool_total_child_width": 449,
        "same_mass": 0.333333333,
        "support_count": 1,
        "task_i": 11,
        "task_j": 16
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": true,
        "pool_balance_gap": 56,
        "pool_max_child_width": 254,
        "pool_same_allowed": 198,
        "pool_separate_allowed": 254,
        "pool_total_child_width": 452,
        "same_mass": 0.333333333,
        "support_count": 1,
        "task_i": 11,
        "task_j": 17
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.333333333,
        "incumbent_relation": false,
        "pool_balance_gap": 44,
        "pool_max_child_width": 257,
        "pool_same_allowed": 213,
        "pool_separate_allowed": 257,
        "pool_total_child_width": 470,
        "same_mass": 0.333333333,
        "support_count": 1,
        "task_i": 12,
        "task_j": 14
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.333333333,
        "incumbent_relation": false,
        "pool_balance_gap": 42,
        "pool_max_child_width": 255,
        "pool_same_allowed": 213,
        "pool_separate_allowed": 255,
        "pool_total_child_width": 468,
        "same_mass": 0.333333333,
        "support_count": 1,
        "task_i": 14,
        "task_j": 16
      }
    ],
    "unprocessed_child_count": 1,
    "usable_for_branch_impact_training": false
  }
]
```
