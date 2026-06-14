# BPC_future 根因补充：exact-context replay capture 扩展尝试

日期：2026-06-13

## 目标

在不改变 production driver、certificate 或 official lower bound 的前提下，尝试把 `mt20_greedy_apollo_01` 之外的 20-task context 纳入 exact-context counterfactual replay 数据集。

本轮只做 diagnostic-only capture：

- capture event 仍要求 `certificate_capable=false`；
- capture event 仍要求 `official_bound_effect=false`；
- replay 只允许后续离线局部 RMP treatment，不允许影响求解路径；
- 不把 no-capture 结果当作 optimization proof。

## 工具补充

`BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 新增 opt-in 参数：

```bash
--counterfactual-replay-capture
--counterfactual-replay-capture-max-journeys
--counterfactual-replay-capture-pool-max-journeys
--counterfactual-replay-capture-log-empty
```

默认关闭。开启后只向 JSONL 写 `journey_counterfactual_replay_capture` 事件，复用 driver 内已有 no-certificate-effect capture contract。

新增 focused test：

```text
test_roi_calibration_counterfactual_replay_capture_is_opt_in
```

## 尝试 1：mt20_greedy_tranq_01

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_tranq_20260613 \
--instances mt20_greedy_tranq_01 \
--profiles strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority \
--time-limit 10 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1 \
--max-cg-iterations 3 \
--worker-time-limit 0.5 \
--current-probe-time-limit 0.5 \
--worker-max-recursions 100000 \
--current-probe-max-recursions 50000 \
--counterfactual-replay-capture \
--quiet
```

结果：

- status：`TIME_LIMIT`；
- official pricing state：`INCOMPLETE_LIMIT`；
- official best RC：`15.7995965`；
- pricing calls：`3`；
- legacy final judge calls：`2`；
- worker events：`0`；
- worker returned / added journeys：`0 / 0`；
- profile-DP tail class：`profile_dp_state_cap_tail`；
- capture events：`0`。

audit：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/audit_counterfactual_replay_capture.py \
BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_tranq_20260613/logs \
--output-dir BPC_future/results/root_cause_counterfactual_replay_real_capture_mt20_tranq_20260613/audit
```

`has_capture_events=false`，因此不能 build ready replay manifest。

## 尝试 2：tranq20_01

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/root_cause_counterfactual_replay_real_capture_tranq20_01_20260613 \
--instances tranq20_01 \
--profiles strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority \
--time-limit 10 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1 \
--max-cg-iterations 3 \
--worker-time-limit 0.5 \
--current-probe-time-limit 0.5 \
--worker-max-recursions 100000 \
--current-probe-max-recursions 50000 \
--counterfactual-replay-capture \
--quiet
```

结果：

- status：`TIME_LIMIT`；
- official pricing state：`INCOMPLETE_LIMIT`；
- official best RC：`26.8389145`；
- pricing calls：`3`；
- legacy final judge calls：`2`；
- worker events：`0`；
- worker returned / added journeys：`0 / 0`；
- profile-DP tail class：`profile_dp_state_cap_tail`；
- capture events：`0`。

audit：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/audit_counterfactual_replay_capture.py \
BPC_future/results/root_cause_counterfactual_replay_real_capture_tranq20_01_20260613/logs \
--output-dir BPC_future/results/root_cause_counterfactual_replay_real_capture_tranq20_01_20260613/audit
```

`has_capture_events=false`，因此不能 build ready replay manifest。

## 尝试 3：apollo20_01

命令同上，仅替换 instance 为 `apollo20_01`。

结果：

```text
ValueError: task 17 has no feasible single-task timed trip on the configured grid
```

该实例在当前 initial single-task timed-trip grid 下不可作为同类 capture 样本。

## 结论

本轮没有得到新的 ready replay case。

这不是 replay harness 的失败，而是说明：

1. `mt20_greedy_apollo_01` 中的 high-impact worker returned batch 不是稳定可复现的普遍事件；
2. 在 `mt20_greedy_tranq_01` 和 `tranq20_01` 的同 profile / 同小预算设置下，worker/current probe 没有触发，pricing 直接停在 `profile_dp_state_cap_tail` / `INCOMPLETE_LIMIT`；
3. 因此当前 exact-context replay 数据集扩展的主要瓶颈，是如何稳定产生 no-certificate-effect returned-batch capture，而不是 manifest/replay/impact-dataset 工具缺失；
4. 这进一步支持当前根因判断：有用 batch 存在，但还没有 addition-before、context-aware、可泛化、低开销的 selector 或触发机制。

## 对目标状态的影响

- 当前仍不能证明 production selector；
- 当前仍不能证明 5/10 不退化且 20 大幅加速；
- 下一步如果继续取证，应优先扩大 no-certificate-effect capture 样本来源，例如围绕已知 observational improved/worsened contexts 设计更直接的 returned-batch capture，而不是继续扩大 worker budget 或打开 certificate gate。
