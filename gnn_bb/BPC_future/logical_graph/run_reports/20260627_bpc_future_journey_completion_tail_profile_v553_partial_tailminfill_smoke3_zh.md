# Journey Completion-Bound Tail Profile

日期：2026-06-23

## 目的

读取 solver JSONL 日志，聚合 true-dual completion-bound final judge 的尾部状态。该脚本只读日志，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_completion_tail_profile = current
log_count = 3
completion_retry_class_counts = {'completion_bound_found_negative': 1, 'no_completion_bound_retry': 2}
incomplete_tail_count = 0
completion_retry_total_profile_generation_time = 46.298308
completion_retry_profile_timing_enabled_count = 0
completion_retry_profile_time_top = {}
completion_retry_profile_time_share_top = {}
completion_retry_cache_count_totals = {'direct_next_sortie_cache_hits': 0, 'direct_next_sortie_cache_misses': 0, 'generated_next_sorties_before_bound': 245525, 'generated_next_sorties_after_bound': 245490}
completion_retry_total_generated_sequences = 245525
completion_retry_total_evaluated_timed_trips = 586504
completion_retry_total_negative_journeys = 5
completion_retry_total_selected_trips = 1
completion_retry_tail_min_fill_mode_count = 2
completion_retry_tail_min_fill_candidate_count = 2
completion_retry_tail_min_fill_applied_count = 2
completion_retry_tail_min_fill_optin_disabled_count = 0
completion_retry_tail_min_fill_reason_counts = {'applied': 2}
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## 解释

final judge 仍在承担昂贵 worker 职责，找到负列后应优先检查 harvesting 是否一次性返回足够正交列。

## Records

