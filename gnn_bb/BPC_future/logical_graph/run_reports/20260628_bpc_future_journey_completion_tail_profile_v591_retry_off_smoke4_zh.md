# Journey Completion-Bound Tail Profile

日期：2026-06-23

## 目的

读取 solver JSONL 日志，聚合 true-dual completion-bound final judge 的尾部状态。该脚本只读日志，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_completion_tail_profile = current
log_count = 4
completion_retry_class_counts = {'no_completion_bound_retry': 4}
incomplete_tail_count = 0
completion_retry_total_profile_generation_time = 0.0
completion_retry_profile_timing_enabled_count = 0
completion_retry_profile_time_top = {}
completion_retry_profile_time_share_top = {}
completion_retry_cache_count_totals = {'direct_next_sortie_cache_hits': 0, 'direct_next_sortie_cache_misses': 0, 'generated_next_sorties_before_bound': 0, 'generated_next_sorties_after_bound': 0}
completion_retry_harvest_count_totals = {'harvest_candidate_negative_count': 0, 'harvest_selected_count': 0, 'harvest_candidate_new_task_set_count': 0, 'harvest_selected_new_task_set_count': 0, 'harvest_selected_replacement_task_set_count': 0, 'harvest_candidate_priority_task_set_count': 0, 'harvest_selected_priority_task_set_count': 0, 'harvest_candidate_support_changing_count': 0, 'harvest_selected_support_changing_count': 0, 'harvest_fallback_fill_count': 0, 'harvest_fallback_fill_new_mask_count': 0, 'harvest_fallback_fill_replacement_count': 0, 'harvest_selected_weak_replacement_count': 0}
completion_retry_harvest_tail_class_counts = {'no_completion_bound_retry': 4}
completion_retry_total_generated_sequences = 0
completion_retry_total_evaluated_timed_trips = 0
completion_retry_total_negative_journeys = 0
completion_retry_total_selected_trips = 0
completion_retry_tail_min_fill_mode_count = 0
completion_retry_tail_min_fill_candidate_count = 0
completion_retry_tail_min_fill_applied_count = 0
completion_retry_tail_min_fill_optin_disabled_count = 0
completion_retry_tail_min_fill_reason_counts = {}
completion_retry_harvest_top_profile_records = [{"instance": null, "log_file": "BPC_future/results/20260628_retry_on_off_gate_smoke4_randomtw20/retry_off/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl", "finish_status": "TIME_LIMIT", "completion_retry_class": "no_completion_bound_retry", "harvest_tail_class": "no_completion_bound_retry", "profile_generation_time": 0, "harvest_candidate_negative_count": 0, "harvest_selected_count": 0, "harvest_candidate_new_task_set_count": 0, "harvest_selected_new_task_set_count": 0, "harvest_selected_replacement_task_set_count": 0}, {"instance": null, "log_file": "BPC_future/results/20260628_retry_on_off_gate_smoke4_randomtw20/retry_off/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json.jsonl", "finish_status": "TIME_LIMIT", "completion_retry_class": "no_completion_bound_retry", "harvest_tail_class": "no_completion_bound_retry", "profile_generation_time": 0, "harvest_candidate_negative_count": 0, "harvest_selected_count": 0, "harvest_candidate_new_task_set_count": 0, "harvest_selected_new_task_set_count": 0, "harvest_selected_replacement_task_set_count": 0}, {"instance": null, "log_file": "BPC_future/results/20260628_retry_on_off_gate_smoke4_randomtw20/retry_off/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json.jsonl", "finish_status": "TIME_LIMIT", "completion_retry_class": "no_completion_bound_retry", "harvest_tail_class": "no_completion_bound_retry", "profile_generation_time": 0, "harvest_candidate_negative_count": 0, "harvest_selected_count": 0, "harvest_candidate_new_task_set_count": 0, "harvest_selected_new_task_set_count": 0, "harvest_selected_replacement_task_set_count": 0}, {"instance": null, "log_file": "BPC_future/results/20260628_retry_on_off_gate_smoke4_randomtw20/retry_off/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json.jsonl", "finish_status": "TIME_LIMIT", "completion_retry_class": "no_completion_bound_retry", "harvest_tail_class": "no_completion_bound_retry", "profile_generation_time": 0, "harvest_candidate_negative_count": 0, "harvest_selected_count": 0, "harvest_candidate_new_task_set_count": 0, "harvest_selected_new_task_set_count": 0, "harvest_selected_replacement_task_set_count": 0}]
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## 解释

completion-bound tail 类型混合，需要按 records 逐条查看。

## Records

