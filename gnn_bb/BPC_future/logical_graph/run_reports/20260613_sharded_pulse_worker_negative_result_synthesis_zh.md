# Sharded Pulse Worker Negative-result Synthesis 报告

日期：2026-06-13

## 目标

本轮不继续写新算法，也不继续扩大 worker budget。

目标是汇总 Phase 7O / 7P 的 hard-tail worker ROI A/B 与后续 gate-stacking 证据，判断 `current-context Pulse hidden-negative worker` 这条 active worker 子路线是否值得继续推进。

结论限定在：

- active hidden-negative worker；
- current-context probe；
- impact filter / follow-up reserve / early CG / failure cooldown / hard-tail fingerprint 等 gate 组合；
- opt-in experimental profile。

这不是整个 Sharded Pulse proof 路线的最终 negative result，因为 proof-closed resume、正式 certificate gate、完整 20/100 proof engine 仍未作为生产路线验证。

## 结论

当前证据支持停止继续扩大 active worker gate-stacking。

原因：

1. worker 能安全加入 true-RC negative columns；
2. 小规模 5/10 no-regression 主要来自 gate 把 worker 关掉，而不是 worker 带来性能收益；
3. 20-task smoke 中 worker 有时改善 under-budget primal，但平均 wall time 没有稳定下降；
4. follow-up attribution 显示 worker 列可以进入 active support、移动 RMP objective，但 follow-up pricing tail 仍存在；
5. 后续 failure cooldown / hard-tail fingerprint gate 能减少部分无效 probe，但也会消掉原本有效的 `mt20_greedy_apollo_01` worker impact；
6. 没有证据显示 worker 加列稳定减少 legacy final judge tail、completion retry 或总 wall time。

因此：

- 不默认启用 worker；
- 不开启 official certificate gate；
- 不增加 worker time limit；
- 不继续堆更多 active worker gate；
- 下一步应转向 RMP stabilization / column pool compression / legacy proof-tail optimization，或者在需要最终 negative-result 交付时补齐 refinement/resume 无 ROI 证据。

## 关键证据

### 1. Phase 7O expanded A/B：worker 会加列，但 wall time 明显变差

结果目录：

`BPC_future/results/sharded_pulse_phase7o_worker_roi_ab_expanded_20260612/summary.json`

| scale | profile | avg wall | worker events | added | new task-set | support-changing |
|---:|---|---:|---:|---:|---:|---:|
| 5 | baseline | 0.028776 | 0 | 0 | 0 | 0 |
| 5 | strict current probe | 0.362103 | 2 | 0 | 0 | 0 |
| 10 | baseline | 0.102410 | 0 | 0 | 0 | 0 |
| 10 | strict current probe | 0.614190 | 11 | 10 | 4 | 2 |
| 20 | baseline | 0.191645 | 0 | 0 | 0 | 0 |
| 20 | strict current probe | 0.764784 | 5 | 4 | 2 | 1 |

解释：

- current probe 能产生真实可加列；
- 但在 5/10/20 都显著增加 wall time；
- 5-task worker 即使没有加列，也会产生明显 overhead；
- 这证明 active worker 不能默认打开。

### 2. Delayed low-cap gate：保护 5-task，但 10/20 仍无稳定 ROI

结果目录：

- `BPC_future/results/sharded_pulse_phase7o_delayed_lowcap_5_10_gate_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_delayed_lowcap_20_smoke_20260612/summary.json`

| scale | profile | avg wall | worker events | added | new task-set | support-changing |
|---:|---|---:|---:|---:|---:|---:|
| 5 | baseline | 0.025109 | 0 | 0 | 0 | 0 |
| 5 | delayed impact | 0.024503 | 0 | 0 | 0 | 0 |
| 10 | baseline | 0.102995 | 0 | 0 | 0 | 0 |
| 10 | delayed impact | 0.172349 | 6 | 2 | 1 | 1 |
| 20 | baseline | 0.192558 | 0 | 0 | 0 | 0 |
| 20 | delayed impact | 0.309870 | 3 | 2 | 2 | 0 |

解释：

- min-task / delayed gate 能保护 5-task；
- 但 10-task 仍被拖慢；
- 20-task 有新增 task-set，但平均 wall time 上升；
- 加列本身不等于 tail ROI。

### 3. Follow-up reserve / early CG / failure cooldown：安全但仍不形成 wall-time ROI

代表结果：

- `BPC_future/results/sharded_pulse_phase7p_followup_reserve_gate_20_smoke_1s_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7p_early_cg_gate_20_smoke_1s_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7p_failure_cooldown_gate_20_smoke_1s_20260613/summary.json`

