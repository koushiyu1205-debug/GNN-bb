# GAT Worker ROI Dataset v25 合并报告

日期：2026-06-15

## 机器字段

```text
training_row_count = 99
positive_trajectory_roi_count = 34
negative_trajectory_roi_count = 65
training_rows_to_150 = 51
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
    "negative": 9,
    "positive": 6,
    "positive_rate": 0.4,
    "total": 15
  },
  "(20, 'sector-wave', 'tranquillitatis_balmer_like_20km')": {
    "negative": 7,
    "positive": 9,
    "positive_rate": 0.5625,
    "total": 16
  }
}
```

## 结论

- v25 合并只使用真实 worker A/B 后的 trajectory ROI 标签；
- HIGH_PRIORITY / DELAY_QUEUE 本身不作为训练标签；
- GAT 仍只用于 trajectory-impact 表达，kNN/OOD 只作安全壳；
- 所有 true-RC negative 仍必须 eventually reachable，不能永久过滤，不能参与证书。
