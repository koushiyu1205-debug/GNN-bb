# Root Cause Selector Context Sufficiency Gap 报告

日期：2026-06-14

## 目的

本报告只读 target002 trajectory branch、feature availability 和 enriched
 holdout summary，审计当前 selector 上下文是否足够。它不运行 BPC /
 pricing / RMP / Pulse，也不改变 worker、certificate 或 solver 默认行为。

## 机器字段

```text
root_cause_selector_context_sufficiency_gap = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_context_sufficiency_gap_audited
selector_context_status = insufficient_for_production_selector
same_active_event_count = 10
same_active_context_hash_count = 7
non_source_same_active_event_count = 9
exact_disambiguator_fields_present_any = 
robust_single_feature_selector_count = 0
robust_multifeature_model_count = 0
all_checks_pass = true
```

## 结论

target002 same-active 分叉证明 active_hash 和当前 aggregate/proxy RMP 特征还不足以定义 production selector。candidate rows 已有若干 addition-before proxy，但缺少能概括 pool/forbidden signature composition 和 returned-batch-vs-pool overlap 的可泛化特征；现有 enriched single-feature 和 multifeature holdout 也没有 robust all-holdout selector。

## Aggregate Proxy Fields Present

```json
[
  "active_hash_before",
  "rmp_objective_before",
  "column_pool_size_before",
  "duplicate_signature_pool_count_before",
  "task_set_pool_count_before",
  "active_basis_size_before",
  "active_basis_unique_task_set_count_before",
  "active_basis_churn_count_before",
  "rmp_degeneracy_pressure_before"
]
```

## Required Next Feature Families

```json
[
  "pool_signature_composition_features",
  "forbidden_signature_pressure_features",
  "returned_batch_vs_pool_overlap_features",
  "active_basis_full_snapshot_features",
  "recent_rmp_trajectory_features"
]
```

## Checks

```json
{
  "aggregate_proxy_fields_present": true,
  "diagnostic_not_production_selector": true,
  "exact_disambiguators_absent_from_candidate_rows": true,
  "multifeature_holdout_has_no_robust_selector": true,
  "objective_or_batch_drift_present": true,
  "pool_or_forbidden_signature_drift_present": true,
  "same_active_not_context_sufficient": true,
  "single_feature_holdout_has_no_robust_selector": true,
  "trajectory_branch_passed": true
}
```