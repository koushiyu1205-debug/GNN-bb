# GAT Target-Priority Worker A/B Runbook

日期：2026-06-15

## 目的

生成下一轮 5/10 no-regression 与 20-task ROI A/B 命令。GAT 仍只负责 embedding / trajectory impact 表达，kNN/OOD 只做安全壳；通过安全壳的 true-RC negative 可优先进入 worker target，不通过的负列进入 DELAY_QUEUE，不能永久丢弃，也不能参与 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_runbook = current
status = ready
worker_method = target_materialization_fixed
worker_batch_size = 4
input_candidate_count = 24
candidate_group_count = 9
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
  "fixed_worker_scope": "same-context target materialization only; no Pulse search, harvest, archive, adaptive sharding, bound pruning, or certificate effect",
  "gat_role": "embedding_and_trajectory_impact_expression",
  "knn_ood_role": "safety_shell",
  "negative_discard_allowed": false,
  "safe_negative_action": "HIGH_PRIORITY",
  "unsafe_negative_action": "DELAY_QUEUE",
  "worker_batch_size": 4,
  "worker_method": "target_materialization_fixed",
  "worker_stage_policy": "match_capture_pricing_kind: heuristic_before_heuristic_exact_before_exact"
}
```

## Candidate Runs

```json
[
  {
    "active_hash_before": "db1b163885849bab",
    "baseline_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 4,
    "candidate_batch_target_sequences": [
      [
        8,
        11
      ],
      [
        2,
        4
      ],
      [
        2,
        3,
        18,
        11
      ],
      [
        5,
        1,
        2,
        15
      ]
    ],
    "candidate_context_complete": true,
    "candidate_names": [
      "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11",
      "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank2_2_4",
      "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank4_2_3_18_11",
      "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank5_5_1_2_15"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "d519291840dd7000",
    "forbidden_signature_hash": "8c559ff7a164a116",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4",
    "pool_signature_hash": "530406beed850f36",
    "pool_task_set_hash": "e8b7e3dc10f8202e",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->11:low_time:0",
      "11->0:low_time:0"
    ],
    "target_materialization_journey_count": 4,
    "target_priority_sequence": [
      8,
      11
    ],
    "target_sequence": [
      8,
      11,
      2,
      4,
      2,
      3,
      18,
      11,
      5,
      1,
      2,
      15
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->11:low_time:0",
          "11->0:low_time:0"
        ],
        "sequence": [
          8,
          11
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "7a8482acd5dc4633",
    "worker_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "8fea27ca936f24d2",
    "baseline_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3_batch4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 4,
    "candidate_batch_target_sequences": [
      [
        5,
        1,
        2,
        18,
        3
      ],
      [
        2,
        1,
        15,
        3
      ],
      [
        2,
        18,
        3,
        15
      ],
      [
        5,
        18,
        15,
        3
      ]
    ],
    "candidate_context_complete": true,
    "candidate_names": [
      "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3",
      "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank3_2_1_15_3",
      "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank4_2_18_3_15",
      "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank5_5_18_15_3"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "67c11b5ec80925ec",
    "forbidden_signature_hash": "19812e842cb95df9",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3_batch4",
    "pool_signature_hash": "549b0ebff4d503f5",
    "pool_task_set_hash": "27845f832af78f68",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->2:low_risk:2",
      "2->18:low_risk:2",
      "18->3:low_risk:2",
      "3->0:low_risk:2"
    ],
    "target_materialization_journey_count": 4,
    "target_priority_sequence": [
      5,
      1,
      2,
      18,
      3
    ],
    "target_sequence": [
      5,
      1,
      2,
      18,
      3,
      2,
      1,
      15,
      3,
      2,
      18,
      3,
      15,
      5,
      18,
      15,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->1:low_risk:2",
          "1->2:low_risk:2",
          "2->18:low_risk:2",
          "18->3:low_risk:2",
          "3->0:low_risk:2"
        ],
        "sequence": [
          5,
          1,
          2,
          18,
          3
        ],
        "start_time": 11.291563
      }
    ],
    "true_dual_hash": "8d0b48016c368950",
    "worker_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3_batch4_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "eb92a6a521734d12",
    "baseline_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "409f65576794fa39",
    "forbidden_signature_hash": "2759f01a2dec4e9a",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13",
    "pool_signature_hash": "61505b62c0f9a4a1",
    "pool_task_set_hash": "bba64460221b3547",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->17:low_time:0",
      "17->0:low_risk:2"
    ],
    "target_priority_sequence": [
      17
    ],
    "target_sequence": [
      17,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->17:low_time:0",
          "17->0:low_risk:2"
        ],
        "sequence": [
          17
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->0:low_risk:2"
        ],
        "sequence": [
          13
        ],
        "start_time": 376.101788
      }
    ],
    "true_dual_hash": "efc2fb20ceb858b3",
    "worker_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3341a4ba541bfa32",
    "baseline_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13_batch4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 4,
    "candidate_batch_target_sequences": [
      [
        8,
        20,
        13
      ],
      [
        5,
        9
      ],
      [
        2,
        15,
        3,
        12
      ],
      [
        18,
        15,
        3,
        12
      ]
    ],
    "candidate_context_complete": true,
    "candidate_names": [
      "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13",
      "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank2_5_9",
      "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank4_2_15_3_12",
      "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank5_18_15_3_12"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "62c86745ed2b3aaa",
    "forbidden_signature_hash": "ddf56f63968049f0",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13_batch4",
    "pool_signature_hash": "50dc555c1757eeca",
    "pool_task_set_hash": "fdf2e77ba9b76816",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->20:low_risk:2",
      "20->13:low_time:0",
      "13->0:low_risk:2"
    ],
    "target_materialization_journey_count": 4,
    "target_priority_sequence": [
      8,
      20,
      13
    ],
    "target_sequence": [
      8,
      20,
      13,
      5,
      9,
      2,
      15,
      3,
      12,
      18,
      15,
      3,
      12
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->20:low_risk:2",
          "20->13:low_time:0",
          "13->0:low_risk:2"
        ],
        "sequence": [
          8,
          20,
          13
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "9bd9a1d18b7a5cf5",
    "worker_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13_batch4_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "03a8d149c5bdfc16",
    "baseline_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "3100b787bf438dfe",
    "forbidden_signature_hash": "59f58c79d1e50d49",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11",
    "pool_signature_hash": "7a249193fdd37789",
    "pool_task_set_hash": "e3f049a263f86c82",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->2:low_risk:2",
      "2->4:low_risk:2",
      "4->7:low_risk:2",
      "7->11:low_risk:2",
      "11->0:low_risk:2"
    ],
    "target_priority_sequence": [
      5,
      1,
      2,
      4,
      7,
      11
    ],
    "target_sequence": [
      5,
      1,
      2,
      4,
      7,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->1:low_risk:2",
          "1->2:low_risk:2",
          "2->4:low_risk:2",
          "4->7:low_risk:2",
          "7->11:low_risk:2",
          "11->0:low_risk:2"
        ],
        "sequence": [
          5,
          1,
          2,
          4,
          7,
          11
        ],
        "start_time": 12.976513
      }
    ],
    "true_dual_hash": "d4d21a0866a5f19c",
    "worker_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "03a8d149c5bdfc16",
    "baseline_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_rank2_5_1_2_4_7_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_rank2_5_1_2_4_7"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "fbfd88d4ebde5459",
    "forbidden_signature_hash": "69ba243ea44bf530",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_rank2_5_1_2_4_7",
    "pool_signature_hash": "4846218d8d5926f5",
    "pool_task_set_hash": "b3efd3d85e0ad5f4",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->2:low_risk:2",
      "2->4:low_risk:2",
      "4->7:low_risk:2",
      "7->0:low_risk:2"
    ],
    "target_priority_sequence": [
      5,
      1,
      2,
      4,
      7
    ],
    "target_sequence": [
      5,
      1,
      2,
      4,
      7
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->1:low_risk:2",
          "1->2:low_risk:2",
          "2->4:low_risk:2",
          "4->7:low_risk:2",
          "7->0:low_risk:2"
        ],
        "sequence": [
          5,
          1,
          2,
          4,
          7
        ],
        "start_time": 12.976513
      }
    ],
    "true_dual_hash": "c9745e8a1c010c30",
    "worker_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_rank2_5_1_2_4_7_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "a8681375b98abe9b",
    "baseline_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_rank1_10_3_batch4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 4,
    "candidate_batch_target_sequences": [
      [
        10,
        3
      ],
      [
        16,
        11
      ],
      [
        8,
        16,
        11
      ],
      [
        11,
        8,
        4,
        16
      ]
    ],
    "candidate_context_complete": true,
    "candidate_names": [
      "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_rank1_10_3",
      "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_rank2_16_11",
      "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_rank3_8_16_11",
      "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_rank5_11_8_4_16"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ddcb5387bef3bf63",
    "forbidden_signature_hash": "30f21d8900d08486",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_rank1_10_3_batch4",
    "pool_signature_hash": "9434aed561bacc3e",
    "pool_task_set_hash": "e4123a7322872a6a",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->10:low_risk:2",
      "10->3:low_risk:2",
      "3->0:low_risk:2"
    ],
    "target_materialization_journey_count": 4,
    "target_priority_sequence": [
      10,
      3
    ],
    "target_sequence": [
      10,
      3,
      16,
      11,
      8,
      16,
      11,
      11,
      8,
      4,
      16
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->10:low_risk:2",
          "10->3:low_risk:2",
          "3->0:low_risk:2"
        ],
        "sequence": [
          10,
          3
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "755b99c23a4b6c8e",
    "worker_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_rank1_10_3_batch4_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "a4c0969f3e85a752",
    "baseline_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_rank1_10_14_18_batch4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 4,
    "candidate_batch_target_sequences": [
      [
        10,
        14,
        18
      ],
      [
        11,
        3,
        1,
        20
      ],
      [
        11,
        4,
        14,
        20
      ],
      [
        11,
        3,
        13,
        20
      ]
    ],
    "candidate_context_complete": true,
    "candidate_names": [
      "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_rank1_10_14_18",
      "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_rank3_11_3_1_20",
      "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_rank4_11_4_14_20",
      "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_rank5_11_3_13_20"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "5c522ff2995f86be",
    "forbidden_signature_hash": "626c424ddedf4f80",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_rank1_10_14_18_batch4",
    "pool_signature_hash": "51167fe6d51c9788",
    "pool_task_set_hash": "a07b207bdd9a5b98",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->10:low_risk:2",
      "10->0:low_risk:2"
    ],
    "target_materialization_journey_count": 4,
    "target_priority_sequence": [
      10
    ],
    "target_sequence": [
      10,
      14,
      18,
      11,
      3,
      1,
      20,
      11,
      4,
      14,
      20,
      11,
      3,
      13,
      20
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->10:low_risk:2",
          "10->0:low_risk:2"
        ],
        "sequence": [
          10
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->14:low_risk:2",
          "14->18:low_time:0",
          "18->0:low_time:0"
        ],
        "sequence": [
          14,
          18
        ],
        "start_time": 252.451189
      }
    ],
    "true_dual_hash": "88344526d1d391bd",
    "worker_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_rank1_10_14_18_batch4_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "51df5d79e9ac45ae",
    "baseline_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_rank2_8_16_11_14_9_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_rank2_8_16_11_14_9"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "08b8d772e2ab9623",
    "forbidden_signature_hash": "0c230e1a6c7fee96",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_rank2_8_16_11_14_9",
    "pool_signature_hash": "07ce45c4b7ea1c45",
    "pool_task_set_hash": "ba7679f84bbb38ae",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->16:low_risk:2",
      "16->11:low_energy:1",
      "11->0:low_risk:2"
    ],
    "target_priority_sequence": [
      8,
      16,
      11
    ],
    "target_sequence": [
      8,
      16,
      11,
      14,
      9
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_risk:2",
          "8->16:low_risk:2",
          "16->11:low_energy:1",
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
          "0->14:low_time:0",
          "14->9:low_risk:2",
          "9->0:low_risk:2"
        ],
        "sequence": [
          14,
          9
        ],
        "start_time": 299.814635
      }
    ],
    "true_dual_hash": "c923eda9f0bcc8d2",
    "worker_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_rank2_8_16_11_14_9_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4_mainline_baseline/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4_target_priority_worker/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4_target_priority_worker/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=d519291840dd7000 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,11,2,4,2,3,18,11,5,1,2,15 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys=[{"traces":[{"arc_option_sequence":["0->8:low_time:0","8->11:low_time:0","11->0:low_time:0"],"sequence":[8,11],"start_time":0.0}]},{"traces":[{"arc_option_sequence":["0->2:low_risk:1","2->4:low_risk:2","4->0:low_risk:2"],"sequence":[2,4],"start_time":66.643786}]},{"traces":[{"arc_option_sequence":["0->2:low_risk:1","2->3:low_risk:2","3->18:low_risk:2","18->11:low_risk:1","11->0:low_risk:2"],"sequence":[2,3,18,11],"start_time":0.985679}]},{"traces":[{"arc_option_sequence":["0->5:low_risk:2","5->1:low_risk:2","1->2:low_risk:2","2->15:low_time:0","15->0:low_risk:2"],"sequence":[5,1,2,15],"start_time":11.291563}]}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_time:0,8->11:low_time:0,11->0:low_time:0'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3_batch4_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3_batch4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3_batch4_mainline_baseline/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3_batch4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3_batch4_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3_batch4_target_priority_worker/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3_batch4_target_priority_worker/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3_batch4_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=67c11b5ec80925ec --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,1,2,18,3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,1,2,18,3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,1,2,18,3,2,1,15,3,2,18,3,15,5,18,15,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys=[{"traces":[{"arc_option_sequence":["0->5:low_risk:2","5->1:low_risk:2","1->2:low_risk:2","2->18:low_risk:2","18->3:low_risk:2","3->0:low_risk:2"],"sequence":[5,1,2,18,3],"start_time":11.291563}]},{"traces":[{"arc_option_sequence":["0->2:low_risk:1","2->1:low_risk:2","1->15:low_time:0","15->3:low_time:0","3->0:low_risk:2"],"sequence":[2,1,15,3],"start_time":0.0}]},{"traces":[{"arc_option_sequence":["0->2:low_risk:1","2->18:low_risk:2","18->3:low_risk:2","3->15:low_risk:2","15->0:low_risk:2"],"sequence":[2,18,3,15],"start_time":0.0}]},{"traces":[{"arc_option_sequence":["0->5:low_risk:2","5->18:low_risk:2","18->15:low_time:0","15->3:low_risk:2","3->0:low_risk:2"],"sequence":[5,18,15,3],"start_time":0.0}]}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->1:low_risk:2,1->2:low_risk:2,2->18:low_risk:2,18->3:low_risk:2,3->0:low_risk:2'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13_target_priority_worker/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13_target_priority_worker/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=409f65576794fa39 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=17 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=17 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=17,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->17:low_time:0","17->0:low_risk:2"],"sequence":[17],"start_time":0.0},{"arc_option_sequence":["0->13:low_risk:2","13->0:low_risk:2"],"sequence":[13],"start_time":376.101788}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->17:low_time:0,17->0:low_risk:2'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13_batch4_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13_batch4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13_batch4_mainline_baseline/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13_batch4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13_batch4_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13_batch4_target_priority_worker/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13_batch4_target_priority_worker/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13_batch4_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=62c86745ed2b3aaa --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,20,13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,20,13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,20,13,5,9,2,15,3,12,18,15,3,12 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys=[{"traces":[{"arc_option_sequence":["0->8:low_time:0","8->20:low_risk:2","20->13:low_time:0","13->0:low_risk:2"],"sequence":[8,20,13],"start_time":0.0}]},{"traces":[{"arc_option_sequence":["0->5:low_risk:2","5->0:low_risk:2"],"sequence":[5],"start_time":0.0},{"arc_option_sequence":["0->9:low_risk:2","9->0:low_risk:2"],"sequence":[9],"start_time":129.323853}]},{"traces":[{"arc_option_sequence":["0->2:low_risk:1","2->0:low_risk:1"],"sequence":[2],"start_time":0.0},{"arc_option_sequence":["0->15:low_time:0","15->3:low_time:0","3->12:low_risk:1","12->0:low_risk:2"],"sequence":[15,3,12],"start_time":136.60041}]},{"traces":[{"arc_option_sequence":["0->18:low_time:0","18->15:low_time:0","15->3:low_time:0","3->12:low_time:0","12->0:low_energy:1"],"sequence":[18,15,3,12],"start_time":63.640253}]}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_time:0,8->20:low_risk:2,20->13:low_time:0,13->0:low_risk:2'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11_target_priority_worker/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11_target_priority_worker/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=3100b787bf438dfe --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,1,2,4,7,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,1,2,4,7,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,1,2,4,7,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->1:low_risk:2","1->2:low_risk:2","2->4:low_risk:2","4->7:low_risk:2","7->11:low_risk:2","11->0:low_risk:2"],"sequence":[5,1,2,4,7,11],"start_time":12.976513}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->1:low_risk:2,1->2:low_risk:2,2->4:low_risk:2,4->7:low_risk:2,7->11:low_risk:2,11->0:low_risk:2'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_rank2_5_1_2_4_7_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_rank2_5_1_2_4_7_mainline_baseline/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_rank2_5_1_2_4_7_mainline_baseline/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_rank2_5_1_2_4_7_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_rank2_5_1_2_4_7_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_rank2_5_1_2_4_7_target_priority_worker/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_rank2_5_1_2_4_7_target_priority_worker/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_rank2_5_1_2_4_7_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=fbfd88d4ebde5459 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,1,2,4,7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,1,2,4,7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,1,2,4,7 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->1:low_risk:2","1->2:low_risk:2","2->4:low_risk:2","4->7:low_risk:2","7->0:low_risk:2"],"sequence":[5,1,2,4,7],"start_time":12.976513}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->1:low_risk:2,1->2:low_risk:2,2->4:low_risk:2,4->7:low_risk:2,7->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_rank1_10_3_batch4_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_rank1_10_3_batch4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_rank1_10_3_batch4_mainline_baseline/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_rank1_10_3_batch4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_rank1_10_3_batch4_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_rank1_10_3_batch4_target_priority_worker/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_rank1_10_3_batch4_target_priority_worker/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_rank1_10_3_batch4_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ddcb5387bef3bf63 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=10,3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=10,3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=10,3,16,11,8,16,11,11,8,4,16 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys=[{"traces":[{"arc_option_sequence":["0->10:low_risk:2","10->3:low_risk:2","3->0:low_risk:2"],"sequence":[10,3],"start_time":0.0}]},{"traces":[{"arc_option_sequence":["0->16:low_risk:2","16->11:low_risk:2","11->0:low_risk:2"],"sequence":[16,11],"start_time":74.915015}]},{"traces":[{"arc_option_sequence":["0->8:low_risk:2","8->16:low_risk:2","16->11:low_risk:2","11->0:low_risk:2"],"sequence":[8,16,11],"start_time":14.542572}]},{"traces":[{"arc_option_sequence":["0->11:low_time:0","11->8:low_energy:1","8->4:low_time:0","4->16:low_risk:2","16->0:low_energy:1"],"sequence":[11,8,4,16],"start_time":79.461116}]}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->10:low_risk:2,10->3:low_risk:2,3->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_rank1_10_14_18_batch4_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_rank1_10_14_18_batch4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_rank1_10_14_18_batch4_mainline_baseline/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_rank1_10_14_18_batch4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_rank1_10_14_18_batch4_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_rank1_10_14_18_batch4_target_priority_worker/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_rank1_10_14_18_batch4_target_priority_worker/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_rank1_10_14_18_batch4_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=5c522ff2995f86be --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=10,14,18,11,3,1,20,11,4,14,20,11,3,13,20 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys=[{"traces":[{"arc_option_sequence":["0->10:low_risk:2","10->0:low_risk:2"],"sequence":[10],"start_time":0.0},{"arc_option_sequence":["0->14:low_risk:2","14->18:low_time:0","18->0:low_time:0"],"sequence":[14,18],"start_time":252.451189}]},{"traces":[{"arc_option_sequence":["0->11:low_energy:1","11->0:low_time:0"],"sequence":[11],"start_time":79.265081},{"arc_option_sequence":["0->3:low_risk:2","3->1:low_risk:1","1->20:low_risk:2","20->0:low_time:0"],"sequence":[3,1,20],"start_time":173.842018}]},{"traces":[{"arc_option_sequence":["0->11:low_energy:1","11->0:low_time:0"],"sequence":[11],"start_time":79.265081},{"arc_option_sequence":["0->4:low_energy:1","4->14:low_time:0","14->20:low_energy:1","20->0:low_time:0"],"sequence":[4,14,20],"start_time":173.842018}]},{"traces":[{"arc_option_sequence":["0->11:low_energy:1","11->0:low_time:0"],"sequence":[11],"start_time":79.265081},{"arc_option_sequence":["0->3:low_time:0","3->13:low_time:0","13->20:low_time:0","20->0:low_time:0"],"sequence":[3,13,20],"start_time":173.842018}]}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->10:low_risk:2,10->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_rank2_8_16_11_14_9_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_rank2_8_16_11_14_9_mainline_baseline/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_rank2_8_16_11_14_9_mainline_baseline/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_rank2_8_16_11_14_9_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_rank2_8_16_11_14_9_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 90.000000 --results-csv BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_rank2_8_16_11_14_9_target_priority_worker/results.csv --log-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_rank2_8_16_11_14_9_target_priority_worker/logs --solution-dir BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_rank2_8_16_11_14_9_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=08b8d772e2ab9623 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,16,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,16,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,16,11,14,9 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_risk:2","8->16:low_risk:2","16->11:low_energy:1","11->0:low_risk:2"],"sequence":[8,16,11],"start_time":14.542572},{"arc_option_sequence":["0->14:low_time:0","14->9:low_risk:2","9->0:low_risk:2"],"sequence":[14,9],"start_time":299.814635}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_risk:2,8->16:low_risk:2,16->11:low_energy:1,11->0:low_risk:2'
```

## 边界

- 5/10 命令不关闭主线 GAT/learning，也不启用新 worker；
- 20 baseline/worker 命令也不关闭主线 GAT/learning，避免候选捕获上下文无法复现；
- 20 baseline/worker 命令开启 counterfactual replay capture；如果旧 target context 没到，仍保留实际到达的 context 供下一轮候选抽取；
- 20 worker 命令是显式 opt-in，默认只做 same-context target materialization，不运行 Pulse 搜索 / harvest / archive / bound pruning；
- 固定 worker 的 current-probe 开关只作为 expected context 触发器；target materialization 会在任何 Pulse 搜索前返回结果；
- `worker_batch_size > 1` 时，只会合并同一 instance + expected context 的候选，并通过 `target_materialization_journeys` 批量物化；
- 20 worker 候选必须带完整 context / dual / cuts / branch / pool hash；
- 所有命令都不启用 sharded Pulse certificate 或 official lower-bound effect；
- 含 `->` 的 arc-option 配置通过 `shlex.join` 自动引用，不能手工去掉引号；
- 该 runbook 不是生产开关，跑完后仍需看 5/10 no-regression 和 20-task ROI。
