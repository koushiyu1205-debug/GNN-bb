# BPC_future 5/10 回退与 20-task 无稳定优化根因审计

日期：2026-06-13

## 目标

本报告回答一个比 Pulse 更上层的问题：

为什么做了大量安全改造、worker、profile-DP、selection、quota、dual stabilization 之后，仍然不能同时做到：

1. 5-task 不退化；
2. 10-task 不退化；
3. selected 20-task 明显优化；
4. exactness / no critical disagreement 保持成立。

本轮不做主线大修改，不启用 production worker，不开放 certificate gate，不改变 lower-bound 规则。

## 根因判定标准

本报告不把“看起来合理”的解释写成根因。

一个原因必须同时满足：

1. 在现有日志 / summary / 报告中能观察到对应症状；
2. 至少有一个受控干预能改变该症状或结果；
3. 干预结果能解释为什么它不能稳定扩展到 5/10/20 全目标；
4. 没有被后续 A/B 或 guard 直接证伪。

如果只有症状、没有干预正证据，只能标为“候选方向”或“阻塞现象”，不能标为根本原因。

## 结论

当前证据支持的根本原因是：

**求解性能主要受 early-column / RMP active trajectory 的路径依赖控制，而不是单纯缺少更多负列、Pulse 不够强、profile-DP cap 太小、pricing time 太短、selection mode 不好，或列池 duplicate 太多。**

更具体地说：

1. 5/10 规模基线很快，任何默认启用的 audit / worker / probe 固定开销都会吃掉收益；5/10 no-regression 主要靠 `20-only / no-op gate`，不是靠新机制本身带来收益。
2. 20-task 上确实存在能改善某些实例的 early-column / RMP trajectory 干预，但同一干预会让另一些 hard case 回退。
3. 这说明 20-task 的瓶颈不是一个单调 knob，而是实例和上下文相关的列进入顺序 / active basis 轨迹问题。
4. profile-DP / proof-tail incomplete 是重要阻塞现象，但简单增大 cap、time、label budget 或 selection mode 没有稳定减少 incomplete，因此它不是已经被证明的单一根因。

因此当前不能继续做“全局加预算 / 全局加 worker / 全局改 selection / 全局调 cap”。

下一步如果继续追求优化，当前最有证据支持的候选诊断方向是：

- context-aware early-column / active-family trajectory control；
- RMP active-family stabilization；
- column impact filtering / pool policy；
- legacy/profile-DP proof-tail 的结构化 ordering，而不是粗粒度预算扩张。

这不是最终优化方案完成声明。

当前还没有百分百证据证明某个方案能够在保持 exactness、5/10 不退化的同时，大幅加速 selected 20-task 最优解求解。后续必须用新的受控干预证明这一点，不能只凭本报告宣布目标完成。

## 证据 1：5/10 回退的根因是固定开销，没有足够收益空间

### 1.1 默认 worker/probe 会拖慢小规模

`Sharded Pulse Worker Negative-result Synthesis` 中的 expanded A/B：

| scale | profile | avg wall | worker events | added | new task-set | support-changing |
|---:|---|---:|---:|---:|---:|---:|
| 5 | baseline | 0.028776 | 0 | 0 | 0 | 0 |
| 5 | strict current probe | 0.362103 | 2 | 0 | 0 | 0 |
| 10 | baseline | 0.102410 | 0 | 0 | 0 | 0 |
| 10 | strict current probe | 0.614190 | 11 | 10 | 4 | 2 |
| 20 | baseline | 0.191645 | 0 | 0 | 0 | 0 |
| 20 | strict current probe | 0.764784 | 5 | 4 | 2 | 1 |

解释：

- 5-task 即使没有加列，也因为 probe / audit / skip path 产生明显 overhead；
- 10-task 能加列，但 wall time 显著变差；
- 20-task 能加列，但平均 wall time仍明显上升。

这证明：

**5/10 不退化不能靠默认启用新机制，只能靠小规模完全不触发或接近零开销。**

### 1.2 能通过 5/10 guard 的 profile，本质上是 no-op

多个后续 profile 都通过 5/10 guard，但原因是 `task_count < 20` 时直接 no-op：

- Phase 9L previous-anchor dual stabilization：
  - 5-task rows = 40，experimental avg wall 只比 baseline 增 `0.000042s`；
  - 10-task rows = 40，experimental avg wall 只比 baseline 增 `0.000665s`；
  - `dual_stabilization_events=0`。
- Phase 10H early new-task-set quota：
  - 5/10 guard rows = 15；
  - `official_result_changed_vs_baseline=False`；
  - primal 与 baseline 完全一致。
