# V534 Controlled-Weighted Tree Policy Event Rows

日期：2026-06-27

## 机器字段

```text
row_count = 967
label_type_counts = {'strong_positive': 29, 'hard_negative': 52, 'controlled_replay_positive': 2, 'controlled_replay_hard_negative': 1, 'context_competitor_negative': 883}
controlled_replay_positive_weight = 10.0
controlled_replay_hard_negative_weight = 5.0
controlled_context_competitor_weight = 0.1
production_ready = false
official_bound_effect = false
certificate_effect = false
runs_bpc_or_pricing = false
```

## 目的

只做离线训练权重重标定，验证 V525 controlled replay 正例是否能被模型学到；不改变 solver 默认行为。