```json
[
  {
    "added_journeys": 96,
    "addition_event_count": 19,
    "completion_retry_cache_count_totals": {
      "direct_next_sortie_cache_hits": 0,
      "direct_next_sortie_cache_misses": 0,
      "generated_next_sorties_after_bound": 0,
      "generated_next_sorties_before_bound": 0
    },
    "completion_retry_class": "no_completion_bound_retry",
    "completion_retry_count": 0,
    "completion_retry_last": null,
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
      "direct_label_profile_bound_check_time": 0,
      "direct_label_profile_completed_dedup_time": 0,
      "direct_label_profile_completed_process_time": 0,
      "direct_label_profile_completion_time": 0,
      "direct_label_profile_dominance_time": 0,
      "direct_label_profile_extend_time": 0,
      "direct_label_profile_label_create_time": 0,
      "direct_label_profile_next_sortie_total_time": 0,
      "direct_label_profile_option_lookup_time": 0,
      "direct_label_profile_partial_bound_completion_route_time": 0,
      "direct_label_profile_partial_bound_cut_time": 0,
      "direct_label_profile_partial_bound_dual_sum_time": 0,
      "direct_label_profile_partial_bound_resource_pareto_time": 0,
      "direct_label_profile_partial_bound_unique_route_time": 0,
      "direct_label_profile_partial_bound_unique_task_time": 0,
      "direct_label_profile_pre_dominance_time": 0,
      "direct_label_profile_priority_queue_time": 0,
      "direct_label_profile_resource_precheck_time": 0,
      "direct_label_profile_stream_callback_time": 0,
      "direct_label_profile_task_filter_time": 0
    },
    "completion_retry_profile_timing_enabled_count": 0,
    "completion_retry_tail_min_fill_applied_count": 0,
    "completion_retry_tail_min_fill_candidate_count": 0,
    "completion_retry_tail_min_fill_last": null,
    "completion_retry_tail_min_fill_mode_count": 0,
    "completion_retry_tail_min_fill_optin_disabled_count": 0,
    "completion_retry_tail_min_fill_reason_counts": {},
    "completion_retry_total_bound_build_time": 0,
    "completion_retry_total_evaluated_timed_trips": 0,
    "completion_retry_total_expanded_after_bound": 0,
    "completion_retry_total_expanded_before_bound": 0,
    "completion_retry_total_generated_sequences": 0,
    "completion_retry_total_lb_pruned": 0,
    "completion_retry_total_negative_journeys": 0,
    "completion_retry_total_profile_generation_time": 0,
    "completion_retry_total_selected_trips": 0,
    "completion_retry_total_two_cycle_build_time": 0,
    "completion_retry_trigger_count": 0,
    "finish_columns": null,
    "finish_exact_pricing_calls": null,
    "finish_pricing_calls": null,
    "finish_pricing_incomplete_nodes": null,
    "finish_primal_bound": null,
    "finish_rmp_solves": null,
    "finish_solving_time": null,
    "finish_status": null,
    "instance": null,
    "log_file": "BPC_future/results/20260627_v553_v545_tail_minfill_depth4_smoke3_tasks20/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "new_journeys": 87,
    "pricing_event_count": 24,
    "pricing_kind_counts": {
      "exact": 4,
      "heuristic": 20
    },
    "pricing_state_counts": {
      "exact:FOUND_NEGATIVE:streaming_partial_negative_journey": 4,
      "heuristic:FOUND_NEGATIVE:streaming_partial_negative_journey": 18,
      "heuristic:INCOMPLETE_LIMIT:partial_profile_scan_no_negative_journey": 2
    },
    "replacement_journeys": 9
  },
  {
    "added_journeys": 148,
    "addition_event_count": 34,
    "completion_retry_cache_count_totals": {
      "direct_next_sortie_cache_hits": 0,
      "direct_next_sortie_cache_misses": 0,
      "generated_next_sorties_after_bound": 0,
      "generated_next_sorties_before_bound": 0
    },
    "completion_retry_class": "no_completion_bound_retry",
    "completion_retry_count": 0,
    "completion_retry_last": null,
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
      "direct_label_profile_bound_check_time": 0,
      "direct_label_profile_completed_dedup_time": 0,
      "direct_label_profile_completed_process_time": 0,
      "direct_label_profile_completion_time": 0,
      "direct_label_profile_dominance_time": 0,
      "direct_label_profile_extend_time": 0,
      "direct_label_profile_label_create_time": 0,
      "direct_label_profile_next_sortie_total_time": 0,
      "direct_label_profile_option_lookup_time": 0,
      "direct_label_profile_partial_bound_completion_route_time": 0,
      "direct_label_profile_partial_bound_cut_time": 0,
      "direct_label_profile_partial_bound_dual_sum_time": 0,
      "direct_label_profile_partial_bound_resource_pareto_time": 0,
      "direct_label_profile_partial_bound_unique_route_time": 0,
      "direct_label_profile_partial_bound_unique_task_time": 0,
      "direct_label_profile_pre_dominance_time": 0,
      "direct_label_profile_priority_queue_time": 0,
      "direct_label_profile_resource_precheck_time": 0,
      "direct_label_profile_stream_callback_time": 0,
      "direct_label_profile_task_filter_time": 0
    },
    "completion_retry_profile_timing_enabled_count": 0,
    "completion_retry_tail_min_fill_applied_count": 0,
    "completion_retry_tail_min_fill_candidate_count": 0,
    "completion_retry_tail_min_fill_last": null,
    "completion_retry_tail_min_fill_mode_count": 0,
    "completion_retry_tail_min_fill_optin_disabled_count": 0,
    "completion_retry_tail_min_fill_reason_counts": {},
    "completion_retry_total_bound_build_time": 0,
    "completion_retry_total_evaluated_timed_trips": 0,
    "completion_retry_total_expanded_after_bound": 0,
    "completion_retry_total_expanded_before_bound": 0,
    "completion_retry_total_generated_sequences": 0,
    "completion_retry_total_lb_pruned": 0,
    "completion_retry_total_negative_journeys": 0,
    "completion_retry_total_profile_generation_time": 0,
    "completion_retry_total_selected_trips": 0,
    "completion_retry_total_two_cycle_build_time": 0,
    "completion_retry_trigger_count": 0,
    "finish_columns": null,
    "finish_exact_pricing_calls": null,
    "finish_pricing_calls": null,
    "finish_pricing_incomplete_nodes": null,
    "finish_primal_bound": null,
    "finish_rmp_solves": null,
    "finish_solving_time": null,
    "finish_status": null,
    "instance": null,
    "log_file": "BPC_future/results/20260627_v553_v545_tail_minfill_depth4_smoke3_tasks20/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json.jsonl",
    "new_journeys": 141,
    "pricing_event_count": 38,
    "pricing_kind_counts": {
      "exact": 3,
      "heuristic": 35
    },
    "pricing_state_counts": {
      "exact:FOUND_NEGATIVE:streaming_partial_negative_journey": 3,
      "heuristic:FOUND_NEGATIVE:streaming_partial_negative_journey": 35
    },
    "replacement_journeys": 7
  },
  {
    "added_journeys": 120,
    "addition_event_count": 17,
    "completion_retry_cache_count_totals": {
      "direct_next_sortie_cache_hits": 0,
      "direct_next_sortie_cache_misses": 0,
      "generated_next_sorties_after_bound": 245490,
      "generated_next_sorties_before_bound": 245525
    },
    "completion_retry_class": "completion_bound_found_negative",
    "completion_retry_count": 1,
    "completion_retry_last": {
      "best_reduced_cost": -20.939633182,
      "bound_build_time": 2.822493,
      "candidate_trips": 106,
      "cg_iter": 15,
      "completion_bound_enabled": true,
      "direct_journey_label_next_sortie_cache_enabled": false,
      "direct_label_harvest_candidate_count": 4312,
      "direct_label_harvest_min_fill": 4,
      "direct_label_harvest_selected_count": 5,
      "direct_label_harvest_selected_new_task_set_count": 5,
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
      "evaluated_timed_trips": 586504,
      "exhausted": false,
      "expanded_labels_after_bound": 791197,
      "expanded_labels_before_bound": 791232,
      "generated_next_sorties_after_bound": 245490,
      "generated_next_sorties_before_bound": 245525,
      "generated_sequences": 245525,
      "global_certificate": false,
      "global_certificate_capable": true,
      "harvest_candidate_negative_count": 4312,
      "harvest_selected_count": 5,
      "harvest_selected_new_task_set_count": 5,
      "harvest_selected_replacement_task_set_count": 0,
      "lb_mean_value": -50.94827473,
      "lb_min_value": -290.893235545,
      "lb_negative_state_count": 1024,
      "lb_pruned_labels": 35,
      "lb_state_count": 2541,
      "negative_journeys": 5,
      "pricing_kind": "exact_completion_bound_retry",
      "pricing_state": "FOUND_NEGATIVE",
      "pricing_time_limit": 45.0,
      "profile_generation_time": 46.298308,
      "reason": "time_limit",
      "selected_trips": 1,
      "two_cycle_blocked_extensions": 97526,
      "two_cycle_build_time": 2.769334,
      "two_cycle_enabled": true,
      "two_cycle_incompatible_queries": 15007,
      "two_cycle_second_best_queries": 15007,
      "two_cycle_state_count": 160083,
      "two_cycle_table_complete": true,
      "two_cycle_top2_replacements": 139271
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
    "completion_retry_tail_min_fill_applied_count": 2,
    "completion_retry_tail_min_fill_candidate_count": 2,
    "completion_retry_tail_min_fill_last": {
      "completion_bound_diverse_harvest_tail_min_fill_applied": true,
      "completion_bound_diverse_harvest_tail_min_fill_audit_enabled": true,
      "completion_bound_diverse_harvest_tail_min_fill_base": 10,
      "completion_bound_diverse_harvest_tail_min_fill_candidate": true,
      "completion_bound_diverse_harvest_tail_min_fill_enabled": true,
      "completion_bound_diverse_harvest_tail_min_fill_final_probe_only": true,
      "completion_bound_diverse_harvest_tail_min_fill_max_depth": 4,
      "completion_bound_diverse_harvest_tail_min_fill_reason": "applied",
      "completion_bound_diverse_harvest_tail_min_fill_target": 4
    },
    "completion_retry_tail_min_fill_mode_count": 2,
    "completion_retry_tail_min_fill_optin_disabled_count": 0,
    "completion_retry_tail_min_fill_reason_counts": {
      "applied": 2
    },
    "completion_retry_total_bound_build_time": 2.822493,
    "completion_retry_total_evaluated_timed_trips": 586504,
    "completion_retry_total_expanded_after_bound": 791197,
    "completion_retry_total_expanded_before_bound": 791232,
    "completion_retry_total_generated_sequences": 245525,
    "completion_retry_total_lb_pruned": 35,
    "completion_retry_total_negative_journeys": 5,
    "completion_retry_total_profile_generation_time": 46.298308,
    "completion_retry_total_selected_trips": 1,
    "completion_retry_total_two_cycle_build_time": 2.769334,
    "completion_retry_trigger_count": 2,
    "finish_columns": null,
    "finish_exact_pricing_calls": null,
    "finish_pricing_calls": null,
    "finish_pricing_incomplete_nodes": null,
    "finish_primal_bound": null,
    "finish_rmp_solves": null,
    "finish_solving_time": null,
    "finish_status": null,
    "instance": null,
    "log_file": "BPC_future/results/20260627_v553_v545_tail_minfill_depth4_smoke3_tasks20/logs/BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json.jsonl",
    "new_journeys": 115,
    "pricing_event_count": 24,
    "pricing_kind_counts": {
      "exact": 5,
      "exact_completion_bound_retry": 1,
      "heuristic": 18
    },
    "pricing_state_counts": {
      "exact:FOUND_NEGATIVE:streaming_partial_negative_journey": 3,
      "exact:INCOMPLETE_LIMIT:weak_negative_journeys_filtered": 2,
      "exact_completion_bound_retry:FOUND_NEGATIVE:time_limit": 1,
      "heuristic:FOUND_NEGATIVE:partial_negative_journey": 5,
      "heuristic:FOUND_NEGATIVE:streaming_partial_negative_journey": 8,
      "heuristic:INCOMPLETE_LIMIT:partial_profile_scan_no_negative_journey": 5
    },
    "replacement_journeys": 5
  }
]
```
