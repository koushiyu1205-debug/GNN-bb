# Journey Tail Min-Fill A/B Results

日期：2026-06-25

## 目的

读取已完成的 paired replay 输出，判断低 min-fill opt-in 是 strong positive、hard negative、regression 还是 no-effect。该脚本只读日志，不运行 BPC / pricing / RMP。

## 机器字段

```text
journey_tail_minfill_ab_results = current
entry_count = 7
row_count = 7
target_wall = 200.0
classification_counts = {'hard_negative': 2, 'missing_result': 2, 'no_effect': 1, 'positive_speedup': 1, 'strong_positive': 1}
classification_reason_counts = {'baseline_or_optin_result_missing': 2, 'both_nonoptimal_no_target_resolution': 2, 'both_optimal_wall_reduced': 1, 'no_target_or_wall_change': 1, 'nonoptimal_to_target_optimal': 1}
strong_positive_count = 1
hard_negative_count = 2
regression_count = 0
runs_bpc_or_pricing = false
certificate_effect = false
official_bound_effect = false
```

## Rows

```json
[
  {
    "baseline": {
      "columns": 0,
      "completion_retry_count": 4,
      "completion_retry_negative_journeys": 17,
      "completion_retry_selected_trips": 4,
      "completion_retry_state_counts": {
        "FOUND_NEGATIVE:direct_label_partial_negative_journey": 1,
        "FOUND_NEGATIVE:time_limit": 3
      },
      "direct_label_harvest_min_fill_values": [
        10
      ],
      "dual_bound": "",
      "evaluated_timed_trips": 0,
      "exact_pricing_calls": 0,
      "external_timeout": true,
      "gap": "",
      "generated_sequences": 0,
      "has_result": true,
      "node_count": 0,
      "pricing_calls": 0,
      "primal_bound": "",
      "result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v340_from_v339_root_tail8_20260625/001_apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph/baseline",
      "rmp_solves": 0,
      "solving_time": 0.0,
      "status": "EXTERNAL_TIME_LIMIT",
      "tail_minfill_applied_count": 0,
      "tail_minfill_candidate_count": 5,
      "tail_minfill_optin_disabled_count": 5,
      "tail_minfill_reason_counts": {
        "optin_disabled": 5
      },
      "wall_time": 260.038373
    },
    "certificate_effect": false,
    "classification": "hard_negative",
    "classification_reason": "both_nonoptimal_no_target_resolution",
    "deltas": {
      "columns": 0.0,
      "completion_retry_count": -1.0,
      "completion_retry_negative_journeys": -6.0,
      "completion_retry_selected_trips": -1.0,
      "evaluated_timed_trips": 0.0,
      "exact_pricing_calls": 0.0,
      "generated_sequences": 0.0,
      "node_count": 0.0,
      "pricing_calls": 0.0,
      "rmp_solves": 0.0,
      "solving_time": 0.0,
      "wall_time": 0.003804
    },
    "diagnostic_only": true,
    "entry_id": 1,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
    "official_bound_effect": false,
    "optin": {
      "columns": 0,
      "completion_retry_count": 3,
      "completion_retry_negative_journeys": 11,
      "completion_retry_selected_trips": 3,
      "completion_retry_state_counts": {
        "FOUND_NEGATIVE:time_limit": 3
      },
      "direct_label_harvest_min_fill_values": [
        4
      ],
      "dual_bound": "",
      "evaluated_timed_trips": 0,
      "exact_pricing_calls": 0,
      "external_timeout": true,
      "gap": "",
      "generated_sequences": 0,
      "has_result": true,
      "node_count": 0,
      "pricing_calls": 0,
      "primal_bound": "",
      "result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v340_from_v339_root_tail8_20260625/001_apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph/tail_minfill_optin",
      "rmp_solves": 0,
      "solving_time": 0.0,
      "status": "EXTERNAL_TIME_LIMIT",
      "tail_minfill_applied_count": 4,
      "tail_minfill_candidate_count": 4,
      "tail_minfill_optin_disabled_count": 0,
      "tail_minfill_reason_counts": {
        "applied": 4
      },
      "wall_time": 260.042177
    },
    "runs_bpc_or_pricing": false,
    "schema_version": "journey_tail_minfill_ab_result_row_v1",
    "source_completion_retry_class": "completion_bound_found_negative",
    "source_tail_min_fill_candidate_count": 5
  },
  {
    "baseline": {
      "columns": 645,
      "completion_retry_count": 4,
      "completion_retry_negative_journeys": 30,
      "completion_retry_selected_trips": 5,
      "completion_retry_state_counts": {
        "FOUND_NEGATIVE:direct_label_partial_negative_journey": 3,
        "INCOMPLETE_LIMIT:time_limit": 1
      },
      "direct_label_harvest_min_fill_values": [
        10
      ],
      "dual_bound": "",
      "evaluated_timed_trips": 1772731,
      "exact_pricing_calls": 13,
      "external_timeout": false,
      "gap": "",
      "generated_sequences": 1805889,
      "has_result": true,
      "node_count": 1,
      "pricing_calls": 46,
      "primal_bound": "608.139688",
      "result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v340_from_v339_root_tail8_20260625/002_apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph/baseline",
      "rmp_solves": 33,
      "solving_time": 149.361071,
      "status": "TIME_LIMIT",
      "tail_minfill_applied_count": 0,
      "tail_minfill_candidate_count": 4,
      "tail_minfill_optin_disabled_count": 4,
      "tail_minfill_reason_counts": {
        "optin_disabled": 4
      },
      "wall_time": 151.443002
    },
    "certificate_effect": false,
    "classification": "strong_positive",
    "classification_reason": "nonoptimal_to_target_optimal",
    "deltas": {
      "columns": -20.0,
      "completion_retry_count": -2.0,
      "completion_retry_negative_journeys": -21.0,
      "completion_retry_selected_trips": -3.0,
      "evaluated_timed_trips": -572243.0,
      "exact_pricing_calls": -5.0,
      "generated_sequences": 380930.0,
      "node_count": 0.0,
      "pricing_calls": -5.0,
      "rmp_solves": 0.0,
      "solving_time": -19.676981,
      "wall_time": -19.705823
    },
    "diagnostic_only": true,
    "entry_id": 2,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
    "official_bound_effect": false,
    "optin": {
      "columns": 625,
      "completion_retry_count": 2,
      "completion_retry_negative_journeys": 9,
      "completion_retry_selected_trips": 2,
      "completion_retry_state_counts": {
        "CERTIFIED_NO_NEGATIVE:direct_label_no_negative_journey": 1,
        "FOUND_NEGATIVE:time_limit": 1
      },
      "direct_label_harvest_min_fill_values": [
        4
      ],
      "dual_bound": "606.538972",
      "evaluated_timed_trips": 1200488,
      "exact_pricing_calls": 8,
      "external_timeout": false,
      "gap": "0.0",
      "generated_sequences": 2186819,
      "has_result": true,
      "node_count": 1,
      "pricing_calls": 41,
      "primal_bound": "606.538972",
      "result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v340_from_v339_root_tail8_20260625/002_apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph/tail_minfill_optin",
      "rmp_solves": 33,
      "solving_time": 129.68409,
      "status": "OPTIMAL",
      "tail_minfill_applied_count": 2,
      "tail_minfill_candidate_count": 2,
      "tail_minfill_optin_disabled_count": 0,
      "tail_minfill_reason_counts": {
        "applied": 2
      },
      "wall_time": 131.737179
    },
    "runs_bpc_or_pricing": false,
    "schema_version": "journey_tail_minfill_ab_result_row_v1",
    "source_completion_retry_class": "completion_bound_time_limit_no_column_uncertified",
    "source_tail_min_fill_candidate_count": 4
  },
  {
    "baseline": {
      "columns": 252,
      "completion_retry_count": 5,
      "completion_retry_negative_journeys": 0,
      "completion_retry_selected_trips": 0,
      "completion_retry_state_counts": {
        "CERTIFIED_NO_NEGATIVE:direct_label_no_negative_journey": 5
      },
      "direct_label_harvest_min_fill_values": [
        10
      ],
      "dual_bound": "537.218772",
      "evaluated_timed_trips": 1458223,
      "exact_pricing_calls": 24,
      "external_timeout": false,
      "gap": "0.0",
      "generated_sequences": 3638189,
      "has_result": true,
      "node_count": 5,
      "pricing_calls": 52,
      "primal_bound": "537.218772",
      "result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v340_from_v339_root_tail8_20260625/003_apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph/baseline",
      "rmp_solves": 28,
      "solving_time": 208.306272,
      "status": "OPTIMAL",
      "tail_minfill_applied_count": 0,
      "tail_minfill_candidate_count": 1,
      "tail_minfill_optin_disabled_count": 1,
      "tail_minfill_reason_counts": {
        "depth_gt_max": 4,
        "optin_disabled": 1
      },
      "wall_time": 210.922646
    },
    "certificate_effect": false,
    "classification": "no_effect",
    "classification_reason": "no_target_or_wall_change",
    "deltas": {
      "columns": 0.0,
      "completion_retry_count": 0.0,
      "completion_retry_negative_journeys": 0.0,
      "completion_retry_selected_trips": 0.0,
      "evaluated_timed_trips": 0.0,
      "exact_pricing_calls": 0.0,
      "generated_sequences": -139.0,
      "node_count": 0.0,
      "pricing_calls": 0.0,
      "rmp_solves": 0.0,
      "solving_time": -0.30286,
      "wall_time": -0.320087
    },
    "diagnostic_only": true,
    "entry_id": 3,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
    "official_bound_effect": false,
    "optin": {
      "columns": 252,
      "completion_retry_count": 5,
      "completion_retry_negative_journeys": 0,
      "completion_retry_selected_trips": 0,
      "completion_retry_state_counts": {
        "CERTIFIED_NO_NEGATIVE:direct_label_no_negative_journey": 5
      },
      "direct_label_harvest_min_fill_values": [
        4,
        10
      ],
      "dual_bound": "537.218772",
      "evaluated_timed_trips": 1458223,
      "exact_pricing_calls": 24,
      "external_timeout": false,
      "gap": "0.0",
      "generated_sequences": 3638050,
      "has_result": true,
      "node_count": 5,
      "pricing_calls": 52,
      "primal_bound": "537.218772",
      "result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v340_from_v339_root_tail8_20260625/003_apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph/tail_minfill_optin",
      "rmp_solves": 28,
      "solving_time": 208.003412,
      "status": "OPTIMAL",
      "tail_minfill_applied_count": 1,
      "tail_minfill_candidate_count": 1,
      "tail_minfill_optin_disabled_count": 0,
      "tail_minfill_reason_counts": {
        "applied": 1,
        "depth_gt_max": 4
      },
      "wall_time": 210.602559
    },
    "runs_bpc_or_pricing": false,
    "schema_version": "journey_tail_minfill_ab_result_row_v1",
    "source_completion_retry_class": "completion_bound_certified_no_negative",
    "source_tail_min_fill_candidate_count": 1
  },
  {
    "baseline": {
      "columns": 0,
      "completion_retry_count": 0,
      "completion_retry_negative_journeys": 0,
      "completion_retry_selected_trips": 0,
      "completion_retry_state_counts": {},
      "direct_label_harvest_min_fill_values": [],
      "dual_bound": "",
      "evaluated_timed_trips": 0,
      "exact_pricing_calls": 0,
      "external_timeout": true,
      "gap": "",
      "generated_sequences": 0,
      "has_result": true,
      "node_count": 0,
      "pricing_calls": 0,
      "primal_bound": "",
      "result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v340_from_v339_root_tail8_20260625/004_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/baseline",
      "rmp_solves": 0,
      "solving_time": 0.0,
      "status": "EXTERNAL_TIME_LIMIT",
      "tail_minfill_applied_count": 0,
      "tail_minfill_candidate_count": 1,
      "tail_minfill_optin_disabled_count": 1,
      "tail_minfill_reason_counts": {
        "optin_disabled": 1
      },
      "wall_time": 260.029108
    },
    "certificate_effect": false,
    "classification": "hard_negative",
    "classification_reason": "both_nonoptimal_no_target_resolution",
    "deltas": {
      "columns": 0.0,
      "completion_retry_count": 0.0,
      "completion_retry_negative_journeys": 0.0,
      "completion_retry_selected_trips": 0.0,
      "evaluated_timed_trips": 0.0,
      "exact_pricing_calls": 0.0,
      "generated_sequences": 0.0,
      "node_count": 0.0,
      "pricing_calls": 0.0,
      "rmp_solves": 0.0,
      "solving_time": 0.0,
      "wall_time": 0.000782
    },
    "diagnostic_only": true,
    "entry_id": 4,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json",
    "official_bound_effect": false,
    "optin": {
      "columns": 0,
      "completion_retry_count": 0,
      "completion_retry_negative_journeys": 0,
      "completion_retry_selected_trips": 0,
      "completion_retry_state_counts": {},
      "direct_label_harvest_min_fill_values": [],
      "dual_bound": "",
      "evaluated_timed_trips": 0,
      "exact_pricing_calls": 0,
      "external_timeout": true,
      "gap": "",
      "generated_sequences": 0,
      "has_result": true,
      "node_count": 0,
      "pricing_calls": 0,
      "primal_bound": "",
      "result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v340_from_v339_root_tail8_20260625/004_apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph/tail_minfill_optin",
      "rmp_solves": 0,
      "solving_time": 0.0,
      "status": "EXTERNAL_TIME_LIMIT",
      "tail_minfill_applied_count": 1,
      "tail_minfill_candidate_count": 1,
      "tail_minfill_optin_disabled_count": 0,
      "tail_minfill_reason_counts": {
        "applied": 1
      },
      "wall_time": 260.02989
    },
    "runs_bpc_or_pricing": false,
    "schema_version": "journey_tail_minfill_ab_result_row_v1",
    "source_completion_retry_class": "completion_bound_found_negative",
    "source_tail_min_fill_candidate_count": 1
  },
  {
    "baseline": {
      "columns": 392,
      "completion_retry_count": 5,
      "completion_retry_negative_journeys": 0,
      "completion_retry_selected_trips": 0,
      "completion_retry_state_counts": {
        "CERTIFIED_NO_NEGATIVE:direct_label_no_negative_journey": 5
      },
      "direct_label_harvest_min_fill_values": [
        10
      ],
      "dual_bound": "513.110284",
      "evaluated_timed_trips": 1543338,
      "exact_pricing_calls": 22,
      "external_timeout": false,
      "gap": "0.0",
      "generated_sequences": 3236444,
      "has_result": true,
      "node_count": 5,
      "pricing_calls": 53,
      "primal_bound": "513.110284",
      "result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v340_from_v339_root_tail8_20260625/005_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/baseline",
      "rmp_solves": 31,
      "solving_time": 249.118871,
      "status": "OPTIMAL",
      "tail_minfill_applied_count": 0,
      "tail_minfill_candidate_count": 1,
      "tail_minfill_optin_disabled_count": 1,
      "tail_minfill_reason_counts": {
        "depth_gt_max": 4,
        "optin_disabled": 1
      },
      "wall_time": 251.830028
    },
    "certificate_effect": false,
    "classification": "positive_speedup",
    "classification_reason": "both_optimal_wall_reduced",
    "deltas": {
      "columns": 0.0,
      "completion_retry_count": 0.0,
      "completion_retry_negative_journeys": 0.0,
      "completion_retry_selected_trips": 0.0,
      "evaluated_timed_trips": -446.0,
      "exact_pricing_calls": 0.0,
      "generated_sequences": -264.0,
      "node_count": 0.0,
      "pricing_calls": 0.0,
      "rmp_solves": 0.0,
      "solving_time": -0.704753,
      "wall_time": -1.150707
    },
    "diagnostic_only": true,
    "entry_id": 5,
    "instance": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json",
    "official_bound_effect": false,
    "optin": {
      "columns": 392,
      "completion_retry_count": 5,
      "completion_retry_negative_journeys": 0,
      "completion_retry_selected_trips": 0,
      "completion_retry_state_counts": {
        "CERTIFIED_NO_NEGATIVE:direct_label_no_negative_journey": 5
      },
      "direct_label_harvest_min_fill_values": [
        4,
        10
      ],
      "dual_bound": "513.110284",
      "evaluated_timed_trips": 1542892,
      "exact_pricing_calls": 22,
      "external_timeout": false,
      "gap": "0.0",
      "generated_sequences": 3236180,
      "has_result": true,
      "node_count": 5,
      "pricing_calls": 53,
      "primal_bound": "513.110284",
      "result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v340_from_v339_root_tail8_20260625/005_apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph/tail_minfill_optin",
      "rmp_solves": 31,
      "solving_time": 248.414118,
      "status": "OPTIMAL",
      "tail_minfill_applied_count": 1,
      "tail_minfill_candidate_count": 1,
      "tail_minfill_optin_disabled_count": 0,
      "tail_minfill_reason_counts": {
        "applied": 1,
        "depth_gt_max": 4
      },
      "wall_time": 250.679321
    },
    "runs_bpc_or_pricing": false,
    "schema_version": "journey_tail_minfill_ab_result_row_v1",
    "source_completion_retry_class": "completion_bound_certified_no_negative",
    "source_tail_min_fill_candidate_count": 1
  },
  {
    "baseline": {
      "columns": 0,
      "completion_retry_count": 0,
      "completion_retry_negative_journeys": 0,
      "completion_retry_selected_trips": 0,
      "completion_retry_state_counts": {},
      "direct_label_harvest_min_fill_values": [],
      "dual_bound": null,
      "evaluated_timed_trips": 0,
      "exact_pricing_calls": 0,
      "external_timeout": false,
      "gap": null,
      "generated_sequences": 0,
      "has_result": false,
      "node_count": 0,
      "pricing_calls": 0,
      "primal_bound": null,
      "result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v340_from_v339_root_tail8_20260625/006_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/baseline",
      "rmp_solves": 0,
      "solving_time": 0.0,
      "status": null,
      "tail_minfill_applied_count": 0,
      "tail_minfill_candidate_count": 0,
      "tail_minfill_optin_disabled_count": 0,
      "tail_minfill_reason_counts": {},
      "wall_time": 0.0
    },
    "certificate_effect": false,
    "classification": "missing_result",
    "classification_reason": "baseline_or_optin_result_missing",
    "deltas": {
      "columns": 0.0,
      "completion_retry_count": 0.0,
      "completion_retry_negative_journeys": 0.0,
      "completion_retry_selected_trips": 0.0,
      "evaluated_timed_trips": 0.0,
      "exact_pricing_calls": 0.0,
      "generated_sequences": 0.0,
      "node_count": 0.0,
      "pricing_calls": 0.0,
      "rmp_solves": 0.0,
      "solving_time": 0.0,
      "wall_time": 0.0
    },
    "diagnostic_only": true,
    "entry_id": 6,
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
    "official_bound_effect": false,
    "optin": {
      "columns": 0,
      "completion_retry_count": 0,
      "completion_retry_negative_journeys": 0,
      "completion_retry_selected_trips": 0,
      "completion_retry_state_counts": {},
      "direct_label_harvest_min_fill_values": [],
      "dual_bound": null,
      "evaluated_timed_trips": 0,
      "exact_pricing_calls": 0,
      "external_timeout": false,
      "gap": null,
      "generated_sequences": 0,
      "has_result": false,
      "node_count": 0,
      "pricing_calls": 0,
      "primal_bound": null,
      "result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v340_from_v339_root_tail8_20260625/006_apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph/tail_minfill_optin",
      "rmp_solves": 0,
      "solving_time": 0.0,
      "status": null,
      "tail_minfill_applied_count": 0,
      "tail_minfill_candidate_count": 0,
      "tail_minfill_optin_disabled_count": 0,
      "tail_minfill_reason_counts": {},
      "wall_time": 0.0
    },
    "runs_bpc_or_pricing": false,
    "schema_version": "journey_tail_minfill_ab_result_row_v1",
    "source_completion_retry_class": "completion_bound_certified_no_negative",
    "source_tail_min_fill_candidate_count": 1
  },
  {
    "baseline": {
      "columns": 0,
      "completion_retry_count": 0,
      "completion_retry_negative_journeys": 0,
      "completion_retry_selected_trips": 0,
      "completion_retry_state_counts": {},
      "direct_label_harvest_min_fill_values": [],
      "dual_bound": null,
      "evaluated_timed_trips": 0,
      "exact_pricing_calls": 0,
      "external_timeout": false,
      "gap": null,
      "generated_sequences": 0,
      "has_result": false,
      "node_count": 0,
      "pricing_calls": 0,
      "primal_bound": null,
      "result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v340_from_v339_root_tail8_20260625/007_apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph/baseline",
      "rmp_solves": 0,
      "solving_time": 0.0,
      "status": null,
      "tail_minfill_applied_count": 0,
      "tail_minfill_candidate_count": 0,
      "tail_minfill_optin_disabled_count": 0,
      "tail_minfill_reason_counts": {},
      "wall_time": 0.0
    },
    "certificate_effect": false,
    "classification": "missing_result",
    "classification_reason": "baseline_or_optin_result_missing",
    "deltas": {
      "columns": 0.0,
      "completion_retry_count": 0.0,
      "completion_retry_negative_journeys": 0.0,
      "completion_retry_selected_trips": 0.0,
      "evaluated_timed_trips": 0.0,
      "exact_pricing_calls": 0.0,
      "generated_sequences": 0.0,
      "node_count": 0.0,
      "pricing_calls": 0.0,
      "rmp_solves": 0.0,
      "solving_time": 0.0,
      "wall_time": 0.0
    },
    "diagnostic_only": true,
    "entry_id": 7,
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json",
    "official_bound_effect": false,
    "optin": {
      "columns": 0,
      "completion_retry_count": 0,
      "completion_retry_negative_journeys": 0,
      "completion_retry_selected_trips": 0,
      "completion_retry_state_counts": {},
      "direct_label_harvest_min_fill_values": [],
      "dual_bound": null,
      "evaluated_timed_trips": 0,
      "exact_pricing_calls": 0,
      "external_timeout": false,
      "gap": null,
      "generated_sequences": 0,
      "has_result": false,
      "node_count": 0,
      "pricing_calls": 0,
      "primal_bound": null,
      "result_dir": "BPC_future/results/journey_tail_minfill_ab_runbook_v340_from_v339_root_tail8_20260625/007_apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph/tail_minfill_optin",
      "rmp_solves": 0,
      "solving_time": 0.0,
      "status": null,
      "tail_minfill_applied_count": 0,
      "tail_minfill_candidate_count": 0,
      "tail_minfill_optin_disabled_count": 0,
      "tail_minfill_reason_counts": {},
      "wall_time": 0.0
    },
    "runs_bpc_or_pricing": false,
    "schema_version": "journey_tail_minfill_ab_result_row_v1",
    "source_completion_retry_class": "completion_bound_certified_no_negative",
    "source_tail_min_fill_candidate_count": 1
  }
]
```
