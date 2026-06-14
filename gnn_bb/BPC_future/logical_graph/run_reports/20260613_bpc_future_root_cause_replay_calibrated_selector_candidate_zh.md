# BPC_future Root Cause replay-calibrated selector candidate 审计报告

日期：2026-06-13

## 目标

本轮只做根因证据审计，不修改主线求解逻辑。

目标是回答：

1. target002 pt0.3 exact replay 加入后，是否已经出现 addition-before selector candidate；
2. 如果有，哪个候选最适合作为下一步 full BPC A/B 的入口；
3. 这个候选为什么仍不能被当作 production-validated selector。

## 输入

审计脚本：

```text
BPC_future/scripts/analyze_replay_calibrated_selector_candidate.py
```

输出目录：

```text
BPC_future/results/root_cause_replay_calibrated_selector_candidate_20260613
```

输入 candidate-impact rows 来自 5 组 exact replay 数据：

```text
BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/duplicate_noop_smoke/candidate_impact_rows.csv
BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/real_capture_mt20_apollo/candidate_impact_rows.csv
BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/impact/candidate_impact_rows.csv
BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613/impact/candidate_impact_rows.csv
BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/impact/candidate_impact_rows.csv
```

selector gate summary：

```text
BPC_future/results/root_cause_counterfactual_replay_selector_gate_with_target002_pt03_20260613/summary.json
```

## 数据规模

```text
row_count = 280
label_counts:
  improved = 209
  noop = 71
```

这里的 label 来自 counterfactual replay 中单列 treatment 对 RMP objective 的影响，不是 observational downstream label。

## 推荐候选

当前最直接的 replay-calibrated addition-before selector candidate 是：

```text
true_reduced_cost <= -12.430587
```

对应规则：

```text
feature = true_reduced_cost
operator = <=
threshold = -12.430587
```

它只使用加列前已经可见的 true reduced cost，不依赖后验 RMP outcome、后验 active support、incumbent 变化或 certificate effect。

## Full-sample 指标

```text
total = 280
predicted_positive = 200
tp = 178
fp = 22
tn = 49
fn = 31
precision = 0.89
recall = 0.8516746411483254
accuracy = 0.8107142857142857
```

含义：

- 该阈值能覆盖大部分 replay-positive rows；
- precision 已经足够作为下一步 A/B selector 候选；
- 但仍有 22 个 false positives 和 31 个 false negatives，不能视为 production proof。

机器 verifier 对应字段：

```text
false_positive_count = 22
false_negative_count = 31
```

## Case-level 指标

```text
case_count = 82
cases_with_positive = 70
cases_with_selected = 68
cases_with_selected_positive = 58
selected_only_noop = 10
missed_positive_case = 12
```

这比 row-level 指标更重要，因为 full BPC 中一次 worker/probe 的开销按 context/case 支付。

`selected_only_noop = 10` 说明这个规则仍会在一些 context 中只选出 no-op candidate。
`missed_positive_case = 12` 说明它也会漏掉一部分 replay-positive context。

所以它不能直接成为默认 worker gate。

## 与旧结论的关系

旧结论是：

```text
has_stable_addition_before_selector = false
```

加入 target002 pt0.3 后，这个结论应修正为：

```text
has_replay_calibrated_selector_candidate = true
has_production_validated_selector = false
```

也就是说：

- 不能再说“完全没有 selector 候选”；
- 也不能说“优化方向已经证明”。

当前更准确的状态是：已有一个足够进入生产 A/B 的 replay-calibrated selector candidate，但它尚未证明能在真实 BPC trajectory 中同时满足 5/10 no-regression 与 selected 20-task speedup。

## 为什么不能直接进主线

这个候选仍然不是 production-validated selector，原因有三点：

1. 它仍有 false positives：`fp = 22`、`selected_only_noop = 10`；
2. 它仍有 false negatives：`fn = 31`、`missed_positive_case = 12`；
3. 它只证明 replay-local RMP impact，不证明 full BPC wall time、gap、status、final-judge tail 会改善。

因此它只能作为下一步 full BPC A/B 的 candidate gate，不能被默认启用，不能触发 official certificate，也不能被写成“根因目标已完成”。

## 与已有 worker 配置的关系

已有 worker impact-filter profile 中出现过 `min_true_rc=-30.0` 这类阈值，但它不是当前审计出的阈值。

当前 replay-calibrated 阈值是：

```text
true_reduced_cost <= -12.430587
```

所以旧 profile 不能替代下一步 A/B。下一步需要单独配置严格的 addition-before selector，并按 5/10 no-regression 与 20 hard-repeat ROI gate 重新验证。

## 下一步 A/B 要求

下一步若继续，应做 full BPC A/B，而不是继续堆 Pulse 算法：

1. baseline；
2. calibrated selector candidate；
3. 5/10 全量 no-regression gate；
4. selected 20 hard repeats 的 wall time / gap / status / final-judge tail gate；
5. official exactness 不变；
6. no certificate effect；
7. worker/probe no-column 或 incomplete 不得产生 lower bound。

只有当这个 A/B 同时通过 5/10 和 20 gate，才能把 `has_production_validated_selector` 改成 true。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_replay_calibrated_selector_candidate.py \
--output-dir BPC_future/results/root_cause_replay_calibrated_selector_candidate_20260613
```

结果：

```text
all_checks_pass = true
recommended_selector_candidate = true_reduced_cost_<=_-12.430587
production_validated_selector = false
```

## 结论

本轮审计把根因结论推进了一步：

> 已经有 replay-calibrated addition-before selector candidate；推荐候选是 `true_reduced_cost <= -12.430587`。

但目标仍未完成：

```text
production_validated_selector = false
has_20_walltime_speedup_evidence = false
production_direction_proven = false
```

真正的下一步不是继续扩大 Pulse worker，而是用这个候选跑受控 full BPC A/B，证明它能在 exactness 不变、5/10 不退化的前提下，稳定改善 selected 20-task hard repeats。
