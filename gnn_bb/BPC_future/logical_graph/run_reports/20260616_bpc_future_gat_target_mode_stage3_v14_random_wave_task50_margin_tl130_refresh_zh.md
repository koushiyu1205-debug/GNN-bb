# 2026-06-16 BPC_future GAT Target Mode Stage 3 v14 Random-wave Task50 Margin Refresh 报告

## 结论

本轮沿着 v13 score-margin audit 的结论，针对 random-wave task50
`5751b1799b606ad1` context 执行了 guarded target-materialization worker A/B，
并把 85s 下缺失 post-worker RMP 的问题修正为 130s diagnostic probe。

核心结论：

```text
same_context_pair_collected = true
row_builder_all_checks_pass = true
dataset_v14_built = true
training_v14_finished = true
random_wave_family_capture_shortfall_fixed_in_validation = true
stage4_candidate_ready = false
new_primary_blocker =
  false_high_priority_on_delay_too_high
  false_safe_rate_union_too_high
  knn_ood_audit_missing
```

v14 说明补 same-context hard margin pair 的方向是对的：random-wave holdout
high-ROI capture 从 v13 的 `1 / 5` 提升到 `4 / 6`。但 v14 仍不能进入 Stage 4，
因为安全 gate 变成主 blocker：validation false HIGH_PRIORITY on delay 为
`2 / 79 = 2.5316%`，超过当前 Stage 3/4 上限。

## 85s Probe 反例

先按原 runbook 跑了 `5751b1799b606ad1` 的第一组 baseline / worker：

```text
baseline_csv =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v13_random_wave_task50_margin_20260616/worker_ab_runbook/task050_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks050_04_seed91307_5751b1799b606ad1_mb1_4_40_3_mainline_baseline/results.csv
worker_csv =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v13_random_wave_task50_margin_20260616/worker_ab_runbook/task050_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks050_04_seed91307_5751b1799b606ad1_mb1_4_40_3_target_priority_worker/results.csv

baseline status = TIME_LIMIT
baseline primal = 1404.72385
baseline dual_bound = none
baseline rmp/pricing/exact = 44 / 45 / 1

worker status = TIME_LIMIT
worker primal = 1387.386078
worker dual_bound = none
worker rmp/pricing/exact = 44 / 46 / 2
```

日志确认 worker 在 `cg_iter=44` 命中 expected context 并物化 true-RC negative，
但该 hit 发生在 time-limit 末尾，之后没有 `cg_iter+1` 的 `journey_rmp`。严格
row builder 因此拒绝输出训练 row：

```text
row_builder_status = no_rows
skipped_counts = {'missing_worker_before_or_after_rmp': 1, 'missing_worker_logs': 5}
```

这个反例很重要：CSV-level primal improvement 不能直接贴训练标签。必须有
worker target causal match 和 post-worker RMP state，才能进入 Stage 3 数据。

## 130s Same-context Pair

随后把同 context 的前两组 target worker 以相同安全边界延长到 130s，只为观察
post-worker RMP state：

```text
derived_runbook =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v13_random_wave_task50_margin_tl130_20260616/worker_ab_runbook/summary.json
worker_rows =
  BPC_future/results/gat_multibatch_worker_rows_v13_random_wave_task50_margin_tl130_20260616/summary.json
row_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v13_random_wave_task50_margin_tl130_worker_rows_zh.md

candidate_count = 2
row_count = 2
context_count = 1
pairwise_context_count = 1
largest_context_size = 2
all_checks_pass = true
```

两条 row 均来自同一 context / 同一 `cg_iter=44`，且都由当前 true dual 下的
target-materialization worker 物化为 true-RC negative：

| target | true RC | RMP before | RMP after | improvement | class |
| --- | ---: | ---: | ---: | ---: | --- |
| `[4,40,3]` | -11.539468769 | 1349.923664 | 1345.538039 | 4.385625 | changed_inactive_only |
| `[4,8,25,32,45,9]` | -2.633324538 | 1349.923664 | 1349.898806 | 0.024858 | changed_inactive_only |

这正是 Stage 3 需要的 hard margin pair：同 context、同 dual/cut/branch/pool
状态下，两个 true-RC negative 都能加入，但 trajectory utility 相差两个数量级。
训练不能只学 `rc < 0`，也不能只学 active replacement；必须学
`score(strong ROI) > score(weak ROI)`。

## v14 Dataset

将这两条 row 追加到 v13 mixed dataset 源列表，生成 v14：

