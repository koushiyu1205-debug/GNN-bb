# GAT Target-Priority Worker A/B Runbook

日期：2026-06-16

## 目的

生成下一轮 5/10 no-regression 与 candidate-scale ROI A/B 命令。GAT 仍只负责 embedding / trajectory impact 表达，kNN/OOD 只做安全壳；通过安全壳的 true-RC negative 可优先进入 worker target，不通过的负列进入 DELAY_QUEUE，不能永久丢弃，也不能参与 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_runbook = current
status = ready
worker_method = target_materialization_fixed
worker_batch_size = 8
input_candidate_count = 32
candidate_group_count = 4
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
  "worker_batch_size": 8,
  "worker_method": "target_materialization_fixed",
  "worker_stage_policy": "match_capture_pricing_kind: heuristic_before_heuristic_exact_before_exact"
}
```

## Candidate Runs

```json
[
  {
    "active_hash_before": "28d1a1350601d64c",
    "baseline_command_type": "task020_tranq20_ctxac056820_cg07_r00_tasks16_20_batch8_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r00_tasks16_20_batch8_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 8,
    "candidate_batch_target_sequences": [
      [
        20,
        16
      ],
      [
        17,
        16
      ],
      [
        5,
        1
      ],
      [
        15,
        17,
        7,
        3
      ],
      [
        15,
        17,
        11,
        3
      ],
      [
        6,
        7,
        3
      ],
      [
        8,
        7,
        3
      ],
      [
        17,
        7,
        3
      ]
    ],
    "candidate_context_complete": true,
    "candidate_names": [
      "tranq20_ctxac056820_cg07_r00_tasks16_20",
      "tranq20_ctxac056820_cg07_r01_tasks16_17",
      "tranq20_ctxac056820_cg07_r02_tasks1_5",
      "tranq20_ctxac056820_cg07_r03_tasks3_7_15_17",
      "tranq20_ctxac056820_cg07_r04_tasks3_11_15_17",
      "tranq20_ctxac056820_cg07_r05_tasks3_6_7",
      "tranq20_ctxac056820_cg07_r06_tasks3_7_8",
      "tranq20_ctxac056820_cg07_r07_tasks3_7_17"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ac056820151e9ad7",
    "forbidden_signature_hash": "c2f8c77dbd063d37",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "instance_family": "sector-wave",
    "name": "tranq20_ctxac056820_cg07_r00_tasks16_20_batch8",
    "pool_signature_hash": "3656986558341232",
    "pool_task_set_hash": "f8819dd1a2dda152",
    "region": "tranquillitatis_balmer_like_20km",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "source_file": "BPC_future/results/gat_target_mode_stage4_v10_20_shadow_capture_context_20260616/logs_sector_tranq20_01_shadow_capture/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_materialization_journey_count": 8,
    "target_priority_sequence": [
      20,
      16
    ],
    "target_sequence": [
      20,
      16,
      17,
      16,
      5,
      1,
      15,
      17,
      7,
      3,
      15,
      17,
      11,
      3,
      6,
      7,
      3,
      8,
      7,
      3,
      17,
      7,
      3
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
    "task_count": 20,
    "true_dual_hash": "af26c5fef326d91a",
    "worker_command_type": "task020_tranq20_ctxac056820_cg07_r00_tasks16_20_batch8_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r00_tasks16_20_batch8_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "28d1a1350601d64c",
    "baseline_command_type": "task020_tranq20_ctxac056820_cg07_r08_tasks3_6_11_batch8_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r08_tasks3_6_11_batch8_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 8,
    "candidate_batch_target_sequences": [
      [
        6,
        11,
        3
      ],
      [
        8,
        11,
        3
      ],
      [
        17,
        11,
        3
      ],
      [
        15,
        17,
        9
      ],
      [
        15,
        17,
        4
      ],
      [
        15,
        5,
        16,
        7,
        3
      ],
      [
        17,
        14,
        7,
        3
      ],
      [
        2,
        5,
        16
      ]
    ],
    "candidate_context_complete": true,
    "candidate_names": [
      "tranq20_ctxac056820_cg07_r08_tasks3_6_11",
      "tranq20_ctxac056820_cg07_r09_tasks3_8_11",
      "tranq20_ctxac056820_cg07_r10_tasks3_11_17",
      "tranq20_ctxac056820_cg07_r11_tasks9_15_17",
      "tranq20_ctxac056820_cg07_r12_tasks4_15_17",
      "tranq20_ctxac056820_cg07_r13_tasks3_5_7_15_16",
      "tranq20_ctxac056820_cg07_r14_tasks3_7_14_17",
      "tranq20_ctxac056820_cg07_r15_tasks2_5_16"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ac056820151e9ad7",
    "forbidden_signature_hash": "c2f8c77dbd063d37",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "instance_family": "sector-wave",
    "name": "tranq20_ctxac056820_cg07_r08_tasks3_6_11_batch8",
    "pool_signature_hash": "3656986558341232",
    "pool_task_set_hash": "f8819dd1a2dda152",
    "region": "tranquillitatis_balmer_like_20km",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "source_file": "BPC_future/results/gat_target_mode_stage4_v10_20_shadow_capture_context_20260616/logs_sector_tranq20_01_shadow_capture/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->6:low_risk:2",
      "6->0:low_risk:2",
      "0->11:low_time:0",
      "11->3:low_time:0",
      "3->0:low_risk:2"
    ],
    "target_materialization_journey_count": 8,
    "target_priority_sequence": [
      6,
      11,
      3
    ],
    "target_sequence": [
      6,
      11,
      3,
      8,
      11,
      3,
      17,
      11,
      3,
      15,
      17,
      9,
      15,
      17,
      4,
      15,
      5,
      16,
      7,
      3,
      17,
      14,
      7,
      3,
      2,
      5,
      16
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
          "0->11:low_time:0",
          "11->3:low_time:0",
          "3->0:low_risk:2"
        ],
        "sequence": [
          11,
          3
        ],
        "start_time": 342.116184
      }
    ],
    "task_count": 20,
    "true_dual_hash": "af26c5fef326d91a",
    "worker_command_type": "task020_tranq20_ctxac056820_cg07_r08_tasks3_6_11_batch8_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r08_tasks3_6_11_batch8_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "28d1a1350601d64c",
    "baseline_command_type": "task020_tranq20_ctxac056820_cg07_r16_tasks1_15_batch8_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r16_tasks1_15_batch8_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 8,
    "candidate_batch_target_sequences": [
      [
        15,
        1
      ],
      [
        20,
        14,
        7,
        3
      ],
      [
        15,
        2,
        16,
        7,
        3
      ],
      [
        15,
        2,
        5,
        12,
        13
      ],
      [
        15,
        2,
        5,
        10,
        12
      ],
      [
        17,
        10
      ],
      [
        15,
        17
      ],
      [
        15,
        17,
        3
      ]
    ],
    "candidate_context_complete": true,
    "candidate_names": [
      "tranq20_ctxac056820_cg07_r16_tasks1_15",
      "tranq20_ctxac056820_cg07_r17_tasks3_7_14_20",
      "tranq20_ctxac056820_cg07_r18_tasks2_3_7_15_16",
      "tranq20_ctxac056820_cg07_r19_tasks2_5_12_13_15",
      "tranq20_ctxac056820_cg07_r20_tasks2_5_10_12_15",
      "tranq20_ctxac056820_cg07_r21_tasks10_17",
      "tranq20_ctxac056820_cg07_r22_tasks15_17",
      "tranq20_ctxac056820_cg07_r23_tasks3_15_17"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ac056820151e9ad7",
    "forbidden_signature_hash": "c2f8c77dbd063d37",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "instance_family": "sector-wave",
    "name": "tranq20_ctxac056820_cg07_r16_tasks1_15_batch8",
    "pool_signature_hash": "3656986558341232",
    "pool_task_set_hash": "f8819dd1a2dda152",
    "region": "tranquillitatis_balmer_like_20km",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "source_file": "BPC_future/results/gat_target_mode_stage4_v10_20_shadow_capture_context_20260616/logs_sector_tranq20_01_shadow_capture/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->15:low_energy:1",
      "15->1:low_energy:1",
      "1->0:low_risk:2"
    ],
    "target_materialization_journey_count": 8,
    "target_priority_sequence": [
      15,
      1
    ],
    "target_sequence": [
      15,
      1,
      20,
      14,
      7,
      3,
      15,
      2,
      16,
      7,
      3,
      15,
      2,
      5,
      12,
      13,
      15,
      2,
      5,
      10,
      12,
      17,
      10,
      15,
      17,
      15,
      17,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->15:low_energy:1",
          "15->1:low_energy:1",
          "1->0:low_risk:2"
        ],
        "sequence": [
          15,
          1
        ],
        "start_time": 0.0
      }
    ],
    "task_count": 20,
    "true_dual_hash": "af26c5fef326d91a",
    "worker_command_type": "task020_tranq20_ctxac056820_cg07_r16_tasks1_15_batch8_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r16_tasks1_15_batch8_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "28d1a1350601d64c",
    "baseline_command_type": "task020_tranq20_ctxac056820_cg07_r24_tasks7_15_17_batch8_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r24_tasks7_15_17_batch8_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 8,
    "candidate_batch_target_sequences": [
      [
        15,
        17,
        7
      ],
      [
        15,
        17,
        11
      ],
      [
        15,
        17,
        19,
        7,
        3
      ],
      [
        15,
        2,
        16,
        10
      ],
      [
        15,
        5,
        16,
        10
      ],
      [
        15,
        20
      ],
      [
        18,
        16
      ],
      [
        20,
        14,
        3,
        11
      ]
    ],
    "candidate_context_complete": true,
    "candidate_names": [
      "tranq20_ctxac056820_cg07_r24_tasks7_15_17",
      "tranq20_ctxac056820_cg07_r25_tasks11_15_17",
      "tranq20_ctxac056820_cg07_r26_tasks3_7_15_17_19",
      "tranq20_ctxac056820_cg07_r27_tasks2_10_15_16",
      "tranq20_ctxac056820_cg07_r28_tasks5_10_15_16",
      "tranq20_ctxac056820_cg07_r29_tasks15_20",
      "tranq20_ctxac056820_cg07_r30_tasks16_18",
      "tranq20_ctxac056820_cg07_r31_tasks3_11_14_20"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ac056820151e9ad7",
    "forbidden_signature_hash": "c2f8c77dbd063d37",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "instance_family": "sector-wave",
    "name": "tranq20_ctxac056820_cg07_r24_tasks7_15_17_batch8",
    "pool_signature_hash": "3656986558341232",
    "pool_task_set_hash": "f8819dd1a2dda152",
    "region": "tranquillitatis_balmer_like_20km",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "source_file": "BPC_future/results/gat_target_mode_stage4_v10_20_shadow_capture_context_20260616/logs_sector_tranq20_01_shadow_capture/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->15:low_risk:2",
      "15->17:low_time:0",
      "17->0:low_risk:2",
      "0->7:low_risk:2",
      "7->0:low_time:0"
    ],
    "target_materialization_journey_count": 8,
    "target_priority_sequence": [
      15,
      17,
      7
    ],
    "target_sequence": [
      15,
      17,
      7,
      15,
      17,
      11,
      15,
      17,
      19,
      7,
      3,
      15,
      2,
      16,
      10,
      15,
      5,
      16,
      10,
      15,
      20,
      18,
      16,
      20,
      14,
      3,
      11
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->15:low_risk:2",
          "15->17:low_time:0",
          "17->0:low_risk:2"
        ],
        "sequence": [
          15,
          17
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->7:low_risk:2",
          "7->0:low_time:0"
        ],
        "sequence": [
          7
        ],
        "start_time": 269.239916
      }
    ],
    "task_count": 20,
    "true_dual_hash": "af26c5fef326d91a",
    "worker_command_type": "task020_tranq20_ctxac056820_cg07_r24_tasks7_15_17_batch8_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r24_tasks7_15_17_batch8_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_tranq20_ctxac056820_cg07_r00_tasks16_20_batch8_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r00_tasks16_20_batch8_mainline_baseline/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r00_tasks16_20_batch8_mainline_baseline/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r00_tasks16_20_batch8_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranq20_ctxac056820_cg07_r00_tasks16_20_batch8_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r00_tasks16_20_batch8_target_priority_worker/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r00_tasks16_20_batch8_target_priority_worker/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r00_tasks16_20_batch8_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ac056820151e9ad7 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,16 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,16 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,16,17,16,5,1,15,17,7,3,15,17,11,3,6,7,3,8,7,3,17,7,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys=[{"traces":[{"arc_option_sequence":["0->20:low_time:0","20->16:low_time:0","16->0:low_time:0"],"sequence":[20,16],"start_time":29.421768}]},{"traces":[{"arc_option_sequence":["0->17:low_energy:1","17->16:low_energy:1","16->0:low_energy:1"],"sequence":[17,16],"start_time":0.0}]},{"traces":[{"arc_option_sequence":["0->5:low_time:0","5->1:low_risk:2","1->0:low_energy:1"],"sequence":[5,1],"start_time":21.409885}]},{"traces":[{"arc_option_sequence":["0->15:low_risk:2","15->17:low_time:0","17->0:low_risk:2"],"sequence":[15,17],"start_time":0.0},{"arc_option_sequence":["0->7:low_time:0","7->3:low_risk:2","3->0:low_time:0"],"sequence":[7,3],"start_time":272.956467}]},{"traces":[{"arc_option_sequence":["0->15:low_risk:2","15->17:low_time:0","17->0:low_risk:2"],"sequence":[15,17],"start_time":0.0},{"arc_option_sequence":["0->11:low_time:0","11->3:low_time:0","3->0:low_risk:2"],"sequence":[11,3],"start_time":342.116184}]},{"traces":[{"arc_option_sequence":["0->6:low_risk:2","6->0:low_risk:2"],"sequence":[6],"start_time":0.0},{"arc_option_sequence":["0->7:low_time:0","7->3:low_risk:2","3->0:low_time:0"],"sequence":[7,3],"start_time":285.273183}]},{"traces":[{"arc_option_sequence":["0->8:low_time:0","8->0:low_risk:2"],"sequence":[8],"start_time":0.0},{"arc_option_sequence":["0->7:low_time:0","7->3:low_risk:2","3->0:low_time:0"],"sequence":[7,3],"start_time":272.956467}]},{"traces":[{"arc_option_sequence":["0->17:low_risk:2","17->0:low_risk:2"],"sequence":[17],"start_time":0.0},{"arc_option_sequence":["0->7:low_time:0","7->3:low_risk:2","3->0:low_time:0"],"sequence":[7,3],"start_time":272.956467}]}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->16:low_time:0,16->0:low_time:0'