- Phase 11A pricing-time profiles：
  - 5/10 profiles 均为 no-op；
  - primal 与 baseline 完全一致。
- Phase 11B selection-mode profiles：
  - 5/10 profiles 均为 no-op；
  - primal 与 baseline 完全一致。

结论：

**5/10 不退化的可行工程边界已经很清楚：任何非零 worker/probe 类机制都必须被 gate 掉。**

这不是优化成功，而是避免污染小规模。

## 证据 2：20-task 有真实正信号，但不是全局单调优化

### 2.1 Early-column quota 是最清楚的正向干预证据

Phase 10H 是目前最强的“尝试修改并影响结果”的证据。

它没有启用 Pulse worker、certificate 或 dual stabilization，只改 20-only early new-task-set quota。

20-task repeats：

| instance | baseline repeats | quota return8 repeats | quota return12 repeats |
|---|---:|---:|---:|
| `tranq20_01` | 781.101309, 781.101309, 781.101309 | 597.118613, 596.176491, 594.045835 | 605.126958, 593.924951, 605.126958 |
| `mt20_greedy_apollo_01` | 847.812231, 921.640296, 921.640296 | 1061.554044, 1061.554044, 770.211317 | 1061.554044, 1061.554044, 1061.554044 |
| `mt20_greedy_tranq_01` | 761.814403, 761.814403, 761.814403 | 829.395319, 829.395319, 829.395319 | 704.228463, 704.228463, 704.228463 |

关键观察：

- `tranq20_01`：两个 quota profile 三次 repeat 都改善；
- `mt20_greedy_tranq_01`：return12 三次改善，但 return8 三次变差；
- `mt20_greedy_apollo_01`：return8 只有一次改善，两次明显变差；return12 三次都变差。

因此：

**early-column trajectory 干预是真实有效的，但方向强烈依赖 instance/context。**

这就是为什么 20-task 不能靠一个全局 profile 稳定优化。

### 2.2 Early inactive columns 后续进入 active basis，是结果分叉的直接机制

Phase 10G 只读归因显示：

- 所有 27 行 `early_column_trajectory_class` 都是 `inactive_addition_enters_active_basis`；
- early `journey_column_addition` 记录中 `active_changed_task_set_count=0`；
- 加列当下主要是 inactive changed/new task-set；
- 后续 RMP 的 active top samples 中出现这些 task-set；
- 因此 active-basis 分叉不是“加列立即 active”，而是“inactive column 进入 pool 后，在后续 RMP 中成为 active basis 的一部分”。

这解释了为什么：

- 一个 early intervention 可以显著改变后续 incumbent；
- 但相同 intervention 在不同 instance 上方向不一致；
- 单纯看 true-RC 最负或 returned count 不足以预测收益。

### 2.3 Previous-anchor dual stabilization 也支持“trajectory-sensitive”判断

Phase 9L previous-anchor dual stabilization：

20-task hard smoke：

| profile | rows | avg wall | changed | improved | worsened | accepted |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 6 | 1.829656 | 0 | 0 | 0 | 0 |
| previous-anchor | 6 | 1.763805 | 4 | 4 | 2 | 24 |

明细：

- `mt20_greedy_tranq_01`：两个 repeat 都稳定改善；
- `tranq20_01`：一次 improved，一次 worsened；
- `mt20_greedy_apollo_01`：一次 improved，一次 worsened。

这与 Phase 10H 方向一致：

**稳定化/轨迹类干预能改变 20-task 结果，但还没有一个全局规则能保证 selected hard set 全部改善。**

## 证据 3：几个直觉候选根因已被证伪或降级

### 3.1 “只是 Pulse 不够强”不是根因

证据：

- worker 能安全加入 true-RC negative columns；
- Phase 8Q 中 worker returned / added journeys = 10 / 10；
- 其中 added new task sets = 8，support-changing = 2；
- 但 official status 仍是 35 / 35 `TIME_LIMIT`；
- worker 加列不稳定降低 residual pricing tail。

因此：

Pulse coverage 有缺口，但“再让 Pulse 多找几条列”不是已证明的根因修复。

### 3.2 “profile-DP cap 太小”不是根因

Phase 10B state-cap sensitivity：

- 5/10 no-op guard 生效；
- 20-task cap2000 / cap3000 没有稳定减少 incomplete；
- `mt20_greedy_apollo_01` 和 `mt20_greedy_tranq_01` 出现 incumbent 变差；
- cap 提高能找到更负 candidate，但没有改善 3s 内 incumbent。

