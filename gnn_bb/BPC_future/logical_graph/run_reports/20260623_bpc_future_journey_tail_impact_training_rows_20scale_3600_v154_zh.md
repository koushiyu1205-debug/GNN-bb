# Journey Tail-Impact Training Rows

日期：2026-06-23

## 目的

合成 weak-negative tail 与 branch-impact 两类离线审计 row，为后续 GAT 学习“哪些候选会制造 proof tail、哪些分支会缩短 proof tail”提供统一训练接口。该脚本只读现有审计产物，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_tail_impact_training_rows = current
output_dir = BPC_future/results/journey_tail_impact_training_rows_20scale_3600_v154_20260623
training_row_count = 53
raw_training_row_count = 53
deduplicated_row_count = 0
weak_row_count = 10
branch_row_count = 43
source_counts = {'branch_impact': 43, 'weak_negative_tail': 10}
tail_class_counts = {'completion_bound_tail': 30, 'early_branch_continues': 1, 'unprocessed_children': 12, 'weak_negative_filtered': 10}
label_positive_counts = {'y_useful_tail_reduction': 0, 'y_tail_risk': 53, 'y_weak_negative_filtered': 10, 'y_completion_bound_tail': 30, 'y_early_branch_continues': 1, 'y_negative_chain_continues': 0, 'y_active_touch': 8, 'y_inactive_only': 22, 'y_child_negative_pricing_events': 31, 'y_child_completion_bound_retries': 30, 'y_child_early_branch_triggers': 5}
regression_label_totals = {'child_negative_pricing_events': 257, 'child_completion_bound_retries': 126, 'child_early_branch_triggers': 6}
hard_negative_catalog_ready = true
contrastive_tail_training_ready = false
tail_label_training_ready = false
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## 解释

这一步没有让 20 规模求解变快，也不改变 solver。它把当前失败机制转成统一监督信号：weak-negative row 是 rough/profile 负列信号失效的负例，branch-impact row 是分支后 active-support、negative-chain、completion-bound tail 的结果标签。

如果 `contrastive_tail_training_ready=false`，这批数据只能作为 hard-negative catalog，不能单独训练“选好分支/好候选”的 GAT；下一步必须补能减少 tail 的正例。不能把这些 row 当作剪枝依据或 no-negative certificate。
