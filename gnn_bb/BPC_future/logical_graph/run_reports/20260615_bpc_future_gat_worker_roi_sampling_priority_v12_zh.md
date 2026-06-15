# GAT Worker ROI Sampling Priority Audit 报告

日期：2026-06-15

## 目的

根据已有 target-priority worker ROI 标签，找出下一批最值得采样的
family/region/ordinal cell。该流程只读现有 JSON/JSONL，不运行 BPC、
pricing、RMP、worker，也不产生证书或 official bound。

## 机器字段

```text
gat_worker_roi_sampling_priority = current
row_count = 54
candidate_count = 16
recommendation_count = 16
roi_class_counts = {'columns_only_roi': 4, 'negative_primal_roi': 12, 'no_observed_roi': 20, 'positive_primal_roi': 18}
production_ready = false
certificate_ready = false
```

## Positive-rich cells

```json
{
  "greedy-anchor|apollo15_20km": {
    "avg_positive_primal_improvement": 5.19656950000001,
    "key": [
      "greedy-anchor",
      "apollo15_20km"
    ],
    "positive_count": 4,
    "positive_rate": 0.5,
    "roi_class_counts": {
      "negative_primal_roi": 1,
      "no_observed_roi": 3,
      "positive_primal_roi": 4
    },
    "row_count": 8,
    "training_negative_count": 4,
    "unsupported_count": 0
  },
  "greedy-anchor|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 42.43771266666664,
    "key": [
      "greedy-anchor",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 6,
    "positive_rate": 0.8571428571428571,
    "roi_class_counts": {
      "no_observed_roi": 1,
      "positive_primal_roi": 6
    },
    "row_count": 7,
    "training_negative_count": 1,
    "unsupported_count": 0
  },
  "random-wave|apollo15_20km": {
    "avg_positive_primal_improvement": 7.742461000000048,
    "key": [
      "random-wave",
      "apollo15_20km"
    ],
    "positive_count": 1,
    "positive_rate": 0.1,
    "roi_class_counts": {
      "columns_only_roi": 2,
      "negative_primal_roi": 3,
      "no_observed_roi": 4,
      "positive_primal_roi": 1
    },
    "row_count": 10,
    "training_negative_count": 7,
    "unsupported_count": 2
  },
  "random-wave|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 4.6900210000000015,
    "key": [
      "random-wave",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 1,
    "positive_rate": 0.07692307692307693,
    "roi_class_counts": {
      "columns_only_roi": 1,
      "negative_primal_roi": 5,
      "no_observed_roi": 6,
      "positive_primal_roi": 1
    },
    "row_count": 13,
    "training_negative_count": 11,
    "unsupported_count": 1
  },
  "sector-wave|apollo15_20km": {
    "avg_positive_primal_improvement": 0.705948666666662,
    "key": [
      "sector-wave",
      "apollo15_20km"
    ],
    "positive_count": 3,
    "positive_rate": 0.375,
    "roi_class_counts": {
      "columns_only_roi": 1,
      "no_observed_roi": 4,
      "positive_primal_roi": 3
    },
    "row_count": 8,
    "training_negative_count": 4,
    "unsupported_count": 1
  },
  "sector-wave|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 2.221542999999997,
    "key": [
      "sector-wave",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 3,
    "positive_rate": 0.375,
    "roi_class_counts": {
      "negative_primal_roi": 3,
      "no_observed_roi": 2,
      "positive_primal_roi": 3
    },
    "row_count": 8,
    "training_negative_count": 5,
    "unsupported_count": 0
  }
}
```

## Sample gaps

```json
[
  {
    "avg_positive_primal_improvement": 7.742461000000048,
    "cell": "random-wave|apollo15_20km",
    "negative_gap": 0,
    "positive_gap": 1,
    "positive_rate": 0.1,
    "row_count": 10
  },
  {
    "avg_positive_primal_improvement": 4.6900210000000015,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "negative_gap": 0,
    "positive_gap": 1,
    "positive_rate": 0.07692307692307693,
    "row_count": 13
  },
  {
    "avg_positive_primal_improvement": 42.43771266666664,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "negative_gap": 1,
    "positive_gap": 0,
    "positive_rate": 0.8571428571428571,
    "row_count": 7
  }
]
```

## Recommendations

