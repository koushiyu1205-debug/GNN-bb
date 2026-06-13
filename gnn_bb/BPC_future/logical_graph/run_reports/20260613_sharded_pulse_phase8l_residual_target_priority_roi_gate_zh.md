# Sharded Pulse Phase 8L Residual-aware First-task Priority ROI Gate 报告

日期：2026-06-13

## 目标

Phase 8L 的目标是把 Phase 8K 发现的 residual first-task priority 信号放进更严格的 ROI gate 中验证：

- 不默认启用 worker；
- 不启用 official certificate；
- 不做 resume / parallel；
- 不做 20/100 A/B；
- 不扩大默认 worker budget；
- 继续报告 5/10 no-regression。

本轮做了两层 smoke：

1. `residual_target_priority_roi_gate`：严格 gated profile，带 hard-tail fingerprint / current-context / follow-up guard；
2. `coverage_target_priority`：无 gate 的诊断对照，只用于判断 target first-task priority 的潜在 ROI。

## 实现摘要

新增 ROI profile：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_residual_target_priority_roi_gate`

该 profile：

- 20-task only，5/10 task 配置直接 no-op；
- pre-heuristic worker；
- `stop_after_first_negative=False`；
- target first-task priority sequence = `8,15,5`；
- `continue_same_iteration_after_add=True`；
- `continue_only_on_active_support=True`；
- inactive success cooldown = 2；
- true-RC gate：`impact_filter_min_true_rc=-30.0`；
- follow-up reserve：`min_followup_time_after_add=0.4`；
- failure cooldown = 2；
- current-probe hard-tail fingerprint enabled。

该 profile 只改变 calibration profile 配置，不改变 solver 默认配置。

## Smoke 1：严格 gated profile

输出：

- `BPC_future/results/sharded_pulse_phase8l_residual_target_priority_roi_gate_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase8l_residual_target_priority_roi_gate_smoke_20260613/summary.csv`

矩阵：

- Apollo5
- Tranq5
- Apollo10
- Tranq10_09
- mt20_greedy_apollo_01

结果：

| instance | scale | worker triggered | official unchanged | critical |
|---|---:|---:|---:|---:|
| Apollo5 | 5 | False | True | False |
| Tranq5 | 5 | False | True | False |
| Apollo10 | 10 | False | True | False |
| Tranq10_09 | 10 | False | True | False |
| mt20_greedy_apollo_01 | 20 | False | True | False |

结论：

- strict gate 没有污染 5/10；
- 20-task 当前 smoke 中也没有触发 worker；
- profile 是安全的，但 gate 太保守，不能回答 target-priority 是否有 ROI。

## Smoke 2：无 gate target-priority 诊断对照

输出：

- `BPC_future/results/sharded_pulse_phase8l_residual_target_priority_probe_no_gate_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase8l_residual_target_priority_probe_no_gate_20260613/summary.csv`
- `BPC_future/results/sharded_pulse_phase8l_residual_target_priority_tranq20_probe_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase8l_residual_target_priority_tranq20_probe_20260613/summary.csv`

矩阵：

- Apollo5 / Tranq5 / Apollo10 / Tranq10_09 / mt20_greedy_apollo_01
- 额外 mt20_greedy_tranq_01

关键结果：

| instance | worker triggered | worker added | target exact returned | primal baseline -> profile | follow-up |
|---|---:|---:|---:|---|---|
| Apollo5 | False | 0 | False | unchanged | no worker |
| Tranq5 | False | 0 | False | unchanged | no worker |
| Apollo10 | False | 0 | False | unchanged | no worker |
| Tranq10_09 | False | 0 | False | unchanged | no worker |
| mt20_greedy_apollo_01 | True | 8 | True | `921.640296 -> 857.401315` | still found `4,12,18` |
| mt20_greedy_tranq_01 | False | 0 | False | unchanged | no worker |

Apollo20 细节：

- worker returned / added = `8 / 8`；
- returned candidates include exact target task-set `[5,8,15]`；
- worker addition class = `changed_inactive_only`；
- support-changing count = `0`；
- follow-up still found a negative task-set `[4,12,18]`；
- RMP objective delta after worker = `-204.152729`；
- dual L1 delta after worker = `204.497989`；
- no critical disagreement。

Tranq20 细节：

- hardcoded Apollo residual target `8,15,5` 没有触发 useful worker；
- official result unchanged；
- no critical disagreement。

## 结论

Phase 8L 的结论是：

1. Strict gated residual target profile 当前安全但太保守。
   - 5/10 不触发；
   - Apollo20 smoke 也不触发；
   - 不能作为 ROI 证据。

2. Residual target first-task priority 有局部潜在 ROI。
   - 在 `mt20_greedy_apollo_01` 上，target priority 能返回 exact `[5,8,15]`，并让短时 primal 从 `921.640296` 改到 `857.401315`；
   - 但所有 worker added columns 仍是 `changed_inactive_only`，不是 active-support changing；
   - follow-up 仍继续发现 residual negative `[4,12,18]`。

3. Hardcoded residual target 不具备跨实例泛化。
   - 在 `mt20_greedy_tranq_01` 上没有触发/改善；
   - 后续需要从当前 context 自动提取 residual target，而不是固定 `8,15,5`。

4. 还不能宣称 production ROI 成立。
   - 这只是 Apollo20 的诊断性正信号；
   - strict gate 没触发；
   - target-priority no-gate profile 仍改变 official short-run outcome，因此只能作为实验诊断。

## Exactness 边界

- 所有新增内容都在 calibration profile 内；
- solver 默认配置不变；
- no-column / duplicate-only / incomplete 不产生 certificate；
- Pulse worker 返回列仍走 true-RC negative 和正常 add-column path；
- no official lower-bound side effect；
- 5/10 profile no-op，未启用 worker。

## 验证

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
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 3 tests in 0.002s
OK
```

全量回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 477 tests in 1.419s
OK (skipped=1)
```

Diff 检查：

```bash
git diff --check
```

结果：通过。

## 下一步建议

下一步不应直接默认启用 target-priority worker。

建议 Phase 8M：

自动 residual target extraction / residual-aware scheduling。

具体目标：

- 从 ordinary follow-up / previous diagnostic evidence 中提取 residual task-set，而不是 hardcode `8,15,5`；
- 只在 context hash 匹配、20-task hard-tail、strict follow-up reserve 下启用；
- 优先 first-task shard，而不是强行 exact sequence；
- 对比 target-priority worker 后是否减少 follow-up residual negatives；
- 继续要求 5/10 no-regression 和 no critical disagreement。
