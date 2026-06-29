# 20260628 retry gate smoke4 与 completion-bound cache 诊断总结

## 结论

这次需要明确分成两类 retry：

1. **不完整 no-column 后的普通补救 retry**
   - 事件：`journey_exact_pricing_retry`
   - 开关：`journey_retry_incomplete_no_column_enabled`
   - 作用：当 cheap/exact pricing 给出“不完整、没找到列”时，补一次更强的 exact retry，避免把不完整 no-column 当成证书。

2. **completion-bound / final-judge retry**
   - 事件：`journey_exact_pricing_completion_bound_retry`
   - 开关：`journey_certificate_completion_bound_after_retry_enabled`
   - gate/cap：`journey_certificate_completion_bound_retry_gate_*`、`journey_certificate_completion_bound_retry_budget_cap_*`
   - 作用：进入 true-dual direct-label final judge，拿 `CERTIFIED_NO_NEGATIVE` 或真实负列。只有这条路径能支撑 official bound / gap / certificate。

当前 smoke4 的结果说明：**retry gate 不是当前 20 规模 proof tail 的主优化方向**。关掉 completion-bound/final-judge retry 会明显变快，但全部失去 exact gap/证书，不是有效加速；打开 gate 与 retry on 基本等价；adaptive cap 只减少了极少量调用，收益可以忽略。

## 代码状态

相关代码位置：

- 普通 no-column retry：`BPC_future/solver/journey_driver.py:1685`、`1783`、`6608`、`6773`
- completion-bound/final-judge retry：`BPC_future/solver/journey_driver.py:1711`、`2362`、`6389`、`6888`、`7479`、`7779`、`8792`
- retry gate / budget cap：`BPC_future/solver/journey_driver.py:15568` 到 `15992`
- certificate-mode next-sortie cache 配置透传：`BPC_future/solver/journey_driver.py:18213`
- gate 单元测试：`BPC_future/tests/test_bpc_future.py:15877` 到 `16136`

已经验证过的 gate 单元测试：

```text
python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_is_opt_in_and_requires_history \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_blocks_expensive_zero_harvest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_keeps_harvest_signal \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_context_scope_isolates_depth_trigger \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_budget_cap_is_opt_in_and_contextual \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_budget_cap_keeps_unseen_context_uncapped
```

结果：`Ran 6 tests ... OK`。

## 实验设置

结果根目录：

```text
BPC_future/results/20260628_retry_on_off_gate_smoke4_randomtw20/
```

固定 4 个 20-scale random-TW 实例：

- seed61205：apollo15 / greedy-anchor / tasks020_03
- seed61311：tranquillitatis / greedy-anchor / tasks020_04
- seed61717：tranquillitatis / random-wave / tasks020_08
- seed61410：tranquillitatis / sector-wave / tasks020_05

共同设置：

- 600s 外部时限
- `max-workers=4`
- V545-like branch score on
- early branch off
- admission off
- 普通 no-column retry 保持 on，除非特殊说明

对比组：

- `retry_on`：completion-bound/final-judge retry on
- `retry_off`：completion-bound/final-judge retry off，completion bound required off
- `retry_gate`：completion-bound/final-judge retry on + corrected gate
- `retry_gate_adaptive_cap`：gate + adaptive budget cap
- 额外 smoke2：`retry_on_cb_nextsortie_cache_smoke2`，只跑 seed61311/seed61410，打开 `journey_certificate_completion_bound_next_sortie_cache_enabled=True`

## 求解结果

| instance | retry on | retry off | retry gate | gate + cap |
|---|---:|---:|---:|---:|
| seed61205 | TIME_LIMIT 335.3s, gap n/a | TIME_LIMIT 267.7s, gap n/a | TIME_LIMIT 335.5s, gap n/a | TIME_LIMIT 335.0s, gap n/a |
| seed61311 | EXTERNAL_TIME_LIMIT 600.0s, gap 0.041522 | TIME_LIMIT 22.0s, gap n/a | EXTERNAL_TIME_LIMIT 600.0s, gap 0.041522 | EXTERNAL_TIME_LIMIT 600.0s, gap 0.041522 |
| seed61717 | EXTERNAL_TIME_LIMIT 600.0s, gap 0.036955 | TIME_LIMIT 58.7s, gap n/a | EXTERNAL_TIME_LIMIT 600.0s, gap 0.036955 | EXTERNAL_TIME_LIMIT 600.0s, gap 0.036955 |
| seed61410 | EXTERNAL_TIME_LIMIT 600.0s, gap 0.034203 | TIME_LIMIT 9.1s, gap n/a | EXTERNAL_TIME_LIMIT 600.0s, gap 0.034203 | EXTERNAL_TIME_LIMIT 600.0s, gap 0.034203 |

