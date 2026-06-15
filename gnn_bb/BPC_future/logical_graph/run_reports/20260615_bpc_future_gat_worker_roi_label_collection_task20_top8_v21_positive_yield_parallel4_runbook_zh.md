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
    "active_hash_before": "8a93da8ed9d9c4ac",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_2d1da4555bf67a8c_19_12_5_18_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 8,
    "cell_positive_rate": 0.615385,
    "cell_training_negative_count": 5,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "2d1da4555bf67a8c",
    "forbidden_signature_hash": "f7b3702257e9647b",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_2d1da4555bf67a8c_19_12_5_18",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|6",
    "pool_signature_hash": "4a8bf57bb13abdb4",
    "pool_task_set_hash": "9985c211f1f9ded5",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 6.95382,
    "target_arc_option_sequence": [
      "0->19:low_risk:2",
      "19->12:low_risk:2",
      "12->5:low_risk:2",
      "5->0:low_risk:2"
    ],
    "target_priority_sequence": [
      19,
      12,
      5
    ],
    "target_sequence": [
      19,
      12,
      5,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->19:low_risk:2",
          "19->12:low_risk:2",
          "12->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          19,
          12,
          5
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->18:low_risk:2",
          "18->0:low_risk:2"
        ],
        "sequence": [
          18
        ],
        "start_time": 329.868328
      }
    ],
    "true_dual_hash": "a74efb011c7acebf",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_2d1da4555bf67a8c_19_12_5_18_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "6cb4dad22a220111",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_3_20_16_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 8,
    "cell_positive_rate": 0.615385,
    "cell_training_negative_count": 5,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7714263901aeb2ec",
    "forbidden_signature_hash": "d0adc91cc9df80e5",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_3_20_16_17",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|4",
    "pool_signature_hash": "10deac344d39477b",
    "pool_task_set_hash": "ceb76ec4ad68b7b9",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 6.913878,
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->20:low_time:0",
      "20->0:low_risk:2"
    ],
    "target_priority_sequence": [
      3,
      20
    ],
    "target_sequence": [
      3,
      20,
      16,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->20:low_time:0",
          "20->0:low_risk:2"
        ],
        "sequence": [
          3,
          20
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->16:low_risk:2",
          "16->17:low_time:0",
          "17->0:low_time:0"
        ],
        "sequence": [
          16,
          17
        ],
        "start_time": 207.647328
      }
    ],
    "true_dual_hash": "a99ea13dc01c6919",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_3_20_16_17_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "8a93da8ed9d9c4ac",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_5d9c7e881a00ee06_20_1_10_18_9_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 8,
    "cell_positive_rate": 0.615385,
    "cell_training_negative_count": 5,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "5d9c7e881a00ee06",
    "forbidden_signature_hash": "0071bed0201799cd",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_5d9c7e881a00ee06_20_1_10_18_9",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|6",
    "pool_signature_hash": "3fe484e6a7a0a26c",
    "pool_task_set_hash": "a4890ea87e69595a",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 6.909944,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_risk:2",
      "1->0:low_risk:2"
    ],
    "target_priority_sequence": [
      20,
      1
    ],
    "target_sequence": [
      20,
      1,
      10,
      18,
      9
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->1:low_risk:2",
          "1->0:low_risk:2"
        ],
        "sequence": [
          20,
          1
        ],
        "start_time": 4.735202
      },
      {
        "arc_option_sequence": [
          "0->10:low_time:0",
          "10->18:low_risk:2",
          "18->0:low_time:0"
        ],
        "sequence": [
          10,
          18
        ],
        "start_time": 208.588951
      },
      {
        "arc_option_sequence": [
          "0->9:low_time:0",
          "9->0:low_time:0"
        ],
        "sequence": [
          9
        ],
        "start_time": 507.629198
      }
    ],
    "true_dual_hash": "ba0c00446491e223",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_5d9c7e881a00ee06_20_1_10_18_9_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "5dc419f8a78d5837",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_6cbf8d7c2c4fe23f_20_1_4_18_9_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 8,
    "cell_positive_rate": 0.615385,
    "cell_training_negative_count": 5,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "6cbf8d7c2c4fe23f",
    "forbidden_signature_hash": "a57efd83d2d0f94c",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_6cbf8d7c2c4fe23f_20_1_4_18_9",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|tranquillitatis_balmer_like_20km|6",
    "pool_signature_hash": "595b10a2daa0e691",
    "pool_task_set_hash": "990b4cf1b0f986a5",
    "positive_gap": 0,
    "reason": "positive_like_cell",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 6.904436,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_risk:2",
      "1->0:low_risk:2"
    ],
    "target_priority_sequence": [
      20,
      1
    ],
    "target_sequence": [
      20,
      1,
      4,
      18,
      9
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->1:low_risk:2",
          "1->0:low_risk:2"
        ],
        "sequence": [
          20,
          1
        ],
        "start_time": 4.735202
      },
      {
        "arc_option_sequence": [
          "0->4:low_time:0",
          "4->18:low_time:0",
          "18->0:low_time:0"
        ],
        "sequence": [
          4,
          18
        ],
        "start_time": 208.588951
      },
      {
        "arc_option_sequence": [
          "0->9:low_risk:2",
          "9->0:low_time:0"
        ],
        "sequence": [
          9
        ],
        "start_time": 496.515004
      }
    ],
    "true_dual_hash": "c58020b7461188c8",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_6cbf8d7c2c4fe23f_20_1_4_18_9_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "ef813699d84ea6a5",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|apollo15_20km",
    "cell_positive_count": 4,
    "cell_positive_rate": 0.285714,
    "cell_training_negative_count": 9,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "c4004463c80918b5",
    "forbidden_signature_hash": "dd40587035aa50c3",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|apollo15_20km|2",
    "pool_signature_hash": "ef821b4e7d87f726",
    "pool_task_set_hash": "e9c9b682e80c660e",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "score": 4.71725,
    "target_arc_option_sequence": [
      "0->9:low_energy:1",
      "9->3:low_time:0",
      "3->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_priority_sequence": [
      9,
      3,
      20
    ],
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
    "true_dual_hash": "95eafdfe84624eeb",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "0959cbac9e46d813",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_7_11_4_2_8_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|apollo15_20km",
    "cell_positive_count": 4,
    "cell_positive_rate": 0.285714,
    "cell_training_negative_count": 9,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "12cfa32e4756fd37",
    "forbidden_signature_hash": "aca48a99c4cebe6f",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_7_11_4_2_8",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|apollo15_20km|2",
    "pool_signature_hash": "e4f62a0f69ce5910",
    "pool_task_set_hash": "ce877e4ac6870ac8",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "score": 4.493534,
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->9:low_time:0",
      "9->7:low_time:0",
      "7->0:low_time:0"
    ],
    "target_priority_sequence": [
      3,
      9,
      7
    ],
    "target_sequence": [
      3,
      9,
      7,
      11,
      4,
      2,
      8
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->9:low_time:0",
          "9->7:low_time:0",
          "7->0:low_time:0"
        ],
        "sequence": [
          3,
          9,
          7
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->11:low_risk:2",
          "11->4:low_risk:1",
          "4->2:low_risk:1",
          "2->8:low_risk:1",
          "8->0:low_risk:2"
        ],
        "sequence": [
          11,
          4,
          2,
          8
        ],
        "start_time": 307.81881
      }
    ],
    "true_dual_hash": "714062ee92317ed5",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_7_11_4_2_8_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "eb7ddfb3029ed64d",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 5,
    "cell_positive_rate": 0.454545,
    "cell_training_negative_count": 6,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b1fb77954b949bf0",
    "forbidden_signature_hash": "81497f2e29d39933",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|4",
    "pool_signature_hash": "e2151485b49e03db",
    "pool_task_set_hash": "74fb358c2ad9aae8",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 4.482427,
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->12:low_time:0",
      "12->7:low_time:0",
      "7->0:low_time:0"
    ],
    "target_priority_sequence": [
      6,
      12,
      7
    ],
    "target_sequence": [
      6,
      12,
      7,
      16,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->6:low_time:0",
          "6->12:low_time:0",
          "12->7:low_time:0",
          "7->0:low_time:0"
        ],
        "sequence": [
          6,
          12,
          7
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->16:low_time:0",
          "16->17:low_time:0",
          "17->0:low_time:0"
        ],
        "sequence": [
          16,
          17
        ],
        "start_time": 425.79128
      }
    ],
    "true_dual_hash": "ba52399ea678f004",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "f8111e12b798ea28",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 3,
    "cell_positive_rate": 0.2,
    "cell_training_negative_count": 12,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "dfd68d5873b84183",
    "forbidden_signature_hash": "6de0b545d5e610b8",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|tranquillitatis_balmer_like_20km|2",
    "pool_signature_hash": "8ec5c004bb6bc8ed",
    "pool_task_set_hash": "95cda2345f7c9f1e",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "candidate_pool_high_score",
    "score": 4.406814,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_priority_sequence": [
      20,
      1
    ],
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
    "true_dual_hash": "958e2cb48777f988",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_2d1da4555bf67a8c_19_12_5_18_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_2d1da4555bf67a8c_19_12_5_18_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_2d1da4555bf67a8c_19_12_5_18_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_2d1da4555bf67a8c_19_12_5_18_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_2d1da4555bf67a8c_19_12_5_18_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_2d1da4555bf67a8c_19_12_5_18_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_2d1da4555bf67a8c_19_12_5_18_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_2d1da4555bf67a8c_19_12_5_18_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=2d1da4555bf67a8c --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=19,12,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=19,12,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=19,12,5,18 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->19:low_risk:2","19->12:low_risk:2","12->5:low_risk:2","5->0:low_risk:2"],"sequence":[19,12,5],"start_time":0.0},{"arc_option_sequence":["0->18:low_risk:2","18->0:low_risk:2"],"sequence":[18],"start_time":329.868328}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->19:low_risk:2,19->12:low_risk:2,12->5:low_risk:2,5->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_3_20_16_17_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_3_20_16_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_3_20_16_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_3_20_16_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_3_20_16_17_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_3_20_16_17_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_3_20_16_17_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_3_20_16_17_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7714263901aeb2ec --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3,20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3,20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,20,16,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_time:0","3->20:low_time:0","20->0:low_risk:2"],"sequence":[3,20],"start_time":0.0},{"arc_option_sequence":["0->16:low_risk:2","16->17:low_time:0","17->0:low_time:0"],"sequence":[16,17],"start_time":207.647328}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_time:0,3->20:low_time:0,20->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_5d9c7e881a00ee06_20_1_10_18_9_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_5d9c7e881a00ee06_20_1_10_18_9_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_5d9c7e881a00ee06_20_1_10_18_9_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_5d9c7e881a00ee06_20_1_10_18_9_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_5d9c7e881a00ee06_20_1_10_18_9_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_5d9c7e881a00ee06_20_1_10_18_9_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_5d9c7e881a00ee06_20_1_10_18_9_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_5d9c7e881a00ee06_20_1_10_18_9_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=5d9c7e881a00ee06 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,1,10,18,9 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->1:low_risk:2","1->0:low_risk:2"],"sequence":[20,1],"start_time":4.735202},{"arc_option_sequence":["0->10:low_time:0","10->18:low_risk:2","18->0:low_time:0"],"sequence":[10,18],"start_time":208.588951},{"arc_option_sequence":["0->9:low_time:0","9->0:low_time:0"],"sequence":[9],"start_time":507.629198}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->1:low_risk:2,1->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_6cbf8d7c2c4fe23f_20_1_4_18_9_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_6cbf8d7c2c4fe23f_20_1_4_18_9_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_6cbf8d7c2c4fe23f_20_1_4_18_9_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_6cbf8d7c2c4fe23f_20_1_4_18_9_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_6cbf8d7c2c4fe23f_20_1_4_18_9_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_6cbf8d7c2c4fe23f_20_1_4_18_9_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_6cbf8d7c2c4fe23f_20_1_4_18_9_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_6cbf8d7c2c4fe23f_20_1_4_18_9_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=6cbf8d7c2c4fe23f --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,1,4,18,9 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->1:low_risk:2","1->0:low_risk:2"],"sequence":[20,1],"start_time":4.735202},{"arc_option_sequence":["0->4:low_time:0","4->18:low_time:0","18->0:low_time:0"],"sequence":[4,18],"start_time":208.588951},{"arc_option_sequence":["0->9:low_risk:2","9->0:low_time:0"],"sequence":[9],"start_time":496.515004}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->1:low_risk:2,1->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_11_4_8_10_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=c4004463c80918b5 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=9,3,20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=9,3,20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=9,3,20,11,4,8,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->9:low_energy:1","9->3:low_time:0","3->20:low_time:0","20->0:low_time:0"],"sequence":[9,3,20],"start_time":0.0},{"arc_option_sequence":["0->11:low_risk:2","11->4:low_risk:1","4->8:low_time:0","8->10:low_risk:2","10->0:low_risk:2"],"sequence":[11,4,8,10],"start_time":307.81881}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->9:low_energy:1,9->3:low_time:0,3->20:low_time:0,20->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_7_11_4_2_8_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_7_11_4_2_8_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_7_11_4_2_8_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_7_11_4_2_8_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_7_11_4_2_8_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_7_11_4_2_8_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_7_11_4_2_8_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_7_11_4_2_8_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=12cfa32e4756fd37 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3,9,7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3,9,7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,9,7,11,4,2,8 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_time:0","3->9:low_time:0","9->7:low_time:0","7->0:low_time:0"],"sequence":[3,9,7],"start_time":0.0},{"arc_option_sequence":["0->11:low_risk:2","11->4:low_risk:1","4->2:low_risk:1","2->8:low_risk:1","8->0:low_risk:2"],"sequence":[11,4,2,8],"start_time":307.81881}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_time:0,3->9:low_time:0,9->7:low_time:0,7->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b1fb77954b949bf0 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=6,12,7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=6,12,7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=6,12,7,16,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->6:low_time:0","6->12:low_time:0","12->7:low_time:0","7->0:low_time:0"],"sequence":[6,12,7],"start_time":0.0},{"arc_option_sequence":["0->16:low_time:0","16->17:low_time:0","17->0:low_time:0"],"sequence":[16,17],"start_time":425.79128}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->6:low_time:0,6->12:low_time:0,12->7:low_time:0,7->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_top8_v21_positive_yield_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=dfd68d5873b84183 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,1,17,12 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->1:low_time:0","1->0:low_time:0"],"sequence":[20,1],"start_time":0.0},{"arc_option_sequence":["0->17:low_time:0","17->12:low_time:0","12->0:low_time:0"],"sequence":[17,12],"start_time":296.270931}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->1:low_time:0,1->0:low_time:0'
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
