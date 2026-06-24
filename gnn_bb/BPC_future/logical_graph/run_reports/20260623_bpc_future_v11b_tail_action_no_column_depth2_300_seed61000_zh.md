# Journey Tail Action Controller 审计

## 元信息

- diagnostic_only = true
- runs_bpc_or_pricing = false
- certificate_effect = false
- official_bound_effect = false
- log_file_count = 1
- row_count = 17

## Tail Action Counts

- `CONTINUE_COLUMN_GENERATION`: 6
- `EARLY_BRANCH`: 6
- `FRONTIER_REFINEMENT`: 5

## 关键计数

- A/frontier refinement: 5
- B/broad plateau: 0
- C/continue CG: 6
- D/early branch: 6
- unknown action: 0
- fathom_possible_if_rc_zero: 5
- micro expansion attempted rows: 0
- recent active-support addition rows: 7
- recent RMP objective progress rows: 6
- early branch triggers: 2
- tail-action early branch triggers: 2
- tail-action no-column early branch triggers: 1
- non-exact early branch triggers: 2
- tail-action queued children: 4
- tail-action non-exact queued children: 4
- observed tail-action child audit rows: 8
- tail-action child min queue priority width: -1
- tail-action child max queue priority width: -1

## 输出

- summary: `BPC_future/results/journey_tail_action_controller_audit_v11b_tail_action_no_column_depth2_300_seed61000_20260623/tail_action_rows.jsonl` 的同目录 `summary.json`
- rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v11b_tail_action_no_column_depth2_300_seed61000_20260623/tail_action_rows.jsonl`
- rows csv: `BPC_future/results/journey_tail_action_controller_audit_v11b_tail_action_no_column_depth2_300_seed61000_20260623/tail_action_rows.csv`
- early branch rows jsonl: `BPC_future/results/journey_tail_action_controller_audit_v11b_tail_action_no_column_depth2_300_seed61000_20260623/early_branch_trigger_rows.jsonl`
- early branch rows csv: `BPC_future/results/journey_tail_action_controller_audit_v11b_tail_action_no_column_depth2_300_seed61000_20260623/early_branch_trigger_rows.csv`

## 运行结论

该 fresh probe 使用 canonical random-TW 20 `seed61000`，外部预算 300s，结果为：

```text
status=EXTERNAL_TIME_LIMIT
wall_time=300.029456s
```

本次只验证 no-column D 类 gate，不是 20 规模 200s gate。

关键事件序列：

```text
90.313525s   root local no-column D 类 audit；因 min_depth=2，未触发 root no-column 分支
105.265030s  root exact_completion_bound_retry OPTIMAL
142.493001s  node 1 普通 tail-action early branch，child 3/4 lower_bound_exact=false
196.221668s  node 3 no-column tail-action early branch，tail_action_no_column=true
196.265865s  child 5 queued，queue_priority_width=-1，lower_bound_exact=false
196.265894s  child 6 queued，queue_priority_width=-1，lower_bound_exact=false
231.713072s  node 4 exact_pricing_completion_bound_retry
276.772964s  node 5 starts
294.162041s  node 5 exact_retry 仍找到 true negative journey
300.029456s  external timeout
```

## 边界

`journey_tail_action_no_column_early_branch_enabled` 只改变搜索调度：

- 不产生 certificate；
- 不把当前 RMP objective 当 exact node bound；
- 不用该 bound 剪枝；
- child 继承已有合法祖先下界，且 `lower_bound_exact=false`；
- child 最终仍要靠 exact pricing / completion-bound closure。

因此 V11b 的结论是“node 3 的 local no-column completion-bound retry 可以被 exact-safe 地调度掉”，不是“20 规模已经加速达标”。

新的阻塞是 sibling/deeper child 的 proof-tail 链：node 4 在 cg1 进入 completion-bound retry，node 5 到 294s 仍找到 true negative journey。下一步如果把 no-column gate 放宽到 cg1，必须增加 branch-width、remaining time、depth 和 child-budget 限制，否则可能只是更快制造更深子树。
