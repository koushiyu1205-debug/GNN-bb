# Journey Tail-Impact Training Rows

日期：2026-06-23

## 目的

合成 weak-negative tail、branch-impact、tail-action proof-cost 与 late-negative tail 离线审计 row，为后续 GAT 学习“哪些候选会制造 proof tail、哪些分支会缩短 proof tail、哪些 true-negative 真的改变 active support”提供统一训练接口。该脚本只读现有审计产物，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_tail_impact_training_rows = current
output_dir = BPC_future/results/journey_tail_impact_training_rows_full600_randomtw60_tasks20_20260624
training_row_count = 999
raw_training_row_count = 999
deduplicated_row_count = 0
weak_row_count = 0
branch_row_count = 0
tail_action_row_count = 0
late_negative_row_count = 999
source_counts = {'late_negative_tail': 999}
tail_class_counts = {'true_negative_active_support_changing': 59, 'true_negative_inactive_only': 570, 'true_negative_no_addition_observed': 318, 'weak_false_negative_filtered': 52}
label_positive_counts = {'y_useful_tail_reduction': 0, 'y_tail_risk': 999, 'y_weak_negative_filtered': 117, 'y_completion_bound_tail': 0, 'y_early_branch_continues': 0, 'y_negative_chain_continues': 947, 'y_active_touch': 59, 'y_inactive_only': 570, 'y_child_negative_pricing_events': 0, 'y_child_completion_bound_retries': 0, 'y_child_early_branch_triggers': 0, 'y_tail_action_no_column': 0, 'y_child_unstarted': 0, 'y_subtree_no_column_chain': 0, 'y_late_true_negative': 947, 'y_late_active_support_changing': 59, 'y_late_inactive_only': 570, 'y_late_weak_filtered': 117}
regression_label_totals = {'child_negative_pricing_events': 0, 'child_completion_bound_retries': 0, 'child_early_branch_triggers': 0, 'child_unstarted': 0, 'subtree_no_column_chain': 0, 'late_true_negative': 947, 'late_active_support_changing': 59, 'late_inactive_only': 570, 'late_weak_filtered': 117}
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

## 诊断口径说明

本次 `tail_action_row_count=0` 来自 full600 日志未写 `journey_corrected_node_bound_audit` 事件；这不是 Tail Action Controller 没有触发机会的证据。已在 canonical 20-task 配置中打开 `journey_tail_action_audit_enabled`，后续复验应重新生成 tail-action audit，再把 A/B/C/D、child proof-cost 与 late-negative 行合并。

当前 `999` 行主要来自 late-negative tail，可用于训练/筛选：

- `inactive-only` 真负列 hard negative；
- `active-support-changing` 少量正向候选；
- weak/profile filtered 噪声；
- late true-negative chain 风险。

它还不能单独支撑“有用 tail reduction”或 branch-action policy 训练。
