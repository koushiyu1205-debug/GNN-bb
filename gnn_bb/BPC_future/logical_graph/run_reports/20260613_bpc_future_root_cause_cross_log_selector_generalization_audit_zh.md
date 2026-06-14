# BPC_future 根因审计补充：cross-log selector generalization audit

日期：2026-06-13

## 目标

前一轮 `trajectory selector calibration audit` 只在 Phase 10H 的 3 个 20-task instance 上校准，结论是：

- active-relation + batch coherence 是当前最强的 addition-before 信号；
- 但 leave-one-instance 已经明显失败；
- 因此不能把 Phase 10H 内部阈值直接接入主线。

本轮继续做只读交叉日志审计：

> 把相同特征抽取扩展到多个已有 20-task 结果集，检查 Phase 10H 的规则是否外推，以及在更大 strict improved/worsened 集合上是否能重新学到稳定规则。

本轮不改 solver、pricing、RMP、Pulse worker、certificate 或 lower-bound。

## 数据

扫描并选取同时满足以下条件的 summary/log：

- 20-task；
- 非 baseline；
- 有 `log_path`；
- JSONL 中存在 heuristic `journey_pricing` 的 returned task-set samples；
- summary 中有 `improvement_class`，取值至少包含 `improved` / `worsened` / `no_regression`。

纳入的 7 个结果集：

- `sharded_pulse_phase10b_profile_dp_state_cap_sensitivity_smoke_20260613`
- `sharded_pulse_phase10d_profile_dp_mask_hotspot_repeat_smoke_20260613`
- `sharded_pulse_phase10e_profile_dp_ordering_attribution_smoke_20260613`
- `sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613`
- `sharded_pulse_phase11a_profile_pricing_time_sensitivity_smoke_20260613`
- `sharded_pulse_phase9j_rmp_dual_stabilization_repeat_ab_smoke_20260613`
- `sharded_pulse_phase9k_rmp_dual_stabilization_hardset_ab_smoke_20260613`

总样本：

```text
stage rows = 334
runs = 98
datasets = 7
```

标签分布：

```text
improved = 98
worsened = 120
no_regression = 116

incumbent_within2 True = 143
incumbent_within2 False = 191

zero_within2 True = 192
zero_within2 False = 142
```

各结果集分布：

| dataset | stage rows | runs | labels | incumbent labels |
|---|---:|---:|---|---|
| phase10b state cap sensitivity | 22 | 6 | worsened 16, no_regression 3, improved 3 | false 16, true 6 |
| phase10d mask hotspot repeat | 60 | 18 | no_regression 47, worsened 7, improved 6 | false 38, true 22 |
| phase10e ordering attribution | 60 | 18 | no_regression 40, worsened 20 | false 40, true 20 |
| phase10h early new-task-set quota | 64 | 18 | improved 40, worsened 24 | false 38, true 26 |
| phase11a pricing time sensitivity | 44 | 12 | worsened 25, improved 19 | true 24, false 20 |
| phase9j dual stabilization repeat | 24 | 8 | no_regression 10, improved 10, worsened 4 | true 14, false 10 |
| phase9k dual stabilization hardset | 60 | 18 | worsened 24, improved 20, no_regression 16 | true 31, false 29 |

## Phase10H 规则外推结果

把前一轮 Phase10H 上最好的规则直接应用到全部 334 rows。

### `incumbent_within2`

Phase10H 单特征规则：

```text
active_avg_jaccard <= 0.3055555555555555
```

全量外推：

```text
accuracy = 0.6287425149700598
tp = 84
fp = 65
tn = 126
fn = 59
n = 334
```

Phase10H 二特征规则：

```text
active_redundant_frac <= 0.16666666666666666
and pair_overlap >= 0.25
```

全量外推：

```text
accuracy = 0.6197604790419161
tp = 19
fp = 3
tn = 188
fn = 124
n = 334
```

解释：

- 二特征规则 false positive 少；
- 但漏掉 124 个 downstream incumbent positives；
- 它太保守，不能作为 hidden-good-batch selector。

### Final improved

Phase10H 单特征规则：

```text
active_avg_overlap <= 0.5555555555555556
```

全量外推：

