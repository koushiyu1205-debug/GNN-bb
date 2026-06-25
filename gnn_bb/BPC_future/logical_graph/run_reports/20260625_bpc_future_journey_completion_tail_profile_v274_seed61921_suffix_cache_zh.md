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
completion_retry_total_profile_generation_time = 118.845694
completion_retry_profile_timing_enabled_count = 0
completion_retry_profile_time_top = {}
completion_retry_profile_time_share_top = {}
completion_retry_cache_count_totals = {'direct_next_sortie_cache_hits': 0, 'direct_next_sortie_cache_misses': 3, 'generated_next_sorties_before_bound': 474106, 'generated_next_sorties_after_bound': 474106}
completion_retry_total_generated_sequences = 474106
completion_retry_total_evaluated_timed_trips = 863890
completion_retry_total_negative_journeys = 11
completion_retry_total_selected_trips = 2
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
    "added_journeys": 163,
    "addition_event_count": 31,
    "completion_retry_cache_count_totals": {
      "direct_next_sortie_cache_hits": 0,
      "direct_next_sortie_cache_misses": 3,
      "generated_next_sorties_after_bound": 474106,
      "generated_next_sorties_before_bound": 474106
    },
    "completion_retry_class": "completion_bound_time_limit_no_column_uncertified",
    "completion_retry_count": 3,
    "completion_retry_last": {
      "best_reduced_cost": 0.0,
      "bound_build_time": 3.385869,
      "candidate_trips": 236,
      "cg_iter": 32,
      "completion_bound_enabled": true,
      "direct_journey_label_next_sortie_cache_enabled": true,
      "direct_label_harvest_candidate_count": 0,
      "direct_label_harvest_selected_count": 0,
      "direct_label_harvest_selected_new_task_set_count": 0,
      "direct_label_harvest_selected_replacement_task_set_count": 0,
      "direct_label_profile_bound_check_time": 0.0,
      "direct_label_profile_bound_checks": 0,
      "direct_label_profile_completed_dedup_time": 0.0,
      "direct_label_profile_completed_process_time": 0.0,
      "direct_label_profile_completion_calls": 0,
      "direct_label_profile_completion_time": 0.0,
      "direct_label_profile_dominance_checks": 0,
      "direct_label_profile_dominance_time": 0.0,
      "direct_label_profile_extend_time": 0.0,
      "direct_label_profile_extension_attempts": 0,
      "direct_label_profile_label_create_time": 0.0,
      "direct_label_profile_next_sortie_calls": 0,
      "direct_label_profile_next_sortie_total_time": 0.0,
      "direct_label_profile_option_attempts": 0,
      "direct_label_profile_option_lookup_time": 0.0,
      "direct_label_profile_partial_bound_completion_route_time": 0.0,
      "direct_label_profile_partial_bound_cut_time": 0.0,
      "direct_label_profile_partial_bound_dual_sum_time": 0.0,
      "direct_label_profile_partial_bound_resource_pareto_time": 0.0,
      "direct_label_profile_partial_bound_unique_route_time": 0.0,
      "direct_label_profile_partial_bound_unique_task_time": 0.0,
      "direct_label_profile_partial_bucket_count": 0,
      "direct_label_profile_partial_bucket_label_count": 0,
      "direct_label_profile_partial_bucket_max_size": 0,
      "direct_label_profile_partial_bucket_mean_size": 0.0,
      "direct_label_profile_partial_heap_pops": 0,
      "direct_label_profile_pre_dominance_checks": 0,
      "direct_label_profile_pre_dominance_pruned": 0,
      "direct_label_profile_pre_dominance_time": 0.0,
      "direct_label_profile_priority_queue_time": 0.0,
      "direct_label_profile_resource_precheck_time": 0.0,
      "direct_label_profile_stream_callback_time": 0.0,
      "direct_label_profile_task_filter_time": 0.0,
      "direct_label_profile_timing_enabled": false,
      "direct_next_sortie_cache_hits": 0,
      "direct_next_sortie_cache_misses": 1,
      "evaluated_timed_trips": 247333,
      "exhausted": false,
      "expanded_labels_after_bound": 800,
      "expanded_labels_before_bound": 800,
      "generated_next_sorties_after_bound": 157170,
      "generated_next_sorties_before_bound": 157170,
      "generated_sequences": 157170,
      "global_certificate": false,
      "global_certificate_capable": true,
      "harvest_candidate_negative_count": 0,
      "harvest_selected_count": 0,
      "harvest_selected_new_task_set_count": 0,
      "harvest_selected_replacement_task_set_count": 0,
      "lb_mean_value": -115.119073759,
      "lb_min_value": -258.2863495,
      "lb_negative_state_count": 1225,
      "lb_pruned_labels": 0,
      "lb_state_count": 2541,
      "negative_journeys": 0,
      "pricing_kind": "exact_completion_bound_retry",
      "pricing_state": "INCOMPLETE_LIMIT",
      "pricing_time_limit": 20.0,
      "profile_generation_time": 21.840738,
      "reason": "time_limit",
      "selected_trips": 0,
      "two_cycle_blocked_extensions": 158095,
      "two_cycle_build_time": 3.319586,
      "two_cycle_enabled": true,
      "two_cycle_incompatible_queries": 0,
      "two_cycle_second_best_queries": 0,
      "two_cycle_state_count": 160083,
      "two_cycle_table_complete": true,
      "two_cycle_top2_replacements": 136016
    },
    "completion_retry_profile_count_totals": {
      "direct_label_profile_bound_checks": 0,
      "direct_label_profile_completion_calls": 0,
      "direct_label_profile_dominance_checks": 0,
      "direct_label_profile_extension_attempts": 0,
      "direct_label_profile_next_sortie_calls": 0,
      "direct_label_profile_option_attempts": 0,
      "direct_label_profile_partial_bucket_count": 0,
      "direct_label_profile_partial_bucket_label_count": 0,
      "direct_label_profile_partial_bucket_max_size": 0,
      "direct_label_profile_partial_heap_pops": 0,
      "direct_label_profile_pre_dominance_checks": 0,
      "direct_label_profile_pre_dominance_pruned": 0
    },
    "completion_retry_profile_time_share_top": {},
    "completion_retry_profile_time_top": {},
    "completion_retry_profile_time_totals": {
      "direct_label_profile_bound_check_time": 0.0,
      "direct_label_profile_completed_dedup_time": 0.0,
      "direct_label_profile_completed_process_time": 0.0,
      "direct_label_profile_completion_time": 0.0,
      "direct_label_profile_dominance_time": 0.0,
      "direct_label_profile_extend_time": 0.0,
      "direct_label_profile_label_create_time": 0.0,
      "direct_label_profile_next_sortie_total_time": 0.0,
      "direct_label_profile_option_lookup_time": 0.0,
      "direct_label_profile_partial_bound_completion_route_time": 0.0,
      "direct_label_profile_partial_bound_cut_time": 0.0,
      "direct_label_profile_partial_bound_dual_sum_time": 0.0,
      "direct_label_profile_partial_bound_resource_pareto_time": 0.0,
      "direct_label_profile_partial_bound_unique_route_time": 0.0,
      "direct_label_profile_partial_bound_unique_task_time": 0.0,
      "direct_label_profile_pre_dominance_time": 0.0,
      "direct_label_profile_priority_queue_time": 0.0,
      "direct_label_profile_resource_precheck_time": 0.0,
      "direct_label_profile_stream_callback_time": 0.0,
      "direct_label_profile_task_filter_time": 0.0
    },
    "completion_retry_profile_timing_enabled_count": 0,
    "completion_retry_total_bound_build_time": 10.261172,
    "completion_retry_total_evaluated_timed_trips": 863890,
    "completion_retry_total_expanded_after_bound": 2400,
    "completion_retry_total_expanded_before_bound": 2400,
    "completion_retry_total_generated_sequences": 474106,
    "completion_retry_total_lb_pruned": 0,
    "completion_retry_total_negative_journeys": 11,
    "completion_retry_total_profile_generation_time": 118.845694,
    "completion_retry_total_selected_trips": 2,
    "completion_retry_total_two_cycle_build_time": 10.062969,
    "completion_retry_trigger_count": 3,
    "finish_columns": 628,
    "finish_exact_pricing_calls": 10,
    "finish_pricing_calls": 42,
    "finish_pricing_incomplete_nodes": 1,
    "finish_primal_bound": 608.139688,
    "finish_rmp_solves": 32,
    "finish_solving_time": 194.850872,
    "finish_status": "TIME_LIMIT",
    "instance": null,
    "log_file": "BPC_future/results/logs_20260625_seed61921_suffix_cache_300/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json.jsonl",
    "new_journeys": 151,
    "pricing_event_count": 42,
    "pricing_kind_counts": {
      "exact": 7,
      "exact_completion_bound_retry": 3,
      "heuristic": 32
    },
    "pricing_state_counts": {
      "exact:FOUND_NEGATIVE:streaming_partial_negative_journey": 4,
      "exact:INCOMPLETE_LIMIT:weak_negative_journeys_filtered": 3,
      "exact_completion_bound_retry:FOUND_NEGATIVE:time_limit": 2,
      "exact_completion_bound_retry:INCOMPLETE_LIMIT:time_limit": 1,
      "heuristic:FOUND_NEGATIVE:streaming_partial_dp_negative_journey": 9,
      "heuristic:FOUND_NEGATIVE:streaming_partial_negative_journey": 23
    },
    "replacement_journeys": 12
  }
]
```
