# Journey Completion-Bound Tail Profile

日期：2026-06-23

## 目的

读取 solver JSONL 日志，聚合 true-dual completion-bound final judge 的尾部状态。该脚本只读日志，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_completion_tail_profile = current
log_count = 1
completion_retry_class_counts = {'completion_bound_certified_no_negative': 1}
incomplete_tail_count = 0
completion_retry_total_profile_generation_time = 65.415737
completion_retry_profile_timing_enabled_count = 0
completion_retry_profile_time_top = {}
completion_retry_profile_time_share_top = {}
completion_retry_cache_count_totals = {'direct_next_sortie_cache_hits': 0, 'direct_next_sortie_cache_misses': 0, 'generated_next_sorties_before_bound': 1531696, 'generated_next_sorties_after_bound': 449271}
completion_retry_total_generated_sequences = 1531696
completion_retry_total_evaluated_timed_trips = 302510
completion_retry_total_negative_journeys = 9
completion_retry_total_selected_trips = 2
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## 解释

已有 certified no-negative 样本，可对比成功证书与失败尾部的剪枝字段。

## Records

```json
[
  {
    "added_journeys": 160,
    "addition_event_count": 32,
    "completion_retry_cache_count_totals": {
      "direct_next_sortie_cache_hits": 0,
      "direct_next_sortie_cache_misses": 0,
      "generated_next_sorties_after_bound": 449271,
      "generated_next_sorties_before_bound": 1531696
    },
    "completion_retry_class": "completion_bound_certified_no_negative",
    "completion_retry_count": 2,
    "completion_retry_last": {
      "best_reduced_cost": 0.0,
      "bound_build_time": 3.617657,
      "candidate_trips": 20364,
      "cg_iter": 33,
      "completion_bound_enabled": true,
      "direct_journey_label_next_sortie_cache_enabled": false,
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
      "direct_next_sortie_cache_misses": 0,
      "evaluated_timed_trips": 141014,
      "exhausted": true,
      "expanded_labels_after_bound": 439130,
      "expanded_labels_before_bound": 1216740,
      "generated_next_sorties_after_bound": 176666,
      "generated_next_sorties_before_bound": 954276,
      "generated_sequences": 954276,
      "global_certificate": true,
      "global_certificate_capable": true,
      "harvest_candidate_negative_count": 0,
      "harvest_selected_count": 0,
      "harvest_selected_new_task_set_count": 0,
      "harvest_selected_replacement_task_set_count": 0,
      "lb_mean_value": -115.751854323,
      "lb_min_value": -260.3896385,
      "lb_negative_state_count": 1223,
      "lb_pruned_labels": 777610,
      "lb_state_count": 2541,
      "negative_journeys": 0,
      "pricing_kind": "exact_completion_bound_retry",
      "pricing_state": "CERTIFIED_NO_NEGATIVE",
      "pricing_time_limit": 45.0,
      "profile_generation_time": 20.397178,
      "reason": "direct_label_no_negative_journey",
      "selected_trips": 0,
      "two_cycle_blocked_extensions": 158324,
      "two_cycle_build_time": 3.554623,
      "two_cycle_enabled": true,
      "two_cycle_incompatible_queries": 17676,
      "two_cycle_second_best_queries": 11215,
      "two_cycle_state_count": 160083,
      "two_cycle_table_complete": true,
      "two_cycle_top2_replacements": 125828
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
    "completion_retry_total_bound_build_time": 7.294932,
    "completion_retry_total_evaluated_timed_trips": 302510,
    "completion_retry_total_expanded_after_bound": 999235,
    "completion_retry_total_expanded_before_bound": 2081660,
    "completion_retry_total_generated_sequences": 1531696,
    "completion_retry_total_lb_pruned": 1082425,
    "completion_retry_total_negative_journeys": 9,
    "completion_retry_total_profile_generation_time": 65.415737,
    "completion_retry_total_selected_trips": 2,
    "completion_retry_total_two_cycle_build_time": 7.167299,
    "completion_retry_trigger_count": 2,
    "finish_columns": 625,
    "finish_exact_pricing_calls": 8,
    "finish_pricing_calls": 41,
    "finish_pricing_incomplete_nodes": 0,
    "finish_primal_bound": 606.538972,
    "finish_rmp_solves": 33,
    "finish_solving_time": 129.509272,
    "finish_status": "OPTIMAL",
    "instance": null,
    "log_file": "BPC_future/results/logs_20260625_seed61921_cb_harvest_minfill4_forceexit_220/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json.jsonl",
    "new_journeys": 148,
    "pricing_event_count": 41,
    "pricing_kind_counts": {
      "exact": 6,
      "exact_completion_bound_retry": 2,
      "heuristic": 33
    },
    "pricing_state_counts": {
      "exact:FOUND_NEGATIVE:streaming_partial_negative_journey": 4,
      "exact:INCOMPLETE_LIMIT:weak_negative_journeys_filtered": 2,
      "exact_completion_bound_retry:CERTIFIED_NO_NEGATIVE:direct_label_no_negative_journey": 1,
      "exact_completion_bound_retry:FOUND_NEGATIVE:time_limit": 1,
      "heuristic:FOUND_NEGATIVE:streaming_partial_dp_negative_journey": 9,
      "heuristic:FOUND_NEGATIVE:streaming_partial_negative_journey": 24
    },
    "replacement_journeys": 12
  }
]
```