```

### task020_tranq20_ctxac056820_cg07_r08_tasks3_6_11_batch8_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r08_tasks3_6_11_batch8_mainline_baseline/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r08_tasks3_6_11_batch8_mainline_baseline/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r08_tasks3_6_11_batch8_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranq20_ctxac056820_cg07_r08_tasks3_6_11_batch8_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r08_tasks3_6_11_batch8_target_priority_worker/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r08_tasks3_6_11_batch8_target_priority_worker/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r08_tasks3_6_11_batch8_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ac056820151e9ad7 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=6,11,3 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=6,11,3 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=6,11,3,8,11,3,17,11,3,15,17,9,15,17,4,15,5,16,7,3,17,14,7,3,2,5,16 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys=[{"traces":[{"arc_option_sequence":["0->6:low_risk:2","6->0:low_risk:2"],"sequence":[6],"start_time":0.0},{"arc_option_sequence":["0->11:low_time:0","11->3:low_time:0","3->0:low_risk:2"],"sequence":[11,3],"start_time":342.116184}]},{"traces":[{"arc_option_sequence":["0->8:low_time:0","8->0:low_risk:2"],"sequence":[8],"start_time":0.0},{"arc_option_sequence":["0->11:low_time:0","11->3:low_time:0","3->0:low_risk:2"],"sequence":[11,3],"start_time":342.116184}]},{"traces":[{"arc_option_sequence":["0->17:low_risk:2","17->0:low_risk:2"],"sequence":[17],"start_time":0.0},{"arc_option_sequence":["0->11:low_time:0","11->3:low_time:0","3->0:low_risk:2"],"sequence":[11,3],"start_time":342.116184}]},{"traces":[{"arc_option_sequence":["0->15:low_risk:2","15->17:low_time:0","17->0:low_risk:2"],"sequence":[15,17],"start_time":0.0},{"arc_option_sequence":["0->9:low_risk:2","9->0:low_energy:1"],"sequence":[9],"start_time":269.239916}]},{"traces":[{"arc_option_sequence":["0->15:low_risk:2","15->17:low_time:0","17->0:low_risk:2"],"sequence":[15,17],"start_time":0.0},{"arc_option_sequence":["0->4:low_risk:2","4->0:low_risk:2"],"sequence":[4],"start_time":269.239916}]},{"traces":[{"arc_option_sequence":["0->15:low_risk:2","15->5:low_risk:2","5->16:low_risk:2","16->0:low_risk:2"],"sequence":[15,5,16],"start_time":0.0},{"arc_option_sequence":["0->7:low_time:0","7->3:low_risk:2","3->0:low_time:0"],"sequence":[7,3],"start_time":297.783925}]},{"traces":[{"arc_option_sequence":["0->17:low_risk:2","17->14:low_risk:2","14->0:low_time:0"],"sequence":[17,14],"start_time":0.0},{"arc_option_sequence":["0->7:low_time:0","7->3:low_risk:2","3->0:low_time:0"],"sequence":[7,3],"start_time":298.171332}]},{"traces":[{"arc_option_sequence":["0->2:low_risk:2","2->5:low_risk:2","5->16:low_time:0","16->0:low_time:0"],"sequence":[2,5,16],"start_time":0.0}]}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->6:low_risk:2,6->0:low_risk:2,0->11:low_time:0,11->3:low_time:0,3->0:low_risk:2'
```

