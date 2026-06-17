# GAT Target-Priority Worker A/B Runbook

日期：2026-06-16

## 目的

生成下一轮 5/10 no-regression 与 candidate-scale ROI A/B 命令。GAT 仍只负责 embedding / trajectory impact 表达，kNN/OOD 只做安全壳；通过安全壳的 true-RC negative 可优先进入 worker target，不通过的负列进入 DELAY_QUEUE，不能永久丢弃，也不能参与 certificate。

## 机器字段

```text
gat_target_priority_worker_ab_runbook = current
status = ready
worker_method = target_materialization_fixed
worker_batch_size = 1
input_candidate_count = 15
candidate_group_count = 15
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
required_candidate_context_field_count = 8
all_checks_pass = true
```

## Candidate Policy

```json
{
  "certificate_effect": false,
  "context_miss_policy": "capture_actual_reached_contexts_for_next_iteration",
  "fixed_worker_scope": "same-context target materialization only; no Pulse search, harvest, archive, adaptive sharding, bound pruning, or certificate effect",
  "gat_role": "embedding_and_trajectory_impact_expression",
  "knn_ood_role": "safety_shell",
  "negative_discard_allowed": false,
  "safe_negative_action": "HIGH_PRIORITY",
  "unsafe_negative_action": "DELAY_QUEUE",
  "worker_batch_size": 1,
  "worker_method": "target_materialization_fixed",
  "worker_stage_policy": "match_capture_pricing_kind: heuristic_before_heuristic_exact_before_exact"
}
```

## Candidate Runs

