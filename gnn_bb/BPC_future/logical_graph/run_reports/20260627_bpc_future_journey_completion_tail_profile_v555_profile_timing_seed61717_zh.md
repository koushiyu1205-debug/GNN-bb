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
completion_retry_total_profile_generation_time = 295.849556
completion_retry_profile_timing_enabled_count = 8
completion_retry_profile_time_top = {'direct_label_profile_next_sortie_total_time': 230.297112, 'direct_label_profile_extend_time': 39.467256, 'direct_label_profile_bound_check_time': 36.320264, 'direct_label_profile_completed_process_time': 34.594679, 'direct_label_profile_stream_callback_time': 30.579666, 'direct_label_profile_completion_time': 23.465228, 'direct_label_profile_task_filter_time': 22.263183, 'direct_label_profile_resource_precheck_time': 20.709032}
completion_retry_profile_time_share_top = {'direct_label_profile_next_sortie_total_time': 0.778426, 'direct_label_profile_extend_time': 0.133403, 'direct_label_profile_bound_check_time': 0.122766, 'direct_label_profile_completed_process_time': 0.116933, 'direct_label_profile_stream_callback_time': 0.103362, 'direct_label_profile_completion_time': 0.079315, 'direct_label_profile_task_filter_time': 0.075252, 'direct_label_profile_resource_precheck_time': 0.069999}
completion_retry_cache_count_totals = {'direct_next_sortie_cache_hits': 0, 'direct_next_sortie_cache_misses': 0, 'generated_next_sorties_before_bound': 7793987, 'generated_next_sorties_after_bound': 2706331}
completion_retry_harvest_count_totals = {'harvest_candidate_negative_count': 0, 'harvest_selected_count': 0, 'harvest_candidate_new_task_set_count': 0, 'harvest_selected_new_task_set_count': 0, 'harvest_selected_replacement_task_set_count': 0, 'harvest_candidate_priority_task_set_count': 0, 'harvest_selected_priority_task_set_count': 0, 'harvest_candidate_support_changing_count': 0, 'harvest_selected_support_changing_count': 0, 'harvest_fallback_fill_count': 0, 'harvest_fallback_fill_new_mask_count': 0, 'harvest_fallback_fill_replacement_count': 0, 'harvest_selected_weak_replacement_count': 0}
completion_retry_harvest_tail_class_counts = {'expensive_no_harvest_candidate': 1}
completion_retry_total_generated_sequences = 7793987
completion_retry_total_evaluated_timed_trips = 1431160
completion_retry_total_negative_journeys = 0
completion_retry_total_selected_trips = 0
completion_retry_tail_min_fill_mode_count = 9
completion_retry_tail_min_fill_candidate_count = 1
completion_retry_tail_min_fill_applied_count = 0
completion_retry_tail_min_fill_optin_disabled_count = 1
completion_retry_tail_min_fill_reason_counts = {'depth_gt_max': 8, 'optin_disabled': 1}
completion_retry_harvest_top_profile_records = [{"instance": null, "log_file": "BPC_future/results/20260627_v555_v545_profile_timing_expensive_no_candidate_seed61717_tasks20/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json.jsonl", "finish_status": null, "completion_retry_class": "completion_bound_time_limit_no_column_uncertified", "harvest_tail_class": "expensive_no_harvest_candidate", "profile_generation_time": 295.849556, "harvest_candidate_negative_count": 0, "harvest_selected_count": 0, "harvest_candidate_new_task_set_count": 0, "harvest_selected_new_task_set_count": 0, "harvest_selected_replacement_task_set_count": 0}]
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## 解释

completion-bound tail 主要表现为高 profile-generation 时间但没有可 harvest 的 true-RC 负列候选。下一步优先看 direct-label proof loop / completion-bound 剪枝成本，而不是降低返回门槛。

## Records

