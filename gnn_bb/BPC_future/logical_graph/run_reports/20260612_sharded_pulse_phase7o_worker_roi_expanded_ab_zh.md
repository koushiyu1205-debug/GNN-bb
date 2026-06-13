# Sharded Pulse Phase 7O Worker ROI Expanded A/B 报告

日期：2026-06-12

## 目标

本轮继续 Phase 7O：验证 current-context Pulse worker 加入的 true-RC negative columns 是否真的减少 legacy final judge tail，而不是只增加开销。

本轮不做：

- 不写新 Pulse 搜索算法；
- 不默认启用 Sharded Pulse；
- 不做 official certificate gate；
- 不改变 solver 默认 benchmark 配置；
- 不把 Pulse incomplete / no-column / duplicate-only 转成 official lower bound。

## 运行矩阵

实例：

- 5-task regression gate：
  - `apollo5`
  - `tranq5`
- 10-task regression / hard-tail gate：
  - `apollo10`
  - `tranq10_09`
  - `tranq10_04`
  - `tranq10_01`
  - `tranq10_06`
  - `apollo10_04`
  - `apollo10_09`
- 20-task smoke：
  - `tranq20_01`
  - `mt20_greedy_apollo_01`
  - `mt20_greedy_tranq_01`

Profiles：

- `baseline`
- `audit_only`
- `strict_worker_previous_signal_only`
- `strict_worker_current_probe`
- `strict_worker_current_probe_support_aware`
- `strict_worker_current_probe_support_aware_low_budget`
- `strict_worker_current_probe_support_aware_mid_budget`
- `strict_worker_current_probe_support_aware_impact_filter`
- `strict_worker_current_probe_hard_tail_only`

总计：

- 12 instances
- 9 profiles
- 108 summary rows

## 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_worker_roi_ab_expanded_20260612 \
--instances apollo5 tranq5 apollo10 tranq10_09 tranq10_04 tranq10_01 tranq10_06 apollo10_04 apollo10_09 tranq20_01 mt20_greedy_apollo_01 mt20_greedy_tranq_01 \
--profiles baseline audit_only strict_worker_previous_signal_only strict_worker_current_probe strict_worker_current_probe_support_aware strict_worker_current_probe_support_aware_low_budget strict_worker_current_probe_support_aware_mid_budget strict_worker_current_probe_support_aware_impact_filter strict_worker_current_probe_hard_tail_only \
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

- `BPC_future/results/sharded_pulse_phase7o_worker_roi_ab_expanded_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_worker_roi_ab_expanded_20260612/summary.csv`
- per-run JSONL logs under `BPC_future/results/sharded_pulse_phase7o_worker_roi_ab_expanded_20260612/logs/`

## Summary

### Exactness / safety

- `critical_disagreement_count=0` for all rows；
- 没有两个 `OPTIMAL` run 之间的 objective / dual mismatch；
- Pulse worker returned columns 仍走 driver 的 true-RC sanitize path；
- 所有 non-certificate Pulse outcomes 仍不产生 official lower bound；
- default config 未改变。

### 5-task no-regression

结果不达标。

观察：

- `apollo5` / `tranq5` worker 都被 gate 拦住；
- current-probe profiles skip reason 为 `current_probe_instance_too_small`；
- hard-tail-only skip reason 为 `instance_too_small`；
- 但 audit / skip logging 的固定开销在短 baseline 下仍明显；
- 所有 non-baseline profiles 在 conservative wall-time gate 下为 `worsened`。

结论：

- active worker 没有拖成加列错误；
- 但 audit/worker profile 仍不适合默认进入 5-task；
- 若要继续，必须对 5-task 默认完全关闭 audit/worker，而不仅是关闭 worker。

### 10-task no-regression / hard-tail signal

结果不达标。

正向信号：