```json
[
  {
    "active_hash_before": "28d1a1350601d64c",
    "baseline_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_mainline_baseline/results.csv",
    "best_true_reduced_cost": -25.4432665,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16"
    ],
    "capture_pricing_kind": "exact",
    "context_false_delay_accepted_batch_count": 1,
    "context_false_delay_batch_record_count": 6,
    "context_false_delay_candidate_signature_count": 32,
    "context_false_delay_false_high_priority_on_delay_count": 33,
    "context_false_delay_max_delay_risk_score": 0.4392900764942169,
    "context_false_delay_median_delay_risk_score": 0.4320344030857086,
    "context_false_delay_median_raw_high_priority_score": 0.5038455128669739,
    "context_priority_action": "collect_same_context_false_delay_hard_negative_contrast",
    "context_priority_primary_blocker": "context_local_false_delay_ranking",
    "context_priority_score": 33327.0,
    "context_target_count": 3,
    "context_target_rank": 1,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ac056820151e9ad7",
    "forbidden_signature_hash": "c2f8c77dbd063d37",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16",
    "opportunity_score": 0.0,
    "pool_signature_hash": "3656986558341232",
    "pool_task_set_hash": "f8819dd1a2dda152",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "selection_ranking": "best_rc",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave05/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->20:low_time:0",
      "20->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_priority_sequence": [
      20,
      16
    ],
    "target_sequence": [
      20,
      16
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->20:low_time:0",
          "20->16:low_time:0",
          "16->0:low_time:0"
        ],
        "sequence": [
          20,
          16
        ],
        "start_time": 29.421768
      }
    ],
    "task_count": 20,
    "true_dual_hash": "af26c5fef326d91a",
    "worker_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "28d1a1350601d64c",
    "baseline_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3_mainline_baseline/results.csv",
    "best_true_reduced_cost": -4.97015675,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3"
    ],
    "capture_pricing_kind": "exact",
    "context_false_delay_accepted_batch_count": 1,
    "context_false_delay_batch_record_count": 6,
    "context_false_delay_candidate_signature_count": 32,
    "context_false_delay_false_high_priority_on_delay_count": 33,
    "context_false_delay_max_delay_risk_score": 0.4392900764942169,
    "context_false_delay_median_delay_risk_score": 0.4320344030857086,
    "context_false_delay_median_raw_high_priority_score": 0.5038455128669739,
    "context_priority_action": "collect_same_context_false_delay_hard_negative_contrast",
    "context_priority_primary_blocker": "context_local_false_delay_ranking",
    "context_priority_score": 33327.0,
    "context_target_count": 3,
    "context_target_rank": 2,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ac056820151e9ad7",
    "forbidden_signature_hash": "c2f8c77dbd063d37",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3",
    "opportunity_score": 0.0,
    "pool_signature_hash": "3656986558341232",
    "pool_task_set_hash": "f8819dd1a2dda152",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "selection_ranking": "impact",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave05/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->15:low_risk:2",
      "15->5:low_risk:2",
      "5->16:low_risk:2",
      "16->0:low_risk:2"
    ],
    "target_priority_sequence": [
      15,
      5,
      16
    ],
    "target_sequence": [
      15,
      5,
      16,
      7,
      3
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->15:low_risk:2",
          "15->5:low_risk:2",
          "5->16:low_risk:2",
          "16->0:low_risk:2"
        ],
        "sequence": [
          15,
          5,
          16
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->7:low_time:0",
          "7->3:low_risk:2",
          "3->0:low_time:0"
        ],
        "sequence": [
          7,
          3
        ],
        "start_time": 297.783925
      }
    ],
    "task_count": 20,
    "true_dual_hash": "af26c5fef326d91a",
    "worker_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "28d1a1350601d64c",
    "baseline_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20_mainline_baseline/results.csv",
    "best_true_reduced_cost": -3.41733,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20"
    ],
    "capture_pricing_kind": "exact",
    "context_false_delay_accepted_batch_count": 1,
    "context_false_delay_batch_record_count": 6,
    "context_false_delay_candidate_signature_count": 32,
    "context_false_delay_false_high_priority_on_delay_count": 33,
    "context_false_delay_max_delay_risk_score": 0.4392900764942169,
    "context_false_delay_median_delay_risk_score": 0.4320344030857086,
    "context_false_delay_median_raw_high_priority_score": 0.5038455128669739,
    "context_priority_action": "collect_same_context_false_delay_hard_negative_contrast",
    "context_priority_primary_blocker": "context_local_false_delay_ranking",
    "context_priority_score": 33327.0,
    "context_target_count": 3,
    "context_target_rank": 3,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ac056820151e9ad7",
    "forbidden_signature_hash": "c2f8c77dbd063d37",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20",
    "opportunity_score": 0.0,
    "pool_signature_hash": "3656986558341232",
    "pool_task_set_hash": "f8819dd1a2dda152",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "selection_ranking": "active_replacement",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave05/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->15:low_risk:2",
      "15->20:low_time:0",
      "20->0:low_time:0"
    ],
    "target_priority_sequence": [
      15,
      20
    ],
    "target_sequence": [
      15,
      20
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->15:low_risk:2",
          "15->20:low_time:0",
          "20->0:low_time:0"
        ],
        "sequence": [
          15,
          20
        ],
        "start_time": 0.0
      }
    ],
    "task_count": 20,
    "true_dual_hash": "af26c5fef326d91a",
    "worker_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "a71d3ab5cf5a282a",
    "baseline_command_type": "task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_mainline_baseline/results.csv",
    "best_true_reduced_cost": -41.3185275,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19"
    ],
    "capture_pricing_kind": "exact",
    "context_false_delay_accepted_batch_count": 5,
    "context_false_delay_batch_record_count": 9,
    "context_false_delay_candidate_signature_count": 4,
    "context_false_delay_false_high_priority_on_delay_count": 4,
    "context_false_delay_max_delay_risk_score": 0.37911903858184814,
    "context_false_delay_median_delay_risk_score": 0.34422458708286285,
    "context_false_delay_median_raw_high_priority_score": 0.6995677649974823,
    "context_priority_action": "collect_same_context_false_delay_hard_negative_contrast",
    "context_priority_primary_blocker": "context_local_false_delay_ranking",
    "context_priority_score": 4054.0,
    "context_target_count": 3,
    "context_target_rank": 1,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b6d808ebac2a6dd8",
    "forbidden_signature_hash": "6b0ab3de1090984f",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_region": "apollo15_20km",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19",
    "opportunity_score": 0.0,
    "pool_signature_hash": "2934629ac06005ef",
    "pool_task_set_hash": "978c7f39b6d714fe",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "selection_ranking": "best_rc",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave08/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->19:low_risk:2",
      "19->0:low_time:0"
    ],
    "target_priority_sequence": [
      16,
      19
    ],
    "target_sequence": [
      16,
      19
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->16:low_time:0",
          "16->19:low_risk:2",
          "19->0:low_time:0"
        ],
        "sequence": [
          16,
          19
        ],
        "start_time": 0.0
      }
    ],
    "task_count": 20,
    "true_dual_hash": "0249cbb92e9ec2a0",
    "worker_command_type": "task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "a71d3ab5cf5a282a",
    "baseline_command_type": "task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8_mainline_baseline/results.csv",
    "best_true_reduced_cost": -28.2396105,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8"
    ],
    "capture_pricing_kind": "exact",
    "context_false_delay_accepted_batch_count": 5,
    "context_false_delay_batch_record_count": 9,
    "context_false_delay_candidate_signature_count": 4,
    "context_false_delay_false_high_priority_on_delay_count": 4,
    "context_false_delay_max_delay_risk_score": 0.37911903858184814,
    "context_false_delay_median_delay_risk_score": 0.34422458708286285,
    "context_false_delay_median_raw_high_priority_score": 0.6995677649974823,
    "context_priority_action": "collect_same_context_false_delay_hard_negative_contrast",
    "context_priority_primary_blocker": "context_local_false_delay_ranking",
    "context_priority_score": 4054.0,
    "context_target_count": 3,
    "context_target_rank": 2,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b6d808ebac2a6dd8",
    "forbidden_signature_hash": "6b0ab3de1090984f",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_region": "apollo15_20km",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8",
    "opportunity_score": 0.0,
    "pool_signature_hash": "2934629ac06005ef",
    "pool_task_set_hash": "978c7f39b6d714fe",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "selection_ranking": "impact",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave08/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->1:low_risk:2",
      "1->2:low_risk:2",
      "2->8:low_time:0",
      "8->0:low_risk:2"
    ],
    "target_priority_sequence": [
      1,
      2,
      8
    ],
    "target_sequence": [
      1,
      2,
      8
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->1:low_risk:2",
          "1->2:low_risk:2",
          "2->8:low_time:0",
          "8->0:low_risk:2"
        ],
        "sequence": [
          1,
          2,
          8
        ],
        "start_time": 0.0
      }
    ],
    "task_count": 20,
    "true_dual_hash": "0249cbb92e9ec2a0",
    "worker_command_type": "task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "a71d3ab5cf5a282a",
    "baseline_command_type": "task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19_mainline_baseline/results.csv",
    "best_true_reduced_cost": -0.873676,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19"
    ],
    "capture_pricing_kind": "exact",
    "context_false_delay_accepted_batch_count": 5,
    "context_false_delay_batch_record_count": 9,
    "context_false_delay_candidate_signature_count": 4,
    "context_false_delay_false_high_priority_on_delay_count": 4,
    "context_false_delay_max_delay_risk_score": 0.37911903858184814,
    "context_false_delay_median_delay_risk_score": 0.34422458708286285,
    "context_false_delay_median_raw_high_priority_score": 0.6995677649974823,
    "context_priority_action": "collect_same_context_false_delay_hard_negative_contrast",
    "context_priority_primary_blocker": "context_local_false_delay_ranking",
    "context_priority_score": 4054.0,
    "context_target_count": 3,
    "context_target_rank": 3,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "b6d808ebac2a6dd8",
    "forbidden_signature_hash": "6b0ab3de1090984f",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_region": "apollo15_20km",
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19",
    "opportunity_score": 0.0,
    "pool_signature_hash": "2934629ac06005ef",
    "pool_task_set_hash": "978c7f39b6d714fe",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "selection_ranking": "active_replacement",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave08/logs/BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->5:low_risk:2",
      "5->19:low_time:0",
      "19->0:low_time:0"
    ],
    "target_priority_sequence": [
      5,
      19
    ],
    "target_sequence": [
      5,
      19
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_risk:2",
          "5->19:low_time:0",
          "19->0:low_time:0"
        ],
        "sequence": [
          5,
          19
        ],
        "start_time": 0.0
      }
    ],
    "task_count": 20,
    "true_dual_hash": "0249cbb92e9ec2a0",
    "worker_command_type": "task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "e3204e165ebb29a4",
    "baseline_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_mainline_baseline/results.csv",
    "best_true_reduced_cost": -29.939646,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17"
    ],
    "capture_pricing_kind": "exact",
    "context_false_delay_accepted_batch_count": 4,
    "context_false_delay_batch_record_count": 8,
    "context_false_delay_candidate_signature_count": 3,
    "context_false_delay_false_high_priority_on_delay_count": 4,
    "context_false_delay_max_delay_risk_score": 0.408302366733551,
    "context_false_delay_median_delay_risk_score": 0.4060160219669342,
    "context_false_delay_median_raw_high_priority_score": 0.5648878216743469,
    "context_priority_action": "collect_same_context_false_delay_hard_negative_contrast",
    "context_priority_primary_blocker": "context_local_false_delay_ranking",
    "context_priority_score": 4042.0,
    "context_target_count": 3,
    "context_target_rank": 1,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "79fde658840fe2b8",
    "forbidden_signature_hash": "64f1f111a409966f",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17",
    "opportunity_score": 0.0,
    "pool_signature_hash": "e13cb15840f7914a",
    "pool_task_set_hash": "fe600e7457dfdb19",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "selection_ranking": "best_rc",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave08/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->1:low_risk:2",
      "1->0:low_risk:2"
    ],
    "target_priority_sequence": [
      1
    ],
    "target_sequence": [
      1,
      15,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->1:low_risk:2",
          "1->0:low_risk:2"
        ],
        "sequence": [
          1
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->15:low_risk:2",
          "15->17:low_energy:1",
          "17->0:low_risk:2"
        ],
        "sequence": [
          15,
          17
        ],
        "start_time": 187.086563
      }
    ],
    "task_count": 20,
    "true_dual_hash": "f03a071e71fa8841",
    "worker_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "e3204e165ebb29a4",
    "baseline_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_mainline_baseline/results.csv",
    "best_true_reduced_cost": -20.0283435,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5"
    ],
    "capture_pricing_kind": "exact",
    "context_false_delay_accepted_batch_count": 4,
    "context_false_delay_batch_record_count": 8,
    "context_false_delay_candidate_signature_count": 3,
    "context_false_delay_false_high_priority_on_delay_count": 4,
    "context_false_delay_max_delay_risk_score": 0.408302366733551,
    "context_false_delay_median_delay_risk_score": 0.4060160219669342,
    "context_false_delay_median_raw_high_priority_score": 0.5648878216743469,
    "context_priority_action": "collect_same_context_false_delay_hard_negative_contrast",
    "context_priority_primary_blocker": "context_local_false_delay_ranking",
    "context_priority_score": 4042.0,
    "context_target_count": 3,
    "context_target_rank": 2,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "79fde658840fe2b8",
    "forbidden_signature_hash": "64f1f111a409966f",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5",
    "opportunity_score": 0.0,
    "pool_signature_hash": "e13cb15840f7914a",
    "pool_task_set_hash": "fe600e7457dfdb19",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "selection_ranking": "impact",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave08/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->4:low_time:0",
      "4->0:low_time:0"
    ],
    "target_priority_sequence": [
      12,
      4
    ],
    "target_sequence": [
      12,
      4,
      13,
      5
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_risk:2",
          "12->4:low_time:0",
          "4->0:low_time:0"
        ],
        "sequence": [
          12,
          4
        ],
        "start_time": 52.632685
      },
      {
        "arc_option_sequence": [
          "0->13:low_time:0",
          "13->5:low_time:0",
          "5->0:low_time:0"
        ],
        "sequence": [
          13,
          5
        ],
        "start_time": 358.448011
      }
    ],
    "task_count": 20,
    "true_dual_hash": "f03a071e71fa8841",
    "worker_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "e3204e165ebb29a4",
    "baseline_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_mainline_baseline/results.csv",
    "best_true_reduced_cost": -14.7797715,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13"
    ],
    "capture_pricing_kind": "exact",
    "context_false_delay_accepted_batch_count": 4,
    "context_false_delay_batch_record_count": 8,
    "context_false_delay_candidate_signature_count": 3,
    "context_false_delay_false_high_priority_on_delay_count": 4,
    "context_false_delay_max_delay_risk_score": 0.408302366733551,
    "context_false_delay_median_delay_risk_score": 0.4060160219669342,
    "context_false_delay_median_raw_high_priority_score": 0.5648878216743469,
    "context_priority_action": "collect_same_context_false_delay_hard_negative_contrast",
    "context_priority_primary_blocker": "context_local_false_delay_ranking",
    "context_priority_score": 4042.0,
    "context_target_count": 3,
    "context_target_rank": 3,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "79fde658840fe2b8",
    "forbidden_signature_hash": "64f1f111a409966f",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13",
    "opportunity_score": 0.0,
    "pool_signature_hash": "e13cb15840f7914a",
    "pool_task_set_hash": "fe600e7457dfdb19",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "selection_ranking": "active_replacement",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave08/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->12:low_risk:2",
      "12->4:low_time:0",
      "4->0:low_time:0"
    ],
    "target_priority_sequence": [
      12,
      4
    ],
    "target_sequence": [
      12,
      4,
      19,
      13
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->12:low_risk:2",
          "12->4:low_time:0",
          "4->0:low_time:0"
        ],
        "sequence": [
          12,
          4
        ],
        "start_time": 52.632685
      },
      {
        "arc_option_sequence": [
          "0->19:low_risk:2",
          "19->13:low_risk:2",
          "13->0:low_risk:2"
        ],
        "sequence": [
          19,
          13
        ],
        "start_time": 358.448011
      }
    ],
    "task_count": 20,
    "true_dual_hash": "f03a071e71fa8841",
    "worker_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "96c7c0766604244a",
    "baseline_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_mainline_baseline/results.csv",
    "best_true_reduced_cost": -31.9356514,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15"
    ],
    "capture_pricing_kind": "exact",
    "context_false_delay_accepted_batch_count": 6,
    "context_false_delay_batch_record_count": 8,
    "context_false_delay_candidate_signature_count": 2,
    "context_false_delay_false_high_priority_on_delay_count": 2,
    "context_false_delay_max_delay_risk_score": 0.3857404589653015,
    "context_false_delay_median_delay_risk_score": 0.37403224408626556,
    "context_false_delay_median_raw_high_priority_score": 0.6449823081493378,
    "context_priority_action": "collect_same_context_false_delay_hard_negative_contrast",
    "context_priority_primary_blocker": "context_local_false_delay_ranking",
    "context_priority_score": 2034.0,
    "context_target_count": 3,
    "context_target_rank": 1,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "forbidden_signature_hash": "16f38b9203fc0908",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15",
    "opportunity_score": -1.7641903999999922,
    "pool_signature_hash": "a3a808a977a593aa",
    "pool_task_set_hash": "393c147abf261db2",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "selection_ranking": "best_rc",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave06/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->16:low_time:0",
      "16->0:low_time:0"
    ],
    "target_priority_sequence": [
      16
    ],
    "target_sequence": [
      16,
      17,
      15
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->16:low_time:0",
          "16->0:low_time:0"
        ],
        "sequence": [
          16
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->17:low_time:0",
          "17->15:low_energy:1",
          "15->0:low_risk:2"
        ],
        "sequence": [
          17,
          15
        ],
        "start_time": 264.580456
      }
    ],
    "task_count": 20,
    "true_dual_hash": "b49472077fb42329",
    "worker_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "96c7c0766604244a",
    "baseline_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_mainline_baseline/results.csv",
    "best_true_reduced_cost": -26.5430824,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17"
    ],
    "capture_pricing_kind": "exact",
    "context_false_delay_accepted_batch_count": 6,
    "context_false_delay_batch_record_count": 8,
    "context_false_delay_candidate_signature_count": 2,
    "context_false_delay_false_high_priority_on_delay_count": 2,
    "context_false_delay_max_delay_risk_score": 0.3857404589653015,
    "context_false_delay_median_delay_risk_score": 0.37403224408626556,
    "context_false_delay_median_raw_high_priority_score": 0.6449823081493378,
    "context_priority_action": "collect_same_context_false_delay_hard_negative_contrast",
    "context_priority_primary_blocker": "context_local_false_delay_ranking",
    "context_priority_score": 2034.0,
    "context_target_count": 3,
    "context_target_rank": 2,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "forbidden_signature_hash": "16f38b9203fc0908",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17",
    "opportunity_score": -1.7641903999999922,
    "pool_signature_hash": "a3a808a977a593aa",
    "pool_task_set_hash": "393c147abf261db2",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "selection_ranking": "impact",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave06/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->0:low_risk:2"
    ],
    "target_priority_sequence": [
      4
    ],
    "target_sequence": [
      4,
      19,
      10,
      17
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->0:low_risk:2"
        ],
        "sequence": [
          4
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->19:low_risk:2",
          "19->10:low_time:0",
          "10->17:low_risk:2",
          "17->0:low_time:0"
        ],
        "sequence": [
          19,
          10,
          17
        ],
        "start_time": 202.264867
      }
    ],
    "task_count": 20,
    "true_dual_hash": "b49472077fb42329",
    "worker_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "96c7c0766604244a",
    "baseline_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_mainline_baseline/results.csv",
    "best_true_reduced_cost": -21.7182942,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7"
    ],
    "capture_pricing_kind": "exact",
    "context_false_delay_accepted_batch_count": 6,
    "context_false_delay_batch_record_count": 8,
    "context_false_delay_candidate_signature_count": 2,
    "context_false_delay_false_high_priority_on_delay_count": 2,
    "context_false_delay_max_delay_risk_score": 0.3857404589653015,
    "context_false_delay_median_delay_risk_score": 0.37403224408626556,
    "context_false_delay_median_raw_high_priority_score": 0.6449823081493378,
    "context_priority_action": "collect_same_context_false_delay_hard_negative_contrast",
    "context_priority_primary_blocker": "context_local_false_delay_ranking",
    "context_priority_score": 2034.0,
    "context_target_count": 3,
    "context_target_rank": 3,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "ac15bc4e7e3d6fff",
    "forbidden_signature_hash": "16f38b9203fc0908",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7",
    "opportunity_score": -1.7641903999999922,
    "pool_signature_hash": "a3a808a977a593aa",
    "pool_task_set_hash": "393c147abf261db2",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "selection_ranking": "active_replacement",
    "source_file": "BPC_future/results/gat_bulk_sampling_runbook_v13_20260615/task020_bulk_capture_wave06/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->4:low_risk:2",
      "4->0:low_risk:2"
    ],
    "target_priority_sequence": [
      4
    ],
    "target_sequence": [
      4,
      10,
      17,
      7
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->4:low_risk:2",
          "4->0:low_risk:2"
        ],
        "sequence": [
          4
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->10:low_risk:2",
          "10->17:low_risk:2",
          "17->7:low_time:0",
          "7->0:low_risk:2"
        ],
        "sequence": [
          10,
          17,
          7
        ],
        "start_time": 171.602203
      }
    ],
    "task_count": 20,
    "true_dual_hash": "b49472077fb42329",
    "worker_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3ee7a90ac6308fe9",
    "baseline_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_mainline_baseline/results.csv",
    "best_true_reduced_cost": -18.05904625,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1"
    ],
    "capture_pricing_kind": "exact",
    "context_false_delay_accepted_batch_count": 0,
    "context_false_delay_batch_record_count": 1,
    "context_false_delay_candidate_signature_count": 1,
    "context_false_delay_false_high_priority_on_delay_count": 1,
    "context_false_delay_max_delay_risk_score": 0.46171408891677856,
    "context_false_delay_median_delay_risk_score": 0.46171408891677856,
    "context_false_delay_median_raw_high_priority_score": 0.44783666729927063,
    "context_priority_action": "collect_same_context_false_delay_hard_negative_contrast",
    "context_priority_primary_blocker": "context_local_false_delay_ranking",
    "context_priority_score": 1011.0,
    "context_target_count": 3,
    "context_target_rank": 1,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7b430465c7ae76b3",
    "forbidden_signature_hash": "9442d521be840545",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1",
    "opportunity_score": -4.1411999999999995,
    "pool_signature_hash": "3b394c6efaa8c39f",
    "pool_task_set_hash": "b9009b10793c0039",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "selection_ranking": "best_rc",
    "source_file": "BPC_future/results/gat_target_priority_worker_ab_active_replacement_active_only_20260616/task020_tranq20_ctxac056820_cg07_r29_tasks15_20_target_priority_worker/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->5:low_time:0",
      "5->1:low_risk:2",
      "1->0:low_energy:1"
    ],
    "target_priority_sequence": [
      5,
      1
    ],
    "target_sequence": [
      5,
      1
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->5:low_time:0",
          "5->1:low_risk:2",
          "1->0:low_energy:1"
        ],
        "sequence": [
          5,
          1
        ],
        "start_time": 21.409885
      }
    ],
    "task_count": 20,
    "true_dual_hash": "2d5b9d2e524fe6e0",
    "worker_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3ee7a90ac6308fe9",
    "baseline_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb2_15_17_19_9_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb2_15_17_19_9_mainline_baseline/results.csv",
    "best_true_reduced_cost": -9.400881,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb2_15_17_19_9"
    ],
    "capture_pricing_kind": "exact",
    "context_false_delay_accepted_batch_count": 0,
    "context_false_delay_batch_record_count": 1,
    "context_false_delay_candidate_signature_count": 1,
    "context_false_delay_false_high_priority_on_delay_count": 1,
    "context_false_delay_max_delay_risk_score": 0.46171408891677856,
    "context_false_delay_median_delay_risk_score": 0.46171408891677856,
    "context_false_delay_median_raw_high_priority_score": 0.44783666729927063,
    "context_priority_action": "collect_same_context_false_delay_hard_negative_contrast",
    "context_priority_primary_blocker": "context_local_false_delay_ranking",
    "context_priority_score": 1011.0,
    "context_target_count": 3,
    "context_target_rank": 2,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7b430465c7ae76b3",
    "forbidden_signature_hash": "9442d521be840545",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb2_15_17_19_9",
    "opportunity_score": -4.1411999999999995,
    "pool_signature_hash": "3b394c6efaa8c39f",
    "pool_task_set_hash": "b9009b10793c0039",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "selection_ranking": "impact",
    "source_file": "BPC_future/results/gat_target_priority_worker_ab_active_replacement_active_only_20260616/task020_tranq20_ctxac056820_cg07_r29_tasks15_20_target_priority_worker/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->15:low_risk:2",
      "15->17:low_time:0",
      "17->19:low_risk:2",
      "19->0:low_risk:2"
    ],
    "target_priority_sequence": [
      15,
      17,
      19
    ],
    "target_sequence": [
      15,
      17,
      19,
      9
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->15:low_risk:2",
          "15->17:low_time:0",
          "17->19:low_risk:2",
          "19->0:low_risk:2"
        ],
        "sequence": [
          15,
          17,
          19
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->9:low_risk:2",
          "9->0:low_energy:1"
        ],
        "sequence": [
          9
        ],
        "start_time": 288.94697
      }
    ],
    "task_count": 20,
    "true_dual_hash": "2d5b9d2e524fe6e0",
    "worker_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb2_15_17_19_9_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb2_15_17_19_9_target_priority_worker/results.csv"
  },
  {
    "active_hash_before": "3ee7a90ac6308fe9",
    "baseline_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb3_1_9_mainline_baseline",
    "baseline_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb3_1_9_mainline_baseline/results.csv",
    "best_true_reduced_cost": -1.397984,
    "branch_hash": "da39a3ee5e6b4b0d",
    "candidate_batch_count": 1,
    "candidate_context_complete": true,
    "candidate_names": [
      "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb3_1_9"
    ],
    "capture_pricing_kind": "exact",
    "context_false_delay_accepted_batch_count": 0,
    "context_false_delay_batch_record_count": 1,
    "context_false_delay_candidate_signature_count": 1,
    "context_false_delay_false_high_priority_on_delay_count": 1,
    "context_false_delay_max_delay_risk_score": 0.46171408891677856,
    "context_false_delay_median_delay_risk_score": 0.46171408891677856,
    "context_false_delay_median_raw_high_priority_score": 0.44783666729927063,
    "context_priority_action": "collect_same_context_false_delay_hard_negative_contrast",
    "context_priority_primary_blocker": "context_local_false_delay_ranking",
    "context_priority_score": 1011.0,
    "context_target_count": 3,
    "context_target_rank": 3,
    "cut_hash": "d653e60106177bb4",
    "expected_context_hash": "7b430465c7ae76b3",
    "forbidden_signature_hash": "9442d521be840545",
    "instance": "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
    "instance_family": "sector-wave",
    "instance_region": "tranquillitatis_balmer_like_20km",
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb3_1_9",
    "opportunity_score": -4.1411999999999995,
    "pool_signature_hash": "3b394c6efaa8c39f",
    "pool_task_set_hash": "b9009b10793c0039",
    "scale_config": "BPC_future/configs/moon_trek_20_smoke.yaml",
    "scale_config_fallback_from_task20": false,
    "selection_ranking": "active_replacement",
    "source_file": "BPC_future/results/gat_target_priority_worker_ab_active_replacement_active_only_20260616/task020_tranq20_ctxac056820_cg07_r29_tasks15_20_target_priority_worker/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json.jsonl",
    "target_arc_option_sequence": [
      "0->1:low_risk:2",
      "1->0:low_risk:2"
    ],
    "target_priority_sequence": [
      1
    ],
    "target_sequence": [
      1,
      9
    ],
    "target_sortie_traces": [
      {
        "arc_option_sequence": [
          "0->1:low_risk:2",
          "1->0:low_risk:2"
        ],
        "sequence": [
          1
        ],
        "start_time": 0.0
      },
      {
        "arc_option_sequence": [
          "0->9:low_risk:2",
          "9->0:low_energy:1"
        ],
        "sequence": [
          9
        ],
        "start_time": 287.981087
      }
    ],
    "task_count": 20,
    "true_dual_hash": "2d5b9d2e524fe6e0",
    "worker_command_type": "task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb3_1_9_target_priority_worker",
    "worker_csv": "BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb3_1_9_target_priority_worker/results.csv"
  }
]
```

