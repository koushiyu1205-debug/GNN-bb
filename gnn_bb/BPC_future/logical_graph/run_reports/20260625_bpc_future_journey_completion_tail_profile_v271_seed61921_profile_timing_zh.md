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
completion_retry_total_profile_generation_time = 100.789918
completion_retry_profile_timing_enabled_count = 5
completion_retry_profile_time_top = {'direct_label_profile_next_sortie_total_time': 76.864031, 'direct_label_profile_bound_check_time': 12.440164, 'direct_label_profile_extend_time': 10.626592, 'direct_label_profile_completion_time': 10.428588, 'direct_label_profile_pre_dominance_time': 7.626978, 'direct_label_profile_resource_precheck_time': 7.109272, 'direct_label_profile_completed_process_time': 6.092916, 'direct_label_profile_dominance_time': 6.086746}
completion_retry_profile_time_share_top = {'direct_label_profile_next_sortie_total_time': 0.762616, 'direct_label_profile_bound_check_time': 0.123427, 'direct_label_profile_extend_time': 0.105433, 'direct_label_profile_completion_time': 0.103469, 'direct_label_profile_pre_dominance_time': 0.075672, 'direct_label_profile_resource_precheck_time': 0.070536, 'direct_label_profile_completed_process_time': 0.060452, 'direct_label_profile_dominance_time': 0.06039}
completion_retry_total_generated_sequences = 2193243
completion_retry_total_evaluated_timed_trips = 715938
completion_retry_total_negative_journeys = 40
completion_retry_total_selected_trips = 7
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
    "added_journeys": 195,
    "addition_event_count": 36,
    "completion_retry_class": "completion_bound_certified_no_negative",
    "completion_retry_count": 5,
    "completion_retry_last": {
      "best_reduced_cost": 0.0,
      "bound_build_time": 3.373878,
      "candidate_trips": 26964,
      "cg_iter": 37,
      "completion_bound_enabled": true,
      "direct_label_harvest_candidate_count": 0,
      "direct_label_harvest_selected_count": 0,
      "direct_label_harvest_selected_new_task_set_count": 0,
      "direct_label_harvest_selected_replacement_task_set_count": 0,
      "direct_label_profile_bound_check_time": 3.947939523,
      "direct_label_profile_bound_checks": 1208990,
      "direct_label_profile_completed_dedup_time": 0.790504829,
      "direct_label_profile_completed_process_time": 1.28961886,
      "direct_label_profile_completion_calls": 210699,
      "direct_label_profile_completion_time": 2.510909272,
      "direct_label_profile_dominance_checks": 210699,
      "direct_label_profile_dominance_time": 1.583758783,
      "direct_label_profile_extend_time": 4.80179782,
      "direct_label_profile_extension_attempts": 3755100,
      "direct_label_profile_label_create_time": 0.669928874,
      "direct_label_profile_next_sortie_calls": 21078,
      "direct_label_profile_next_sortie_total_time": 23.641552106,
      "direct_label_profile_option_attempts": 2266696,
      "direct_label_profile_option_lookup_time": 0.184627133,
      "direct_label_profile_partial_bound_completion_route_time": 0.696736237,
      "direct_label_profile_partial_bound_cut_time": 0.205601858,
      "direct_label_profile_partial_bound_dual_sum_time": 0.109539882,
      "direct_label_profile_partial_bound_resource_pareto_time": 0.0,
      "direct_label_profile_partial_bound_unique_route_time": 0.122024009,
      "direct_label_profile_partial_bound_unique_task_time": 0.451200755,
      "direct_label_profile_partial_bucket_count": 345244,
      "direct_label_profile_partial_bucket_label_count": 219738,
      "direct_label_profile_partial_bucket_max_size": 738,
      "direct_label_profile_partial_bucket_mean_size": 0.636471597,
      "direct_label_profile_partial_heap_pops": 231777,
      "direct_label_profile_pre_dominance_checks": 235494,
      "direct_label_profile_pre_dominance_pruned": 25162,
      "direct_label_profile_pre_dominance_time": 2.025180212,
      "direct_label_profile_priority_queue_time": 0.333388645,
      "direct_label_profile_resource_precheck_time": 1.988132338,
      "direct_label_profile_stream_callback_time": 0.406509703,
      "direct_label_profile_task_filter_time": 1.119073929,
      "direct_label_profile_timing_enabled": true,
      "evaluated_timed_trips": 190401,
      "exhausted": true,
      "expanded_labels_after_bound": 591501,
      "expanded_labels_before_bound": 1589792,
      "generated_sequences": 1234152,
      "global_certificate": true,
      "global_certificate_capable": true,
      "harvest_candidate_negative_count": 0,
      "harvest_selected_count": 0,
      "harvest_selected_new_task_set_count": 0,
      "harvest_selected_replacement_task_set_count": 0,
      "lb_mean_value": -115.692333021,
      "lb_min_value": -260.5469045,
      "lb_negative_state_count": 1223,
      "lb_pruned_labels": 998291,
      "lb_state_count": 2541,
      "negative_journeys": 0,
      "pricing_kind": "exact_completion_bound_retry",
      "pricing_state": "CERTIFIED_NO_NEGATIVE",
      "pricing_time_limit": 45.0,
      "profile_generation_time": 29.21615,
      "reason": "direct_label_no_negative_journey",
      "selected_trips": 0,
      "two_cycle_blocked_extensions": 158501,
      "two_cycle_build_time": 3.309,
      "two_cycle_enabled": true,
      "two_cycle_incompatible_queries": 25729,
      "two_cycle_second_best_queries": 16025,
      "two_cycle_state_count": 160083,
      "two_cycle_table_complete": true,
      "two_cycle_top2_replacements": 127886
    },
    "completion_retry_profile_count_totals": {
      "direct_label_profile_bound_checks": 2087203,
      "direct_label_profile_completion_calls": 828615,
      "direct_label_profile_dominance_checks": 828615,
      "direct_label_profile_extension_attempts": 12940395,
      "direct_label_profile_next_sortie_calls": 21106,
      "direct_label_profile_option_attempts": 6521055,
      "direct_label_profile_partial_bucket_count": 361524,
      "direct_label_profile_partial_bucket_label_count": 798902,
      "direct_label_profile_partial_bucket_max_size": 738,
      "direct_label_profile_partial_heap_pops": 815964,
      "direct_label_profile_pre_dominance_checks": 935658,
      "direct_label_profile_pre_dominance_pruned": 106040
    },
    "completion_retry_profile_time_share_top": {
      "direct_label_profile_bound_check_time": 0.123427,
      "direct_label_profile_completed_process_time": 0.060452,
      "direct_label_profile_completion_time": 0.103469,
      "direct_label_profile_dominance_time": 0.06039,
      "direct_label_profile_extend_time": 0.105433,
      "direct_label_profile_next_sortie_total_time": 0.762616,
      "direct_label_profile_pre_dominance_time": 0.075672,
      "direct_label_profile_resource_precheck_time": 0.070536
    },
    "completion_retry_profile_time_top": {
      "direct_label_profile_bound_check_time": 12.440164,
      "direct_label_profile_completed_process_time": 6.092916,
      "direct_label_profile_completion_time": 10.428588,
      "direct_label_profile_dominance_time": 6.086746,
      "direct_label_profile_extend_time": 10.626592,
      "direct_label_profile_next_sortie_total_time": 76.864031,
      "direct_label_profile_pre_dominance_time": 7.626978,
      "direct_label_profile_resource_precheck_time": 7.109272
    },
    "completion_retry_profile_time_totals": {
      "direct_label_profile_bound_check_time": 12.440164,
      "direct_label_profile_completed_dedup_time": 2.36387,
      "direct_label_profile_completed_process_time": 6.092916,
      "direct_label_profile_completion_time": 10.428588,
      "direct_label_profile_dominance_time": 6.086746,
      "direct_label_profile_extend_time": 10.626592,
      "direct_label_profile_label_create_time": 1.270998,
      "direct_label_profile_next_sortie_total_time": 76.864031,
      "direct_label_profile_option_lookup_time": 0.553279,
      "direct_label_profile_partial_bound_completion_route_time": 3.02581,
      "direct_label_profile_partial_bound_cut_time": 0.804922,
      "direct_label_profile_partial_bound_dual_sum_time": 0.416935,
      "direct_label_profile_partial_bound_resource_pareto_time": 0.0,
      "direct_label_profile_partial_bound_unique_route_time": 0.473232,
      "direct_label_profile_partial_bound_unique_task_time": 1.67462,
      "direct_label_profile_pre_dominance_time": 7.626978,
      "direct_label_profile_priority_queue_time": 1.30626,
      "direct_label_profile_resource_precheck_time": 7.109272,
      "direct_label_profile_stream_callback_time": 3.373733,
      "direct_label_profile_task_filter_time": 3.804699
    },
    "completion_retry_profile_timing_enabled_count": 5,
    "completion_retry_total_bound_build_time": 17.847964,
    "completion_retry_total_evaluated_timed_trips": 715938,
    "completion_retry_total_expanded_after_bound": 2199463,
    "completion_retry_total_expanded_before_bound": 3458053,
    "completion_retry_total_generated_sequences": 2193243,
    "completion_retry_total_lb_pruned": 1258588,
    "completion_retry_total_negative_journeys": 40,
    "completion_retry_total_profile_generation_time": 100.789918,
    "completion_retry_total_selected_trips": 7,
    "completion_retry_total_two_cycle_build_time": 17.524669,
    "completion_retry_trigger_count": 5,
    "finish_columns": 660,
    "finish_exact_pricing_calls": 17,
    "finish_pricing_calls": 54,
    "finish_pricing_incomplete_nodes": 0,
    "finish_primal_bound": 606.538972,
    "finish_rmp_solves": 37,
    "finish_solving_time": 219.342332,
    "finish_status": "OPTIMAL",
    "instance": null,
    "log_file": "BPC_future/results/logs_20260625_seed61921_profile_timing_300/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json.jsonl",
    "new_journeys": 183,
    "pricing_event_count": 54,
    "pricing_kind_counts": {
      "exact": 10,
      "exact_completion_bound_retry": 5,
      "exact_hidden_negative_patrol": 1,
      "exact_same_dual_supplement": 1,
      "heuristic": 37
    },
    "pricing_state_counts": {
      "exact:FOUND_NEGATIVE:negative_journey": 1,
      "exact:FOUND_NEGATIVE:streaming_partial_negative_journey": 4,
      "exact:INCOMPLETE_LIMIT:weak_negative_journeys_filtered": 4,
      "exact:LOCAL_NO_COLUMN_UNCERTIFIED:no_negative_journey": 1,
      "exact_completion_bound_retry:CERTIFIED_NO_NEGATIVE:direct_label_no_negative_journey": 1,
      "exact_completion_bound_retry:FOUND_NEGATIVE:direct_label_partial_negative_journey": 4,
      "exact_hidden_negative_patrol:INCOMPLETE_LIMIT:time_limit": 1,
      "exact_same_dual_supplement:INCOMPLETE_LIMIT:time_limit": 1,
      "heuristic:FOUND_NEGATIVE:streaming_partial_dp_negative_journey": 9,
      "heuristic:FOUND_NEGATIVE:streaming_partial_negative_journey": 28
    },
    "replacement_journeys": 12
  }
]
```
