# GAT Bulk Sampling Runbook 报告

日期：2026-06-15

## 目的

把慢的单候选 worker A/B 改成批量采样流程：20-task 只做
capture-only 批量采集 same-run batch-impact 标签，5/10 只保留
baseline/capture sentinel 来证明 no-regression。后续 GAT 训练、kNN/OOD
审计和候选抽取都在离线命令中完成。

## 机器字段

```text
gat_bulk_sampling_runbook = current
status = gat_bulk_sampling_runbook_ready
target_total_samples = 300
target_positive_samples = 100
existing_row_count = 54
existing_positive_count = 18
selected_new_instance_count = 33
selected_wave_count = 9
estimated_total_after = 285
estimated_positive_after = 100
production_ready = false
certificate_ready = false
default_enabled = false
all_checks_pass = true
```

## Bulk Sampling Policy

```json
{
  "cheap_sampling": "20_task_capture_only",
  "delay_queue": "delayed_negative_not_discarded",
  "expensive_worker_ab": "top_k_after_gat_knn_ood_only",
  "gat_role": "embedding_and_trajectory_impact_representation",
  "high_priority": "priority_only_not_certificate",
  "knn_ood_role": "safety_shell",
  "permanent_negative_filter_allowed": false
}
```

## Selected 20-task Instances

```json
[
  {
    "family": "random-wave",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
    "ordinal": 3,
    "region": "tranquillitatis",
    "task_count": 20
  },
  {
    "family": "random-wave",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "ordinal": 8,
    "region": "apollo",
    "task_count": 20
  },
  {
    "family": "random-wave",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json",
    "ordinal": 8,
    "region": "tranquillitatis",
    "task_count": 20
  },
  {
    "family": "random-wave",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json",
    "ordinal": 9,
    "region": "tranquillitatis",
    "task_count": 20
  },
  {
    "family": "random-wave",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "ordinal": 10,
    "region": "apollo",
    "task_count": 20
  },
  {
    "family": "random-wave",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
    "ordinal": 10,
    "region": "tranquillitatis",
    "task_count": 20
  },
  {
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "ordinal": 4,
    "region": "apollo",
    "task_count": 20
  },
  {
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json",
    "ordinal": 4,
    "region": "tranquillitatis",
    "task_count": 20
  },
  {
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "ordinal": 5,
    "region": "apollo",
    "task_count": 20
  },
  {
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json",
    "ordinal": 5,
    "region": "tranquillitatis",
    "task_count": 20
  },
  {
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "ordinal": 6,
    "region": "apollo",
    "task_count": 20
  },
  {
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "ordinal": 6,
    "region": "tranquillitatis",
    "task_count": 20
  },
  {
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json",
    "ordinal": 7,
    "region": "apollo",
    "task_count": 20
  },
  {
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json",
    "ordinal": 7,
    "region": "tranquillitatis",
    "task_count": 20
  },
  {
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json",
    "ordinal": 8,
    "region": "apollo",
    "task_count": 20
  },
  {
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json",
    "ordinal": 8,
    "region": "tranquillitatis",
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
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "ordinal": 10,
    "region": "apollo",
    "task_count": 20
  },
  {
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json",
    "ordinal": 10,
    "region": "tranquillitatis",
    "task_count": 20
  },
  {
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "ordinal": 1,
    "region": "tranquillitatis",
    "task_count": 20
  },
  {
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "ordinal": 2,
    "region": "tranquillitatis",
    "task_count": 20
  },
  {
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "ordinal": 3,
    "region": "apollo",
    "task_count": 20
  },
  {
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
    "ordinal": 3,
    "region": "tranquillitatis",
    "task_count": 20
  },
  {
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
    "ordinal": 4,
    "region": "apollo",
    "task_count": 20
  },
  {
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "ordinal": 5,
    "region": "apollo",
    "task_count": 20
  },
  {
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
    "ordinal": 5,
    "region": "tranquillitatis",
    "task_count": 20
  },
  {
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json",
    "ordinal": 6,
    "region": "apollo",
    "task_count": 20
  },
  {
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
    "ordinal": 7,
    "region": "apollo",
    "task_count": 20
  },
  {
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
    "ordinal": 7,
    "region": "tranquillitatis",
    "task_count": 20
  },
  {
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "ordinal": 8,
    "region": "apollo",
    "task_count": 20
  },
  {
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "ordinal": 8,
    "region": "tranquillitatis",
    "task_count": 20
  },
  {
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
    "ordinal": 9,
    "region": "apollo",
    "task_count": 20
  },
  {
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
    "ordinal": 10,
    "region": "tranquillitatis",
    "task_count": 20
  }
]
```

## Commands

### task005_baseline_sentinel

5/10 no-regression sentinel with current mainline config.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task005_baseline_sentinel/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task005_baseline_sentinel/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task005_baseline_sentinel/solutions --run-log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task005_baseline_sentinel/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks005_01_seed46001_logical_graph.json BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007_logical_graph.json
```

### task005_capture_sentinel

5/10 capture sentinel; capture logging only, no online effect.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task005_capture_sentinel/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task005_capture_sentinel/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task005_capture_sentinel/solutions --run-log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task005_capture_sentinel/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks005_01_seed46001_logical_graph.json BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task010_baseline_sentinel

5/10 no-regression sentinel with current mainline config.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task010_baseline_sentinel/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task010_baseline_sentinel/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task010_baseline_sentinel/solutions --run-log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task010_baseline_sentinel/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_01_seed51000_logical_graph.json
```

