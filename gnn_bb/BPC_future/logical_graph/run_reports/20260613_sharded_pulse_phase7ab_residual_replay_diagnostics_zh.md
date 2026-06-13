# Sharded Pulse Phase 7AB Residual Replay Diagnostics 报告

日期：2026-06-13

## 目标

Phase 7AB 只做同 context residual replay 诊断。

Phase 7AA 已经定位 ordinary follow-up residual negative：

- `[5,8,15]` 的实际 sequence 是 `[8,15,5]`，start `0.0`；
- `[5,12,18]` 的实际 sequence 是 `[12,18,5]`，start `3.086313`。

本轮目标是验证这些 ordinary residual journeys 能否通过 Phase 3A Pulse leaf materialization contract 回放，并在当前 true dual / cuts context 下得到一致 true RC。

## 实现摘要

### 1. 新增 opt-in replay config

新增配置：

- `journey_pulse_residual_replay_diagnostics_enabled`
- `journey_pulse_residual_replay_diagnostics_max_journeys`

默认关闭。

仅在 coverage diagnostic profiles 中打开：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate`

### 2. 新增 diagnostic event

新增事件：

- `journey_pulse_residual_replay_diagnostic`

replay 逻辑：

1. 读取 ordinary pricing 返回的 `JourneyColumn.trips`；
2. 从 `TimedTrip.tasks/start_time/arc_option_ids` 重建 `PulseSortieTrace`；
3. 用 Phase 3A `materialize_pulse_leaf_candidate()` 回放；
4. 用当前 true dual / cuts 计算 true RC；
5. 记录 materialized / negative / signature mismatch / RC delta。

该事件只读，不修改：

- pool；
- pricing result；
- worker trigger；
- certificate state；
- official lower bound。

### 3. ROI summary 新增字段

新增：

- `pulse_residual_replay_events`
- `pulse_residual_replay_checked`
- `pulse_residual_replay_materialized`
- `pulse_residual_replay_negative`
- `pulse_residual_replay_rc_mismatch_count`
- `pulse_residual_replay_signature_mismatch_count`
- `pulse_residual_replay_first_status`
- `pulse_residual_replay_first_sequence`
- `pulse_residual_replay_first_original_true_rc`
- `pulse_residual_replay_first_replay_true_rc`
- `pulse_residual_replay_first_rc_delta`

## 验证命令

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_pricing_log_reports_negative_task_set_samples \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 4 tests in 0.002s
OK
```

## Probe 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7ab_residual_replay_diagnostics_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate \
  --time-limit 4.0 \
  --audit-time-limit 0.2 \
  --worker-time-limit 0.2 \
  --current-probe-time-limit 0.2 \
  --pricing-time-limit 0.4 \
  --pricing-max-dp-states 1000 \
  --max-cg-iterations 3 \
  --audit-max-recursions 30000 \
  --worker-max-recursions 30000 \
  --current-probe-max-recursions 20000 \
  --current-probe-min-tasks 20 \
  --quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7ab_residual_replay_diagnostics_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7ab_residual_replay_diagnostics_20260613/summary.csv`

## 结果

| profile | follow-up sequence | original true RC | replay true RC | RC delta | materialized | signature mismatch |
|---|---|---:|---:|---:|---:|---:|
| coverage-scan | `[8,15,5]` | `-138.437225` | `-138.437225` | `0.0` | 1 | 0 |
| coverage no-ROI-gate | `[8,15,5]` | `-138.437225` | `-138.437225` | `0.0` | 1 | 0 |

JSONL 还显示第二个 ordinary residual：

- sequence `[12,18,5]`
- original true RC `-128.547499`
- replay true RC `-128.547499`
- RC delta `0.0`
- signature mismatch `0`

## 结论

Phase 7AB 排除了一个重要风险：

ordinary residual family 不是因为 Pulse leaf materialization / true-RC recomputation 不兼容才缺失。

具体来说：

- `[8,15,5]` 能通过 Phase 3A helper 回放；
- `evaluate_timed_trip()` / `make_journey()` / `manual_journey_reduced_cost()` 语义一致；
- signature 与 true RC 都一致；
- `[12,18,5]` 也一致。

因此当前 worker coverage 缺口更集中在：

1. transition DFS 没有在小预算内走到 first-task shard `8` 的 `[8,15,5]` family；
2. shard scheduling / child ordering / recursion cap 导致 relevant early-start family 未被访问；
3. 或该 sequence 被 transition-level feasibility / bound / archive pruning 提前剪掉。

下一步若继续 Pulse 方向，应做 transition reachability diagnostic：

- target sequence `[8,15,5]`；
- 记录 first-task shard `8` 中每个 prefix 是否 visited / pruned / not reached；
- 区分 `time_window_pruned`、`energy_pruned`、`return_pruned`、`bound_pruned`、`archive_pruned`、`budget_not_reached`；
- 不扩大 worker budget，不默认启用 worker，不开启 certificate gate。

## 边界

- 本轮只增加 opt-in diagnostic；
- default benchmark 行为不变；
- 没有 certificate effect；
- 没有 official lower-bound effect；
- Pulse incomplete / duplicate-only / no-column 仍不能产生 official lower bound。
