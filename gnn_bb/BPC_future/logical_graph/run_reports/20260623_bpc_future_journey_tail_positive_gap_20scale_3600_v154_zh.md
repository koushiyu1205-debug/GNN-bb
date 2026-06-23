# Journey Tail Positive Gap Audit

日期：2026-06-23

## 目的

读取 tail-impact training rows，审计是否已经具备可训练的 tail-reduction 正例。该脚本只读离线 artifact，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_tail_positive_gap_audit = current
output_dir = BPC_future/results/journey_tail_positive_gap_audit_20scale_3600_v154_20260623
row_count = 53
source_counts = {'branch_impact': 43, 'weak_negative_tail': 10}
tail_class_counts = {'completion_bound_tail': 30, 'early_branch_continues': 1, 'unprocessed_children': 12, 'weak_negative_filtered': 10}
useful_tail_reduction_positive_count = 0
tail_risk_count = 53
active_touch_count = 8
active_touch_still_tail_risk_count = 8
active_touch_completion_bound_tail_count = 7
active_touch_early_branch_count = 1
active_touch_negative_chain_count = 0
weak_negative_filtered_count = 10
positive_gap_reason = no_useful_tail_reduction_positive
contrastive_tail_training_ready = false
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## 解释

当前数据可以支持 hard-negative suppression：weak-negative filtered、inactive-only、completion-bound tail、early-branch tail 都有证据。但 `useful_tail_reduction_positive_count=0` 时，它不能支持 GAT 学习“哪个候选会加速证明”。

## Near Positive Rows

```json
[
  {
    "depth": 2,
    "log_file": "BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 3,
    "source_type": "branch_impact",
    "tail_badness_score": 66.0,
    "tail_class": "early_branch_continues",
    "task_i": 2,
    "task_j": 7,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 0.0,
    "y_child_early_branch_triggers": 2.0,
    "y_child_negative_pricing_events": 10.0,
    "y_completion_bound_tail": 0.0,
    "y_early_branch_continues": 1.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 3,
    "log_file": "BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 19,
    "source_type": "branch_impact",
    "tail_badness_score": 128.0,
    "tail_class": "completion_bound_tail",
    "task_i": 2,
    "task_j": 7,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 4.0,
    "y_child_early_branch_triggers": 0.0,
    "y_child_negative_pricing_events": 8.0,
    "y_completion_bound_tail": 1.0,
    "y_early_branch_continues": 0.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 6,
    "log_file": "BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 76,
    "source_type": "branch_impact",
    "tail_badness_score": 129.0,
    "tail_class": "completion_bound_tail",
    "task_i": 3,
    "task_j": 8,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 4.0,
    "y_child_early_branch_triggers": 0.0,
    "y_child_negative_pricing_events": 9.0,
    "y_completion_bound_tail": 1.0,
    "y_early_branch_continues": 0.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 5,
    "log_file": "BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 25,
    "source_type": "branch_impact",
    "tail_badness_score": 130.0,
    "tail_class": "completion_bound_tail",
    "task_i": 2,
    "task_j": 7,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 4.0,
    "y_child_early_branch_triggers": 0.0,
    "y_child_negative_pricing_events": 10.0,
    "y_completion_bound_tail": 1.0,
    "y_early_branch_continues": 0.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 5,
    "log_file": "BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 38,
    "source_type": "branch_impact",
    "tail_badness_score": 130.0,
    "tail_class": "completion_bound_tail",
    "task_i": 2,
    "task_j": 4,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 4.0,
    "y_child_early_branch_triggers": 0.0,
    "y_child_negative_pricing_events": 10.0,
    "y_completion_bound_tail": 1.0,
    "y_early_branch_continues": 0.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 1,
    "log_file": "BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 1,
    "source_type": "branch_impact",
    "tail_badness_score": 136.0,
    "tail_class": "completion_bound_tail",
    "task_i": 2,
    "task_j": 3,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 4.0,
    "y_child_early_branch_triggers": 1.0,
    "y_child_negative_pricing_events": 13.0,
    "y_completion_bound_tail": 1.0,
    "y_early_branch_continues": 0.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 3,
    "log_file": "BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 6,
    "source_type": "branch_impact",
    "tail_badness_score": 156.0,
    "tail_class": "completion_bound_tail",
    "task_i": 2,
    "task_j": 6,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 8.0,
    "y_child_early_branch_triggers": 0.0,
    "y_child_negative_pricing_events": 16.0,
    "y_completion_bound_tail": 1.0,
    "y_early_branch_continues": 0.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 3,
    "log_file": "BPC_future/results/journey_20scale_longrun_3600_v154_20260623/gat_on_root56_depth3_width_greedy_apollo20_3600/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 5,
    "source_type": "branch_impact",
    "tail_badness_score": 157.0,
    "tail_class": "completion_bound_tail",
    "task_i": 4,
    "task_j": 9,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 9.0,
    "y_child_early_branch_triggers": 0.0,
    "y_child_negative_pricing_events": 12.0,
    "y_completion_bound_tail": 1.0,
    "y_early_branch_continues": 0.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  }
]
```
