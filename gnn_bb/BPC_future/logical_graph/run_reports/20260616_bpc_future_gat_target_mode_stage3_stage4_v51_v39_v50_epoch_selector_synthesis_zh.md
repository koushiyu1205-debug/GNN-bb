# 2026-06-16 BPC_future GAT Stage 3/4 v51 跨版本综合报告

## 读取范围

本轮复读了 `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`、Stage 1/2 基础报告、Stage 3 v15/v23/v24/v28/v39/v41/v44/v45/v46、Stage 4 v14/v38/v40/v50，以及 Stage 5 的 20/30/50/100 exact-safe 加速目标。

目标边界保持不变：

```text
Learning-guided discovery, exact-certified closure
```

GAT / CBF / kNN / OOD 只能做 discovery、ordering 和 finite-delay admission scheduling；进入 RMP 的列仍必须 true-RC verified；最终 optimality certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive no-negative closure。

## v51 本轮产物

### Dataset

```text
dataset =
  BPC_future/data/gat_batch_impact/v51_mixed_v39_plus_v50_false_delay_context_batch_20260616

dataset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_dataset_v51_v39_plus_v50_false_delay_context_batch_zh.md

all_checks_pass = true
training_ready = true
ranking_ready = true
production_ready = false
```

v51 相比 v39 的主要变化：

| field | v39 | v51 | delta |
|---|---:|---:|---:|
| sample_count | 379 | 383 | +4 |
| candidate_count | 4682 | 4694 | +12 |
| non_improving batch | 105 | 109 | +4 |
| roi_positive batch | 274 | 274 | 0 |
| delay_queue candidate | 388 | 400 | +12 |
| high_priority candidate | 4294 | 4294 | 0 |
| positive_negative_label_pair_count | 108 | 124 | +16 |
| sector-wave samples | 107 | 111 | +4 |
| tasks020 samples | 196 | 200 | +4 |

这说明 v50 回流没有新增正例，而是把 4 个 reachability-confirmed context rows 写成 hard-negative / ambiguous non-positive feedback。它提高了 same-context positive/negative 对比密度，但规模仍很小。

### Training

```text
training =
  BPC_future/results/gat_batch_impact_training_v51_v39_plus_v50_false_delay_context_batch_20260616/metrics.json

training_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v51_v39_plus_v50_false_delay_context_batch_training_zh.md

checkpoint_gate_pass = false
stage4_candidate_ready = false
production_ready = false
best_epoch = 3
selected_checkpoint_reason =
  no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_roi_ci
```

selected epoch 3 的核心指标：

```text
accepted_batch_count = 10
accepted_batch_roi = 23.265176677703856
accepted_batch_roi_ci_low = 16.149670701096916
high_priority_precision = 0.43478260869565216
high_priority_precision_ci_low = 0.25634368332198654
safe_precision = 1.0
safe_precision_ci_low = 0.7224598312333834
false_high_priority_on_delay = 0.09701492537313433
false_high_priority_on_delay_count = 13
false_safe_rate_union = 0.09701492537313433
```

Stage 4 blockers：

```text
[
  'false_high_priority_on_delay_too_high',
  'false_safe_rate_union_too_high',
  'family_holdout_accepted_batch_missing',
  'high_priority_precision_below_threshold_or_no_predictions',
  'high_priority_precision_ci_low_below_threshold_or_not_measurable',
  'knn_ood_audit_missing',
  'knn_ood_holdout_audit_not_run',
  'online_shadow_and_opt_in_ab_not_run',
  'safe_precision_ci_low_below_threshold_or_not_measurable'
]
```

family holdout 仍然塌缩：

```text
sector-wave accepted_batch_count = 10
sector-wave oracle_high_roi_count = 24
random-wave accepted_batch_count = 0
random-wave oracle_high_roi_count = 6
greedy-anchor accepted_batch_count = 0
```

## v52 Epoch Selector 审计

