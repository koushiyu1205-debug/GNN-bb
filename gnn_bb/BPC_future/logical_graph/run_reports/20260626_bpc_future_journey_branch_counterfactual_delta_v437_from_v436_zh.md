# Journey Branch Counterfactual Delta v437 from v436

日期：2026-06-26

## 目的

把 v436 selection-gate smoke 的真实整实例结果转成 branch/action 训练 row。该脚本只读完成的结果和日志，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。

## 机器字段

```text
analysis = BPC_future/results/20260626_v436_branch_score_selection_gate062_smoke20_topscore12/analysis_summary.json
output_dir = BPC_future/results/journey_branch_counterfactual_delta_v437_from_v436_selection_gate062_20260626
row_count = 8
label_type_counts = {'changed_timeout_no_effect_hard_negative': 6, 'strong_positive': 2}
status_pair_counts = {'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 6, 'EXTERNAL_TIME_LIMIT->OPTIMAL': 1, 'OPTIMAL->OPTIMAL': 1}
skipped_counts = {'root_not_changed': 4}
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## 边界

这些 row 只用于训练 branch 候选排序和 gate；不能作为剪枝依据，不能替代 exact pricing closure。
