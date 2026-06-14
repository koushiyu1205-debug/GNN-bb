# GAT Embedding Sector-Wave Audit-Only Smoke Runbook

日期：2026-06-14

## 目的

本报告生成 `20|sector-wave` 的 opt-in capture + GAT embedding
kNN/OOD validation 命令。它本身不运行 BPC / pricing / RMP，不启用
worker，不产生 certificate，也不改变 official lower bound。

## 机器字段

```text
gat_embedding_sector_wave_smoke_runbook = current
status = gat_embedding_sector_wave_smoke_runbook_ready
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
  "embedding_model": "BPC_future/data/gat_trajectory_cbf/v1/context_aware_trajectory_cbf_gat.pt",
  "knn_k": 3,
  "max_neighbor_unsafe_fraction": 0.0,
  "min_high_priority_threshold": 0.8,
  "official_bound_effect": false,
  "policy": "gat_embedding_knn_ood_delay_scheduler",
  "safe_radius_multiplier": 1.0,
  "safe_radius_quantile": 1.0,
  "train_dataset_dir": "BPC_future/data/gat_trajectory_cbf/v1",
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
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 90.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_embedding_sector_wave_smoke_runbook_20260614/sector_wave_capture/results.csv --log-dir BPC_future/results/gat_embedding_sector_wave_smoke_runbook_20260614/sector_wave_capture/logs --solution-dir BPC_future/results/gat_embedding_sector_wave_smoke_runbook_20260614/sector_wave_capture/solutions --run-log-dir BPC_future/results/gat_embedding_sector_wave_smoke_runbook_20260614/sector_wave_capture/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### gat_embedding_knn_ood_capture_validation

Read capture logs and validate GAT embedding plus kNN/OOD safety shell.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_gat_embedding_knn_ood_capture_validation.py BPC_future/results/gat_embedding_sector_wave_smoke_runbook_20260614/sector_wave_capture/logs --train-dataset-dir BPC_future/data/gat_trajectory_cbf/v1 --checkpoint BPC_future/data/gat_trajectory_cbf/v1/context_aware_trajectory_cbf_gat.pt --output-dir BPC_future/results/gat_embedding_sector_wave_smoke_runbook_20260614/sector_wave_gat_embedding_capture_validation --report BPC_future/results/gat_embedding_sector_wave_smoke_runbook_20260614/sector_wave_gat_embedding_capture_validation_zh.md --device cpu --knn-k 3 --max-neighbor-unsafe-fraction 0.0 --min-high-priority-threshold 0.800000 --safe-radius-quantile 1.000000 --safe-radius-multiplier 1.000000
```

## 解释

- capture 命令只启用 counterfactual replay capture，不启用 worker 或 certificate；
- validation 命令先从日志构建 trajectory/GAT validation dataset，再跑 GAT embedding safety shell；
- 通过该 runbook 只能证明下一步可以做 audit-only smoke，不证明可以 production 默认启用；
- 若 GAT embedding validation 出现 fp，则必须保持 delay / abstain；
- 即使 validation 有 high-priority，也不能永久丢弃任何 true-RC negative。
