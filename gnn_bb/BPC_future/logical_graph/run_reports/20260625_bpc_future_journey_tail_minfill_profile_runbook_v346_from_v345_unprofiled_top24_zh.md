# Journey Tail Min-Fill Profile Runbook

日期：2026-06-25

## 目的

为 canonical random-TW 20-scale 未覆盖实例生成 audit-only profile 命令。这些命令只采集 low min-fill candidate 字段，行为保持 disabled；后续再用 completion-tail profile 筛出真正需要 paired replay 的候选。

## 机器字段

```text
journey_tail_minfill_profile_runbook = current
raw_instance_count = 60
excluded_instance_count = 8
candidate_pool_count = 52
entry_count = 24
command_count = 24
time_limit = 260
tail_min_fill = 4
tail_min_fill_enabled = false
positive_template_count = 1
negative_template_count = 2
guard_template_count = 3
runs_bpc_or_pricing = false
certificate_effect = false
official_bound_effect = false
```

## Entries

```json
[
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/001_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/001_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/001_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/001_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 1,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json",
    "priority_reason": "same_positive_family,same_positive_scenario",
    "priority_score": 129.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/001_apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph",
    "scenario": "apollo15_20km",
    "seed": 61614,
    "task_index": 7
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/002_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/002_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/002_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/002_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 2,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "priority_reason": "same_positive_family,same_positive_scenario",
    "priority_score": 127.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/002_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph",
    "scenario": "apollo15_20km",
    "seed": 61512,
    "task_index": 6
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/003_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/003_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/003_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/003_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 3,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "priority_reason": "same_positive_family,same_positive_scenario",
    "priority_score": 125.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/003_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph",
    "scenario": "apollo15_20km",
    "seed": 61410,
    "task_index": 5
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/004_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/004_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/004_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/004_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 4,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "priority_reason": "same_positive_family,same_positive_scenario",
    "priority_score": 123.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/004_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph",
    "scenario": "apollo15_20km",
    "seed": 61308,
    "task_index": 4
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/005_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/005_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/005_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/005_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 5,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "priority_reason": "same_positive_family,same_positive_scenario",
    "priority_score": 119.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/005_apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph",
    "scenario": "apollo15_20km",
    "seed": 61103,
    "task_index": 2
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/006_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/006_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/006_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/006_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 6,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json",
    "priority_reason": "same_positive_family,same_positive_scenario",
    "priority_score": 117.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/006_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph",
    "scenario": "apollo15_20km",
    "seed": 61000,
    "task_index": 1
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/007_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/007_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/007_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/007_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 7,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json",
    "priority_reason": "near_positive_task_index,same_positive_family",
    "priority_score": 115.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/007_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph",
    "scenario": "tranquillitatis_balmer_like_20km",
    "seed": 61948,
    "task_index": 10
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/008_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/008_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/008_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/008_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 8,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
    "priority_reason": "near_positive_task_index,same_positive_family",
    "priority_score": 113.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/008_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph",
    "scenario": "tranquillitatis_balmer_like_20km",
    "seed": 61846,
    "task_index": 9
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/009_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/009_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/009_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/009_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 9,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json",
    "priority_reason": "near_positive_task_index,same_positive_family",
    "priority_score": 111.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/009_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph",
    "scenario": "tranquillitatis_balmer_like_20km",
    "seed": 61744,
    "task_index": 8
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/010_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/010_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/010_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/010_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 10,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json",
    "priority_reason": "same_positive_family",
    "priority_score": 109.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/010_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph",
    "scenario": "tranquillitatis_balmer_like_20km",
    "seed": 61635,
    "task_index": 7
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/011_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/011_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/011_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/011_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 11,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
    "priority_reason": "same_positive_family",
    "priority_score": 107.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/011_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph",
    "scenario": "tranquillitatis_balmer_like_20km",
    "seed": 61520,
    "task_index": 6
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/012_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/012_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/012_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/012_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 12,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json",
    "priority_reason": "same_positive_family",
    "priority_score": 105.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/012_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph",
    "scenario": "tranquillitatis_balmer_like_20km",
    "seed": 61414,
    "task_index": 5
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/013_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/013_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/013_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/013_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 13,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json",
    "priority_reason": "same_positive_family",
    "priority_score": 103.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/013_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph",
    "scenario": "tranquillitatis_balmer_like_20km",
    "seed": 61311,
    "task_index": 4
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/014_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/014_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/014_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/014_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 14,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
    "priority_reason": "same_positive_family",
    "priority_score": 99.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/014_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph",
    "scenario": "tranquillitatis_balmer_like_20km",
    "seed": 61103,
    "task_index": 2
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/015_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/015_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/015_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/015_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 15,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json",
    "priority_reason": "same_positive_family",
    "priority_score": 97.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/015_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph",
    "scenario": "tranquillitatis_balmer_like_20km",
    "seed": 61001,
    "task_index": 1
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/016_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/016_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/016_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/016_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 16,
    "family": "greedy-anchor",
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json",
    "priority_reason": "same_hard_negative_bucket,same_positive_family",
    "priority_score": 56.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/016_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph",
    "scenario": "tranquillitatis_balmer_like_20km",
    "seed": 61206,
    "task_index": 3
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/017_apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/017_apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/017_apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/017_apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 17,
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "priority_reason": "near_positive_task_index,same_positive_scenario",
    "priority_score": 40.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/017_apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph",
    "scenario": "apollo15_20km",
    "seed": 61919,
    "task_index": 10
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/018_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/018_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/018_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/018_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 18,
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
    "priority_reason": "near_positive_task_index,same_positive_scenario",
    "priority_score": 38.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/018_apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph",
    "scenario": "apollo15_20km",
    "seed": 61817,
    "task_index": 9
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/019_apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/019_apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/019_apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/019_apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 19,
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "priority_reason": "near_positive_task_index,same_positive_scenario",
    "priority_score": 36.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/019_apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph",
    "scenario": "apollo15_20km",
    "seed": 61715,
    "task_index": 8
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/020_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/020_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/020_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/020_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 20,
    "family": "random-wave",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
    "priority_reason": "near_positive_task_index,same_positive_scenario",
    "priority_score": 35.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/020_apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph",
    "scenario": "apollo15_20km",
    "seed": 61919,
    "task_index": 10
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/021_apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/021_apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/021_apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/021_apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 21,
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
    "priority_reason": "same_positive_scenario",
    "priority_score": 34.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/021_apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph",
    "scenario": "apollo15_20km",
    "seed": 61612,
    "task_index": 7
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_09_seed61817_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/022_apollo15_20km_random-wave_randomtw_tasks020_09_seed61817_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/022_apollo15_20km_random-wave_randomtw_tasks020_09_seed61817_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/022_apollo15_20km_random-wave_randomtw_tasks020_09_seed61817_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/022_apollo15_20km_random-wave_randomtw_tasks020_09_seed61817_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 22,
    "family": "random-wave",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
    "priority_reason": "near_positive_task_index,same_positive_scenario",
    "priority_score": 33.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/022_apollo15_20km_random-wave_randomtw_tasks020_09_seed61817_logical_graph",
    "scenario": "apollo15_20km",
    "seed": 61817,
    "task_index": 9
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/023_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/023_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/023_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/023_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 23,
    "family": "sector-wave",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json",
    "priority_reason": "same_positive_scenario",
    "priority_score": 32.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/023_apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph",
    "scenario": "apollo15_20km",
    "seed": 61510,
    "task_index": 6
  },
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 260 --results-csv BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/024_apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph/results.csv --log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/024_apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph/logs --solution-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/024_apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph/solutions --run-log-dir BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/024_apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=0 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True",
    "entry_id": 24,
    "family": "random-wave",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "priority_reason": "near_positive_task_index,same_positive_scenario",
    "priority_score": 31.0,
    "result_dir": "BPC_future/results/journey_tail_minfill_profile_runbook_v346_from_v345_unprofiled_top24_20260625/024_apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph",
    "scenario": "apollo15_20km",
    "seed": 61715,
    "task_index": 8
  }
]
```