## Commands

### task005_mainline_no_regression_gat_kept

Run task-5 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_5_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task005_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task005_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task005_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task005_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json
```

### task010_mainline_no_regression_gat_kept

Run task-10 no-regression with mainline GAT/learning kept; no new worker or gate is enabled.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future_external_timeout_batch.py --config BPC_future/configs/moon_trek_10_journey.yaml --time-limit 60.000000 --timeout-kill-after 30s --max-workers 1 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task010_mainline_no_regression_gat_kept/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task010_mainline_no_regression_gat_kept/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task010_mainline_no_regression_gat_kept/solutions --run-log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task010_mainline_no_regression_gat_kept/run_logs --quiet --instances BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_mainline_baseline/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_mainline_baseline/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_target_priority_worker/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_target_priority_worker/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb1_20_16_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ac056820151e9ad7 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=20,16 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=20,16 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=20,16 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->20:low_time:0","20->16:low_time:0","16->0:low_time:0"],"sequence":[20,16],"start_time":29.421768}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_time:0,20->16:low_time:0,16->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3_mainline_baseline/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3_mainline_baseline/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3_target_priority_worker/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3_target_priority_worker/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb2_15_5_16_7_3_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ac056820151e9ad7 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=15,5,16 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=15,5,16 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=15,5,16,7,3 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->15:low_risk:2","15->5:low_risk:2","5->16:low_risk:2","16->0:low_risk:2"],"sequence":[15,5,16],"start_time":0.0},{"arc_option_sequence":["0->7:low_time:0","7->3:low_risk:2","3->0:low_time:0"],"sequence":[7,3],"start_time":297.783925}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->15:low_risk:2,15->5:low_risk:2,5->16:low_risk:2,16->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20_mainline_baseline/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20_mainline_baseline/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20_target_priority_worker/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20_target_priority_worker/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_mb3_15_20_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ac056820151e9ad7 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=15,20 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=15,20 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=15,20 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->15:low_risk:2","15->20:low_time:0","20->0:low_time:0"],"sequence":[15,20],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->15:low_risk:2,15->20:low_time:0,20->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_mainline_baseline/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_mainline_baseline/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_target_priority_worker/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_target_priority_worker/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb1_16_19_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b6d808ebac2a6dd8 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=16,19 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=16,19 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=16,19 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->16:low_time:0","16->19:low_risk:2","19->0:low_time:0"],"sequence":[16,19],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->16:low_time:0,16->19:low_risk:2,19->0:low_time:0'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8_mainline_baseline/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8_mainline_baseline/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8_target_priority_worker/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8_target_priority_worker/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb2_1_2_8_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b6d808ebac2a6dd8 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=1,2,8 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=1,2,8 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=1,2,8 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->1:low_risk:2","1->2:low_risk:2","2->8:low_time:0","8->0:low_risk:2"],"sequence":[1,2,8],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->1:low_risk:2,1->2:low_risk:2,2->8:low_time:0,8->0:low_risk:2'
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19_mainline_baseline/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19_mainline_baseline/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19_target_priority_worker/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19_target_priority_worker/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_mb3_5_19_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=b6d808ebac2a6dd8 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,19 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,19 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,19 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_risk:2","5->19:low_time:0","19->0:low_time:0"],"sequence":[5,19],"start_time":0.0}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_risk:2,5->19:low_time:0,19->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_target_priority_worker/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_target_priority_worker/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb1_1_15_17_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=79fde658840fe2b8 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=1,15,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->1:low_risk:2","1->0:low_risk:2"],"sequence":[1],"start_time":0.0},{"arc_option_sequence":["0->15:low_risk:2","15->17:low_energy:1","17->0:low_risk:2"],"sequence":[15,17],"start_time":187.086563}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->1:low_risk:2,1->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_mainline_baseline/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_mainline_baseline/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_target_priority_worker/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_target_priority_worker/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb2_12_4_13_5_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=79fde658840fe2b8 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,4 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,4 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,4,13,5 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_risk:2","12->4:low_time:0","4->0:low_time:0"],"sequence":[12,4],"start_time":52.632685},{"arc_option_sequence":["0->13:low_time:0","13->5:low_time:0","5->0:low_time:0"],"sequence":[13,5],"start_time":358.448011}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_risk:2,12->4:low_time:0,4->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_mainline_baseline/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_mainline_baseline/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_target_priority_worker/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_target_priority_worker/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_79fde658840fe2b8_mb3_12_4_19_13_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=79fde658840fe2b8 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=12,4 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=12,4 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=12,4,19,13 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->12:low_risk:2","12->4:low_time:0","4->0:low_time:0"],"sequence":[12,4],"start_time":52.632685},{"arc_option_sequence":["0->19:low_risk:2","19->13:low_risk:2","13->0:low_risk:2"],"sequence":[19,13],"start_time":358.448011}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->12:low_risk:2,12->4:low_time:0,4->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_mainline_baseline/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_mainline_baseline/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_target_priority_worker/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_target_priority_worker/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb1_16_17_15_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ac15bc4e7e3d6fff --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=16 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=16 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=16,17,15 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->16:low_time:0","16->0:low_time:0"],"sequence":[16],"start_time":0.0},{"arc_option_sequence":["0->17:low_time:0","17->15:low_energy:1","15->0:low_risk:2"],"sequence":[17,15],"start_time":264.580456}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->16:low_time:0,16->0:low_time:0'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_mainline_baseline/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_mainline_baseline/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_target_priority_worker/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_target_priority_worker/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb2_4_19_10_17_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ac15bc4e7e3d6fff --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,19,10,17 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_risk:2","4->0:low_risk:2"],"sequence":[4],"start_time":0.0},{"arc_option_sequence":["0->19:low_risk:2","19->10:low_time:0","10->17:low_risk:2","17->0:low_time:0"],"sequence":[19,10,17],"start_time":202.264867}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_risk:2,4->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_mainline_baseline/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_mainline_baseline/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_target_priority_worker/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_target_priority_worker/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_mb3_4_10_17_7_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=ac15bc4e7e3d6fff --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=4 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=4 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=4,10,17,7 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->4:low_risk:2","4->0:low_risk:2"],"sequence":[4],"start_time":0.0},{"arc_option_sequence":["0->10:low_risk:2","10->17:low_risk:2","17->7:low_time:0","7->0:low_risk:2"],"sequence":[10,17,7],"start_time":171.602203}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->4:low_risk:2,4->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_mainline_baseline/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_mainline_baseline/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_target_priority_worker/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_target_priority_worker/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb1_5_1_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7b430465c7ae76b3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=5,1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=5,1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=5,1 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->5:low_time:0","5->1:low_risk:2","1->0:low_energy:1"],"sequence":[5,1],"start_time":21.409885}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->5:low_time:0,5->1:low_risk:2,1->0:low_energy:1'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb2_15_17_19_9_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb2_15_17_19_9_mainline_baseline/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb2_15_17_19_9_mainline_baseline/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb2_15_17_19_9_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb2_15_17_19_9_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb2_15_17_19_9_target_priority_worker/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb2_15_17_19_9_target_priority_worker/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb2_15_17_19_9_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7b430465c7ae76b3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=15,17,19 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=15,17,19 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=15,17,19,9 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->15:low_risk:2","15->17:low_time:0","17->19:low_risk:2","19->0:low_risk:2"],"sequence":[15,17,19],"start_time":0.0},{"arc_option_sequence":["0->9:low_risk:2","9->0:low_energy:1"],"sequence":[9],"start_time":288.94697}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->15:low_risk:2,15->17:low_time:0,17->19:low_risk:2,19->0:low_risk:2'
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb3_1_9_mainline_baseline

Run task-20 mainline baseline for the same target context. Learning/GAT stays enabled so the captured context can be reached.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb3_1_9_mainline_baseline/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb3_1_9_mainline_baseline/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb3_1_9_mainline_baseline/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256
```