```text
selector_audit =
  BPC_future/results/gat_batch_impact_epoch_selector_v52_v51_false_delay_context_batch_20260616/summary.json

selector_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v52_v51_epoch_selector_audit_zh.md

epoch_count = 8
false_delay_safe_epoch_count = 3
coverage_confidence_ready_epoch_count = 3
coverage_and_false_delay_safe_epoch_count = 0
primary = no_epoch_satisfies_coverage_and_false_delay_constraints
checkpoint_selection_is_primary_blocker = false
recommended_next_step = not_a_checkpoint_selection_problem_collect_context_local_hard_negatives
```

epoch-level 分布：

| epoch | class | accepted | ROI | false-delay | HP precision |
|---:|---|---:|---:|---:|---:|
| 1 | false_delay_safe_but_low_coverage | 20 | 1.922835 | 0.000000 | 1.000000 |
| 2 | false_delay_safe_but_low_coverage | 4 | 0.794640 | 0.000000 | 1.000000 |
| 3 | low_coverage_and_false_delay_unsafe | 10 | 23.265177 | 0.097015 | 0.434783 |
| 4 | false_delay_safe_but_low_coverage | 8 | 4.255640 | 0.000000 | 1.000000 |
| 5 | coverage_ready_but_false_delay_unsafe | 46 | 6.367897 | 0.418182 | 0.942500 |
| 6 | coverage_ready_but_false_delay_unsafe | 49 | 6.342413 | 0.425373 | 0.905473 |
| 7 | low_coverage_and_false_delay_unsafe | 17 | 7.405960 | 0.082090 | 0.970109 |
| 8 | coverage_ready_but_false_delay_unsafe | 39 | 7.661405 | 0.417910 | 0.908646 |

解释：

1. v51 的确出现了 false-delay safe epoch，但 accepted batch 低于 Wilson CI 所需的 `35` 个全成功样本下限；
2. 覆盖达到置信度下限的 epoch 全部 false-delay unsafe；
3. 因此当前不是 checkpoint selector 漏选了好 epoch，而是训练分布/模型表示没有形成“高覆盖且 delay-safe”的区域。

## 与旧版本的对比

| version | 主要现象 | 当前含义 |
|---|---|---|
| v15 | false-safe 降到 0，但 accepted 只有 13，CI 不够 | 硬负例可提高安全性，但覆盖容易塌缩 |
| v23 | accepted 约 56，ROI 覆盖上去，false-delay 约 0.425532 | 只追 high-ROI 会把 delay hard-negative 放进 HIGH_PRIORITY |
| v24/v28 | false-delay 压到 0.008475，但 accepted 17/22 | delay suppression 有效，但安全壳太窄 |
| v39 | accepted 46，ROI CI-low 3.321518，false-delay 0.448980 | coverage 回来后 false-delay 复发 |
| v41 | 44 个 false high-priority 集中在 sector-wave|20 的 5 个 context | blocker 是 context-local ranking failure，不是全局随机噪声 |
| v44 | delay-safe shell 存在，但最多只接受 2 个 batch | 安全阈值不是不存在，而是无法覆盖足够机会 |
| v45 | false-delay contrast smoke 可安全，full 后复发 | 局部 loss 没改变结构性分不开 |
| v50 | 4 条 reachable feedback 都非正 trajectory ROI，且 4/4 即时 objective improvement | 即时 RMP movement 会误导，标签必须看 trajectory ROI / retry / workload |
| v51/v52 | 新 hard-negative 让 false-delay safe epoch 出现，但无 epoch 同时满足 coverage | 不是 selector 问题，需要更多 context-local hard-negative + positive 对照或模型结构修复 |

## 新理解

### 1. v50 hard-negative 回流方向是对的，但量太少

v51 只新增了 4 个 non-improving batch / 12 个 delay_queue candidate。这个增量足以让早期 epoch 出现 `false_delay_safe_but_low_coverage`，说明标签方向有效；但它不足以让高覆盖区域也保持安全。

