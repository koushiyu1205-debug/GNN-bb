# 2026-06-16 BPC_future GAT Stage 3/4 v50 Reachability / Row Feedback 综合报告

## 读取范围

本轮继续复读：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- Stage 1 模型结构报告
- Stage 2 数据采集报告
- Stage 3 v50 cross-version false-delay context synthesis
- Stage 4 v50 context-batch ROI audit
- Stage 5 20/30/50/100 scale acceleration 目标段

目标模式不变：GAT / CBF / kNN / OOD 只能做 discovery、ordering 和 finite-delay admission scheduling；进入 RMP 的列必须 true-RC verified；最终 certificate 只能来自当前 branch/cut/dual 下 full exact pricing no-negative closure。

## 本轮补充审计

### 1. Reachability audit

命令只读 v49 context-batch runbook 和 v50 已有 worker 日志，不运行 BPC / pricing / RMP / worker：

```text
reachability_summary =
  BPC_future/results/gat_batch_impact_false_delay_context_plan_v50_v39_context_batch_pilot_20260616/reachability_audit_legacy/summary.json

reachability_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_stage4_v50_false_delay_context_batch_reachability_legacy_zh.md
```

结果：

```text
record_count = 5
reachable_target_intervention_count = 4
reachability_class_counts = {
  'target_intervention_reachable': 4,
  'worker_context_not_reached': 1
}
all_checks_pass = true
production_ready = false
certificate_ready = false
official_bound_effect = false
```

可达 context：

| context | reachability | returned journeys | best rc | label allowed |
|---|---|---:|---:|---|
| `ac056820151e9ad7` | `target_intervention_reachable` | 3 | -25.4432665 | yes |
| `b6d808ebac2a6dd8` | `target_intervention_reachable` | 3 | -41.3185275 | yes |
| `79fde658840fe2b8` | `target_intervention_reachable` | 3 | -29.9396460 | yes |
| `ac15bc4e7e3d6fff` | `target_intervention_reachable` | 3 | -31.9356514 | yes |
| `7b430465c7ae76b3` | `worker_context_not_reached` | 0 | n/a | no |

这一步修正了 v50 cross-version synthesis 中的训练写回范围：`7b430465c7ae76b3` 虽然 ROI audit 是 no-observed，但 worker 没有 reach 到 expected context，不能贴 Stage 3 训练标签；只能保留为 no-label / context-miss 诊断。

### 2. Worker rows 回流

命令只读 runbook summary、ROI audit summary、reachability summary 和 worker 日志：

```text
rows_summary =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v50_false_delay_context_batch_20260616/summary.json

rows_jsonl =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v50_false_delay_context_batch_20260616/same_context_target_worker_batch_impact_rows.jsonl

rows_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v50_false_delay_context_batch_worker_rows_zh.md
```

结果：

```text
candidate_count = 5
row_count = 4
reachability_allowed_candidate_count = 4
skipped_counts = {'reachability_not_training_label': 1}
signature_sample_row_count = 4
positive_objective_improvement_count = 4
positive_trajectory_roi_count = 0
nonpositive_trajectory_roi_count = 4
roi_class_counts = {
  'negative_primal_roi': 2,
  'negative_retry_roi': 1,
  'no_observed_roi': 1
}
all_rows_have_worker_target_causal_match = true
all_checks_pass = false
```

`all_checks_pass=false` 的原因是：

```text
has_same_context_pairs = false
pairwise_context_count = 0
largest_context_size = 1
```

这不是数据无效，而是说明 v50 rows 只能作为 hard-negative / ambiguous feedback 增量，不能单独构成 Stage 3 所需的 same-context pairwise training coverage。

## 样本标签判断

| context | ROI class | objective improved | trajectory ROI | label |
|---|---|---:|---:|---|
| `ac056820151e9ad7` | `negative_retry_roi` | yes | -1.9382478 | retry hard-negative |
| `b6d808ebac2a6dd8` | `no_observed_roi` | yes | 0.0 | workload-only / ambiguous non-positive |
| `79fde658840fe2b8` | `negative_primal_roi` | yes | -25.9231931 | high-confidence hard-negative |
| `ac15bc4e7e3d6fff` | `negative_primal_roi` | yes | -0.3056810 | high-confidence hard-negative |
| `7b430465c7ae76b3` | context not reached | n/a | n/a | no training label |

关键点：4/4 可达 rows 都有即时 RMP objective improvement，但 4/4 trajectory ROI 非正。因此 v50 进一步确认：训练标签不能用即时 objective movement；必须用 A/B trajectory ROI、tail retry、pricing workload 和 reachability causal match 覆盖。

## 对 Stage 3 的影响

1. `79fde658840fe2b8` 与 `ac15bc4e7e3d6fff` 可以作为 high-confidence context-local hard-negative。
2. `ac056820151e9ad7` 可以作为 retry hard-negative，且它是 v41 中最大的 false-positive context。
3. `b6d808ebac2a6dd8` 不应再作为 high-ROI anchor；它只能作为 ambiguous / workload-only non-positive。
4. `7b430465c7ae76b3` 必须从训练写回中排除，除非后续重新跑到 expected context。
5. v50 rows 没有 same-context positive 对照，不能单独解决 candidate-head context-local ranking；下一步仍要在 `ac056` / `b6d808` 等 context 内采正负对照。

## 对 Stage 4 / Stage 5 的影响

- v50 不产生 Stage 4 candidate。
- v50 不支持 mutating admission。
- v50 不支持 production default。
- v50 不证明 20-task exact 加速；所有相关 20-task runs 仍是 `TIME_LIMIT` 且 `dual_bound=None`。
- v50 的价值是把 false-delay blocker 的负样本变成 reachability-confirmed hard-negative feedback，为下一轮 Stage 3 训练目标和 context-local contrast 提供证据。

## 下一步

1. 把这 4 条 rows 作为 `v50_false_delay_context_batch_reachable_hard_negative` 增量源接入下一版 dataset，但保留 `diagnostic_only=true`。
2. 不把 `7b430465c7ae76b3` 写入训练标签；它需要 recapture 或 context-miss 专门诊断。
3. 下一批采样只优先拆 `ac056` 和 `b6d808`：
   - `ac056` 覆盖 33/44 个 false-positive，需要同 context 正负对照；
   - `b6d808` 有 workload-only 弱信号，需要拆分 individual target 判断是否存在可用子目标。
4. 下一版训练必须继续使用 `precision-constrained ROI maximization`，并让 context-local false-delay hard-negative 在 candidate head / delay-risk head 中形成排序约束。

## Exactness Boundary

```text
reachability_audit_runs_bpc_or_pricing = false
rows_builder_runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

target materialization 只说明这些 true-RC negative columns 被找到并加入过 RMP；它不能证明 no-negative closure。最终 certificate 仍必须由当前 branch/cut/dual 下 exact pricing 对完整配置宇宙执行 exhaustive no-negative check。
