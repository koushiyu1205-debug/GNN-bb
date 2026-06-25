# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 5
- row_count = 146

## Tail Action Counts

- `BROAD_PLATEAU_FALLBACK`: 2
- `CONTINUE_COLUMN_GENERATION`: 48
- `EARLY_BRANCH`: 96

## Tail Action Classes

- `B_BROAD_PLATEAU`: 2
- `C_CONTINUE_CG`: 48
- `D_EARLY_BRANCH`: 96

## Tail Action Productivity Classes

- `pricing_active_support_productive`: 24
- `pricing_has_negative_columns`: 6
- `pricing_no_negative_columns`: 2
- `pricing_productivity_signals_incomplete`: 18
- `pricing_unproductive_no_negative_columns`: 89
- `pricing_weak_columns_tail`: 7

## 关键计数

- A/frontier refinement: 0
- B/broad plateau: 2
- C/continue CG: 48
- D/early branch: 96
- unknown action: 0
- fathom_possible_if_rc_zero: 8
- micro expansion attempted rows: 0
- recent active-support addition rows: 34
- recent RMP objective progress rows: 29
- early branch triggers: 7
- tail-action early branch triggers: 7
- tail-action no-column early branch triggers: 7
- non-exact early branch triggers: 7
- no-column gate rows: 30
- no-column before-final-probe gate rows: 30
- no-column before-final-probe disabled rows: 0
- no-column gate D/early-branch rows: 28
- no-column before-final-probe disabled D rows: 0
- tail-action queued children: 14
- tail-action non-exact queued children: 14
- observed tail-action child audit rows: 43
- tail-action low min-fill completion retries: 0
- tail-action completion retry found-negative rows: 1
- tail-action completion retry certified no-negative rows: 8
- tail-action completion retry incomplete rows: 5
- tail-action child min queue priority width: -1
- tail-action child max queue priority width: -1

## 输出

- summary: `BPC_future/results/journey_tail_action_controller_audit_v365_v364_strict_dtail_replay_20260625/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v365_v364_strict_dtail_replay_20260625/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_v365_v364_strict_dtail_replay_20260625/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v365_v364_strict_dtail_replay_20260625/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_v365_v364_strict_dtail_replay_20260625/early_branch_trigger_rows.csv`
- no-column gate rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v365_v364_strict_dtail_replay_20260625/no_column_gate_rows.jsonl`
- no-column gate rows csv: `BPC_future/results/journey_tail_action_controller_audit_v365_v364_strict_dtail_replay_20260625/no_column_gate_rows.csv`

## No-column Gate Counts

按 gate_reason:
- `depth_above_max`: 14
- `depth_below_min`: 14
- `tail_action_not_early_branch`: 2

按 tail_action:
- `BROAD_PLATEAU_FALLBACK`: 2
- `EARLY_BRANCH`: 28

按 tail_action_class:
- `B_BROAD_PLATEAU`: 2
- `D_EARLY_BRANCH`: 28

按 tail_action_productivity_class:
- `pricing_no_negative_columns`: 2
- `pricing_unproductive_no_negative_columns`: 28

## Early Branch Child Activity

- node=0 depth=0 cg=35 no_column=true children=`1,2` started=2/2 subtree_nodes=10 pricing=38 negative_pricing=17 cb_retry=20 cb_low_min_fill=0 cb_min_fill_values=`10:6` subtree_early_branch=0 subtree_no_column=0 span=491.199086
- node=1 depth=1 cg=1 no_column=true children=`3,4` started=2/2 subtree_nodes=4 pricing=13 negative_pricing=5 cb_retry=7 cb_low_min_fill=0 cb_min_fill_values=`10:2` subtree_early_branch=0 subtree_no_column=0 span=416.513363
- node=2 depth=1 cg=3 no_column=true children=`7,8` started=2/2 subtree_nodes=2 pricing=14 negative_pricing=7 cb_retry=7 cb_low_min_fill=0 cb_min_fill_values=`10:2` subtree_early_branch=0 subtree_no_column=0 span=187.551216
- node=3 depth=2 cg=1 no_column=true children=`5,6` started=2/2 subtree_nodes=6 pricing=13 negative_pricing=10 cb_retry=6 cb_low_min_fill=0 cb_min_fill_values=`10:2` subtree_early_branch=0 subtree_no_column=0 span=121.944162
- node=4 depth=2 cg=1 no_column=true children=`11,12` started=1/2 subtree_nodes=2 pricing=7 negative_pricing=3 cb_retry=1 cb_low_min_fill=0 cb_min_fill_values=`` subtree_early_branch=0 subtree_no_column=0 span=40.287284
- node=5 depth=3 cg=1 no_column=true children=`7,8` started=2/2 subtree_nodes=4 pricing=8 negative_pricing=4 cb_retry=3 cb_low_min_fill=0 cb_min_fill_values=`10:1` subtree_early_branch=0 subtree_no_column=0 span=76.774352
- node=5 depth=3 cg=3 no_column=true children=`7,8` started=1/2 subtree_nodes=2 pricing=9 negative_pricing=9 cb_retry=6 cb_low_min_fill=0 cb_min_fill_values=`10:1` subtree_early_branch=0 subtree_no_column=0 span=81.89658
