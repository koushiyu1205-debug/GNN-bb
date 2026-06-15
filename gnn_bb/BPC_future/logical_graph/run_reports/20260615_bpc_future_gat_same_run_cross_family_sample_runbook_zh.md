# GAT Same-Run Batch Impact Audit-Only A/B Runbook

日期：2026-06-15

## 目的

生成 same-run GAT+kNN/OOD 进入 online 前的 audit-only A/B 命令。
该 runbook 本身不运行求解器；命令默认单 worker，保留当前 mainline
learning/GAT 配置，只对 capture profile 打开日志。

## 机器字段

```text
gat_same_run_batch_impact_audit_ab_runbook = current
status = gat_same_run_batch_impact_audit_ab_runbook_ready
diagnostic_only = true
runs_bpc_or_pricing = false
production_ready = false
active_worker_ready = false
certificate_ready = false
default_enabled = false
audit_decision_scope = all
requested_small_families = ['sector-wave', 'greedy-anchor', 'random-wave']
requested_twenty_families = ['greedy-anchor', 'random-wave']
selected_families_by_scale = {'5': ['greedy-anchor', 'random-wave', 'sector-wave'], '10': ['greedy-anchor', 'random-wave', 'sector-wave'], '20': ['greedy-anchor', 'random-wave']}
selected_family_region_counts = {'5': {'greedy-anchor|apollo': 1, 'greedy-anchor|tranquillitatis': 1, 'random-wave|apollo': 1, 'random-wave|tranquillitatis': 1, 'sector-wave|apollo': 1, 'sector-wave|tranquillitatis': 1}, '10': {'greedy-anchor|apollo': 1, 'greedy-anchor|tranquillitatis': 1, 'random-wave|apollo': 1, 'random-wave|tranquillitatis': 1, 'sector-wave|apollo': 1, 'sector-wave|tranquillitatis': 1}, '20': {'greedy-anchor|apollo': 2, 'greedy-anchor|tranquillitatis': 2, 'random-wave|apollo': 2, 'random-wave|tranquillitatis': 2}}
all_checks_pass = true
```

## Candidate Policy

```json
{
  "active_worker_effect": false,
  "certificate_effect": false,
  "negative_columns_must_remain_eventually_reachable": true,
  "nonnegative_decision": "REJECT_NONNEGATIVE_ONLY",
  "official_bound_effect": false,
  "permanent_negative_filter_allowed": false,
  "policy": "same_run_gat_embedding_knn_ood_delay_scheduler",
  "safe_negative_decision": "HIGH_PRIORITY",
  "unsafe_negative_decision": "DELAY_QUEUE"
}
```

## Productionization Standard

```json
{
  "certificate_effect_allowed": false,
  "default_enable_allowed": false,
  "negative_column_discard_allowed": false,
  "small_sample_training_requires_audit_only": true,
  "task20_wall_time_roi_required": true,
  "task5_10_no_regression_required": true
}
```

## Result Pairs

