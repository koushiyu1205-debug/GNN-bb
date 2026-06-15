# GAT Worker ROI Solver A/B Runbook 报告

日期：2026-06-15

## 目的

生成下一轮 solver A/B 命令：5/10 只做 no-regression sentinel，20 只对
worker-ROI GAT + kNN/OOD 筛出的候选做显式 opt-in
worker A/B。该脚本不运行求解器。

## 机器字段

```text
gat_worker_roi_solver_ab_runbook = current
status = ready
runs_bpc_or_pricing = false
candidate_count = 20
decision_split = train
decision_name = DELAY_QUEUE
positive_label_only = true
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
    "active_hash_before": "5894e951a05a1faa",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "95e9afaf1ecbdc5e",
    "forbidden_signature_hash": "4182ceb6aa0b797b",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5",
    "pool_signature_hash": "45291c069493c3fc",
    "pool_task_set_hash": "ef6a763bfdd0598d",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 90,
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->13:low_time:0",
      "13->5:low_risk:2",
      "5->0:low_risk:2"
    ],
    "target_priority_sequence": [
      16,
      13,
      5
    ],
    "target_sequence": [
      16,
      13,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->16:low_time:0",
          "16->13:low_time:0",
          "13->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          16,
          13,
          5
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "e33e47c513ec81dd",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.9202136993408203
  },
  {
    "active_hash_before": "5484cfcba13e66bf",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b9550ffc9a42531a",
    "forbidden_signature_hash": "8a7f2efca8be1f44",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7",
    "pool_signature_hash": "9961c8d724c0a30e",
    "pool_task_set_hash": "6b572b1a351f1547",
    "roi_class": "positive_retry_roi",
    "source_decision_split": "train",
    "source_row_index": 86,
    "target_arc_option_sequence": [
      "0->13:low_time:0",
      "13->0:low_time:0"
    ],
    "target_priority_sequence": [
      13,
      20,
      7
    ],
    "target_sequence": [
      13,
      20,
      7
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
          "0->20:low_time:0",
          "20->7:low_risk:2",
          "7->0:low_time:0"
        ],
        "sequence": [
          20,
          7
        ],
        "start_time": 136.776061
      }
    ],
    "true_dual_hash": "9973b6cde0956787",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.8044934868812561
  },
  {
    "active_hash_before": "f8111e12b798ea28",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "dfd68d5873b84183",
    "forbidden_signature_hash": "6de0b545d5e610b8",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12",
    "pool_signature_hash": "8ec5c004bb6bc8ed",
    "pool_task_set_hash": "95cda2345f7c9f1e",
    "roi_class": "positive_retry_roi",
    "source_decision_split": "train",
    "source_row_index": 106,
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_priority_sequence": [
      20,
      1,
      17,
      12
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.7884826064109802
  },
  {
    "active_hash_before": "240ab10c01bd8a48",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_2_7_9_15_1_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "f567a0928007db23",
    "forbidden_signature_hash": "77884aa39a1dfb7d",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_2_7_9_15_1_5",
    "pool_signature_hash": "144ee34f7c1f59b7",
    "pool_task_set_hash": "e27862a3103c1271",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 23,
    "target_arc_option_sequence": [
      "0->2:low_risk:2",
      "2->7:low_risk:1",
      "7->9:low_time:0",
      "9->0:low_energy:1"
    ],
    "target_priority_sequence": [
      2,
      7,
      9,
      15,
      1,
      5
    ],
    "target_sequence": [
      2,
      7,
      9,
      15,
      1,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_risk:2",
          "2->7:low_risk:1",
          "7->9:low_time:0",
          "9->0:low_energy:1"
        ],
        "sequence": [
          2,
          7,
          9
        ],
        "start_time": 47.875727
      },
      {
        "arc_option_sequence": [
          "0->15:low_time:0",
          "15->1:low_time:0",
          "1->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          15,
          1,
          5
        ],
        "start_time": 352.973083
      }
    ],
    "true_dual_hash": "fc035d8cb1f6391c",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_2_7_9_15_1_5_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.7474702596664429
  },
  {
    "active_hash_before": "ac999a633578a283",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "1bb852f9988a595e",
    "forbidden_signature_hash": "5cf7f32e658eaf1a",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12",
    "pool_signature_hash": "2265db912eaee1f7",
    "pool_task_set_hash": "82653d475a300e52",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 22,
    "target_arc_option_sequence": [
      "0->6:low_risk:2",
      "6->0:low_risk:2"
    ],
    "target_priority_sequence": [
      6,
      8,
      12
    ],
    "target_sequence": [
      6,
      8,
      12
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->6:low_risk:2",
          "6->0:low_risk:2"
        ],
        "sequence": [
          6
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->8:low_risk:2",
          "8->12:low_risk:2",
          "12->0:low_risk:2"
        ],
        "sequence": [
          8,
          12
        ],
        "start_time": 120.753552
      }
    ],
    "true_dual_hash": "9ead6b00b998aab0",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.739058256149292
  },
  {
    "active_hash_before": "cc42ac61a4bb4b25",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "476979944ba39894",
    "forbidden_signature_hash": "3001f40bc7704684",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2",
    "pool_signature_hash": "88e14580c1ef8568",
    "pool_task_set_hash": "60d6171b920b56ac",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 89,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->2:low_risk:2",
      "2->0:low_risk:2"
    ],
    "target_priority_sequence": [
      12,
      2
    ],
    "target_sequence": [
      12,
      2
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_risk:2",
          "12->2:low_risk:2",
          "2->0:low_risk:2"
        ],
        "sequence": [
          12,
          2
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "2200cc932203c596",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.724624752998352
  },
  {
    "active_hash_before": "6f26a129c0a74572",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_13_3_8_18_1_11_15_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "301df9ab59b370e5",
    "forbidden_signature_hash": "27613a5a2fc0bdd9",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_13_3_8_18_1_11_15_5",
    "pool_signature_hash": "f8a257bac43ed26d",
    "pool_task_set_hash": "e23235e41c882db8",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 20,
    "target_arc_option_sequence": [
      "0->13:low_risk:1",
      "13->0:low_risk:1"
    ],
    "target_priority_sequence": [
      13,
      3,
      8,
      18,
      1,
      11,
      15,
      5
    ],
    "target_sequence": [
      13,
      3,
      8,
      18,
      1,
      11,
      15,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->13:low_risk:1",
          "13->0:low_risk:1"
        ],
        "sequence": [
          13
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->3:low_risk:1",
          "3->8:low_time:0",
          "8->18:low_risk:1",
          "18->1:low_time:0",
          "1->11:low_time:0",
          "11->15:low_risk:2",
          "15->0:low_time:0"
        ],
        "sequence": [
          3,
          8,
          18,
          1,
          11,
          15
        ],
        "start_time": 51.811325
      },
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          5
        ],
        "start_time": 600.34012
      }
    ],
    "true_dual_hash": "70940f4fa376fcc3",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_13_3_8_18_1_11_15_5_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.7190026640892029
  },
  {
    "active_hash_before": "96c7c0766604244a",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "forbidden_signature_hash": "16f38b9203fc0908",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17",
    "pool_signature_hash": "a3a808a977a593aa",
    "pool_task_set_hash": "393c147abf261db2",
    "roi_class": "positive_retry_roi",
    "source_decision_split": "train",
    "source_row_index": 105,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->0:low_risk:2"
    ],
    "target_priority_sequence": [
      4,
      19,
      10,
      17
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.7045243978500366
  },
  {
    "active_hash_before": "ede095c6ba8539c1",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "9fadf4f7b39742a2",
    "forbidden_signature_hash": "cc076c836d200e54",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10",
    "pool_signature_hash": "b0fe906b0c1ab18d",
    "pool_task_set_hash": "ee50cf9eb4b638b3",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 109,
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->7:low_time:0",
      "7->0:low_time:0"
    ],
    "target_priority_sequence": [
      1,
      7,
      20,
      4,
      10
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.7042238712310791
  },
  {
    "active_hash_before": "6f26a129c0a74572",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "301df9ab59b370e5",
    "forbidden_signature_hash": "27613a5a2fc0bdd9",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14",
    "pool_signature_hash": "f8a257bac43ed26d",
    "pool_task_set_hash": "e23235e41c882db8",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 19,
    "target_arc_option_sequence": [
      "0->3:low_risk:1",
      "3->8:low_risk:2",
      "8->0:low_time:0"
    ],
    "target_priority_sequence": [
      3,
      8,
      9,
      14
    ],
    "target_sequence": [
      3,
      8,
      9,
      14
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_risk:1",
          "3->8:low_risk:2",
          "8->0:low_time:0"
        ],
        "sequence": [
          3,
          8
        ],
        "start_time": 25.896557
      },
      {
        "arc_option_sequence": [
          "0->9:low_risk:2",
          "9->14:low_time:0",
          "14->0:low_time:0"
        ],
        "sequence": [
          9,
          14
        ],
        "start_time": 288.359466
      }
    ],
    "true_dual_hash": "70940f4fa376fcc3",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.7024853825569153
  },
  {
    "active_hash_before": "0d3647e8bc157d9b",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "09187873900ecefa",
    "forbidden_signature_hash": "98790f7f88eda8f5",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16",
    "pool_signature_hash": "8e11a6df2fd8e8c8",
    "pool_task_set_hash": "fa332705423b4447",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 116,
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_priority_sequence": [
      6,
      20,
      4,
      16
    ],
    "target_sequence": [
      6,
      20,
      4,
      16
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->6:low_time:0",
          "6->20:low_time:0",
          "20->0:low_time:0"
        ],
        "sequence": [
          6,
          20
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->4:low_energy:1",
          "4->16:low_time:0",
          "16->0:low_time:0"
        ],
        "sequence": [
          4,
          16
        ],
        "start_time": 265.299525
      }
    ],
    "true_dual_hash": "8bc1731e75d1e97a",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.6899321675300598
  },
  {
    "active_hash_before": "eb7ddfb3029ed64d",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b1fb77954b949bf0",
    "forbidden_signature_hash": "81497f2e29d39933",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17",
    "pool_signature_hash": "e2151485b49e03db",
    "pool_task_set_hash": "74fb358c2ad9aae8",
    "roi_class": "positive_retry_roi",
    "source_decision_split": "train",
    "source_row_index": 7,
    "target_arc_option_sequence": [
      "0->6:low_time:0",
      "6->12:low_time:0",
      "12->7:low_time:0",
      "7->0:low_time:0"
    ],
    "target_priority_sequence": [
      6,
      12,
      7,
      16,
      17
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.6806185841560364
  },
  {
    "active_hash_before": "0d3647e8bc157d9b",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "09187873900ecefa",
    "forbidden_signature_hash": "98790f7f88eda8f5",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18",
    "pool_signature_hash": "8e11a6df2fd8e8c8",
    "pool_task_set_hash": "fa332705423b4447",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 147,
    "target_arc_option_sequence": [
      "0->6:low_risk:2",
      "6->5:low_risk:2",
      "5->0:low_risk:2"
    ],
    "target_priority_sequence": [
      6,
      5,
      4,
      16,
      18
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.6662838459014893
  },
  {
    "active_hash_before": "0959cbac9e46d813",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_4_2_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "12cfa32e4756fd37",
    "forbidden_signature_hash": "aca48a99c4cebe6f",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_4_2_10",
    "pool_signature_hash": "e4f62a0f69ce5910",
    "pool_task_set_hash": "ce877e4ac6870ac8",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 79,
    "target_arc_option_sequence": [
      "0->3:low_time:0",
      "3->9:low_time:0",
      "9->0:low_risk:2"
    ],
    "target_priority_sequence": [
      3,
      9,
      4,
      2,
      10
    ],
    "target_sequence": [
      3,
      9,
      4,
      2,
      10
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->9:low_time:0",
          "9->0:low_risk:2"
        ],
        "sequence": [
          3,
          9
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
    "true_dual_hash": "714062ee92317ed5",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_4_2_10_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.6601263284683228
  },
  {
    "active_hash_before": "b54cdb488e305b84",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "1625c1776efc58ed",
    "forbidden_signature_hash": "4bcc9f644e25d5f6",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4",
    "pool_signature_hash": "e0dbc1428ea1e199",
    "pool_task_set_hash": "8fc2386d5b9953d0",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 25,
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->7:low_risk:2",
      "7->2:low_risk:2",
      "2->1:low_time:0",
      "1->0:low_time:0"
    ],
    "target_priority_sequence": [
      12,
      7,
      2,
      1,
      10,
      4
    ],
    "target_sequence": [
      12,
      7,
      2,
      1,
      10,
      4
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_risk:2",
          "12->7:low_risk:2",
          "7->2:low_risk:2",
          "2->1:low_time:0",
          "1->0:low_time:0"
        ],
        "sequence": [
          12,
          7,
          2,
          1
        ],
        "start_time": 2.442032
      },
      {
        "arc_option_sequence": [
          "0->10:low_risk:2",
          "10->4:low_risk:2",
          "4->0:low_time:0"
        ],
        "sequence": [
          10,
          4
        ],
        "start_time": 271.464168
      }
    ],
    "true_dual_hash": "557fc046535ce949",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.6574167609214783
  },
  {
    "active_hash_before": "7eeb299c32e32476",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_79c1e81dc9889c24_5_6_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "79c1e81dc9889c24",
    "forbidden_signature_hash": "30ac0a14812aa5f5",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_79c1e81dc9889c24_5_6_10",
    "pool_signature_hash": "da6d30eaaf75199b",
    "pool_task_set_hash": "768d5dfa2337a920",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 67,
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
      10
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
      }
    ],
    "true_dual_hash": "2747ddfbfd0c5866",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_79c1e81dc9889c24_5_6_10_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.5676180124282837
  },
  {
    "active_hash_before": "3c1f1334f5a3a2bc",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "d8b85dff55093cb1",
    "forbidden_signature_hash": "49b6ee68adb7494e",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7",
    "pool_signature_hash": "68e19f6eafe316a7",
    "pool_task_set_hash": "5d7b3c3440e0a8ae",
    "roi_class": "positive_primal_roi",
    "source_decision_split": "train",
    "source_row_index": 31,
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->6:low_time:0",
      "6->20:low_risk:1",
      "20->0:low_risk:2"
    ],
    "target_priority_sequence": [
      4,
      6,
      20,
      3,
      7
    ],
    "target_sequence": [
      4,
      6,
      20,
      3,
      7
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->6:low_time:0",
          "6->20:low_risk:1",
          "20->0:low_risk:2"
        ],
        "sequence": [
          4,
          6,
          20
        ],
        "start_time": 4.4203
      },
      {
        "arc_option_sequence": [
          "0->3:low_time:0",
          "3->7:low_time:0",
          "7->0:low_time:0"
        ],
        "sequence": [
          3,
          7
        ],
        "start_time": 326.708516
      }
    ],
    "true_dual_hash": "d3c94df3fc13c59d",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.5635644793510437
  },
  {
    "active_hash_before": "5260be3d13fa9cda",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b36178f6655c5f75",
    "forbidden_signature_hash": "b7258704c52ca4cf",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3",
    "pool_signature_hash": "6dae80d2a19d1b2c",
    "pool_task_set_hash": "b8a49f5ce498f751",
    "roi_class": "positive_retry_roi",
    "source_decision_split": "train",
    "source_row_index": 8,
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->12:low_risk:1",
      "12->13:low_risk:2",
      "13->8:low_risk:2",
      "8->15:low_time:0",
      "15->3:low_risk:2",
      "3->0:low_time:0"
    ],
    "target_priority_sequence": [
      2,
      12,
      13,
      8,
      15,
      3
    ],
    "target_sequence": [
      2,
      12,
      13,
      8,
      15,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_time:0",
          "2->12:low_risk:1",
          "12->13:low_risk:2",
          "13->8:low_risk:2",
          "8->15:low_time:0",
          "15->3:low_risk:2",
          "3->0:low_time:0"
        ],
        "sequence": [
          2,
          12,
          13,
          8,
          15,
          3
        ],
        "start_time": 53.762891
      }
    ],
    "true_dual_hash": "8c208ac829a68b55",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "neighbor_delay_fraction_too_high",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.5428135991096497
  },
  {
    "active_hash_before": "e26a52ba1316b49c",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7079ec06a2d9eab3",
    "forbidden_signature_hash": "3359fd60e0ee35a2",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5",
    "pool_signature_hash": "25120bd919c33dc8",
    "pool_task_set_hash": "436be223c00e008d",
    "roi_class": "positive_retry_roi",
    "source_decision_split": "train",
    "source_row_index": 157,
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->14:low_risk:2",
      "14->11:low_time:0",
      "11->9:low_time:0",
      "9->0:low_time:0"
    ],
    "target_priority_sequence": [
      8,
      14,
      11,
      9,
      17,
      5
    ],
    "target_sequence": [
      8,
      14,
      11,
      9,
      17,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->14:low_risk:2",
          "14->11:low_time:0",
          "11->9:low_time:0",
          "9->0:low_time:0"
        ],
        "sequence": [
          8,
          14,
          11,
          9
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->17:low_time:0",
          "17->5:low_risk:2",
          "5->0:low_risk:2"
        ],
        "sequence": [
          17,
          5
        ],
        "start_time": 381.433678
      }
    ],
    "true_dual_hash": "1fc854fed0a1689d",
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "score_below_threshold",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.3333333333333333,
    "worker_roi_score": 0.528631865978241
  },
  {
    "active_hash_before": "20ecd0ba075a5cd4",
    "baseline_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b6507dfb6db81d64",
    "forbidden_signature_hash": "a9fa6948e89224a2",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10",
    "pool_signature_hash": "256ff5712f06f6ee",
    "pool_task_set_hash": "5ab012b4a6716038",
    "roi_class": "positive_retry_roi",
    "source_decision_split": "train",
    "source_row_index": 135,
    "target_arc_option_sequence": [
      "0->16:low_risk:2",
      "16->0:low_risk:2"
    ],
    "target_priority_sequence": [
      16,
      11,
      12,
      10
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
    "worker_csv": "BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_worker_roi_gat_priority/results.csv",
    "worker_roi_decision_reason": "score_below_threshold",
    "worker_roi_label_positive": 1,
    "worker_roi_neighbor_delay_fraction": 0.6666666666666666,
    "worker_roi_score": 0.525368869304657
  }
]
```

