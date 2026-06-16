# 2026-06-16 BPC_future GAT Target Mode Stage 3 v14 Safety Frontier 报告

## 结论

本轮完成 v14 threshold frontier、kNN/OOD safety shell 和 safe-source export。

核心结果：

```text
threshold_only_feasible = false
global_knn_ood_candidate_ready = true
scale_knn_ood_candidate_ready = true
family_knn_ood_candidate_ready = false
scale_family_knn_ood_candidate_ready = false
v14_global_safe_source_ready = true
v14_scale_safe_source_ready = true
production_ready = false
stage4_mutating_admission_ready = false
```

解释：v14 raw threshold 仍不能自己通过 Stage 3 gate，但 strict global / scale
kNN-OOD shell 能把 false HIGH_PRIORITY / false-safe 从 `2 / 79` 过滤到 `0`，
同时保留非零 accepted batch ROI。因此 v14 可以作为 offline safe-source candidate
进入 Stage 4 shadow / online coverage audit，不能直接进入 mutating opt-in 或
production。

## Threshold Frontier

输入：

```text
dataset =
  BPC_future/data/gat_batch_impact/v14_mixed_v13_plus_random_wave_task50_margin_tl130_20260616
training =
  BPC_future/results/gat_batch_impact_training_v14_random_wave_task50_margin_tl130_20260616/metrics.json
frontier =
  BPC_future/results/gat_batch_impact_threshold_frontier_v14_random_wave_task50_margin_tl130_20260616/summary.json
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_threshold_frontier_v14_random_wave_task50_margin_tl130_zh.md
```

结果：

```text
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0

best_global:
  accepted_batch_count = 35
  accepted_batch_roi_ci_low = 5.2559083249600445
  safe_precision_ci_low = 0.9010957324106112
  false_high_priority_on_delay = 0.3924050632911392
  false_safe_rate_union = 0.3924050632911392

best_family_local:
  accepted_batch_count = 20
  accepted_batch_roi_ci_low = 6.838762183273009
  safe_precision_ci_low = 0.8388698745050667
  false_high_priority_on_delay = 0.0
  false_safe_rate_union = 0.0
```

threshold-only 结论是两难：

- 保留较多 ROI / coverage 时 false-safe 过高；
- 严格到 zero false-safe 时 accepted count / safe CI / family capture 不够；
- 因此不能靠事后调 threshold 把 v14 raw model 升级成 Stage 4 candidate。

## kNN/OOD Safety Shell

四个 strict 配置均使用：

```text
knn_k = 3
max_neighbor_delay_fraction = 0.0
safe_radius_quantile = 1.0
safe_radius_multiplier = 1.0
max_false_high_priority_on_delay = 0.01
max_validation_false_safe_rate = 0.02
min_safe_precision = 0.90
min_safe_precision_ci_low = 0.85
min_accepted_batch_roi = 0.65
min_accepted_batch_roi_ci_low = 0.65
```

结果对比：

| grouping | candidate ready | accepted | ROI | ROI CI low | safe CI low | false-safe | blockers |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| global | true | 25 | 8.059135 | 3.113815 | 0.866804 | 0.0 | [] |
| scale | true | 23 | 7.057524 | 2.108712 | 0.856879 | 0.0 | [] |
| family | false | 14 | 0.472209 | 0.323547 | 0.784683 | 0.0 | ROI / safe CI below gate |
| scale_family | false | 14 | 0.472209 | 0.323547 | 0.784683 | 0.0 | ROI / safe CI below gate |

global 和 scale 均通过 Stage 3 offline kNN/OOD safety gate。family / scale_family
过保守，虽然 false-safe 也是 0，但 ROI 和 safe precision CI 不够。

## Safe-source Export

导出前发现 `export_gat_batch_impact_safe_source.py` 只认 raw training gate，
会错误挡住“raw false-safe 失败、但 kNN/OOD 已修复”的模型。已把 export gate
收紧为：

```text
raw training gate pass
OR
all training reject reasons are kNN/OOD-repairable raw safety reasons
AND kNN/OOD validation_candidate_ready = true
AND kNN/OOD validation_safety_ready = true
```

允许修复的 raw training reject reason 只有：

```text
false_high_priority_on_delay_too_high
false_safe_rate_union_too_high
knn_ood_audit_missing
```

ROI、ROI-CI、coverage、family capture、precision CI 等失败仍不能被 kNN/OOD
绕过。

导出结果：

```text
global_safe_source =
  BPC_future/results/gat_batch_impact_safe_source_v14_random_wave_task50_margin_tl130_global_20260616/safe_source.json
  safe_source_ready = true
  safe_candidate_id_count = 1226
  high_priority_decision_record_count = 59
  blockers = []

scale_safe_source =
  BPC_future/results/gat_batch_impact_safe_source_v14_random_wave_task50_margin_tl130_scale_20260616/safe_source.json
  safe_source_ready = true
  safe_candidate_id_count = 1198
  high_priority_decision_record_count = 56
  blockers = []
```

两个 safe-source 都保持：

```text
diagnostic_only = true
production_ready = false
default_enabled = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## Exactness Boundary

本轮新增脚本运行全部是 offline / diagnostic-only：

- 不运行 BPC / pricing / RMP；
- 不生成 official bound；
- 不产生 no-negative certificate；
- safe candidate ids 只能用于已经 true-RC verified negative journeys 的
  `HIGH_PRIORITY` admission scheduling；
- unsafe 只能表示 `DELAY_QUEUE`，不能 reject；
- final certificate 仍必须由当前 branch/cut/dual 下 exact pricing 对完整配置宇宙
  执行 no-negative closure。

## 下一步

1. 用 v14 global safe-source 做 Stage 4 online coverage audit，先看 exact-id /
   sequence / task-set / context-compatible hit-rate。
2. 如果 online safe-source hit 仍为 0，继续走 model-scored online safe-source
   audit，不得直接启用 mutating delay。
3. 对 global 与 scale 的差异做 Stage 4 shadow 对比：global ROI 更高，scale 稍窄；
   二者都必须先通过 5/10 pass-through no-regression 和 20-task online coverage。
4. 继续补 `a67f331bdb819d7d`、`e6b17bbf825984ae` 的 same-context rows，作为
   下一轮泛化与 safety margin 数据。
