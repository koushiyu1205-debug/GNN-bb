# Sharded Pulse Phase 8R Active-worker Negative-result / Pivot 报告

日期：2026-06-13

## 目标

本轮不写新算法，不扩大 worker budget，不打开 official certificate gate。

目标是把 Phase 7O-8Q 的连续证据收束为一个明确决策：

1. `current-context Pulse hidden-negative active worker` 是否还值得继续扩张；
2. 是否允许进入 production worker / official certificate gate；
3. 后续主线应转向哪里。

结论范围只覆盖 active-worker 子路线，不覆盖尚未完整验证的 proof-closed resume / parallel / production certificate proof engine。

## 结论

停止继续扩大 Pulse active-worker 主线。

当前证据已经足够说明：

- Pulse worker 可以安全加入 true-RC negative columns；
- 但这些 columns 没有稳定减少 residual pricing tail；
- 5/10 no-regression 主要来自 worker no-op gate，而不是 worker 正收益；
- 20-task selected smoke 没有形成稳定 wall-time / gap / primal / final-judge-tail 改善；
- target-specific source / shard / transition / arc-option priority 已进入过度特化，仍不能消除 `8,15,5` residual family；
- passed source `12,4,18` 可重复应用，但只产生 active-replacement column，follow-up residual 又回到 disjoint `8,15,5`。

因此：

- 不默认启用 Pulse worker；
- 不打开 official certificate gate；
- 不继续增加 worker time limit；
- 不继续叠 active-worker trigger / cooldown / target-ordering gates；
- 不把 20-task 单点可加列视为 production ROI。

## 证据链

### 1. Phase 7O-7P：worker 能加列，但 wall-time ROI 不稳定

原始 current probe 在 10/20 上能返回并加入 true-RC negative columns，但 5-task 无加列也引入明显 overhead。后续 delayed / low-cap / follow-up reserve / cooldown gates 能减少部分无效 probe，却没有稳定降低 wall time 或 completion-bound tail。

这说明 active worker 的安全接入成立，但不能直接 production 化。

### 2. Phase 7U-7Z：worker 后 residual tail 仍存在

pool / residual attribution 显示：

- worker 新列能进入 column pool 并改变 active support；
- 但 ordinary / exact pricing 后续仍返回 disjoint residual negatives；
- Apollo20 典型 residual family 反复为 `5,8,15` / `8,15,5`；
- 当前瓶颈不是单纯 duplicate task-set pool pressure。

关闭 stop-after-first-negative、关闭 no-ROI gate、扩大 coverage scan 都没有覆盖该 residual family。

### 3. Phase 7AA-7AG：target diagnostics 定位缺口，但没有转化成 ROI

诊断结果逐步排除了：

- leaf materialization mismatch；
- true-RC context mismatch；
- signature mismatch；
- first-task shard 完全未进入；
- next-task ordering 单点问题。

最后缺口收窄到 target path / arc-option / start-time family，但 target arc-option priority 仍没有覆盖 `8,15,5`，且在短预算下没有返回可加列。

因此继续为单个 residual family 写 active-worker ordering gate 不符合求解性能目标。

### 4. Phase 8A-8F：pivot diagnostics 不支持 pool duplicate 主线

ROI pivot classifier 和后续 attribution 显示主要信号是：

- `residual_disjoint_negative`；
- `profile_dp_state_cap` / profile-DP reachable mask 扩张；
- 部分 20-task 的 active fractional pressure。

但 active duplicate ratio 和 active avg journeys/task-set 不支持把简单 pool duplicate compression 作为第一主线。

### 5. Phase 8L-8Q：active residual target 仍无重复 ROI

Phase 8P 找到 passed source `12,4,18`，Phase 8Q 重复验证：

| profile | worker added | support-changing | follow-up residual | objective delta | ROI 判断 |
|---|---:|---:|---|---:|---|
| coverage target priority | 8 | 0 | `4,12,18` | `-204.152729` | changed inactive only |
| auto-active diagnostic | 1 | 1 | `5,8,15` | `-0.760334` | active replacement |
| validation diagnostic | 1 | 1 | `5,8,15` | `-0.760334` | active replacement |
| validation ROI gate | 0 | 0 | none | none | `max_cg_iter_exceeded` |

同一 passed source 可重复应用，但不能消除 residual tail。在 1.8s smoke 预算下，Apollo20 validation rows 的 primal 也没有优于 baseline。

## Final Requirement Audit

| 条件 | 当前状态 | 结论 |
|---|---|---|
| A：5/10 无回退且 20 明显改善 | 未满足 | 5/10 靠 gate no-op，20 没稳定改善 |
| B：连续 A/B 无改善 | active-worker 子路线满足 | 7O-8Q 多轮 A/B / source-search / validation 无稳定 ROI |
| B：worker 加列不降低 tail | active-worker 子路线满足 | follow-up residual tail 反复出现 |
| B：20-task 没明显改善 | active-worker 子路线满足 | no stable wall-time / primal / tail improvement |
| B：refinement/resume 无降低 incomplete | 未完全满足 | proof-closed resume 未实现；7J 只证明 refinement exactness |
| C：correctness blocker | 未发现 | no critical disagreement / no RC mismatch / no signature mismatch |

所以本轮不能宣布整个目标完成，也不能证明完整 Pulse proof 路线无 ROI。

但可以正式关闭 active-worker 扩张子路线，并把后续优化主线转出 worker stacking。

## Exactness 边界

本轮只新增报告和文档结论，不改变求解代码。

既有阶段继续保持：

- worker-added journeys 进入 RMP 前必须经过 true-RC 检查；
- Pulse incomplete / duplicate-only / empty-harvest / no-column 不产生 official lower bound；
- official certificate gate 仍关闭；
- default benchmark config 不启用 Pulse worker；
- source-search / ROI validation 仅为 opt-in calibration；
- no critical disagreement。

## Pivot 建议

下一步不应继续 Phase 7/8 的 active-worker gate stacking。

建议进入新的非 worker 主线，优先级：

1. `legacy/profile-DP proof-tail structural control`
   - 目标：解释 profile-DP broad reachable-mask expansion、ordinary-vs-profile candidate gap、residual task-set materialization差异；
   - 推荐 Phase 9A：ordinary heuristic 与 profile-DP residual candidate bridge / rough-vs-true RC ordering 诊断。

2. `RMP stabilization / active fractional degeneracy`
   - 目标：处理 active fractional pressure、弱 replacement 列移动 objective 后仍不消除 tail 的问题；
   - 当前不建议先做简单 duplicate compression，因为 active duplicate pressure 证据不足。

3. `proof-closed resume`
   - 只有在需要补齐最终条件 B 的 proof-route 证据时再做；
   - 不能把 resume 当作 active-worker ROI 修复手段。

## 验证

本轮无求解代码变更。Phase 8R 文档更新后已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_auto_residual_target_uses_prior_context \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 3 tests in 0.002s
OK
```

完整 `BPCFutureTests`：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 479 tests in 1.423s
OK (skipped=1)
```

diff whitespace 检查：

```bash
git diff --check
```

结果：通过。

## 结论

Phase 8R 正式给出 active-worker 子路线 negative result：

- 机制安全；
- 可加 true-RC negative columns；
- 但没有稳定 ROI；
- 不应继续扩大 active worker；
- 不应开启 production worker 或 certificate gate。

后续应转向 legacy/profile-DP proof-tail structural control 或 RMP stabilization，而不是继续为 Pulse worker 增加预算、gate 或 target-specific ordering。