结论不是“v50 没用”，而是“v50 只修了局部安全壳，没有补齐安全壳外的正负排序结构”。

### 2. v51 排除了单纯 checkpoint selection 解释

如果某个 epoch 同时 `coverage_confidence_ready=true` 且 `false_delay_safe=true`，那么问题可能主要是 selector 没选它。v52 审计显示这样的 epoch 数为 0，所以继续只改 checkpoint selector 或只调 validation loss 权重，不太可能把模型送进 Stage 4。

### 3. 当前 blocker 是同 context 下的 action consequence 表示不足

这些候选列都可能是 true-RC negative，也可能让即时 RMP objective movement 变好，但 longer-horizon trajectory ROI、tail retry、pricing workload 和 final proof tail 可能变差。当前 GAT 的 candidate score / delay-risk score 还没有稳定学到这种动作后果。

需要的监督不是“这个 column reduced cost 负不负”，而是同一 RMP context 下：

```text
high-ROI safe target > retry hard-negative > negative-primal hard-negative
```

并且这个排序要能跨 `sector-wave|20`、random-wave high-ROI、不同 task_count holdout 泛化。

### 4. random-wave high-ROI 仍是当前模型盲区

v51 selected checkpoint 只接受 sector-wave，validation 里 random-wave 有 6 个 oracle high-ROI，却 0 accepted。这个现象和 v15 missed high-ROI 诊断一致：不是阈值差一点，而是 candidate head / embedding 对一部分 high-ROI family 结构性分不开。

### 5. Stage 4 还不能启动 mutating admission

v51 没有通过 HP precision CI、safe precision CI、false-safe、family holdout、kNN/OOD、online shadow / opt-in A/B。它只能作为 Stage 3 diagnostic，不是 Stage 4 candidate，更不能默认启用。

## 当前问题列表

1. `sector-wave|20` false-delay hard-negative 的 context-local ranking 仍没有解决。
2. random-wave high-ROI 机会在 validation 上没有被 accepted，family holdout 不过。
3. false-delay safe shell 可以出现，但 coverage 达不到 Stage 3 置信度要求。
4. coverage 达到置信度要求时，false-delay 回到 0.418-0.425 量级。
5. 训练 history 中 epoch-level 审计缺少部分 CI / false-safe / family holdout 字段，只能做趋势审计；最终 Stage 3 gate 仍要看完整 deployment metrics。
6. 当前没有 knn/OOD holdout audit，也没有 online shadow / opt-in A/B，因此 Stage 4 blocker 仍完整存在。

## 下一步建议

1. 不继续把 v51 当作 Stage 4 checkpoint 推进；它没有通过 gate。
2. 下一批数据不要泛采，应在 `ac056820151e9ad7`、`79fde658840fe2b8`、`ac15bc4e7e3d6fff` 等 false-positive context 内补 same-context positive/negative 对照。
3. `b6d808ebac2a6dd8` 暂时降级为 workload-only / ambiguous，不再作为 high-ROI anchor，除非后续 individual attribution 找到正 trajectory ROI 子目标。
4. 训练上继续保留 precision-constrained ROI maximization，但要强化 context-local candidate-head gate：先证明 candidate head 自己能把 high-ROI safe target 排在 delay hard-negative 前面，再叠 delay-risk。
5. 如果补充 context-local rows 后仍无法形成高覆盖 delay-safe shell，就需要改模型输入/结构，加入更直接的 order/timing/path-option/basis trajectory 表示，而不是继续扫阈值。

## Exactness Boundary

```text
v51_dataset_runs_bpc_or_pricing = false
v51_training_runs_bpc_or_pricing = false
v52_selector_runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
stage4_candidate_ready = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

GAT 可以让 column generation 前段更聪明，但不能完成证明。最终 certificate 必须由 exact pricing 在当前 branch/cut/dual 下重新确认：完整配置宇宙中没有任何负 reduced-cost journey。
