# 2026-06-16 BPC_future GAT Target Mode Stage 4 Target-materialization Batch A/B 报告

## 结论

本轮执行 20-task `sector-wave/tranquillitatis` same-context target-materialization A/B。
实验仍是显式 opt-in worker，不启用 admission scheduler，不产生 certificate，不改变默认配置。

核心结论：

- 单列 true-RC negative 不是足够的 RMP trajectory 改善目标；
- 同 context batch materialization 比单列更好，但当前 batch 仍主要是 inactive-only；
- 真正推动最终 incumbent 的还是后续 exact batch 里的 `active_replacement_task_set`；
- 下一步训练/采样目标必须转向 active-support / replacement-aware batch impact，而不是继续扩大普通 task-set overlap 负列。

```text
stage4_target_materialization_probe = completed
production_ready = false
stage5_ready = false
certificate_ready = false
```

## 输入

实例：

```text
BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json
```

候选来源：

```text
BPC_future/results/gat_online_shadow_target_candidates_v10_tranq20_01_20260616/candidates.json
```

runbook：

```text
BPC_future/results/gat_target_priority_worker_ab_v10_online_shadow_candidates_20260616/summary.json
BPC_future/results/gat_target_priority_worker_ab_v10_online_shadow_batch5_20260616/summary.json
BPC_future/results/gat_target_priority_worker_ab_v10_online_shadow_batch8_20260616/summary.json
```

## 运行结果

所有运行最终仍为：

```text
status = TIME_LIMIT
primal_bound = 632.987632
dual_bound = None
```

因此本轮不能证明 20-task optimality，也不能进入 Stage 5。

| run | worker returned | immediate RMP after target | time | rmp | pricing | exact | generated | evaluated | columns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| shared baseline | 0 | 632.987632 after exact batch | 53.477662 | 9 | 14 | 5 | 30378 | 48696 | 236 |
| single `[1,5]` | 1 | 635.508935 | 52.826863 | 10 | 16 | 6 | 32443 | 53274 | 235 |
| single `[16,20]` | 1 | 655.276646 | 52.901764 | 10 | 16 | 6 | 32560 | 53368 | 233 |
| batch5 | 5 | 635.508935 | 52.529435 | 9 | 14 | 5 | 30302 | 48610 | 224 |
| batch7 | 7 | 635.508935 | 52.495316 | 9 | 14 | 5 | 30293 | 48612 | 226 |

batch5 物化：

```text
[1, 5]
[3, 8, 11]
[9, 15, 17]
[4, 15, 17]
[16, 20]
```

batch7 额外加入：

```text
[16, 17]
[10, 17]
```

## 关键轨迹诊断

baseline 在 `cg_iter=7` 的 exact batch 返回 48 条列：

```text
best_true_rc = -25.4432665
added_journeys = 48
active_changed_task_set_count = 3
addition_productivity_class = active_replacement_task_set
next_rmp_objective = 632.987632
```

single `[1,5]`：

```text
worker_true_rc = -19.76771125
returned_journeys = 1
added_journeys = 1
active_changed_task_set_count = 0
addition_productivity_class = changed_inactive_only
next_rmp_objective = 635.508935
followup_exact_required = true
```

single `[16,20]`：

```text
worker_true_rc = -25.4432665
returned_journeys = 1
added_journeys = 1
active_changed_task_set_count = 0
addition_productivity_class = changed_inactive_only
next_rmp_objective = 655.276646
followup_exact_required = true
```

batch5 / batch7：

```text
worker_best_true_rc = -25.4432665
worker_returned_journeys = 5 / 7
active_changed_task_set_count = 0
addition_productivity_class = changed_inactive_only
next_rmp_objective = 635.508935
followup_exact_batch_returned = 48
followup_exact_addition_productivity_class = active_replacement_task_set
```

解释：worker 能按 expected context 物化 true-RC negative columns，但这些列没有立刻改变 active support。
最终 incumbent 仍依赖后续 exact batch 的 active replacement 列族。

## 判定

```text
single_column_roi_gate = failed
naive_task_set_overlap_batch_roi_gate = weak_positive_but_insufficient
active_replacement_batch_needed = true
mutating_admission_ready = false
stage5_ready = false
```

本轮有一个弱正信号：batch5 / batch7 相比 shared baseline 的 generated / evaluated workload 和 wall-time 均小幅下降，且 rmp/pricing/exact call 数没有增加。
但这个点估计太弱，不能作为 Stage 4 opt-in ROI gate 通过证据。

## Exactness Boundary

本轮保持：

```text
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
certificate_ready = false
default_enabled = false
```

所有运行都是 `TIME_LIMIT` 且 `dual_bound=None`。最终 certificate 仍必须由当前 branch/cut/dual 下的 exact pricing 对完整配置宇宙重新确认无负 reduced-cost journey。

## 下一步

1. 从 exact capture batch 中抽取 `active_changed_task_set_samples` / `replacement_task_set_samples` 对应列，生成 active-replacement target batch。
2. 把 Stage 3/4 训练和候选选择从 `true-RC negative` / task-set overlap 改成 active-support / replacement-aware batch impact。
3. 继续保持 precision / ROI / false-safe 硬门槛；不要把 task-set overlap 直接升级为 safe-source。
4. 只有 active-replacement batch 在 20-task 上产生稳定 tail / exact workload ROI 后，才允许继续 mutating admission A/B。
