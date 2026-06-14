# GAT Embedding Audit-Only A/B Runbook

日期：2026-06-14

## 目的

生成生产化前的 GAT embedding 审计 A/B 命令。该 runbook 不运行 solver，
不启用 worker，不产生 certificate，也不改变 official lower bound。

## 机器字段

```text
gat_embedding_audit_ab_runbook = current
status = gat_embedding_audit_ab_runbook_ready
diagnostic_only = true
runs_bpc_or_pricing = false
production_ready = false
active_worker_ready = false
certificate_ready = false
all_checks_pass = true
```

## Result Pairs

```json
[
  {
    "baseline_csv": "BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task005_baseline/results.csv",
    "capture_csv": "BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task005_capture/results.csv",
    "instance_count": 2,
    "instances": [
      {
        "family": "sector-wave",
        "instance": "BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json",
        "ordinal": 1,
        "region": "apollo",
        "task_count": 5,
        "task_family": "5|sector-wave"
      },
      {
        "family": "sector-wave",
        "instance": "BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json",
        "ordinal": 1,
        "region": "tranquillitatis",
        "task_count": 5,
        "task_family": "5|sector-wave"
      }
    ],
    "task_count": 5
  },
  {
    "baseline_csv": "BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task010_baseline/results.csv",
    "capture_csv": "BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task010_capture/results.csv",
    "instance_count": 2,
    "instances": [
      {
        "family": "sector-wave",
        "instance": "BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json",
        "ordinal": 1,
        "region": "apollo",
        "task_count": 10,
        "task_family": "10|sector-wave"
      },
      {
        "family": "sector-wave",
        "instance": "BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json",
        "ordinal": 1,
        "region": "tranquillitatis",
        "task_count": 10,
        "task_family": "10|sector-wave"
      }
    ],
    "task_count": 10
  },
  {
    "baseline_csv": "BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task020_baseline/results.csv",
    "capture_csv": "BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task020_capture/results.csv",
    "instance_count": 4,
    "instances": [
      {
        "family": "sector-wave",
        "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
        "ordinal": 1,
        "region": "apollo",
        "task_count": 20,
        "task_family": "20|sector-wave"
      },
      {
        "family": "sector-wave",
        "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
        "ordinal": 1,
        "region": "tranquillitatis",
        "task_count": 20,
        "task_family": "20|sector-wave"
      },
      {
        "family": "sector-wave",
        "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
        "ordinal": 5,
        "region": "apollo",
        "task_count": 20,
        "task_family": "20|sector-wave"
      },
      {
        "family": "sector-wave",
        "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
        "ordinal": 5,
        "region": "tranquillitatis",
        "task_count": 20,
        "task_family": "20|sector-wave"
      }
    ],
    "task_count": 20
  }
]
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

## Baseline Overrides

```json
[
  "journey_learning_enabled=False",
  "journey_learning_required=False",
  "journey_learning_fail_hard=False",
  "journey_learning_force_light_profile_pricing=False",
  "journey_learning_prewarm_enabled=False",
  "journey_learning_pricing_enabled=False"
]
```

## Commands

### task005_baseline

Run baseline solver.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task005_baseline/results.csv --log-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task005_baseline/logs --solution-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task005_baseline/solutions --run-log-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task005_baseline/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json --set journey_learning_enabled=False --set journey_learning_required=False --set journey_learning_fail_hard=False --set journey_learning_force_light_profile_pricing=False --set journey_learning_prewarm_enabled=False --set journey_learning_pricing_enabled=False
```

### task005_capture

Run solver with counterfactual replay capture enabled only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task005_capture/results.csv --log-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task005_capture/logs --solution-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task005_capture/solutions --run-log-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task005_capture/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json --set journey_learning_enabled=False --set journey_learning_required=False --set journey_learning_fail_hard=False --set journey_learning_force_light_profile_pricing=False --set journey_learning_prewarm_enabled=False --set journey_learning_pricing_enabled=False --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task010_baseline

Run baseline solver.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task010_baseline/results.csv --log-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task010_baseline/logs --solution-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task010_baseline/solutions --run-log-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task010_baseline/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json --set journey_learning_enabled=False --set journey_learning_required=False --set journey_learning_fail_hard=False --set journey_learning_force_light_profile_pricing=False --set journey_learning_prewarm_enabled=False --set journey_learning_pricing_enabled=False
```

### task010_capture

Run solver with counterfactual replay capture enabled only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task010_capture/results.csv --log-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task010_capture/logs --solution-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task010_capture/solutions --run-log-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task010_capture/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json --set journey_learning_enabled=False --set journey_learning_required=False --set journey_learning_fail_hard=False --set journey_learning_force_light_profile_pricing=False --set journey_learning_prewarm_enabled=False --set journey_learning_pricing_enabled=False --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_baseline

Run baseline solver.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 200.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task020_baseline/results.csv --log-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task020_baseline/logs --solution-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task020_baseline/solutions --run-log-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task020_baseline/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --set journey_learning_enabled=False --set journey_learning_required=False --set journey_learning_fail_hard=False --set journey_learning_force_light_profile_pricing=False --set journey_learning_prewarm_enabled=False --set journey_learning_pricing_enabled=False
```

### task020_capture

Run solver with counterfactual replay capture enabled only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 200.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task020_capture/results.csv --log-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task020_capture/logs --solution-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task020_capture/solutions --run-log-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task020_capture/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json --set journey_learning_enabled=False --set journey_learning_required=False --set journey_learning_fail_hard=False --set journey_learning_force_light_profile_pricing=False --set journey_learning_prewarm_enabled=False --set journey_learning_pricing_enabled=False --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_gat_embedding_capture_validation

Validate GAT embedding kNN/OOD safety shell on task-20 capture logs.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_gat_embedding_knn_ood_capture_validation.py BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task020_capture/logs --train-dataset-dir BPC_future/data/gat_trajectory_cbf/v1 --checkpoint BPC_future/data/gat_trajectory_cbf/v1/context_aware_trajectory_cbf_gat.pt --output-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task020_gat_embedding_capture_validation --report BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/task020_gat_embedding_capture_validation_zh.md --device cpu --knn-k 3 --max-neighbor-unsafe-fraction 0.0 --min-high-priority-threshold 0.800000 --safe-radius-quantile 1.000000 --safe-radius-multiplier 1.000000
```

### audit_ab_result_analysis

Read result CSVs and validation summary after the previous commands finish.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_gat_embedding_audit_ab_results.py --runbook-summary BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/summary.json --output-dir BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/audit_ab_analysis --report BPC_future/results/gat_embedding_audit_ab_runbook_branchfilter_20260614/audit_ab_analysis_zh.md
```

## 解释

- 5/10 pair 只验证 capture-only 是否保持官方结果不变；
- 20 pair 只收集 GAT embedding validation 所需的真实日志；
- 该 runbook 不能证明 wall-time ROI，因为还没有 online opt-in effect；
- 任何 true-RC negative 都不能被 GAT/kNN/OOD 永久丢弃。
