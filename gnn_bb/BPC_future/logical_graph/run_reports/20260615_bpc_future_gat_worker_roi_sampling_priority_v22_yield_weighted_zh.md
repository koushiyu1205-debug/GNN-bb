# GAT Worker ROI Sampling Priority Audit 报告

日期：2026-06-15

## 目的

根据已有 target-priority worker ROI 标签，找出下一批最值得采样的
family/region/ordinal cell。该流程只读现有 JSON/JSONL，不运行 BPC、
pricing、RMP、worker，也不产生证书或 official bound。

## 机器字段

```text
gat_worker_roi_sampling_priority = current
row_count = 96
candidate_count = 35
recommendation_count = 16
max_per_cell = 4
roi_class_counts = {'columns_only_roi': 6, 'negative_primal_roi': 17, 'negative_retry_roi': 11, 'no_observed_roi': 38, 'positive_primal_roi': 21, 'positive_retry_roi': 3}
production_ready = false
certificate_ready = false
```

## Positive-rich cells

```json
{
  "greedy-anchor|apollo15_20km": {
    "avg_positive_primal_improvement": 3.464379666666673,
    "key": [
      "greedy-anchor",
      "apollo15_20km"
    ],
    "positive_count": 6,
    "positive_rate": 0.5,
    "roi_class_counts": {
      "negative_primal_roi": 1,
      "no_observed_roi": 5,
      "positive_primal_roi": 4,
      "positive_retry_roi": 2
    },
    "row_count": 12,
    "training_negative_count": 6,
    "unsupported_count": 0
  },
  "greedy-anchor|tranquillitatis_balmer_like_20km": {
    "avg_positive_primal_improvement": 33.391141249999976,
    "key": [
      "greedy-anchor",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 8,
    "positive_rate": 0.47058823529411764,
    "roi_class_counts": {
      "negative_primal_roi": 2,
      "negative_retry_roi": 5,
      "no_observed_roi": 2,
      "positive_primal_roi": 8
    },
    "row_count": 17,
    "training_negative_count": 9,
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
    "avg_positive_primal_improvement": 1.6661572499999977,
    "key": [
      "sector-wave",
      "tranquillitatis_balmer_like_20km"
    ],
    "positive_count": 4,
    "positive_rate": 0.25,
    "roi_class_counts": {
      "negative_primal_roi": 3,
      "no_observed_roi": 9,
      "positive_primal_roi": 3,
      "positive_retry_roi": 1
    },
    "row_count": 16,
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
    "active_hash_before": "7497860baf634782",
    "best_true_reduced_cost": -2.403075167,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 17,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 2,
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 33.391141,
    "cell_positive_count": 8,
    "cell_positive_rate": 0.470588,
    "cell_training_negative_count": 9,
    "certificate_effect": false,
    "context_hash": "048e5f66efcd12df",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "DELAY_QUEUE",
    "decision_probability": 0.7114976644515991,
    "decision_reason": "below_threshold_delay_queue",
    "decision_record_index": 63,
    "existing_roi_target": false,
    "expected_context_hash": "048e5f66efcd12df",
    "forbidden_signature_hash": "a9d74a61c4c73072",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 7,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|7",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "fd82c4ddd8b3be43",
    "pool_task_set_hash": "e717738ba4daed8d",
    "positive_gap": 0,
    "positive_gap_weight": 7.342583,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.667823,
    "sample_path": "samples/sample_000063.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 6.08253,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave04/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json.jsonl",
    "source_row_index": 63,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->10:low_risk:2",
      "10->0:low_risk:2"
    ],
    "target_impact_bucket": "new_task_set",
    "target_max_active_jaccard": 0.8,
    "target_priority_sequence": [
      2,
      10
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      2,
      10,
      19,
      9,
      1
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_risk:2",
          "2->10:low_risk:2",
          "10->0:low_risk:2"
        ],
        "sequence": [
          2,
          10
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->19:low_time:0",
          "19->9:low_risk:2",
          "9->0:low_time:0"
        ],
        "sequence": [
          19,
          9
        ],
        "start_time": 133.023545
      },
      {
        "arc_option_sequence": [
          "0->1:low_risk:2",
          "1->0:low_risk:2"
        ],
        "sequence": [
          1
        ],
        "start_time": 490.57921
      }
    ],
    "target_support_changing_proxy": false,
    "target_task_set": [
      1,
      2,
      9,
      10,
      19
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "0d0dc5ddf5fe17ee",
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
    "active_hash_before": "2c2e416db249f720",
    "best_true_reduced_cost": -27.31408425,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 3,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 1.666157,
    "cell_positive_count": 4,
    "cell_positive_rate": 0.25,
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
    "ordinal_positive_rate": 0.5,
    "pool_signature_hash": "eddad0807740a5f3",
    "pool_task_set_hash": "e1b494c430dfa84e",
    "positive_gap": 0,
    "positive_gap_weight": 6.0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.5,
    "sample_path": "samples/sample_000018.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.219445,
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
    "active_hash_before": "96c7c0766604244a",
    "best_true_reduced_cost": -26.5430824,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 4,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 49,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 1.666157,
    "cell_positive_count": 4,
    "cell_positive_rate": 0.25,
    "cell_training_negative_count": 12,
    "certificate_effect": false,
    "context_hash": "ac15bc4e7e3d6fff",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9569950699806213,
    "decision_reason": "high_priority",
    "decision_record_index": 19,
    "existing_roi_target": false,
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "forbidden_signature_hash": "16f38b9203fc0908",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 2,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|2",
    "ordinal_positive_rate": 0.5,
    "pool_signature_hash": "a3a808a977a593aa",
    "pool_task_set_hash": "393c147abf261db2",
    "positive_gap": 0,
    "positive_gap_weight": 6.0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.5,
    "sample_path": "samples/sample_000019.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 5.200765,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json.jsonl",
    "source_row_index": 19,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.4,
    "target_priority_sequence": [
      4
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      4,
      19,
      10,
      17
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
          "0->19:low_risk:2",
          "19->10:low_time:0",
          "10->17:low_risk:2",
          "17->0:low_time:0"
        ],
        "sequence": [
          19,
          10,
          17
        ],
        "start_time": 202.264867
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      4,
      10,
      17,
      19
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "b49472077fb42329",
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
    "active_hash_before": "d15d7fc02d890349",
    "best_true_reduced_cost": -4.926893429,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 55,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 2,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 3.46438,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.5,
    "cell_training_negative_count": 6,
    "certificate_effect": false,
    "context_hash": "7fcd171c2901efb5",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8824695348739624,
    "decision_reason": "high_priority",
    "decision_record_index": 30,
    "existing_roi_target": false,
    "expected_context_hash": "7fcd171c2901efb5",
    "forbidden_signature_hash": "65513f06a8d2c6a4",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 4,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|4",
    "ordinal_positive_rate": 0.5,
    "pool_signature_hash": "4f52b9c82025ab2f",
    "pool_task_set_hash": "7dfc197ee7d41f57",
    "positive_gap": 0,
    "positive_gap_weight": 6.0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.5,
    "sample_path": "samples/sample_000030.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.475252,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "source_row_index": 30,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->6:low_energy:1",
      "6->12:low_energy:1",
      "12->13:low_time:0",
      "13->8:low_time:0",
      "8->15:low_energy:1",
      "15->3:low_risk:2",
      "3->0:low_time:0"
    ],
    "target_impact_bucket": "new_task_set",
    "target_max_active_jaccard": 0.714285714,
    "target_priority_sequence": [
      6,
      12,
      13,
      8,
      15,
      3
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      6,
      12,
      13,
      8,
      15,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->6:low_energy:1",
          "6->12:low_energy:1",
          "12->13:low_time:0",
          "13->8:low_time:0",
          "8->15:low_energy:1",
          "15->3:low_risk:2",
          "3->0:low_time:0"
        ],
        "sequence": [
          6,
          12,
          13,
          8,
          15,
          3
        ],
        "start_time": 51.341994
      }
    ],
    "target_support_changing_proxy": false,
    "target_task_set": [
      3,
      6,
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
    "true_dual_hash": "6ea9f0c50b174947",
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
    "cell_avg_positive_primal_improvement": 3.46438,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.5,
    "cell_training_negative_count": 6,
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
    "positive_gap_weight": 6.0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.5,
    "sample_path": "samples/sample_000041.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.456723,
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
    "active_hash_before": "4981a129b0afed8b",
    "best_true_reduced_cost": -11.8352155,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 7,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 26,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 1.666157,
    "cell_positive_count": 4,
    "cell_positive_rate": 0.25,
    "cell_training_negative_count": 12,
    "certificate_effect": false,
    "context_hash": "17ccb5dc2e9bbac0",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.8906409740447998,
    "decision_reason": "high_priority",
    "decision_record_index": 21,
    "existing_roi_target": false,
    "expected_context_hash": "17ccb5dc2e9bbac0",
    "forbidden_signature_hash": "33392c6eb4d6d5e3",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 2,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|2",
    "ordinal_positive_rate": 0.5,
    "pool_signature_hash": "64b6b6e5f8185d85",
    "pool_task_set_hash": "f0ca8f0b97d1e3aa",
    "positive_gap": 0,
    "positive_gap_weight": 6.0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.5,
    "sample_path": "samples/sample_000021.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.399017,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json.jsonl",
    "source_row_index": 21,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->5:low_energy:1",
      "5->0:low_energy:1"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.6,
    "target_priority_sequence": [
      20,
      5
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      20,
      5,
      6,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_risk:2",
          "20->5:low_energy:1",
          "5->0:low_energy:1"
        ],
        "sequence": [
          20,
          5
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->6:low_risk:2",
          "6->3:low_risk:2",
          "3->0:low_risk:2"
        ],
        "sequence": [
          6,
          3
        ],
        "start_time": 319.390739
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      3,
      5,
      6,
      20
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 4,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "f70ed544ccc62915",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "b93aae5cccac1118",
    "best_true_reduced_cost": -10.236468667,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 23,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 24,
    "cell": "greedy-anchor|apollo15_20km",
    "cell_avg_positive_primal_improvement": 3.46438,
    "cell_positive_count": 6,
    "cell_positive_rate": 0.5,
    "cell_training_negative_count": 6,
    "certificate_effect": false,
    "context_hash": "fd0697a8f685dbe7",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9168443083763123,
    "decision_reason": "high_priority",
    "decision_record_index": 42,
    "existing_roi_target": false,
    "expected_context_hash": "fd0697a8f685dbe7",
    "forbidden_signature_hash": "0f689d4c8de40e9f",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "instance_family": "greedy-anchor",
    "instance_ordinal": 5,
    "instance_region": "apollo15_20km",
    "instance_task_count": 20,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "greedy-anchor|apollo15_20km|5",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "f282ddf79984d5e0",
    "pool_task_set_hash": "8f081174704db2ae",
    "positive_gap": 0,
    "positive_gap_weight": 6.0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.5,
    "sample_path": "samples/sample_000042.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.275106,
    "source_candidate_file": "BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json.jsonl",
    "source_row_index": 42,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->15:low_time:0",
      "15->1:low_time:0",
      "1->7:low_time:0",
      "7->17:low_time:0",
      "17->0:low_time:0"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.5,
    "target_priority_sequence": [
      12,
      15,
      1,
      7,
      17
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      12,
      15,
      1,
      7,
      17,
      14
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_time:0",
          "12->15:low_time:0",
          "15->1:low_time:0",
          "1->7:low_time:0",
          "7->17:low_time:0",
          "17->0:low_time:0"
        ],
        "sequence": [
          12,
          15,
          1,
          7,
          17
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->14:low_risk:2",
          "14->0:low_risk:2"
        ],
        "sequence": [
          14
        ],
        "start_time": 517.054496
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      1,
      7,
      12,
      14,
      15,
      17
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 6,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "ec99caad81ccb4f2",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  },
  {
    "active_hash_before": "10f398c0f4b36821",
    "best_true_reduced_cost": -25.905037196,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_ranking": "impact",
    "capture_cg_iter": 7,
    "capture_pricing_kind": "exact",
    "capture_returned_journey_count": 48,
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_avg_positive_primal_improvement": 1.666157,
    "cell_positive_count": 4,
    "cell_positive_rate": 0.25,
    "cell_training_negative_count": 12,
    "certificate_effect": false,
    "context_hash": "02259d538b5f4b8d",
    "cut_hash": "d653e60106177bb4",
    "decision_name": "HIGH_PRIORITY",
    "decision_probability": 0.9230185151100159,
    "decision_reason": "high_priority",
    "decision_record_index": 24,
    "existing_roi_target": false,
    "expected_context_hash": "02259d538b5f4b8d",
    "forbidden_signature_hash": "84dca92831f508c1",
    "gate_role": "same_run_gat_embedding_knn_ood_safety_shell",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_ordinal": 3,
    "instance_region": "tranquillitatis_balmer_like_20km",
    "instance_task_count": 20,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15",
    "negative_gap": 0,
    "official_bound_effect": false,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|3",
    "ordinal_positive_rate": 0.0,
    "pool_signature_hash": "f5b0689c334ed19d",
    "pool_task_set_hash": "4210441777cceb45",
    "positive_gap": 0,
    "positive_gap_weight": 4.0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "requires_worker_target_causal_match": true,
    "roi_yield_signal": 0.25,
    "sample_path": "samples/sample_000024.pt",
    "schema_version": "gat_same_run_target_priority_candidate_v1",
    "score": 4.134886,
    "source_candidate_file": "BPC_future/results/gat_same_run_seed_impact_unsampled_candidates_20260615/candidates.json",
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json.jsonl",
    "source_row_index": 24,
    "support_change_jaccard_threshold": 0.6,
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_impact_bucket": "new_support_changing",
    "target_max_active_jaccard": 0.428571429,
    "target_priority_sequence": [
      8,
      13
    ],
    "target_replacement_like_proxy": false,
    "target_sequence": [
      8,
      13,
      3,
      9,
      15
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_risk:2",
          "8->13:low_risk:2",
          "13->0:low_risk:2"
        ],
        "sequence": [
          8,
          13
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->9:low_time:0",
          "9->15:low_risk:2",
          "15->0:low_risk:2"
        ],
        "sequence": [
          3,
          9,
          15
        ],
        "start_time": 256.62628
      }
    ],
    "target_support_changing_proxy": true,
    "target_task_set": [
      3,
      8,
      9,
      13,
      15
    ],
    "target_task_set_in_active": false,
    "target_task_set_in_pool": false,
    "target_task_set_new": true,
    "target_task_set_size": 5,
    "training_label_allowed_before_worker_reachability": false,
    "true_dual_hash": "2ae0733dd7f24197",
    "worker_role": "explicit_opt_in_same_context_target_intervention_probe"
  }
]
```

## 结论

- 正 ROI 高度集中，不能按 rc 或 HIGH 数量盲目采样；
- 每个 family/region cell 都需要正负样本平衡；
- 候选推荐只用于下一批 audit-only A/B，不允许默认启用 worker；
- GAT/kNN/OOD 仍不能证书，不能产生 official lower bound。
