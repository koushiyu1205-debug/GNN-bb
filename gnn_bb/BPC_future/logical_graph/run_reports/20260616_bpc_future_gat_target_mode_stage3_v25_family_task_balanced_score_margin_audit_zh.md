# GAT Batch Impact Score Margin Audit 报告

日期：2026-06-16

## 结论

本报告复用 opportunity mining 的 validation records，审计 missed high-ROI batch
距离当前 candidate / batch threshold 还差多少，以及是否缺同 context 对照样本。
它只做离线诊断，不运行 BPC、pricing、RMP、worker 或 certificate。

```text
validation_record_count = 119
candidate_threshold = 0.31243568658828735
batch_threshold = 0.0
high_roi_opportunities = 30
accepted_high_roi_opportunities = 24
missed_high_roi_opportunities = 6
missed_candidate_score_margin_mean = -0.043098509311676025
missed_candidate_score_margin_min = -0.06432318687438965
missed_without_same_context_contrast_count = 2
recommended_primary = collect_same_context_positive_negative_pairs_for_missed_high_roi_contexts
production_ready = false
selector_can_certificate = false
```

## Candidate Margin Buckets

```json
{
  "moderate_candidate_score_gap": 1,
  "near_candidate_threshold": 5
}
```

## Family Summary

```json
{
  "random-wave": {
    "candidate_margin_bucket_counts": {
      "near_candidate_threshold": 5
    },
    "contexts": [
      "5751b1799b606ad1",
      "a67f331bdb819d7d",
      "e6b17bbf825984ae"
    ],
    "missed_candidate_score_margin_mean": -0.038853573799133304,
    "missed_candidate_score_margin_min": -0.04308205842971802,
    "missed_high_roi_opportunities": 5,
    "missed_without_same_context_contrast_count": 2,
    "task_count_counts": {
      "50": 5
    }
  },
  "sector-wave": {
    "candidate_margin_bucket_counts": {
      "moderate_candidate_score_gap": 1
    },
    "contexts": [
      "45baa40751a0bf77"
    ],
    "missed_candidate_score_margin_mean": -0.06432318687438965,
    "missed_candidate_score_margin_min": -0.06432318687438965,
    "missed_high_roi_opportunities": 1,
    "missed_without_same_context_contrast_count": 0,
    "task_count_counts": {
      "20": 1
    }
  }
}
```

## Recommended Next Step

```json
{
  "candidate_margin_bucket_counts": {
    "moderate_candidate_score_gap": 1,
    "near_candidate_threshold": 5
  },
  "contexts_needing_contrast": [
    {
      "context_hash": "a67f331bdb819d7d",
      "family": "random-wave",
      "missed_high_roi_opportunities": 1,
      "task_counts": [
        50
      ]
    },
    {
      "context_hash": "e6b17bbf825984ae",
      "family": "random-wave",
      "missed_high_roi_opportunities": 1,
      "task_counts": [
        50
      ]
    }
  ],
  "missed_family_counts": {
    "random-wave": 5,
    "sector-wave": 1
  },
  "missed_without_same_context_contrast": 2,
  "primary": "collect_same_context_positive_negative_pairs_for_missed_high_roi_contexts"
}
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
