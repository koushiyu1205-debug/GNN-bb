# GAT Fixed Worker Post-Injection Trajectory Audit 报告

日期：2026-06-15

## 目的

只读分析固定 worker 注入目标列之后的 trajectory 后效。该脚本不运行 BPC、pricing 或 worker，
只读取已有 JSONL/CSV。

## 机器字段

```text
gat_fixed_worker_post_injection_trajectory_audit = current
status = audited
allow_partial = true
runbook_candidate_count = 9
record_count = 5
skipped_missing_log_count = 4
target_injection_success_count = 5
target_returned_journeys_sum = 14.0
target_active_changed_task_set_sum = 5.0
target_inactive_changed_task_set_sum = 9.0
immediate_objective_improved_count = 4
immediate_vs_baseline_same_iter_improved_count = 0
worker_next_objective_delta_sum = -22.666161018
worker_next_dual_l1_delta_mean = 22.3306103134
worker_next_objective_vs_baseline_same_iter_delta_sum = 166.43642
followup_pricing_event_sum = 72.0
followup_exact_event_sum = 36.0
followup_completion_retry_event_sum = 8.0
context_mismatch_skip_sum = 25.0
final_positive_roi_count = 4
final_negative_roi_count = 1
strict_trajectory_positive_count = 0
strict_trajectory_negative_count = 5
strict_trajectory_uncertain_count = 0
next_decision = retune_labels_from_long_horizon_trajectory_not_true_rc
all_checks_pass = true
```

## 核心发现

注入后一轮 RMP 虽可能本地下降，但相对 baseline 同迭代没有优势，需要把标签改成 post-injection trajectory impact。

## 结论

- `target_returned_journeys_sum` 衡量 GAT/worker 是否真的注入了 true-RC negative 列；
- `target_active_changed_task_set_sum` 衡量这些列是否立刻进入 active support；
- `worker_next_objective_delta_sum` 衡量注入后一轮 RMP 目标改善；
- `worker_next_dual_l1_delta_mean` 衡量注入后 dual 震荡；
- `context_mismatch_skip_sum` 衡量注入后 context 是否快速漂移；
- `final_*_roi_count` 是粗粒度长程统计；
- `strict_trajectory_*_count` 才是 GAT 训练更应使用的 ROI 标签口径：active 改变且相对 baseline 同迭代 objective 不变差。

## Records

