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
    "active_hash_before": "13951c54226c029d",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.4,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "e8e35421df342768",
    "forbidden_signature_hash": "8d39350d16921119",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20",
    "pool_signature_hash": "d5e85e9e642773cd",
    "pool_task_set_hash": "3555c1f405e7afcb",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->14:low_risk:2",
      "14->1:low_risk:2",
      "1->0:low_risk:2"
    ],
    "target_priority_sequence": [
      5,
      14,
      1
    ],
    "target_sequence": [
      5,
      14,
      1,
      20
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->14:low_risk:2",
          "14->1:low_risk:2",
          "1->0:low_risk:2"
        ],
        "sequence": [
          5,
          14,
          1
        ],
        "start_time": 51.181514
      },
      {
        "arc_option_sequence": [
          "0->20:low_risk:2",
          "20->0:low_risk:2"
        ],
        "sequence": [
          20
        ],
        "start_time": 257.592567
      }
    ],
    "true_dual_hash": "c1d6bf0dee5fe2af",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "20ecd0ba075a5cd4",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.269231,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b6507dfb6db81d64",
    "forbidden_signature_hash": "a9fa6948e89224a2",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10",
    "pool_signature_hash": "256ff5712f06f6ee",
    "pool_task_set_hash": "5ab012b4a6716038",
    "target_arc_option_sequence": [
      "0->16:low_risk:2",
      "16->0:low_risk:2"
    ],
    "target_priority_sequence": [
      16
    ],
    "target_sequence": [
      16,
      11,
      12,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->16:low_risk:2",
          "16->0:low_risk:2"
        ],
        "sequence": [
          16
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->11:low_time:0",
          "11->12:low_time:0",
          "12->10:low_time:0",
          "10->0:low_risk:2"
        ],
        "sequence": [
          11,
          12,
          10
        ],
        "start_time": 318.585773
      }
    ],
    "true_dual_hash": "3fd56392816e9c8d",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "692009a078d4b4fa",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.4,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "126440b08b9f25f5",
    "forbidden_signature_hash": "8fc01c49285ec128",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20",
    "pool_signature_hash": "dc713c97248b0eab",
    "pool_task_set_hash": "603464bf2edb1804",
    "target_arc_option_sequence": [
      "0->5:low_time:0",
      "5->18:low_time:0",
      "18->10:low_time:0",
      "10->14:low_time:0",
      "14->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_priority_sequence": [
      5,
      18,
      10,
      14,
      1
    ],
    "target_sequence": [
      5,
      18,
      10,
      14,
      1,
      20
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_time:0",
          "5->18:low_time:0",
          "18->10:low_time:0",
          "10->14:low_time:0",
          "14->1:low_time:0",
          "1->0:low_time:0"
        ],
        "sequence": [
          5,
          18,
          10,
          14,
          1
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->0:low_time:0"
        ],
        "sequence": [
          20
        ],
        "start_time": 296.523456
      }
    ],
    "true_dual_hash": "ae9b0b49e1be577b",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "778c07cb4ef85021",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.4,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "f9d0b6b18a0a28d3",
    "forbidden_signature_hash": "419f8f65acc3551b",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4",
    "pool_signature_hash": "d26348c8579fe2e4",
    "pool_task_set_hash": "49305ade6883086a",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->18:low_energy:1",
      "18->0:low_risk:2"
    ],
    "target_priority_sequence": [
      20,
      18
    ],
    "target_sequence": [
      20,
      18,
      3,
      4
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->18:low_energy:1",
          "18->0:low_risk:2"
        ],
        "sequence": [
          20,
          18
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->4:low_risk:2",
          "4->0:low_time:0"
        ],
        "sequence": [
          3,
          4
        ],
        "start_time": 228.617125
      }
    ],
    "true_dual_hash": "1f5fbbb40123e95b",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "16e2d0342cb4ce87",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.4,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7db256d4f7224cc6",
    "forbidden_signature_hash": "5aeacc70a6d978d0",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4",
    "pool_signature_hash": "c5ddd5b68ac1fbd8",
    "pool_task_set_hash": "6f8bb60d3048867b",
    "target_arc_option_sequence": [
      "0->10:low_time:0",
      "10->1:low_risk:2",
      "1->16:low_time:0",
      "16->7:low_risk:2",
      "7->17:low_time:0",
      "17->0:low_time:0"
    ],
    "target_priority_sequence": [
      10,
      1,
      16,
      7,
      17
    ],
    "target_sequence": [
      10,
      1,
      16,
      7,
      17,
      4
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->10:low_time:0",
          "10->1:low_risk:2",
          "1->16:low_time:0",
          "16->7:low_risk:2",
          "7->17:low_time:0",
          "17->0:low_time:0"
        ],
        "sequence": [
          10,
          1,
          16,
          7,
          17
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->4:low_time:0",
          "4->0:low_time:0"
        ],
        "sequence": [
          4
        ],
        "start_time": 409.464411
      }
    ],
    "true_dual_hash": "2fbba0a0a55dc9ef",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "ede095c6ba8539c1",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.36,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "9fadf4f7b39742a2",
    "forbidden_signature_hash": "cc076c836d200e54",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11",
    "pool_signature_hash": "b0fe906b0c1ab18d",
    "pool_task_set_hash": "ee50cf9eb4b638b3",
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->8:low_time:0",
      "8->11:low_risk:2",
      "11->0:low_time:0"
    ],
    "target_priority_sequence": [
      13,
      8,
      11
    ],
    "target_sequence": [
      13,
      8,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->8:low_time:0",
          "8->11:low_risk:2",
          "11->0:low_time:0"
        ],
        "sequence": [
          13,
          8,
          11
        ],
        "start_time": 0.264013
      }
    ],
    "true_dual_hash": "4dba67189cd38261",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "f94d076935f27fde",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_6_11_2_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.347826,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "bec78bfc0baddb44",
    "forbidden_signature_hash": "e89be873ab67ab24",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_6_11_2",
    "pool_signature_hash": "06bc54750fc9ac71",
    "pool_task_set_hash": "80b62e66b4be6dc3",
    "target_arc_option_sequence": [
      "0->6:low_risk:2",
      "6->11:low_risk:2",
      "11->0:low_time:0"
    ],
    "target_priority_sequence": [
      6,
      11
    ],
    "target_sequence": [
      6,
      11,
      2
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->6:low_risk:2",
          "6->11:low_risk:2",
          "11->0:low_time:0"
        ],
        "sequence": [
          6,
          11
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->2:low_time:0",
          "2->0:low_risk:2"
        ],
        "sequence": [
          2
        ],
        "start_time": 308.516937
      }
    ],
    "true_dual_hash": "dc29f619e1498bc2",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_6_11_2_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "cc48ebab3274044c",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_15_6_11_12_14_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.36,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "587e2ac350a8619b",
    "forbidden_signature_hash": "bf14d230f6d7ff3d",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_15_6_11_12_14",
    "pool_signature_hash": "8153eb9aa98c60b1",
    "pool_task_set_hash": "53617fb7789de47f",
    "target_arc_option_sequence": [
      "0->15:low_risk:2",
      "15->6:low_time:0",
      "6->0:low_time:0"
    ],
    "target_priority_sequence": [
      15,
      6
    ],
    "target_sequence": [
      15,
      6,
      11,
      12,
      14
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->15:low_risk:2",
          "15->6:low_time:0",
          "6->0:low_time:0"
        ],
        "sequence": [
          15,
          6
        ],
        "start_time": 8.449793
      },
      {
        "arc_option_sequence": [
          "0->11:low_time:0",
          "11->12:low_time:0",
          "12->14:low_risk:2",
          "14->0:low_risk:2"
        ],
        "sequence": [
          11,
          12,
          14
        ],
        "start_time": 288.548811
      }
    ],
    "true_dual_hash": "7d1951d926fb0a0b",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_15_6_11_12_14_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "8fa22105b7d71a70",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_20_18_2_1_19_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.347826,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "0f0c5d214add6400",
    "forbidden_signature_hash": "64cde73bd524b1e5",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_20_18_2_1_19",
    "pool_signature_hash": "5a140851789d466b",
    "pool_task_set_hash": "a3df5269fcbc2319",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_priority_sequence": [
      20
    ],
    "target_sequence": [
      20,
      18,
      2,
      1,
      19
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->0:low_time:0"
        ],
        "sequence": [
          20
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->18:low_time:0",
          "18->2:low_time:0",
          "2->1:low_risk:2",
          "1->0:low_time:0"
        ],
        "sequence": [
          18,
          2,
          1
        ],
        "start_time": 65.070996
      },
      {
        "arc_option_sequence": [
          "0->19:low_risk:2",
          "19->0:low_time:0"
        ],
        "sequence": [
          19
        ],
        "start_time": 405.748559
      }
    ],
    "true_dual_hash": "5c6902f41c1a1901",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_20_18_2_1_19_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "b7829a86dcf262e8",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.347826,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "d1096c4029531f56",
    "forbidden_signature_hash": "2aae101758b54a89",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19",
    "pool_signature_hash": "b6f90c6314ebd7e2",
    "pool_task_set_hash": "25774e8e0baa5782",
    "target_arc_option_sequence": [
      "0->7:low_risk:2",
      "7->0:low_risk:2"
    ],
    "target_priority_sequence": [
      7
    ],
    "target_sequence": [
      7,
      1,
      8,
      11,
      19
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->7:low_risk:2",
          "7->0:low_risk:2"
        ],
        "sequence": [
          7
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->1:low_time:0",
          "1->8:low_time:0",
          "8->11:low_energy:1",
          "11->0:low_energy:1"
        ],
        "sequence": [
          1,
          8,
          11
        ],
        "start_time": 83.548501
      },
      {
        "arc_option_sequence": [
          "0->19:low_risk:2",
          "19->0:low_time:0"
        ],
        "sequence": [
          19
        ],
        "start_time": 415.228421
      }
    ],
    "true_dual_hash": "49982d413c04cf67",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "09a48f148e1b778f",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_13_1_16_8_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.347826,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "1b98b5f990279d7b",
    "forbidden_signature_hash": "25f63db63fe6d91e",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_13_1_16_8",
    "pool_signature_hash": "13e3faea86aedecc",
    "pool_task_set_hash": "3bbfa1d0ffb5a306",
    "target_arc_option_sequence": [
      "0->13:low_time:0",
      "13->0:low_time:0"
    ],
    "target_priority_sequence": [
      13
    ],
    "target_sequence": [
      13,
      1,
      16,
      8
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->13:low_time:0",
          "13->0:low_time:0"
        ],
        "sequence": [
          13
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->1:low_time:0",
          "1->16:low_risk:2",
          "16->8:low_risk:2",
          "8->0:low_risk:2"
        ],
        "sequence": [
          1,
          16,
          8
        ],
        "start_time": 292.629943
      }
    ],
    "true_dual_hash": "710570cbd4775dae",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_13_1_16_8_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "6b9694c80b4ec27f",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_15_12_9_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.269231,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "3a9af4966d4b91d5",
    "forbidden_signature_hash": "1bc80a34f05a06ef",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_15_12_9",
    "pool_signature_hash": "5e81fe0c45048e0d",
    "pool_task_set_hash": "038174f89a2b97ba",
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->15:low_risk:2",
      "15->12:low_time:0",
      "12->9:low_risk:2",
      "9->0:low_risk:2"
    ],
    "target_priority_sequence": [
      8,
      15,
      12,
      9
    ],
    "target_sequence": [
      8,
      15,
      12,
      9
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->15:low_risk:2",
          "15->12:low_time:0",
          "12->9:low_risk:2",
          "9->0:low_risk:2"
        ],
        "sequence": [
          8,
          15,
          12,
          9
        ],
        "start_time": 55.435969
      }
    ],
    "true_dual_hash": "6d5385399c719f88",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_15_12_9_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "f3c4a439371e8dbb",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_6_14_3_4_18_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.36,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ea2f1344458c548f",
    "forbidden_signature_hash": "b1461d78eba5da01",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_6_14_3_4_18",
    "pool_signature_hash": "0951222227202144",
    "pool_task_set_hash": "9648365788fb0dca",
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->0:low_time:0"
    ],
    "target_priority_sequence": [
      6
    ],
    "target_sequence": [
      6,
      14,
      3,
      4,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->6:low_time:0",
          "6->0:low_time:0"
        ],
        "sequence": [
          6
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->14:low_risk:1",
          "14->3:low_time:0",
          "3->4:low_time:0",
          "4->18:low_time:0",
          "18->0:low_risk:2"
        ],
        "sequence": [
          14,
          3,
          4,
          18
        ],
        "start_time": 157.389825
      }
    ],
    "true_dual_hash": "0c02b974fe060f9a",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_6_14_3_4_18_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "0d3647e8bc157d9b",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.36,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "09187873900ecefa",
    "forbidden_signature_hash": "98790f7f88eda8f5",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18",
    "pool_signature_hash": "8e11a6df2fd8e8c8",
    "pool_task_set_hash": "fa332705423b4447",
    "target_arc_option_sequence": [
      "0->6:low_risk:2",
      "6->5:low_risk:2",
      "5->0:low_risk:2"
    ],
    "target_priority_sequence": [
      6,
      5
    ],
    "target_sequence": [
      6,
      5,
      4,
      16,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->6:low_risk:2",
          "6->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          6,
          5
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->16:low_risk:2",
          "16->18:low_risk:2",
          "18->0:low_risk:2"
        ],
        "sequence": [
          4,
          16,
          18
        ],
        "start_time": 241.140271
      }
    ],
    "true_dual_hash": "8bc1731e75d1e97a",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3ca14dba75894c6f",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.269231,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "1fa17aea2063098d",
    "forbidden_signature_hash": "5559157b1af629c3",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11",
    "pool_signature_hash": "8a1916cc5ebaa441",
    "pool_task_set_hash": "961b82b5eee8dfe0",
    "target_arc_option_sequence": [
      "0->4:low_time:0",
      "4->0:low_risk:1"
    ],
    "target_priority_sequence": [
      4
    ],
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
    "true_dual_hash": "09d58d42a46b577b",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "94ad34057d1d4681",
    "baseline_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_8b4a2367b0350bfe_4_18_6_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cell_positive_rate": 0.269231,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "8b4a2367b0350bfe",
    "forbidden_signature_hash": "cc30556ca9ce570f",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_8b4a2367b0350bfe_4_18_6",
    "pool_signature_hash": "920ba8de2d183b5b",
    "pool_task_set_hash": "09df3f89293d5b5c",
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->18:low_risk:2",
      "18->6:low_time:0",
      "6->0:low_risk:2"
    ],
    "target_priority_sequence": [
      4,
      18,
      6
    ],
    "target_sequence": [
      4,
      18,
      6
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->18:low_risk:2",
          "18->6:low_time:0",
          "6->0:low_risk:2"
        ],
        "sequence": [
          4,
          18,
          6
        ],
        "start_time": 74.514535
      }
    ],
    "true_dual_hash": "b2ac4bfb0777560e",
    "worker_csv": "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_8b4a2367b0350bfe_4_18_6_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=e8e35421df342768 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,14,1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,14,1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,14,1,20 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->14:low_risk:2","14->1:low_risk:2","1->0:low_risk:2"],"sequence":[5,14,1],"start_time":51.181514},{"arc_option_sequence":["0->20:low_risk:2","20->0:low_risk:2"],"sequence":[20],"start_time":257.592567}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->14:low_risk:2,14->1:low_risk:2,1->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b6507dfb6db81d64 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=16 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=16 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=16,11,12,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->16:low_risk:2","16->0:low_risk:2"],"sequence":[16],"start_time":0.0},{"arc_option_sequence":["0->11:low_time:0","11->12:low_time:0","12->10:low_time:0","10->0:low_risk:2"],"sequence":[11,12,10],"start_time":318.585773}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->16:low_risk:2,16->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=126440b08b9f25f5 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,18,10,14,1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,18,10,14,1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,18,10,14,1,20 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_time:0","5->18:low_time:0","18->10:low_time:0","10->14:low_time:0","14->1:low_time:0","1->0:low_time:0"],"sequence":[5,18,10,14,1],"start_time":0.0},{"arc_option_sequence":["0->20:low_time:0","20->0:low_time:0"],"sequence":[20],"start_time":296.523456}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_time:0,5->18:low_time:0,18->10:low_time:0,10->14:low_time:0,14->1:low_time:0,1->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=f9d0b6b18a0a28d3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,18 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,18 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,18,3,4 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->18:low_energy:1","18->0:low_risk:2"],"sequence":[20,18],"start_time":0.0},{"arc_option_sequence":["0->3:low_risk:2","3->4:low_risk:2","4->0:low_time:0"],"sequence":[3,4],"start_time":228.617125}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->18:low_energy:1,18->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7db256d4f7224cc6 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=10,1,16,7,17 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=10,1,16,7,17 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=10,1,16,7,17,4 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->10:low_time:0","10->1:low_risk:2","1->16:low_time:0","16->7:low_risk:2","7->17:low_time:0","17->0:low_time:0"],"sequence":[10,1,16,7,17],"start_time":0.0},{"arc_option_sequence":["0->4:low_time:0","4->0:low_time:0"],"sequence":[4],"start_time":409.464411}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->10:low_time:0,10->1:low_risk:2,1->16:low_time:0,16->7:low_risk:2,7->17:low_time:0,17->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=9fadf4f7b39742a2 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13,8,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13,8,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,8,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_risk:2","13->8:low_time:0","8->11:low_risk:2","11->0:low_time:0"],"sequence":[13,8,11],"start_time":0.264013}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_risk:2,13->8:low_time:0,8->11:low_risk:2,11->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_6_11_2_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_6_11_2_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_6_11_2_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_6_11_2_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_6_11_2_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_6_11_2_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_6_11_2_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_6_11_2_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=bec78bfc0baddb44 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=6,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=6,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=6,11,2 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->6:low_risk:2","6->11:low_risk:2","11->0:low_time:0"],"sequence":[6,11],"start_time":0.0},{"arc_option_sequence":["0->2:low_time:0","2->0:low_risk:2"],"sequence":[2],"start_time":308.516937}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->6:low_risk:2,6->11:low_risk:2,11->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_15_6_11_12_14_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_15_6_11_12_14_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_15_6_11_12_14_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_15_6_11_12_14_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_15_6_11_12_14_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_15_6_11_12_14_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_15_6_11_12_14_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_15_6_11_12_14_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=587e2ac350a8619b --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=15,6 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=15,6 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=15,6,11,12,14 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->15:low_risk:2","15->6:low_time:0","6->0:low_time:0"],"sequence":[15,6],"start_time":8.449793},{"arc_option_sequence":["0->11:low_time:0","11->12:low_time:0","12->14:low_risk:2","14->0:low_risk:2"],"sequence":[11,12,14],"start_time":288.548811}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->15:low_risk:2,15->6:low_time:0,6->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_20_18_2_1_19_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_20_18_2_1_19_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_20_18_2_1_19_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_20_18_2_1_19_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_20_18_2_1_19_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_20_18_2_1_19_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_20_18_2_1_19_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_20_18_2_1_19_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=0f0c5d214add6400 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,18,2,1,19 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->0:low_time:0"],"sequence":[20],"start_time":0.0},{"arc_option_sequence":["0->18:low_time:0","18->2:low_time:0","2->1:low_risk:2","1->0:low_time:0"],"sequence":[18,2,1],"start_time":65.070996},{"arc_option_sequence":["0->19:low_risk:2","19->0:low_time:0"],"sequence":[19],"start_time":405.748559}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=d1096c4029531f56 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=7,1,8,11,19 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->7:low_risk:2","7->0:low_risk:2"],"sequence":[7],"start_time":0.0},{"arc_option_sequence":["0->1:low_time:0","1->8:low_time:0","8->11:low_energy:1","11->0:low_energy:1"],"sequence":[1,8,11],"start_time":83.548501},{"arc_option_sequence":["0->19:low_risk:2","19->0:low_time:0"],"sequence":[19],"start_time":415.228421}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->7:low_risk:2,7->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_13_1_16_8_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_13_1_16_8_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_13_1_16_8_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_13_1_16_8_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_13_1_16_8_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_13_1_16_8_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_13_1_16_8_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_13_1_16_8_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=1b98b5f990279d7b --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,1,16,8 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_time:0","13->0:low_time:0"],"sequence":[13],"start_time":0.0},{"arc_option_sequence":["0->1:low_time:0","1->16:low_risk:2","16->8:low_risk:2","8->0:low_risk:2"],"sequence":[1,16,8],"start_time":292.629943}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_time:0,13->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_15_12_9_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_15_12_9_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_15_12_9_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_15_12_9_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_15_12_9_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_15_12_9_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_15_12_9_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_15_12_9_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=3a9af4966d4b91d5 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,15,12,9 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,15,12,9 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,15,12,9 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_time:0","8->15:low_risk:2","15->12:low_time:0","12->9:low_risk:2","9->0:low_risk:2"],"sequence":[8,15,12,9],"start_time":55.435969}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_time:0,8->15:low_risk:2,15->12:low_time:0,12->9:low_risk:2,9->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_6_14_3_4_18_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_6_14_3_4_18_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_6_14_3_4_18_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_6_14_3_4_18_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_6_14_3_4_18_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_6_14_3_4_18_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_6_14_3_4_18_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_6_14_3_4_18_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ea2f1344458c548f --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=6 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=6 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=6,14,3,4,18 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->6:low_time:0","6->0:low_time:0"],"sequence":[6],"start_time":0.0},{"arc_option_sequence":["0->14:low_risk:1","14->3:low_time:0","3->4:low_time:0","4->18:low_time:0","18->0:low_risk:2"],"sequence":[14,3,4,18],"start_time":157.389825}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->6:low_time:0,6->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=09187873900ecefa --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=6,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=6,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=6,5,4,16,18 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->6:low_risk:2","6->5:low_risk:2","5->0:low_risk:2"],"sequence":[6,5],"start_time":0.0},{"arc_option_sequence":["0->4:low_risk:2","4->16:low_risk:2","16->18:low_risk:2","18->0:low_risk:2"],"sequence":[4,16,18],"start_time":241.140271}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->6:low_risk:2,6->5:low_risk:2,5->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=1fa17aea2063098d --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,12,15,6,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_time:0","4->0:low_risk:1"],"sequence":[4],"start_time":0.0},{"arc_option_sequence":["0->12:low_risk:2","12->15:low_risk:2","15->6:low_risk:2","6->11:low_risk:2","11->0:low_risk:2"],"sequence":[12,15,6,11],"start_time":253.641299}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_time:0,4->0:low_risk:1'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_8b4a2367b0350bfe_4_18_6_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_8b4a2367b0350bfe_4_18_6_mainline_baseline/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_8b4a2367b0350bfe_4_18_6_mainline_baseline/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_8b4a2367b0350bfe_4_18_6_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_8b4a2367b0350bfe_4_18_6_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_8b4a2367b0350bfe_4_18_6_target_priority_worker/results.csv --log-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_8b4a2367b0350bfe_4_18_6_target_priority_worker/logs --solution-dir BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_07_seed61612_8b4a2367b0350bfe_4_18_6_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=8b4a2367b0350bfe --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4,18,6 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4,18,6 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,18,6 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_risk:2","4->18:low_risk:2","18->6:low_time:0","6->0:low_risk:2"],"sequence":[4,18,6],"start_time":74.514535}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_risk:2,4->18:low_risk:2,18->6:low_time:0,6->0:low_risk:2'
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