## Commands

### task005_mainline_no_regression_no_new_worker

Run task-5 no-regression sentinel. No worker, certificate, or official-bound shortcut is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task005_mainline_no_regression_no_new_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task005_mainline_no_regression_no_new_worker/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task005_mainline_no_regression_no_new_worker/solutions --run-log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task005_mainline_no_regression_no_new_worker/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_no_new_worker

Run task-10 no-regression sentinel. No worker, certificate, or official-bound shortcut is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task010_mainline_no_regression_no_new_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task010_mainline_no_regression_no_new_worker/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task010_mainline_no_regression_no_new_worker/solutions --run-log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task010_mainline_no_regression_no_new_worker/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=95e9afaf1ecbdc5e --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=16,13,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=16,13,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=16,13,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->16:low_time:0","16->13:low_time:0","13->5:low_risk:2","5->0:low_risk:2"],"sequence":[16,13,5],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->16:low_time:0,16->13:low_time:0,13->5:low_risk:2,5->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b9550ffc9a42531a --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13,20,7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13,20,7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,20,7 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_time:0","13->0:low_time:0"],"sequence":[13],"start_time":0.0},{"arc_option_sequence":["0->20:low_time:0","20->7:low_risk:2","7->0:low_time:0"],"sequence":[20,7],"start_time":136.776061}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_time:0,13->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_dfd68d5873b84183_20_1_17_12_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=dfd68d5873b84183 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,1,17,12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,1,17,12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,1,17,12 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->1:low_time:0","1->0:low_time:0"],"sequence":[20,1],"start_time":0.0},{"arc_option_sequence":["0->17:low_time:0","17->12:low_time:0","12->0:low_time:0"],"sequence":[17,12],"start_time":296.270931}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->1:low_time:0,1->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_2_7_9_15_1_5_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_2_7_9_15_1_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_2_7_9_15_1_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_2_7_9_15_1_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_2_7_9_15_1_5_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_2_7_9_15_1_5_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_2_7_9_15_1_5_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_f567a0928007db23_2_7_9_15_1_5_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=f567a0928007db23 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=2,7,9,15,1,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=2,7,9,15,1,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=2,7,9,15,1,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->2:low_risk:2","2->7:low_risk:1","7->9:low_time:0","9->0:low_energy:1"],"sequence":[2,7,9],"start_time":47.875727},{"arc_option_sequence":["0->15:low_time:0","15->1:low_time:0","1->5:low_risk:2","5->0:low_risk:2"],"sequence":[15,1,5],"start_time":352.973083}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->2:low_risk:2,2->7:low_risk:1,7->9:low_time:0,9->0:low_energy:1'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_01_seed61001_1bb852f9988a595e_6_8_12_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=1bb852f9988a595e --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=6,8,12 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=6,8,12 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=6,8,12 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->6:low_risk:2","6->0:low_risk:2"],"sequence":[6],"start_time":0.0},{"arc_option_sequence":["0->8:low_risk:2","8->12:low_risk:2","12->0:low_risk:2"],"sequence":[8,12],"start_time":120.753552}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->6:low_risk:2,6->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=476979944ba39894 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,2 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,2 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,2 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_risk:2","12->2:low_risk:2","2->0:low_risk:2"],"sequence":[12,2],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_risk:2,12->2:low_risk:2,2->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_13_3_8_18_1_11_15_5_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_13_3_8_18_1_11_15_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_13_3_8_18_1_11_15_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_13_3_8_18_1_11_15_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_13_3_8_18_1_11_15_5_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_13_3_8_18_1_11_15_5_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_13_3_8_18_1_11_15_5_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_13_3_8_18_1_11_15_5_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=301df9ab59b370e5 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13,3,8,18,1,11,15,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13,3,8,18,1,11,15,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,3,8,18,1,11,15,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_risk:1","13->0:low_risk:1"],"sequence":[13],"start_time":0.0},{"arc_option_sequence":["0->3:low_risk:1","3->8:low_time:0","8->18:low_risk:1","18->1:low_time:0","1->11:low_time:0","11->15:low_risk:2","15->0:low_time:0"],"sequence":[3,8,18,1,11,15],"start_time":51.811325},{"arc_option_sequence":["0->5:low_risk:2","5->0:low_risk:2"],"sequence":[5],"start_time":600.34012}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_risk:1,13->0:low_risk:1'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ac15bc4e7e3d6fff --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4,19,10,17 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4,19,10,17 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,19,10,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_risk:2","4->0:low_risk:2"],"sequence":[4],"start_time":0.0},{"arc_option_sequence":["0->19:low_risk:2","19->10:low_time:0","10->17:low_risk:2","17->0:low_time:0"],"sequence":[19,10,17],"start_time":202.264867}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_risk:2,4->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_1_7_20_4_10_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=9fadf4f7b39742a2 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=1,7,20,4,10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=1,7,20,4,10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=1,7,20,4,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->1:low_time:0","1->7:low_time:0","7->0:low_time:0"],"sequence":[1,7],"start_time":0.0},{"arc_option_sequence":["0->20:low_risk:2","20->4:low_time:0","4->10:low_time:0","10->0:low_risk:2"],"sequence":[20,4,10],"start_time":210.842101}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->1:low_time:0,1->7:low_time:0,7->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_09_seed61818_301df9ab59b370e5_3_8_9_14_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=301df9ab59b370e5 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3,8,9,14 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3,8,9,14 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,8,9,14 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_risk:1","3->8:low_risk:2","8->0:low_time:0"],"sequence":[3,8],"start_time":25.896557},{"arc_option_sequence":["0->9:low_risk:2","9->14:low_time:0","14->0:low_time:0"],"sequence":[9,14],"start_time":288.359466}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_risk:1,3->8:low_risk:2,8->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=09187873900ecefa --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=6,20,4,16 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=6,20,4,16 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=6,20,4,16 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->6:low_time:0","6->20:low_time:0","20->0:low_time:0"],"sequence":[6,20],"start_time":0.0},{"arc_option_sequence":["0->4:low_energy:1","4->16:low_time:0","16->0:low_time:0"],"sequence":[4,16],"start_time":265.299525}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->6:low_time:0,6->20:low_time:0,20->0:low_time:0'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b1fb77954b949bf0_6_12_7_16_17_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b1fb77954b949bf0 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=6,12,7,16,17 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=6,12,7,16,17 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=6,12,7,16,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->6:low_time:0","6->12:low_time:0","12->7:low_time:0","7->0:low_time:0"],"sequence":[6,12,7],"start_time":0.0},{"arc_option_sequence":["0->16:low_time:0","16->17:low_time:0","17->0:low_time:0"],"sequence":[16,17],"start_time":425.79128}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->6:low_time:0,6->12:low_time:0,12->7:low_time:0,7->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_5_4_16_18_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=09187873900ecefa --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=6,5,4,16,18 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=6,5,4,16,18 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=6,5,4,16,18 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->6:low_risk:2","6->5:low_risk:2","5->0:low_risk:2"],"sequence":[6,5],"start_time":0.0},{"arc_option_sequence":["0->4:low_risk:2","4->16:low_risk:2","16->18:low_risk:2","18->0:low_risk:2"],"sequence":[4,16,18],"start_time":241.140271}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->6:low_risk:2,6->5:low_risk:2,5->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_4_2_10_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_4_2_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_4_2_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_4_2_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_4_2_10_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_4_2_10_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_4_2_10_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_02_seed61102_12cfa32e4756fd37_3_9_4_2_10_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=12cfa32e4756fd37 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=3,9,4,2,10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=3,9,4,2,10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=3,9,4,2,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->3:low_time:0","3->9:low_time:0","9->0:low_risk:2"],"sequence":[3,9],"start_time":0.0},{"arc_option_sequence":["0->4:low_risk:2","4->2:low_risk:1","2->10:low_risk:2","10->0:low_risk:2"],"sequence":[4,2,10],"start_time":293.846584}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->3:low_time:0,3->9:low_time:0,9->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_02_seed61103_1625c1776efc58ed_12_7_2_1_10_4_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=1625c1776efc58ed --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,7,2,1,10,4 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,7,2,1,10,4 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,7,2,1,10,4 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_risk:2","12->7:low_risk:2","7->2:low_risk:2","2->1:low_time:0","1->0:low_time:0"],"sequence":[12,7,2,1],"start_time":2.442032},{"arc_option_sequence":["0->10:low_risk:2","10->4:low_risk:2","4->0:low_time:0"],"sequence":[10,4],"start_time":271.464168}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_risk:2,12->7:low_risk:2,7->2:low_risk:2,2->1:low_time:0,1->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_79c1e81dc9889c24_5_6_10_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_79c1e81dc9889c24_5_6_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_79c1e81dc9889c24_5_6_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_79c1e81dc9889c24_5_6_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_79c1e81dc9889c24_5_6_10_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_79c1e81dc9889c24_5_6_10_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_79c1e81dc9889c24_5_6_10_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_79c1e81dc9889c24_5_6_10_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=79c1e81dc9889c24 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,6,10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,6,10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,6,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->6:low_risk:2","6->10:low_energy:1","10->0:low_risk:2"],"sequence":[5,6,10],"start_time":10.218359}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->6:low_risk:2,6->10:low_energy:1,10->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_05_seed61414_d8b85dff55093cb1_4_6_20_3_7_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=d8b85dff55093cb1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4,6,20,3,7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4,6,20,3,7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,6,20,3,7 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_risk:2","4->6:low_time:0","6->20:low_risk:1","20->0:low_risk:2"],"sequence":[4,6,20],"start_time":4.4203},{"arc_option_sequence":["0->3:low_time:0","3->7:low_time:0","7->0:low_time:0"],"sequence":[3,7],"start_time":326.708516}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_risk:2,4->6:low_time:0,6->20:low_risk:1,20->0:low_risk:2'
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_b36178f6655c5f75_2_12_13_8_15_3_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b36178f6655c5f75 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=2,12,13,8,15,3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=2,12,13,8,15,3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=2,12,13,8,15,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->2:low_time:0","2->12:low_risk:1","12->13:low_risk:2","13->8:low_risk:2","8->15:low_time:0","15->3:low_risk:2","3->0:low_time:0"],"sequence":[2,12,13,8,15,3],"start_time":53.762891}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->2:low_time:0,2->12:low_risk:1,12->13:low_risk:2,13->8:low_risk:2,8->15:low_time:0,15->3:low_risk:2,3->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7079ec06a2d9eab3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,14,11,9,17,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,14,11,9,17,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,14,11,9,17,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->8:low_time:0","8->14:low_risk:2","14->11:low_time:0","11->9:low_time:0","9->0:low_time:0"],"sequence":[8,14,11,9],"start_time":0.0},{"arc_option_sequence":["0->17:low_time:0","17->5:low_risk:2","5->0:low_risk:2"],"sequence":[17,5],"start_time":381.433678}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_time:0,8->14:low_risk:2,14->11:low_time:0,11->9:low_time:0,9->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_mainline_baseline

