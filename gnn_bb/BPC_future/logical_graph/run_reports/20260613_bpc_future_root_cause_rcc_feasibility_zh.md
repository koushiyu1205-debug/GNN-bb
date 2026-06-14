# BPC_future 根因审计补充：RC-C 可表达性检查

日期：2026-06-13

## 目标

本轮继续根因审计，不做主线大修改。

上一轮 RC-B 已把当前最精确根因收紧为：

> 20-task 的改善 / 回退来自 context-sensitive early-column 到 RMP active-basis trajectory 的改写。

本轮检查一个更具体的问题：

> 现有 calibration/profile 机制能不能直接表达 RC-C：per-context active trajectory replay？

如果现有工具不能表达这个干预，那么“直接跑现有 profile 没收益”不能算 RC-C 方向失败，只能说明当前 profile 仍是粗粒度全局扰动。

## 检查范围

只读检查：

- `BPC_future/scripts/run_sharded_pulse_roi_calibration.py`
- `BPC_future/pricing/journey_pricing.py`
- `BPC_future/solver/journey_driver.py`

本轮没有改：

- solver；
- pricing；
- RMP；
- Sharded Pulse worker / audit；
- certificate / lower-bound 语义；
- 默认 benchmark 配置。

## 结论

当前现有 calibration/profile 不能直接表达 RC-C。

原因是：

1. calibration profile 只接收 `profile + task_count`，没有 instance/context 参数；
2. `experimental_early_new_task_set_quota_*` 只能设置全局 early-return quota、return limit 和 selection mode；
3. profile-DP early candidate selection 只支持 `reduced_cost / diverse / integer_diverse / orthogonal` 这类全局排序；
4. 现有 priority task-set 接口主要用于 harvest / direct-label / repair，不控制 ordinary profile-DP 的 early returned candidate order；
5. 现有接口没有办法指定：
   - 某个 instance；
   - 某个 CG context hash；
   - 某组 early task-set chain；
   - 某个 JourneyColumn signature / start-time / sortie composition；
   - 某个 active-basis trajectory replay target。

因此，当前已有 profile 只能“扰动轨迹”，不能“选择有益轨迹”。

这解释了为什么做了很多全局 knob 后仍然不稳定：

- 它们能改变 early-column / active-pool trajectory；
- 但不能根据当前 context 选择应该推哪组列；
- 所以同一类干预在 `tranq20_01` 可以改善，在 `mt20_greedy_tranq_01` 或 `mt20_greedy_apollo_01` 可能回退。

## 代码证据

### 1. `_apply_profile()` 只按 profile 和 task_count 分派

`run_sharded_pulse_roi_calibration.py` 中：

- `_apply_profile(config, profile, args, *, task_count=None)` 没有 `instance_name`、`context_hash`、`cg_iter` 或 active-basis 信息；
- 20-only gating 只判断 `task_count < 20`；
- early quota profiles 只调用 `_apply_early_new_task_set_quota_experiment_profile()`。

这说明 calibration profile 当前只能表达 scale-level / global profile，不支持 per-context replay。

### 2. early quota profile 是全局扰动

`_apply_early_new_task_set_quota_experiment_profile()` 只设置：

- `journey_pricing_early_return_new_task_set_min_count = 3`
- `journey_heuristic_early_return_new_task_set_min_count = 3`
- `journey_pricing_max_returned_journeys = 8 或 12`
- `journey_heuristic_max_returned_journeys = 8 或 12`
- `journey_pricing_selection_mode = diverse`
- `journey_heuristic_selection_mode = diverse`

它不指定具体 task-set、signature 或 active trajectory target。

因此 Phase 10H 的结果应解释为：

> early quota 是真实 trajectory 干预，但仍是全局粗粒度干预，不是 RC-C 的 per-context replay。

### 3. profile-DP candidate selection 没有 priority task-set 输入

`_solve_best_journey_profile_dp()` 的核心 candidate 选择参数是：

- `max_returned`
- `early_return_negative`
- `early_return_min_count`
- `selection_mode`
- duplicate / forbidden / dominated filters

其中 `_select_negative_journey_candidates()` 支持：

- default reduced-cost order；
- `diverse`；
- `integer_diverse`；
- `orthogonal`。

