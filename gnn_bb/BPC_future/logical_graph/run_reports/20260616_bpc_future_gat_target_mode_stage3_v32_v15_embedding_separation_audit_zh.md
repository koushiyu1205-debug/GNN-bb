# GAT Batch Impact Embedding Separation Audit 报告

日期：2026-06-16

## 结论

本报告只做离线 embedding / kNN 结构审计，用来判断 missed high-ROI 是分数阈值边界问题，还是模型表示空间中与低 ROI / bad 样本混杂。
它不运行 BPC、pricing、RMP、worker 或 certificate。

```text
train_record_count = 222
validation_record_count = 110
candidate_threshold = 0.9019626379013062
knn_k = 5
high_roi_opportunities = 28
accepted_high_roi_opportunities = 12
missed_high_roi_opportunities = 16
accepted_low_roi_or_bad = 1
missed_nearest_negative_closer_count = 10
missed_knn_positive_fraction_mean = 0.1625
accepted_high_roi_knn_positive_fraction_mean = 0.5
recommended_primary = collect_context_local_positive_negative_pairs_or_add_embedding_contrast
diagnostic_only = true
runs_bpc_or_pricing = false
selector_can_certificate = false
```

## Family Summary

```json
{
  "greedy-anchor": {
    "accepted_high_roi_opportunities": 0,
    "accepted_low_roi_or_bad": 0,
    "high_roi_opportunities": 0,
    "missed_high_roi_opportunities": 0,
    "missed_nearest_negative_closer_count": 0,
    "records": 14
  },
  "random-wave": {
    "accepted_high_roi_opportunities": 1,
    "accepted_low_roi_or_bad": 0,
    "high_roi_opportunities": 6,
    "missed_high_roi_opportunities": 5,
    "missed_nearest_negative_closer_count": 5,
    "records": 44
  },
  "sector-wave": {
    "accepted_high_roi_opportunities": 11,
    "accepted_low_roi_or_bad": 1,
    "high_roi_opportunities": 22,
    "missed_high_roi_opportunities": 11,
    "missed_nearest_negative_closer_count": 5,
    "records": 52
  }
}
```

## Top Missed High-ROI

