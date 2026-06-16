# 2026-06-16 BPC_future GAT Stage 3 v21 Train-Split Sector Contrast Runbook 交接报告

## 结论

已重读五阶段主计划以及 v15 到 v20 的关键报告。当前下一步不是继续盲调
threshold / loss multiplier，而是补 train split 的 same-context sector-wave
task20 contrast 数据。

v15 missed high-ROI 不是“分数差一点”的问题：v15/v17/v18 的 margin audit 都显示
大量 missed high-ROI 是 candidate-level deep / moderate score gap；v19/v20 的
pairwise margin 能减少 low-ROI / bad admission，但会牺牲 coverage 和 safe
precision CI；v18/v19/v20 cross-checkpoint selector 也没有找到可行组合规则。

因此 v21 的目标是：在不污染 validation holdout 的前提下，生成 train-split
`sector-wave` task20 same-context intervention 候选，让下一轮 worker A/B 能回答
candidate head 是缺 contrast，还是模型结构仍然分不开。

## 已完成的 offline artifact

新增 family 过滤能力：

```text
script =
  BPC_future/scripts/build_gat_batch_impact_multibatch_intervention_plan.py
new_arg =
  --include-families
test =
  BPC_future/tests/test_gat_batch_impact_multibatch_intervention_plan.py
```

v21 full train-split sector contrast plan：

```text
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v21_train_split_sector_contrast_plan_zh.md
summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_20260616/summary.json
worker_ab_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_20260616/worker_ab_runbook/summary.json

split_mode = train
split_instance_count = 40
include_families = ['sector-wave']
include_task_counts = [20]
selected_context_count = 6
candidate_count = 18
candidate_task_count_counts = {'20': 18}
candidate_family_region_counts =
  {'sector-wave|apollo15_20km': 15,
   'sector-wave|tranquillitatis_balmer_like_20km': 3}
candidate_selection_ranking_counts =
  {'active_replacement': 6, 'best_rc': 6, 'impact': 6}
candidate_impact_bucket_counts =
  {'new_support_changing': 12, 'new_task_set': 2, 'replacement_like': 4}
all_checks_pass = true
```

first-tranche 子集和 guarded runbook：

```text
subset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v21_train_split_sector_contrast_first_tranche_zh.md
subset_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/summary.json
worker_ab_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/summary.json

selected_context_count = 3
candidate_count = 9
candidate_context_counts =
  {'0df8d5cea7864e69': 3,
   'b9550ffc9a42531a': 3,
   '4e481a6307fca228': 3}
candidate_family_counts = {'sector-wave': 9}
candidate_task_count_counts = {'20': 9}
candidate_group_count = 9
worker_method = target_materialization_fixed
worker_batch_size = 1
all_checks_pass = true
```

## 边界

这些 artifact 只是 offline 计划和 runbook builder 输出：

```text
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
official_bound_effect = false
certificate_ready = false
```

candidate 都是 materialized true-RC negative，但 true-RC negative 不等于
`HIGH_PRIORITY` 正例。worker 跑完前，所有候选标签都必须保持 blocked；只有
expected-context reachability、target causal match、trajectory ROI 和 certificate
audit 全部完成后，才允许回流训练。

最终 certificate 仍只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的
exhaustive no-negative closure；GAT / CBF / kNN / OOD / worker / delay queue 都不能
证明 no-negative。

## 下一步

1. 显式执行 first-tranche guarded worker A/B runbook。
2. 审计 reachability、target causal match、trajectory ROI、tail-risk 和 certificate。
3. 用 reachability summary 过滤 worker rows，构造 v21 train-side rows。
4. 构建 v21 dataset，确认新增的是 train split same-context contrast。
5. 重训并检查 accepted count、safe precision CI、false-safe、family ROI。
6. 若仍是 deep / moderate score gap，再改 candidate head、context-local margin 或
   batch-candidate interaction；仍不得降低 Stage 3/4 hard gate。
