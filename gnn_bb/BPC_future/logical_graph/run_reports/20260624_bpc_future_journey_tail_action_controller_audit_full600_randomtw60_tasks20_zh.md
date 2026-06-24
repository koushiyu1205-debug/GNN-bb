# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 60
- row_count = 0

## 结论

本次 `row_count=0` 是日志口径问题，不是算法结论。当时 full600 benchmark 使用的 canonical 20-task 配置没有写出 `journey_corrected_node_bound_audit` 事件，因此审计脚本没有可解析的 Tail Action Controller 行。

已补修正：`moon_trek_20_smoke.yaml` 现在打开 `journey_tail_action_audit_enabled`，只用于记录 A/B/C/D 分类、waterline 和 productivity 信号；不启用 corrected-bound fathom，也不启用 tail-action early branch。下一轮 full600 / 小批复验应重新跑本审计，才能得到真实的 A/B/C/D 分布。

## Tail Action Counts


## 关键计数

- A/frontier refinement: 0
- B/broad plateau: 0
- C/continue CG: 0
- D/early branch: 0
- unknown action: 0
- fathom_possible_if_rc_zero: 0
- micro expansion attempted rows: 0
- recent active-support addition rows: 0
- recent RMP objective progress rows: 0
- early branch triggers: 0
- tail-action early branch triggers: 0
- tail-action no-column early branch triggers: 0
- non-exact early branch triggers: 0
- tail-action queued children: 0
- tail-action non-exact queued children: 0
- observed tail-action child audit rows: 0
- tail-action child min queue priority width: None
- tail-action child max queue priority width: None

## 输出

- summary: `BPC_future/results/journey_tail_action_controller_audit_full600_randomtw60_tasks20_20260624/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_full600_randomtw60_tasks20_20260624/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_full600_randomtw60_tasks20_20260624/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_full600_randomtw60_tasks20_20260624/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_full600_randomtw60_tasks20_20260624/early_branch_trigger_rows.csv`
