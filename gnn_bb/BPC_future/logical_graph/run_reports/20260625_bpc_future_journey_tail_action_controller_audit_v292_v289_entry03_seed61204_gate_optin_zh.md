# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 1
- row_count = 18

## Tail Action Counts

- `BROAD_PLATEAU_FALLBACK`: 6
- `CONTINUE_COLUMN_GENERATION`: 8
- `EARLY_BRANCH`: 4

## 关键计数

- A/frontier refinement: 0
- B/broad plateau: 6
- C/continue CG: 8
- D/early branch: 4
- unknown action: 0
- fathom_possible_if_rc_zero: 11
- micro expansion attempted rows: 0
- recent active-support addition rows: 7
- recent RMP objective progress rows: 8
- early branch triggers: 1
- tail-action early branch triggers: 1
- tail-action no-column early branch triggers: 1
- non-exact early branch triggers: 1
- no-column gate rows: 4
- no-column before-final-probe gate rows: 4
- no-column before-final-probe disabled rows: 0
- no-column gate D/early-branch rows: 1
- no-column before-final-probe disabled D rows: 0
- tail-action queued children: 2
- tail-action non-exact queued children: 2
- observed tail-action child audit rows: 8
- tail-action low min-fill completion retries: 0
- tail-action completion retry found-negative rows: 0
- tail-action completion retry certified no-negative rows: 3
- tail-action completion retry incomplete rows: 1
- tail-action child min queue priority width: -1
- tail-action child max queue priority width: -1

## 输出

- summary: `BPC_future/results/journey_tail_action_controller_audit_v292_v289_entry03_seed61204_gate_optin_20260625/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v292_v289_entry03_seed61204_gate_optin_20260625/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_v292_v289_entry03_seed61204_gate_optin_20260625/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v292_v289_entry03_seed61204_gate_optin_20260625/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_v292_v289_entry03_seed61204_gate_optin_20260625/early_branch_trigger_rows.csv`
- no-column gate rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v292_v289_entry03_seed61204_gate_optin_20260625/no_column_gate_rows.jsonl`
- no-column gate rows csv: `BPC_future/results/journey_tail_action_controller_audit_v292_v289_entry03_seed61204_gate_optin_20260625/no_column_gate_rows.csv`

## No-column Gate Counts

按 gate_reason:
- `depth_above_max`: 1
- `tail_action_not_early_branch`: 3

按 tail_action:
- `BROAD_PLATEAU_FALLBACK`: 3
- `EARLY_BRANCH`: 1

## Early Branch Child Activity

- node=0 depth=0 cg=17 no_column=true children=`1,2` started=2/2 subtree_nodes=4 pricing=30 negative_pricing=9 cb_retry=13 cb_low_min_fill=0 cb_min_fill_values=`10:4` subtree_early_branch=0 subtree_no_column=0 span=146.439583
