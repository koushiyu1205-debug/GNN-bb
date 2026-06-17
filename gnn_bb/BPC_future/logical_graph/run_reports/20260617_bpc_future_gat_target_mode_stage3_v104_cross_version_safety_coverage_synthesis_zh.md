# 2026-06-17 BPC_future GAT Target Mode Stage 3 v104 Cross-version 综合报告

## 读取范围

本报告把早期 Stage 3 结论和最近 v99/v102/v103 训练结果放在一起看，目标是判断下一步是否还应继续盲目调参。

读取/复核范围：

- `v36_neighbor_roi_repair_plan`
- `v41_v39_false_positive_catalog`
- `v43_v15_missed_high_roi_diagnosis`
- `v44_v39_delay_safe_shell_shortfall`
- `v45_false_delay_contrast_synthesis`
- `v98_focused_pair_failure_anatomy`
- `v100_v99_focused_pair_failure_anatomy`
- `v101_focused_failure_and_combined_training_synthesis`
- `v102_seed13_safety_constrained_focused_combined_training`
- `v102_focused_pair_failure_anatomy`
- `v103_seed13_light_safety_focused_combined_training`
- `v103_focused_pair_failure_anatomy`

边界保持不变：这些都是离线 Stage 3 诊断/训练/阈值选择，不运行 BPC、pricing、RMP 或 certificate。GAT / CBF / kNN / OOD 只能做 discovery ordering 和 finite-delay admission scheduling；最终证明必须由当前 branch/cut/dual 下的 full exact pricing no-negative closure 给出。

## 总结论

v99 到 v103 没有推翻早期 v36/v41/v44/v45 的判断，而是把同一个问题量化得更清楚：

1. 当前模型已经能学到一部分 high-ROI / delay-safe 信号；
2. 但全局放宽会重新打开 false-delay / low-ROI admission；
3. 风险约束和 delay gate 可以把 false-safe 压到 0，但会把 accepted shell 收得过窄；
4. 现在的主要问题不是单个 loss 权重，而是 admission scheduling 缺少 coverage/family/context 约束；
5. Stage 4 仍不能进入，因为 Stage 3 hard gate 没过，尤其 focused pair gate、safe precision CI、family coverage、kNN/OOD、online shadow 都未满足。

当前判断：

```text
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
selector_can_certificate = false
recommended_next_step = coverage_constrained_family_context_frontier_before_more_loss_sweeps
```

## 旧版本到新版本的因果链

### v36: high-ROI 被延迟

v36 发现 `roi_neighbor_delayed_high_roi_count = 3`，说明某些真实 high-ROI batch 会被 ROI-neighbor shell 延迟。

当时结论是不要全局放宽 threshold，而要做 narrow same-context contrast 和 ROI-neighborhood stability。这个判断仍然成立。

### v41: 放宽后 false-positive 集中爆出

v41 catalog 了 v39 的 delay false-positive：

```text
false_high_priority_on_delay_count = 44
delay_label_count = 98
false_high_priority_on_delay = 0.4489795918367347
high_priority_precision = 0.9402985074626866
candidate_delay_gate_blocked_count = 329
primary_diagnosis = raise_candidate_threshold_or_make_candidate_head_usable_before_delay_gate
```

这说明单纯依赖 delay gate 或全局 threshold 会在少数 `sector-wave|20` context 上出问题。

### v43: missed high-ROI 不是只差阈值

v43 对 v15 missed high-ROI 的诊断是：

```text
primary = candidate_head_score_gap_plus_embedding_structural_gap
missed_high_roi_opportunities = 16
random-wave = 5
sector-wave = 11
```

这一步很关键：missed high-ROI 不是简单把阈值降低一点就能修好，而是 candidate-head 分数差、embedding 结构差、same-context hard-negative 不足同时存在。

### v44/v45: delay-safe 壳层存在，但覆盖太小

v44 的 frontier 证明严格 delay-safe threshold 确实存在：

```text
delay_safe_threshold_count = 1309
delay_safe_with_accepted_batch_count = 335
delay_safe_accepted_batch_count_max = 2
recommended_primary = delay_safe_shell_exists_but_coverage_too_small
```

v45 的 false-delay contrast smoke 把 false-delay 压到了 0：

```text
safe_precision = 1.0
safe_precision_ci_low = 0.4384939195509822
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
accepted = 3 / 123
```

所以旧版本已经给出方向：delay safety 可以做到，但 coverage 不够，不能直接进 Stage 4。

## v99/v102/v103 对照