| profile | avg wall | worker events | added | new task-set | 备注 |
|---|---:|---:|---:|---:|---|
| baseline | 约 0.806-0.810 | 0 | 0 | 0 | 1s 20-task smoke |
| follow-up reserve | 约 0.827-0.828 | 2-3 | 1-2 | 1-2 | 有 primal 改善，但平均 wall 上升 |
| early CG | 0.818963 | 1 | 1 | 1 | 减少 worker 次数但仍慢于 baseline |
| failure cooldown | 0.817907 | 2 | 1 | 1 | 减少 no-change probe，不形成 ROI |

单例信号：

- `mt20_greedy_apollo_01` 在部分 profile 中 primal 可从 `921.640296` 改到 `890.088613`；
- 但该收益伴随额外 worker/follow-up 成本；
- 平均 wall time 没有下降；
- `mt20_greedy_tranq_01` 上 worker 常触发但没有可加列，或被 impact filter 丢弃。

### 4. Hard-tail fingerprint gate：减少无效 probe，但也丢掉有效 impact

结果目录：

- `BPC_future/results/sharded_pulse_phase7p_hard_tail_fingerprint_gate_20_smoke_1s_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7p_hard_tail_fingerprint_gate_small_matrix_20260613/summary.json`

| profile | avg wall | worker events | added | changed |
|---|---:|---:|---:|---:|
| baseline | 0.806852 | 0 | 0 | 0 |
| failure cooldown | 0.821690 | 2 | 1 | 1 |
| hard-tail fingerprint | 0.816895 | 1 | 1 | 0 |

解释：

- fingerprint gate 减少了一个无效 current probe；
- 但它也使 `mt20_greedy_apollo_01` 的有效 worker impact 消失，primal 回到 baseline；
- 5/10/20 short matrix 中 worker events 都是 0，说明 no-regression 主要来自 worker 被 gate 关闭；
- 该 gate 是安全 guard，不是 production ROI 候选。

## Exactness 边界

本轮 synthesis 不改变代码路径。

已有阶段结果共同保持：

- worker returned journeys 进入 RMP 前必须经过 true-RC 检查；
- worker no-column / incomplete / duplicate-only / empty harvest 不产生 certificate；
- Pulse worker 不设置 official `dual_bound`；
- official certificate gate 仍关闭；
- default benchmark config 不启用 worker；
- 5/10 no-regression gate 不能通过牺牲 exactness 或减少 proof 达成。

## ROI 判断

当前 active worker 子路线不满足继续生产化条件。

已观察到的正向信号：

- Pulse 能找到 true-RC negative columns；
- 部分列是 new task-set；
- 部分列可进入 active support；
- 部分单例 under-budget primal 改善。

但缺失的核心 ROI：

- 没有稳定降低 wall time；
- 没有稳定减少 legacy final judge / completion-bound retry；
- follow-up pricing tail 仍存在；
- gate 越严格，越容易把有效 worker impact 一起过滤掉；
- gate 放松，则 5/10 或 20 平均 wall overhead 过高。

因此不能从这些结果推出：

- worker 应默认启用；
- worker 应获得更大预算；
- worker 可以作为 official certificate gate 的前置信号。

## 下一步建议

建议停止 active worker gate-stacking，转向以下之一：

1. `RMP stabilization / pool compression`：
   - 重点处理 replacement-tail、退化、列池污染、弱 replacement 反复进出；
   - 目标是让已找到的负列更容易产生稳定 objective / dual movement。

2. `legacy proof-tail optimization`：
   - 继续定位 follow-up `INCOMPLETE_LIMIT` / proof-tail；
   - 优先 profile direct-label / completion-bound tail，而不是增加 Pulse worker budget。

3. `formal negative-result completion`：
   - 若要满足目标文档的最终条件 B，还需要补齐 refinement/resume 无 ROI 证据；
   - 当前报告只证明 active hidden-negative worker gate-stacking 子路线不值得继续扩大。

## 验证

本轮只新增报告和计划文档摘要，不改求解代码。

复用的最新代码验证记录：

- Phase 7P failure-cooldown：`BPCFutureTests Ran 464 tests OK (skipped=1)`；
- Phase 7P hard-tail fingerprint：`BPCFutureTests Ran 466 tests OK (skipped=1)`；
- `py_compile` 和 `git diff --check` 在对应阶段通过。

本轮文档编辑后已运行：

```bash
git diff --check
```

结果：通过。

## 结论

Phase 7N/7O/7P 证明了 Pulse current-context worker 的安全接入价值，但没有证明稳定 ROI。

更具体地说：

- 它能找列；
- 它能安全加列；
- 它有时改善单例 primal；
- 但它没有稳定减少 hard-tail wall time；
- 继续加 gate 只是把触发变少，并不能解决 follow-up proof-tail。

所以当前应停止 active worker 子路线扩展，保留其为实验性诊断/找列工具，把优化主线转向 RMP 退化、列池质量和 legacy final judge proof-tail。
