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
all_checks_pass = true
```

## Candidate Policy

```json
{
  "certificate_effect": false,
  "gat_role": "embedding_and_trajectory_impact_expression",
  "knn_ood_role": "safety_shell",
  "negative_discard_allowed": false,
  "safe_negative_action": "HIGH_PRIORITY",
  "unsafe_negative_action": "DELAY_QUEUE"
}
```

## Candidate Runs

```json
[
  {
    "baseline_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_no_learning_baseline/results.csv",
    "expected_context_hash": "c488c428ee5822de",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
    "name": "apollo20_sector_wave_c488c428_target_20_17_16",
    "target_arc_option_sequence": [
      "0->20:low_risk:2",
      "20->17:low_risk:2",
      "17->16:low_risk:2",
      "16->0:low_risk:2"
    ],
    "target_sequence": [
      20,
      17,
      16
    ],
    "worker_csv": "BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_target_priority_worker/results.csv"
  }
]
```

## 实跑结果

### 5/10 No-regression

本轮实际执行了 runbook 中的 5/10 主线 no-regression 命令。这里没有关闭主线
GAT/learning，也没有启用新的 GAT/kNN/OOD worker gate。

| scale | instance | status | primal | dual | gap | wall |
|---:|---|---|---:|---:|---:|---:|
| 5 | Apollo sector-wave #1 | OPTIMAL | 284.084294 | 284.084294 | 0.0 | 2.276397s |
| 5 | Tranq sector-wave #1 | OPTIMAL | 179.982081 | 179.982081 | 0.0 | 2.173830s |
| 10 | Apollo sector-wave #1 | OPTIMAL | 456.756326 | 456.756326 | 0.0 | 5.153385s |
| 10 | Tranq sector-wave #1 | OPTIMAL | 330.363821 | 330.363821 | 0.0 | 3.551559s |

结论：主线 GAT 没有被放弃，也没有因为新 gate/worker 发生默认路径回退；5/10 仍然保持秒级到数秒级
`OPTIMAL`。

### 20-task ROI A/B

本轮继续在 Apollo20 sector-wave #1 上复跑 target-priority A/B。两组都没有 official lower bound，
也没有 certificate effect。

| profile | status | primal | dual_bound | rmp_solves | pricing_calls | exact_pricing_calls | columns | generated_sequences | evaluated_timed_trips |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| no-learning baseline | TIME_LIMIT | 740.122399 | None | 12 | 16 | 6 | 257 | 71338 | 152186 |
| target-priority worker | TIME_LIMIT | 739.158736 | None | 13 | 16 | 7 | 259 | 73071 | 153882 |

结论：这个 GAT/kNN/OOD residual-family target 仍有正向 ROI 信号，primal 改善
`0.963663`，列数增加 `2`。但它还没有解决 exact-proof tail：`dual_bound=None`，仍是
`TIME_LIMIT`，因此不能默认启用，也不能进入证书路径。

本轮 `run_bpc_future.py` 只写出 `results.csv`，没有生成 JSONL 事件日志；worker 事件级证据仍沿用同配置上一轮
stdout 记录：`sharded_pulse_hidden_negative_worker best_rc=-1.85699125 journeys=1`。后续若要做更细
ROI 分析，应改用会保留 JSONL 的 driver/logging 路径。

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_target_priority_worker_ab_20260614/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_target_priority_worker_ab_20260614/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_apollo20_sector_wave_c488c428_target_20_17_16_no_learning_baseline

Run task-20 no-learning baseline for the same target context.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_no_learning_baseline/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_no_learning_baseline/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_no_learning_baseline/solutions --quiet --set journey_learning_enabled=False --set journey_learning_required=False --set journey_learning_fail_hard=False --set journey_learning_force_light_profile_pricing=False --set journey_learning_prewarm_enabled=False --set journey_learning_pricing_enabled=False
```

### task020_apollo20_sector_wave_c488c428_target_20_17_16_target_priority_worker

Run explicit opt-in target-priority Pulse worker. This may add true-RC negative columns but cannot certify no-negative.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instance BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_target_priority_worker/results.csv --log-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_target_priority_worker/logs --solution-dir BPC_future/results/gat_target_priority_worker_ab_20260614/task020_apollo20_sector_wave_c488c428_target_20_17_16_target_priority_worker/solutions --quiet --set journey_learning_enabled=False --set journey_learning_required=False --set journey_learning_fail_hard=False --set journey_learning_force_light_profile_pricing=False --set journey_learning_prewarm_enabled=False --set journey_learning_pricing_enabled=False --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=1.0 --set journey_sharded_pulse_worker_current_probe_max_recursions=50000 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=16 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=True --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=True --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=True --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=16 --set journey_sharded_pulse_hidden_negative_worker_max_columns=4 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=c488c428ee5822de --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,17,16 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,17,16 --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_risk:2,20->17:low_risk:2,17->16:low_risk:2,16->0:low_risk:2'
```

## 边界

- 5/10 命令不关闭主线 GAT/learning，也不启用新 worker；
- 20 worker 命令是显式 opt-in，只验证 target-priority ROI；
- 所有命令都不启用 sharded Pulse certificate 或 official lower-bound effect；
- 含 `->` 的 arc-option 配置通过 `shlex.join` 自动引用，不能手工去掉引号；
- 该 runbook 不是生产开关，跑完后仍需看 5/10 no-regression 和 20-task ROI。
