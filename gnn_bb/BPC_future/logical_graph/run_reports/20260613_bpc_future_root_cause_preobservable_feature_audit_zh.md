# BPC_future 根因审计补充：pre-observable feature audit

日期：2026-06-13

## 目标

上一轮 trajectory impact extractor 说明：

- future active hit 比 immediate active_changed 更接近真实机制；
- zero-fractional episodes 与 incumbent update 更能解释 outcome；
- 但这些都是 RMP solve 后的事后信号。

本轮继续检查：

> addition 当时可见的特征，是否已经足以形成稳定 selector？

本轮只读已有 JSONL / CSV，不改 solver、pricing、RMP、Pulse worker、certificate 或 lower-bound。

## 数据与特征

只读输入：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/summary.csv`
- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/logs/*.jsonl`
- `BPC_future/results/root_cause_rcc_context_replay_return12_ablation_20260613/summary.csv`
- `BPC_future/results/root_cause_rcc_context_replay_return12_ablation_20260613/logs/*.jsonl`

抽取每个 `journey_column_addition` 在 addition 当时可见的字段：

- `changed_task_set_hash`
- `candidate_signature_hash`
- `pricing_best_reduced_cost`
- `added_journeys`
- `new_task_set_count`
- `replacement_task_set_count`
- `active_changed_task_set_count`
- `addition_productivity_class`

对每个 run 构造：

- first-2 task hash sequence；
- first-2 signature hash sequence；
- first-3 composition class sequence；
- first-3 best-RC sequence。

## 关键反例：Apollo20 同前缀不同 outcome

`mt20_greedy_apollo_01` 的 return8 profile 有一个最关键的对照：

| repeat | outcome | primal | first-2 task hash | first-2 signature hash |
|---:|---|---:|---|---|
| r0 | worsened | 1061.554044 | `23e2d6c7dfcd631b` -> `ad399a8299c80f10` | `b764a94bfbc6e661` -> `58603ae23ad95e60` |
| r2 | improved | 770.211317 | `23e2d6c7dfcd631b` -> `ad399a8299c80f10` | `b764a94bfbc6e661` -> `58603ae23ad95e60` |

前两轮 additions 的 task hash 和 signature hash 完全相同，但最终结果相反。

前 3 轮 composition class 也相同：

```text
cg1: added=8, new=8, replacement=0, active_changed=0, class=changed_inactive_only
cg2: added=8, new=8, replacement=0, active_changed=0, class=changed_inactive_only
cg3: added=8, new=7, replacement=1, active_changed=0, class=changed_inactive_only
```

分叉发生在 cg3 的具体 candidate：

| repeat | cg3 signature | cg3 samples | cg3 best RC |后续|
|---:|---|---|---:|---|
| r0 worsened | `a0cff104367cbbc7` | 包含 `[4,14,18]` | `-64.283` | 后续 `fractional_sum=5.75`，无 incumbent update |
| r2 improved | `ce10940e649c88ce` | 包含 `[5,10,18]` | `-20.191` | cg4 `fractional_sum=0`，有 incumbent update |

这给出两个强结论：

1. first-2 prefix 特征不足以预测 outcome；
2. `best_rc` 更负不代表更好，r0 的 cg3 RC 更负但 outcome 更差。

因此，简单的 best-RC-first、task-family whitelist、composition-class gate 都不足以作为稳定 selector。

## 关键反例：Tranq20 同 best-RC 前缀只能说明局部正向，不可泛化

`tranq20_01` Phase 10H 中 return8 / return12 的 first-3 best-RC sequence 相同：

```text
cg1 -57.089
cg2 -53.860
cg3 -48.675
```

但 return8 / return12 的 primal 仍有不同：

- return8 improved avg `595.780`；
- return12 improved avg `601.393`。

在这个 instance 上，best-RC 前缀能说明两个 profile 都进入有利大方向，但不能解释 return8 / return12 的具体差异，也不能推广到 Apollo20。

## 关键反例：RC-C 和 return12 同前缀不说明 priority 更好

`root_cause_rcc_context_replay_return12_ablation_20260613` 中，`tranq20_01` 的 return12 与 RC-C priority 有相同 first-2 task hash 和 signature hash：

