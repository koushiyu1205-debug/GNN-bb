# Sharded Pulse Phase 7P Follow-up Pricing Trajectory Attribution 报告

日期：2026-06-13

## 目标

本轮继续沿 Phase 7P 的 worker ROI 诊断推进，但不增加 worker 预算、不修改触发逻辑、不做 official certificate gate。

目标是补齐一个缺失归因：

- worker 加列后，follow-up pricing 是否先找到负列、随后又以 incomplete 结束；
- 如果是，不能简单把 `followup_found_negative` 当作 tail 改善；
- 需要在 summary 中明确记录 trajectory，便于区分“worker 后续找不到负列”和“找到了负列但终端仍 incomplete”。

## 实现摘要

`run_sharded_pulse_roi_calibration.py` 新增 worker follow-up trajectory 字段：

- `followup_pricing_state_sequence`
- `followup_first_negative_cg_iter`
- `followup_first_negative_pricing_kind`
- `followup_first_negative_best_rc`
- `followup_terminal_after_negative_incomplete`
- `followup_last_pricing_time_limit`
- `followup_last_pricing_max_dp_states`
- `followup_last_pricing_profile_dp_time`
- `followup_last_pricing_dp_state_count`

并提供对应 `pulse_worker_followup_*` 别名。

这些字段只来自 JSONL 后处理，不改变求解行为。

## Smoke

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7p_followup_trajectory_dp1000_single_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate \
  --time-limit 0.3 \
  --pricing-time-limit 0.12 \
  --pricing-max-dp-states 1000
```

结果摘要：

| profile | official pricing | worker added | follow-up sequence | terminal after negative incomplete |
|---|---|---:|---|---:|
| baseline | `FOUND_NEGATIVE` | 0 | - | False |
| active-gate | `INCOMPLETE_LIMIT` | 1 | `heuristic:FOUND_NEGATIVE:partial_dp_negative_journey -> heuristic:INCOMPLETE_LIMIT:profile_dp_incomplete` | True |

active-gate 关键字段：

- `followup_first_negative_cg_iter=2`
- `followup_first_negative_pricing_kind=heuristic`
- `followup_first_negative_best_rc=-139.600327`
- `followup_last_pricing_time_limit=0.033069`
- `followup_last_pricing_max_dp_states=1000`
- `followup_last_pricing_profile_dp_time=0.001468`
- `followup_last_pricing_dp_state_count=1`
- `followup_profile_dp_incomplete_class=profile_dp_unknown_best_rc_incomplete`
- `critical_disagreement_count=0`

## 解释

这组结果说明当前 active-gate worker profile 不是完全找不到后续负列：

1. worker 自身先加入 1 列；
2. 下一轮 official heuristic pricing 仍找到一条更强负列；
3. 但随后在剩余短预算下再次进入 `profile_dp_incomplete`；
4. 最终 official pricing state 因最后一次 pricing 变成 `INCOMPLETE_LIMIT`。

因此，这不是 official certificate 问题，也不是 Pulse returned journey exactness 问题。更像是短时间预算下，worker 额外 CG 轨迹改变了后续 pricing 调度和剩余时间分配。

## 验证

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 2 tests in 0.006s
OK
```

## 当前边界

- 未改变 solver 行为；
- 未改变 Pulse worker 触发；
- 未改变 certificate / lower-bound 规则；
- 未默认启用 worker；
- 未做 resume / parallel / official certificate gate；
- trajectory 字段只用于 ROI 归因。

## 结论

当前更精确的结论是：

Pulse worker 在 `mt20_greedy_apollo_01` 上能加入列，也可能让 follow-up heuristic 继续找到负列；但它没有稳定缩短 tail，反而在短预算下把最终 official pricing state 推到 `INCOMPLETE_LIMIT`。

下一步应避免继续加大 worker。更合理的是分析 time-budget / CG-iteration 轨迹：

- worker 前置是否消耗了足以让最后一轮 exact/heuristic 失去闭合机会的时间；
- worker 加列后的 RMP objective 改善是否值得额外 CG 轮次；
- 是否需要把 worker 触发改成“只在剩余时间足够覆盖后续 official pricing reserve”而不是单纯当前 probe negative。
