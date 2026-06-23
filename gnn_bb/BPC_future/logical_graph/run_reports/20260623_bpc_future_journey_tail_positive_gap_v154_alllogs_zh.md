# Journey Tail Positive Gap Audit

日期：2026-06-23

## 目的

读取 tail-impact training rows，审计是否已经具备可训练的 tail-reduction 正例。该脚本只读离线 artifact，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_tail_positive_gap_audit = current
output_dir = BPC_future/results/journey_tail_positive_gap_audit_v154_alllogs_20260623
row_count = 130
source_counts = {'branch_impact': 109, 'weak_negative_tail': 21}
tail_class_counts = {'completion_bound_tail': 72, 'early_branch_continues': 14, 'negative_chain_continues': 6, 'node_incomplete_tail': 1, 'unprocessed_children': 16, 'weak_negative_filtered': 21}
useful_tail_reduction_positive_count = 0
tail_risk_count = 130
active_touch_count = 15
active_touch_still_tail_risk_count = 15
active_touch_completion_bound_tail_count = 6
active_touch_early_branch_count = 7
active_touch_negative_chain_count = 2
weak_negative_filtered_count = 21
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
    "depth": 3,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_no_column_depth3_width_greedy_apollo20_direct200/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 5,
    "source_type": "branch_impact",
    "tail_badness_score": 36.0,
    "tail_class": "negative_chain_continues",
    "task_i": 2,
    "task_j": 6,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 0.0,
    "y_child_early_branch_triggers": 0.0,
    "y_child_negative_pricing_events": 6.0,
    "y_completion_bound_tail": 0.0,
    "y_early_branch_continues": 0.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 1.0
  },
  {
    "depth": 1,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root55_child3_width_greedy_apollo20_direct200/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 1,
    "source_type": "branch_impact",
    "tail_badness_score": 41.0,
    "tail_class": "negative_chain_continues",
    "task_i": 17,
    "task_j": 20,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 0.0,
    "y_child_early_branch_triggers": 0.0,
    "y_child_negative_pricing_events": 11.0,
    "y_completion_bound_tail": 0.0,
    "y_early_branch_continues": 0.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 1.0
  },
  {
    "depth": 1,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_no_column_depth2_width_greedy_apollo20_direct200/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 1,
    "source_type": "branch_impact",
    "tail_badness_score": 58.0,
    "tail_class": "early_branch_continues",
    "task_i": 2,
    "task_j": 3,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 0.0,
    "y_child_early_branch_triggers": 1.0,
    "y_child_negative_pricing_events": 5.0,
    "y_completion_bound_tail": 0.0,
    "y_early_branch_continues": 1.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 1,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_no_column_depth3_width_greedy_apollo20_direct200/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 1,
    "source_type": "branch_impact",
    "tail_badness_score": 58.0,
    "tail_class": "early_branch_continues",
    "task_i": 2,
    "task_j": 3,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 0.0,
    "y_child_early_branch_triggers": 1.0,
    "y_child_negative_pricing_events": 5.0,
    "y_completion_bound_tail": 0.0,
    "y_early_branch_continues": 1.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 1,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_no_column_depth3_width_selectedlog_refresh_greedy_apollo20_direct200/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 1,
    "source_type": "branch_impact",
    "tail_badness_score": 58.0,
    "tail_class": "early_branch_continues",
    "task_i": 2,
    "task_j": 3,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 0.0,
    "y_child_early_branch_triggers": 1.0,
    "y_child_negative_pricing_events": 5.0,
    "y_completion_bound_tail": 0.0,
    "y_early_branch_continues": 1.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 0,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_no_column_poolsplit_width_greedy_apollo20_direct200/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 0,
    "source_type": "branch_impact",
    "tail_badness_score": 58.0,
    "tail_class": "early_branch_continues",
    "task_i": 2,
    "task_j": 13,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 0.0,
    "y_child_early_branch_triggers": 1.0,
    "y_child_negative_pricing_events": 5.0,
    "y_completion_bound_tail": 0.0,
    "y_early_branch_continues": 1.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 0,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_no_column_poolsplit_width_scan8_selectedlog_greedy_apollo20_direct200/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 0,
    "source_type": "branch_impact",
    "tail_badness_score": 58.0,
    "tail_class": "early_branch_continues",
    "task_i": 2,
    "task_j": 13,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 0.0,
    "y_child_early_branch_triggers": 1.0,
    "y_child_negative_pricing_events": 5.0,
    "y_completion_bound_tail": 0.0,
    "y_early_branch_continues": 1.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 0,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_no_column_poolsplit_width_selectedlog_refresh_greedy_apollo20_direct200/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 0,
    "source_type": "branch_impact",
    "tail_badness_score": 58.0,
    "tail_class": "early_branch_continues",
    "task_i": 2,
    "task_j": 13,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 0.0,
    "y_child_early_branch_triggers": 1.0,
    "y_child_negative_pricing_events": 5.0,
    "y_completion_bound_tail": 0.0,
    "y_early_branch_continues": 1.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 0,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root55_child3_width_greedy_apollo20_direct200/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 0,
    "source_type": "branch_impact",
    "tail_badness_score": 59.0,
    "tail_class": "early_branch_continues",
    "task_i": 2,
    "task_j": 3,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 0.0,
    "y_child_early_branch_triggers": 1.0,
    "y_child_negative_pricing_events": 6.0,
    "y_completion_bound_tail": 0.0,
    "y_early_branch_continues": 1.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 2,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/sector_tranq_static_src_tl200/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json.jsonl",
    "node_id": 5,
    "source_type": "branch_impact",
    "tail_badness_score": 107.0,
    "tail_class": "completion_bound_tail",
    "task_i": 4,
    "task_j": 7,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 1.0,
    "y_child_early_branch_triggers": 0.0,
    "y_child_negative_pricing_events": 2.0,
    "y_completion_bound_tail": 1.0,
    "y_early_branch_continues": 0.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 1,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_early_branch_child3_width_greedy_apollo20_direct200/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 1,
    "source_type": "branch_impact",
    "tail_badness_score": 112.0,
    "tail_class": "completion_bound_tail",
    "task_i": 2,
    "task_j": 3,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 1.0,
    "y_child_early_branch_triggers": 0.0,
    "y_child_negative_pricing_events": 7.0,
    "y_completion_bound_tail": 1.0,
    "y_early_branch_continues": 0.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  },
  {
    "depth": 1,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/gat_on_root56_no_column_branch_width_greedy_apollo20_direct200/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "node_id": 1,
    "source_type": "branch_impact",
    "tail_badness_score": 120.0,
    "tail_class": "completion_bound_tail",
    "task_i": 2,
    "task_j": 3,
    "y_active_touch": 1.0,
    "y_child_completion_bound_retries": 2.0,
    "y_child_early_branch_triggers": 0.0,
    "y_child_negative_pricing_events": 10.0,
    "y_completion_bound_tail": 1.0,
    "y_early_branch_continues": 0.0,
    "y_inactive_only": 0.0,
    "y_negative_chain_continues": 0.0
  }
]
```
