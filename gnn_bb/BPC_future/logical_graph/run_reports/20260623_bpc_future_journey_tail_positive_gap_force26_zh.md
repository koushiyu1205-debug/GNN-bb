# Journey Tail Positive Gap Audit

日期：2026-06-23

## 目的

读取 tail-impact training rows，审计是否已经具备可训练的 tail-reduction 正例。该脚本只读离线 artifact，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_tail_positive_gap_audit = current
output_dir = BPC_future/results/journey_tail_positive_gap_audit_force26_20260623
row_count = 9
source_counts = {'branch_impact': 4, 'weak_negative_tail': 5}
tail_class_counts = {'completion_bound_tail': 1, 'early_branch_continues': 3, 'weak_negative_filtered': 5}
useful_tail_reduction_positive_count = 0
tail_risk_count = 9
active_touch_count = 2
active_touch_still_tail_risk_count = 2
active_touch_completion_bound_tail_count = 1
active_touch_early_branch_count = 1
active_touch_negative_chain_count = 0
weak_negative_filtered_count = 5
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
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_depth3_width_force26_greedy_apollo20_direct200/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 3,
    "source_type": "branch_impact",
    "tail_badness_score": 57.0,
    "tail_class": "early_branch_continues",
    "task_i": 2,
    "task_j": 11,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 0.0,
    "y_child_early_branch_triggers": 1.0,
    "y_child_negative_pricing_events": 4.0,
    "y_completion_bound_tail": 0.0,
    "y_early_branch_continues": 1.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 3,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_depth3_width_force26_greedy_apollo20_direct200/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 5,
    "source_type": "branch_impact",
    "tail_badness_score": 113.0,
    "tail_class": "completion_bound_tail",
    "task_i": 4,
    "task_j": 5,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 1.0,
    "y_child_early_branch_triggers": 0.0,
    "y_child_negative_pricing_events": 8.0,
    "y_completion_bound_tail": 1.0,
    "y_early_branch_continues": 0.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  }
]
```
