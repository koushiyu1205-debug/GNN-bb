# Tree-Policy Top200 Context Competitors

日期：2026-06-27

## 机器字段

```text
input_row_count = 189
output_row_count = 966
added_context_competitor_count = 885
max_competitors_per_positive = 200
competitor_weight = 0.05
label_type_counts = {'strong_positive': 29, 'hard_negative': 52, 'context_competitor_negative': 885}
skipped_counts = {'dropped_existing_context_competitor': 108, 'duplicate_context_pair': 1}
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
production_ready = false
```

## 边界

新增 competitor rows 是低权重排序负例，不是完整反事实求解失败证书；只能用于 tree-policy 排序训练。