```json
[
  {
    "best_true_reduced_cost": -39.677578,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 0.705949,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 4,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9488986134529114,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 3,
    "instance_region": "apollo15_20km",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|apollo15_20km|3",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 5.128372,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      16,
      5,
      12,
      10
    ]
  },
  {
    "best_true_reduced_cost": -7.71849675,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 0.705949,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 4,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8971446752548218,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 2,
    "instance_region": "apollo15_20km",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|apollo15_20km|2",
    "ordinal_positive_rate": 0.75,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 4.978664,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      9,
      3,
      20,
      11,
      4,
      8,
      10
    ]
  },
  {
    "best_true_reduced_cost": -32.653181714,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 2.221543,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 5,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9520010948181152,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 2,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|2",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 4.931814,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      20,
      1,
      17,
      12
    ]
  },
  {
    "best_true_reduced_cost": -3.339913,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 0.705949,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 4,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8923575282096863,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 2,
    "instance_region": "apollo15_20km",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_7_11_4_2_8",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|apollo15_20km|2",
    "ordinal_positive_rate": 0.75,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 4.754948,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      3,
      9,
      7,
      11,
      4,
      2,
      8
    ]
  },
  {
    "best_true_reduced_cost": -18.394183,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 2.221543,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 5,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9526166915893555,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 6,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_6_14_3_4_18",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|6",
    "ordinal_positive_rate": 0.25,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 4.71948,
    "source_candidate_file": "BPC_future/results/gat_same_run_base_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      6,
      14,
      3,
      4,
      18
    ]
  },
  {
    "best_true_reduced_cost": -27.31408425,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 2.221543,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 5,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9371248483657837,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 2,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|2",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 4.649983,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      8,
      11,
      10,
      17
    ]
  },
  {
    "best_true_reduced_cost": -26.5430824,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 2.221543,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 5,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9569950699806213,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 2,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|2",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 4.631303,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      4,
      19,
      10,
      17
    ]
  },
  {
    "best_true_reduced_cost": -25.905037196,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 2.221543,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 5,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9230185151100159,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 3,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 4.565425,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      8,
      13,
      3,
      9,
      15
    ]
  },
  {
    "best_true_reduced_cost": -12.74033275,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 2.221543,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 5,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9269914627075195,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 6,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|6",
    "ordinal_positive_rate": 0.25,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 4.411162,
    "source_candidate_file": "BPC_future/results/gat_same_run_base_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      6,
      5,
      4,
      16,
      18
    ]
  },
  {
    "best_true_reduced_cost": -21.659046,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 2.221543,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 5,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.965408444404602,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 3,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 4.395515,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      1,
      7,
      20,
      4,
      10
    ]
  },
  {
    "best_true_reduced_cost": -3.429108,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 2.221543,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 5,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8592458367347717,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 4,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_15_6_11_12_14",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|4",
    "ordinal_positive_rate": 0.5,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 4.377856,
    "source_candidate_file": "BPC_future/results/gat_same_run_base_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      15,
      6,
      11,
      12,
      14
    ]
  },
  {
    "best_true_reduced_cost": -1.006043722,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 2.221543,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 5,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9364012479782104,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 6,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_5_8_18_16_9",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|6",
    "ordinal_positive_rate": 0.25,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 3.833858,
    "source_candidate_file": "BPC_future/results/gat_same_run_base_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      5,
      8,
      18,
      16,
      9
    ]
  },
  {
    "best_true_reduced_cost": -11.8352155,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 2.221543,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 5,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8906409740447998,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 2,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|2",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 3.829556,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      20,
      5,
      6,
      3
    ]
  },
  {
    "best_true_reduced_cost": -13.4341552,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 0.705949,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 4,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9293051362037659,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 3,
    "instance_region": "apollo15_20km",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|apollo15_20km|3",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 3.796608,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      4,
      12,
      15,
      6,
      11
    ]
  },
  {
    "best_true_reduced_cost": -9.801078667,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 2.221543,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 5,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9283106327056885,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 3,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 3.765519,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      8,
      1,
      3,
      9,
      15
    ]
  },
  {
    "best_true_reduced_cost": -0.028786,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 0.705949,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 4,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8972326517105103,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 1,
    "instance_region": "apollo15_20km",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_15_12_9",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|apollo15_20km|1",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "score": 3.094267,
    "source_candidate_file": "BPC_future/results/gat_same_run_base_impact_unsampled_candidates_20260615/candidates.json",
    "target_sequence": [
      8,
      15,
      12,
      9
    ]
  }
]
```

## 结论

- 正 ROI 高度集中，不能按 rc 或 HIGH 数量盲目采样；
- 每个 family/region cell 都需要正负样本平衡；
- 候选推荐只用于下一批 audit-only A/B，不允许默认启用 worker；
- GAT/kNN/OOD 仍不能证书，不能产生 official lower bound。
