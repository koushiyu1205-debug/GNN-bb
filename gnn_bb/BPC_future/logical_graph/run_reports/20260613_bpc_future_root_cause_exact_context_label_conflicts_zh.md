# BPC_future 根因审计补充：exact-context label conflicts

日期：2026-06-13

## 目标

本轮继续只读分析，不运行 solver，不修改 pricing / RMP / Pulse 主线。

前几轮已经说明：

- addition-before aggregate features 不稳定；
- matched `instance + profile` 内仍无稳定 selector；
- matched-context pairwise ranking 也没有 production 级特征。

本轮进一步检查更强的问题：

> 在同一个 RMP/active context，甚至同一个 returned batch descriptor 下，现有 run-level improved/worsened 标签是否仍会冲突？

如果冲突存在，说明当前观测日志里的 improved/worsened 不是 returned batch 的因果标签，不能直接训练 production selector。

## 输入与脚本

输入：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/stage_rows.csv
```

脚本：

```text
BPC_future/scripts/analyze_exact_context_label_conflicts.py
```

复跑：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_exact_context_label_conflicts.py \
--output-dir BPC_future/results/root_cause_exact_context_label_conflicts_20260613
```

输出：

```text
BPC_future/results/root_cause_exact_context_label_conflicts_20260613/summary.json
```

## 样本

20-task strict stage rows：

```text
rows = 288
improved = 136
worsened = 152
```

## Exact Context 冲突

exact context key：

```text
instance
cg_iter
pricing_kind
active_hash_before
rmp_objective_before
```

结果：

```text
group_count = 102
conflict_group_count = 12
conflict_rows = 120
conflict_row_share = 0.4166666666666667
```

也就是说，约 `41.7%` 的 strict rows 位于 exact RMP/active context 下仍同时出现 improved 与 worsened 标签的组中。

最大冲突组：

```text
instance = mt20_greedy_apollo_01
cg_iter = 1
pricing_kind = heuristic
active_hash_before = c6ea96127d7c5d7b
rmp_objective_before = 1061.554044
rows = 25
labels = {improved: 8, worsened: 17}
```

这说明仅仅匹配 RMP active basis 和 objective 仍不能把 run-level outcome 变成 batch-level 因果标签。

## Exact Context + Returned Full Features 冲突

更严格的 key：

```text
instance
cg_iter
pricing_kind
active_hash_before
rmp_objective_before
best_rc
selected_count
materialized_count
returned_count
returned_union_size
returned_task_sets
returned_sequences
returned_arc_families
```

结果：

```text
group_count = 153
conflict_group_count = 14
conflict_rows = 65
conflict_row_share = 0.22569444444444445
```

也就是说，即使把 returned batch 的 task-set、sequence、arc family 和主要 pre-batch count / RC 特征都纳入 key，仍有 `65` 行冲突。

最大 full-feature 冲突组：

```text
instance = mt20_greedy_apollo_01
cg_iter = 1
pricing_kind = heuristic
active_hash_before = c6ea96127d7c5d7b
rmp_objective_before = 1061.554044
best_rc = -139.913748
selected_count = 4
materialized_count = 1
returned_count = 1
returned_union_size = 3
returned_task_sets = 5,8,15
returned_sequences = 8,15,5
returned_arc_families = low_time,low_risk,low_risk,low_risk
rows = 15
labels = {improved: 4, worsened: 11}
```

这是一条很强的负证据：对这些字段可见的 deterministic selector 来说，上述 rows 是同一个输入，却有两种 run-level 标签。

## 例子

同一 full-feature key 下可以看到：

```text
dataset = sharded_pulse_phase10d_profile_dp_mask_hotspot_repeat_smoke_20260613
profile = experimental_profile_dp_mask_label_cap_16_20_only
returned_task_sets = 5,8,15
returned_sequences = 8,15,5
returned_arc_families = low_time,low_risk,low_risk,low_risk
run_improvement_class = improved
```

同组中也有：

```text
dataset = sharded_pulse_phase10d_profile_dp_mask_hotspot_repeat_smoke_20260613
profile = experimental_profile_dp_mask_label_cap_16_20_only
returned_task_sets = 5,8,15
returned_sequences = 8,15,5
returned_arc_families = low_time,low_risk,low_risk,low_risk
run_improvement_class = worsened
```

这表明同一个 returned batch descriptor 在不同 repeat / downstream trajectory 中可能对应不同最终 run label。

## 对根因判断的影响

这轮把根因进一步收紧为：

> 当前观测日志中的 run-level improved/worsened 标签不是 returned batch 的因果标签。即使 exact context 和 returned batch descriptor 相同，标签仍会冲突。因此仅靠现有 stage/candidate rows 训练 production selector 会把下游 trajectory 噪声和重复实验差异误学成 batch 质量。

这解释了为什么前面很多方法都“看起来有信号但不能上线”：

- aggregate feature 有弱相关；
- context identity 有信号；
- hindsight trajectory 有更强信号；
- 但 addition-before selector 一到 leave-one-dataset / matched context / pairwise contrast 就不稳；
- 因为监督标签本身不是 batch-level causal label。

## 当前不能得出的结论

不能说：

- 某个 pre-batch feature 就是根因；
- 同一个 returned batch descriptor 一定好或一定坏；
- 用当前 run-level label 训练一个更复杂模型就能上线；
- context 分层后就可以安全学习 selector。

只能说：

- 现有观测日志足以支持根因解释；
- 但不足以证明 production 优化方向；
- 下一步若继续，必须构造同一 pricing/RMP context 下的 counterfactual/replay：
  - 同一 candidate pool 的 returned batch 子集 A/B；
  - 同一 returned candidates 的排序 A/B；
  - 同一 signature/start-time composition 的 controlled replay；
  - 每个 replay 都必须 no certificate effect，并保留 5/10 no-op guard。

## 当前目标状态

目标仍未完成。

理由：

- 根因已经更明确：5/10 是固定开销敏感，20 是 returned-batch trajectory selector / causal labeling 缺失；
- 但还没有证明一个 exact-safe、5/10 不退化、20 大幅加速的优化方案；
- 不能把当前 selector、worker、profile-DP cap、return count、pairwise ranker 或 context gate 放进生产路径。
