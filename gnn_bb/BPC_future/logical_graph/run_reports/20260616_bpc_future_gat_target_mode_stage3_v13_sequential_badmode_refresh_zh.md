# 2026-06-16 BPC_future GAT Target Mode Stage 3 v13 Sequential Bad-mode Refresh 报告

## 结论

本轮把 Stage 4 sequential target-materialization 失败样本转成的 workload-aware
hard-negative rows 并入 batch-impact 训练数据，并重新训练 / 审计 v13 checkpoint。

核心结论：

```text
sequential_bad_mode_rows_integrated = true
accepted_bad_mode_count = 0
stage4_candidate_ready = false
primary_blocker = family_high_roi_capture_shortfall
random_wave_high_roi_capture = 1 / 5
candidate_boost_variant_passed = false
```

v13 正确推进了标签安全性：active replacement / true-RC negative 只要造成
longer-horizon workload 变重，就会成为 hard negative / DELAY_QUEUE 信号。
但 v13 还不能进入 Stage 4 admission，因为 random-wave holdout 的 high-ROI
capture 不足。

## 输入

```text
base_dataset =
  BPC_future/data/gat_batch_impact/v10_mixed_v8_plus_random_wave_task50_5751_20260616

sequential_badmode_rows =
  BPC_future/results/gat_sequential_target_materialization_utility_rows_tranq20_01_20260616/sequential_target_materialization_utility_rows.jsonl
```

## v13 Dataset

```text
dataset =
  BPC_future/data/gat_batch_impact/v13_mixed_v10_plus_sequential_badmode_20260616
dataset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_dataset_v13_sequential_badmode_zh.md

sample_count = 326
candidate_count = 4601
batch_label_counts = {'non_improving': 69, 'roi_positive': 257}
candidate_label_counts = {'delay_queue': 324, 'high_priority': 4277}
ranking_ready = true
training_ready = true
```

相对 v10，新增的 2 个样本都是 sequential workload-aware bad-mode：

```text
accepted_batch_roi_label = -4.1412
rmp_solves_delta = +5
pricing_calls_delta = +8
exact_pricing_calls_delta = +3
generated_sequences_delta = +11106
evaluated_timed_trips_delta = +23359
```

## v13 Training

```text
training =
  BPC_future/results/gat_batch_impact_training_v13_sequential_badmode_20260616/metrics.json
training_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v13_sequential_badmode_training_zh.md

training_objective = precision_constrained_roi_maximization
checkpoint_gate_pass = false
best_loss_epoch_gate_pass = false
accepted_bad_mode_count = 0
validation_high_priority_precision = 1.0
validation_safe_precision = 1.0
validation_accepted_batch_roi = 12.850568531589074
validation_accepted_batch_roi_ci_low = 7.4080270953516765
```

Reject reasons:

```text
family_accepted_high_roi_count_below_threshold
family_high_roi_capture_rate_below_threshold
knn_ood_audit_missing
```

## Threshold Frontier

```text
threshold_frontier =
  BPC_future/results/gat_batch_impact_threshold_frontier_v13_sequential_badmode_20260616/summary.json

feasible_threshold_count = 0
best_accepted_batch_count = 29
best_safe_precision_ci_low = 0.8830264055344442
best_accepted_batch_roi_ci_low = 5.286264888364512
best_local_reject_reasons =
  family_accepted_high_roi_count_below_threshold
  family_high_roi_capture_rate_below_threshold
```

## Opportunity Mining

```text
opportunity_mining =
  BPC_future/results/gat_batch_impact_opportunity_mining_v13_sequential_badmode_20260616/summary.json

validation_high_roi_opportunities = 27
accepted_high_roi_opportunities = 18
missed_high_roi_opportunities = 9
random_wave_missed_high_roi = 4 / 5
sector_wave_missed_high_roi = 5 / 22
primary_missed_reason = no_candidate_above_threshold
```

这说明当前 v13 failure 不是 ROI point estimate 不够，也不是 precision 不够；
主要是 high-ROI batch 内的 candidate score 没稳定越过阈值，导致 family coverage
不达标。

## Candidate Boost 反例

尝试了更强的 candidate-score 训练权重：

```text
training =
  BPC_future/results/gat_batch_impact_training_v13_candidate_boost_20260616/metrics.json
training_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v13_candidate_boost_training_zh.md

hard_roi_candidate_loss_multiplier = 2.0
pairwise_ranking_loss_multiplier = 2.0
bad_mode_loss_multiplier = 4.0
validation_accepted_bad_mode_count = 0
validation_random_wave_high_roi_capture = 1 / 5
stage4_candidate_ready = false
```

该变体仍未解决 random-wave coverage；同时 train split 出现
`false_high_priority_on_delay_too_high` 和 `false_safe_rate_union_too_high` 风险。
因此后续不应继续把主要精力放在简单调大 candidate loss / pairwise loss。

## Score Margin Audit

随后对 v13 opportunity mining 的 validation records 做 candidate score margin
审计：

