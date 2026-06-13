# Sharded Pulse Phase 7P Failure-Cooldown Worker Gate 报告

日期：2026-06-13

## 目标

前几轮结果显示：

- Pulse hidden-negative worker 能在部分 20-task hard-ish 样本中加入 true-RC negative columns；
- 但 worker 加列并没有稳定转化为 wall-time ROI；
- late / no-column / impact-filter-empty worker 仍会产生额外开销。

本轮只做一个 exact-safe 的 opt-in 收紧：

- 当 optional Pulse worker 没有产生可加入 changed column 时，后续若干 CG round 冷却；
- 不增加 worker 搜索预算；
- 不影响 official certificate / lower bound；
- 不改变默认 benchmark 行为。

## 实现摘要

### 1. 新增 failure cooldown 配置

新增配置：

```text
journey_sharded_pulse_hidden_negative_worker_failure_cooldown_rounds
```

规则：

- 默认 `0`，等价于关闭；
- 必须非负；
- worker 返回 no-column / incomplete / empty / duplicate-no-change 时，可触发 cooldown；
- worker 真实加入 changed column 时不触发 failure cooldown；
- cooldown skip reason：

```text
failure_cooldown
```

原有 success / inactive-support cooldown 仍保留，skip reason 仍为：

```text
success_cooldown
```

### 2. 新增 ROI profile

新增 calibration profile：

```text
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown
```

该 profile 继承：

- 20-task gate；
- pre-heuristic worker；
- same-iteration continue；
- active-support continuation gate；
- `impact_filter_min_true_rc=-30.0`；
- `min_followup_time_after_add=0.4`；
- `failure_cooldown_rounds=2`。

## Focused Tests

新增/更新覆盖：

- failure cooldown 仅在 no-column / no-changed-column 后触发；
- changed worker column 不触发 failure cooldown；
- 默认关闭时 failure cooldown 为 `0`；
- profile registry 包含 failure-cooldown profile；
- profile opt-in 配置包含 20-task gate、RC gate、follow-up reserve 和 failure cooldown。

验证：

```text
Ran 5 focused tests in 0.004s
OK
```

全量：

```text
Ran 464 tests in 1.409s
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
--output-dir BPC_future/results/sharded_pulse_phase7p_failure_cooldown_gate_20_smoke_1s_20260613 \
--instances mt20_greedy_apollo_01 mt20_greedy_tranq_01 tranq20_01 \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_followup_reserve strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown \
--time-limit 1.0 --pricing-time-limit 0.2 --pricing-max-dp-states 5000
```

结果摘要：

| profile | avg wall | worker triggered | worker added | changed |
|---|---:|---:|---:|---:|
| baseline | 0.806675 | 0 | 0 | 0 |
| RC + follow-up reserve | 0.821722 | 2 | 1 | 1 |
| failure cooldown | 0.817907 | 2 | 1 | 1 |

逐实例观察：

- `mt20_greedy_apollo_01`：failure-cooldown profile 保留有效 worker 列，primal 从 baseline `921.640296` 改善到 `890.088613`，wall 为 `0.782414`，仍高于 baseline `0.772266`。
- `mt20_greedy_tranq_01`：worker 触发但没有加列，`pulse_worker_impact_filter_dropped_count=2`，说明仍有无效 current-probe 调用。
- `tranq20_01`：worker 未触发；primal 改善属于短跑轨迹差异，不是 worker 直接导致。

## 5/10/20 Short Matrix

命令摘要：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7p_failure_cooldown_gate_small_matrix_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 mt20_greedy_tranq_01 tranq20_01 \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown \
--time-limit 0.3 --pricing-time-limit 0.12 --pricing-max-dp-states 1000
```

结果摘要：

| scale | profile | avg wall | worker triggered | worker added | changed |
|---:|---|---:|---:|---:|---:|
| 5 | baseline | 0.038171 | 0 | 0 | 0 |
| 5 | failure cooldown | 0.036492 | 0 | 0 | 0 |
| 10 | baseline | 0.298526 | 0 | 0 | 0 |
| 10 | failure cooldown | 0.298138 | 0 | 0 | 0 |
| 20 | baseline | 0.308354 | 0 | 0 | 0 |
| 20 | failure cooldown | 0.309443 | 0 | 0 | 0 |

短预算矩阵中：

- 5-task 没有 worker 触发；
- 10-task 没有 worker 触发；
- 20-task 短预算也没有 worker 触发；
- official result 没有因 Pulse worker 发生 semantic 改变。

## Exactness 边界

- failure cooldown 只跳过 optional worker；
- worker no-column / incomplete / duplicate-no-change 不会 certificate；
- worker 返回列仍必须逐条 true-RC negative；
- official lower bound 仍只来自 true-dual exact certificate；
- 默认 benchmark 不启用该 profile。

## 结论

failure cooldown 是安全的工程收紧：它能防止 no-column / no-change worker 在后续 round 重复消耗预算，并且不会挡掉已经成功加入 changed column 的 worker。

但本轮 ROI 仍未达标：

1. 20-only 1s 中，failure-cooldown profile 平均 wall 仍高于 baseline；
2. `mt20_greedy_apollo_01` 的 primal 改善仍伴随额外 wall time；
3. `mt20_greedy_tranq_01` 仍存在触发 worker 但 impact filter 清空的无效调用；
4. 5/10 guard 生效，但这只是 no-regression 证据，不是 20-task improvement 证据。

因此当前仍不能默认启用 worker，也不能进入 official certificate gate。

下一步应停止单纯叠加 worker gate，转向更直接的无效 probe 避免策略，例如在 current-context probe 前做更便宜的 hard-tail fingerprint / profile-DP incomplete 信号判断；如果后续两轮 A/B 仍无 20-task improvement，应按目标文档进入 negative-result report，并建议转向 RMP stabilization / pool compression / legacy final judge optimization。
