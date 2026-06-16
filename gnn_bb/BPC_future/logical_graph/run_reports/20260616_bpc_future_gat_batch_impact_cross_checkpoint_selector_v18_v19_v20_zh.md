# GAT Batch Impact Cross-Checkpoint Selector Audit 报告

日期：2026-06-16

## 目的

本报告检查 v18/v19/v20 这类 checkpoint 能否通过固定组合规则，把 v18 的
coverage 和 v19/v20 的 low-ROI suppression 合并成一个 coverage-constrained
ROI admission selector。它只使用已有 opportunity-mining validation records，
不运行 BPC、pricing、RMP、worker 或 certificate。

## 结论

```text
validation_record_count = 119
minimum_all_success_count_for_safe_precision_ci = 35
feasible_rule_count = 0
best_diagnostic_rule = v18_and_v19
best_diagnostic_accepted_count = 20
best_diagnostic_roi = 8.33569827824831
best_diagnostic_roi_ci_low = 2.2722559375239006
best_diagnostic_safe_precision_ci_low = 0.8388698745050667
best_diagnostic_low_roi_or_bad = 9
best_diagnostic_family_min_roi = 0.4911726514498393
recommended_primary = collect_reachability_valid_same_context_contrast_before_more_threshold_tuning
production_ready = false
selector_can_certificate = false
```

## Rule Frontier

| rule | accepted | roi | roi_ci_low | safe_ci_low | high_roi | low_bad | pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| v18_and_v19 | 20 | 8.335698 | 2.272256 | 0.838870 | 11 | 9 | false |
| v18_and_v19_or_v20 | 20 | 8.335698 | 2.272256 | 0.838870 | 11 | 9 | false |
| v19_or_v20 | 20 | 8.335698 | 2.272256 | 0.838870 | 11 | 9 | false |
| v19_selected | 20 | 8.335698 | 2.272256 | 0.838870 | 11 | 9 | false |
| v18_sector_only | 22 | 7.598520 | 2.009984 | 0.851340 | 11 | 11 | false |
| v20_plus_v18_sector | 23 | 7.316235 | 1.947619 | 0.856879 | 12 | 11 | false |
| v18_sector_plus_v19_random | 25 | 6.745638 | 1.755055 | 0.866804 | 12 | 13 | false |
| v19_or_v20_plus_v18_sector | 25 | 6.745638 | 1.755055 | 0.866804 | 12 | 13 | false |
| v18_no_greedy_anchor | 33 | 5.159189 | 1.273869 | 0.895727 | 12 | 21 | false |
| v18_or_v19 | 39 | 4.383892 | 1.053580 | 0.910330 | 12 | 27 | false |
| v18_or_v20 | 39 | 4.383892 | 1.053580 | 0.910330 | 12 | 27 | false |
| v18_selected | 39 | 4.383892 | 1.053580 | 0.910330 | 12 | 27 | false |
| v18_and_v20 | 10 | 10.493026 | 0.804256 | 0.722460 | 8 | 2 | false |
| v19_and_v20 | 10 | 10.493026 | 0.804256 | 0.722460 | 8 | 2 | false |
| v20_selected | 10 | 10.493026 | 0.804256 | 0.722460 | 8 | 2 | false |

## Reject Reason Counts

```json
{
  "accepted_all_success_count_below_safe_precision_ci_requirement": 12,
  "family_holdout_accepted_roi_below_threshold": 10,
  "safe_precision_ci_low_below_threshold_or_not_measurable": 12
}
```

## Recommended Next Step

```json
{
  "additional_all_success_accepts_needed": 15,
  "best_diagnostic_accepted_count": 20,
  "best_diagnostic_rule": "v18_and_v19",
  "minimum_all_success_count_for_safe_precision_ci": 35,
  "primary": "collect_reachability_valid_same_context_contrast_before_more_threshold_tuning",
  "reason": "fixed_hybrid_selectors_reduce_low_roi_but_do_not_restore_confidence_coverage"
}
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- 该 selector 审计不能证明没有负 reduced-cost journey，最终 certificate 仍必须由 true-dual exact pricing full closure 给出。

## 验证

```text
unit_test =
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
    -m unittest \
      BPC_future.tests.test_gat_batch_impact_training \
      BPC_future.tests.test_gat_batch_impact_score_margins \
      BPC_future.tests.test_gat_batch_impact_cross_checkpoint_selector

result =
  Ran 16 tests in 1.163s
  OK

py_compile =
  PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
    BPC_future/scripts/audit_gat_batch_impact_cross_checkpoint_selector.py \
    BPC_future/tests/test_gat_batch_impact_cross_checkpoint_selector.py

py_compile_result =
  OK

trailing_whitespace_scan =
  rg -n "[ \t]$" \
    BPC_future/scripts/audit_gat_batch_impact_cross_checkpoint_selector.py \
    BPC_future/tests/test_gat_batch_impact_cross_checkpoint_selector.py \
    BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md \
    BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_cross_checkpoint_selector_v18_v19_v20_zh.md

trailing_whitespace_scan_result =
  no matches
```
