# GAT Target-Priority Worker A/B Runbook

日期：2026-06-23

## 目的

生成下一轮 5/10 no-regression 与 candidate-scale ROI A/B 命令。GAT 仍只负责 embedding / trajectory impact 表达，kNN/OOD 只做安全壳；通过安全壳的 true-RC negative 可优先进入 worker target，不通过的负列进入 DELAY_QUEUE，不能永久丢弃，也不能参与 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_runbook = current
status = ready
worker_method = target_materialization_fixed
worker_batch_size = 4
input_candidate_count = 8
candidate_group_count = 3
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
    "active_hash_before": "c3b07098b37ddf29",
    "baseline_command_type": "task020_tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 2,
    "candidate_batch_target_sequences": [
      [
        8,
        2,
        3,
        18
      ],
      [
        8,
        3,
        2
      ]
    ],
    "candidate_context_complete": true,
    "candidate_names": [
      "tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18",
      "tranq20_ctxdd1c3812_cg01_r06_tasks2_3_8"
    ],
    "capture_pricing_kind": "heuristic",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "dd1c3812ce457e30",
    "forbidden_signature_hash": "9d3354522d3b4ca2",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "instance_family": "sector-wave",
    "name": "tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2",
    "pool_signature_hash": "0131b8621a209823",
    "pool_task_set_hash": "dd89d0007a00b23d",
    "region": "tranquillitatis_balmer_like_20km",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "source_file": "BPC_future/results/gat_stage4_v154_actual_probe_20260623/task020_v154_online_shadow_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->2:low_time:0",
      "2->3:low_time:0",
      "3->18:low_energy:1",
      "18->0:low_time:0"
    ],
    "target_materialization_journey_count": 2,
    "target_priority_sequence": [
      8,
      2,
      3,
      18
    ],
    "target_sequence": [
      8,
      2,
      3,
      18,
      8,
      3,
      2
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->8:low_time:0",
          "8->2:low_time:0",
          "2->3:low_time:0",
          "3->18:low_energy:1",
          "18->0:low_time:0"
        ],
        "sequence": [
          8,
          2,
          3,
          18
        ],
        "start_time": 100.038929
      }
    ],
    "task_count": 20,
    "true_dual_hash": "0f1e770512cdb0c1",
    "worker_command_type": "task020_tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "2424a01a18ad7363",
    "baseline_command_type": "task020_tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 4,
    "candidate_batch_target_sequences": [
      [
        20,
        8,
        3,
        18
      ],
      [
        20,
        8,
        6,
        18
      ],
      [
        20,
        8,
        3
      ],
      [
        20,
        8,
        6
      ]
    ],
    "candidate_context_complete": true,
    "candidate_names": [
      "tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20",
      "tranq20_ctxb095fbae_cg03_r01_tasks6_8_18_20",
      "tranq20_ctxb095fbae_cg03_r02_tasks3_8_20",
      "tranq20_ctxb095fbae_cg03_r03_tasks6_8_20"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b095fbae18116443",
    "forbidden_signature_hash": "995793c429970b9d",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "instance_family": "sector-wave",
    "name": "tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4",
    "pool_signature_hash": "1f7318ce6eb42254",
    "pool_task_set_hash": "8d81b083be1af31b",
    "region": "tranquillitatis_balmer_like_20km",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "source_file": "BPC_future/results/gat_stage4_v154_actual_probe_20260623/task020_v154_online_shadow_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->8:low_risk:2",
      "8->3:low_risk:2",
      "3->18:low_risk:2",
      "18->0:low_time:0"
    ],
    "target_materialization_journey_count": 4,
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
      18,
      20,
      8,
      6,
      18,
      20,
      8,
      3,
      20,
      8,
      6
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
    "task_count": 20,
    "true_dual_hash": "3c15f908501c7b46",
    "worker_command_type": "task020_tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "f3c4a439371e8dbb",
    "baseline_command_type": "task020_tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 2,
    "candidate_batch_target_sequences": [
      [
        1,
        11
      ],
      [
        11,
        1
      ]
    ],
    "candidate_context_complete": true,
    "candidate_names": [
      "tranq20_ctxea2f1344_cg04_r00_tasks1_11",
      "tranq20_ctxea2f1344_cg04_r01_tasks1_11"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ea2f1344458c548f",
    "forbidden_signature_hash": "b1461d78eba5da01",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
    "instance_family": "sector-wave",
    "name": "tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2",
    "pool_signature_hash": "0951222227202144",
    "pool_task_set_hash": "9648365788fb0dca",
    "region": "tranquillitatis_balmer_like_20km",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "source_file": "BPC_future/results/gat_stage4_v154_actual_probe_20260623/task020_v154_online_shadow_capture/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->1:low_time:0",
      "1->11:low_risk:2",
      "11->0:low_time:0"
    ],
    "target_materialization_journey_count": 2,
    "target_priority_sequence": [
      1,
      11
    ],
    "target_sequence": [
      1,
      11,
      11,
      1
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->1:low_time:0",
          "1->11:low_risk:2",
          "11->0:low_time:0"
        ],
        "sequence": [
          1,
          11
        ],
        "start_time": 0.0
      }
    ],
    "task_count": 20,
    "true_dual_hash": "0c02b974fe060f9a",
    "worker_command_type": "task020_tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 2 --results-csv BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 2 --results-csv BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2_mainline_baseline/results.csv --log-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2_mainline_baseline/logs --solution-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2_target_priority_worker/results.csv --log-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2_target_priority_worker/logs --solution-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxdd1c3812_cg01_r02_tasks2_3_8_18_batch2_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=False --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=dd1c3812ce457e30 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=8,2,3,18 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=8,2,3,18 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=8,2,3,18,8,3,2 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys=[{"traces":[{"arc_option_sequence":["0->8:low_time:0","8->2:low_time:0","2->3:low_time:0","3->18:low_energy:1","18->0:low_time:0"],"sequence":[8,2,3,18],"start_time":100.038929}]},{"traces":[{"arc_option_sequence":["0->8:low_risk:2","8->3:low_risk:2","3->2:low_risk:2","2->0:low_risk:2"],"sequence":[8,3,2],"start_time":90.147202}]}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->8:low_time:0,8->2:low_time:0,2->3:low_time:0,3->18:low_energy:1,18->0:low_time:0'
