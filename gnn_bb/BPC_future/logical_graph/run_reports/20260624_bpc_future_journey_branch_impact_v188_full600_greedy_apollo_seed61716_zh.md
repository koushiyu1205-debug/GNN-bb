# Journey Branch-Impact Audit

日期：2026-06-24

## 目的

读取 solver JSONL 日志，聚合每次 Journey 分支后的子节点负列、列添加、active-support 和证明尾段行为。该脚本只读日志，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_branch_impact_audit = current
log_count = 1
branch_count = 2
branch_training_row_count = 2
child_probe_row_count = 4
tail_class_counts = {'completion_bound_tail': 2}
priority_mode_counts = {'not_logged': 2}
selected_match_count = 0
top_contains_branch_count = 0
top_first_branch_count = 0
priority_top_first_branch_count = 0
candidate_log_branch_count = 0
forced_pair_branch_count = 0
forced_pair_matched_branch_count = 0
right_censored_branch_count = 0
complete_label_branch_count = 2
usable_branch_impact_training_count = 0
run_status_counts = {'OPTIMAL': 2}
active_touch_branch_count = 1
inactive_only_branch_count = 1
unprocessed_child_count = 0
total_child_negative_pricing_events = 25
total_child_exact_pricing_events = 18
total_child_certificate_pricing_events = 4
total_child_column_additions = 10
total_child_added_journeys = 106
total_child_completion_bound_retries = 8
total_child_early_branch_triggers = 0
total_child_fathom_events = 3
max_child_lower_bound_gain = 0.0
max_child_corrected_bound_gain = None
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## 解释

