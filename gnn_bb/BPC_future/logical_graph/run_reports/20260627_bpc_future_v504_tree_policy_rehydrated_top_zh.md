# V504 Tree-Policy Rows Rehydrated Top

日期：2026-06-27

## 结论

从 source_log_file 补回原始 branch candidate `top`：rehydrated_rows = 189, missing = 0。

## 机器字段

```text
source_rows = 189
rehydrated_rows = 189
missing_source_event_rows = 0
label_type_counts = {'strong_positive': 29, 'hard_negative': 52, 'context_competitor_negative': 108}
output_path = BPC_future/data/gat_branch_action_sanity/v504_tree_policy_event_rows_rehydrated_top_20260627/tree_policy_event_rows.jsonl
official_bound_effect = false
certificate_effect = false
production_ready = false
```

## 说明

V503 暴露出训练 rows 使用 priority_top rank、部署使用 baseline top rank 的口径不一致。V504 rows 保留 top 和 priority_top，使 dataset builder 可以同时构造 baseline rank 与 score-priority rank。
