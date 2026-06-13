# Sharded Pulse Phase 7AH Active-worker Closure Audit 报告

日期：2026-06-13

## 目标

本轮不写新算法，不扩大 worker budget，不打开 official certificate gate。

目标是基于当前 worktree 和已有 `summary.json` 证据，复核 Phase 7O 到 Phase 7AG 的 active hidden-negative worker / gate-stacking / target diagnostic 结果，判断这条子路线是否还值得继续推进。

结论范围：

- 仅覆盖 `current-context Pulse hidden-negative worker` 与后续 active-worker gate / ordering / target diagnostic 子路线；
- 不覆盖尚未实现的 proof-closed resume；
- 不覆盖 production-grade official certificate gate；
- 不覆盖完整 20/100 proof engine。

## Evidence Sources

本轮直接读取以下结果目录：

- `BPC_future/results/sharded_pulse_phase7o_worker_roi_ab_expanded_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_delayed_lowcap_5_10_gate_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_delayed_lowcap_20_smoke_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7p_failure_cooldown_gate_20_smoke_1s_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7z_worker_no_roi_gate_coverage_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7ag_target_arc_option_priority_20260613/summary.json`

同时参考 Phase 7J / 7U-7AG 的 run reports。

## 关键证据

### 1. 原始 current-probe worker 会加列，但 wall-time 明显劣化

`phase7o_worker_roi_ab_expanded`：

| scale | profile | avg wall | avg worker events | avg added |
|---:|---|---:|---:|---:|
| 5 | baseline | 0.028776 | 0.000 | 0.000 |
| 5 | strict_worker_current_probe | 0.362103 | 1.000 | 0.000 |
| 10 | baseline | 0.102410 | 0.000 | 0.000 |
| 10 | strict_worker_current_probe | 0.614190 | 1.571 | 1.429 |
| 20 | baseline | 0.191645 | 0.000 | 0.000 |
| 20 | strict_worker_current_probe | 0.764784 | 1.667 | 1.333 |

解释：

- worker 能在 10/20 找到并加入 true-RC negative columns；
- 但 5-task 没有加列也引入明显 overhead；
- 10/20 平均 wall time 也显著高于 baseline；
- 这已经排除“直接启用 active worker”的生产化可能。

### 2. Delayed / low-cap gate 能保护 5-task，但 10/20 仍无稳定 ROI

`phase7o_delayed_lowcap_5_10_gate`：

| scale | profile | n | avg wall | avg worker events | avg added |
|---:|---|---:|---:|---:|---:|
| 5 | baseline | 20 | 0.025109 | 0.000 | 0.000 |
| 5 | delayed impact | 20 | 0.024503 | 0.000 | 0.000 |
| 10 | baseline | 7 | 0.102995 | 0.000 | 0.000 |
| 10 | delayed impact | 7 | 0.172349 | 0.857 | 0.286 |

`phase7o_delayed_lowcap_20_smoke`：

- `mt20_greedy_apollo_01`：worker 加 2 列，primal 改善，但 wall `0.153375 -> 0.503120`；
- `tranq20_01` / `mt20_greedy_tranq_01`：没有形成稳定收益。

解释：

- gate 可以把小快 5-task 关掉；
- 但 10-task 仍被拖慢；
- 20-task 有单例 primal signal，但不是 wall-time ROI。

### 3. Follow-up reserve / failure cooldown 仍不形成稳定 wall-time ROI

`phase7p_failure_cooldown_gate_20_smoke_1s`：

| profile | avg wall | avg worker events | avg added | avg new task-set |
|---|---:|---:|---:|---:|
| baseline | 0.806675 | 0.000 | 0.000 | 0.000 |
| follow-up reserve | 0.821722 | 0.667 | 0.333 | 0.333 |
| failure cooldown | 0.817907 | 0.667 | 0.333 | 0.333 |

解释：

- cooldown / reserve 能减少一部分无效 probe；
- 但平均 wall time 仍高于 baseline；
- 它们是安全 guard，不是生产 ROI 候选。

### 4. Coverage scan / no-ROI gate 没覆盖 residual negative family

`phase7z_worker_no_roi_gate_coverage` on `mt20_greedy_apollo_01`：

| profile | wall | worker returned / added | follow-up first negative | relation |
|---|---:|---:|---|---|
| baseline | 1.261945 | 0 / 0 | none | no_worker_add |
| coverage scan | 0.921510 | 2 / 2 | `5,8,15` | disjoint_task_set |
| coverage no-ROI-gate | 0.907832 | 1 / 1 | `5,8,15` | disjoint_task_set |

解释：

- 关闭 `stop_after_first_negative` 或关闭 shard ROI gate 都没有覆盖 ordinary follow-up 的 `[5,8,15]`；
- worker 加列后 residual negative tail 仍然存在；
- coverage 缺口不是单个 gate 的问题。

### 5. Target diagnostics 逐步定位缺口，但没有转化为 ROI

Phase 7AA-7AB：

