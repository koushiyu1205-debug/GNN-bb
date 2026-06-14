# BPC_future 根因审计补充：target001/002 exact-context capture 与 replay

日期：2026-06-13

## 目的

上一轮全局 target coverage 显示：

- `capture_target_003 / tranq20_01` 已有 replay-ready exact capture；
- `capture_target_001 / mt20_greedy_tranq_01` 与 `capture_target_002 / mt20_greedy_apollo_01` 仍未覆盖。

本轮只做 diagnostic-only / no-certificate-effect 的窄 capture sweep，目标是检查 target001/002 是否能在当前 runner/config 下产生非空 exact-context returned batch，并继续扩大 local RMP replay calibration。

这不是 production worker，也不是 official certificate gate。

## Capture 命令

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

## Capture Audit

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/audit_counterfactual_replay_capture.py \
--output-dir BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/audit \
BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs
```

结果：

```text
event_count = 66
captured_journey_count = 176
returned_journey_count = 176
complete_event_count = 66
all_checks_pass = true
```

## 全局 Target Coverage 更新

全局复跑：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/audit_counterfactual_capture_target_coverage.py \
--targets BPC_future/results/root_cause_counterfactual_capture_targets_20260613/summary.json \
--output-dir BPC_future/results/root_cause_counterfactual_capture_target_coverage_20260613 \
BPC_future/results
```

结果：

```text
capture_event_count = 104
target_with_exact_capture_count = 2
uncovered_target_count = 1
all_checks_pass = true
```

Target 级别：

| target | candidate | exact coverage | near match | 状态 |
|---|---|---:|---:|---|
| `capture_target_001` | `replay_candidate_001` | 6 | 57 | 已覆盖：`mt20_greedy_tranq_01 / cg2 / heuristic / obj=761.814403 / active=5c6420f757a39d2d` |
| `capture_target_002` | `replay_candidate_003` | 0 | 51 | 仍未覆盖：本轮到达 Apollo cg3 的 active/objective 是 `a37fc1e4e8451f9b / 761.626550333`，不是 target 要求的 `16862add48072518 / 780.586496` |
| `capture_target_003` | `replay_candidate_004` | 2 | 56 | 之前 dp1000 `tranq20_01` capture 已覆盖 |

这说明 target001 已从 uncovered 变成 replay-ready exact capture；target002 仍是缺口。

后续针对 target002 的 reproduction-gap 复核显示，缺口来自更早的 cg1 returned-batch 分叉：旧 phase10h cg1 返回 `[5,8,12] / [5,12,15] / [5,15,18]` 等批次并进入 `427b1308ea279e0c`，当前 target capture 与 no-capture mirror cg1 返回 `[5,8,18] / [4,5,18] / [8,15,16]` 等批次并进入 `6907bf1e60739a97`。因此当前 run 无法到达 target002 的 `cg3 / active=16862add48072518 / obj=780.586496` exact context。详见 `BPC_future/logical_graph/run_reports/20260613_bpc_future_root_cause_target002_reproduction_gap_zh.md`。

## Replay / Impact 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/build_counterfactual_replay_manifest.py \
--output-dir BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/replay_manifest \
BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_counterfactual_replay_from_manifest.py \
--output-dir BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/replay_result \
BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/replay_manifest/replay_cases.json

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_counterfactual_replay_impact_dataset.py \
--manifest BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/replay_manifest/replay_cases.json \
--replay-result BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/replay_result/replay_results.json \
--output-dir BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/impact
```

Manifest：

```text
case_count = 66
ready_case_count = 66
candidate_count = 176
treatment_count = 440
all_checks_pass = true
```

Replay：

```text
case_count = 66
ready_case_count = 66
changed_treatment_count = 353
improving_treatment_count = 288
all_checks_pass = true
```

Impact dataset：

```text
candidate_row_count = 176
full_batch_count = 66
full_batch_improved_count = 57
high_impact_candidate_count = 117
noop_candidate_count = 59
best_objective_delta = -267.639664
all_checks_pass = true
```

## 解释

这轮证据进一步加强了两个判断。

第一，20-task 中存在大量能在 exact captured RMP context 下改善 local RMP objective 的 returned batches。target001 及同轮上下文的 replay 显示，局部 treatment impact 不只存在于 Apollo20 单一上下文，也存在于 `mt20_greedy_tranq_01` 相关上下文。

第二，负列仍不等于有用列。`noop_candidate_count=59` 说明同一批 exact-context replay 中也有不改变 local RMP objective 的 candidate。也就是说，扩大 capture 样本后，“缺少 selector”这个结论没有被削弱，反而更清楚：同一个 replay universe 里 high-impact 和 no-op candidate 同时存在。

target002 仍未覆盖也很重要。本轮 `mt20_greedy_apollo_01` 的 `experimental_early_new_task_set_quota_3_20_only` 到达了 cg3 heuristic context，但 active hash / objective 变成：

```text
active_hash_before = a37fc1e4e8451f9b
rmp_objective_before = 761.626550333
```

而 target002 要求：

```text
active_hash_before = 16862add48072518
rmp_objective_before = 780.586496
```

因此不能把 near match 当作 exact treatment。target002 仍是当前最重要的 uncovered exact-context 分叉样本。

target002 的新增解释是：当前代码/选择语义已经在 cg1 改变 returned batch composition，导致 active trajectory 从第一轮加列后就分叉。这支持当前根因判断，即 early returned-batch 的 concrete composition 对后续 RMP 轨迹有强影响，单纯“多返回”或“更负 RC”不能替代 addition-before selector。

## 对根因判断的影响

当前根因判断更新为：

> 20-task 确实存在多个 context family 的 local high-impact returned batch；但同一 replay 数据里也存在 no-op candidate，且 target002 这种关键 Apollo 分叉仍未覆盖。production 优化仍缺少 addition-before、context-aware、低开销、可泛化的 returned-batch selector。

这仍不是可上线优化方向：

- replay 是 local RMP treatment，不是完整 BPC wall-time speedup；
- target002 未覆盖；
- selector 仍未通过跨 context / 跨 instance gate；
- 5/10 no-regression 仍只能靠极早 gate / no-op；
- 不能打开 worker default 或 official certificate gate。

## 结论

本轮把 exact-context replay calibration 从 `target003 / tranq20_01` 扩展到 `target001 / mt20_greedy_tranq_01`，并形成 66 个 ready replay cases。它强化了“有用 batch 存在”的证据，也强化了“必须先解决 selector”的结论。

目标仍未完成：当前还没有百分百确定、可保证 exactness、5/10 不退化且能大幅加速 20-task optimal 求解的优化方向。