```text
task hash:
cg1 0412b006daec2764
cg2 c9b631800bac4018

signature hash:
cg1 d064a169693033f0
cg2 4a8ef99eaf6f9ece
```

但平均结果：

- return12 avg primal `587.058145`；
- RC-C priority avg primal `589.387683`。

这再次说明：

- priority 命中不是必要条件；
- 同前缀 additions 之后的后续 trajectory 才决定最终效果；
- 手写 priority chain 不是根因修复。

## 目前能确定的根因层

到这一轮为止，证据支持的根因层已经很明确：

1. 不是找不到 true-RC negative columns；
2. 不是 leaf materialization / true-RC mismatch；
3. 不是单纯 Pulse worker budget 不够；
4. 不是单纯 profile-DP cap/time/label cap；
5. 不是 duplicate pool pressure；
6. 不是 task-set family / priority hit / best RC / immediate active_changed / future active hit 任一单独指标；
7. 而是：

> 在 20-task hard set 上，早期 column additions 会通过 RMP active-basis trajectory 决定后续 incumbent 和 proof tail；当前系统没有一个事前可见、可泛化、低开销、exact-safe 的 selector 来选择有利 trajectory。

更具体地说：

- 前两轮 additions 可以完全相同，但第三轮具体 signature 让 outcome 分叉；
- 更负 RC 可以导向更差 trajectory；
- 相同 task family 可以在不同 return quota 下方向相反；
- future active hit / zero-fractional / incumbent update 能后验解释，但不能直接在线使用；
- 5/10 小实例太快，不能承担大规模尝试多个 trajectory 的默认成本。

## 为什么这解释了 5/10 不退化与 20 优化不能同时满足

5/10：

- baseline 已经很快；
- active worker / audit / larger cap / stabilization / return quota 都有非零固定开销；
- 没有非常可靠的 trigger 时，这些机制很容易在小实例上纯增加时间；
- 所以 5/10 no-regression 只能靠严格 no-op gate。

20：

- 20-task 改善需要改变 early active-basis path；
- 但当前候选规则只能随机扰动 path；
- 某些扰动在 `tranq20_01` 有效，在 Apollo20 / greedy Tranq20 上可能相反；
- 没有 selector 时，扩大 batch 或增加 worker budget 只是提高“碰到好 path”的概率，同时也提高“碰到坏 path”和开销的概率。

因此，当前失败是结构性的：

**我们已经有多个能产生局部正信号的机制，但缺少能在不同 instance/context 下事前判断该用哪个机制、返回哪些具体 columns 的选择层。**

## 下一步仍不能做什么

不能因为这些证据就：

- 默认启用 return12；
- 默认启用 Pulse worker；
- 增大 worker time limit；
- 用 best-RC-first 替代 trajectory reasoning；
- 用 priority whitelist 作为 production rule；
- 打开 official certificate gate；
- 宣称目标完成。

## 下一步可做什么

如果继续 root-cause 方向，下一步应做 calibration-only candidate-level contrast：

1. 在同一 pricing call 内记录被返回与未返回的 negative candidates；
2. 对比它们的 task-set、signature、rough/true RC、relation to active basis、new/replacement/support-changing class；
3. 离线追踪哪些 returned candidates 后续进入 active basis、触发 incumbent update；
4. 重点解释 Apollo20 cg3 分叉：为什么 `ce10940e649c88ce` 比 `a0cff104367cbbc7` 更有益，尽管 RC 没那么负；
5. 只有当事前特征能稳定区分这种分叉后，才考虑 opt-in selection rule。

## 目标状态

目标仍未完成。

本轮的明确进展是：根因不再停留在“active-basis trajectory 很重要”的泛化表述，而是定位到：

> 当前缺的是 candidate/signature 级别的事前 trajectory selector；现有 pricing 选择信号无法在同 early prefix 下避免坏的第三轮 trajectory 分叉。

这仍是根因解释，不是已证明的优化方案。

## 验证

本轮为只读归因与文档更新。

未修改 solver 语义，未运行新的 benchmark。
