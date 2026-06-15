# GAT Worker ROI Sampling Priority Audit 报告

日期：2026-06-15

## 目的

根据已有 target-priority worker ROI 标签，找出下一批最值得采样的
family/region/ordinal cell。该流程只读现有 JSON/JSONL，不运行 BPC、
pricing、RMP、worker，也不产生证书或 official bound。

## 机器字段

```text
gat_worker_roi_sampling_priority = current
row_count = 188
candidate_count = 27
recommendation_count = 17
max_per_cell = 6
roi_class_counts = {'columns_only_roi': 10, 'negative_primal_roi': 35, 'negative_retry_roi': 41, 'no_observed_roi': 46, 'positive_primal_roi': 45, 'positive_retry_roi': 11}
production_ready = false
certificate_ready = false
```

## Positive-rich cells

```json
{
  "greedy-anchor|apollo15_20km": {
    "avg_positive_primal_improvement": 2.730553882352952,
    "key": [
      "greedy-anchor",
      "apollo15_20km"
    ],
    "positive_count": 17,
    "positive_rate": 0.4146341463414634,
    "roi_class_counts": {
      "negative_primal_roi": 7,
      "negative_retry_roi": 10,
      "no_observed_roi": 7,
      "positive_primal_roi": 15,
      "positive_retry_roi": 2
    },
    "row_count": 41,
    "training_negative_count": 24,
    "unsupported_count": 0
  },
  "greedy-anchor|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 22.341971249999983,
    "key": [
      "greedy-anchor",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 12,
    "positive_rate": 0.34285714285714286,
    "roi_class_counts": {
      "columns_only_roi": 1,
      "negative_primal_roi": 3,
      "negative_retry_roi": 14,
      "no_observed_roi": 5,
      "positive_primal_roi": 9,
      "positive_retry_roi": 3
    },
    "row_count": 35,
    "training_negative_count": 22,
    "unsupported_count": 1
  },
  "random-wave|apollo15_20km": {
    "avg_positive_primal_improvement": 2.5808203333333495,
    "key": [
      "random-wave",
      "apollo15_20km"
    ],
    "positive_count": 3,
    "positive_rate": 0.15789473684210525,
    "roi_class_counts": {
      "columns_only_roi": 3,
      "negative_primal_roi": 5,
      "negative_retry_roi": 1,
      "no_observed_roi": 7,
      "positive_primal_roi": 1,
      "positive_retry_roi": 2
    },
    "row_count": 19,
    "training_negative_count": 13,
    "unsupported_count": 3
  },
  "random-wave|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 4.6900210000000015,
    "key": [
      "random-wave",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 3,
    "positive_rate": 0.125,
    "roi_class_counts": {
      "columns_only_roi": 2,
      "negative_primal_roi": 6,
      "negative_retry_roi": 5,
      "no_observed_roi": 8,
      "positive_primal_roi": 3
    },
    "row_count": 24,
    "training_negative_count": 19,
    "unsupported_count": 2
  },
  "sector-wave|apollo15_20km": {
    "avg_positive_primal_improvement": 12.151140899999996,
    "key": [
      "sector-wave",
      "apollo15_20km"
    ],
    "positive_count": 10,
    "positive_rate": 0.2777777777777778,
    "roi_class_counts": {
      "columns_only_roi": 2,
      "negative_primal_roi": 6,
      "negative_retry_roi": 8,
      "no_observed_roi": 10,
      "positive_primal_roi": 8,
      "positive_retry_roi": 2
    },
    "row_count": 36,
    "training_negative_count": 24,
    "unsupported_count": 2
  },
  "sector-wave|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 4.2956621818181535,
    "key": [
      "sector-wave",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 11,
    "positive_rate": 0.3333333333333333,
    "roi_class_counts": {
      "columns_only_roi": 2,
      "negative_primal_roi": 8,
      "negative_retry_roi": 3,
      "no_observed_roi": 9,
      "positive_primal_roi": 9,
      "positive_retry_roi": 2
    },
    "row_count": 33,
    "training_negative_count": 20,
    "unsupported_count": 2
  }
}
```

