# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 24
- row_count = 529

## Tail Action Counts

- `BROAD_PLATEAU_FALLBACK`: 49
- `CONTINUE_COLUMN_GENERATION`: 223
- `EARLY_BRANCH`: 257

## Tail Action Classes

- `B_BROAD_PLATEAU`: 49
- `C_CONTINUE_CG`: 223
- `D_EARLY_BRANCH`: 257

## Tail Action Productivity Classes

- `unknown`: 529

## 关键计数

- A/frontier refinement: 0
- B/broad plateau: 49
- C/continue CG: 223
- D/early branch: 257
- unknown action: 0
- fathom_possible_if_rc_zero: 100
- micro expansion attempted rows: 0
- recent active-support addition rows: 211
- recent RMP objective progress rows: 212
- early branch triggers: 0
- tail-action early branch triggers: 0
- tail-action no-column early branch triggers: 0
- non-exact early branch triggers: 0
- no-column gate rows: 146
- no-column before-final-probe gate rows: 146
- no-column before-final-probe disabled rows: 146
- no-column gate D/early-branch rows: 119
- no-column before-final-probe disabled D rows: 119
- tail-action queued children: 0
- tail-action non-exact queued children: 0
- observed tail-action child audit rows: 0
- tail-action low min-fill completion retries: 0
- tail-action completion retry found-negative rows: 0
- tail-action completion retry certified no-negative rows: 0
- tail-action completion retry incomplete rows: 0
- tail-action child min queue priority width: None
- tail-action child max queue priority width: None

## 输出

- summary: `BPC_future/results/journey_tail_action_controller_audit_v358_v347_profile_top24_20260625/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v358_v347_profile_top24_20260625/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_v358_v347_profile_top24_20260625/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v358_v347_profile_top24_20260625/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_v358_v347_profile_top24_20260625/early_branch_trigger_rows.csv`
- no-column gate rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v358_v347_profile_top24_20260625/no_column_gate_rows.jsonl`
- no-column gate rows csv: `BPC_future/results/journey_tail_action_controller_audit_v358_v347_profile_top24_20260625/no_column_gate_rows.csv`

## No-column Gate Counts

按 gate_reason:
- `before_final_probe_disabled`: 146

按 tail_action:
- `BROAD_PLATEAU_FALLBACK`: 27
- `EARLY_BRANCH`: 119

按 tail_action_class:
- `B_BROAD_PLATEAU`: 27
- `D_EARLY_BRANCH`: 119

按 tail_action_productivity_class:
- `unknown`: 146
