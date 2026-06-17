# 2026-06-16 BPC_future GAT Stage 3/4 v54-v56 Individual Follow-up 综合报告

## 读取范围

本轮复读了：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- Stage 1 模型结构报告与 Stage 2 数据采集报告
- v15 / v36 / v39 / v41 / v44 / v45 / v46 / v50 / v51 / v52 / v53 关键报告
- 本轮新增的 v54 dataset、v55 training、v56 epoch-selector 审计结果

目标边界保持不变：

```text
Learning-guided discovery, exact-certified closure
```

GAT / CBF / kNN / OOD 只能用于 discovery、ordering 和 finite-delay admission scheduling。进入 RMP 的列仍必须 true-RC verified；delay queue 只能有限延迟，不能永久 reject；最终 optimality certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive no-negative closure。

## 本轮新增产物

### v53 worker rows

```text
rows =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v53_post_v51_individual_followup_20260616/same_context_target_worker_batch_impact_rows.jsonl

row_count = 9
candidate_count = 9
context_count = 3
pairwise_context_count = 3
largest_context_size = 3
positive_trajectory_roi_count = 2
nonpositive_trajectory_roi_count = 7
roi_class_counts = {
  'negative_primal_roi': 4,
  'negative_retry_roi': 3,
  'positive_primal_roi': 1,
  'positive_retry_roi': 1
}
all_checks_pass = true
```

关键标签：

| context | target sequence | ROI class | training implication |
|---|---|---|---|
| `ac056820151e9ad7` | `20,16` | `negative_retry_roi` | retry hard-negative / delay |
| `ac056820151e9ad7` | `15,5,16,7,3` | `negative_retry_roi` | retry hard-negative / delay |
| `ac056820151e9ad7` | `15,20` | `negative_retry_roi` | retry hard-negative / delay |
| `79fde658840fe2b8` | `1,15,17` | `negative_primal_roi` | primal hard-negative |
| `79fde658840fe2b8` | `12,4,13,5` | `negative_primal_roi` | primal hard-negative |
| `79fde658840fe2b8` | `12,4,19,13` | `positive_primal_roi` | positive trajectory label |
| `ac15bc4e7e3d6fff` | `16,17,15` | `negative_primal_roi` | primal hard-negative |
| `ac15bc4e7e3d6fff` | `4,19,10,17` | `positive_retry_roi` | workload/retry positive, not primal-only proof |
| `ac15bc4e7e3d6fff` | `4,10,17,7` | `negative_primal_roi` | primal hard-negative |

### v54 dataset

```text
dataset =
  BPC_future/data/gat_batch_impact/v54_v51_plus_v53_individual_followup_20260616

dataset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_dataset_v54_v51_plus_v53_individual_followup_zh.md

all_checks_pass = true
training_ready = true
ranking_ready = true
production_ready = false
```

v54 相比 v51 的变化：

| field | v51 | v54 | delta |
|---|---:|---:|---:|
| sample_count | 383 | 392 | +9 |
| candidate_count | 4694 | 4703 | +9 |
| roi_positive batch | 274 | 276 | +2 |
| non_improving batch | 109 | 116 | +7 |
| high_priority candidates | 4294 | 4296 | +2 |
| delay_queue candidates | 400 | 407 | +7 |
| same_context_pair_count | 343 | 427 | +84 |
| positive_negative_label_pair_count | 124 | 159 | +35 |
| sector-wave samples | 111 | 120 | +9 |
| tasks020 samples | 200 | 209 | +9 |

解释：v53 个体级回流确实增加了同一 context 下的正负对照密度，尤其是把 v50 中过粗的 `79fde` context-level negative 标签拆出了一个 positive primal 子目标。

### v55 training

```text
training =
  BPC_future/results/gat_batch_impact_training_v55_v54_individual_followup_20260616/metrics.json

training_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v55_v54_individual_followup_training_zh.md

checkpoint_gate_pass = false
stage4_candidate_ready = false
production_ready = false
best_epoch = 3
selected_checkpoint_reason =
  no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_roi_ci
```

selected epoch 的主要 blocker：

```text
false_high_priority_on_delay_too_high
false_safe_rate_union_too_high
family_holdout_accepted_batch_missing
high_priority_precision_below_threshold_or_no_predictions
high_priority_precision_ci_low_below_threshold_or_not_measurable
safe_precision_ci_low_below_threshold_or_not_measurable
knn_ood_audit_missing
online_shadow_and_opt_in_ab_not_run
```

