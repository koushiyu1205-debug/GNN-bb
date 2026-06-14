# Root Cause Selector Context Trajectory Capture Protocol 报告

日期：2026-06-14

## 目的

本报告把 priority target / capture miss 证据转成下一轮 selector holdout
补采协议。它只读已有 summary，不运行 BPC / pricing / RMP / Pulse，也不
改变 worker 或 certificate 行为。

```text
root_cause_selector_context_trajectory_capture_protocol = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_context_trajectory_capture_protocol_ready
source_profile_rerun_is_not_sufficient = true
same_active_hash_is_not_sufficient = true
exact_context_component_count = 9
required_capture_payload_count = 9
all_checks_pass = true
```

## Exact Context Components

- `context_hash`
- `active_hash_before`
- `pool_signature_hash`
- `forbidden_signature_hash`
- `pool_task_set_hash`
- `returned_task_set_hash`
- `rmp_objective_before`
- `pricing_state`
- `pricing_best_reduced_cost`

## Required Capture Payload

- `no_certificate_effect`
- `complete_active_basis_snapshot`
- `complete_returned_batch`
- `explicit_forbidden_signature_payload`
- `pool_signature_payload`
- `true_dual_hash_and_vector`
- `cuts_hash`
- `branch_hash`
- `pricing_config_hash`

## Match Policy

- `all_exact_components_match` -> `fills_target_context`：The replay/capture row belongs to the intended pricing universe.
- `same_active_hash_but_component_drift` -> `new_context_sample_only`：Same active hash is not sufficient: pool, forbidden, returned batch, RMP objective, or pricing outcome can change the downstream trajectory.
- `source_active_hash_not_reached` -> `new_context_sample_only`：The source profile rerun did not reach the intended active-basis neighborhood, so it cannot close the target holdout gap.
- `missing_required_payload` -> `reject_for_selector_holdout`：Incomplete payload would make the selector label unverifiable.

## Collection Steps

- collect no-certificate-effect capture events for priority mixed/noop contexts
- record every reached context instead of only checking target context hashes
- classify exact target hits by full component match, not by active hash alone
- route near misses into new context rows with their own hashes and components
- rerun selector holdout only after mixed/noop full-snapshot rows are present

## Target Priority Evidence

```json
{
  "mixed_missing_full_snapshot_context_count": 7,
  "noop_missing_full_snapshot_context_count": 12,
  "priority_context_count": 15,
  "recommended_next_stage": "collect_priority_negative_noop_mixed_full_snapshot_contexts",
  "top_targets": [
    {
      "complete_snapshot_row_count": 0,
      "context_hash": "774573a2964cb1c5",
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
      "priority_score": 431,
      "row_count": 48
    },
    {
      "complete_snapshot_row_count": 0,
      "context_hash": "3c36c602289637b4",
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
      "priority_score": 431,
      "row_count": 48
    },
    {
      "complete_snapshot_row_count": 0,
      "context_hash": "79de1ece885a7f67",
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
      "priority_score": 413,
      "row_count": 30
    },
    {
      "complete_snapshot_row_count": 0,
      "context_hash": "7f2e531534d18ad2",
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
      "priority_score": 405,
      "row_count": 22
    },
    {
      "complete_snapshot_row_count": 0,
      "context_hash": "1db815e33b9ea471",
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
      "priority_score": 395,
      "row_count": 12
    },
    {
      "complete_snapshot_row_count": 0,
      "context_hash": "c27d904416342f6b",
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
      "priority_score": 379,
      "row_count": 16
    },
    {
      "complete_snapshot_row_count": 0,
      "context_hash": "794ecbd6fefaa1d7",
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
      "priority_score": 379,
      "row_count": 16
    },
    {
      "complete_snapshot_row_count": 0,
      "context_hash": "3f914a0d2b97fd27",
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
      "priority_score": 163,
      "row_count": 10
    }
  ],
  "uncovered_priority_context_count": 6
}
```

## Priority Capture Miss Evidence

```json
{
  "exact_hit_context_count": 0,
  "expected_context_count": 3,
  "observed_event_count": 12,
  "same_active_component_drift_context_count": 1,
  "source_active_hash_missing_context_count": 2
}
```

## Checks

```json
{
  "exact_match_requires_full_components": true,
  "mixed_noop_targets_exist": true,
  "next_action_plan_passed": true,
  "no_production_ab_or_certificate_gate": true,
  "payload_requires_no_certificate_effect": true,
  "priority_capture_miss_passed": true,
  "protocol_is_diagnostic_only": true,
  "same_active_hash_is_not_sufficient": true,
  "source_active_hash_miss_is_observed": true,
  "source_profile_rerun_is_not_sufficient": true,
  "target_priority_matrix_passed": true
}
```
