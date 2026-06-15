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
candidate_count = 50
recommendation_count = 4
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
  }
]
```

## 结论

- 正 ROI 高度集中，不能按 rc 或 HIGH 数量盲目采样；
- 每个 family/region cell 都需要正负样本平衡；
- 候选推荐只用于下一批 audit-only A/B，不允许默认启用 worker；
- GAT/kNN/OOD 仍不能证书，不能产生 official lower bound。
