# BPC_future 根因审计补充：candidate-level contrast

日期：2026-06-13

## 目标

上一轮 pre-observable feature audit 把根因收紧到：

> 当前缺的是 candidate/signature 级别的事前 trajectory selector。

本轮继续只读检查一个更具体的问题：

**Apollo20 的好/坏 cg3 分叉，是因为有益 candidate 完全不存在，还是存在但没有被 materialized / returned？**

本轮不改 solver、pricing、RMP、Pulse worker、certificate 或 lower-bound。

## 数据

只读输入：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl`
- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl`

抽取事件：

- `journey_rmp`
- `journey_pool_structure_diagnostics`
- `journey_rmp_dual_diagnostics`
- `journey_pricing`
- `journey_column_addition`

## 关键对照：cg3 前 context 完全一致

`mt20_greedy_apollo_01` return8 r0 / r2 在 cg3 pricing 前一致：

| item | r0 worsened | r2 improved |
|---|---|---|
| cg1 RMP objective | `1061.554044` | `1061.554044` |
| cg1 active hash | `c6ea96127d7c5d7b` | `c6ea96127d7c5d7b` |
| cg1 dual hash | `7053153641b2ef79` | `7053153641b2ef79` |
| cg1 addition signature | `b764a94bfbc6e661` | `b764a94bfbc6e661` |
| cg1 addition task hash | `23e2d6c7dfcd631b` | `23e2d6c7dfcd631b` |
| cg2 RMP objective | `859.357131` | `859.357131` |
| cg2 active hash | `427b1308ea279e0c` | `427b1308ea279e0c` |
| cg2 dual hash | `cef33f774ab67d26` | `cef33f774ab67d26` |
| cg2 addition signature | `58603ae23ad95e60` | `58603ae23ad95e60` |
| cg2 addition task hash | `ad399a8299c80f10` | `ad399a8299c80f10` |
| cg3 RMP objective before pricing | `780.586496` | `780.586496` |
| cg3 active hash before pricing | `16862add48072518` | `16862add48072518` |
| cg3 dual hash before pricing | `350001260a512742` | `350001260a512742` |
| cg3 fractional sum before pricing | `7.0` | `7.0` |

因此，这不是“前两轮 trajectory 已经不同”导致的结果。

分叉发生在同一个 cg3 context 的 candidate / materialization / return 路径。

## cg3 r0：有益 family 出现，但没进入 returned batch

r0 最终 worsened，cg3 pricing：

```text
best_rc = -64.283449
negative_candidate_count = 86
selected_candidate_count = 16
returned_count = 8
return_limit_truncated_count = 8
```

关键样本：

- `diagnostic_negative_task_set_samples` 包含 `[4,14,18]` 和 `[5,10,18]`；
- `diagnostic_selected_task_set_samples` 也包含 `[4,14,18]` 和 `[5,10,18]`；
- 但 `diagnostic_selected_materialized_task_set_samples` 只包含 `[4,14,18]`，不包含 `[5,10,18]`；
- `diagnostic_selected_returned_task_set_samples` 也只包含 `[4,14,18]`，不包含 `[5,10,18]`。

r0 cg3 addition：

```text
signature = a0cff104367cbbc7
changed_task_set_samples include [4,14,18]
best_rc = -64.283449
```

后续：

```text
cg4 objective = 766.969656
cg4 fractional_sum = 5.75
no incumbent update
final outcome = worsened
```

解释：

`[5,10,18]` 并不是完全不可见。它已经出现在 negative/selected samples 中，但没有被扫到 materialized/returned 前 8，主要受 return-limit / selected scan 顺序影响。

## cg3 r2：较弱 RC 的 candidate 被返回，并走到好 trajectory

r2 最终 improved，cg3 pricing：

```text
best_rc = -20.1912655
negative_candidate_count = 78
selected_candidate_count = 14
returned_count = 8
return_limit_truncated_count = 6
```

关键样本：

- `diagnostic_negative_task_set_samples` 包含 `[5,10,18]`；
- `diagnostic_selected_task_set_samples` 包含 `[5,10,18]`；
- `diagnostic_selected_materialized_task_set_samples` 包含 `[5,10,18]`；
- `diagnostic_selected_returned_task_set_samples` 包含 `[5,10,18]`。

