# 20260628 两类 Retry、Gate 对照与当前优化判断

## 结论

当前 retry 必须分成两类，不能混在一起看。

第一类是“不完整 no-column 后的补救 retry”。它对应 `journey_exact_pricing_retry` / `exact_retry`，主要由 `journey_retry_incomplete_no_column_enabled` 控制。它的作用是 cheap/profile pricing 没找到列但结果不完整时，再补一次真实 reduced-cost 检查，避免把不完整 no-column 当成证书。这类 retry 应继续保留。

第二类是 `completion-bound / final-judge retry`。它对应 `journey_exact_pricing_completion_bound_retry` / `exact_completion_bound_retry`，主要由 `journey_certificate_completion_bound_after_retry_enabled` 以及 `journey_certificate_completion_bound_retry_gate_*`、`journey_certificate_completion_bound_retry_budget_cap_*` 控制。它是 true-dual direct-label final judge，用来得到 `CERTIFIED_NO_NEGATIVE` 或发现隐藏负列。只有这条路径能支撑 exact gap / certificate。

smoke4 对比说明：retry gate 不是当前 20 规模 proof tail 的主优化方向。`retry_off` 很快，但没有 gap；`retry_gate` 和 `retry_on` 基本一样；`gate + cap` 只减少极少量调用和时间。

## 当前代码状态

已完成的边界：

- completion-bound retry gate 只统计 `exact_completion_bound_retry` / `exact_completion_bound_escalation_retry`。
- ordinary `exact_retry` 不进入 completion-bound gate/cap 统计。
- gate/cap 都是 opt-in。
- gate/cap 只改变调度或预算，不提供 bound、不提供 certificate、不剪枝。
- 被 gate/cap/off 后如果没有真实 certificate，必须 fail-closed，节点不能当作已闭合。

已验证测试：

```text
python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_is_opt_in_and_requires_history \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_blocks_expensive_zero_harvest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_keeps_harvest_signal \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_gate_context_scope_isolates_depth_trigger \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_budget_cap_is_opt_in_and_contextual \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_retry_budget_cap_keeps_unseen_context_uncapped
```

结果为 `OK`。

## Retry On / Off / Gate 结果

结果根目录：

```text
BPC_future/results/20260628_retry_on_off_gate_smoke4_randomtw20/
```

4 个 20-scale random-TW 难例，600 秒外部时限，branch score on，early branch off，admission off。

| group | rows | status | mean wall | gap available | mean gap |
|---|---:|---|---:|---:|---:|
| retry_on | 4 | 1 TIME_LIMIT, 3 EXTERNAL_TIME_LIMIT | 533.845s | 3/4 | 0.037560 |
| retry_off | 4 | 4 TIME_LIMIT | 89.389s | 0/4 | n/a |
| retry_gate | 4 | 1 TIME_LIMIT, 3 EXTERNAL_TIME_LIMIT | 533.900s | 3/4 | 0.037560 |
| retry_gate_adaptive_cap | 4 | 1 TIME_LIMIT, 3 EXTERNAL_TIME_LIMIT | 533.761s | 3/4 | 0.037560 |

事件侧：

| group | branch | right-censored branch | child CB retries | child certificate events | usable branch rows |
|---|---:|---:|---:|---:|---:|
| retry_on | 86 | 86 | 269 | 83 | 0 |
| retry_off | 0 | 0 | 0 | 0 | 0 |
| retry_gate | 86 | 86 | 269 | 83 | 0 |
| retry_gate_adaptive_cap | 85 | 85 | 266 | 82 | 0 |

解释：

- `retry_off` 的低 wall time 是因为不做 final-judge certificate，所有实例 `gap_available=false`，不能算优化。
- `retry_gate` 没有明显阻断，说明当前昂贵部分不是 gate 要拦的“昂贵、不完整、零 harvest retry”。
- `gate + cap` 只少了 1 次 branch、3 次 child CB retry、1 次 child certificate event，对 600 秒求解没有实质改善。

## Completion-Bound Cache 诊断

