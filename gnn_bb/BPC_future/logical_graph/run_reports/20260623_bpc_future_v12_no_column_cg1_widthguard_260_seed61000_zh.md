# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 1
- row_count = 14

## Tail Action Counts

- `CONTINUE_COLUMN_GENERATION`: 6
- `EARLY_BRANCH`: 5
- `FRONTIER_REFINEMENT`: 3

## 关键计数

- A/frontier refinement: 3
- B/broad plateau: 0
- C/continue CG: 6
- D/early branch: 5
- unknown action: 0
- fathom_possible_if_rc_zero: 3
- micro expansion attempted rows: 0
- recent active-support addition rows: 7
- recent RMP objective progress rows: 6
- early branch triggers: 3
- tail-action early branch triggers: 3
- tail-action no-column early branch triggers: 2
- non-exact early branch triggers: 3
- tail-action queued children: 6
- tail-action non-exact queued children: 6
- observed tail-action child audit rows: 5
- tail-action child min queue priority width: -1
- tail-action child max queue priority width: -1

## 输出

- summary: `BPC_future/results/journey_tail_action_controller_audit_v12_no_column_cg1_widthguard_260_seed61000_20260623/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v12_no_column_cg1_widthguard_260_seed61000_20260623/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_v12_no_column_cg1_widthguard_260_seed61000_20260623/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v12_no_column_cg1_widthguard_260_seed61000_20260623/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_v12_no_column_cg1_widthguard_260_seed61000_20260623/early_branch_trigger_rows.csv`

## Early Branch Child Activity

- node=1 depth=1 cg=2 no_column=false children=`3,4` started=2/2 subtree_nodes=6 pricing=11 negative_pricing=3 cb_retry=0 subtree_early_branch=2 subtree_no_column=2 span=90.093774
- node=3 depth=2 cg=4 no_column=true children=`5,6` started=1/2 subtree_nodes=2 pricing=1 negative_pricing=0 cb_retry=0 subtree_early_branch=0 subtree_no_column=0 span=36.140748
- node=4 depth=2 cg=1 no_column=true children=`7,8` started=0/2 subtree_nodes=2 pricing=0 negative_pricing=0 cb_retry=0 subtree_early_branch=0 subtree_no_column=0 span=0.038115
