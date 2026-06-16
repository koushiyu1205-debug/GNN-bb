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
input_candidate_count = 1
candidate_group_count = 1
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
    "active_hash_before": "3ee7a90ac6308fe9",
    "baseline_command_type": "task020_tranq20_ctx7b430465_cg09_r25_tasks1_9_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task020_tranq20_ctx7b430465_cg09_r25_tasks1_9_mainline_baseline/results.csv",
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "tranq20_ctx7b430465_cg09_r25_tasks1_9"
    ],
    "capture_pricing_kind": "exact",
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7b430465c7ae76b3",
    "forbidden_signature_hash": "9442d521be840545",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "instance_family": "sector-wave",
    "name": "tranq20_ctx7b430465_cg09_r25_tasks1_9",
    "pool_signature_hash": "3b394c6efaa8c39f",
    "pool_task_set_hash": "b9009b10793c0039",
    "region": "tranquillitatis_balmer_like_20km",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "source_file": "BPC_future/results/gat_target_priority_worker_ab_active_replacement_active_only_20260616/task020_tranq20_ctxac056820_cg07_r29_tasks15_20_target_priority_worker/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->1:low_risk:2",
      "1->0:low_risk:2",
      "0->9:low_risk:2",
      "9->0:low_energy:1"
    ],
    "target_priority_sequence": [
      1,
      9
    ],
    "target_sequence": [
      1,
      9
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->1:low_risk:2",
          "1->0:low_risk:2"
        ],
        "sequence": [
          1
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->9:low_risk:2",
          "9->0:low_energy:1"
        ],
        "sequence": [
          9
        ],
        "start_time": 287.981087
      }
    ],
    "task_count": 20,
    "true_dual_hash": "2d5b9d2e524fe6e0",
    "worker_command_type": "task020_tranq20_ctx7b430465_cg09_r25_tasks1_9_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task020_tranq20_ctx7b430465_cg09_r25_tasks1_9_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_tranq20_ctx7b430465_cg09_r25_tasks1_9_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task020_tranq20_ctx7b430465_cg09_r25_tasks1_9_mainline_baseline/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task020_tranq20_ctx7b430465_cg09_r25_tasks1_9_mainline_baseline/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task020_tranq20_ctx7b430465_cg09_r25_tasks1_9_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranq20_ctx7b430465_cg09_r25_tasks1_9_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task020_tranq20_ctx7b430465_cg09_r25_tasks1_9_target_priority_worker/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task020_tranq20_ctx7b430465_cg09_r25_tasks1_9_target_priority_worker/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_active_replacement_stage2_after_15_20_20260616/task020_tranq20_ctx7b430465_cg09_r25_tasks1_9_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7b430465c7ae76b3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=1,9 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=1,9 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=1,9 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->1:low_risk:2","1->0:low_risk:2"],"sequence":[1],"start_time":0.0},{"arc_option_sequence":["0->9:low_risk:2","9->0:low_energy:1"],"sequence":[9],"start_time":287.981087}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->1:low_risk:2,1->0:low_risk:2,0->9:low_risk:2,9->0:low_energy:1'
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