| run | admission mode | accepted | accepted ROI | ROI CI low | safe CI low | false-safe | family min ROI | family missing | focused strict |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| v99 | high_priority | 49 | 3.9984 | 1.7758 | 0.9273 | 0.2069 | 0.1618 | none | 0.4483 |
| v102 | risk_adjusted_product, delay penalty 2.0 | 5 | 0.9782 | 0.7365 | 0.5655 | 0.0000 | 0.9719 | greedy-anchor | 0.4414 |
| v103 | risk_adjusted_product, delay penalty 1.0 | 2 | 1.3101 | 1.2792 | 0.3424 | 0.0000 | 1.3101 | greedy-anchor, sector-wave | 0.5793 |

### v99 的含义

v99 证明 explicit focused combined loss 能扩大 high-ROI capture：

```text
accepted_batch_count = 49
accepted_batch_roi = 3.9983911766335503
accepted_batch_roi_ci_low = 1.775848488768101
family_holdout_missing_accepted_families = []
family_holdout_min_high_roi_capture_rate = 1.0
```

但它同时失败在 safety 和 family ROI：

```text
false_high_priority_on_delay = 0.20689655172413793
false_safe_rate_union = 0.20689655172413793
family_holdout_min_accepted_roi = 0.16178512875110476
```

更细看 family：

- `greedy-anchor`: accepted 13，但 ROI 只有 `0.1618`；
- `random-wave`: accepted 10，ROI `0.4043`；
- `sector-wave`: accepted 26，ROI `7.2990`。

也就是说 v99 的总体 ROI 被 `sector-wave` 高 ROI 拉高，但 admission policy 仍会放进低 ROI family。这不能作为 Stage 4 gate。

### v102 的含义

v102 加强 safety：

```text
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_score_penalty = 2.0
hard_roi_negative_delay_loss_multiplier = 2.0
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
```

但代价是 coverage 明显收缩：

```text
accepted_batch_count = 5
accepted_batch_rate = 0.0684931506849315
safe_precision_ci_low = 0.565508505247919
family_holdout_missing_accepted_families = ['greedy-anchor']
family_holdout_min_high_roi_capture_rate = 0.16666666666666666
```

focused pair failure audit：

```text
pair_count = 145
pair_pass_count = 64
strict_pair_pass_rate = 0.4413793103448276
all_failed_heads_near_rate_among_failed = 1.0
any_failed_head_deep_rate_among_failed = 0.0
```

这说明 v102 的问题不是 deep structural impossible，而是 safety 过强以后 ranking/coverage 没跟上。

### v103 的含义

v103 放松 v102 的 safety penalty 后，focused pair ranking 变好：

```text
focused_raw_pair_pass_rate = 0.6689655172413793
focused_admission_pair_pass_rate = 0.6896551724137931
focused_delay_risk_pair_pass_rate = 0.6344827586206897
focused_strict_pair_pass_rate = 0.5793103448275863
```

并且 false-safe 仍为 0：

```text
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
```

但 accepted shell 进一步变窄：

```text
accepted_batch_count = 2
accepted_batch_rate = 0.0273972602739726
safe_precision_ci_low = 0.3423719528896193
family_holdout_missing_accepted_families = ['greedy-anchor', 'sector-wave']
family_holdout_min_high_roi_capture_rate = 0.0
```

最严重的是 sector-wave：

```text
sector-wave oracle_high_roi_count = 18
sector-wave accepted_batch_count = 0
sector-wave accepted_high_roi_count = 0
```

因此 v103 不能被解读为更接近 Stage 4。它只是说明 near-margin focused pair 可以继续被推高，但当前 threshold/family fallback 选择会漏掉真正重要的 high-ROI family。

## v103 failure anatomy

v103 的 focused pair failure 审计：

```text
pair_count = 145
pair_pass_count = 84
strict_pair_pass_rate = 0.5793103448275863
raw_fail_rate = 0.3310344827586207
admission_fail_rate = 0.3103448275862069
delay_risk_fail_rate = 0.36551724137931035
all_failed_heads_near_rate_among_failed = 0.9344262295081968
any_failed_head_deep_rate_among_failed = 0.0
```

Top failing contexts 仍集中在 20-task sector-wave：

