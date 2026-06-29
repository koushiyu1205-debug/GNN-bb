# V556/V557：两类 retry 与 on/off/gate 对比（seed61717）

## 两类 retry

本轮必须区分两类 retry。

1. 普通 no-column 补救 retry

- 典型日志：`journey_exact_pricing_retry`
- 典型 pricing_kind：`exact_retry`
- 作用：在 worker / ordinary exact pricing 不完整或 no-column 后，再用真实对偶 pricing 找负列。
- 精确性边界：它找到的列仍要真实 reduced cost 验证；它的 no-column 结果不能直接当全局 certificate。

2. completion-bound / final-judge retry

- 典型日志：`journey_exact_pricing_completion_bound_retry`
- 典型 pricing_kind：`exact_completion_bound_retry`
- 作用：用 completion-bound / direct-label final judge 尝试证明 no-negative certificate，或者发现隐藏负列。
- 精确性边界：只有它真正返回 certified no-negative 时，才可作为闭合证据；跳过它必须 fail-closed，不能剪枝。

V556 新增的 retry gate 只作用于第二类，不作用于普通 no-column 补救 retry。

## 实验设置

实例：

`tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json`

三组都使用 V545 branch score 配置，普通 no-column retry 保持开启。

| 组别 | final-judge retry | gate | 说明 |
|---|---:|---:|---|
| V555 retry on | 开 | 关 | 原始 V545 行为，加 profile timing |
| V556 retry gate | 开 | 开 | 前 2 次昂贵 zero-harvest 后，后续 final-judge retry gate 为 branch |
| V557b retry off | 关 | 关 | 实验性关闭 final judge；需同时关闭 `journey_completion_bound_required`，不是生产配置 |

## 结果

| 组别 | status | wall time | gap | ordinary retry | final-judge retry | final-judge profile s | gate events | branch nodes | fathom |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V555 retry on | EXTERNAL_TIME_LIMIT | 600.039 | 0.039594 | 0 | 8 | 295.850 | 0 | 6 | 0 |
| V556 retry gate | EXTERNAL_TIME_LIMIT | 600.033 | 0.039594 | 1 | 2 | 71.127 | 24 | 22 | 0 |
| V557b retry off | TIME_LIMIT | 59.059 | n/a | 1 | 0 | 0.000 | 0 | 0 | 0 |

V556 gate 的第一条 gate 日志：

- `reason = expensive_zero_harvest_limit`
- `action = branch`
- `retry_gate_total_count = 2`
- `retry_gate_total_profile_generation_time = 71.127107`
- `exact_bound_available = False`
- `child_lower_bound_exact = False`

这说明 gate 没有把 RMP objective 当 exact bound，也没有把 child lower bound 标成 exact。

## 判断

retry gate 能优化 final-judge retry 的局部耗时，但当前 V556 没有优化完整求解。

V556 把 final-judge retry profile time 从 `295.850s` 降到 `71.127s`，但 branch nodes 从 `6` 增到 `22`，fathom 仍为 `0`，最终仍是 `EXTERNAL_TIME_LIMIT`。这说明省下的证明时间被更宽的 branch tree 吃掉了。

V557b 更直接说明 final judge 不能简单关闭。关闭后 solver 约 `59s` 就内部 `TIME_LIMIT`，因为失去了 required completion-bound certificate 路径。它不是一个可接受的生产优化，只能作为 off 对照。

## 意料之外的地方

最大意外是 gate 的全局统计过于强。一旦 root 和一个 child 出现两次昂贵 zero-harvest，后续很多不同 child 都被 blanket gate 掉，导致大量 early branch。这个行为虽然 exact-safe，但太粗，容易把 proof cost 转成 branch-tree cost。

第二个意外是普通 no-column retry 在这个实例里不是瓶颈。V555 中 ordinary retry 为 `0`，V556/V557b 也只有 `1` 次且很短。当前主要问题确实是 final-judge proof tail，不是普通补救 retry。

## 下一步优化方向

1. retry gate 不能用全局 blanket 统计。

应改成按 context 分桶，例如：

- depth
- branch state key
- task-set / active-support signature
- final-probe trigger
- completion-bound profile shape

只有同类 context 连续 expensive zero-harvest，才 gate 该类 context。

2. `gate_action=branch` 不能裸用。

应增加 branch 前置条件：

- branch score 命中当前 context
- top score 过阈值
- child width / balance 不超限
- open node 数不高
- depth 不超过限制

否则 gate 后应 fail-closed 为 `PRICING_INCOMPLETE` 或降预算 final judge，而不是继续扩树。

3. 优先做 retry budget cap，而不是 retry hard skip。

当前 seed61717 的热点是 `direct_label_profile_next_sortie_total_time`。更合理的策略是：

- 第一次 full final-judge retry 保留
- 后续同类 context 只给小预算 probe
- 小预算无收获则 fail-closed
- 只有 strong branch-score context 才转 branch

4. GAT branch score 的训练标签要加入 proof-tail 后果。

当前 branch score 能改变分支，但还没学到“这个分支是否减少 final-judge proof cost / child certificate time”。后续标签应加入：

- child final-judge retry count
- child final-judge profile time
- gate 后 open-node growth
- child time-to-certificate
- child fathom probability

## 结论

不能简单 retry off。

当前证据支持：

- final-judge retry 是大成本来源；
- retry gate 能减少这部分成本；
- 但粗粒度 gate + branch fallback 会把成本转移到 branch tree；
- 下一步应做 context-aware retry gate + score-gated branch fallback，而不是全局关闭 retry。
