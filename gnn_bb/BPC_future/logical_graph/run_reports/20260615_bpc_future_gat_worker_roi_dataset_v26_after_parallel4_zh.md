# GAT Worker ROI Dataset v26 合并报告

日期：2026-06-15

## 机器字段

```text
training_row_count = 104
positive_trajectory_roi_count = 34
negative_trajectory_roi_count = 70
training_rows_to_150 = 46
positive_to_50 = 16
production_ready = false
certificate_ready = false
```

## Cell Counts

```json
{
  "(20, 'greedy-anchor', 'apollo15_20km')": {
    "negative": 12,
    "positive": 9,
    "positive_rate": 0.42857142857142855,
    "total": 21
  },
  "(20, 'greedy-anchor', 'tranquillitatis_balmer_like_20km')": {
    "negative": 11,
    "positive": 8,
    "positive_rate": 0.42105263157894735,
    "total": 19
  },
  "(20, 'random-wave', 'apollo15_20km')": {
    "negative": 11,
    "positive": 1,
    "positive_rate": 0.08333333333333333,
    "total": 12
  },
  "(20, 'random-wave', 'tranquillitatis_balmer_like_20km')": {
    "negative": 15,
    "positive": 1,
    "positive_rate": 0.0625,
    "total": 16
  },
  "(20, 'sector-wave', 'apollo15_20km')": {
    "negative": 13,
    "positive": 6,
    "positive_rate": 0.3157894736842105,
    "total": 19
  },
  "(20, 'sector-wave', 'tranquillitatis_balmer_like_20km')": {
    "negative": 8,
    "positive": 9,
    "positive_rate": 0.5294117647058824,
    "total": 17
  }
}
```

## 结论

- v26 增量 5 条全部为 negative trajectory ROI；
- 当前正样本缺口没有缩小，说明 remaining sector/greedy high-priority pool 的 ROI 已转弱；
- 下一步应优先采能产生正 ROI 的新上下文，而不是继续消费同类 Apollo sector 候选；
- 训练标签仍只来自真实 worker A/B trajectory ROI。
