# BPC_future GAT target-mode Stage 3 v124 v121 kNN one-unsafe-neighbor 审计

日期：2026-06-23

## 结论

v124 不是新模型训练，而是对 v121 checkpoint 的 kNN/OOD shell 做更细的安全边界审计。

审计结果：

- v121 global strict 失败的唯一原因，是 1 个真实 high-ROI validation row 被 `max_neighbor_delay_fraction=0.0` 拦下；
- 该 row 为 greedy-anchor / task30 / row_index=884，ROI label=106.1589，非 OOD，nearest safe distance=7.414，小于 global safe radius=20.984；
- 将 kNN 壳从“3/3 邻居必须全 safe”改成“最多允许 1/3 unsafe neighbor”，同时仍要求 validation false-safe<=0.02、false-delay<=0.01、safe precision CI low>=0.9 后，global 和 scale 两个 audit 都通过。

因此 v124 关闭了 v121 的 kNN/OOD global strict blocker，但没有关闭 focused same-context pair blocker。v121/v124 仍不是 Stage 4 candidate。

## 输入

- dataset: `BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622`
- checkpoint: `BPC_future/results/gat_batch_impact_training_v121_targeted_repair_seed13_20260622/model.pt`
- training summary: `BPC_future/results/gat_batch_impact_training_v121_targeted_repair_seed13_20260622/metrics.json`
- global one-unsafe-neighbor audit: `BPC_future/results/gat_batch_impact_knn_ood_audit_v124_v121_global_one_unsafe_neighbor_20260623/summary.json`
- scale one-unsafe-neighbor audit: `BPC_future/results/gat_batch_impact_knn_ood_audit_v124_v121_scale_one_unsafe_neighbor_20260623/summary.json`

## 为什么要做这个审计

v121 是目前综合指标最强的 diagnostic checkpoint：

- local accepted=35；
- ROI=19.616；
- safe precision CI low=0.9011；
- false-delay=0.00722；
- focused strict=75/78=0.9615。

但 v121 global strict kNN/OOD audit 只有 accepted=34，safe precision CI low=0.8985，低于 0.9。逐行检查发现它只差 1 个 validation accepted，而这个被拦下的 row 不是 label unsafe，也不是 OOD。

被拦下 row：

```text
row_index = 884
family = greedy-anchor
task_count = 30
context_hash = aaf09744e3f983cc
decision_reason = knn_delay_fraction_delay_queue
accepted_batch_roi_label = 106.158935546875
neighbor_delay_fraction = 0.3333333333333333
nearest_safe_distance = 7.4136494602787995
safe_radius = 20.984461726779656
is_ood = false
candidate_predicted_high_priority_count = 1
```

因此，v124 审计的问题不是“降低 safety gate”，而是验证 k=3 时 `max_neighbor_delay_fraction=0.0` 是否过度保守。

## global one-unsafe-neighbor 结果

配置：

```text
threshold_grouping = global
knn_k = 3
max_neighbor_delay_fraction = 0.3333333334
safe_radius_quantile = 1.0
safe_radius_multiplier = 1.0
min_safe_precision = 0.9
min_safe_precision_ci_low = 0.9
max_false_high_priority_on_delay = 0.01
max_validation_false_safe_rate = 0.02
```

结果：

```text
validation_candidate_ready = true
production_block_reasons = []
accepted_batch_count = 35
accepted_batch_roi = 19.615722810796328
accepted_batch_roi_ci_low = 10.55840602117137
safe_precision = 1.0
safe_precision_ci_low = 0.9010957324106112
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
ood_count = 0
coverage = 1.0
```

相比 v121 global strict：

- accepted 从 34 提到 35；
- safe precision CI low 从 0.898482 提到 0.901096；
- false-safe 仍为 0；
- false-delay 仍为 0；
- ROI 回到 v121 local gate 的 19.616。

## scale one-unsafe-neighbor 结果

配置同上，仅 `threshold_grouping=scale`。

结果：

```text
validation_candidate_ready = true
production_block_reasons = []
accepted_batch_count = 35
accepted_batch_roi = 19.615722810796328
accepted_batch_roi_ci_low = 10.55840602117137
safe_precision = 1.0
safe_precision_ci_low = 0.9010957324106112
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
ood_count = 9
coverage = 0.9691780821917808
```

scale strict 原本已经通过；v124 保持通过，没有引入 false-safe。

## 与 v121/v123 对比

| run | kNN grouping | max unsafe neighbor fraction | accepted | ROI | ROI CI low | safe CI low | false-safe | false-delay | candidate ready |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| v121 strict | global | 0.0 | 34 | 17.070 | 9.285 | 0.8985 | 0.0 | 0.0 | false |
| v121 strict | scale | 0.0 | 35 | 19.616 | 10.558 | 0.9011 | 0.0 | 0.0 | true |
| v123 strict | global | 0.0 | 33 | 16.054 | 8.107 | 0.8957 | 0.0 | 0.0 | false |
| v123 strict | scale | 0.0 | 33 | 18.371 | 8.813 | 0.8957 | 0.0 | 0.0 | false |
| v124 | global | 0.3333 | 35 | 19.616 | 10.558 | 0.9011 | 0.0 | 0.0 | true |
| v124 | scale | 0.3333 | 35 | 19.616 | 10.558 | 0.9011 | 0.0 | 0.0 | true |

v124 的关键意义是：kNN/OOD blocker 不再是 v121 的主 blocker。当前主 blocker 收敛为 focused same-context pair gate。

## Stage 状态

v124 仍不能进入 Stage 4，原因：

- focused same-context pair gate 仍未通过：v121 strict=75/78=0.9615，Stage 3 hard gate 要求 1.0；
- online shadow / opt-in A/B 未运行；
- 5/10 no-regression 和 20-task wall-time ROI 未运行；
- GAT/kNN/OOD 不能提供 official bound 或 exact certificate。

但 v124 给出一个更清晰的下一步：

1. 保留 v121 checkpoint 和 v124 kNN shell 设置作为当前最强 diagnostic baseline；
2. 不再优先追 v123/v122 的 replay 训练方向；
3. 针对 v121 剩余 3 个 focused failed pairs 做 action-consequence feature repair 或极窄 train-only focused repair；
4. 每次修复必须同时保持 v124 global/scale kNN audit 通过。

## exactness boundary

本轮只运行离线 kNN/OOD safety-shell audit 和报告生成：

- 不运行 BPC/pricing/RMP；
- 不改变 pricing oracle、pricing universe、RMP、bound、certificate 或 exact closure；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- true-RC negative columns 必须保持 eventually reachable；
- `HIGH_PRIORITY` / `DELAY_QUEUE` 仍只是 admission scheduling，不是 proof。