Run task-20 baseline with context capture only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_worker_roi_gat_priority

Run explicit opt-in worker-ROI GAT target-priority worker. This cannot certify no-negative or set an official bound.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json --time-limit 200.000000 --results-csv BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_worker_roi_gat_priority/results.csv --log-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_worker_roi_gat_priority/logs --solution-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10_worker_roi_gat_priority/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b6507dfb6db81d64 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=16,11,12,10 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=16,11,12,10 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=16,11,12,10 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->16:low_risk:2","16->0:low_risk:2"],"sequence":[16],"start_time":0.0},{"arc_option_sequence":["0->11:low_time:0","11->12:low_time:0","12->10:low_time:0","10->0:low_risk:2"],"sequence":[11,12,10],"start_time":318.585773}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->16:low_risk:2,16->0:low_risk:2'
```

### audit_worker_roi_solver_ab_results

Read result CSVs after the solver commands finish.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_gat_worker_roi_solver_ab_results.py --runbook-summary BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/summary.json --output-dir BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/ab_audit --report BPC_future/results/gat_worker_roi_solver_ab_runbook_v31_train_delay_positive_20260615/ab_audit_zh.md
```

## 边界

- 该 runbook 不是生产开关；
- 5/10 命令不启用新的 hidden-negative worker；
- 20 worker 命令必须显式 opt-in；
- 所有命令都不启用 sharded Pulse certificate 或 official-bound shortcut；
- 未通过安全壳的 true-RC negative 只能延迟，不能永久丢弃。
