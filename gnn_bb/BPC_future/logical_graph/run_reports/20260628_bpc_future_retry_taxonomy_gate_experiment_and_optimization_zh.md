# 20260628：两类 Retry、Gate 对照与下一步优化判断

## 结论

当前必须把 retry 分成两类看。

第一类是普通不完整 no-column 后的补救 retry：

- 典型事件：`journey_exact_pricing_retry`
- 典型 `pricing_kind`：`exact_retry`
- 主要开关：`journey_retry_incomplete_no_column_enabled`
- 作用：ordinary exact pricing 返回不完整 / no-column 后，再尝试用真实 reduced cost 找负列。
- 精确性边界：它找到的列仍要真实 reduced cost 验证；它自己的 no-column 结果不能直接升级成全局 certificate。

第二类是 completion-bound / final-judge retry：

- 典型事件：`journey_exact_pricing_completion_bound_retry`
- 典型 `pricing_kind`：`exact_completion_bound_retry`
- 主要 gate/cap 开关：`journey_certificate_completion_bound_retry_gate_enabled`、`journey_certificate_completion_bound_retry_budget_cap_enabled`
- 作用：用 direct-label / completion-bound final judge 证明没有遗漏负列，或者发现 hidden negative。
- 精确性边界：只有返回真实 `CERTIFIED_NO_NEGATIVE` 时才是闭合证据；被 gate/cap 后没有完成时必须 fail-closed，不能剪枝。

现在瓶颈主要是第二类，不是第一类。

## 当前代码状态

已完成：

- `journey_driver.py` 中 completion-bound retry gate 只统计 `exact_completion_bound_retry` / `exact_completion_bound_escalation_retry`，不统计普通 `exact_retry`。
- gate stats 已区分：
  - `certified_zero_harvest_count`
  - `expensive_certified_zero_harvest_count`
  - `incomplete_zero_harvest_count`
  - `expensive_incomplete_zero_harvest_count`
  - `certified_zero_harvest_profile_time_max`
- gate 默认只把 `expensive_incomplete_zero_harvest_count` 当作 block 依据，避免把昂贵但有用的 no-negative certificate 当坏样本。
- budget cap 是 opt-in，只缩短后续 final-judge retry 的 time limit，不提供 bound、不提供 certificate、不剪枝。
- gate/cap 日志输出上下文统计字段，便于后续做 retry on/off/gate 对比。

已验证：

```text
python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py BPC_future/scripts/build_gat_tree_policy_event_dataset.py

python -m unittest \
  BPC_future.tests.test_gat_tree_policy_event_dataset \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_budget_cap_is_opt_in_and_contextual \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_budget_cap_keeps_unseen_context_uncapped \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_is_opt_in_and_requires_history \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_blocks_expensive_zero_harvest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_keeps_harvest_signal \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_context_scope_isolates_depth_trigger \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_retry_budget_completion_reserve_is_opt_in_and_bounded \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_final_probe_verifies_profile_no_column_certificates
```

## 已有 Seed61717 对照

实例：

`tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json`

| 组别 | completion-bound retry 策略 | status | wall s | gap | 结论 |
|---|---|---:|---:|---:|---|
| V555 retry on | 全开 | `EXTERNAL_TIME_LIMIT` | 600.039 | 0.039594 | 证书路径完整，但 final-judge profile 很重 |
| V556 global gate | 两次昂贵 zero-harvest 后 gate 到 branch | `EXTERNAL_TIME_LIMIT` | 600.033 | 0.039594 | profile 降低，但 branch tree 变宽 |
| V557b retry off | 关闭 final judge，并关闭 required completion-bound | `TIME_LIMIT` | 59.059 | n/a | 不是优化，只是停止证明，gap 不可靠 |
| V558 context gate | depth/trigger 分桶 + score branch gate | `EXTERNAL_TIME_LIMIT` | 600.019 | 0.039594 | 安全但收益不足，深层 score 缺失 |
| V559 budget cap | 同 trigger 后续 retry cap 到 12s | `TIME_LIMIT` | 170.139 | 0.039594 | 大幅省 profile，但 child 证书 incomplete |
| V560 cert-aware cap 5s margin | cap 下限参考已认证 profile | `EXTERNAL_TIME_LIMIT` | 600.018 | 0.036955 | gap 改善一点，但仍未 OPTIMAL |
| V561 cert-aware cap 8s margin | cap 下限参考已认证 profile | `EXTERNAL_TIME_LIMIT` | 600.019 | 0.036955 | 与 V560 类似 |

