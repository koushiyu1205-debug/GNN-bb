# CBF Mode Transition Capture Runbook

日期：2026-06-14

## 目的

本报告生成 CBF mode transition capture 的 opt-in 命令清单。
它本身不运行 BPC / pricing / RMP / Pulse，也不改变任何默认 benchmark。

## 机器字段

```text
cbf_mode_transition_capture_runbook = current
status = cbf_mode_transition_capture_runbook_ready
diagnostic_only = true
runs_bpc_or_pricing = false
target_count = 8
command_count = 16
all_checks_pass = true
production_ready = false
goal_complete = false
```

## Profiles

- `capped_smoke`：短时、payload 有上限，只验证 capture plumbing；
- `full_capture`：完整 payload，用于后续 barrier dataset，但可能有明显日志开销。

## Commands

### capped_smoke / task05_apollo_smoke

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_5_journey.yaml --instances BPC_future/data/generated/moon_trek_60/logical_graphs/apollo15_20km/tasks_05/apollo15_20km_tasks05_01_seed6000_logical_graph.json --time-limit 30.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/capped_smoke/task05_apollo_smoke --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task05_apollo_smoke.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/capped_smoke/task05_apollo_smoke --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### capped_smoke / task05_tranq_smoke

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_5_journey.yaml --instances BPC_future/data/generated/moon_trek_60/logical_graphs/tranquillitatis_balmer_like_20km/tasks_05/tranquillitatis_balmer_like_20km_tasks05_01_seed6000_logical_graph.json --time-limit 30.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/capped_smoke/task05_tranq_smoke --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task05_tranq_smoke.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/capped_smoke/task05_tranq_smoke --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### capped_smoke / task10_apollo_smoke

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_10_journey.yaml --instances BPC_future/data/generated/moon_trek_60/logical_graphs/apollo15_20km/tasks_10/apollo15_20km_tasks10_01_seed11000_logical_graph.json --time-limit 45.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/capped_smoke/task10_apollo_smoke --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task10_apollo_smoke.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/capped_smoke/task10_apollo_smoke --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### capped_smoke / task10_tranq_smoke

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_10_journey.yaml --instances BPC_future/data/generated/moon_trek_60/logical_graphs/tranquillitatis_balmer_like_20km/tasks_10/tranquillitatis_balmer_like_20km_tasks10_01_seed11000_logical_graph.json --time-limit 45.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/capped_smoke/task10_tranq_smoke --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task10_tranq_smoke.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/capped_smoke/task10_tranq_smoke --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### capped_smoke / task20_apollo_random_wave_probe

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 90.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/capped_smoke/task20_apollo_random_wave_probe --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task20_apollo_random_wave_probe.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/capped_smoke/task20_apollo_random_wave_probe --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### capped_smoke / task20_tranq_random_wave_probe

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 90.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/capped_smoke/task20_tranq_random_wave_probe --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task20_tranq_random_wave_probe.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/capped_smoke/task20_tranq_random_wave_probe --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### capped_smoke / task20_apollo_sector_wave_probe

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 90.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/capped_smoke/task20_apollo_sector_wave_probe --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task20_apollo_sector_wave_probe.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/capped_smoke/task20_apollo_sector_wave_probe --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### capped_smoke / task20_tranq_sector_wave_probe

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 90.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/capped_smoke/task20_tranq_sector_wave_probe --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task20_tranq_sector_wave_probe.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/capped_smoke/task20_tranq_sector_wave_probe --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### full_capture / task05_apollo_smoke

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_5_journey.yaml --instances BPC_future/data/generated/moon_trek_60/logical_graphs/apollo15_20km/tasks_05/apollo15_20km_tasks05_01_seed6000_logical_graph.json --time-limit 30.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/full_capture/task05_apollo_smoke --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task05_apollo_smoke.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/full_capture/task05_apollo_smoke --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0
```

### full_capture / task05_tranq_smoke

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_5_journey.yaml --instances BPC_future/data/generated/moon_trek_60/logical_graphs/tranquillitatis_balmer_like_20km/tasks_05/tranquillitatis_balmer_like_20km_tasks05_01_seed6000_logical_graph.json --time-limit 30.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/full_capture/task05_tranq_smoke --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task05_tranq_smoke.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/full_capture/task05_tranq_smoke --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0
```

### full_capture / task10_apollo_smoke

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_10_journey.yaml --instances BPC_future/data/generated/moon_trek_60/logical_graphs/apollo15_20km/tasks_10/apollo15_20km_tasks10_01_seed11000_logical_graph.json --time-limit 45.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/full_capture/task10_apollo_smoke --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task10_apollo_smoke.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/full_capture/task10_apollo_smoke --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0
```

### full_capture / task10_tranq_smoke

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_10_journey.yaml --instances BPC_future/data/generated/moon_trek_60/logical_graphs/tranquillitatis_balmer_like_20km/tasks_10/tranquillitatis_balmer_like_20km_tasks10_01_seed11000_logical_graph.json --time-limit 45.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/full_capture/task10_tranq_smoke --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task10_tranq_smoke.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/full_capture/task10_tranq_smoke --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0
```

### full_capture / task20_apollo_random_wave_probe

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 90.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/full_capture/task20_apollo_random_wave_probe --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task20_apollo_random_wave_probe.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/full_capture/task20_apollo_random_wave_probe --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0
```

### full_capture / task20_tranq_random_wave_probe

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 90.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/full_capture/task20_tranq_random_wave_probe --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task20_tranq_random_wave_probe.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/full_capture/task20_tranq_random_wave_probe --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0
```

### full_capture / task20_apollo_sector_wave_probe

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 90.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/full_capture/task20_apollo_sector_wave_probe --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task20_apollo_sector_wave_probe.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/full_capture/task20_apollo_sector_wave_probe --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0
```

### full_capture / task20_tranq_sector_wave_probe

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 90.0 --log-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/logs/full_capture/task20_tranq_sector_wave_probe --results-csv BPC_future/results/cbf_mode_transition_capture_runbook_20260614/csv/task20_tranq_sector_wave_probe.csv --solution-dir BPC_future/results/cbf_mode_transition_capture_runbook_20260614/solutions/full_capture/task20_tranq_sector_wave_probe --quiet --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0
```
