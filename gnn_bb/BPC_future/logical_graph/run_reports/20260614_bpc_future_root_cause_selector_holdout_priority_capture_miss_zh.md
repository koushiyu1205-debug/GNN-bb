# Root Cause Selector Holdout Priority Capture Miss 报告

日期：2026-06-14

## 目的

本报告解释 priority collection 已安全采集但没有命中目标 context 的原因。
它只读 runbook、capture audit 和 JSONL，不运行 BPC / pricing / RMP / Pulse，
也不改变 solver 行为。

## 机器字段

```text
root_cause_selector_holdout_priority_capture_miss = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_holdout_priority_capture_miss_diagnosed
expected_context_count = 3
exact_hit_context_count = 0
source_active_hash_missing_context_count = 2
same_active_component_drift_context_count = 1
observed_event_count = 12
observed_unique_context_count = 6
all_checks_pass = true
```

## 结论

priority collection 补采链路是安全的，但没有复现目标上下文：目标 context 中一部分连历史 active hash 都没到达，另一部分虽然到达同 active hash，但 pool / forbidden / returned-batch 组成不同。这进一步说明 active hash 或 source profile 本身不足以作为生产 selector 或 replay key。

priority collection did not miss because the capture path was unsafe; it missed because the rerun followed a different trajectory.  Some target contexts never reached the historical active hash, and the target that did share active hash still diverged in pool/forbidden/returned-batch components.

## Command Summaries

