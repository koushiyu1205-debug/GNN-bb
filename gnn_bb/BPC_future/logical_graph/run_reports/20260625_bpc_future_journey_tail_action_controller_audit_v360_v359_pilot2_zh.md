# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 4
- row_count = 81

## Tail Action Counts

- `BROAD_PLATEAU_FALLBACK`: 4
- `CONTINUE_COLUMN_GENERATION`: 33
- `EARLY_BRANCH`: 44

## Tail Action Classes

- `B_BROAD_PLATEAU`: 4
- `C_CONTINUE_CG`: 33
- `D_EARLY_BRANCH`: 44

## Tail Action Productivity Classes

- `pricing_active_support_productive`: 18
- `pricing_has_negative_columns`: 9
- `pricing_no_negative_columns`: 4
- `pricing_productivity_signals_incomplete`: 6
- `pricing_unproductive_no_negative_columns`: 42
- `pricing_weak_columns_tail`: 2

## 关键计数

- A/frontier refinement: 0
- B/broad plateau: 4
- C/continue CG: 33
- D/early branch: 44
- unknown action: 0
- fathom_possible_if_rc_zero: 13
- micro expansion attempted rows: 0
- recent active-support addition rows: 27
- recent RMP objective progress rows: 24
- early branch triggers: 0
- tail-action early branch triggers: 0
- tail-action no-column early branch triggers: 0
- non-exact early branch triggers: 0
- no-column gate rows: 18
- no-column before-final-probe gate rows: 18
- no-column before-final-probe disabled rows: 18
- no-column gate D/early-branch rows: 16
- no-column before-final-probe disabled D rows: 16
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

- summary: `BPC_future/results/journey_tail_action_controller_audit_v360_v359_pilot2_20260625/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v360_v359_pilot2_20260625/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_v360_v359_pilot2_20260625/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v360_v359_pilot2_20260625/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_v360_v359_pilot2_20260625/early_branch_trigger_rows.csv`
- no-column gate rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v360_v359_pilot2_20260625/no_column_gate_rows.jsonl`
- no-column gate rows csv: `BPC_future/results/journey_tail_action_controller_audit_v360_v359_pilot2_20260625/no_column_gate_rows.csv`

## No-column Gate Counts

按 gate_reason:
- `before_final_probe_disabled`: 18

按 tail_action:
- `BROAD_PLATEAU_FALLBACK`: 2
- `EARLY_BRANCH`: 16

按 tail_action_class:
- `B_BROAD_PLATEAU`: 2
- `D_EARLY_BRANCH`: 16

按 tail_action_productivity_class:
- `pricing_no_negative_columns`: 2
- `pricing_unproductive_no_negative_columns`: 16
