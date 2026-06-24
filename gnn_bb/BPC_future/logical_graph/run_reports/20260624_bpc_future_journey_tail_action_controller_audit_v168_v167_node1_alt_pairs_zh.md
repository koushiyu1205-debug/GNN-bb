# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 2
- row_count = 114

## Tail Action Counts

- `CONTINUE_COLUMN_GENERATION`: 25
- `EARLY_BRANCH`: 89

## 关键计数

- A/frontier refinement: 0
- B/broad plateau: 0
- C/continue CG: 25
- D/early branch: 89
- unknown action: 0
- fathom_possible_if_rc_zero: 0
- micro expansion attempted rows: 0
- recent active-support addition rows: 34
- recent RMP objective progress rows: 36
- early branch triggers: 3
- tail-action early branch triggers: 3
- tail-action no-column early branch triggers: 3
- non-exact early branch triggers: 3
- no-column gate rows: 46
- no-column before-final-probe gate rows: 46
- no-column before-final-probe disabled rows: 0
- no-column gate D/early-branch rows: 46
- no-column before-final-probe disabled D rows: 0
- tail-action queued children: 6
- tail-action non-exact queued children: 6
- observed tail-action child audit rows: 15
- tail-action child min queue priority width: -1
- tail-action child max queue priority width: -1

## 输出

- summary: `BPC_future/results/journey_tail_action_controller_audit_v168_v167_node1_alt_pairs_20260624/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v168_v167_node1_alt_pairs_20260624/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_v168_v167_node1_alt_pairs_20260624/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v168_v167_node1_alt_pairs_20260624/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_v168_v167_node1_alt_pairs_20260624/early_branch_trigger_rows.csv`
- no-column gate rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v168_v167_node1_alt_pairs_20260624/no_column_gate_rows.jsonl`
- no-column gate rows csv: `BPC_future/results/journey_tail_action_controller_audit_v168_v167_node1_alt_pairs_20260624/no_column_gate_rows.csv`

## No-column Gate Counts

按 gate_reason:
- `depth_above_max`: 43
- `depth_below_min`: 2
- `width_guard_pool_child_width_exceeds_cap`: 1

按 tail_action:
- `EARLY_BRANCH`: 46

## Early Branch Child Activity

- node=1 depth=1 cg=2 no_column=true children=`3,4` started=2/2 subtree_nodes=6 pricing=17 negative_pricing=10 cb_retry=6 subtree_early_branch=0 subtree_no_column=0 span=198.833792
- node=2 depth=1 cg=1 no_column=true children=`9,10` started=2/2 subtree_nodes=36 pricing=92 negative_pricing=37 cb_retry=56 subtree_early_branch=0 subtree_no_column=0 span=175.34964
- node=1 depth=1 cg=2 no_column=true children=`3,4` started=2/2 subtree_nodes=10 pricing=25 negative_pricing=13 cb_retry=12 subtree_early_branch=0 subtree_no_column=0 span=199.521826
