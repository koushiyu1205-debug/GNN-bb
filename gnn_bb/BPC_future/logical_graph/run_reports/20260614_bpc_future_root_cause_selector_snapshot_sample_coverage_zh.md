# Root Cause Selector Snapshot Sample Coverage 报告

日期：2026-06-14

## 目的

本报告扫描现有 candidate impact CSV，确认是否已经有足够 full active-basis
snapshot rows 可用于 production selector holdout。它不运行 BPC / pricing / RMP / Pulse。

## 机器字段

```text
root_cause_selector_snapshot_sample_coverage = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_snapshot_sample_coverage_audited
csv_path_count = 14
candidate_row_count = 630
combined_replay_selector_row_count = 280
combined_replay_selector_complete_snapshot_row_count = 0
complete_snapshot_row_count = 62
holdout_ready = false
all_checks_pass = true
```

## 结论

全局 candidate impact CSV 中确实存在 full active-basis snapshot rows，现在包括 active-basis snapshot smoke 的 14 行和 targeted component payload addition-before rows 的 48 行；但主 replay selector combined dataset 的 280 行里 complete snapshot 仍为 0，component payload rows 也还只是单目标上下文校准数据。因此当前不是已有样本未利用，而是还没有足够的、已合入 selector holdout 的 no-certificate-effect full-snapshot 数据。

## Complete Snapshot Source Classes

```json
{
  "active_basis_snapshot_smoke": 14,
  "component_payload_addition_before_rows": 48
}
```

## Checks

```json
{
  "both_labels_exist_in_complete_snapshot_rows": true,
  "candidate_rows_exist": true,
  "combined_replay_selector_rows_have_no_complete_snapshot": true,
  "complete_snapshot_rows_exist": true,
  "complete_snapshot_rows_include_component_payload": true,
  "complete_snapshot_rows_not_production_selector_dataset": true,
  "diagnostic_not_production_selector": true,
  "holdout_not_ready": true
}
```
