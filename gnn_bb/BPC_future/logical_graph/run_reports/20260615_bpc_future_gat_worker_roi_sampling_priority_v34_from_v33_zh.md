# GAT Worker ROI Sampling Priority Audit 报告

日期：2026-06-15

## 目的

根据已有 target-priority worker ROI 标签，找出下一批最值得采样的
family/region/ordinal cell。该流程只读现有 JSON/JSONL，不运行 BPC、
pricing、RMP、worker，也不产生证书或 official bound。

## 机器字段

```text
gat_worker_roi_sampling_priority = current
row_count = 205
candidate_count = 42
recommendation_count = 24
max_per_cell = 6
roi_class_counts = {'columns_only_roi': 11, 'negative_primal_roi': 37, 'negative_retry_roi': 50, 'no_observed_roi': 48, 'positive_primal_roi': 46, 'positive_retry_roi': 13}
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
    "positive_rate": 0.3695652173913043,
    "roi_class_counts": {
      "columns_only_roi": 1,
      "negative_primal_roi": 7,
      "negative_retry_roi": 13,
      "no_observed_roi": 8,
      "positive_primal_roi": 15,
      "positive_retry_roi": 2
    },
    "row_count": 46,
    "training_negative_count": 28,
    "unsupported_count": 1
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
    "avg_positive_primal_improvement": 1.5484922000000096,
    "key": [
      "random-wave",
      "apollo15_20km"
    ],
    "positive_count": 5,
    "positive_rate": 0.2,
    "roi_class_counts": {
      "columns_only_roi": 3,
      "negative_primal_roi": 6,
      "negative_retry_roi": 4,
      "no_observed_roi": 7,
      "positive_primal_roi": 1,
      "positive_retry_roi": 4
    },
    "row_count": 25,
    "training_negative_count": 17,
    "unsupported_count": 3
  },
  "random-wave|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 4.6900210000000015,
    "key": [
      "random-wave",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 4,
    "positive_rate": 0.13333333333333333,
    "roi_class_counts": {
      "columns_only_roi": 2,
      "negative_primal_roi": 7,
      "negative_retry_roi": 8,
      "no_observed_roi": 9,
      "positive_primal_roi": 4
    },
    "row_count": 30,
    "training_negative_count": 24,
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
    "positive_gap": 8,
    "positive_rate": 0.13333333333333333,
    "row_count": 30
  },
  {
    "avg_positive_primal_improvement": 1.5484922000000096,
    "cell": "random-wave|apollo15_20km",
    "negative_gap": 0,
    "positive_gap": 7,
    "positive_rate": 0.2,
    "row_count": 25
  },
  {
    "avg_positive_primal_improvement": 12.151140899999996,
    "cell": "sector-wave|apollo15_20km",
    "negative_gap": 0,
    "positive_gap": 2,
    "positive_rate": 0.2777777777777778,
    "row_count": 36
  },
  {
    "avg_positive_primal_improvement": 4.2956621818181535,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "negative_gap": 0,
    "positive_gap": 1,
    "positive_rate": 0.3333333333333333,
    "row_count": 33
  }
]
```

## Recommendations

