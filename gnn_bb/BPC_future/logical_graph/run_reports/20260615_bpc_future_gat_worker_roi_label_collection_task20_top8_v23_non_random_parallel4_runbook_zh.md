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
    "active_hash_before": "16e2d0342cb4ce87",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 8,
    "cell_positive_rate": 0.533333,
    "cell_training_negative_count": 7,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7db256d4f7224cc6",
    "forbidden_signature_hash": "5aeacc70a6d978d0",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|5",
    "pool_signature_hash": "c5ddd5b68ac1fbd8",
    "pool_task_set_hash": "6f8bb60d3048867b",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 5.887583,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->20:low_risk:1",
      "20->0:low_time:0"
    ],
    "target_priority_sequence": [
      12,
      20
    ],
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
    "true_dual_hash": "2fbba0a0a55dc9ef",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "ede095c6ba8539c1",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 6,
    "cell_positive_rate": 0.3,
    "cell_training_negative_count": 13,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "9fadf4f7b39742a2",
    "forbidden_signature_hash": "cc076c836d200e54",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|3",
    "pool_signature_hash": "b0fe906b0c1ab18d",
    "pool_task_set_hash": "ee50cf9eb4b638b3",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "score": 5.229199,
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->7:low_time:0",
      "7->0:low_time:0"
    ],
    "target_priority_sequence": [
      1,
      7
    ],
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
    "true_dual_hash": "4dba67189cd38261",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "f709fd0ac80f9da6",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 6,
    "cell_positive_rate": 0.3,
    "cell_training_negative_count": 13,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "1f855fbf33f8155e",
    "forbidden_signature_hash": "86f0c2ecc2a5f670",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|3",
    "pool_signature_hash": "d39cf2bdac1f86c0",
    "pool_task_set_hash": "e8bed3973827ac75",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "score": 4.599203,
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->1:low_time:0",
      "1->0:low_risk:2"
    ],
    "target_priority_sequence": [
      8,
      1
    ],
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
    "true_dual_hash": "62e7f0a17b457469",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "d42e4dfcb1b824f6",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 8,
    "cell_positive_rate": 0.533333,
    "cell_training_negative_count": 7,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "eb102a126dd0d5e3",
    "forbidden_signature_hash": "81285dc9803e02f3",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|7",
    "pool_signature_hash": "dcb5e786134f42c8",
    "pool_task_set_hash": "d38707bfb680f48a",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 4.188946,
    "target_arc_option_sequence": [
      "0->9:low_time:0",
      "9->10:low_risk:2",
      "10->4:low_time:0",
      "4->14:low_time:0",
      "14->0:low_risk:2"
    ],
    "target_priority_sequence": [
      9,
      10,
      4,
      14
    ],
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
    "true_dual_hash": "ed31e680c7b12e76",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "0780f9f032c659a7",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_7_8_20_3_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 8,
    "cell_positive_rate": 0.533333,
    "cell_training_negative_count": 7,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "22dec9cfc13bb3d6",
    "forbidden_signature_hash": "9324e282befa1ac8",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_7_8_20_3",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|8",
    "pool_signature_hash": "b8aa00efb6e169f6",
    "pool_task_set_hash": "a98072364d0bfc1e",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 4.140616,
    "target_arc_option_sequence": [
      "0->7:low_risk:2",
      "7->8:low_risk:2",
      "8->20:low_risk:2",
      "20->0:low_time:0"
    ],
    "target_priority_sequence": [
      7,
      8,
      20
    ],
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
    "true_dual_hash": "f41cb57ae52a541e",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_7_8_20_3_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "7e1550730bce4588",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_4_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 8,
    "cell_positive_rate": 0.533333,
    "cell_training_negative_count": 7,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "84ae11479ed592d4",
    "forbidden_signature_hash": "cfbda5e70fc052f2",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_4_10",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|6",
    "pool_signature_hash": "6321282f868e0007",
    "pool_task_set_hash": "f699ccb296afaee5",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 3.949768,
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->17:low_risk:2",
      "17->11:low_time:0",
      "11->0:low_risk:2"
    ],
    "target_priority_sequence": [
      13,
      17,
      11
    ],
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
    "true_dual_hash": "a5dfa0099f5679ed",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_4_10_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "7639b6652856b577",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_39d7643d5a478407_7_14_3_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 8,
    "cell_positive_rate": 0.533333,
    "cell_training_negative_count": 7,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "39d7643d5a478407",
    "forbidden_signature_hash": "e6b5e61118e78a0b",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_39d7643d5a478407_7_14_3_5",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|7",
    "pool_signature_hash": "3ba0638653a59e8e",
    "pool_task_set_hash": "06278cc81bec04c9",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 3.927524,
    "target_arc_option_sequence": [
      "0->7:low_time:0",
      "7->14:low_time:0",
      "14->0:low_risk:2"
    ],
    "target_priority_sequence": [
      7,
      14
    ],
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
    "true_dual_hash": "2ff601b483978496",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_39d7643d5a478407_7_14_3_5_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "d9a28376789baaec",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_3_13_17_8_4_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 8,
    "cell_positive_rate": 0.533333,
    "cell_training_negative_count": 7,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "4c81d9ecf77097c9",
    "forbidden_signature_hash": "72e4076e648b8514",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_3_13_17_8_4_10",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|6",
    "pool_signature_hash": "c387cec8e60241d1",
    "pool_task_set_hash": "ee499f80528aeea9",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 3.885124,
    "target_arc_option_sequence": [
      "0->3:low_risk:1",
      "3->13:low_risk:2",
      "13->17:low_risk:2",
      "17->0:low_risk:2"
    ],
    "target_priority_sequence": [
      3,
      13,
      17
    ],
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
    "true_dual_hash": "7e4b750a4d705954",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_3_13_17_8_4_10_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7db256d4f7224cc6 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,20,5,3,6,4 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_risk:2","12->20:low_risk:1","20->0:low_time:0"],"sequence":[12,20],"start_time":0.0},{"arc_option_sequence":["0->5:low_time:0","5->3:low_risk:2","3->6:low_time:0","6->4:low_energy:1","4->0:low_time:0"],"sequence":[5,3,6,4],"start_time":127.287307}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_risk:2,12->20:low_risk:1,20->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=9fadf4f7b39742a2 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=1,7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=1,7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=1,7,20,4,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->1:low_time:0","1->7:low_time:0","7->0:low_time:0"],"sequence":[1,7],"start_time":0.0},{"arc_option_sequence":["0->20:low_risk:2","20->4:low_time:0","4->10:low_time:0","10->0:low_risk:2"],"sequence":[20,4,10],"start_time":210.842101}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->1:low_time:0,1->7:low_time:0,7->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=1f855fbf33f8155e --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,1,3,9,15 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_time:0","8->1:low_time:0","1->0:low_risk:2"],"sequence":[8,1],"start_time":0.0},{"arc_option_sequence":["0->3:low_time:0","3->9:low_risk:2","9->15:low_risk:2","15->0:low_risk:2"],"sequence":[3,9,15],"start_time":261.945896}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_time:0,8->1:low_time:0,1->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=eb102a126dd0d5e3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=9,10,4,14 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=9,10,4,14 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=9,10,4,14,1 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->9:low_time:0","9->10:low_risk:2","10->4:low_time:0","4->14:low_time:0","14->0:low_risk:2"],"sequence":[9,10,4,14],"start_time":0.0},{"arc_option_sequence":["0->1:low_risk:1","1->0:low_risk:1"],"sequence":[1],"start_time":417.91101}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->9:low_time:0,9->10:low_risk:2,10->4:low_time:0,4->14:low_time:0,14->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_7_8_20_3_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_7_8_20_3_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_7_8_20_3_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_7_8_20_3_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_7_8_20_3_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_7_8_20_3_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_7_8_20_3_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_7_8_20_3_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=22dec9cfc13bb3d6 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=7,8,20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=7,8,20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=7,8,20,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->7:low_risk:2","7->8:low_risk:2","8->20:low_risk:2","20->0:low_time:0"],"sequence":[7,8,20],"start_time":0.0},{"arc_option_sequence":["0->3:low_risk:2","3->0:low_risk:2"],"sequence":[3],"start_time":302.772773}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->7:low_risk:2,7->8:low_risk:2,8->20:low_risk:2,20->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_4_10_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_4_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_4_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_4_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_4_10_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_4_10_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_4_10_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_4_10_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=84ae11479ed592d4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13,17,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13,17,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,17,11,4,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_risk:2","13->17:low_risk:2","17->11:low_time:0","11->0:low_risk:2"],"sequence":[13,17,11],"start_time":19.222023},{"arc_option_sequence":["0->4:low_time:0","4->10:low_risk:2","10->0:low_time:0"],"sequence":[4,10],"start_time":279.592641}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_risk:2,13->17:low_risk:2,17->11:low_time:0,11->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_39d7643d5a478407_7_14_3_5_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_39d7643d5a478407_7_14_3_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_39d7643d5a478407_7_14_3_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_39d7643d5a478407_7_14_3_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_39d7643d5a478407_7_14_3_5_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_39d7643d5a478407_7_14_3_5_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_39d7643d5a478407_7_14_3_5_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_39d7643d5a478407_7_14_3_5_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=39d7643d5a478407 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=7,14 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=7,14 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=7,14,3,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->7:low_time:0","7->14:low_time:0","14->0:low_risk:2"],"sequence":[7,14],"start_time":0.0},{"arc_option_sequence":["0->3:low_risk:2","3->5:low_risk:1","5->0:low_risk:2"],"sequence":[3,5],"start_time":296.326085}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->7:low_time:0,7->14:low_time:0,14->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_3_13_17_8_4_10_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_3_13_17_8_4_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_3_13_17_8_4_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_3_13_17_8_4_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_3_13_17_8_4_10_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_3_13_17_8_4_10_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_3_13_17_8_4_10_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v23_non_random_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_4c81d9ecf77097c9_3_13_17_8_4_10_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=4c81d9ecf77097c9 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3,13,17 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3,13,17 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,13,17,8,4,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_risk:1","3->13:low_risk:2","13->17:low_risk:2","17->0:low_risk:2"],"sequence":[3,13,17],"start_time":0.0},{"arc_option_sequence":["0->8:low_time:0","8->4:low_time:0","4->10:low_time:0","10->0:low_energy:1"],"sequence":[8,4,10],"start_time":227.873491}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_risk:1,3->13:low_risk:2,13->17:low_risk:2,17->0:low_risk:2'
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
