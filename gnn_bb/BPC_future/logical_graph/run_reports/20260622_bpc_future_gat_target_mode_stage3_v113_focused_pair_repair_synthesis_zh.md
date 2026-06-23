# 2026-06-22 BPC_future GAT Target Mode Stage 3 v113 Focused Pair Repair 负结果报告

## 结论

v113 不替代 v112。它尝试在 v112 基础上加强 focused same-context pair loss，但结果同时破坏了 local Stage 3 safety gate，并且没有改善 focused pair gate。

当前最好离线证据仍是 v112：

```text
v112 local gate = pass
v112 strict global kNN/OOD = pass
v112 strict scale kNN/OOD = pass
v112 threshold frontier feasible_threshold_count = 135
v112 focused strict pair pass rate = 0.7421875
```

v113 的状态：

```text
best_epoch = 3
best_loss_epoch = 2
checkpoint_gate_pass = false
stage4_candidate_ready = false
production_ready = false
selected_checkpoint_reason = no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_ci_safe_ci_coverage
```

v113 不进入 kNN/OOD 或 Stage 4 shadow，因为它已经在 local Stage 3 gate 失败。

## v113 训练目的

v112 的主要 blocker 是 focused pair gate：

```text
pair_count = 384
strict_pair_pass_rate = 0.7421875
primary blocker = candidate_head_context_ranking_failure
```

v112 pair failure audit 显示多数失败是 near-margin，因此 v113 做了一个保守实验：

- 不降低 Stage 3 hard gate；
- 不放宽 false-delay / false-safe；
- 保持 `risk_adjusted_product` admission；
- 保持 `candidate_delay_gate_enabled=true`；
- 把 focused pair margin 和 focused candidate/admission/delay-risk ranking loss 加强。

输入文件：

```text
BPC_future/results/gat_batch_impact_v113_focused_pair_repair_inputs_20260622/focused_row_indices_v113_combined.json
```

该文件由 v110 focused tranche 与 v112 failed pair rows 合并得到。合并后仍是 `207` 行，说明 v112 的 failed pair rows 已经全部在 focused tranche 内；问题不是失败样本没有进入训练，而是当前表示/损失无法稳定分开这些 same-context pairs。

## 训练结果

v113 selected metrics：

```text
accepted_batch_count = 76
accepted_batch_roi = 2.529040358323408
accepted_batch_roi_ci_low = 1.375749975406458
safe_precision = 1.0
safe_precision_ci_low = 0.9518847317689024
high_priority_precision = 0.9983397897066962
high_priority_precision_ci_low = 0.9951299471559595
false_high_priority_on_delay = 0.01048951048951049
false_high_priority_on_delay_count = 3
false_safe_rate_union = 0.01048951048951049
threshold_local_gate_pass = false
threshold_local_reject_reasons = ["false_high_priority_on_delay_too_high"]
```

关键问题是 false-delay 只比 1% 上限高一点，但 Stage 3 contract 是硬门槛：

```text
max_false_high_priority_on_delay = 0.01
observed_false_high_priority_on_delay = 0.01048951048951049
```

因此 v113 只能作为 diagnostic checkpoint，不能作为 Stage 4 candidate。

epoch 轨迹：

| epoch | accepted | ROI | false-delay | local gate |
| --- | ---: | ---: | ---: | --- |
| 1 | 26 | 10.7965 | 0.000000 | fail |
| 2 | 37 | 8.5973 | 0.017483 | fail |
| 3 | 76 | 2.5290 | 0.010490 | fail |
| 4 | 38 | 8.9780 | 0.017483 | fail |
| 5 | 17 | 8.3076 | 0.000000 | fail |
| 6 | 42 | 9.0981 | 0.013986 | fail |
| 7 | 165 | 6.6668 | 0.034965 | fail |
| 8 | 36 | 16.4813 | 0.017483 | fail |

这个轨迹说明 v113 的更强 pair loss 没有形成稳定的 safe frontier：要么 accepted 太少，要么 false-delay 超过硬上限。

## Focused pair audit

v113 focused pair gate：

```text
pair_count = 384
raw_pair_pass_rate = 0.7708333333333334
admission_pair_pass_rate = 0.7838541666666666
delay_risk_pair_pass_rate = 0.7734375
strict_pair_pass_rate = 0.7395833333333334
required strict_pair_pass_rate = 1.0
```

对比 v112：

| metric | v112 | v113 | change |
| --- | ---: | ---: | ---: |
| raw pair pass | 0.783854 | 0.770833 | worse |
| admission pair pass | 0.783854 | 0.783854 | same |
| delay-risk pair pass | 0.765625 | 0.773438 | slightly better |
| strict pair pass | 0.742188 | 0.739583 | worse |
| failed pairs | 99 | 100 | worse |
| deep structural failed pairs | 0 | 19 | worse |

v113 pair audit summary：

```text
failed_pair_count = 100
pair_pass_count = 284
strict_pair_pass_rate = 0.7395833333333334
all_failed_heads_near_rate_among_failed = 0.63
any_failed_head_deep_rate_among_failed = 0.19
diagnosis_counts.deep_structural_score_gap = 19
diagnosis_counts.near_margin_loss_tuning_candidate = 27
diagnosis_counts.near_margin_with_shared_signature = 36
```

top blocker 仍然是：

```text
context_hash = b6d808ebac2a6dd8
family = sector-wave
task_count = 20
pair_count = 55
failed_pair_count = 32
pair_pass_count = 23
min_raw_margin = -0.150951087474823
min_admission_margin = -0.16905644085175525
min_delay_risk_margin = -0.132705956697464
```

v112 中这个 context 的最小 margin 约为 `-0.04`；v113 变成约 `-0.15 ~ -0.17`，说明简单加大 loss 反而制造了更深的结构性反排。

pair audit 给出的下一步建议：

```text
recommended_next_step.primary = add_or_repair_context_action_consequence_features_before_more_sweeps
recommended_next_step.avoid = do_not_continue_blind_multiplier_sweeps
```

## 判断

v113 证明了一件事：当前 focused tranche 已经覆盖 v112 失败 pair，继续只调 loss multiplier 和 pair margin 不是主方向。

更具体地说：

- v112 的失败看起来主要 near-margin；
- v113 加强 loss 后没有把 near-margin 推正；
- 反而引入了 19 个 deep structural score gap；
- false-delay 被推到 1% 以上；
- local gate 和 focused pair gate 都没有通过。

因此不应继续盲目做 multiplier sweep。

## 下一步

继续 Stage 3，但回到 v112 作为当前 best checkpoint / evidence baseline。

下一步应做两件事之一：

1. 做 top-context 特征/表示审计，优先针对 `b6d808ebac2a6dd8`、`d519291840dd7000`、`ddcb5387bef3bf63` 这类 v113 出现 deep gap 的 context，检查 candidate/action consequence 特征是否缺失或不可分。
2. 写更窄的 top-context repair sampler，只训练高失败 context 的正负 pair，并保持 v112 的 loss 强度附近，不再全局加大 focused pair multiplier。

仍然禁止：

- 不降低 `false_high_priority_on_delay <= 0.01`；
- 不降低 `safe_precision_ci_low >= 0.90`；
- 不把 v113 的高 accepted count 当成进步，因为 local gate 已失败；
- 不进入 Stage 4。

## 本轮状态

```text
v113_training = completed
v113_local_gate = fail
v113_pair_gate = fail
v113_replaces_v112 = false
recommended_action = return_to_v112_baseline_and_repair_context_features_or_sampler
stage4_candidate_ready = false
production_ready = false
```