额外试了 `journey_certificate_completion_bound_next_sortie_cache_enabled=True`。

结果：

- partial pruning 保持默认开启时，cache 实际被关闭，hit/miss 为 0。
- 关闭 partial pruning 后，cache 真实生效，但两个 smoke 实例仍 600 秒超时，profile generation time 从约 `580.233s` 上升到 `862.402s`。

原因是 partial pruning 使用 parent-specific label state 做剪枝；只按 used-mask 复用 next-sortie profile 会丢掉这些剪枝，导致 evaluated timed trips 大幅上升。结论是：不能靠关闭 partial pruning 来换 cache。

## 能不能优化

如果问题是“retry gate 能不能优化完整 20-scale 求解”，当前答案是：不能作为主线。

它能做的是安全阀：

- 阻断少数昂贵且不完整、零 harvest 的 final-judge retry；
- 给 proof-tail 行为提供诊断字段；
- 帮助生成 hard negative / proof-risk 标签。

它不能做的是：

- 替代 completion-bound final judge；
- 让没有 certificate 的节点变成 closed；
- 单独把 20-scale 从 timeout 拉到 OPTIMAL。

## 当前真正的问题

当前问题不是“retry 没关好”，而是：

1. branch score 仍会把搜索带进大量需要 certified final-judge 的子树；
2. 很多 final-judge retry 是合法 certificate proof，不是浪费调用；
3. 每次 certified no-negative 的证明本身很贵；
4. 深层 branch score 覆盖不足，gate 识别到风险后经常没有可信 score 接管；
5. 现有 deep child-probe 仍大量 right-censored，完整正例仍不足。

## 意料之外的地方

最意外的是 `retry_off` 这么快，但完全没有 gap。这说明单看 wall time 会误判。

第二个意外是 expensive tail 主要不是 incomplete zero-harvest，而是 certified no-negative proof。也就是说，慢的部分很多是精确证明链必须做的工作，不能简单砍掉。

第三个意外是 next-sortie cache 与 partial pruning 冲突。cache 有 hit 不代表更快；默认 partial pruning 比这个 cache 更重要。

## 当前优化思路

下一步不继续扩大 retry gate 网格，而是转向 proof-tail-aware branch score。

主线：

```text
保留 completion-bound/final-judge retry
+ retry gate/cap 作为安全阀
+ 从 completion-bound-tail / child CB retry / certificate events 提取风险标签
+ 训练或叠加 branch score 惩罚
+ 减少进入昂贵 certified final-judge 子树的次数
```

具体方向：

1. 普通 no-column retry 保持开启。
2. completion-bound/final-judge retry 保持开启，保证 gap/certificate。
3. retry gate/cap 保留，但只作为 opt-in 安全阀和诊断，不作为默认主加速器。
4. branch score 新增 proof-tail penalty：
   - 惩罚高 `child_completion_bound_retries`；
   - 惩罚高 `child_certificate_pricing_events`；
   - 惩罚 right-censored `completion_bound_tail`；
   - 惩罚深层缺 score / 宽 child / balance 差的候选。
5. 深层 child-probe 要改成 paired probe：同一 context 下比较 baseline pair 与 1-2 个 alternative pair 的 proof cost，而不是盲跑大量 alternative。
6. 未最优实例继续记录 `gap_available`、`gap_source`、`best_primal_bound`、`best_dual_bound`、`gap`、`gap_unavailable_reason`，避免把无证书快停误判为优化。

## 当前进度

- retry gate / cap 代码和测试已完成。
- retry on/off/gate/gate+cap smoke4 已完成。
- cache / partial pruning 诊断已完成。
- V596 timeout-suppressed score overlay 已能改变 root pair，但 V597 smoke4 仍为 4/4 `EXTERNAL_TIME_LIMIT`。
- V598/V599 deep child-probe 已开始，first8 没有正例，都是 right-censored / hard-negative proof-cost 样本。

当前目标仍未达成：20-scale random-TW 还没有实现 600 秒内全量 OPTIMAL，更没有达到 200 秒平均/目标线。