- worker negative：`[6,19]`；
- ordinary follow-up first residual negative：`[8,15,5]`；
- residual replay 能用 Phase 3A materialization 回放 `[8,15,5]`；
- RC delta = `0.0`，signature mismatch = `0`。

Phase 7AC-7AF：

- target first-task priority 能进入 shard `8`；
- target transition priority 能推进到 prefix `[8,15]`；
- path diagnostics 显示 reached prefix 用了 `0->8:low_risk:2`；
- residual replay 可行 signature 用 `0->8:low_time:0`。

Phase 7AG：

| profile | target prefix | blocked | worker returned / added |
|---|---:|---|---:|
| target path diagnostic | 2 | `time_window` at `[8,15] -> 5` | 4 / 4 |
| target arc-option priority | 1 | `deadline` | 0 / 0 |
| target arc-option priority, 1.0s budget | 1 | `deadline` | 0 / 0 |

解释：

- target arc-option priority 接线有效，能把 `0->8` 改为 `low_time:0`；
- 但没有覆盖 `[8,15,5]`，也没有返回可加列；
- 继续叠 target-specific active-worker gate 不是有希望的优化路线。

### 6. Refinement 证据只支持 exactness，不支持 ROI 完成

Phase 7J 已证明：

- second-action child partition exact-safe；
- parent `REFINED` 后不当 proof-closed；
- child incomplete 阻断 certificate；
- child negative 正确传播；
- stress smoke 中 refined child certified 数量上升。

但 Phase 7J 也明确：

- driver-level audit smoke 没触发有效 refinement 场景；
- 未做 resume / parallel；
- 不是 20/100 A/B；
- 不能证明 refinement/resume 降低了 production incomplete。

因此 refinement 证据足以保证语义安全，但不足以满足最终条件 B 的 `refinement/resume 无降低 incomplete` 这一完整证明项。

## Closure Decision

当前证据足以关闭以下子路线：

1. 继续扩大 `current-context Pulse hidden-negative worker` 时间预算；
2. 继续叠加 active-worker trigger / cooldown / follow-up reserve gate；
3. 继续为 `[8,15,5]` 写 target-specific worker ordering gate；
4. 基于 active worker 打开 official certificate gate；
5. 默认启用 Pulse worker。

原因：

- 连续多轮 A/B 没有稳定 wall-time ROI；
- worker 加列没有稳定降低 follow-up residual negative tail；
- coverage scan / no-ROI gate / target ordering 诊断都没有修复 residual family 缺口；
- 5-task/10-task no-regression 主要靠 gate 关闭 worker，而不是 worker 带来收益；
- target diagnostics 已经进入过度特化，继续推进会偏离求解性能目标。

## Final Requirement Audit

对 `目标.md` 最终交付条件的当前状态：

| 条件 | 当前状态 | 证据 |
|---|---|---|
| A：5/10 无回退且 20 明显改善 | 未满足 | worker profiles 无稳定 wall-time ROI；5/10 需要 gate 关闭 worker |
| B：连续 A/B 无改善 | active-worker 子路线满足 | 7O/7P/7Z/7AG 多轮结果 |
| B：worker 加列不降低 tail | active-worker 子路线满足 | 7U-7AG residual attribution / target diagnostics |
| B：refinement/resume 无降低 incomplete | 未完全满足 | 7J 只证明 refinement exactness；resume 未实现为 proof route |
| B：20-task 没明显改善 | active-worker 子路线满足 | 7O/7P/7AG 无稳定 wall-time ROI |
| C：correctness blocker | 未发现 | no critical disagreement / no RC mismatch / no signature mismatch |

所以不能把整个目标标记为完成。

但可以把 active-worker 子路线正式停止，转向更可能影响最终目标的方向。

## 下一步建议

不要继续 Phase 7 系列的 active worker gate stacking。

下一步建议进入新的主线：

1. `RMP stabilization / pool compression`
   - 目标：减少 replacement-tail 和列池退化；
   - 依据：worker 能加列但 residual negative tail 仍 disjoint，说明单纯找更多列无法稳定收敛。

2. `legacy final judge proof-tail optimization`
   - 目标：降低 completion-bound / direct-label tail；
   - 依据：active Pulse worker 未能替代或减少 tail。

3. `formal proof route`
   - 只有在确实要完成最终条件 B 的 proof 子项时，再做 proof-closed resume；
   - 但当前没有证据表明 resume 会改善 active worker ROI。

## 验证

本轮没有修改求解代码。

运行：

```bash
git diff --check
```

结果：通过。

## 结论

Phase 7AH 的结论是：

`current-context Pulse hidden-negative active worker` 这条子路线安全，但当前没有稳定 ROI，应停止继续扩大。

这不是整个 Sharded Pulse proof 路线的最终否定，也不是目标完成声明；它是一个工程决策边界：不要再为 active worker 增加 gate、budget 或 target-specific ordering。后续应转向 RMP / pool / legacy proof-tail，或者单独实现 proof-closed resume 来补齐最终条件 B 的剩余证据。
