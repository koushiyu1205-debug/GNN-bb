# GAT Target-Priority Worker A/B Runbook

日期：2026-06-14

## 目的

生成下一轮 5/10 no-regression 与 20-task ROI A/B 命令。GAT 仍只负责 embedding / trajectory impact 表达，kNN/OOD 只做安全壳；通过安全壳的 true-RC negative 可优先进入 worker target，不通过的负列进入 DELAY_QUEUE，不能永久丢弃，也不能参与 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_runbook = current
status = ready
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
required_candidate_context_field_count = 8
all_checks_pass = true
```

## Candidate Policy

```json
{
  "certificate_effect": false,
  "context_miss_policy": "capture_actual_reached_contexts_for_next_iteration",
  "gat_role": "embedding_and_trajectory_impact_expression",
  "knn_ood_role": "safety_shell",
  "negative_discard_allowed": false,
  "safe_negative_action": "HIGH_PRIORITY",
  "unsafe_negative_action": "DELAY_QUEUE",
  "worker_stage_policy": "match_capture_pricing_kind: heuristic_before_heuristic_exact_before_exact"
}
```

## Candidate Runs

```json
[
  {
    "active_hash_before": "7497860baf634782",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 8,
    "cell_positive_rate": 0.470588,
    "cell_training_negative_count": 9,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "048e5f66efcd12df",
    "forbidden_signature_hash": "a9d74a61c4c73072",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|7",
    "pool_signature_hash": "fd82c4ddd8b3be43",
    "pool_task_set_hash": "e717738ba4daed8d",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 6.08253,
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->10:low_risk:2",
      "10->0:low_risk:2"
    ],
    "target_priority_sequence": [
      2,
      10
    ],
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
    "true_dual_hash": "0d0dc5ddf5fe17ee",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "2c2e416db249f720",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 4,
    "cell_positive_rate": 0.25,
    "cell_training_negative_count": 12,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "3d1bd8618099b573",
    "forbidden_signature_hash": "dd79a2cfb5c63e21",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|2",
    "pool_signature_hash": "eddad0807740a5f3",
    "pool_task_set_hash": "e1b494c430dfa84e",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "score": 5.219445,
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->0:low_risk:2"
    ],
    "target_priority_sequence": [
      8
    ],
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
    "true_dual_hash": "bc2e3db079d173a6",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "96c7c0766604244a",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 4,
    "cell_positive_rate": 0.25,
    "cell_training_negative_count": 12,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "forbidden_signature_hash": "16f38b9203fc0908",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|2",
    "pool_signature_hash": "a3a808a977a593aa",
    "pool_task_set_hash": "393c147abf261db2",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "score": 5.200765,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->0:low_risk:2"
    ],
    "target_priority_sequence": [
      4
    ],
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
    "true_dual_hash": "b49472077fb42329",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "d15d7fc02d890349",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 6,
    "cell_positive_rate": 0.5,
    "cell_training_negative_count": 6,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7fcd171c2901efb5",
    "forbidden_signature_hash": "65513f06a8d2c6a4",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|4",
    "pool_signature_hash": "4f52b9c82025ab2f",
    "pool_task_set_hash": "7dfc197ee7d41f57",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 4.475252,
    "target_arc_option_sequence": [
      "0->6:low_energy:1",
      "6->12:low_energy:1",
      "12->13:low_time:0",
      "13->8:low_time:0",
      "8->15:low_energy:1",
      "15->3:low_risk:2",
      "3->0:low_time:0"
    ],
    "target_priority_sequence": [
      6,
      12,
      13,
      8,
      15,
      3
    ],
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
    "true_dual_hash": "6ea9f0c50b174947",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "778c07cb4ef85021",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 6,
    "cell_positive_rate": 0.5,
    "cell_training_negative_count": 6,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "f9d0b6b18a0a28d3",
    "forbidden_signature_hash": "419f8f65acc3551b",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|5",
    "pool_signature_hash": "d26348c8579fe2e4",
    "pool_task_set_hash": "49305ade6883086a",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 4.456723,
    "target_arc_option_sequence": [
      "0->18:low_risk:2",
      "18->0:low_risk:2"
    ],
    "target_priority_sequence": [
      18
    ],
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
    "true_dual_hash": "1f5fbbb40123e95b",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "4981a129b0afed8b",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 4,
    "cell_positive_rate": 0.25,
    "cell_training_negative_count": 12,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "17ccb5dc2e9bbac0",
    "forbidden_signature_hash": "33392c6eb4d6d5e3",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|2",
    "pool_signature_hash": "64b6b6e5f8185d85",
    "pool_task_set_hash": "f0ca8f0b97d1e3aa",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "score": 4.399017,
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->5:low_energy:1",
      "5->0:low_energy:1"
    ],
    "target_priority_sequence": [
      20,
      5
    ],
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
    "true_dual_hash": "f70ed544ccc62915",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "b93aae5cccac1118",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 6,
    "cell_positive_rate": 0.5,
    "cell_training_negative_count": 6,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "fd0697a8f685dbe7",
    "forbidden_signature_hash": "0f689d4c8de40e9f",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|5",
    "pool_signature_hash": "f282ddf79984d5e0",
    "pool_task_set_hash": "8f081174704db2ae",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 4.275106,
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->15:low_time:0",
      "15->1:low_time:0",
      "1->7:low_time:0",
      "7->17:low_time:0",
      "17->0:low_time:0"
    ],
    "target_priority_sequence": [
      12,
      15,
      1,
      7,
      17
    ],
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
    "true_dual_hash": "ec99caad81ccb4f2",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "10f398c0f4b36821",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 4,
    "cell_positive_rate": 0.25,
    "cell_training_negative_count": 12,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "02259d538b5f4b8d",
    "forbidden_signature_hash": "84dca92831f508c1",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|3",
    "pool_signature_hash": "f5b0689c334ed19d",
    "pool_task_set_hash": "4210441777cceb45",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "score": 4.134886,
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_priority_sequence": [
      8,
      13
    ],
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
    "true_dual_hash": "2ae0733dd7f24197",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=048e5f66efcd12df --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=2,10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=2,10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=2,10,19,9,1 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->2:low_risk:2","2->10:low_risk:2","10->0:low_risk:2"],"sequence":[2,10],"start_time":0.0},{"arc_option_sequence":["0->19:low_time:0","19->9:low_risk:2","9->0:low_time:0"],"sequence":[19,9],"start_time":133.023545},{"arc_option_sequence":["0->1:low_risk:2","1->0:low_risk:2"],"sequence":[1],"start_time":490.57921}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->2:low_risk:2,2->10:low_risk:2,10->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=3d1bd8618099b573 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,11,10,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_risk:2","8->0:low_risk:2"],"sequence":[8],"start_time":0.0},{"arc_option_sequence":["0->11:low_risk:2","11->10:low_energy:1","10->17:low_energy:1","17->0:low_time:0"],"sequence":[11,10,17],"start_time":180.341466}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_risk:2,8->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ac15bc4e7e3d6fff --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,19,10,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_risk:2","4->0:low_risk:2"],"sequence":[4],"start_time":0.0},{"arc_option_sequence":["0->19:low_risk:2","19->10:low_time:0","10->17:low_risk:2","17->0:low_time:0"],"sequence":[19,10,17],"start_time":202.264867}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_risk:2,4->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7fcd171c2901efb5 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=6,12,13,8,15,3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=6,12,13,8,15,3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=6,12,13,8,15,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->6:low_energy:1","6->12:low_energy:1","12->13:low_time:0","13->8:low_time:0","8->15:low_energy:1","15->3:low_risk:2","3->0:low_time:0"],"sequence":[6,12,13,8,15,3],"start_time":51.341994}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->6:low_energy:1,6->12:low_energy:1,12->13:low_time:0,13->8:low_time:0,8->15:low_energy:1,15->3:low_risk:2,3->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=f9d0b6b18a0a28d3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=18 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=18 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=18,3,13,6,19 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->18:low_risk:2","18->0:low_risk:2"],"sequence":[18],"start_time":0.0},{"arc_option_sequence":["0->3:low_time:0","3->13:low_risk:2","13->6:low_risk:2","6->19:low_risk:2","19->0:low_time:0"],"sequence":[3,13,6,19],"start_time":206.946847}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->18:low_risk:2,18->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=17ccb5dc2e9bbac0 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,5,6,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_risk:2","20->5:low_energy:1","5->0:low_energy:1"],"sequence":[20,5],"start_time":0.0},{"arc_option_sequence":["0->6:low_risk:2","6->3:low_risk:2","3->0:low_risk:2"],"sequence":[6,3],"start_time":319.390739}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_risk:2,20->5:low_energy:1,5->0:low_energy:1'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=fd0697a8f685dbe7 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,15,1,7,17 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,15,1,7,17 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,15,1,7,17,14 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_time:0","12->15:low_time:0","15->1:low_time:0","1->7:low_time:0","7->17:low_time:0","17->0:low_time:0"],"sequence":[12,15,1,7,17],"start_time":0.0},{"arc_option_sequence":["0->14:low_risk:2","14->0:low_risk:2"],"sequence":[14],"start_time":517.054496}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_time:0,12->15:low_time:0,15->1:low_time:0,1->7:low_time:0,7->17:low_time:0,17->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v22_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=02259d538b5f4b8d --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,13,3,9,15 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_risk:2","8->13:low_risk:2","13->0:low_risk:2"],"sequence":[8,13],"start_time":0.0},{"arc_option_sequence":["0->3:low_risk:2","3->9:low_time:0","9->15:low_risk:2","15->0:low_risk:2"],"sequence":[3,9,15],"start_time":256.62628}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_risk:2,8->13:low_risk:2,13->0:low_risk:2'
```

## 边界

- 5/10 命令不关闭主线 GAT/learning，也不启用新 worker；
- 20 baseline/worker 命令也不关闭主线 GAT/learning，避免候选捕获上下文无法复现；
- 20 baseline/worker 命令开启 counterfactual replay capture；如果旧 target context 没到，仍保留实际到达的 context 供下一轮候选抽取；
- 20 worker 命令是显式 opt-in，只验证 target-priority ROI；
- 20 worker 候选必须带完整 context / dual / cuts / branch / pool hash；
- 所有命令都不启用 sharded Pulse certificate 或 official lower-bound effect；
- 含 `->` 的 arc-option 配置通过 `shlex.join` 自动引用，不能手工去掉引号；
- 该 runbook 不是生产开关，跑完后仍需看 5/10 no-regression 和 20-task ROI。
