# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 1
- row_count = 32

## Tail Action Counts

- `BROAD_PLATEAU_FALLBACK`: 8
- `CONTINUE_COLUMN_GENERATION`: 16
- `EARLY_BRANCH`: 8

## 关键计数

- A/frontier refinement: 0
- B/broad plateau: 8
- C/continue CG: 16
- D/early branch: 8
- unknown action: 0
- fathom_possible_if_rc_zero: 16
- micro expansion attempted rows: 0
- recent active-support addition rows: 14
- recent RMP objective progress rows: 15
- early branch triggers: 0
- tail-action early branch triggers: 0
- tail-action no-column early branch triggers: 0
- non-exact early branch triggers: 0
- no-column gate rows: 7
- no-column before-final-probe gate rows: 7
- no-column before-final-probe disabled rows: 7
- no-column gate D/early-branch rows: 3
- no-column before-final-probe disabled D rows: 3
- tail-action queued children: 0
- tail-action non-exact queued children: 0
- observed tail-action child audit rows: 0
- tail-action child min queue priority width: None
- tail-action child max queue priority width: None

## 输出

- summary: `BPC_future/results/journey_tail_action_controller_audit_v173_sector_apollo_seed61408_diag260_20260624/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v173_sector_apollo_seed61408_diag260_20260624/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_v173_sector_apollo_seed61408_diag260_20260624/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v173_sector_apollo_seed61408_diag260_20260624/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_v173_sector_apollo_seed61408_diag260_20260624/early_branch_trigger_rows.csv`
- no-column gate rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v173_sector_apollo_seed61408_diag260_20260624/no_column_gate_rows.jsonl`
- no-column gate rows csv: `BPC_future/results/journey_tail_action_controller_audit_v173_sector_apollo_seed61408_diag260_20260624/no_column_gate_rows.csv`

## No-column Gate Counts

按 gate_reason:
- `before_final_probe_disabled`: 7

按 tail_action:
- `BROAD_PLATEAU_FALLBACK`: 4
- `EARLY_BRANCH`: 3
