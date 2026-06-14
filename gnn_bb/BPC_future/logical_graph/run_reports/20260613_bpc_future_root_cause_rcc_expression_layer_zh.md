# BPC_future 根因审计补充：RC-C 最小表达层

日期：2026-06-13

## 目标

本轮不是证明性能优化已经成立，而是补齐一个前置能力：

> 让 `per-context active trajectory replay` 至少可以被 calibration profile 显式表达。

上一份 RC-C 可表达性检查已经确认：现有 profile 只能做全局 early quota / selection 扰动，不能直接指定 context-specific early task-set chain。因此如果继续只跑旧 profile，无法证明或证伪 RC-C。

本轮只做极窄 opt-in 表达层，不做 production 默认启用。

## 实现摘要

### 1. profile-DP priority task-set ordering

`JourneyPricingConfig` 新增：

- `profile_priority_task_masks`
- `profile_priority_min_returned`

`_select_negative_journey_candidates()` 新增可选 `pricing_config` 参数。

当且仅当：

- `profile_priority_task_masks` 非空；
- `profile_priority_min_returned > 0`；
- 候选中存在匹配 priority mask；

选择器才会把匹配 priority mask 的 negative candidate 放到 returned batch 前部，然后用原有 selection mode 填充剩余名额。

默认空配置下行为不变。

该逻辑只改变 candidate return order，不改变：

- reduced cost 计算；
- materialization；
- true-RC filter；
- branch / cut context；
- certificate / lower-bound 判断；
- duplicate / forbidden 过滤语义。

### 2. driver config 映射

`_journey_pricing_config()` 新增显式配置映射：

- `journey_pricing_profile_priority_task_sets`
- `journey_pricing_profile_priority_min_returned`
- 对应 heuristic 前缀：
  - `journey_heuristic_profile_priority_task_sets`
  - `journey_heuristic_profile_priority_min_returned`

task-set 会按当前 instance 的 `data.tasks` 转成 profile-DP 内部 mask。不存在的 task 会导致该 task-set 被忽略。

### 3. calibration-only RC-C profile

`run_sharded_pulse_roi_calibration.py` 新增：

- profile: `experimental_rcc_tranq20_task1_chain_20_only`
- group: `phase_rcc_context_replay`

该 profile 严格受控：

- `task_count < 20` 时 no-op；
- `instance_name != "tranq20_01"` 时 no-op；
- 不启用 Sharded Pulse audit；
- 不启用 hidden-negative worker；
- 不启用 dual stabilization；
- 不产生 certificate / lower-bound effect。

对 `tranq20_01`，它设置上一轮 RC-B 中识别出的 task-1 anchored positive chain：

- `(1, 15, 20)`
- `(1, 13, 18)`
- `(1, 3, 6)`
- `(1, 3, 10)`
- `(1, 9, 15)`

并设置：

- `journey_pricing_profile_priority_min_returned = 3`
- `journey_heuristic_profile_priority_min_returned = 3`
- `max_returned_journeys = 12`
- selection mode 仍为 `diverse`

## Exactness 边界

本轮没有把 RC-C profile 接入任何 official certificate path。

Priority ordering 只在 negative candidates 已经存在时改变 returned batch 顺序；它不把 no-column / incomplete 变成 certificate，也不改变 true-RC 复算。

因此：

- `DUPLICATE_ONLY` 仍不能证书化；
- Pulse incomplete / empty / no-column 仍不影响 lower bound；
- profile-DP priority candidate 仍必须走既有 materialization 和 true-RC 过滤；
- 默认 benchmark 行为不变。

## 当前意义

这一步不是最终优化证据。

它只解决一个此前阻塞：

> 现有工具不能表达 RC-C，所以旧 profile 无法证明 / 证伪 per-context active trajectory replay。

现在可以开始做一个更干净的下一轮实验：

- baseline；
- `experimental_rcc_tranq20_task1_chain_20_only`；
- 只跑 `tranq20_01` 与 5/10 guard；
- 检查 early returned candidates 是否命中 priority chain；
- 检查 RMP active hash path 是否进入 RC-B 记录的有利 trajectory；
- 检查 official result、critical disagreement、wall time、primal/gap。

## 当前仍不能做的结论

不能说：

- RC-C 已证明有效；
- 20-task 已经可以稳定优化；
- 可以默认启用 priority selector；
- 可以放开到 5/10/20 production；
- 可以打开 certificate gate；
- 可以回到扩大 Pulse worker。

目前只能说：

> RC-C 的最小表达层已经具备，可以进入受控 A/B 验证。

## 验证

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_negative_journey_priority_selection_is_opt_in \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_pricing_config_maps_profile_priority_task_sets \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 4 tests in 0.003s
OK
```

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

## 下一步

下一步才是证据实验：

1. 先跑 5/10 guard，确认该 profile no-op；
2. 跑 `tranq20_01` baseline vs RC-C profile；
3. 检查 priority task-set 是否实际 returned / materialized / added；
4. 检查 active-basis trajectory 是否朝 RC-B 观察到的 positive path 迁移；
5. 如果没有收益，不能直接判 RC-C 失败，还要先看 target 是否真正命中；
6. 如果 target 命中但无收益，才说明这一条 positive-chain replay 不足。

目标仍未完成。

