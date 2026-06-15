# GAT Worker ROI Solver A/B Runbook 报告

日期：2026-06-15

## 目的

生成下一轮 solver A/B 命令：5/10 只做 no-regression sentinel，20 只对
worker-ROI GAT + kNN/OOD 的 validation HIGH_PRIORITY 候选做显式 opt-in
worker A/B。该脚本不运行求解器。

## 机器字段

```text
gat_worker_roi_solver_ab_runbook = current
status = ready
runs_bpc_or_pricing = false
candidate_count = 9
max_workers = 4
production_ready = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

## Candidate Policy

```json
{
  "certificate_effect": false,
  "context_policy": "expected_context_hash_plus_recovered_capture_context",
  "gat_role": "trajectory_roi_embedding_and_impact_expression",
  "knn_ood_role": "safety_shell",
  "negative_discard_allowed": false,
  "safe_negative_action": "HIGH_PRIORITY",
  "unsafe_negative_action": "DELAY_QUEUE"
}
```

## Source OOD Metrics

```json
{
  "accuracy": 0.6666666666666666,
  "add_precision": 0.5555555555555556,
  "add_recall": 0.38461538461538464,
  "false_high_priority_rate": 0.17391304347826086,
  "false_negative_delay_queue": 8,
  "false_positive_high_priority": 4,
  "predicted_delay_queue": 27,
  "predicted_high_priority": 9,
  "total": 36,
  "true_negative_delay_queue": 19,
  "true_positive_high_priority": 5
}
```

## Candidate Runs

```json
[
  {
    "active_hash_before": "0ac8cb9a6ab0732f",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "35a4908dfecb7ff3",
    "forbidden_signature_hash": "48df1e7f52f569ad",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13",
    "pool_signature_hash": "e4bd17f60af80372",
    "pool_task_set_hash": "4a147e30b41d2b25",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "validation",
    "source_row_index": 1,
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->18:low_time:0",
      "18->10:low_risk:1",
      "10->0:low_risk:2"
    ],
    "target_priority_sequence": [
      5,
      18,
      10,
      8,
      13
    ],
    "target_sequence": [
      5,
      18,
      10,
      8,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->18:low_time:0",
          "18->10:low_risk:1",
          "10->0:low_risk:2"
        ],
        "sequence": [
          5,
          18,
          10
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->13:low_time:0",
          "13->0:low_time:0"
        ],
        "sequence": [
          8,
          13
        ],
        "start_time": 230.776211
      }
    ],
    "true_dual_hash": "3a4993d175b27e81",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.6782415509223938
  },
  {
    "active_hash_before": "6da932b87f5dccf6",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7fc1de982db572be",
    "forbidden_signature_hash": "45633cd412e425ae",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13",
    "pool_signature_hash": "1bd6802adf3e1260",
    "pool_task_set_hash": "98633eab2bb25abc",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "validation",
    "source_row_index": 2,
    "target_arc_option_sequence": [
      "0->18:low_risk:2",
      "18->10:low_risk:1",
      "10->0:low_time:0"
    ],
    "target_priority_sequence": [
      18,
      10,
      12,
      4,
      13
    ],
    "target_sequence": [
      18,
      10,
      12,
      4,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->18:low_risk:2",
          "18->10:low_risk:1",
          "10->0:low_time:0"
        ],
        "sequence": [
          18,
          10
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->12:low_risk:2",
          "12->4:low_time:0",
          "4->13:low_time:0",
          "13->0:low_time:0"
        ],
        "sequence": [
          12,
          4,
          13
        ],
        "start_time": 205.925
      }
    ],
    "true_dual_hash": "028c4f12cfc5d246",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.6607596278190613
  },
  {
    "active_hash_before": "16e2d0342cb4ce87",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7db256d4f7224cc6",
    "forbidden_signature_hash": "5aeacc70a6d978d0",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4",
    "pool_signature_hash": "c5ddd5b68ac1fbd8",
    "pool_task_set_hash": "6f8bb60d3048867b",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "validation",
    "source_row_index": 9,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->20:low_risk:1",
      "20->0:low_time:0"
    ],
    "target_priority_sequence": [
      12,
      20,
      5,
      3,
      6,
      4
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.5666528344154358
  },
  {
    "active_hash_before": "b93aae5cccac1118",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "fd0697a8f685dbe7",
    "forbidden_signature_hash": "0f689d4c8de40e9f",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14",
    "pool_signature_hash": "f282ddf79984d5e0",
    "pool_task_set_hash": "8f081174704db2ae",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "validation",
    "source_row_index": 11,
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
      17,
      14
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.5442947745323181
  },
  {
    "active_hash_before": "692009a078d4b4fa",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "126440b08b9f25f5",
    "forbidden_signature_hash": "8fc01c49285ec128",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20",
    "pool_signature_hash": "dc713c97248b0eab",
    "pool_task_set_hash": "603464bf2edb1804",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "validation",
    "source_row_index": 136,
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
      1,
      20
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.5340699553489685
  },
  {
    "active_hash_before": "2ea75ed4e70d366e",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "f4e732e2cfdeea6e",
    "forbidden_signature_hash": "2bd421a6b14906d2",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17",
    "pool_signature_hash": "18669646faec5846",
    "pool_task_set_hash": "732bd8493c75ee14",
    "roi_class": "negative_retry_roi",
    "source_decision_split": "validation",
    "source_row_index": 38,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->12:low_time:0",
      "12->0:low_risk:2"
    ],
    "target_priority_sequence": [
      20,
      12,
      18,
      17
    ],
    "target_sequence": [
      20,
      12,
      18,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->12:low_time:0",
          "12->0:low_risk:2"
        ],
        "sequence": [
          20,
          12
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->18:low_time:0",
          "18->17:low_risk:2",
          "17->0:low_time:0"
        ],
        "sequence": [
          18,
          17
        ],
        "start_time": 282.783247
      }
    ],
    "true_dual_hash": "755dfe2226982436",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 0,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.7431362271308899
  },
  {
    "active_hash_before": "931e9eb7f04e3978",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "67925c0d2fd4abde",
    "forbidden_signature_hash": "0497e0ba36dd09db",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7",
    "pool_signature_hash": "c1ce4f0c1c5fedec",
    "pool_task_set_hash": "eb7766f8ef463e03",
    "roi_class": "negative_primal_roi",
    "source_decision_split": "validation",
    "source_row_index": 34,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->17:low_time:0",
      "17->16:low_risk:2",
      "16->1:low_time:0",
      "1->0:low_risk:2"
    ],
    "target_priority_sequence": [
      20,
      17,
      16,
      1,
      7
    ],
    "target_sequence": [
      20,
      17,
      16,
      1,
      7
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->17:low_time:0",
          "17->16:low_risk:2",
          "16->1:low_time:0",
          "1->0:low_risk:2"
        ],
        "sequence": [
          20,
          17,
          16,
          1
        ],
        "start_time": 25.406293
      },
      {
        "arc_option_sequence": [
          "0->7:low_time:0",
          "7->0:low_time:0"
        ],
        "sequence": [
          7
        ],
        "start_time": 370.348334
      }
    ],
    "true_dual_hash": "8be9fa1cee656941",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 0,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.7299097776412964
  },
  {
    "active_hash_before": "7e1550730bce4588",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "84ae11479ed592d4",
    "forbidden_signature_hash": "cfbda5e70fc052f2",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5",
    "pool_signature_hash": "6321282f868e0007",
    "pool_task_set_hash": "f699ccb296afaee5",
    "roi_class": "no_observed_roi",
    "source_decision_split": "validation",
    "source_row_index": 176,
    "target_arc_option_sequence": [
      "0->13:low_risk:2",
      "13->17:low_risk:2",
      "17->11:low_risk:2",
      "11->0:low_time:0"
    ],
    "target_priority_sequence": [
      13,
      17,
      11,
      5
    ],
    "target_sequence": [
      13,
      17,
      11,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->17:low_risk:2",
          "17->11:low_risk:2",
          "11->0:low_time:0"
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
          "0->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          5
        ],
        "start_time": 275.78131
      }
    ],
    "true_dual_hash": "a5dfa0099f5679ed",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 0,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.7163357734680176
  },
  {
    "active_hash_before": "859cbba15c6585c7",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "4575716b3939cb89",
    "forbidden_signature_hash": "e844295219f3e8fe",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12",
    "pool_signature_hash": "2355b3378249fd7c",
    "pool_task_set_hash": "a232e0dde7906105",
    "roi_class": "negative_retry_roi",
    "source_decision_split": "validation",
    "source_row_index": 53,
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->19:low_energy:1",
      "19->9:low_risk:2",
      "9->12:low_risk:2",
      "12->0:low_time:0"
    ],
    "target_priority_sequence": [
      3,
      19,
      9,
      12
    ],
    "target_sequence": [
      3,
      19,
      9,
      12
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->19:low_energy:1",
          "19->9:low_risk:2",
          "9->12:low_risk:2",
          "12->0:low_time:0"
        ],
        "sequence": [
          3,
          19,
          9,
          12
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "2723e3b6445060e7",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 0,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.7135826349258423
  }
]
```

## Commands

### task005_mainline_no_regression_no_new_worker

Run task-5 no-regression sentinel. No worker, certificate, or official-bound shortcut is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task005_mainline_no_regression_no_new_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task005_mainline_no_regression_no_new_worker/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task005_mainline_no_regression_no_new_worker/solutions --run-log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task005_mainline_no_regression_no_new_worker/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_no_new_worker

Run task-10 no-regression sentinel. No worker, certificate, or official-bound shortcut is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task010_mainline_no_regression_no_new_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task010_mainline_no_regression_no_new_worker/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task010_mainline_no_regression_no_new_worker/solutions --run-log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task010_mainline_no_regression_no_new_worker/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_35a4908dfecb7ff3_5_18_10_8_13_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=35a4908dfecb7ff3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,18,10,8,13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,18,10,8,13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,18,10,8,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->18:low_time:0","18->10:low_risk:1","10->0:low_risk:2"],"sequence":[5,18,10],"start_time":0.0},{"arc_option_sequence":["0->8:low_time:0","8->13:low_time:0","13->0:low_time:0"],"sequence":[8,13],"start_time":230.776211}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->18:low_time:0,18->10:low_risk:1,10->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_7fc1de982db572be_18_10_12_4_13_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7fc1de982db572be --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=18,10,12,4,13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=18,10,12,4,13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=18,10,12,4,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->18:low_risk:2","18->10:low_risk:1","10->0:low_time:0"],"sequence":[18,10],"start_time":0.0},{"arc_option_sequence":["0->12:low_risk:2","12->4:low_time:0","4->13:low_time:0","13->0:low_time:0"],"sequence":[12,4,13],"start_time":205.925}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->18:low_risk:2,18->10:low_risk:1,10->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_12_20_5_3_6_4_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7db256d4f7224cc6 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,20,5,3,6,4 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,20,5,3,6,4 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,20,5,3,6,4 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_risk:2","12->20:low_risk:1","20->0:low_time:0"],"sequence":[12,20],"start_time":0.0},{"arc_option_sequence":["0->5:low_time:0","5->3:low_risk:2","3->6:low_time:0","6->4:low_energy:1","4->0:low_time:0"],"sequence":[5,3,6,4],"start_time":127.287307}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_risk:2,12->20:low_risk:1,20->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=fd0697a8f685dbe7 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,15,1,7,17,14 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,15,1,7,17,14 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,15,1,7,17,14 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_time:0","12->15:low_time:0","15->1:low_time:0","1->7:low_time:0","7->17:low_time:0","17->0:low_time:0"],"sequence":[12,15,1,7,17],"start_time":0.0},{"arc_option_sequence":["0->14:low_risk:2","14->0:low_risk:2"],"sequence":[14],"start_time":517.054496}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_time:0,12->15:low_time:0,15->1:low_time:0,1->7:low_time:0,7->17:low_time:0,17->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=126440b08b9f25f5 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,18,10,14,1,20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,18,10,14,1,20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,18,10,14,1,20 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_time:0","5->18:low_time:0","18->10:low_time:0","10->14:low_time:0","14->1:low_time:0","1->0:low_time:0"],"sequence":[5,18,10,14,1],"start_time":0.0},{"arc_option_sequence":["0->20:low_time:0","20->0:low_time:0"],"sequence":[20],"start_time":296.523456}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_time:0,5->18:low_time:0,18->10:low_time:0,10->14:low_time:0,14->1:low_time:0,1->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_f4e732e2cfdeea6e_20_12_18_17_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=f4e732e2cfdeea6e --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,12,18,17 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,12,18,17 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,12,18,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->12:low_time:0","12->0:low_risk:2"],"sequence":[20,12],"start_time":0.0},{"arc_option_sequence":["0->18:low_time:0","18->17:low_risk:2","17->0:low_time:0"],"sequence":[18,17],"start_time":282.783247}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->12:low_time:0,12->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_06_seed61520_67925c0d2fd4abde_20_17_16_1_7_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=67925c0d2fd4abde --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,17,16,1,7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,17,16,1,7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,17,16,1,7 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->17:low_time:0","17->16:low_risk:2","16->1:low_time:0","1->0:low_risk:2"],"sequence":[20,17,16,1],"start_time":25.406293},{"arc_option_sequence":["0->7:low_time:0","7->0:low_time:0"],"sequence":[7],"start_time":370.348334}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->17:low_time:0,17->16:low_risk:2,16->1:low_time:0,1->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_06_seed61512_84ae11479ed592d4_13_17_11_5_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=84ae11479ed592d4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13,17,11,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13,17,11,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,17,11,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_risk:2","13->17:low_risk:2","17->11:low_risk:2","11->0:low_time:0"],"sequence":[13,17,11],"start_time":19.222023},{"arc_option_sequence":["0->5:low_risk:2","5->0:low_risk:2"],"sequence":[5],"start_time":275.78131}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_risk:2,13->17:low_risk:2,17->11:low_risk:2,11->0:low_time:0'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_4575716b3939cb89_3_19_9_12_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=4575716b3939cb89 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3,19,9,12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3,19,9,12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,19,9,12 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_risk:2","3->19:low_energy:1","19->9:low_risk:2","9->12:low_risk:2","12->0:low_time:0"],"sequence":[3,19,9,12],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_risk:2,3->19:low_energy:1,19->9:low_risk:2,9->12:low_risk:2,12->0:low_time:0'
```

### audit_worker_roi_solver_ab_results

Read result CSVs after the solver commands finish.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_gat_worker_roi_solver_ab_results.py --runbook-summary BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/summary.json --output-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/ab_audit --report BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_20260615/ab_audit_zh.md
```

## 边界

- 该 runbook 不是生产开关；
- 5/10 命令不启用新的 hidden-negative worker；
- 20 worker 命令必须显式 opt-in；
- 所有命令都不启用 sharded Pulse certificate 或 official-bound shortcut；
- 未通过安全壳的 true-RC negative 只能延迟，不能永久丢弃。
