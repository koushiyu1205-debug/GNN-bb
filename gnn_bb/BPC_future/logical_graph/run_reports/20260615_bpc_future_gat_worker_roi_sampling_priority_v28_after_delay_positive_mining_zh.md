# GAT Worker ROI Sampling Priority Audit 报告

日期：2026-06-15

## 目的

根据已有 target-priority worker ROI 标签，找出下一批最值得采样的
family/region/ordinal cell。该流程只读现有 JSON/JSONL，不运行 BPC、
pricing、RMP、worker，也不产生证书或 official bound。

## 机器字段

```text
gat_worker_roi_sampling_priority = current
row_count = 134
candidate_count = 113
recommendation_count = 16
max_per_cell = 4
roi_class_counts = {'columns_only_roi': 9, 'negative_primal_roi': 27, 'negative_retry_roi': 22, 'no_observed_roi': 40, 'positive_primal_roi': 31, 'positive_retry_roi': 5}
production_ready = false
certificate_ready = false
```

## Positive-rich cells

```json
{
  "greedy-anchor|apollo15_20km": {
    "avg_positive_primal_improvement": 2.9124184000000013,
    "key": [
      "greedy-anchor",
      "apollo15_20km"
    ],
    "positive_count": 10,
    "positive_rate": 0.4,
    "roi_class_counts": {
      "negative_primal_roi": 5,
      "negative_retry_roi": 5,
      "no_observed_roi": 5,
      "positive_primal_roi": 8,
      "positive_retry_roi": 2
    },
    "row_count": 25,
    "training_negative_count": 15,
    "unsupported_count": 0
  },
  "greedy-anchor|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 33.391141249999976,
    "key": [
      "greedy-anchor",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 8,
    "positive_rate": 0.34782608695652173,
    "roi_class_counts": {
      "columns_only_roi": 1,
      "negative_primal_roi": 2,
      "negative_retry_roi": 9,
      "no_observed_roi": 3,
      "positive_primal_roi": 8
    },
    "row_count": 23,
    "training_negative_count": 14,
    "unsupported_count": 1
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
    "avg_positive_primal_improvement": 17.263620714285707,
    "key": [
      "sector-wave",
      "apollo15_20km"
    ],
    "positive_count": 7,
    "positive_rate": 0.2692307692307692,
    "roi_class_counts": {
      "columns_only_roi": 2,
      "negative_primal_roi": 5,
      "negative_retry_roi": 2,
      "no_observed_roi": 10,
      "positive_primal_roi": 6,
      "positive_retry_roi": 1
    },
    "row_count": 26,
    "training_negative_count": 17,
    "unsupported_count": 2
  },
  "sector-wave|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 4.046049444444419,
    "key": [
      "sector-wave",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 9,
    "positive_rate": 0.36,
    "roi_class_counts": {
      "columns_only_roi": 1,
      "negative_primal_roi": 5,
      "negative_retry_roi": 1,
      "no_observed_roi": 9,
      "positive_primal_roi": 7,
      "positive_retry_roi": 2
    },
    "row_count": 25,
    "training_negative_count": 15,
    "unsupported_count": 1
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
    "active_hash_before": "6405fc3f1de6a512",
    "best_true_reduced_cost": -15.337043333,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 4,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 49,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.05,
    "cell_training_negative_count": 17,
    "certificate_effect": false,
    "context_hash": "7e68afc79aa7bf1c",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9017964601516724,
    "decision_reason": "high_priority",
    "decision_record_index": 10,
    "existing_roi_target": false,
    "expected_context_hash": "7e68afc79aa7bf1c",
    "forbidden_signature_hash": "0f0a419aa700271f",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 5,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_7e68afc79aa7bf1c_19_5_6_7_13_11",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|5",
    "ordinal_positive_rate": 1.0,
    "pool_signature_hash": "2552d35e4f5bc395",
    "pool_task_set_hash": "4906a46f34a934ea",
    "positive_gap": 1,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 1.0,
    "sample_path": "samples/sample_000010.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 7.787651,
    "source_candidate_file": "BPC_future/results/gat_same_run_random_wave_ord5_high_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord5_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json.jsonl",
    "source_row_index": 10,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->19:low_time:0",
      "19->5:low_risk:2",
      "5->6:low_risk:2",
      "6->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.375,
    "target_priority_sequence": [
      19,
      5,
      6
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      19,
      5,
      6,
      7,
      13,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->19:low_time:0",
          "19->5:low_risk:2",
          "5->6:low_risk:2",
          "6->0:low_time:0"
        ],
        "sequence": [
          19,
          5,
          6
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->7:low_risk:2",
          "7->13:low_time:0",
          "13->11:low_risk:2",
          "11->0:low_time:0"
        ],
        "sequence": [
          7,
          13,
          11
        ],
        "start_time": 329.828536
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      5,
      6,
      7,
      11,
      13,
      19
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "a785e3611b95c5a0",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "f4ef4c446bfd05a0",
    "best_true_reduced_cost": -9.110462,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 3,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 49,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.05,
    "cell_training_negative_count": 17,
    "certificate_effect": false,
    "context_hash": "0c7912c345131f8a",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9249536991119385,
    "decision_reason": "high_priority",
    "decision_record_index": 9,
    "existing_roi_target": false,
    "expected_context_hash": "0c7912c345131f8a",
    "forbidden_signature_hash": "2d8cd7980ca0d585",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 5,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_0c7912c345131f8a_19_5_7_13_11",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|5",
    "ordinal_positive_rate": 1.0,
    "pool_signature_hash": "dfa044acf58a8d10",
    "pool_task_set_hash": "813e0fe047dfb373",
    "positive_gap": 1,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 1.0,
    "sample_path": "samples/sample_000009.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 7.499479,
    "source_candidate_file": "BPC_future/results/gat_same_run_random_wave_ord5_high_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord5_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json.jsonl",
    "source_row_index": 9,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->19:low_risk:2",
      "19->5:low_risk:2",
      "5->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.428571429,
    "target_priority_sequence": [
      19,
      5
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      19,
      5,
      7,
      13,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->19:low_risk:2",
          "19->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          19,
          5
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->7:low_risk:2",
          "7->13:low_time:0",
          "13->11:low_risk:2",
          "11->0:low_time:0"
        ],
        "sequence": [
          7,
          13,
          11
        ],
        "start_time": 273.238078
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      5,
      7,
      11,
      13,
      19
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "c7d49aa88295ad51",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "db1b163885849bab",
    "best_true_reduced_cost": -68.344953,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 1,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 25,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 11,
    "certificate_effect": false,
    "context_hash": "d519291840dd7000",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 1.0,
    "decision_reason": "high_priority",
    "decision_record_index": 10,
    "existing_roi_target": false,
    "expected_context_hash": "d519291840dd7000",
    "forbidden_signature_hash": "8c559ff7a164a116",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 8,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_14_10",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "530406beed850f36",
    "pool_task_set_hash": "e8b7e3dc10f8202e",
    "positive_gap": 1,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.154849,
    "sample_path": "samples/sample_000010.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 7.474246,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "source_row_index": 10,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->10:low_time:0",
      "10->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      14,
      10
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      14,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->14:low_risk:2",
          "14->10:low_time:0",
          "10->0:low_time:0"
        ],
        "sequence": [
          14,
          10
        ],
        "start_time": 15.571461
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      10,
      14
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 2,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "7a8482acd5dc4633",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "00a3a80d5df57238",
    "best_true_reduced_cost": -8.1512385,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 6,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 25,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.05,
    "cell_training_negative_count": 17,
    "certificate_effect": false,
    "context_hash": "b311d02d7b40608e",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9267851114273071,
    "decision_reason": "high_priority",
    "decision_record_index": 12,
    "existing_roi_target": false,
    "expected_context_hash": "b311d02d7b40608e",
    "forbidden_signature_hash": "0bc81e546efd120e",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 5,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_b311d02d7b40608e_5_19_18_7_13_11",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|5",
    "ordinal_positive_rate": 1.0,
    "pool_signature_hash": "b29e112d2500e7bf",
    "pool_task_set_hash": "fc2bbd519971b812",
    "positive_gap": 1,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 1.0,
    "sample_path": "samples/sample_000012.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 7.453349,
    "source_candidate_file": "BPC_future/results/gat_same_run_random_wave_ord5_high_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord5_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json.jsonl",
    "source_row_index": 12,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->5:low_time:0",
      "5->19:low_time:0",
      "19->18:low_time:0",
      "18->0:low_energy:1"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.375,
    "target_priority_sequence": [
      5,
      19,
      18
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      5,
      19,
      18,
      7,
      13,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_time:0",
          "5->19:low_time:0",
          "19->18:low_time:0",
          "18->0:low_energy:1"
        ],
        "sequence": [
          5,
          19,
          18
        ],
        "start_time": 26.027931
      },
      {
        "arc_option_sequence": [
          "0->7:low_risk:2",
          "7->13:low_time:0",
          "13->11:low_risk:2",
          "11->0:low_time:0"
        ],
        "sequence": [
          7,
          13,
          11
        ],
        "start_time": 353.878284
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      5,
      7,
      11,
      13,
      18,
      19
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "91f342e1bf6c44a3",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "8fea27ca936f24d2",
    "best_true_reduced_cost": -37.8568215,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 6,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 11,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 11,
    "certificate_effect": false,
    "context_hash": "67c11b5ec80925ec",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9998925924301147,
    "decision_reason": "high_priority",
    "decision_record_index": 11,
    "existing_roi_target": false,
    "expected_context_hash": "67c11b5ec80925ec",
    "forbidden_signature_hash": "19812e842cb95df9",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 8,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_19_16",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "549b0ebff4d503f5",
    "pool_task_set_hash": "27845f832af78f68",
    "positive_gap": 1,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.154849,
    "sample_path": "samples/sample_000011.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 7.36698,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "source_row_index": 11,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->19:low_time:0",
      "19->16:low_risk:2",
      "16->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      19,
      16
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      19,
      16
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->19:low_time:0",
          "19->16:low_risk:2",
          "16->0:low_time:0"
        ],
        "sequence": [
          19,
          16
        ],
        "start_time": 0.0
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      16,
      19
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 2,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "8d0b48016c368950",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "20ecd0ba075a5cd4",
    "best_true_reduced_cost": -19.1028872,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 7,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 42,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 17.263621,
    "cell_positive_count": 7,
    "cell_positive_rate": 0.269231,
    "cell_training_negative_count": 17,
    "certificate_effect": false,
    "context_hash": "b6507dfb6db81d64",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.6914450526237488,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 25,
    "existing_roi_target": false,
    "expected_context_hash": "b6507dfb6db81d64",
    "forbidden_signature_hash": "a9fa6948e89224a2",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 4,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|apollo15_20km|4",
    "ordinal_positive_rate": 1.0,
    "pool_signature_hash": "256ff5712f06f6ee",
    "pool_task_set_hash": "5ab012b4a6716038",
    "positive_gap": 0,
    "positive_gap_weight": 10.0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 1.0,
    "sample_path": "samples/sample_000025.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 7.180644,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v25_parallel4_20260615/delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v25_parallel4_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json.jsonl",
    "source_row_index": 25,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->16:low_risk:2",
      "16->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      16
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      16,
      11,
      12,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->16:low_risk:2",
          "16->0:low_risk:2"
        ],
        "sequence": [
          16
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->11:low_time:0",
          "11->12:low_time:0",
          "12->10:low_time:0",
          "10->0:low_risk:2"
        ],
        "sequence": [
          11,
          12,
          10
        ],
        "start_time": 318.585773
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      10,
      11,
      12,
      16
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "3fd56392816e9c8d",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "a8681375b98abe9b",
    "best_true_reduced_cost": -83.5112654,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 2,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 25,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.05,
    "cell_training_negative_count": 17,
    "certificate_effect": false,
    "context_hash": "ddcb5387bef3bf63",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9999945163726807,
    "decision_reason": "high_priority",
    "decision_record_index": 16,
    "existing_roi_target": false,
    "expected_context_hash": "ddcb5387bef3bf63",
    "forbidden_signature_hash": "30f21d8900d08486",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 3,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_2_17_16",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "9434aed561bacc3e",
    "pool_task_set_hash": "e4123a7322872a6a",
    "positive_gap": 1,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.0938,
    "sample_path": "samples/sample_000016.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 7.118997,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "source_row_index": 16,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->17:low_risk:1",
      "17->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.25,
    "target_priority_sequence": [
      2,
      17,
      16
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      2,
      17,
      16
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
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      2,
      16,
      17
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 3,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "755b99c23a4b6c8e",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "f94d076935f27fde",
    "best_true_reduced_cost": -9.919815,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 16,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 30,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 33.391141,
    "cell_positive_count": 8,
    "cell_positive_rate": 0.347826,
    "cell_training_negative_count": 14,
    "certificate_effect": false,
    "context_hash": "bec78bfc0baddb44",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9190742373466492,
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
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_6_11_2",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|4",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "06bc54750fc9ac71",
    "pool_task_set_hash": "80b62e66b4be6dc3",
    "positive_gap": 0,
    "positive_gap_weight": 7.342583,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.667823,
    "sample_path": "samples/sample_000031.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 6.797657,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json.jsonl",
    "source_row_index": 31,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->6:low_risk:2",
      "6->11:low_risk:2",
      "11->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.4,
    "target_priority_sequence": [
      6,
      11
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      6,
      11,
      2
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->6:low_risk:2",
          "6->11:low_risk:2",
          "11->0:low_time:0"
        ],
        "sequence": [
          6,
          11
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->2:low_time:0",
          "2->0:low_risk:2"
        ],
        "sequence": [
          2
        ],
        "start_time": 308.516937
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      2,
      6,
      11
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 3,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "dc29f619e1498bc2",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "931e9eb7f04e3978",
    "best_true_reduced_cost": -14.195524,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 10,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 33.391141,
    "cell_positive_count": 8,
    "cell_positive_rate": 0.347826,
    "cell_training_negative_count": 14,
    "certificate_effect": false,
    "context_hash": "67925c0d2fd4abde",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9544597864151001,
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
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_11_15_6",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|6",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "c1ce4f0c1c5fedec",
    "pool_task_set_hash": "eb7766f8ef463e03",
    "positive_gap": 0,
    "positive_gap_weight": 7.342583,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.667823,
    "sample_path": "samples/sample_000052.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 6.546828,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json.jsonl",
    "source_row_index": 52,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->11:low_risk:2",
      "11->15:low_risk:2",
      "15->0:low_risk:2"
    ],
    "target_impact_bucket": "new_task_set",
    "target_max_active_jaccard": 0.666666667,
    "target_priority_sequence": [
      11,
      15
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      11,
      15,
      6
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->11:low_risk:2",
          "11->15:low_risk:2",
          "15->0:low_risk:2"
        ],
        "sequence": [
          11,
          15
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->6:low_risk:2",
          "6->0:low_risk:2"
        ],
        "sequence": [
          6
        ],
        "start_time": 307.577781
      }
    ],
    "target_support_changing_proxy": false,
    "target_task_set": [
      6,
      11,
      15
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 3,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "8be9fa1cee656941",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "7f58f54e29eaf87d",
    "best_true_reduced_cost": -24.6631105,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 11,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 11,
    "certificate_effect": false,
    "context_hash": "ff6827bb236f4831",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.8228176832199097,
    "decision_reason": "below_threshold_delay_queue",
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
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_ff6827bb236f4831_3_13_12",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|10",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "e7b1f9704726e1eb",
    "pool_task_set_hash": "4a05d50ee276e2c8",
    "positive_gap": 1,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.154849,
    "sample_path": "samples/sample_000033.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 6.530219,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json.jsonl",
    "source_row_index": 33,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->13:low_risk:2",
      "13->12:low_risk:2",
      "12->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.25,
    "target_priority_sequence": [
      3,
      13,
      12
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      3,
      13,
      12
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->13:low_risk:2",
          "13->12:low_risk:2",
          "12->0:low_time:0"
        ],
        "sequence": [
          3,
          13,
          12
        ],
        "start_time": 0.0
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      3,
      12,
      13
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 3,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "d311567607dbafaa",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "8fa22105b7d71a70",
    "best_true_reduced_cost": -1.466535,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 60,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 27,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 33.391141,
    "cell_positive_count": 8,
    "cell_positive_rate": 0.347826,
    "cell_training_negative_count": 14,
    "certificate_effect": false,
    "context_hash": "0f0c5d214add6400",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9196915626525879,
    "decision_reason": "high_priority",
    "decision_record_index": 65,
    "existing_roi_target": false,
    "expected_context_hash": "0f0c5d214add6400",
    "forbidden_signature_hash": "64cde73bd524b1e5",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 8,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_20_18_2_1_19",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|8",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "5a140851789d466b",
    "pool_task_set_hash": "a3df5269fcbc2319",
    "positive_gap": 0,
    "positive_gap_weight": 7.342583,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.667823,
    "sample_path": "samples/sample_000065.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 6.375611,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave04/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json.jsonl",
    "source_row_index": 65,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      20
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      20,
      18,
      2,
      1,
      19
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->0:low_time:0"
        ],
        "sequence": [
          20
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->18:low_time:0",
          "18->2:low_time:0",
          "2->1:low_risk:2",
          "1->0:low_time:0"
        ],
        "sequence": [
          18,
          2,
          1
        ],
        "start_time": 65.070996
      },
      {
        "arc_option_sequence": [
          "0->19:low_risk:2",
          "19->0:low_time:0"
        ],
        "sequence": [
          19
        ],
        "start_time": 405.748559
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      2,
      18,
      19,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "5c6902f41c1a1901",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "b7829a86dcf262e8",
    "best_true_reduced_cost": -2.185878,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 12,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 26,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 33.391141,
    "cell_positive_count": 8,
    "cell_positive_rate": 0.347826,
    "cell_training_negative_count": 14,
    "certificate_effect": false,
    "context_hash": "d1096c4029531f56",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.8320755362510681,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 24,
    "existing_roi_target": false,
    "expected_context_hash": "d1096c4029531f56",
    "forbidden_signature_hash": "2aae101758b54a89",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 3,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "b6f90c6314ebd7e2",
    "pool_task_set_hash": "25774e8e0baa5782",
    "positive_gap": 0,
    "positive_gap_weight": 7.342583,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.667823,
    "sample_path": "samples/sample_000024.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 6.323962,
    "source_candidate_file": "BPC_future/results/gat_same_run_gap_focused_ord3_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_gap_focused_ord3_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json.jsonl",
    "source_row_index": 24,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->7:low_risk:2",
      "7->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.571428571,
    "target_priority_sequence": [
      7
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      7,
      1,
      8,
      11,
      19
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->7:low_risk:2",
          "7->0:low_risk:2"
        ],
        "sequence": [
          7
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->1:low_time:0",
          "1->8:low_time:0",
          "8->11:low_energy:1",
          "11->0:low_energy:1"
        ],
        "sequence": [
          1,
          8,
          11
        ],
        "start_time": 83.548501
      },
      {
        "arc_option_sequence": [
          "0->19:low_risk:2",
          "19->0:low_time:0"
        ],
        "sequence": [
          19
        ],
        "start_time": 415.228421
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      7,
      8,
      11,
      19
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "49982d413c04cf67",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "778c07cb4ef85021",
    "best_true_reduced_cost": -13.6231534,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 22,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.912418,
    "cell_positive_count": 10,
    "cell_positive_rate": 0.4,
    "cell_training_negative_count": 15,
    "certificate_effect": false,
    "context_hash": "f9d0b6b18a0a28d3",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9435222744941711,
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
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|5",
    "ordinal_positive_rate": 1.0,
    "pool_signature_hash": "d26348c8579fe2e4",
    "pool_task_set_hash": "49305ade6883086a",
    "positive_gap": 0,
    "positive_gap_weight": 10.0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 1.0,
    "sample_path": "samples/sample_000041.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 6.115922,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json.jsonl",
    "source_row_index": 41,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->18:low_energy:1",
      "18->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.6,
    "target_priority_sequence": [
      20,
      18
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      20,
      18,
      3,
      4
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->18:low_energy:1",
          "18->0:low_risk:2"
        ],
        "sequence": [
          20,
          18
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->4:low_risk:2",
          "4->0:low_time:0"
        ],
        "sequence": [
          3,
          4
        ],
        "start_time": 228.617125
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      3,
      4,
      18,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "1f5fbbb40123e95b",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "ede095c6ba8539c1",
    "best_true_reduced_cost": -59.766543,
    "branch_hash": "da39a3ee5e6b4b0d",
    "capture_cg_iter": 3,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 49,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.046049,
    "cell_positive_count": 9,
    "cell_positive_rate": 0.36,
    "cell_training_negative_count": 15,
    "certificate_effect": false,
    "context_hash": "9fadf4f7b39742a2",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.965408444404602,
    "decision_reason": "high_priority",
    "decision_record_index": 23,
    "existing_roi_target": false,
    "expected_context_hash": "9fadf4f7b39742a2",
    "forbidden_signature_hash": "cc076c836d200e54",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 3,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.75,
    "pool_signature_hash": "b0fe906b0c1ab18d",
    "pool_task_set_hash": "ee50cf9eb4b638b3",
    "positive_gap": 0,
    "positive_gap_weight": 8.0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.75,
    "sample_path": "samples/sample_000023.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.950013,
    "source_candidate_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json.jsonl",
    "source_row_index": 23,
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->8:low_time:0",
      "8->11:low_risk:2",
      "11->0:low_time:0"
    ],
    "target_priority_sequence": [
      13,
      8,
      11
    ],
    "target_sequence": [
      13,
      8,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->8:low_time:0",
          "8->11:low_risk:2",
          "11->0:low_time:0"
        ],
        "sequence": [
          13,
          8,
          11
        ],
        "start_time": 0.264013
      }
    ],
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "4dba67189cd38261",
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
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.154849,
    "sample_path": "samples/sample_000013.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.507723,
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
    "active_hash_before": "809582ff03414493",
    "best_true_reduced_cost": -67.696691,
    "branch_hash": "da39a3ee5e6b4b0d",
    "capture_cg_iter": 4,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 49,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 17.263621,
    "cell_positive_count": 7,
    "cell_positive_rate": 0.269231,
    "cell_training_negative_count": 17,
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
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_0df8d5cea7864e69_1_18",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|apollo15_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "6d15c64a02b6077f",
    "pool_task_set_hash": "3f59bd5d0556eaf7",
    "positive_gap": 0,
    "positive_gap_weight": 4.762179,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.345272,
    "sample_path": "samples/sample_000011.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.482953,
    "source_candidate_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json.jsonl",
    "source_row_index": 11,
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->18:low_risk:2",
      "18->0:low_time:0"
    ],
    "target_priority_sequence": [
      1,
      18
    ],
    "target_sequence": [
      1,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->1:low_time:0",
          "1->18:low_risk:2",
          "18->0:low_time:0"
        ],
        "sequence": [
          1,
          18
        ],
        "start_time": 0.0
      }
    ],
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "1ce0a0d2ebfba758",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  }
]
```

## 结论

- 正 ROI 高度集中，不能按 rc 或 HIGH 数量盲目采样；
- 每个 family/region cell 都需要正负样本平衡；
- 候选推荐只用于下一批 audit-only A/B，不允许默认启用 worker；
- GAT/kNN/OOD 仍不能证书，不能产生 official lower bound。