聚合：

| group | rows | status | mean wall | gap available |
|---|---:|---|---:|---:|
| retry_on | 4 | 1 TIME_LIMIT, 3 EXTERNAL_TIME_LIMIT | 533.845s | 3/4 |
| retry_off | 4 | 4 TIME_LIMIT | 89.389s | 0/4 |
| retry_gate | 4 | 1 TIME_LIMIT, 3 EXTERNAL_TIME_LIMIT | 533.900s | 3/4 |
| retry_gate_adaptive_cap | 4 | 1 TIME_LIMIT, 3 EXTERNAL_TIME_LIMIT | 533.761s | 3/4 |

解释：

- `retry_off` 看起来快，但不是优化。它没有 final-judge certificate，所有实例 `gap_available=false`，原因都是 `no_exact_dual_bound`。
- `retry_gate` 与 `retry_on` 几乎完全一致，说明 corrected gate 没有触发有效阻断。
- `gate+cap` 只减少约 0.08s capped mean，不构成有效优化。

## 事件与 tail profile

| group | ordinary retry | completion-bound retry | branch | branch rows usable | child CB retries | total profile generation time |
|---|---:|---:|---:|---:|---:|---:|
| retry_on | 2 | 93 | 86 | 0 | 269 | 979.810s |
| retry_off | 2 | 0 | 0 | 0 | 0 | 0.000s |
| retry_gate | 2 | 93 | 86 | 0 | 269 | 982.276s |
| gate+cap | 2 | 92 | 85 | 0 | 266 | 972.759s |

completion retry 分类：

| group | completion retry class |
|---|---|
| retry_on | 3 certified no-negative, 1 time-limit no-column uncertified |
| retry_gate | 3 certified no-negative, 1 time-limit no-column uncertified |
| gate+cap | 3 certified no-negative, 1 time-limit no-column uncertified |
| retry_off | no completion-bound retry |

这说明当前昂贵部分不是“大量不完整 zero-harvest retry”，而是大量 `CERTIFIED_NO_NEGATIVE` 的 true-dual final-judge 证明。corrected gate 只针对“昂贵、不完整、零 harvest”的无效 retry，所以它不触发是正确的。

## cache-on smoke2

额外试了两个主要耗时实例：

```text
journey_certificate_completion_bound_next_sortie_cache_enabled=True
```

结果：

| instance | status | wall | gap |
|---|---:|---:|---:|
| seed61311 | EXTERNAL_TIME_LIMIT | 600.050s | 0.041522 |
| seed61410 | EXTERNAL_TIME_LIMIT | 600.017s | 0.034203 |

profile 对比：

| instance | retry_on profile | gate+cap profile | cache-on profile | cache hits/misses |
|---|---:|---:|---:|---:|
| seed61311 | 270.982s | 262.971s | 262.884s | 0 / 0 |
| seed61410 | 316.193s | 316.488s | 317.349s | 0 / 0 |

cache-on 日志里 `direct_journey_label_next_sortie_cache_enabled=true`，但 `direct_next_sortie_cache_hits=0`、`direct_next_sortie_cache_misses=0`。也就是说当前 completion-bound certificate 路径没有从这个 cache 获益；这个开关本身不是已经验证的优化。

## 是否能靠 retry gate 优化

短结论：**不能作为主线优化**。

它能优化的情况：

- final-judge retry 已经多次证明是昂贵；
- 这些 retry 主要是不完整 no-column；
- 没有选出新 task-set / 没有 harvest / 没有真实负列；
- gate 阻断后仍然 exact-safe 地返回 incomplete 或 early branch，不把 RMP objective 当 exact bound。

本批实际情况：

- 主要耗时来自 certified no-negative proof，而不是 incomplete no-column。
- certified no-negative 是官方证明链的一部分，不能简单跳过。
- retry_off 低耗时来自不证明，所以没有 gap，不是可接受结果。
- gate+cap 只减少 1 次 branch、1 次 completion-bound retry 和约 7s profile generation time，对 600s 总体没有实质影响。

所以 retry gate 应保留为安全阀和诊断工具，不应继续当主加速线。

## 当前真正的问题

当前 20 规模没有卡在“找不到正例”这一层，也不是单纯 GAT admission 找列不够。现在卡住的是：

