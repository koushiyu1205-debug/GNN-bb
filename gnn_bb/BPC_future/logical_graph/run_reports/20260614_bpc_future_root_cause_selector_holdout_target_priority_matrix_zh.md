# Selector Holdout Target Priority Matrix 报告

日期：2026-06-14

## 目的

本报告把 selector holdout gap 转成下一批补采优先 context。它只读
已有 CSV / summary，不运行 BPC / pricing / RMP / Pulse。

## 机器字段

```text
selector_holdout_target_priority_matrix = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_holdout_target_priority_matrix_audited
total_candidate_row_count = 630
context_count = 39
priority_context_count = 15
mixed_missing_full_snapshot_context_count = 7
noop_missing_full_snapshot_context_count = 12
manifest_priority_context_overlap_count = 9
uncovered_priority_context_count = 6
recommended_next_stage = collect_priority_negative_noop_mixed_full_snapshot_contexts
all_checks_pass = true
```

## 结论

现有候选行已经能定位下一批补采目标：优先补 mixed/noop contexts 的 complete full-snapshot 与 explicit-forbidden payload。已有 collection manifest 只覆盖一部分高优先 context，仍有 priority contexts 未覆盖；因此下一步应补采这些 target，而不是进入 production A/B、默认 worker 或 certificate gate。

## Category counts

```json
{
  "existing_collection_manifest_target": 10,
  "mixed_context_not_represented_as_complete_mixed": 7,
  "mixed_missing_full_snapshot": 7,
  "noop_missing_explicit_forbidden": 15,
  "noop_missing_full_snapshot": 12,
  "positive_missing_full_snapshot": 17
}
```

## Top priority targets