### task020_tranq20_ctxac056820_cg07_r16_tasks1_15_batch8_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r16_tasks1_15_batch8_mainline_baseline/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r16_tasks1_15_batch8_mainline_baseline/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r16_tasks1_15_batch8_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranq20_ctxac056820_cg07_r16_tasks1_15_batch8_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r16_tasks1_15_batch8_target_priority_worker/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r16_tasks1_15_batch8_target_priority_worker/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r16_tasks1_15_batch8_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ac056820151e9ad7 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=15,1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=15,1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=15,1,20,14,7,3,15,2,16,7,3,15,2,5,12,13,15,2,5,10,12,17,10,15,17,15,17,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys=[{"traces":[{"arc_option_sequence":["0->15:low_energy:1","15->1:low_energy:1","1->0:low_risk:2"],"sequence":[15,1],"start_time":0.0}]},{"traces":[{"arc_option_sequence":["0->20:low_energy:1","20->14:low_time:0","14->0:low_time:0"],"sequence":[20,14],"start_time":29.010789},{"arc_option_sequence":["0->7:low_energy:1","7->3:low_time:0","3->0:low_time:0"],"sequence":[7,3],"start_time":312.732475}]},{"traces":[{"arc_option_sequence":["0->15:low_risk:2","15->2:low_risk:2","2->16:low_risk:2","16->0:low_risk:2"],"sequence":[15,2,16],"start_time":0.0},{"arc_option_sequence":["0->7:low_time:0","7->3:low_risk:2","3->0:low_time:0"],"sequence":[7,3],"start_time":314.629964}]},{"traces":[{"arc_option_sequence":["0->15:low_energy:1","15->2:low_risk:2","2->5:low_time:0","5->0:low_risk:2"],"sequence":[15,2,5],"start_time":0.0},{"arc_option_sequence":["0->12:low_time:0","12->13:low_risk:1","13->0:low_risk:2"],"sequence":[12,13],"start_time":216.107005}]},{"traces":[{"arc_option_sequence":["0->15:low_risk:2","15->2:low_time:0","2->5:low_time:0","5->0:low_time:0"],"sequence":[15,2,5],"start_time":0.0},{"arc_option_sequence":["0->10:low_time:0","10->12:low_time:0","12->0:low_risk:2"],"sequence":[10,12],"start_time":207.578758}]},{"traces":[{"arc_option_sequence":["0->17:low_time:0","17->0:low_risk:2"],"sequence":[17],"start_time":0.0},{"arc_option_sequence":["0->10:low_energy:1","10->0:low_risk:2"],"sequence":[10],"start_time":233.396749}]},{"traces":[{"arc_option_sequence":["0->15:low_risk:2","15->17:low_time:0","17->0:low_risk:2"],"sequence":[15,17],"start_time":0.0}]},{"traces":[{"arc_option_sequence":["0->15:low_risk:2","15->17:low_time:0","17->0:low_risk:2"],"sequence":[15,17],"start_time":0.0},{"arc_option_sequence":["0->3:low_risk:2","3->0:low_risk:2"],"sequence":[3],"start_time":309.124629}]}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->15:low_energy:1,15->1:low_energy:1,1->0:low_risk:2'
```

### task020_tranq20_ctxac056820_cg07_r24_tasks7_15_17_batch8_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r24_tasks7_15_17_batch8_mainline_baseline/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r24_tasks7_15_17_batch8_mainline_baseline/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r24_tasks7_15_17_batch8_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranq20_ctxac056820_cg07_r24_tasks7_15_17_batch8_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r24_tasks7_15_17_batch8_target_priority_worker/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r24_tasks7_15_17_batch8_target_priority_worker/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/task020_tranq20_ctxac056820_cg07_r24_tasks7_15_17_batch8_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ac056820151e9ad7 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=15,17,7 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=15,17,7 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=15,17,7,15,17,11,15,17,19,7,3,15,2,16,10,15,5,16,10,15,20,18,16,20,14,3,11 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys=[{"traces":[{"arc_option_sequence":["0->15:low_risk:2","15->17:low_time:0","17->0:low_risk:2"],"sequence":[15,17],"start_time":0.0},{"arc_option_sequence":["0->7:low_risk:2","7->0:low_time:0"],"sequence":[7],"start_time":269.239916}]},{"traces":[{"arc_option_sequence":["0->15:low_risk:2","15->17:low_time:0","17->0:low_risk:2"],"sequence":[15,17],"start_time":0.0},{"arc_option_sequence":["0->11:low_risk:2","11->0:low_risk:2"],"sequence":[11],"start_time":336.514473}]},{"traces":[{"arc_option_sequence":["0->15:low_risk:2","15->17:low_time:0","17->19:low_risk:2","19->0:low_risk:2"],"sequence":[15,17,19],"start_time":0.0},{"arc_option_sequence":["0->7:low_time:0","7->3:low_risk:2","3->0:low_time:0"],"sequence":[7,3],"start_time":288.94697}]},{"traces":[{"arc_option_sequence":["0->15:low_risk:2","15->2:low_risk:2","2->0:low_risk:2"],"sequence":[15,2],"start_time":0.0},{"arc_option_sequence":["0->16:low_risk:2","16->10:low_risk:1","10->0:low_risk:2"],"sequence":[16,10],"start_time":160.488046}]},{"traces":[{"arc_option_sequence":["0->15:low_risk:2","15->5:low_risk:2","5->0:low_risk:2"],"sequence":[15,5],"start_time":0.0},{"arc_option_sequence":["0->16:low_risk:2","16->10:low_risk:1","10->0:low_risk:2"],"sequence":[16,10],"start_time":154.183438}]},{"traces":[{"arc_option_sequence":["0->15:low_risk:2","15->20:low_time:0","20->0:low_time:0"],"sequence":[15,20],"start_time":0.0}]},{"traces":[{"arc_option_sequence":["0->18:low_time:0","18->16:low_risk:2","16->0:low_time:0"],"sequence":[18,16],"start_time":0.0}]},{"traces":[{"arc_option_sequence":["0->20:low_energy:1","20->14:low_time:0","14->0:low_time:0"],"sequence":[20,14],"start_time":29.010789},{"arc_option_sequence":["0->3:low_risk:2","3->11:low_time:0","11->0:low_time:0"],"sequence":[3,11],"start_time":312.732475}]}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->15:low_risk:2,15->17:low_time:0,17->0:low_risk:2,0->7:low_risk:2,7->0:low_time:0'
```

