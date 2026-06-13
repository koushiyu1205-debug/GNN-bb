# Sharded Pulse Phase 7P Same-Iteration Worker Gate 报告

日期：2026-06-13

## 目标

本轮针对 Phase 7P 中发现的短预算退化做一个更直接的实验：

旧 active-gate 轨迹为：

```text
cg1 worker adds weak negative
cg2 heuristic finds strong negative
cg3 short-budget heuristic -> profile_dp_incomplete
```

这说明 pre-heuristic worker 加列后立即重解 RMP，会把本轮 heuristic 强负列推迟到下一轮，额外消耗一个 CG 轮次。

本轮目标是引入一个严格 opt-in 开关：

```text
worker adds column
then continue same CG iteration to heuristic pricing
then re-solve RMP once
```

只用于 ROI profile，不改变默认 benchmark。

## 实现摘要

### 1. Driver opt-in 开关

`journey_driver.py` 新增配置：

- `journey_sharded_pulse_hidden_negative_worker_continue_same_iteration_after_add`

默认 `False`。

仅在 pre-heuristic worker 加列后生效：

- `False`：保持旧行为，worker 加列后立即 `continue`，重解 RMP；
- `True`：记录事件 `journey_sharded_pulse_worker_continue_same_iteration`，继续同轮 heuristic pricing。

该开关只增加可行负列，同样通过原有 add-column path，不改变 official certificate / lower-bound 语义。

### 2. ROI profile

`run_sharded_pulse_roi_calibration.py` 新增 profile：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_active_gate`

该 profile：

- 20-only；
- opt-in；
- active-support continuation gate；
- pre-heuristic worker；
- stop-after-first-negative；
- impact filter；
- worker 加列后同轮继续 heuristic。

### 3. Summary 字段

新增：

- `worker_continue_same_iteration_events`
- `pulse_worker_continue_same_iteration_events`

## Single Smoke

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7p_same_iteration_single_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline \
             strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate \
             strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_active_gate \
  --time-limit 0.3 \
  --pricing-time-limit 0.12 \
  --pricing-max-dp-states 1000
```

关键结果：

| profile | worker added | same-iter event | official pricing | follow-up trajectory |
|---|---:|---:|---|---|
| baseline | 0 | 0 | `FOUND_NEGATIVE` | - |
| old active-gate | 1 | 0 | `INCOMPLETE_LIMIT` | negative -> incomplete |
| same-iter active-gate | 1 | 1 | `FOUND_NEGATIVE` | negative |

same-iter 详细轨迹：

```text
cg1 worker FOUND_NEGATIVE, add 1
cg1 heuristic FOUND_NEGATIVE, add 1
cg2 RMP objective_delta = -171.152010
cg2 heuristic FOUND_NEGATIVE, add 1
```

这验证了假设：同轮继续 heuristic 能避免旧 active-gate 的额外 CG 轮次和 terminal incomplete。

## Small Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7p_same_iteration_small_matrix_20260613 \
  --instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 mt20_greedy_tranq_01 tranq20_01 \
  --profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_active_gate \
  --time-limit 0.3 \
  --pricing-time-limit 0.12 \
  --pricing-max-dp-states 1000
```

聚合结果：

| scale | n | worker events | same-iter events | changed official rows | critical |
|---:|---:|---:|---:|---:|---:|
| 5 | 2 | 0 | 0 | 0 | 0 |
| 10 | 2 | 0 | 0 | 0 | 0 |
| 20 | 3 | 2 | 2 | 1 | 0 |

5/10 由于 20-only gate 没有触发 worker，未观察到回退。

20 中：

- `mt20_greedy_apollo_01`：official pricing 仍为 `FOUND_NEGATIVE`，不再 terminal incomplete，但 `best_rc` 与 baseline 不完全相同；
- `mt20_greedy_tranq_01`：worker 加 2 列，official result 与 baseline 一致；
- `tranq20_01`：worker 未触发或未改变 official result。

## 20-task 1s Smoke

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7p_same_iteration_20_smoke_1s_20260613 \
  --instances mt20_greedy_apollo_01 mt20_greedy_tranq_01 tranq20_01 \
  --profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_active_gate \
  --time-limit 1.0 \
  --pricing-time-limit 0.2 \
  --pricing-max-dp-states 5000
```

关键观测：

| instance | wall delta | primal change | worker added | terminal incomplete |
|---|---:|---:|---:|---:|
| `mt20_greedy_apollo_01` | `+0.040302` | `921.640296 -> 890.088613` | 1 | False |
| `mt20_greedy_tranq_01` | `-0.001476` | unchanged | 2 | False |
| `tranq20_01` | `+0.026366` | unchanged | 1 | False |

20 平均 wall：

```text
baseline    0.801352s
same-iter   0.823082s
delta      +0.021731s
```

解释：same-iteration 能避免 terminal incomplete，并在一个 20-task smoke 上改善 primal，但平均 wall 仍变慢。它不能作为最终 ROI 证据。

## 验证

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 2 tests in 0.001s
OK
```

## 当前边界

- 默认 benchmark 不变；
- same-iteration 仅 opt-in；
- 不影响 official certificate；
- worker returned journeys 仍走原有 true-RC negative add-column path；
- 未做 resume / parallel / official gate；
- 当前证据不足以说明 20-task wall time ROI 成立。

## 结论

same-iteration worker gate 是一个有价值的防退化修复：它解决了 pre-heuristic worker 把强 heuristic 列推迟一轮的问题。

但它还没有达到 `目标.md` 的最终交付标准：

- 5/10 no-regression 初步成立；
- 20 terminal incomplete 问题改善；
- 20 平均 wall 仍变慢；
- 只有一个 20 smoke 出现 primal 改善。

下一步不应扩大 worker budget。更合理的方向是把 same-iteration 与更严格 productivity gate 结合：

- worker 候选必须 new/support-changing；
- worker 加列后同轮 heuristic 必须仍可运行；
- 若 worker 返回 weak negative 且不能与 heuristic 同轮合并，则跳过 worker；
- 继续评估是否能在 20 上稳定带来 primal/gap 改善而不增加 wall。