### task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb3_1_9_target_priority_worker

Run explicit opt-in same-context target-materialization worker. This may add true-RC negative columns selected by GAT, but cannot certify no-negative or run official lower-bound shortcuts.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config BPC_future/configs/moon_trek_20_smoke.yaml --instances BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json --time-limit 85.000000 --results-csv BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb3_1_9_target_priority_worker/results.csv --log-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb3_1_9_target_priority_worker/logs --solution-dir BPC_future/results/gat_batch_impact_false_delay_context_plan_v49_v39_runbooks_20260616/individual_worker_ab_runbook/task020_tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_7b430465c7ae76b3_mb3_1_9_target_priority_worker/solutions --quiet --set journey_counterfactual_replay_capture_enabled=True --set journey_counterfactual_replay_capture_active_basis_enabled=True --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=True --set journey_counterfactual_replay_capture_log_empty=True --set journey_counterfactual_replay_capture_active_basis_max_rows=96 --set journey_counterfactual_replay_capture_max_journeys=32 --set journey_counterfactual_replay_capture_pool_max_journeys=256 --set journey_counterfactual_replay_capture_forbidden_signature_max_count=256 --set journey_sharded_pulse_hidden_negative_worker_enabled=True --set journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe --set journey_sharded_pulse_hidden_negative_worker_log_skips=True --set journey_sharded_pulse_worker_current_probe_enabled=True --set journey_sharded_pulse_worker_current_probe_time_limit=0.250 --set journey_sharded_pulse_worker_current_probe_max_recursions=0 --set journey_sharded_pulse_worker_current_probe_max_columns=1 --set journey_sharded_pulse_worker_current_probe_min_tasks=20 --set journey_sharded_pulse_worker_current_probe_min_remaining_time=0.0 --set journey_sharded_pulse_worker_current_probe_min_certificate_flat_rounds=0 --set journey_sharded_pulse_worker_current_probe_min_no_column_rounds=0 --set journey_sharded_pulse_worker_current_probe_hard_tail_fingerprint_enabled=False --set journey_sharded_pulse_worker_current_probe_harvesting_enabled=False --set journey_sharded_pulse_worker_current_probe_negative_harvest_limit=0 --set journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True --set journey_sharded_pulse_hidden_negative_worker_time_limit=0.250 --set journey_sharded_pulse_hidden_negative_worker_max_recursions=0 --set journey_sharded_pulse_hidden_negative_worker_archive_enabled=False --set journey_sharded_pulse_hidden_negative_worker_bound_pruning_enabled=False --set journey_sharded_pulse_hidden_negative_worker_harvesting_enabled=False --set journey_sharded_pulse_hidden_negative_worker_negative_harvest_limit=0 --set journey_sharded_pulse_hidden_negative_worker_adaptive_sharding_enabled=False --set journey_sharded_pulse_hidden_negative_worker_refine_incomplete_first_task_shards=False --set journey_sharded_pulse_hidden_negative_worker_shard_scheduling_enabled=False --set journey_sharded_pulse_hidden_negative_worker_shard_roi_gate_enabled=False --set journey_sharded_pulse_hidden_negative_worker_impact_filter_mode=off --set journey_sharded_pulse_hidden_negative_worker_max_columns=1 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_enabled=True --set journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_enabled=False --set journey_sharded_pulse_hidden_negative_worker_target_materialization_enabled=True --set journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=False --set journey_sharded_pulse_hidden_negative_worker_before_exact_enabled=True --set journey_sharded_pulse_hidden_negative_worker_expected_context_hash=7b430465c7ae76b3 --set journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_sequence=1 --set journey_sharded_pulse_hidden_negative_worker_target_transition_priority_sequence=1 --set journey_sharded_pulse_hidden_negative_worker_target_sequence_diagnostics_sequence=1,9 --set 'journey_sharded_pulse_hidden_negative_worker_target_materialization_traces=[{"arc_option_sequence":["0->1:low_risk:2","1->0:low_risk:2"],"sequence":[1],"start_time":0.0},{"arc_option_sequence":["0->9:low_risk:2","9->0:low_energy:1"],"sequence":[9],"start_time":287.981087}]' --set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->1:low_risk:2,1->0:low_risk:2'
```

## 边界

- 5/10 命令不关闭主线 GAT/learning，也不启用新 worker；
- candidate baseline/worker 命令也不关闭主线 GAT/learning，避免候选捕获上下文无法复现；
- candidate baseline/worker 命令开启 counterfactual replay capture；如果旧 target context 没到，仍保留实际到达的 context 供下一轮候选抽取；
- candidate worker 命令是显式 opt-in，默认只做 same-context target materialization，不运行 Pulse 搜索 / harvest / archive / bound pruning；
- 30/50/100 尚无专用 config 时，runbook 会显式记录 `scale_config_fallback_from_task20=true`，并通过命令行传入目标 logical graph；
- 固定 worker 的 current-probe 开关只作为 expected context 触发器；target materialization 会在任何 Pulse 搜索前返回结果；
- `worker_batch_size > 1` 时，只会合并同一 instance + expected context 的候选，并通过 `target_materialization_journeys` 批量物化；
- candidate worker 候选必须带完整 context / dual / cuts / branch / pool hash；
- 所有命令都不启用 sharded Pulse certificate 或 official lower-bound effect；
- 含 `->` 的 arc-option 配置通过 `shlex.join` 自动引用，不能手工去掉引号；
- 该 runbook 不是生产开关，跑完后仍需看 5/10 no-regression 和 20-task ROI。
