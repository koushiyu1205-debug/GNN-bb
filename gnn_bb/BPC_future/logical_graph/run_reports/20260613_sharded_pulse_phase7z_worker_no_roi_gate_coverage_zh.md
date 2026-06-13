# Sharded Pulse Phase 7Z Worker No-ROI-gate Coverage Diagnostic 报告

日期：2026-06-13

## 目标

Phase 7Z 继续沿着 Phase 7Y 的 coverage mismatch 诊断推进。

本轮只回答一个问题：

`[5,8,15]` 这类 ordinary heuristic follow-up residual negative 没被 Pulse worker 找到，是不是因为 worker shard ROI gate 在小预算下提前截断了相关 shard？

本轮不做：

- production worker 默认开启；
- official certificate gate；
- 20/100 A/B；
- worker time limit 放大；
- resume / parallel。

## 实现摘要

### 1. 补 worker shard summary 字段

`run_sharded_pulse_roi_calibration.py` 新增 summary 字段：

- `worker_shards_total`
- `worker_shards_certified`
- `worker_shards_incomplete`
- `worker_shards_negative`
- `worker_shards_refined`
- `worker_low_roi_shards`
- 对应 `pulse_worker_shards_*` / `pulse_worker_low_roi_shards`

这些字段只汇总已有 JSONL payload，不改变求解路径。

### 2. 新增 opt-in diagnostic profile

新增：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate`

profile 边界：

- 20-task only；
- current-context probe；
- pre-heuristic hidden-negative worker；
- impact-filtered add-column path；
- 同 coverage-scan 小预算；
- `stop_after_first_negative=False`；
- `journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False`；
- `journey_sharded_pulse_hidden_negative_worker_max_cg_iter=1`；
- 不进入默认 `PROFILE_ORDER`；
- 不产生 certificate effect；
- 不更新 official lower bound。

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
Ran 2 tests in 0.001s
OK
```

## Probe 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7z_worker_no_roi_gate_coverage_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown \
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

- `BPC_future/results/sharded_pulse_phase7z_worker_no_roi_gate_coverage_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7z_worker_no_roi_gate_coverage_20260613/summary.csv`

## 结果

| profile | stop-after-first | ROI gate | worker task-sets | shards total | incomplete | negative | recursions | worker time | follow-up first negative |
|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| early-stop failure-cooldown | true | true | `[6,19]` | 2 | 0 | 1 | 115 | 0.031180282 | `[5,8,15]` |
| coverage-scan | false | true | `[6,19]`, `[7,19]` | 20 | 17 | 2 | 248 | 0.068645513 | `[5,8,15]` |
| coverage no-ROI-gate | false | false | `[6,19]` | 20 | 18 | 1 | 233 | 0.068482884 | `[5,8,15]` |

关键观察：

- 关闭 early stop 后，worker 会访问全部 20 个 first-task shard，但多数 shard 仍 incomplete；
- coverage-scan 本轮可多返回 `[7,19]`，说明关闭 early stop 有时能增加同类 worker candidate；
- 关闭 shard ROI gate 后仍没有返回 `[5,8,15]`；
- ordinary heuristic follow-up 首个 residual negative 仍是 `[5,8,15]`；
- residual relation 仍是 `disjoint_task_set`；
- no-ROI-gate profile 没有改善 coverage，且仍只有 1 个 worker candidate。

## 结论

Phase 7Z 说明：

`[5,8,15]` residual ordinary negative 不是被 worker shard ROI gate 单独挡掉的。

当前 evidence 更支持：

1. 小预算下 transition Pulse 仍有大量 first-task shards incomplete；
2. worker 能找到 `[6,19]` / 偶发 `[7,19]`，但未覆盖 ordinary heuristic 的 `[5,8,15]` family；
3. 缺口更像 Pulse 候选子空间探索不足，或 transition Pulse 与 ordinary heuristic/profile-DP 在候选生成语义上存在差异。

因此仍不应：

- 扩大 active worker 时间；
- 继续堆 worker gate；
- 默认启用 worker；
- 推进 official certificate gate。

下一步若继续 Pulse 诊断，应直接对照同一 true dual / cuts / forbidden context 下的 ordinary heuristic/profile-DP candidate generation 与 transition Pulse state semantics，尤其是 `[5,8,15]` 这类具体 residual family 是否在 Pulse candidate universe 中可达。

## 边界

- 本轮仅新增 opt-in diagnostic profile 和只读 summary 字段；
- default benchmark 行为不变；
- 没有 certificate effect；
- Pulse no-column / incomplete / duplicate-only 仍不能更新 official lower bound；
- worker 返回列仍逐条走 normal add-column path。
