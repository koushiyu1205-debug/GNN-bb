# Root Cause Component Payload Selector Holdout Extension 报告

日期：2026-06-14

## 目的

本报告把 targeted component-payload addition-before rows 合入既有
 selector holdout 口径，检查它是否已经足以产生 production selector。

它只读 CSV / JSON summary，不运行 BPC / pricing / RMP / Pulse / replay，
也不改变 solver 默认行为。

## 机器字段

```text
root_cause_component_payload_selector_holdout_extension = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = component_payload_selector_holdout_extension_audited
base_row_count = 280
component_row_count = 48
combined_row_count = 328
component_positive_only = true
combined_robust_all_holdout_derived_feature_count = 0
combined_robust_all_holdout_model_count = 0
combined_best_context_model = linear_mean_diff
combined_best_context_model_context_folds = 18/30
component_context_overlap_with_base_count = 2
component_context_new_count = 2
combined_has_no_robust_selector = true
all_checks_pass = true
```

## 结论

Targeted component-payload rows 新增了 48 行显式 forbidden-signature payload 完整的 addition-before 正样本校准行；但把它们与 base 280 行 selector rows 合并后，仍没有产生任何通过 context / instance / dataset all-holdout 的单特征或多特征 selector。它们降低了 schema gap，但还没有形成 production selector，也没有证明 solver speedup。

## Label Counts

```json
{
  "base": {
    "improved": 209,
    "noop": 71
  },
  "combined": {
    "improved": 257,
    "noop": 71
  },
  "component_only": {
    "improved": 48
  }
}
```

## Holdout Summary

```json
{
  "base": {
    "best_context": "17/28",
    "robust_features": 0,
    "robust_models": 0
  },
  "combined": {
    "best_context": "18/30",
    "robust_features": 0,
    "robust_models": 0
  },
  "component_only": {
    "best_context": "4/4",
    "robust_features": 0,
    "robust_models": 0
  }
}
```

## Checks

```json
{
  "base_rows_joined_to_manifest": true,
  "base_rows_present": true,
  "combined_has_no_robust_all_holdout_selector": true,
  "combined_rows_expected": true,
  "component_rows_are_positive_only": true,
  "component_rows_have_explicit_forbidden_payload": true,
  "component_rows_present": true,
  "diagnostic_not_production_selector": true,
  "runs_bpc_or_pricing_false": true
}
```