## Sample gaps

```json
[
  {
    "avg_positive_primal_improvement": 4.6900210000000015,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "negative_gap": 0,
    "positive_gap": 1,
    "positive_rate": 0.125,
    "row_count": 24
  },
  {
    "avg_positive_primal_improvement": 2.5808203333333495,
    "cell": "random-wave|apollo15_20km",
    "negative_gap": 0,
    "positive_gap": 1,
    "positive_rate": 0.15789473684210525,
    "row_count": 19
  }
]
```

## Recommendations

```json
[
  {
    "active_hash_before": "03a8d149c5bdfc16",
    "best_true_reduced_cost": -1.632716,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 11,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 2,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.58082,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.157895,
    "cell_training_negative_count": 13,
    "certificate_effect": false,
    "context_hash": "fbfd88d4ebde5459",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.7041040658950806,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 10,
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
    "ordinal_positive_rate": 0.4,
    "pool_signature_hash": "4846218d8d5926f5",
    "pool_task_set_hash": "b3efd3d85e0ad5f4",
    "positive_gap": 1,
    "positive_gap_weight": 5.2,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.4,
    "sample_path": "samples/sample_000010.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 8.517506,
    "source_candidate_file": "BPC_future/results/gat_same_run_random_wave_ord8_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord8_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "source_row_index": 10,
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
    "cell_avg_positive_primal_improvement": 2.58082,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.157895,
    "cell_training_negative_count": 13,
    "certificate_effect": false,
    "context_hash": "3100b787bf438dfe",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.7076878547668457,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 9,
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
    "ordinal_positive_rate": 0.4,
    "pool_signature_hash": "7a249193fdd37789",
    "pool_task_set_hash": "e3f049a263f86c82",
    "positive_gap": 1,
    "positive_gap_weight": 5.2,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.4,
    "sample_path": "samples/sample_000009.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 8.446177,
    "source_candidate_file": "BPC_future/results/gat_same_run_random_wave_ord8_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord8_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "source_row_index": 9,
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
    "active_hash_before": "eb92a6a521734d12",
    "best_true_reduced_cost": -0.791942,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 7,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 3,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.58082,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.157895,
    "cell_training_negative_count": 13,
    "certificate_effect": false,
    "context_hash": "409f65576794fa39",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.8982958793640137,
    "decision_reason": "knn_delay_fraction_delay_queue",
    "decision_record_index": 7,
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
    "ordinal_positive_rate": 0.4,
    "pool_signature_hash": "61505b62c0f9a4a1",
    "pool_task_set_hash": "bba64460221b3547",
    "positive_gap": 1,
    "positive_gap_weight": 5.2,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.4,
    "sample_path": "samples/sample_000007.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 8.169659,
    "source_candidate_file": "BPC_future/results/gat_same_run_random_wave_ord8_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord8_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "source_row_index": 7,
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
    "active_hash_before": "6405fc3f1de6a512",
    "best_true_reduced_cost": -1.366833,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 5,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 49,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.125,
    "cell_training_negative_count": 19,
    "certificate_effect": false,
    "context_hash": "5f4498eb39858b1d",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9133797287940979,
    "decision_reason": "high_priority",
    "decision_record_index": 11,
    "existing_roi_target": false,
    "expected_context_hash": "5f4498eb39858b1d",
    "forbidden_signature_hash": "d223202b3043800f",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 5,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_5f4498eb39858b1d_5_6_10_7_13_11",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|5",
    "ordinal_positive_rate": 0.75,
    "pool_signature_hash": "a14ffdc8106d7c11",
    "pool_task_set_hash": "57819ddf969ca320",
    "positive_gap": 1,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.75,
    "sample_path": "samples/sample_000011.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 6.825723,
    "source_candidate_file": "BPC_future/results/gat_same_run_random_wave_ord5_high_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord5_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json.jsonl",
    "source_row_index": 11,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->6:low_risk:2",
      "6->10:low_energy:1",
      "10->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.375,
    "target_priority_sequence": [
      5,
      6,
      10
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      5,
      6,
      10,
      7,
      13,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->6:low_risk:2",
          "6->10:low_energy:1",
          "10->0:low_risk:2"
        ],
        "sequence": [
          5,
          6,
          10
        ],
        "start_time": 10.218359
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
        "start_time": 331.722549
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      5,
      6,
      7,
      10,
      11,
      13
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "788890d1a40f457f",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "d8dee49da637491a",
    "best_true_reduced_cost": -0.738944,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 7,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 1,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.125,
    "cell_training_negative_count": 19,
    "certificate_effect": false,
    "context_hash": "8f2088cfefc3e3b1",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.9278675317764282,
    "decision_reason": "knn_delay_fraction_delay_queue",
    "decision_record_index": 13,
    "existing_roi_target": false,
    "expected_context_hash": "8f2088cfefc3e3b1",
    "forbidden_signature_hash": "7fb0f1421be973cb",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 5,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_8f2088cfefc3e3b1_20_3_7",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|5",
    "ordinal_positive_rate": 0.75,
    "pool_signature_hash": "8c4430995d61f86b",
    "pool_task_set_hash": "37c69d4231a5d4f1",
    "positive_gap": 1,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.75,
    "sample_path": "samples/sample_000013.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 6.308817,
    "source_candidate_file": "BPC_future/results/gat_same_run_random_wave_ord5_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord5_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json.jsonl",
    "source_row_index": 13,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->0:low_risk:2"
    ],
    "target_impact_bucket": "new_task_set",
    "target_max_active_jaccard": 0.75,
    "target_priority_sequence": [
      20
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      20,
      3,
      7
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_risk:2",
          "20->0:low_risk:2"
        ],
        "sequence": [
          20
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->7:low_risk:2",
          "7->0:low_risk:2"
        ],
        "sequence": [
          3,
          7
        ],
        "start_time": 142.305648
      }
    ],
    "target_support_changing_proxy": false,
    "target_task_set": [
      3,
      7,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 3,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "7c6a6d9ca297c314",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "2a0b4670d5737413",
    "best_true_reduced_cost": -1.3002795,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 12,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 5,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.58082,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.157895,
    "cell_training_negative_count": 13,
    "certificate_effect": false,
    "context_hash": "2d9686e5aa73b5f3",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.8996635675430298,
    "decision_reason": "knn_delay_fraction_delay_queue",
    "decision_record_index": 7,
    "existing_roi_target": false,
    "expected_context_hash": "2d9686e5aa73b5f3",
    "forbidden_signature_hash": "72d882a694a7afb4",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 5,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_2d9686e5aa73b5f3_9_19_1_16_11",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|5",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "b9a92aab0d0618a2",
    "pool_task_set_hash": "348ad9b59205f105",
    "positive_gap": 1,
    "positive_gap_weight": 3.263158,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.157895,
    "sample_path": "samples/sample_000007.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.959602,
    "source_candidate_file": "BPC_future/results/gat_same_run_random_wave_ord5_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord5_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json.jsonl",
    "source_row_index": 7,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->9:low_risk:2",
      "9->19:low_risk:2",
      "19->1:low_risk:2",
      "1->16:low_risk:2",
      "16->11:low_risk:2",
      "11->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.428571429,
    "target_priority_sequence": [
      9,
      19,
      1,
      16,
      11
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      9,
      19,
      1,
      16,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->9:low_risk:2",
          "9->19:low_risk:2",
          "19->1:low_risk:2",
          "1->16:low_risk:2",
          "16->11:low_risk:2",
          "11->0:low_risk:2"
        ],
        "sequence": [
          9,
          19,
          1,
          16,
          11
        ],
        "start_time": 26.061884
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      9,
      11,
      16,
      19
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "794c11f3b9f87222",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "84a32099330f4216",
    "best_true_reduced_cost": -3.4372954,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 16,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 38,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.58082,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.157895,
    "cell_training_negative_count": 13,
    "certificate_effect": false,
    "context_hash": "5c6127a7add1e6f6",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.7727511525154114,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 20,
    "existing_roi_target": false,
    "expected_context_hash": "5c6127a7add1e6f6",
    "forbidden_signature_hash": "31b3354de2646468",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 2,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_5c6127a7add1e6f6_13_11_15_6",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|2",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "622f9128ae38a6db",
    "pool_task_set_hash": "b440da82d9e3a2ed",
    "positive_gap": 1,
    "positive_gap_weight": 3.263158,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.157895,
    "sample_path": "samples/sample_000020.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.93954,
    "source_candidate_file": "BPC_future/results/gat_same_run_gap_focused_ord2_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_gap_focused_ord2_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json.jsonl",
    "source_row_index": 20,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->11:low_time:0",
      "11->15:low_risk:2",
      "15->6:low_time:0",
      "6->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.4,
    "target_priority_sequence": [
      13,
      11,
      15,
      6
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      13,
      11,
      15,
      6
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->11:low_time:0",
          "11->15:low_risk:2",
          "15->6:low_time:0",
          "6->0:low_time:0"
        ],
        "sequence": [
          13,
          11,
          15,
          6
        ],
        "start_time": 71.0893
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      6,
      11,
      13,
      15
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "0848b9e9ea448d4e",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "c404098cefa45555",
    "best_true_reduced_cost": -5.162046,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 6,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.58082,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.157895,
    "cell_training_negative_count": 13,
    "certificate_effect": false,
    "context_hash": "ffe911c2088f42a2",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.5983518362045288,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 6,
    "existing_roi_target": false,
    "expected_context_hash": "ffe911c2088f42a2",
    "forbidden_signature_hash": "94bc86dc7e0423a8",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 4,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_ffe911c2088f42a2_6_5_12_11_10_18",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|4",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "76f5f269e52fcc11",
    "pool_task_set_hash": "b8995e889fe16310",
    "positive_gap": 1,
    "positive_gap_weight": 3.263158,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.157895,
    "sample_path": "samples/sample_000006.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.851378,
    "source_candidate_file": "BPC_future/results/gat_same_run_random_wave_ord4_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord4_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_04_seed61306_logical_graph.json.jsonl",
    "source_row_index": 6,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->6:low_risk:1",
      "6->5:low_risk:2",
      "5->12:low_risk:2",
      "12->11:low_risk:2",
      "11->10:low_risk:2",
      "10->18:low_risk:2",
      "18->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.571428571,
    "target_priority_sequence": [
      6,
      5,
      12,
      11,
      10,
      18
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      6,
      5,
      12,
      11,
      10,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->6:low_risk:1",
          "6->5:low_risk:2",
          "5->12:low_risk:2",
          "12->11:low_risk:2",
          "11->10:low_risk:2",
          "10->18:low_risk:2",
          "18->0:low_risk:2"
        ],
        "sequence": [
          6,
          5,
          12,
          11,
          10,
          18
        ],
        "start_time": 0.0
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      5,
      6,
      10,
      11,
      12,
      18
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "3bed7040b564e435",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "db0c1f2c45a0c84f",
    "best_true_reduced_cost": -4.595146,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 12,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 21,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.125,
    "cell_training_negative_count": 19,
    "certificate_effect": false,
    "context_hash": "94989e70b81983eb",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9317850470542908,
    "decision_reason": "high_priority",
    "decision_record_index": 7,
    "existing_roi_target": false,
    "expected_context_hash": "94989e70b81983eb",
    "forbidden_signature_hash": "434de1d47f21c0d5",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 6,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_94989e70b81983eb_14_4_13_16",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|6",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "62adf022ae0f62e0",
    "pool_task_set_hash": "d8d378ea700f9633",
    "positive_gap": 1,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.125,
    "sample_path": "samples/sample_000007.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.505544,
    "source_candidate_file": "BPC_future/results/gat_same_run_random_wave_ord6_high_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord6_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json.jsonl",
    "source_row_index": 7,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->14:low_risk:1",
      "14->4:low_time:0",
      "4->13:low_energy:1",
      "13->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.333333333,
    "target_priority_sequence": [
      14,
      4,
      13
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      14,
      4,
      13,
      16
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->14:low_risk:1",
          "14->4:low_time:0",
          "4->13:low_energy:1",
          "13->0:low_time:0"
        ],
        "sequence": [
          14,
          4,
          13
        ],
        "start_time": 61.759229
      },
      {
        "arc_option_sequence": [
          "0->16:low_risk:2",
          "16->0:low_risk:2"
        ],
        "sequence": [
          16
        ],
        "start_time": 415.5713
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      4,
      13,
      14,
      16
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "10c5d24d15b7fe6c",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "520afd05a482d5e9",
    "best_true_reduced_cost": -0.502472833,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 17,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 8,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.125,
    "cell_training_negative_count": 19,
    "certificate_effect": false,
    "context_hash": "3375e356a084eadb",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.7878299951553345,
    "decision_reason": "knn_delay_fraction_delay_queue",
    "decision_record_index": 24,
    "existing_roi_target": false,
    "expected_context_hash": "3375e356a084eadb",
    "forbidden_signature_hash": "8d50059d689b2887",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 2,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3375e356a084eadb_12_5_1_9_7_15",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|2",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "b86b85a1777a7128",
    "pool_task_set_hash": "19f0f6cb6c508fef",
    "positive_gap": 1,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.125,
    "sample_path": "samples/sample_000024.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.156956,
    "source_candidate_file": "BPC_future/results/gat_same_run_gap_focused_ord2_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_gap_focused_ord2_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json.jsonl",
    "source_row_index": 24,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->5:low_risk:2",
      "5->1:low_time:0",
      "1->9:low_risk:2",
      "9->7:low_risk:2",
      "7->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.571428571,
    "target_priority_sequence": [
      12,
      5,
      1,
      9,
      7
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      12,
      5,
      1,
      9,
      7,
      15
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_risk:2",
          "12->5:low_risk:2",
          "5->1:low_time:0",
          "1->9:low_risk:2",
          "9->7:low_risk:2",
          "7->0:low_risk:2"
        ],
        "sequence": [
          12,
          5,
          1,
          9,
          7
        ],
        "start_time": 17.038329
      },
      {
        "arc_option_sequence": [
          "0->15:low_risk:2",
          "15->0:low_risk:2"
        ],
        "sequence": [
          15
        ],
        "start_time": 390.349024
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      5,
      7,
      9,
      12,
      15
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "aaea9214556f4f61",
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
    "cell_positive_count": 3,
    "cell_positive_rate": 0.125,
    "cell_training_negative_count": 19,
    "certificate_effect": false,
    "context_hash": "a77e5457bde80b8e",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.7405292391777039,
    "decision_reason": "high_priority",
    "decision_record_index": 11,
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
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.125,
    "sample_path": "samples/sample_000011.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.145577,
    "source_candidate_file": "BPC_future/results/gat_same_run_random_wave_ord8_high_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord8_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json.jsonl",
    "source_row_index": 11,
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
    "active_hash_before": "22baed86ddf23d15",
    "best_true_reduced_cost": -4.364312,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 14,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 5,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 3,
    "cell_positive_rate": 0.125,
    "cell_training_negative_count": 19,
    "certificate_effect": false,
    "context_hash": "7c518307952f17f7",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.5483608841896057,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 9,
    "existing_roi_target": false,
    "expected_context_hash": "7c518307952f17f7",
    "forbidden_signature_hash": "db575711fa559d70",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 6,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_7c518307952f17f7_19_2_8",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|6",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "f0a36a19229897f6",
    "pool_task_set_hash": "24ef3d780ca7d29f",
    "positive_gap": 1,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.125,
    "sample_path": "samples/sample_000009.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.110579,
    "source_candidate_file": "BPC_future/results/gat_same_run_random_wave_ord6_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord6_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json.jsonl",
    "source_row_index": 9,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->19:low_time:0",
      "19->2:low_risk:2",
      "2->8:low_risk:2",
      "8->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.4,
    "target_priority_sequence": [
      19,
      2,
      8
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      19,
      2,
      8
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->19:low_time:0",
          "19->2:low_risk:2",
          "2->8:low_risk:2",
          "8->0:low_time:0"
        ],
        "sequence": [
          19,
          2,
          8
        ],
        "start_time": 23.990832
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      2,
      8,
      19
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 3,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "ecdc1afd090a8d52",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "b385bb1cafde884c",
    "best_true_reduced_cost": -1.373495,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 22,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 13,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.730554,
    "cell_positive_count": 17,
    "cell_positive_rate": 0.414634,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "aa6ac3757841f1b3",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.8451055288314819,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 21,
    "existing_roi_target": false,
    "expected_context_hash": "aa6ac3757841f1b3",
    "forbidden_signature_hash": "ec17776b9ea2b9e0",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 3,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_aa6ac3757841f1b3_13_3_2_18_10_1",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "70e4dfba6a2de489",
    "pool_task_set_hash": "d38cc4a9bc6c538a",
    "positive_gap": 0,
    "positive_gap_weight": 5.317073,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.414634,
    "sample_path": "samples/sample_000021.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 3.430738,
    "source_candidate_file": "BPC_future/results/gat_same_run_gap_focused_ord3_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_gap_focused_ord3_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "source_row_index": 21,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      13
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      13,
      3,
      2,
      18,
      10,
      1
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->0:low_risk:2"
        ],
        "sequence": [
          13
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->2:low_risk:2",
          "2->18:low_risk:2",
          "18->10:low_risk:2",
          "10->1:low_risk:2",
          "1->0:low_time:0"
        ],
        "sequence": [
          3,
          2,
          18,
          10,
          1
        ],
        "start_time": 69.07485
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      2,
      3,
      10,
      13,
      18
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "f97516f02039c303",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "0ca6979bb961a3dd",
    "best_true_reduced_cost": -0.902539,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 19,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 8,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.730554,
    "cell_positive_count": 17,
    "cell_positive_rate": 0.414634,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "8af5db3562524c9f",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.8338466882705688,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 18,
    "existing_roi_target": false,
    "expected_context_hash": "8af5db3562524c9f",
    "forbidden_signature_hash": "8ce3fc284a217d5c",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 3,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_8af5db3562524c9f_11_4_9_5_1",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "51e4ad7adf6e04c1",
    "pool_task_set_hash": "a782e0ad467ced57",
    "positive_gap": 0,
    "positive_gap_weight": 5.317073,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.414634,
    "sample_path": "samples/sample_000018.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 3.395931,
    "source_candidate_file": "BPC_future/results/gat_same_run_gap_focused_ord3_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_gap_focused_ord3_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "source_row_index": 18,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->11:low_risk:2",
      "11->4:low_time:0",
      "4->9:low_time:0",
      "9->5:low_time:0",
      "5->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.428571429,
    "target_priority_sequence": [
      11,
      4,
      9,
      5
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      11,
      4,
      9,
      5,
      1
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->11:low_risk:2",
          "11->4:low_time:0",
          "4->9:low_time:0",
          "9->5:low_time:0",
          "5->0:low_time:0"
        ],
        "sequence": [
          11,
          4,
          9,
          5
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->1:low_time:0",
          "1->0:low_time:0"
        ],
        "sequence": [
          1
        ],
        "start_time": 407.256981
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      4,
      5,
      9,
      11
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "c7ad8eb19ca21bee",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "5cb6c522a05a124e",
    "best_true_reduced_cost": -0.7505265,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 24,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 4,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.730554,
    "cell_positive_count": 17,
    "cell_positive_rate": 0.414634,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "a504ecc531a8f8b3",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.840583324432373,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 23,
    "existing_roi_target": false,
    "expected_context_hash": "a504ecc531a8f8b3",
    "forbidden_signature_hash": "ffee33e0f5f13dad",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 3,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_a504ecc531a8f8b3_3_13_17",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "53706f1884c682a9",
    "pool_task_set_hash": "7e5ae3e616b3a95c",
    "positive_gap": 0,
    "positive_gap_weight": 5.317073,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.414634,
    "sample_path": "samples/sample_000023.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 3.395067,
    "source_candidate_file": "BPC_future/results/gat_same_run_gap_focused_ord3_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_gap_focused_ord3_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "source_row_index": 23,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      3
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      3,
      13,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->0:low_risk:2"
        ],
        "sequence": [
          3
        ],
        "start_time": 15.271817
      },
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->17:low_risk:2",
          "17->0:low_time:0"
        ],
        "sequence": [
          13,
          17
        ],
        "start_time": 91.522898
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      3,
      13,
      17
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 3,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "fd472aca89b38ca8",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "c165c6e9753428fc",
    "best_true_reduced_cost": -0.044787,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 21,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 11,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.730554,
    "cell_positive_count": 17,
    "cell_positive_rate": 0.414634,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "0c8ac146692baefa",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.8396121859550476,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 20,
    "existing_roi_target": false,
    "expected_context_hash": "0c8ac146692baefa",
    "forbidden_signature_hash": "9adf96bed089a64a",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 3,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_0c8ac146692baefa_13_14_2_18_10_1",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "664057160a142598",
    "pool_task_set_hash": "4043a847157ced95",
    "positive_gap": 0,
    "positive_gap_weight": 5.317073,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.414634,
    "sample_path": "samples/sample_000020.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 3.358809,
    "source_candidate_file": "BPC_future/results/gat_same_run_gap_focused_ord3_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_gap_focused_ord3_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "source_row_index": 20,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.571428571,
    "target_priority_sequence": [
      13
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      13,
      14,
      2,
      18,
      10,
      1
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->0:low_risk:2"
        ],
        "sequence": [
          13
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->14:low_risk:2",
          "14->2:low_time:0",
          "2->18:low_risk:2",
          "18->10:low_risk:2",
          "10->1:low_risk:2",
          "1->0:low_time:0"
        ],
        "sequence": [
          14,
          2,
          18,
          10,
          1
        ],
        "start_time": 58.959462
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      2,
      10,
      13,
      14,
      18
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "3fea26dd49d52b77",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "5053e72622eff22b",
    "best_true_reduced_cost": -0.5478395,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 23,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 1,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.730554,
    "cell_positive_count": 17,
    "cell_positive_rate": 0.414634,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "c7c654f79d6f4852",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.860686182975769,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 22,
    "existing_roi_target": false,
    "expected_context_hash": "c7c654f79d6f4852",
    "forbidden_signature_hash": "cd032ba47583046c",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 3,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_c7c654f79d6f4852_14_3_2_20_10_1",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "115cf20a7c62f7fc",
    "pool_task_set_hash": "a5927207514ffc35",
    "positive_gap": 0,
    "positive_gap_weight": 5.317073,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.414634,
    "sample_path": "samples/sample_000022.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 2.905036,
    "source_candidate_file": "BPC_future/results/gat_same_run_gap_focused_ord3_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_gap_focused_ord3_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "source_row_index": 22,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->3:low_risk:2",
      "3->2:low_risk:2",
      "2->20:low_risk:2",
      "20->10:low_risk:1",
      "10->1:low_risk:2",
      "1->0:low_time:0"
    ],
    "target_impact_bucket": "new_task_set",
    "target_max_active_jaccard": 0.714285714,
    "target_priority_sequence": [
      14,
      3,
      2,
      20,
      10,
      1
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      14,
      3,
      2,
      20,
      10,
      1
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->14:low_risk:2",
          "14->3:low_risk:2",
          "3->2:low_risk:2",
          "2->20:low_risk:2",
          "20->10:low_risk:1",
          "10->1:low_risk:2",
          "1->0:low_time:0"
        ],
        "sequence": [
          14,
          3,
          2,
          20,
          10,
          1
        ],
        "start_time": 4.165907
      }
    ],
    "target_support_changing_proxy": false,
    "target_task_set": [
      1,
      2,
      3,
      10,
      14,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "7c9171ea78e05ff1",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  }
]
```

## 结论

- 正 ROI 高度集中，不能按 rc 或 HIGH 数量盲目采样；
- 每个 family/region cell 都需要正负样本平衡；
- 候选推荐只用于下一批 audit-only A/B，不允许默认启用 worker；
- GAT/kNN/OOD 仍不能证书，不能产生 official lower bound。
