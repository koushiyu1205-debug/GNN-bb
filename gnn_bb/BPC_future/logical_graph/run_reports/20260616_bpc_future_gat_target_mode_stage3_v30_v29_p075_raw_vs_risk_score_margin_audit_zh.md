# GAT Batch Impact Score Margin Audit 报告

日期：2026-06-16

## 结论

本报告复用 opportunity mining 的 validation records，审计 missed high-ROI batch
距离当前 candidate / batch threshold 还差多少，以及是否缺同 context 对照样本。
它只做离线诊断，不运行 BPC、pricing、RMP、worker 或 certificate。

```text
validation_record_count = 119
candidate_threshold = 0.2425465249523217
batch_threshold = 0.0
high_roi_opportunities = 30
accepted_high_roi_opportunities = 22
missed_high_roi_opportunities = 8
missed_candidate_score_margin_mean = -0.06281578960353397
missed_candidate_score_margin_min = -0.2420731901040063
missed_raw_candidate_score_margin_mean = 0.06487655251317898
missed_raw_candidate_score_margin_min = -0.23788717073124593
risk_adjusted_suppressed_miss_count = 7
missed_without_same_context_contrast_count = 2
recommended_primary = calibrate_delay_risk_penalty_or_two_stage_rescue_window
production_ready = false
selector_can_certificate = false
```

## Candidate Margin Buckets

```json
{
  "deep_candidate_score_gap": 1,
  "moderate_candidate_score_gap": 1,
  "near_candidate_threshold": 6
}
```

## Raw Candidate Margin Buckets

```json
{
  "deep_candidate_score_gap": 1,
  "near_candidate_threshold": 7
}
```

## Family Summary

```json
{
  "random-wave": {
    "candidate_margin_bucket_counts": {
      "moderate_candidate_score_gap": 1,
      "near_candidate_threshold": 4
    },
    "contexts": [
      "5751b1799b606ad1",
      "a67f331bdb819d7d",
      "e6b17bbf825984ae"
    ],
    "missed_candidate_score_margin_mean": -0.0380531518854578,
    "missed_candidate_score_margin_min": -0.0673587987747856,
    "missed_high_roi_opportunities": 5,
    "missed_raw_candidate_score_margin_mean": 0.10707136755141669,
    "missed_raw_candidate_score_margin_min": 0.05755615596923286,
    "missed_without_same_context_contrast_count": 2,
    "raw_candidate_margin_bucket_counts": {
      "near_candidate_threshold": 5
    },
    "risk_adjusted_suppressed_miss_count": 5,
    "task_count_counts": {
      "50": 5
    }
  },
  "sector-wave": {
    "candidate_margin_bucket_counts": {
      "deep_candidate_score_gap": 1,
      "near_candidate_threshold": 2
    },
    "contexts": [
      "45baa40751a0bf77",
      "ce3508e12ad69da7"
    ],
    "missed_candidate_score_margin_mean": -0.10408685246699426,
    "missed_candidate_score_margin_min": -0.2420731901040063,
    "missed_high_roi_opportunities": 3,
    "missed_raw_candidate_score_margin_mean": -0.005448139217217225,
    "missed_raw_candidate_score_margin_min": -0.23788717073124593,
    "missed_without_same_context_contrast_count": 0,
    "raw_candidate_margin_bucket_counts": {
      "deep_candidate_score_gap": 1,
      "near_candidate_threshold": 2
    },
    "risk_adjusted_suppressed_miss_count": 2,
    "task_count_counts": {
      "20": 3
    }
  }
}
```

## Recommended Next Step

```json
{
  "candidate_margin_bucket_counts": {
    "deep_candidate_score_gap": 1,
    "moderate_candidate_score_gap": 1,
    "near_candidate_threshold": 6
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
    "sector-wave": 3
  },
  "missed_without_same_context_contrast": 2,
  "primary": "calibrate_delay_risk_penalty_or_two_stage_rescue_window",
  "raw_candidate_margin_bucket_counts": {
    "deep_candidate_score_gap": 1,
    "near_candidate_threshold": 7
  },
  "risk_adjusted_suppressed_miss_count": 7
}
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
