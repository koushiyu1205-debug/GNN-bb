# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 60
- row_count = 2712

## Tail Action Counts

- `BROAD_PLATEAU_FALLBACK`: 366
- `CONTINUE_COLUMN_GENERATION`: 854
- `EARLY_BRANCH`: 1492

## Tail Action Classes

- `B_BROAD_PLATEAU`: 366
- `C_CONTINUE_CG`: 854
- `D_EARLY_BRANCH`: 1492

## Tail Action Productivity Classes

- `pricing_active_support_productive`: 223
- `pricing_has_negative_columns`: 249
- `pricing_no_negative_columns`: 366
- `pricing_objective_productive`: 60
- `pricing_productivity_signals_incomplete`: 322
- `pricing_unproductive_no_negative_columns`: 1382
- `pricing_weak_columns_tail`: 110

## 关键计数

- A/frontier refinement: 0
- B/broad plateau: 366
- C/continue CG: 854
- D/early branch: 1492
- unknown action: 0
- fathom_possible_if_rc_zero: 615
- micro expansion attempted rows: 0
- recent active-support addition rows: 796
- recent RMP objective progress rows: 813
- early branch triggers: 0
- tail-action early branch triggers: 0
- tail-action no-column early branch triggers: 0
- non-exact early branch triggers: 0
- no-column gate rows: 897
- no-column before-final-probe gate rows: 897
- no-column before-final-probe disabled rows: 897
- no-column gate D/early-branch rows: 704
- no-column before-final-probe disabled D rows: 704
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

- summary: `BPC_future/results/journey_tail_action_controller_audit_v474_v468_full60_20260627/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v474_v468_full60_20260627/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_v474_v468_full60_20260627/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v474_v468_full60_20260627/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_v474_v468_full60_20260627/early_branch_trigger_rows.csv`
- no-column gate rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v474_v468_full60_20260627/no_column_gate_rows.jsonl`
- no-column gate rows csv: `BPC_future/results/journey_tail_action_controller_audit_v474_v468_full60_20260627/no_column_gate_rows.csv`

## No-column Gate Counts

按 gate_reason:
- `before_final_probe_disabled`: 897

按 tail_action:
- `BROAD_PLATEAU_FALLBACK`: 193
- `EARLY_BRANCH`: 704

按 tail_action_class:
- `B_BROAD_PLATEAU`: 193
- `D_EARLY_BRANCH`: 704

按 tail_action_productivity_class:
- `pricing_no_negative_columns`: 193
- `pricing_unproductive_no_negative_columns`: 704
