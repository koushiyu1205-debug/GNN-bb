# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 1
- row_count = 10

## Tail Action Counts

- `CONTINUE_COLUMN_GENERATION`: 6
- `EARLY_BRANCH`: 4

## 关键计数

- A/frontier refinement: 0
- B/broad plateau: 0
- C/continue CG: 6
- D/early branch: 4
- unknown action: 0
- fathom_possible_if_rc_zero: 0
- micro expansion attempted rows: 0
- recent active-support addition rows: 4
- recent RMP objective progress rows: 3
- early branch triggers: 1
- tail-action early branch triggers: 1
- non-exact early branch triggers: 1
- tail-action queued children: 2
- tail-action non-exact queued children: 2
- observed tail-action child audit rows: 0

## 输出

- summary: `BPC_future/results/journey_tail_action_controller_audit_v9_tail_action_early_branch_180_seed61000_20260623/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v9_tail_action_early_branch_180_seed61000_20260623/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_v9_tail_action_early_branch_180_seed61000_20260623/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v9_tail_action_early_branch_180_seed61000_20260623/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_v9_tail_action_early_branch_180_seed61000_20260623/early_branch_trigger_rows.csv`

补充：后续代码已增加默认关闭的 `journey_tail_action_child_priority_enabled`。它只让 tail-action early branch 生成的 child 可以通过 `journey_tail_action_child_priority_width` 调整队列顺序，不改变 lower bound、exactness、分支约束或剪枝。此 V9 报告基于补丁前日志，因此只证明 D 类 early branch 本身触发且 exact-safe，不证明 child-priority 的速度收益。
