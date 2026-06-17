# 2026-06-16 BPC_future GAT Stage 3/4 v53 Post-v51 Follow-up Runbook 综合报告

## 读取范围

本轮复读了 `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`、Stage 1/2 基础报告、Stage 3 v45/v46/v51/v52、Stage 4 v14/v38/v50，以及 Stage 5 的 20/30/50/100 exact-safe 加速目标。

目标模式保持不变：

```text
Learning-guided discovery, exact-certified closure
```

GAT / CBF / kNN / OOD 只能做 discovery、ordering 和 finite-delay admission scheduling；进入 RMP 的列必须 true-RC verified；最终 certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive no-negative closure。

## 背景

v51/v52 的新结论是：

```text
false_delay_safe_epoch_count = 3
coverage_confidence_ready_epoch_count = 3
coverage_and_false_delay_safe_epoch_count = 0
checkpoint_selection_is_primary_blocker = false
recommended_next_step = not_a_checkpoint_selection_problem_collect_context_local_hard_negatives
```

这说明当前不是“选错 epoch”或“阈值差一点”，而是同一 context 内缺少足够的 action consequence 监督。安全壳可以出现，但覆盖不足；覆盖一上来，false-delay 又回到 0.418 到 0.425 量级。

v50 又确认：

```text
reachable_target_intervention_count = 4
positive_trajectory_roi_count = 0
nonpositive_trajectory_roi_count = 4
positive_objective_improvement_count = 4
```

也就是说，即时 RMP objective improvement 仍会误导标签；下一批数据必须拆 individual target，而不是继续把 batch3 合在一起当整体正例或整体负例。

## v53 本轮产物

### 1. Post-v51 individual follow-up subset

```text
subset_summary =
  BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/summary.json

subset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v53_post_v51_individual_followup_subset_zh.md

source_candidate_count = 15
selected_context_count = 3
candidate_count = 9
candidate_context_counts = {
  'ac056820151e9ad7': 3,
  '79fde658840fe2b8': 3,
  'ac15bc4e7e3d6fff': 3
}
exclude_context_hashes = ['7b430465c7ae76b3', 'b6d808ebac2a6dd8']
all_checks_pass = true
```

筛选逻辑：

- 保留 `ac056820151e9ad7`：v41 中 33/44 false positive 集中在这里，是最大 false-delay blocker；v50 batch3 是 negative retry ROI，需要 individual attribution。
- 保留 `79fde658840fe2b8`：v50 是 negative primal ROI，适合作为 high-confidence hard-negative context，拆 individual target 可确认是否所有子目标都 harmful。
- 保留 `ac15bc4e7e3d6fff`：v50 是 negative primal ROI，且 columns 降低仍伴随 primal 变差，适合训练模型识别“workload 看似改善但 trajectory 有害”的动作后果。
- 排除 `7b430465c7ae76b3`：v50 reachability audit 显示 `worker_context_not_reached`，不能写训练标签，除非后续专门 recapture。
- 排除 `b6d808ebac2a6dd8`：v38 individual 与 v50 batch 都没有正 trajectory ROI，当前降级为 workload-only / ambiguous；不应继续当 high-ROI anchor。

### 2. Guarded worker A/B runbook

```text
worker_runbook_summary =
  BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook/summary.json

worker_runbook_report =
  BPC_future/results/gat_batch_impact_false_delay_context_plan_v53_post_v51_individual_followup_subset_20260616/worker_ab_runbook.md

status = ready
worker_method = target_materialization_fixed
worker_batch_size = 1
input_candidate_count = 9
candidate_group_count = 9
command_count = 20
all_checks_pass = true
production_ready = false
certificate_ready = false
official_bound_effect = false
```

`command_count=20` 包括：

- 2 条 5/10 no-regression pass-through 命令；
- 9 组 task20 baseline；
- 9 组 task20 target-materialization worker。

该 runbook 只生成命令，不运行 BPC / pricing / RMP / worker。实际执行后仍必须做 ROI audit、reachability audit、certificate audit，再决定是否写回 Stage 3 dataset。

## Candidate 明细

