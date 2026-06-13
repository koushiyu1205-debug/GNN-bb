# Sharded Pulse Phase 7P Hard-tail Fingerprint Gate 报告

日期：2026-06-13

## 目标

前几轮 `same-iteration`、`RC gate`、`follow-up reserve`、`failure cooldown` 都说明：

- Pulse worker 有时能加入 true-RC negative columns；
- 但 worker 触发过宽时会带来无效 current-context probe；
- 继续增加 worker budget 没有依据；
- official certificate gate 仍必须关闭。

本轮只做一个更便宜的 hard-tail fingerprint gate：

- current-context probe 只有在当前节点已有 flat certificate-candidate round 或 no-column round 时才允许；
- 该 gate 默认关闭，只通过 opt-in profile 启用；
- gate 只跳过 optional Pulse worker，不影响 ordinary pricing、RMP、final judge certificate。

## 实现摘要

### 1. 新增 hard-tail fingerprint helper

新增 helper：

```text
_journey_sharded_pulse_current_probe_hard_tail_fingerprint_allows()
```

新增配置：

```text
journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled
journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds
journey_sharded_pulse_worker_current_probe_min_no_column_rounds
```

规则：

- 默认关闭；
- 启用后，`certificate_flat_rounds` 或 `certificate_no_column_rounds` 任一达到阈值才允许 current probe；
- 未达到阈值时 skip reason：

```text
current_probe_hard_tail_fingerprint_missing
```

### 2. 修正 failure cooldown 覆盖缺口

上一轮 failure cooldown 已覆盖 duplicate-no-change，但 pre-heuristic worker 返回 empty journeys 时没有进入 cooldown。

本轮修正：

- pre-heuristic worker no-column / empty result 也会触发 failure cooldown；
- 成功加入 changed column 仍不触发 failure cooldown。

### 3. 新增 ROI profile

新增 calibration profile：

```text
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_hard_tail_fingerprint
```

该 profile 继承：

- 20-task gate；
- pre-heuristic worker；
- same-iteration continue；
- active-support continuation gate；
- `impact_filter_min_true_rc=-30.0`；
- `min_followup_time_after_add=0.4`；
- `failure_cooldown_rounds=2`；
- `current_probe_hard_tail_fingerprint_enabled=True`；
- `min_certificate_flat_rounds=1`；
- `min_no_column_rounds=1`。

## Focused Tests

新增/更新覆盖：

- helper 关闭时保持旧行为；
- helper 启用后 flat/no-column 任一达到阈值即可通过；
- fingerprint missing 时不调用 `price_journeys()`；
- profile registry 包含 hard-tail-fingerprint profile；
- profile opt-in 配置包含 fingerprint gate 和 failure cooldown。

验证：

```text
Ran 6 focused tests in 0.004s
OK
```

全量：

```text
Ran 466 tests in 1.418s
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
--output-dir BPC_future/results/sharded_pulse_phase7p_hard_tail_fingerprint_gate_20_smoke_1s_20260613 \
--instances mt20_greedy_apollo_01 mt20_greedy_tranq_01 tranq20_01 \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_hard_tail_fingerprint \
--time-limit 1.0 --pricing-time-limit 0.2 --pricing-max-dp-states 5000
```

结果摘要：

| profile | avg wall | worker triggered | worker added | changed |
|---|---:|---:|---:|---:|
| baseline | 0.806852 | 0 | 0 | 0 |
| failure cooldown | 0.821690 | 2 | 1 | 1 |
| hard-tail fingerprint | 0.816895 | 1 | 1 | 0 |

逐实例观察：

- `mt20_greedy_apollo_01`：hard-tail fingerprint 后 worker 仍触发并 added `1`，但 `followup_worker_changed_task_set_count=0`，primal 回到 baseline `921.640296`，丢失了 failure-cooldown profile 中的有效 RMP impact。
- `mt20_greedy_tranq_01`：hard-tail fingerprint 成功挡掉无效 current probe，worker triggered 从 `1` 降到 `0`。
- `tranq20_01`：worker 未触发，结果与 baseline 语义一致。

## 5/10/20 Short Matrix

命令摘要：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7p_hard_tail_fingerprint_gate_small_matrix_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 mt20_greedy_tranq_01 tranq20_01 \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_hard_tail_fingerprint \
--time-limit 0.3 --pricing-time-limit 0.12 --pricing-max-dp-states 1000
```

结果摘要：

| scale | profile | avg wall | worker triggered | worker added | changed |
|---:|---|---:|---:|---:|---:|
| 5 | baseline | 0.039263 | 0 | 0 | 0 |
| 5 | hard-tail fingerprint | 0.037477 | 0 | 0 | 0 |
| 10 | baseline | 0.298326 | 0 | 0 | 0 |
| 10 | hard-tail fingerprint | 0.297865 | 0 | 0 | 0 |
| 20 | baseline | 0.314410 | 0 | 0 | 0 |
| 20 | hard-tail fingerprint | 0.309350 | 0 | 0 | 0 |

短预算矩阵中，hard-tail fingerprint profile 没有触发 worker，因此：

- 5-task no-regression gate 保持；
- 10-task no-regression gate 保持；
- 20-task 没有真实 worker improvement 证据。

## Exactness 边界

- hard-tail fingerprint 只跳过 optional current-context probe；
- no-probe / no-column / incomplete 不会 certificate；
- worker 返回列仍需 true-RC negative；
- official lower bound 仍只来自 true-dual exact certificate；
- 默认 benchmark 不启用该 profile。

## 结论

hard-tail fingerprint gate 是 exact-safe 的，但不是好的 ROI 候选：

1. 它能挡掉 `mt20_greedy_tranq_01` 的无效 current probe；
2. 但也削弱了 `mt20_greedy_apollo_01` 的有效 worker impact；
3. 20-only 1s 平均 wall 仍高于 baseline；
4. 5/10 不触发 worker，只能说明 no-regression guard 生效，不能说明性能收益；
5. 20-task short matrix 没有 worker-triggered improvement。

因此本轮进一步支持一个负面判断：继续在 Pulse worker 上叠加触发 gate，已经很难得到稳定 ROI。下一步应停止扩大 active worker 主线，整理 negative-result evidence，并转向 RMP stabilization / pool compression / legacy final judge proof-tail optimization。
