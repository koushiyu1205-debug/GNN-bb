# CBF kNN+OOD Sector-Wave Audit-Only Smoke Runbook

日期：2026-06-14

## 目的

本报告只生成 `20|sector-wave` 的 opt-in audit-only smoke 命令。
它本身不运行 BPC / pricing / RMP，不启用 worker，不产生 certificate，
也不改变 official lower bound。

## 机器字段

```text
cbf_knn_ood_sector_wave_smoke_runbook = current
status = cbf_knn_ood_sector_wave_smoke_runbook_ready
diagnostic_only = true
runs_bpc_or_pricing = false
target_task_family = 20|sector-wave
selected_instance_count = 4
all_checks_pass = true
production_ready = false
active_worker_ready = false
certificate_ready = false
```

## Candidate

```json
{
  "active_worker_effect": false,
  "certificate_effect": false,
  "knn_k": 3,
  "max_neighbor_unsafe_fraction": 0.0,
  "min_high_priority_threshold": 0.8,
  "official_bound_effect": false,
  "policy": "knn_ood_delay_queue_scheduler",
  "safe_radius_multiplier": 1.0,
  "safe_radius_quantile": 1.0,
  "unsafe_action": "delay_not_reject"
}
```

## Proof Budget Contract

```json
{
  "delay_queue_can_extend_proof_budget": false,
  "delay_queue_runs_proof_sweep": false,
  "proof_stage_budget_effect": "none_existing_exact_deadlines_unchanged",
  "proof_stage_policy": "delay_queue_never_replaces_or_extends_exact_final_judge"
}
```

## Selected Instances

- `apollo` ordinal=1: `BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json`
- `tranquillitatis` ordinal=1: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json`
- `apollo` ordinal=5: `BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json`
- `tranquillitatis` ordinal=5: `BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json`

## Commands

### sector_wave_capture

Run baseline solver with replay capture enabled only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 90.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_capture/results.csv --log-dir BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_capture/logs --solution-dir BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_capture/solutions --run-log-dir BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_capture/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### knn_ood_capture_validation

Read produced JSONL logs and validate the k=3 kNN+OOD scheduler.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_cbf_delay_queue_knn_ood_capture_validation.py BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_capture/logs --train-dataset BPC_future/results/cbf_trajectory_gate_dataset_global_h2_20260614/cbf_trajectory_gate_transitions.jsonl --output-dir BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_knn_ood_capture_validation --report BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_knn_ood_capture_validation_zh.md --knn-k 3 --max-neighbor-unsafe-fraction 0.0 --min-high-priority-threshold 0.800000 --safe-radius-quantile 1.000000 --safe-radius-multiplier 1.000000
```

## 解释

- 这是 sector-wave-only 的真实日志采集协议，不是 production 接入；
- capture 命令只启用 counterfactual replay capture，不启用 Pulse worker 或 certificate；
- validation 命令使用当前外部网格里有信号的 `k=3, threshold=0.8, q=1.0, m=1.0`；
- 通过该 smoke 只能证明值得继续 A/B，不能证明可以默认启用；
- 若 validation 仍全 delay，则候选还没有真实 ROI 证据；
- 若出现 false positive，则该候选必须继续保持 delay / abstain。