| context hash | family | task | pair | failed | min raw margin | min admission margin | min delay-risk margin |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ac15bc4e7e3d6fff | sector-wave | 20 | 35 | 18 | -0.0023 | -0.0013 | -0.0006 |
| b6d808ebac2a6dd8 | sector-wave | 20 | 25 | 16 | -0.0005 | -0.0047 | -0.0103 |
| 79fde658840fe2b8 | sector-wave | 20 | 35 | 10 | -0.0027 | -0.0016 | -0.0008 |
| 4e481a6307fca228 | sector-wave | 20 | 12 | 6 | -0.0060 | -0.0091 | -0.0134 |
| d519291840dd7000 | random-wave | 20 | 10 | 4 | 0.0116 | 0.0050 | -0.0007 |
| 67c11b5ec80925ec | random-wave | 20 | 7 | 4 | -0.0011 | 0.0000 | 0.0000 |
| 45baa40751a0bf77 | sector-wave | 20 | 3 | 3 | -0.0237 | -0.0204 | -0.0198 |

新理解：

- 大多数失败的 margin 很小，继续做 targeted near-margin repair 有意义；
- 但 top contexts 与 sector-wave high-ROI miss 重叠，不能只优化 focused strict pair pass；
- 如果 selection frontier 没有显式 family/context coverage 约束，ranking 变好也可能被阈值选择吞掉；
- v103 的 `sector-wave accepted = 0` 比 focused pair pass 更重要，因为 Stage 5 的 20-task 加速主要依赖这些高 ROI 20-task 区域。

## 新问题

### 1. Safety 与 coverage 的 Pareto 不稳定

v99 是高 coverage / 高 ROI / unsafe，v102/v103 是 safe / low coverage。当前没有一个 checkpoint 同时满足：

- false-safe 接近 0；
- safe precision CI 过线；
- high-ROI family capture 不坍缩；
- focused pair strict pass 过线。

这说明下一步不能只扫 loss multiplier。需要把 selection frontier 本身改成 coverage-constrained。

### 2. Family ROI guard 不能只看全局 accepted ROI

v99 全局 accepted ROI 很高，但 greedy-anchor 和 random-wave 低 ROI admission 被 sector-wave 掩盖。v103 全局 accepted ROI/CI 看起来干净，但直接漏掉 sector-wave。

因此 Stage 3 gate 需要继续坚持 family holdout，不应降低 family gate。

### 3. Delay-safe 壳层不是 production policy

v44/v45/v102/v103 共同证明 delay-safe shell 存在，但都太窄。它只能作为安全基线或 fallback，不是最终 admission policy。

### 4. Candidate head 与 delay-risk head 仍需同 context 联合约束

v103 的 failure audit 显示 raw/admission/delay-risk failure 都有，且 mostly near-margin。这支持继续训练三头联合 focused pair loss，但需要配合 coverage-constrained threshold search，否则训练收益不会转化成 accepted high-ROI family。

### 5. Stage 4/Stage 5 仍缺在线证据

即使 Stage 3 离线 gate 通过，也还需要：

- 5/10 no-regression sentinel；
- 20-task ROI A/B；
- kNN/OOD shell；
- online shadow/opt-in replay；
- final exact pricing certificate。

当前 v99/v102/v103 都不满足这些条件。

## 下一步建议

不要继续做普通参数扫。下一步应先做一个 coverage-constrained frontier audit，然后再决定是否训练。

建议 v105：

1. 在现有 v99/v102/v103 checkpoint 上离线枚举 threshold/admission frontier；
2. 增加硬约束：
   - `false_safe_rate_union <= 0.01`；
   - `false_high_priority_on_delay <= 0.01`；
   - 每个有 oracle high-ROI 的 family 至少接受一个 high-ROI batch；
   - sector-wave high-ROI capture 不得为 0；
   - safe precision CI 不低于当前 Stage 3 gate；
3. 输出 Pareto frontier：
   - accepted count；
   - accepted ROI/CI；
   - family high-ROI capture；
   - focused pair strict pass；
   - false-safe；
4. 如果现有 logits 上存在可行 frontier，再把该 frontier 规则固化成 admission scheduling；
5. 如果不存在可行 frontier，再回到模型训练，优先加入 family/context coverage-aware loss 或 per-family calibrated threshold head。

这个顺序比继续调 v104/v105 loss 更稳，因为它先回答一个关键问题：当前模型分数空间里是否已经存在“安全且覆盖 high-ROI family”的可行阈值面。

## Exactness Boundary

```text
runs_bpc_or_pricing = false
runs_rmp = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
stage4_candidate_ready = false
```

`DELAY_QUEUE` 只能有限延迟 true-RC negative column，不能永久丢弃。GAT 可以让前面的 column generation 更聪明，但最后 certificate 必须由 exact pricing 重新确认：在当前 branch/cut/dual 下，整个配置宇宙没有任何负 reduced-cost journey。

