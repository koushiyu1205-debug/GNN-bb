# Sharded Pulse Phase 7O Full-profile ROI Gate 报告

日期：2026-06-12

## 目标

本轮补齐 Phase 7O 的字段完整 A/B gate，不继续扩大 worker budget，不开启 official certificate gate。

目标是回答：

1. Phase 7O 明列的 worker profiles 在 5/10/20 分层 gate 下是否有 ROI；
2. 当前最有希望的 `20-only + pre-heuristic + cooldown + leaf-stop` profile 是否保持 5/10 no-regression；
3. 20-task smoke 是否仍有真实加列 / primal / RMP movement 信号；
4. 是否存在 critical disagreement 或 certificate side effect。

## 运行矩阵

实例：

- 5-task：balanced 5 全量 20 个；
- 10-task：`Apollo10`、`tranq10_09`、`tranq10_04`、`tranq10_01`、`tranq10_06`、`apollo10_04`、`apollo10_09`；
- 20-task：`tranq20_01`、`mt20_greedy_apollo_01`、`mt20_greedy_tranq_01`。

profiles：

- `baseline`
- `audit_only`
- `strict_worker_previous_signal_only`
- `strict_worker_current_probe`
- `strict_worker_current_probe_support_aware`
- `strict_worker_current_probe_support_aware_low_budget`
- `strict_worker_current_probe_support_aware_mid_budget`
- `strict_worker_current_probe_support_aware_impact_filter`
- `strict_worker_current_probe_hard_tail_only`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown`

输出：

- `BPC_future/results/sharded_pulse_phase7o_full_profile_gate_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_full_profile_gate_20260612/summary.csv`
- `BPC_future/results/sharded_pulse_phase7o_full_profile_gate_20260612/logs/`

共 300 个 run，summary 字段完整，包含 Phase 7O 要求的 wall time、official result、worker、follow-up、critical disagreement 和 improvement class 字段。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_full_profile_gate_20260612 \
--instances phase7o_gate \
--profiles baseline audit_only strict_worker_previous_signal_only strict_worker_current_probe \
strict_worker_current_probe_support_aware strict_worker_current_probe_support_aware_low_budget \
strict_worker_current_probe_support_aware_mid_budget strict_worker_current_probe_support_aware_impact_filter \
strict_worker_current_probe_hard_tail_only strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown \
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

结果：

```text
Sharded Pulse calibration summary written: BPC_future/results/sharded_pulse_phase7o_full_profile_gate_20260612/summary.json
Sharded Pulse calibration CSV written: BPC_future/results/sharded_pulse_phase7o_full_profile_gate_20260612/summary.csv
```

字段检查：

```text
rows 300
missing keys {}
summary.csv lines 301
logs 300
```

## 结果摘要

### 5-task gate

| profile | n | avg wall | median wall | worker events | triggered | added | critical | class |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| baseline | 20 | 0.033721 | 0.025408 | 0 | 0 | 0 | 0 | baseline 20 |
| audit_only | 20 | 0.342638 | 0.341713 | 0 | 0 | 0 | 0 | 19 worsened |
| strict_worker_current_probe | 20 | 0.342177 | 0.340948 | 20 | 0 | 0 | 0 | 19 worsened |
| strict_worker_current_probe_support_aware_impact_filter | 20 | 0.343168 | 0.342898 | 20 | 0 | 0 | 0 | 19 worsened |
| strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown | 20 | 0.027400 | 0.025309 | 0 | 0 | 0 | 0 | 2 improved, 18 no_regression |

结论：

- 普通 audit/current-probe profiles 即使 worker 未触发，也会因 audit/skip/log path 明显拖慢 5-task；
- 这些 profiles 不能作为候选；
- `20-only + pre-heuristic + cooldown + leaf-stop` 在 5-task 完全不触发 worker，未产生 official change / mismatch / critical disagreement。

### 10-task gate

| profile | n | avg wall | median wall | worker events | triggered | added | new task-set | critical | class |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| baseline | 7 | 0.102558 | 0.101869 | 0 | 0 | 0 | 0 | 0 | baseline 7 |
| audit_only | 7 | 0.429770 | 0.427829 | 0 | 0 | 0 | 0 | 0 | 7 worsened |
| strict_worker_current_probe | 7 | 0.587733 | 0.552927 | 11 | 4 | 10 | 4 | 0 | 7 worsened |
| strict_worker_current_probe_support_aware_impact_filter | 7 | 0.586054 | 0.553181 | 11 | 4 | 6 | 4 | 0 | 7 worsened |
| strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown | 7 | 0.102557 | 0.101654 | 0 | 0 | 0 | 0 | 0 | 7 no_regression |

结论：

- current-probe 能在 10-task 加列，但短预算下 wall time 明显变差；
- impact filter 减少返回列数量，但没有解决 10-task wall-time ROI；
- 20-only delayed profile 完全跳过 10-task worker，保持 no-regression。

### 20-task gate

| profile | n | avg wall | median wall | worker events | triggered | added | new task-set | support-changing | critical | class |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| baseline | 3 | 0.192061 | 0.172191 | 0 | 0 | 0 | 0 | 0 | 0 | baseline 3 |
| strict_worker_current_probe | 3 | 0.718480 | 0.561295 | 5 | 1 | 4 | 2 | 1 | 0 | 1 improved, 2 worsened |
| strict_worker_current_probe_support_aware_impact_filter | 3 | 0.633842 | 0.560824 | 4 | 1 | 3 | 2 | 1 | 0 | 1 improved, 2 worsened |
| strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown | 3 | 0.206804 | 0.202359 | 1 | 1 | 1 | 1 | 0 | 0 | 1 improved, 2 no_regression |

Active row：

| instance | profile | wall | primal | added | new task-set | class | worker time | recursions | next RMP obj delta | next dual L1 delta |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| mt20_greedy_apollo_01 | delayed 20-only leaf-stop | 0.202359 | 1030.002361 | 1 | 1 | changed_inactive_only | 0.031042 | 115 | -31.551683 | 77.428681 |

结论：

- 宽 current-probe profiles 能加入更多列，但 wall overhead 过大；
- impact filter 能减少弱 replacement，但仍未解决 wall-time ROI；
- delayed 20-only leaf-stop profile 是目前最干净候选：5/10 不触发，20 上保留 1 个 new task-set 与 RMP movement；
- 但 20-task 平均 wall 仍从 0.192061 到 0.206804，不能解释为 wall-time speedup。

## Exactness 检查

本轮所有 profiles：

- `critical_disagreement_count = 0`；
- `objective_mismatch_vs_baseline = 0`；
- Pulse worker no-column / skip / incomplete 未产生 certificate；
- 所有 worker 影响都走正常 add-column path；
- `20-only` candidate 不改变 5/10 official result；
- default benchmark 仍未启用 sharded Pulse worker。

## 当前判断

Phase 7O 的完整 profile gate 给出更清楚的结论：

1. 普通 audit/current-probe profiles 不能作为 production candidate，因为 5/10 明显拖慢；
2. 10-task current-probe 的加列能力真实，但短预算下没有 ROI；
3. 20-task 上 current-probe / impact-filter 有 stronger column-quality signal，但开销仍过大；
4. `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown` 是当前唯一通过 5/10 no-regression gate 的候选；
5. 该候选在 `mt20_greedy_apollo_01` 有 new task-set / primal / RMP movement 信号，但仍未证明 wall-time ROI。

因此：

- 不能进入 Phase 7P production tuning；
- 不能默认启用 worker；
- 不能开启 official certificate gate；
- 不应扩大 worker time limit。

## 后续建议

下一步若继续 Sharded Pulse worker 路线，应围绕两个方向做窄改：

1. 继续降低 active shard 内部成本：
   - high-yield first-task / second-action ordering；
   - active row 的 task-set target fingerprint；
   - 更早的 impact-aware stop。
2. 改进 productivity gate：
   - 区分 `changed_inactive_only` 与 `active_new_task_set` / `active_replacement_task_set`；
   - 对 inactive-only new task-set 先记录 follow-up tail 影响，不盲目扩大 worker；
   - 若后续仍不能减少 legacy final judge tail，转向 RMP degeneracy / column-pool 管理。

当前仍不建议：

- resume；
- parallel；
- 20/100 A/B；
- cut/subset-row prefix bound；
- production default enable；
- official certificate effect。
