# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 1
- row_count = 16

## Tail Action Counts

- `CONTINUE_COLUMN_GENERATION`: 7
- `EARLY_BRANCH`: 9

## 关键计数

- A/frontier refinement: 0
- B/broad plateau: 0
- C/continue CG: 7
- D/early branch: 9
- unknown action: 0
- fathom_possible_if_rc_zero: 4
- micro expansion attempted rows: 0
- recent active-support addition rows: 5
- recent RMP objective progress rows: 5
- early branch triggers: 0
- tail-action early branch triggers: 0
- tail-action no-column early branch triggers: 0
- non-exact early branch triggers: 0
- tail-action queued children: 0
- tail-action non-exact queued children: 0
- observed tail-action child audit rows: 0
- tail-action child min queue priority width: None
- tail-action child max queue priority width: None

## 输出

- summary: `BPC_future/results/journey_tail_action_controller_audit_diag_top100_seed61001_140_20260624/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_diag_top100_seed61001_140_20260624/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_diag_top100_seed61001_140_20260624/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_diag_top100_seed61001_140_20260624/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_diag_top100_seed61001_140_20260624/early_branch_trigger_rows.csv`
