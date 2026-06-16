# GAT Batch Impact Score Margin Audit 报告

日期：2026-06-16

## 结论

本报告复用 opportunity mining 的 validation records，审计 missed high-ROI batch
距离当前 candidate / batch threshold 还差多少，以及是否缺同 context 对照样本。
它只做离线诊断，不运行 BPC、pricing、RMP、worker 或 certificate。

```text
validation_record_count = 110
candidate_threshold = 0.9019626379013062
batch_threshold = 0.0
high_roi_opportunities = 28
accepted_high_roi_opportunities = 12
missed_high_roi_opportunities = 16
missed_candidate_score_margin_mean = -0.3829170756507665
missed_candidate_score_margin_min = -0.8569196499884129
missed_without_same_context_contrast_count = 7
recommended_primary = collect_same_context_positive_negative_pairs_for_missed_high_roi_contexts
production_ready = false
selector_can_certificate = false
```

## Candidate Margin Buckets

```json
{
  "deep_candidate_score_gap": 11,
  "moderate_candidate_score_gap": 5
}
```

## Family Summary

```json
{
  "random-wave": {
    "candidate_margin_bucket_counts": {
      "deep_candidate_score_gap": 5
    },
    "contexts": [
      "5751b1799b606ad1",
      "a67f331bdb819d7d",
      "e6b17bbf825984ae"
    ],
    "missed_candidate_score_margin_mean": -0.505402696877718,
    "missed_candidate_score_margin_min": -0.8569196499884129,
    "missed_high_roi_opportunities": 5,
    "missed_without_same_context_contrast_count": 2,
    "task_count_counts": {
      "50": 5
    }
  },
  "sector-wave": {
    "candidate_margin_bucket_counts": {
      "deep_candidate_score_gap": 6,
      "moderate_candidate_score_gap": 5
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
    "missed_candidate_score_margin_mean": -0.32724179327487946,
    "missed_candidate_score_margin_min": -0.7810833007097244,
    "missed_high_roi_opportunities": 11,
    "missed_without_same_context_contrast_count": 5,
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
    "deep_candidate_score_gap": 11,
    "moderate_candidate_score_gap": 5
  },
  "contexts_needing_contrast": [
    {
      "context_hash": "ac15bc4e7e3d6fff",
      "family": "sector-wave",
      "missed_high_roi_opportunities": 1,
      "task_counts": [
        20
      ]
    },
    {
      "context_hash": "9fadf4f7b39742a2",
      "family": "sector-wave",
      "missed_high_roi_opportunities": 3,
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
    "sector-wave": 11
  },
  "missed_without_same_context_contrast": 7,
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
