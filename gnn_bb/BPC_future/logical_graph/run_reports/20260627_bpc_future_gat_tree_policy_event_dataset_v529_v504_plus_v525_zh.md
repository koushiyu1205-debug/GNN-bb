# V529 Tree Policy Event Rows: V504 + V525

日期：2026-06-27

## 结论

合并 V504 rehydrated tree-policy event rows 与 V525 seed61001 严格 controlled replay 标签，并移除已有 context-competitor rows，作为后续统一 top200 competitor expansion 的输入。

## 机器字段

```text
row_count = 84
label_type_counts = {'strong_positive': 31, 'hard_negative': 53}
tree_policy_label_type_counts = {'strong_positive': 29, 'hard_negative': 52, 'controlled_replay_positive': 2, 'controlled_replay_hard_negative': 1}
instance_count = 7
dropped_existing_context_competitors = 108
production_ready = false
official_bound_effect = false
certificate_effect = false
runs_bpc_or_pricing = false
```

## 边界

V529 只是离线标签合并；不运行 BPC/pricing/RMP，不影响 official bound、certificate 或剪枝。
