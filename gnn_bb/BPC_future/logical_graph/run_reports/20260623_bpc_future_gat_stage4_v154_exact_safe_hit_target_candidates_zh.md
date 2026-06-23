# 2026-06-16 BPC_future GAT Stage 4 v14 Exact Safe-hit Target Candidates 报告

## 结论

本报告把 v14 online coverage 中的 exact safe-id hits 导出为 target-materialization
runbook 可消费的 candidates.json。它只读 safe-source、model-scored evidence 和
counterfactual replay capture 日志；不运行 BPC / pricing / RMP / worker，也不改变 admission。

```text
capture_exact_safe_hit_count = 115
selected_candidate_count = 8
selected_context_counts = {'b095fbae18116443': 4, 'dd1c3812ce457e30': 2, 'ea2f1344458c548f': 2}
selected_pricing_kind_counts = {'exact': 6, 'heuristic': 2}
selected_true_reduced_cost_min = -81.758497
selected_true_reduced_cost_max = -62.285026824
candidates_path = BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_target_candidates_top8/candidates.json
all_checks_pass = true
```

## Selected Task Sets

```text
[2, 3, 8, 18]
[2, 3, 8]
[3, 8, 18, 20]
[6, 8, 18, 20]
[3, 8, 20]
[1, 11]
[1, 11]
[6, 8, 20]
```

## 判定

这些候选已经是 exact safe-id hit，但仍只表示候选可被定位；
它们尚未证明加入 RMP 后会改善 objective、dual、basis、tail retry 或 certificate tail。

```text
stage4_mutating_admission_ready = false
next_step = target_materialization_online_trajectory_roi_ab
```

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
```
