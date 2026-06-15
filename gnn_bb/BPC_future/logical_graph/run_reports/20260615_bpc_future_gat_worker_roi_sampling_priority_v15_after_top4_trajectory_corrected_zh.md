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
candidate_count = 46
recommendation_count = 12
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
    "active_hash_before": "3341a4ba541bfa32",
    "best_true_reduced_cost": -4.42725,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 9,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 24,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.076923,
    "cell_training_negative_count": 9,
    "certificate_effect": false,
    "context_hash": "62c86745ed2b3aaa",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.8121140599250793,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 13,
    "existing_roi_target": false,
    "expected_context_hash": "62c86745ed2b3aaa",
    "forbidden_signature_hash": "ddf56f63968049f0",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 8,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_2_1_5_3_12",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "50dc555c1757eeca",
    "pool_task_set_hash": "fdf2e77ba9b76816",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000013.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 13.038492,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "source_row_index": 13,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->2:low_risk:1",
      "2->1:low_time:0",
      "1->5:low_risk:2",
      "5->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      2,
      1,
      5
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      2,
      1,
      5,
      3,
      12
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_risk:1",
          "2->1:low_time:0",
          "1->5:low_risk:2",
          "5->0:low_time:0"
        ],
        "sequence": [
          2,
          1,
          5
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->12:low_risk:1",
          "12->0:low_risk:2"
        ],
        "sequence": [
          3,
          12
        ],
        "start_time": 228.218699
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      2,
      3,
      5,
      12
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "9bd9a1d18b7a5cf5",
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
    "active_hash_before": "c1dd396614b6fcc3",
    "best_true_reduced_cost": -1.220905,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 18,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 30,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.055556,
    "cell_training_negative_count": 15,
    "certificate_effect": false,
    "context_hash": "a77e5457bde80b8e",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9340042471885681,
    "decision_reason": "high_priority",
    "decision_record_index": 21,
    "existing_roi_target": false,
    "expected_context_hash": "a77e5457bde80b8e",
    "forbidden_signature_hash": "efeea73c001eabf6",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 8,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_8_4_14_9_3_13",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|8",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "b7bd078f29df934d",
    "pool_task_set_hash": "4c99b33b1ffe8829",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000021.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 12.630718,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json.jsonl",
    "source_row_index": 21,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.375,
    "target_priority_sequence": [
      8
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      8,
      4,
      14,
      9,
      3,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->0:low_time:0"
        ],
        "sequence": [
          8
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->4:low_energy:1",
          "4->14:low_time:0",
          "14->9:low_energy:1",
          "9->3:low_time:0",
          "3->13:low_time:0",
          "13->0:low_energy:1"
        ],
        "sequence": [
          4,
          14,
          9,
          3,
          13
        ],
        "start_time": 179.463458
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      3,
      4,
      8,
      9,
      13,
      14
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "d2ea374c6f1b01b2",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "3f3606e7b26a6cfc",
    "best_true_reduced_cost": -1.829877375,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 14,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 2,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.076923,
    "cell_training_negative_count": 9,
    "certificate_effect": false,
    "context_hash": "e978a55b1e53d13f",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9575245380401611,
    "decision_reason": "high_priority",
    "decision_record_index": 35,
    "existing_roi_target": false,
    "expected_context_hash": "e978a55b1e53d13f",
    "forbidden_signature_hash": "37abfa2909b26822",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 10,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_e978a55b1e53d13f_3_18_8_9",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|10",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "11c553d09c3a264d",
    "pool_task_set_hash": "3bd4921eb0bcec7d",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000035.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 12.554034,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json.jsonl",
    "source_row_index": 35,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->0:low_time:0"
    ],
    "target_impact_bucket": "new_task_set",
    "target_max_active_jaccard": 0.8,
    "target_priority_sequence": [
      3
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      3,
      18,
      8,
      9
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->0:low_time:0"
        ],
        "sequence": [
          3
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->18:low_time:0",
          "18->8:low_risk:2",
          "8->9:low_risk:2",
          "9->0:low_time:0"
        ],
        "sequence": [
          18,
          8,
          9
        ],
        "start_time": 161.492434
      }
    ],
    "target_support_changing_proxy": false,
    "target_task_set": [
      3,
      8,
      9,
      18
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "707af46274d67d3a",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "eb92a6a521734d12",
    "best_true_reduced_cost": -0.791942,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 7,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 3,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.076923,
    "cell_training_negative_count": 9,
    "certificate_effect": false,
    "context_hash": "409f65576794fa39",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.9502686858177185,
    "decision_reason": "knn_delay_fraction_delay_queue",
    "decision_record_index": 12,
    "existing_roi_target": false,
    "expected_context_hash": "409f65576794fa39",
    "forbidden_signature_hash": "2759f01a2dec4e9a",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 8,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_13",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "61505b62c0f9a4a1",
    "pool_task_set_hash": "bba64460221b3547",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000012.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 12.494881,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "source_row_index": 12,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->20:low_energy:1",
      "20->13:low_time:0",
      "13->0:low_time:0"
    ],
    "target_impact_bucket": "new_task_set",
    "target_max_active_jaccard": 0.666666667,
    "target_priority_sequence": [
      8,
      20,
      13
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      8,
      20,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->20:low_energy:1",
          "20->13:low_time:0",
          "13->0:low_time:0"
        ],
        "sequence": [
          8,
          20,
          13
        ],
        "start_time": 0.0
      }
    ],
    "target_support_changing_proxy": false,
    "target_task_set": [
      8,
      13,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 3,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "efc2fb20ceb858b3",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "03a8d149c5bdfc16",
    "best_true_reduced_cost": -1.632716,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 11,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 2,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.076923,
    "cell_training_negative_count": 9,
    "certificate_effect": false,
    "context_hash": "fbfd88d4ebde5459",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.40113312005996704,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 15,
    "existing_roi_target": false,
    "expected_context_hash": "fbfd88d4ebde5459",
    "forbidden_signature_hash": "69ba243ea44bf530",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 8,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_5_1_2_4_7_13",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "4846218d8d5926f5",
    "pool_task_set_hash": "b3efd3d85e0ad5f4",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000015.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 12.487784,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "source_row_index": 15,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->2:low_risk:2",
      "2->4:low_risk:2",
      "4->7:low_risk:2",
      "7->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      5,
      1,
      2,
      4,
      7,
      13
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      5,
      1,
      2,
      4,
      7,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->1:low_risk:2",
          "1->2:low_risk:2",
          "2->4:low_risk:2",
          "4->7:low_risk:2",
          "7->13:low_risk:2",
          "13->0:low_risk:2"
        ],
        "sequence": [
          5,
          1,
          2,
          4,
          7,
          13
        ],
        "start_time": 12.976513
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      2,
      4,
      5,
      7,
      13
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "c9745e8a1c010c30",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "03a8d149c5bdfc16",
    "best_true_reduced_cost": -0.134464,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 10,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 3,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.076923,
    "cell_training_negative_count": 9,
    "certificate_effect": false,
    "context_hash": "3100b787bf438dfe",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.4149324893951416,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 14,
    "existing_roi_target": false,
    "expected_context_hash": "3100b787bf438dfe",
    "forbidden_signature_hash": "59f58c79d1e50d49",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 8,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_13",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "7a249193fdd37789",
    "pool_task_set_hash": "e3f049a263f86c82",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000014.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 12.426671,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "source_row_index": 14,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->5:low_time:0",
      "5->1:low_risk:2",
      "1->2:low_time:0",
      "2->4:low_time:0",
      "4->11:low_risk:2",
      "11->13:low_risk:2",
      "13->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      5,
      1,
      2,
      4,
      11,
      13
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      5,
      1,
      2,
      4,
      11,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_time:0",
          "5->1:low_risk:2",
          "1->2:low_time:0",
          "2->4:low_time:0",
          "4->11:low_risk:2",
          "11->13:low_risk:2",
          "13->0:low_time:0"
        ],
        "sequence": [
          5,
          1,
          2,
          4,
          11,
          13
        ],
        "start_time": 13.918479
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      2,
      4,
      5,
      11,
      13
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "d4d21a0866a5f19c",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "b16d57084589277c",
    "best_true_reduced_cost": -5.674159,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 6,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 49,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.055556,
    "cell_training_negative_count": 15,
    "certificate_effect": false,
    "context_hash": "03605a430acbd104",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.48401594161987305,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 39,
    "existing_roi_target": false,
    "expected_context_hash": "03605a430acbd104",
    "forbidden_signature_hash": "9236c86814a8c318",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 10,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_03605a430acbd104_12_15_14_1_18",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|10",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "9dbecede2fcd086c",
    "pool_task_set_hash": "bdf5916f06e1b540",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000039.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 12.403393,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json.jsonl",
    "source_row_index": 39,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->15:low_risk:2",
      "15->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.285714286,
    "target_priority_sequence": [
      12,
      15
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      12,
      15,
      14,
      1,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_risk:2",
          "12->15:low_risk:2",
          "15->0:low_risk:2"
        ],
        "sequence": [
          12,
          15
        ],
        "start_time": 2.130446
      },
      {
        "arc_option_sequence": [
          "0->14:low_risk:2",
          "14->1:low_risk:2",
          "1->18:low_risk:2",
          "18->0:low_risk:2"
        ],
        "sequence": [
          14,
          1,
          18
        ],
        "start_time": 311.826653
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      12,
      14,
      15,
      18
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "44f49d1cb8c21b0c",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "b07cc85945edeae9",
    "best_true_reduced_cost": -0.224969,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 19,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 13,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.055556,
    "cell_training_negative_count": 15,
    "certificate_effect": false,
    "context_hash": "07f408aca742dc53",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.6791179180145264,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 22,
    "existing_roi_target": false,
    "expected_context_hash": "07f408aca742dc53",
    "forbidden_signature_hash": "d99b1bdac6bebedf",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 8,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_07f408aca742dc53_11_7_9_4_15_6",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|8",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "54caa5bc7311afc7",
    "pool_task_set_hash": "931f50b9534ef66d",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000022.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 12.326035,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json.jsonl",
    "source_row_index": 22,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->11:low_energy:1",
      "11->7:low_time:0",
      "7->9:low_risk:2",
      "9->4:low_risk:2",
      "4->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.571428571,
    "target_priority_sequence": [
      11,
      7,
      9,
      4
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      11,
      7,
      9,
      4,
      15,
      6
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->11:low_energy:1",
          "11->7:low_time:0",
          "7->9:low_risk:2",
          "9->4:low_risk:2",
          "4->0:low_risk:2"
        ],
        "sequence": [
          11,
          7,
          9,
          4
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->15:low_risk:2",
          "15->6:low_risk:2",
          "6->0:low_risk:2"
        ],
        "sequence": [
          15,
          6
        ],
        "start_time": 324.983033
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      4,
      6,
      7,
      9,
      11,
      15
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "96d40026f701b61e",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  }
]
```

## 结论

- 正 ROI 高度集中，不能按 rc 或 HIGH 数量盲目采样；
- 每个 family/region cell 都需要正负样本平衡；
- 候选推荐只用于下一批 audit-only A/B，不允许默认启用 worker；
- GAT/kNN/OOD 仍不能证书，不能产生 official lower bound。