```json
[
  {
    "command_id": "selector_priority_capture_001",
    "comparisons": [
      {
        "context_hash": "46e7a2883459d4fb",
        "exact_hit_count": 0,
        "miss_class": "same_active_but_returned_batch_or_component_drift",
        "same_active_event_count": 6,
        "same_active_events_sample": [
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "c0259858cde05f02",
            "forbidden_signature_hash": "7e455bb80c6e0673",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "38e26a8d1170a5e6",
            "pool_task_set_hash": "f15b6208a8de2f68",
            "pricing_best_reduced_cost": null,
            "pricing_kind": "heuristic",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.780917
          },
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "c0259858cde05f02",
            "forbidden_signature_hash": "7e455bb80c6e0673",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "38e26a8d1170a5e6",
            "pool_task_set_hash": "f15b6208a8de2f68",
            "pricing_best_reduced_cost": 0.0,
            "pricing_kind": "exact",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.780917
          },
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "4da9e3127c0713c4",
            "forbidden_signature_hash": "958acd2bcfaf88ca",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "807c3f4b9f083a75",
            "pool_task_set_hash": "0f732c335b64446c",
            "pricing_best_reduced_cost": null,
            "pricing_kind": "heuristic",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.81512425
          },
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "4da9e3127c0713c4",
            "forbidden_signature_hash": "958acd2bcfaf88ca",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "807c3f4b9f083a75",
            "pool_task_set_hash": "0f732c335b64446c",
            "pricing_best_reduced_cost": 0.0,
            "pricing_kind": "exact",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.81512425
          },
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "be5e5e89972d48fe",
            "forbidden_signature_hash": "9415676456386f04",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "9b512f66d8662bc5",
            "pool_task_set_hash": "bb266ce7df1e9a54",
            "pricing_best_reduced_cost": null,
            "pricing_kind": "heuristic",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.780917
          },
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "be5e5e89972d48fe",
            "forbidden_signature_hash": "9415676456386f04",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "9b512f66d8662bc5",
            "pool_task_set_hash": "bb266ce7df1e9a54",
            "pricing_best_reduced_cost": 0.0,
            "pricing_kind": "exact",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.780917
          }
        ],
        "same_active_field_counts": {
          "active_hash_before": 6,
          "forbidden_signature_hash": 0,
          "pool_journey_count": 0,
          "pool_signature_hash": 0,
          "pool_task_set_hash": 0,
          "pricing_best_reduced_cost": 0,
          "pricing_state": 0,
          "returned_task_set_hash": 0,
          "rmp_objective_before": 0
        },
        "same_active_returned_task_sets_same_count": 0,
        "same_cg_iter_event_count": 0,
        "same_cg_iter_events_sample": [],
        "same_cg_iter_field_counts": {
          "active_hash_before": 0,
          "forbidden_signature_hash": 0,
          "pool_journey_count": 0,
          "pool_signature_hash": 0,
          "pool_task_set_hash": 0,
          "pricing_best_reduced_cost": 0,
          "pricing_state": 0,
          "returned_task_set_hash": 0,
          "rmp_objective_before": 0
        },
        "source_event": {
          "active_hash_before": "f0b96be45c5015c9",
          "captured_journey_count": 4,
          "cg_iter": 4,
          "context_hash": "46e7a2883459d4fb",
          "forbidden_signature_hash": "3687de2e101ec200",
          "log_path": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
          "pool_journey_count": 187,
          "pool_signature_hash": "c636dcc7cf1246b5",
          "pool_task_set_hash": "f0d282513afc4fd4",
          "pricing_best_reduced_cost": -6.110727,
          "pricing_kind": "heuristic",
          "pricing_state": "FOUND_NEGATIVE",
          "returned_journey_count": 4,
          "returned_task_set_hash": "2,10,20|2,13,20|2,20|2,3,20",
          "rmp_objective_before": 766.96965575
        }
      },
      {
        "context_hash": "794ecbd6fefaa1d7",
        "exact_hit_count": 0,
        "miss_class": "source_active_hash_not_reached",
        "same_active_event_count": 0,
        "same_active_events_sample": [],
        "same_active_field_counts": {
          "active_hash_before": 0,
          "forbidden_signature_hash": 0,
          "pool_journey_count": 0,
          "pool_signature_hash": 0,
          "pool_task_set_hash": 0,
          "pricing_best_reduced_cost": 0,
          "pricing_state": 0,
          "returned_task_set_hash": 0,
          "rmp_objective_before": 0
        },
        "same_active_returned_task_sets_same_count": 0,
        "same_cg_iter_event_count": 6,
        "same_cg_iter_events_sample": [
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "c0259858cde05f02",
            "forbidden_signature_hash": "7e455bb80c6e0673",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "38e26a8d1170a5e6",
            "pool_task_set_hash": "f15b6208a8de2f68",
            "pricing_best_reduced_cost": null,
            "pricing_kind": "heuristic",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.780917
          },
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "c0259858cde05f02",
            "forbidden_signature_hash": "7e455bb80c6e0673",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "38e26a8d1170a5e6",
            "pool_task_set_hash": "f15b6208a8de2f68",
            "pricing_best_reduced_cost": 0.0,
            "pricing_kind": "exact",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.780917
          },
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "4da9e3127c0713c4",
            "forbidden_signature_hash": "958acd2bcfaf88ca",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "807c3f4b9f083a75",
            "pool_task_set_hash": "0f732c335b64446c",
            "pricing_best_reduced_cost": null,
            "pricing_kind": "heuristic",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.81512425
          },
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "4da9e3127c0713c4",
            "forbidden_signature_hash": "958acd2bcfaf88ca",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "807c3f4b9f083a75",
            "pool_task_set_hash": "0f732c335b64446c",
            "pricing_best_reduced_cost": 0.0,
            "pricing_kind": "exact",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.81512425
          },
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "be5e5e89972d48fe",
            "forbidden_signature_hash": "9415676456386f04",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "9b512f66d8662bc5",
            "pool_task_set_hash": "bb266ce7df1e9a54",
            "pricing_best_reduced_cost": null,
            "pricing_kind": "heuristic",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.780917
          },
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "be5e5e89972d48fe",
            "forbidden_signature_hash": "9415676456386f04",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "9b512f66d8662bc5",
            "pool_task_set_hash": "bb266ce7df1e9a54",
            "pricing_best_reduced_cost": 0.0,
            "pricing_kind": "exact",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.780917
          }
        ],
        "same_cg_iter_field_counts": {
          "active_hash_before": 0,
          "forbidden_signature_hash": 0,
          "pool_journey_count": 6,
          "pool_signature_hash": 0,
          "pool_task_set_hash": 0,
          "pricing_best_reduced_cost": 0,
          "pricing_state": 0,
          "returned_task_set_hash": 0,
          "rmp_objective_before": 0
        },
        "source_event": {
          "active_hash_before": "16862add48072518",
          "captured_journey_count": 8,
          "cg_iter": 3,
          "context_hash": "794ecbd6fefaa1d7",
          "forbidden_signature_hash": "cf620c69803f678c",
          "log_path": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
          "pool_journey_count": 180,
          "pool_signature_hash": "e1bb214b2f47ddc5",
          "pool_task_set_hash": "ebf58210ad9b65f3",
          "pricing_best_reduced_cost": -64.283449,
          "pricing_kind": "heuristic",
          "pricing_state": "FOUND_NEGATIVE",
          "returned_journey_count": 8,
          "returned_task_set_hash": "10,14,18|14,15,18|14,18|3,14,18|4,14,18|4,8,14|5,12,18|5,14,18",
          "rmp_objective_before": 780.5864965
        }
      },
      {
        "context_hash": "c27d904416342f6b",
        "exact_hit_count": 0,
        "miss_class": "source_active_hash_not_reached",
        "same_active_event_count": 0,
        "same_active_events_sample": [],
        "same_active_field_counts": {
          "active_hash_before": 0,
          "forbidden_signature_hash": 0,
          "pool_journey_count": 0,
          "pool_signature_hash": 0,
          "pool_task_set_hash": 0,
          "pricing_best_reduced_cost": 0,
          "pricing_state": 0,
          "returned_task_set_hash": 0,
          "rmp_objective_before": 0
        },
        "same_active_returned_task_sets_same_count": 0,
        "same_cg_iter_event_count": 6,
        "same_cg_iter_events_sample": [
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "c0259858cde05f02",
            "forbidden_signature_hash": "7e455bb80c6e0673",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "38e26a8d1170a5e6",
            "pool_task_set_hash": "f15b6208a8de2f68",
            "pricing_best_reduced_cost": null,
            "pricing_kind": "heuristic",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.780917
          },
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "c0259858cde05f02",
            "forbidden_signature_hash": "7e455bb80c6e0673",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "38e26a8d1170a5e6",
            "pool_task_set_hash": "f15b6208a8de2f68",
            "pricing_best_reduced_cost": 0.0,
            "pricing_kind": "exact",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.780917
          },
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "4da9e3127c0713c4",
            "forbidden_signature_hash": "958acd2bcfaf88ca",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "807c3f4b9f083a75",
            "pool_task_set_hash": "0f732c335b64446c",
            "pricing_best_reduced_cost": null,
            "pricing_kind": "heuristic",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.81512425
          },
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "4da9e3127c0713c4",
            "forbidden_signature_hash": "958acd2bcfaf88ca",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "807c3f4b9f083a75",
            "pool_task_set_hash": "0f732c335b64446c",
            "pricing_best_reduced_cost": 0.0,
            "pricing_kind": "exact",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.81512425
          },
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "be5e5e89972d48fe",
            "forbidden_signature_hash": "9415676456386f04",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "9b512f66d8662bc5",
            "pool_task_set_hash": "bb266ce7df1e9a54",
            "pricing_best_reduced_cost": null,
            "pricing_kind": "heuristic",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.780917
          },
          {
            "active_hash_before": "f0b96be45c5015c9",
            "captured_journey_count": 0,
            "cg_iter": 3,
            "context_hash": "be5e5e89972d48fe",
            "forbidden_signature_hash": "9415676456386f04",
            "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
            "pool_journey_count": 180,
            "pool_signature_hash": "9b512f66d8662bc5",
            "pool_task_set_hash": "bb266ce7df1e9a54",
            "pricing_best_reduced_cost": 0.0,
            "pricing_kind": "exact",
            "pricing_state": "INCOMPLETE_LIMIT",
            "returned_journey_count": 0,
            "returned_task_set_hash": "",
            "rmp_objective_before": 766.780917
          }
        ],
        "same_cg_iter_field_counts": {
          "active_hash_before": 0,
          "forbidden_signature_hash": 0,
          "pool_journey_count": 6,
          "pool_signature_hash": 0,
          "pool_task_set_hash": 0,
          "pricing_best_reduced_cost": 0,
          "pricing_state": 0,
          "returned_task_set_hash": 0,
          "rmp_objective_before": 0
        },
        "source_event": {
          "active_hash_before": "16862add48072518",
          "captured_journey_count": 8,
          "cg_iter": 3,
          "context_hash": "c27d904416342f6b",
          "forbidden_signature_hash": "ff19e0daf4e1f3b9",
          "log_path": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl",
          "pool_journey_count": 180,
          "pool_signature_hash": "319a23581b696187",
          "pool_task_set_hash": "ebf58210ad9b65f3",
          "pricing_best_reduced_cost": -64.283449,
          "pricing_kind": "heuristic",
          "pricing_state": "FOUND_NEGATIVE",
          "returned_journey_count": 8,
          "returned_task_set_hash": "10,14,18|14,15,18|14,18|3,14,18|4,14,18|4,8,14|5,12,18|5,14,18",
          "rmp_objective_before": 780.5864965
        }
      }
    ],
    "expected_context_hashes": [
      "46e7a2883459d4fb",
      "794ecbd6fefaa1d7",
      "c27d904416342f6b"
    ],
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "observed_active_hashes": [
      "427b1308ea279e0c",
      "c6ea96127d7c5d7b",
      "f0b96be45c5015c9"
    ],
    "observed_context_hashes": [
      "080a188d2484ee3e",
      "080a188d2484ee3e",
      "080a188d2484ee3e",
      "4da9e3127c0713c4",
      "4da9e3127c0713c4",
      "691e9f3cc93a695c",
      "a9831c8a34a4a2f4",
      "a9831c8a34a4a2f4",
      "be5e5e89972d48fe",
      "be5e5e89972d48fe",
      "c0259858cde05f02",
      "c0259858cde05f02"
    ],
    "observed_event_count": 12,
    "observed_events_by_repeat": {
      "0": 4,
      "1": 4,
      "2": 4
    },
    "observed_pricing_state_counts": {
      "FOUND_NEGATIVE": 6,
      "INCOMPLETE_LIMIT": 6
    },
    "observed_unique_context_hashes": [
      "080a188d2484ee3e",
      "4da9e3127c0713c4",
      "691e9f3cc93a695c",
      "a9831c8a34a4a2f4",
      "be5e5e89972d48fe",
      "c0259858cde05f02"
    ],
    "output_dir": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8",
    "profile": "experimental_early_new_task_set_quota_3_20_only",
    "source_event_count": 3
  }
]
```

## 检查项

```json
{
  "capture_audit_complete_active_basis": true,
  "capture_audit_passed": true,
  "capture_audit_safe_no_certificate": true,
  "expected_contexts_were_not_hit": true,
  "miss_explained_by_active_or_component_drift": true,
  "observed_events_exist": true,
  "runbook_passed": true
}
```
