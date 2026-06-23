# Journey Completion-Bound Tail Profile

日期：2026-06-23

## 目的

读取 solver JSONL 日志，聚合 true-dual completion-bound final judge 的尾部状态。该脚本只读日志，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_completion_tail_profile = current
log_count = 1
completion_retry_class_counts = {'completion_bound_time_limit_no_column_uncertified': 1}
incomplete_tail_count = 1
completion_retry_total_profile_generation_time = 90.028115
completion_retry_profile_timing_enabled_count = 1
completion_retry_profile_time_top = {'direct_label_profile_next_sortie_total_time': 87.621436, 'direct_label_profile_extend_time': 0.398187, 'direct_label_profile_bound_check_time': 0.37851, 'direct_label_profile_resource_precheck_time': 0.30193, 'direct_label_profile_completion_time': 0.205857, 'direct_label_profile_partial_bound_completion_route_time': 0.14898, 'direct_label_profile_partial_bound_unique_task_time': 0.062556, 'direct_label_profile_dominance_time': 0.05933}
completion_retry_total_generated_sequences = 38479
completion_retry_total_evaluated_timed_trips = 14288
completion_retry_total_negative_journeys = 0
completion_retry_total_selected_trips = 0
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## 解释

主要瓶颈是 completion-bound final judge 在无负列尾部耗尽时间，不是 GAT/worker 没触发。下一步应做 final-judge budget/profiling 和 direct-label loop 剪枝优化。

## Records

