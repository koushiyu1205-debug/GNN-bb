# CBF Delay-Queue kNN Risk Grid 审计报告

日期：2026-06-14

## 目的

枚举 kNN-risk scheduler 的 `k / neighbor risk / threshold` 组合，寻找
是否存在 family-safe 且仍有 high-priority 的保守区域。该脚本只读 H=2
dataset，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
cbf_delay_queue_knn_risk_grid_audit = current
status = cbf_delay_queue_knn_risk_grid_audited
diagnostic_only = true
runs_bpc_or_pricing = false
trial_count = 40
best_production_candidate_ready = false
best_scale_ready_count = 27
all_checks_pass = true
```

## 摘要

```json
{
  "best_production_candidate_ready": false,
  "best_scale_ready_count": 27,
  "production_candidates": [],
  "scale_ready_trials": [
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 7,
        "total_delay_queue_count": 103,
        "total_high_priority_count": 7,
        "unsafe_high_priority_fold_count": 3
      },
      "family_scheduler_ready": false,
      "knn_k": 1,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.95,
      "production_candidate_ready": false,
      "ready_families": [],
      "ready_task_counts": [
        20
      ],
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 7,
        "total_delay_queue_count": 116,
        "total_high_priority_count": 13,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 5,
        "total_delay_queue_count": 7,
        "total_high_priority_count": 5,
        "unsafe_high_priority_fold_count": 2
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 7,
        "total_delay_queue_count": 103,
        "total_high_priority_count": 7,
        "unsafe_high_priority_fold_count": 3
      },
      "family_scheduler_ready": false,
      "knn_k": 1,
      "max_neighbor_unsafe_fraction": 0.2,
      "min_high_priority_threshold": 0.95,
      "production_candidate_ready": false,
      "ready_families": [],
      "ready_task_counts": [
        20
      ],
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 7,
        "total_delay_queue_count": 116,
        "total_high_priority_count": 13,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 5,
        "total_delay_queue_count": 7,
        "total_high_priority_count": 5,
        "unsafe_high_priority_fold_count": 2
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 7,
        "total_delay_queue_count": 101,
        "total_high_priority_count": 9,
        "unsafe_high_priority_fold_count": 3
      },
      "family_scheduler_ready": false,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.8,
      "production_candidate_ready": false,
      "ready_families": [],
      "ready_task_counts": [
        20
      ],
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 8,
        "total_delay_queue_count": 118,
        "total_high_priority_count": 11,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 6,
        "total_delay_queue_count": 4,
        "total_high_priority_count": 8,
        "unsafe_high_priority_fold_count": 2
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 7,
        "total_delay_queue_count": 101,
        "total_high_priority_count": 9,
        "unsafe_high_priority_fold_count": 3
      },
      "family_scheduler_ready": false,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.85,
      "production_candidate_ready": false,
      "ready_families": [],
      "ready_task_counts": [
        20
      ],
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 8,
        "total_delay_queue_count": 118,
        "total_high_priority_count": 11,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 6,
        "total_delay_queue_count": 4,
        "total_high_priority_count": 8,
        "unsafe_high_priority_fold_count": 2
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 7,
        "total_delay_queue_count": 102,
        "total_high_priority_count": 8,
        "unsafe_high_priority_fold_count": 3
      },
      "family_scheduler_ready": false,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.9,
      "production_candidate_ready": false,
      "ready_families": [],
      "ready_task_counts": [
        20
      ],
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 8,
        "total_delay_queue_count": 118,
        "total_high_priority_count": 11,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 6,
        "total_delay_queue_count": 5,
        "total_high_priority_count": 7,
        "unsafe_high_priority_fold_count": 2
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 7,
        "total_delay_queue_count": 101,
        "total_high_priority_count": 9,
        "unsafe_high_priority_fold_count": 3
      },
      "family_scheduler_ready": false,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.2,
      "min_high_priority_threshold": 0.8,
      "production_candidate_ready": false,
      "ready_families": [],
      "ready_task_counts": [
        20
      ],
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 8,
        "total_delay_queue_count": 118,
        "total_high_priority_count": 11,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 6,
        "total_delay_queue_count": 4,
        "total_high_priority_count": 8,
        "unsafe_high_priority_fold_count": 2
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 7,
        "total_delay_queue_count": 101,
        "total_high_priority_count": 9,
        "unsafe_high_priority_fold_count": 3
      },
      "family_scheduler_ready": false,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.2,
      "min_high_priority_threshold": 0.85,
      "production_candidate_ready": false,
      "ready_families": [],
      "ready_task_counts": [
        20
      ],
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 8,
        "total_delay_queue_count": 118,
        "total_high_priority_count": 11,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 6,
        "total_delay_queue_count": 4,
        "total_high_priority_count": 8,
        "unsafe_high_priority_fold_count": 2
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 7,
        "total_delay_queue_count": 102,
        "total_high_priority_count": 8,
        "unsafe_high_priority_fold_count": 3
      },
      "family_scheduler_ready": false,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.2,
      "min_high_priority_threshold": 0.9,
      "production_candidate_ready": false,
      "ready_families": [],
      "ready_task_counts": [
        20
      ],
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 8,
        "total_delay_queue_count": 118,
        "total_high_priority_count": 11,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 6,
        "total_delay_queue_count": 5,
        "total_high_priority_count": 7,
        "unsafe_high_priority_fold_count": 2
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 5,
        "total_delay_queue_count": 105,
        "total_high_priority_count": 5,
        "unsafe_high_priority_fold_count": 2
      },
      "family_scheduler_ready": false,
      "knn_k": 5,
      "max_neighbor_unsafe_fraction": 0.2,
      "min_high_priority_threshold": 0.95,
      "production_candidate_ready": false,
      "ready_families": [],
      "ready_task_counts": [
        20
      ],
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 5,
        "total_delay_queue_count": 120,
        "total_high_priority_count": 9,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 5,
        "total_delay_queue_count": 7,
        "total_high_priority_count": 5,
        "unsafe_high_priority_fold_count": 2
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 6,
        "total_delay_queue_count": 104,
        "total_high_priority_count": 6,
        "unsafe_high_priority_fold_count": 3
      },
      "family_scheduler_ready": false,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.95,
      "production_candidate_ready": false,
      "ready_families": [],
      "ready_task_counts": [
        20
      ],
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 6,
        "total_delay_queue_count": 120,
        "total_high_priority_count": 9,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 5,
        "total_delay_queue_count": 7,
        "total_high_priority_count": 5,
        "unsafe_high_priority_fold_count": 2
      }
    }
  ],
  "trial_count": 40
}
```

## 结论

- production candidate 必须同时 scale-ready 与 family-ready；
- scale-only ready 只能作为继续补采/建模信号，不能接 production；
- 所有 trial 都保持 delay-queue exactness guard。