family holdout 继续塌缩：

```text
sector-wave accepted_batch_count = 3
sector-wave oracle_high_roi_count = 26
random-wave accepted_batch_count = 0
random-wave oracle_high_roi_count = 6
greedy-anchor accepted_batch_count = 0
```

### v56 epoch selector

```text
selector_audit =
  BPC_future/results/gat_batch_impact_epoch_selector_v56_v55_individual_followup_20260616/summary.json

selector_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v56_v55_individual_followup_epoch_selector_audit_zh.md

epoch_count = 8
false_delay_safe_epoch_count = 3
coverage_confidence_ready_epoch_count = 4
coverage_and_false_delay_safe_epoch_count = 0
primary = no_epoch_satisfies_coverage_and_false_delay_constraints
checkpoint_selection_is_primary_blocker = false
recommended_next_step =
  not_a_checkpoint_selection_problem_collect_context_local_hard_negatives
```

epoch 分布：

| epoch | class | accepted | ROI | false-delay | HP precision |
|---:|---|---:|---:|---:|---:|
| 1 | false_delay_safe_but_low_coverage | 6 | 0.759492 | 0.000000 | 1.000000 |
| 2 | false_delay_safe_but_low_coverage | 9 | 0.889054 | 0.000000 | 1.000000 |
| 3 | low_coverage_and_false_delay_unsafe | 3 | 32.523210 | 0.042553 | 0.333333 |
| 4 | coverage_ready_but_false_delay_unsafe | 46 | 6.560289 | 0.446809 | 0.923451 |
| 5 | false_delay_safe_but_low_coverage | 6 | 1.042441 | 0.000000 | 1.000000 |
| 6 | coverage_ready_but_false_delay_unsafe | 38 | 7.882191 | 0.446809 | 0.841709 |
| 7 | coverage_ready_but_false_delay_unsafe | 57 | 5.102844 | 0.460993 | 0.937620 |
| 8 | coverage_ready_but_false_delay_unsafe | 36 | 8.336969 | 0.538462 | 0.890815 |

## 与旧版本的对比

| version | 旧结论 | v54-v56 后的理解 |
|---|---|---|
| v15 | false-safe 能压到 0，但 accepted 只有 13，missed high-ROI 不是 near-threshold | 结构性 gap 仍成立；v55 没有把 random-wave high-ROI 拉回来。 |
| v36 | ROI-neighbor repair 指向少数 context，需要 same-context contrast | 方向正确；v53 正是在 `79fde/ac15/ac056` 上补了个体级 contrast。 |
| v39 | coverage 和 ROI 回来，但 false-delay = 0.448980 | v55 高覆盖 epoch 仍在 0.446809-0.538462，说明 false-delay 复发没有被 v53 小增量解决。 |
| v41 | 44 个 false high-priority 全集中在 `sector-wave|20` 的 5 个 context | v53 覆盖其中 3 个 context，证明 cluster 可被拆细，但还不足以形成稳定 high-coverage safe shell。 |
| v44 | delay-safe shell 存在，但最多只接受 2 个 batch | v56 仍是同一个形态：safe epoch accepted 6/9/6，不足以过 coverage confidence。 |
| v45/v46 | false-delay contrast 可制造低覆盖安全壳；full coverage 后 false-delay 复发 | v55/v56 基本复现该 tradeoff，排除“只需再训一版”或“只需换 selector”的解释。 |
| v50 | context-batch 级别 4/4 trajectory ROI 非正，且即时 objective improvement 会误导 | v53 修正了 v50 的过粗粒度：`79fde` 里确有正 primal 子目标，但 labels 必须 individual attribution。 |
| v51/v52 | v50 hard-negative 增量让 safe epoch 出现，但无 epoch 同时满足 coverage 和 false-delay safe | v54-v56 加入 v53 后结论不变：增量提升 pairwise 密度，但没有改变 coverage/safety tradeoff。 |

## 新理解

### 1. v53 不是无效数据，但也不是结构修复

v53 把 sample_count 从 383 提到 392、positive-negative pair 从 124 提到 159，这对训练是实质增量。它还纠正了 v50 的一个重要误判：同一个 `79fde658840fe2b8` context 内，既有 negative primal target，也有 positive primal target。

但 v55/v56 说明，这 9 条个体级 rows 只补了少数 sector-wave context 的局部标签，没有让模型学到可泛化的 context-local action consequence。高覆盖 epoch 的 false-delay 仍回到 0.45-0.54，低 false-delay epoch 仍只有 6-9 个 accepted。