r2 cg3 addition：

```text
signature = ce10940e649c88ce
changed_task_set_samples include [5,10,18]
best_rc = -20.1912655
```

后续：

```text
cg4 objective = 770.211317
cg4 fractional_sum = 0
incumbent update exists
final outcome = improved
```

## 直接结论

这个对照很关键，因为它排除了几个错误解释：

1. **不是 `[5,10,18]` family 完全不在候选域。**
   - r0 cg3 negative/selected samples 已经包含 `[5,10,18]`。
2. **不是前两轮 RMP/dual context 不同。**
   - cg3 前 active hash、dual hash、objective 都一致。
3. **不是更负 RC 更好。**
   - r0 best RC `-64.283449`，但 worsened；
   - r2 best RC `-20.1912655`，但 improved。
4. **不是只要 selected 就够。**
   - r0 selected samples 包含 `[5,10,18]`，但没 materialized/returned。
5. **问题集中在 selected candidate scan / materialization / return cut 的排序与截断。**
   - r0 selected 16，只扫/返回 8；
   - `[5,10,18]` 落在 returned cut 外；
   - r2 中 `[5,10,18]` 进入 returned cut。

## 根因进一步收紧

当前最具体的根因层是：

> 在相同 RMP/dual context 下，profile-DP 已经能产生有益 family 的 negative/selected candidate，但当前 returned batch ordering 按 rough/best RC 与简单 diverse 规则截断，可能优先返回更负但 trajectory 更差的 signature，截掉较弱 RC 但能触发有利 active-basis path 的 candidate。

这解释了为什么前面很多尝试都不稳定：

- 提高 cap/time 只会产生更多 candidate，不保证 returned cut 选对；
- Pulse worker 找到负列，不保证这些负列是 active-trajectory 有益列；
- return12 有时有效，是因为它扩大 returned cut，偶尔把有益但不够靠前的 candidate 带进去；
- 但 return12 也会带入坏 trajectory，所以不能默认启用；
- priority whitelist 命中特定 family 不够，因为关键还在具体 signature / timing / scan order；
- 5/10 不能靠扩大 returned cut 解决，因为固定开销和额外列会回退。

## 为什么这仍不是优化方案

这轮证明了“问题在哪里”，但还没有证明“怎么安全优化”。

不能直接做：

- 默认增大 returned count；
- 默认 return12；
- best-RC 反向排序；
- 手写 `[5,10,18]` whitelist；
- 用后验 incumbent / zero-fractional 信号在线选择；
- 打开 official certificate gate。

原因：

- `[5,10,18]` 是 Apollo20 这个 context 的有益 family，不一定泛化；
- return12 在 `tranq20_01` 有效，但在 Apollo20 也有 worsened rows；
- r0/r2 的分叉证明需要 candidate/signature 级 selector，而不是粗 task-set selector；
- selector 必须用 addition 前可见特征，并经过 5/10 no-regression 与 20 hard set repeat 验证。

## 下一步建议

下一步应是 calibration-only，不是 production 改动：

1. 增强 candidate-level diagnostics，记录 returned cut 边界附近的 candidates：
   - top returned candidates；
   - first truncated candidates；
   - rough RC；
   - task set；
   - selected profile signature / timing摘要；
   - relation to active top task sets。
2. 专门复盘 Apollo cg3：
   - 为什么 `[4,14,18]` 排在 `[5,10,18]` 前面；
   - 两者 rough RC / true RC / profile timing / relation-to-active 有何差异；
   - 是否存在一个事前可见特征能偏向 `[5,10,18]` 而不伤害其他 cases。
3. 若能找到候选规则，先做 calibration-only A/B：
   - 5/10 no-op；
   - Apollo20 / Tranq20 / greedy hard set repeat；
   - no certificate effect；
   - no critical disagreement。

## 当前目标状态

目标仍未完成。

本轮把根因从“缺 active-basis trajectory selector”进一步定位为：

**当前 returned batch 的 candidate-level ordering / truncation 会在同一 RMP/dual context 下截掉有益 signature，返回更负但 trajectory 更差的 candidate。**

这是明确根因证据，但不是最终优化方向证明。

## 验证

本轮只读已有 JSONL，未改求解语义。

未运行新的 benchmark。
