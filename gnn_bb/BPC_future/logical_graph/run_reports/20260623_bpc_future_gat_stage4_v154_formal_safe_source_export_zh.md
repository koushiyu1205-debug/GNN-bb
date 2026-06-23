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
decision_record_count = 292
high_priority_decision_record_count = 36
safe_ids_exportable = false
training_gate_repaired_by_knn_ood = false
training_gate_reject_reasons = ['knn_ood_audit_missing', 'raw_pair_pass_rate_below_threshold', 'strict_pair_pass_rate_below_threshold']
blockers = ['training_validation_non_knn_repairable_reject_reasons']
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
  "journey_gat_safe_candidate_ids": "<0 ids in safe_source.json>",
  "journey_gat_shadow_safe_candidate_ids": "<0 ids in safe_source.json>"
}
```

完整 safe candidate id 列表在：

```text
BPC_future/results/gat_stage4_v154_actual_probe_20260623/formal_safe_source_export/safe_source.json
```
