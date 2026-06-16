# GAT Batch Impact Score Margin Audit 报告

日期：2026-06-16

## 结论

本报告复用 opportunity mining 的 validation records，审计 missed high-ROI batch
距离当前 candidate / batch threshold 还差多少，以及是否缺同 context 对照样本。
它只做离线诊断，不运行 BPC、pricing、RMP、worker 或 certificate。

```text
validation_record_count = 119
candidate_threshold = 0.4959893226623535
batch_threshold = 0.0
high_roi_opportunities = 30
accepted_high_roi_opportunities = 13
missed_high_roi_opportunities = 17
missed_candidate_score_margin_mean = -0.10645150700036217
missed_candidate_score_margin_min = -0.3923274278640747
missed_without_same_context_contrast_count = 6
recommended_primary = collect_same_context_positive_negative_pairs_for_missed_high_roi_contexts
production_ready = false
selector_can_certificate = false
```

## Candidate Margin Buckets

```json
{
  "deep_candidate_score_gap": 6,
  "moderate_candidate_score_gap": 3,
  "near_candidate_threshold": 8
}
```

## Family Summary

```json
{
  "random-wave": {
    "candidate_margin_bucket_counts": {
      "deep_candidate_score_gap": 5,
      "near_candidate_threshold": 1
    },
    "contexts": [
      "5751b1799b606ad1",
      "9f80ae35ea87da5b",
      "a67f331bdb819d7d",
      "e6b17bbf825984ae"
    ],
    "missed_candidate_score_margin_mean": -0.1990807776649793,
    "missed_candidate_score_margin_min": -0.25070591270923615,
    "missed_high_roi_opportunities": 6,
    "missed_without_same_context_contrast_count": 3,
    "task_count_counts": {
      "30": 1,
      "50": 5
    }
  },
  "sector-wave": {
    "candidate_margin_bucket_counts": {
      "deep_candidate_score_gap": 1,
      "moderate_candidate_score_gap": 3,
      "near_candidate_threshold": 7
    },
    "contexts": [
      "3d1bd8618099b573",
      "45baa40751a0bf77",
      "79fde658840fe2b8",
      "9fadf4f7b39742a2",
      "ac15bc4e7e3d6fff",
      "b6d808ebac2a6dd8",
      "ce3508e12ad69da7"
    ],
    "missed_candidate_score_margin_mean": -0.055926450274207375,
    "missed_candidate_score_margin_min": -0.3923274278640747,
    "missed_high_roi_opportunities": 11,
    "missed_without_same_context_contrast_count": 3,
    "task_count_counts": {
      "20": 11
    }
  }
}
```

## Recommended Next Step

```json
{
  "candidate_margin_bucket_counts": {
    "deep_candidate_score_gap": 6,
    "moderate_candidate_score_gap": 3,
    "near_candidate_threshold": 8
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
      "context_hash": "b6d808ebac2a6dd8",
      "family": "sector-wave",
      "missed_high_roi_opportunities": 1,
      "task_counts": [
        20
      ]
    },
    {
      "context_hash": "9f80ae35ea87da5b",
      "family": "random-wave",
      "missed_high_roi_opportunities": 1,
      "task_counts": [
        30
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
    "random-wave": 6,
    "sector-wave": 11
  },
  "missed_without_same_context_contrast": 6,
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