## 能不能优化

能优化局部 proof-tail 成本，但目前还不能把它单独算作完整求解优化。

证据：

- V556/V559 都能减少 completion-bound final-judge profile 时间。
- V559 能把 seed61717 的 wall time 从约 `600s` 压到 `170s`。
- 但 V559 没有 OPTIMAL，两个 child final-judge retry 是 `INCOMPLETE/time_limit`，节点没有 certificate。
- V557b 的 `59s TIME_LIMIT` 更不能当加速，因为它失去 exact dual bound / gap。

所以 retry gate/cap 的真实作用是：识别和削减“明显可能无收益的昂贵证明尝试”。它不是 certificate 的替代品，也不是直接让节点 fathom 的手段。

## 当前问题

1. retry off 不可用

关闭 completion-bound / final-judge retry 后，worker no-column 不能成为 official certificate。求解器更快停下来，不代表更快求到最优。

2. global gate 太粗

V556 证明全局 gate 可以省 final-judge 时间，但会把 proof cost 转成 branch-tree cost，branch nodes 明显上升。

3. context gate 太保守

V558 避免了树爆炸，但 gate 触发少，final-judge profile 时间几乎回到 retry-on。深层 score source 缺失时，只能 fail-closed。

4. hard budget cap 太硬

V559 控制住 wall time，但会留下 incomplete child。它适合做诊断和训练标签，不适合直接上线。

5. 需要把 retry 后果接进 branch score 学习

V562 branch-impact 审计已经给出 19 个 right-censored branch rows，其中 14 个是 completion-bound tail 风险行。V564 数据集已把它们转成 `tree_policy_proof_tail_hard_negative`，用于让 GAT 学会避开会制造 proof-tail 的分支。

## 下一步实验设计

等 retry gate/cap 代码稳定后，做三组主对比，必要时加 cap 作为第四组：

1. `retry on`
   - completion-bound / final-judge retry 全开。
   - 用作 exact-safe 主基线。

2. `retry off`
   - 只作诊断，不作生产候选。
   - 报告必须单独列出 `gap_available=false` / `no_exact_dual_bound`。

3. `retry gate`
   - 开 context-aware gate。
   - gate 后如果 branch score 缺失或 child width/balance 不合格，必须 fail-closed，不裸 branch。

4. `retry gate + adaptive cap`
   - 推荐作为真正优化候选。
   - 第一次 full final judge 保留；后续同类 context 先 cap；如果 cap 后仍 incomplete，只有 score-gated branch 通过才 branch。

对比指标：

- `OPTIMAL` 数量
- capped mean wall time
- `<=200s OPTIMAL`
- 未最优实例 gap、gap source、gap available
- ordinary no-column retry count
- completion-bound retry count
- completion-bound retry profile time
- certified no-negative / found-negative / incomplete retry 分型
- branch nodes / open nodes
- gate action：`incomplete` 还是 `branch`
- score missing / score low / width blocked 的次数

## 优化方向

主线不应是“关 retry”，而是：

`branch score 主线 + completion-bound retry adaptive budget + score-gated branch fallback + proof-tail 标签`

具体做法：

1. 保留普通 no-column rescue retry，不把它和 final-judge retry 混在一起。
2. 对 completion-bound final-judge retry 做 context-aware stats，默认只用 expensive incomplete zero-harvest 触发硬 gate。
3. 对昂贵 certified no-negative 不直接 gate，而是用 `certified_zero_harvest_profile_time_max + margin` 作为 cap floor，避免把可认证节点 cap 到 incomplete。
4. gate 后不裸 branch；必须有 score source、score 阈值、child width/balance/open-node 限制。
5. 把 V562/V564 的 proof-tail hard negatives 接入 tree-policy/GAT branch score，让模型学“哪个 branch pair 会把 child 推进 completion-bound retry 拖尾”。

## 当前判断

retry gate 线有价值，但它只是 proof-tail controller，不是独立求解器。

目前意料之外的地方有两个：

- 直接省掉 retry 时间很容易制造“看起来很快的 TIME_LIMIT”，但这不是优化。
- 深层 branch score 覆盖不足比预期更严重；context gate 能识别 proof-tail，却经常没有可信 score 来接管。

下一步应先做小规模 retry on / retry gate / retry gate+adaptive cap smoke，再决定是否跑 full 60。`retry off` 只保留为诊断下界，不作为候选方案。
