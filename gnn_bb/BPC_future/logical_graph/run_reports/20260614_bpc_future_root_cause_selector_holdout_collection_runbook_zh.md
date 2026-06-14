# Root Cause Selector Holdout Collection Runbook 报告

日期：2026-06-14

## 目的

本报告把 selector holdout manifest 中的 context targets 解析成可执行
component payload 采集命令。生成报告不会运行 BPC / pricing / RMP / Pulse；
真正执行 `commands.sh` 才会启动 calibration runs。

## 机器字段

```text
root_cause_selector_holdout_collection_runbook = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_holdout_collection_runbook_ready
collection_target_count = 10
collection_target_profile_mapping_count = 10
command_count = 6
source_profile_count = 3
source_config_class_count = 2
instance_count = 2
all_checks_pass = true
```

## 结论

当前 selector holdout 的 10 个 priority contexts 已能映射到 calibration runner 支持的 source profiles 和本地 logical graph 路径。该 runbook 只生成 no-certificate-effect active-basis / pool / returned-batch / forbidden-signature capture 命令；它本身不运行 BPC，也不证明 selector 或优化方向已经可上线。

## Source profiles

```json
[
  "experimental_early_new_task_set_quota_3_20_only",
  "experimental_l1_previous_dual_stabilization_20_only",
  "experimental_pricing_time_0_6_20_only"
]
```

## Source config classes

```json
[
  "dp1000_pt02_cg4_tl8",
  "target002_pt03_dp1000_cg4_tl8"
]
```

## Commands

