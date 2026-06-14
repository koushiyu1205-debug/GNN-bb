# BPC_future Root Cause target002 pt0.3 恢复与 Selector 结论修正报告

日期：2026-06-13

## 目标

本轮不做主线 solver 修改，只修正根因诊断中的过时结论。

需要回答两个问题：

1. `capture_target_002 / replay_candidate_003` 为什么之前没有 exact capture？
2. 新增 target002 pt0.3 exact replay 后，addition-before selector 结论是否仍然是“没有候选”？

## 结论

之前 target002 uncovered 的直接原因不是 current code 无法到达该 context，而是复核时使用了更紧的 `pricing_time_limit=0.2`，导致 cg1 returned-batch trajectory 提前分叉。

当前代码用 `pricing_time_limit=0.3`、`pricing_max_dp_states=1000`、同一 profile 重跑后，target002 对应的旧 phase10h context 可以恢复：

```text
active_hash_before = 16862add48072518
```

同时，加入 target002 pt0.3 exact replay 后，selector gate 结论也必须修正：

```text
旧结论：没有 addition-before selector 候选。
新结论：已有 replay-calibrated selector candidate，但还没有 production-validated selector。
```

因此，根因不是“完全没有 selector 信号”，而是：

> selector 信号已经出现，但还没有 full BPC A/B 证明它能在 exactness 不变、5/10 不退化的前提下大幅加速 20。

## target002 时间预算敏感性

`pricing_time_limit=0.2` 的 no-capture mirror 路径：

```text
c6ea96127d7c5d7b -> 6907bf1e60739a97 -> a37fc1e4e8451f9b
```

这会在 cg1 后进入另一个 active trajectory，因此 cg3 不能 exact 命中目标 context：

```text
target active_hash_before = 16862add48072518
```

`pricing_time_limit=0.3` 的 3-repeat no-capture mirror 恢复旧路径：

```text
c6ea96127d7c5d7b -> 427b1308ea279e0c -> 16862add48072518
```

该差异说明：20-task hard case 的 returned-batch composition 对早期 budget / truncation 非常敏感。早期加列选择会改变 active basis，然后改变后续 pricing universe。

## 新 exact capture 覆盖

新增 capture：

```text
BPC_future/results/root_cause_target002_capture_pt03_r3_20260613
```

capture audit：

```text
all_checks_pass = true
event_count = 10
complete_event_count = 10
returned_journey_count = 73
captured_journey_count = 73
```

target coverage：

```text
BPC_future/results/root_cause_counterfactual_capture_target_coverage_after_target002_pt03_20260613/summary.json

target_with_exact_capture_count = 3
uncovered_target_count = 0
capture_event_count = 114
all_checks_pass = true
```

这说明先前 3 个 recommended capture targets 现在都有 exact capture 覆盖。

## target002 local RMP impact

target002 pt0.3 replay impact：

```text
BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/impact/summary.json

case_count = 10
candidate_row_count = 73
high_impact_candidate_count = 62
noop_candidate_count = 11
full_batch_count = 10
full_batch_improved_count = 8
best_objective_delta = -202.1969135
all_checks_pass = true
```

这组证据同时支持两个判断：

1. 有大量 high-impact returned candidates；
2. 同一 exact replay 数据中仍存在 noop candidates。

所以不能说“负列都没用”，也不能说“true-RC negative 都值得加”。

## Selector gate 结论修正

加入 target002 pt0.3 行后，exact replay selector gate 数据变成：

```text
row_count = 280
label_counts = {improved: 209, noop: 71}
```

单特征 gate：

```text
passing_features_all_holdouts =
  true_reduced_cost
  cost
  new_task_set
  strict_replacement_by_cost
```

pair selector：

```text
no_pair_rule_passes_all_holdout_gates = true
```

simple model selector：

```text
context / instance / dataset holdout 中出现 passing candidates
```

需要注意：这些 selector 脚本的 `all_checks_pass=false` 在这里不是计算失败，而是脚本旧的成功条件仍然是“没有 selector 通过”。新数据推翻了旧否定预期。

## 对根因判断的影响

旧表述：

```text
has_stable_addition_before_selector = false
```

应替换为：

```text
has_replay_calibrated_selector_candidate = true
has_production_validated_selector = false
```

这不是目标完成，因为生产方向仍缺两类证据：

1. full BPC 5/10 no-regression A/B；
2. selected 20 hard repeats 的 wall-time / gap / status / final-judge tail 改善。

## 当前下一步

下一步不应继续堆 Pulse 搜索机制，也不应打开 official certificate gate。

更合理的下一步是：

1. 基于 280-row exact replay 数据定义严格 addition-before selector candidate；
2. 只使用 addition-before features；
3. 做 full BPC A/B；
4. 验证 5/10 不退化；
5. 验证 selected 20 hard repeats 是否真正减少 tail 或 wall time。

在这组 A/B 通过前，当前目标仍未完成。

