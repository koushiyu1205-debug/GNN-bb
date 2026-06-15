# GAT Worker ROI Sampling Priority Audit 报告

日期：2026-06-15

## 目的

根据已有 target-priority worker ROI 标签，找出下一批最值得采样的
family/region/ordinal cell。该流程只读现有 JSON/JSONL，不运行 BPC、
pricing、RMP、worker，也不产生证书或 official bound。

## 机器字段

```text
gat_worker_roi_sampling_priority = current
row_count = 58
candidate_count = 60
recommendation_count = 16
roi_class_counts = {'columns_only_roi': 6, 'negative_primal_roi': 12, 'no_observed_roi': 22, 'positive_primal_roi': 18}
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
    "positive_rate": 0.08333333333333333,
    "roi_class_counts": {
      "columns_only_roi": 3,
      "negative_primal_roi": 3,
      "no_observed_roi": 5,
      "positive_primal_roi": 1
    },
    "row_count": 12,
    "training_negative_count": 8,
    "unsupported_count": 3
  },
  "random-wave|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 4.6900210000000015,
    "key": [
      "random-wave",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 1,
    "positive_rate": 0.06666666666666667,
    "roi_class_counts": {
      "columns_only_roi": 2,
      "negative_primal_roi": 5,
      "no_observed_roi": 7,
      "positive_primal_roi": 1
    },
    "row_count": 15,
    "training_negative_count": 12,
    "unsupported_count": 2
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
    "positive_rate": 0.08333333333333333,
    "row_count": 12
  },
  {
    "avg_positive_primal_improvement": 4.6900210000000015,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "negative_gap": 0,
    "positive_gap": 1,
    "positive_rate": 0.06666666666666667,
    "row_count": 15
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
    "best_true_reduced_cost": -47.282952,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 42.437713,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.857143,
    "cell_training_negative_count": 1,
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.5381238460540771,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 1,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks005_01_seed146007_8fe84b4354ce24e7_4_2_5_1",
    "negative_gap": 1,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|1",
    "ordinal_positive_rate": 1.0,
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "score": 14.353324,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "target_sequence": [
      4,
      2,
      5,
      1
    ]
  },
  {
    "best_true_reduced_cost": -29.773378,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 12,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 1.0,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 10,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_20_17_10_13",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|10",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "score": 14.157671,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "target_sequence": [
      20,
      17,
      10,
      13
    ]
  },
  {
    "best_true_reduced_cost": -21.7627212,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 12,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.999619722366333,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 3,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "score": 13.756758,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "target_sequence": [
      17,
      11,
      14,
      9
    ]
  },
  {
    "best_true_reduced_cost": -14.569046451,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 42.437713,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.857143,
    "cell_training_negative_count": 1,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9862507581710815,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_01_seed51000_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 1,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks010_01_seed51000_69d263f35a0a779f_2_7_1_4",
    "negative_gap": 1,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|1",
    "ordinal_positive_rate": 1.0,
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "score": 13.529903,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "target_sequence": [
      2,
      7,
      1,
      4
    ]
  },
  {
    "best_true_reduced_cost": -8.99552175,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.083333,
    "cell_training_negative_count": 8,
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.9657554626464844,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 10,
    "instance_region": "apollo15_20km",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_1b5a36a64a700b58_2_4_7_12",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|10",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "score": 13.439778,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "target_sequence": [
      2,
      4,
      7,
      12
    ]
  },
  {
    "best_true_reduced_cost": -24.5139606,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 42.437713,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.857143,
    "cell_training_negative_count": 1,
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.2752927541732788,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 1,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks005_01_seed146007_5628d4c655ec93e5_4_3_2_5",
    "negative_gap": 1,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|1",
    "ordinal_positive_rate": 1.0,
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "score": 13.316191,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "target_sequence": [
      4,
      3,
      2,
      5
    ]
  },
  {
    "best_true_reduced_cost": -12.4144668,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 12,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9925243258476257,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 3,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "score": 13.28225,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "target_sequence": [
      8,
      16,
      11,
      15,
      18
    ]
  },
  {
    "best_true_reduced_cost": -2.881583375,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.083333,
    "cell_training_negative_count": 8,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9324136972427368,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 10,
    "instance_region": "apollo15_20km",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|10",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "score": 13.100739,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "target_sequence": [
      3,
      19,
      9,
      12
    ]
  },
  {
    "best_true_reduced_cost": -1.770543,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.083333,
    "cell_training_negative_count": 8,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9781931638717651,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 10,
    "instance_region": "apollo15_20km",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|10",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "score": 13.090966,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "target_sequence": [
      3,
      18,
      8,
      7,
      9,
      12
    ]
  },
  {
    "best_true_reduced_cost": -4.42725,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.083333,
    "cell_training_negative_count": 8,
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.8121140599250793,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 8,
    "instance_region": "apollo15_20km",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_2_1_5_3_12",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "score": 13.057723,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "target_sequence": [
      2,
      1,
      5,
      3,
      12
    ]
  },
  {
    "best_true_reduced_cost": -9.696532,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 12,
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.7473084926605225,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 3,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "score": 12.901137,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "target_sequence": [
      2,
      17,
      16,
      13,
      18
    ]
  },
  {
    "best_true_reduced_cost": -7.057221,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 42.437713,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.857143,
    "cell_training_negative_count": 1,
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.6894165873527527,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_01_seed51000_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 1,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks010_01_seed51000_d692a8eb196de3d6_2_6_7_4_1",
    "negative_gap": 1,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|1",
    "ordinal_positive_rate": 1.0,
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "score": 12.857477,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "target_sequence": [
      2,
      6,
      7,
      4,
      1
    ]
  },
  {
    "best_true_reduced_cost": -3.6951123,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 12,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9999500513076782,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 10,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|10",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "score": 12.853708,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "target_sequence": [
      20,
      17,
      15,
      1,
      13
    ]
  },
  {
    "best_true_reduced_cost": -1.220905,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 12,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9340042471885681,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 8,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_8_4_14_9_3_13",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|8",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "score": 12.664052,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "target_sequence": [
      8,
      4,
      14,
      9,
      3,
      13
    ]
  },
  {
    "best_true_reduced_cost": -1.829877375,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.083333,
    "cell_training_negative_count": 8,
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9575245380401611,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 10,
    "instance_region": "apollo15_20km",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_e978a55b1e53d13f_3_18_8_9",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|10",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "score": 12.573265,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "target_sequence": [
      3,
      18,
      8,
      9
    ]
  },
  {
    "best_true_reduced_cost": -0.791942,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.083333,
    "cell_training_negative_count": 8,
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.9502686858177185,
    "existing_roi_target": false,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 8,
    "instance_region": "apollo15_20km",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_13",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "ordinal_positive_rate": 0.0,
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "score": 12.514112,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "target_sequence": [
      8,
      20,
      13
    ]
  }
]
```

## 结论

- 正 ROI 高度集中，不能按 rc 或 HIGH 数量盲目采样；
- 每个 family/region cell 都需要正负样本平衡；
- 候选推荐只用于下一批 audit-only A/B，不允许默认启用 worker；
- GAT/kNN/OOD 仍不能证书，不能产生 official lower bound。
