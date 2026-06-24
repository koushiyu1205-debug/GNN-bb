# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 3
- row_count = 148

## Tail Action Counts

- `BROAD_PLATEAU_FALLBACK`: 13
- `CONTINUE_COLUMN_GENERATION`: 36
- `EARLY_BRANCH`: 99

## 关键计数

- A/frontier refinement: 0
- B/broad plateau: 13
- C/continue CG: 36
- D/early branch: 99
- unknown action: 0
- fathom_possible_if_rc_zero: 20
- micro expansion attempted rows: 0
- recent active-support addition rows: 37
- recent RMP objective progress rows: 38
- early branch triggers: 0
- tail-action early branch triggers: 0
- tail-action no-column early branch triggers: 0
- non-exact early branch triggers: 0
- no-column gate rows: 56
- no-column before-final-probe gate rows: 56
- no-column before-final-probe disabled rows: 56
- no-column gate D/early-branch rows: 49
- no-column before-final-probe disabled D rows: 49
- tail-action queued children: 0
- tail-action non-exact queued children: 0
- observed tail-action child audit rows: 0
- tail-action child min queue priority width: None
- tail-action child max queue priority width: None

## 输出

- summary: `BPC_future/results/journey_tail_action_controller_audit_v165_gate_probe3_220_20260624/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v165_gate_probe3_220_20260624/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_v165_gate_probe3_220_20260624/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v165_gate_probe3_220_20260624/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_v165_gate_probe3_220_20260624/early_branch_trigger_rows.csv`
- no-column gate rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v165_gate_probe3_220_20260624/no_column_gate_rows.jsonl`
- no-column gate rows csv: `BPC_future/results/journey_tail_action_controller_audit_v165_gate_probe3_220_20260624/no_column_gate_rows.csv`

## No-column Gate Counts

按 gate_reason:
- `before_final_probe_disabled`: 56

按 tail_action:
- `BROAD_PLATEAU_FALLBACK`: 7
- `EARLY_BRANCH`: 49
