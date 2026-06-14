# BPC_future 根因审计补充：counterfactual capture target coverage

日期：2026-06-13

## 目的

本轮包含两部分：

1. 先做只读全局 coverage audit；
2. 再用 no-certificate-effect capture 开关做一轮小矩阵 target capture attempt，仍不改变 pricing / RMP / Pulse 主线语义。

目的只是检查：

> 当前已有 `BPC_future/results` 里的 capture events 是否已经覆盖了上一轮定义的 3 个 exact-context capture targets？

当前答案是：`capture_target_001` 和 `capture_target_003` 已经被 replay-ready exact capture 覆盖，`capture_target_002` 仍未覆盖。

## 命令

只读 coverage 脚本：

```text
BPC_future/scripts/audit_counterfactual_capture_target_coverage.py
```

全局复跑：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/audit_counterfactual_capture_target_coverage.py \
--output-dir BPC_future/results/root_cause_counterfactual_capture_target_coverage_20260613 \
BPC_future/results
```

另外补了一轮 target source-profile capture attempt，用于检查 planned targets 是否能在当前 runner/config 下自然重现：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/root_cause_counterfactual_target_capture_empty_context_scan_20260613 \
--instances mt20_greedy_tranq_01 mt20_greedy_apollo_01 tranq20_01 \
--profiles \
  experimental_l1_previous_dual_stabilization_20_only \
  experimental_pricing_time_0_6_20_only \
  experimental_early_new_task_set_quota_3_20_only \
  experimental_early_new_task_set_quota_3_return12_20_only \
  experimental_l1_zero_dual_stabilization_20_only \
--time-limit 8.0 \
--max-cg-iterations 4 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1 \
--counterfactual-replay-capture \
--counterfactual-replay-capture-max-journeys 0 \
--counterfactual-replay-capture-pool-max-journeys 0 \
--counterfactual-replay-capture-log-empty \
--quiet
```

这轮 capture attempt 是 diagnostic-only；`--counterfactual-replay-capture-log-empty` 只用于判断是否到达目标上下文，空 returned batch 不能算 replay treatment。

之后又补了一轮窄的 `tranq20_01` dp1000 capture，用于验证 target003 的空批次是否只是过低 state cap 造成：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/root_cause_counterfactual_target_capture_dp1000_tranq20_20260613 \
--instances tranq20_01 \
--profiles experimental_early_new_task_set_quota_3_return12_20_only experimental_l1_zero_dual_stabilization_20_only \
--time-limit 8.0 \
--max-cg-iterations 2 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--counterfactual-replay-capture \
--counterfactual-replay-capture-max-journeys 0 \
--counterfactual-replay-capture-pool-max-journeys 0 \
--quiet
```

最后补了一轮 `target001/002` dp1000 capture sweep，用于验证 `mt20_greedy_tranq_01` 和 `mt20_greedy_apollo_01` planned targets 是否能产生非空 exact-context returned batch：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613 \
--instances mt20_greedy_tranq_01 mt20_greedy_apollo_01 \
--profiles experimental_l1_previous_dual_stabilization_20_only experimental_pricing_time_0_6_20_only experimental_early_new_task_set_quota_3_20_only \
--repeat-count 3 \
--time-limit 8.0 \
--max-cg-iterations 4 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--counterfactual-replay-capture \
--counterfactual-replay-capture-max-journeys 0 \
--counterfactual-replay-capture-pool-max-journeys 0 \
--quiet
```

输出：

```text
BPC_future/results/root_cause_counterfactual_capture_target_coverage_20260613/summary.json
```

## 结果

```text
target_count = 3
capture_event_count = 104
target_with_near_match_count = 3
target_with_exact_capture_count = 2
uncovered_target_count = 1
all_checks_pass = true
```

target source-profile capture attempt 自身结果：

```text
event_count = 30
captured_journey_count = 0
returned_journey_count = 0
all_checks_pass = true
```

`tranq20_01` dp1000 capture 自身结果：

```text
event_count = 4
captured_journey_count = 26
returned_journey_count = 26
all_checks_pass = true
```

`target001/002` dp1000 capture 自身结果：

```text
event_count = 66
captured_journey_count = 176
returned_journey_count = 176
all_checks_pass = true
```

## Target 覆盖情况

| target | candidate | exact coverage | near match | 说明 |
|---|---|---:|---:|---|
| `capture_target_001` | `replay_candidate_001` | 6 | 57 | dp1000 scan 命中 `mt20_greedy_tranq_01 / cg2 / heuristic / obj=761.814403 / active=5c6420f757a39d2d`，并产生 replay-ready exact captures |
| `capture_target_002` | `replay_candidate_003` | 0 | 51 | Apollo20 本轮到达 cg3 heuristic，但 active/objective 是 `a37fc1e4e8451f9b / 761.626550333`，不是 target 的 `16862add48072518 / 780.586496` |
| `capture_target_003` | `replay_candidate_004` | 2 | 56 | dp1000 scan 命中 `tranq20_01 / cg1 / heuristic / obj=838.0048415 / active=aa2b834c9d43f2a6`，并产生 `returned=12` 与 `returned=1` 两个 replay-ready exact captures |