```

### task020_tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4_mainline_baseline/results.csv --log-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4_mainline_baseline/logs --solution-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4_target_priority_worker/results.csv --log-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4_target_priority_worker/logs --solution-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxb095fbae_cg03_r00_tasks3_8_18_20_batch4_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b095fbae18116443 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,8,3,18 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,8,3,18 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,8,3,18,20,8,6,18,20,8,3,20,8,6 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys=[{"traces":[{"arc_option_sequence":["0->20:low_time:0","20->8:low_risk:2","8->3:low_risk:2","3->18:low_risk:2","18->0:low_time:0"],"sequence":[20,8,3,18],"start_time":64.219577}]},{"traces":[{"arc_option_sequence":["0->20:low_time:0","20->8:low_energy:1","8->6:low_time:0","6->18:low_risk:2","18->0:low_time:0"],"sequence":[20,8,6,18],"start_time":64.219577}]},{"traces":[{"arc_option_sequence":["0->20:low_time:0","20->8:low_energy:1","8->3:low_time:0","3->0:low_time:0"],"sequence":[20,8,3],"start_time":64.219577}]},{"traces":[{"arc_option_sequence":["0->20:low_time:0","20->8:low_energy:1","8->6:low_time:0","6->0:low_time:0"],"sequence":[20,8,6],"start_time":64.219577}]}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->8:low_risk:2,8->3:low_risk:2,3->18:low_risk:2,18->0:low_time:0'
```

### task020_tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2_mainline_baseline/results.csv --log-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2_mainline_baseline/logs --solution-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2_target_priority_worker/results.csv --log-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2_target_priority_worker/logs --solution-dir BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/task020_tranq20_ctxea2f1344_cg04_r00_tasks1_11_batch2_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ea2f1344458c548f --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=1,11 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=1,11 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=1,11,11,1 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_journeys=[{"traces":[{"arc_option_sequence":["0->1:low_time:0","1->11:low_risk:2","11->0:low_time:0"],"sequence":[1,11],"start_time":0.0}]},{"traces":[{"arc_option_sequence":["0->11:low_time:0","11->1:low_risk:2","1->0:low_time:0"],"sequence":[11,1],"start_time":2.23819}]}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->1:low_time:0,1->11:low_risk:2,11->0:low_time:0'
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
