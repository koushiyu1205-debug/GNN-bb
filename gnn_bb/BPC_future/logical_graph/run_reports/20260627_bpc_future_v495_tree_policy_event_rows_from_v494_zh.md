# V495 Tree-Policy Event Rows From V494

日期：2026-06-27

## 结论

V494 smoke 0 个 OPTIMAL；从 changed branch events 提取 hard-negative rows = 12。

## 机器字段

```text
previous_rows = 69
added_rows = 12
merged_rows = 81
added_reason_counts = {'changed_pair_no_recovery': 8, 'previous_optimal_to_timeout': 4}
output_path = BPC_future/data/gat_branch_action_sanity/v495_tree_policy_event_rows_20260627/tree_policy_event_rows.jsonl
official_bound_effect = false
certificate_effect = false
production_ready = false
```

## 说明

这些 rows 只作为离线 tree-policy hard negative。它们不改变 solver，不提供 bound/certificate。V494 中 seed61001 把 V490 的 OPTIMAL 路径打坏，因此标记为 previous_optimal_to_timeout，权重高于普通 no-recovery。