后续复核进一步定位了 `capture_target_002` 的缺口：它不是 cg3 才偏离，而是 `mt20_greedy_apollo_01 / experimental_early_new_task_set_quota_3_20_only` 在 cg1 的 returned batch 已经与旧 phase10h 不同。旧 phase10h cg1 后 active hash 是 `427b1308ea279e0c`，当前 target capture 与 no-capture mirror 都变成 `6907bf1e60739a97`，所以后续只能到达 near match `a37fc1e4e8451f9b / 761.626550333`。详细证据见 `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_target002_reproduction_gap_zh.md`。

## 为什么 near match 不能算 exact capture

本轮匹配规则是 fail-closed：

- instance / source path 近似匹配不够；
- `cg_iter` 必须一致；
- `pricing_kind` 必须一致；
- `rmp_objective_before` 必须一致；
- `active_hash_before` 必须可比较且一致；
- event 必须 no-certificate-effect；
- event 必须有完整 pool / returned batch payload；
- returned/captured journey count 必须大于 0；
- event 必须 replay-ready。

当前已有 Apollo20 clean replay 是有价值样本，但它对应：

```text
cg_iter = 1
pricing_kind = sharded_pulse_hidden_negative_worker
rmp_objective_before = 1061.554044
context_hash = 080a188d2484ee3e
```

而推荐 target `replay_candidate_003` 要求：

```text
cg_iter = 3
pricing_kind = heuristic
active_hash_before = 16862add48072518
rmp_objective_before = 780.586496
```

因此它们不是同一个 exact-context treatment。

本轮新增的 `tranq20_01` dp1000 capture 则覆盖了 `capture_target_003`：

```text
cg_iter = 1
pricing_kind = heuristic
active_hash_before = aa2b834c9d43f2a6
rmp_objective_before = 838.0048415
returned_journey_count = 12 / 1
```

本轮还修正了一个诊断口径问题：`journey_counterfactual_replay_capture` 的 `active_hash_before` 原先按 `(len(task_set), task_set)` 排序，而 trajectory dataset 的 `pool_active_task_set_hash` 按 task-set tuple 排序。对同一 `tranq20_01` active set，旧 capture 口径会得到 `017c956005365eb2`，trajectory 口径是 `aa2b834c9d43f2a6`。现在 capture hash 已统一到 trajectory/pool diagnostic 口径，并增加测试防止再次漂移。

## 对根因判断的影响

这一步进一步说明：

1. 当前全局 scan 的 `104` 个 capture events 已覆盖 `2/3` 个推荐 replay targets；
2. Apollo20 ready replay 证明 high-impact batch 存在，但不能替代 `replay_candidate_003` 的 cg3 heuristic context；
3. target source-profile empty scan 说明，`pricing_max_dp_states=1` 会让 target003 到达 context 但返回空 batch；
4. dp1000 scan 说明 target003 不是无负列，而是原先 capture sweep 资源上限过窄；
5. target001 已经由 dp1000 scan 形成非空 exact capture；
6. target002 仍需复现对应 cg/objective/active context；当前复核显示它从 cg1 returned batch 开始发生 trajectory drift，不能用 near match 替代；
7. 在覆盖更多 exact contexts 并重新审计 selector 前，worker 方向仍没有足够 production calibration evidence。

## Verifier 对应项

新增 evidence ledger section：

```text
counterfactual_capture_target_coverage
```

关键 check：

```text
check_capture_targets_have_partial_exact_capture_coverage = true
```

该 check 要求：

- target count 为 3；
- capture event count 为 104；
- near match target 为 3；
- exact capture target 为 2；
- uncovered target 为 1；
- near matches 不能算 exact capture；
- 剩余 targets 仍需要新 capture。

## 结论

当前结论更具体：

> 已有日志里有 high-impact replay 样本，也有 3 个清晰的下一步 replay targets；其中 target001 和 target003 已有非空 exact capture 与 replay impact，target002 仍没有 replay-ready exact capture。

所以目标仍未完成。下一步要做的是继续按 target 生成新的 no-certificate-effect、非空 returned-batch capture；target001/003 已证明有 local RMP impact，target002 则还需要复现对应 cg/objective/active context。不能从新增 target replay 直接推断 selector 已可用，也不应继续修改主线求解器。
