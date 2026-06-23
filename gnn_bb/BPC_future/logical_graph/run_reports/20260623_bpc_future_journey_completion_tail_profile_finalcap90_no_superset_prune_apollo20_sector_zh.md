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
completion_retry_total_profile_generation_time = 4.4017
completion_retry_profile_timing_enabled_count = 1
completion_retry_profile_time_top = {'direct_label_profile_next_sortie_total_time': 2.244003, 'direct_label_profile_extend_time': 0.571485, 'direct_label_profile_bound_check_time': 0.396147, 'direct_label_profile_resource_precheck_time': 0.246411, 'direct_label_profile_completion_time': 0.194704, 'direct_label_profile_task_filter_time': 0.156308, 'direct_label_profile_partial_bound_completion_route_time': 0.125848, 'direct_label_profile_completed_process_time': 0.062859}
completion_retry_total_generated_sequences = 112583
completion_retry_total_evaluated_timed_trips = 14316
completion_retry_total_negative_journeys = 0
completion_retry_total_selected_trips = 0
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
    "added_journeys": 140,
    "addition_event_count": 5,
    "completion_retry_class": "completion_bound_certified_no_negative",
    "completion_retry_count": 1,
    "completion_retry_last": {
      "best_reduced_cost": 0.0,
      "bound_build_time": 2.041252,
      "candidate_trips": 2102,
      "cg_iter": 6,
      "completion_bound_enabled": true,
      "direct_label_harvest_candidate_count": 0,
      "direct_label_harvest_selected_count": 0,
      "direct_label_harvest_selected_new_task_set_count": 0,
      "direct_label_harvest_selected_replacement_task_set_count": 0,
      "direct_label_profile_bound_check_time": 0.396147468,
      "direct_label_profile_bound_checks": 111462,
      "direct_label_profile_completed_dedup_time": 0.020750573,
      "direct_label_profile_completed_process_time": 0.062859385,
      "direct_label_profile_completion_calls": 27228,
      "direct_label_profile_completion_time": 0.194703962,
      "direct_label_profile_dominance_checks": 27228,
      "direct_label_profile_dominance_time": 0.05653014,
      "direct_label_profile_extend_time": 0.571485477,
      "direct_label_profile_extension_attempts": 557520,
      "direct_label_profile_label_create_time": 0.058442742,
      "direct_label_profile_next_sortie_calls": 1651,
      "direct_label_profile_next_sortie_total_time": 2.244003069,
      "direct_label_profile_option_attempts": 539505,
      "direct_label_profile_option_lookup_time": 0.034403193,
      "direct_label_profile_partial_bound_completion_route_time": 0.125847613,
      "direct_label_profile_partial_bound_cut_time": 0.024149493,
      "direct_label_profile_partial_bound_dual_sum_time": 0.011540675,
      "direct_label_profile_partial_bound_resource_pareto_time": 0.0,
      "direct_label_profile_partial_bound_unique_route_time": 0.01057077,
      "direct_label_profile_partial_bound_unique_task_time": 0.045742012,
      "direct_label_profile_partial_bucket_count": 32072,
      "direct_label_profile_partial_bucket_label_count": 27876,
      "direct_label_profile_partial_bucket_max_size": 60,
      "direct_label_profile_partial_bucket_mean_size": 0.869169369,
      "direct_label_profile_partial_heap_pops": 28879,
      "direct_label_profile_pre_dominance_checks": 25861,
      "direct_label_profile_pre_dominance_pruned": 1121,
      "direct_label_profile_pre_dominance_time": 0.042217542,
      "direct_label_profile_priority_queue_time": 0.035217145,
      "direct_label_profile_resource_precheck_time": 0.246410817,
      "direct_label_profile_stream_callback_time": 0.034347066,
      "direct_label_profile_task_filter_time": 0.156308229,
      "direct_label_profile_timing_enabled": true,
      "evaluated_timed_trips": 14316,
      "exhausted": true,
      "expanded_labels_after_bound": 55860,
      "expanded_labels_before_bound": 140094,
      "generated_sequences": 112583,
      "global_certificate": true,
      "global_certificate_capable": true,
      "harvest_candidate_negative_count": 0,
      "harvest_selected_count": 0,
      "harvest_selected_new_task_set_count": 0,
      "harvest_selected_replacement_task_set_count": 0,
      "lb_mean_value": -15.310976197,
      "lb_min_value": -281.05544775,
      "lb_negative_state_count": 789,
      "lb_pruned_labels": 84234,
      "lb_state_count": 2541,
      "negative_journeys": 0,
      "pricing_kind": "exact_completion_bound_retry",
      "pricing_state": "CERTIFIED_NO_NEGATIVE",
      "pricing_time_limit": 90.0,
      "profile_generation_time": 4.4017,
      "reason": "direct_label_no_negative_journey",
      "selected_trips": 0,
      "two_cycle_blocked_extensions": 92757,
      "two_cycle_build_time": 1.992573,
      "two_cycle_enabled": true,
      "two_cycle_incompatible_queries": 4198,
      "two_cycle_second_best_queries": 4198,
      "two_cycle_state_count": 160083,
      "two_cycle_table_complete": true,
      "two_cycle_top2_replacements": 82354
    },
    "completion_retry_profile_count_totals": {
      "direct_label_profile_bound_checks": 111462,
      "direct_label_profile_completion_calls": 27228,
      "direct_label_profile_dominance_checks": 27228,
      "direct_label_profile_extension_attempts": 557520,
      "direct_label_profile_next_sortie_calls": 1651,
      "direct_label_profile_option_attempts": 539505,
      "direct_label_profile_partial_bucket_count": 32072,
      "direct_label_profile_partial_bucket_label_count": 27876,
      "direct_label_profile_partial_bucket_max_size": 60,
      "direct_label_profile_partial_heap_pops": 28879,
      "direct_label_profile_pre_dominance_checks": 25861,
      "direct_label_profile_pre_dominance_pruned": 1121
    },
    "completion_retry_profile_time_top": {
      "direct_label_profile_bound_check_time": 0.396147,
      "direct_label_profile_completed_process_time": 0.062859,
      "direct_label_profile_completion_time": 0.194704,
      "direct_label_profile_extend_time": 0.571485,
      "direct_label_profile_next_sortie_total_time": 2.244003,
      "direct_label_profile_partial_bound_completion_route_time": 0.125848,
      "direct_label_profile_resource_precheck_time": 0.246411,
      "direct_label_profile_task_filter_time": 0.156308
    },
    "completion_retry_profile_time_totals": {
      "direct_label_profile_bound_check_time": 0.396147,
      "direct_label_profile_completed_dedup_time": 0.020751,
      "direct_label_profile_completed_process_time": 0.062859,
      "direct_label_profile_completion_time": 0.194704,
      "direct_label_profile_dominance_time": 0.05653,
      "direct_label_profile_extend_time": 0.571485,
      "direct_label_profile_label_create_time": 0.058443,
      "direct_label_profile_next_sortie_total_time": 2.244003,
      "direct_label_profile_option_lookup_time": 0.034403,
      "direct_label_profile_partial_bound_completion_route_time": 0.125848,
      "direct_label_profile_partial_bound_cut_time": 0.024149,
      "direct_label_profile_partial_bound_dual_sum_time": 0.011541,
      "direct_label_profile_partial_bound_resource_pareto_time": 0.0,
      "direct_label_profile_partial_bound_unique_route_time": 0.010571,
      "direct_label_profile_partial_bound_unique_task_time": 0.045742,
      "direct_label_profile_pre_dominance_time": 0.042218,
      "direct_label_profile_priority_queue_time": 0.035217,
      "direct_label_profile_resource_precheck_time": 0.246411,
      "direct_label_profile_stream_callback_time": 0.034347,
      "direct_label_profile_task_filter_time": 0.156308
    },
    "completion_retry_profile_timing_enabled_count": 1,
    "completion_retry_total_bound_build_time": 2.041252,
    "completion_retry_total_evaluated_timed_trips": 14316,
    "completion_retry_total_expanded_after_bound": 55860,
    "completion_retry_total_expanded_before_bound": 140094,
    "completion_retry_total_generated_sequences": 112583,
    "completion_retry_total_lb_pruned": 84234,
    "completion_retry_total_negative_journeys": 0,
    "completion_retry_total_profile_generation_time": 4.4017,
    "completion_retry_total_selected_trips": 0,
    "completion_retry_total_two_cycle_build_time": 1.992573,
    "completion_retry_trigger_count": 1,
    "finish_columns": 218,
    "finish_exact_pricing_calls": 7,
    "finish_pricing_calls": 13,
    "finish_pricing_incomplete_nodes": 0,
    "finish_primal_bound": 744.848595,
    "finish_rmp_solves": 6,
    "finish_solving_time": 11.288483,
    "finish_status": "OPTIMAL",
    "instance": null,
    "log_file": "BPC_future/results/journey_completion_tail_direction1_v154_20260623/finalcap90_no_superset_prune_apollo20_sector/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
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
      "exact_completion_bound_retry:CERTIFIED_NO_NEGATIVE:direct_label_no_negative_journey": 1,
      "exact_hidden_negative_patrol:INCOMPLETE_LIMIT:time_limit": 1,
      "heuristic:FOUND_NEGATIVE:negative_journey": 1,
      "heuristic:LOCAL_NO_COLUMN_UNCERTIFIED:no_negative_journey": 5
    },
    "replacement_journeys": 22
  }
]
```
