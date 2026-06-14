# Root Cause Selector Holdout target002 Probe Matrix 报告

日期：2026-06-14

## 目的

本报告汇总 target002 剩余 exact context 缺口的最小 probe matrix。它只读
已经完成的 probe 日志，不运行 BPC / pricing / RMP / Pulse，也不改变
worker、certificate 或 solver 默认行为。

## 机器字段

```text
root_cause_selector_holdout_target002_probe_matrix = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_holdout_target002_probe_matrix_audited
target_context_hash = 3f914a0d2b97fd27
probe_count = 5
reproduction_probe_count = 4
source_target_hit_count = 1
target_recovered_probe_count = 0
all_checks_pass = true
```

## 结论

原始 target002 pt0.3 capture 中存在目标 exact context，但当前代码下的 config-matched active-basis 补采、去 active-basis 补采、实例别名补采、多 profile 顺序补采均未复现该 context。剩余缺口因此不是某一个采集字段或命令分组开关导致，而是 time-limit/returned-batch trajectory 本身在临界区域不稳定；它继续阻塞 production selector holdout。

## Probe Summary

| probe | role | events | target hits | found negative | incomplete | contexts |
|---|---:|---:|---:|---:|---:|---:|
| historical_source | source | 10 | 1 | 10 | 0 | 7 |
| config_matched_active_basis_capture | new_capture | 12 | 0 | 6 | 6 | 7 |
| no_active_basis_capture | probe | 7 | 0 | 7 | 0 | 3 |
| alias_instance_capture | probe | 7 | 0 | 7 | 0 | 4 |
| multi_profile_order_capture | probe | 6 | 0 | 6 | 0 | 2 |

## Probe Paths

