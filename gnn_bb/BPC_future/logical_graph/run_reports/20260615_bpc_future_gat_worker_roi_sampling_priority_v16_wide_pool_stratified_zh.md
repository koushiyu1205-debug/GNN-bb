# GAT Worker ROI Sampling Priority Audit 报告

日期：2026-06-15

## 目的

根据已有 target-priority worker ROI 标签，找出下一批最值得采样的
family/region/ordinal cell。该流程只读现有 JSON/JSONL，不运行 BPC、
pricing、RMP、worker，也不产生证书或 official bound。

## 机器字段

```text
gat_worker_roi_sampling_priority = current
row_count = 62
candidate_count = 64
recommendation_count = 12
max_per_cell = 2
roi_class_counts = {'columns_only_roi': 6, 'negative_primal_roi': 13, 'negative_retry_roi': 3, 'no_observed_roi': 22, 'positive_primal_roi': 18}
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
    "positive_rate": 0.07692307692307693,
    "roi_class_counts": {
      "columns_only_roi": 3,
      "negative_primal_roi": 4,
      "no_observed_roi": 5,
      "positive_primal_roi": 1
    },
    "row_count": 13,
    "training_negative_count": 9,
    "unsupported_count": 3
  },
  "random-wave|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 4.6900210000000015,
    "key": [
      "random-wave",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 1,
    "positive_rate": 0.05555555555555555,
    "roi_class_counts": {
      "columns_only_roi": 2,
      "negative_primal_roi": 5,
      "negative_retry_roi": 3,
      "no_observed_roi": 7,
      "positive_primal_roi": 1
    },
    "row_count": 18,
    "training_negative_count": 15,
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
    "positive_rate": 0.07692307692307693,
    "row_count": 13
  },
  {
    "avg_positive_primal_improvement": 4.6900210000000015,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "negative_gap": 0,
    "positive_gap": 1,
    "positive_rate": 0.05555555555555555,
    "row_count": 18
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
    "active_hash_before": "859cbba15c6585c7",
    "best_true_reduced_cost": -2.881583375,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 15,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 11,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.076923,
    "cell_training_negative_count": 9,
    "certificate_effect": false,
    "context_hash": "4575716b3939cb89",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9324136972427368,
    "decision_reason": "high_priority",
    "decision_record_index": 36,
    "existing_roi_target": false,
    "expected_context_hash": "4575716b3939cb89",
    "forbidden_signature_hash": "e844295219f3e8fe",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 10,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|10",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "2355b3378249fd7c",
    "pool_task_set_hash": "a232e0dde7906105",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000036.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 13.081508,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json.jsonl",
    "source_row_index": 36,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->19:low_energy:1",
      "19->9:low_risk:2",
      "9->12:low_risk:2",
      "12->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.333333333,
    "target_priority_sequence": [
      3,
      19,
      9,
      12
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      3,
      19,
      9,
      12
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->19:low_energy:1",
          "19->9:low_risk:2",
          "9->12:low_risk:2",
          "12->0:low_time:0"
        ],
        "sequence": [
          3,
          19,
          9,
          12
        ],
        "start_time": 0.0
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      3,
      9,
      12,
      19
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "2723e3b6445060e7",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "7f58f54e29eaf87d",
    "best_true_reduced_cost": -1.770543,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 11,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.076923,
    "cell_training_negative_count": 9,
    "certificate_effect": false,
    "context_hash": "ff6827bb236f4831",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9781931638717651,
    "decision_reason": "high_priority",
    "decision_record_index": 33,
    "existing_roi_target": false,
    "expected_context_hash": "ff6827bb236f4831",
    "forbidden_signature_hash": "3b2a853c944fe40e",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 10,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_18_8_7_9_12",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|10",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "e7b1f9704726e1eb",
    "pool_task_set_hash": "4a05d50ee276e2c8",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000033.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 13.071736,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json.jsonl",
    "source_row_index": 33,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->18:low_time:0",
      "18->8:low_risk:2",
      "8->7:low_time:0",
      "7->9:low_energy:1",
      "9->12:low_risk:2",
      "12->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      3,
      18,
      8,
      7,
      9,
      12
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      3,
      18,
      8,
      7,
      9,
      12
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->18:low_time:0",
          "18->8:low_risk:2",
          "8->7:low_time:0",
          "7->9:low_energy:1",
          "9->12:low_risk:2",
          "12->0:low_time:0"
        ],
        "sequence": [
          3,
          18,
          8,
          7,
          9,
          12
        ],
        "start_time": 0.0
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      3,
      7,
      8,
      9,
      12,
      18
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "d311567607dbafaa",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "e00e5f54b69345ba",
    "best_true_reduced_cost": -9.696532,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 6,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 23,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.055556,
    "cell_training_negative_count": 15,
    "certificate_effect": false,
    "context_hash": "9eb0dc7839bf91ec",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.7473084926605225,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 20,
    "existing_roi_target": false,
    "expected_context_hash": "9eb0dc7839bf91ec",
    "forbidden_signature_hash": "eefa5f433de1f487",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 3,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_9eb0dc7839bf91ec_2_17_16_13_18",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "8c1c94d7b1c2c4b2",
    "pool_task_set_hash": "3b02449ad82d2dc3",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000020.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 12.867804,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "source_row_index": 20,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->17:low_risk:1",
      "17->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.6,
    "target_priority_sequence": [
      2,
      17,
      16
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      2,
      17,
      16,
      13,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_time:0",
          "2->17:low_risk:1",
          "17->16:low_time:0",
          "16->0:low_time:0"
        ],
        "sequence": [
          2,
          17,
          16
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->18:low_time:0",
          "18->0:low_time:0"
        ],
        "sequence": [
          13,
          18
        ],
        "start_time": 336.687825
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      2,
      13,
      16,
      17,
      18
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "4fa661248332899c",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "86d9789a5b8352f0",
    "best_true_reduced_cost": -3.6951123,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 5,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.055556,
    "cell_training_negative_count": 15,
    "certificate_effect": false,
    "context_hash": "ec59d1f203f1630c",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9999500513076782,
    "decision_reason": "high_priority",
    "decision_record_index": 38,
    "existing_roi_target": false,
    "expected_context_hash": "ec59d1f203f1630c",
    "forbidden_signature_hash": "a9b02ad000676eeb",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 10,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_20_17_15_1_13",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|10",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "b22e9d42681f1d67",
    "pool_task_set_hash": "c400b3d02d0fc424",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000038.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 12.820374,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json.jsonl",
    "source_row_index": 38,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->17:low_risk:2",
      "17->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.333333333,
    "target_priority_sequence": [
      20,
      17
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      20,
      17,
      15,
      1,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_risk:2",
          "20->17:low_risk:2",
          "17->0:low_risk:2"
        ],
        "sequence": [
          20,
          17
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->15:low_risk:2",
          "15->1:low_energy:1",
          "1->13:low_time:0",
          "13->0:low_time:0"
        ],
        "sequence": [
          15,
          1,
          13
        ],
        "start_time": 195.108447
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      13,
      15,
      17,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "e408b632cdf39f5e",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "931e9eb7f04e3978",
    "best_true_reduced_cost": -9.569628,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 10,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 42.437713,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.857143,
    "cell_training_negative_count": 1,
    "certificate_effect": false,
    "context_hash": "67925c0d2fd4abde",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9807486534118652,
    "decision_reason": "high_priority",
    "decision_record_index": 52,
    "existing_roi_target": false,
    "expected_context_hash": "67925c0d2fd4abde",
    "forbidden_signature_hash": "0497e0ba36dd09db",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 6,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7",
    "negative_gap": 1,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|6",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "c1ce4f0c1c5fedec",
    "pool_task_set_hash": "eb7766f8ef463e03",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000052.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 11.27443,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json.jsonl",
    "source_row_index": 52,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->17:low_time:0",
      "17->16:low_risk:2",
      "16->1:low_time:0",
      "1->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.6,
    "target_priority_sequence": [
      20,
      17,
      16,
      1
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      20,
      17,
      16,
      1,
      7
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->17:low_time:0",
          "17->16:low_risk:2",
          "16->1:low_time:0",
          "1->0:low_risk:2"
        ],
        "sequence": [
          20,
          17,
          16,
          1
        ],
        "start_time": 25.406293
      },
      {
        "arc_option_sequence": [
          "0->7:low_time:0",
          "7->0:low_time:0"
        ],
        "sequence": [
          7
        ],
        "start_time": 370.348334
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      7,
      16,
      17,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "8be9fa1cee656941",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "2ea75ed4e70d366e",
    "best_true_reduced_cost": -5.714076,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 15,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 8,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 42.437713,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.857143,
    "cell_training_negative_count": 1,
    "certificate_effect": false,
    "context_hash": "f4e732e2cfdeea6e",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9274771213531494,
    "decision_reason": "high_priority",
    "decision_record_index": 62,
    "existing_roi_target": false,
    "expected_context_hash": "f4e732e2cfdeea6e",
    "forbidden_signature_hash": "2bd421a6b14906d2",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 7,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17",
    "negative_gap": 1,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|7",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "18669646faec5846",
    "pool_task_set_hash": "732bd8493c75ee14",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000062.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 11.028381,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave04/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json.jsonl",
    "source_row_index": 62,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->12:low_time:0",
      "12->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.4,
    "target_priority_sequence": [
      20,
      12
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      20,
      12,
      18,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->12:low_time:0",
          "12->0:low_risk:2"
        ],
        "sequence": [
          20,
          12
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->18:low_time:0",
          "18->17:low_risk:2",
          "17->0:low_time:0"
        ],
        "sequence": [
          18,
          17
        ],
        "start_time": 282.783247
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      12,
      17,
      18,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "755dfe2226982436",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "5260be3d13fa9cda",
    "best_true_reduced_cost": -28.945943667,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 41,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 5.19657,
    "cell_positive_count": 4,
    "cell_positive_rate": 0.5,
    "cell_training_negative_count": 4,
    "certificate_effect": false,
    "context_hash": "b36178f6655c5f75",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9752851128578186,
    "decision_reason": "high_priority",
    "decision_record_index": 26,
    "existing_roi_target": false,
    "expected_context_hash": "b36178f6655c5f75",
    "forbidden_signature_hash": "b7258704c52ca4cf",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 4,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|4",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "6dae80d2a19d1b2c",
    "pool_task_set_hash": "b8a49f5ce498f751",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000026.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.442239,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "source_row_index": 26,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->12:low_risk:1",
      "12->13:low_risk:2",
      "13->8:low_risk:2",
      "8->15:low_time:0",
      "15->3:low_risk:2",
      "3->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.428571429,
    "target_priority_sequence": [
      2,
      12,
      13,
      8,
      15,
      3
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      2,
      12,
      13,
      8,
      15,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_time:0",
          "2->12:low_risk:1",
          "12->13:low_risk:2",
          "13->8:low_risk:2",
          "8->15:low_time:0",
          "15->3:low_risk:2",
          "3->0:low_time:0"
        ],
        "sequence": [
          2,
          12,
          13,
          8,
          15,
          3
        ],
        "start_time": 53.762891
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      2,
      3,
      8,
      12,
      13,
      15
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "8c208ac829a68b55",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "809582ff03414493",
    "best_true_reduced_cost": -39.677578,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 4,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 49,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 0.705949,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 4,
    "certificate_effect": false,
    "context_hash": "0df8d5cea7864e69",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9488986134529114,
    "decision_reason": "high_priority",
    "decision_record_index": 11,
    "existing_roi_target": false,
    "expected_context_hash": "0df8d5cea7864e69",
    "forbidden_signature_hash": "76b64c9004112874",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 3,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_16_5_12_10",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|apollo15_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "6d15c64a02b6077f",
    "pool_task_set_hash": "3f59bd5d0556eaf7",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000011.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.128372,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json.jsonl",
    "source_row_index": 11,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->5:low_risk:2",
      "5->12:low_time:0",
      "12->10:low_risk:2",
      "10->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.2,
    "target_priority_sequence": [
      16,
      5,
      12,
      10
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      16,
      5,
      12,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->16:low_time:0",
          "16->5:low_risk:2",
          "5->12:low_time:0",
          "12->10:low_risk:2",
          "10->0:low_risk:2"
        ],
        "sequence": [
          16,
          5,
          12,
          10
        ],
        "start_time": 0.0
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      5,
      10,
      12,
      16
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "1ce0a0d2ebfba758",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "ef813699d84ea6a5",
    "best_true_reduced_cost": -7.71849675,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 22,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 0.705949,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 4,
    "certificate_effect": false,
    "context_hash": "c4004463c80918b5",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8971446752548218,
    "decision_reason": "high_priority",
    "decision_record_index": 4,
    "existing_roi_target": false,
    "expected_context_hash": "c4004463c80918b5",
    "forbidden_signature_hash": "dd40587035aa50c3",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 2,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|apollo15_20km|2",
    "ordinal_positive_rate": 0.75,
    "pool_signature_hash": "ef821b4e7d87f726",
    "pool_task_set_hash": "e9c9b682e80c660e",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000004.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.978664,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json.jsonl",
    "source_row_index": 4,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->9:low_energy:1",
      "9->3:low_time:0",
      "3->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.555555556,
    "target_priority_sequence": [
      9,
      3,
      20
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      9,
      3,
      20,
      11,
      4,
      8,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->9:low_energy:1",
          "9->3:low_time:0",
          "3->20:low_time:0",
          "20->0:low_time:0"
        ],
        "sequence": [
          9,
          3,
          20
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->11:low_risk:2",
          "11->4:low_risk:1",
          "4->8:low_time:0",
          "8->10:low_risk:2",
          "10->0:low_risk:2"
        ],
        "sequence": [
          11,
          4,
          8,
          10
        ],
        "start_time": 307.81881
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      3,
      4,
      8,
      9,
      10,
      11,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 7,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "95eafdfe84624eeb",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "f8111e12b798ea28",
    "best_true_reduced_cost": -32.653181714,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 6,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 49,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 2.221543,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 5,
    "certificate_effect": false,
    "context_hash": "dfd68d5873b84183",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9520010948181152,
    "decision_reason": "high_priority",
    "decision_record_index": 20,
    "existing_roi_target": false,
    "expected_context_hash": "dfd68d5873b84183",
    "forbidden_signature_hash": "6de0b545d5e610b8",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 2,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|2",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "8ec5c004bb6bc8ed",
    "pool_task_set_hash": "95cda2345f7c9f1e",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000020.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.931814,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json.jsonl",
    "source_row_index": 20,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      20,
      1
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      20,
      1,
      17,
      12
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->1:low_time:0",
          "1->0:low_time:0"
        ],
        "sequence": [
          20,
          1
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->17:low_time:0",
          "17->12:low_time:0",
          "12->0:low_time:0"
        ],
        "sequence": [
          17,
          12
        ],
        "start_time": 296.270931
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      12,
      17,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "958e2cb48777f988",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "2c2e416db249f720",
    "best_true_reduced_cost": -27.31408425,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 3,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 2.221543,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.375,
    "cell_training_negative_count": 5,
    "certificate_effect": false,
    "context_hash": "3d1bd8618099b573",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9371248483657837,
    "decision_reason": "high_priority",
    "decision_record_index": 18,
    "existing_roi_target": false,
    "expected_context_hash": "3d1bd8618099b573",
    "forbidden_signature_hash": "dd79a2cfb5c63e21",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 2,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|2",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "eddad0807740a5f3",
    "pool_task_set_hash": "e1b494c430dfa84e",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000018.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.649983,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json.jsonl",
    "source_row_index": 18,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.285714286,
    "target_priority_sequence": [
      8
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      8,
      11,
      10,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_risk:2",
          "8->0:low_risk:2"
        ],
        "sequence": [
          8
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->11:low_risk:2",
          "11->10:low_energy:1",
          "10->17:low_energy:1",
          "17->0:low_time:0"
        ],
        "sequence": [
          11,
          10,
          17
        ],
        "start_time": 180.341466
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      8,
      10,
      11,
      17
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "bc2e3db079d173a6",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "778c07cb4ef85021",
    "best_true_reduced_cost": -12.702497933,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 22,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 5.19657,
    "cell_positive_count": 4,
    "cell_positive_rate": 0.5,
    "cell_training_negative_count": 4,
    "certificate_effect": false,
    "context_hash": "f9d0b6b18a0a28d3",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9751601219177246,
    "decision_reason": "high_priority",
    "decision_record_index": 41,
    "existing_roi_target": false,
    "expected_context_hash": "f9d0b6b18a0a28d3",
    "forbidden_signature_hash": "419f8f65acc3551b",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 5,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|5",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "d26348c8579fe2e4",
    "pool_task_set_hash": "49305ade6883086a",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000041.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.629942,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json.jsonl",
    "source_row_index": 41,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->18:low_risk:2",
      "18->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.571428571,
    "target_priority_sequence": [
      18
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      18,
      3,
      13,
      6,
      19
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->18:low_risk:2",
          "18->0:low_risk:2"
        ],
        "sequence": [
          18
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->13:low_risk:2",
          "13->6:low_risk:2",
          "6->19:low_risk:2",
          "19->0:low_time:0"
        ],
        "sequence": [
          3,
          13,
          6,
          19
        ],
        "start_time": 206.946847
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      3,
      6,
      13,
      18,
      19
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "1f5fbbb40123e95b",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  }
]
```

## 结论

- 正 ROI 高度集中，不能按 rc 或 HIGH 数量盲目采样；
- 每个 family/region cell 都需要正负样本平衡；
- 候选推荐只用于下一批 audit-only A/B，不允许默认启用 worker；
- GAT/kNN/OOD 仍不能证书，不能产生 official lower bound。