```text
accuracy = 0.5029940119760479
tp = 60
fp = 128
tn = 108
fn = 38
n = 334
```

Phase10H 二特征规则：

```text
active_redundant_frac <= 0.5833333333333334
and pair_overlap <= 0.5416666666666666
```

全量外推：

```text
accuracy = 0.7964071856287425
tp = 36
fp = 6
tn = 230
fn = 62
n = 334
```

注意：

- 二特征规则的 accuracy 看起来高；
- 但 tp 只有 36，fn 有 62；
- 它主要靠保守地预测 negative / non-improved 获得高准确率；
- 对“找出能改善 20 的 batch”这个目标来说，这不是可用 selector。

## Strict improved/worsened 集合

排除 `no_regression` 后：

```text
strict rows = 218
improved = 98
worsened = 120
```

各结果集 strict rows：

```text
phase10h = 64
phase11a = 44
phase9k = 44
phase10e = 20
phase10b = 19
phase9j = 14
phase10d = 13
```

### Strict 集合内重拟合：仍不够

预测 `incumbent_within2` 的最佳单特征：

```text
best_rc <= -56.513515941
accuracy = 0.6284403669724771
tp = 58
fp = 34
tn = 79
fn = 47
n = 218
```

预测 `incumbent_within2` 的最佳二特征：

```text
active_avg_jaccard <= 0.3333333333333333
and best_rc <= -27.84693

accuracy = 0.6834862385321101
tp = 89
fp = 53
tn = 60
fn = 16
n = 218
```

预测 final improved 的最佳单特征：

```text
pair_overlap <= 0.5416666666666666
accuracy = 0.6467889908256881
tp = 40
fp = 19
tn = 101
fn = 58
n = 218
```

预测 final improved 的最佳二特征：

```text
active_redundant_frac <= 0.5833333333333334
and pair_overlap <= 0.5416666666666666

accuracy = 0.6880733944954128
tp = 36
fp = 6
tn = 114
fn = 62
n = 218
```

解释：

- 在更大的 strict 集合里，最佳规则精度比 Phase10H 内部显著下降；
- final improved 的最佳二特征仍只抓到 36/98 个 improved；
- 这仍然是 negative filter，不是 positive selector。

## Leave-one-dataset 泛化

对 strict improved/worsened 集合做 leave-one-dataset：

- 每次留出一个结果集；
- 在其余结果集上拟合最佳单特征阈值；
- 在留出的结果集上测试。

### `incumbent_within2`

总结果：

```text
accuracy = 0.5321100917431193
tp = 47
fp = 44
tn = 69
fn = 58
n = 218
```

留出明细：

| holdout | train-selected rule | test accuracy | tp | fp | tn | fn |
|---|---|---:|---:|---:|---:|---:|
| phase10b | `best_rc <= -56.513515941` | 0.473684 | 3 | 8 | 6 | 2 |
| phase10d | `best_rc <= -56.513515941` | 0.692308 | 8 | 4 | 1 | 0 |
| phase10e | `best_rc <= -56.513515941` | 0.650000 | 4 | 5 | 9 | 2 |
| phase10h | `best_rc <= -56.513515941` | 0.500000 | 7 | 13 | 25 | 19 |
| phase11a | `active_avg_overlap >= 1.0` | 0.636364 | 8 | 0 | 20 | 16 |
| phase9j | `best_rc <= -56.7919775` | 0.500000 | 3 | 0 | 4 | 7 |
| phase9k | `best_rc <= -52.5965645` | 0.409091 | 14 | 14 | 4 | 12 |

### Final improved

总结果：

```text
accuracy = 0.5642201834862385
tp = 3
fp = 0
tn = 120
fn = 95
n = 218
```

留出明细：