```json
[
  {
    "added_journeys": 101,
    "addition_event_count": 21,
    "completion_retry_cache_count_totals": {
      "direct_next_sortie_cache_hits": 0,
      "direct_next_sortie_cache_misses": 0,
      "generated_next_sorties_after_bound": 0,
      "generated_next_sorties_before_bound": 0
    },
    "completion_retry_class": "no_completion_bound_retry",
    "completion_retry_count": 0,
    "completion_retry_harvest_count_totals": {
      "harvest_candidate_negative_count": 0,
      "harvest_candidate_new_task_set_count": 0,
      "harvest_candidate_priority_task_set_count": 0,
      "harvest_candidate_support_changing_count": 0,
      "harvest_fallback_fill_count": 0,
      "harvest_fallback_fill_new_mask_count": 0,
      "harvest_fallback_fill_replacement_count": 0,
      "harvest_selected_count": 0,
      "harvest_selected_new_task_set_count": 0,
      "harvest_selected_priority_task_set_count": 0,
      "harvest_selected_replacement_task_set_count": 0,
      "harvest_selected_support_changing_count": 0,
      "harvest_selected_weak_replacement_count": 0
    },
    "completion_retry_harvest_tail_class": "no_completion_bound_retry",
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
    "finish_columns": 336,
    "finish_exact_pricing_calls": 8,
    "finish_pricing_calls": 30,
    "finish_pricing_incomplete_nodes": 1,
    "finish_primal_bound": 642.291219,
    "finish_rmp_solves": 22,
    "finish_solving_time": 265.206628,
    "finish_status": "TIME_LIMIT",
    "instance": null,
    "log_file": "BPC_future/results/20260628_retry_on_off_gate_smoke4_randomtw20/retry_off/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "new_journeys": 89,
    "pricing_event_count": 30,
    "pricing_kind_counts": {
      "exact": 7,
      "exact_retry": 1,
      "heuristic": 22
    },
    "pricing_state_counts": {
      "exact:FOUND_NEGATIVE:streaming_partial_negative_journey": 6,
      "exact:INCOMPLETE_LIMIT:weak_negative_journeys_filtered": 1,
      "exact_retry:INCOMPLETE_LIMIT:weak_negative_journeys_filtered": 1,
      "heuristic:FOUND_NEGATIVE:streaming_partial_negative_journey": 20,
      "heuristic:INCOMPLETE_LIMIT:partial_profile_scan_no_negative_journey": 2
    },
    "replacement_journeys": 12
  },
  {
    "added_journeys": 86,
    "addition_event_count": 16,
    "completion_retry_cache_count_totals": {
      "direct_next_sortie_cache_hits": 0,
      "direct_next_sortie_cache_misses": 0,
      "generated_next_sorties_after_bound": 0,
      "generated_next_sorties_before_bound": 0
    },
    "completion_retry_class": "no_completion_bound_retry",
    "completion_retry_count": 0,
    "completion_retry_harvest_count_totals": {
      "harvest_candidate_negative_count": 0,
      "harvest_candidate_new_task_set_count": 0,
      "harvest_candidate_priority_task_set_count": 0,
      "harvest_candidate_support_changing_count": 0,
      "harvest_fallback_fill_count": 0,
      "harvest_fallback_fill_new_mask_count": 0,
      "harvest_fallback_fill_replacement_count": 0,
      "harvest_selected_count": 0,
      "harvest_selected_new_task_set_count": 0,
      "harvest_selected_priority_task_set_count": 0,
      "harvest_selected_replacement_task_set_count": 0,
      "harvest_selected_support_changing_count": 0,
      "harvest_selected_weak_replacement_count": 0
    },
    "completion_retry_harvest_tail_class": "no_completion_bound_retry",
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
    "finish_columns": 319,
    "finish_exact_pricing_calls": 4,
    "finish_pricing_calls": 21,
    "finish_pricing_incomplete_nodes": 1,
    "finish_primal_bound": 577.168388,
    "finish_rmp_solves": 17,
    "finish_solving_time": 19.545949,
    "finish_status": "TIME_LIMIT",
    "instance": null,
    "log_file": "BPC_future/results/20260628_retry_on_off_gate_smoke4_randomtw20/retry_off/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json.jsonl",
    "new_journeys": 82,
    "pricing_event_count": 21,
    "pricing_kind_counts": {
      "exact": 4,
      "heuristic": 17
    },
    "pricing_state_counts": {
      "exact:FOUND_NEGATIVE:negative_journey": 3,
      "exact:LOCAL_NO_COLUMN_UNCERTIFIED:no_negative_journey": 1,
      "heuristic:FOUND_NEGATIVE:negative_journey": 7,
      "heuristic:FOUND_NEGATIVE:streaming_partial_dp_negative_journey": 6,
      "heuristic:INCOMPLETE_LIMIT:negative_journeys_already_in_pool": 4
    },
    "replacement_journeys": 4
  },
  {
    "added_journeys": 97,
    "addition_event_count": 18,
    "completion_retry_cache_count_totals": {
      "direct_next_sortie_cache_hits": 0,
      "direct_next_sortie_cache_misses": 0,
      "generated_next_sorties_after_bound": 0,
      "generated_next_sorties_before_bound": 0
    },
    "completion_retry_class": "no_completion_bound_retry",
    "completion_retry_count": 0,
    "completion_retry_harvest_count_totals": {
      "harvest_candidate_negative_count": 0,
      "harvest_candidate_new_task_set_count": 0,
      "harvest_candidate_priority_task_set_count": 0,
      "harvest_candidate_support_changing_count": 0,
      "harvest_fallback_fill_count": 0,
      "harvest_fallback_fill_new_mask_count": 0,
      "harvest_fallback_fill_replacement_count": 0,
      "harvest_selected_count": 0,
      "harvest_selected_new_task_set_count": 0,
      "harvest_selected_priority_task_set_count": 0,
      "harvest_selected_replacement_task_set_count": 0,
      "harvest_selected_support_changing_count": 0,
      "harvest_selected_weak_replacement_count": 0
    },
    "completion_retry_harvest_tail_class": "no_completion_bound_retry",
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
    "finish_columns": 372,
    "finish_exact_pricing_calls": 5,
    "finish_pricing_calls": 24,
    "finish_pricing_incomplete_nodes": 1,
    "finish_primal_bound": 620.675078,
    "finish_rmp_solves": 19,
    "finish_solving_time": 56.116426,
    "finish_status": "TIME_LIMIT",
    "instance": null,
    "log_file": "BPC_future/results/20260628_retry_on_off_gate_smoke4_randomtw20/retry_off/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json.jsonl",
    "new_journeys": 89,
    "pricing_event_count": 24,
    "pricing_kind_counts": {
      "exact": 4,
      "exact_retry": 1,
      "heuristic": 19
    },
    "pricing_state_counts": {
      "exact:FOUND_NEGATIVE:negative_journey": 1,
      "exact:FOUND_NEGATIVE:streaming_partial_negative_journey": 2,
      "exact:INCOMPLETE_LIMIT:weak_negative_journeys_filtered": 1,
      "exact_retry:INCOMPLETE_LIMIT:weak_negative_journeys_filtered": 1,
      "heuristic:FOUND_NEGATIVE:partial_negative_journey": 1,
      "heuristic:FOUND_NEGATIVE:streaming_partial_negative_journey": 14,
      "heuristic:INCOMPLETE_LIMIT:negative_journeys_already_in_pool": 1,
      "heuristic:INCOMPLETE_LIMIT:partial_profile_scan_no_negative_journey": 3
    },
    "replacement_journeys": 8
  },
  {
    "added_journeys": 133,
    "addition_event_count": 6,
    "completion_retry_cache_count_totals": {
      "direct_next_sortie_cache_hits": 0,
      "direct_next_sortie_cache_misses": 0,
      "generated_next_sorties_after_bound": 0,
      "generated_next_sorties_before_bound": 0
    },
    "completion_retry_class": "no_completion_bound_retry",
    "completion_retry_count": 0,
    "completion_retry_harvest_count_totals": {
      "harvest_candidate_negative_count": 0,
      "harvest_candidate_new_task_set_count": 0,
      "harvest_candidate_priority_task_set_count": 0,
      "harvest_candidate_support_changing_count": 0,
      "harvest_fallback_fill_count": 0,
      "harvest_fallback_fill_new_mask_count": 0,
      "harvest_fallback_fill_replacement_count": 0,
      "harvest_selected_count": 0,
      "harvest_selected_new_task_set_count": 0,
      "harvest_selected_priority_task_set_count": 0,
      "harvest_selected_replacement_task_set_count": 0,
      "harvest_selected_support_changing_count": 0,
      "harvest_selected_weak_replacement_count": 0
    },
    "completion_retry_harvest_tail_class": "no_completion_bound_retry",
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
    "finish_columns": 257,
    "finish_exact_pricing_calls": 4,
    "finish_pricing_calls": 11,
    "finish_pricing_incomplete_nodes": 1,
    "finish_primal_bound": 673.976604,
    "finish_rmp_solves": 7,
    "finish_solving_time": 6.538124,
    "finish_status": "TIME_LIMIT",
    "instance": null,
    "log_file": "BPC_future/results/20260628_retry_on_off_gate_smoke4_randomtw20/retry_off/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json.jsonl",
    "new_journeys": 104,
    "pricing_event_count": 11,
    "pricing_kind_counts": {
      "exact": 4,
      "heuristic": 7
    },
    "pricing_state_counts": {
      "exact:FOUND_NEGATIVE:negative_journey": 1,
      "exact:FOUND_NEGATIVE:streaming_partial_dp_negative_journey": 2,
      "exact:LOCAL_NO_COLUMN_UNCERTIFIED:no_negative_journey": 1,
      "heuristic:FOUND_NEGATIVE:streaming_partial_dp_negative_journey": 3,
      "heuristic:LOCAL_NO_COLUMN_UNCERTIFIED:no_negative_journey": 4
    },
    "replacement_journeys": 29
  }
]
```