因此：

profile-DP state cap 是阻塞症状，但简单增大 cap 不是根因修复。

### 3.3 “pricing time 太短”不是根因

Phase 11A pricing-time sensitivity：

| profile | pricing state | improvement class | profile-DP incomplete sum | state-cap hits | profile-DP time |
|---|---|---|---:|---:|---:|
| baseline | 4 `INCOMPLETE_LIMIT`, 2 `FOUND_NEGATIVE` | baseline | 4 | 29 | 0.391099 |
| 0.6s | 6 `INCOMPLETE_LIMIT` | 4 improved, 2 worsened | 6 | 30 | 0.581605 |
| 1.0s | 6 `INCOMPLETE_LIMIT` | 1 improved, 5 worsened | 6 | 20 | 0.498347 |

关键观察：

- 增加 pricing time 没有减少 incomplete；
- baseline 的两个 `FOUND_NEGATIVE` 在 0.6s / 1.0s 下都变成 `INCOMPLETE_LIMIT`；
- 0.6s 有部分 incumbent 改善，但 wall time 接近 time limit；
- 1.0s 大多回退。

因此：

**不是简单“给 pricing 更多时间”就能优化。更多时间会改变列进入顺序，并可能把 negative-returning path 扰动成 incomplete path。**

### 3.4 “selection mode 不好”不是根因

Phase 11B selection-mode sensitivity：

- state-cap smoke (`pricing_max_dp_states=1`)：
  - selected input/materialized/returned = 0 / 0 / 0；
  - selection mode 根本没有机会介入；
  - tail 在 candidates 产生前已撞到 state cap。
- activation smoke (`pricing_max_dp_states=1000`)：
  - baseline / integer_diverse / orthogonal 都是 6 `FOUND_NEGATIVE`；
  - selected input/materialized/returned 都是 72 / 18 / 18；
  - official outcome 没有改变；
  - orthogonal 一次改变 returned task-set，但没有收益。

因此：

returned-column selection 不是当前主要根因。

### 3.5 “列池 duplicate 太多”不是根因

Phase 9E pool / RMP attribution：

- Apollo20 coverage-target profile：
  - pool duplicate ratio = 0.0；
  - active duplicate ratio = 0.0；
  - active fractional ratio = 0.583333333；
  - RMP degeneracy pressure class = `active_fractional_pressure`。
- Apollo20 auto-active validation profile：
  - duplicate ratio = 0.0；
  - active duplicate ratio = 0.0；
  - active fractional ratio = 0.0；
  - active basis stable；
  - dual 明显移动；
  - 仍有 overlapping negative family。

因此：

简单 duplicate compression 不是第一根因。

### 3.6 “profile-DP proof-tail incomplete”是阻塞现象，但不是已证明的单一根因

Phase 10A 显示 20-task tail 中确实有：

- `profile_dp_incomplete_tail`；
- state-cap hits；
- top mask hotspots。

但后续干预显示：

- 提高 state cap 不稳定；
- label-cap 不稳定；
- 增加 pricing time 不稳定；
- selection mode 不稳定；
- refinement 没有降低 incomplete。

因此：

profile-DP proof-tail 是必须继续关注的阻塞层，但当前证据还不能把它简化成“cap/time/selection 任一项不足”。

## 为什么 5/10 不退化和 20 优化难以同时满足

核心矛盾是：

1. 5/10 需要几乎零开销：
   - worker/probe/audit 只要默认启用，就有显著固定成本；
   - 因此 5/10 只能靠 no-op / 20-only gate 保护。
2. 20-task 需要改变 early-column / active-basis trajectory：
   - 只有真正改变列进入顺序的干预才会改变 20-task outcome；
   - 但这些干预在不同 hard case 上方向相反；
   - 同一个 quota / stabilization profile 可以同时改善一个 20-task、恶化另一个 20-task。
3. 粗粒度预算扩张不能解决这个矛盾：
   - cap/time 增大不等于更好；
   - 它会扰动候选顺序和 active trajectory；
   - 有时还把 `FOUND_NEGATIVE` 变成 `INCOMPLETE_LIMIT`。

所以根本问题不是“还没找到足够强的全局 knob”，而是：

**当前求解轨迹对 early-column order / active-family 选择高度敏感，而我们还没有一个能预测哪类 early trajectory 对当前 instance/context 有益的选择机制。**

## 当前有依据的下一步候选方向

可以继续推进验证的方向只有一个：

**context-aware early-column / active-family trajectory control。**

理由：

