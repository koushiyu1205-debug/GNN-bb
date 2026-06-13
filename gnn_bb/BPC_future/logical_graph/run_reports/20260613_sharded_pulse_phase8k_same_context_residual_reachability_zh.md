# Sharded Pulse Phase 8K Same-context Residual Reachability 诊断报告

日期：2026-06-13

## 目标

Phase 8K 继续沿着 Phase 8J 的结论推进，只回答一个窄问题：

> 在同一 worker context 下，关闭 `stop_after_first_negative` 并调整 shard / transition / arc ordering 后，Pulse worker 是否能 reach / return ordinary follow-up 的 residual family `5,8,15`？

本轮仍然不做：

- production worker 默认开启；
- official certificate gate；
- resume / parallel；
- 20/100 A/B；
- 增大默认 worker budget；
- 改变 worker add-column path；
- 改变 certificate / official lower-bound 语义。

## 实现摘要

新增 ROI summary 只读字段，用于把 target sequence 的 task-set 与 worker 内部候选池直接对比：

- `worker_target_sequence_task_set`
- `worker_target_negative_pool_overlap/jaccard/relation/exact`
- `worker_target_harvested_overlap/jaccard/relation/exact`
- `worker_target_returned_candidate_overlap/jaccard/relation/exact`
- 对应 `pulse_worker_target_*` aliases

这些字段只解析 worker diagnostic event 中的 target sequence，不改变 Pulse 搜索、排序、剪枝、过滤或返回逻辑。

## Probe 配置

输出目录：

- `BPC_future/results/sharded_pulse_phase8k_same_context_residual_reachability_probe_20260613`

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase8k_same_context_residual_reachability_probe_20260613 \
--instances mt20_greedy_apollo_01 \
--profiles \
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan \
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate \
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority \
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_transition_priority \
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_arc_option_priority \
--time-limit 1.5 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 3 \
--current-probe-time-limit 0.5 \
--profile-mask-diagnostics \
--quiet
```

## 关键结果

| profile | worker returned / added | target prefix | target blocked | target returned exact | returned candidates |
|---|---:|---:|---|---:|---|
| coverage_scan | 3 / 3 | 0 | deadline | False | `[7,19]`, `[6,19]`, `[11,12]` |
| coverage_no_roi_gate | 3 / 3 | 0 | deadline | False | `[7,19]`, `[6,19]`, `[11,12]` |
| coverage_target_priority | 8 / 8 | 1 | deadline | True | includes `[5,8,15]` |
| coverage_target_transition_priority | 6 / 6 | 2 | time_window | False | includes `[8,15]`, `[4,8,15]`, `[8,15,18]` |
| coverage_target_arc_option_priority | 0 / 0 | 1 | deadline | False | none |

更具体地：

- 基础 `coverage_scan` 和 `coverage_no_roi_gate` 即使关闭 `stop_after_first_negative`，仍没有触达 target first-task shard，`target_reached_prefix_len=0`；
- `coverage_target_priority` 只提升 first-task shard 后，worker returned-candidate pool 中出现 exact target task-set `5,8,15`；
- `coverage_target_priority` 返回的 sequence sample 包含 `8,5,15`，说明 residual task-set family 可达且可返回，但不是 ordinary follow-up 的 exact sequence `8,15,5`；
- `coverage_target_transition_priority` 强行优先 exact transition `8 -> 15` 后，能到达 prefix `8,15`，但下一步被 `time_window` 阻断；
- `coverage_target_arc_option_priority` 在当前低预算下没有返回列，target 只到 prefix 1 后 deadline；
- 所有 profile 都没有 critical disagreement。

## 结论

Phase 8K 把 Phase 8J 的缺口进一步拆开：

1. Residual task-set family `5,8,15` 不是不可达。
   - 只要优先调度 target first-task shard，worker 就能把 `5,8,15` 放进 returned-candidate pool。

2. 基础 worker 没看到 `5,8,15` 的主要原因是 first-task shard / budget / ordering。
   - 关闭 `stop_after_first_negative` 仍不够；
   - 不调整 first-task shard 优先级时，target prefix 仍为 0，并以 deadline 结束。

3. Ordinary follow-up 的 exact sequence `8,15,5` 与 worker 可返回的 residual family 不完全一致。
   - target transition priority 到达 `8,15` 后被 `time_window` 阻断；
   - worker 可返回的是同 task-set 的其他 sequence，例如 `8,5,15`。

4. 当前不应继续简单扩大 worker budget。
   - 更有价值的方向是 shard scheduling / residual-aware first-task priority / support-aware targeting；
   - 如果要让 worker 覆盖 residual family，应先做严格 ROI gate，而不是默认扩展搜索。

## Exactness 边界

- 本轮新增字段只读；
- 不改变 Pulse DFS、候选排序、剪枝、impact filter 或 RMP 加列；
- worker 返回列仍必须 true-RC negative，并走正常 add-column path；
- incomplete / duplicate-only / no-column 不产生 certificate；
- official result 不因这些诊断字段改变。

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
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 2 tests in 0.002s
OK
```

全量回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 477 tests in 1.494s
OK (skipped=1)
```

Diff 检查：

```bash
git diff --check
```

结果：通过。

## 下一步建议

下一步不要放开 production worker，也不要做 certificate gate。建议进入：

Phase 8L：residual-aware shard scheduling / first-task priority ROI gate。

只在 hard-tail fingerprint + previous residual evidence 下启用：

- residual target first-task priority；
- small max-columns；
- strict current-context hash；
- no certificate effect；
- 继续记录 5/10 no-regression。

目标是验证：把 worker 从 `[6,19]` 引导到 `5,8,15` 这类 residual family 后，是否真的降低 follow-up tail，而不是只增加 inactive columns。