```json
[
  {
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task005_baseline/results.csv",
    "capture_csv": "BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task005_capture/results.csv",
    "instance_count": 6,
    "instances": [
      {
        "family": "greedy-anchor",
        "instance": "BPC_future/logical_graph/tasks_005/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks005_01_seed46001_logical_graph.json",
        "ordinal": 1,
        "region": "apollo",
        "task_count": 5
      },
      {
        "family": "greedy-anchor",
        "instance": "BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007_logical_graph.json",
        "ordinal": 1,
        "region": "tranquillitatis",
        "task_count": 5
      },
      {
        "family": "random-wave",
        "instance": "BPC_future/logical_graph/tasks_005/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks005_01_seed1046000_logical_graph.json",
        "ordinal": 1,
        "region": "apollo",
        "task_count": 5
      },
      {
        "family": "random-wave",
        "instance": "BPC_future/logical_graph/tasks_005/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_01_seed1146000_logical_graph.json",
        "ordinal": 1,
        "region": "tranquillitatis",
        "task_count": 5
      },
      {
        "family": "sector-wave",
        "instance": "BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json",
        "ordinal": 1,
        "region": "apollo",
        "task_count": 5
      },
      {
        "family": "sector-wave",
        "instance": "BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json",
        "ordinal": 1,
        "region": "tranquillitatis",
        "task_count": 5
      }
    ],
    "task_count": 5
  },
  {
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task010_baseline/results.csv",
    "capture_csv": "BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task010_capture/results.csv",
    "instance_count": 6,
    "instances": [
      {
        "family": "greedy-anchor",
        "instance": "BPC_future/logical_graph/tasks_010/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks010_01_seed51001_logical_graph.json",
        "ordinal": 1,
        "region": "apollo",
        "task_count": 10
      },
      {
        "family": "greedy-anchor",
        "instance": "BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_01_seed51000_logical_graph.json",
        "ordinal": 1,
        "region": "tranquillitatis",
        "task_count": 10
      },
      {
        "family": "random-wave",
        "instance": "BPC_future/logical_graph/tasks_010/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks010_01_seed51001_logical_graph.json",
        "ordinal": 1,
        "region": "apollo",
        "task_count": 10
      },
      {
        "family": "random-wave",
        "instance": "BPC_future/logical_graph/tasks_010/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_01_seed51000_logical_graph.json",
        "ordinal": 1,
        "region": "tranquillitatis",
        "task_count": 10
      },
      {
        "family": "sector-wave",
        "instance": "BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json",
        "ordinal": 1,
        "region": "apollo",
        "task_count": 10
      },
      {
        "family": "sector-wave",
        "instance": "BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json",
        "ordinal": 1,
        "region": "tranquillitatis",
        "task_count": 10
      }
    ],
    "task_count": 10
  },
  {
    "baseline_csv": "BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task020_baseline/results.csv",
    "capture_csv": "BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task020_capture/results.csv",
    "instance_count": 8,
    "instances": [
      {
        "family": "greedy-anchor",
        "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json",
        "ordinal": 1,
        "region": "apollo",
        "task_count": 20
      },
      {
        "family": "greedy-anchor",
        "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json",
        "ordinal": 1,
        "region": "tranquillitatis",
        "task_count": 20
      },
      {
        "family": "random-wave",
        "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
        "ordinal": 1,
        "region": "apollo",
        "task_count": 20
      },
      {
        "family": "random-wave",
        "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json",
        "ordinal": 1,
        "region": "tranquillitatis",
        "task_count": 20
      },
      {
        "family": "greedy-anchor",
        "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json",
        "ordinal": 9,
        "region": "apollo",
        "task_count": 20
      },
      {
        "family": "greedy-anchor",
        "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
        "ordinal": 9,
        "region": "tranquillitatis",
        "task_count": 20
      },
      {
        "family": "random-wave",
        "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
        "ordinal": 9,
        "region": "apollo",
        "task_count": 20
      },
      {
        "family": "random-wave",
        "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json",
        "ordinal": 9,
        "region": "tranquillitatis",
        "task_count": 20
      }
    ],
    "task_count": 20
  }
]
```

## Commands

### task005_baseline

Run current mainline solver with existing learning/GAT config.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task005_baseline/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task005_baseline/logs --solution-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task005_baseline/solutions --run-log-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task005_baseline/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks005_01_seed46001_logical_graph.json BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007_logical_graph.json BPC_future/logical_graph/tasks_005/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks005_01_seed1046000_logical_graph.json BPC_future/logical_graph/tasks_005/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_01_seed1146000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task005_capture

Run current mainline solver with capture logging only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task005_capture/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task005_capture/logs --solution-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task005_capture/solutions --run-log-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task005_capture/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks005_01_seed46001_logical_graph.json BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007_logical_graph.json BPC_future/logical_graph/tasks_005/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks005_01_seed1046000_logical_graph.json BPC_future/logical_graph/tasks_005/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_01_seed1146000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task010_baseline

