# 2026-06-16 BPC_future GAT Target Mode Stage 4 Active-replacement Candidates 报告

## 结论

本报告从 exact capture batch 和同迭代 column-addition 事件中抽取 active/replacement target candidates。
它只读日志，不运行 BPC / pricing / worker，也不改变 admission。

```text
capture_candidate_count = 3
selected_candidate_count = 1
selected_category_counts = {'active_replacement': 1}
selected_task_sets = [[15, 20]]
candidates_path = BPC_future/results/gat_active_replacement_target_candidates_active_only_tranq20_01_20260616/candidates.json
all_checks_pass = true
```

## 选择策略

- 优先选择同迭代 `active_changed_task_set_samples` 命中的 returned journeys；
- 其中同时属于 `replacement_task_set_samples` 的标记为 `active_replacement`；
- 少量保留 replacement-only controls，用于下一步区分 active ROI 与普通 replacement；
- 输出只给 target-materialization runbook 使用，不是 admission safe-source。

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
```
