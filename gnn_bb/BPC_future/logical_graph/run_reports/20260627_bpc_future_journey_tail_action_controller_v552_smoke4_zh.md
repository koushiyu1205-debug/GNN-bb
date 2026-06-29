# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 4
- row_count = 211

## Tail Action Counts

- `BROAD_PLATEAU_FALLBACK`: 22
- `CONTINUE_COLUMN_GENERATION`: 86
- `EARLY_BRANCH`: 103

## Tail Action Classes

- `B_BROAD_PLATEAU`: 22
- `C_CONTINUE_CG`: 86
- `D_EARLY_BRANCH`: 103

## Tail Action Productivity Classes

- `pricing_active_support_productive`: 25
- `pricing_has_negative_columns`: 25
- `pricing_no_negative_columns`: 22
- `pricing_objective_productive`: 4
- `pricing_productivity_signals_incomplete`: 32
- `pricing_unproductive_no_negative_columns`: 89
- `pricing_weak_columns_tail`: 14

## 关键计数

- A/frontier refinement: 0
- B/broad plateau: 22
- C/continue CG: 86
- D/early branch: 103
- unknown action: 0
- fathom_possible_if_rc_zero: 47
- micro expansion attempted rows: 0
- recent active-support addition rows: 78
- recent RMP objective progress rows: 73
- early branch triggers: 4
- tail-action early branch triggers: 4
- tail-action no-column early branch triggers: 4
- non-exact early branch triggers: 4
- no-column gate rows: 54
- no-column before-final-probe gate rows: 54
- no-column before-final-probe disabled rows: 0
- no-column gate D/early-branch rows: 42
- no-column before-final-probe disabled D rows: 0
- tail-action queued children: 8
- tail-action non-exact queued children: 8
- observed tail-action child audit rows: 35
- tail-action low min-fill completion retries: 0
- tail-action completion retry found-negative rows: 2
- tail-action completion retry certified no-negative rows: 25
- tail-action completion retry incomplete rows: 3
- tail-action child min queue priority width: -1
- tail-action child max queue priority width: -1

## 输出

- summary: `BPC_future/results/journey_tail_action_controller_v552_smoke4_20260627/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_v552_smoke4_20260627/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_v552_smoke4_20260627/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_v552_smoke4_20260627/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_v552_smoke4_20260627/early_branch_trigger_rows.csv`
- no-column gate rows jsonl: `BPC_future/results/journey_tail_action_controller_v552_smoke4_20260627/no_column_gate_rows.jsonl`
- no-column gate rows csv: `BPC_future/results/journey_tail_action_controller_v552_smoke4_20260627/no_column_gate_rows.csv`

## No-column Gate Counts

按 gate_reason:
- `depth_above_max`: 30
- `depth_below_min`: 8
- `tail_action_not_early_branch`: 12
- `width_guard_pool_child_width_exceeds_cap`: 4

按 tail_action:
- `BROAD_PLATEAU_FALLBACK`: 12
- `EARLY_BRANCH`: 42

按 tail_action_class:
- `B_BROAD_PLATEAU`: 12
- `D_EARLY_BRANCH`: 42

按 tail_action_productivity_class:
- `pricing_no_negative_columns`: 12
- `pricing_unproductive_no_negative_columns`: 42

## Early Branch Child Activity

- node=1 depth=1 cg=2 no_column=true children=`3,4` started=2/2 subtree_nodes=22 pricing=89 negative_pricing=37 cb_retry=43 cb_low_min_fill=0 cb_min_fill_values=`10:14` subtree_early_branch=0 subtree_no_column=0 span=532.710984
- node=3 depth=2 cg=3 no_column=true children=`7,8` started=2/2 subtree_nodes=10 pricing=39 negative_pricing=15 cb_retry=19 cb_low_min_fill=0 cb_min_fill_values=`10:6` subtree_early_branch=0 subtree_no_column=0 span=384.546365
- node=1 depth=1 cg=5 no_column=true children=`3,4` started=2/2 subtree_nodes=2 pricing=15 negative_pricing=12 cb_retry=3 cb_low_min_fill=0 cb_min_fill_values=`10:1` subtree_early_branch=0 subtree_no_column=0 span=202.598186
- node=1 depth=1 cg=5 no_column=true children=`3,4` started=2/2 subtree_nodes=14 pricing=87 negative_pricing=65 cb_retry=31 cb_low_min_fill=0 cb_min_fill_values=`10:9` subtree_early_branch=0 subtree_no_column=0 span=439.513265
