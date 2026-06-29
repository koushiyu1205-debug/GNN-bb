# GAT Branch/Action Checkpoint Ranking Audit

日期：2026-06-28

## 目的

用 context-local ranking 指标审计 v658/v659 branch/action checkpoint。该审计只读离线 dataset 和 checkpoint，不运行 BPC、pricing、RMP，也不产生 official bound 或 certificate。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_branch_action_sanity/v658_all_counterfactual_delta_rows_20260628
output_dir = BPC_future/results/gat_branch_action_v660_v658_v659_checkpoint_ranking_20260628
run_count = 6
score_map_export_recommended = false
diagnostic_only = true
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
solver_default_effect = false
```

## Validation Ranking

| run | pos/neg | branch AUC/AP/pair | walltime AUC/AP/pair | walltime top1 ctx | best field | gate |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| v658_seed7 | 30/40 | 0.5908/0.4901/0.2432 | 0.4117/0.3627/0.8378 | 0.7500 | branch_priority_probability | validation_comparable_context_lt_5,validation_auc_lt_0_60,validation_context_pairwise_lt_0_60 |
| v658_seed13 | 5/28 | 0.7000/0.3705/0.6667 | 0.6571/0.4500/0.7778 | 0.5000 | branch_priority_probability | validation_positive_count_lt_10,validation_comparable_context_lt_5 |
| v658_seed29 | 14/31 | 0.5945/0.4670/0.6800 | 0.4654/0.3036/0.3000 | 0.2500 | branch_priority_probability | validation_comparable_context_lt_5,validation_auc_lt_0_60 |
| v659_seed7 | 30/40 | 0.5833/0.4644/0.7297 | 0.5600/0.4303/0.7027 | 0.2500 | branch_priority_probability | validation_comparable_context_lt_5,validation_auc_lt_0_60 |
| v659_seed13 | 5/28 | 0.4000/0.1433/0.6667 | 0.6786/0.5256/0.4444 | 0.5000 | predicted_walltime_gain | validation_positive_count_lt_10,validation_comparable_context_lt_5,validation_context_pairwise_lt_0_60 |
| v659_seed29 | 14/31 | 0.7604/0.6849/0.4000 | 0.7811/0.5916/0.6800 | 0.7500 | predicted_walltime_gain | validation_comparable_context_lt_5 |

## 判断

- best_run_by_validation_branch_auc = v659_seed29
- best_validation_score_field = predicted_walltime_gain
- score_map_export_recommended = false
- 当前最有用的信号可能来自 wall-time regression head，而不是 0.5 分类阈值；但 validation 可比 context 数仍不足，不能直接上线。
- 若 gate 未通过，checkpoint 只能继续作为离线诊断，不能导出生产 score map，也不能接入 solver 默认行为。
- branch score 仍只允许影响排序/测试对象选择；official bound、certificate 和 fathom 仍必须来自合法 RMP + exact pricing closure。
