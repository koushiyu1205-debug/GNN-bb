# Sharded Pulse Phase 7O Delayed Low-cap 5/10 Gate 报告

日期：2026-06-12

## 目标

本轮继续 Phase 7O，目标是把上一轮 delayed current-probe 的正向信号推进到更接近 `目标.md` 的 5/10 no-regression gate。

本轮仍不做：

- 不默认启用 Sharded Pulse；
- 不做 official certificate gate；
- 不改 production solver 默认配置；
- 不扩大 worker time limit；
- 不把 Pulse incomplete / no-column / duplicate-only 证书化。

## 实现摘要

### 1. Reproducible instance groups

`run_sharded_pulse_roi_calibration.py` 新增 instance groups：

- `balanced5_all`
- `balanced10_all`
- `phase7o_5_gate`
- `phase7o_10_gate`
- `phase7o_20_smoke`
- `phase7o_gate`

其中：

- `phase7o_5_gate` 展开为 balanced dataset 中 20 个 5-task logical graphs；
- `phase7o_10_gate` 展开为 `目标.md` 指定的 7 个 10-task gate 实例；
- `phase7o_20_smoke` 展开为 3 个当前可用 20-task smoke 实例。

### 2. Candidate profile

新增 profile：

- `strict_worker_delayed_current_probe_impact_low_budget`

语义：

- 5-task：完全 no-op，不注入 Pulse audit/worker 配置；
- 10/20-task：只在 certificate-candidate context 进入；
- current probe time / recursion / max-columns 内置缩小；
- impact filter 开启，只保留 new task-set 或 active support-changing replacement；
- 所有返回列仍走 true-RC sanitize；
- no certificate / official lower-bound effect。

## 5/10 Gate Run

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_delayed_lowcap_5_10_gate_20260612 \
--instances phase7o_5_gate phase7o_10_gate \
--profiles baseline strict_worker_delayed_current_probe_impact \
--time-limit 4.0 \
--audit-time-limit 0.05 \
--worker-time-limit 0.05 \
--current-probe-time-limit 0.05 \
--pricing-time-limit 0.08 \
--max-cg-iterations 3 \
--audit-max-recursions 10000 \
--worker-max-recursions 10000 \
--current-probe-max-recursions 5000 \
--current-probe-min-tasks 10 \
--current-probe-min-remaining-time 0.0 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7o_delayed_lowcap_5_10_gate_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_delayed_lowcap_5_10_gate_20260612/summary.csv`

### 5-task gate

| metric | baseline | candidate |
|---|---:|---:|
| instances | 20 | 20 |
| status | 20 TIME_LIMIT | 20 TIME_LIMIT |
| avg wall time | 0.025109 | 0.024503 |
| max wall time | 0.033956 | 0.027225 |
| worker events | 0 | 0 |
| added columns | 0 | 0 |
| official changed | 0 | 0 |
| objective mismatch | 0 | 0 |
| critical disagreement | 0 | 0 |
| class | baseline | 1 improved, 19 no_regression |

结论：

- candidate profile 在 5-task 全量 balanced set 上没有 Pulse overhead；
- 这是当前 Sharded Pulse worker 路线第一次满足短预算 5-task no-regression gate。

### 10-task gate

| metric | baseline | candidate |
|---|---:|---:|
| instances | 7 | 7 |
| status | 7 TIME_LIMIT | 7 TIME_LIMIT |
| avg wall time | 0.102995 | 0.172349 |
| max wall time | 0.110595 | 0.291019 |
| worker added columns | 0 | 2 |
| official changed | 0 | 2 |
| objective mismatch | 0 | 0 |
| critical disagreement | 0 | 0 |
| class | baseline | 7 no_regression |

Active cases：

| instance | added | composition | objective delta | class |
|---|---:|---|---:|---|
| Apollo10 | 1 | support-changing replacement | -0.220167 | no_regression |
| tranq10_09 | 1 | new task-set | -8.209058 | no_regression |

Other specified 10-task instances did not add columns and remained no-regression:

- `tranq10_04`
- `tranq10_01`
- `tranq10_06`
- `apollo10_04`
- `apollo10_09`

## 20-task Smoke

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_delayed_lowcap_20_smoke_20260612 \
--instances phase7o_20_smoke \
--profiles baseline strict_worker_delayed_current_probe_impact \
--time-limit 4.0 \
--audit-time-limit 0.05 \
--worker-time-limit 0.05 \
--current-probe-time-limit 0.05 \
--pricing-time-limit 0.08 \
--max-cg-iterations 3 \
--audit-max-recursions 10000 \
--worker-max-recursions 10000 \
--current-probe-max-recursions 5000 \
--current-probe-min-tasks 10 \
--current-probe-min-remaining-time 0.0 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7o_delayed_lowcap_20_smoke_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_delayed_lowcap_20_smoke_20260612/summary.csv`

结果：

| instance | added | composition | objective delta | class |
|---|---:|---|---:|---|
| tranq20_01 | 0 | no worker | - | no_regression |
| mt20_greedy_tranq_01 | 0 | no worker | - | no_regression |
| mt20_greedy_apollo_01 | 2 | 2 new task-set | -31.551683 | worsened |

结论：

- 20-task 仍未达标；
- only active 20-task case 仍因 worker overhead classified `worsened`；
- 不能把当前 profile 推为 20-task improvement solution。

## Exactness 边界

- 本轮新增内容仅在 calibration script 中显式 opt-in；
- 5-task no-op gate 不修改 solver config；
- current probe 仍不是 certificate oracle；
- worker returned columns 仍走 true-RC sanitize；
- worker incomplete / no-column / duplicate-only 不会更新 official lower bound；
- no critical disagreement in all runs。

## Verification

语法和 focused tests：

```text
py_compile: OK
focused tests: OK
```

后续还需要跑完整 `BPCFutureTests` 和 `git diff --check` 作为本阶段收尾。

## 当前判断

候选方向比上一轮更强：

- 5-task full balanced set：短预算 no-regression；
- 10-task specified gate：短预算 no-regression，并保留两个 hidden-negative add-column signals；
- 20-task：仍未改善。

下一步：

1. 用 `strict_worker_delayed_current_probe_impact_low_budget` 复跑同一 gate，避免依赖命令行低 cap；
2. 针对 20-task active case 加更严格 ROI trigger 或 per-instance cooldown；
3. 如果 20-task 继续无 improvement，应按 `目标.md` 的 B 条件准备 negative-result path，而不是继续扩大 worker budget。
