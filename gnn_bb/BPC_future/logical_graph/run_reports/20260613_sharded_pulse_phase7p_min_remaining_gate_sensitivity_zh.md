# Sharded Pulse Phase 7P Min-Remaining Gate Sensitivity 报告

日期：2026-06-13

## 目标

本轮不扩大 worker，也不做 certificate gate。

目标是验证：在短预算下，较高的 current-probe / worker min-remaining gate 能否避免 Phase 7P 中观察到的“worker 加列后 terminal incomplete”回退。

## 实现摘要

### 1. 新增 opt-in calibration profile

`run_sharded_pulse_roi_calibration.py` 新增 profile：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_deep_reserve_active_gate`

该 profile：

- 仍是 20-only；
- 仍是 opt-in；
- 仍使用 active-support continuation gate；
- 将 worker post-call reserve 从 `0.08` 提到 `0.16`；
- 不改变默认 benchmark。

### 2. 新增 follow-up trajectory 字段

同一轮中还补充了 worker follow-up trajectory 诊断：

- `followup_pricing_state_sequence`
- `followup_first_negative_cg_iter`
- `followup_first_negative_pricing_kind`
- `followup_first_negative_best_rc`
- `followup_terminal_after_negative_incomplete`
- `followup_last_pricing_time_limit`
- `followup_last_pricing_max_dp_states`
- `followup_last_pricing_profile_dp_time`
- `followup_last_pricing_dp_state_count`

这些字段只用于 ROI 后处理，不改变求解行为。

## Deep Reserve Single Smoke

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7p_deep_reserve_single_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline \
             strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate \
             strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_deep_reserve_active_gate \
  --time-limit 0.3 \
  --pricing-time-limit 0.12 \
  --pricing-max-dp-states 1000
```

结果：

| profile | worker events | worker added | official pricing | trajectory |
|---|---:|---:|---|---|
| baseline | 0 | 0 | `FOUND_NEGATIVE` | - |
| reserve active-gate | 1 | 1 | `INCOMPLETE_LIMIT` | negative -> incomplete |
| deep-reserve active-gate | 1 | 1 | `INCOMPLETE_LIMIT` | negative -> incomplete |

解释：单纯提高 post-call reserve 到 `0.16` 没有阻止 worker 触发，也没有避免 terminal incomplete。

## Min-Remaining Sensitivity

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7p_min_remaining_gate_small_matrix_20260613 \
  --instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 \
  --profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate \
  --time-limit 0.3 \
  --pricing-time-limit 0.12 \
  --pricing-max-dp-states 1000 \
  --current-probe-min-remaining-time 0.28
```

结果：

| scale | instances | worker events | official changed vs baseline | critical disagreement |
|---:|---:|---:|---:|---:|
| 5 | 2 | 0 | 0 | 0 |
| 10 | 2 | 0 | 0 | 0 |
| 20 | 1 | 0 | 0 | 0 |

逐项观测：

- Apollo5 / Tranq5：worker 未触发，official pricing 与 baseline 一致；
- Apollo10 / tranq10_09：worker 未触发，official pricing 与 baseline 一致；
- `mt20_greedy_apollo_01`：worker 未触发，official pricing 与 baseline 一致；
- 全部 `critical_disagreement_count=0`。

## 结论

1. Deep post-call reserve 不是当前短预算回退的有效修复；
2. 较高 min-remaining gate 可以避免短预算下 worker 触发，从而避免回退；
3. 但该 gate 的效果是“防回退”，不是性能提升：worker events 为 0，不能证明 Pulse worker ROI；
4. 当前仍不支持默认启用 worker，也不支持 official certificate gate。

下一步如果继续 worker 路线，应把触发条件改成更明确的 time-budget ROI gate：

- 只在剩余时间足够覆盖 worker + 至少一轮后续 official pricing 时触发；
- 短预算下宁可跳过 worker，保持 baseline；
- 不能通过提高 worker budget 解决当前问题。
