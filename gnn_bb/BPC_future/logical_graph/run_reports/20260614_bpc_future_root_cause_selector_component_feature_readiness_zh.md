# Root Cause Selector Component Feature Readiness 报告

日期：2026-06-14

## 目的

本报告合并 context schema gap、pool overlap probe、target002 missing-context
和 component drift 证据，判断 pool / forbidden / returned-batch component
特征是否已经能作为 production addition-before selector。

它只读已有 summary，不运行 BPC / pricing / RMP / Pulse，也不改变 solver 行为。

## 机器字段

```text
selector_component_feature_readiness = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_component_features_not_production_ready
row_count = 280
derived_feature_count = 31
robust_all_holdout_derived_feature_count = 0
robust_all_holdout_model_count = 0
explicit_forbidden_signature_list_available_count = 18
target002_pool_signature_same_count = 0
target002_forbidden_signature_same_count = 0
ready_for_selector_holdout = false
all_checks_pass = true
```

## 结论

Pool/returned overlap features are derivable and populated on the current 280 replay rows, but they still fail robust holdout.  The targeted component payload now exposes explicit forbidden signatures, but those rows are still single-context calibration evidence rather than a broad production selector holdout.  target002 proves active hash alone is insufficient.  Therefore component features remain a wider holdout/data-collection direction, not a production optimization direction yet.

所以当前方向不是上线 component selector，而是补齐 no-certificate-effect
component-context 采集，并重新做 context / instance / dataset holdout。

## Readiness Items

```json
[
  {
    "evidence": {
      "core_field_nonempty_counts": {
        "pool_candidate_task_freq_sum": 280,
        "pool_candidate_task_set_max_jaccard": 280,
        "returned_batch_min_true_rc": 280,
        "returned_batch_new_task_set_count": 280,
        "returned_batch_size": 280,
        "returned_batch_true_rc_gap_from_best": 280,
        "root_forbidden_candidate_task_set_max_jaccard": 280,
        "root_forbidden_signature_count": 280
      },
      "derived_feature_count": 31,
      "robust_all_holdout_derived_feature_count": 0,
      "robust_all_holdout_model_count": 0,
      "row_count": 280
    },
    "item": "pool_returned_overlap_features",
    "status": "available_but_not_production_validated"
  },
  {
    "evidence": {
      "explicit_forbidden_signature_list_available_count": 18,
      "forbidden_manifest_case_count": 122
    },
    "item": "forbidden_signature_pressure",
    "status": "explicit_payload_available_not_production_validated"
  },
  {
    "evidence": {
      "config_matched_exact_returned_task_sets_same_count": 0,
      "forbidden_signature_hash_same_count": 0,
      "non_source_same_active_event_count": 9,
      "pool_signature_hash_same_count": 0,
      "target_active_hash": "f0b96be45c5015c9",
      "target_context_hash": "3f914a0d2b97fd27"
    },
    "item": "active_hash_only_context",
    "status": "insufficient"
  },
  {
    "evidence": {
      "missing_context_hashes": [
        "3f914a0d2b97fd27"
      ],
      "ready_for_selector_holdout": false,
      "target002_target_recovered_probe_count": 0
    },
    "item": "selector_holdout_dataset",
    "status": "not_ready"
  }
]
```

## Checks

```json
{
  "active_hash_only_insufficient": true,
  "component_drift_passed": true,
  "context_schema_gap_passed": true,
  "core_pool_returned_features_populated": true,
  "explicit_forbidden_signature_payload_accounted": true,
  "missing_context_diagnosis_passed": true,
  "next_feature_gate_passed": true,
  "pool_overlap_probe_passed": true,
  "pool_returned_features_not_robust": true,
  "required_feature_families_listed": true,
  "selector_holdout_not_ready": true
}
```
