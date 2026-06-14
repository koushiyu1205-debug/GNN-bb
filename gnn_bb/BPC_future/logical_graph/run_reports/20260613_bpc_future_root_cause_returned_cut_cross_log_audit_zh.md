# BPC_future 根因审计补充：returned-cut cross-log audit

日期：2026-06-13

## 目标

上一轮 candidate-level contrast 证明了一个强反例：

> `mt20_greedy_apollo_01` 在相同 cg3 RMP/dual context 下，较弱 RC 的 `[5,10,18]` candidate 被 returned 后走到 improved trajectory；更负 RC 的 `[4,14,18]` candidate 被 returned 后走到 worsened trajectory。

本轮继续只读检查一个更宽的问题：

**这个现象能不能由某个简单 scalar 解释，例如 returned 数量、final fractional pressure、active hash churn、best RC、priority hit？**

如果能，就可以把优化方向收紧到一个简单 rule。  
如果不能，说明根因仍然是 candidate/signature/timing 级 trajectory selector，而不是单一开关。

本轮不改 solver 行为，不启用 production worker，不改变 certificate。

## 输入

只读输入：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/summary.csv`
- `BPC_future/results/root_cause_rcc_context_replay_return12_ablation_20260613/summary.csv`
- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_5_10_guard_20260613/summary.csv`
- 对应 JSONL 日志用于确认已有字段范围。

对每个非 baseline row，按同一 `source / instance / repeat_index` 的 baseline primal 做 `improved / worsened / same` 分类。

## 机械复核 1：20-task outcome 与简单 scalar 不单调

### Phase 10H 20-task

| instance | profile | repeat | outcome vs baseline | primal delta | tail returned | final fractional sum | active hash churn | best rc |
|---|---|---:|---|---:|---:|---:|---:|---:|
| `tranq20_01` | return8 | 0 | improved | -183.982696 | 64 | 0.0 | 6 | -24.368039 |
| `tranq20_01` | return8 | 1 | improved | -184.924818 | 64 | 0.0 | 7 | -16.233700 |
| `tranq20_01` | return8 | 2 | improved | -187.055474 | 64 | 0.0 | 7 | -11.345522 |
| `tranq20_01` | return12 | 0 | improved | -175.974351 | 96 | 7.0 | 7 | -12.894086 |
| `tranq20_01` | return12 | 1 | improved | -187.176358 | 96 | 0.0 | 7 | -11.373906 |
| `tranq20_01` | return12 | 2 | improved | -175.974351 | 96 | 7.0 | 7 | -12.894086 |
| `mt20_greedy_tranq_01` | return8 | 0/1/2 | worsened | +67.580916 | 25 | 7.75 | 4 | 17.199974 |
| `mt20_greedy_tranq_01` | return12 | 0 | improved | -57.585940 | 29 | 7.75 | 4 | 17.199974 |
| `mt20_greedy_tranq_01` | return12 | 1/2 | improved | -57.585940 | 30 | 7.75 | 4 | 17.199974 |
| `mt20_greedy_apollo_01` | return8 | 0 | worsened | +213.741813 | 24 | 5.75 | 3 | 0.0 |
| `mt20_greedy_apollo_01` | return8 | 1 | worsened | +139.913748 | 16 | 5.75 | 2 | 0.0 |
| `mt20_greedy_apollo_01` | return8 | 2 | improved | -151.428979 | 32 | 5.75 | 4 | 0.0 |
| `mt20_greedy_apollo_01` | return12 | 0 | worsened | +213.741813 | 24 | 1.666667 | 2 | 0.0 |
| `mt20_greedy_apollo_01` | return12 | 1 | worsened | +139.913748 | 24 | 1.666667 | 2 | 0.0 |
| `mt20_greedy_apollo_01` | return12 | 2 | worsened | +139.913748 | 28 | 1.666667 | 2 | 0.034526 |

关键反例：

1. `mt20_greedy_tranq_01` return8 和 return12 的 `final fractional sum=7.75`、`active hash churn=4`、`best rc=17.199974` 相同，但 return8 三次 worsened，return12 三次 improved。
2. `mt20_greedy_apollo_01` return8 r0/r1/r2 的 `final fractional sum=5.75`、`best rc=0.0` 相同，但 r0/r1 worsened，r2 improved。
3. `mt20_greedy_apollo_01` return12 final fractional sum 更低，为 `1.666667`，但三次全部 worsened。因此 final fractional pressure 不是充分指标。
4. `tranq20_01` return12 的 `tail returned=96` 能改善；但 `mt20_greedy_apollo_01` return12 虽然 returned 增加到 `24/24/28`，仍全部 worsened。returned count 本身不是 production rule。
5. best RC 不是可靠方向。Apollo20 candidate-level contrast 已经给出更强证据：`best_rc=-64.283449` 的 r0 worsened，`best_rc=-20.1912655` 的 r2 improved。

