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
completion_retry_total_profile_generation_time = 90.008683
completion_retry_profile_timing_enabled_count = 1
completion_retry_profile_time_top = {'direct_label_profile_next_sortie_total_time': 87.560703, 'direct_label_profile_task_filter_time': 85.666304, 'direct_label_profile_extend_time': 0.394613, 'direct_label_profile_resource_precheck_time': 0.379952, 'direct_label_profile_bound_check_time': 0.289241, 'direct_label_profile_completion_time': 0.211045, 'direct_label_profile_completed_process_time': 0.066768, 'direct_label_profile_partial_bound_unique_task_time': 0.061696}
completion_retry_total_generated_sequences = 38602
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
      "bound_build_time": 2.0167,
      "candidate_trips": 2090,
      "cg_iter": 6,
      "completion_bound_enabled": true,
      "direct_label_harvest_candidate_count": 0,
      "direct_label_harvest_selected_count": 0,
      "direct_label_harvest_selected_new_task_set_count": 0,
      "direct_label_harvest_selected_replacement_task_set_count": 0,
      "direct_label_profile_bound_check_time": 0.289240514,
      "direct_label_profile_bound_checks": 37517,
      "direct_label_profile_completed_dedup_time": 0.021455073,
      "direct_label_profile_completed_process_time": 0.066768407,
      "direct_label_profile_completion_calls": 25523,
      "direct_label_profile_completion_time": 0.211044571,
      "direct_label_profile_dominance_checks": 25523,
      "direct_label_profile_dominance_time": 0.060409003,
      "direct_label_profile_extend_time": 0.394613428,
      "direct_label_profile_extension_attempts": 492922,
      "direct_label_profile_label_create_time": 0.030736104,
      "direct_label_profile_next_sortie_calls": 73,
      "direct_label_profile_next_sortie_total_time": 87.560703073,
      "direct_label_profile_option_attempts": 417458,
      "direct_label_profile_option_lookup_time": 0.037956371,
      "direct_label_profile_partial_bound_completion_route_time": 0.057794997,
      "direct_label_profile_partial_bound_cut_time": 0.028009812,
      "direct_label_profile_partial_bound_dual_sum_time": 0.013526765,
      "direct_label_profile_partial_bound_resource_pareto_time": 0.0,
      "direct_label_profile_partial_bound_unique_route_time": 0.012402598,
      "direct_label_profile_partial_bound_unique_task_time": 0.061696426,
      "direct_label_profile_partial_bucket_count": 4032,
      "direct_label_profile_partial_bucket_label_count": 24647,
      "direct_label_profile_partial_bucket_max_size": 60,
      "direct_label_profile_partial_bucket_mean_size": 6.112847222,
      "direct_label_profile_partial_heap_pops": 25596,
      "direct_label_profile_pre_dominance_checks": 24356,
      "direct_label_profile_pre_dominance_pruned": 1085,
      "direct_label_profile_pre_dominance_time": 0.044302415,
      "direct_label_profile_priority_queue_time": 0.038387999,
      "direct_label_profile_resource_precheck_time": 0.379951594,
      "direct_label_profile_stream_callback_time": 0.037320365,
      "direct_label_profile_task_filter_time": 85.666303921,
      "direct_label_profile_timing_enabled": true,
      "evaluated_timed_trips": 14288,
      "exhausted": false,
      "expanded_labels_after_bound": 54099,
      "expanded_labels_before_bound": 66093,
      "generated_sequences": 38602,
      "global_certificate": false,
      "global_certificate_capable": true,
      "harvest_candidate_negative_count": 0,
      "harvest_selected_count": 0,
      "harvest_selected_new_task_set_count": 0,
      "harvest_selected_replacement_task_set_count": 0,
      "lb_mean_value": -15.310976197,
      "lb_min_value": -281.05544775,
      "lb_negative_state_count": 789,
      "lb_pruned_labels": 11994,
      "lb_state_count": 2541,
      "negative_journeys": 0,
      "pricing_kind": "exact_completion_bound_retry",
      "pricing_state": "INCOMPLETE_LIMIT",
      "pricing_time_limit": 90.0,
      "profile_generation_time": 90.008683,
      "reason": "time_limit",
      "selected_trips": 0,
      "two_cycle_blocked_extensions": 92757,
      "two_cycle_build_time": 1.971079,
      "two_cycle_enabled": true,
      "two_cycle_incompatible_queries": 3933,
      "two_cycle_second_best_queries": 3933,
      "two_cycle_state_count": 160083,
      "two_cycle_table_complete": true,
      "two_cycle_top2_replacements": 82354
    },
    "completion_retry_profile_count_totals": {
      "direct_label_profile_bound_checks": 37517,
      "direct_label_profile_completion_calls": 25523,
      "direct_label_profile_dominance_checks": 25523,
      "direct_label_profile_extension_attempts": 492922,
      "direct_label_profile_next_sortie_calls": 73,
      "direct_label_profile_option_attempts": 417458,
      "direct_label_profile_partial_bucket_count": 4032,
      "direct_label_profile_partial_bucket_label_count": 24647,
      "direct_label_profile_partial_bucket_max_size": 60,
      "direct_label_profile_partial_heap_pops": 25596,
      "direct_label_profile_pre_dominance_checks": 24356,
      "direct_label_profile_pre_dominance_pruned": 1085
    },
    "completion_retry_profile_time_top": {
      "direct_label_profile_bound_check_time": 0.289241,
      "direct_label_profile_completed_process_time": 0.066768,
      "direct_label_profile_completion_time": 0.211045,
      "direct_label_profile_extend_time": 0.394613,
      "direct_label_profile_next_sortie_total_time": 87.560703,
      "direct_label_profile_partial_bound_unique_task_time": 0.061696,
      "direct_label_profile_resource_precheck_time": 0.379952,
      "direct_label_profile_task_filter_time": 85.666304
    },
    "completion_retry_profile_time_totals": {
      "direct_label_profile_bound_check_time": 0.289241,
      "direct_label_profile_completed_dedup_time": 0.021455,
      "direct_label_profile_completed_process_time": 0.066768,
      "direct_label_profile_completion_time": 0.211045,
      "direct_label_profile_dominance_time": 0.060409,
      "direct_label_profile_extend_time": 0.394613,
      "direct_label_profile_label_create_time": 0.030736,
      "direct_label_profile_next_sortie_total_time": 87.560703,
      "direct_label_profile_option_lookup_time": 0.037956,
      "direct_label_profile_partial_bound_completion_route_time": 0.057795,
      "direct_label_profile_partial_bound_cut_time": 0.02801,
      "direct_label_profile_partial_bound_dual_sum_time": 0.013527,
      "direct_label_profile_partial_bound_resource_pareto_time": 0.0,
      "direct_label_profile_partial_bound_unique_route_time": 0.012403,
      "direct_label_profile_partial_bound_unique_task_time": 0.061696,
      "direct_label_profile_pre_dominance_time": 0.044302,
      "direct_label_profile_priority_queue_time": 0.038388,
      "direct_label_profile_resource_precheck_time": 0.379952,
      "direct_label_profile_stream_callback_time": 0.03732,
      "direct_label_profile_task_filter_time": 85.666304
    },
    "completion_retry_profile_timing_enabled_count": 1,
    "completion_retry_total_bound_build_time": 2.0167,
    "completion_retry_total_evaluated_timed_trips": 14288,
    "completion_retry_total_expanded_after_bound": 54099,
    "completion_retry_total_expanded_before_bound": 66093,
    "completion_retry_total_generated_sequences": 38602,
    "completion_retry_total_lb_pruned": 11994,
    "completion_retry_total_negative_journeys": 0,
    "completion_retry_total_profile_generation_time": 90.008683,
    "completion_retry_total_selected_trips": 0,
    "completion_retry_total_two_cycle_build_time": 1.971079,
    "completion_retry_trigger_count": 1,
    "finish_columns": 218,
    "finish_exact_pricing_calls": 7,
    "finish_pricing_calls": 13,
    "finish_pricing_incomplete_nodes": 1,
    "finish_primal_bound": 744.848595,
    "finish_rmp_solves": 6,
    "finish_solving_time": 97.157486,
    "finish_status": "TIME_LIMIT",
    "instance": null,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/finalcap90_profile_timing_v2_apollo20_sector/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
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
