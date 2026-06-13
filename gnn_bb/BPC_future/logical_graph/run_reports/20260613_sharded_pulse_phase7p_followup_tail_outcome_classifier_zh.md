# Sharded Pulse Phase 7P Follow-up Tail Outcome Classifier 报告

日期：2026-06-13

## 目标

本轮不新增求解算法，不扩大 worker budget，不放开 certificate gate。

目标是补一个 ROI 归因字段：Pulse worker 加列后，后续 pricing tail 到底属于哪类状态。

已有诊断已经证明：

- worker 加入的 true-RC negative new task-set 能进入下一轮 RMP active support；
- next RMP objective 有明显 movement；
- 但 follow-up exact pricing tail 仍然存在。

本轮要进一步区分：

- follow-up pricing 是否仍发现负列；
- 是否只是 incomplete；
- incomplete 时 best RC 是负、近零、正，还是未知。

## 实现摘要

### 1. Tail outcome classifier

在 ROI calibration 脚本中新增 follow-up tail 分类：

- `no_worker_add`
- `no_followup_pricing`
- `followup_found_negative`
- `followup_certified_no_negative`
- `followup_incomplete_negative_best_rc`
- `followup_incomplete_near_zero_best_rc`
- `followup_incomplete_positive_best_rc`
- `followup_incomplete_unknown_best_rc`
- `followup_nonnegative_state_negative_best_rc`
- `followup_no_negative_observed`

该 classifier 只读 JSONL 记录，不改变 solver / pricing / RMP / certificate 行为。

### 2. 新增 summary 字段

新增：

- `followup_tail_outcome`
- `followup_negative_pricing_calls`
- `followup_incomplete_pricing_calls`
- `followup_min_best_rc`
- `pulse_worker_followup_tail_outcome`
- `pulse_worker_followup_negative_pricing_calls`
- `pulse_worker_followup_incomplete_pricing_calls`
- `pulse_worker_followup_min_best_rc`

## Focused 测试

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 2 tests in 0.005s
OK
```

## 单例 smoke

输出：

- `BPC_future/results/sharded_pulse_phase7p_tail_outcome_single_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7p_tail_outcome_single_20260613/summary.csv`

实例：`mt20_greedy_apollo_01`

Profile：`strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate`

结果：

- worker events：`1`
- worker added：`1`
- follow-up active task-set ratio：`1.0`
- follow-up pricing calls：`2`
- follow-up negative pricing calls：`0`
- follow-up incomplete pricing calls：`2`
- follow-up min best RC：`0.034526`
- follow-up last pricing：`exact / INCOMPLETE_LIMIT / profile_dp_incomplete`
- tail outcome：`followup_incomplete_positive_best_rc`

解释：

worker 加的列进入 active support 后，follow-up pricing 没有观测到负 best RC；tail 仍然是 exact pricing incomplete。

## Gate 矩阵

输出：

- `BPC_future/results/sharded_pulse_phase7p_tail_outcome_gate_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7p_tail_outcome_gate_20260613/summary.csv`

矩阵：

- 5-task balanced 全量 20 个；
- 10-task 指定 7 个；
- 20-task smoke 3 个；
- profiles：`baseline` vs `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate`。

结果摘要：

| scale | profile | n | avg wall | worker events | added | tail outcomes | critical |
|---:|---|---:|---:|---:|---:|---|---:|
| 5 | baseline | 20 | 0.024975 | 0 | 0 | `no_worker_add`: 20 | 0 |
| 5 | active gate | 20 | 0.024743 | 0 | 0 | `no_worker_add`: 20 | 0 |
| 10 | baseline | 7 | 0.117431 | 0 | 0 | `no_worker_add`: 7 | 0 |
| 10 | active gate | 7 | 0.117473 | 0 | 0 | `no_worker_add`: 7 | 0 |
| 20 | baseline | 3 | 0.211570 | 0 | 0 | `no_worker_add`: 3 | 0 |
| 20 | active gate | 3 | 0.228310 | 1 | 1 | `no_worker_add`: 2, `followup_incomplete_positive_best_rc`: 1 | 0 |

20-task active row：

- `mt20_greedy_apollo_01`
  - worker added：`1`
  - follow-up active ratio：`1.0`
  - follow-up min best RC：`0.034526`
  - follow-up outcome：`followup_incomplete_positive_best_rc`
  - primal：`1061.554044 -> 1030.002361`
  - wall：仍高于 baseline

## 结论

本轮分类进一步缩小了 ROI 缺口：

- worker 列能进入 active support；
- worker 列能移动 RMP objective；
- follow-up pricing 没有观测到负 best RC；
- 但 exact pricing 仍以 `INCOMPLETE_LIMIT / profile_dp_incomplete` 结束。

这说明当前问题更像：

- legacy/profile final judge proof incomplete；
- completion/proof tail 过慢；
- 或 RMP/列池退化导致单个 worker 列不足以改变 tail 结构。

而不是：

- worker 列没进 active；
- worker 后仍漏了明显负列；
- 需要继续加大 Pulse worker budget。

当前建议不变：

- 不默认启用 worker；
- 不进入 official certificate gate；
- 不扩大 Pulse worker budget；
- 下一步应转向 legacy final judge proof tail、profile DP incomplete 原因、RMP stabilization / pool compression，或整理 negative-result synthesis。