```json
[
  {
    "complete_explicit_forbidden_label_counts": {},
    "complete_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {},
    "complete_snapshot_row_count": 0,
    "context_hash": "774573a2964cb1c5",
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "mixed_missing_full_snapshot",
      "mixed_context_not_represented_as_complete_mixed",
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden",
      "positive_missing_full_snapshot",
      "existing_collection_manifest_target"
    ],
    "instance_counts": {
      "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001": 48
    },
    "label_counts": {
      "improved": 24,
      "noop": 24
    },
    "manifest_target": {
      "candidate_label_counts": {
        "improved": 12,
        "noop": 12
      },
      "candidate_row_count": 24,
      "collection_target_id": "selector_holdout_context_009",
      "failure_kind": "mixed_low_precision_or_recall_context",
      "needs_active_basis_snapshot_capture": true
    },
    "objective_delta_max": 0.0,
    "objective_delta_min": -8.163653188,
    "priority_score": 431,
    "row_count": 48,
    "sample_rows": [
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0032",
        "cg_iter": "2",
        "explicit_forbidden_signature_list_available": false,
        "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "sequence": "10-7-2",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "2,7,10",
        "true_reduced_cost": -12.0449185
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0001",
        "case_id": "capture_case_0032",
        "cg_iter": "2",
        "explicit_forbidden_signature_list_available": false,
        "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "sequence": "14-1",
        "single_impact_class": "improved",
        "single_objective_delta": -8.163653188,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "1,14",
        "true_reduced_cost": -11.794395583
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0002",
        "case_id": "capture_case_0032",
        "cg_iter": "2",
        "explicit_forbidden_signature_list_available": false,
        "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "sequence": "17-10-2",
        "single_impact_class": "improved",
        "single_objective_delta": -0.029549222,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "2,10,17",
        "true_reduced_cost": -10.9472235
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0003",
        "case_id": "capture_case_0032",
        "cg_iter": "2",
        "explicit_forbidden_signature_list_available": false,
        "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "sequence": "7-2-1",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "1,2,7",
        "true_reduced_cost": -10.5971645
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0004",
        "case_id": "capture_case_0032",
        "cg_iter": "2",
        "explicit_forbidden_signature_list_available": false,
        "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "sequence": "17-10-7",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "7,10,17",
        "true_reduced_cost": -10.07996
      }
    ],
    "source_class_counts": {
      "base_replay_selector": 24,
      "counterfactual_replay_dataset": 24
    },
    "source_csv_count": 2,
    "true_rc_max": -8.186793583,
    "true_rc_min": -12.0449185
  },
  {
    "complete_explicit_forbidden_label_counts": {},
    "complete_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {},
    "complete_snapshot_row_count": 0,
    "context_hash": "3c36c602289637b4",
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "mixed_missing_full_snapshot",
      "mixed_context_not_represented_as_complete_mixed",
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden",
      "positive_missing_full_snapshot",
      "existing_collection_manifest_target"
    ],
    "instance_counts": {
      "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000": 48
    },
    "label_counts": {
      "improved": 24,
      "noop": 24
    },
    "manifest_target": {
      "candidate_label_counts": {
        "improved": 12,
        "noop": 12
      },
      "candidate_row_count": 24,
      "collection_target_id": "selector_holdout_context_008",
      "failure_kind": "mixed_low_precision_or_recall_context",
      "needs_active_basis_snapshot_capture": true
    },
    "objective_delta_max": 0.0,
    "objective_delta_min": -32.287829667,
    "priority_score": 431,
    "row_count": 48,
    "sample_rows": [
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0002",
        "cg_iter": "2",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "12-16-17",
        "single_impact_class": "improved",
        "single_objective_delta": -32.287829667,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "12,16,17",
        "true_reduced_cost": -123.681417
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0001",
        "case_id": "capture_case_0002",
        "cg_iter": "2",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "17-12-4",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "4,12,17",
        "true_reduced_cost": -121.65471
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0002",
        "case_id": "capture_case_0002",
        "cg_iter": "2",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "14-12-16",
        "single_impact_class": "improved",
        "single_objective_delta": -7.888907667,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "12,14,16",
        "true_reduced_cost": -74.761131
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0003",
        "case_id": "capture_case_0002",
        "cg_iter": "2",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "14-12-17",
        "single_impact_class": "improved",
        "single_objective_delta": -23.973329,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "12,14,17",
        "true_reduced_cost": -74.197467
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0004",
        "case_id": "capture_case_0002",
        "cg_iter": "2",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "14-12-4",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "4,12,14",
        "true_reduced_cost": -73.864202
      }
    ],
    "source_class_counts": {
      "base_replay_selector": 24,
      "counterfactual_replay_dataset": 24
    },
    "source_csv_count": 2,
    "true_rc_max": -70.814616,
    "true_rc_min": -123.681417
  },
  {
    "complete_explicit_forbidden_label_counts": {},
    "complete_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {},
    "complete_snapshot_row_count": 0,
    "context_hash": "79de1ece885a7f67",
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "mixed_missing_full_snapshot",
      "mixed_context_not_represented_as_complete_mixed",
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden",
      "positive_missing_full_snapshot",
      "existing_collection_manifest_target"
    ],
    "instance_counts": {
      "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001": 30
    },
    "label_counts": {
      "improved": 6,
      "noop": 24
    },
    "manifest_target": {
      "candidate_label_counts": {
        "improved": 3,
        "noop": 12
      },
      "candidate_row_count": 15,
      "collection_target_id": "selector_holdout_context_010",
      "failure_kind": "mixed_low_precision_or_recall_context",
      "needs_active_basis_snapshot_capture": true
    },
    "objective_delta_max": 0.0,
    "objective_delta_min": -3.837824829,
    "priority_score": 413,
    "row_count": 30,
    "sample_rows": [
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0033",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "sequence": "17-8-12",
        "single_impact_class": "improved",
        "single_objective_delta": -3.837824829,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "8,12,17",
        "true_reduced_cost": -9.978344556
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0001",
        "case_id": "capture_case_0033",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "sequence": "4-19",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "4,19",
        "true_reduced_cost": -4.304435444
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0002",
        "case_id": "capture_case_0033",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "sequence": "8-12",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "8,12",
        "true_reduced_cost": -3.989702444
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0003",
        "case_id": "capture_case_0033",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "sequence": "17-10-9",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "9,10,17",
        "true_reduced_cost": -1.107536556
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0004",
        "case_id": "capture_case_0033",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "sequence": "2-7-19",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "2,7,19",
        "true_reduced_cost": -0.375033444
      }
    ],
    "source_class_counts": {
      "base_replay_selector": 15,
      "counterfactual_replay_dataset": 15
    },
    "source_csv_count": 2,
    "true_rc_max": -0.375033444,
    "true_rc_min": -9.978344556
  },
  {
    "complete_explicit_forbidden_label_counts": {},
    "complete_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {},
    "complete_snapshot_row_count": 0,
    "context_hash": "7f2e531534d18ad2",
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "mixed_missing_full_snapshot",
      "mixed_context_not_represented_as_complete_mixed",
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden",
      "positive_missing_full_snapshot",
      "existing_collection_manifest_target"
    ],
    "instance_counts": {
      "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000": 22
    },
    "label_counts": {
      "improved": 4,
      "noop": 18
    },
    "manifest_target": {
      "candidate_label_counts": {
        "improved": 2,
        "noop": 9
      },
      "candidate_row_count": 11,
      "collection_target_id": "selector_holdout_context_007",
      "failure_kind": "missed_positive_context",
      "needs_active_basis_snapshot_capture": true
    },
    "objective_delta_max": 0.0,
    "objective_delta_min": -0.168249,
    "priority_score": 405,
    "row_count": 22,
    "sample_rows": [
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0003",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "9-2-20",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "2,9,20",
        "true_reduced_cost": -8.341483
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0001",
        "case_id": "capture_case_0003",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "13-20-2",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "2,13,20",
        "true_reduced_cost": -5.527594
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0002",
        "case_id": "capture_case_0003",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "3-2-20",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "2,3,20",
        "true_reduced_cost": -4.938736
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0003",
        "case_id": "capture_case_0003",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "20-2",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "2,20",
        "true_reduced_cost": -4.467174
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0004",
        "case_id": "capture_case_0003",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "12-18-15",
        "single_impact_class": "improved",
        "single_objective_delta": -0.168249,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "12,15,18",
        "true_reduced_cost": -3.826192
      }
    ],
    "source_class_counts": {
      "base_replay_selector": 11,
      "counterfactual_replay_dataset": 11
    },
    "source_csv_count": 2,
    "true_rc_max": -0.586,
    "true_rc_min": -8.341483
  },
  {
    "complete_explicit_forbidden_label_counts": {},
    "complete_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {},
    "complete_snapshot_row_count": 0,
    "context_hash": "1db815e33b9ea471",
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "mixed_missing_full_snapshot",
      "mixed_context_not_represented_as_complete_mixed",
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden",
      "positive_missing_full_snapshot",
      "existing_collection_manifest_target"
    ],
    "instance_counts": {
      "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000": 12
    },
    "label_counts": {
      "improved": 2,
      "noop": 10
    },
    "manifest_target": {
      "candidate_label_counts": {
        "improved": 1,
        "noop": 5
      },
      "candidate_row_count": 6,
      "collection_target_id": "selector_holdout_context_006",
      "failure_kind": "missed_positive_context",
      "needs_active_basis_snapshot_capture": true
    },
    "objective_delta_max": 0.0,
    "objective_delta_min": -0.168249,
    "priority_score": 395,
    "row_count": 12,
    "sample_rows": [
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0009",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "9-2-20",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
        "task_set": "2,9,20",
        "true_reduced_cost": -8.341483
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0001",
        "case_id": "capture_case_0009",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "13-20-2",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
        "task_set": "2,13,20",
        "true_reduced_cost": -5.527594
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0002",
        "case_id": "capture_case_0009",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "3-2-20",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
        "task_set": "2,3,20",
        "true_reduced_cost": -4.938736
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0003",
        "case_id": "capture_case_0009",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "20-2",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
        "task_set": "2,20",
        "true_reduced_cost": -4.467174
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0004",
        "case_id": "capture_case_0009",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "12-18-15",
        "single_impact_class": "improved",
        "single_objective_delta": -0.168249,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
        "task_set": "12,15,18",
        "true_reduced_cost": -3.826192
      }
    ],
    "source_class_counts": {
      "base_replay_selector": 6,
      "counterfactual_replay_dataset": 6
    },
    "source_csv_count": 2,
    "true_rc_max": -0.586,
    "true_rc_min": -8.341483
  },
  {
    "complete_explicit_forbidden_label_counts": {},
    "complete_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {},
    "complete_snapshot_row_count": 0,
    "context_hash": "c27d904416342f6b",
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "mixed_missing_full_snapshot",
      "mixed_context_not_represented_as_complete_mixed",
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden",
      "positive_missing_full_snapshot"
    ],
    "instance_counts": {
      "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000": 16
    },
    "label_counts": {
      "improved": 14,
      "noop": 2
    },
    "manifest_target": null,
    "objective_delta_max": 0.0,
    "objective_delta_min": -13.61684075,
    "priority_score": 379,
    "row_count": 16,
    "sample_rows": [
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0010",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "14-18-4",
        "single_impact_class": "improved",
        "single_objective_delta": -13.61684075,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
        "task_set": "4,14,18",
        "true_reduced_cost": -64.283449
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0001",
        "case_id": "capture_case_0010",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "14-18-5",
        "single_impact_class": "improved",
        "single_objective_delta": -10.3751795,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
        "task_set": "5,14,18",
        "true_reduced_cost": -20.1912655
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0002",
        "case_id": "capture_case_0010",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "3-14-18",
        "single_impact_class": "improved",
        "single_objective_delta": -1.022723,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
        "task_set": "3,14,18",
        "true_reduced_cost": -11.861532
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0003",
        "case_id": "capture_case_0010",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "10-14-18",
        "single_impact_class": "improved",
        "single_objective_delta": -0.7338715,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
        "task_set": "10,14,18",
        "true_reduced_cost": -11.283829
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0004",
        "case_id": "capture_case_0010",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "14-18",
        "single_impact_class": "improved",
        "single_objective_delta": -0.654733,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
        "task_set": "14,18",
        "true_reduced_cost": -11.125552
      }
    ],
    "source_class_counts": {
      "base_replay_selector": 8,
      "other": 8
    },
    "source_csv_count": 2,
    "true_rc_max": -6.7223885,
    "true_rc_min": -64.283449
  },
  {
    "complete_explicit_forbidden_label_counts": {},
    "complete_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {},
    "complete_snapshot_row_count": 0,
    "context_hash": "794ecbd6fefaa1d7",
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "mixed_missing_full_snapshot",
      "mixed_context_not_represented_as_complete_mixed",
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden",
      "positive_missing_full_snapshot"
    ],
    "instance_counts": {
      "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000": 16
    },
    "label_counts": {
      "improved": 14,
      "noop": 2
    },
    "manifest_target": null,
    "objective_delta_max": 0.0,
    "objective_delta_min": -13.61684075,
    "priority_score": 379,
    "row_count": 16,
    "sample_rows": [
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0006",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "14-18-4",
        "single_impact_class": "improved",
        "single_objective_delta": -13.61684075,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
        "task_set": "4,14,18",
        "true_reduced_cost": -64.283449
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0001",
        "case_id": "capture_case_0006",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "14-18-5",
        "single_impact_class": "improved",
        "single_objective_delta": -10.3751795,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
        "task_set": "5,14,18",
        "true_reduced_cost": -20.1912655
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0002",
        "case_id": "capture_case_0006",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "3-14-18",
        "single_impact_class": "improved",
        "single_objective_delta": -1.022723,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
        "task_set": "3,14,18",
        "true_reduced_cost": -11.861532
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0003",
        "case_id": "capture_case_0006",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "10-14-18",
        "single_impact_class": "improved",
        "single_objective_delta": -0.7338715,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
        "task_set": "10,14,18",
        "true_reduced_cost": -11.283829
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0004",
        "case_id": "capture_case_0006",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "14-18",
        "single_impact_class": "improved",
        "single_objective_delta": -0.654733,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
        "task_set": "14,18",
        "true_reduced_cost": -11.125552
      }
    ],
    "source_class_counts": {
      "base_replay_selector": 8,
      "other": 8
    },
    "source_csv_count": 2,
    "true_rc_max": -6.7223885,
    "true_rc_min": -64.283449
  },
  {
    "complete_explicit_forbidden_label_counts": {},
    "complete_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {},
    "complete_snapshot_row_count": 0,
    "context_hash": "3f914a0d2b97fd27",
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden",
      "existing_collection_manifest_target"
    ],
    "instance_counts": {
      "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000": 10
    },
    "label_counts": {
      "noop": 10
    },
    "manifest_target": {
      "candidate_label_counts": {
        "noop": 5
      },
      "candidate_row_count": 5,
      "collection_target_id": "selector_holdout_context_001",
      "failure_kind": "false_positive_no_positive_context",
      "needs_active_basis_snapshot_capture": true
    },
    "objective_delta_max": 0.0,
    "objective_delta_min": 0.0,
    "priority_score": 163,
    "row_count": 10,
    "sample_rows": [
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0003",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "13-2-20",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "2,13,20",
        "true_reduced_cost": -6.110727
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0001",
        "case_id": "capture_case_0003",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "12-18-5",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "5,12,18",
        "true_reduced_cost": -5.95738825
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0002",
        "case_id": "capture_case_0003",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "10-2-20",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "2,10,20",
        "true_reduced_cost": -5.153952
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0003",
        "case_id": "capture_case_0003",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "3-2-20",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "2,3,20",
        "true_reduced_cost": -4.938736
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0004",
        "case_id": "capture_case_0003",
        "cg_iter": "3",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "20-2",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "task_set": "2,20",
        "true_reduced_cost": -4.467174
      }
    ],
    "source_class_counts": {
      "base_replay_selector": 5,
      "other": 5
    },
    "source_csv_count": 2,
    "true_rc_max": -4.467174,
    "true_rc_min": -6.110727
  },
  {
    "complete_explicit_forbidden_label_counts": {},
    "complete_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {},
    "complete_snapshot_row_count": 0,
    "context_hash": "d60fcf4b919b7d22",
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden",
      "existing_collection_manifest_target"
    ],
    "instance_counts": {
      "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000": 6
    },
    "label_counts": {
      "noop": 6
    },
    "manifest_target": {
      "candidate_label_counts": {
        "noop": 3
      },
      "candidate_row_count": 3,
      "collection_target_id": "selector_holdout_context_003",
      "failure_kind": "false_positive_no_positive_context",
      "needs_active_basis_snapshot_capture": true
    },
    "objective_delta_max": 0.0,
    "objective_delta_min": 0.0,
    "priority_score": 159,
    "row_count": 6,
    "sample_rows": [
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0020",
        "cg_iter": "2",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "12-18-5",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_pricing_time_0_6_20_only__r0.jsonl",
        "task_set": "5,12,18",
        "true_reduced_cost": -128.547499
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0024",
        "cg_iter": "2",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "12-18-5",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_pricing_time_0_6_20_only__r1.jsonl",
        "task_set": "5,12,18",
        "true_reduced_cost": -128.547499
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0028",
        "cg_iter": "2",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "12-18-5",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_pricing_time_0_6_20_only__r2.jsonl",
        "task_set": "5,12,18",
        "true_reduced_cost": -128.547499
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0020",
        "cg_iter": "2",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "12-18-5",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "counterfactual_replay_dataset",
        "source_csv": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/impact/candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_pricing_time_0_6_20_only__r0.jsonl",
        "task_set": "5,12,18",
        "true_reduced_cost": -128.547499
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0024",
        "cg_iter": "2",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "12-18-5",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "counterfactual_replay_dataset",
        "source_csv": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/impact/candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_pricing_time_0_6_20_only__r1.jsonl",
        "task_set": "5,12,18",
        "true_reduced_cost": -128.547499
      }
    ],
    "source_class_counts": {
      "base_replay_selector": 3,
      "counterfactual_replay_dataset": 3
    },
    "source_csv_count": 2,
    "true_rc_max": -128.547499,
    "true_rc_min": -128.547499
  },
  {
    "complete_explicit_forbidden_label_counts": {},
    "complete_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {},
    "complete_snapshot_row_count": 0,
    "context_hash": "c5a59a95c2c9971a",
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden",
      "existing_collection_manifest_target"
    ],
    "instance_counts": {
      "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001": 6
    },
    "label_counts": {
      "noop": 6
    },
    "manifest_target": {
      "candidate_label_counts": {
        "noop": 3
      },
      "candidate_row_count": 3,
      "collection_target_id": "selector_holdout_context_002",
      "failure_kind": "false_positive_no_positive_context",
      "needs_active_basis_snapshot_capture": true
    },
    "objective_delta_max": 0.0,
    "objective_delta_min": 0.0,
    "priority_score": 159,
    "row_count": 6,
    "sample_rows": [
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0046",
        "cg_iter": "4",
        "explicit_forbidden_signature_list_available": false,
        "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "sequence": "10-17-2-7",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_l1_previous_dual_stabilization_20_only__r0.jsonl",
        "task_set": "2,7,10,17",
        "true_reduced_cost": -34.525806
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0050",
        "cg_iter": "4",
        "explicit_forbidden_signature_list_available": false,
        "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "sequence": "10-17-2-7",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_l1_previous_dual_stabilization_20_only__r1.jsonl",
        "task_set": "2,7,10,17",
        "true_reduced_cost": -34.525806
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0054",
        "cg_iter": "4",
        "explicit_forbidden_signature_list_available": false,
        "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "sequence": "10-17-2-7",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_l1_previous_dual_stabilization_20_only__r2.jsonl",
        "task_set": "2,7,10,17",
        "true_reduced_cost": -34.525806
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0046",
        "cg_iter": "4",
        "explicit_forbidden_signature_list_available": false,
        "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "sequence": "10-17-2-7",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "counterfactual_replay_dataset",
        "source_csv": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/impact/candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_l1_previous_dual_stabilization_20_only__r0.jsonl",
        "task_set": "2,7,10,17",
        "true_reduced_cost": -34.525806
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0050",
        "cg_iter": "4",
        "explicit_forbidden_signature_list_available": false,
        "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
        "sequence": "10-17-2-7",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "counterfactual_replay_dataset",
        "source_csv": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/impact/candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_l1_previous_dual_stabilization_20_only__r1.jsonl",
        "task_set": "2,7,10,17",
        "true_reduced_cost": -34.525806
      }
    ],
    "source_class_counts": {
      "base_replay_selector": 3,
      "counterfactual_replay_dataset": 3
    },
    "source_csv_count": 2,
    "true_rc_max": -34.525806,
    "true_rc_min": -34.525806
  },
  {
    "complete_explicit_forbidden_label_counts": {},
    "complete_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {},
    "complete_snapshot_row_count": 0,
    "context_hash": "46e7a2883459d4fb",
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden"
    ],
    "instance_counts": {
      "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000": 8
    },
    "label_counts": {
      "noop": 8
    },
    "manifest_target": null,
    "objective_delta_max": 0.0,
    "objective_delta_min": 0.0,
    "priority_score": 141,
    "row_count": 8,
    "sample_rows": [
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0007",
        "cg_iter": "4",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "13-2-20",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
        "task_set": "2,13,20",
        "true_reduced_cost": -6.110727
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0001",
        "case_id": "capture_case_0007",
        "cg_iter": "4",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "10-2-20",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
        "task_set": "2,10,20",
        "true_reduced_cost": -5.153952
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0002",
        "case_id": "capture_case_0007",
        "cg_iter": "4",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "3-2-20",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
        "task_set": "2,3,20",
        "true_reduced_cost": -4.938736
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0003",
        "case_id": "capture_case_0007",
        "cg_iter": "4",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "20-2",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
        "task_set": "2,20",
        "true_reduced_cost": -4.467174
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0007",
        "cg_iter": "4",
        "explicit_forbidden_signature_list_available": false,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "sequence": "13-2-20",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "other",
        "source_csv": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/impact/candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
        "task_set": "2,13,20",
        "true_reduced_cost": -6.110727
      }
    ],
    "source_class_counts": {
      "base_replay_selector": 4,
      "other": 4
    },
    "source_csv_count": 2,
    "true_rc_max": -4.467174,
    "true_rc_min": -6.110727
  },
  {
    "complete_explicit_forbidden_label_counts": {},
    "complete_explicit_forbidden_row_count": 0,
    "complete_snapshot_label_counts": {},
    "complete_snapshot_row_count": 0,
    "context_hash": "7b9a35f8f7c6581a",
    "explicit_forbidden_label_counts": {},
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden"
    ],
    "instance_counts": {
      "very_small": 2
    },
    "label_counts": {
      "noop": 2
    },
    "manifest_target": null,
    "objective_delta_max": 0.0,
    "objective_delta_min": 0.0,
    "priority_score": 135,
    "row_count": 2,
    "sample_rows": [
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0001",
        "cg_iter": "1",
        "explicit_forbidden_signature_list_available": false,
        "instance": "very_small",
        "sequence": "1",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "base_replay_selector",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/combined/combined_candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_replay_feasible_smoke_20260613/logs/very_small_duplicate_noop_capture.jsonl",
        "task_set": "1",
        "true_reduced_cost": -91.914096
      },
      {
        "active_basis_snapshot_complete_before": false,
        "candidate_id": "journey_0000",
        "case_id": "capture_case_0001",
        "cg_iter": "1",
        "explicit_forbidden_signature_list_available": false,
        "instance": "very_small",
        "sequence": "1",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "source_class": "counterfactual_replay_dataset",
        "source_csv": "BPC_future/results/root_cause_counterfactual_replay_impact_dataset_20260613/duplicate_noop_smoke/candidate_impact_rows.csv",
        "source_file": "BPC_future/results/root_cause_counterfactual_replay_feasible_smoke_20260613/logs/very_small_duplicate_noop_capture.jsonl",
        "task_set": "1",
        "true_reduced_cost": -91.914096
      }
    ],
    "source_class_counts": {
      "base_replay_selector": 1,
      "counterfactual_replay_dataset": 1
    },
    "source_csv_count": 2,
    "true_rc_max": -91.914096,
    "true_rc_min": -91.914096
  }
]
```

## Uncovered priority contexts

```json
[
  "1b95888aae8dd7c2",
  "46e7a2883459d4fb",
  "794ecbd6fefaa1d7",
  "7b9a35f8f7c6581a",
  "988c728382b4a376",
  "c27d904416342f6b"
]
```

## Checks

```json
{
  "candidate_rows_present": true,
  "collection_manifest_passed": true,
  "diagnostic_not_solver_run": true,
  "gap_matrix_passed": true,
  "gap_matrix_recommends_negative_mixed": true,
  "manifest_covers_some_priority_contexts": true,
  "mixed_missing_full_snapshot_contexts_present": true,
  "noop_missing_full_snapshot_contexts_present": true,
  "priority_targets_have_samples": true,
  "uncovered_priority_contexts_identified": true
}
```