```json
[
  {
    "added_journeys": 140,
    "addition_event_count": 5,
    "completion_retry_class": "completion_bound_time_limit_no_column_uncertified",
    "completion_retry_count": 1,
    "completion_retry_last": {
      "best_reduced_cost": 0.0,
      "bound_build_time": 1.980363,
      "candidate_trips": 2090,
      "cg_iter": 6,
      "completion_bound_enabled": true,
      "direct_label_harvest_candidate_count": 0,
      "direct_label_harvest_selected_count": 0,
      "direct_label_harvest_selected_new_task_set_count": 0,
      "direct_label_harvest_selected_replacement_task_set_count": 0,
      "direct_label_profile_bound_check_time": 0.378509905,
      "direct_label_profile_bound_checks": 37394,
      "direct_label_profile_completion_calls": 25523,
      "direct_label_profile_completion_time": 0.205856532,
      "direct_label_profile_dominance_checks": 25523,
      "direct_label_profile_dominance_time": 0.059330136,
      "direct_label_profile_extend_time": 0.398186905,
      "direct_label_profile_extension_attempts": 492862,
      "direct_label_profile_next_sortie_calls": 70,
      "direct_label_profile_next_sortie_total_time": 87.621436359,
      "direct_label_profile_option_attempts": 417329,
      "direct_label_profile_partial_bound_completion_route_time": 0.148980172,
      "direct_label_profile_partial_bound_cut_time": 0.026802235,
      "direct_label_profile_partial_bound_dual_sum_time": 0.013590261,
      "direct_label_profile_partial_bound_resource_pareto_time": 0.0,
      "direct_label_profile_partial_bound_unique_route_time": 0.012233779,
      "direct_label_profile_partial_bound_unique_task_time": 0.062556026,
      "direct_label_profile_partial_bucket_count": 3983,
      "direct_label_profile_partial_bucket_label_count": 24644,
      "direct_label_profile_partial_bucket_max_size": 60,
      "direct_label_profile_partial_bucket_mean_size": 6.187296008,
      "direct_label_profile_partial_heap_pops": 25593,
      "direct_label_profile_pre_dominance_checks": 24356,
      "direct_label_profile_pre_dominance_pruned": 1085,
      "direct_label_profile_pre_dominance_time": 0.043905071,
      "direct_label_profile_resource_precheck_time": 0.301930438,
      "direct_label_profile_timing_enabled": true,
      "evaluated_timed_trips": 14288,
      "exhausted": false,
      "expanded_labels_after_bound": 54099,
      "expanded_labels_before_bound": 65970,
      "generated_sequences": 38479,
      "global_certificate": false,
      "global_certificate_capable": true,
      "harvest_candidate_negative_count": 0,
      "harvest_selected_count": 0,
      "harvest_selected_new_task_set_count": 0,
      "harvest_selected_replacement_task_set_count": 0,
      "lb_mean_value": -15.310976197,
      "lb_min_value": -281.05544775,
      "lb_negative_state_count": 789,
      "lb_pruned_labels": 11871,
      "lb_state_count": 2541,
      "negative_journeys": 0,
      "pricing_kind": "exact_completion_bound_retry",
      "pricing_state": "INCOMPLETE_LIMIT",
      "pricing_time_limit": 90.0,
      "profile_generation_time": 90.028115,
      "reason": "time_limit",
      "selected_trips": 0,
      "two_cycle_blocked_extensions": 92757,
      "two_cycle_build_time": 1.935285,
      "two_cycle_enabled": true,
      "two_cycle_incompatible_queries": 3933,
      "two_cycle_second_best_queries": 3933,
      "two_cycle_state_count": 160083,
      "two_cycle_table_complete": true,
      "two_cycle_top2_replacements": 82354
    },
    "completion_retry_profile_count_totals": {
      "direct_label_profile_bound_checks": 37394,
      "direct_label_profile_completion_calls": 25523,
      "direct_label_profile_dominance_checks": 25523,
      "direct_label_profile_extension_attempts": 492862,
      "direct_label_profile_next_sortie_calls": 70,
      "direct_label_profile_option_attempts": 417329,
      "direct_label_profile_partial_bucket_count": 3983,
      "direct_label_profile_partial_bucket_label_count": 24644,
      "direct_label_profile_partial_bucket_max_size": 60,
      "direct_label_profile_partial_heap_pops": 25593,
      "direct_label_profile_pre_dominance_checks": 24356,
      "direct_label_profile_pre_dominance_pruned": 1085
    },
    "completion_retry_profile_time_top": {
      "direct_label_profile_bound_check_time": 0.37851,
      "direct_label_profile_completion_time": 0.205857,
      "direct_label_profile_dominance_time": 0.05933,
      "direct_label_profile_extend_time": 0.398187,
      "direct_label_profile_next_sortie_total_time": 87.621436,
      "direct_label_profile_partial_bound_completion_route_time": 0.14898,
      "direct_label_profile_partial_bound_unique_task_time": 0.062556,
      "direct_label_profile_resource_precheck_time": 0.30193
    },
    "completion_retry_profile_time_totals": {
      "direct_label_profile_bound_check_time": 0.37851,
      "direct_label_profile_completion_time": 0.205857,
      "direct_label_profile_dominance_time": 0.05933,
      "direct_label_profile_extend_time": 0.398187,
      "direct_label_profile_next_sortie_total_time": 87.621436,
      "direct_label_profile_partial_bound_completion_route_time": 0.14898,
      "direct_label_profile_partial_bound_cut_time": 0.026802,
      "direct_label_profile_partial_bound_dual_sum_time": 0.01359,
      "direct_label_profile_partial_bound_resource_pareto_time": 0.0,
      "direct_label_profile_partial_bound_unique_route_time": 0.012234,
      "direct_label_profile_partial_bound_unique_task_time": 0.062556,
      "direct_label_profile_pre_dominance_time": 0.043905,
      "direct_label_profile_resource_precheck_time": 0.30193
    },
    "completion_retry_profile_timing_enabled_count": 1,
    "completion_retry_total_bound_build_time": 1.980363,
    "completion_retry_total_evaluated_timed_trips": 14288,
    "completion_retry_total_expanded_after_bound": 54099,
    "completion_retry_total_expanded_before_bound": 65970,
    "completion_retry_total_generated_sequences": 38479,
    "completion_retry_total_lb_pruned": 11871,
    "completion_retry_total_negative_journeys": 0,
    "completion_retry_total_profile_generation_time": 90.028115,
    "completion_retry_total_selected_trips": 0,
    "completion_retry_total_two_cycle_build_time": 1.935285,
    "completion_retry_trigger_count": 1,
    "finish_columns": 218,
    "finish_exact_pricing_calls": 7,
    "finish_pricing_calls": 13,
    "finish_pricing_incomplete_nodes": 1,
    "finish_primal_bound": 744.848595,
    "finish_rmp_solves": 6,
    "finish_solving_time": 97.135529,
    "finish_status": "TIME_LIMIT",
    "instance": null,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/finalcap90_profile_timing_apollo20_sector/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "new_journeys": 118,
    "pricing_event_count": 13,
    "pricing_kind_counts": {
      "exact": 5,
      "exact_completion_bound_retry": 1,
      "exact_hidden_negative_patrol": 1,
      "heuristic": 6
    },
    "pricing_state_counts": {
      "exact:FOUND_NEGATIVE:negative_journey": 1,
      "exact:FOUND_NEGATIVE:streaming_partial_dp_negative_journey": 3,
      "exact:LOCAL_NO_COLUMN_UNCERTIFIED:no_negative_journey": 1,
      "exact_completion_bound_retry:INCOMPLETE_LIMIT:time_limit": 1,
      "exact_hidden_negative_patrol:INCOMPLETE_LIMIT:time_limit": 1,
      "heuristic:FOUND_NEGATIVE:negative_journey": 1,
      "heuristic:LOCAL_NO_COLUMN_UNCERTIFIED:no_negative_journey": 5
    },
    "replacement_journeys": 22
  }
]
```
