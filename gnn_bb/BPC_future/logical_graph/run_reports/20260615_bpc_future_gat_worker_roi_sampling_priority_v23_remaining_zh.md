# GAT Worker ROI Sampling Priority Audit 报告

日期：2026-06-15

## 目的

根据已有 target-priority worker ROI 标签，找出下一批最值得采样的
family/region/ordinal cell。该流程只读现有 JSON/JSONL，不运行 BPC、
pricing、RMP、worker，也不产生证书或 official bound。

## 机器字段

```text
gat_worker_roi_sampling_priority = current
row_count = 104
candidate_count = 27
recommendation_count = 20
max_per_cell = 6
roi_class_counts = {'columns_only_roi': 7, 'negative_primal_roi': 18, 'negative_retry_roi': 13, 'no_observed_roi': 38, 'positive_primal_roi': 24, 'positive_retry_roi': 4}
production_ready = false
certificate_ready = false
```

## Positive-rich cells

```json
{
  "greedy-anchor|apollo15_20km": {
    "avg_positive_primal_improvement": 3.260931999999997,
    "key": [
      "greedy-anchor",
      "apollo15_20km"
    ],
    "positive_count": 8,
    "positive_rate": 0.5333333333333333,
    "roi_class_counts": {
      "negative_primal_roi": 1,
      "negative_retry_roi": 1,
      "no_observed_roi": 5,
      "positive_primal_roi": 6,
      "positive_retry_roi": 2
    },
    "row_count": 15,
    "training_negative_count": 7,
    "unsupported_count": 0
  },
  "greedy-anchor|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 33.391141249999976,
    "key": [
      "greedy-anchor",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 8,
    "positive_rate": 0.4444444444444444,
    "roi_class_counts": {
      "negative_primal_roi": 2,
      "negative_retry_roi": 6,
      "no_observed_roi": 2,
      "positive_primal_roi": 8
    },
    "row_count": 18,
    "training_negative_count": 10,
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
    "positive_rate": 0.25,
    "roi_class_counts": {
      "columns_only_roi": 1,
      "negative_primal_roi": 1,
      "negative_retry_roi": 1,
      "no_observed_roi": 9,
      "positive_primal_roi": 4
    },
    "row_count": 16,
    "training_negative_count": 11,
    "unsupported_count": 1
  },
  "sector-wave|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 2.808386333333317,
    "key": [
      "sector-wave",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 6,
    "positive_rate": 0.3,
    "roi_class_counts": {
      "columns_only_roi": 1,
      "negative_primal_roi": 4,
      "no_observed_roi": 9,
      "positive_primal_roi": 4,
      "positive_retry_roi": 2
    },
    "row_count": 20,
    "training_negative_count": 13,
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
    "active_hash_before": "16e2d0342cb4ce87",
    "best_true_reduced_cost": -0.246846,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 30,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 22,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 3.260932,
    "cell_positive_count": 8,
    "cell_positive_rate": 0.533333,
    "cell_training_negative_count": 7,
    "certificate_effect": false,
    "context_hash": "7db256d4f7224cc6",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9491479396820068,
    "decision_reason": "high_priority",
    "decision_record_index": 43,
    "existing_roi_target": false,
    "expected_context_hash": "7db256d4f7224cc6",
    "forbidden_signature_hash": "5aeacc70a6d978d0",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 5,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|5",
    "ordinal_positive_rate": 1.0,
    "pool_signature_hash": "c5ddd5b68ac1fbd8",
    "pool_task_set_hash": "6f8bb60d3048867b",
    "positive_gap": 0,
    "positive_gap_weight": 10.0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 1.0,
    "sample_path": "samples/sample_000043.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.887583,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json.jsonl",
    "source_row_index": 43,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->20:low_risk:1",
      "20->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.555555556,
    "target_priority_sequence": [
      12,
      20
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      12,
      20,
      5,
      3,
      6,
      4
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_risk:2",
          "12->20:low_risk:1",
          "20->0:low_time:0"
        ],
        "sequence": [
          12,
          20
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->5:low_time:0",
          "5->3:low_risk:2",
          "3->6:low_time:0",
          "6->4:low_energy:1",
          "4->0:low_time:0"
        ],
        "sequence": [
          5,
          3,
          6,
          4
        ],
        "start_time": 127.287307
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      3,
      4,
      5,
      6,
      12,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "2fbba0a0a55dc9ef",
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
    "active_hash_before": "ede095c6ba8539c1",
    "best_true_reduced_cost": -21.659046,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 3,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 49,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 2.808386,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.3,
    "cell_training_negative_count": 13,
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
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.5,
    "pool_signature_hash": "b0fe906b0c1ab18d",
    "pool_task_set_hash": "ee50cf9eb4b638b3",
    "positive_gap": 0,
    "positive_gap_weight": 6.0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.5,
    "sample_path": "samples/sample_000023.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.229199,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json.jsonl",
    "source_row_index": 23,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->7:low_time:0",
      "7->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.4,
    "target_priority_sequence": [
      1,
      7
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      1,
      7,
      20,
      4,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->1:low_time:0",
          "1->7:low_time:0",
          "7->0:low_time:0"
        ],
        "sequence": [
          1,
          7
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->20:low_risk:2",
          "20->4:low_time:0",
          "4->10:low_time:0",
          "10->0:low_risk:2"
        ],
        "sequence": [
          20,
          4,
          10
        ],
        "start_time": 210.842101
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      4,
      7,
      10,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "4dba67189cd38261",
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
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.0938,
    "sample_path": "samples/sample_000021.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.114052,
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
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.154849,
    "sample_path": "samples/sample_000035.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.023265,
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
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 11,
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
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.154849,
    "sample_path": "samples/sample_000012.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.964112,
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
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 11,
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
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.154849,
    "sample_path": "samples/sample_000015.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.957015,
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
    "cell_positive_rate": 0.066667,
    "cell_training_negative_count": 11,
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
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.154849,
    "sample_path": "samples/sample_000014.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.895902,
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
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.0938,
    "sample_path": "samples/sample_000039.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.886726,
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
    "cell_positive_rate": 0.05,
    "cell_training_negative_count": 17,
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
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.0938,
    "sample_path": "samples/sample_000022.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.809368,
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
  },
  {
    "active_hash_before": "950498a3c24cb589",
    "best_true_reduced_cost": -0.236974,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 11,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 28,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.05,
    "cell_training_negative_count": 17,
    "certificate_effect": false,
    "context_hash": "7cb380a02e30e5a8",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.6580277681350708,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 24,
    "existing_roi_target": false,
    "expected_context_hash": "7cb380a02e30e5a8",
    "forbidden_signature_hash": "5cd3c347558839d5",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 9,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_09_seed61820_7cb380a02e30e5a8_1_2_9_16",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|9",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "7ef6419dc8239cb4",
    "pool_task_set_hash": "dad9d51aaf8ae5e1",
    "positive_gap": 1,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.0938,
    "sample_path": "samples/sample_000024.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.788879,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json.jsonl",
    "source_row_index": 24,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->2:low_risk:2",
      "2->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.4,
    "target_priority_sequence": [
      1,
      2
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      1,
      2,
      9,
      16
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->1:low_time:0",
          "1->2:low_risk:2",
          "2->0:low_time:0"
        ],
        "sequence": [
          1,
          2
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->9:low_time:0",
          "9->16:low_risk:2",
          "16->0:low_energy:1"
        ],
        "sequence": [
          9,
          16
        ],
        "start_time": 322.611909
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      2,
      9,
      16
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "51702c3dec001ab6",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "747568d75e418e47",
    "best_true_reduced_cost": -0.936402,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 20,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 6,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.05,
    "cell_training_negative_count": 17,
    "certificate_effect": false,
    "context_hash": "86b8842ee1325e6d",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.6069411635398865,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 23,
    "existing_roi_target": false,
    "expected_context_hash": "86b8842ee1325e6d",
    "forbidden_signature_hash": "e21155e61ada7f2a",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 8,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_86b8842ee1325e6d_18_4_20_6",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|8",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "75aac9a255e1aa94",
    "pool_task_set_hash": "190a13b94f7da58e",
    "positive_gap": 1,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.0938,
    "sample_path": "samples/sample_000023.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.772763,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json.jsonl",
    "source_row_index": 23,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->18:low_energy:1",
      "18->4:low_energy:1",
      "4->0:low_energy:1"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      18,
      4
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      18,
      4,
      20,
      6
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->18:low_energy:1",
          "18->4:low_energy:1",
          "4->0:low_energy:1"
        ],
        "sequence": [
          18,
          4
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->20:low_risk:2",
          "20->6:low_time:0",
          "6->0:low_risk:2"
        ],
        "sequence": [
          20,
          6
        ],
        "start_time": 345.431386
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      4,
      6,
      18,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "9f3104088caab5c6",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "f709fd0ac80f9da6",
    "best_true_reduced_cost": -9.801078667,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 9,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 49,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 2.808386,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.3,
    "cell_training_negative_count": 13,
    "certificate_effect": false,
    "context_hash": "1f855fbf33f8155e",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9283106327056885,
    "decision_reason": "high_priority",
    "decision_record_index": 25,
    "existing_roi_target": false,
    "expected_context_hash": "1f855fbf33f8155e",
    "forbidden_signature_hash": "86f0c2ecc2a5f670",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 3,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.5,
    "pool_signature_hash": "d39cf2bdac1f86c0",
    "pool_task_set_hash": "e8bed3973827ac75",
    "positive_gap": 0,
    "positive_gap_weight": 6.0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.5,
    "sample_path": "samples/sample_000025.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.599203,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json.jsonl",
    "source_row_index": 25,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->1:low_time:0",
      "1->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.428571429,
    "target_priority_sequence": [
      8,
      1
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      8,
      1,
      3,
      9,
      15
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->1:low_time:0",
          "1->0:low_risk:2"
        ],
        "sequence": [
          8,
          1
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->9:low_risk:2",
          "9->15:low_risk:2",
          "15->0:low_risk:2"
        ],
        "sequence": [
          3,
          9,
          15
        ],
        "start_time": 261.945896
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      3,
      8,
      9,
      15
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "62e7f0a17b457469",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "b16d57084589277c",
    "best_true_reduced_cost": -1.154811,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 7,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 1,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 1,
    "cell_positive_rate": 0.05,
    "cell_training_negative_count": 17,
    "certificate_effect": false,
    "context_hash": "ea4caec0fad0f878",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.28301921486854553,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 40,
    "existing_roi_target": false,
    "expected_context_hash": "ea4caec0fad0f878",
    "forbidden_signature_hash": "29594d546381ae7a",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 10,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ea4caec0fad0f878_19_8_7",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|10",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "6f01c6996a796aed",
    "pool_task_set_hash": "f6abc9810d4b48df",
    "positive_gap": 1,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.0938,
    "sample_path": "samples/sample_000040.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.459762,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json.jsonl",
    "source_row_index": 40,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->19:low_risk:2",
      "19->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.25,
    "target_priority_sequence": [
      19
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      19,
      8,
      7
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->19:low_risk:2",
          "19->0:low_risk:2"
        ],
        "sequence": [
          19
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->8:low_energy:1",
          "8->7:low_time:0",
          "7->0:low_time:0"
        ],
        "sequence": [
          8,
          7
        ],
        "start_time": 167.129072
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      7,
      8,
      19
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 3,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "874bcc1af142ff7e",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "d42e4dfcb1b824f6",
    "best_true_reduced_cost": -6.160642855,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 20,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 24,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 3.260932,
    "cell_positive_count": 8,
    "cell_positive_rate": 0.533333,
    "cell_training_negative_count": 7,
    "certificate_effect": false,
    "context_hash": "eb102a126dd0d5e3",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9548203945159912,
    "decision_reason": "high_priority",
    "decision_record_index": 57,
    "existing_roi_target": false,
    "expected_context_hash": "eb102a126dd0d5e3",
    "forbidden_signature_hash": "81285dc9803e02f3",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 7,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|7",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "dcb5e786134f42c8",
    "pool_task_set_hash": "d38707bfb680f48a",
    "positive_gap": 0,
    "positive_gap_weight": 6.266667,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.533333,
    "sample_path": "samples/sample_000057.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.188946,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave04/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json.jsonl",
    "source_row_index": 57,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->9:low_time:0",
      "9->10:low_risk:2",
      "10->4:low_time:0",
      "4->14:low_time:0",
      "14->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.428571429,
    "target_priority_sequence": [
      9,
      10,
      4,
      14
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      9,
      10,
      4,
      14,
      1
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->9:low_time:0",
          "9->10:low_risk:2",
          "10->4:low_time:0",
          "4->14:low_time:0",
          "14->0:low_risk:2"
        ],
        "sequence": [
          9,
          10,
          4,
          14
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->1:low_risk:1",
          "1->0:low_risk:1"
        ],
        "sequence": [
          1
        ],
        "start_time": 417.91101
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      4,
      9,
      10,
      14
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "ed31e680c7b12e76",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "0780f9f032c659a7",
    "best_true_reduced_cost": -5.136822556,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 16,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 24,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 3.260932,
    "cell_positive_count": 8,
    "cell_positive_rate": 0.533333,
    "cell_training_negative_count": 7,
    "certificate_effect": false,
    "context_hash": "22dec9cfc13bb3d6",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9576816558837891,
    "decision_reason": "high_priority",
    "decision_record_index": 59,
    "existing_roi_target": false,
    "expected_context_hash": "22dec9cfc13bb3d6",
    "forbidden_signature_hash": "9324e282befa1ac8",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 8,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_7_8_20_3",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|8",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "b8aa00efb6e169f6",
    "pool_task_set_hash": "a98072364d0bfc1e",
    "positive_gap": 0,
    "positive_gap_weight": 6.266667,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.533333,
    "sample_path": "samples/sample_000059.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.140616,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave04/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json.jsonl",
    "source_row_index": 59,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->7:low_risk:2",
      "7->8:low_risk:2",
      "8->20:low_risk:2",
      "20->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.428571429,
    "target_priority_sequence": [
      7,
      8,
      20
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      7,
      8,
      20,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->7:low_risk:2",
          "7->8:low_risk:2",
          "8->20:low_risk:2",
          "20->0:low_time:0"
        ],
        "sequence": [
          7,
          8,
          20
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->0:low_risk:2"
        ],
        "sequence": [
          3
        ],
        "start_time": 302.772773
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      3,
      7,
      8,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "f41cb57ae52a541e",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "7e1550730bce4588",
    "best_true_reduced_cost": -1.622126,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 17,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 29,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 3.260932,
    "cell_positive_count": 8,
    "cell_positive_rate": 0.533333,
    "cell_training_negative_count": 7,
    "certificate_effect": false,
    "context_hash": "84ae11479ed592d4",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.942568302154541,
    "decision_reason": "high_priority",
    "decision_record_index": 45,
    "existing_roi_target": false,
    "expected_context_hash": "84ae11479ed592d4",
    "forbidden_signature_hash": "cfbda5e70fc052f2",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 6,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_4_10",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|6",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "6321282f868e0007",
    "pool_task_set_hash": "f699ccb296afaee5",
    "positive_gap": 0,
    "positive_gap_weight": 6.266667,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.533333,
    "sample_path": "samples/sample_000045.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 3.949768,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json.jsonl",
    "source_row_index": 45,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->17:low_risk:2",
      "17->11:low_time:0",
      "11->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.375,
    "target_priority_sequence": [
      13,
      17,
      11
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      13,
      17,
      11,
      4,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->17:low_risk:2",
          "17->11:low_time:0",
          "11->0:low_risk:2"
        ],
        "sequence": [
          13,
          17,
          11
        ],
        "start_time": 19.222023
      },
      {
        "arc_option_sequence": [
          "0->4:low_time:0",
          "4->10:low_risk:2",
          "10->0:low_time:0"
        ],
        "sequence": [
          4,
          10
        ],
        "start_time": 279.592641
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      4,
      10,
      11,
      13,
      17
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "a5dfa0099f5679ed",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "7639b6652856b577",
    "best_true_reduced_cost": -0.631375,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 21,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 7,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 3.260932,
    "cell_positive_count": 8,
    "cell_positive_rate": 0.533333,
    "cell_training_negative_count": 7,
    "certificate_effect": false,
    "context_hash": "39d7643d5a478407",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9698616862297058,
    "decision_reason": "high_priority",
    "decision_record_index": 58,
    "existing_roi_target": false,
    "expected_context_hash": "39d7643d5a478407",
    "forbidden_signature_hash": "e6b5e61118e78a0b",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 7,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_39d7643d5a478407_7_14_3_5",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|7",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "3ba0638653a59e8e",
    "pool_task_set_hash": "06278cc81bec04c9",
    "positive_gap": 0,
    "positive_gap_weight": 6.266667,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.533333,
    "sample_path": "samples/sample_000058.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 3.927524,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave04/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json.jsonl",
    "source_row_index": 58,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->7:low_time:0",
      "7->14:low_time:0",
      "14->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      7,
      14
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      7,
      14,
      3,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->7:low_time:0",
          "7->14:low_time:0",
          "14->0:low_risk:2"
        ],
        "sequence": [
          7,
          14
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->5:low_risk:1",
          "5->0:low_risk:2"
        ],
        "sequence": [
          3,
          5
        ],
        "start_time": 296.326085
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      3,
      5,
      7,
      14
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "2ff601b483978496",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "d9a28376789baaec",
    "best_true_reduced_cost": -0.546964,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 20,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 5,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 3.260932,
    "cell_positive_count": 8,
    "cell_positive_rate": 0.533333,
    "cell_training_negative_count": 7,
    "certificate_effect": false,
    "context_hash": "4c81d9ecf77097c9",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9316824674606323,
    "decision_reason": "high_priority",
    "decision_record_index": 48,
    "existing_roi_target": false,
    "expected_context_hash": "4c81d9ecf77097c9",
    "forbidden_signature_hash": "72e4076e648b8514",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 6,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_3_13_17_8_4_10",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|6",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "c387cec8e60241d1",
    "pool_task_set_hash": "ee499f80528aeea9",
    "positive_gap": 0,
    "positive_gap_weight": 6.266667,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.533333,
    "sample_path": "samples/sample_000048.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 3.885124,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json.jsonl",
    "source_row_index": 48,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->3:low_risk:1",
      "3->13:low_risk:2",
      "13->17:low_risk:2",
      "17->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.571428571,
    "target_priority_sequence": [
      3,
      13,
      17
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      3,
      13,
      17,
      8,
      4,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_risk:1",
          "3->13:low_risk:2",
          "13->17:low_risk:2",
          "17->0:low_risk:2"
        ],
        "sequence": [
          3,
          13,
          17
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->4:low_time:0",
          "4->10:low_time:0",
          "10->0:low_energy:1"
        ],
        "sequence": [
          8,
          4,
          10
        ],
        "start_time": 227.873491
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      3,
      4,
      8,
      10,
      13,
      17
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "7e4b750a4d705954",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "3ca14dba75894c6f",
    "best_true_reduced_cost": -13.4341552,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 7,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 47,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 0.770377,
    "cell_positive_count": 4,
    "cell_positive_rate": 0.25,
    "cell_training_negative_count": 11,
    "certificate_effect": false,
    "context_hash": "1fa17aea2063098d",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9293051362037659,
    "decision_reason": "high_priority",
    "decision_record_index": 13,
    "existing_roi_target": false,
    "expected_context_hash": "1fa17aea2063098d",
    "forbidden_signature_hash": "5559157b1af629c3",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 3,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|apollo15_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "8a1916cc5ebaa441",
    "pool_task_set_hash": "961b82b5eee8dfe0",
    "positive_gap": 0,
    "positive_gap_weight": 4.0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.25,
    "sample_path": "samples/sample_000013.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 3.428051,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json.jsonl",
    "source_row_index": 13,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->4:low_time:0",
      "4->0:low_risk:1"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.428571429,
    "target_priority_sequence": [
      4
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      4,
      12,
      15,
      6,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_time:0",
          "4->0:low_risk:1"
        ],
        "sequence": [
          4
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->12:low_risk:2",
          "12->15:low_risk:2",
          "15->6:low_risk:2",
          "6->11:low_risk:2",
          "11->0:low_risk:2"
        ],
        "sequence": [
          12,
          15,
          6,
          11
        ],
        "start_time": 253.641299
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      4,
      6,
      11,
      12,
      15
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "09d58d42a46b577b",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  }
]
```

## 结论

- 正 ROI 高度集中，不能按 rc 或 HIGH 数量盲目采样；
- 每个 family/region cell 都需要正负样本平衡；
- 候选推荐只用于下一批 audit-only A/B，不允许默认启用 worker；
- GAT/kNN/OOD 仍不能证书，不能产生 official lower bound。
