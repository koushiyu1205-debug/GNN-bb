# CBF Family Capture Worklist

日期：2026-06-14

## 目的

把 family-aware CBF gate 审计中的缺口转成可执行 capture worklist。
本脚本只读数据和实例目录，不运行 BPC / pricing / RMP，也不改变默认求解路径。

## 机器字段

```text
cbf_family_capture_worklist = current
status = cbf_family_capture_worklist_ready
diagnostic_only = true
runs_bpc_or_pricing = false
work_item_count = 4
command_count = 3
all_checks_pass = true
production_ready = false
```

## 摘要

```json
{
  "command_count": 3,
  "work_item_count": 4,
  "work_items": [
    {
      "family": "greedy-anchor",
      "priority": 100,
      "recommended_action": "capture_family_context_rows",
      "selected_instance_count": 2,
      "status": "family_gate_not_ready",
      "task_count": 20
    },
    {
      "family": "moon_trek_tasks20",
      "priority": 80,
      "recommended_action": "recover_family_mapping_before_capture",
      "selected_instance_count": 0,
      "status": "insufficient_family_rows",
      "task_count": 20
    },
    {
      "family": "random-wave",
      "priority": 80,
      "recommended_action": "capture_family_context_rows",
      "selected_instance_count": 4,
      "status": "insufficient_family_rows",
      "task_count": 20
    },
    {
      "family": "sector-wave",
      "priority": 80,
      "recommended_action": "capture_family_context_rows",
      "selected_instance_count": 4,
      "status": "insufficient_family_rows",
      "task_count": 20
    }
  ]
}
```

## Commands

### greedy-anchor / task_count=20

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 90.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/greedy-anchor/results.csv --log-dir BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/greedy-anchor/logs --solution-dir BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/greedy-anchor/solutions --run-log-dir BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/greedy-anchor/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### random-wave / task_count=20

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 90.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/random-wave/results.csv --log-dir BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/random-wave/logs --solution-dir BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/random-wave/solutions --run-log-dir BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/random-wave/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### sector-wave / task_count=20

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 90.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave/results.csv --log-dir BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave/logs --solution-dir BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave/solutions --run-log-dir BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

## 解释

- 这些命令只用于后续 no-certificate-effect capture；
- 小规模不会被安排采样，以保持 5/10 默认不退化；
- 采样后必须重新 build CBF dataset、readiness、family-policy 审计；
- worklist 不是 production gate，也不是 certificate。