## 边界

- 5/10 命令不关闭主线 GAT/learning，也不启用新 worker；
- candidate baseline/worker 命令也不关闭主线 GAT/learning，避免候选捕获上下文无法复现；
- candidate baseline/worker 命令开启 counterfactual replay capture；如果旧 target context 没到，仍保留实际到达的 context 供下一轮候选抽取；
- candidate worker 命令是显式 opt-in，默认只做 same-context target materialization，不运行 Pulse 搜索 / harvest / archive / bound pruning；
- 30/50/100 尚无专用 config 时，runbook 会显式记录 `scale_config_fallback_from_task20=true`，并通过命令行传入目标 logical graph；
- 固定 worker 的 current-probe 开关只作为 expected context 触发器；target materialization 会在任何 Pulse 搜索前返回结果；
- `worker_batch_size > 1` 时，只会合并同一 instance + expected context 的候选，并通过 `target_materialization_journeys` 批量物化；
- candidate worker 候选必须带完整 context / dual / cuts / branch / pool hash；
- 所有命令都不启用 sharded Pulse certificate 或 official lower-bound effect；
- 含 `->` 的 arc-option 配置通过 `shlex.join` 自动引用，不能手工去掉引号；
- 该 runbook 不是生产开关，跑完后仍需看 5/10 no-regression 和 20-task ROI。
