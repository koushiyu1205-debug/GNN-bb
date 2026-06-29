# V726 RouteOpt/BKF Phased Controller 复现实验与下一步判断

日期：2026-06-28

## 目的

V725 在 V622 hard4 上得到 `2/4 TIMEOUT -> OPTIMAL` 的正信号，但当时 `phase0_min_fractionality=0.45` 在部分节点会把候选全部过滤，再 fail-closed 回退继续 phase1/phase2，旧日志把这些候选显示成 `filtered`，容易污染训练标签。

V726 的目的：

1. 用修补后的 phase0 fallback 日志重跑同一 hard4。
2. 验证 V725 的两条 strict positive 是否可复现。
3. 判断下一步是直接扩 full60，还是先处理 greedy-anchor 失败族。

## 日志修补验证

V726 日志新增并验证了以下字段：

- `phased_testing_phase0_fallback_count`
- `phased_testing_phase0_fallback_all_filtered`
- `phased_testing_phase0_fallback_reason`
- candidate 级别：
  - `phased_testing_phase0_fallback_enabled`
  - `phased_testing_phase0_fallback_reason`

`sector-wave seed61718` root 节点：

```text
p0 pass count = 0
fallback_count = 30
fallback_all = True
fallback_reason = all_candidates_filtered_fail_closed_to_priority_order
selected = [7,8]
selected decision = probed_complete
selected fallback_enabled = True
```

这说明现在日志能正确表达：

```text
phase0 全过滤
-> exact-safe fail-closed 回退
-> 继续 phase1/phase2 probe
-> 选择 [7,8]
```

不再把 selected candidate 误写成单纯 `filtered`。

## V622 / V725 / V726 对比

| instance | V622 status | V622 gap | V725 status | V725 wall | V725 gap | V726 status | V726 wall | V726 gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| greedy seed61311 | EXTERNAL_TIME_LIMIT | 0.051215 | EXTERNAL_TIME_LIMIT | 600.019958 | 0.041522 | EXTERNAL_TIME_LIMIT | 600.018471 | 0.041522 |
| greedy seed61635 | EXTERNAL_TIME_LIMIT | 0.061278 | EXTERNAL_TIME_LIMIT | 600.018201 | 0.060588 | EXTERNAL_TIME_LIMIT | 600.019286 | 0.060588 |
| sector seed61410 | EXTERNAL_TIME_LIMIT | 0.034203 | OPTIMAL | 278.161323 | 0.000000 | OPTIMAL | 274.617106 | 0.000000 |
| sector seed61718 | EXTERNAL_TIME_LIMIT | 0.043777 | OPTIMAL | 335.792500 | 0.000000 | OPTIMAL | 331.692639 | 0.000000 |

V726 复现结论：

- `sector seed61410`: 复现 `TIMEOUT -> OPTIMAL`，且 wall 从 V725 的 `278.16s` 到 V726 的 `274.62s`。
- `sector seed61718`: 复现 `TIMEOUT -> OPTIMAL`，且 wall 从 V725 的 `335.79s` 到 V726 的 `331.69s`。
- `greedy seed61311`: 复现 timeout，但 gap 从 V622 的 `0.051215` 改善到 `0.041522`。
- `greedy seed61635`: 复现 timeout，但 gap 从 V622 的 `0.061278` 改善到 `0.060588`。

## V726 root phased-testing 摘要

| instance | root baseline | root selected | phase0 pass | phase0 fallback | phase1 probes | phase2 probes | branch | CB retry | fathom | result |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| greedy seed61311 | `[1,10]` | `[2,16]` | 41 | 0 | 10 | 4 | 24 | 38 | 6 | timeout |
| greedy seed61635 | `[1,3]` | `[12,20]` | 29 | 0 | 11 | 3 | 34 | 39 | 3 | timeout |
| sector seed61410 | `[3,6]` | `[4,7]` | 18 | 0 | 10 | 4 | 7 | 15 | 8 | OPTIMAL |
| sector seed61718 | `[3,5]` | `[7,8]` | 0 | 30 | 11 | 3 | 17 | 35 | 18 | OPTIMAL |

## 可以进入训练的数据

### Strict positive

这两条可以作为严格 full-solve positive：

1. `sector-wave tasks020_05_seed61410`
   - baseline root pair: `[3,6]`
   - selected root pair: `[4,7]`
   - V622: `EXTERNAL_TIME_LIMIT`
   - V726: `OPTIMAL 274.62s`
   - label: `timeout_to_optimal_strict_positive`

