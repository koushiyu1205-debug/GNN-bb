# BPC_future 根因审计补充：counterfactual replay coverage

日期：2026-06-13

## 目标

本轮继续只读分析，不运行 solver，不修改 pricing / RMP / Pulse 主线。

上一轮 exact-context label conflict 已经证明：现有 run-level improved/worsened 不是 returned batch 的因果标签。本轮进一步回答一个更实用的问题：

> 现有日志里是否至少有一些同 exact RMP/active context 下的 pure improved-vs-pure worsened returned descriptor 对，可以作为下一步 controlled replay 的候选？

如果有，只能说明“有 replay 候选”；不能说明 selector 已经可上线。

## 输入与脚本

输入：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/stage_rows.csv
```

脚本：

```text
BPC_future/scripts/analyze_counterfactual_replay_coverage.py
```

复跑：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_counterfactual_replay_coverage.py \
--output-dir BPC_future/results/root_cause_counterfactual_replay_coverage_20260613
```

输出：

```text
BPC_future/results/root_cause_counterfactual_replay_coverage_20260613/summary.json
```

## 样本

20-task strict stage rows：

```text
rows = 288
improved = 136
worsened = 152
```

exact context key：

```text
instance
cg_iter
pricing_kind
active_hash_before
rmp_objective_before
```

returned descriptor key：

```text
best_rc
selected_count
materialized_count
returned_count
returned_union_size
returned_task_sets
returned_sequences
returned_arc_families
```

## Coverage 结果

在 mixed exact contexts 中：

```text
mixed_context_count = 12
mixed_context_rows = 120
```

returned descriptor group 分类：

```text
pure_improved = 12
pure_worsened = 21
mixed = 14
```

可形成的 pure improved-vs-pure worsened descriptor pair：

```text
pure_descriptor_pair_count = 40
replay_candidate_context_count = 6
```

同时：

```text
mixed_descriptor_context_count = 10
```

也就是说，12 个 mixed exact contexts 中有 10 个仍存在同 descriptor 混合标签。

## 解释

这轮结论是双重的。

第一，现有日志确实能提供少量 replay 候选：

```text
has_replay_candidates = true
```

这些候选可以用于下一步构造 controlled replay：

- 同 exact RMP/active context；
- 一个 pure improved descriptor；
- 一个 pure worsened descriptor；
- 对比它们的 returned task-set、sequence、arc family、start/timing composition；
- 在 no certificate effect 的 replay harness 中测试是否真的因果改变后续 trajectory。

第二，这些候选仍然稀疏且被混合标签污染包围：

```text
replay_candidates_are_sparse = true
mixed_descriptors_remain_common = true
existing_observational_replay_is_candidate_only = true
```

因此不能把这些 observational pairs 直接当成 production selector 训练集。

## 对根因判断的影响

当前根因进一步明确为：

> 20-task hard-tail 的问题不是缺少负列，而是缺少 batch-level causal evidence。现有日志有少量 replay 候选，但 run-level 标签仍有大量混杂；下一步必须做 controlled replay 才能把“候选信号”转成“可上线优化方向”。

这也解释为什么前面工作做了很多仍不能上线：

- Pulse worker 能加负列，但加列是否改变 trajectory 不稳定；
- returned count / best RC / batch overlap 有弱信号，但不是因果；
- context-only 与 pairwise ranking 都不够；
- supervised selector 不能直接依赖 run-level label。

## 下一步边界

如果继续推进优化方向，应做一个极窄、只读或 opt-in 的 replay harness：

1. 从本报告的 pure descriptor pairs 中选 2-3 个 exact contexts；
2. 固定同一 RMP/dual/active context；
3. 分别注入 pure improved descriptor batch 与 pure worsened descriptor batch；
4. 只观测 next RMP objective delta、dual movement、active basis change、incumbent update、next pricing state；
5. 不更新 official lower bound；
6. 不开启 production path；
7. 保持 5/10 no-op guard。

只有 replay 证明某类 batch descriptor 在同 context 下稳定改善 trajectory，才可能进入下一步 opt-in A/B。

## 当前目标状态

目标仍未完成。

理由：

- 已经有根因解释：5/10 是固定开销敏感，20 是 returned-batch trajectory / causal labeling 缺失；
- 已找到少量 counterfactual replay 候选；
- 但 replay 还未执行，不能证明任何 selector 或求解器修改能 exact-safe、5/10 不退化、20 大幅加速。
