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
completion_retry_total_profile_generation_time = 61.615033
completion_retry_profile_timing_enabled_count = 0
completion_retry_profile_time_top = {}
completion_retry_profile_time_share_top = {}
completion_retry_cache_count_totals = {'direct_next_sortie_cache_hits': 0, 'direct_next_sortie_cache_misses': 0, 'generated_next_sorties_before_bound': 891491, 'generated_next_sorties_after_bound': 670940}
completion_retry_total_generated_sequences = 891491
completion_retry_total_evaluated_timed_trips = 518622
completion_retry_total_negative_journeys = 30
completion_retry_total_selected_trips = 5
completion_retry_tail_min_fill_mode_count = 4
completion_retry_tail_min_fill_candidate_count = 4
completion_retry_tail_min_fill_applied_count = 0
completion_retry_tail_min_fill_optin_disabled_count = 4
completion_retry_tail_min_fill_reason_counts = {'optin_disabled': 4}
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
    "added_journeys": 180,
    "addition_event_count": 32,
    "completion_retry_cache_count_totals": {
      "direct_next_sortie_cache_hits": 0,
      "direct_next_sortie_cache_misses": 0,
      "generated_next_sorties_after_bound": 670940,
      "generated_next_sorties_before_bound": 891491
    },
    "completion_retry_class": "completion_bound_time_limit_no_column_uncertified",
    "completion_retry_count": 4,
    "completion_retry_last": {
      "best_reduced_cost": 0.0,
      "bound_build_time": 3.371115,
      "candidate_trips": 22635,
      "cg_iter": 33,
      "completion_bound_enabled": true,
      "direct_journey_label_next_sortie_cache_enabled": false,
      "direct_label_harvest_candidate_count": 0,
      "direct_label_harvest_min_fill": 10,
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
      "direct_next_sortie_cache_misses": 0,
      "evaluated_timed_trips": 190814,
      "exhausted": false,
      "expanded_labels_after_bound": 559850,
      "expanded_labels_before_bound": 619057,
      "generated_next_sorties_after_bound": 232769,
      "generated_next_sorties_before_bound": 291976,
      "generated_sequences": 291976,
      "global_certificate": false,
      "global_certificate_capable": true,
      "harvest_candidate_negative_count": 0,
      "harvest_selected_count": 0,
      "harvest_selected_new_task_set_count": 0,
      "harvest_selected_replacement_task_set_count": 0,
      "lb_mean_value": -114.822538471,
      "lb_min_value": -257.2213115,
      "lb_negative_state_count": 1225,
      "lb_pruned_labels": 59207,
      "lb_state_count": 2541,
      "negative_journeys": 0,
      "pricing_kind": "exact_completion_bound_retry",
      "pricing_state": "INCOMPLETE_LIMIT",
      "pricing_time_limit": 20.0,
      "profile_generation_time": 20.079668,
      "reason": "time_limit",
      "selected_trips": 0,
      "two_cycle_blocked_extensions": 155912,
      "two_cycle_build_time": 3.305762,
      "two_cycle_enabled": true,
      "two_cycle_incompatible_queries": 25320,
      "two_cycle_second_best_queries": 15634,
      "two_cycle_state_count": 160083,
      "two_cycle_table_complete": true,
      "two_cycle_top2_replacements": 131018
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
    "completion_retry_tail_min_fill_applied_count": 0,
    "completion_retry_tail_min_fill_candidate_count": 4,
    "completion_retry_tail_min_fill_last": {
      "completion_bound_diverse_harvest_tail_min_fill_applied": false,
      "completion_bound_diverse_harvest_tail_min_fill_audit_enabled": true,
      "completion_bound_diverse_harvest_tail_min_fill_base": 10,
      "completion_bound_diverse_harvest_tail_min_fill_candidate": true,
      "completion_bound_diverse_harvest_tail_min_fill_enabled": false,
      "completion_bound_diverse_harvest_tail_min_fill_final_probe_only": true,
      "completion_bound_diverse_harvest_tail_min_fill_max_depth": 0,
      "completion_bound_diverse_harvest_tail_min_fill_reason": "optin_disabled",
      "completion_bound_diverse_harvest_tail_min_fill_target": 4
    },
    "completion_retry_tail_min_fill_mode_count": 4,
    "completion_retry_tail_min_fill_optin_disabled_count": 4,
    "completion_retry_tail_min_fill_reason_counts": {
      "optin_disabled": 4
    },
    "completion_retry_total_bound_build_time": 14.270542,
    "completion_retry_total_evaluated_timed_trips": 518622,
    "completion_retry_total_expanded_after_bound": 1539811,
    "completion_retry_total_expanded_before_bound": 1760363,
    "completion_retry_total_generated_sequences": 891491,
    "completion_retry_total_lb_pruned": 220551,
    "completion_retry_total_negative_journeys": 30,
    "completion_retry_total_profile_generation_time": 61.615033,
    "completion_retry_total_selected_trips": 5,
    "completion_retry_total_two_cycle_build_time": 13.869377,
    "completion_retry_trigger_count": 4,
    "finish_columns": 645,
    "finish_exact_pricing_calls": 13,
    "finish_pricing_calls": 46,
    "finish_pricing_incomplete_nodes": 1,
    "finish_primal_bound": 608.139688,
    "finish_rmp_solves": 33,
    "finish_solving_time": 149.361071,
    "finish_status": "TIME_LIMIT",
    "instance": null,
    "log_file": "BPC_future/results/journey_tail_minfill_ab_runbook_v340_from_v339_root_tail8_20260625/002_apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph/baseline/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json.jsonl",
    "new_journeys": 168,
    "pricing_event_count": 46,
    "pricing_kind_counts": {
      "exact": 8,
      "exact_completion_bound_retry": 4,
      "exact_same_dual_supplement": 1,
      "heuristic": 33
    },
    "pricing_state_counts": {
      "exact:FOUND_NEGATIVE:streaming_partial_negative_journey": 4,
      "exact:INCOMPLETE_LIMIT:weak_negative_journeys_filtered": 4,
      "exact_completion_bound_retry:FOUND_NEGATIVE:direct_label_partial_negative_journey": 3,
      "exact_completion_bound_retry:INCOMPLETE_LIMIT:time_limit": 1,
      "exact_same_dual_supplement:INCOMPLETE_LIMIT:time_limit": 1,
      "heuristic:FOUND_NEGATIVE:streaming_partial_dp_negative_journey": 9,
      "heuristic:FOUND_NEGATIVE:streaming_partial_negative_journey": 24
    },
    "replacement_journeys": 12
  }
]
```
