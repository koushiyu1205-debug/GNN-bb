# Sharded Pulse Phase 8J Worker 内部候选族覆盖诊断报告

日期：2026-06-13

## 目标

Phase 8J 只做只读诊断，回答一个问题：

> 在同一 worker context 中，Pulse worker 内部候选池是否已经包含 ordinary follow-up 的 residual negative task-set `5,8,15`，只是后续 impact filter / return selection 没选出来？

本轮不改变：

- Pulse transition / pruning / ordering；
- worker trigger / time limit / stop-after-first-negative；
- impact filter 行为；
- RMP add-column path；
- official certificate / lower-bound 语义；
- production 默认配置。

## 实现摘要

新增 `JourneyPricingResult` 诊断字段：

- `pulse_negative_pool_task_set_samples`
- `pulse_negative_pool_sequence_samples`
- `pulse_negative_pool_signature_samples`
- `pulse_harvested_task_set_samples`
- `pulse_harvested_sequence_samples`
- `pulse_harvested_signature_samples`
- `pulse_returned_candidate_task_set_samples`
- `pulse_returned_candidate_sequence_samples`
- `pulse_returned_candidate_signature_samples`

这些字段分别记录：

- worker / guarded Pulse 内部 negative pool 样本；
- harvesting pool 样本；
- impact filter 选择前后可返回候选样本。

ROI calibration summary 新增对比字段：

- `worker_vs_ordinary_negative_pool_*`
- `worker_vs_ordinary_harvested_*`
- `worker_vs_ordinary_returned_candidate_*`
- 对应 `pulse_worker_vs_ordinary_*` aliases。

对比对象是：

- worker 首个 added task-set；
- worker 后 ordinary follow-up 首个 negative task-set；
- worker 内部三个候选池样本。

## Apollo20 窄 probe

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase8j_worker_internal_candidate_family_probe_20260613 \
--instances mt20_greedy_apollo_01 \
--profiles strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown \
--time-limit 1.5 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 3 \
--current-probe-time-limit 0.5 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase8j_worker_internal_candidate_family_probe_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase8j_worker_internal_candidate_family_probe_20260613/summary.csv`

关键结果：

| 字段 | 值 |
|---|---|
| worker added task-set | `6,19` |
| ordinary follow-up first negative | `5,8,15` |
| worker negative pool samples | `[[6,19]]` |
| worker harvested samples | `[[6,19]]` |
| worker returned candidate samples | `[[6,19]]` |
| negative-pool exact hit for `5,8,15` | `False` |
| harvested exact hit for `5,8,15` | `False` |
| returned-candidate exact hit for `5,8,15` | `False` |
| overlap / jaccard | `0 / 0.0` |
| critical disagreement | `False` |

同时，ordinary follow-up 仍显示：

- `5,8,15` 在 profile reachable / negative / selected / materialized / returned 样本中都是 exact hit；
- ordinary follow-up 首个 negative sequence 为 `8,15,5`；
- worker 内部三个候选池没有覆盖该 residual family。

## 结论

Phase 8J 证伪了“worker 已经看到 `5,8,15`，只是 impact filter 或 returned-candidate path 丢掉”的假设。

当前更准确的结论是：

- Pulse worker 当前调用只生成 / harvest / return 了 `6,19`；
- ordinary follow-up 的 residual `5,8,15` 不在 worker negative pool、harvested pool 或 returned-candidate pool 中；
- ROI 缺口在 worker 内部搜索覆盖 / 停止时机 / shard ordering / current context，而不是 impact filter 丢列。

## Exactness 边界

- 新字段全部是只读诊断；
- 不改变任何候选排序、剪枝、过滤、返回或加列决策；
- Pulse incomplete / duplicate-only / no-column 仍不会产生 certificate；
- worker 返回列仍走原有 true-RC negative 与正常 add-column path；
- production 默认配置不变。

## 验证

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_driver_smoke_harvest_counters_surface \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 3 tests in 0.031s
OK
```

全量回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 477 tests in 49.984s
OK (skipped=1)
```

Diff 检查：

```bash
git diff --check
```

结果：通过。

## 下一步建议

下一步不要扩大 worker budget，也不要放开 certificate。建议进入：

Phase 8K：same-context residual reachability / stop-after-first-negative 诊断。

重点检查：

- 在同一 worker dual / cuts / pool / forbidden context 中，若不在首个 negative 后停止，是否能 reach / select / materialize `5,8,15`；
- 若仍不能，差异来自 shard coverage、task ordering、arc-option ordering、deadline，还是 worker context 与 ordinary follow-up context 已经不同；
- 若能，则再评估多返回少量候选是否提升 ROI。
