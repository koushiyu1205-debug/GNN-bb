# GAT Batch Impact Score Margin Audit 报告

日期：2026-06-16

## 结论

本报告复用 opportunity mining 的 validation records，审计 missed high-ROI batch
距离当前 candidate / batch threshold 还差多少，以及是否缺同 context 对照样本。
它只做离线诊断，不运行 BPC、pricing、RMP、worker 或 certificate。

```text
validation_record_count = 104
candidate_threshold = 0.60591059923172
batch_threshold = 0.4583219885826111
high_roi_opportunities = 27
accepted_high_roi_opportunities = 18
missed_high_roi_opportunities = 9
missed_candidate_score_margin_mean = -0.29302062425348496
missed_candidate_score_margin_min = -0.46770481765270233
missed_without_same_context_contrast_count = 4
recommended_primary = collect_same_context_positive_negative_pairs_for_missed_high_roi_contexts
production_ready = false
selector_can_certificate = false
```

## Candidate Margin Buckets

```json
{
  "deep_candidate_score_gap": 6,
  "moderate_candidate_score_gap": 2,
  "near_candidate_threshold": 1
}
```

## Family Summary

```json
{
  "random-wave": {
    "candidate_margin_bucket_counts": {
      "deep_candidate_score_gap": 3,
      "moderate_candidate_score_gap": 1
    },
    "contexts": [
      "5751b1799b606ad1",
      "a67f331bdb819d7d",
      "e6b17bbf825984ae"
    ],
    "missed_candidate_score_margin_mean": -0.3019028417766094,
    "missed_candidate_score_margin_min": -0.4113938957452774,
    "missed_high_roi_opportunities": 4,
    "missed_without_same_context_contrast_count": 2,
    "task_count_counts": {
      "50": 4
    }
  },
  "sector-wave": {
    "candidate_margin_bucket_counts": {
      "deep_candidate_score_gap": 3,
      "moderate_candidate_score_gap": 1,
      "near_candidate_threshold": 1
    },
    "contexts": [
      "45baa40751a0bf77",
      "9fadf4f7b39742a2",
      "ce3508e12ad69da7"
    ],
    "missed_candidate_score_margin_mean": -0.28591485023498536,
    "missed_candidate_score_margin_min": -0.46770481765270233,
    "missed_high_roi_opportunities": 5,
    "missed_without_same_context_contrast_count": 2,
    "task_count_counts": {
      "20": 5
    }
  }
}
```

## Recommended Next Step

```json
{
  "candidate_margin_bucket_counts": {
    "deep_candidate_score_gap": 6,
    "moderate_candidate_score_gap": 2,
    "near_candidate_threshold": 1
  },
  "contexts_needing_contrast": [
    {
      "context_hash": "9fadf4f7b39742a2",
      "family": "sector-wave",
      "missed_high_roi_opportunities": 2,
      "task_counts": [
        20
      ]
    },
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
    "random-wave": 4,
    "sector-wave": 5
  },
  "missed_without_same_context_contrast": 4,
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
