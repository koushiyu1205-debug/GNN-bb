# GAT scale-family same-run 20 worker A/B 报告

日期：2026-06-15

## 目标

本轮不继续采样，也不重新定义标签。目标是在同一批 v14 multiscale same-run ROI 数据上验证：

1. 只改 kNN/OOD 安全壳校准方式，是否能提高 HIGH_PRIORITY 召回；
2. 是否能抽取真实 20 规模 HIGH_PRIORITY worker target；
3. worker 是否真实命中目标 context，而不是再次出现 context mismatch；
4. 对一个真实 20 实例的 90s 窄 A/B 是否出现加速信号。

## 代码改动

修改 `BPC_future/scripts/audit_gat_same_run_batch_impact_knn_ood.py`：

- 新增 `--threshold-grouping={global,scale,family,scale_family}`；
- 分组内同时有 HIGH_PRIORITY 和 DELAY_QUEUE 训练证据时，使用组内 threshold / kNN / safe-radius；
- 分组过小或单标签时，自动回退 global guard；
- decision records 增加：
  - `decision_name`
  - `instance_task_count`
  - `instance_family`
  - `threshold_group`
  - `threshold_scope`

新增/更新 focused tests：

- 默认 global 行为保持；
- scale/family sparse group 必须 fallback global；
- decision record 保留候选提取所需字段。

## 离线 GAT+kNN/OOD 审计

数据集：

```text
BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_graph_dataset
```

checkpoint：

```text
BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_same_run_batch_impact_training/context_aware_bulk_sampling_gat.pt
```

对比结果：

| guard | validation HP precision | validation HP recall | delay recall | validation FP | decision-scope HP recall |
|---|---:|---:|---:|---:|---:|
| global | 1.000 | 0.565 | 1.000 | 0 | 0.580 |
| scale | 1.000 | 0.652 | 1.000 | 0 | 0.623 |
| family | 1.000 | 0.667 | 1.000 | 0 | 0.632 |
| scale_family | 1.000 | 0.681 | 1.000 | 0 | 0.654 |

结论：

- `scale_family` 是当前最好校准；
- 在不增加训练样本、不改模型、不改标签的情况下，验证集召回从 `0.565` 提升到 `0.681`；
- 仍保持 `false HIGH_PRIORITY on DELAY_QUEUE = 0`；
- 这说明之前召回不足有一部分来自全局安全壳过保守，不完全是 GAT 表达能力问题。

## 20 规模候选抽取

命令使用 `scale_family` decision records，只抽 `tasks=20`：

```text
BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates_scale_family_task020
```

结果：

```text
candidate_count = 8
candidate_task_count_counts = {"20": 8}
candidate_impact_bucket_counts = {"new_support_changing": 8}
candidate_new_task_set_count = 8
candidate_support_changing_proxy_count = 8
candidate_replacement_like_proxy_count = 0
all_checks_pass = true
```

结论：

- 8 个候选全部是 20 规模；
- 全部是 true-RC negative；
- 全部是 new task set；
- 全部是 support-changing proxy；
- 这说明 same-run GAT+kNN/OOD 可以产生可执行的 20 规模 worker target。

## 真实 20 窄 A/B

实例：

```text
BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json
```

候选：

```text
context = d519291840dd7000
target_sequence = [5, 1, 2, 18, 3]
target_true_rc = -9.973161
capture_cg_iter = 1
```

90s A/B 结果：

| run | status | time | primal | rmp | pricing | exact | columns |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline | TIME_LIMIT | 90.312s | 619.142683 | 12 | 24 | 12 | 240 |
| worker | TIME_LIMIT | 90.077s | 619.173509 | 9 | 19 | 10 | 241 |

worker 日志确认：

```text
cg_iter = 1
pulse_worker_status = FOUND_NEGATIVE
pulse_worker_context_hash = d519291840dd7000
pulse_worker_returned_journeys = 1
pricing_kind = sharded_pulse_hidden_negative_worker
pricing_state = FOUND_NEGATIVE
reason = target_materialized_negative_true_rc
```

后续 worker attempts：

```text
cg_iter 2/4/5/6/7/8/9: residual_target_context_mismatch
```

## 判断

这次不是上一轮那种“worker 没触发”的无效 A/B。worker 确实在 `cg_iter=1` 命中目标 context，并通过 target materialization 加入了 1 条 true-RC negative 列。

但本轮没有观察到求解加速：

- worker 仍然 TIME_LIMIT；
- primal 略差；
- columns 只多 1；
- RMP/pricing/exact 轮次数减少，但这更像轨迹改变，不足以证明 ROI；
- 后续 context 快速偏离，worker 只在第一个目标 context 有效，之后全部 context mismatch。

当前结论：

```text
GAT 表达/安全壳不是完全失败；
scale_family 校准能提高召回并保持安全；
worker target 可以真实命中并加列；
但单个 HIGH_PRIORITY target 仍不能稳定改善 20-task tail。
```

## 失败原因倾向

更像是部署策略/控制策略不足，而不是单纯训练样本不足或 GAT 架构无效：

1. 模型能筛出 20 规模 new_support_changing 候选；
2. 安全壳能保持 0 false HIGH_PRIORITY；
3. worker 能把候选转成真实列；
4. 但只加 1 条列不足以稳定改变 20 规模 dual trajectory；
5. 加列后 context 变化，后续 target 全部 mismatch，说明 static target replay 不是稳定 worker policy。

## 下一步建议

不要继续扩大 worker time limit，也不要把 official certificate gate 打开。

更合理的下一步：

1. 用 `scale_family` guard 作为当前默认离线安全壳；
2. 对 20 规模 HIGH_PRIORITY 候选做 batch-level intervention，而不是单 target；
3. worker 一次最多加入多个同 context HIGH_PRIORITY / support-changing targets；
4. A/B 指标看下一轮 objective delta、dual_l1_delta、completion retry 是否下降；
5. 如果 batch intervention 仍无 ROI，再判断是 GAT trajectory impact 标签不够，还是 Pulse worker 本身加列强度不足。

当前不应下结论说“训练不够”：

- 召回不足已被分组校准改善；
- 单 target worker 的无 ROI 不能证明训练样本不足；
- 真正需要验证的是 batch-level HIGH_PRIORITY 是否能稳定推动 RMP trajectory。

