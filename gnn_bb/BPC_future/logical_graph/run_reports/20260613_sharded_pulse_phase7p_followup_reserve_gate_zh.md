# Sharded Pulse Phase 7P Follow-up Reserve Gate 报告

日期：2026-06-13

## 目标

上一轮 `same-iteration + RC gate` 说明：

- worker 可筛掉 weak true-RC 列；
- 但仍会出现 worker 加列后没有足够 follow-up pricing/RMP 空间的样本；
- 这种样本不会破坏 exactness，但会消耗时间，且 ROI 不稳定。

本轮目标是增加一个更保守的 follow-up reserve gate：

- 若 worker 调用前剩余时间不足以保留后续 pricing/RMP 空间，直接跳过 worker；
- 若 worker 调用后才发现剩余 follow-up 时间不足，则把 worker 输出降级为 `INCOMPLETE_LIMIT`，不返回列；
- 该 gate 只影响 optional Pulse worker 列，不影响 official certificate / lower bound。

## 实现摘要

### 1. 新增 opt-in 配置

新增配置：

```text
journey_sharded_pulse_hidden_negative_worker_min_followup_time_after_add
```

规则：

- 默认 `0.0`，等价于关闭；
- 必须非负；
- 若调用前 `remaining_time <= min_followup_time_after_add`，worker 直接跳过；
- 若调用后 `remaining_after_worker < min_followup_time_after_add` 且已有 worker journeys，则清空 journeys 并返回 `INCOMPLETE_LIMIT`；
- 降级 reason：

```text
sharded_pulse_hidden_negative_worker_followup_reserve
```

该状态不可能成为 global certificate。

### 2. 新增 ROI profile

新增 calibration profile：

```text
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_followup_reserve
```

该 profile 继承：

- 20-task gate；
- pre-heuristic worker；
- same-iteration continue；
- active-support continuation gate；
- `impact_filter_min_true_rc=-30.0`；
- `min_followup_time_after_add=0.4`。

### 3. 日志与 summary 字段

新增 worker payload / summary 字段：

- `pulse_worker_followup_reserve_min_time`
- `pulse_worker_followup_reserve_remaining_time`
- `pulse_worker_followup_reserve_dropped_journeys`

## Focused Tests

新增/更新覆盖：

- profile 注册和 summary 字段注册；
- profile 配置中 20-task 才启用，且 follow-up reserve 为 `0.4`；
- 短预算时 worker 在调用前跳过，不调用 `price_journeys()`；
- 已有 worker 候选但 follow-up 时间不足时，helper 将其降级为 `INCOMPLETE_LIMIT`，不证书。

验证：

```text
Ran 4 focused tests in 0.007s
OK
```

全量：

```text
Ran 462 tests in 1.409s
OK (skipped=1)
```

语法与 diff 检查：

```text
py_compile: passed
git diff --check: passed
```

## 20-only 1s Smoke

命令摘要：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7p_followup_reserve04_skip_gate_20_smoke_1s_20260613 \
--instances mt20_greedy_apollo_01 mt20_greedy_tranq_01 tranq20_01 \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_followup_reserve \
--time-limit 1.0 --pricing-time-limit 0.2 --pricing-max-dp-states 5000
```

结果摘要：

| profile | avg wall | worker triggered | worker added | reserve dropped | changed |
|---|---:|---:|---:|---:|---:|
| baseline | 0.806430 | 0 | 0 | 0 | 0 |
| RC + follow-up reserve | 0.827313 | 2 | 1 | 0 | 1 |

逐实例观察：

- `mt20_greedy_apollo_01`：保留 worker 列，primal 从 `921.640296` 改善到 `890.088613`，但 wall 高于 baseline。
- `mt20_greedy_tranq_01`：RC gate 筛掉 2 个弱列，无 worker 加列。
- `tranq20_01`：调用前 follow-up reserve gate 使 worker 不触发，避免上一轮“加列但无 follow-up pricing”的路径。

## 5/10/20 Short Matrix

命令摘要：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7p_followup_reserve04_skip_gate_small_matrix_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 mt20_greedy_tranq_01 tranq20_01 \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_followup_reserve \
--time-limit 0.3 --pricing-time-limit 0.12 --pricing-max-dp-states 1000
```

结果摘要：

| scale | profile | avg wall | worker triggered | worker added | changed |
|---:|---|---:|---:|---:|---:|
| 5 | baseline | 0.038943 | 0 | 0 | 0 |
| 5 | reserve gate | 0.037806 | 0 | 0 | 0 |
| 10 | baseline | 0.297743 | 0 | 0 | 0 |
| 10 | reserve gate | 0.298152 | 0 | 0 | 0 |
| 20 | baseline | 0.308741 | 0 | 0 | 0 |
| 20 | reserve gate | 0.309722 | 0 | 0 | 0 |

短预算下 reserve gate 没有触发 worker，因此避免了上一版“先跑 worker 再降级导致 terminal incomplete”的额外开销。5/10 仍无 worker 触发。

## Exactness 边界

- 该 gate 只过滤 optional Pulse worker 输出；
- 跳过 worker 或降级 worker 输出不会更新 official lower bound；
- `INCOMPLETE_LIMIT` / empty worker output 仍不是 certificate；
- 返回给 RMP 的 worker columns 仍需逐条 true-RC negative；
- 默认 benchmark 不启用该 profile。

## 结论

follow-up reserve gate 修掉了一个真实工程问题：短预算或 late-tail worker 不再为了“找到但来不及利用”的列消耗求解时间。

但 ROI 结论仍然不够好：

1. 20-only 1s 中，`mt20_greedy_apollo_01` 有 primal 改善，但 wall 仍高于 baseline；
2. `tranq20_01` 的 late worker 已被挡掉，但整体平均 wall 仍未优于 baseline；
3. 5/10 no-regression gate 继续成立；
4. 当前仍不能默认启用 worker，也不能进入 official certificate gate。

下一步不应继续单纯增加 worker budget。更合理的方向是：

- 继续收紧 worker trigger，只在历史上真正产生 follow-up objective/gap 改善的 fingerprint 下启用；
- 或转向 RMP/列池退化治理，降低 replacement-tail；
- official certificate gate 仍然暂停。