```json
[
  {
    "active_hash_before": "3341a4ba541bfa32",
    "best_true_reduced_cost": -6.934057667,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 9,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 24,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 1.548492,
    "cell_positive_count": 5,
    "cell_positive_rate": 0.2,
    "cell_training_negative_count": 17,
    "certificate_effect": false,
    "context_hash": "62c86745ed2b3aaa",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.6070942282676697,
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
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_1_10",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "ordinal_positive_rate": 0.5,
    "pool_signature_hash": "50dc555c1757eeca",
    "pool_task_set_hash": "fdf2e77ba9b76816",
    "positive_gap": 7,
    "positive_gap_weight": 6.0,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.5,
    "sample_path": "samples/sample_000013.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 45.708646,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "source_row_index": 13,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->1:low_risk:2",
      "1->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.333333333,
    "target_priority_sequence": [
      1
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      1,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->1:low_risk:2",
          "1->0:low_time:0"
        ],
        "sequence": [
          1
        ],
        "start_time": 57.409177
      },
      {
        "arc_option_sequence": [
          "0->10:low_time:0",
          "10->0:low_risk:2"
        ],
        "sequence": [
          10
        ],
        "start_time": 174.386986
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      10
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 2,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "9bd9a1d18b7a5cf5",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "eb92a6a521734d12",
    "best_true_reduced_cost": -1.716841,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 7,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 3,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 1.548492,
    "cell_positive_count": 5,
    "cell_positive_rate": 0.2,
    "cell_training_negative_count": 17,
    "certificate_effect": false,
    "context_hash": "409f65576794fa39",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.9787089824676514,
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
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "ordinal_positive_rate": 0.5,
    "pool_signature_hash": "61505b62c0f9a4a1",
    "pool_task_set_hash": "bba64460221b3547",
    "positive_gap": 7,
    "positive_gap_weight": 6.0,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.5,
    "sample_path": "samples/sample_000012.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 44.8194,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "source_row_index": 12,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->20:low_risk:2",
      "20->0:low_risk:2"
    ],
    "target_impact_bucket": "replacement_like",
    "target_max_active_jaccard": 1.0,
    "target_priority_sequence": [
      8,
      20
    ],
    "target_replacement_like_proxy": true,
    "target_sequence": [
      8,
      20
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->20:low_risk:2",
          "20->0:low_risk:2"
        ],
        "sequence": [
          8,
          20
        ],
        "start_time": 0.0
      }
    ],
    "target_support_changing_proxy": false,
    "target_task_set": [
      8,
      20
    ],
    "target_task_set_in_active": true,
    "target_task_set_in_pool": true,
    "target_task_set_new": false,
    "target_task_set_size": 2,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "efc2fb20ceb858b3",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "03a8d149c5bdfc16",
    "best_true_reduced_cost": -0.97526,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 10,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 3,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 1.548492,
    "cell_positive_count": 5,
    "cell_positive_rate": 0.2,
    "cell_training_negative_count": 17,
    "certificate_effect": false,
    "context_hash": "3100b787bf438dfe",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.30074623227119446,
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
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_6",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "ordinal_positive_rate": 0.5,
    "pool_signature_hash": "7a249193fdd37789",
    "pool_task_set_hash": "e3f049a263f86c82",
    "positive_gap": 7,
    "positive_gap_weight": 6.0,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.5,
    "sample_path": "samples/sample_000014.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 44.604358,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "source_row_index": 14,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->2:low_risk:2",
      "2->4:low_risk:2",
      "4->11:low_risk:2",
      "11->6:low_risk:2",
      "6->0:low_risk:2"
    ],
    "target_impact_bucket": "new_task_set",
    "target_max_active_jaccard": 0.714285714,
    "target_priority_sequence": [
      5,
      1,
      2,
      4,
      11,
      6
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      5,
      1,
      2,
      4,
      11,
      6
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->1:low_risk:2",
          "1->2:low_risk:2",
          "2->4:low_risk:2",
          "4->11:low_risk:2",
          "11->6:low_risk:2",
          "6->0:low_risk:2"
        ],
        "sequence": [
          5,
          1,
          2,
          4,
          11,
          6
        ],
        "start_time": 11.291563
      }
    ],
    "target_support_changing_proxy": false,
    "target_task_set": [
      1,
      2,
      4,
      5,
      6,
      11
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
    "active_hash_before": "05e452aa352874cd",
    "best_true_reduced_cost": -2.5206325,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 18,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 6,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 1.548492,
    "cell_positive_count": 5,
    "cell_positive_rate": 0.2,
    "cell_training_negative_count": 17,
    "certificate_effect": false,
    "context_hash": "9cb802808b9a3356",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.6089179515838623,
    "decision_reason": "knn_delay_fraction_delay_queue",
    "decision_record_index": 6,
    "existing_roi_target": false,
    "expected_context_hash": "9cb802808b9a3356",
    "forbidden_signature_hash": "c0b30757b93e2af2",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 6,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_9cb802808b9a3356_19_6_13",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|6",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "282d861529661f7c",
    "pool_task_set_hash": "c99ec5f484dca958",
    "positive_gap": 7,
    "positive_gap_weight": 3.6,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.2,
    "sample_path": "samples/sample_000006.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 27.689799,
    "source_candidate_file": "BPC_future/results/gat_same_run_random_wave_ord6_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord6_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json.jsonl",
    "source_row_index": 6,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->19:low_time:0",
      "19->6:low_risk:2",
      "6->13:low_risk:2",
      "13->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      19,
      6,
      13
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      19,
      6,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->19:low_time:0",
          "19->6:low_risk:2",
          "6->13:low_risk:2",
          "13->0:low_time:0"
        ],
        "sequence": [
          19,
          6,
          13
        ],
        "start_time": 0.0
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      6,
      13,
      19
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 3,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "91685c5bd22052ec",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "2b7d17df31de0a68",
    "best_true_reduced_cost": -1.532347,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 13,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 11,
    "cell": "random-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 1.548492,
    "cell_positive_count": 5,
    "cell_positive_rate": 0.2,
    "cell_training_negative_count": 17,
    "certificate_effect": false,
    "context_hash": "411d44c3e21bcb1f",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.5109930038452148,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 6,
    "existing_roi_target": false,
    "expected_context_hash": "411d44c3e21bcb1f",
    "forbidden_signature_hash": "2f591733ba3de3f1",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
    "instance_family": "random-wave",
    "instance_ordinal": 7,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_411d44c3e21bcb1f_17_18_9_5",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|apollo15_20km|7",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "be632cace8973051",
    "pool_task_set_hash": "bacd75bd93f71e9e",
    "positive_gap": 7,
    "positive_gap_weight": 3.6,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.2,
    "sample_path": "samples/sample_000006.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 27.54246,
    "source_candidate_file": "BPC_future/results/gat_same_run_random_wave_ord7_delay_candidates_task020_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord7_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_07_seed61612_logical_graph.json.jsonl",
    "source_row_index": 6,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->17:low_time:0",
      "17->18:low_risk:2",
      "18->9:low_time:0",
      "9->5:low_time:0",
      "5->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.4,
    "target_priority_sequence": [
      17,
      18,
      9,
      5
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      17,
      18,
      9,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->17:low_time:0",
          "17->18:low_risk:2",
          "18->9:low_time:0",
          "9->5:low_time:0",
          "5->0:low_risk:2"
        ],
        "sequence": [
          17,
          18,
          9,
          5
        ],
        "start_time": 0.0
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      5,
      9,
      17,
      18
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "0e4f804b68c2ee6d",
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
    "cell_avg_positive_primal_improvement": 1.548492,
    "cell_positive_count": 5,
    "cell_positive_rate": 0.2,
    "cell_training_negative_count": 17,
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
    "positive_gap": 7,
    "positive_gap_weight": 3.6,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.2,
    "sample_path": "samples/sample_000035.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 27.503868,
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
    "active_hash_before": "7ecd36ca50af55f8",
    "best_true_reduced_cost": -34.609111,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 3,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 49,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 4,
    "cell_positive_rate": 0.133333,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "da555dc83edc174c",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9998178482055664,
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
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_5_16_1",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|10",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "abbfed8882abbb97",
    "pool_task_set_hash": "fec52a4ed3d6375b",
    "positive_gap": 8,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.133333,
    "sample_path": "samples/sample_000037.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 24.599275,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json.jsonl",
    "source_row_index": 37,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->5:low_energy:1",
      "5->16:low_energy:1",
      "16->1:low_time:0",
      "1->0:low_energy:1"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.25,
    "target_priority_sequence": [
      5,
      16,
      1
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      5,
      16,
      1
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_energy:1",
          "5->16:low_energy:1",
          "16->1:low_time:0",
          "1->0:low_energy:1"
        ],
        "sequence": [
          5,
          16,
          1
        ],
        "start_time": 53.794396
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      5,
      16
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 3,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "4197690e912b9c36",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "51df5d79e9ac45ae",
    "best_true_reduced_cost": -18.3447928,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 4,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 49,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 4,
    "cell_positive_rate": 0.133333,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "08b8d772e2ab9623",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9475746154785156,
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
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_10_11",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "07ce45c4b7ea1c45",
    "pool_task_set_hash": "ba7679f84bbb38ae",
    "positive_gap": 8,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.133333,
    "sample_path": "samples/sample_000018.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 23.733816,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "source_row_index": 18,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->10:low_time:0",
      "10->11:low_time:0",
      "11->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.333333333,
    "target_priority_sequence": [
      10,
      11
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      10,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->10:low_time:0",
          "10->11:low_time:0",
          "11->0:low_risk:2"
        ],
        "sequence": [
          10,
          11
        ],
        "start_time": 0.0
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      10,
      11
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 2,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "c923eda9f0bcc8d2",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "86d9789a5b8352f0",
    "best_true_reduced_cost": -24.6125642,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 5,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 4,
    "cell_positive_rate": 0.133333,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "ec59d1f203f1630c",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9997891187667847,
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
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_12_5_8",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|10",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "b22e9d42681f1d67",
    "pool_task_set_hash": "c400b3d02d0fc424",
    "positive_gap": 8,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.133333,
    "sample_path": "samples/sample_000038.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 23.599419,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json.jsonl",
    "source_row_index": 38,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->0:low_risk:2"
    ],
    "target_impact_bucket": "new_task_set",
    "target_max_active_jaccard": 0.666666667,
    "target_priority_sequence": [
      12
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      12,
      5,
      8
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_time:0",
          "12->0:low_risk:2"
        ],
        "sequence": [
          12
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->5:low_energy:1",
          "5->8:low_time:0",
          "8->0:low_energy:1"
        ],
        "sequence": [
          5,
          8
        ],
        "start_time": 123.356368
      }
    ],
    "target_support_changing_proxy": false,
    "target_task_set": [
      5,
      8,
      12
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 3,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "e408b632cdf39f5e",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "622200ad1fc583cc",
    "best_true_reduced_cost": -21.7627212,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 5,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 4,
    "cell_positive_rate": 0.133333,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "e897b76f2888f822",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9772281050682068,
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
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_10_11_14_9",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "cbd4c17130829b87",
    "pool_task_set_hash": "71fc2cca8fb5ace4",
    "positive_gap": 8,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.133333,
    "sample_path": "samples/sample_000019.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 23.434366,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "source_row_index": 19,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->10:low_time:0",
      "10->11:low_time:0",
      "11->0:low_risk:2"
    ],
    "target_impact_bucket": "new_task_set",
    "target_max_active_jaccard": 0.75,
    "target_priority_sequence": [
      10,
      11
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      10,
      11,
      14,
      9
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->10:low_time:0",
          "10->11:low_time:0",
          "11->0:low_risk:2"
        ],
        "sequence": [
          10,
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
        "start_time": 299.342015
      }
    ],
    "target_support_changing_proxy": false,
    "target_task_set": [
      9,
      10,
      11,
      14
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
    "active_hash_before": "950498a3c24cb589",
    "best_true_reduced_cost": -17.309346667,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 11,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 28,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 4,
    "cell_positive_rate": 0.133333,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "7cb380a02e30e5a8",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.5416556596755981,
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
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_09_seed61820_7cb380a02e30e5a8_14_6_7",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|9",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "7ef6419dc8239cb4",
    "pool_task_set_hash": "dad9d51aaf8ae5e1",
    "positive_gap": 8,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.133333,
    "sample_path": "samples/sample_000024.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 23.276125,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json.jsonl",
    "source_row_index": 24,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      14
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      14,
      6,
      7
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->14:low_risk:2",
          "14->0:low_risk:2"
        ],
        "sequence": [
          14
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->6:low_time:0",
          "6->7:low_risk:2",
          "7->0:low_risk:2"
        ],
        "sequence": [
          6,
          7
        ],
        "start_time": 271.117057
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      6,
      7,
      14
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 3,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "51702c3dec001ab6",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "c1dd396614b6fcc3",
    "best_true_reduced_cost": -5.669367,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 18,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 30,
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 4.690021,
    "cell_positive_count": 4,
    "cell_positive_rate": 0.133333,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "a77e5457bde80b8e",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.8371341228485107,
    "decision_reason": "below_threshold_delay_queue",
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
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_18_4_3_13",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|8",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "b7bd078f29df934d",
    "pool_task_set_hash": "4c99b33b1ffe8829",
    "positive_gap": 8,
    "positive_gap_weight": 2.5,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.133333,
    "sample_path": "samples/sample_000021.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 22.989605,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json.jsonl",
    "source_row_index": 21,
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
      3,
      13
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
          "0->3:low_risk:2",
          "3->13:low_risk:2",
          "13->0:low_risk:2"
        ],
        "sequence": [
          3,
          13
        ],
        "start_time": 345.431386
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      3,
      4,
      13,
      18
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "d2ea374c6f1b01b2",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "4cc24e29b5b5bc64",
    "best_true_reduced_cost": -1.3332575,
    "branch_hash": "da39a3ee5e6b4b0d",
    "capture_cg_iter": 26,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 15,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 12.151141,
    "cell_positive_count": 10,
    "cell_positive_rate": 0.277778,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "43dcab2f9dde0fc6",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.8698002099990845,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 8,
    "existing_roi_target": false,
    "expected_context_hash": "43dcab2f9dde0fc6",
    "forbidden_signature_hash": "d70b88300dacc227",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 2,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_43dcab2f9dde0fc6_20_7_14_13_11_4_17",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|apollo15_20km|2",
    "ordinal_positive_rate": 0.5,
    "pool_signature_hash": "2aa70182537b5744",
    "pool_task_set_hash": "99618ce9f91e5c3b",
    "positive_gap": 2,
    "positive_gap_weight": 6.0,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.5,
    "sample_path": "samples/sample_000008.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 15.984911,
    "source_candidate_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json.jsonl",
    "source_row_index": 8,
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->7:low_risk:1",
      "7->14:low_time:0",
      "14->0:low_risk:2"
    ],
    "target_priority_sequence": [
      20,
      7,
      14
    ],
    "target_sequence": [
      20,
      7,
      14,
      13,
      11,
      4,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_risk:2",
          "20->7:low_risk:1",
          "7->14:low_time:0",
          "14->0:low_risk:2"
        ],
        "sequence": [
          20,
          7,
          14
        ],
        "start_time": 12.274109
      },
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->11:low_time:0",
          "11->4:low_risk:1",
          "4->17:low_risk:2",
          "17->0:low_risk:2"
        ],
        "sequence": [
          13,
          11,
          4,
          17
        ],
        "start_time": 326.644296
      }
    ],
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "803930670c9b7c3e",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "9b65d1ccd219057e",
    "best_true_reduced_cost": -0.015125,
    "branch_hash": "da39a3ee5e6b4b0d",
    "capture_cg_iter": 27,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 4,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 12.151141,
    "cell_positive_count": 10,
    "cell_positive_rate": 0.277778,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "c97a1cf4f842dd6c",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.8714934587478638,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 9,
    "existing_roi_target": false,
    "expected_context_hash": "c97a1cf4f842dd6c",
    "forbidden_signature_hash": "bbe4d9823521bc46",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 2,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c97a1cf4f842dd6c_3_5_11_4_2",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|apollo15_20km|2",
    "ordinal_positive_rate": 0.5,
    "pool_signature_hash": "7b871b6ac0a97331",
    "pool_task_set_hash": "e6cfea636ca0ef92",
    "positive_gap": 2,
    "positive_gap_weight": 6.0,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.5,
    "sample_path": "samples/sample_000009.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 15.920697,
    "source_candidate_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json.jsonl",
    "source_row_index": 9,
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->5:low_risk:2",
      "5->0:low_risk:2"
    ],
    "target_priority_sequence": [
      3,
      5
    ],
    "target_sequence": [
      3,
      5,
      11,
      4,
      2
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          3,
          5
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->11:low_risk:2",
          "11->4:low_risk:1",
          "4->2:low_risk:1",
          "2->0:low_risk:2"
        ],
        "sequence": [
          11,
          4,
          2
        ],
        "start_time": 307.81881
      }
    ],
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "d8913862cdbef9fc",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "3448ff27bd84701d",
    "best_true_reduced_cost": -0.083721,
    "branch_hash": "da39a3ee5e6b4b0d",
    "capture_cg_iter": 28,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 1,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 12.151141,
    "cell_positive_count": 10,
    "cell_positive_rate": 0.277778,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "d66c7e548fe94bd5",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.8606614470481873,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 10,
    "existing_roi_target": false,
    "expected_context_hash": "d66c7e548fe94bd5",
    "forbidden_signature_hash": "503c2e9e52dc6c05",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 2,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_d66c7e548fe94bd5_12_2_8_10_17",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|apollo15_20km|2",
    "ordinal_positive_rate": 0.5,
    "pool_signature_hash": "610f643bbe1c48e2",
    "pool_task_set_hash": "e6cfea636ca0ef92",
    "positive_gap": 2,
    "positive_gap_weight": 6.0,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.5,
    "sample_path": "samples/sample_000010.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 15.913295,
    "source_candidate_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json.jsonl",
    "source_row_index": 10,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->0:low_risk:2"
    ],
    "target_priority_sequence": [
      12
    ],
    "target_sequence": [
      12,
      2,
      8,
      10,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_risk:2",
          "12->0:low_risk:2"
        ],
        "sequence": [
          12
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->2:low_risk:2",
          "2->8:low_risk:1",
          "8->10:low_risk:2",
          "10->17:low_risk:1",
          "17->0:low_risk:2"
        ],
        "sequence": [
          2,
          8,
          10,
          17
        ],
        "start_time": 274.382116
      }
    ],
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "c20643a988836b9c",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "3ca14dba75894c6f",
    "best_true_reduced_cost": -23.2995114,
    "branch_hash": "da39a3ee5e6b4b0d",
    "capture_cg_iter": 7,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 47,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 12.151141,
    "cell_positive_count": 10,
    "cell_positive_rate": 0.277778,
    "cell_training_negative_count": 24,
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
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_6_20_11",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|apollo15_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "8a1916cc5ebaa441",
    "pool_task_set_hash": "961b82b5eee8dfe0",
    "positive_gap": 2,
    "positive_gap_weight": 4.222222,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.277778,
    "sample_path": "samples/sample_000013.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 12.587173,
    "source_candidate_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json.jsonl",
    "source_row_index": 13,
    "target_arc_option_sequence": [
      "0->4:low_time:0",
      "4->0:low_time:0"
    ],
    "target_priority_sequence": [
      4
    ],
    "target_sequence": [
      4,
      6,
      20,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_time:0",
          "4->0:low_time:0"
        ],
        "sequence": [
          4
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->6:low_risk:2",
          "6->20:low_time:0",
          "20->11:low_time:0",
          "11->0:low_risk:2"
        ],
        "sequence": [
          6,
          20,
          11
        ],
        "start_time": 240.88539
      }
    ],
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "09d58d42a46b577b",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "13107ac7c4d480c2",
    "best_true_reduced_cost": -22.979615,
    "branch_hash": "da39a3ee5e6b4b0d",
    "capture_cg_iter": 5,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 12.151141,
    "cell_positive_count": 10,
    "cell_positive_rate": 0.277778,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "fec7e16a3758171c",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.811603844165802,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 12,
    "existing_roi_target": false,
    "expected_context_hash": "fec7e16a3758171c",
    "forbidden_signature_hash": "fdaffe3cde3b498f",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 3,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_fec7e16a3758171c_13_5_12_10",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|apollo15_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "d1ce044825e59261",
    "pool_task_set_hash": "5c04e222ccbca69f",
    "positive_gap": 2,
    "positive_gap_weight": 4.222222,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.277778,
    "sample_path": "samples/sample_000012.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 12.453476,
    "source_candidate_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json.jsonl",
    "source_row_index": 12,
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->5:low_risk:2",
      "5->12:low_risk:2",
      "12->10:low_risk:2",
      "10->0:low_risk:2"
    ],
    "target_priority_sequence": [
      13,
      5,
      12,
      10
    ],
    "target_sequence": [
      13,
      5,
      12,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->5:low_risk:2",
          "5->12:low_risk:2",
          "12->10:low_risk:2",
          "10->0:low_risk:2"
        ],
        "sequence": [
          13,
          5,
          12,
          10
        ],
        "start_time": 0.0
      }
    ],
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "b3a964e273809348",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "da3932a04297ce01",
    "best_true_reduced_cost": -2.835253,
    "branch_hash": "da39a3ee5e6b4b0d",
    "capture_cg_iter": 8,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 10,
    "cell": "sector-wave|apollo15_20km",
    "cell_avg_positive_primal_improvement": 12.151141,
    "cell_positive_count": 10,
    "cell_positive_rate": 0.277778,
    "cell_training_negative_count": 24,
    "certificate_effect": false,
    "context_hash": "19758e70e56ed7e7",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.8299528956413269,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 14,
    "existing_roi_target": false,
    "expected_context_hash": "19758e70e56ed7e7",
    "forbidden_signature_hash": "90773505d87758ac",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 3,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_19758e70e56ed7e7_13_3_19_7",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|apollo15_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "5aeac7911c50e0dc",
    "pool_task_set_hash": "e9b74f32d120ab0d",
    "positive_gap": 2,
    "positive_gap_weight": 4.222222,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.277778,
    "sample_path": "samples/sample_000014.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 11.464607,
    "source_candidate_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json.jsonl",
    "source_row_index": 14,
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_priority_sequence": [
      13
    ],
    "target_sequence": [
      13,
      3,
      19,
      7
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
          "0->3:low_time:0",
          "3->19:low_risk:2",
          "19->7:low_risk:2",
          "7->0:low_risk:2"
        ],
        "sequence": [
          3,
          19,
          7
        ],
        "start_time": 115.963142
      }
    ],
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "6ac906efca5737d6",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "e5d989275b12a554",
    "best_true_reduced_cost": -0.205245,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 16,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 43,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.730554,
    "cell_positive_count": 17,
    "cell_positive_rate": 0.369565,
    "cell_training_negative_count": 28,
    "certificate_effect": false,
    "context_hash": "453b7d680cd04697",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8901892900466919,
    "decision_reason": "high_priority",
    "decision_record_index": 44,
    "existing_roi_target": false,
    "expected_context_hash": "453b7d680cd04697",
    "forbidden_signature_hash": "0287e5c37b46ec43",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 6,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_453b7d680cd04697_2_13_11_12_14_18",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|6",
    "ordinal_positive_rate": 0.25,
    "pool_signature_hash": "da52482a46dee291",
    "pool_task_set_hash": "4cc07b9527a8442e",
    "positive_gap": 0,
    "positive_gap_weight": 4.956522,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.369565,
    "sample_path": "samples/sample_000044.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 3.782203,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json.jsonl",
    "source_row_index": 44,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.571428571,
    "target_priority_sequence": [
      2,
      13
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      2,
      13,
      11,
      12,
      14,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_risk:2",
          "2->13:low_risk:2",
          "13->0:low_risk:2"
        ],
        "sequence": [
          2,
          13
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->11:low_risk:2",
          "11->12:low_risk:2",
          "12->14:low_energy:1",
          "14->18:low_time:0",
          "18->0:low_risk:2"
        ],
        "sequence": [
          11,
          12,
          14,
          18
        ],
        "start_time": 136.354496
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      2,
      11,
      12,
      13,
      14,
      18
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "7c0ee4cff79aa555",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "d9c2b511b8c9398b",
    "best_true_reduced_cost": -0.182861,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 18,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 1,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.730554,
    "cell_positive_count": 17,
    "cell_positive_rate": 0.369565,
    "cell_training_negative_count": 28,
    "certificate_effect": false,
    "context_hash": "370fd4c047e0a42c",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.8112690448760986,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 46,
    "existing_roi_target": false,
    "expected_context_hash": "370fd4c047e0a42c",
    "forbidden_signature_hash": "e5a442a3d8d78d2e",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 6,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_370fd4c047e0a42c_3_2_9_6",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|6",
    "ordinal_positive_rate": 0.25,
    "pool_signature_hash": "ebcd0be23e73ec7f",
    "pool_task_set_hash": "791323a96cf45e2d",
    "positive_gap": 0,
    "positive_gap_weight": 4.956522,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.369565,
    "sample_path": "samples/sample_000046.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 3.702163,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json.jsonl",
    "source_row_index": 46,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->2:low_risk:2",
      "2->9:low_time:0",
      "9->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.6,
    "target_priority_sequence": [
      3,
      2,
      9
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      3,
      2,
      9,
      6
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->2:low_risk:2",
          "2->9:low_time:0",
          "9->0:low_time:0"
        ],
        "sequence": [
          3,
          2,
          9
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->6:low_risk:2",
          "6->0:low_time:0"
        ],
        "sequence": [
          6
        ],
        "start_time": 277.996588
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      2,
      3,
      6,
      9
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "51d177f1ededb626",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "0780f9f032c659a7",
    "best_true_reduced_cost": -13.304471556,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 16,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 24,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.730554,
    "cell_positive_count": 17,
    "cell_positive_rate": 0.369565,
    "cell_training_negative_count": 28,
    "certificate_effect": false,
    "context_hash": "22dec9cfc13bb3d6",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9586074948310852,
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
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_5_20_3",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|8",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "b8aa00efb6e169f6",
    "pool_task_set_hash": "a98072364d0bfc1e",
    "positive_gap": 0,
    "positive_gap_weight": 4.956522,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.369565,
    "sample_path": "samples/sample_000059.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 3.505582,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave04/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json.jsonl",
    "source_row_index": 59,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->20:low_risk:1",
      "20->0:low_risk:1"
    ],
    "target_impact_bucket": "new_task_set",
    "target_max_active_jaccard": 0.666666667,
    "target_priority_sequence": [
      5,
      20
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      5,
      20,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->20:low_risk:1",
          "20->0:low_risk:1"
        ],
        "sequence": [
          5,
          20
        ],
        "start_time": 43.068364
      },
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->0:low_risk:2"
        ],
        "sequence": [
          3
        ],
        "start_time": 290.731573
      }
    ],
    "target_support_changing_proxy": false,
    "target_task_set": [
      3,
      5,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 3,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "f41cb57ae52a541e",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "4799ece3f3778c1d",
    "best_true_reduced_cost": -0.087484909,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 20,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 1,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.730554,
    "cell_positive_count": 17,
    "cell_positive_rate": 0.369565,
    "cell_training_negative_count": 28,
    "certificate_effect": false,
    "context_hash": "165e10ca9c212e34",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.945199728012085,
    "decision_reason": "knn_delay_fraction_delay_queue",
    "decision_record_index": 61,
    "existing_roi_target": false,
    "expected_context_hash": "165e10ca9c212e34",
    "forbidden_signature_hash": "bc6c99de1633c549",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 8,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_165e10ca9c212e34_12_15_6_19",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|8",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "68a7c626fa03980d",
    "pool_task_set_hash": "8df343753a026328",
    "positive_gap": 0,
    "positive_gap_weight": 4.956522,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.369565,
    "sample_path": "samples/sample_000061.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 3.331325,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave04/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json.jsonl",
    "source_row_index": 61,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->15:low_time:0",
      "15->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.6,
    "target_priority_sequence": [
      12,
      15
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      12,
      15,
      6,
      19
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_risk:2",
          "12->15:low_time:0",
          "15->0:low_time:0"
        ],
        "sequence": [
          12,
          15
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->6:low_time:0",
          "6->19:low_time:0",
          "19->0:low_risk:2"
        ],
        "sequence": [
          6,
          19
        ],
        "start_time": 410.34574
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      6,
      12,
      15,
      19
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "933a95bfc92ef7b3",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "517ef99313f19406",
    "best_true_reduced_cost": -0.002873,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "best_rc",
    "capture_cg_iter": 21,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 6,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.730554,
    "cell_positive_count": 17,
    "cell_positive_rate": 0.369565,
    "cell_training_negative_count": 28,
    "certificate_effect": false,
    "context_hash": "26b1956faca276a4",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9290037751197815,
    "decision_reason": "high_priority",
    "decision_record_index": 49,
    "existing_roi_target": false,
    "expected_context_hash": "26b1956faca276a4",
    "forbidden_signature_hash": "3c1ca0479a0423a8",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 6,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_1_8_4",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|6",
    "ordinal_positive_rate": 0.25,
    "pool_signature_hash": "a680790d9f31e526",
    "pool_task_set_hash": "f0c4222586112e82",
    "positive_gap": 0,
    "positive_gap_weight": 4.956522,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.369565,
    "sample_path": "samples/sample_000049.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 3.310898,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json.jsonl",
    "source_row_index": 49,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->3:low_risk:1",
      "3->0:low_risk:1"
    ],
    "target_impact_bucket": "new_task_set",
    "target_max_active_jaccard": 0.75,
    "target_priority_sequence": [
      3
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      3,
      1,
      8,
      4
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_risk:1",
          "3->0:low_risk:1"
        ],
        "sequence": [
          3
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->1:low_time:0",
          "1->8:low_risk:2",
          "8->4:low_time:0",
          "4->0:low_time:0"
        ],
        "sequence": [
          1,
          8,
          4
        ],
        "start_time": 147.079424
      }
    ],
    "target_support_changing_proxy": false,
    "target_task_set": [
      1,
      3,
      4,
      8
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "7351bac64f33621b",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "517ef99313f19406",
    "best_true_reduced_cost": -0.002873,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 21,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 6,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 2.730554,
    "cell_positive_count": 17,
    "cell_positive_rate": 0.369565,
    "cell_training_negative_count": 28,
    "certificate_effect": false,
    "context_hash": "26b1956faca276a4",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9242444634437561,
    "decision_reason": "high_priority",
    "decision_record_index": 49,
    "existing_roi_target": false,
    "expected_context_hash": "26b1956faca276a4",
    "forbidden_signature_hash": "3c1ca0479a0423a8",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 6,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_13_17_11_12_14_18",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|6",
    "ordinal_positive_rate": 0.25,
    "pool_signature_hash": "a680790d9f31e526",
    "pool_task_set_hash": "f0c4222586112e82",
    "positive_gap": 0,
    "positive_gap_weight": 4.956522,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.369565,
    "sample_path": "samples/sample_000049.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 3.306139,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json.jsonl",
    "source_row_index": 49,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->3:low_risk:1",
      "3->0:low_risk:1"
    ],
    "target_impact_bucket": "new_task_set",
    "target_max_active_jaccard": 1.0,
    "target_priority_sequence": [
      3
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      3,
      13,
      17,
      11,
      12,
      14,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_risk:1",
          "3->0:low_risk:1"
        ],
        "sequence": [
          3
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->13:low_time:0",
          "13->17:low_time:0",
          "17->11:low_risk:2",
          "11->12:low_time:0",
          "12->14:low_energy:1",
          "14->18:low_risk:2",
          "18->0:low_time:0"
        ],
        "sequence": [
          13,
          17,
          11,
          12,
          14,
          18
        ],
        "start_time": 69.943499
      }
    ],
    "target_support_changing_proxy": false,
    "target_task_set": [
      3,
      11,
      12,
      13,
      14,
      17,
      18
    ],
    "target_task_set_in_active": true,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 7,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "7351bac64f33621b",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  }
]
```

## 结论

- 正 ROI 高度集中，不能按 rc 或 HIGH 数量盲目采样；
- 每个 family/region cell 都需要正负样本平衡；
- 候选推荐只用于下一批 audit-only A/B，不允许默认启用 worker；
- GAT/kNN/OOD 仍不能证书，不能产生 official lower bound。