```json
[
  {
    "accepted": false,
    "accepted_batch_roi_label": 15.120423316955566,
    "batch_score": 0.6782926321029663,
    "candidate_count": 1,
    "candidate_threshold": 0.9019626379013062,
    "context_hash": "ac15bc4e7e3d6fff",
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "is_accepted_high_roi_opportunity": false,
    "is_accepted_low_roi_or_bad": false,
    "is_high_roi_opportunity": true,
    "is_missed_high_roi_opportunity": true,
    "knn_accepted_positive_fraction": 0.0,
    "knn_positive_fraction": 0.4,
    "max_candidate_score": 0.8292728066444397,
    "max_candidate_score_margin": -0.07268983125686646,
    "nearest_negative_candidate_score": 0.33119887113571167,
    "nearest_negative_closer": true,
    "nearest_negative_distance": 0.525543793182972,
    "nearest_negative_family": "greedy-anchor",
    "nearest_positive_candidate_score": 0.5028241276741028,
    "nearest_positive_distance": 0.5490588480116309,
    "nearest_positive_family": "sector-wave",
    "sample_path": "samples/sample_000304.pt",
    "task_count": 20
  },
  {
    "accepted": false,
    "accepted_batch_roi_label": 14.969822883605957,
    "batch_score": 0.6713162064552307,
    "candidate_count": 1,
    "candidate_threshold": 0.9019626379013062,
    "context_hash": "79fde658840fe2b8",
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "is_accepted_high_roi_opportunity": false,
    "is_accepted_low_roi_or_bad": false,
    "is_high_roi_opportunity": true,
    "is_missed_high_roi_opportunity": true,
    "knn_accepted_positive_fraction": 0.0,
    "knn_positive_fraction": 0.0,
    "max_candidate_score": 0.8296931982040405,
    "max_candidate_score_margin": -0.07226943969726562,
    "nearest_negative_candidate_score": 0.33119887113571167,
    "nearest_negative_closer": true,
    "nearest_negative_distance": 0.5421189330212474,
    "nearest_negative_family": "greedy-anchor",
    "nearest_positive_candidate_score": 0.5028241276741028,
    "nearest_positive_distance": 0.6946851520362866,
    "nearest_positive_family": "sector-wave",
    "sample_path": "samples/sample_000305.pt",
    "task_count": 20
  },
  {
    "accepted": false,
    "accepted_batch_roi_label": 13.568206787109375,
    "batch_score": 0.6660787463188171,
    "candidate_count": 1,
    "candidate_threshold": 0.9019626379013062,
    "context_hash": "79fde658840fe2b8",
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "is_accepted_high_roi_opportunity": false,
    "is_accepted_low_roi_or_bad": false,
    "is_high_roi_opportunity": true,
    "is_missed_high_roi_opportunity": true,
    "knn_accepted_positive_fraction": 0.0,
    "knn_positive_fraction": 0.2,
    "max_candidate_score": 0.5879952311515808,
    "max_candidate_score_margin": -0.31396740674972534,
    "nearest_negative_candidate_score": 0.03371068090200424,
    "nearest_negative_closer": false,
    "nearest_negative_distance": 0.44060354037328175,
    "nearest_negative_family": "random-wave",
    "nearest_positive_candidate_score": 0.5028241276741028,
    "nearest_positive_distance": 0.31545242580096905,
    "nearest_positive_family": "sector-wave",
    "sample_path": "samples/sample_000317.pt",
    "task_count": 20
  },
  {
    "accepted": false,
    "accepted_batch_roi_label": 13.436327934265137,
    "batch_score": 0.6266599297523499,
    "candidate_count": 1,
    "candidate_threshold": 0.9019626379013062,
    "context_hash": "45baa40751a0bf77",
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "is_accepted_high_roi_opportunity": false,
    "is_accepted_low_roi_or_bad": false,
    "is_high_roi_opportunity": true,
    "is_missed_high_roi_opportunity": true,
    "knn_accepted_positive_fraction": 0.0,
    "knn_positive_fraction": 0.2,
    "max_candidate_score": 0.3269463777542114,
    "max_candidate_score_margin": -0.5750162601470947,
    "nearest_negative_candidate_score": 0.03371068090200424,
    "nearest_negative_closer": false,
    "nearest_negative_distance": 0.34971343936962357,
    "nearest_negative_family": "random-wave",
    "nearest_positive_candidate_score": 0.5028241276741028,
    "nearest_positive_distance": 0.27376487887970335,
    "nearest_positive_family": "sector-wave",
    "sample_path": "samples/sample_000319.pt",
    "task_count": 20
  },
  {
    "accepted": false,
    "accepted_batch_roi_label": 13.129931449890137,
    "batch_score": 0.6540209054946899,
    "candidate_count": 1,
    "candidate_threshold": 0.9019626379013062,
    "context_hash": "3d1bd8618099b573",
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "is_accepted_high_roi_opportunity": false,
    "is_accepted_low_roi_or_bad": false,
    "is_high_roi_opportunity": true,
    "is_missed_high_roi_opportunity": true,
    "knn_accepted_positive_fraction": 0.0,
    "knn_positive_fraction": 0.2,
    "max_candidate_score": 0.8057916760444641,
    "max_candidate_score_margin": -0.09617096185684204,
    "nearest_negative_candidate_score": 0.12801571190357208,
    "nearest_negative_closer": true,
    "nearest_negative_distance": 0.530924971020744,
    "nearest_negative_family": "sector-wave",
    "nearest_positive_candidate_score": 0.5028241276741028,
    "nearest_positive_distance": 0.587411098963119,
    "nearest_positive_family": "sector-wave",
    "sample_path": "samples/sample_000318.pt",
    "task_count": 20
  },
  {
    "accepted": false,
    "accepted_batch_roi_label": 11.614195823669434,
    "batch_score": 0.6127294301986694,
    "candidate_count": 1,
    "candidate_threshold": 0.9019626379013062,
    "context_hash": "9fadf4f7b39742a2",
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "is_accepted_high_roi_opportunity": false,
    "is_accepted_low_roi_or_bad": false,
    "is_high_roi_opportunity": true,
    "is_missed_high_roi_opportunity": true,
    "knn_accepted_positive_fraction": 0.2,
    "knn_positive_fraction": 0.6,
    "max_candidate_score": 0.7568244934082031,
    "max_candidate_score_margin": -0.14513814449310303,
    "nearest_negative_candidate_score": 0.4124501645565033,
    "nearest_negative_closer": false,
    "nearest_negative_distance": 0.5866237717566481,
    "nearest_negative_family": "random-wave",
    "nearest_positive_candidate_score": 0.3649211823940277,
    "nearest_positive_distance": 0.5105791817539319,
    "nearest_positive_family": "random-wave",
    "sample_path": "samples/sample_000299.pt",
    "task_count": 20
  },
  {
    "accepted": false,
    "accepted_batch_roi_label": 7.219682216644287,
    "batch_score": 0.6085962653160095,
    "candidate_count": 1,
    "candidate_threshold": 0.9019626379013062,
    "context_hash": "9fadf4f7b39742a2",
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "is_accepted_high_roi_opportunity": false,
    "is_accepted_low_roi_or_bad": false,
    "is_high_roi_opportunity": true,
    "is_missed_high_roi_opportunity": true,
    "knn_accepted_positive_fraction": 0.0,
    "knn_positive_fraction": 0.2,
    "max_candidate_score": 0.6217765212059021,
    "max_candidate_score_margin": -0.28018611669540405,
    "nearest_negative_candidate_score": 0.33119887113571167,
    "nearest_negative_closer": false,
    "nearest_negative_distance": 0.5033605175974947,
    "nearest_negative_family": "greedy-anchor",
    "nearest_positive_candidate_score": 0.5028241276741028,
    "nearest_positive_distance": 0.29972551590498736,
    "nearest_positive_family": "sector-wave",
    "sample_path": "samples/sample_000300.pt",
    "task_count": 20
  },
  {
    "accepted": false,
    "accepted_batch_roi_label": 4.385624885559082,
    "batch_score": 0.5069952011108398,
    "candidate_count": 1,
    "candidate_threshold": 0.9019626379013062,
    "context_hash": "5751b1799b606ad1",
    "family": "random-wave",
    "instance": "BPC_future/logical_graph/tasks_050/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks050_04_seed91307_logical_graph.json",
    "is_accepted_high_roi_opportunity": false,
    "is_accepted_low_roi_or_bad": false,
    "is_high_roi_opportunity": true,
    "is_missed_high_roi_opportunity": true,
    "knn_accepted_positive_fraction": 0.0,
    "knn_positive_fraction": 0.2,
    "max_candidate_score": 0.5407941937446594,
    "max_candidate_score_margin": -0.36116844415664673,
    "nearest_negative_candidate_score": 0.4124501645565033,
    "nearest_negative_closer": true,
    "nearest_negative_distance": 0.435810269759057,
    "nearest_negative_family": "random-wave",
    "nearest_positive_candidate_score": 0.3649211823940277,
    "nearest_positive_distance": 0.5201489667538008,
    "nearest_positive_family": "random-wave",
    "sample_path": "samples/sample_000320.pt",
    "task_count": 50
  },
  {
    "accepted": false,
    "accepted_batch_roi_label": 4.385624885559082,
    "batch_score": 0.5069952011108398,
    "candidate_count": 1,
    "candidate_threshold": 0.9019626379013062,
    "context_hash": "5751b1799b606ad1",
    "family": "random-wave",
    "instance": "BPC_future/logical_graph/tasks_050/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks050_04_seed91307_logical_graph.json",
    "is_accepted_high_roi_opportunity": false,
    "is_accepted_low_roi_or_bad": false,
    "is_high_roi_opportunity": true,
    "is_missed_high_roi_opportunity": true,
    "knn_accepted_positive_fraction": 0.0,
    "knn_positive_fraction": 0.2,
    "max_candidate_score": 0.5407941937446594,
    "max_candidate_score_margin": -0.36116844415664673,
    "nearest_negative_candidate_score": 0.4124501645565033,
    "nearest_negative_closer": true,
    "nearest_negative_distance": 0.435810261336788,
    "nearest_negative_family": "random-wave",
    "nearest_positive_candidate_score": 0.3649211823940277,
    "nearest_positive_distance": 0.5201489772815765,
    "nearest_positive_family": "random-wave",
    "sample_path": "samples/sample_000326.pt",
    "task_count": 50
  },
  {
    "accepted": false,
    "accepted_batch_roi_label": 3.3431410789489746,
    "batch_score": 0.507205605506897,
    "candidate_count": 1,
    "candidate_threshold": 0.9019626379013062,
    "context_hash": "9fadf4f7b39742a2",
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "is_accepted_high_roi_opportunity": false,
    "is_accepted_low_roi_or_bad": false,
    "is_high_roi_opportunity": true,
    "is_missed_high_roi_opportunity": true,
    "knn_accepted_positive_fraction": 0.0,
    "knn_positive_fraction": 0.2,
    "max_candidate_score": 0.3272972106933594,
    "max_candidate_score_margin": -0.5746654272079468,
    "nearest_negative_candidate_score": 0.03371068090200424,
    "nearest_negative_closer": false,
    "nearest_negative_distance": 0.46581446874480054,
    "nearest_negative_family": "random-wave",
    "nearest_positive_candidate_score": 0.5028241276741028,
    "nearest_positive_distance": 0.31449540806926185,
    "nearest_positive_family": "sector-wave",
    "sample_path": "samples/sample_000301.pt",
    "task_count": 20
  }
]
```
