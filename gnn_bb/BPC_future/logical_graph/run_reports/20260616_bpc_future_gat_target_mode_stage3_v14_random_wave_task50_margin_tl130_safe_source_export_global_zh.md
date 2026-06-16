# GAT Batch Impact Safe-source Export 报告

日期：2026-06-16

## 结论

`safe_source_ready = true`
`safe_candidate_id_count = 1226`

该导出只服务 Stage 4 admission scheduling。它不运行 BPC / pricing / RMP，
不产生 official bound，也不能作为 no-negative certificate source。

## 机器字段

```text
status = safe_source_exported
decision_record_count = 328
high_priority_decision_record_count = 59
safe_ids_exportable = true
training_gate_repaired_by_knn_ood = true
training_gate_reject_reasons = ['false_high_priority_on_delay_too_high', 'false_safe_rate_union_too_high', 'knn_ood_audit_missing']
blockers = []
production_ready = false
default_enabled = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## Config Snippet

```json
{
  "journey_gat_admission_allow_unsourced_delay": false,
  "journey_gat_admission_safe_source_ready": true,
  "journey_gat_admission_scheduler_enabled": true,
  "journey_gat_certificate_hard_filter_enabled": false,
  "journey_gat_safe_candidate_ids": "<1226 ids in safe_source.json>",
  "journey_gat_shadow_safe_candidate_ids": "<1226 ids in safe_source.json>"
}
```

完整 safe candidate id 列表在：

```text
BPC_future/results/gat_batch_impact_safe_source_v14_random_wave_task50_margin_tl130_global_20260616/safe_source.json
```
