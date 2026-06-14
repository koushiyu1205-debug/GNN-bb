# BPC_future 根因审计补充：counterfactual capture targets

日期：2026-06-13

## 目的

本轮不运行 solver，不修改 pricing / RMP / Pulse 主线。

目的只是把已经筛出的 replay candidates 转成下一步可执行的 exact-context capture targets。

这一步解决的是工程证据问题：

> 既然现在已有 replay target，但 clean capture 样本不足，下一步到底应该按哪些 context 和 payload contract 去抓数据？

## 脚本

新增离线脚本：

```text
BPC_future/scripts/build_counterfactual_capture_targets.py
```

复跑命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/build_counterfactual_capture_targets.py \
--output-dir BPC_future/results/root_cause_counterfactual_capture_targets_20260613
```

输出：

```text
BPC_future/results/root_cause_counterfactual_capture_targets_20260613/summary.json
BPC_future/results/root_cause_counterfactual_capture_targets_20260613/targets.csv
```

## Target Manifest

```text
target_count = 3
candidate_ids = [
  replay_candidate_001,
  replay_candidate_003,
  replay_candidate_004
]
exact_context_count = 3
low_context_noise_target_count = 2
mixed_descriptor_context_target_count = 1
all_checks_pass = true
```

三个 target：

| target | candidate | instance | cg_iter | active hash | 类型 |
|---|---|---|---:|---|---|
| `capture_target_001` | `replay_candidate_001` | `mt20_greedy_tranq_01` | 2 | `5c6420f757a39d2d` | low-context-noise |
| `capture_target_002` | `replay_candidate_003` | `mt20_greedy_apollo_01` | 3 | `16862add48072518` | low-context-noise |
| `capture_target_003` | `replay_candidate_004` | `tranq20_01` | 1 | `aa2b834c9d43f2a6` | mixed descriptor stress |

## Capture Contract

所有 targets 都要求：

```text
diagnostic_only = true
replay_no_certificate_effect = true
certificate_capable = false
official_bound_effect = false
must_not_change_solver_path = true
ready_for_replay_now = false
not_ready_reason = observational_candidate_needs_exact_context_capture
```

必须捕获的字段包括：

```text
vehicle_count
context_hash
true_dual_hash
cut_hash
branch_hash
forbidden_signature_hash
rmp_objective_before
true_dual_vector
cuts
branch_constraints
pool_journeys
pool_signatures
pool_task_sets
returned_journeys
returned_journey.trips.tasks
returned_journey.trips.start_time
returned_journey.trips.end_time
returned_journey.trips.arc_option_ids
returned_journey.trips.occupancy
```

配置层必须保持：

```text
journey_counterfactual_replay_capture_enabled = true
journey_counterfactual_replay_capture_no_certificate_effect = true
journey_counterfactual_replay_capture_require_complete_pool = true
journey_counterfactual_replay_capture_require_complete_returned_batch = true
```

## 为什么这一步重要

之前的全局 scan 已经说明：

```text
global_ready_20_context_count = 1
```

而 replay candidate manifest 有：

```text
candidate_count = 40
recommended_candidate_count = 3
```

这一步把推荐候选变成了精确 capture 目标，避免后续继续泛泛扫描日志。

但它仍然不是优化证据：

- target manifest 只说明下一步该抓哪里；
- 还没有产生新的 ready replay case；
- 还没有 control RMP `OPTIMAL`；
- 还没有 single-candidate finite delta；
- 还没有跨 context selector calibration。

## Verifier 对应项

新增 evidence ledger section：

```text
counterfactual_capture_targets
```

关键 check：

```text
check_capture_targets_are_precise_no_certificate_targets = true
```

该检查要求：

- target count 为 3；
- candidate ids 正好是 `replay_candidate_001 / 003 / 004`；
- exact context count 为 3；
- low-context-noise target count 为 2；
- mixed descriptor stress target count 为 1；
- 所有 target 都是 diagnostic-only；
- 所有 target 都要求 no-certificate-effect；
- 所有 target 都要求完整 payload；
- 所有 target 当前都不能被当作 replay-ready case。

## 对根因判断的影响

这一步没有改变根因结论，但让下一步证据路线更具体：

> 当前根因解释已经足够明确；生产优化方向未证明；下一步应按这 3 个 exact-context targets 扩大 no-certificate-effect capture，而不是继续修改主线求解逻辑。

目标仍未完成。只有当这些 targets 产生多个 ready 20-task replay cases，并通过跨 context / 跨 instance selector gate 后，才可以讨论 production 优化方向。
