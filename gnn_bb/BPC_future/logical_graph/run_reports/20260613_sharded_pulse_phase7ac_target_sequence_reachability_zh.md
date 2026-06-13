# Sharded Pulse Phase 7AC Target Sequence Reachability 诊断报告

日期：2026-06-13

## 目标

本轮只做 opt-in 诊断，不改变求解路径、worker gate、certificate 或 official lower bound。

目标是回答 Phase 7AB 后留下的问题：

`[8,15,5]` 这条 ordinary residual negative sequence 已证明可以被 Pulse leaf materialization 原样回放，那么 transition Pulse worker 为什么没有覆盖它？

## 实现摘要

### 1. Transition target-sequence 诊断

`transition_root_only_pulse()` 新增只读诊断参数：

- `target_sequence_diagnostics_enabled`
- `target_sequence_diagnostics_sequence`

诊断记录：

- target sequence；
- 最大触达 prefix 长度；
- 是否完成 / materialized / true-RC negative；
- first blocked reason / blocked prefix / blocked next task；
- target transition attempts / accepted；
- prune reason counts。

诊断严格限制在目标 first-task shard 内。对于 `[8,15,5]`，只有 first-task shard `8` 会贡献 target reachability 数据，避免其他 first-task shard 的后续 sortie 从 8 开始时污染诊断。

### 2. Driver / ROI summary 透传

新增配置：

- `journey_pulse_target_sequence_diagnostics_enabled`
- `journey_pulse_target_sequence_diagnostics_sequence`
- `journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled`
- `journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence`

新增日志字段：

- `pulse_target_sequence_*`
- `pulse_worker_target_sequence_*`

新增 ROI summary 字段：

- `worker_target_sequence`
- `worker_target_sequence_reached_prefix_len`
- `worker_target_sequence_completed`
- `worker_target_sequence_materialized`
- `worker_target_sequence_negative`
- `worker_target_sequence_blocked_reason`
- `worker_target_sequence_blocked_prefix`
- `worker_target_sequence_blocked_next_task`
- `worker_target_sequence_transition_attempts`
- `worker_target_sequence_transition_accepted`
- `worker_target_sequence_prune_reason_counts`

coverage diagnostic profiles 自动开启目标 sequence `[8,15,5]`：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate`

## Apollo20 窄 Probe

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7ac_target_sequence_reachability_20260613_rerun \
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

- `BPC_future/results/sharded_pulse_phase7ac_target_sequence_reachability_20260613_rerun/summary.json`
- `BPC_future/results/sharded_pulse_phase7ac_target_sequence_reachability_20260613_rerun/summary.csv`

## 结果

| profile | worker returned | worker sequence | follow-up first negative | target reached prefix | target attempts | accepted | target materialized | blocked reason |
|---|---:|---|---|---:|---:|---:|---|---|
| coverage_scan | 1 | `6,19` | `8,15,5` | 0 | 0 | 0 | False | `deadline` |
| coverage_no_roi_gate | 1 | `6,19` | `8,15,5` | 0 | 0 | 0 | False | `deadline` |

两个 coverage profiles 都显示：

- worker 仍只返回 `[6,19]`；
- ordinary follow-up 首个 residual negative 仍是 `[8,15,5]`；
- target sequence `[8,15,5]` 在目标 first-task shard 内没有产生任何 transition attempt；
- 没有 time-window / energy / return / bound / archive prune reason；
- blocked reason 为 `deadline`。

## 结论

Phase 7AC 将 coverage gap 进一步定位：

`[8,15,5]` 不是被 transition feasibility rule 误剪，也不是 leaf materialization / true-RC context mismatch；当前小预算 worker 在触达 first-task shard `8` 的目标 transition 前就耗尽了 deadline。

因此下一步应做 shard scheduling / target-shard priority 诊断，而不是扩大 worker budget、打开 production worker 或 certificate gate。

## 验证

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/pulse_toy_exhaustive.py \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_target_sequence_reachability_materialized \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_target_sequence_reachability_reports_prune_reason \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_target_sequence_diagnostics_surface_in_pricing_log \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 5 tests in 0.049s
OK
```

## 当前边界

- 默认 benchmark 行为不变；
- 诊断只在显式 profile 中开启；
- 不产生 official certificate；
- 不更新 official lower bound；
- 不改变 worker returned journeys 的选择逻辑；
- 不接 resume / parallel / 20/100 默认 A/B。

## 下一步建议

Phase 7AD：Target-shard scheduling priority diagnostic。

只在 coverage diagnostic profile 下尝试把 residual target first-task shard `8` 提前，观察：

1. first-task shard `8` 是否能在 deadline 前开始扩展；
2. `[8,15,5]` 是否 materialized；
3. 若仍未 materialize，具体被哪条 transition rule exact-safely prune；
4. worker 是否从 `[6,19]` 转向 `[8,15,5]` 或其他 residual family。

仍不要扩大 worker budget，也不要打开 production worker 或 certificate gate。
