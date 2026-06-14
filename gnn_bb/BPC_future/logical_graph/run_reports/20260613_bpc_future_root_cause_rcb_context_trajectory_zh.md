# BPC_future Root-cause RC-B Context Trajectory Attribution 报告

日期：2026-06-13

## 目标

本轮继续根因审计，不做主线大修改。

上一份 early-family attribution 已证明：

- `tranq20_01` 上 early task-set family 与改善强相关；
- `mt20_greedy_tranq_01` 上同一 early task-set family 在 return8 / return12 下方向相反；
- `mt20_greedy_apollo_01` 没有 clean improved-only family。

因此本轮进一步检查：

**同一 early family 为什么会在不同 context 下改善或回退？**

本轮只读已有 JSONL：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/logs/*.jsonl`

抽取：

- `journey_column_addition`
- `journey_flat_weak_column_pressure`
- `journey_rmp`
- `journey_pool_structure_diagnostics`
- `incumbent`

不改 solver、pricing、RMP、worker、certificate 或 lower-bound。

## 结论

本轮把根因进一步收紧为：

**20-task 的改善/回退取决于 early additions 是否把 RMP active trajectory 推入“有利的 active basis path”，尤其是是否快速解除 fractional active pressure 或形成更好的 integer incumbent。**

这比“early task-set family”更精确：

- task-set family 是可观测信号；
- 但真正影响结果的是具体加入列集合、return quota、signature/hash、后续 RMP active basis 和 fractional pressure；
- 同一 family 可以因为 return quota 不同而产生相反 outcome。

## Case 1：`mt20_greedy_tranq_01` 证明 return quota / active basis 比 family 更关键

两个 profile 的 early primary sequence 完全一致：

```text
[3,4], [1,2,7], [4,19], [1,3]
```

但 outcome 相反：

- return8：三次 worsened，代表 r0 primal `829.395319`；
- return12：三次 improved，代表 r0 primal `704.228463`。

### return8 r0 轨迹

关键 JSONL：

- `mt20_greedy_tranq_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl`

轨迹：

```text
RMP cg1 objective = 800.402764
ADD cg1: added 8, new 8, best_rc -38.7838905
  samples: [3,4], [8,16], [13,16], [2,7,9], [6,8,13], [7,9,10], [8,10,13], [8,13,17]
RMP cg2 objective = 716.482817
POOL cg2 fractional_sum = 3.0

ADD cg2: added 8, new 6, best_rc -32.993153667
  samples: [2,7,10], [2,7,17], [2,10,17], [2,17,19], [7,10,17], [2,7,10,17]
RMP cg3 objective = 711.359117
POOL cg3 fractional_sum = 7.961538462

ADD cg3: added 8, new 5, best_rc -12.813296308
RMP cg4 objective = 697.800551
POOL cg4 fractional_sum = 7.75
```

解释：

- return8 能加列；
- RMP objective 下降；
- 但 active basis 很快进入高 fractional pressure；
- 没有形成稳定好的 incumbent；
- 最终仍是 worsened。

### return12 r0 轨迹

关键 JSONL：

- `mt20_greedy_tranq_01__experimental_early_new_task_set_quota_3_return12_20_only__r0.jsonl`

轨迹：

```text
RMP cg1 objective = 800.402764
ADD cg1: added 12, new 12, best_rc -38.7838905
  samples include: [3,4], [8,16], [13,16], [2,7,9], [6,8,13], [7,9,10], [7,9,17], [8,10,13]
RMP cg2 objective = 710.348212
POOL cg2 fractional_sum = 3.916666667

ADD cg2: added 12, new 8, best_rc -26.06958275
  samples include: [2,6,7], [2,6,10], [2,7,10], [2,7,17], [2,17,19], [6,7,10], [7,10,17], [2,7,10,17]
RMP cg3 objective = 704.228463
POOL cg3 fractional_sum = 0
  active top includes: [1,6,15], [2,5,19], [3,4], [7,9,10]
```

解释：

- return12 的 family 看起来和 return8 类似；
- 但它多加入了具体列；
- 到 cg3 时 active basis 变为 integral / fractional_sum=0；
- 这直接对应 improved incumbent `704.228463`。

判断：

`mt20_greedy_tranq_01` 的根因不是 early task-set family 本身，而是：

**return quota 改变具体列集合，具体列集合改变 active basis path，active basis path 决定 incumbent 改善还是回退。**

## Case 2：`mt20_greedy_apollo_01` 证明 signature / concrete journey 差异会改变 outcome

比较 return8 profile：

- r2 improved：primal `770.211317`
- r0 worsened：primal `1061.554044`

二者前两轮非常接近：

```text
cg1:
  added 8, new 8, hash 23e2d6c7dfcd631b
  sig b764a94bfbc6e661
  best_rc -139.913748
  samples: [4,5,8], [4,5,15], [4,8,15], [5,8,12], [5,8,15], [5,12,15], [5,15,18], [8,15,18]

cg2:
  added 8, new 8, hash ad399a8299c80f10
  sig 58603ae23ad95e60
  best_rc -123.353561
  samples: [3,12,17], [3,16,17], [4,12,14], [4,12,17], [12,13,17], [12,14,17], [12,16,17], [13,16,17]
```

差异从 cg3 开始出现。

### r2 improved

```text
ADD cg3:
  hash 772156774c9d6f38
  sig ce10940e649c88ce
  best_rc -20.1912655
  samples: [3,14,18], [4,8,14], [5,10,18], [5,12,18], [5,14,18], [10,14,18], [14,15,18]
RMP cg4 objective = 770.211317
POOL cg4 fractional_sum = 0
  active top includes: [1,9], [2,10,19], [3,6], [4,8,15]
```

### r0 worsened

```text
ADD cg3:
  hash 74b85de6210de2f6
  sig a0cff104367cbbc7
  best_rc -64.283449
  samples: [3,14,18], [4,8,14], [4,14,18], [5,12,18], [5,14,18], [10,14,18], [14,15,18]
RMP cg4 objective = 766.969656
POOL cg4 fractional_sum = 5.75
```

解释：

- r0 的 cg3 best_rc 更负，但 outcome 更差；
- r2 的 cg3 best_rc 没那么负，但包含 `[5,10,18]`，并在 cg4 形成 fractional_sum=0 的 active basis；
- r0 包含 `[4,14,18]`，cg4 仍有 high fractional pressure。

判断：

Apollo20 不能用“更负 RC”或“同一 family”解释。

更具体的根因是：

**具体 JourneyColumn signature / task-set replacement 在 RMP active trajectory 中的作用，比单个 rough/best RC 更重要。**

这也是为什么简单 selection mode、state cap、pricing time 都不稳定。

## Case 3：`tranq20_01` 的改善是 progressive active path 改写

代表：

- `tranq20_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl`
- final improved primal：`597.118613`

轨迹：

```text
cg1 add [1,15,20] family group
RMP cg2 objective = 781.101309
POOL cg2 fractional_sum = 0

cg2 add [1,13,18] family group
RMP cg3 objective = 727.595997
POOL cg3 fractional_sum = 4.5

cg3 add [1,3,6] family group
RMP cg4 objective = 683.581356
POOL cg4 fractional_sum = 0

cg4 add [1,3,10] family group
RMP cg5 objective = 632.554546
POOL cg5 fractional_sum = 3.5

cg7 add [1,9,15] family group
RMP cg8 objective = 597.118613
POOL cg8 fractional_sum = 0
```

解释：

- 改善不是单次列导致；
- 是一串 task-1 anchored groups 连续改变 active path；
- 多次进入 fractional_sum=0 的 integral active basis；
- 这解释了为什么该实例上 early family 信号很干净。

判断：

`tranq20_01` 是当前最适合做 per-context replay 的实例，因为它有明确 positive family chain。

## 根因更新

当前最精确的根因陈述：

> BPC_future 当前难以同时做到 5/10 不退化和 20 优化，是因为小规模不能承受任何默认额外搜索开销，而 20-task 的收益来自极其 context-sensitive 的 early-column 到 RMP active-basis 轨迹改写。这个轨迹不仅取决于 task-set family，还取决于 return quota、具体 JourneyColumn signature、加入顺序、RMP fractional pressure 和后续 pricing tail。现有全局 knob 只能扰动轨迹，不能稳定选择有益轨迹。

这解释了：

- 为什么 5/10 必须 no-op；
- 为什么 worker 能加列但不一定优化；
- 为什么 cap/time/selection 增强会混合改善和回退；
- 为什么同一 early family 在 return8 / return12 下结果相反；
- 为什么更负 RC 不一定带来更好 incumbent。

## 当前仍不能宣布的内容

不能宣布：

- 已经找到最终优化方案；
- 已经能大幅加速 20 最优解；
- early family whitelist 足够；
- best-RC-first 足够；
- return12 应默认启用；
- task-1 anchored family 应默认启用；
- 任何 production default change。

## 下一步最小 evidence phase

建议下一步不是大改，而是一个极窄 replay/intervention：

### RC-C：per-context active trajectory replay

目标：

1. `tranq20_01`：
   - 只在 calibration profile 中优先 task-1 anchored positive family chain；
   - 验证是否复现改善；
   - 检查 incomplete 是否不增加。
2. `mt20_greedy_tranq_01`：
   - 对比 return8 / return12 额外加入的具体 task-set 和 signature；
   - 尝试只补 return12 的关键 extra columns，而不是全局提高 return quota。
3. `mt20_greedy_apollo_01`：
   - 对比 improved r2 与 worsened r0 的 cg3 signature；
   - 验证 `[5,10,18]` vs `[4,14,18]` 这类 concrete difference 是否能解释 active fractional_sum=0 / 5.75 的分叉。

验收：

- calibration-only；
- 5/10 no-op；
- selected 20-task 不允许某个 hard case 明显回退；
- 至少两个 hard case repeat 改善；
- no critical disagreement；
- no certificate / lower-bound side effect。

如果 RC-C 无法通过，就说明当前 trajectory 方向仍不能成为最终优化方向，应转向更底层的 RMP formulation / active-family stabilization 或 legacy proof-tail 重构。

## Exactness 边界

本轮只读 JSONL 并写报告：

- 不改 solver；
- 不改 pricing；
- 不改 RMP；
- 不改 default config；
- 不启用 worker；
- 不启用 certificate；
- 不改 lower-bound。

## 验证

本轮报告写入后运行：

```bash
git diff --check
```

结果：

```text
git diff --check: passed
BPCFutureTests: Ran 483 tests in 1.445s OK (skipped=1)
```
