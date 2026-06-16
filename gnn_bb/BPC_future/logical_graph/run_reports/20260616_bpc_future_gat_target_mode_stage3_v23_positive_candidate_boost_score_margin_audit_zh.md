# GAT Batch Impact Score Margin Audit 报告

日期：2026-06-16

## 结论

本报告复用 opportunity mining 的 validation records，审计 missed high-ROI batch
距离当前 candidate / batch threshold 还差多少，以及是否缺同 context 对照样本。
它只做离线诊断，不运行 BPC、pricing、RMP、worker 或 certificate。

```text
validation_record_count = 119
candidate_threshold = 0.2866392135620117
batch_threshold = 0.46148547530174255
high_roi_opportunities = 30
accepted_high_roi_opportunities = 27
missed_high_roi_opportunities = 3
missed_candidate_score_margin_mean = -0.02922963397577405
missed_candidate_score_margin_min = -0.28226951649412513
missed_without_same_context_contrast_count = 1
recommended_primary = collect_same_context_positive_negative_pairs_for_missed_high_roi_contexts
production_ready = false
selector_can_certificate = false
```

## Candidate Margin Buckets

```json
{
  "deep_candidate_score_gap": 1,
  "near_candidate_threshold": 2
}
```

## Family Summary

```json
{
  "random-wave": {
    "candidate_margin_bucket_counts": {
      "near_candidate_threshold": 1
    },
    "contexts": [
      "e6b17bbf825984ae"
    ],
    "missed_candidate_score_margin_mean": 0.1353708803653717,
    "missed_candidate_score_margin_min": 0.1353708803653717,
    "missed_high_roi_opportunities": 1,
    "missed_without_same_context_contrast_count": 1,
    "task_count_counts": {
      "50": 1
    }
  },
  "sector-wave": {
    "candidate_margin_bucket_counts": {
      "deep_candidate_score_gap": 1,
      "near_candidate_threshold": 1
    },
    "contexts": [
      "45baa40751a0bf77",
      "ce3508e12ad69da7"
    ],
    "missed_candidate_score_margin_mean": -0.11152989114634693,
    "missed_candidate_score_margin_min": -0.28226951649412513,
    "missed_high_roi_opportunities": 2,
    "missed_without_same_context_contrast_count": 0,
    "task_count_counts": {
      "20": 2
    }
  }
}
```

## Recommended Next Step

```json
{
  "candidate_margin_bucket_counts": {
    "deep_candidate_score_gap": 1,
    "near_candidate_threshold": 2
  },
  "contexts_needing_contrast": [
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
    "random-wave": 1,
    "sector-wave": 2
  },
  "missed_without_same_context_contrast": 1,
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