Run current mainline solver with existing learning/GAT config.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task010_baseline/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task010_baseline/logs --solution-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task010_baseline/solutions --run-log-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task010_baseline/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_01_seed51000_logical_graph.json BPC_future/logical_graph/tasks_010/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_01_seed51000_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task010_capture

Run current mainline solver with capture logging only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task010_capture/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task010_capture/logs --solution-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task010_capture/solutions --run-log-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task010_capture/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_01_seed51000_logical_graph.json BPC_future/logical_graph/tasks_010/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_01_seed51000_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_baseline

Run current mainline solver with existing learning/GAT config.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 200.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task020_baseline/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task020_baseline/logs --solution-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task020_baseline/solutions --run-log-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task020_baseline/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_09_seed61817_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json
```

### task020_capture

Run current mainline solver with capture logging only.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 200.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task020_capture/results.csv --log-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task020_capture/logs --solution-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task020_capture/solutions --run-log-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task020_capture/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_09_seed61817_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### same_run_batch_impact_rows_build

Build same-run raw ROI rows from capture logs after capture commands finish.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_gat_same_run_batch_impact_dataset.py --output-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/same_run_batch_impact_dataset --report BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/same_run_batch_impact_dataset_zh.md --log-root BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task005_capture/logs --log-root BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task010_capture/logs --log-root BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/task020_capture/logs
```

### same_run_batch_impact_graph_dataset_build

Build graph samples for the same-run GAT checkpoint from raw ROI rows.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_gat_same_run_batch_impact_graph_dataset.py --input-jsonl BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/same_run_batch_impact_dataset/same_run_batch_impact_rows.jsonl --output-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/graph_dataset --report BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/same_run_batch_impact_graph_dataset_zh.md
```

### same_run_gat_knn_ood_offline_audit

Read offline same-run GAT checkpoint and validate kNN/OOD safety shell.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_gat_same_run_batch_impact_knn_ood.py --dataset-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/graph_dataset --checkpoint BPC_future/results/gat_same_run_batch_impact_training_20260615/context_aware_same_run_batch_impact_gat.pt --training-summary BPC_future/results/gat_same_run_batch_impact_training_20260615/summary.json --output-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/same_run_gat_knn_ood_audit --report BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/same_run_gat_knn_ood_audit_zh.md --device cpu --knn-k 3 --max-neighbor-delay-fraction 0.0 --safe-radius-quantile 1.0 --safe-radius-multiplier 1.0 --min-validation-high-priority 1 --min-delay-recall 0.500000 --decision-scope all
```

### target_priority_candidate_extract

Extract HIGH_PRIORITY target-intervention candidates from audit decisions.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_gat_same_run_target_priority_candidates.py --decision-records BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/same_run_gat_knn_ood_audit/decision_records.jsonl --output-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/target_priority_candidates --report BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/target_priority_candidates_zh.md --max-candidates 12
```

### delay_queue_candidate_extract

Extract DELAY_QUEUE target-intervention candidates for negative-label balance.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_gat_same_run_target_priority_candidates.py --decision-records BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/same_run_gat_knn_ood_audit/decision_records.jsonl --output-dir BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/delay_queue_target_candidates --report BPC_future/results/gat_same_run_cross_family_sample_runbook_20260615/delay_queue_target_candidates_zh.md --max-candidates 12 --delay-queue-only
```

## 解释

- 5/10 baseline 与 capture 都保留当前 mainline GAT/learning；
- capture-only 不允许改变 official result；
- same-run GAT+kNN/OOD 只做离线审计，不接 worker、不接 certificate；
- true-RC negative 只能 HIGH_PRIORITY 或 DELAY_QUEUE，不能永久丢弃；
- 该 runbook 不能证明 wall-time ROI，真正 ROI 要等 online opt-in A/B。
