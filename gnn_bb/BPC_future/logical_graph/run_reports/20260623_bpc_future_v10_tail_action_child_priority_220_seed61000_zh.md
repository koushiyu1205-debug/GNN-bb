# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 1
- row_count = 13

## Tail Action Counts

- `CONTINUE_COLUMN_GENERATION`: 6
- `EARLY_BRANCH`: 4
- `FRONTIER_REFINEMENT`: 3

## 关键计数

- A/frontier refinement: 3
- B/broad plateau: 0
- C/continue CG: 6
- D/early branch: 4
- unknown action: 0
- fathom_possible_if_rc_zero: 3
- micro expansion attempted rows: 0
- recent active-support addition rows: 7
- recent RMP objective progress rows: 6
- early branch triggers: 1
- tail-action early branch triggers: 1
- tail-action no-column early branch triggers: 0
- non-exact early branch triggers: 1
- tail-action queued children: 2
- tail-action non-exact queued children: 2
- observed tail-action child audit rows: 4
- tail-action child min queue priority width: -1
- tail-action child max queue priority width: -1

## 输出

- summary: `BPC_future/results/journey_tail_action_controller_audit_v10_tail_action_child_priority_220_seed61000_20260623/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v10_tail_action_child_priority_220_seed61000_20260623/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_v10_tail_action_child_priority_220_seed61000_20260623/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v10_tail_action_child_priority_220_seed61000_20260623/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_v10_tail_action_child_priority_220_seed61000_20260623/early_branch_trigger_rows.csv`

## 运行结论

该 fresh probe 使用 canonical random-TW 20 `seed61000`，外部预算 220s，结果为：

```text
status=EXTERNAL_TIME_LIMIT
wall_time=220.034807s
```

本次只验证 child-priority 调度，不是 20 规模 200s gate。

关键事件序列：

```text
125.603298s  root exact_completion_bound_retry OPTIMAL
125.685520s  root branch，child 1/2 lower_bound_exact=true
162.723293s  node 1 tail-action early branch，trigger=tail_action_controller
162.761930s  child 3 queued，queue_priority_width=-1，lower_bound_exact=false
162.761971s  child 4 queued，queue_priority_width=-1，lower_bound_exact=false
162.781012s  node 3 RMP starts
216.582741s  node 3 exact_pricing_completion_bound_retry
220.034807s  external timeout
```

与 V9 的区别是：V9 中 node 1 生成 child 3/4 后，180s 内没有观察到 child audit；V10 中 `tail_action_observed_child_audit_count=4`，说明 D 类 child 确实被优先处理到了。

## 边界

`journey_tail_action_child_priority_enabled` 只改变队列顺序：

- 不改变 inherited lower bound；
- 不把 node 1 的 RMP objective 当 exact bound；
- 不改变 branch constraint；
- 不剪枝；
- 子节点仍需要 exact pricing / completion-bound closure。

因此 V10 的结论是“队列问题已验证解决”，不是“proof tail 已解决”。node 3 在 216.58s 进入 completion-bound retry，说明当前阻塞已转移到 D 类 child 自身的 proof tail。

node 3 前几轮 controller 给出 `FRONTIER_REFINEMENT`，但这些 audit row 都伴随 `negative_journey_requires_column_addition`；这不是 final-probe 的可剪枝 Tier 1 机会。到 node 3 no-negative 时，`rmp_objective=584.2437713 < incumbent=584.354872`，再次不满足 A 类 `z_RMP >= UB - eps`。
