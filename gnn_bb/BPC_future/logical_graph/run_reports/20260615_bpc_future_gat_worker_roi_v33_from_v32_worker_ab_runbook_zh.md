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
    "active_hash_before": "03a8d149c5bdfc16",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_5_1_2_4_7_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|apollo15_20km",
    "cell_positive_count": 3,
    "cell_positive_rate": 0.157895,
    "cell_training_negative_count": 13,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "fbfd88d4ebde5459",
    "forbidden_signature_hash": "69ba243ea44bf530",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_5_1_2_4_7_13",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "pool_signature_hash": "4846218d8d5926f5",
    "pool_task_set_hash": "b3efd3d85e0ad5f4",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 8.517506,
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord8_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->2:low_risk:2",
      "2->4:low_risk:2",
      "4->7:low_risk:2",
      "7->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_priority_sequence": [
      5,
      1,
      2,
      4,
      7,
      13
    ],
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
    "true_dual_hash": "c9745e8a1c010c30",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_5_1_2_4_7_13_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "03a8d149c5bdfc16",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|apollo15_20km",
    "cell_positive_count": 3,
    "cell_positive_rate": 0.157895,
    "cell_training_negative_count": 13,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "3100b787bf438dfe",
    "forbidden_signature_hash": "59f58c79d1e50d49",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_13",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "pool_signature_hash": "7a249193fdd37789",
    "pool_task_set_hash": "e3f049a263f86c82",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 8.446177,
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord8_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->5:low_time:0",
      "5->1:low_risk:2",
      "1->2:low_time:0",
      "2->4:low_time:0",
      "4->11:low_risk:2",
      "11->13:low_risk:2",
      "13->0:low_time:0"
    ],
    "target_priority_sequence": [
      5,
      1,
      2,
      4,
      11,
      13
    ],
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
    "true_dual_hash": "d4d21a0866a5f19c",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_13_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "eb92a6a521734d12",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|apollo15_20km",
    "cell_positive_count": 3,
    "cell_positive_rate": 0.157895,
    "cell_training_negative_count": 13,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "409f65576794fa39",
    "forbidden_signature_hash": "2759f01a2dec4e9a",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_13",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "pool_signature_hash": "61505b62c0f9a4a1",
    "pool_task_set_hash": "bba64460221b3547",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 8.169659,
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord8_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->20:low_energy:1",
      "20->13:low_time:0",
      "13->0:low_time:0"
    ],
    "target_priority_sequence": [
      8,
      20,
      13
    ],
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
    "true_dual_hash": "efc2fb20ceb858b3",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_13_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "6405fc3f1de6a512",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_5f4498eb39858b1d_5_6_10_7_13_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 3,
    "cell_positive_rate": 0.125,
    "cell_training_negative_count": 19,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "5f4498eb39858b1d",
    "forbidden_signature_hash": "d223202b3043800f",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_5f4498eb39858b1d_5_6_10_7_13_11",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|5",
    "pool_signature_hash": "a14ffdc8106d7c11",
    "pool_task_set_hash": "57819ddf969ca320",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 6.825723,
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord5_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->6:low_risk:2",
      "6->10:low_energy:1",
      "10->0:low_risk:2"
    ],
    "target_priority_sequence": [
      5,
      6,
      10
    ],
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
    "true_dual_hash": "788890d1a40f457f",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_5f4498eb39858b1d_5_6_10_7_13_11_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "d8dee49da637491a",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_8f2088cfefc3e3b1_20_3_7_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 3,
    "cell_positive_rate": 0.125,
    "cell_training_negative_count": 19,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "8f2088cfefc3e3b1",
    "forbidden_signature_hash": "7fb0f1421be973cb",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_8f2088cfefc3e3b1_20_3_7",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|5",
    "pool_signature_hash": "8c4430995d61f86b",
    "pool_task_set_hash": "37c69d4231a5d4f1",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 6.308817,
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord5_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->0:low_risk:2"
    ],
    "target_priority_sequence": [
      20
    ],
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
    "true_dual_hash": "7c6a6d9ca297c314",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_8f2088cfefc3e3b1_20_3_7_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "2a0b4670d5737413",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_2d9686e5aa73b5f3_9_19_1_16_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|apollo15_20km",
    "cell_positive_count": 3,
    "cell_positive_rate": 0.157895,
    "cell_training_negative_count": 13,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "2d9686e5aa73b5f3",
    "forbidden_signature_hash": "72d882a694a7afb4",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_2d9686e5aa73b5f3_9_19_1_16_11",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|5",
    "pool_signature_hash": "b9a92aab0d0618a2",
    "pool_task_set_hash": "348ad9b59205f105",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 5.959602,
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord5_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->9:low_risk:2",
      "9->19:low_risk:2",
      "19->1:low_risk:2",
      "1->16:low_risk:2",
      "16->11:low_risk:2",
      "11->0:low_risk:2"
    ],
    "target_priority_sequence": [
      9,
      19,
      1,
      16,
      11
    ],
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
    "true_dual_hash": "794c11f3b9f87222",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_2d9686e5aa73b5f3_9_19_1_16_11_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "84a32099330f4216",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_5c6127a7add1e6f6_13_11_15_6_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|apollo15_20km",
    "cell_positive_count": 3,
    "cell_positive_rate": 0.157895,
    "cell_training_negative_count": 13,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "5c6127a7add1e6f6",
    "forbidden_signature_hash": "31b3354de2646468",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_5c6127a7add1e6f6_13_11_15_6",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|2",
    "pool_signature_hash": "622f9128ae38a6db",
    "pool_task_set_hash": "b440da82d9e3a2ed",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 5.93954,
    "source_file": "BPC_future/results/gat_same_run_gap_focused_ord2_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->11:low_time:0",
      "11->15:low_risk:2",
      "15->6:low_time:0",
      "6->0:low_time:0"
    ],
    "target_priority_sequence": [
      13,
      11,
      15,
      6
    ],
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
    "true_dual_hash": "0848b9e9ea448d4e",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_5c6127a7add1e6f6_13_11_15_6_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "c404098cefa45555",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_ffe911c2088f42a2_6_5_12_11_10_18_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|apollo15_20km",
    "cell_positive_count": 3,
    "cell_positive_rate": 0.157895,
    "cell_training_negative_count": 13,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ffe911c2088f42a2",
    "forbidden_signature_hash": "94bc86dc7e0423a8",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_ffe911c2088f42a2_6_5_12_11_10_18",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|4",
    "pool_signature_hash": "76f5f269e52fcc11",
    "pool_task_set_hash": "b8995e889fe16310",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 5.851378,
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord4_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_04_seed61306_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->6:low_risk:1",
      "6->5:low_risk:2",
      "5->12:low_risk:2",
      "12->11:low_risk:2",
      "11->10:low_risk:2",
      "10->18:low_risk:2",
      "18->0:low_risk:2"
    ],
    "target_priority_sequence": [
      6,
      5,
      12,
      11,
      10,
      18
    ],
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
    "true_dual_hash": "3bed7040b564e435",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_ffe911c2088f42a2_6_5_12_11_10_18_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "db0c1f2c45a0c84f",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_94989e70b81983eb_14_4_13_16_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 3,
    "cell_positive_rate": 0.125,
    "cell_training_negative_count": 19,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "94989e70b81983eb",
    "forbidden_signature_hash": "434de1d47f21c0d5",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_94989e70b81983eb_14_4_13_16",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|6",
    "pool_signature_hash": "62adf022ae0f62e0",
    "pool_task_set_hash": "d8d378ea700f9633",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 5.505544,
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord6_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->14:low_risk:1",
      "14->4:low_time:0",
      "4->13:low_energy:1",
      "13->0:low_time:0"
    ],
    "target_priority_sequence": [
      14,
      4,
      13
    ],
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
    "true_dual_hash": "10c5d24d15b7fe6c",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_94989e70b81983eb_14_4_13_16_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "520afd05a482d5e9",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3375e356a084eadb_12_5_1_9_7_15_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 3,
    "cell_positive_rate": 0.125,
    "cell_training_negative_count": 19,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "3375e356a084eadb",
    "forbidden_signature_hash": "8d50059d689b2887",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3375e356a084eadb_12_5_1_9_7_15",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|2",
    "pool_signature_hash": "b86b85a1777a7128",
    "pool_task_set_hash": "19f0f6cb6c508fef",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 5.156956,
    "source_file": "BPC_future/results/gat_same_run_gap_focused_ord2_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->5:low_risk:2",
      "5->1:low_time:0",
      "1->9:low_risk:2",
      "9->7:low_risk:2",
      "7->0:low_risk:2"
    ],
    "target_priority_sequence": [
      12,
      5,
      1,
      9,
      7
    ],
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
    "true_dual_hash": "aaea9214556f4f61",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3375e356a084eadb_12_5_1_9_7_15_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "c1dd396614b6fcc3",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_8_4_14_9_3_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 3,
    "cell_positive_rate": 0.125,
    "cell_training_negative_count": 19,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "a77e5457bde80b8e",
    "forbidden_signature_hash": "efeea73c001eabf6",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_8_4_14_9_3_13",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|8",
    "pool_signature_hash": "b7bd078f29df934d",
    "pool_task_set_hash": "4c99b33b1ffe8829",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 5.145577,
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord8_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->0:low_time:0"
    ],
    "target_priority_sequence": [
      8
    ],
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
    "true_dual_hash": "d2ea374c6f1b01b2",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_8_4_14_9_3_13_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "22baed86ddf23d15",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_7c518307952f17f7_19_2_8_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 3,
    "cell_positive_rate": 0.125,
    "cell_training_negative_count": 19,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7c518307952f17f7",
    "forbidden_signature_hash": "db575711fa559d70",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_7c518307952f17f7_19_2_8",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|6",
    "pool_signature_hash": "f0a36a19229897f6",
    "pool_task_set_hash": "24ef3d780ca7d29f",
    "positive_gap": 1,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 5.110579,
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord6_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->19:low_time:0",
      "19->2:low_risk:2",
      "2->8:low_risk:2",
      "8->0:low_time:0"
    ],
    "target_priority_sequence": [
      19,
      2,
      8
    ],
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
    "true_dual_hash": "ecdc1afd090a8d52",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_7c518307952f17f7_19_2_8_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "b385bb1cafde884c",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_aa6ac3757841f1b3_13_3_2_18_10_1_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 17,
    "cell_positive_rate": 0.414634,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "aa6ac3757841f1b3",
    "forbidden_signature_hash": "ec17776b9ea2b9e0",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_aa6ac3757841f1b3_13_3_2_18_10_1",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|3",
    "pool_signature_hash": "70e4dfba6a2de489",
    "pool_task_set_hash": "d38cc4a9bc6c538a",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 3.430738,
    "source_file": "BPC_future/results/gat_same_run_gap_focused_ord3_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
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
    "true_dual_hash": "f97516f02039c303",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_aa6ac3757841f1b3_13_3_2_18_10_1_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "0ca6979bb961a3dd",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_8af5db3562524c9f_11_4_9_5_1_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 17,
    "cell_positive_rate": 0.414634,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "8af5db3562524c9f",
    "forbidden_signature_hash": "8ce3fc284a217d5c",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_8af5db3562524c9f_11_4_9_5_1",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|3",
    "pool_signature_hash": "51e4ad7adf6e04c1",
    "pool_task_set_hash": "a782e0ad467ced57",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 3.395931,
    "source_file": "BPC_future/results/gat_same_run_gap_focused_ord3_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->11:low_risk:2",
      "11->4:low_time:0",
      "4->9:low_time:0",
      "9->5:low_time:0",
      "5->0:low_time:0"
    ],
    "target_priority_sequence": [
      11,
      4,
      9,
      5
    ],
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
    "true_dual_hash": "c7ad8eb19ca21bee",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_8af5db3562524c9f_11_4_9_5_1_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "5cb6c522a05a124e",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_a504ecc531a8f8b3_3_13_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 17,
    "cell_positive_rate": 0.414634,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "a504ecc531a8f8b3",
    "forbidden_signature_hash": "ffee33e0f5f13dad",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_a504ecc531a8f8b3_3_13_17",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|3",
    "pool_signature_hash": "53706f1884c682a9",
    "pool_task_set_hash": "7e5ae3e616b3a95c",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 3.395067,
    "source_file": "BPC_future/results/gat_same_run_gap_focused_ord3_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->0:low_risk:2"
    ],
    "target_priority_sequence": [
      3
    ],
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
    "true_dual_hash": "fd472aca89b38ca8",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_a504ecc531a8f8b3_3_13_17_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "c165c6e9753428fc",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_0c8ac146692baefa_13_14_2_18_10_1_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 17,
    "cell_positive_rate": 0.414634,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "0c8ac146692baefa",
    "forbidden_signature_hash": "9adf96bed089a64a",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_0c8ac146692baefa_13_14_2_18_10_1",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|3",
    "pool_signature_hash": "664057160a142598",
    "pool_task_set_hash": "4043a847157ced95",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 3.358809,
    "source_file": "BPC_future/results/gat_same_run_gap_focused_ord3_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_priority_sequence": [
      13
    ],
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
    "true_dual_hash": "3fea26dd49d52b77",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_0c8ac146692baefa_13_14_2_18_10_1_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "5053e72622eff22b",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_c7c654f79d6f4852_14_3_2_20_10_1_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 17,
    "cell_positive_rate": 0.414634,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "c7c654f79d6f4852",
    "forbidden_signature_hash": "cd032ba47583046c",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_c7c654f79d6f4852_14_3_2_20_10_1",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|3",
    "pool_signature_hash": "115cf20a7c62f7fc",
    "pool_task_set_hash": "a5927207514ffc35",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 2.905036,
    "source_file": "BPC_future/results/gat_same_run_gap_focused_ord3_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->3:low_risk:2",
      "3->2:low_risk:2",
      "2->20:low_risk:2",
      "20->10:low_risk:1",
      "10->1:low_risk:2",
      "1->0:low_time:0"
    ],
    "target_priority_sequence": [
      14,
      3,
      2,
      20,
      10,
      1
    ],
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
    "true_dual_hash": "7c9171ea78e05ff1",
    "worker_csv": "BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_c7c654f79d6f4852_14_3_2_20_10_1_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_5_1_2_4_7_13_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_5_1_2_4_7_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_5_1_2_4_7_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_5_1_2_4_7_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_5_1_2_4_7_13_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_5_1_2_4_7_13_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_5_1_2_4_7_13_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_5_1_2_4_7_13_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=fbfd88d4ebde5459 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,1,2,4,7,13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,1,2,4,7,13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,1,2,4,7,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->1:low_risk:2","1->2:low_risk:2","2->4:low_risk:2","4->7:low_risk:2","7->13:low_risk:2","13->0:low_risk:2"],"sequence":[5,1,2,4,7,13],"start_time":12.976513}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->1:low_risk:2,1->2:low_risk:2,2->4:low_risk:2,4->7:low_risk:2,7->13:low_risk:2,13->0:low_risk:2'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_13_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_13_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_13_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_13_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_13_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=3100b787bf438dfe --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,1,2,4,11,13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,1,2,4,11,13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,1,2,4,11,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_time:0","5->1:low_risk:2","1->2:low_time:0","2->4:low_time:0","4->11:low_risk:2","11->13:low_risk:2","13->0:low_time:0"],"sequence":[5,1,2,4,11,13],"start_time":13.918479}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_time:0,5->1:low_risk:2,1->2:low_time:0,2->4:low_time:0,4->11:low_risk:2,11->13:low_risk:2,13->0:low_time:0'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_13_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_13_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_13_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_13_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_13_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=409f65576794fa39 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,20,13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,20,13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,20,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_time:0","8->20:low_energy:1","20->13:low_time:0","13->0:low_time:0"],"sequence":[8,20,13],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_time:0,8->20:low_energy:1,20->13:low_time:0,13->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_5f4498eb39858b1d_5_6_10_7_13_11_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_5f4498eb39858b1d_5_6_10_7_13_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_5f4498eb39858b1d_5_6_10_7_13_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_5f4498eb39858b1d_5_6_10_7_13_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_5f4498eb39858b1d_5_6_10_7_13_11_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_5f4498eb39858b1d_5_6_10_7_13_11_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_5f4498eb39858b1d_5_6_10_7_13_11_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_5f4498eb39858b1d_5_6_10_7_13_11_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=5f4498eb39858b1d --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,6,10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,6,10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,6,10,7,13,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->6:low_risk:2","6->10:low_energy:1","10->0:low_risk:2"],"sequence":[5,6,10],"start_time":10.218359},{"arc_option_sequence":["0->7:low_risk:2","7->13:low_time:0","13->11:low_risk:2","11->0:low_time:0"],"sequence":[7,13,11],"start_time":331.722549}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->6:low_risk:2,6->10:low_energy:1,10->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_8f2088cfefc3e3b1_20_3_7_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_8f2088cfefc3e3b1_20_3_7_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_8f2088cfefc3e3b1_20_3_7_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_8f2088cfefc3e3b1_20_3_7_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_8f2088cfefc3e3b1_20_3_7_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_8f2088cfefc3e3b1_20_3_7_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_8f2088cfefc3e3b1_20_3_7_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_8f2088cfefc3e3b1_20_3_7_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=8f2088cfefc3e3b1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,3,7 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_risk:2","20->0:low_risk:2"],"sequence":[20],"start_time":0.0},{"arc_option_sequence":["0->3:low_risk:2","3->7:low_risk:2","7->0:low_risk:2"],"sequence":[3,7],"start_time":142.305648}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_risk:2,20->0:low_risk:2'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_2d9686e5aa73b5f3_9_19_1_16_11_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_2d9686e5aa73b5f3_9_19_1_16_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_2d9686e5aa73b5f3_9_19_1_16_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_2d9686e5aa73b5f3_9_19_1_16_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_2d9686e5aa73b5f3_9_19_1_16_11_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_2d9686e5aa73b5f3_9_19_1_16_11_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_2d9686e5aa73b5f3_9_19_1_16_11_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_2d9686e5aa73b5f3_9_19_1_16_11_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=2d9686e5aa73b5f3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=9,19,1,16,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=9,19,1,16,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=9,19,1,16,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->9:low_risk:2","9->19:low_risk:2","19->1:low_risk:2","1->16:low_risk:2","16->11:low_risk:2","11->0:low_risk:2"],"sequence":[9,19,1,16,11],"start_time":26.061884}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->9:low_risk:2,9->19:low_risk:2,19->1:low_risk:2,1->16:low_risk:2,16->11:low_risk:2,11->0:low_risk:2'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_5c6127a7add1e6f6_13_11_15_6_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_5c6127a7add1e6f6_13_11_15_6_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_5c6127a7add1e6f6_13_11_15_6_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_5c6127a7add1e6f6_13_11_15_6_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_5c6127a7add1e6f6_13_11_15_6_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_5c6127a7add1e6f6_13_11_15_6_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_5c6127a7add1e6f6_13_11_15_6_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_5c6127a7add1e6f6_13_11_15_6_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=5c6127a7add1e6f6 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13,11,15,6 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13,11,15,6 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,11,15,6 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_risk:2","13->11:low_time:0","11->15:low_risk:2","15->6:low_time:0","6->0:low_time:0"],"sequence":[13,11,15,6],"start_time":71.0893}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_risk:2,13->11:low_time:0,11->15:low_risk:2,15->6:low_time:0,6->0:low_time:0'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_ffe911c2088f42a2_6_5_12_11_10_18_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_04_seed61306_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_ffe911c2088f42a2_6_5_12_11_10_18_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_ffe911c2088f42a2_6_5_12_11_10_18_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_ffe911c2088f42a2_6_5_12_11_10_18_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_ffe911c2088f42a2_6_5_12_11_10_18_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_04_seed61306_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_ffe911c2088f42a2_6_5_12_11_10_18_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_ffe911c2088f42a2_6_5_12_11_10_18_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_ffe911c2088f42a2_6_5_12_11_10_18_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ffe911c2088f42a2 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=6,5,12,11,10,18 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=6,5,12,11,10,18 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=6,5,12,11,10,18 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->6:low_risk:1","6->5:low_risk:2","5->12:low_risk:2","12->11:low_risk:2","11->10:low_risk:2","10->18:low_risk:2","18->0:low_risk:2"],"sequence":[6,5,12,11,10,18],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->6:low_risk:1,6->5:low_risk:2,5->12:low_risk:2,12->11:low_risk:2,11->10:low_risk:2,10->18:low_risk:2,18->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_94989e70b81983eb_14_4_13_16_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_94989e70b81983eb_14_4_13_16_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_94989e70b81983eb_14_4_13_16_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_94989e70b81983eb_14_4_13_16_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_94989e70b81983eb_14_4_13_16_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_94989e70b81983eb_14_4_13_16_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_94989e70b81983eb_14_4_13_16_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_94989e70b81983eb_14_4_13_16_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=94989e70b81983eb --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=14,4,13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=14,4,13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=14,4,13,16 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->14:low_risk:1","14->4:low_time:0","4->13:low_energy:1","13->0:low_time:0"],"sequence":[14,4,13],"start_time":61.759229},{"arc_option_sequence":["0->16:low_risk:2","16->0:low_risk:2"],"sequence":[16],"start_time":415.5713}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->14:low_risk:1,14->4:low_time:0,4->13:low_energy:1,13->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3375e356a084eadb_12_5_1_9_7_15_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3375e356a084eadb_12_5_1_9_7_15_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3375e356a084eadb_12_5_1_9_7_15_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3375e356a084eadb_12_5_1_9_7_15_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3375e356a084eadb_12_5_1_9_7_15_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3375e356a084eadb_12_5_1_9_7_15_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3375e356a084eadb_12_5_1_9_7_15_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3375e356a084eadb_12_5_1_9_7_15_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=3375e356a084eadb --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,5,1,9,7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,5,1,9,7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,5,1,9,7,15 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_risk:2","12->5:low_risk:2","5->1:low_time:0","1->9:low_risk:2","9->7:low_risk:2","7->0:low_risk:2"],"sequence":[12,5,1,9,7],"start_time":17.038329},{"arc_option_sequence":["0->15:low_risk:2","15->0:low_risk:2"],"sequence":[15],"start_time":390.349024}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_risk:2,12->5:low_risk:2,5->1:low_time:0,1->9:low_risk:2,9->7:low_risk:2,7->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_8_4_14_9_3_13_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_8_4_14_9_3_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_8_4_14_9_3_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_8_4_14_9_3_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_8_4_14_9_3_13_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_8_4_14_9_3_13_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_8_4_14_9_3_13_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_8_4_14_9_3_13_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=a77e5457bde80b8e --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,4,14,9,3,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_time:0","8->0:low_time:0"],"sequence":[8],"start_time":0.0},{"arc_option_sequence":["0->4:low_energy:1","4->14:low_time:0","14->9:low_energy:1","9->3:low_time:0","3->13:low_time:0","13->0:low_energy:1"],"sequence":[4,14,9,3,13],"start_time":179.463458}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_time:0,8->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_7c518307952f17f7_19_2_8_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_7c518307952f17f7_19_2_8_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_7c518307952f17f7_19_2_8_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_7c518307952f17f7_19_2_8_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_7c518307952f17f7_19_2_8_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_7c518307952f17f7_19_2_8_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_7c518307952f17f7_19_2_8_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_7c518307952f17f7_19_2_8_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7c518307952f17f7 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=19,2,8 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=19,2,8 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=19,2,8 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->19:low_time:0","19->2:low_risk:2","2->8:low_risk:2","8->0:low_time:0"],"sequence":[19,2,8],"start_time":23.990832}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->19:low_time:0,19->2:low_risk:2,2->8:low_risk:2,8->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_aa6ac3757841f1b3_13_3_2_18_10_1_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_aa6ac3757841f1b3_13_3_2_18_10_1_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_aa6ac3757841f1b3_13_3_2_18_10_1_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_aa6ac3757841f1b3_13_3_2_18_10_1_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_aa6ac3757841f1b3_13_3_2_18_10_1_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_aa6ac3757841f1b3_13_3_2_18_10_1_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_aa6ac3757841f1b3_13_3_2_18_10_1_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_aa6ac3757841f1b3_13_3_2_18_10_1_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=aa6ac3757841f1b3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,3,2,18,10,1 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_risk:2","13->0:low_risk:2"],"sequence":[13],"start_time":0.0},{"arc_option_sequence":["0->3:low_risk:2","3->2:low_risk:2","2->18:low_risk:2","18->10:low_risk:2","10->1:low_risk:2","1->0:low_time:0"],"sequence":[3,2,18,10,1],"start_time":69.07485}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_risk:2,13->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_8af5db3562524c9f_11_4_9_5_1_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_8af5db3562524c9f_11_4_9_5_1_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_8af5db3562524c9f_11_4_9_5_1_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_8af5db3562524c9f_11_4_9_5_1_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_8af5db3562524c9f_11_4_9_5_1_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_8af5db3562524c9f_11_4_9_5_1_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_8af5db3562524c9f_11_4_9_5_1_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_8af5db3562524c9f_11_4_9_5_1_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=8af5db3562524c9f --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=11,4,9,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=11,4,9,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=11,4,9,5,1 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->11:low_risk:2","11->4:low_time:0","4->9:low_time:0","9->5:low_time:0","5->0:low_time:0"],"sequence":[11,4,9,5],"start_time":0.0},{"arc_option_sequence":["0->1:low_time:0","1->0:low_time:0"],"sequence":[1],"start_time":407.256981}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->11:low_risk:2,11->4:low_time:0,4->9:low_time:0,9->5:low_time:0,5->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_a504ecc531a8f8b3_3_13_17_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_a504ecc531a8f8b3_3_13_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_a504ecc531a8f8b3_3_13_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_a504ecc531a8f8b3_3_13_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_a504ecc531a8f8b3_3_13_17_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_a504ecc531a8f8b3_3_13_17_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_a504ecc531a8f8b3_3_13_17_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_a504ecc531a8f8b3_3_13_17_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=a504ecc531a8f8b3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,13,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_risk:2","3->0:low_risk:2"],"sequence":[3],"start_time":15.271817},{"arc_option_sequence":["0->13:low_risk:2","13->17:low_risk:2","17->0:low_time:0"],"sequence":[13,17],"start_time":91.522898}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_risk:2,3->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_0c8ac146692baefa_13_14_2_18_10_1_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_0c8ac146692baefa_13_14_2_18_10_1_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_0c8ac146692baefa_13_14_2_18_10_1_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_0c8ac146692baefa_13_14_2_18_10_1_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_0c8ac146692baefa_13_14_2_18_10_1_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_0c8ac146692baefa_13_14_2_18_10_1_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_0c8ac146692baefa_13_14_2_18_10_1_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_0c8ac146692baefa_13_14_2_18_10_1_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=0c8ac146692baefa --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,14,2,18,10,1 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_risk:2","13->0:low_risk:2"],"sequence":[13],"start_time":0.0},{"arc_option_sequence":["0->14:low_risk:2","14->2:low_time:0","2->18:low_risk:2","18->10:low_risk:2","10->1:low_risk:2","1->0:low_time:0"],"sequence":[14,2,18,10,1],"start_time":58.959462}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_risk:2,13->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_c7c654f79d6f4852_14_3_2_20_10_1_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_c7c654f79d6f4852_14_3_2_20_10_1_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_c7c654f79d6f4852_14_3_2_20_10_1_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_c7c654f79d6f4852_14_3_2_20_10_1_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_c7c654f79d6f4852_14_3_2_20_10_1_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_c7c654f79d6f4852_14_3_2_20_10_1_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_c7c654f79d6f4852_14_3_2_20_10_1_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v33_from_v32_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_03_seed61205_c7c654f79d6f4852_14_3_2_20_10_1_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=c7c654f79d6f4852 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=14,3,2,20,10,1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=14,3,2,20,10,1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=14,3,2,20,10,1 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->14:low_risk:2","14->3:low_risk:2","3->2:low_risk:2","2->20:low_risk:2","20->10:low_risk:1","10->1:low_risk:2","1->0:low_time:0"],"sequence":[14,3,2,20,10,1],"start_time":4.165907}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->14:low_risk:2,14->3:low_risk:2,3->2:low_risk:2,2->20:low_risk:2,20->10:low_risk:1,10->1:low_risk:2,1->0:low_time:0'
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
