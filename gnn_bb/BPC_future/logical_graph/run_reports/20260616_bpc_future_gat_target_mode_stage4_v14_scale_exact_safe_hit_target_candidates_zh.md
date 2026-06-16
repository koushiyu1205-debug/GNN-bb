# 2026-06-16 BPC_future GAT Stage 4 v14 Exact Safe-hit Target Candidates 报告

## 结论

本报告把 v14 online coverage 中的 exact safe-id hits 导出为 target-materialization
runbook 可消费的 candidates.json。它只读 safe-source、model-scored evidence 和
counterfactual replay capture 日志；不运行 BPC / pricing / RMP / worker，也不改变 admission。

```text
capture_exact_safe_hit_count = 32
selected_candidate_count = 32
selected_context_counts = {'ac056820151e9ad7': 32}
selected_pricing_kind_counts = {'exact': 32}
selected_true_reduced_cost_min = -25.4432665
selected_true_reduced_cost_max = -2.095736
candidates_path = BPC_future/results/gat_exact_safe_hit_target_candidates_v14_scale_tranq20_01_20260616/candidates.json
all_checks_pass = true
```

## Selected Task Sets

```text
[16, 20]
[16, 17]
[1, 5]
[3, 7, 15, 17]
[3, 11, 15, 17]
[3, 6, 7]
[3, 7, 8]
[3, 7, 17]
[3, 6, 11]
[3, 8, 11]
[3, 11, 17]
[9, 15, 17]
[4, 15, 17]
[3, 5, 7, 15, 16]
[3, 7, 14, 17]
[2, 5, 16]
[1, 15]
[3, 7, 14, 20]
[2, 3, 7, 15, 16]
[2, 5, 12, 13, 15]
[2, 5, 10, 12, 15]
[10, 17]
[15, 17]
[3, 15, 17]
[7, 15, 17]
[11, 15, 17]
[3, 7, 15, 17, 19]
[2, 10, 15, 16]
[5, 10, 15, 16]
[15, 20]
[16, 18]
[3, 11, 14, 20]
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
