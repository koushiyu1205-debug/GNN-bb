# Root Cause Component Payload Addition-Before Rows 报告

日期：2026-06-14

## 目的

本报告检查 target002 component payload 是否已经能转成可做 selector
holdout 的 addition-before candidate rows。它只审计离线 manifest /
local RMP replay / impact CSV，不运行 BPC、pricing、Pulse 或 certificate。

## 机器字段

```text
component_payload_addition_before_rows = current
diagnostic_only = true
runs_bpc_or_pricing = false
runs_local_rmp_replay = true
status = component_payload_addition_before_rows_audited
raw_capture_case_count = 12
ready_case_count = 6
candidate_row_count = 48
high_impact_candidate_count = 48
noop_candidate_count = 0
explicit_forbidden_true_count = 48
all_checks_pass = true
```

## 字段覆盖

```json
{
  "field_complete": {
    "active_basis_snapshot_complete_before": true,
    "candidate_forbidden_signature": true,
    "candidate_signature_in_pool": true,
    "explicit_forbidden_signature_list_available": true,
    "forbidden_signature_count_before": true,
    "forbidden_signature_payload_complete_before": true,
    "forbidden_signature_payload_count_before": true,
    "pool_candidate_task_freq_sum": true,
    "pool_candidate_task_set_max_jaccard": true,
    "returned_batch_forbidden_signature_count": true,
    "returned_batch_new_task_set_count": true,
    "returned_batch_size": true,
    "returned_batch_true_rc_gap_from_best": true,
    "returned_candidate_true_rc_rank": true
  },
  "field_nonempty_counts": {
    "active_basis_snapshot_complete_before": 48,
    "candidate_forbidden_signature": 48,
    "candidate_signature_in_pool": 48,
    "explicit_forbidden_signature_list_available": 48,
    "forbidden_signature_count_before": 48,
    "forbidden_signature_payload_complete_before": 48,
    "forbidden_signature_payload_count_before": 48,
    "pool_candidate_task_freq_sum": 48,
    "pool_candidate_task_set_max_jaccard": 48,
    "returned_batch_forbidden_signature_count": 48,
    "returned_batch_new_task_set_count": 48,
    "returned_batch_size": 48,
    "returned_batch_true_rc_gap_from_best": 48,
    "returned_candidate_true_rc_rank": 48
  }
}
```

## 解释

The targeted component capture can now be converted into addition-before candidate rows with active-basis, pool, returned-batch, and explicit forbidden-signature payload fields. This is calibration evidence only: it is not a production selector, BPC speedup proof, or certificate effect.

## 检查项

```json
{
  "all_required_addition_before_fields_complete": true,
  "candidate_rows_present": true,
  "diagnostic_not_production_selector": true,
  "explicit_forbidden_payload_observed": true,
  "forbidden_payload_complete": true,
  "impact_all_checks_pass": true,
  "manifest_all_checks_pass": true,
  "manifest_has_ready_cases": true,
  "manifest_ready_only": true,
  "replay_all_checks_pass": true,
  "replay_no_certificate_effect": true
}
```
