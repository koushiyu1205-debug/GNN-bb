# BPC_future GAT Target Mode Stage 3 v117 Focused Head Tight 负结果报告

日期：2026-06-22

## 结论

v117 不替代 v116，也不能作为 Stage 4 candidate。

本轮在 v116 数据集上只调整训练 loss，不改 solver、pricing、RMP、worker、
certificate 或 online 配置。实验目标是验证：更强的 focused candidate/admission/delay
head loss 能否把 v116 的 focused strict pair pass rate 从 0.93548 推到 1.0。

结果相反：v117 的 local deployment gate 没有任何 epoch 通过，focused strict 从
v116 的 0.9354838709677419 退化到 0.8709677419354839。更强的 focused head loss
导致 coverage / safety tradeoff 变坏，并把 v116 的 near-margin 失败放大成 mixed/deep
score gap。

## Exactness 边界

- 只运行 offline training 和 offline audit；
- 不运行 BPC / pricing / RMP / worker；
- 不生成 official bound 或 certificate；
- GAT/kNN/OOD 仍不能永久丢弃 true-RC negative；
- final certificate 仍只能来自 exact pricing full closure。

## v117 配置

数据集：

```text
BPC_future/data/gat_batch_impact/v116_context_interaction_label_conflict_cleaned_5000_stage4_biased_20260622
```

相对 v116 的主要变化：

```text
focused_pair_loss_multiplier: 1.0 -> 1.25
focused_pair_candidate_loss_multiplier: 1.5 -> 2.0
focused_pair_admission_loss_multiplier: 2.0 -> 4.0
focused_pair_delay_risk_loss_multiplier: 2.0 -> 3.0
focused_pair_batch_loss_multiplier: 0.5 -> 0.5
```

输出：

```text
metrics = BPC_future/results/gat_batch_impact_training_v117_context_interaction_cleaned_focused_head_tight_seed13_20260622/metrics.json
checkpoint = BPC_future/results/gat_batch_impact_training_v117_context_interaction_cleaned_focused_head_tight_seed13_20260622/model.pt
training_report = BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v117_context_interaction_cleaned_focused_head_tight_retrain_seed13_zh.md
epoch_selector = BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v117_context_interaction_cleaned_focused_head_tight_epoch_selector_audit_zh.md
focused_failure_audit = BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v117_context_interaction_cleaned_focused_head_tight_pair_failure_audit_zh.md
```

## 训练结果

```text
best_epoch = 3
best_loss_epoch = 2
checkpoint_gate_pass = false
selected_checkpoint_reason = no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_ci_safe_ci_coverage
validation accepted = 20
validation accepted ROI = 5.4356356404721735
validation accepted ROI CI low = 3.2992362949247274
validation safe precision CI low = 0.8388698745050667
false high-priority on delay = 0.0
```

v117 的 ROI 点估计高于 v116，但 accepted count 太低，safe precision CI low 低于
Stage 3 local gate。因此它不是可行 checkpoint。

## Epoch Selector

```text
coverage_and_false_delay_safe_epoch_count = 0
coverage_confidence_ready_epoch_count = 1
false_delay_safe_epoch_count = 7
primary = no_epoch_satisfies_coverage_and_false_delay_constraints
```

关键 epoch：

| epoch | accepted | ROI | false-delay | class |
|---:|---:|---:|---:|---|
| 2 | 8 | 14.403059 | 0.000000 | false_delay_safe_but_low_coverage |
| 3 | 20 | 5.435636 | 0.000000 | false_delay_safe_but_low_coverage |
| 4 | 131 | 1.327487 | 0.066434 | coverage_ready_but_false_delay_unsafe |
| 8 | 8 | 11.542411 | 0.006993 | false_delay_safe_but_low_coverage |

解释：这不是 checkpoint selector 漏选了好 epoch，而是没有 epoch 同时满足 coverage
和 false-delay safety。强 focused loss 让模型在“极保守”和“覆盖上升但 false-delay
不安全”之间摆动。

## Focused Pair 对比

| run | pair_count | passed | failed | strict | raw_fail | admission_fail | delay_fail | deep_fail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v116 | 217 | 203 | 14 | 0.935484 | 7 | 13 | 7 | 0 |
| v117 | 217 | 189 | 28 | 0.870968 | 17 | 17 | 28 | 11 |

v117 不但没有压掉 near-margin 失败，反而新增 deep structural score gap：

```text
all_failed_heads_near_rate_among_failed: 0.7142857142857143 -> 0.32142857142857145
any_failed_head_deep_count: 0 -> 11
```

最差上下文之一：

```text
context = apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000
pair_count = 12
pair_pass_count = 0
failed_pair_count = 12
primary = deep_structural_score_gap
```

这说明盲目加大 focused head multiplier 会让局部上下文排序结构更差，而不是稳定修复
v116 的近边界错误。

## v116 / v117 总体对比

| run | best_epoch | accepted | ROI | ROI CI low | safe CI low | false-delay | focused strict | local gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| v116 | 1 | 36 | 4.602683 | 2.355012 | 0.903578 | 0.000000 | 0.935484 | pass |
| v117 | 3 | 20 | 5.435636 | 3.299236 | 0.838870 | 0.000000 | 0.870968 | fail |

v117 的 ROI 更高是以 accepted coverage 和 safe precision CI 为代价换来的，不满足
Stage 3 hard gate。

## kNN/OOD

未运行 v117 kNN/OOD。

理由：v117 的 local deployment gate 已经因为 safe precision CI low 失败，focused-pair
gate 也明显退化。继续跑 kNN/OOD 不能把该 checkpoint 升级为 Stage 4 candidate，只会增加
无效审计成本。

## 下一步

1. 保留 v116 为当前最好基线。
2. 不继续做盲目 multiplier sweep，尤其不要再整体加大 focused admission/delay 权重。
3. 下一轮应回到更温和的 v116 附近配置，优先尝试：
   - admission-only 轻微上调，例如 `focused_pair_admission_loss_multiplier=2.5~3.0`；
   - delay-risk 不再整体上调，避免制造新的 deep gap；
   - 或对 v116 剩余 9 个 failure contexts 做 context-local margin shaping / explicit tranche full training。
4. 若下一轮仍不能把 focused strict 推到 1.0，应优先分析失败 contexts 的 action-consequence 特征，而不是继续加权重。
