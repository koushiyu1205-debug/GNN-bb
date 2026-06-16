# GAT Batch Impact Safe-source Export 报告

日期：2026-06-16

## 结论

`safe_source_ready = false`
`safe_candidate_id_count = 0`

该导出只服务 Stage 4 admission scheduling。它不运行 BPC / pricing / RMP，
不产生 official bound，也不能作为 no-negative certificate source。

## 机器字段

```text
status = safe_source_blocked
decision_record_count = 78
high_priority_decision_record_count = 2
safe_ids_exportable = false
blockers = ['candidate_signature_ids_missing_or_incomplete', 'knn_ood_accepted_batch_roi_ci_low_met_failed', 'knn_ood_safe_precision_ci_low_met_failed', 'knn_ood_validation_candidate_not_ready', 'knn_ood_validation_safety_not_ready', 'no_exportable_high_priority_candidate_signature_ids', 'training_validation_local_gate_not_passed']
production_ready = false
default_enabled = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## Config Snippet

```json
{
  "journey_gat_admission_allow_unsourced_delay": false,
  "journey_gat_admission_safe_source_ready": false,
  "journey_gat_admission_scheduler_enabled": false,
  "journey_gat_certificate_hard_filter_enabled": false,
  "journey_gat_safe_candidate_ids": [],
  "journey_gat_shadow_safe_candidate_ids": []
}
```
