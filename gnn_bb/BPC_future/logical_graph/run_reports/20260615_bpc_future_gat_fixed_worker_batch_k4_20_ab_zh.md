# GAT Fixed Worker Batch-k4 20-Task A/B 报告

日期：2026-06-15

## 目标

本轮在固定 worker 口径下验证 batch-level trajectory intervention：

- GAT + kNN/OOD 只负责选择 HIGH_PRIORITY trajectory ROI 候选；
- worker 固定为 `target_materialization_fixed`；
- 每个 same-context 一次 materialize 4 条 target journeys；
- worker 不做 Pulse 搜索、harvest、archive、bound pruning、adaptive sharding；
- 所有返回列必须通过 `evaluate_timed_trip()` / `make_journey()` / `manual_journey_reduced_cost()`；
- 不产生 certificate 或 official lower bound。

## OOD/kNN 安全壳指标

使用 v14 multiscale 数据集、`scale_family` 分组阈值和同一 checkpoint 复算。

| 范围 | false-safe union | coverage | delay rate | accepted batch count | accepted batch ROI |
|---|---:|---:|---:|---:|---:|
| validation | 0.0 | 94.1% | 44.7% | 47 | 1.0 |
| all-scope | 0.0 | 96.9% | 48.6% | 151 | 1.0 |

结论：OOD/kNN safety shell 目前不是瓶颈。它没有把 OOD / unsafe 样本误放成 safe，且 coverage 不是过低。

## Batch-k4 Candidate Set

候选生成位置：

```text
BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates_scale_family_task020_batch_k4
```

关键字段：

```text
candidate_count = 32
context_group_count = 8
max_targets_per_context = 4
all_checks_pass = true
```

每个 20-task same-context group 保留 4 条 `new_support_changing` 候选，避免单列 intervention 太弱。

## 固定 Worker Runbook

生成位置：

```text
BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/scale_family_task020_fixed_materialization_batch_k4_worker_ab_runbook
```

关键字段：

```text
worker_method = target_materialization_fixed
worker_batch_size = 4
input_candidate_count = 32
candidate_group_count = 8
worker_count = 8
all_checks_pass = true
```

固定 worker 命令全部满足：

- `journey_sharded_pulse_hidden_negative_worker_max_recursions=0`
- `journey_sharded_pulse_worker_current_probe_max_recursions=0`
- `journey_sharded_pulse_hidden_negative_worker_archive_enabled=False`
- `journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False`
- `journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False`
- `journey_sharded_pulse_worker_current_probe_harvesting_enabled=False`
- `journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True`
- 使用 `journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys=[...]` 批量注入 4 条目标 journey。

## 20-Task A/B 结果

并行度：4。16 条命令全部完成，无失败。可用内存最低仍在 11GiB 以上，无内存风险。

| 候选组 | baseline | worker | baseline time | worker time | delta time | delta primal | delta RMP | delta exact | returned journeys |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| apollo d519 batch4 | TIME_LIMIT | TIME_LIMIT | 72.6 | 90.2 | +17.6 | 0.0 | -2 | 0 | 4 |
| apollo 67c batch4 | TIME_LIMIT | TIME_LIMIT | 73.1 | 90.4 | +17.3 | 0.0 | +4 | -1 | 4 |
| apollo 62c batch4 | TIME_LIMIT | TIME_LIMIT | 70.4 | 90.6 | +20.1 | 0.0 | 0 | 0 | 4 |
| tranq ddcb batch4 | TIME_LIMIT | TIME_LIMIT | 54.4 | 60.4 | +6.0 | 0.0 | +2 | +1 | 4 |
| tranq 5c52 batch4 | TIME_LIMIT | TIME_LIMIT | 54.3 | 75.0 | +20.7 | 0.0 | +6 | +8 | 4 |
| tranq 08b8 batch4 | TIME_LIMIT | TIME_LIMIT | 54.3 | 63.2 | +8.8 | 0.0 | +2 | +2 | 4 |
| tranq e897 batch4 | TIME_LIMIT | TIME_LIMIT | 54.3 | 68.4 | +14.1 | 0.0 | +3 | +4 | 4 |
| tranq 9eb0 batch4 | TIME_LIMIT | TIME_LIMIT | 54.4 | 59.1 | +4.7 | 0.0 | +2 | +2 | 4 |

聚合：

```text
baseline_status_counts = {TIME_LIMIT: 8}
worker_status_counts = {TIME_LIMIT: 8}
worker_found_negative_total = 8
target_materialized_total = 8
worker_returned_journeys_total = 32
context_mismatch_skips_total = 60
time_delta_sum = +109.26s
rmp_delta_sum = +17
pricing_delta_sum = +33
exact_delta_sum = +16
columns_delta_sum = -14
```

## 判断

这轮比单列测试更强，因为每个 context 都成功加入 4 条 true-RC negative journeys。结果仍然没有 20-task ROI：

1. 所有 worker run 仍是 `TIME_LIMIT`；
2. `worker_returned_journeys_total=32`，说明 GAT 选择的列能被固定 worker 真实物化；
3. `delta_primal=0`，说明这些列没有带来可观 primal 改善；
4. `rmp_delta_sum=+17`、`pricing_delta_sum=+33`、`exact_delta_sum=+16`，说明 batch 注入反而增加了后续求解负担；
5. `context_mismatch_skips_total=60`，说明同一 context 注入后，dual / residual context 很快迁移，后续 target materialization 不再适用。

一句话：

当前失败不是 OOD/kNN 误判，也不是 target materialization 找不到负列，而是 HIGH_PRIORITY 候选的“真实负 reduced cost”与“长程 trajectory 稳定/加速”仍然没有对齐。

## 结论

不要继续简单扩大 worker time limit、增加 Pulse 搜索、或把 worker 默认开启。

下一步应该转向 trajectory 后效分析：

1. 明确记录 worker 注入后的下一轮 RMP objective delta；
2. 记录下一轮 dual L1 delta / support churn；
3. 记录 follow-up legacy final judge / completion retry 是否减少；
4. 用这些后效重新校准 GAT/ranking，而不是只看 same-context true-RC negative；
5. 负列仍然只能 HIGH_PRIORITY 或 DELAY_QUEUE，不能永久丢弃，也不能参与 certificate。

