# Tree-Policy Top200 Context Competitors

日期：2026-06-27

## 机器字段

```text
input_row_count = 84
output_row_count = 967
added_context_competitor_count = 883
max_competitors_per_positive = 200
competitor_weight = 0.05
label_type_counts = {'strong_positive': 29, 'hard_negative': 52, 'controlled_replay_positive': 2, 'controlled_replay_hard_negative': 1, 'context_competitor_negative': 883}
skipped_counts = {'duplicate_context_pair': 53, 'positive_without_added_competitor': 2}
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
production_ready = false
```

## 边界

新增 competitor rows 是低权重排序负例，不是完整反事实求解失败证书；只能用于 tree-policy 排序训练。