```json
[
  {
    "baseline_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_exact_pricing_calls": 11,
    "baseline_jsonl_exists": true,
    "baseline_pricing_calls": 23,
    "baseline_rmp_solves": 12,
    "baseline_same_iter_dual_l1_delta": 346.229826,
    "baseline_same_iter_objective": 748.758409,
    "baseline_same_iter_objective_delta": -141.82419,
    "baseline_solving_time": 71.26332,
    "baseline_status": "TIME_LIMIT",
    "candidate_batch_count": 4,
    "candidate_batch_target_arc_option_sequences": [],
    "candidate_batch_target_sequences": [
      [
        8,
        11
      ],
      [
        2,
        4
      ],
      [
        2,
        3,
        18,
        11
      ],
      [
        5,
        1,
        2,
        15
      ]
    ],
    "certificate_effect": false,
    "exact_pricing_calls_delta": 0.0,
    "expected_context_hash": "d519291840dd7000",
    "final_roi_class": "positive_pricing_roi",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4",
    "official_bound_effect": false,
    "pricing_calls_delta": -1.0,
    "rmp_solves_delta": -1.0,
    "solving_time_delta": 18.81804600000001,
    "strict_trajectory_roi_class": "negative_worse_than_baseline_same_iter",
    "strict_trajectory_roi_label": 0,
    "strict_trajectory_roi_reason": "worse_than_baseline_same_iter_objective",
    "target_active_changed_task_set_count": 1,
    "target_added_journeys": 4,
    "target_addition_productivity_class": "active_replacement_task_set",
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->11:low_time:0",
      "11->0:low_time:0"
    ],
    "target_best_rc": -7.660825,
    "target_cg_iter": 1,
    "target_context_hash": "d519291840dd7000",
    "target_inactive_changed_task_set_count": 3,
    "target_injection_success": true,
    "target_new_journeys": 2,
    "target_replacement_journeys": 2,
    "target_returned_journeys": 4,
    "target_sequence": [
      8,
      11
    ],
    "target_signal_source": "expected_context_current_probe",
    "worker_context_mismatch_skips_after_injection": 8,
    "worker_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_exact_pricing_calls": 11,
    "worker_followup_completion_retry_events": 2,
    "worker_followup_exact_pricing_events": 10,
    "worker_followup_pricing_events": 20,
    "worker_followup_worker_events": 8,
    "worker_jsonl_exists": true,
    "worker_next_active_support_hash": "46c65721781b361f",
    "worker_next_cg_iter": 2,
    "worker_next_dual_l1_delta": 11.157344,
    "worker_next_dual_l1_vs_baseline_same_iter_delta": -335.072482,
    "worker_next_objective": 882.363323,
    "worker_next_objective_delta": -8.219276,
    "worker_next_objective_vs_baseline_same_iter_delta": 133.604914,
    "worker_pricing_calls": 22,
    "worker_rmp_solves": 11,
    "worker_solving_time": 90.081366,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3_batch4_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_exact_pricing_calls": 12,
    "baseline_jsonl_exists": true,
    "baseline_pricing_calls": 24,
    "baseline_rmp_solves": 12,
    "baseline_same_iter_dual_l1_delta": 74.215748802,
    "baseline_same_iter_objective": 656.998142,
    "baseline_same_iter_objective_delta": -39.213245304,
    "baseline_solving_time": 90.368522,
    "baseline_status": "TIME_LIMIT",
    "candidate_batch_count": 4,
    "candidate_batch_target_arc_option_sequences": [],
    "candidate_batch_target_sequences": [
      [
        5,
        1,
        2,
        18,
        3
      ],
      [
        2,
        1,
        15,
        3
      ],
      [
        2,
        18,
        3,
        15
      ],
      [
        5,
        18,
        15,
        3
      ]
    ],
    "certificate_effect": false,
    "exact_pricing_calls_delta": -2.0,
    "expected_context_hash": "67c11b5ec80925ec",
    "final_roi_class": "positive_exact_roi",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3_batch4",
    "official_bound_effect": false,
    "pricing_calls_delta": 2.0,
    "rmp_solves_delta": 4.0,
    "solving_time_delta": 0.1691069999999968,
    "strict_trajectory_roi_class": "negative_worse_than_baseline_same_iter",
    "strict_trajectory_roi_label": 0,
    "strict_trajectory_roi_reason": "worse_than_baseline_same_iter_objective",
    "target_active_changed_task_set_count": 1,
    "target_added_journeys": 4,
    "target_addition_productivity_class": "active_replacement_task_set",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->2:low_risk:2",
      "2->18:low_risk:2",
      "18->3:low_risk:2",
      "3->0:low_risk:2"
    ],
    "target_best_rc": -12.689023625,
    "target_cg_iter": 6,
    "target_context_hash": "67c11b5ec80925ec",
    "target_inactive_changed_task_set_count": 3,
    "target_injection_success": true,
    "target_new_journeys": 3,
    "target_replacement_journeys": 1,
    "target_returned_journeys": 4,
    "target_sequence": [
      5,
      1,
      2,
      18,
      3
    ],
    "target_signal_source": "expected_context_current_probe",
    "worker_context_mismatch_skips_after_injection": 6,
    "worker_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3_batch4_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_exact_pricing_calls": 10,
    "worker_followup_completion_retry_events": 2,
    "worker_followup_exact_pricing_events": 8,
    "worker_followup_pricing_events": 18,
    "worker_followup_worker_events": 6,
    "worker_jsonl_exists": true,
    "worker_next_active_support_hash": "6ec1a1507f27761d",
    "worker_next_cg_iter": 7,
    "worker_next_dual_l1_delta": 53.085807625,
    "worker_next_dual_l1_vs_baseline_same_iter_delta": -21.129941176999992,
    "worker_next_objective": 688.081981,
    "worker_next_objective_delta": -8.129405875,
    "worker_next_objective_vs_baseline_same_iter_delta": 31.08383900000001,
    "worker_pricing_calls": 26,
    "worker_rmp_solves": 16,
    "worker_solving_time": 90.537629,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_exact_pricing_calls": 12,
    "baseline_jsonl_exists": true,
    "baseline_pricing_calls": 24,
    "baseline_rmp_solves": 12,
    "baseline_same_iter_dual_l1_delta": 2.378605002,
    "baseline_same_iter_objective": 655.218275,
    "baseline_same_iter_objective_delta": -1.779866143,
    "baseline_solving_time": 90.532909,
    "baseline_status": "TIME_LIMIT",
    "candidate_batch_count": 1,
    "candidate_batch_target_arc_option_sequences": [],
    "candidate_batch_target_sequences": [],
    "certificate_effect": false,
    "exact_pricing_calls_delta": -2.0,
    "expected_context_hash": "409f65576794fa39",
    "final_roi_class": "positive_exact_roi",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13",
    "official_bound_effect": false,
    "pricing_calls_delta": 3.0,
    "rmp_solves_delta": 5.0,
    "solving_time_delta": -0.22235400000000993,
    "strict_trajectory_roi_class": "negative_worse_than_baseline_same_iter",
    "strict_trajectory_roi_label": 0,
    "strict_trajectory_roi_reason": "worse_than_baseline_same_iter_objective",
    "target_active_changed_task_set_count": 1,
    "target_added_journeys": 1,
    "target_addition_productivity_class": "active_replacement_task_set",
    "target_arc_option_sequence": [
      "0->17:low_time:0",
      "17->0:low_risk:2"
    ],
    "target_best_rc": -0.110294,
    "target_cg_iter": 7,
    "target_context_hash": "409f65576794fa39",
    "target_inactive_changed_task_set_count": 0,
    "target_injection_success": true,
    "target_new_journeys": 0,
    "target_replacement_journeys": 1,
    "target_returned_journeys": 1,
    "target_sequence": [
      17
    ],
    "target_signal_source": "expected_context_current_probe",
    "worker_context_mismatch_skips_after_injection": 5,
    "worker_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_exact_pricing_calls": 10,
    "worker_followup_completion_retry_events": 2,
    "worker_followup_exact_pricing_events": 7,
    "worker_followup_pricing_events": 17,
    "worker_followup_worker_events": 5,
    "worker_jsonl_exists": true,
    "worker_next_active_support_hash": "d67079b9dca84370",
    "worker_next_cg_iter": 8,
    "worker_next_dual_l1_delta": 0.756301718,
    "worker_next_dual_l1_vs_baseline_same_iter_delta": -1.622303284,
    "worker_next_objective": 656.935116,
    "worker_next_objective_delta": -0.063025143,
    "worker_next_objective_vs_baseline_same_iter_delta": 1.716841000000045,
    "worker_pricing_calls": 27,
    "worker_rmp_solves": 17,
    "worker_solving_time": 90.310555,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13_batch4_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_exact_pricing_calls": 11,
    "baseline_jsonl_exists": true,
    "baseline_pricing_calls": 23,
    "baseline_rmp_solves": 12,
    "baseline_same_iter_dual_l1_delta": 73.892698664,
    "baseline_same_iter_objective": 619.142683,
    "baseline_same_iter_objective_delta": -6.28528,
    "baseline_solving_time": 70.306612,
    "baseline_status": "TIME_LIMIT",
    "candidate_batch_count": 4,
    "candidate_batch_target_arc_option_sequences": [],
    "candidate_batch_target_sequences": [
      [
        8,
        20,
        13
      ],
      [
        5,
        9
      ],
      [
        2,
        15,
        3,
        12
      ],
      [
        18,
        15,
        3,
        12
      ]
    ],
    "certificate_effect": false,
    "exact_pricing_calls_delta": 0.0,
    "expected_context_hash": "62c86745ed2b3aaa",
    "final_roi_class": "negative_walltime_roi",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13_batch4",
    "official_bound_effect": false,
    "pricing_calls_delta": 0.0,
    "rmp_solves_delta": 0.0,
    "solving_time_delta": 19.792271999999997,
    "strict_trajectory_roi_class": "negative_worse_than_baseline_same_iter",
    "strict_trajectory_roi_label": 0,
    "strict_trajectory_roi_reason": "worse_than_baseline_same_iter_objective",
    "target_active_changed_task_set_count": 2,
    "target_added_journeys": 4,
    "target_addition_productivity_class": "active_replacement_task_set",
    "target_arc_option_sequence": [
      "0->8:low_time:0",
      "8->20:low_risk:2",
      "20->13:low_time:0",
      "13->0:low_risk:2"
    ],
    "target_best_rc": -5.663312,
    "target_cg_iter": 9,
    "target_context_hash": "62c86745ed2b3aaa",
    "target_inactive_changed_task_set_count": 2,
    "target_injection_success": true,
    "target_new_journeys": 2,
    "target_replacement_journeys": 2,
    "target_returned_journeys": 4,
    "target_sequence": [
      8,
      20,
      13
    ],
    "target_signal_source": "expected_context_current_probe",
    "worker_context_mismatch_skips_after_injection": 3,
    "worker_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13_batch4_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_exact_pricing_calls": 11,
    "worker_followup_completion_retry_events": 2,
    "worker_followup_exact_pricing_events": 5,
    "worker_followup_pricing_events": 8,
    "worker_followup_worker_events": 3,
    "worker_jsonl_exists": true,
    "worker_next_active_support_hash": "d701941276bec625",
    "worker_next_cg_iter": 10,
    "worker_next_dual_l1_delta": 23.369766225,
    "worker_next_dual_l1_vs_baseline_same_iter_delta": -50.522932438999995,
    "worker_next_objective": 619.173509,
    "worker_next_objective_delta": -6.254454,
    "worker_next_objective_vs_baseline_same_iter_delta": 0.03082599999993363,
    "worker_pricing_calls": 23,
    "worker_rmp_solves": 12,
    "worker_solving_time": 90.098884,
    "worker_status": "TIME_LIMIT"
  },
  {
    "baseline_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11_mainline_baseline/results.csv",
    "baseline_csv_exists": true,
    "baseline_exact_pricing_calls": 12,
    "baseline_jsonl_exists": true,
    "baseline_pricing_calls": 24,
    "baseline_rmp_solves": 12,
    "baseline_same_iter_dual_l1_delta": 15.794982,
    "baseline_same_iter_objective": 619.142683,
    "baseline_same_iter_objective_delta": 0.0,
    "baseline_solving_time": 90.539538,
    "baseline_status": "TIME_LIMIT",
    "candidate_batch_count": 1,
    "candidate_batch_target_arc_option_sequences": [],
    "candidate_batch_target_sequences": [],
    "certificate_effect": false,
    "exact_pricing_calls_delta": 1.0,
    "expected_context_hash": "3100b787bf438dfe",
    "final_roi_class": "positive_walltime_roi",
    "instance": "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11",
    "official_bound_effect": false,
    "pricing_calls_delta": 2.0,
    "rmp_solves_delta": 1.0,
    "solving_time_delta": -17.57420599999999,
    "strict_trajectory_roi_class": "negative_inactive_only",
    "strict_trajectory_roi_label": 0,
    "strict_trajectory_roi_reason": "target_columns_inactive_only",
    "target_active_changed_task_set_count": 0,
    "target_added_journeys": 1,
    "target_addition_productivity_class": "changed_inactive_only",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->1:low_risk:2",
      "1->2:low_risk:2",
      "2->4:low_risk:2",
      "4->7:low_risk:2",
      "7->11:low_risk:2",
      "11->0:low_risk:2"
    ],
    "target_best_rc": -0.824859,
    "target_cg_iter": 10,
    "target_context_hash": "3100b787bf438dfe",
    "target_inactive_changed_task_set_count": 1,
    "target_injection_success": true,
    "target_new_journeys": 1,
    "target_replacement_journeys": 0,
    "target_returned_journeys": 1,
    "target_sequence": [
      5,
      1,
      2,
      4,
      7,
      11
    ],
    "target_signal_source": "expected_context_current_probe",
    "worker_context_mismatch_skips_after_injection": 3,
    "worker_csv": "BPC_future/results/gat_active_replacement_target_worker_ab_runbook_v36_20260615/task020_apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11_target_priority_worker/results.csv",
    "worker_csv_exists": true,
    "worker_exact_pricing_calls": 13,
    "worker_followup_completion_retry_events": 0,
    "worker_followup_exact_pricing_events": 6,
    "worker_followup_pricing_events": 9,
    "worker_followup_worker_events": 3,
    "worker_jsonl_exists": true,
    "worker_next_active_support_hash": "70528dce9730c0ed",
    "worker_next_cg_iter": 11,
    "worker_next_dual_l1_delta": 23.283831999,
    "worker_next_dual_l1_vs_baseline_same_iter_delta": 7.488849999000001,
    "worker_next_objective": 619.142683,
    "worker_next_objective_delta": 0.0,
    "worker_next_objective_vs_baseline_same_iter_delta": 0.0,
    "worker_pricing_calls": 26,
    "worker_rmp_solves": 13,
    "worker_solving_time": 72.965332,
    "worker_status": "TIME_LIMIT"
  }
]
```

## 边界

- 该分析不产生 certificate；
- 该分析不改变任何求解结果；
- 后续训练标签应优先使用 long-horizon trajectory ROI，而不是仅使用 true-RC negative。
