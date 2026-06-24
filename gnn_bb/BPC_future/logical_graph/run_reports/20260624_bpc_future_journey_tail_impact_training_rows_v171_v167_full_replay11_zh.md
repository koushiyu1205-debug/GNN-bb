# Journey Tail-Impact Training Rows

日期：2026-06-24

## 目的

合成 weak-negative tail、branch-impact、tail-action proof-cost、tail-action counterfactual delta 与 late-negative tail 离线审计 row，为后续 GAT 学习“哪些候选会制造 proof tail、哪些分支会缩短 proof tail、哪些 true-negative 真的改变 active support”提供统一训练接口。该脚本只读现有审计产物，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_tail_impact_training_rows = current
output_dir = BPC_future/results/journey_tail_impact_training_rows_v171_v167_full_replay11_20260624
training_row_count = 28
raw_training_row_count = 28
deduplicated_row_count = 0
weak_row_count = 0
branch_row_count = 0
tail_action_row_count = 28
tail_action_counterfactual_row_count = 0
late_negative_row_count = 0
source_counts = {'tail_action_proof_cost': 28}
tail_class_counts = {'tail_action_no_column': 28}
label_positive_counts = {'y_useful_tail_reduction': 0, 'y_tail_risk': 28, 'y_weak_negative_filtered': 0, 'y_completion_bound_tail': 28, 'y_early_branch_continues': 0, 'y_negative_chain_continues': 28, 'y_active_touch': 0, 'y_inactive_only': 0, 'y_child_negative_pricing_events': 28, 'y_child_completion_bound_retries': 28, 'y_child_early_branch_triggers': 0, 'y_tail_action_no_column': 28, 'y_tail_action_counterfactual': 0, 'y_local_tail_improved': 0, 'y_whole_run_improved': 0, 'y_local_improved_but_whole_run_not': 0, 'y_timeout_resolved': 0, 'y_timeout_regression': 0, 'y_right_censored_counterfactual': 0, 'y_child_unstarted': 0, 'y_subtree_no_column_chain': 0, 'y_late_true_negative': 0, 'y_late_active_support_changing': 0, 'y_late_inactive_only': 0, 'y_late_weak_filtered': 0}
regression_label_totals = {'child_negative_pricing_events': 342, 'child_completion_bound_retries': 362, 'child_early_branch_triggers': 0, 'child_unstarted': 0, 'subtree_no_column_chain': 0, 'late_true_negative': 0, 'late_active_support_changing': 0, 'late_inactive_only': 0, 'late_weak_filtered': 0, 'tail_action_counterfactual': 0, 'local_tail_improved': 0, 'whole_run_improved': 0, 'local_improved_but_whole_run_not': 0, 'right_censored_counterfactual': 0}
hard_negative_catalog_ready = true
contrastive_tail_training_ready = false
tail_label_training_ready = false
production_ready = false
stage4_candidate_ready = false
certificate_effect = false
official_bound_effect = false
```

## 解释

这一步没有让 20 规模求解变快，也不改变 solver。它把当前失败机制转成统一监督信号：weak-negative row 是 rough/profile 负列信号失效的负例，branch-impact row 是分支后 active-support、negative-chain、completion-bound tail 的结果标签，tail-action row 记录 early branch 后子树的 proof-cost 和 no-column 链条，tail-action counterfactual delta row 区分 local-only improvement 与 whole-run improvement，late-negative row 则区分 true negative 是 active-support-changing 还是 inactive-only。

如果 `contrastive_tail_training_ready=false`，这批数据只能作为 hard-negative catalog，不能单独训练“选好分支/好候选”的 GAT；下一步必须补能减少 tail 的正例。不能把这些 row 当作剪枝依据或 no-negative certificate。
