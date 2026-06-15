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
    "active_hash_before": "3341a4ba541bfa32",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_1_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|apollo15_20km",
    "cell_positive_count": 5,
    "cell_positive_rate": 0.2,
    "cell_training_negative_count": 17,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "62c86745ed2b3aaa",
    "forbidden_signature_hash": "ddf56f63968049f0",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_1_10",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "pool_signature_hash": "50dc555c1757eeca",
    "pool_task_set_hash": "fdf2e77ba9b76816",
    "positive_gap": 7,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 45.708646,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->1:low_risk:2",
      "1->0:low_time:0"
    ],
    "target_priority_sequence": [
      1
    ],
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
    "true_dual_hash": "9bd9a1d18b7a5cf5",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_1_10_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "eb92a6a521734d12",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|apollo15_20km",
    "cell_positive_count": 5,
    "cell_positive_rate": 0.2,
    "cell_training_negative_count": 17,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "409f65576794fa39",
    "forbidden_signature_hash": "2759f01a2dec4e9a",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "pool_signature_hash": "61505b62c0f9a4a1",
    "pool_task_set_hash": "bba64460221b3547",
    "positive_gap": 7,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 44.8194,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->20:low_risk:2",
      "20->0:low_risk:2"
    ],
    "target_priority_sequence": [
      8,
      20
    ],
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
    "true_dual_hash": "efc2fb20ceb858b3",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "03a8d149c5bdfc16",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_6_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|apollo15_20km",
    "cell_positive_count": 5,
    "cell_positive_rate": 0.2,
    "cell_training_negative_count": 17,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "3100b787bf438dfe",
    "forbidden_signature_hash": "59f58c79d1e50d49",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_6",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|8",
    "pool_signature_hash": "7a249193fdd37789",
    "pool_task_set_hash": "e3f049a263f86c82",
    "positive_gap": 7,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 44.604358,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->2:low_risk:2",
      "2->4:low_risk:2",
      "4->11:low_risk:2",
      "11->6:low_risk:2",
      "6->0:low_risk:2"
    ],
    "target_priority_sequence": [
      5,
      1,
      2,
      4,
      11,
      6
    ],
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
    "true_dual_hash": "d4d21a0866a5f19c",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_6_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "05e452aa352874cd",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_9cb802808b9a3356_19_6_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|apollo15_20km",
    "cell_positive_count": 5,
    "cell_positive_rate": 0.2,
    "cell_training_negative_count": 17,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "9cb802808b9a3356",
    "forbidden_signature_hash": "c0b30757b93e2af2",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_9cb802808b9a3356_19_6_13",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|6",
    "pool_signature_hash": "282d861529661f7c",
    "pool_task_set_hash": "c99ec5f484dca958",
    "positive_gap": 7,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 27.689799,
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord6_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->19:low_time:0",
      "19->6:low_risk:2",
      "6->13:low_risk:2",
      "13->0:low_time:0"
    ],
    "target_priority_sequence": [
      19,
      6,
      13
    ],
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
    "true_dual_hash": "91685c5bd22052ec",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_9cb802808b9a3356_19_6_13_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "2b7d17df31de0a68",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_411d44c3e21bcb1f_17_18_9_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|apollo15_20km",
    "cell_positive_count": 5,
    "cell_positive_rate": 0.2,
    "cell_training_negative_count": 17,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "411d44c3e21bcb1f",
    "forbidden_signature_hash": "2f591733ba3de3f1",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_411d44c3e21bcb1f_17_18_9_5",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|7",
    "pool_signature_hash": "be632cace8973051",
    "pool_task_set_hash": "bacd75bd93f71e9e",
    "positive_gap": 7,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 27.54246,
    "source_file": "BPC_future/results/gat_same_run_random_wave_ord7_capture_runbook_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_07_seed61612_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->17:low_time:0",
      "17->18:low_risk:2",
      "18->9:low_time:0",
      "9->5:low_time:0",
      "5->0:low_risk:2"
    ],
    "target_priority_sequence": [
      17,
      18,
      9,
      5
    ],
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
    "true_dual_hash": "0e4f804b68c2ee6d",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_411d44c3e21bcb1f_17_18_9_5_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3f3606e7b26a6cfc",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_e978a55b1e53d13f_3_18_8_9_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|apollo15_20km",
    "cell_positive_count": 5,
    "cell_positive_rate": 0.2,
    "cell_training_negative_count": 17,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "e978a55b1e53d13f",
    "forbidden_signature_hash": "37abfa2909b26822",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_e978a55b1e53d13f_3_18_8_9",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|apollo15_20km|10",
    "pool_signature_hash": "11c553d09c3a264d",
    "pool_task_set_hash": "3bd4921eb0bcec7d",
    "positive_gap": 7,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 27.503868,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->0:low_time:0"
    ],
    "target_priority_sequence": [
      3
    ],
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
    "true_dual_hash": "707af46274d67d3a",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_e978a55b1e53d13f_3_18_8_9_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "7ecd36ca50af55f8",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_5_16_1_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 4,
    "cell_positive_rate": 0.133333,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "da555dc83edc174c",
    "forbidden_signature_hash": "f8cedff217e2a211",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_5_16_1",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|10",
    "pool_signature_hash": "abbfed8882abbb97",
    "pool_task_set_hash": "fec52a4ed3d6375b",
    "positive_gap": 8,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 24.599275,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->5:low_energy:1",
      "5->16:low_energy:1",
      "16->1:low_time:0",
      "1->0:low_energy:1"
    ],
    "target_priority_sequence": [
      5,
      16,
      1
    ],
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
    "true_dual_hash": "4197690e912b9c36",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_5_16_1_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "51df5d79e9ac45ae",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_10_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 4,
    "cell_positive_rate": 0.133333,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "08b8d772e2ab9623",
    "forbidden_signature_hash": "0c230e1a6c7fee96",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_10_11",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|3",
    "pool_signature_hash": "07ce45c4b7ea1c45",
    "pool_task_set_hash": "ba7679f84bbb38ae",
    "positive_gap": 8,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 23.733816,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->10:low_time:0",
      "10->11:low_time:0",
      "11->0:low_risk:2"
    ],
    "target_priority_sequence": [
      10,
      11
    ],
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
    "true_dual_hash": "c923eda9f0bcc8d2",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_10_11_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "86d9789a5b8352f0",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_12_5_8_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 4,
    "cell_positive_rate": 0.133333,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ec59d1f203f1630c",
    "forbidden_signature_hash": "a9b02ad000676eeb",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_12_5_8",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|10",
    "pool_signature_hash": "b22e9d42681f1d67",
    "pool_task_set_hash": "c400b3d02d0fc424",
    "positive_gap": 8,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 23.599419,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->0:low_risk:2"
    ],
    "target_priority_sequence": [
      12
    ],
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
    "true_dual_hash": "e408b632cdf39f5e",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_12_5_8_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "622200ad1fc583cc",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_10_11_14_9_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 4,
    "cell_positive_rate": 0.133333,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "e897b76f2888f822",
    "forbidden_signature_hash": "7b7bc18b58faa1db",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_10_11_14_9",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|3",
    "pool_signature_hash": "cbd4c17130829b87",
    "pool_task_set_hash": "71fc2cca8fb5ace4",
    "positive_gap": 8,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 23.434366,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->10:low_time:0",
      "10->11:low_time:0",
      "11->0:low_risk:2"
    ],
    "target_priority_sequence": [
      10,
      11
    ],
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
    "true_dual_hash": "ed98088cdfa83a03",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_10_11_14_9_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "950498a3c24cb589",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_09_seed61820_7cb380a02e30e5a8_14_6_7_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 4,
    "cell_positive_rate": 0.133333,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7cb380a02e30e5a8",
    "forbidden_signature_hash": "5cd3c347558839d5",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_09_seed61820_7cb380a02e30e5a8_14_6_7",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|9",
    "pool_signature_hash": "7ef6419dc8239cb4",
    "pool_task_set_hash": "dad9d51aaf8ae5e1",
    "positive_gap": 8,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 23.276125,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->0:low_risk:2"
    ],
    "target_priority_sequence": [
      14
    ],
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
    "true_dual_hash": "51702c3dec001ab6",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_09_seed61820_7cb380a02e30e5a8_14_6_7_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "c1dd396614b6fcc3",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_18_4_3_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "random-wave|tranquillitatis_balmer_like_20km",
    "cell_positive_count": 4,
    "cell_positive_rate": 0.133333,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "a77e5457bde80b8e",
    "forbidden_signature_hash": "efeea73c001eabf6",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_18_4_3_13",
    "negative_gap": 0,
    "ordinal_cell": "random-wave|tranquillitatis_balmer_like_20km|8",
    "pool_signature_hash": "b7bd078f29df934d",
    "pool_task_set_hash": "4c99b33b1ffe8829",
    "positive_gap": 8,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 22.989605,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->18:low_energy:1",
      "18->4:low_energy:1",
      "4->0:low_energy:1"
    ],
    "target_priority_sequence": [
      18,
      4
    ],
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
    "true_dual_hash": "d2ea374c6f1b01b2",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_18_4_3_13_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "4cc24e29b5b5bc64",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_43dcab2f9dde0fc6_20_7_14_13_11_4_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|apollo15_20km",
    "cell_positive_count": 10,
    "cell_positive_rate": 0.277778,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "43dcab2f9dde0fc6",
    "forbidden_signature_hash": "d70b88300dacc227",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_43dcab2f9dde0fc6_20_7_14_13_11_4_17",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|apollo15_20km|2",
    "pool_signature_hash": "2aa70182537b5744",
    "pool_task_set_hash": "99618ce9f91e5c3b",
    "positive_gap": 2,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 15.984911,
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json.jsonl",
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
    "true_dual_hash": "803930670c9b7c3e",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_43dcab2f9dde0fc6_20_7_14_13_11_4_17_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "9b65d1ccd219057e",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c97a1cf4f842dd6c_3_5_11_4_2_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|apollo15_20km",
    "cell_positive_count": 10,
    "cell_positive_rate": 0.277778,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "c97a1cf4f842dd6c",
    "forbidden_signature_hash": "bbe4d9823521bc46",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c97a1cf4f842dd6c_3_5_11_4_2",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|apollo15_20km|2",
    "pool_signature_hash": "7b871b6ac0a97331",
    "pool_task_set_hash": "e6cfea636ca0ef92",
    "positive_gap": 2,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 15.920697,
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json.jsonl",
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
    "true_dual_hash": "d8913862cdbef9fc",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c97a1cf4f842dd6c_3_5_11_4_2_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3448ff27bd84701d",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_d66c7e548fe94bd5_12_2_8_10_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|apollo15_20km",
    "cell_positive_count": 10,
    "cell_positive_rate": 0.277778,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "d66c7e548fe94bd5",
    "forbidden_signature_hash": "503c2e9e52dc6c05",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_d66c7e548fe94bd5_12_2_8_10_17",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|apollo15_20km|2",
    "pool_signature_hash": "610f643bbe1c48e2",
    "pool_task_set_hash": "e6cfea636ca0ef92",
    "positive_gap": 2,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 15.913295,
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json.jsonl",
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
    "true_dual_hash": "c20643a988836b9c",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_d66c7e548fe94bd5_12_2_8_10_17_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3ca14dba75894c6f",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_6_20_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|apollo15_20km",
    "cell_positive_count": 10,
    "cell_positive_rate": 0.277778,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "1fa17aea2063098d",
    "forbidden_signature_hash": "5559157b1af629c3",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_6_20_11",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|apollo15_20km|3",
    "pool_signature_hash": "8a1916cc5ebaa441",
    "pool_task_set_hash": "961b82b5eee8dfe0",
    "positive_gap": 2,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 12.587173,
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json.jsonl",
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
    "true_dual_hash": "09d58d42a46b577b",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_6_20_11_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "13107ac7c4d480c2",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_fec7e16a3758171c_13_5_12_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|apollo15_20km",
    "cell_positive_count": 10,
    "cell_positive_rate": 0.277778,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "fec7e16a3758171c",
    "forbidden_signature_hash": "fdaffe3cde3b498f",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_fec7e16a3758171c_13_5_12_10",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|apollo15_20km|3",
    "pool_signature_hash": "d1ce044825e59261",
    "pool_task_set_hash": "5c04e222ccbca69f",
    "positive_gap": 2,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 12.453476,
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json.jsonl",
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
    "true_dual_hash": "b3a964e273809348",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_fec7e16a3758171c_13_5_12_10_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "da3932a04297ce01",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_19758e70e56ed7e7_13_3_19_7_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "sector-wave|apollo15_20km",
    "cell_positive_count": 10,
    "cell_positive_rate": 0.277778,
    "cell_training_negative_count": 24,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "19758e70e56ed7e7",
    "forbidden_signature_hash": "90773505d87758ac",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_19758e70e56ed7e7_13_3_19_7",
    "negative_gap": 0,
    "ordinal_cell": "sector-wave|apollo15_20km|3",
    "pool_signature_hash": "5aeac7911c50e0dc",
    "pool_task_set_hash": "e9b74f32d120ab0d",
    "positive_gap": 2,
    "reason": "positive_gap_with_negative_support",
    "recommendation_bucket": "positive_gap_explore",
    "score": 11.464607,
    "source_file": "BPC_future/results/gat_same_run_batch_impact_audit_ab_runbook_seed_20260615/task020_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json.jsonl",
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
    "true_dual_hash": "6ac906efca5737d6",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_19758e70e56ed7e7_13_3_19_7_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "e5d989275b12a554",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_453b7d680cd04697_2_13_11_12_14_18_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 17,
    "cell_positive_rate": 0.369565,
    "cell_training_negative_count": 28,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "453b7d680cd04697",
    "forbidden_signature_hash": "0287e5c37b46ec43",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_453b7d680cd04697_2_13_11_12_14_18",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|6",
    "pool_signature_hash": "da52482a46dee291",
    "pool_task_set_hash": "4cc07b9527a8442e",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 3.782203,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_priority_sequence": [
      2,
      13
    ],
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
    "true_dual_hash": "7c0ee4cff79aa555",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_453b7d680cd04697_2_13_11_12_14_18_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "d9c2b511b8c9398b",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_370fd4c047e0a42c_3_2_9_6_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 17,
    "cell_positive_rate": 0.369565,
    "cell_training_negative_count": 28,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "370fd4c047e0a42c",
    "forbidden_signature_hash": "e5a442a3d8d78d2e",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_370fd4c047e0a42c_3_2_9_6",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|6",
    "pool_signature_hash": "ebcd0be23e73ec7f",
    "pool_task_set_hash": "791323a96cf45e2d",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 3.702163,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->2:low_risk:2",
      "2->9:low_time:0",
      "9->0:low_time:0"
    ],
    "target_priority_sequence": [
      3,
      2,
      9
    ],
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
    "true_dual_hash": "51d177f1ededb626",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_370fd4c047e0a42c_3_2_9_6_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "0780f9f032c659a7",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_5_20_3_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 17,
    "cell_positive_rate": 0.369565,
    "cell_training_negative_count": 28,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "22dec9cfc13bb3d6",
    "forbidden_signature_hash": "9324e282befa1ac8",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_5_20_3",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|8",
    "pool_signature_hash": "b8aa00efb6e169f6",
    "pool_task_set_hash": "a98072364d0bfc1e",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 3.505582,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave04/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->20:low_risk:1",
      "20->0:low_risk:1"
    ],
    "target_priority_sequence": [
      5,
      20
    ],
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
    "true_dual_hash": "f41cb57ae52a541e",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_5_20_3_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "4799ece3f3778c1d",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_165e10ca9c212e34_12_15_6_19_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 17,
    "cell_positive_rate": 0.369565,
    "cell_training_negative_count": 28,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "165e10ca9c212e34",
    "forbidden_signature_hash": "bc6c99de1633c549",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_165e10ca9c212e34_12_15_6_19",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|8",
    "pool_signature_hash": "68a7c626fa03980d",
    "pool_task_set_hash": "8df343753a026328",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 3.331325,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave04/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->15:low_time:0",
      "15->0:low_time:0"
    ],
    "target_priority_sequence": [
      12,
      15
    ],
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
    "true_dual_hash": "933a95bfc92ef7b3",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_165e10ca9c212e34_12_15_6_19_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "517ef99313f19406",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_1_8_4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 17,
    "cell_positive_rate": 0.369565,
    "cell_training_negative_count": 28,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "26b1956faca276a4",
    "forbidden_signature_hash": "3c1ca0479a0423a8",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_1_8_4",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|6",
    "pool_signature_hash": "a680790d9f31e526",
    "pool_task_set_hash": "f0c4222586112e82",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 3.310898,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->3:low_risk:1",
      "3->0:low_risk:1"
    ],
    "target_priority_sequence": [
      3
    ],
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
    "true_dual_hash": "7351bac64f33621b",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_1_8_4_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "517ef99313f19406",
    "baseline_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_13_17_11_12_14_18_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell": "greedy-anchor|apollo15_20km",
    "cell_positive_count": 17,
    "cell_positive_rate": 0.369565,
    "cell_training_negative_count": 28,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "26b1956faca276a4",
    "forbidden_signature_hash": "3c1ca0479a0423a8",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_13_17_11_12_14_18",
    "negative_gap": 0,
    "ordinal_cell": "greedy-anchor|apollo15_20km|6",
    "pool_signature_hash": "a680790d9f31e526",
    "pool_task_set_hash": "f0c4222586112e82",
    "positive_gap": 0,
    "reason": "candidate_pool_high_score",
    "recommendation_bucket": "positive_rich_exploit",
    "score": 3.306139,
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->3:low_risk:1",
      "3->0:low_risk:1"
    ],
    "target_priority_sequence": [
      3
    ],
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
    "true_dual_hash": "7351bac64f33621b",
    "worker_csv": "BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_13_17_11_12_14_18_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_1_10_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_1_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_1_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_1_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_1_10_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_1_10_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_1_10_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_1_10_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=62c86745ed2b3aaa --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=1,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->1:low_risk:2","1->0:low_time:0"],"sequence":[1],"start_time":57.409177},{"arc_option_sequence":["0->10:low_time:0","10->0:low_risk:2"],"sequence":[10],"start_time":174.386986}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->1:low_risk:2,1->0:low_time:0'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=409f65576794fa39 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,20 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_time:0","8->20:low_risk:2","20->0:low_risk:2"],"sequence":[8,20],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_time:0,8->20:low_risk:2,20->0:low_risk:2'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_6_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_6_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_6_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_6_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_6_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_6_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_6_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_6_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=3100b787bf438dfe --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,1,2,4,11,6 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,1,2,4,11,6 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,1,2,4,11,6 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->1:low_risk:2","1->2:low_risk:2","2->4:low_risk:2","4->11:low_risk:2","11->6:low_risk:2","6->0:low_risk:2"],"sequence":[5,1,2,4,11,6],"start_time":11.291563}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->1:low_risk:2,1->2:low_risk:2,2->4:low_risk:2,4->11:low_risk:2,11->6:low_risk:2,6->0:low_risk:2'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_9cb802808b9a3356_19_6_13_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_9cb802808b9a3356_19_6_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_9cb802808b9a3356_19_6_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_9cb802808b9a3356_19_6_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_9cb802808b9a3356_19_6_13_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_9cb802808b9a3356_19_6_13_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_9cb802808b9a3356_19_6_13_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_9cb802808b9a3356_19_6_13_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=9cb802808b9a3356 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=19,6,13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=19,6,13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=19,6,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->19:low_time:0","19->6:low_risk:2","6->13:low_risk:2","13->0:low_time:0"],"sequence":[19,6,13],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->19:low_time:0,19->6:low_risk:2,6->13:low_risk:2,13->0:low_time:0'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_411d44c3e21bcb1f_17_18_9_5_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_07_seed61612_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_411d44c3e21bcb1f_17_18_9_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_411d44c3e21bcb1f_17_18_9_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_411d44c3e21bcb1f_17_18_9_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_411d44c3e21bcb1f_17_18_9_5_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_07_seed61612_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_411d44c3e21bcb1f_17_18_9_5_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_411d44c3e21bcb1f_17_18_9_5_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_411d44c3e21bcb1f_17_18_9_5_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=411d44c3e21bcb1f --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=17,18,9,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=17,18,9,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=17,18,9,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->17:low_time:0","17->18:low_risk:2","18->9:low_time:0","9->5:low_time:0","5->0:low_risk:2"],"sequence":[17,18,9,5],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->17:low_time:0,17->18:low_risk:2,18->9:low_time:0,9->5:low_time:0,5->0:low_risk:2'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_e978a55b1e53d13f_3_18_8_9_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_e978a55b1e53d13f_3_18_8_9_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_e978a55b1e53d13f_3_18_8_9_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_e978a55b1e53d13f_3_18_8_9_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_e978a55b1e53d13f_3_18_8_9_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_e978a55b1e53d13f_3_18_8_9_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_e978a55b1e53d13f_3_18_8_9_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_e978a55b1e53d13f_3_18_8_9_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=e978a55b1e53d13f --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,18,8,9 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_time:0","3->0:low_time:0"],"sequence":[3],"start_time":0.0},{"arc_option_sequence":["0->18:low_time:0","18->8:low_risk:2","8->9:low_risk:2","9->0:low_time:0"],"sequence":[18,8,9],"start_time":161.492434}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_time:0,3->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_5_16_1_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_5_16_1_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_5_16_1_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_5_16_1_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_5_16_1_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_5_16_1_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_5_16_1_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_5_16_1_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=da555dc83edc174c --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,16,1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,16,1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,16,1 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_energy:1","5->16:low_energy:1","16->1:low_time:0","1->0:low_energy:1"],"sequence":[5,16,1],"start_time":53.794396}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_energy:1,5->16:low_energy:1,16->1:low_time:0,1->0:low_energy:1'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_10_11_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_10_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_10_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_10_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_10_11_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_10_11_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_10_11_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_10_11_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=08b8d772e2ab9623 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=10,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=10,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=10,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->10:low_time:0","10->11:low_time:0","11->0:low_risk:2"],"sequence":[10,11],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->10:low_time:0,10->11:low_time:0,11->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_12_5_8_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_12_5_8_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_12_5_8_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_12_5_8_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_12_5_8_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_12_5_8_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_12_5_8_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_12_5_8_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ec59d1f203f1630c --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,5,8 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_time:0","12->0:low_risk:2"],"sequence":[12],"start_time":0.0},{"arc_option_sequence":["0->5:low_energy:1","5->8:low_time:0","8->0:low_energy:1"],"sequence":[5,8],"start_time":123.356368}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_time:0,12->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_10_11_14_9_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_10_11_14_9_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_10_11_14_9_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_10_11_14_9_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_10_11_14_9_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_10_11_14_9_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_10_11_14_9_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_10_11_14_9_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=e897b76f2888f822 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=10,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=10,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=10,11,14,9 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->10:low_time:0","10->11:low_time:0","11->0:low_risk:2"],"sequence":[10,11],"start_time":0.0},{"arc_option_sequence":["0->14:low_time:0","14->9:low_risk:2","9->0:low_risk:2"],"sequence":[14,9],"start_time":299.342015}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->10:low_time:0,10->11:low_time:0,11->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_09_seed61820_7cb380a02e30e5a8_14_6_7_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_09_seed61820_7cb380a02e30e5a8_14_6_7_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_09_seed61820_7cb380a02e30e5a8_14_6_7_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_09_seed61820_7cb380a02e30e5a8_14_6_7_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_09_seed61820_7cb380a02e30e5a8_14_6_7_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_09_seed61820_7cb380a02e30e5a8_14_6_7_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_09_seed61820_7cb380a02e30e5a8_14_6_7_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_09_seed61820_7cb380a02e30e5a8_14_6_7_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7cb380a02e30e5a8 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=14 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=14 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=14,6,7 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->14:low_risk:2","14->0:low_risk:2"],"sequence":[14],"start_time":0.0},{"arc_option_sequence":["0->6:low_time:0","6->7:low_risk:2","7->0:low_risk:2"],"sequence":[6,7],"start_time":271.117057}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->14:low_risk:2,14->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_18_4_3_13_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_18_4_3_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_18_4_3_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_18_4_3_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_18_4_3_13_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_18_4_3_13_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_18_4_3_13_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_18_4_3_13_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=a77e5457bde80b8e --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=18,4 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=18,4 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=18,4,3,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->18:low_energy:1","18->4:low_energy:1","4->0:low_energy:1"],"sequence":[18,4],"start_time":0.0},{"arc_option_sequence":["0->3:low_risk:2","3->13:low_risk:2","13->0:low_risk:2"],"sequence":[3,13],"start_time":345.431386}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->18:low_energy:1,18->4:low_energy:1,4->0:low_energy:1'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_43dcab2f9dde0fc6_20_7_14_13_11_4_17_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_43dcab2f9dde0fc6_20_7_14_13_11_4_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_43dcab2f9dde0fc6_20_7_14_13_11_4_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_43dcab2f9dde0fc6_20_7_14_13_11_4_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_43dcab2f9dde0fc6_20_7_14_13_11_4_17_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_43dcab2f9dde0fc6_20_7_14_13_11_4_17_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_43dcab2f9dde0fc6_20_7_14_13_11_4_17_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_43dcab2f9dde0fc6_20_7_14_13_11_4_17_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=43dcab2f9dde0fc6 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,7,14 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,7,14 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,7,14,13,11,4,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_risk:2","20->7:low_risk:1","7->14:low_time:0","14->0:low_risk:2"],"sequence":[20,7,14],"start_time":12.274109},{"arc_option_sequence":["0->13:low_risk:2","13->11:low_time:0","11->4:low_risk:1","4->17:low_risk:2","17->0:low_risk:2"],"sequence":[13,11,4,17],"start_time":326.644296}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_risk:2,20->7:low_risk:1,7->14:low_time:0,14->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c97a1cf4f842dd6c_3_5_11_4_2_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c97a1cf4f842dd6c_3_5_11_4_2_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c97a1cf4f842dd6c_3_5_11_4_2_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c97a1cf4f842dd6c_3_5_11_4_2_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c97a1cf4f842dd6c_3_5_11_4_2_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c97a1cf4f842dd6c_3_5_11_4_2_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c97a1cf4f842dd6c_3_5_11_4_2_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c97a1cf4f842dd6c_3_5_11_4_2_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=c97a1cf4f842dd6c --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,5,11,4,2 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_time:0","3->5:low_risk:2","5->0:low_risk:2"],"sequence":[3,5],"start_time":0.0},{"arc_option_sequence":["0->11:low_risk:2","11->4:low_risk:1","4->2:low_risk:1","2->0:low_risk:2"],"sequence":[11,4,2],"start_time":307.81881}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_time:0,3->5:low_risk:2,5->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_d66c7e548fe94bd5_12_2_8_10_17_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_d66c7e548fe94bd5_12_2_8_10_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_d66c7e548fe94bd5_12_2_8_10_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_d66c7e548fe94bd5_12_2_8_10_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_d66c7e548fe94bd5_12_2_8_10_17_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_d66c7e548fe94bd5_12_2_8_10_17_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_d66c7e548fe94bd5_12_2_8_10_17_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_d66c7e548fe94bd5_12_2_8_10_17_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=d66c7e548fe94bd5 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,2,8,10,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_risk:2","12->0:low_risk:2"],"sequence":[12],"start_time":0.0},{"arc_option_sequence":["0->2:low_risk:2","2->8:low_risk:1","8->10:low_risk:2","10->17:low_risk:1","17->0:low_risk:2"],"sequence":[2,8,10,17],"start_time":274.382116}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_risk:2,12->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_6_20_11_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_6_20_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_6_20_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_6_20_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_6_20_11_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_6_20_11_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_6_20_11_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_6_20_11_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=1fa17aea2063098d --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,6,20,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_time:0","4->0:low_time:0"],"sequence":[4],"start_time":0.0},{"arc_option_sequence":["0->6:low_risk:2","6->20:low_time:0","20->11:low_time:0","11->0:low_risk:2"],"sequence":[6,20,11],"start_time":240.88539}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_time:0,4->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_fec7e16a3758171c_13_5_12_10_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_fec7e16a3758171c_13_5_12_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_fec7e16a3758171c_13_5_12_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_fec7e16a3758171c_13_5_12_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_fec7e16a3758171c_13_5_12_10_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_fec7e16a3758171c_13_5_12_10_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_fec7e16a3758171c_13_5_12_10_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_fec7e16a3758171c_13_5_12_10_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=fec7e16a3758171c --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13,5,12,10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13,5,12,10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,5,12,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_risk:2","13->5:low_risk:2","5->12:low_risk:2","12->10:low_risk:2","10->0:low_risk:2"],"sequence":[13,5,12,10],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_risk:2,13->5:low_risk:2,5->12:low_risk:2,12->10:low_risk:2,10->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_19758e70e56ed7e7_13_3_19_7_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_19758e70e56ed7e7_13_3_19_7_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_19758e70e56ed7e7_13_3_19_7_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_19758e70e56ed7e7_13_3_19_7_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_19758e70e56ed7e7_13_3_19_7_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_19758e70e56ed7e7_13_3_19_7_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_19758e70e56ed7e7_13_3_19_7_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_19758e70e56ed7e7_13_3_19_7_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=19758e70e56ed7e7 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,3,19,7 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_risk:2","13->0:low_risk:2"],"sequence":[13],"start_time":0.0},{"arc_option_sequence":["0->3:low_time:0","3->19:low_risk:2","19->7:low_risk:2","7->0:low_risk:2"],"sequence":[3,19,7],"start_time":115.963142}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_risk:2,13->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_453b7d680cd04697_2_13_11_12_14_18_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_453b7d680cd04697_2_13_11_12_14_18_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_453b7d680cd04697_2_13_11_12_14_18_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_453b7d680cd04697_2_13_11_12_14_18_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_453b7d680cd04697_2_13_11_12_14_18_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_453b7d680cd04697_2_13_11_12_14_18_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_453b7d680cd04697_2_13_11_12_14_18_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_453b7d680cd04697_2_13_11_12_14_18_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=453b7d680cd04697 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=2,13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=2,13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=2,13,11,12,14,18 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->2:low_risk:2","2->13:low_risk:2","13->0:low_risk:2"],"sequence":[2,13],"start_time":0.0},{"arc_option_sequence":["0->11:low_risk:2","11->12:low_risk:2","12->14:low_energy:1","14->18:low_time:0","18->0:low_risk:2"],"sequence":[11,12,14,18],"start_time":136.354496}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->2:low_risk:2,2->13:low_risk:2,13->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_370fd4c047e0a42c_3_2_9_6_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_370fd4c047e0a42c_3_2_9_6_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_370fd4c047e0a42c_3_2_9_6_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_370fd4c047e0a42c_3_2_9_6_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_370fd4c047e0a42c_3_2_9_6_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_370fd4c047e0a42c_3_2_9_6_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_370fd4c047e0a42c_3_2_9_6_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_370fd4c047e0a42c_3_2_9_6_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=370fd4c047e0a42c --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3,2,9 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3,2,9 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,2,9,6 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_time:0","3->2:low_risk:2","2->9:low_time:0","9->0:low_time:0"],"sequence":[3,2,9],"start_time":0.0},{"arc_option_sequence":["0->6:low_risk:2","6->0:low_time:0"],"sequence":[6],"start_time":277.996588}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_time:0,3->2:low_risk:2,2->9:low_time:0,9->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_5_20_3_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_5_20_3_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_5_20_3_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_5_20_3_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_5_20_3_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_5_20_3_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_5_20_3_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_22dec9cfc13bb3d6_5_20_3_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=22dec9cfc13bb3d6 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,20,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->20:low_risk:1","20->0:low_risk:1"],"sequence":[5,20],"start_time":43.068364},{"arc_option_sequence":["0->3:low_risk:2","3->0:low_risk:2"],"sequence":[3],"start_time":290.731573}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->20:low_risk:1,20->0:low_risk:1'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_165e10ca9c212e34_12_15_6_19_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_165e10ca9c212e34_12_15_6_19_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_165e10ca9c212e34_12_15_6_19_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_165e10ca9c212e34_12_15_6_19_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_165e10ca9c212e34_12_15_6_19_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_165e10ca9c212e34_12_15_6_19_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_165e10ca9c212e34_12_15_6_19_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_08_seed61716_165e10ca9c212e34_12_15_6_19_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=165e10ca9c212e34 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,15 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,15 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,15,6,19 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_risk:2","12->15:low_time:0","15->0:low_time:0"],"sequence":[12,15],"start_time":0.0},{"arc_option_sequence":["0->6:low_time:0","6->19:low_time:0","19->0:low_risk:2"],"sequence":[6,19],"start_time":410.34574}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_risk:2,12->15:low_time:0,15->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_1_8_4_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_1_8_4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_1_8_4_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_1_8_4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_1_8_4_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_1_8_4_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_1_8_4_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_1_8_4_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=26b1956faca276a4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,1,8,4 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_risk:1","3->0:low_risk:1"],"sequence":[3],"start_time":0.0},{"arc_option_sequence":["0->1:low_time:0","1->8:low_risk:2","8->4:low_time:0","4->0:low_time:0"],"sequence":[1,8,4],"start_time":147.079424}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_risk:1,3->0:low_risk:1'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_13_17_11_12_14_18_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_13_17_11_12_14_18_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_13_17_11_12_14_18_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_13_17_11_12_14_18_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_13_17_11_12_14_18_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_13_17_11_12_14_18_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_13_17_11_12_14_18_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_v34_from_v33_worker_ab_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_26b1956faca276a4_3_13_17_11_12_14_18_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=26b1956faca276a4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,13,17,11,12,14,18 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_risk:1","3->0:low_risk:1"],"sequence":[3],"start_time":0.0},{"arc_option_sequence":["0->13:low_time:0","13->17:low_time:0","17->11:low_risk:2","11->12:low_time:0","12->14:low_energy:1","14->18:low_risk:2","18->0:low_time:0"],"sequence":[13,17,11,12,14,18],"start_time":69.943499}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_risk:1,3->0:low_risk:1'
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
