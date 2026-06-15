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
candidate_count = 20
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
    "active_hash_before": "ac999a633578a283",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_2_9_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "1bb852f9988a595e",
    "forbidden_signature_hash": "5cf7f32e658eaf1a",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_2_9_11",
    "pool_signature_hash": "2265db912eaee1f7",
    "pool_task_set_hash": "82653d475a300e52",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 21,
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->0:low_time:0"
    ],
    "target_priority_sequence": [
      6,
      2,
      9,
      11
    ],
    "target_sequence": [
      6,
      2,
      9,
      11
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
          "0->2:low_time:0",
          "2->9:low_risk:2",
          "9->0:low_risk:2"
        ],
        "sequence": [
          2,
          9
        ],
        "start_time": 111.591638
      },
      {
        "arc_option_sequence": [
          "0->11:low_time:0",
          "11->0:low_risk:2"
        ],
        "sequence": [
          11
        ],
        "start_time": 398.134043
      }
    ],
    "true_dual_hash": "9ead6b00b998aab0",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_2_9_11_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.0,
    "worker_roi_score": 0.7540791034698486
  },
  {
    "active_hash_before": "240ab10c01bd8a48",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "f567a0928007db23",
    "forbidden_signature_hash": "77884aa39a1dfb7d",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5",
    "pool_signature_hash": "144ee34f7c1f59b7",
    "pool_task_set_hash": "e27862a3103c1271",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 24,
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->0:low_time:0"
    ],
    "target_priority_sequence": [
      14,
      19,
      5
    ],
    "target_sequence": [
      14,
      19,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->14:low_risk:2",
          "14->0:low_time:0"
        ],
        "sequence": [
          14
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->19:low_time:0",
          "19->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          19,
          5
        ],
        "start_time": 321.763501
      }
    ],
    "true_dual_hash": "fc035d8cb1f6391c",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.7472492456436157
  },
  {
    "active_hash_before": "f709fd0ac80f9da6",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "1f855fbf33f8155e",
    "forbidden_signature_hash": "86f0c2ecc2a5f670",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15",
    "pool_signature_hash": "d39cf2bdac1f86c0",
    "pool_task_set_hash": "e8bed3973827ac75",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 108,
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->1:low_time:0",
      "1->0:low_risk:2"
    ],
    "target_priority_sequence": [
      8,
      1,
      3,
      9,
      15
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.0,
    "worker_roi_score": 0.7470447421073914
  },
  {
    "active_hash_before": "10f398c0f4b36821",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "02259d538b5f4b8d",
    "forbidden_signature_hash": "84dca92831f508c1",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15",
    "pool_signature_hash": "f5b0689c334ed19d",
    "pool_task_set_hash": "4210441777cceb45",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 107,
    "target_arc_option_sequence": [
      "0->8:low_risk:2",
      "8->13:low_risk:2",
      "13->0:low_risk:2"
    ],
    "target_priority_sequence": [
      8,
      13,
      3,
      9,
      15
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.7446147799491882
  },
  {
    "active_hash_before": "7d81deb6b7371fa5",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "68f9b4e3d7515691",
    "forbidden_signature_hash": "f9fe31b819c2bd10",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8",
    "pool_signature_hash": "f92473b9e781f066",
    "pool_task_set_hash": "8979a0515dec9dc3",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 165,
    "target_arc_option_sequence": [
      "0->7:low_time:0",
      "7->6:low_energy:1",
      "6->1:low_time:0",
      "1->19:low_energy:1",
      "19->2:low_energy:1",
      "2->8:low_time:0",
      "8->0:low_time:0"
    ],
    "target_priority_sequence": [
      7,
      6,
      1,
      19,
      2,
      8
    ],
    "target_sequence": [
      7,
      6,
      1,
      19,
      2,
      8
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->7:low_time:0",
          "7->6:low_energy:1",
          "6->1:low_time:0",
          "1->19:low_energy:1",
          "19->2:low_energy:1",
          "2->8:low_time:0",
          "8->0:low_time:0"
        ],
        "sequence": [
          7,
          6,
          1,
          19,
          2,
          8
        ],
        "start_time": 42.02574
      }
    ],
    "true_dual_hash": "b58ef7c1fadb8b40",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.0,
    "worker_roi_score": 0.743628203868866
  },
  {
    "active_hash_before": "ede095c6ba8539c1",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "9fadf4f7b39742a2",
    "forbidden_signature_hash": "cc076c836d200e54",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11",
    "pool_signature_hash": "b0fe906b0c1ab18d",
    "pool_task_set_hash": "ee50cf9eb4b638b3",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 139,
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.0,
    "worker_roi_score": 0.7339262366294861
  },
  {
    "active_hash_before": "ecf24ed55f829c83",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ee378d5c9364745a",
    "forbidden_signature_hash": "113d6a36088892f0",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11",
    "pool_signature_hash": "e5d792a2f67bb738",
    "pool_task_set_hash": "4be88547572266bd",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 167,
    "target_arc_option_sequence": [
      "0->7:low_risk:2",
      "7->14:low_time:0",
      "14->6:low_time:0",
      "6->19:low_time:0",
      "19->11:low_time:0",
      "11->0:low_risk:2"
    ],
    "target_priority_sequence": [
      7,
      14,
      6,
      19,
      11
    ],
    "target_sequence": [
      7,
      14,
      6,
      19,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->7:low_risk:2",
          "7->14:low_time:0",
          "14->6:low_time:0",
          "6->19:low_time:0",
          "19->11:low_time:0",
          "11->0:low_risk:2"
        ],
        "sequence": [
          7,
          14,
          6,
          19,
          11
        ],
        "start_time": 37.590443
      }
    ],
    "true_dual_hash": "457accd186602990",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.7206705212593079
  },
  {
    "active_hash_before": "cc48ebab3274044c",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "587e2ac350a8619b",
    "forbidden_signature_hash": "bf14d230f6d7ff3d",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14",
    "pool_signature_hash": "8153eb9aa98c60b1",
    "pool_task_set_hash": "53617fb7789de47f",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 111,
    "target_arc_option_sequence": [
      "0->3:low_risk:2",
      "3->9:low_time:0",
      "9->0:low_time:0"
    ],
    "target_priority_sequence": [
      3,
      9,
      11,
      14
    ],
    "target_sequence": [
      3,
      9,
      11,
      14
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_risk:2",
          "3->9:low_time:0",
          "9->0:low_time:0"
        ],
        "sequence": [
          3,
          9
        ],
        "start_time": 56.499463
      },
      {
        "arc_option_sequence": [
          "0->11:low_time:0",
          "11->14:low_risk:2",
          "14->0:low_risk:2"
        ],
        "sequence": [
          11,
          14
        ],
        "start_time": 370.005578
      }
    ],
    "true_dual_hash": "7d1951d926fb0a0b",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.7202669978141785
  },
  {
    "active_hash_before": "64565b767ae27294",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "8f2fd95e2f03ec41",
    "forbidden_signature_hash": "ca614602b523bed0",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13",
    "pool_signature_hash": "7154afaa8d60e43b",
    "pool_task_set_hash": "794efea398562cf5",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 26,
    "target_arc_option_sequence": [
      "0->12:low_time:0",
      "12->7:low_energy:1",
      "7->20:low_energy:1",
      "20->1:low_risk:2",
      "1->5:low_time:0",
      "5->0:low_time:0"
    ],
    "target_priority_sequence": [
      12,
      7,
      20,
      1,
      5,
      13
    ],
    "target_sequence": [
      12,
      7,
      20,
      1,
      5,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_time:0",
          "12->7:low_energy:1",
          "7->20:low_energy:1",
          "20->1:low_risk:2",
          "1->5:low_time:0",
          "5->0:low_time:0"
        ],
        "sequence": [
          12,
          7,
          20,
          1,
          5
        ],
        "start_time": 5.657341
      },
      {
        "arc_option_sequence": [
          "0->13:low_risk:2",
          "13->0:low_risk:2"
        ],
        "sequence": [
          13
        ],
        "start_time": 380.267365
      }
    ],
    "true_dual_hash": "7fcbacf6b50a27c1",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.7195776104927063
  },
  {
    "active_hash_before": "ecb46fa5e3167f5e",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "8c83e7f0dc9171d5",
    "forbidden_signature_hash": "e0d2102e81148d29",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17",
    "pool_signature_hash": "dc125a9d56232a66",
    "pool_task_set_hash": "0becd54a3becd84c",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 82,
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->5:low_time:0",
      "5->0:low_time:0"
    ],
    "target_priority_sequence": [
      3,
      5,
      10,
      8,
      17
    ],
    "target_sequence": [
      3,
      5,
      10,
      8,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->5:low_time:0",
          "5->0:low_time:0"
        ],
        "sequence": [
          3,
          5
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->10:low_risk:2",
          "10->8:low_risk:2",
          "8->17:low_time:0",
          "17->0:low_risk:2"
        ],
        "sequence": [
          10,
          8,
          17
        ],
        "start_time": 276.653227
      }
    ],
    "true_dual_hash": "9e186096c210877a",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.7068584561347961
  },
  {
    "active_hash_before": "4a4a5e04b94c74f8",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "4e481a6307fca228",
    "forbidden_signature_hash": "1d9c5491d5d23d95",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7",
    "pool_signature_hash": "d75c86554f8bc4ac",
    "pool_task_set_hash": "aeb1f7fbfb5d3984",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 113,
    "target_arc_option_sequence": [
      "0->11:low_time:0",
      "11->4:low_energy:1",
      "4->7:low_energy:1",
      "7->0:low_energy:1"
    ],
    "target_priority_sequence": [
      11,
      4,
      7
    ],
    "target_sequence": [
      11,
      4,
      7
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->11:low_time:0",
          "11->4:low_energy:1",
          "4->7:low_energy:1",
          "7->0:low_energy:1"
        ],
        "sequence": [
          11,
          4,
          7
        ],
        "start_time": 1.454325
      }
    ],
    "true_dual_hash": "07005e29e1a1264d",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.7035775780677795
  },
  {
    "active_hash_before": "ef813699d84ea6a5",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_4_2_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "c4004463c80918b5",
    "forbidden_signature_hash": "dd40587035aa50c3",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_4_2_10",
    "pool_signature_hash": "ef821b4e7d87f726",
    "pool_task_set_hash": "e9c9b682e80c660e",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 83,
    "target_arc_option_sequence": [
      "0->9:low_energy:1",
      "9->3:low_time:0",
      "3->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_priority_sequence": [
      9,
      3,
      20,
      4,
      2,
      10
    ],
    "target_sequence": [
      9,
      3,
      20,
      4,
      2,
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
          "0->4:low_risk:2",
          "4->2:low_risk:1",
          "2->10:low_risk:2",
          "10->0:low_risk:2"
        ],
        "sequence": [
          4,
          2,
          10
        ],
        "start_time": 293.846584
      }
    ],
    "true_dual_hash": "95eafdfe84624eeb",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_4_2_10_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.6579995155334473
  },
  {
    "active_hash_before": "b7829a86dcf262e8",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "d1096c4029531f56",
    "forbidden_signature_hash": "2aae101758b54a89",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19",
    "pool_signature_hash": "b6f90c6314ebd7e2",
    "pool_task_set_hash": "25774e8e0baa5782",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 143,
    "target_arc_option_sequence": [
      "0->7:low_risk:2",
      "7->0:low_risk:2"
    ],
    "target_priority_sequence": [
      7,
      1,
      8,
      11,
      19
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.6480450630187988
  },
  {
    "active_hash_before": "40f42b78b78e3668",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "77bc967e4038b08b",
    "forbidden_signature_hash": "1420da74d3d03f9f",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10",
    "pool_signature_hash": "336001920de5c08d",
    "pool_task_set_hash": "5c3e9193d63d59ad",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 30,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->6:low_risk:2",
      "6->20:low_risk:1",
      "20->0:low_risk:2"
    ],
    "target_priority_sequence": [
      4,
      6,
      20,
      18,
      2,
      10
    ],
    "target_sequence": [
      4,
      6,
      20,
      18,
      2,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->6:low_risk:2",
          "6->20:low_risk:1",
          "20->0:low_risk:2"
        ],
        "sequence": [
          4,
          6,
          20
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->18:low_risk:2",
          "18->2:low_time:0",
          "2->10:low_risk:2",
          "10->0:low_risk:2"
        ],
        "sequence": [
          18,
          2,
          10
        ],
        "start_time": 337.557281
      }
    ],
    "true_dual_hash": "702d11c8080b0386",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.6410548686981201
  },
  {
    "active_hash_before": "dddce018a60cca35",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "39ec05e43b291642",
    "forbidden_signature_hash": "77e68285a0c7aef5",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9",
    "pool_signature_hash": "23a0075d28f31ca9",
    "pool_task_set_hash": "401c7ff0289b7a0c",
    "roi_class": "negative_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 118,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_priority_sequence": [
      20,
      1,
      16,
      9
    ],
    "target_sequence": [
      20,
      1,
      16,
      9
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
          "0->16:low_time:0",
          "16->9:low_time:0",
          "9->0:low_risk:2"
        ],
        "sequence": [
          16,
          9
        ],
        "start_time": 338.393792
      }
    ],
    "true_dual_hash": "061fdac57224cbc4",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 0,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.7711381316184998
  },
  {
    "active_hash_before": "d42e4dfcb1b824f6",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "eb102a126dd0d5e3",
    "forbidden_signature_hash": "81285dc9803e02f3",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1",
    "pool_signature_hash": "dcb5e786134f42c8",
    "pool_task_set_hash": "d38707bfb680f48a",
    "roi_class": "negative_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 15,
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
      14,
      1
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 0,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.7101427316665649
  },
  {
    "active_hash_before": "a8b72d4d2bfa31e3",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_03_seed61204_6fe9dc2c7bd2affb_4_16_3_7_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "6fe9dc2c7bd2affb",
    "forbidden_signature_hash": "b93f300c295d6ec7",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_03_seed61204_6fe9dc2c7bd2affb_4_16_3_7",
    "pool_signature_hash": "ca88ae757ec81435",
    "pool_task_set_hash": "b0ca5af12c08256a",
    "roi_class": "no_observed_roi",
    "source_decision_split": "train",
    "source_row_index": 43,
    "target_arc_option_sequence": [
      "0->4:low_time:0",
      "4->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_priority_sequence": [
      4,
      16,
      3,
      7
    ],
    "target_sequence": [
      4,
      16,
      3,
      7
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_time:0",
          "4->16:low_time:0",
          "16->0:low_time:0"
        ],
        "sequence": [
          4,
          16
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->7:low_risk:2",
          "7->0:low_time:0"
        ],
        "sequence": [
          3,
          7
        ],
        "start_time": 298.516958
      }
    ],
    "true_dual_hash": "e84f3babefa22663",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_03_seed61204_6fe9dc2c7bd2affb_4_16_3_7_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 0,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.7076248526573181
  },
  {
    "active_hash_before": "3ca14dba75894c6f",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "1fa17aea2063098d",
    "forbidden_signature_hash": "5559157b1af629c3",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11",
    "pool_signature_hash": "8a1916cc5ebaa441",
    "pool_task_set_hash": "961b82b5eee8dfe0",
    "roi_class": "negative_retry_roi",
    "source_decision_split": "train",
    "source_row_index": 148,
    "target_arc_option_sequence": [
      "0->4:low_time:0",
      "4->0:low_risk:1"
    ],
    "target_priority_sequence": [
      4,
      12,
      15,
      6,
      11
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 0,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.6565749049186707
  },
  {
    "active_hash_before": "d15d7fc02d890349",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7fcd171c2901efb5",
    "forbidden_signature_hash": "65513f06a8d2c6a4",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3",
    "pool_signature_hash": "4f52b9c82025ab2f",
    "pool_task_set_hash": "7dfc197ee7d41f57",
    "roi_class": "negative_retry_roi",
    "source_decision_split": "train",
    "source_row_index": 6,
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 0,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.5408888459205627
  },
  {
    "active_hash_before": "2997fbc2110f0655",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "27b61a4367a5c961",
    "forbidden_signature_hash": "8f673626592596c9",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10",
    "pool_signature_hash": "3e7af4d3033632d1",
    "pool_task_set_hash": "1f65f261c2892ea7",
    "roi_class": "no_observed_roi",
    "source_decision_split": "train",
    "source_row_index": 132,
    "target_arc_option_sequence": [
      "0->14:low_risk:2",
      "14->2:low_risk:2",
      "2->0:low_time:0"
    ],
    "target_priority_sequence": [
      14,
      2,
      1,
      10
    ],
    "target_sequence": [
      14,
      2,
      1,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->14:low_risk:2",
          "14->2:low_risk:2",
          "2->0:low_time:0"
        ],
        "sequence": [
          14,
          2
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->1:low_time:0",
          "1->10:low_time:0",
          "10->0:low_risk:2"
        ],
        "sequence": [
          1,
          10
        ],
        "start_time": 308.552862
      }
    ],
    "true_dual_hash": "129d7d3c03467e21",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "high_priority",
    "worker_roi_label_positive": 0,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.5342870950698853
  }
]
```

## Commands

### task005_mainline_no_regression_no_new_worker

Run task-5 no-regression sentinel. No worker, certificate, or official-bound shortcut is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task005_mainline_no_regression_no_new_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task005_mainline_no_regression_no_new_worker/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task005_mainline_no_regression_no_new_worker/solutions --run-log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task005_mainline_no_regression_no_new_worker/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_no_new_worker

Run task-10 no-regression sentinel. No worker, certificate, or official-bound shortcut is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task010_mainline_no_regression_no_new_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task010_mainline_no_regression_no_new_worker/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task010_mainline_no_regression_no_new_worker/solutions --run-log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task010_mainline_no_regression_no_new_worker/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_2_9_11_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_2_9_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_2_9_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_2_9_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_2_9_11_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_2_9_11_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_2_9_11_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_2_9_11_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=1bb852f9988a595e --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=6,2,9,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=6,2,9,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=6,2,9,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->6:low_time:0","6->0:low_time:0"],"sequence":[6],"start_time":0.0},{"arc_option_sequence":["0->2:low_time:0","2->9:low_risk:2","9->0:low_risk:2"],"sequence":[2,9],"start_time":111.591638},{"arc_option_sequence":["0->11:low_time:0","11->0:low_risk:2"],"sequence":[11],"start_time":398.134043}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->6:low_time:0,6->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_14_19_5_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=f567a0928007db23 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=14,19,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=14,19,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=14,19,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->14:low_risk:2","14->0:low_time:0"],"sequence":[14],"start_time":0.0},{"arc_option_sequence":["0->19:low_time:0","19->5:low_risk:2","5->0:low_risk:2"],"sequence":[19,5],"start_time":321.763501}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->14:low_risk:2,14->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_1f855fbf33f8155e_8_1_3_9_15_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=1f855fbf33f8155e --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,1,3,9,15 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,1,3,9,15 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,1,3,9,15 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_time:0","8->1:low_time:0","1->0:low_risk:2"],"sequence":[8,1],"start_time":0.0},{"arc_option_sequence":["0->3:low_time:0","3->9:low_risk:2","9->15:low_risk:2","15->0:low_risk:2"],"sequence":[3,9,15],"start_time":261.945896}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_time:0,8->1:low_time:0,1->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=02259d538b5f4b8d --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,13,3,9,15 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,13,3,9,15 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,13,3,9,15 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_risk:2","8->13:low_risk:2","13->0:low_risk:2"],"sequence":[8,13],"start_time":0.0},{"arc_option_sequence":["0->3:low_risk:2","3->9:low_time:0","9->15:low_risk:2","15->0:low_risk:2"],"sequence":[3,9,15],"start_time":256.62628}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_risk:2,8->13:low_risk:2,13->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_68f9b4e3d7515691_7_6_1_19_2_8_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=68f9b4e3d7515691 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=7,6,1,19,2,8 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=7,6,1,19,2,8 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=7,6,1,19,2,8 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->7:low_time:0","7->6:low_energy:1","6->1:low_time:0","1->19:low_energy:1","19->2:low_energy:1","2->8:low_time:0","8->0:low_time:0"],"sequence":[7,6,1,19,2,8],"start_time":42.02574}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->7:low_time:0,7->6:low_energy:1,6->1:low_time:0,1->19:low_energy:1,19->2:low_energy:1,2->8:low_time:0,8->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=9fadf4f7b39742a2 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13,8,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13,8,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,8,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_risk:2","13->8:low_time:0","8->11:low_risk:2","11->0:low_time:0"],"sequence":[13,8,11],"start_time":0.264013}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_risk:2,13->8:low_time:0,8->11:low_risk:2,11->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_ee378d5c9364745a_7_14_6_19_11_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ee378d5c9364745a --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=7,14,6,19,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=7,14,6,19,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=7,14,6,19,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->7:low_risk:2","7->14:low_time:0","14->6:low_time:0","6->19:low_time:0","19->11:low_time:0","11->0:low_risk:2"],"sequence":[7,14,6,19,11],"start_time":37.590443}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->7:low_risk:2,7->14:low_time:0,14->6:low_time:0,6->19:low_time:0,19->11:low_time:0,11->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=587e2ac350a8619b --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3,9,11,14 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3,9,11,14 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,9,11,14 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_risk:2","3->9:low_time:0","9->0:low_time:0"],"sequence":[3,9],"start_time":56.499463},{"arc_option_sequence":["0->11:low_time:0","11->14:low_risk:2","14->0:low_risk:2"],"sequence":[11,14],"start_time":370.005578}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_risk:2,3->9:low_time:0,9->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_8f2fd95e2f03ec41_12_7_20_1_5_13_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=8f2fd95e2f03ec41 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,7,20,1,5,13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,7,20,1,5,13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,7,20,1,5,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_time:0","12->7:low_energy:1","7->20:low_energy:1","20->1:low_risk:2","1->5:low_time:0","5->0:low_time:0"],"sequence":[12,7,20,1,5],"start_time":5.657341},{"arc_option_sequence":["0->13:low_risk:2","13->0:low_risk:2"],"sequence":[13],"start_time":380.267365}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_time:0,12->7:low_energy:1,7->20:low_energy:1,20->1:low_risk:2,1->5:low_time:0,5->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_8c83e7f0dc9171d5_3_5_10_8_17_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=8c83e7f0dc9171d5 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3,5,10,8,17 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3,5,10,8,17 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,5,10,8,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_time:0","3->5:low_time:0","5->0:low_time:0"],"sequence":[3,5],"start_time":0.0},{"arc_option_sequence":["0->10:low_risk:2","10->8:low_risk:2","8->17:low_time:0","17->0:low_risk:2"],"sequence":[10,8,17],"start_time":276.653227}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_time:0,3->5:low_time:0,5->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=4e481a6307fca228 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=11,4,7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=11,4,7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=11,4,7 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->11:low_time:0","11->4:low_energy:1","4->7:low_energy:1","7->0:low_energy:1"],"sequence":[11,4,7],"start_time":1.454325}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->11:low_time:0,11->4:low_energy:1,4->7:low_energy:1,7->0:low_energy:1'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_4_2_10_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_4_2_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_4_2_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_4_2_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_4_2_10_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_4_2_10_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_4_2_10_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_c4004463c80918b5_9_3_20_4_2_10_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=c4004463c80918b5 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=9,3,20,4,2,10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=9,3,20,4,2,10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=9,3,20,4,2,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->9:low_energy:1","9->3:low_time:0","3->20:low_time:0","20->0:low_time:0"],"sequence":[9,3,20],"start_time":0.0},{"arc_option_sequence":["0->4:low_risk:2","4->2:low_risk:1","2->10:low_risk:2","10->0:low_risk:2"],"sequence":[4,2,10],"start_time":293.846584}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->9:low_energy:1,9->3:low_time:0,3->20:low_time:0,20->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=d1096c4029531f56 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=7,1,8,11,19 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=7,1,8,11,19 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=7,1,8,11,19 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->7:low_risk:2","7->0:low_risk:2"],"sequence":[7],"start_time":0.0},{"arc_option_sequence":["0->1:low_time:0","1->8:low_time:0","8->11:low_energy:1","11->0:low_energy:1"],"sequence":[1,8,11],"start_time":83.548501},{"arc_option_sequence":["0->19:low_risk:2","19->0:low_time:0"],"sequence":[19],"start_time":415.228421}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->7:low_risk:2,7->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_77bc967e4038b08b_4_6_20_18_2_10_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=77bc967e4038b08b --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4,6,20,18,2,10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4,6,20,18,2,10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,6,20,18,2,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_risk:2","4->6:low_risk:2","6->20:low_risk:1","20->0:low_risk:2"],"sequence":[4,6,20],"start_time":0.0},{"arc_option_sequence":["0->18:low_risk:2","18->2:low_time:0","2->10:low_risk:2","10->0:low_risk:2"],"sequence":[18,2,10],"start_time":337.557281}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_risk:2,4->6:low_risk:2,6->20:low_risk:1,20->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=39ec05e43b291642 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,1,16,9 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,1,16,9 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,1,16,9 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->1:low_time:0","1->0:low_time:0"],"sequence":[20,1],"start_time":0.0},{"arc_option_sequence":["0->16:low_time:0","16->9:low_time:0","9->0:low_risk:2"],"sequence":[16,9],"start_time":338.393792}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->1:low_time:0,1->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_07_seed61614_eb102a126dd0d5e3_9_10_4_14_1_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=eb102a126dd0d5e3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=9,10,4,14,1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=9,10,4,14,1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=9,10,4,14,1 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->9:low_time:0","9->10:low_risk:2","10->4:low_time:0","4->14:low_time:0","14->0:low_risk:2"],"sequence":[9,10,4,14],"start_time":0.0},{"arc_option_sequence":["0->1:low_risk:1","1->0:low_risk:1"],"sequence":[1],"start_time":417.91101}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->9:low_time:0,9->10:low_risk:2,10->4:low_time:0,4->14:low_time:0,14->0:low_risk:2'
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_03_seed61204_6fe9dc2c7bd2affb_4_16_3_7_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_03_seed61204_6fe9dc2c7bd2affb_4_16_3_7_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_03_seed61204_6fe9dc2c7bd2affb_4_16_3_7_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_03_seed61204_6fe9dc2c7bd2affb_4_16_3_7_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_random_wave_randomtw_tasks020_03_seed61204_6fe9dc2c7bd2affb_4_16_3_7_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_03_seed61204_6fe9dc2c7bd2affb_4_16_3_7_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_03_seed61204_6fe9dc2c7bd2affb_4_16_3_7_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_03_seed61204_6fe9dc2c7bd2affb_4_16_3_7_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=6fe9dc2c7bd2affb --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4,16,3,7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4,16,3,7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,16,3,7 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_time:0","4->16:low_time:0","16->0:low_time:0"],"sequence":[4,16],"start_time":0.0},{"arc_option_sequence":["0->3:low_time:0","3->7:low_risk:2","7->0:low_time:0"],"sequence":[3,7],"start_time":298.516958}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_time:0,4->16:low_time:0,16->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_03_seed61204_1fa17aea2063098d_4_12_15_6_11_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=1fa17aea2063098d --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4,12,15,6,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4,12,15,6,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,12,15,6,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_time:0","4->0:low_risk:1"],"sequence":[4],"start_time":0.0},{"arc_option_sequence":["0->12:low_risk:2","12->15:low_risk:2","15->6:low_risk:2","6->11:low_risk:2","11->0:low_risk:2"],"sequence":[12,15,6,11],"start_time":253.641299}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_time:0,4->0:low_risk:1'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7fcd171c2901efb5 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=6,12,13,8,15,3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=6,12,13,8,15,3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=6,12,13,8,15,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->6:low_energy:1","6->12:low_energy:1","12->13:low_time:0","13->8:low_time:0","8->15:low_energy:1","15->3:low_risk:2","3->0:low_time:0"],"sequence":[6,12,13,8,15,3],"start_time":51.341994}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->6:low_energy:1,6->12:low_energy:1,12->13:low_time:0,13->8:low_time:0,8->15:low_energy:1,15->3:low_risk:2,3->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=27b61a4367a5c961 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=14,2,1,10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=14,2,1,10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=14,2,1,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->14:low_risk:2","14->2:low_risk:2","2->0:low_time:0"],"sequence":[14,2],"start_time":0.0},{"arc_option_sequence":["0->1:low_time:0","1->10:low_time:0","10->0:low_risk:2"],"sequence":[1,10],"start_time":308.552862}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->14:low_risk:2,14->2:low_risk:2,2->0:low_time:0'
```

### audit_worker_roi_solver_ab_results

Read result CSVs after the solver commands finish.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_gat_worker_roi_solver_ab_results.py --runbook-summary BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/summary.json --output-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/ab_audit --report BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_high_priority_20260615/ab_audit_zh.md
```

## 边界

- 该 runbook 不是生产开关；
- 5/10 命令不启用新的 hidden-negative worker；
- 20 worker 命令必须显式 opt-in；
- 所有命令都不启用 sharded Pulse certificate 或 official-bound shortcut；
- 未通过安全壳的 true-RC negative 只能延迟，不能永久丢弃。