本批 branch row 没有 branch-candidate feature log，只能使用 child-width fallback；再加上右删失 row 较多，因此只能做 proof-tail 诊断，不能直接作为 GAT branch-impact 正例训练集。

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
    "y_child_exact_pricing_events",
    "y_child_completion_bound_retries",
    "y_child_early_branch_triggers",
    "y_child_fathom_events",
    "y_child_max_safe_bound_gain",
    "y_child_max_corrected_bound_gain"
  ],
  "child_probe_label_schema": [
    "child_lower_bound_gain",
    "child_max_corrected_node_lb",
    "child_max_corrected_bound_gain",
    "child_pricing_event_count",
    "child_exact_pricing_event_count",
    "child_negative_pricing_event_count",
    "child_completion_bound_retry_count",
    "child_early_branch_trigger_count",
    "child_proof_cpu",
    "child_time_to_first_certificate",
    "child_time_to_fathom",
    "child_fathomed"
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
    "all_children_started": true,
    "bound_reference": 510.74864,
    "branch_bound": 510.74864,
    "branch_feature_source": "child_width_fallback",
    "branch_feature_vector": [
      0.0,
      0.0,
      0.0,
      0.0,
      -1.0,
      -1.0,
      0.466666667,
      0.466666667,
      0.0,
      0.0,
      0.0,
      0.0,
      227.0,
      289.0,
      289.0,
      516.0,
      62.0
    ],
    "branch_labels": {
      "y_active_touch": 1.0,
      "y_child_completion_bound_retries": 4.0,
      "y_child_early_branch_triggers": 0.0,
      "y_child_exact_pricing_events": 9.0,
      "y_child_fathom_events": 1.0,
      "y_child_max_corrected_bound_gain": 0.0,
      "y_child_max_safe_bound_gain": 0.0,
      "y_child_negative_pricing_events": 13.0,
      "y_completion_bound_tail": 1.0,
      "y_early_branch_continues": 0.0,
      "y_inactive_only": 0.0,
      "y_negative_chain_continues": 0.0,
      "y_tail_improved": 0.0
    },
    "branch_node_id": 0,
    "branch_observation_window": 193.488676,
    "branch_rank_in_priority_top": null,
    "branch_rank_in_top": null,
    "branch_time": 58.694028,
    "candidate_count": null,
    "child_count": 2,
    "child_lower_bound_exact": true,
    "children": [
      {
        "active_new_task_set_count": 0,
        "active_replacement_task_set_count": 0,
        "added_journeys": 5,
        "addition_productivity_class_counts": {
          "changed_inactive_only": 1
        },
        "allowed_current_journeys": 227,
        "bound_reference": 510.74864,
        "branch_same_mass": 0.466666667,
        "branch_triggered": true,
        "certificate_pricing_event_count": 1,
        "child_node_id": 1,
        "column_addition_count": 1,
        "completion_bound_retry_count": 2,
        "constraint": "RF(4,12)=same_vehicle",
        "constraint_kind": "same_vehicle",
        "depth": 1,
        "early_branch_trigger_count": 0,
        "exact_pricing_event_count": 3,
        "fathom_event_count": 0,
        "fathom_reason": null,
        "inactive_changed_task_set_count": 5,
        "last_time": 113.896558,
        "lower_bound": 510.74864,
        "lower_bound_exact": true,
        "lower_bound_gain": 0.0,
        "max_corrected_bound_gain": null,
        "max_corrected_node_lb": null,
        "min_best_reduced_cost": -5.847334,
        "negative_journeys_total": 7,
        "negative_pricing_event_count": 4,
        "new_journeys": 5,
        "node_incomplete_reason": null,
        "parent_lower_bound": 0.0,
        "pricing_event_count": 5,
        "replacement_journeys": 0,
        "selected_trips_total": 8,
        "start_time": 58.694306,
        "started": true,
        "time_span": 55.202252,
        "time_to_fathom": null,
        "time_to_first_certificate": 55.133065
      },
      {
        "active_new_task_set_count": 0,
        "active_replacement_task_set_count": 1,
        "added_journeys": 38,
        "addition_productivity_class_counts": {
          "active_replacement_task_set": 1,
          "changed_inactive_only": 3
        },
        "allowed_current_journeys": 289,
        "bound_reference": 510.74864,
        "branch_same_mass": 0.466666667,
        "branch_triggered": false,
        "certificate_pricing_event_count": 1,
        "child_node_id": 2,
        "column_addition_count": 4,
        "completion_bound_retry_count": 2,
        "constraint": "RF(4,12)=separate_vehicle",
        "constraint_kind": "separate_vehicle",
        "depth": 1,
        "early_branch_trigger_count": 0,
        "exact_pricing_event_count": 6,
        "fathom_event_count": 1,
        "fathom_reason": "bound",
        "inactive_changed_task_set_count": 37,
        "last_time": 162.180462,
        "lower_bound": 510.74864,
        "lower_bound_exact": true,
        "lower_bound_gain": 0.0,
        "max_corrected_bound_gain": null,
        "max_corrected_node_lb": null,
        "min_best_reduced_cost": -23.999483833,
        "negative_journeys_total": 41,
        "negative_pricing_event_count": 9,
        "new_journeys": 34,
        "node_incomplete_reason": null,
        "parent_lower_bound": 0.0,
        "pricing_event_count": 11,
        "replacement_journeys": 4,
        "selected_trips_total": 14,
        "start_time": 113.89688,
        "started": true,
        "time_span": 48.283582,
        "time_to_fathom": 48.283582,
        "time_to_first_certificate": 48.258534
      }
    ],
    "depth": 0,
    "eligible_count": null,
    "exact_bound_available": false,
    "first_child_allowed_current_journeys": 227,
    "first_child_column_additions": 1,
    "first_child_completion_bound_retry_count": 2,
    "first_child_early_branch_trigger_count": 0,
    "first_child_negative_pricing_event_count": 4,
    "first_child_time_span": 55.202252,
    "first_started_child_node_id": 1,
    "forced_pair": null,
    "forced_pair_matched": null,
    "label_observation_complete": true,
    "left": "RF(4,12)=same_vehicle",
    "log_end_time": 252.182704,
    "log_file": "BPC_future/results/logs_20260624_full600_randomtw60_tasks20_parallel4/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json.jsonl",
    "log_has_finish": true,
    "max_child_allowed_current_journeys": 289,
    "max_child_corrected_bound_gain": null,
    "max_child_lower_bound_gain": 0.0,
    "min_child_allowed_current_journeys": 227,
    "observed_branch_candidate": null,
    "parent_lower_bound": 0.0,
    "priority_mode": null,
    "priority_top": [],
    "processed_child_count": 2,
    "right": "RF(4,12)=separate_vehicle",
    "right_censored": false,
    "right_kind": "separate_vehicle",
    "run_status": "OPTIMAL",
    "selected": null,
    "selected_matches_branch": null,
    "sum_child_active_new_task_set_count": 0,
    "sum_child_active_replacement_task_set_count": 1,
    "sum_child_added_journeys": 43,
    "sum_child_certificate_pricing_event_count": 2,
    "sum_child_column_additions": 5,
    "sum_child_completion_bound_retry_count": 4,
    "sum_child_early_branch_trigger_count": 0,
    "sum_child_exact_pricing_event_count": 9,
    "sum_child_fathom_event_count": 1,
    "sum_child_inactive_changed_task_set_count": 42,
    "sum_child_negative_pricing_event_count": 13,
    "tail_class": "completion_bound_tail",
    "task_i": 4,
    "task_j": 12,
    "top": [],
    "unprocessed_child_count": 0,
    "usable_for_branch_impact_training": false
  },
  {
    "all_children_started": true,
    "bound_reference": 512.689204,
    "branch_bound": 512.689204,
    "branch_feature_source": "child_width_fallback",
    "branch_feature_vector": [
      1.0,
      0.0,
      0.0,
      0.0,
      -1.0,
      -1.0,
      0.5,
      0.5,
      0.0,
      0.0,
      0.0,
      0.0,
      195.0,
      230.0,
      230.0,
      425.0,
      35.0
    ],
    "branch_labels": {
      "y_active_touch": 0.0,
      "y_child_completion_bound_retries": 4.0,
      "y_child_early_branch_triggers": 0.0,
      "y_child_exact_pricing_events": 9.0,
      "y_child_fathom_events": 2.0,
      "y_child_max_corrected_bound_gain": 0.0,
      "y_child_max_safe_bound_gain": 0.0,
      "y_child_negative_pricing_events": 12.0,
      "y_completion_bound_tail": 1.0,
      "y_early_branch_continues": 0.0,
      "y_inactive_only": 1.0,
      "y_negative_chain_continues": 0.0,
      "y_tail_improved": 0.0
    },
    "branch_node_id": 1,
    "branch_observation_window": 138.286146,
    "branch_rank_in_priority_top": null,
    "branch_rank_in_top": null,
    "branch_time": 113.896558,
    "candidate_count": null,
    "child_count": 2,
    "child_lower_bound_exact": true,
    "children": [
      {
        "active_new_task_set_count": 0,
        "active_replacement_task_set_count": 0,
        "added_journeys": 29,
        "addition_productivity_class_counts": {
          "changed_inactive_only": 2
        },
        "allowed_current_journeys": 195,
        "bound_reference": 512.689204,
        "branch_same_mass": 0.5,
        "branch_triggered": false,
        "certificate_pricing_event_count": 1,
        "child_node_id": 3,
        "column_addition_count": 2,
        "completion_bound_retry_count": 2,
        "constraint": "RF(4,6)=same_vehicle",
        "constraint_kind": "same_vehicle",
        "depth": 2,
        "early_branch_trigger_count": 0,
        "exact_pricing_event_count": 4,
        "fathom_event_count": 1,
        "fathom_reason": "bound",
        "inactive_changed_task_set_count": 29,
        "last_time": 216.627657,
        "lower_bound": 512.689204,
        "lower_bound_exact": true,
        "lower_bound_gain": 0.0,
        "max_corrected_bound_gain": null,
        "max_corrected_node_lb": null,
        "min_best_reduced_cost": -20.735748,
        "negative_journeys_total": 30,
        "negative_pricing_event_count": 4,
        "new_journeys": 26,
        "node_incomplete_reason": null,
        "parent_lower_bound": 510.74864,
        "pricing_event_count": 7,
        "replacement_journeys": 3,
        "selected_trips_total": 6,
        "start_time": 162.180533,
        "started": true,
        "time_span": 54.447124,
        "time_to_fathom": 54.447124,
        "time_to_first_certificate": 54.425904
      },
      {
        "active_new_task_set_count": 0,
        "active_replacement_task_set_count": 0,
        "added_journeys": 34,
        "addition_productivity_class_counts": {
          "changed_inactive_only": 3
        },
        "allowed_current_journeys": 230,
        "bound_reference": 512.689204,
        "branch_same_mass": 0.5,
        "branch_triggered": false,
        "certificate_pricing_event_count": 1,
        "child_node_id": 4,
        "column_addition_count": 3,
        "completion_bound_retry_count": 2,
        "constraint": "RF(4,6)=separate_vehicle",
        "constraint_kind": "separate_vehicle",
        "depth": 2,
        "early_branch_trigger_count": 0,
        "exact_pricing_event_count": 5,
        "fathom_event_count": 1,
        "fathom_reason": "bound",
        "inactive_changed_task_set_count": 34,
        "last_time": 252.182615,
        "lower_bound": 512.689204,
        "lower_bound_exact": true,
        "lower_bound_gain": 0.0,
        "max_corrected_bound_gain": null,
        "max_corrected_node_lb": null,
        "min_best_reduced_cost": -35.644647,
        "negative_journeys_total": 43,
        "negative_pricing_event_count": 8,
        "new_journeys": 33,
        "node_incomplete_reason": null,
        "parent_lower_bound": 510.74864,
        "pricing_event_count": 9,
        "replacement_journeys": 1,
        "selected_trips_total": 14,
        "start_time": 216.627739,
        "started": true,
        "time_span": 35.554876,
        "time_to_fathom": 35.554876,
        "time_to_first_certificate": 35.538412
      }
    ],
    "depth": 1,
    "eligible_count": null,
    "exact_bound_available": false,
    "first_child_allowed_current_journeys": 195,
    "first_child_column_additions": 2,
    "first_child_completion_bound_retry_count": 2,
    "first_child_early_branch_trigger_count": 0,
    "first_child_negative_pricing_event_count": 4,
    "first_child_time_span": 54.447124,
    "first_started_child_node_id": 3,
    "forced_pair": null,
    "forced_pair_matched": null,
    "label_observation_complete": true,
    "left": "RF(4,6)=same_vehicle",
    "log_end_time": 252.182704,
    "log_file": "BPC_future/results/logs_20260624_full600_randomtw60_tasks20_parallel4/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json.jsonl",
    "log_has_finish": true,
    "max_child_allowed_current_journeys": 230,
    "max_child_corrected_bound_gain": null,
    "max_child_lower_bound_gain": 0.0,
    "min_child_allowed_current_journeys": 195,
    "observed_branch_candidate": null,
    "parent_lower_bound": 510.74864,
    "priority_mode": null,
    "priority_top": [],
    "processed_child_count": 2,
    "right": "RF(4,6)=separate_vehicle",
    "right_censored": false,
    "right_kind": "separate_vehicle",
    "run_status": "OPTIMAL",
    "selected": null,
    "selected_matches_branch": null,
    "sum_child_active_new_task_set_count": 0,
    "sum_child_active_replacement_task_set_count": 0,
    "sum_child_added_journeys": 63,
    "sum_child_certificate_pricing_event_count": 2,
    "sum_child_column_additions": 5,
    "sum_child_completion_bound_retry_count": 4,
    "sum_child_early_branch_trigger_count": 0,
    "sum_child_exact_pricing_event_count": 9,
    "sum_child_fathom_event_count": 2,
    "sum_child_inactive_changed_task_set_count": 63,
    "sum_child_negative_pricing_event_count": 12,
    "tail_class": "completion_bound_tail",
    "task_i": 4,
    "task_j": 6,
    "top": [],
    "unprocessed_child_count": 0,
    "usable_for_branch_impact_training": false
  }
]
```