### Return12 vs RC-C ablation

`tranq20_01` 的 return12 与 RC-C priority 都改善：

| profile | repeats | avg primal | avg tail returned | avg final fractional sum |
|---|---:|---:|---:|---:|
| return12 quota | 3 | 587.058145 | 96.0 | 0.0 |
| RC-C priority | 3 | 589.387683 | 88.0 | 1.833 |

这说明：

- `tranq20_01` 的改善确实来自 early returned trajectory 干预；
- 但 return12 不需要 priority task-set hit 也能达到同量级改善；
- 所以不能把 root cause 简化成“缺某个手写 task-set priority”。

## 机械复核 2：5/10 no-regression 只能靠 20-only no-op guard

Phase 10H 5/10 guard：

| instance | profile | primal delta vs baseline | wall delta 量级 |
|---|---|---:|---:|
| `apollo5` | return8 20-only | 0.0 | -0.009s |
| `apollo5` | return12 20-only | 0.0 | -0.009s |
| `tranq5` | return8 20-only | 0.0 | +0.002s |
| `tranq5` | return12 20-only | 0.0 | +0.002s |
| `apollo10` | return8 20-only | 0.0 | +0.004s |
| `apollo10` | return12 20-only | 0.0 | +0.000s |
| `tranq10_09` | return8 20-only | 0.0 | -0.001s |
| `tranq10_09` | return12 20-only | 0.0 | +0.004s |
| `tranq10_04` | return8 20-only | 0.0 | +0.009s |
| `tranq10_04` | return12 20-only | 0.0 | +0.002s |

这支持一个工程边界：

> 5/10 不退化目前只能通过 20-only no-op guard 保证。任何真实 worker/probe/extra pricing 对 5/10 都必须默认关闭，否则固定开销会吞掉小实例收益空间。

这不是优化成功，只是避免污染小规模。

## 当前根因判断

综合 candidate-level contrast 和本轮 cross-log audit，当前最具体、证据最强的根因是：

> 20-task hard tail 不只是“找不到 negative columns”。pricing 已经能产生很多 true-RC negative / selected candidates；失败在于 early returned batch 的 candidate-level ordering / truncation 会改变后续 active-basis trajectory。现有全局规则按 rough/best RC、简单 diversity、return count、或 coarse task-set priority 扰动 trajectory，但不能稳定选择对后续 RMP/CG 有利的 concrete JourneyColumn signature / timing。

这解释了“做了这么多仍然不行”：

- Pulse worker 能找负列，但负列未必是有利 active trajectory；
- 扩大 returned count 有时把好列带进来，有时把坏列也带进来；
- 提高 cap/time 只扩大候选域，不保证 returned cut 选对；
- priority task-set 太粗，无法区分同 task-set 或邻近 family 下的 signature/timing；
- final fractional / active churn / future active hit 多数是后验指标，不能直接在线作为 exact-safe selection rule；
- 5/10 因为规模太小，任何额外 worker/probe 固定开销都很容易退化。

## 还不能宣称完成的部分

这轮仍然没有证明一个可生产化优化方向。

缺口是：

1. 还没有在新 `diagnostic_returned_boundary_candidate_samples` / `diagnostic_truncated_boundary_candidate_samples` 字段下重新跑 20-task，用直接边界样本验证“第 N+1 个被截断候选”的 signature / timing。
2. 还没有找到 addition 前可见、可泛化的 selector 特征，能稳定区分 `a0cff...` 这类坏 trajectory 与 `ce109...` 这类好 trajectory。
3. 还没有证明 selector 在 5/10 no-op 或严格 gate 下不退化。
4. 还没有证明 selector 在 selected 20-task hard set 上稳定大幅改善，而不是单点或单 profile 改善。

因此，当前目标仍未完成。

## 下一步建议

下一步仍应是 calibration-only：

1. 用新增 returned/truncated boundary diagnostics 重跑极窄 20-task sample，不扩大 worker，不启用 certificate；
2. 记录 top returned 与 first truncated candidates 的：
   - rank；
   - rough RC / true RC；
   - task-set；
   - profile start summary；
   - concrete journey signature / timing 摘要；
3. 离线追踪这些 candidate 是否在后续 N 轮进入 active basis、触发 zero-fractional episode 或 incumbent update；
4. 只有当 addition 前可见特征能稳定区分 improved/worsened，才进入 opt-in selector A/B；
5. 任何 selector A/B 必须先通过 5/10 no-regression guard，再看 20-task hard set repeat。

