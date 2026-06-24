# Journey Tail-Impact Training Rows

日期：2026-06-23

## 目的

合成 weak-negative tail、branch-impact、tail-action proof-cost 与 late-negative tail 离线审计 row，为后续 GAT 学习“哪些候选会制造 proof tail、哪些分支会缩短 proof tail、哪些 true-negative 真的改变 active support”提供统一训练接口。该脚本只读现有审计产物，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_tail_impact_training_rows = current
output_dir = BPC_future/results/journey_tail_impact_training_rows_v16_late_negative_v12_after150_20260624
training_row_count = 7
raw_training_row_count = 7
deduplicated_row_count = 0
weak_row_count = 0
branch_row_count = 0
tail_action_row_count = 3
late_negative_row_count = 4
source_counts = {'late_negative_tail': 4, 'tail_action_proof_cost': 3}
tail_class_counts = {'tail_action_branch': 1, 'tail_action_no_column': 2, 'true_negative_active_support_changing': 2, 'true_negative_inactive_only': 2}
label_positive_counts = {'y_useful_tail_reduction': 0, 'y_tail_risk': 7, 'y_weak_negative_filtered': 0, 'y_completion_bound_tail': 0, 'y_early_branch_continues': 1, 'y_negative_chain_continues': 5, 'y_active_touch': 2, 'y_inactive_only': 2, 'y_child_negative_pricing_events': 1, 'y_child_completion_bound_retries': 0, 'y_child_early_branch_triggers': 1, 'y_tail_action_no_column': 2, 'y_child_unstarted': 2, 'y_subtree_no_column_chain': 1, 'y_late_true_negative': 4, 'y_late_active_support_changing': 2, 'y_late_inactive_only': 2, 'y_late_weak_filtered': 0}
regression_label_totals = {'child_negative_pricing_events': 3, 'child_completion_bound_retries': 0, 'child_early_branch_triggers': 2, 'child_unstarted': 3, 'subtree_no_column_chain': 2, 'late_true_negative': 4, 'late_active_support_changing': 2, 'late_inactive_only': 2, 'late_weak_filtered': 0}
hard_negative_catalog_ready = true
contrastive_tail_training_ready = false
tail_label_training_ready = false
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## 解释

这一步没有让 20 规模求解变快，也不改变 solver。它把当前失败机制转成统一监督信号：weak-negative row 是 rough/profile 负列信号失效的负例，branch-impact row 是分支后 active-support、negative-chain、completion-bound tail 的结果标签，tail-action row 记录 early branch 后子树的 proof-cost 和 no-column 链条，late-negative row 则区分 true negative 是 active-support-changing 还是 inactive-only。

如果 `contrastive_tail_training_ready=false`，这批数据只能作为 hard-negative catalog，不能单独训练“选好分支/好候选”的 GAT；下一步必须补能减少 tail 的正例。不能把这些 row 当作剪枝依据或 no-negative certificate。
