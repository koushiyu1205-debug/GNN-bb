# GAT Batch Impact Score Margin Audit 报告

日期：2026-06-16

## 结论

本报告复用 opportunity mining 的 validation records，审计 missed high-ROI batch
距离当前 candidate / batch threshold 还差多少，以及是否缺同 context 对照样本。
它只做离线诊断，不运行 BPC、pricing、RMP、worker 或 certificate。

```text
validation_record_count = 136
candidate_threshold = 0.19717147624284692
batch_threshold = 0.47844576835632324
high_roi_opportunities = 32
accepted_high_roi_opportunities = 3
missed_high_roi_opportunities = 29
missed_candidate_score_margin_mean = -0.05284464208491011
missed_candidate_score_margin_min = -0.17727450493776242
missed_raw_candidate_score_margin_mean = 0.11838921969720366
missed_raw_candidate_score_margin_min = -0.13319416022092767
risk_adjusted_suppressed_miss_count = 27
missed_without_same_context_contrast_count = 8
recommended_primary = calibrate_delay_risk_penalty_or_two_stage_rescue_window
production_ready = false
selector_can_certificate = false
```

## Candidate Margin Buckets

```json
{
  "moderate_candidate_score_gap": 13,
  "near_candidate_threshold": 16
}
```

## Raw Candidate Margin Buckets

```json
{
  "moderate_candidate_score_gap": 1,
  "near_candidate_threshold": 28
}
```

## Family Summary

```json
{
  "random-wave": {
    "candidate_margin_bucket_counts": {
      "moderate_candidate_score_gap": 5,
      "near_candidate_threshold": 1
    },
    "contexts": [
      "5751b1799b606ad1",
      "9f80ae35ea87da5b",
      "a67f331bdb819d7d",
      "e6b17bbf825984ae"
    ],
    "missed_candidate_score_margin_mean": -0.05935814502527078,
    "missed_candidate_score_margin_min": -0.07166106861776456,
    "missed_high_roi_opportunities": 6,
    "missed_raw_candidate_score_margin_mean": 0.10067252640137407,
    "missed_raw_candidate_score_margin_min": 0.06822732413023047,
    "missed_without_same_context_contrast_count": 3,
    "raw_candidate_margin_bucket_counts": {
      "near_candidate_threshold": 6
    },
    "risk_adjusted_suppressed_miss_count": 6,
    "task_count_counts": {
      "30": 1,
      "50": 5
    }
  },
  "sector-wave": {
    "candidate_margin_bucket_counts": {
      "moderate_candidate_score_gap": 8,
      "near_candidate_threshold": 15
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
    "missed_candidate_score_margin_mean": -0.05114546740481603,
    "missed_candidate_score_margin_min": -0.17727450493776242,
    "missed_high_roi_opportunities": 23,
    "missed_raw_candidate_score_margin_mean": 0.1230109657743766,
    "missed_raw_candidate_score_margin_min": -0.13319416022092767,
    "missed_without_same_context_contrast_count": 5,
    "raw_candidate_margin_bucket_counts": {
      "moderate_candidate_score_gap": 1,
      "near_candidate_threshold": 22
    },
    "risk_adjusted_suppressed_miss_count": 21,
    "task_count_counts": {
      "20": 23
    }
  }
}
```

## Recommended Next Step

```json
{
  "candidate_margin_bucket_counts": {
    "moderate_candidate_score_gap": 13,
    "near_candidate_threshold": 16
  },
  "contexts_needing_contrast": [
    {
      "context_hash": "9fadf4f7b39742a2",
      "family": "sector-wave",
      "missed_high_roi_opportunities": 5,
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
    "sector-wave": 23
  },
  "missed_without_same_context_contrast": 8,
  "primary": "calibrate_delay_risk_penalty_or_two_stage_rescue_window",
  "raw_candidate_margin_bucket_counts": {
    "moderate_candidate_score_gap": 1,
    "near_candidate_threshold": 28
  },
  "risk_adjusted_suppressed_miss_count": 27
}
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
