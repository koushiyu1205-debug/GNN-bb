# GAT Batch Impact Gate Shortfall 报告

日期：2026-06-16

## 结论

本报告只审计 Stage 3 threshold frontier 的 gate shortfall，不运行 BPC、pricing、RMP 或 certificate。
它的用途是把 `stage4_candidate_ready=false` 拆成可执行的补数据 / 调阈值方向，而不是放宽 gate。

```text
total_frontier_rows = 12861
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
best_threshold_scope = global
best_threshold_mode = separate_batch_candidate
best_accepted_batch_count = 14
best_safe_precision_ci_low = 0.7846829880728186
best_safe_precision_extra_all_success_needed = 8
best_accepted_batch_roi = 0.7376467713287899
best_accepted_batch_roi_ci_low = 0.42537332534726846
best_accepted_batch_roi_ci_low_gap = 0.22462667465273156
recommended_primary = collect_more_high_roi_validation_accepts_or_improve_ranking
production_ready = false
selector_can_certificate = false
```

## Family Shortfall

```json
{
  "top_family_specific_delay_fallback_families": {
    "greedy-anchor": 20
  },
  "top_missing_accepted_families": {
    "greedy-anchor": 20
  },
  "top_missing_accepted_opportunity_families": {}
}
```

## Recommended Next Step

```json
{
  "accepted_batch_roi_ci_low_gap": 0.22462667465273156,
  "families_recommended_for_delay_fallback": [
    "greedy-anchor"
  ],
  "families_with_missed_opportunity": [],
  "primary": "collect_more_high_roi_validation_accepts_or_improve_ranking",
  "safe_precision_additional_all_success_needed": 8
}
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
