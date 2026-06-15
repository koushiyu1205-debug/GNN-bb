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
    "active_hash_before": "d24e375c9cf9eac0",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_577b70605147a3cd_15_9_10_1_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "577b70605147a3cd",
    "forbidden_signature_hash": "fe938744d65aeab4",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_577b70605147a3cd_15_9_10_1",
    "pool_signature_hash": "1fd7a3f61873b75c",
    "pool_task_set_hash": "dc9ac44f08fef093",
    "target_arc_option_sequence": [
      "0->15:low_time:0",
      "15->0:low_time:0"
    ],
    "target_priority_sequence": [
      15
    ],
    "target_sequence": [
      15,
      9,
      10,
      1
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->15:low_time:0",
          "15->0:low_time:0"
        ],
        "sequence": [
          15
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->9:low_time:0",
          "9->10:low_energy:1",
          "10->1:low_risk:2",
          "1->0:low_time:0"
        ],
        "sequence": [
          9,
          10,
          1
        ],
        "start_time": 174.62674
      }
    ],
    "true_dual_hash": "c251b446053a2f98",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_577b70605147a3cd_15_9_10_1_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "5484cfcba13e66bf",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_mainline_baseline/results.csv",
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
    "target_arc_option_sequence": [
      "0->13:low_time:0",
      "13->0:low_time:0"
    ],
    "target_priority_sequence": [
      13
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
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "cc42ac61a4bb4b25",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_mainline_baseline/results.csv",
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
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "5894e951a05a1faa",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_mainline_baseline/results.csv",
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
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "28d1a1350601d64c",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_20_16_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ac056820151e9ad7",
    "forbidden_signature_hash": "c2f8c77dbd063d37",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_20_16",
    "pool_signature_hash": "3656986558341232",
    "pool_task_set_hash": "f8819dd1a2dda152",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_priority_sequence": [
      20,
      16
    ],
    "target_sequence": [
      20,
      16
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->16:low_time:0",
          "16->0:low_time:0"
        ],
        "sequence": [
          20,
          16
        ],
        "start_time": 29.421768
      }
    ],
    "true_dual_hash": "af26c5fef326d91a",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_20_16_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "4a4a5e04b94c74f8",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_mainline_baseline/results.csv",
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
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "a71d3ab5cf5a282a",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_16_19_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b6d808ebac2a6dd8",
    "forbidden_signature_hash": "6b0ab3de1090984f",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_16_19",
    "pool_signature_hash": "2934629ac06005ef",
    "pool_task_set_hash": "978c7f39b6d714fe",
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->19:low_risk:2",
      "19->0:low_time:0"
    ],
    "target_priority_sequence": [
      16,
      19
    ],
    "target_sequence": [
      16,
      19
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->16:low_time:0",
          "16->19:low_risk:2",
          "19->0:low_time:0"
        ],
        "sequence": [
          16,
          19
        ],
        "start_time": 0.0
      }
    ],
    "true_dual_hash": "0249cbb92e9ec2a0",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_16_19_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "2424a01a18ad7363",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b095fbae18116443_20_8_3_18_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b095fbae18116443",
    "forbidden_signature_hash": "995793c429970b9d",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b095fbae18116443_20_8_3_18",
    "pool_signature_hash": "1f7318ce6eb42254",
    "pool_task_set_hash": "8d81b083be1af31b",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->8:low_risk:2",
      "8->3:low_risk:2",
      "3->18:low_risk:2",
      "18->0:low_time:0"
    ],
    "target_priority_sequence": [
      20,
      8,
      3,
      18
    ],
    "target_sequence": [
      20,
      8,
      3,
      18
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->8:low_risk:2",
          "8->3:low_risk:2",
          "3->18:low_risk:2",
          "18->0:low_time:0"
        ],
        "sequence": [
          20,
          8,
          3,
          18
        ],
        "start_time": 64.219577
      }
    ],
    "true_dual_hash": "3c15f908501c7b46",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b095fbae18116443_20_8_3_18_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "ef899cce1ce614bd",
    "baseline_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_a4f29d238b2963df_2_20_8_3_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_context_complete": true,
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "a4f29d238b2963df",
    "forbidden_signature_hash": "6d5480be86280cb9",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_a4f29d238b2963df_2_20_8_3",
    "pool_signature_hash": "1141236184a96200",
    "pool_task_set_hash": "9b9520ed0f83f0f7",
    "target_arc_option_sequence": [
      "0->2:low_time:0",
      "2->0:low_risk:1"
    ],
    "target_priority_sequence": [
      2
    ],
    "target_sequence": [
      2,
      20,
      8,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->2:low_time:0",
          "2->0:low_risk:1"
        ],
        "sequence": [
          2
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->8:low_energy:1",
          "8->3:low_risk:2",
          "3->0:low_risk:2"
        ],
        "sequence": [
          20,
          8,
          3
        ],
        "start_time": 130.552412
      }
    ],
    "true_dual_hash": "83d76e191c869bca",
    "worker_csv": "BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_a4f29d238b2963df_2_20_8_3_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 4 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_577b70605147a3cd_15_9_10_1_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_577b70605147a3cd_15_9_10_1_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_577b70605147a3cd_15_9_10_1_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_577b70605147a3cd_15_9_10_1_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_577b70605147a3cd_15_9_10_1_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_577b70605147a3cd_15_9_10_1_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_577b70605147a3cd_15_9_10_1_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_577b70605147a3cd_15_9_10_1_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=577b70605147a3cd --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=15 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=15 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=15,9,10,1 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->15:low_time:0","15->0:low_time:0"],"sequence":[15],"start_time":0.0},{"arc_option_sequence":["0->9:low_time:0","9->10:low_energy:1","10->1:low_risk:2","1->0:low_time:0"],"sequence":[9,10,1],"start_time":174.62674}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->15:low_time:0,15->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b9550ffc9a42531a --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=13 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=13 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=13,20,7 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->13:low_time:0","13->0:low_time:0"],"sequence":[13],"start_time":0.0},{"arc_option_sequence":["0->20:low_time:0","20->7:low_risk:2","7->0:low_time:0"],"sequence":[20,7],"start_time":136.776061}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->13:low_time:0,13->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=476979944ba39894 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,2 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,2 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,2 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_risk:2","12->2:low_risk:2","2->0:low_risk:2"],"sequence":[12,2],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_risk:2,12->2:low_risk:2,2->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=95e9afaf1ecbdc5e --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=16,13,5 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=16,13,5 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=16,13,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->16:low_time:0","16->13:low_time:0","13->5:low_risk:2","5->0:low_risk:2"],"sequence":[16,13,5],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->16:low_time:0,16->13:low_time:0,13->5:low_risk:2,5->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_20_16_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_20_16_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_20_16_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_20_16_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_20_16_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_20_16_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_20_16_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_20_16_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ac056820151e9ad7 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,16 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,16 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,16 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->16:low_time:0","16->0:low_time:0"],"sequence":[20,16],"start_time":29.421768}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->16:low_time:0,16->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=4e481a6307fca228 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=11,4,7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=11,4,7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=11,4,7 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->11:low_time:0","11->4:low_energy:1","4->7:low_energy:1","7->0:low_energy:1"],"sequence":[11,4,7],"start_time":1.454325}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->11:low_time:0,11->4:low_energy:1,4->7:low_energy:1,7->0:low_energy:1'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_16_19_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_16_19_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_16_19_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_16_19_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_16_19_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_16_19_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_16_19_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_16_19_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b6d808ebac2a6dd8 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=16,19 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=16,19 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=16,19 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->16:low_time:0","16->19:low_risk:2","19->0:low_time:0"],"sequence":[16,19],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->16:low_time:0,16->19:low_risk:2,19->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b095fbae18116443_20_8_3_18_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b095fbae18116443_20_8_3_18_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b095fbae18116443_20_8_3_18_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b095fbae18116443_20_8_3_18_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b095fbae18116443_20_8_3_18_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b095fbae18116443_20_8_3_18_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b095fbae18116443_20_8_3_18_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b095fbae18116443_20_8_3_18_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b095fbae18116443 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,8,3,18 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,8,3,18 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,8,3,18 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->8:low_risk:2","8->3:low_risk:2","3->18:low_risk:2","18->0:low_time:0"],"sequence":[20,8,3,18],"start_time":64.219577}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->8:low_risk:2,8->3:low_risk:2,3->18:low_risk:2,18->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_a4f29d238b2963df_2_20_8_3_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_a4f29d238b2963df_2_20_8_3_mainline_baseline/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_a4f29d238b2963df_2_20_8_3_mainline_baseline/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_a4f29d238b2963df_2_20_8_3_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_a4f29d238b2963df_2_20_8_3_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_a4f29d238b2963df_2_20_8_3_target_priority_worker/results.csv --log-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_a4f29d238b2963df_2_20_8_3_target_priority_worker/logs --solution-dir BPC_future/results/gat_worker_roi_label_collection_task20_v25_parallel4_20260615/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_a4f29d238b2963df_2_20_8_3_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=a4f29d238b2963df --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=2 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=2 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=2,20,8,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->2:low_time:0","2->0:low_risk:1"],"sequence":[2],"start_time":0.0},{"arc_option_sequence":["0->20:low_time:0","20->8:low_energy:1","8->3:low_risk:2","3->0:low_risk:2"],"sequence":[20,8,3],"start_time":130.552412}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->2:low_time:0,2->0:low_risk:1'
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