```text
dataset =
  BPC_future/data/gat_batch_impact/v14_mixed_v13_plus_random_wave_task50_margin_tl130_20260616
dataset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_dataset_v14_random_wave_task50_margin_tl130_zh.md

sample_count = 328        # v13: 326
candidate_count = 4603    # v13: 4601
random_wave_samples = 199 # v13: 197
task50_samples = 95       # v13: 93
same_context_pair_count = 79          # v13: 68
same_context_comparable_pair_count = 76 # v13: 67
task50_same_context_pair_count = 21   # v13: 10
training_ready = true
ranking_ready = true
all_checks_pass = true
```

该 dataset 仍保持：

```text
runs_bpc_or_pricing = false
production_ready = false
certificate_source = false
official_bound_effect = false
```

## v14 Training

使用 v13 同类 hard gate 训练 v14：

```text
training =
  BPC_future/results/gat_batch_impact_training_v14_random_wave_task50_margin_tl130_20260616/metrics.json
training_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v14_random_wave_task50_margin_tl130_training_zh.md

training_objective = precision_constrained_roi_maximization
checkpoint_selection = deployment_gate_first_then_roi_ci_baseline_utility_loss
best_epoch = 7
best_loss_epoch = 7
checkpoint_gate_pass = false
stage4_candidate_ready = false
```

validation deployment metrics：

```text
accepted_batch_count = 34
accepted_batch_roi = 9.270531552487656
accepted_batch_roi_ci_low = 5.325235030723549
high_priority_precision = 0.9980601357904947
high_priority_precision_ci_low = 0.9929545460660191
safe_precision = 1.0
safe_precision_ci_low = 0.8984820937803899
accepted_bad_mode_count = 0
```

family holdout 结果相对 v13 明显改善：

```text
random-wave:
  accepted_batch_count = 8
  accepted_batch_roi = 1.4432105637388304
  accepted_high_roi_count = 4 / 6
  high_roi_capture_rate = 0.6666666666666666
  safe_precision = 1.0

sector-wave:
  accepted_batch_count = 26
  accepted_batch_roi = 11.678938010564217
  accepted_high_roi_count = 19 / 22
  high_roi_capture_rate = 0.8636363636363636
  safe_precision = 1.0

greedy-anchor:
  oracle_high_roi_count = 0
  accepted_batch_count = 0
  family_specific_delay_fallback = legal
```

v13 的主 blocker 是：

```text
family_accepted_high_roi_count_below_threshold
family_high_roi_capture_rate_below_threshold
knn_ood_audit_missing
```

v14 的主 blocker 变成：

```text
false_high_priority_on_delay_too_high
false_safe_rate_union_too_high
knn_ood_audit_missing
```

具体数值：

```text
false_high_priority_on_delay = 0.02531645569620253
false_high_priority_on_delay_count = 2
delay_label_count = 79
false_safe_rate_union = 0.02531645569620253
```

因此 v14 不能放宽安全门槛进入 Stage 4。正确下一步不是继续降低 threshold 或追
更多 accepted coverage，而是针对这两个 false-safe / false HIGH_PRIORITY 样本做
threshold frontier、kNN/OOD safety shell 和 hard-negative row 采集。

## Exactness Boundary

本轮所有新增结果仍是 diagnostic：

- 85s/130s worker run 只用于 target-materialization intervention 采样；
- worker 返回列进入 RMP 前由当前 true dual / cut / branch 做 true-RC；
- worker result 不能 certificate；
- row builder / dataset / training 都不运行 BPC / pricing / RMP；
- v14 checkpoint 不是 Stage 4 candidate；
- final certificate 仍只能由当前 branch/cut/dual 下的 exact pricing full closure 给出。

## 下一步

1. 对 v14 跑 threshold / safety frontier，目标是在 `false_safe_rate_union <= 1%~2%`
   下保留 random-wave high-ROI capture；如果无 feasible threshold，则必须补
   false-safe 对应 context 的 hard-negative rows。
2. 对 v14 跑 kNN/OOD audit，确认安全壳能否过滤这 2 个 false HIGH_PRIORITY。
3. 继续补 `a67f331bdb819d7d` 和 `e6b17bbf825984ae` 的 same-context pair；
   `e6...` 当前还缺 unique negative targets，需要先补 capture/harvest。
4. Stage 4 仍保持关闭；在 false-safe / OOD / no-regression / 20 ROI A/B 之前，
   不导出 mutating safe-source。
