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
completion_retry_total_profile_generation_time = 89.722225
completion_retry_profile_timing_enabled_count = 0
completion_retry_profile_time_top = {}
completion_retry_total_generated_sequences = 2205902
completion_retry_total_evaluated_timed_trips = 716581
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
      "bound_build_time": 3.331365,
      "candidate_trips": 26964,
      "cg_iter": 37,
      "completion_bound_enabled": true,
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
      "profile_generation_time": 25.879291,
      "reason": "direct_label_no_negative_journey",
      "selected_trips": 0,
      "two_cycle_blocked_extensions": 158501,
      "two_cycle_build_time": 3.269504,
      "two_cycle_enabled": true,
      "two_cycle_incompatible_queries": 25729,
      "two_cycle_second_best_queries": 16025,
      "two_cycle_state_count": 160083,
      "two_cycle_table_complete": true,
      "two_cycle_top2_replacements": 127886
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
    "completion_retry_total_bound_build_time": 17.120603,
    "completion_retry_total_evaluated_timed_trips": 716581,
    "completion_retry_total_expanded_after_bound": 2203328,
    "completion_retry_total_expanded_before_bound": 3471058,
    "completion_retry_total_generated_sequences": 2205902,
    "completion_retry_total_lb_pruned": 1267729,
    "completion_retry_total_negative_journeys": 40,
    "completion_retry_total_profile_generation_time": 89.722225,
    "completion_retry_total_selected_trips": 7,
    "completion_retry_total_two_cycle_build_time": 16.804133,
    "completion_retry_trigger_count": 5,
    "finish_columns": 660,
    "finish_exact_pricing_calls": 17,
    "finish_pricing_calls": 54,
    "finish_pricing_incomplete_nodes": 0,
    "finish_primal_bound": 606.538972,
    "finish_rmp_solves": 37,
    "finish_solving_time": 207.510153,
    "finish_status": "OPTIMAL",
    "instance": null,
    "log_file": "BPC_future/results/journey_branch_holdout_sampling_plan_v253_full600_v252_target200_gap_20260624/diag_runs/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json.jsonl",
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