```json
[
  {
    "path": [
      {
        "active_hash_before": "c6ea96127d7c5d7b",
        "cg_iter": 1,
        "context_hash": "080a188d2484ee3e",
        "pricing_best_reduced_cost": -139.913748,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "0",
        "returned_journey_count": 8,
        "rmp_objective_before": 1061.554044
      },
      {
        "active_hash_before": "427b1308ea279e0c",
        "cg_iter": 2,
        "context_hash": "827ddca748a70f26",
        "pricing_best_reduced_cost": -123.353561,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "0",
        "returned_journey_count": 8,
        "rmp_objective_before": 859.3571305
      },
      {
        "active_hash_before": "f0b96be45c5015c9",
        "cg_iter": 3,
        "context_hash": "3f914a0d2b97fd27",
        "pricing_best_reduced_cost": -6.110727,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "0",
        "returned_journey_count": 5,
        "rmp_objective_before": 766.81749575
      },
      {
        "active_hash_before": "c6ea96127d7c5d7b",
        "cg_iter": 1,
        "context_hash": "080a188d2484ee3e",
        "pricing_best_reduced_cost": -139.913748,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "1",
        "returned_journey_count": 8,
        "rmp_objective_before": 1061.554044
      },
      {
        "active_hash_before": "427b1308ea279e0c",
        "cg_iter": 2,
        "context_hash": "827ddca748a70f26",
        "pricing_best_reduced_cost": -123.353561,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "1",
        "returned_journey_count": 8,
        "rmp_objective_before": 859.3571305
      },
      {
        "active_hash_before": "16862add48072518",
        "cg_iter": 3,
        "context_hash": "794ecbd6fefaa1d7",
        "pricing_best_reduced_cost": -64.283449,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "1",
        "returned_journey_count": 8,
        "rmp_objective_before": 780.5864965
      },
      {
        "active_hash_before": "f0b96be45c5015c9",
        "cg_iter": 4,
        "context_hash": "46e7a2883459d4fb",
        "pricing_best_reduced_cost": -6.110727,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "1",
        "returned_journey_count": 4,
        "rmp_objective_before": 766.96965575
      },
      {
        "active_hash_before": "c6ea96127d7c5d7b",
        "cg_iter": 1,
        "context_hash": "080a188d2484ee3e",
        "pricing_best_reduced_cost": -139.913748,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "2",
        "returned_journey_count": 8,
        "rmp_objective_before": 1061.554044
      },
      {
        "active_hash_before": "427b1308ea279e0c",
        "cg_iter": 2,
        "context_hash": "691a0f9c2446aabc",
        "pricing_best_reduced_cost": -123.353561,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "2",
        "returned_journey_count": 8,
        "rmp_objective_before": 859.3571305
      },
      {
        "active_hash_before": "16862add48072518",
        "cg_iter": 3,
        "context_hash": "c27d904416342f6b",
        "pricing_best_reduced_cost": -64.283449,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "2",
        "returned_journey_count": 8,
        "rmp_objective_before": 780.5864965
      }
    ],
    "probe_id": "historical_source"
  },
  {
    "path": [
      {
        "active_hash_before": "c6ea96127d7c5d7b",
        "cg_iter": 1,
        "context_hash": "080a188d2484ee3e",
        "pricing_best_reduced_cost": -139.913748,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "0",
        "returned_journey_count": 8,
        "rmp_objective_before": 1061.554044
      },
      {
        "active_hash_before": "427b1308ea279e0c",
        "cg_iter": 2,
        "context_hash": "827ddca748a70f26",
        "pricing_best_reduced_cost": -123.353561,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "0",
        "returned_journey_count": 8,
        "rmp_objective_before": 859.3571305
      },
      {
        "active_hash_before": "f0b96be45c5015c9",
        "cg_iter": 3,
        "context_hash": "71cf005b699054ed",
        "pricing_best_reduced_cost": null,
        "pricing_state": "INCOMPLETE_LIMIT",
        "repeat": "0",
        "returned_journey_count": 0,
        "rmp_objective_before": 766.843656
      },
      {
        "active_hash_before": "f0b96be45c5015c9",
        "cg_iter": 3,
        "context_hash": "71cf005b699054ed",
        "pricing_best_reduced_cost": 0.0,
        "pricing_state": "INCOMPLETE_LIMIT",
        "repeat": "0",
        "returned_journey_count": 0,
        "rmp_objective_before": 766.843656
      },
      {
        "active_hash_before": "c6ea96127d7c5d7b",
        "cg_iter": 1,
        "context_hash": "080a188d2484ee3e",
        "pricing_best_reduced_cost": -139.913748,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "1",
        "returned_journey_count": 8,
        "rmp_objective_before": 1061.554044
      },
      {
        "active_hash_before": "427b1308ea279e0c",
        "cg_iter": 2,
        "context_hash": "691e9f3cc93a695c",
        "pricing_best_reduced_cost": -123.353561,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "1",
        "returned_journey_count": 8,
        "rmp_objective_before": 859.3571305
      },
      {
        "active_hash_before": "f0b96be45c5015c9",
        "cg_iter": 3,
        "context_hash": "25942edc9eb0f1d8",
        "pricing_best_reduced_cost": null,
        "pricing_state": "INCOMPLETE_LIMIT",
        "repeat": "1",
        "returned_journey_count": 0,
        "rmp_objective_before": 766.81512425
      },
      {
        "active_hash_before": "f0b96be45c5015c9",
        "cg_iter": 3,
        "context_hash": "25942edc9eb0f1d8",
        "pricing_best_reduced_cost": 0.0,
        "pricing_state": "INCOMPLETE_LIMIT",
        "repeat": "1",
        "returned_journey_count": 0,
        "rmp_objective_before": 766.81512425
      },
      {
        "active_hash_before": "c6ea96127d7c5d7b",
        "cg_iter": 1,
        "context_hash": "080a188d2484ee3e",
        "pricing_best_reduced_cost": -139.913748,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "2",
        "returned_journey_count": 8,
        "rmp_objective_before": 1061.554044
      },
      {
        "active_hash_before": "427b1308ea279e0c",
        "cg_iter": 2,
        "context_hash": "a9831c8a34a4a2f4",
        "pricing_best_reduced_cost": -123.353561,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "2",
        "returned_journey_count": 8,
        "rmp_objective_before": 859.3571305
      },
      {
        "active_hash_before": "f0b96be45c5015c9",
        "cg_iter": 3,
        "context_hash": "be5e5e89972d48fe",
        "pricing_best_reduced_cost": null,
        "pricing_state": "INCOMPLETE_LIMIT",
        "repeat": "2",
        "returned_journey_count": 0,
        "rmp_objective_before": 766.780917
      },
      {
        "active_hash_before": "f0b96be45c5015c9",
        "cg_iter": 3,
        "context_hash": "be5e5e89972d48fe",
        "pricing_best_reduced_cost": 0.0,
        "pricing_state": "INCOMPLETE_LIMIT",
        "repeat": "2",
        "returned_journey_count": 0,
        "rmp_objective_before": 766.780917
      }
    ],
    "probe_id": "config_matched_active_basis_capture"
  },
  {
    "path": [
      {
        "active_hash_before": "c6ea96127d7c5d7b",
        "cg_iter": 1,
        "context_hash": "080a188d2484ee3e",
        "pricing_best_reduced_cost": -139.913748,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "0",
        "returned_journey_count": 8,
        "rmp_objective_before": 1061.554044
      },
      {
        "active_hash_before": "427b1308ea279e0c",
        "cg_iter": 2,
        "context_hash": "827ddca748a70f26",
        "pricing_best_reduced_cost": -123.353561,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "0",
        "returned_journey_count": 8,
        "rmp_objective_before": 859.3571305
      },
      {
        "active_hash_before": "f0b96be45c5015c9",
        "cg_iter": 3,
        "context_hash": "f3fd1968f01e3ad6",
        "pricing_best_reduced_cost": -6.1107805,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "0",
        "returned_journey_count": 5,
        "rmp_objective_before": 766.8686265
      },
      {
        "active_hash_before": "c6ea96127d7c5d7b",
        "cg_iter": 1,
        "context_hash": "080a188d2484ee3e",
        "pricing_best_reduced_cost": -139.913748,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "1",
        "returned_journey_count": 8,
        "rmp_objective_before": 1061.554044
      },
      {
        "active_hash_before": "427b1308ea279e0c",
        "cg_iter": 2,
        "context_hash": "827ddca748a70f26",
        "pricing_best_reduced_cost": -123.353561,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "1",
        "returned_journey_count": 8,
        "rmp_objective_before": 859.3571305
      },
      {
        "active_hash_before": "c6ea96127d7c5d7b",
        "cg_iter": 1,
        "context_hash": "080a188d2484ee3e",
        "pricing_best_reduced_cost": -139.913748,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "2",
        "returned_journey_count": 8,
        "rmp_objective_before": 1061.554044
      },
      {
        "active_hash_before": "427b1308ea279e0c",
        "cg_iter": 2,
        "context_hash": "827ddca748a70f26",
        "pricing_best_reduced_cost": -123.353561,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "2",
        "returned_journey_count": 8,
        "rmp_objective_before": 859.3571305
      }
    ],
    "probe_id": "no_active_basis_capture"
  },
  {
    "path": [
      {
        "active_hash_before": "c6ea96127d7c5d7b",
        "cg_iter": 1,
        "context_hash": "080a188d2484ee3e",
        "pricing_best_reduced_cost": -139.913748,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "0",
        "returned_journey_count": 8,
        "rmp_objective_before": 1061.554044
      },
      {
        "active_hash_before": "427b1308ea279e0c",
        "cg_iter": 2,
        "context_hash": "691e9f3cc93a695c",
        "pricing_best_reduced_cost": -123.353561,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "0",
        "returned_journey_count": 8,
        "rmp_objective_before": 859.3571305
      },
      {
        "active_hash_before": "f0b96be45c5015c9",
        "cg_iter": 3,
        "context_hash": "91f2210b1b8888cb",
        "pricing_best_reduced_cost": -6.110727,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "0",
        "returned_journey_count": 5,
        "rmp_objective_before": 766.81512425
      },
      {
        "active_hash_before": "c6ea96127d7c5d7b",
        "cg_iter": 1,
        "context_hash": "080a188d2484ee3e",
        "pricing_best_reduced_cost": -139.913748,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "1",
        "returned_journey_count": 8,
        "rmp_objective_before": 1061.554044
      },
      {
        "active_hash_before": "427b1308ea279e0c",
        "cg_iter": 2,
        "context_hash": "827ddca748a70f26",
        "pricing_best_reduced_cost": -123.353561,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "1",
        "returned_journey_count": 8,
        "rmp_objective_before": 859.3571305
      },
      {
        "active_hash_before": "c6ea96127d7c5d7b",
        "cg_iter": 1,
        "context_hash": "080a188d2484ee3e",
        "pricing_best_reduced_cost": -139.913748,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "2",
        "returned_journey_count": 8,
        "rmp_objective_before": 1061.554044
      },
      {
        "active_hash_before": "427b1308ea279e0c",
        "cg_iter": 2,
        "context_hash": "827ddca748a70f26",
        "pricing_best_reduced_cost": -123.353561,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "2",
        "returned_journey_count": 8,
        "rmp_objective_before": 859.3571305
      }
    ],
    "probe_id": "alias_instance_capture"
  },
  {
    "path": [
      {
        "active_hash_before": "c6ea96127d7c5d7b",
        "cg_iter": 1,
        "context_hash": "080a188d2484ee3e",
        "pricing_best_reduced_cost": -139.913748,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "0",
        "returned_journey_count": 8,
        "rmp_objective_before": 1061.554044
      },
      {
        "active_hash_before": "427b1308ea279e0c",
        "cg_iter": 2,
        "context_hash": "827ddca748a70f26",
        "pricing_best_reduced_cost": -123.353561,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "0",
        "returned_journey_count": 8,
        "rmp_objective_before": 859.3571305
      },
      {
        "active_hash_before": "c6ea96127d7c5d7b",
        "cg_iter": 1,
        "context_hash": "080a188d2484ee3e",
        "pricing_best_reduced_cost": -139.913748,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "1",
        "returned_journey_count": 8,
        "rmp_objective_before": 1061.554044
      },
      {
        "active_hash_before": "427b1308ea279e0c",
        "cg_iter": 2,
        "context_hash": "827ddca748a70f26",
        "pricing_best_reduced_cost": -123.353561,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "1",
        "returned_journey_count": 8,
        "rmp_objective_before": 859.3571305
      },
      {
        "active_hash_before": "c6ea96127d7c5d7b",
        "cg_iter": 1,
        "context_hash": "080a188d2484ee3e",
        "pricing_best_reduced_cost": -139.913748,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "2",
        "returned_journey_count": 8,
        "rmp_objective_before": 1061.554044
      },
      {
        "active_hash_before": "427b1308ea279e0c",
        "cg_iter": 2,
        "context_hash": "827ddca748a70f26",
        "pricing_best_reduced_cost": -123.353561,
        "pricing_state": "FOUND_NEGATIVE",
        "repeat": "2",
        "returned_journey_count": 8,
        "rmp_objective_before": 859.3571305
      }
    ],
    "probe_id": "multi_profile_order_capture"
  }
]
```

## Checks

```json
{
  "all_expectations_met": true,
  "all_probe_logs_exist": true,
  "diagnostic_has_no_certificate_effect_claim": true,
  "reproduction_probes_have_events": true,
  "reproduction_probes_have_no_target": true,
  "source_has_target": true
}
```