1. 分支树里产生太多需要 final-judge 证明的节点；
2. 很多节点最终可以 certified no-negative，但每次证明都很贵；
3. branch score 仍然会进入大量 completion-bound-tail / right-censored 子树；
4. 现有 child/branch 标签仍缺少完整闭环观测，branch rows `usable_for_branch_impact_training=0`；
5. 单纯减少 retry 不能减少真实 proof burden。

换句话说：当前失败不是“retry 策略没关好”，而是“分支策略和 proof-tail 成本结构没有被真正压下来”。

## 意料之外的地方

1. corrected retry gate 没有触发，反而是好信号：说明 gate 没有误杀 certified proof。
2. `retry_off` 的 wall time 很低，但 gap 全无；这再次说明不能用 wall time 单独判断优化。
3. 大量耗时来自 certified no-negative，不是 incomplete zero-harvest，这比最初预期更难优化。
4. `journey_certificate_completion_bound_next_sortie_cache_enabled=True` 在日志里生效，但 hit/miss 仍为 0，说明当前 hot path 没吃到这个 cache。
5. branch score 选中的节点仍形成 269 次 child completion-bound retry，说明模型当前还没有学会“避免昂贵证明尾巴”。

## 下一步优化方向

### 1. 保持两类 retry 的正确边界

- 普通 no-column retry：继续开，防止 incomplete no-column 被误当证书。
- completion-bound/final-judge retry：继续开，这是 exact gap 和 certificate 的必要路径。
- retry gate：保留，但只作为安全阀，不作为默认主加速器。
- budget cap：仅用于极端无效 tail，不能让 certified proof 被系统性截断。

### 2. 主攻减少 certified final-judge 调用次数

branch score 的训练目标要继续从“哪个 pair 有局部 bound gain”转向：

- 哪个 pair 会减少 `child_completion_bound_retries`
- 哪个 pair 会减少 `child_certificate_pricing_events`
- 哪个 pair 会降低 `time_to_certificate`
- 哪个 pair 会避免 right-censored completion-bound-tail
- 哪个 pair 会让两个 child 更快 closed，而不是只让一个 child 局部变好

当前 branch impact audit 已经能导出这些风险字段，但本批仍是 right-censored，不能当完整正例；要继续用 controlled replay / fixed-depth child probe 收集更完整的反事实标签。

### 3. 降低单次 certificate 证明成本

优先做窄探针，不要大改：

- 查清为什么 certificate next-sortie cache hits/misses 仍为 0；
- 对比 `generated_next_sorties_before_bound`、`two_cycle_build_time`、`bound_build_time` 在重复节点之间是否可复用；
- 研究 unique-route / two-cycle / completion-bound table 的跨 sibling 复用；
- 只做 exact-safe cache，任何 partial table 超时或 incomplete 都不能缓存成证书依据。

### 4. 调整 branch policy 的惩罚项

在 score map 叠加层增加 proof-tail penalty：

- 惩罚历史上导致大量 `completion_bound_tail` 的 pair/context；
- 惩罚 `pool_total_child_width` 大、`pool_balance_gap` 大、child CB retry 高的候选；
- 奖励 child proof CPU 低、certificate event 少、早期 negative chain 能快速收口的候选；
- 对 right-censored 样本只作为风险负信号，不当作完整 wall-time 标签。

### 5. 对 gap 做持续记录

所有非 OPTIMAL 实例继续记录：

- `gap_available`
- `gap_source`
- `best_primal_bound`
- `best_dual_bound`
- `gap`
- `gap_unavailable_reason`

`retry_off` 这类低 wall time 但 `gap_available=false` 的结果必须单独标记为“无证书早停”，不能和有效求解结果混在一起比较。

## 建议的下一轮实验

不要继续扩大 retry gate 网格；改成两个窄实验：

1. **certificate cache / reuse probe**
   - 固定 seed61311、seed61410；
   - 打开详细 profile timing；
   - 查 next-sortie cache 为什么 0 hit/0 miss；
   - 对比是否能把 `profile_generation_time` 从 260-317s 降下来。

2. **proof-tail-aware branch score replay**
   - 固定这 4 个 smoke 实例和 full60 中 high retry 的实例；
   - 用 `child_completion_bound_retries`、`child_certificate_pricing_events`、`right_censored completion_bound_tail` 做风险标签；
   - 生成新的 score overlay，只改变 branch ordering；
   - 验证是否减少 completion-bound retry 总数，而不是只减少某个局部 retry。

验收口径：

- 不能只看 wall time；
- 必须看 OPTIMAL / gap_available / gap；
- 必须看 completion-bound retry count 和 certified proof CPU；
- 任何 `gap_available=false` 的快结果都不能算成功。
