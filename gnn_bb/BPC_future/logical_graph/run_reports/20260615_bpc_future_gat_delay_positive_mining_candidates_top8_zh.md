# GAT DELAY_QUEUE 正样本挖掘候选 top8 报告

日期：2026-06-15

```json
{
  "all_delay_queue": true,
  "all_new_support_changing": true,
  "all_task20": true,
  "candidate_count": 8,
  "candidate_family_region_counts": {
    "greedy-anchor|apollo15_20km": 4,
    "greedy-anchor|tranquillitatis_balmer_like_20km": 4
  },
  "certificate_ready": false,
  "decision_counts": {
    "DELAY_QUEUE": 8
  },
  "impact_bucket_counts": {
    "new_support_changing": 8
  },
  "production_ready": false,
  "schema_version": "gat_delay_positive_mining_top8_v1",
  "source_files": [
    "BPC_future/results/gat_delay_positive_mining_candidates_v25_20260615/candidates.json",
    "BPC_future/results/gat_delay_positive_mining_candidates_v26_20260615/candidates.json"
  ],
  "training_label_requires_worker_ab": true
}
```

这些候选不能直接作为训练标签，必须先经过 target worker A/B。
