# Sharded Pulse Phase 7Y Worker Coverage-scan Diagnostic 报告

日期：2026-06-13

## 目标

Phase 7Y 只做 worker coverage 诊断，不推进 production worker，也不开放 official certificate gate。

本轮要回答一个窄问题：

如果关闭 `stop_after_first_negative`，当前 transition Pulse worker 是否能覆盖 ordinary heuristic follow-up 后续发现的 disjoint negative task-set family？

## 实现摘要

新增 opt-in ROI calibration profile：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan`

该 profile 的边界：

- 20-task only；
- current-context probe；
- pre-heuristic hidden-negative worker；
- impact-filtered add-column path；
- 使用低预算 current-probe family 的小时间/递归预算；
- 显式设置 `journey_sharded_pulse_hidden_negative_worker_stop_after_first_negative=False`；
- 设置 `journey_sharded_pulse_hidden_negative_worker_max_cg_iter=1`，避免诊断 profile 扩散成长期 worker 策略；
- 不进入默认 `PROFILE_ORDER`；
- 不产生 certificate effect，不更新 official lower bound。

## 验证命令

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 2 tests in 0.002s
OK
```

## Probe 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7y_worker_coverage_scan_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan \
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

- `BPC_future/results/sharded_pulse_phase7y_worker_coverage_scan_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7y_worker_coverage_scan_20260613/summary.csv`

## 结果

| profile | worker stop-after-first | worker returned | worker task-set | recursions | worker time | time-window pruned | follow-up first negative | relation |
|---|---:|---:|---|---:|---:|---:|---|---|
| baseline | false | 0 | - | 0 | 0 | 0 | - | no_worker_add |
| failure-cooldown early-stop | true | 1 | `[6,19]` | 115 | 0.032166443 | 5930 | `[5,8,15]` | disjoint_task_set |
| coverage-scan no early-stop | false | 1 | `[6,19]` | 245 | 0.072859417 | 12666 | `[5,8,15]` | disjoint_task_set |

关键观察：

- 关闭 early stop 后，worker 递归数从 `115` 增至 `245`；
- transition time-window pruning 从 `5930` 增至 `12666`；
- worker 仍然只返回 1 个 task set：`[6,19]`；
- ordinary heuristic follow-up 首个 residual negative 仍是 `[5,8,15]`；
- worker 与 follow-up negative 的关系仍是 `disjoint_task_set`；
- coverage-scan 没有覆盖 ordinary residual negative family。

## 结论

Phase 7Y 说明：当前 worker coverage 缺口不是单纯 `stop_after_first_negative` 或 shard ordering 问题。

关闭 early stop 会让 transition Pulse 多探索一部分状态，但仍没有返回 ordinary heuristic 后续找到的 `[5,8,15]` negative family。因此继续堆 active-worker gate、扩大 worker time limit、或直接推进 production worker 都没有依据。

更合理的下一步是：

1. 直接比较 transition Pulse candidate universe 与 ordinary heuristic/profile-DP 在同一 true dual / cuts / forbidden context 下的候选域；
2. 或暂停 active-worker 主线，转向 ordinary pricing/profile-DP tail、RMP stabilization、column impact filter、legacy final-judge proof-tail 优化。

## 边界

- 本轮 profile 是显式 opt-in 诊断；
- default benchmark 行为不变；
- 没有 certificate effect；
- Pulse incomplete / no-column / duplicate-only 仍不能更新 official lower bound；
- 所有 worker 返回列仍走普通 add-column path。
