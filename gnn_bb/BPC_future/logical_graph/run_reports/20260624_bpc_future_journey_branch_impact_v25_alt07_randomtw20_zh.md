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
tail_class_counts = {'completion_bound_tail': 1}
priority_mode_counts = {'force_pair_path:0:1,18': 1}
selected_match_count = 1
top_contains_branch_count = 1
top_first_branch_count = 0
priority_top_first_branch_count = 1
candidate_log_branch_count = 1
forced_pair_branch_count = 1
forced_pair_matched_branch_count = 1
right_censored_branch_count = 0
complete_label_branch_count = 1
usable_branch_impact_training_count = 1
run_status_counts = {'OPTIMAL': 1}
active_touch_branch_count = 1
inactive_only_branch_count = 0
unprocessed_child_count = 0
total_child_negative_pricing_events = 11
total_child_column_additions = 6
total_child_added_journeys = 82
total_child_completion_bound_retries = 4
total_child_early_branch_triggers = 0
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## 解释

分支后主要瓶颈进入 completion-bound 证明尾段；GAT 不能替代证书，只能作为候选列发现器，需要另行优化 exact final judge 或训练能减少证书尾部状态空间的标签。

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
    "all_children_started": true,
    "branch_feature_source": "candidate_log",
    "branch_feature_vector": [
      0.0,
      28.0,
      11.0,
      1.0,
      5.0,
      0.0,
      0.5,
      0.5,
      1.0,
      1.0,
      0.0,
      0.5,
      136.0,
      154.0,
      154.0,
      290.0,
      18.0
    ],
    "branch_labels": {
      "y_active_touch": 1.0,
      "y_child_completion_bound_retries": 4.0,
      "y_child_early_branch_triggers": 0.0,
      "y_child_negative_pricing_events": 11.0,
      "y_completion_bound_tail": 1.0,
      "y_early_branch_continues": 0.0,
      "y_inactive_only": 0.0,
      "y_negative_chain_continues": 0.0,
      "y_tail_improved": 0.0
    },
    "branch_node_id": 0,
    "branch_observation_window": 25.704409,
    "branch_rank_in_priority_top": 0,
    "branch_rank_in_top": 5,
    "branch_time": 11.507301,
    "candidate_count": 28,
    "child_count": 2,
    "child_lower_bound_exact": true,
    "children": [
      {
        "active_new_task_set_count": 0,
        "active_replacement_task_set_count": 2,
        "added_journeys": 49,
        "addition_productivity_class_counts": {
          "active_replacement_task_set": 1,
          "changed_inactive_only": 2
        },
        "allowed_current_journeys": 136,
        "branch_same_mass": 0.5,
        "branch_triggered": false,
        "child_node_id": 1,
        "column_addition_count": 3,
        "completion_bound_retry_count": 2,
        "constraint": "RF(1,18)=same_vehicle",
        "constraint_kind": "same_vehicle",
        "depth": 1,
        "early_branch_trigger_count": 0,
        "inactive_changed_task_set_count": 47,
        "last_time": 26.702717,
        "lower_bound": 551.306271,
        "lower_bound_exact": true,
        "min_best_reduced_cost": -43.036012333,
        "negative_journeys_total": 49,
        "negative_pricing_event_count": 8,
        "new_journeys": 38,
        "node_incomplete_reason": null,
        "pricing_event_count": 10,
        "replacement_journeys": 11,
        "selected_trips_total": 6,
        "start_time": 11.507462,
        "started": true,
        "time_span": 15.195255
      },
      {
        "active_new_task_set_count": 0,
        "active_replacement_task_set_count": 1,
        "added_journeys": 33,
        "addition_productivity_class_counts": {
          "active_replacement_task_set": 1,
          "changed_inactive_only": 2
        },
        "allowed_current_journeys": 154,
        "branch_same_mass": 0.5,
        "branch_triggered": false,
        "child_node_id": 2,
        "column_addition_count": 3,
        "completion_bound_retry_count": 2,
        "constraint": "RF(1,18)=separate_vehicle",
        "constraint_kind": "separate_vehicle",
        "depth": 1,
        "early_branch_trigger_count": 0,
        "inactive_changed_task_set_count": 32,
        "last_time": 37.211627,
        "lower_bound": 551.306271,
        "lower_bound_exact": true,
        "min_best_reduced_cost": -21.756242,
        "negative_journeys_total": 34,
        "negative_pricing_event_count": 3,
        "new_journeys": 25,
        "node_incomplete_reason": null,
        "pricing_event_count": 9,
        "replacement_journeys": 8,
        "selected_trips_total": 6,
        "start_time": 26.702788,
        "started": true,
        "time_span": 10.508839
      }
    ],
    "depth": 0,
    "eligible_count": 11,
    "exact_bound_available": false,
    "first_child_allowed_current_journeys": 136,
    "first_child_column_additions": 3,
    "first_child_completion_bound_retry_count": 2,
    "first_child_early_branch_trigger_count": 0,
    "first_child_negative_pricing_event_count": 8,
    "first_child_time_span": 15.195255,
    "first_started_child_node_id": 1,
    "forced_pair": [
      1,
      18
    ],
    "forced_pair_matched": true,
    "label_observation_complete": true,
    "left": "RF(1,18)=same_vehicle",
    "log_end_time": 37.21171,
    "log_file": "BPC_future/results/journey_branch_impact_alt_runbook_v25_from_v24_20260624/runs/07_branch_alt_pair_d0_n0_r5_1_18_tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json.jsonl",
    "log_has_finish": true,
    "max_child_allowed_current_journeys": 154,
    "min_child_allowed_current_journeys": 136,
    "observed_branch_candidate": {
      "fractionality": 0.5,
      "incumbent_disagreement": 0.5,
      "incumbent_relation": false,
      "pool_balance_gap": 18,
      "pool_max_child_width": 154,
      "pool_same_allowed": 136,
      "pool_separate_allowed": 154,
      "pool_total_child_width": 290,
      "same_mass": 0.5,
      "support_count": 1,
      "task_i": 1,
      "task_j": 18
    },
    "priority_mode": "force_pair_path:0:1,18",
    "priority_top": [
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 18,
        "pool_max_child_width": 154,
        "pool_same_allowed": 136,
        "pool_separate_allowed": 154,
        "pool_total_child_width": 290,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 1,
        "task_j": 18
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": true,
        "pool_balance_gap": 26,
        "pool_max_child_width": 159,
        "pool_same_allowed": 133,
        "pool_separate_allowed": 159,
        "pool_total_child_width": 292,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 1,
        "task_j": 2
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": true,
        "pool_balance_gap": 21,
        "pool_max_child_width": 157,
        "pool_same_allowed": 136,
        "pool_separate_allowed": 157,
        "pool_total_child_width": 293,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 1,
        "task_j": 4
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 38,
        "pool_max_child_width": 162,
        "pool_same_allowed": 124,
        "pool_separate_allowed": 162,
        "pool_total_child_width": 286,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 1,
        "task_j": 6
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 36,
        "pool_max_child_width": 161,
        "pool_same_allowed": 125,
        "pool_separate_allowed": 161,
        "pool_total_child_width": 286,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 1,
        "task_j": 7
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": true,
        "pool_balance_gap": 33,
        "pool_max_child_width": 158,
        "pool_same_allowed": 125,
        "pool_separate_allowed": 158,
        "pool_total_child_width": 283,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 1,
        "task_j": 11
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 26,
        "pool_max_child_width": 159,
        "pool_same_allowed": 133,
        "pool_separate_allowed": 159,
        "pool_total_child_width": 292,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 2,
        "task_j": 18
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 21,
        "pool_max_child_width": 157,
        "pool_same_allowed": 136,
        "pool_separate_allowed": 157,
        "pool_total_child_width": 293,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 4,
        "task_j": 18
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 38,
        "pool_max_child_width": 162,
        "pool_same_allowed": 124,
        "pool_separate_allowed": 162,
        "pool_total_child_width": 286,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 6,
        "task_j": 18
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 39,
        "pool_max_child_width": 162,
        "pool_same_allowed": 123,
        "pool_separate_allowed": 162,
        "pool_total_child_width": 285,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 7,
        "task_j": 18
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 36,
        "pool_max_child_width": 159,
        "pool_same_allowed": 123,
        "pool_separate_allowed": 159,
        "pool_total_child_width": 282,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 11,
        "task_j": 18
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": false,
        "pool_balance_gap": 17,
        "pool_max_child_width": 161,
        "pool_same_allowed": 144,
        "pool_separate_allowed": 161,
        "pool_total_child_width": 305,
        "same_mass": 0.666666667,
        "support_count": 1,
        "task_i": 5,
        "task_j": 12
      }
    ],
    "processed_child_count": 2,
    "right": "RF(1,18)=separate_vehicle",
    "right_censored": false,
    "right_kind": "separate_vehicle",
    "run_status": "OPTIMAL",
    "selected": {
      "fractionality": 0.5,
      "incumbent_disagreement": 0.5,
      "incumbent_relation": false,
      "pool_balance_gap": 18,
      "pool_max_child_width": 154,
      "pool_same_allowed": 136,
      "pool_separate_allowed": 154,
      "pool_total_child_width": 290,
      "same_mass": 0.5,
      "support_count": 1,
      "task_i": 1,
      "task_j": 18
    },
    "selected_matches_branch": true,
    "sum_child_active_new_task_set_count": 0,
    "sum_child_active_replacement_task_set_count": 3,
    "sum_child_added_journeys": 82,
    "sum_child_column_additions": 6,
    "sum_child_completion_bound_retry_count": 4,
    "sum_child_early_branch_trigger_count": 0,
    "sum_child_inactive_changed_task_set_count": 79,
    "sum_child_negative_pricing_event_count": 11,
    "tail_class": "completion_bound_tail",
    "task_i": 1,
    "task_j": 18,
    "top": [
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": true,
        "pool_balance_gap": 26,
        "pool_max_child_width": 159,
        "pool_same_allowed": 133,
        "pool_separate_allowed": 159,
        "pool_total_child_width": 292,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 1,
        "task_j": 2
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": true,
        "pool_balance_gap": 21,
        "pool_max_child_width": 157,
        "pool_same_allowed": 136,
        "pool_separate_allowed": 157,
        "pool_total_child_width": 293,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 1,
        "task_j": 4
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 38,
        "pool_max_child_width": 162,
        "pool_same_allowed": 124,
        "pool_separate_allowed": 162,
        "pool_total_child_width": 286,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 1,
        "task_j": 6
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 36,
        "pool_max_child_width": 161,
        "pool_same_allowed": 125,
        "pool_separate_allowed": 161,
        "pool_total_child_width": 286,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 1,
        "task_j": 7
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": true,
        "pool_balance_gap": 33,
        "pool_max_child_width": 158,
        "pool_same_allowed": 125,
        "pool_separate_allowed": 158,
        "pool_total_child_width": 283,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 1,
        "task_j": 11
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 18,
        "pool_max_child_width": 154,
        "pool_same_allowed": 136,
        "pool_separate_allowed": 154,
        "pool_total_child_width": 290,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 1,
        "task_j": 18
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 26,
        "pool_max_child_width": 159,
        "pool_same_allowed": 133,
        "pool_separate_allowed": 159,
        "pool_total_child_width": 292,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 2,
        "task_j": 18
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 21,
        "pool_max_child_width": 157,
        "pool_same_allowed": 136,
        "pool_separate_allowed": 157,
        "pool_total_child_width": 293,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 4,
        "task_j": 18
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 38,
        "pool_max_child_width": 162,
        "pool_same_allowed": 124,
        "pool_separate_allowed": 162,
        "pool_total_child_width": 286,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 6,
        "task_j": 18
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 39,
        "pool_max_child_width": 162,
        "pool_same_allowed": 123,
        "pool_separate_allowed": 162,
        "pool_total_child_width": 285,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 7,
        "task_j": 18
      },
      {
        "fractionality": 0.5,
        "incumbent_disagreement": 0.5,
        "incumbent_relation": false,
        "pool_balance_gap": 36,
        "pool_max_child_width": 159,
        "pool_same_allowed": 123,
        "pool_separate_allowed": 159,
        "pool_total_child_width": 282,
        "same_mass": 0.5,
        "support_count": 1,
        "task_i": 11,
        "task_j": 18
      },
      {
        "fractionality": 0.333333333,
        "incumbent_disagreement": 0.666666667,
        "incumbent_relation": false,
        "pool_balance_gap": 17,
        "pool_max_child_width": 161,
        "pool_same_allowed": 144,
        "pool_separate_allowed": 161,
        "pool_total_child_width": 305,
        "same_mass": 0.666666667,
        "support_count": 1,
        "task_i": 5,
        "task_j": 12
      }
    ],
    "unprocessed_child_count": 0,
    "usable_for_branch_impact_training": true
  }
]
```
