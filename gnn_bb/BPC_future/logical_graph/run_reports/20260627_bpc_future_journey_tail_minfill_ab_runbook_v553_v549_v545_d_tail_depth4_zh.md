# Journey Tail Min-Fill A/B Runbook

日期：2026-06-27

## 目的

把 completion-tail profile 中的低 min-fill audit-only 候选转成 paired replay 命令。该脚本只生成 runbook，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_tail_minfill_ab_runbook = current
status = ready
raw_record_count = 60
tail_action_filter_enabled = True
tail_action_filter_row_count = 3476
tail_action_filter_match_key_count = 94
tail_action_filter_required_classes = ['D_EARLY_BRANCH']
tail_action_filter_required_productivity_classes = ['pricing_unproductive_no_negative_columns']
require_source_outside_target_wall = True
target_wall = 200.0
selection_stats = {'candidate_instance_count_before_limit': 38, 'skip_source_target_optimal': 22}
candidate_instance_count = 8
entry_count = 8
command_count = 16
time_limit = 600
tail_min_fill = 4
tail_min_fill_max_depth = 4
tail_min_fill_final_probe_only = True
runs_bpc_or_pricing = false
certificate_effect = false
official_bound_effect = false
```

## 说明

每个 entry 有 baseline 与 tail_minfill_optin 两条命令。baseline 强制保持低 min-fill 关闭，opt-in 只打开低 min-fill 调度；两者都保持 exact oracle 负责 RC 与证书。

## Entries

```json
[
  {
    "baseline_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/001_apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph/baseline/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/001_apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph/baseline/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/001_apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph/baseline/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/001_apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph/baseline/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "baseline_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/001_apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph/baseline",
    "entry_id": 1,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "optin_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/001_apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph/tail_minfill_optin/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/001_apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph/tail_minfill_optin/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/001_apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph/tail_minfill_optin/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/001_apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph/tail_minfill_optin/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "optin_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/001_apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph/tail_minfill_optin",
    "source_completion_retry_class": "completion_bound_time_limit_no_column_uncertified",
    "source_finish_solving_time": 237.584161,
    "source_finish_status": "TIME_LIMIT",
    "source_log_file": "BPC_future/results/20260627_v545_v543_merged_overlay_full60_tasks20/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json.jsonl",
    "source_tail_min_fill_candidate_count": 4,
    "source_tail_min_fill_reason_counts": {
      "optin_disabled": 4
    },
    "tail_action_filter_match": {
      "matched_tail_action_count": 9,
      "tail_action_class_counts": {
        "D_EARLY_BRANCH": 9
      },
      "tail_action_productivity_class_counts": {
        "pricing_unproductive_no_negative_columns": 9
      }
    }
  },
  {
    "baseline_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/002_apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph/baseline/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/002_apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph/baseline/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/002_apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph/baseline/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/002_apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph/baseline/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "baseline_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/002_apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph/baseline",
    "entry_id": 2,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json",
    "optin_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/002_apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph/tail_minfill_optin/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/002_apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph/tail_minfill_optin/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/002_apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph/tail_minfill_optin/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/002_apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph/tail_minfill_optin/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "optin_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/002_apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph/tail_minfill_optin",
    "source_completion_retry_class": "completion_bound_time_limit_no_column_uncertified",
    "source_finish_solving_time": 538.397067,
    "source_finish_status": "TIME_LIMIT",
    "source_log_file": "BPC_future/results/20260627_v545_v543_merged_overlay_full60_tasks20/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json.jsonl",
    "source_tail_min_fill_candidate_count": 3,
    "source_tail_min_fill_reason_counts": {
      "optin_disabled": 3
    },
    "tail_action_filter_match": {
      "matched_tail_action_count": 7,
      "tail_action_class_counts": {
        "D_EARLY_BRANCH": 7
      },
      "tail_action_productivity_class_counts": {
        "pricing_unproductive_no_negative_columns": 7
      }
    }
  },
  {
    "baseline_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/003_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/baseline/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/003_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/baseline/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/003_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/baseline/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/003_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/baseline/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "baseline_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/003_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/baseline",
    "entry_id": 3,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json",
    "optin_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/003_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/tail_minfill_optin/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/003_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/tail_minfill_optin/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/003_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/tail_minfill_optin/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/003_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/tail_minfill_optin/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "optin_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/003_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/tail_minfill_optin",
    "source_completion_retry_class": "completion_bound_time_limit_no_column_uncertified",
    "source_finish_solving_time": 338.455764,
    "source_finish_status": "TIME_LIMIT",
    "source_log_file": "BPC_future/results/20260627_v545_v543_merged_overlay_full60_tasks20/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "source_tail_min_fill_candidate_count": 2,
    "source_tail_min_fill_reason_counts": {
      "optin_disabled": 2
    },
    "tail_action_filter_match": {
      "matched_tail_action_count": 5,
      "tail_action_class_counts": {
        "D_EARLY_BRANCH": 5
      },
      "tail_action_productivity_class_counts": {
        "pricing_unproductive_no_negative_columns": 5
      }
    }
  },
  {
    "baseline_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/004_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/baseline/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/004_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/baseline/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/004_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/baseline/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/004_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/baseline/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "baseline_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/004_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/baseline",
    "entry_id": 4,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
    "optin_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/004_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/tail_minfill_optin/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/004_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/tail_minfill_optin/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/004_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/tail_minfill_optin/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/004_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/tail_minfill_optin/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "optin_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/004_apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph/tail_minfill_optin",
    "source_completion_retry_class": "completion_bound_found_negative",
    "source_finish_solving_time": null,
    "source_finish_status": null,
    "source_log_file": "BPC_future/results/20260627_v545_v543_merged_overlay_full60_tasks20/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json.jsonl",
    "source_tail_min_fill_candidate_count": 1,
    "source_tail_min_fill_reason_counts": {
      "depth_gt_max": 7,
      "optin_disabled": 1
    },
    "tail_action_filter_match": {
      "matched_tail_action_count": 28,
      "tail_action_class_counts": {
        "D_EARLY_BRANCH": 28
      },
      "tail_action_productivity_class_counts": {
        "pricing_unproductive_no_negative_columns": 28
      }
    }
  },
  {
    "baseline_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/baseline/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/baseline/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/baseline/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/baseline/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "baseline_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/baseline",
    "entry_id": 5,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json",
    "optin_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/tail_minfill_optin/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/tail_minfill_optin/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/tail_minfill_optin/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/tail_minfill_optin/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "optin_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph/tail_minfill_optin",
    "source_completion_retry_class": "completion_bound_found_negative",
    "source_finish_solving_time": null,
    "source_finish_status": null,
    "source_log_file": "BPC_future/results/20260627_v545_v543_merged_overlay_full60_tasks20/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json.jsonl",
    "source_tail_min_fill_candidate_count": 1,
    "source_tail_min_fill_reason_counts": {
      "depth_gt_max": 21,
      "optin_disabled": 1
    },
    "tail_action_filter_match": {
      "matched_tail_action_count": 67,
      "tail_action_class_counts": {
        "D_EARLY_BRANCH": 67
      },
      "tail_action_productivity_class_counts": {
        "pricing_unproductive_no_negative_columns": 67
      }
    }
  },
  {
    "baseline_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/006_apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph/baseline/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/006_apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph/baseline/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/006_apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph/baseline/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/006_apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph/baseline/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "baseline_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/006_apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph/baseline",
    "entry_id": 6,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "optin_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/006_apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph/tail_minfill_optin/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/006_apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph/tail_minfill_optin/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/006_apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph/tail_minfill_optin/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/006_apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph/tail_minfill_optin/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "optin_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/006_apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph/tail_minfill_optin",
    "source_completion_retry_class": "completion_bound_certified_no_negative",
    "source_finish_solving_time": 207.948819,
    "source_finish_status": "OPTIMAL",
    "source_log_file": "BPC_future/results/20260627_v545_v543_merged_overlay_full60_tasks20/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json.jsonl",
    "source_tail_min_fill_candidate_count": 5,
    "source_tail_min_fill_reason_counts": {
      "optin_disabled": 5
    },
    "tail_action_filter_match": {
      "matched_tail_action_count": 2,
      "tail_action_class_counts": {
        "D_EARLY_BRANCH": 2
      },
      "tail_action_productivity_class_counts": {
        "pricing_unproductive_no_negative_columns": 2
      }
    }
  },
  {
    "baseline_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/007_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/baseline/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/007_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/baseline/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/007_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/baseline/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/007_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/baseline/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "baseline_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/007_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/baseline",
    "entry_id": 7,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
    "optin_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/007_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/tail_minfill_optin/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/007_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/tail_minfill_optin/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/007_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/tail_minfill_optin/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/007_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/tail_minfill_optin/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "optin_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/007_apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph/tail_minfill_optin",
    "source_completion_retry_class": "completion_bound_certified_no_negative",
    "source_finish_solving_time": null,
    "source_finish_status": null,
    "source_log_file": "BPC_future/results/20260627_v545_v543_merged_overlay_full60_tasks20/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "source_tail_min_fill_candidate_count": 2,
    "source_tail_min_fill_reason_counts": {
      "depth_gt_max": 3,
      "optin_disabled": 2
    },
    "tail_action_filter_match": {
      "matched_tail_action_count": 16,
      "tail_action_class_counts": {
        "D_EARLY_BRANCH": 16
      },
      "tail_action_productivity_class_counts": {
        "pricing_unproductive_no_negative_columns": 16
      }
    }
  },
  {
    "baseline_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/008_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/baseline/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/008_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/baseline/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/008_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/baseline/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/008_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/baseline/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=False --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "baseline_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/008_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/baseline",
    "entry_id": 8,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
    "optin_command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json --time-limit 600 --results-csv BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/008_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/tail_minfill_optin/results.csv --log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/008_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/tail_minfill_optin/logs --solution-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/008_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/tail_minfill_optin/solutions --run-log-dir BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/008_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/tail_minfill_optin/run_logs --python /home/kai/miniconda3/bin/python --timeout-kill-after 30s --max-workers 1 --quiet --set journey_tail_action_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_audit_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_enabled=True --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_max_depth=4 --set journey_certificate_completion_bound_diverse_harvest_tail_min_fill_final_probe_only=True --set journey_tail_action_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_enabled=False --set journey_tail_action_no_column_early_branch_before_final_probe_enabled=False",
    "optin_result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v553_v549_v545_d_tail_depth4_20260627/008_apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph/tail_minfill_optin",
    "source_completion_retry_class": "completion_bound_certified_no_negative",
    "source_finish_solving_time": null,
    "source_finish_status": null,
    "source_log_file": "BPC_future/results/20260627_v545_v543_merged_overlay_full60_tasks20/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json.jsonl",
    "source_tail_min_fill_candidate_count": 2,
    "source_tail_min_fill_reason_counts": {
      "depth_gt_max": 11,
      "optin_disabled": 2
    },
    "tail_action_filter_match": {
      "matched_tail_action_count": 30,
      "tail_action_class_counts": {
        "D_EARLY_BRANCH": 30
      },
      "tail_action_productivity_class_counts": {
        "pricing_unproductive_no_negative_columns": 30
      }
    }
  }
]
```
