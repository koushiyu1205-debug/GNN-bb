# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 11
- row_count = 615

## Tail Action Counts

- `BROAD_PLATEAU_FALLBACK`: 16
- `CONTINUE_COLUMN_GENERATION`: 152
- `EARLY_BRANCH`: 447

## 关键计数

- A/frontier refinement: 0
- B/broad plateau: 16
- C/continue CG: 152
- D/early branch: 447
- unknown action: 0
- fathom_possible_if_rc_zero: 28
- micro expansion attempted rows: 0
- recent active-support addition rows: 194
- recent RMP objective progress rows: 199
- early branch triggers: 28
- tail-action early branch triggers: 28
- tail-action no-column early branch triggers: 28
- non-exact early branch triggers: 28
- no-column gate rows: 228
- no-column before-final-probe gate rows: 228
- no-column before-final-probe disabled rows: 0
- no-column gate D/early-branch rows: 220
- no-column before-final-probe disabled D rows: 0
- tail-action queued children: 56
- tail-action non-exact queued children: 56
- observed tail-action child audit rows: 155
- tail-action child min queue priority width: -1
- tail-action child max queue priority width: -1

## 输出

- summary: `BPC_future/results/journey_tail_action_controller_audit_v171_v167_full_replay11_20260624/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v171_v167_full_replay11_20260624/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_v171_v167_full_replay11_20260624/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v171_v167_full_replay11_20260624/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_v171_v167_full_replay11_20260624/early_branch_trigger_rows.csv`
- no-column gate rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v171_v167_full_replay11_20260624/no_column_gate_rows.jsonl`
- no-column gate rows csv: `BPC_future/results/journey_tail_action_controller_audit_v171_v167_full_replay11_20260624/no_column_gate_rows.csv`

## No-column Gate Counts

按 gate_reason:
- `depth_above_max`: 191
- `depth_below_min`: 23
- `tail_action_not_early_branch`: 8
- `width_guard_pool_child_width_exceeds_cap`: 6

按 tail_action:
- `BROAD_PLATEAU_FALLBACK`: 8
- `EARLY_BRANCH`: 220

## Early Branch Child Activity

- node=1 depth=1 cg=2 no_column=true children=`3,4` started=2/2 subtree_nodes=6 pricing=17 negative_pricing=10 cb_retry=6 subtree_early_branch=0 subtree_no_column=0 span=198.833792
- node=2 depth=1 cg=1 no_column=true children=`9,10` started=2/2 subtree_nodes=36 pricing=92 negative_pricing=37 cb_retry=56 subtree_early_branch=0 subtree_no_column=0 span=175.34964
- node=1 depth=1 cg=2 no_column=true children=`3,4` started=2/2 subtree_nodes=10 pricing=25 negative_pricing=13 cb_retry=12 subtree_early_branch=0 subtree_no_column=0 span=199.521826
- node=1 depth=1 cg=1 no_column=true children=`3,4` started=2/2 subtree_nodes=34 pricing=82 negative_pricing=33 cb_retry=53 subtree_early_branch=0 subtree_no_column=0 span=182.337757
- node=2 depth=1 cg=2 no_column=true children=`9,10` started=2/2 subtree_nodes=6 pricing=12 negative_pricing=8 cb_retry=6 subtree_early_branch=0 subtree_no_column=0 span=24.648863
- node=1 depth=1 cg=1 no_column=true children=`3,4` started=2/2 subtree_nodes=18 pricing=52 negative_pricing=29 cb_retry=27 subtree_early_branch=0 subtree_no_column=0 span=185.463705
- node=2 depth=1 cg=2 no_column=true children=`9,10` started=2/2 subtree_nodes=14 pricing=38 negative_pricing=19 cb_retry=18 subtree_early_branch=0 subtree_no_column=0 span=136.137394
- node=1 depth=1 cg=1 no_column=true children=`3,4` started=2/2 subtree_nodes=22 pricing=65 negative_pricing=25 cb_retry=34 subtree_early_branch=0 subtree_no_column=0 span=183.3332
- node=2 depth=1 cg=1 no_column=true children=`9,10` started=2/2 subtree_nodes=10 pricing=24 negative_pricing=13 cb_retry=12 subtree_early_branch=0 subtree_no_column=0 span=64.798757
- node=3 depth=2 cg=2 no_column=true children=`7,8` started=2/2 subtree_nodes=4 pricing=12 negative_pricing=8 cb_retry=6 subtree_early_branch=0 subtree_no_column=0 span=25.626578
- node=4 depth=2 cg=2 no_column=true children=`11,12` started=2/2 subtree_nodes=6 pricing=13 negative_pricing=6 cb_retry=6 subtree_early_branch=0 subtree_no_column=0 span=23.905413
- node=5 depth=2 cg=1 no_column=true children=`17,18` started=2/2 subtree_nodes=6 pricing=19 negative_pricing=9 cb_retry=6 subtree_early_branch=0 subtree_no_column=0 span=108.071152
- node=3 depth=2 cg=2 no_column=true children=`7,8` started=2/2 subtree_nodes=6 pricing=12 negative_pricing=8 cb_retry=6 subtree_early_branch=0 subtree_no_column=0 span=25.678502
- node=4 depth=2 cg=2 no_column=true children=`13,14` started=2/2 subtree_nodes=6 pricing=13 negative_pricing=6 cb_retry=6 subtree_early_branch=0 subtree_no_column=0 span=23.966499
- node=5 depth=2 cg=1 no_column=true children=`19,20` started=2/2 subtree_nodes=8 pricing=18 negative_pricing=7 cb_retry=9 subtree_early_branch=0 subtree_no_column=0 span=108.196339
- node=3 depth=2 cg=2 no_column=true children=`7,8` started=2/2 subtree_nodes=6 pricing=10 negative_pricing=6 cb_retry=6 subtree_early_branch=0 subtree_no_column=0 span=21.561374
- node=4 depth=2 cg=2 no_column=true children=`13,14` started=2/2 subtree_nodes=6 pricing=13 negative_pricing=6 cb_retry=6 subtree_early_branch=0 subtree_no_column=0 span=23.911195
- node=5 depth=2 cg=1 no_column=true children=`19,20` started=2/2 subtree_nodes=8 pricing=20 negative_pricing=9 cb_retry=9 subtree_early_branch=0 subtree_no_column=0 span=107.135962
- node=3 depth=2 cg=2 no_column=true children=`7,8` started=2/2 subtree_nodes=6 pricing=15 negative_pricing=8 cb_retry=6 subtree_early_branch=0 subtree_no_column=0 span=26.668962
- node=4 depth=2 cg=2 no_column=true children=`13,14` started=2/2 subtree_nodes=2 pricing=12 negative_pricing=8 cb_retry=6 subtree_early_branch=0 subtree_no_column=0 span=26.001942