```json
[
  {
    "added_journeys": 239,
    "addition_event_count": 35,
    "completion_retry_cache_count_totals": {
      "direct_next_sortie_cache_hits": 0,
      "direct_next_sortie_cache_misses": 0,
      "generated_next_sorties_after_bound": 2706331,
      "generated_next_sorties_before_bound": 7793987
    },
    "completion_retry_class": "completion_bound_time_limit_no_column_uncertified",
    "completion_retry_count": 8,
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
    "completion_retry_harvest_tail_class": "expensive_no_harvest_candidate",
    "completion_retry_last": {
      "best_reduced_cost": -47.6928,
      "bound_build_time": 2.516203,
      "candidate_trips": 26473,
      "cg_iter": 4,
      "completion_bound_enabled": true,
      "direct_journey_label_next_sortie_cache_enabled": false,
      "direct_label_harvest_candidate_count": 0,
      "direct_label_harvest_min_fill": 10,
      "direct_label_harvest_selected_count": 0,
      "direct_label_harvest_selected_new_task_set_count": 0,
      "direct_label_harvest_selected_replacement_task_set_count": 0,
      "direct_label_profile_bound_check_time": 2.821168272,
      "direct_label_profile_bound_checks": 330661,
      "direct_label_profile_completed_dedup_time": 0.389864528,
      "direct_label_profile_completed_process_time": 12.221779675,
      "direct_label_profile_completion_calls": 185585,
      "direct_label_profile_completion_time": 3.306875864,
      "direct_label_profile_dominance_checks": 185585,
      "direct_label_profile_dominance_time": 0.636080554,
      "direct_label_profile_extend_time": 2.198510687,
      "direct_label_profile_extension_attempts": 3533240,
      "direct_label_profile_label_create_time": 0.243430512,
      "direct_label_profile_next_sortie_calls": 532,
      "direct_label_profile_next_sortie_total_time": 28.204067958,
      "direct_label_profile_option_attempts": 1480119,
      "direct_label_profile_option_lookup_time": 0.134160038,
      "direct_label_profile_partial_bound_completion_route_time": 0.393683167,
      "direct_label_profile_partial_bound_cut_time": 0.196581366,
      "direct_label_profile_partial_bound_dual_sum_time": 0.085379619,
      "direct_label_profile_partial_bound_resource_pareto_time": 0.0,
      "direct_label_profile_partial_bound_unique_route_time": 0.090541157,
      "direct_label_profile_partial_bound_unique_task_time": 1.101983876,
      "direct_label_profile_partial_bucket_count": 27725,
      "direct_label_profile_partial_bucket_label_count": 176851,
      "direct_label_profile_partial_bucket_max_size": 511,
      "direct_label_profile_partial_bucket_mean_size": 6.378755636,
      "direct_label_profile_partial_heap_pops": 186117,
      "direct_label_profile_pre_dominance_checks": 216067,
      "direct_label_profile_pre_dominance_pruned": 30635,
      "direct_label_profile_pre_dominance_time": 0.63996548,
      "direct_label_profile_priority_queue_time": 0.306898785,
      "direct_label_profile_resource_precheck_time": 1.665055451,
      "direct_label_profile_stream_callback_time": 11.700155942,
      "direct_label_profile_task_filter_time": 1.866787991,
      "direct_label_profile_timing_enabled": true,
      "direct_next_sortie_cache_hits": 0,
      "direct_next_sortie_cache_misses": 0,
      "evaluated_timed_trips": 231054,
      "exhausted": false,
      "expanded_labels_after_bound": 647340,
      "expanded_labels_before_bound": 792416,
      "generated_next_sorties_after_bound": 216220,
      "generated_next_sorties_before_bound": 361296,
      "generated_sequences": 361296,
      "global_certificate": false,
      "global_certificate_capable": true,
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
      "harvest_selected_weak_replacement_count": 0,
      "lb_mean_value": -83.895448698,
      "lb_min_value": -547.598172,
      "lb_negative_state_count": 848,
      "lb_pruned_labels": 145076,
      "lb_state_count": 2541,
      "negative_journeys": 0,
      "pricing_kind": "exact_completion_bound_retry",
      "pricing_state": "INCOMPLETE_LIMIT",
      "pricing_time_limit": 45.0,
      "profile_generation_time": 44.999534,
      "reason": "time_limit",
      "selected_trips": 0,
      "two_cycle_blocked_extensions": 99324,
      "two_cycle_build_time": 2.460829,
      "two_cycle_enabled": true,
      "two_cycle_incompatible_queries": 35228,
      "two_cycle_second_best_queries": 35228,
      "two_cycle_state_count": 160083,
      "two_cycle_table_complete": true,
      "two_cycle_top2_replacements": 107405
    },
    "completion_retry_profile_count_totals": {
      "direct_label_profile_bound_checks": 7421298,
      "direct_label_profile_completion_calls": 2333642,
      "direct_label_profile_dominance_checks": 2333642,
      "direct_label_profile_extension_attempts": 46149447,
      "direct_label_profile_next_sortie_calls": 74570,
      "direct_label_profile_option_attempts": 24046240,
      "direct_label_profile_partial_bucket_count": 1472534,
      "direct_label_profile_partial_bucket_label_count": 2308450,
      "direct_label_profile_partial_bucket_max_size": 511,
      "direct_label_profile_partial_heap_pops": 2407770,
      "direct_label_profile_pre_dominance_checks": 2680577,
      "direct_label_profile_pre_dominance_pruned": 372689
    },
    "completion_retry_profile_time_share_top": {
      "direct_label_profile_bound_check_time": 0.122766,
      "direct_label_profile_completed_process_time": 0.116933,
      "direct_label_profile_completion_time": 0.079315,
      "direct_label_profile_extend_time": 0.133403,
      "direct_label_profile_next_sortie_total_time": 0.778426,
      "direct_label_profile_resource_precheck_time": 0.069999,
      "direct_label_profile_stream_callback_time": 0.103362,
      "direct_label_profile_task_filter_time": 0.075252
    },
    "completion_retry_profile_time_top": {
      "direct_label_profile_bound_check_time": 36.320264,
      "direct_label_profile_completed_process_time": 34.594679,
      "direct_label_profile_completion_time": 23.465228,
      "direct_label_profile_extend_time": 39.467256,
      "direct_label_profile_next_sortie_total_time": 230.297112,
      "direct_label_profile_resource_precheck_time": 20.709032,
      "direct_label_profile_stream_callback_time": 30.579666,
      "direct_label_profile_task_filter_time": 22.263183
    },
    "completion_retry_profile_time_totals": {
      "direct_label_profile_bound_check_time": 36.320264,
      "direct_label_profile_completed_dedup_time": 3.121234,
      "direct_label_profile_completed_process_time": 34.594679,
      "direct_label_profile_completion_time": 23.465228,
      "direct_label_profile_dominance_time": 6.408504,
      "direct_label_profile_extend_time": 39.467256,
      "direct_label_profile_label_create_time": 4.925059,
      "direct_label_profile_next_sortie_total_time": 230.297112,
      "direct_label_profile_option_lookup_time": 1.989691,
      "direct_label_profile_partial_bound_completion_route_time": 4.796854,
      "direct_label_profile_partial_bound_cut_time": 2.331605,
      "direct_label_profile_partial_bound_dual_sum_time": 1.026501,
      "direct_label_profile_partial_bound_resource_pareto_time": 0.0,
      "direct_label_profile_partial_bound_unique_route_time": 1.066667,
      "direct_label_profile_partial_bound_unique_task_time": 11.372508,
      "direct_label_profile_pre_dominance_time": 5.964174,
      "direct_label_profile_priority_queue_time": 3.680774,
      "direct_label_profile_resource_precheck_time": 20.709032,
      "direct_label_profile_stream_callback_time": 30.579666,
      "direct_label_profile_task_filter_time": 22.263183
    },
    "completion_retry_profile_timing_enabled_count": 8,
    "completion_retry_tail_min_fill_applied_count": 0,
    "completion_retry_tail_min_fill_candidate_count": 1,
    "completion_retry_tail_min_fill_last": {
      "completion_bound_diverse_harvest_tail_min_fill_applied": false,
      "completion_bound_diverse_harvest_tail_min_fill_audit_enabled": true,
      "completion_bound_diverse_harvest_tail_min_fill_base": 10,
      "completion_bound_diverse_harvest_tail_min_fill_candidate": false,
      "completion_bound_diverse_harvest_tail_min_fill_enabled": false,
      "completion_bound_diverse_harvest_tail_min_fill_final_probe_only": true,
      "completion_bound_diverse_harvest_tail_min_fill_max_depth": 0,
      "completion_bound_diverse_harvest_tail_min_fill_reason": "depth_gt_max",
      "completion_bound_diverse_harvest_tail_min_fill_target": 4
    },
    "completion_retry_tail_min_fill_mode_count": 9,
    "completion_retry_tail_min_fill_optin_disabled_count": 1,
    "completion_retry_tail_min_fill_reason_counts": {
      "depth_gt_max": 8,
      "optin_disabled": 1
    },
    "completion_retry_total_bound_build_time": 20.425304,
    "completion_retry_total_evaluated_timed_trips": 1431160,
    "completion_retry_total_expanded_after_bound": 5195236,
    "completion_retry_total_expanded_before_bound": 10282892,
    "completion_retry_total_generated_sequences": 7793987,
    "completion_retry_total_lb_pruned": 5087656,
    "completion_retry_total_negative_journeys": 0,
    "completion_retry_total_profile_generation_time": 295.849556,
    "completion_retry_total_selected_trips": 0,
    "completion_retry_total_two_cycle_build_time": 19.986204,
    "completion_retry_trigger_count": 9,
    "finish_columns": null,
    "finish_exact_pricing_calls": null,
    "finish_pricing_calls": null,
    "finish_pricing_incomplete_nodes": null,
    "finish_primal_bound": null,
    "finish_rmp_solves": null,
    "finish_solving_time": null,
    "finish_status": null,
    "instance": null,
    "log_file": "BPC_future/results/20260627_v555_v545_profile_timing_expensive_no_candidate_seed61717_tasks20/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json.jsonl",
    "new_journeys": 220,
    "pricing_event_count": 79,
    "pricing_kind_counts": {
      "exact": 27,
      "exact_completion_bound_retry": 8,
      "heuristic": 44
    },
    "pricing_state_counts": {
      "exact:FOUND_NEGATIVE:negative_journey": 5,
      "exact:FOUND_NEGATIVE:streaming_partial_negative_journey": 13,
      "exact:INCOMPLETE_LIMIT:weak_negative_journeys_filtered": 9,
      "exact_completion_bound_retry:CERTIFIED_NO_NEGATIVE:direct_label_no_negative_journey": 6,
      "exact_completion_bound_retry:INCOMPLETE_LIMIT:time_limit": 2,
      "heuristic:FOUND_NEGATIVE:partial_negative_journey": 3,
      "heuristic:FOUND_NEGATIVE:streaming_partial_dp_negative_journey": 1,
      "heuristic:FOUND_NEGATIVE:streaming_partial_negative_journey": 23,
      "heuristic:INCOMPLETE_LIMIT:negative_journeys_already_in_pool": 1,
      "heuristic:INCOMPLETE_LIMIT:partial_profile_scan_no_negative_journey": 14,
      "heuristic:INCOMPLETE_LIMIT:profile_dp_incomplete": 2
    },
    "replacement_journeys": 19
  }
]
```
