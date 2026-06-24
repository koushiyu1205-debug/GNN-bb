# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 3
- row_count = 155

## Tail Action Counts

- `BROAD_PLATEAU_FALLBACK`: 25
- `CONTINUE_COLUMN_GENERATION`: 44
- `EARLY_BRANCH`: 86

## 关键计数

- A/frontier refinement: 0
- B/broad plateau: 25
- C/continue CG: 44
- D/early branch: 86
- unknown action: 0
- fathom_possible_if_rc_zero: 38
- micro expansion attempted rows: 0
- recent active-support addition rows: 36
- recent RMP objective progress rows: 39
- early branch triggers: 20
- tail-action early branch triggers: 20
- tail-action no-column early branch triggers: 20
- non-exact early branch triggers: 20
- no-column gate rows: 46
- no-column before-final-probe gate rows: 46
- no-column before-final-probe disabled rows: 0
- no-column gate D/early-branch rows: 32
- no-column before-final-probe disabled D rows: 0
- tail-action queued children: 40
- tail-action non-exact queued children: 40
- observed tail-action child audit rows: 47
- tail-action child min queue priority width: 0
- tail-action child max queue priority width: 0

## 输出

- summary: `BPC_future/results/journey_tail_action_controller_audit_v166_before_final_probe_optin_probe3_220_20260624/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v166_before_final_probe_optin_probe3_220_20260624/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_v166_before_final_probe_optin_probe3_220_20260624/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v166_before_final_probe_optin_probe3_220_20260624/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_v166_before_final_probe_optin_probe3_220_20260624/early_branch_trigger_rows.csv`
- no-column gate rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v166_before_final_probe_optin_probe3_220_20260624/no_column_gate_rows.jsonl`
- no-column gate rows csv: `BPC_future/results/journey_tail_action_controller_audit_v166_before_final_probe_optin_probe3_220_20260624/no_column_gate_rows.csv`

## No-column Gate Counts

按 gate_reason:
- `depth_above_max`: 6
- `depth_below_min`: 3
- `tail_action_not_early_branch`: 14
- `width_guard_pool_child_width_exceeds_cap`: 23

按 tail_action:
- `BROAD_PLATEAU_FALLBACK`: 14
- `EARLY_BRANCH`: 32

## Early Branch Child Activity

- node=1 depth=1 cg=2 no_column=true children=`3,4` started=2/2 subtree_nodes=20 pricing=59 negative_pricing=31 cb_retry=14 subtree_early_branch=9 subtree_no_column=9 span=198.988572
- node=2 depth=1 cg=1 no_column=true children=`5,6` started=2/2 subtree_nodes=22 pricing=39 negative_pricing=14 cb_retry=9 subtree_early_branch=9 subtree_no_column=9 span=190.106938
- node=3 depth=2 cg=2 no_column=true children=`7,8` started=2/2 subtree_nodes=4 pricing=24 negative_pricing=16 cb_retry=14 subtree_early_branch=1 subtree_no_column=1 span=112.450288
- node=4 depth=2 cg=2 no_column=true children=`9,10` started=2/2 subtree_nodes=14 pricing=27 negative_pricing=9 cb_retry=0 subtree_early_branch=6 subtree_no_column=6 span=177.453392
- node=5 depth=2 cg=1 no_column=true children=`11,12` started=2/2 subtree_nodes=10 pricing=21 negative_pricing=9 cb_retry=6 subtree_early_branch=4 subtree_no_column=4 span=159.771913
- node=6 depth=2 cg=1 no_column=true children=`13,14` started=2/2 subtree_nodes=10 pricing=14 negative_pricing=3 cb_retry=3 subtree_early_branch=3 subtree_no_column=3 span=164.204139
- node=8 depth=3 cg=2 no_column=true children=`15,16` started=2/2 subtree_nodes=2 pricing=14 negative_pricing=9 cb_retry=11 subtree_early_branch=0 subtree_no_column=0 span=73.472143
- node=9 depth=3 cg=3 no_column=true children=`17,18` started=2/2 subtree_nodes=6 pricing=11 negative_pricing=3 cb_retry=0 subtree_early_branch=2 subtree_no_column=2 span=138.325789
- node=10 depth=3 cg=2 no_column=true children=`19,20` started=2/2 subtree_nodes=6 pricing=7 negative_pricing=2 cb_retry=0 subtree_early_branch=2 subtree_no_column=2 span=86.365065
- node=11 depth=3 cg=2 no_column=true children=`21,22` started=2/2 subtree_nodes=2 pricing=8 negative_pricing=4 cb_retry=6 subtree_early_branch=0 subtree_no_column=0 span=94.697859