| instance | profile family | added columns | new task sets | support-changing | next RMP objective delta |
|---|---:|---:|---:|---:|---:|
| Apollo10 | current probe | 2 | 0 | 1 | -0.220167 |
| tranq10_09 | current probe | 3-4 | 1 | 0-1 | -8.209058 |
| apollo10_04 | current probe | 3-4 | 3 | 0 | -56.782044 to -67.654841 |

负向信号：

- 所有 10-task non-baseline profiles 在 short-budget wall-time gate 下为 `worsened`；
- `strict_worker_previous_signal_only` 基本不触发；
- `strict_worker_current_probe_hard_tail_only` 无 previous audit negative signal 时不触发；
- 当前 probe 加列没有在本短 run 中减少 wall time / retry。

结论：

- current probe 确实能找到 hidden negative columns；
- impact/low-budget 能减少返回列数；
- 但还没有证明 tail ROI；
- 不能把 current probe worker 默认用于 10-task。

### 20-task improvement

结果不达标。

观察：

- `tranq20_01` 和 `mt20_greedy_tranq_01` 本短 run 下 worker 未触发，常见 skip reason 为 `not_certificate_candidate`；
- `mt20_greedy_apollo_01` current probe 能加列：
  - current probe：4 added；
  - low budget：2 added；
  - mid budget：5 added；
  - impact filter：3 added；
  - objective delta 约 `-38.98` 到 `-39.74`；
- 但所有 20-task profiles 仍为 `worsened`，没有 wall-time/gap improvement 证据。

结论：

- 20-task hidden-negative signal 存在，但只在一个 smoke 实例上出现；
- 当前证据不足以声称 20-task 改善；
- 不能进入 20-task production A/B 或 certificate gate。

## Profile-level 结论

| profile | 结论 |
|---|---|
| `audit_only` | 所有 scale 都有 overhead，无 wall-time ROI |
| `strict_worker_previous_signal_only` | 几乎不触发，仍有 audit overhead |
| `strict_worker_current_probe` | 能加列，但 overhead 更大 |
| `strict_worker_current_probe_support_aware` | 与 current probe 主体类似，未显示额外 ROI |
| `strict_worker_current_probe_support_aware_low_budget` | 返回列减少，overhead 下降一些，但仍 worsened |
| `strict_worker_current_probe_support_aware_mid_budget` | 返回列略多，overhead 更大 |
| `strict_worker_current_probe_support_aware_impact_filter` | 保留 new/support-changing signal，减少弱 replacement，但仍无 wall-time ROI |
| `strict_worker_current_probe_hard_tail_only` | 触发过少，当前矩阵主要是 skip overhead |

## ROI 判断

当前 Phase 7O expanded A/B 仍是 negative / diagnostic result：

- 5-task：不满足 no-regression；
- 10-task：有加列信号，但不满足 no-regression；
- 20-task：有单实例加列信号，但无 improvement；
- exactness：未发现 critical disagreement；
- default path：未污染。

因此不能：

- 默认启用 worker；
- 放开 official certificate gate；
- 增加 worker time limit 后继续硬推；
- 宣称性能提升已经达成。

## 下一步建议

如果继续 Sharded Pulse worker 主线，优先方向不应是增大 worker budget，而应是减少固定开销：

1. 对 5-task 默认完全关闭 audit/worker profile，而不是只靠 worker min-task gate；
2. 对 10/20 引入真正 delayed hard-tail trigger，避免每个 final-pricing 都 audit；
3. 只在已有 hard-tail fingerprint 后运行 current probe；
4. 保留 impact filter，因为它减少弱 replacement 且保留当前 RMP movement；
5. 下一轮若仍无 ROI，应按 `目标.md` 的 B 条件准备 negative-result report，并考虑转向 RMP stabilization / pool compression / legacy final judge optimization。

## Verification

本轮扩展矩阵运行前已通过：

```text
py_compile: OK
focused tests: Ran 3 tests in 0.001s OK
```

扩展矩阵运行后仍需继续执行最终 `py_compile`、focused/full regression 与 `git diff --check`，作为本阶段收尾验证。