2. `sector-wave tasks020_08_seed61718`
   - baseline root pair: `[3,5]`
   - selected root pair: `[7,8]`
   - V622: `EXTERNAL_TIME_LIMIT`
   - V726: `OPTIMAL 331.69s`
   - label: `timeout_to_optimal_strict_positive`
   - note: root phase0 全过滤后 fail-closed fallback，训练时必须携带 `phase0_fallback_all_filtered=True`

### Weak positive / failure-analysis rows

这两条不能作为 strict full-solve positive，但应该进入多目标 ranking 的 weak rows：

1. `greedy-anchor tasks020_04_seed61311`
   - root pair: `[2,16]`
   - gap: `0.051215 -> 0.041522`
   - incumbent/primal: `576.723133 -> 570.891016`
   - dual 不变：`547.186422`
   - label: `gap_incumbent_weak_positive`

2. `greedy-anchor tasks020_07_seed61635`
   - root pair: `[12,20]`
   - gap: `0.061278 -> 0.060588`
   - incumbent/primal: `561.030445 -> 560.618366`
   - dual 不变：`526.651393`
   - label: `gap_incumbent_weak_positive`

## 当前判断

V726 说明 V725 不是偶然：

- 两条 strict positive 可复现；
- fallback 日志修补有效；
- sector-wave 对 RouteOpt/BKF phased branch controller 明显敏感；
- greedy-anchor 仍是主要瓶颈。

所以不建议现在直接把 V726 扩到 full60 后就当完成主线。更合理的顺序是：

1. 把 V725/V726 strict positive 和 weak rows 转进 branch action 数据集。
2. 针对 greedy-anchor 做深层 branch replay：
   - root 已经改善 gap，但没改善 dual；
   - 下一步应沿 selected root 后的 depth-1/depth-2 hard path 做 paired replay；
   - 标签重点看 `child proof CPU`、`CB retry`、`fathom_gain`、`gap_improvement`。
3. 同时启动 route-aware / pricing-compatible cuts 设计，因为 greedy-anchor 的 dual 完全不动。
4. 只有在 greedy-anchor 至少出现一条 `TIMEOUT -> OPTIMAL` 或明显 dual 改善后，再扩 random-TW 20 full60。

## 下一步具体任务

### A. 数据集更新

导出 V725/V726 branch rows：

- strict positives:
  - `[3,6] -> [4,7]`
  - `[3,5] -> [7,8]`
- weak positives:
  - `[1,10] -> [2,16]`
  - `[1,3] -> [12,20]`

字段必须包含：

- `instance_family`
- `branch_state_key`
- `depth`
- `selected_pair`
- `baseline_pair`
- `phase0_fallback_all_filtered`
- `phase1_min_child_lp_gain`
- `phase1_child_lp_gain_product`
- `phase2_negative_child_count`
- `phase2_negative_journey_count`
- `branch_count_delta`
- `completion_bound_retry_delta`
- `fathom_gain`
- `gap_improvement`
- `wall_time_gain`
- `label_type`

### B. Greedy-anchor 专项

对 seed61311/seed61635：

- 固定 V726 root pair；
- 沿实际 search path 抽 depth-1/depth-2 branch events；
- 每个 event 做 limited paired replay；
- 不追 top200，仍按 RouteOpt/BKF phased testing 取动态 K。

目标是找到：

- 能抬 child corrected LB 的 pair；
- 能减少 CB retry 的 pair；
- 能增加 fathom 的 pair；
- 或证明当前瓶颈主要是 formulation/cuts。

### C. Cuts/formulation

greedy-anchor 的 dual 不动是关键证据：

```text
seed61311 dual = 547.186422
seed61635 dual = 526.651393
```

这类节点即使 branch 改善 incumbent/gap，也没有明显提高证明下界。因此需要并行推进：

- pricing-compatible subset-row / route-aware cuts；
- 更强 master formulation；
- incumbent heuristic；
- branch-pair 与 cuts 的交互诊断。

## 验收边界

V726 不能视为最终验收：

- random-TW 20 full60 尚未全量验证；
- hard4 仍有 `2/4` timeout；
- 目标“所有 20 规模 600 秒内 OPTIMAL”仍未达到。

但 V726 可以视为 Branch Score 主线的一个实质进展：

- solver 内 phased branch testing 可复现地产生 strict positive；
- 日志足以进入 state-scoped branch action 训练；
- 下一步问题已经从“有没有正例”转为“如何覆盖 greedy-anchor 这类 dual 不动的 hard family”。
