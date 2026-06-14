# BPC_future 根因审计补充：active trajectory scalar check

日期：2026-06-13

## 目标

本轮继续回答一个具体问题：

> 做了这么多工作仍然不能稳定成功，到底是不是因为我们还没有找到一个可直接控制的单一信号？

本轮不改 solver、pricing、RMP、Pulse worker、certificate 或 lower-bound，只读已有结果：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/summary.csv`
- `BPC_future/results/root_cause_rcc_context_replay_return12_ablation_20260613/summary.csv`

检查四类可能解释：

1. priority task-set 命中；
2. returned batch 大小；
3. `active_support_changing_additions`；
4. 最后一轮 active fractional pressure。

## 结论

当前最重要的结论是：

**这些单一指标都不是充分条件。真正的根因层是 returned columns 对后续 RMP active-basis trajectory 的序列影响。**

也就是说，现在失败的原因不是某个局部模块完全没接好，而是：

- Pulse / profile-DP / early quota 都可以产生 true-RC negative columns；
- 但这些 columns 是否改善 20-task tail，取决于它们进入 RMP 后是否把 active basis 引到有利路径；
- 这个路径受具体 JourneyColumn signature、return quota、加入顺序、后续 dual、fractional pressure 和后续 pricing tail 共同影响；
- 现有 global knobs 只能扰动轨迹，不能稳定选择有利轨迹；
- 5/10 小实例又无法承受这些扰动的固定开销。

因此，继续扩大 Pulse worker、继续手写 whitelist、简单提高 cap/time 或默认 return12，都没有足够证据。

## 证据 1：priority task-set 命中不是必要条件

RC-C return12 ablation 中：

| profile | avg primal | priority selected | returned |
|---|---:|---:|---:|
| baseline | 749.331377 | 0 / 0 / 0 | 3 / 5 / 7 |
| return12 quota | 587.058145 | 0 / 0 / 0 | 96 / 96 / 96 |
| RC-C priority | 589.387683 | 4 / 4 / 4 | 96 / 72 / 96 |

关键点：

- return12 没有 priority 命中，但达到同量级改善；
- 本轮 return12 平均 primal 还略好于 RC-C priority；
- 所以 `tranq20_01` 的改善不能归因于手写 priority chain 本身。

priority chain 是一个可表达/可诊断工具，不是已证明的优化规律。

## 证据 2：active_support_changing 是局部强信号，但不是全局充分条件

在当前 RC-C return12 ablation 的 `tranq20_01` 上：

| profile | repeat | primal | active changed | trajectory class | fractional sum last |
|---|---:|---:|---:|---|---:|
| baseline | 0 | 783.715884 | 0 | inactive_addition_enters_active_basis | 3.5 |
| return12 | 0 | 592.501876 | 1 | active_support_changing_additions | 0 |
| RC-C | 0 | 588.579014 | 1 | active_support_changing_additions | 2.75 |
| baseline | 1 | 680.562363 | 0 | inactive_addition_enters_active_basis | 0 |
| return12 | 1 | 584.336280 | 1 | active_support_changing_additions | 0 |
| RC-C | 1 | 588.579014 | 1 | active_support_changing_additions | 0 |
| baseline | 2 | 783.715884 | 0 | inactive_addition_enters_active_basis | 5.0 |
| return12 | 2 | 584.336280 | 1 | active_support_changing_additions | 0 |
| RC-C | 2 | 591.005020 | 1 | active_support_changing_additions | 2.75 |

这里 `active_support_changing_additions` 与改善强相关。

但 Phase 10H 的旧 hard set 反例非常清楚：

- `tranq20_01` return8 / return12 都改善，但 `active_changed=0`；
- `mt20_greedy_tranq_01` return12 三次改善，但 `active_changed=0`；
- `mt20_greedy_apollo_01` return8 r2 改善，`active_changed=0`；
- 大量改善被分类为 `inactive_addition_enters_active_basis`。

所以 active-support-changing 是一个重要局部信号，但不能作为全局 gate。

更准确地说：

> 有些改善来自“新增列立即改变 active support”；另一些改善来自“初始 inactive 的列在后续 RMP 轮次进入 active basis”。

只看 active_changed 会漏掉后一类。

## 证据 3：最后一轮 fractional pressure 不是充分解释

Phase 10H 中有多个同值相反结果。

`mt20_greedy_tranq_01`：

| profile | repeat | outcome | primal | fractional sum last | fractional ratio last |
|---|---:|---|---:|---:|---:|
| return8 | 0/1/2 | worsened | 829.395319 | 7.75 | 1.0 |
| return12 | 0/1/2 | improved | 704.228463 | 7.75 | 1.0 |

相同最后 fractional pressure，一个 profile 稳定变差，另一个稳定改善。

`mt20_greedy_apollo_01`：

| profile | repeat | outcome | primal | fractional sum last | fractional ratio last |
|---|---:|---|---:|---:|---:|
| return8 | 0 | worsened | 1061.554044 | 5.75 | 0.866666667 |
| return8 | 2 | improved | 770.211317 | 5.75 | 0.866666667 |
| return12 | 0/1/2 | worsened | 1061.554044 | 1.666666667 | 0.4 |

同一 profile 同一 fractional pressure 可以一好一坏；更低 fractional pressure 也可以仍然变差。

因此，最后一轮 fractional pressure 只能作为 outcome 观测，不足以单独预测或控制 trajectory。

## 证据 4：returned 数量也不是充分条件

返回更多列可以在 `tranq20_01` 上改善：

- baseline returned `3 / 5 / 7`；
- return12 returned `96 / 96 / 96`；
- primal 从平均 `749.331377` 改善到 `587.058145`。

但 Phase 10H 的 `mt20_greedy_apollo_01` 说明返回更多列也能稳定变差：

- return12 returned `24 / 24 / 28`；
- 三次都 worsened 到 `1061.554044`。

因此，单纯扩大 returned batch 不是 production 方案。

## 为什么做了很多仍然不行

综合前面所有 phases，当前失败不是因为某一层完全没做，而是因为每层都只能解决问题的一部分：

- Pulse materialization / true RC：已证明能正确产列，但 active worker 找到的列不一定改变 tail；
- Sharded/transition/archive/bound/time-domain：能提高搜索语义质量，但不能保证找到对 RMP 有用的列；
- hidden-negative worker：能在 10/20 上加 true-RC negative columns，但 ROI 不稳定，小实例有开销风险；
- profile-DP cap/time/label cap：能改变 candidate domain，但不是稳定收益，且提高 cap 会增加搜索量；
- early quota / return12：能大幅扰动 20-task trajectory，但在不同 hard case 上方向相反；
- RC-C priority：能表达特定 context replay，但改善不来自 priority 命中本身；
- RMP stabilization：有局部正信号，但 hard set repeat 不稳定；
- duplicate/pool compression：关键行 active duplicate ratio 不支持作为主线。

所以真正难点是：

**exact pricing 不只需要找到 negative columns，还要在早期 CG 轨迹中选择会改变 active basis 并持续改善 incumbent / tail 的列。**

这不是一个单步 pricing oracle 可以通过“更负 RC”“更多列”“更大 cap”“更强 worker”直接保证的。

## 更新后的根因表述

当前最精确的根因表述是：

1. 5/10 规模 baseline 太快，任何默认非零 Pulse/RMP 探测开销都会破坏 no-regression；
2. 20-task hard set 的瓶颈在 early-column 到 RMP active-basis path 的上下文敏感性；
3. 有利 path 不是单一 task-set family、priority hit、best RC、returned 数量、active_changed 或 final fractional pressure 能充分刻画；
4. 当前所有 global knobs 都只能随机扰动这个 path，不能稳定选择有利 trajectory；
5. 因此还没有一个可默认启用、exact-safe、5/10 no-regression 且 20-task 稳定加速的规则。

## 下一步建议

如果继续根因方向，下一步不应写新 production 优化，而应做只读/校准型 trajectory impact extractor：

1. 对每个 early returned batch 记录：
   - added task-set / signature hash；
   - 是否与当前 active support 相交；
   - 是否在后续 N 轮进入 active basis；
   - active hash transition sequence；
   - fractional pressure delta sequence；
   - incumbent / primal delta sequence；
   - 后续 residual negative family。
2. 用这些序列特征解释 improved / worsened，而不是继续用单个 scalar；
3. 只有当该 extractor 在 selected hard set 上稳定分辨好/坏 trajectory 后，才考虑把它变成 opt-in selection rule；
4. 仍需保持 5/10 no-op、no certificate effect、no critical disagreement。

当前不能宣布目标完成。

## 验证

本轮为只读归因与文档更新。

只读抽取命令使用 CSV parser 读取：

- `sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/summary.csv`
- `root_cause_rcc_context_replay_return12_ablation_20260613/summary.csv`

未修改 solver 语义，未运行新的 benchmark。
