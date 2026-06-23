# 2026-06-22 BPC_future GAT Stage 3 v121 targeted repair 综合报告

## 结论

v121 在 v120 基础上做了 training-only targeted repair：对 focused 失败行做额外 pair replay，对 train split 中接近阈值但被延迟的 safe-positive 行做额外 sample replay。结果是局部指标有明确改善，但还没有完成 Stage 3，也不能进入 Stage 4。

```text
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
exactness_preserved = true
runs_bpc_or_pricing = false
selector_can_certificate = false
```

主要变化：

- focused strict pair pass 从 v120 的 `72/78 = 0.9230769231` 提升到 v121 的 `75/78 = 0.9615384615`。
- local validation accepted ROI 从 `19.3365859772` 提升到 `19.6157228108`，ROI CI-low 从 `10.2191974778` 提升到 `10.5584060212`。
- kNN/OOD scale strict 已过 safety gate：safe precision CI-low `0.9010957324 >= 0.9`。
- kNN/OOD global strict 仍差一点：safe precision CI-low `0.8984820938 < 0.9`。
- focused gate 仍有 3 个 failed pair，严格要求是 `78/78`。

因此 v121 是一个有用的 Stage 3 进展点，不是 Stage 4 checkpoint。

## 为什么 v108 选 epoch 1 而不是 epoch 7/8

v108 的 checkpoint selection 策略不是最低 validation loss，而是：

```text
deployment gate first -> ROI CI / baseline utility -> validation loss tie-breaker
```

v108 中没有任何 epoch 通过 local deployment gate，所以选择器进入 diagnostic 排序。diagnostic key 优先看失败原因数量、high-priority precision CI-low、safe precision CI-low、ROI CI-low、utility、accepted ROI、accepted count 等安全/收益指标，validation loss 只在很靠后的 tie-breaker 中起作用。

v108 的关键对比：

| epoch | validation loss | accepted | HP precision | accepted ROI | false HP on delay | local gate |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 4.466115 | 13 | 1.000000 | 33.163725 | 0.000000 | false |
| 7 | 3.170040 | 158 | 0.994840 | 7.169939 | 0.034965 | false |
| 8 | 3.544146 | 182 | 0.981457 | 6.289559 | 0.146853 | false |

epoch 7 的 loss 最低，但它接受太多 batch 后把 false-high-priority-on-delay 拉到 `0.034965`，超过 `0.01` 门槛，ROI 也掉到 `7.169939`。epoch 8 更差，false-high-priority-on-delay 到 `0.146853`，HP precision 也掉到 `0.981457`。epoch 1 虽然 validation loss 高，但它是更保守的 checkpoint：false delay 为 0，HP precision 为 1，accepted ROI 最高。所以 v108 选 epoch 1 是符合当前目标函数的。

## v121 训练配置

训练命令核心改动：

- `--focused-pair-boost-row-indices-file`
- `--focused-pair-boost-loss-multiplier 1.5`
- `--targeted-safe-positive-row-indices-file`
- `--targeted-safe-positive-loss-multiplier 0.75`

selector 来自：

- `BPC_future/results/gat_batch_impact_v121_targeted_repair_selectors_20260622/focused_boost_row_indices.json`
- `BPC_future/results/gat_batch_impact_v121_targeted_repair_selectors_20260622/targeted_safe_positive_row_indices.json`

边界：

- focused boost 只用于 training-only extra replay。
- targeted safe-positive selector 只使用 train split 候选；validation delayed-safe rows 只做审计，不进入训练，避免泄漏。
- validation/evaluation/gate 逻辑没有放宽。
- 该模型不能产生 official bound 或 certificate，也不能永久丢弃 true-RC negative columns。

## v120 vs v121

| 指标 | v120 | v121 | 变化 |
|---|---:|---:|---:|
| best epoch | 6 | 4 | - |
| accepted batch count | 35 | 35 | 0 |
| accepted batch ROI | 19.336586 | 19.615723 | +0.279137 |
| accepted ROI CI-low | 10.219197 | 10.558406 | +0.339209 |
| high-priority precision | 0.997271 | 0.996737 | -0.000534 |
| high-priority CI-low | 0.990106 | 0.988183 | -0.001924 |
| safe precision | 1.000000 | 1.000000 | 0 |
| safe precision CI-low | 0.901096 | 0.901096 | 0 |
| false HP on delay | 0.007220 | 0.007220 | 0 |
| focused strict pass | 72/78 | 75/78 | +3 pairs |

v121 的主收益来自 focused 排序修复和 ROI 小幅提高；安全指标没有恶化到越界，但 high-priority precision CI-low 略降。

## v121 epoch 选择