### 2. 当前 blocker 已经不是 checkpoint selector

v52 已经显示：

```text
coverage_and_false_delay_safe_epoch_count = 0
```

v56 再次显示同样结果。若没有任何 epoch 同时 coverage-ready 和 false-delay-safe，继续只改 checkpoint selection、validation loss 排序、best_epoch 规则，不能把模型推进 Stage 4。

### 3. random-wave 仍是未修复盲区

v15 missed high-ROI 诊断中，random-wave missed high-ROI 主要是 embedding structural gap。v55 family holdout 里 random-wave 仍有：

```text
oracle_high_roi_count = 6
accepted_batch_count = 0
```

v53 主要补 sector-wave|20 的 false-positive context，没有补 random-wave high-ROI 正负邻域。因此 v55 的 random-wave 0 accepted 不是意外，而是旧问题还没被数据覆盖。

### 4. `ac056` 应明确作为 retry hard-negative source

v41 最大 false-positive cluster 是 `ac056820151e9ad7`。v53 对它拆出的三个 individual target 全是 `negative_retry_roi`，且没有 primal improvement。它不应继续作为 high-priority source，而应作为 retry hard-negative / delay queue 的核心监督来源。

### 5. `79fde` 证明 context-level label 会误伤正目标

v50 把 `79fde` 写成 hard-negative 是 batch/context 粒度上的合理结论；v53 拆开后发现 `12,4,19,13` 是 positive primal ROI。这说明下一步数据结构必须保留 target sequence / arc-option sequence 粒度，不能只在 context_hash 或 batch_hash 级别贴标签。

### 6. 工作量指标不能替代 trajectory ROI

`ac15bc4e7e3d6fff` 暴露了 workload/retry signal 和 primal trajectory 的冲突：有的 target 降低 columns 或改善 retry，但同 context 里也有 negative primal。训练目标应继续以 trajectory ROI / retry / pricing workload 的分解标签为准，而不是把 columns delta、true-RC negative 或 exact hit 当 HIGH_PRIORITY 充分条件。

## 当前问题

1. 高 ROI 覆盖和 false-delay 抑制仍是结构性 tradeoff，不是单点阈值问题。
2. candidate head 的 context-local ranking 仍不可靠；delay gate 能形成安全壳，但安全壳太窄。
3. random-wave high-ROI 机会没有被 v53 覆盖，family holdout 继续 0 accepted。
4. sector-wave|20 的 hard-negative/positive contrast 增多，但模型没有把它泛化到高覆盖区域。
5. 当前 epoch history 缺少完整 CI / family / OOD 字段，只能做趋势审计；Stage 3 hard gate 仍以完整 deployment metrics 为准。
6. 仍没有 knn/OOD holdout audit，也没有 online shadow / opt-in A/B 通过证据。
7. Stage 4 mutating admission、Stage 5 20-task `OPTIMAL < 200s` 和 final certificate 都没有被满足。

## 下一步建议

1. 不把 v55 checkpoint 推进 Stage 4；它仍是 diagnostic-only。
2. 不降低 precision / ROI / false-safe / coverage / CI gate。放宽 gate 会把 false-delay hard-negative 放回 HIGH_PRIORITY，和目标相反。
3. 下一批数据优先补 random-wave high-ROI 盲区，尤其是 v15/v43 中 missed high-ROI 且 nearest negative closer 的 context。
4. 对 `sector-wave|20` 继续补同 context 正负 target，但重点应从单个 context 扩展到多个 false-positive context 的可泛化 ranking。
5. 训练侧不要只加 loss multiplier；需要审计 candidate head 输入是否缺少 order/timing/path-option/basis/trajectory consequence 特征。
6. 在进入任何 Stage 4 opt-in 之前，先做一个独立 audit：同一 context 内 positive target 的 candidate score 是否稳定高于 retry/primal hard-negative。如果 candidate head 本身不成立，就不要让 delay-risk head 单独兜底。

## Exactness Boundary

```text
v54_dataset_runs_bpc_or_pricing = false
v55_training_runs_bpc_or_pricing = false
v56_selector_runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
stage4_candidate_ready = false
stage5_ready = false
certificate_ready = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

GAT 可以让前面的 column generation 更聪明，但最终证明仍必须由 exact pricing 在当前 branch/cut/dual 下重新确认：完整配置宇宙中没有任何负 reduced-cost journey。
