# Root Cause Selector Context Schema Gap 报告

日期：2026-06-14

## 目的

本报告只读现有 candidate impact rows、replay manifests 与 selector summary，
审计 addition-before selector 还缺哪些上下文字段。它不运行 BPC / pricing / RMP / Pulse。

## 机器字段

```text
root_cause_selector_context_schema_gap = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_context_schema_gap_audited
candidate_row_count = 280
manifest_case_count = 122
manifest_joined_row_count = 280
complete_pool_payload_case_count = 122
complete_returned_batch_case_count = 122
cases_with_explicit_forbidden_signature_list = 18
all_checks_pass = true
```

## 结论

现有 rows 已包含 true-RC、task-set、RMP aggregate、active-basis snapshot 与 recent trajectory 字段，但这些字段已被 holdout / 反例证明不能单独构成 production selector；当前 280 行 replay selector 数据里 full active-basis snapshot 仍未真正填充。pool/returned-batch composition 可以从 manifest 派生，但尚未持久化进 candidate rows，且派生后仍无 robust holdout selector。forbidden pressure 只有 hash/count，没有显式 forbidden signature list 的旧缺口已经被 targeted component payload 部分补上；但这些 payload 还没有合入并通过 production selector holdout。

## Feature Family Status

```json
[
  {
    "evidence": {
      "blocked_families": [
        "true_rc_threshold",
        "new_task_set_only"
      ],
      "nonempty_counts": {
        "cost": 280,
        "duplicate_signature": 280,
        "new_task_set": 280,
        "sequence": 280,
        "strict_replacement_by_cost": 280,
        "task_set": 280,
        "true_reduced_cost": 280,
        "weak_replacement_or_duplicate": 280
      }
    },
    "family": "local_column_geometry",
    "status": "available_but_blocked_as_production_selector_alone"
  },
  {
    "evidence": {
      "blocked_families": [
        "active_basis_scalar_only",
        "current_enriched_single_or_multifeature_selector"
      ],
      "nonempty_counts": {
        "active_hash_before": 275,
        "column_pool_size_before": 280,
        "dual_hash_before": 280,
        "dual_l1_norm_before": 280,
        "dual_linf_norm_before": 280,
        "duplicate_signature_pool_count_before": 280,
        "pricing_tail_retry_count_before": 280,
        "recent_added_column_acceptance_rate_before": 280,
        "recent_dual_l1_delta_before": 280,
        "recent_objective_delta_before": 280,
        "rmp_objective_before": 280,
        "task_set_pool_count_before": 280
      }
    },
    "family": "rmp_aggregate_context",
    "status": "available_but_insufficient"
  },
  {
    "evidence": {
      "active_basis_snapshot_complete_true_count": 0,
      "nonempty_counts": {
        "active_basis_churn_count_before": 0,
        "active_basis_fractional_journey_count_before": 0,
        "active_basis_journey_count_before": 0,
        "active_basis_snapshot_complete_before": 280,
        "active_basis_snapshot_hash_before": 0,
        "active_basis_unique_task_set_count_before": 279,
        "rmp_degeneracy_pressure_before": 0
      },
      "row_count": 280
    },
    "family": "active_basis_full_snapshot_features",
    "status": "missing_from_current_replay_selector_rows"
  },
  {
    "evidence": {
      "cases_with_pool_journeys": 122,
      "complete_pool_cases": 122,
      "row_nonempty_overlap_fields": {
        "pool_candidate_same_task_set_best_cost_delta": 0,
        "pool_candidate_task_freq_sum": 0,
        "pool_candidate_task_set_max_jaccard": 0,
        "returned_batch_new_task_set_count": 0,
        "returned_batch_size": 0,
        "returned_batch_true_rc_gap_from_best": 0,
        "returned_candidate_true_rc_rank": 0
      }
    },
    "family": "pool_signature_composition_features",
    "status": "derivable_from_manifest_not_persisted_in_candidate_rows"
  },
  {
    "evidence": {
      "cases_with_returned_journeys": 116,
      "complete_returned_cases": 122,
      "derived_feature_count": 31,
      "robust_all_holdout_derived_feature_count": 0,
      "robust_all_holdout_model_count": 0
    },
    "family": "returned_batch_vs_pool_overlap_features",
    "status": "derivable_but_not_production_validated"
  },
  {
    "evidence": {
      "cases_with_explicit_forbidden_signature_list": 18,
      "cases_with_forbidden_count_field": 18,
      "cases_with_forbidden_hash": 122
    },
    "family": "forbidden_signature_pressure_features",
    "status": "explicit_payload_available_not_production_validated"
  }
]
```

## Checks

```json
{
  "active_basis_snapshot_missing_from_current_replay_rows": true,
  "candidate_rows_exist": true,
  "candidate_rows_join_manifest": true,
  "derived_overlap_not_persisted_in_candidate_rows": true,
  "diagnostic_not_production_selector": true,
  "explicit_forbidden_signature_payload_observed": true,
  "local_features_present": true,
  "manifest_cases_exist": true,
  "next_gate_blocks_production_shortcuts": true,
  "pool_overlap_probe_not_robust": true,
  "pool_payload_available": true,
  "returned_payload_available": true,
  "rmp_aggregate_features_present": true
}
```
