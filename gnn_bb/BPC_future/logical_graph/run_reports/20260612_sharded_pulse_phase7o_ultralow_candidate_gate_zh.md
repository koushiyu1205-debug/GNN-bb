# Sharded Pulse Phase 7O Ultra-low Candidate Gate 报告

日期：2026-06-12

## 目标

本轮目标是把 delayed current-probe impact 进一步收紧成一个可复现候选 profile，并用更接近 `目标.md` 的 gate 验证：

- 5-task full balanced set no-regression；
- 10-task specified gate no-regression；
- 20-task smoke 是否出现 improvement signal；
- 全程保持 exactness，不改变默认 solver 配置。

## 实现摘要

### 1. Instance groups

`run_sharded_pulse_roi_calibration.py` 新增：

- `balanced5_all`
- `balanced10_all`
- `phase7o_5_gate`
- `phase7o_10_gate`
- `phase7o_20_smoke`
- `phase7o_gate`

这些 group 只用于 calibration script，便于可复现运行 5/10/20 gate。

### 2. Ultra-low candidate profile

新增：

- `strict_worker_delayed_current_probe_impact_low_budget`
- `strict_worker_delayed_current_probe_impact_ultra_low_budget`

其中 ultra-low profile：

- 5-task 直接 no-op；
- 10/20 只在 certificate-candidate context 中运行；
- audit trigger = `on_certificate_candidate`；
- `force_on_root=False`；
- current probe time / recursion / max-columns 更严格缩小；
- impact filter 仍开启；
- worker 只返回 true-RC negative columns；
- 不产生 certificate / official lower-bound side effect。

## Gate Run

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_delayed_ultralow_profile_gate_20260612 \
--instances phase7o_gate \
--profiles baseline strict_worker_delayed_current_probe_impact_ultra_low_budget \
--time-limit 4.0 \
--audit-time-limit 0.15 \
--worker-time-limit 0.15 \
--current-probe-time-limit 0.15 \
--pricing-time-limit 0.08 \
--max-cg-iterations 3 \
--audit-max-recursions 30000 \
--worker-max-recursions 30000 \
--current-probe-max-recursions 15000 \
--current-probe-min-tasks 10 \
--current-probe-min-remaining-time 0.0 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7o_delayed_ultralow_profile_gate_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_delayed_ultralow_profile_gate_20260612/summary.csv`

## Gate 结果

### 5-task full gate

| metric | baseline | ultra-low candidate |
|---|---:|---:|
| instances | 20 | 20 |
| status | 20 TIME_LIMIT | 20 TIME_LIMIT |
| avg wall time | 0.025147 | 0.024757 |
| max wall time | 0.034793 | 0.028858 |
| worker events | 0 | 0 |
| worker added | 0 | 0 |
| official changed | 0 | 0 |
| objective mismatch | 0 | 0 |
| critical disagreement | 0 | 0 |
| class | baseline | 1 improved, 19 no_regression |

结论：5-task full balanced set 在本短预算 gate 下通过 no-regression。

### 10-task specified gate

| metric | baseline | ultra-low candidate |
|---|---:|---:|
| instances | 7 | 7 |
| status | 7 TIME_LIMIT | 7 TIME_LIMIT |
| avg wall time | 0.102563 | 0.145029 |
| max wall time | 0.111724 | 0.231908 |
| worker events | 0 | 6 |
| worker added | 0 | 2 |
| official changed | 0 | 2 |
| objective mismatch | 0 | 0 |
| critical disagreement | 0 | 0 |
| class | baseline | 7 no_regression |

Active rows：

| instance | worker result | objective delta | class |
|---|---|---:|---|
| Apollo10 | added 1 support-changing replacement | -0.220167 | no_regression |
| tranq10_09 | added 1 new task-set | -8.209058 | no_regression |
| apollo10_04 | triggered, returned 0 | - | no_regression |
| apollo10_09 | triggered, returned 0 | - | no_regression |

结论：10-task specified gate 在本短预算下通过 no-regression，并保留两个 hidden-negative add-column signals。

### 20-task smoke

| metric | baseline | ultra-low candidate |
|---|---:|---:|
| instances | 3 | 3 |
| status | 3 TIME_LIMIT | 3 TIME_LIMIT |
| avg wall time | 0.192096 | 0.198374 |
| max wall time | 0.251263 | 0.249119 |
| worker events | 0 | 1 |
| worker added | 0 | 0 |
| official changed | 0 | 0 |
| critical disagreement | 0 | 0 |
| class | baseline | 3 no_regression |

结论：ultra-low profile 对 20-task smoke 不回退，但也没有 improvement。

## 20-task Longer Signal Smoke

为了确认 20-task 是否至少有 solution-quality signal，额外运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_20_longer_signal_smoke_20260612 \
--instances phase7o_20_smoke \
--profiles baseline strict_worker_delayed_current_probe_impact_low_budget strict_worker_delayed_current_probe_impact \
--time-limit 8.0 \
--audit-time-limit 0.15 \
--worker-time-limit 0.15 \
--current-probe-time-limit 0.15 \
--pricing-time-limit 0.15 \
--max-cg-iterations 6 \
--audit-max-recursions 30000 \
--worker-max-recursions 30000 \
--current-probe-max-recursions 15000 \
--current-probe-min-tasks 10 \
--current-probe-min-remaining-time 0.0 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7o_20_longer_signal_smoke_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_20_longer_signal_smoke_20260612/summary.csv`

观察：

| instance | profile | primal | wall time | added | class |
|---|---|---:|---:|---:|---|
| mt20_greedy_apollo_01 | baseline | 1061.554044 | 0.212456 | 0 | baseline |
| mt20_greedy_apollo_01 | delayed impact low-budget | 1022.575388 | 0.683411 | 2 | worsened |
| mt20_greedy_apollo_01 | delayed impact | 1021.815054 | 0.692277 | 3 | worsened |

解释：

- `mt20_greedy_apollo_01` 有 primal / column-quality signal；
- 但 wall time 明显增加，因此仍不能算 20-task improvement success；
- `tranq20_01` 和 `mt20_greedy_tranq_01` 没有变化。

## Exactness 边界

- 本轮只改 calibration script；
- default benchmark 行为不变；
- Pulse worker no-column / incomplete / duplicate-only 不产生 official bound；
- returned columns 仍经过 true-RC sanitize；
- no critical disagreement；
- no objective mismatch between two `OPTIMAL` runs。

## 当前判断

当前最强候选是：

- `strict_worker_delayed_current_probe_impact_ultra_low_budget`

它满足：

- 5-task full gate no-regression；
- 10-task specified gate no-regression；
- 10-task 保留两个 add-column signals；
- 20-task smoke no-regression。

它尚未满足：

- 20-task selected hard set 明显 improvement；
- tail retry / final judge time 明确下降；
- wall-time ROI。

下一步建议：

1. 不要默认启用；
2. 不要做 official certificate gate；
3. 若继续 Pulse worker，围绕 20-task solution-quality signal 做 ROI-aware trigger / post-addition productivity gate；
4. 若下一轮 20-task 仍无 wall-time/gap improvement，应准备 negative-result report，转向 RMP stabilization / pool compression / legacy final judge optimization。
