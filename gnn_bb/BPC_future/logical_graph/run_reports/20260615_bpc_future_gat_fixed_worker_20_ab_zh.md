# GAT Fixed Worker 20-Task A/B 报告

日期：2026-06-15

## 目标

本轮验证固定 worker 口径下的 GAT 20 规模 ROI：

- GAT / kNN-OOD 只负责选择 HIGH_PRIORITY trajectory ROI 候选；
- worker 固定为 `target_materialization_fixed`；
- worker 只做 same-context target materialization，不做 Pulse 搜索、harvest、archive、bound pruning、adaptive sharding；
- 所有返回列必须走 `evaluate_timed_trip()` / `make_journey()` / `manual_journey_reduced_cost()`；
- 不产生 certificate 或 official lower bound。

## OOD/kNN 安全壳指标

使用 v14 multiscale 数据集、`scale_family` 分组阈值和同一 checkpoint 复算：

| 范围 | false-safe union | coverage | delay rate | accepted batch count | accepted batch ROI |
|---|---:|---:|---:|---:|---:|
| validation | 0.0 | 94.1% | 44.7% | 47 | 1.0 |
| all-scope | 0.0 | 96.9% | 48.6% | 151 | 1.0 |

结论：当前安全壳足够保守，false-safe 没有暴露；问题不在 OOD/kNN 误放危险样本。

## 固定 Worker Runbook

生成位置：

```text
BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_fixed_materialization_worker_ab_runbook
```

关键字段：

```text
worker_method = target_materialization_fixed
all_checks_pass = true
candidate_count = 8
```

固定 worker 命令全部满足：

- `journey_sharded_pulse_hidden_negative_worker_max_recursions=0`
- `journey_sharded_pulse_worker_current_probe_max_recursions=0`
- `journey_sharded_pulse_hidden_negative_worker_archive_enabled=False`
- `journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False`
- `journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False`
- `journey_sharded_pulse_worker_current_probe_harvesting_enabled=False`
- `journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True`

## 5/10 No-Regression

runbook 中 5/10 命令不启用 worker，只保持主线 GAT/learning。

| scale | instance | status | wall time |
|---:|---|---|---:|
| 5 | apollo15 sector-wave 01 | OPTIMAL | 2.21s |
| 5 | tranquillitatis sector-wave 01 | OPTIMAL | 2.14s |
| 10 | apollo15 sector-wave 01 | OPTIMAL | 5.33s |
| 10 | tranquillitatis sector-wave 01 | OPTIMAL | 3.62s |

结论：本轮固定 worker 改造没有影响 5/10 默认路径。

## 20-Task A/B 结果

并行度：4。总耗时约 343s。可用内存最低仍在 11GiB 以上，无内存风险。

| 候选 | baseline | worker | baseline time | worker time | delta time | delta primal | delta RMP | delta exact | worker found |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| apollo d519 target 5,1,2,18,3 | TIME_LIMIT | TIME_LIMIT | 71.5 | 90.1 | +18.6 | +0.030826 | -3 | -1 | 1 |
| apollo 67c target 5,1,15,3 | TIME_LIMIT | TIME_LIMIT | 71.3 | 71.4 | +0.1 | +0.000000 | +5 | +0 | 1 |
| apollo 62c target 2,1,5,3,12 | TIME_LIMIT | TIME_LIMIT | 90.5 | 81.8 | -8.7 | +0.000000 | +3 | +1 | 1 |
| tranq ddcb target 8,4,5,16 | TIME_LIMIT | TIME_LIMIT | 54.1 | 61.4 | +7.4 | +0.000000 | +2 | +1 | 1 |
| tranq 5c52 target 11,1,13,20 | TIME_LIMIT | TIME_LIMIT | 54.4 | 56.0 | +1.7 | +0.000000 | +3 | +1 | 1 |
| tranq 08b8 target 8,16,11,15,18 | TIME_LIMIT | TIME_LIMIT | 54.5 | 65.7 | +11.2 | +0.000000 | +3 | +4 | 1 |
| tranq e897 target 17,11,14,9 | TIME_LIMIT | TIME_LIMIT | 54.3 | 68.1 | +13.7 | +0.000000 | +3 | +4 | 1 |
| tranq 9eb0 target 2,17,16,13,18 | TIME_LIMIT | TIME_LIMIT | 54.1 | 64.6 | +10.6 | +0.000000 | +3 | +4 | 1 |

聚合：

```text
baseline_status_counts = {TIME_LIMIT: 8}
worker_status_counts = {TIME_LIMIT: 8}
worker_found_negative_total = 8
target_materialized_total = 8
worker_returned_journeys_total = 8
context_mismatch_skips_total = 59
time_delta_sum = +54.53s
rmp_delta_sum = +19
pricing_delta_sum = +33
exact_delta_sum = +14
columns_delta_sum = -40
```

## 判断

这轮结果说明：

1. GAT 选出的 HIGH_PRIORITY 候选不是假列：8/8 都在对应 context 下被固定 worker 物化为 true-RC negative。
2. OOD/kNN 也没有误放危险样本：false-safe union 为 0。
3. 但单个目标列插入没有形成求解 ROI：20 规模全部仍 TIME_LIMIT，且 RMP/pricing/exact 总调用数反而上升。
4. 主要问题不是训练标签歪，也不是 OOD 壳误放，而是控制输入太弱：每个 context 只加 1 条列，随后 dual/context 迁移，后续 59 次 worker 尝试因 `residual_target_context_mismatch` 跳过。

一句话：

GAT 当前能找到“安全且真实负 reduced-cost”的目标列，但单列 same-context intervention 还不足以稳定 20 规模 RMP trajectory。

## 下一步

不要继续扩大 worker 时间，也不要把固定 worker 默认启用。下一步应该做 batch-level trajectory intervention：

1. 同一 context 下抽取 top-k HIGH_PRIORITY 候选，而不是每个 context 只加 1 条；
2. worker 固定口径不变，但允许同一 context materialize 多条 target traces；
3. 标签仍使用 trajectory ROI，不改成 rc 标签；
4. 对比 `k=1/2/4/8` 的 20-task A/B；
5. 观察是否降低 retry / exact calls / RMP churn，而不只看是否能加列。

如果 batch-level 仍无 ROI，再转向列池/退化控制，而不是继续加强 Pulse 搜索。