```json
[
  {
    "command_id": "selector_holdout_capture_001",
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "profile": "experimental_early_new_task_set_quota_3_20_only",
    "source_config_class": "dp1000_pt02_cg4_tl8",
    "repeat_count": 3,
    "min_repeat_count": 3,
    "time_limit": 8.0,
    "max_cg_iterations": 4,
    "pricing_time_limit": 0.2,
    "pricing_max_dp_states": 1000,
    "expected_context_hashes": [
      "1db815e33b9ea471",
      "3c36c602289637b4",
      "7f2e531534d18ad2"
    ],
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_sharded_pulse_roi_calibration.py --output-dir BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__dp1000_pt02_cg4_tl8 --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --profiles experimental_early_new_task_set_quota_3_20_only --repeat-count 3 --time-limit 8 --max-cg-iterations 4 --pricing-time-limit 0.2 --pricing-max-dp-states 1000 --counterfactual-replay-capture --counterfactual-replay-capture-active-basis --counterfactual-replay-capture-active-basis-max-rows 0 --counterfactual-replay-capture-max-journeys 0 --counterfactual-replay-capture-pool-max-journeys 0 --counterfactual-replay-capture-forbidden-signatures --counterfactual-replay-capture-forbidden-signature-max-count 0 --counterfactual-replay-capture-log-empty --quiet"
  },
  {
    "command_id": "selector_holdout_capture_002",
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "profile": "experimental_early_new_task_set_quota_3_20_only",
    "source_config_class": "target002_pt03_dp1000_cg4_tl8",
    "repeat_count": 3,
    "min_repeat_count": 3,
    "time_limit": 8.0,
    "max_cg_iterations": 4,
    "pricing_time_limit": 0.3,
    "pricing_max_dp_states": 1000,
    "expected_context_hashes": [
      "3f914a0d2b97fd27"
    ],
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_sharded_pulse_roi_calibration.py --output-dir BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8 --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --profiles experimental_early_new_task_set_quota_3_20_only --repeat-count 3 --time-limit 8 --max-cg-iterations 4 --pricing-time-limit 0.3 --pricing-max-dp-states 1000 --counterfactual-replay-capture --counterfactual-replay-capture-active-basis --counterfactual-replay-capture-active-basis-max-rows 0 --counterfactual-replay-capture-max-journeys 0 --counterfactual-replay-capture-pool-max-journeys 0 --counterfactual-replay-capture-forbidden-signatures --counterfactual-replay-capture-forbidden-signature-max-count 0 --counterfactual-replay-capture-log-empty --quiet"
  },
  {
    "command_id": "selector_holdout_capture_003",
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "profile": "experimental_l1_previous_dual_stabilization_20_only",
    "source_config_class": "dp1000_pt02_cg4_tl8",
    "repeat_count": 3,
    "min_repeat_count": 3,
    "time_limit": 8.0,
    "max_cg_iterations": 4,
    "pricing_time_limit": 0.2,
    "pricing_max_dp_states": 1000,
    "expected_context_hashes": [
      "e55ea3e7d277b6d1"
    ],
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_sharded_pulse_roi_calibration.py --output-dir BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/003_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_l1_previous_dual_stabilization_20_only__dp1000_pt02_cg4_tl8 --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --profiles experimental_l1_previous_dual_stabilization_20_only --repeat-count 3 --time-limit 8 --max-cg-iterations 4 --pricing-time-limit 0.2 --pricing-max-dp-states 1000 --counterfactual-replay-capture --counterfactual-replay-capture-active-basis --counterfactual-replay-capture-active-basis-max-rows 0 --counterfactual-replay-capture-max-journeys 0 --counterfactual-replay-capture-pool-max-journeys 0 --counterfactual-replay-capture-forbidden-signatures --counterfactual-replay-capture-forbidden-signature-max-count 0 --counterfactual-replay-capture-log-empty --quiet"
  },
  {
    "command_id": "selector_holdout_capture_004",
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "profile": "experimental_pricing_time_0_6_20_only",
    "source_config_class": "dp1000_pt02_cg4_tl8",
    "repeat_count": 3,
    "min_repeat_count": 3,
    "time_limit": 8.0,
    "max_cg_iterations": 4,
    "pricing_time_limit": 0.2,
    "pricing_max_dp_states": 1000,
    "expected_context_hashes": [
      "d60fcf4b919b7d22"
    ],
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_sharded_pulse_roi_calibration.py --output-dir BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/004_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_pricing_time_0_6_20_only__dp1000_pt02_cg4_tl8 --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --profiles experimental_pricing_time_0_6_20_only --repeat-count 3 --time-limit 8 --max-cg-iterations 4 --pricing-time-limit 0.2 --pricing-max-dp-states 1000 --counterfactual-replay-capture --counterfactual-replay-capture-active-basis --counterfactual-replay-capture-active-basis-max-rows 0 --counterfactual-replay-capture-max-journeys 0 --counterfactual-replay-capture-pool-max-journeys 0 --counterfactual-replay-capture-forbidden-signatures --counterfactual-replay-capture-forbidden-signature-max-count 0 --counterfactual-replay-capture-log-empty --quiet"
  },
  {
    "command_id": "selector_holdout_capture_005",
    "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
    "profile": "experimental_early_new_task_set_quota_3_20_only",
    "source_config_class": "dp1000_pt02_cg4_tl8",
    "repeat_count": 3,
    "min_repeat_count": 3,
    "time_limit": 8.0,
    "max_cg_iterations": 4,
    "pricing_time_limit": 0.2,
    "pricing_max_dp_states": 1000,
    "expected_context_hashes": [
      "05695ab419abfb4b",
      "774573a2964cb1c5",
      "79de1ece885a7f67"
    ],
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_sharded_pulse_roi_calibration.py --output-dir BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_early_new_task_set_quota_3_20_only__dp1000_pt02_cg4_tl8 --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --profiles experimental_early_new_task_set_quota_3_20_only --repeat-count 3 --time-limit 8 --max-cg-iterations 4 --pricing-time-limit 0.2 --pricing-max-dp-states 1000 --counterfactual-replay-capture --counterfactual-replay-capture-active-basis --counterfactual-replay-capture-active-basis-max-rows 0 --counterfactual-replay-capture-max-journeys 0 --counterfactual-replay-capture-pool-max-journeys 0 --counterfactual-replay-capture-forbidden-signatures --counterfactual-replay-capture-forbidden-signature-max-count 0 --counterfactual-replay-capture-log-empty --quiet"
  },
  {
    "command_id": "selector_holdout_capture_006",
    "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
    "profile": "experimental_l1_previous_dual_stabilization_20_only",
    "source_config_class": "dp1000_pt02_cg4_tl8",
    "repeat_count": 3,
    "min_repeat_count": 3,
    "time_limit": 8.0,
    "max_cg_iterations": 4,
    "pricing_time_limit": 0.2,
    "pricing_max_dp_states": 1000,
    "expected_context_hashes": [
      "c5a59a95c2c9971a"
    ],
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_sharded_pulse_roi_calibration.py --output-dir BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/006_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_l1_previous_dual_stabilization_20_only__dp1000_pt02_cg4_tl8 --instances BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json --profiles experimental_l1_previous_dual_stabilization_20_only --repeat-count 3 --time-limit 8 --max-cg-iterations 4 --pricing-time-limit 0.2 --pricing-max-dp-states 1000 --counterfactual-replay-capture --counterfactual-replay-capture-active-basis --counterfactual-replay-capture-active-basis-max-rows 0 --counterfactual-replay-capture-max-journeys 0 --counterfactual-replay-capture-pool-max-journeys 0 --counterfactual-replay-capture-forbidden-signatures --counterfactual-replay-capture-forbidden-signature-max-count 0 --counterfactual-replay-capture-log-empty --quiet"
  }
]
```

## 检查项

```json
{
  "all_commands_are_diagnostic_only": true,
  "all_commands_have_active_basis_capture": true,
  "all_commands_have_forbidden_signature_capture": true,
  "all_commands_have_nondefault_pricing_context_args": true,
  "all_instances_resolved": true,
  "all_source_configs_supported": true,
  "all_source_profiles_extracted": true,
  "all_source_profiles_supported": true,
  "has_commands": true,
  "has_targets": true,
  "manifest_passed": true,
  "runbook_generation_does_not_run_bpc_or_pricing": true
}
```

## 当前边界

- 未执行这些命令；
- 未证明 expected context hash 已被重新命中；
- 未训练或验证 production selector；
- 未打开 worker default 或 certificate gate。