- 它有正向干预证据：
  - Phase 10H 对 `tranq20_01` 稳定改善；
  - Phase 10H 对 `mt20_greedy_tranq_01` 在 return12 下稳定改善；
  - Phase 9L 对 `mt20_greedy_tranq_01` previous-anchor 稳定改善。
- 它也解释了失败：
  - 同一干预在 Apollo20 或另一个 return quota 下回退；
  - 因此不能做 global default。
- 它和只读归因一致：
  - Phase 10G 显示 early inactive columns 后续进入 active basis；
  - Phase 10F 显示 active hash trajectory 分叉与改善行相关。

但这仍只是候选方向，不是已经证明可生产化的优化方向。

下一步不应直接写生产优化，而应先做更窄的 evidence phase：

1. 对每个 selected 20-task hard case，记录 early added task-set family、active hash path、incumbent change；
2. 找出改善 repeat 中 recurring 的 early families；
3. 做 per-instance / per-context replay intervention，而不是全局 quota；
4. 验证：
   - 5/10 仍 no-op；
   - selected 20-task 每个 hard case 不回退；
   - incomplete 数量不增加；
   - no critical disagreement；
   - no certificate / lower-bound effect。

如果这个方向仍不能形成稳定改善，则应停止 trajectory tuning，转向更底层的 RMP formulation / stabilization 或 legacy proof-tail 重构。

## 目标完成边界

本报告没有宣布总体目标完成。

原因：

1. 当前只证明了最有依据的根因是 early-column / active-family trajectory sensitivity；
2. 当前只证明了多个全局 knob 无法稳定优化；
3. 当前没有证明某个新方案能在：
   - 保证 exactness；
   - 5-task 不退化；
   - 10-task 不退化；
   - selected 20-task 明显加速最优解求解；
   - no critical disagreement；
   同时成立。

因此，本报告只能作为下一步优化方向选择的证据基础，不能作为“目标已完成”的依据。

## 当前不能作为下一步主线的方向

不要继续：

- 默认启用 Pulse worker；
- 增加 worker time limit；
- 开 official certificate gate；
- 简单增加 pricing time；
- 简单增加 profile-DP state cap；
- 简单调 label cap；
- 简单换 selection mode；
- 简单做 duplicate pool compression；
- 用 proof-closed resume 作为当前路线补丁。

这些方向要么已经被 A/B 证伪，要么没有正向干预证据。

## Exactness 边界

本报告只做根因审计，不改变 solver 行为。

保持：

- no production default change；
- no worker default；
- no certificate gate；
- no lower-bound rule change；
- no unsafe prefix/cut bound；
- no smoothed/GNN dual certificate；
- no critical disagreement。

## 验证

本轮报告依赖已完成的受控实验与回归：

- Phase 7O / 7P worker A/B；
- Phase 8Q passed-source ROI validation；
- Phase 9E RMP degeneracy / pool-pressure attribution；
- Phase 9L previous-anchor dual stabilization gate；
- Phase 10A profile-DP tail diagnostics；
- Phase 10B state-cap sensitivity；
- Phase 10F / 10G active-pool / early-column attribution；
- Phase 10H early-column controlled intervention；
- Phase 11A pricing-time sensitivity；
- Phase 11B selection-mode sensitivity；
- Phase 11C refinement audit；
- Phase 11D final negative-result / pivot。

本轮文档写入后需要运行：

```bash
git diff --check
```

以及文档相关代码路径的基础回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果待同步。

实际结果：

```text
git diff --check: passed
BPCFutureTests: Ran 483 tests in 47.833s OK (skipped=1)
目标文档同步后复跑:
git diff --check: passed
BPCFutureTests: Ran 483 tests in 1.482s OK (skipped=1)
```

## 最终判断

当前最有证据的根本原因是：

**20-task hard set 的求解质量由 early-column / active-family trajectory 强烈决定；当前机制没有能预测“哪条 early trajectory 对当前 context 有益”的选择器。**

这导致：

- 小规模不能默认启用额外机制，因为固定开销直接造成回退；
- 20-task 不能靠单一全局 profile 稳定优化，因为同一干预对不同 hard case 方向相反；
- cap/time/selection/worker 增强都只能扰动轨迹，不能稳定优化轨迹。

下一步若继续优化，最有证据的候选方向应围绕“识别并控制有益 early active-family trajectory”，而不是继续扩大 Pulse、pricing budget 或 selection knob。

但在这个方向没有通过 5/10 full gate、selected 20-task repeat A/B 和 exactness regression 前，不得宣称已经找到最终优化方向，也不得宣称目标完成。
