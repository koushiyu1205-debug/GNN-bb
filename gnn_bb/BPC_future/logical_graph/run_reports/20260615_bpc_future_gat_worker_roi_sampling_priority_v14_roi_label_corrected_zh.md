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
    "active_hash_before": "345400ced8d93403",
    "best_true_reduced_cost": -47.282952,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 2,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 3,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 42.437713,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.857143,
    "cell_training_negative_count": 1,
    "certificate_effect": false,
    "context_hash": "8fe84b4354ce24e7",
    "cut_hash": "7463733468d9ef71",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.5381238460540771,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 1,
    "existing_roi_target": false,
    "expected_context_hash": "8fe84b4354ce24e7",
    "forbidden_signature_hash": "e2d61d2516aa6231",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 1,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 5,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks005_01_seed146007_8fe84b4354ce24e7_4_2_5_1",
    "negative_gap": 1,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|1",
    "ordinal_positive_rate": 1.0,
    "pool_signature_hash": "55b4c2a61df10014",
    "pool_task_set_hash": "e6388ec5fe0d76cf",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000001.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 14.353324,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task005_capture_sentinel/logs/BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007_logical_graph.json.jsonl",
    "source_row_index": 1,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->2:low_time:0",
      "2->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      4,
      2
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      4,
      2,
      5,
      1
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->2:low_time:0",
          "2->0:low_time:0"
        ],
        "sequence": [
          4,
          2
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->5:low_energy:1",
          "5->0:low_energy:1"
        ],
        "sequence": [
          5
        ],
        "start_time": 312.834267
      },
      {
        "arc_option_sequence": [
          "0->1:low_time:0",
          "1->0:low_time:0"
        ],
        "sequence": [
          1
        ],
        "start_time": 464.361143
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      2,
      4,
      5
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "2f802532a46baf4d",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "7ecd36ca50af55f8",
    "best_true_reduced_cost": -29.773378,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 3,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 49,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 12,
    "certificate_effect": false,
    "context_hash": "da555dc83edc174c",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 1.0,
    "decision_reason": "high_priority",
    "decision_record_index": 37,
    "existing_roi_target": false,
    "expected_context_hash": "da555dc83edc174c",
    "forbidden_signature_hash": "f8cedff217e2a211",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 10,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_20_17_10_13",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|10",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "abbfed8882abbb97",
    "pool_task_set_hash": "fec52a4ed3d6375b",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000037.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 14.157671,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json.jsonl",
    "source_row_index": 37,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->17:low_time:0",
      "17->10:low_risk:2",
      "10->13:low_risk:2",
      "13->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.25,
    "target_priority_sequence": [
      20,
      17,
      10,
      13
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      20,
      17,
      10,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->17:low_time:0",
          "17->10:low_risk:2",
          "10->13:low_risk:2",
          "13->0:low_time:0"
        ],
        "sequence": [
          20,
          17,
          10,
          13
        ],
        "start_time": 89.841934
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      10,
      13,
      17,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "4197690e912b9c36",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "622200ad1fc583cc",
    "best_true_reduced_cost": -21.7627212,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 5,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 12,
    "certificate_effect": false,
    "context_hash": "e897b76f2888f822",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.999619722366333,
    "decision_reason": "high_priority",
    "decision_record_index": 19,
    "existing_roi_target": false,
    "expected_context_hash": "e897b76f2888f822",
    "forbidden_signature_hash": "7b7bc18b58faa1db",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 3,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_17_11_14_9",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "cbd4c17130829b87",
    "pool_task_set_hash": "71fc2cca8fb5ace4",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000019.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 13.756758,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "source_row_index": 19,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->17:low_time:0",
      "17->11:low_risk:2",
      "11->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.6,
    "target_priority_sequence": [
      17,
      11
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      17,
      11,
      14,
      9
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->17:low_time:0",
          "17->11:low_risk:2",
          "11->0:low_risk:2"
        ],
        "sequence": [
          17,
          11
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->14:low_time:0",
          "14->9:low_risk:2",
          "9->0:low_risk:2"
        ],
        "sequence": [
          14,
          9
        ],
        "start_time": 292.997503
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      9,
      11,
      14,
      17
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "ed98088cdfa83a03",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "7b09462dc8d62db9",
    "best_true_reduced_cost": -14.569046451,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 1,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 16,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 42.437713,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.857143,
    "cell_training_negative_count": 1,
    "certificate_effect": false,
    "context_hash": "69d263f35a0a779f",
    "cut_hash": "62d0003f8e0d92c0",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9862507581710815,
    "decision_reason": "high_priority",
    "decision_record_index": 5,
    "existing_roi_target": false,
    "expected_context_hash": "69d263f35a0a779f",
    "forbidden_signature_hash": "825fb5fc285bc52b",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_01_seed51000_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 1,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 10,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks010_01_seed51000_69d263f35a0a779f_2_7_1_4",
    "negative_gap": 1,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|1",
    "ordinal_positive_rate": 1.0,
    "pool_signature_hash": "597a573ce2962aeb",
    "pool_task_set_hash": "e6e4997032767d84",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000005.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 13.529903,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task010_capture_sentinel/logs/BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_01_seed51000_logical_graph.json.jsonl",
    "source_row_index": 5,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->7:low_time:0",
      "7->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.6,
    "target_priority_sequence": [
      2,
      7
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      2,
      7,
      1,
      4
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_risk:2",
          "2->7:low_time:0",
          "7->0:low_risk:2"
        ],
        "sequence": [
          2,
          7
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->1:low_risk:2",
          "1->4:low_risk:2",
          "4->0:low_risk:2"
        ],
        "sequence": [
          1,
          4
        ],
        "start_time": 335.88851
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      2,
      4,
      7
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "a5d7600536f2e3d8",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "1f84cac1741f2492",
    "best_true_reduced_cost": -8.99552175,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 12,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 10,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 7.742461,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.083333,
    "cell_training_negative_count": 8,
    "certificate_effect": false,
    "context_hash": "1b5a36a64a700b58",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.9657554626464844,
    "decision_reason": "knn_delay_fraction_delay_queue",
    "decision_record_index": 34,
    "existing_roi_target": false,
    "expected_context_hash": "1b5a36a64a700b58",
    "forbidden_signature_hash": "024eaacaca8d9192",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 10,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_1b5a36a64a700b58_2_4_7_12",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|10",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "f90c495d5f8e2e4a",
    "pool_task_set_hash": "2ca48158265611a0",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000034.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 13.439778,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json.jsonl",
    "source_row_index": 34,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->4:low_risk:2",
      "4->7:low_risk:2",
      "7->12:low_risk:2",
      "12->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.333333333,
    "target_priority_sequence": [
      2,
      4,
      7,
      12
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      2,
      4,
      7,
      12
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_risk:2",
          "2->4:low_risk:2",
          "4->7:low_risk:2",
          "7->12:low_risk:2",
          "12->0:low_time:0"
        ],
        "sequence": [
          2,
          4,
          7,
          12
        ],
        "start_time": 18.760781
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      2,
      4,
      7,
      12
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "af94cbabb6634220",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "345400ced8d93403",
    "best_true_reduced_cost": -24.5139606,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 1,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 8,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 42.437713,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.857143,
    "cell_training_negative_count": 1,
    "certificate_effect": false,
    "context_hash": "5628d4c655ec93e5",
    "cut_hash": "7463733468d9ef71",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.2752927541732788,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 0,
    "existing_roi_target": false,
    "expected_context_hash": "5628d4c655ec93e5",
    "forbidden_signature_hash": "7366bb4f473f83a3",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 1,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 5,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks005_01_seed146007_5628d4c655ec93e5_4_3_2_5",
    "negative_gap": 1,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|1",
    "ordinal_positive_rate": 1.0,
    "pool_signature_hash": "92c787ff79f0088d",
    "pool_task_set_hash": "c4a3883825fd04b7",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000000.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 13.316191,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task005_capture_sentinel/logs/BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007_logical_graph.json.jsonl",
    "source_row_index": -1,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      4
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      4,
      3,
      2,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->0:low_risk:2"
        ],
        "sequence": [
          4
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->2:low_risk:2",
          "2->0:low_risk:2"
        ],
        "sequence": [
          3,
          2
        ],
        "start_time": 115.545948
      },
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          5
        ],
        "start_time": 407.760954
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      2,
      3,
      4,
      5
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "be3d6456f9e6a8a6",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "51df5d79e9ac45ae",
    "best_true_reduced_cost": -12.4144668,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 4,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 49,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 12,
    "certificate_effect": false,
    "context_hash": "08b8d772e2ab9623",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9925243258476257,
    "decision_reason": "high_priority",
    "decision_record_index": 18,
    "existing_roi_target": false,
    "expected_context_hash": "08b8d772e2ab9623",
    "forbidden_signature_hash": "0c230e1a6c7fee96",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 3,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_8_16_11_15_18",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "07ce45c4b7ea1c45",
    "pool_task_set_hash": "ba7679f84bbb38ae",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000018.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 13.28225,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "source_row_index": 18,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->16:low_risk:2",
      "16->11:low_risk:2",
      "11->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.333333333,
    "target_priority_sequence": [
      8,
      16,
      11
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      8,
      16,
      11,
      15,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_risk:2",
          "8->16:low_risk:2",
          "16->11:low_risk:2",
          "11->0:low_risk:2"
        ],
        "sequence": [
          8,
          16,
          11
        ],
        "start_time": 14.542572
      },
      {
        "arc_option_sequence": [
          "0->15:low_time:0",
          "15->18:low_risk:2",
          "18->0:low_time:0"
        ],
        "sequence": [
          15,
          18
        ],
        "start_time": 302.871307
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      8,
      11,
      15,
      16,
      18
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "c923eda9f0bcc8d2",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
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
    "cell_positive_rate": 0.083333,
    "cell_training_negative_count": 8,
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
    "score": 13.100739,
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
    "cell_positive_rate": 0.083333,
    "cell_training_negative_count": 8,
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
    "score": 13.090966,
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
    "cell_positive_rate": 0.083333,
    "cell_training_negative_count": 8,
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
    "score": 13.057723,
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
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 12,
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
    "score": 12.901137,
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
    "active_hash_before": "d89bcf257212e075",
    "best_true_reduced_cost": -7.057221,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 2,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 16,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 42.437713,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.857143,
    "cell_training_negative_count": 1,
    "certificate_effect": false,
    "context_hash": "d692a8eb196de3d6",
    "cut_hash": "62d0003f8e0d92c0",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.6894165873527527,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 6,
    "existing_roi_target": false,
    "expected_context_hash": "d692a8eb196de3d6",
    "forbidden_signature_hash": "c20653257bfb3a1b",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_01_seed51000_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 1,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 10,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks010_01_seed51000_d692a8eb196de3d6_2_6_7_4_1",
    "negative_gap": 1,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|1",
    "ordinal_positive_rate": 1.0,
    "pool_signature_hash": "50f549caf51e4f4a",
    "pool_task_set_hash": "b6c1b85d3ef94a12",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "requires_worker_target_causal_match": true,
    "sample_path": "samples/sample_000006.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 12.857477,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task010_capture_sentinel/logs/BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_01_seed51000_logical_graph.json.jsonl",
    "source_row_index": 6,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->6:low_risk:2",
      "6->7:low_time:0",
      "7->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.6,
    "target_priority_sequence": [
      2,
      6,
      7
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      2,
      6,
      7,
      4,
      1
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_time:0",
          "2->6:low_risk:2",
          "6->7:low_time:0",
          "7->0:low_risk:2"
        ],
        "sequence": [
          2,
          6,
          7
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->1:low_risk:2",
          "1->0:low_risk:2"
        ],
        "sequence": [
          4,
          1
        ],
        "start_time": 360.228996
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      2,
      4,
      6,
      7
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "8fbab78aa0bbd840",
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
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 12,
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
    "score": 12.853708,
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
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 12,
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
    "score": 12.664052,
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
    "cell_positive_rate": 0.083333,
    "cell_training_negative_count": 8,
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
    "score": 12.573265,
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
    "cell_positive_rate": 0.083333,
    "cell_training_negative_count": 8,
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
    "score": 12.514112,
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
  }
]
```

## 结论

- 正 ROI 高度集中，不能按 rc 或 HIGH 数量盲目采样；
- 每个 family/region cell 都需要正负样本平衡；
- 候选推荐只用于下一批 audit-only A/B，不允许默认启用 worker；
- GAT/kNN/OOD 仍不能证书，不能产生 official lower bound。