v121 中 best loss 是 epoch 3，但最终选 epoch 4：

| epoch | validation loss | local gate | accepted | HP precision | accepted ROI | false HP on delay |
|---:|---:|---|---:|---:|---:|---:|
| 1 | 6.008963 | true | 35 | 1.000000 | 17.043637 | 0.000000 |
| 2 | 6.407225 | true | 35 | 0.997211 | 17.936514 | 0.007220 |
| 3 | 4.623977 | true | 35 | 0.996890 | 19.370466 | 0.007220 |
| 4 | 4.801371 | true | 35 | 0.996737 | 19.615723 | 0.007220 |
| 5 | 4.709010 | true | 36 | 0.996947 | 18.862365 | 0.007220 |
| 6 | 4.927077 | true | 35 | 0.997701 | 19.135394 | 0.007220 |
| 7 | 6.354678 | true | 35 | 0.996055 | 18.511942 | 0.007220 |
| 8 | 6.207435 | false | 51 | 0.973510 | 5.375238 | 0.014440 |

因为 epoch 4 在 local gate 已通过的集合里 ROI/utility 更好，所以优先于 epoch 3；epoch 8 直接 local gate failed。

## focused failure 审计

v121 focused pair：

```text
pair_count = 78
failed_pair_count = 3
strict_pair_pass_rate = 0.9615384615
raw_fail_count = 2
admission_fail_count = 2
delay_risk_fail_count = 3
```

剩余失败集中在两个 random-wave context：

- `9f80ae35ea87da5b`，apollo15 tasks030_03：2 个 failed pair，包含 shared-signature confounder / mixed-margin failure。
- `ddcb5387bef3bf63`，tranquillitatis tasks020_03：1 个 near-margin delay-risk failure，raw/admission 已为正，delay-risk margin 约 `-0.0047`。

v120 中失败的旧 context 已有一批被修复，但新的剩余失败说明继续盲目调 multiplier 的收益有限。

## kNN/OOD 审计

| 审计 | v120 accepted | v120 safe CI-low | v121 accepted | v121 safe CI-low | v121 ready |
|---|---:|---:|---:|---:|---|
| global strict | 33 | 0.895727 | 34 | 0.898482 | false |
| scale strict | 32 | 0.892817 | 35 | 0.901096 | true |

v121 global strict：

```text
accepted_batch_count = 34
accepted_batch_roi = 17.0703342009
safe_precision = 1.0
safe_precision_ci_low = 0.8984820938
false_safe_rate_union = 0.0
validation_candidate_ready = false
```

v121 scale strict：

```text
accepted_batch_count = 35
accepted_batch_roi = 19.6157228108
safe_precision = 1.0
safe_precision_ci_low = 0.9010957324
false_safe_rate_union = 0.0
validation_candidate_ready = true
```

scale grouping 已经满足 kNN/OOD validation safety shell，但 global grouping 还差 `0.0015179062` 的 safe CI-low。因此不能把 v121 说成 kNN/OOD 全通过。

## 当前 blocker

```text
focused_pair_gate_failed = true
global_knn_ood_safe_ci_low_below_min = true
stage4_no_regression_not_run = true
online_shadow_and_opt_in_ab_not_run = true
```

Stage 4 仍然不能启动，直到：

- focused strict pair pass 达到 `78/78`；
- kNN/OOD global strict 和 scale strict 都通过；
- 再做 5/10 no-regression、20-task wall-time ROI 和 opt-in/shadow 运行；
- exact pricing closure 仍然负责 official certificate。

## 下一步

优先针对剩余两个 random-wave context 做小范围修复：

1. 对 `ddcb5387bef3bf63` 做 near-margin delay-risk 定向增强，目标是只修 delay-risk head，不扩大 accepted set。
2. 对 `9f80ae35ea87da5b` 做 action-consequence/context feature 检查或 selector 局部拆分；该 context 不像单纯 margin 不足。
3. 保持 validation delayed-safe rows 不进训练；只用它们作为审计目标。
4. 如果 focused 达到 `78/78`，再复跑 global/scale kNN/OOD；两者都过后才考虑 Stage 4 no-regression。

## 产物

- `BPC_future/results/gat_batch_impact_v121_targeted_repair_selectors_20260622/summary.json`
- `BPC_future/results/gat_batch_impact_training_v121_targeted_repair_seed13_20260622/metrics.json`
- `BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v121_targeted_repair_20260622/summary.json`
- `BPC_future/results/gat_batch_impact_knn_ood_audit_v121_targeted_repair_global_strict_20260622/summary.json`
- `BPC_future/results/gat_batch_impact_knn_ood_audit_v121_targeted_repair_scale_strict_20260622/summary.json`
