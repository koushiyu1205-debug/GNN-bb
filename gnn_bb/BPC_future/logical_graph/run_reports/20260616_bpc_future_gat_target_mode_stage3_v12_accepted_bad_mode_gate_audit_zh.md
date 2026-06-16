# BPC_future GAT Accepted Bad-mode Gate Audit 报告

日期：2026-06-16

## 结论

本报告只读 Stage 3 decision records，检查 HIGH_PRIORITY decision 中是否包含
bad-mode batch。它不运行 BPC / pricing / RMP，不改变 admission，也不产生 certificate。

```text
decision_record_count = 102
high_priority_decision_count = 22
bad_mode_record_count = 8
accepted_bad_mode_count = 0
max_accepted_bad_mode_count = 0
accepted_bad_mode_gate_pass = true
all_checks_pass = true
```

## 判定

训练 gate 的默认硬约束是 `accepted_bad_mode_count = 0`。如果这里失败，
对应 checkpoint / safe-source 只能保留为 diagnostic，不能升级为 Stage 4 candidate。

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
```