```text
script =
  BPC_future/scripts/audit_gat_batch_impact_score_margins.py
output =
  BPC_future/results/gat_batch_impact_score_margin_audit_v13_sequential_badmode_20260616/summary.json
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_score_margin_audit_v13_sequential_badmode_zh.md

validation_record_count = 104
candidate_threshold = 0.60591059923172
batch_threshold = 0.4583219885826111
missed_high_roi_opportunities = 9
missed_candidate_score_margin_mean = -0.29302062425348496
missed_candidate_score_margin_min = -0.46770481765270233
candidate_margin_buckets =
  deep_candidate_score_gap: 6
  moderate_candidate_score_gap: 2
  near_candidate_threshold: 1
missed_without_same_context_contrast_count = 4
```

family 分解：

```text
random-wave:
  missed_high_roi = 4
  task_count = 50
  contexts = 5751b1799b606ad1, a67f331bdb819d7d, e6b17bbf825984ae
  missed_candidate_score_margin_mean = -0.3019028417766094
  missed_without_same_context_contrast_count = 2

sector-wave:
  missed_high_roi = 5
  task_count = 20
  contexts = 45baa40751a0bf77, 9fadf4f7b39742a2, ce3508e12ad69da7
  missed_candidate_score_margin_mean = -0.28591485023498536
  missed_without_same_context_contrast_count = 2
```

这一步把 blocker 进一步收紧：当前主要不是 threshold 轻微错位。9 个 missed
high-ROI 中只有 1 个是 near-threshold，6 个是 deep candidate score gap；并且
4 个 missed high-ROI 缺少同 context low-ROI / delay 对照。推荐下一步因此是
`collect_same_context_positive_negative_pairs_for_missed_high_roi_contexts`，尤其补
random-wave task50 的 `a67f331bdb819d7d`、`e6b17bbf825984ae`，同时继续覆盖
`5751b1799b606ad1` 的 hard margin pair。

## Random-wave Task50 Margin Intervention Plan

已把上述 random-wave task50 blocker 转成 guarded target-materialization worklist：

```text
script =
  BPC_future/scripts/build_gat_batch_impact_multibatch_intervention_plan.py
output =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v13_random_wave_task50_margin_20260616/summary.json
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v13_random_wave_task50_margin_intervention_plan_zh.md
worker_runbook =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v13_random_wave_task50_margin_20260616/worker_ab_runbook/summary.json

planned_context_count = 3
selected_context_count = 2
pairwise_context_target_count = 2
candidate_count = 6
candidate_task_count_counts = {50: 6}
candidate_family_region_counts =
  random-wave|tranquillitatis_balmer_like_20km: 6
candidate_impact_bucket_counts =
  new_support_changing: 4
  new_task_set: 2
candidate_selection_ranking_counts =
  active_replacement: 2
  best_rc: 2
  impact: 2
skipped_counts =
  not_enough_unique_negative_targets: 1
all_checks_pass = true
```

selected contexts：

```text
5751b1799b606ad1:
  selected_targets = 3
  unique_negative_targets = 26
  opportunity_score = 4.385624885559082

a67f331bdb819d7d:
  selected_targets = 3
  unique_negative_targets = 5
  opportunity_score = 0.9191120266914368

e6b17bbf825984ae:
  skipped_reason = not_enough_unique_negative_targets
  unique_negative_targets = 1
```

随后已生成 explicit opt-in worker A/B runbook：

```text
worker_method = target_materialization_fixed
worker_batch_size = 1
input_candidate_count = 6
candidate_group_count = 6
all_checks_pass = true

safe_negative_action = HIGH_PRIORITY
unsafe_negative_action = DELAY_QUEUE
negative_discard_allowed = false
certificate_effect = false
```

这一步只生成 runbook 命令，不运行 BPC / pricing / RMP / worker，也不生成
certificate 或 official lower bound。6 个候选仍只是采样计划；只有显式 worker
A/B 跑完，并确认 expected context reachability、target causal match、RMP
trajectory / tail-risk 改善后，才允许转成 same-context positive/negative rows。

## 下一步

下一步优先级：

1. 补 random-wave same-context high-ROI positive / negative pairs，优先覆盖
   task50 `a67f331bdb819d7d`、`e6b17bbf825984ae`，并继续补
   `5751b1799b606ad1` 的 hard margin pair；当前 runbook 已能覆盖
   `a67f331bdb819d7d` 和 `5751b1799b606ad1`，`e6b17bbf825984ae` 需要先补
   capture/harvest，直到同 context 下有足够 unique negative targets。
2. 改进 candidate-level scoring，使 high-ROI batch 内的 safe candidate score
   稳定高于 threshold，而不是只提高 batch score。
3. 继续保留 `accepted_bad_mode_count=0` 硬 gate。
4. 在新的 candidate-ready checkpoint 出现前，不导出 Stage 4 mutating safe-source。

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
stage4_candidate_ready = false
production_ready = false
```

最终 certificate 仍只能由当前 branch/cut/dual 下的 exact pricing full closure 产生。
