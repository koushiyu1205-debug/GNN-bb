# V500 Tree-Policy Context Competitors

日期：2026-06-27

## 结论

在 V495 的 81 条 rows 基础上，从成功 tree-policy 正例事件中新增低权重 competitor negative = 108。

## 机器字段

```text
source_rows = 81
added_context_competitor_rows = 108
merged_rows = 189
label_type_counts = {'strong_positive': 29, 'hard_negative': 52, 'context_competitor_negative': 108}
output_path = BPC_future/data/gat_branch_action_sanity/v500_tree_policy_event_rows_with_context_competitors_20260627/tree_policy_event_rows.jsonl
official_bound_effect = false
certificate_effect = false
production_ready = false
```

## 边界

context competitor negative 是低权重排序约束，不是严格 single-pair 因果负例。它只表达在一个已知成功 tree-policy context 中，成功 pair 应排在这些未选 top competitors 前面。