### task010_capture_sentinel

5/10 capture sentinel; capture logging only, no online effect.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task010_capture_sentinel/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task010_capture_sentinel/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task010_capture_sentinel/solutions --run-log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task010_capture_sentinel/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_01_seed51000_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_bulk_capture_wave01

20-task bulk same-run label capture only.  No baseline pair, worker, certificate, or official-bound effect.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 200.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/solutions --run-log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_bulk_capture_wave02

20-task bulk same-run label capture only.  No baseline pair, worker, certificate, or official-bound effect.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 200.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/solutions --run-log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_bulk_capture_wave03

20-task bulk same-run label capture only.  No baseline pair, worker, certificate, or official-bound effect.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 200.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/solutions --run-log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_bulk_capture_wave04

20-task bulk same-run label capture only.  No baseline pair, worker, certificate, or official-bound effect.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 200.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave04/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave04/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave04/solutions --run-log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave04/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_bulk_capture_wave05

20-task bulk same-run label capture only.  No baseline pair, worker, certificate, or official-bound effect.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 200.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave05/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave05/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave05/solutions --run-log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave05/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_bulk_capture_wave06

20-task bulk same-run label capture only.  No baseline pair, worker, certificate, or official-bound effect.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 200.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave06/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave06/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave06/solutions --run-log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave06/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_bulk_capture_wave07

20-task bulk same-run label capture only.  No baseline pair, worker, certificate, or official-bound effect.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 200.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave07/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave07/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave07/solutions --run-log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave07/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_bulk_capture_wave08

20-task bulk same-run label capture only.  No baseline pair, worker, certificate, or official-bound effect.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 200.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave08/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave08/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave08/solutions --run-log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave08/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_bulk_capture_wave09

20-task bulk same-run label capture only.  No baseline pair, worker, certificate, or official-bound effect.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --time-limit 200.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave09/results.csv --log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave09/logs --solution-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave09/solutions --run-log-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave09/run_logs --quiet --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_log_empty=true --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### same_run_batch_impact_rows_build

Build same-run raw training rows from all capture log roots.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_gat_same_run_batch_impact_dataset.py --output-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/same_run_batch_impact_dataset --report BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/same_run_batch_impact_dataset_zh.md --log-root BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task005_capture_sentinel/logs --log-root BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task010_capture_sentinel/logs --log-root BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave01/logs --log-root BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave02/logs --log-root BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave03/logs --log-root BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave04/logs --log-root BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave05/logs --log-root BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave06/logs --log-root BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave07/logs --log-root BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave08/logs --log-root BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave09/logs
```

### same_run_batch_impact_graph_dataset_build

Build local graph dataset; do not overwrite global dataset.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_gat_same_run_batch_impact_graph_dataset.py --input-jsonl BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/same_run_batch_impact_dataset/same_run_batch_impact_rows.jsonl --output-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/graph_dataset --report BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/same_run_batch_impact_graph_dataset_zh.md
```

### same_run_gat_train_offline

Train audit-only ContextAwareColumnSelector on the local bulk dataset. This checkpoint remains non-production until safety audits pass.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/train_gnn_column_selector.py --dataset-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/graph_dataset --checkpoint-out BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/same_run_batch_impact_training/context_aware_bulk_sampling_gat.pt --metrics-out BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/same_run_batch_impact_training/summary.json --device cpu --epochs 30
```

### same_run_gat_knn_ood_offline_audit

Audit the local checkpoint with kNN/OOD safety shell.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_gat_same_run_batch_impact_knn_ood.py --dataset-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/graph_dataset --checkpoint BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/same_run_batch_impact_training/context_aware_bulk_sampling_gat.pt --training-summary BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/same_run_batch_impact_training/summary.json --output-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/same_run_gat_knn_ood_audit --report BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/same_run_gat_knn_ood_audit_zh.md --device cpu --knn-k 3 --max-neighbor-delay-fraction 0.0 --safe-radius-quantile 1.0 --safe-radius-multiplier 1.0 --min-validation-high-priority 1 --min-delay-recall 0.500000 --decision-scope all
```

### target_priority_candidate_extract

Extract HIGH_PRIORITY candidates for later small top-K worker A/B.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_gat_same_run_target_priority_candidates.py --decision-records BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/same_run_gat_knn_ood_audit/decision_records.jsonl --output-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/target_priority_candidates --report BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/target_priority_candidates_zh.md --max-candidates 24
```

### delay_queue_candidate_extract

Extract DELAY_QUEUE candidates for boundary/negative balance sampling.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_gat_same_run_target_priority_candidates.py --decision-records BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/same_run_gat_knn_ood_audit/decision_records.jsonl --output-dir BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/delay_queue_target_candidates --report BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/delay_queue_target_candidates_zh.md --max-candidates 24 --delay-queue-only
```

## 结论

- 该 runbook 只生成批量采样命令，本身不运行求解器；
- 20-task 采样使用 capture-only，减少一半以上无标签成本；
- 5/10 只做 sentinel，不把小快实例混入 20-task ROI 目标；
- GAT/kNN/OOD 只做优先级与延迟队列，不能证书，不能丢弃 true-RC negative；
- 真正接 worker 前仍需 top-K target worker A/B 和 5/10 no-regression。
