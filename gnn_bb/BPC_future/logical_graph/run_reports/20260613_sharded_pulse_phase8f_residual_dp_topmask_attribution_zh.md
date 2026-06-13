# Sharded Pulse Phase 8F Residual vs Profile-DP Top-Mask Attribution 报告

日期：2026-06-13

## 目标

Phase 8F 延续 Phase 8C/8D 的 profile-DP 结构归因，新增一个只读问题：

worker 后第一个 residual negative task-set，是否就是 follow-up profile-DP 中 label bucket 最拥挤的 top masks？

如果是 exact hit，下一步可考虑对 top masks 做 targeted materialization / cap 分配。

如果只是 overlap 或 disjoint，则说明 residual tail 不是单纯“top bucket 没物化”，继续围绕 top-bucket cap 做优化可能 ROI 不高。

## 实现摘要

`run_sharded_pulse_roi_calibration.py` 新增 ROI summary 字段：

- `followup_first_negative_profile_dp_top_overlap`
- `followup_first_negative_profile_dp_top_jaccard`
- `followup_first_negative_profile_dp_top_relation`
- `followup_first_negative_profile_dp_top_exact`
- `pulse_worker_followup_first_negative_profile_dp_top_overlap`
- `pulse_worker_followup_first_negative_profile_dp_top_jaccard`
- `pulse_worker_followup_first_negative_profile_dp_top_relation`
- `pulse_worker_followup_first_negative_profile_dp_top_exact`

这些字段只比较：

- worker 后第一个 ordinary follow-up negative task-set；
- follow-up pricing records 中 `dp_top_mask_label_counts` 的 task-set samples。

不改变：

- pricing；
- worker；
- RMP；
- certificate / official lower bound。

## 验证

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields
```

结果：

```text
Ran 2 tests in 0.001s
OK
```

## Probe 输出

输出目录：

- `BPC_future/results/sharded_pulse_phase8f_residual_dp_topmask_cap1000_probe_20260613`
- `BPC_future/results/sharded_pulse_phase8f_residual_dp_topmask_cap5000_probe_20260613`

实例：

- `mt20_greedy_apollo_01`

profiles：

- `baseline`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown`

## 关键结果

### cap1000

worker profile：

- worker added journeys: `1`
- follow-up first negative: `5,8,15`
- relation to worker task set: `disjoint_task_set`
- profile-DP top relation: `overlapping_task_set`
- profile-DP top exact: `False`
- overlap: `2`
- jaccard: `0.5`
- follow-up DP max bucket: `24`
- follow-up nonempty mask count: `132`
- top masks include:
  - `[4,5,15]`
  - `[4,5,8]`
  - `[4,8,15]`
  - but not exact `[5,8,15]`

### cap5000

worker profile：

- worker added journeys: `1`
- follow-up first negative: `5,8,15`
- relation to worker task set: `disjoint_task_set`
- profile-DP top relation: `overlapping_task_set`
- profile-DP top exact: `False`
- overlap: `2`
- jaccard: `0.333333333`
- follow-up DP max bucket: `63`
- follow-up nonempty mask count: `414`
- top masks shift to 2-sortie combinations such as:
  - `[3,4,10,11,18]`
  - `[3,4,10,16,18]`
  - `[3,4,9,10]`
  - `[3,4,5,10,15]`
  - still not exact `[5,8,15]`

## 解释

Residual `[5,8,15]` 不是 profile-DP top-mask exact hit。

它与 cap1000 top masks 有较强 overlap，但不是同一个 task-set；cap5000 后 top masks 转向更大的 2-sortie task-set，和 `[5,8,15]` 的 jaccard 反而更低。

这说明：

1. 当前 residual tail 不是简单“最高 label bucket 没有 materialize”；
2. 只围绕 top overloaded masks 做 materialization 不一定覆盖 residual negative；
3. residual family 可能来自 profile-DP candidate selection / active context / rough-vs-true RC ordering，而不是最高 bucket 压力本身。

## Exactness 边界

本轮没有改变任何求解决策：

- 不改变 candidate generation；
- 不改变 materialization；
- 不改变 add-column；
- 不改变 certificate；
- 不改变 lower bound。

新增字段只用于 JSON/CSV 归因。

## 结论

Phase 8F 排除了一个简单优化方向：直接针对 profile-DP top label buckets 做 materialization 不能保证覆盖 Apollo20 worker 后 residual `[5,8,15]`。

下一步若继续 profile-DP structural control，应更关注：

1. residual task-set / active task-set 定向 materialization；
2. rough RC 与 true RC 的排序偏差；
3. candidate selection 是否压掉了 residual family；
4. legacy final judge / ordinary heuristic 为什么稳定找到 `[5,8,15]`，而 worker/probe 不稳定覆盖。
