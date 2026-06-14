# Active-basis Snapshot Smoke 审计报告

日期：2026-06-14

## 目标

本报告只审计已生成的 no-certificate-effect smoke 产物 `BPC_future/results/root_cause_active_basis_snapshot_mt20_smoke_20260614`，确认 full active-basis snapshot 采集链路能把 `active_basis_churn_count_before` 和 `rmp_degeneracy_pressure_before` 写入 candidate impact rows。

它不运行 BPC / pricing / replay，不改变 worker、certificate 或 official lower bound。

## 关键结果

```text
all_checks_pass = true
capture_event_count = 2
active_complete_capture_count = 2
active_basis_payload_count_min = 10
manifest_ready_case_count = 2
replay_case_count = 2
impact_candidate_row_count = 2
active_basis_churn_nonempty_count = 2
rmp_degeneracy_pressure_nonempty_count = 2
official_effect_count = 0
```

## Churn Source

```json
{
  "initial_active_basis_snapshot": 1,
  "full_active_basis_signature_symmetric_difference": 1
}
```

## Checks

```json
{
  "active_basis_churn_populated_for_all_candidates": true,
  "active_basis_payload_nonempty": true,
  "all_capture_events_have_complete_active_basis_snapshot": true,
  "all_capture_events_no_certificate_effect": true,
  "has_capture_events": true,
  "has_full_snapshot_churn_source": true,
  "has_initial_snapshot_churn_source": true,
  "has_log_file": true,
  "impact_has_candidate_rows": true,
  "impact_passed": true,
  "impact_replay_is_no_certificate_effect": true,
  "manifest_has_ready_cases": true,
  "manifest_passed": true,
  "replay_is_no_certificate_effect": true,
  "replay_passed": true,
  "rmp_degeneracy_pressure_populated_for_all_candidates": true,
  "smoke_root_exists": true
}
```

## 解释

本 smoke 解决的是证据链中的一个窄缺口：证明 active-basis snapshot schema 不只是单元测试可行，也能通过真实 driver 日志、manifest、replay 和 impact dataset 传递到 candidate rows。

它没有证明 production selector，也没有证明 5/10 full no-regression 或 20-task wall-time speedup。下一步仍需采集更多 no-certificate-effect exact-context snapshot rows，并重新做 context / instance / dataset selector holdout。
