# 2026-06-16 BPC_future GAT Target Mode Stage 4 v10 Online Shadow Target Candidates 报告

## 结论

本报告从 20-task shadow+capture 日志中抽取下一轮 same-context target intervention 候选。
它只读日志和 Stage 3 safe-source artifacts，不运行 BPC / pricing / worker，也不改变 admission。

```text
capture_candidate_count = 60
selected_candidate_count = 8
selected_category_counts = {'no_offline_task_set_overlap_control': 2, 'task_set_overlap_conflict_control': 1, 'task_set_overlap_no_conflict': 5}
selected_context_count = 2
candidates_path = BPC_future/results/gat_online_shadow_target_candidates_v10_tranq20_01_20260616/candidates.json
all_checks_pass = true
```

## 选择策略

- 优先选择 offline high-priority task-set 命中且无 offline delay 冲突的 online 候选；
- 少量保留 conflict / miss control，用于下一轮同上下文 ROI 标签区分；
- 所有候选都带完整 context / dual / cut / branch / forbidden / pool hash；
- 输出只给 target-materialization runbook 使用，不是 admission safe-source。

## Selected Task Sets

```text
[1, 5]
[3, 8, 11]
[9, 15, 17]
[4, 15, 17]
[2, 10, 14]
[16, 20]
[16, 17]
[10, 17]
```

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
```
