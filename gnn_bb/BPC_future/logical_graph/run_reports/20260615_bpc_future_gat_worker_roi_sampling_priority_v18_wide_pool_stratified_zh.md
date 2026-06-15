# GAT Worker ROI Sampling Priority Audit 报告

日期：2026-06-15

## 目的

根据已有 target-priority worker ROI 标签，找出下一批最值得采样的
family/region/ordinal cell。该流程只读现有 JSON/JSONL，不运行 BPC、
pricing、RMP、worker，也不产生证书或 official bound。

## 机器字段

```text
gat_worker_roi_sampling_priority = current
row_count = 80
candidate_count = 51
recommendation_count = 12
max_per_cell = 2
roi_class_counts = {'columns_only_roi': 6, 'negative_primal_roi': 15, 'negative_retry_roi': 6, 'no_observed_roi': 34, 'positive_primal_roi': 19}
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
    "positive_rate": 0.6666666666666666,
    "roi_class_counts": {
      "negative_primal_roi": 1,
      "negative_retry_roi": 1,
      "no_observed_roi": 1,
      "positive_primal_roi": 6
    },
    "row_count": 9,
    "training_negative_count": 3,
    "unsupported_count": 0
  },
  "random-wave|apollo15_20km": {
    "avg_positive_primal_improvement": 7.742461000000048,
    "key": [
      "random-wave",
      "apollo15_20km"
    ],
    "positive_count": 1,
    "positive_rate": 0.06666666666666667,
    "roi_class_counts": {
      "columns_only_roi": 3,
      "negative_primal_roi": 5,
      "negative_retry_roi": 1,
      "no_observed_roi": 5,
      "positive_primal_roi": 1
    },
    "row_count": 15,
    "training_negative_count": 11,
    "unsupported_count": 3
  },
  "random-wave|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 4.6900210000000015,
    "key": [
      "random-wave",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 1,
    "positive_rate": 0.05,
    "roi_class_counts": {
      "columns_only_roi": 2,
      "negative_primal_roi": 5,
      "negative_retry_roi": 4,
      "no_observed_roi": 8,
      "positive_primal_roi": 1
    },
    "row_count": 20,
    "training_negative_count": 17,
    "unsupported_count": 2
  },
  "sector-wave|apollo15_20km": {
    "avg_positive_primal_improvement": 0.7703772499999957,
    "key": [
      "sector-wave",
      "apollo15_20km"
    ],
    "positive_count": 4,
    "positive_rate": 0.3076923076923077,
    "roi_class_counts": {
      "columns_only_roi": 1,
      "no_observed_roi": 8,
      "positive_primal_roi": 4
    },
    "row_count": 13,
    "training_negative_count": 8,
    "unsupported_count": 1
  },
  "sector-wave|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 2.221542999999997,
    "key": [
      "sector-wave",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 3,
    "positive_rate": 0.2,
    "roi_class_counts": {
      "negative_primal_roi": 3,
      "no_observed_roi": 9,
      "positive_primal_roi": 3
    },
    "row_count": 15,
    "training_negative_count": 12,
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
    "positive_rate": 0.06666666666666667,
    "row_count": 15
  },
  {
    "avg_positive_primal_improvement": 4.6900210000000015,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "negative_gap": 0,
    "positive_gap": 1,
    "positive_rate": 0.05,
    "row_count": 20
  }
]
```

## Recommendations

```json
[
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
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 11,
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
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000013.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 13.007723,
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
    "cell_positive_rate": 0.05,
    "cell_training_negative_count": 17,
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
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000021.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 12.614052,
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
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 11,
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
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000035.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 12.523265,
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
    "cell_positive_rate": 0.05,
    "cell_training_negative_count": 17,
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
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000039.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 12.386726,
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
    "active_hash_before": "f94d076935f27fde",
    "best_true_reduced_cost": -0.585679,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 16,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 30,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 42.437713,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.666667,
    "cell_training_negative_count": 3,
    "certificate_effect": false,
    "context_hash": "bec78bfc0baddb44",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9785213470458984,
    "decision_reason": "high_priority",
    "decision_record_index": 31,
    "existing_roi_target": false,
    "expected_context_hash": "bec78bfc0baddb44",
    "forbidden_signature_hash": "e89be873ab67ab24",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 4,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_15_3_8_16_2",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|4",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "06bc54750fc9ac71",
    "pool_task_set_hash": "80b62e66b4be6dc3",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000031.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 8.251577,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json.jsonl",
    "source_row_index": 31,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->15:low_risk:2",
      "15->3:low_risk:1",
      "3->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      15,
      3
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      15,
      3,
      8,
      16,
      2
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->15:low_risk:2",
          "15->3:low_risk:1",
          "3->0:low_risk:2"
        ],
        "sequence": [
          15,
          3
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->16:low_time:0",
          "16->2:low_risk:2",
          "2->0:low_time:0"
        ],
        "sequence": [
          8,
          16,
          2
        ],
        "start_time": 185.831264
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      2,
      3,
      8,
      15,
      16
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "dc29f619e1498bc2",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "40f42b78b78e3668",
    "best_true_reduced_cost": -0.303165,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 17,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 21,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 42.437713,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.666667,
    "cell_training_negative_count": 3,
    "certificate_effect": false,
    "context_hash": "77bc967e4038b08b",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9821843504905701,
    "decision_reason": "high_priority",
    "decision_record_index": 50,
    "existing_roi_target": false,
    "expected_context_hash": "77bc967e4038b08b",
    "forbidden_signature_hash": "1420da74d3d03f9f",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 5,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|5",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "336001920de5c08d",
    "pool_task_set_hash": "5c3e9193d63d59ad",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000050.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 8.241114,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json.jsonl",
    "source_row_index": 50,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->6:low_risk:2",
      "6->20:low_risk:1",
      "20->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      4,
      6,
      20
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      4,
      6,
      20,
      18,
      2,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->6:low_risk:2",
          "6->20:low_risk:1",
          "20->0:low_risk:2"
        ],
        "sequence": [
          4,
          6,
          20
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->18:low_risk:2",
          "18->2:low_time:0",
          "2->10:low_risk:2",
          "10->0:low_risk:2"
        ],
        "sequence": [
          18,
          2,
          10
        ],
        "start_time": 337.557281
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      2,
      4,
      6,
      10,
      18,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "702d11c8080b0386",
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
    "cell_avg_positive_primal_improvement": 0.770377,
    "cell_positive_count": 4,
    "cell_positive_rate": 0.307692,
    "cell_training_negative_count": 8,
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
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000011.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.932892,
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
    "cell_avg_positive_primal_improvement": 0.770377,
    "cell_positive_count": 4,
    "cell_positive_rate": 0.307692,
    "cell_training_negative_count": 8,
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
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000004.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.783184,
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
    "cell_positive_rate": 0.2,
    "cell_training_negative_count": 12,
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
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000020.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.406814,
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
    "cell_positive_rate": 0.2,
    "cell_training_negative_count": 12,
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
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000018.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.124983,
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
  }
]
```

## 结论

- 正 ROI 高度集中，不能按 rc 或 HIGH 数量盲目采样；
- 每个 family/region cell 都需要正负样本平衡；
- 候选推荐只用于下一批 audit-only A/B，不允许默认启用 worker；
- GAT/kNN/OOD 仍不能证书，不能产生 official lower bound。