| holdout | train-selected rule | test accuracy | tp | fp | tn | fn |
|---|---|---:|---:|---:|---:|---:|
| phase10b | `pair_overlap <= 0.5416666666666666` | 0.842105 | 0 | 0 | 16 | 3 |
| phase10d | `pair_overlap <= 0.5416666666666666` | 0.538462 | 0 | 0 | 7 | 6 |
| phase10e | `pair_overlap <= 0.5416666666666666` | 1.000000 | 0 | 0 | 20 | 0 |
| phase10h | `active_avg_overlap <= 0.3333333333333333` | 0.421875 | 3 | 0 | 24 | 37 |
| phase11a | `pair_overlap <= 0.5416666666666666` | 0.568182 | 0 | 0 | 25 | 19 |
| phase9j | `pair_overlap <= 0.5416666666666666` | 0.285714 | 0 | 0 | 4 | 10 |
| phase9k | `pair_overlap <= 0.5416666666666666` | 0.545455 | 0 | 0 | 24 | 20 |

这是非常强的负证据：

- leave-one-dataset 后，final improved selector 基本退化成“几乎全预测 non-improved”；
- tp 只有 3，fn 95；
- 这种规则无法承担“20 大幅优化”的任务，因为它几乎不敢选 improved batch；
- 它也不能说明根因已转化为可执行优化方向。

## 根因更新

跨日志审计把边界进一步收紧：

> active-relation / batch-coherence 特征确实是当前最强的可观测信号，但它们不是跨配置、跨结果集稳定的 selector。不同 profile 改变了候选生成、returned cut、RMP active basis 和 residual tail 的耦合方式，使同一个阈值在另一个结果集上失效。

因此根本原因不是 Pulse 本身，也不是某个单一参数，而是：

1. column generation tail 的收益依赖 concrete returned batch 对后续 RMP active-basis trajectory 的影响；
2. 这个影响由 instance、CG stage、profile、RMP active state、candidate signature、timing、arc option、return limit 和 residual pricing tail 共同决定；
3. 当前系统没有能跨这些 context 泛化的 addition-before trajectory selector；
4. 没有 selector 时，任何“多搜一点 / 多返一点 / 多 worker 一点”的机制都只是扰动，可能改善也可能恶化；
5. 5/10 规模无法承受这种扰动的固定成本；
6. 20 规模也无法稳定获益，因为好 trajectory 和坏 trajectory 都会被触发。

## 为什么这解释了“5/10 不退化、20 不优化”

5/10：

- solver 原本很快；
- worker/probe/extra-return/profile change 都有固定成本；
- selector 不可靠时，触发就是纯开销或坏扰动；
- 所以只能靠 no-op / min-task / 20-only gate 避免退化。

20：

- 负列和候选很多；
- 但好 batch 不是由单一 RC、overlap 或 diversity 决定；
- profile 或 return 参数改变后，good/bad trajectory 的分布也变；
- 简单规则跨结果集不泛化；
- 所以 20 无法稳定优化。

## 当前仍不能做的事

不能把以下方向作为已证明根因修复：

- 默认启用 Pulse worker；
- 默认扩大 returned count；
- 默认调高 profile-DP cap；
- 使用 Phase10H 内部阈值；
- 使用同样本最优二特征规则；
- 使用 best-RC 或 low-overlap 单规则；
- 打开 official certificate gate。

这些方向都缺少跨结果集 / 跨 instance 的正向证据。

## 下一步建议

继续 calibration-only，但需要升级数据结构：

1. 从 stage-row 变成 candidate/batch-row；
2. 加入 context 字段：
   - dataset/profile；
   - instance；
   - CG stage；
   - current active top samples；
   - current fractional pressure；
   - recent active hash churn；
   - residual tail pricing state；
3. 加入 concrete column 字段：
   - signature hash；
   - sequence；
   - start time；
   - arc option family；
   - true RC / rough RC gap；
   - new/replacement/support-changing class；
4. 标签不只用 final outcome，还要拆成：
   - next incumbent；
   - next incomplete-heavy path；
   - active persistence；
   - residual tail family chain；
5. 必须做 leave-one-instance / leave-one-dataset 验证；
6. 没有跨日志稳定结果前，不做主线 selector。

## 目标状态

目标仍未完成。

本轮明确新增证据：

- Phase10H 内部看似可用的 selector，在跨日志外推中不稳定；
- 更大 strict improved/worsened 集合中，最佳简单规则只能做弱 negative filter；
- leave-one-dataset 后几乎抓不到 final improved；
- 因此还不能宣称找到能保证 exactness、5/10 不退化、20 大幅加速的优化方向。