| context | target rank | ranking | best true RC | target sequence | 用途 |
|---|---:|---|---:|---|---|
| `ac056820151e9ad7` | 1 | best_rc | -25.4432665 | 20,16 | 最大 false-delay context 的 individual attribution |
| `ac056820151e9ad7` | 2 | impact | -4.97015675 | 15,5,16,7,3 | 拆 batch3 中可能导致 retry 的多-sortie 子目标 |
| `ac056820151e9ad7` | 3 | active_replacement | -3.41733 | 15,20 | 拆 active-replacement 相关子目标 |
| `79fde658840fe2b8` | 1 | best_rc | -29.939646 | 1,15,17 | negative primal context 的 best-RC hard-negative |
| `79fde658840fe2b8` | 2 | impact | -20.0283435 | 12,4,13,5 | negative primal context 的 impact-ranked 子目标 |
| `79fde658840fe2b8` | 3 | active_replacement | -14.7797715 | 12,4,19,13 | negative primal context 的 active-replacement 子目标 |
| `ac15bc4e7e3d6fff` | 1 | best_rc | -31.9356514 | 16,17,15 | columns 降低但 primal 变差 context 的 best-RC hard-negative |
| `ac15bc4e7e3d6fff` | 2 | impact | -26.5430824 | 4,19,10,17 | workload/trajectory 冲突子目标 |
| `ac15bc4e7e3d6fff` | 3 | active_replacement | -21.7182942 | 4,10,17,7 | workload/trajectory 冲突子目标 |

## 执行后写回规则

v53 执行后不能直接把 worker 返回的 true-RC negative 写成 HIGH_PRIORITY。必须按以下顺序审计：

1. reachability：
   - expected context reached；
   - target causal match；
   - worker materialized target；
   - 未 reach 的样本只能作为 context-miss 诊断。

2. A/B ROI：
   - positive primal / retry / pricing ROI 才能作为 high-ROI candidate source；
   - negative primal / negative retry 作为 hard-negative；
   - no-observed 作为 ambiguous / workload-only，不能当 positive。

3. label admission：
   - 只有 reachable 且 trajectory ROI 为正的 true-RC negative 才能进入 `HIGH_PRIORITY` 训练标签；
   - reachable 但 nonpositive ROI 的 true-RC negative 进入 `DELAY_QUEUE` / hard-negative 训练标签；
   - 任何 missing reachability 或 context mismatch 都不能写训练标签。

4. exact boundary：
   - 这些标签只训练 admission scheduling；
   - 不能产生 official lower bound；
   - 不能参与 no-negative certificate；
   - 不能永久丢弃 true-RC negative。

## 对 Stage 3/4 的影响

v53 不是 Stage 4 candidate，也不证明 20-task 加速。它的作用是把 v51/v52 暴露的 blocker 转成下一批可执行的 same-context individual attribution runbook。

如果 v53 执行后：

- `ac056` 中出现 positive individual ROI：下一版 dataset 应补同 context 正负对照，让模型学会在最大 false-delay context 内排序；
- `ac056` 全部 nonpositive：该 context 可整体降级为 hard-negative，不再作为 high-priority source；
- `79fde/ac15` 继续 negative：它们应成为 high-confidence hard-negative anchor，用于强化 candidate head / delay-risk head；
- 任一 context 未 reach：该 context 需要 recapture，不允许贴标签。

## 下一步

1. 不上线 v51 checkpoint，不启动 mutating admission。
2. 可显式执行 v53 runbook 的 20 条命令，执行后先做 reachability audit，再做 ROI audit 和 certificate audit。
3. 把可达的 individual rows 转成 Stage 3 batch-impact rows；只允许 causal matched 样本写入。
4. 用新 rows 重建 v54 dataset，再训练 v55，并检查是否出现 `coverage_and_false_delay_safe_epoch_count > 0`。
5. 如果 v55 仍没有高覆盖 delay-safe epoch，就进入模型结构修复，而不是继续扫阈值。

## Exactness Boundary

```text
v53_subset_runs_bpc_or_pricing = false
v53_runbook_builder_runs_bpc_or_pricing = false
worker_runbook_executed = false
production_ready = false
default_enabled = false
stage4_candidate_ready = false
certificate_ready = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

GAT 可以让 column generation 前段更聪明，但不能完成证明。最终 certificate 必须由 exact pricing 在当前 branch/cut/dual 下重新确认：完整配置宇宙中没有任何负 reduced-cost journey。