但它没有 `priority_task_sets` 或 `priority_signatures` 参数。

这意味着 ordinary profile-DP early return 不能被要求优先返回 RC-B 中识别出的某条具体 positive chain，例如：

- `tranq20_01` 的 task-1 anchored chain；
- `mt20_greedy_tranq_01` 中 return12 的具体 materialized journey set；
- `mt20_greedy_apollo_01` 中 `[5,10,18]` 与 `[4,14,18]` 的 concrete signature 差异。

### 4. priority task-set 接口存在，但不是这个路径

代码中确实存在 `priority_task_sets` / `min_priority_task_sets`：

- `journey_harvesting.py`
- direct-label diverse harvest；
- replacement repair；
- analytic-center worker priority；
- final-judge repair target。

但这些接口主要控制 harvest / repair / direct-label worker，不控制 ordinary profile-DP early returned candidate order。

这点很关键：

> “系统里有 priority_task_sets”不等于“RC-C 已可表达”。

RC-C 需要影响的是 early profile-DP / heuristic pricing 的 returned columns 和随后 RMP active path。

## 对根因判断的影响

本轮没有推翻前面结论，反而进一步解释了“为什么做了很多工作都不行”：

1. Pulse worker route 能安全加列，但没有稳定 ROI，因为它解决的是 hidden-negative discovery，不是 active trajectory selection。
2. profile-DP cap / label cap / pricing time / selection mode 都能扰动 trajectory，但没有 context-aware target，所以无法稳定选择好路径。
3. early new-task-set quota 能改 trajectory，但它只按全局 quota 选列；当同一 family 在不同 context 下方向相反时，这种全局扰动必然不稳定。
4. 当前缺的不是又一个更大的 worker，而是一个能在当前 context 下判断“哪些 early columns 应该被优先进入 pool / active path”的选择机制。

## 当前不能做的结论

不能说：

- RC-C 已经失败；
- early-column trajectory 方向没有价值；
- 只要继续调 `max_returned` / `selection_mode` 就能解决；
- priority task-set 现有接口已经足够；
- 可以打开 worker default 或 certificate gate。

更准确的说法是：

> 现有 profile 还不能直接验证 RC-C；它只能验证粗粒度 trajectory perturbation，而粗粒度扰动已被证明不稳定。

## 下一步最小可证方向

如果继续沿 root-cause 方向推进，下一步应是一个极窄、opt-in、calibration-only 的 RC-C 表达层，而不是主线大改。

最小需求：

1. calibration runner 能按 `instance_name + repeat/context` 应用 profile；
2. profile-DP early candidate selector 支持 test-only priority task-set 或 signature ordering；
3. priority 只能改变候选顺序 / return batch，不能改变 true-RC、certificate、branch/cut context；
4. 必须 20-only/no-op gate，5/10 默认不受影响；
5. 日志必须记录：
   - priority target；
   - target 是否 reachable；
   - target 是否 selected / materialized / returned；
   - returned 后 active basis 是否进入目标 path；
   - official result 是否改变；
   - critical disagreement 是否为 0。

第一批候选不应多：

- `tranq20_01`：task-1 anchored positive chain；
- `mt20_greedy_tranq_01`：return12 具体 journey set vs return8；
- `mt20_greedy_apollo_01`：`[5,10,18]` vs `[4,14,18]` 的 concrete signature / active path。

验收仍然必须严格：

- 5/10 no-op；
- no critical disagreement；
- 不产生 certificate / lower-bound effect；
- selected 20-task hard set 至少两个 context 重复改善；
- 若仍不稳定，停止 trajectory tuning，转向更底层 RMP formulation / active-family stabilization / legacy proof-tail 重构。

## 当前状态

目标尚未完成。

目前只证明了：

- 最有证据的根因是 active trajectory sensitivity；
- 现有全局 profile 不能直接表达 per-context replay；
- 继续扩大 Pulse worker / pricing budget / global selection knob 没有依据。

还没有证明：

- 某个优化方向能在 exactness 下同时做到 5/10 不退化；
- selected 20-task hard set 大幅加速；
- 该方向可以稳定复现。

因此不能宣称最终目标完成。

