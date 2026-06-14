# CBF Delay-Queue kNN+OOD Grid 审计报告

日期：2026-06-14

## 目的

枚举 kNN+safe-radius OOD scheduler 的参数组合，检查第一个
production-candidate 信号是否是稳健区域，而不是单点参数偶然通过。
该脚本只读 H=2 dataset，不运行 BPC / pricing / RMP，不产生
certificate 或 official bound。

## 机器字段

```text
cbf_delay_queue_knn_ood_grid_audit = current
status = cbf_delay_queue_knn_ood_grid_audited
diagnostic_only = true
runs_bpc_or_pricing = false
trial_count = 81
production_candidate_count = 14
robust_candidate_ready = true
production_ready = false
all_checks_pass = true
```

## 摘要

```json
{
  "best_candidates": [
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 107,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      },
      "family_scheduler_ready": true,
      "knn_k": 5,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.8,
      "production_candidate_ready": true,
      "ready_families": [
        {
          "family": "sector-wave",
          "task_count": 20
        }
      ],
      "ready_task_counts": [
        20
      ],
      "safe_radius_multiplier": 0.75,
      "safe_radius_quantile": 1.0,
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 4,
        "total_delay_queue_count": 125,
        "total_high_priority_count": 4,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 9,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 107,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      },
      "family_scheduler_ready": true,
      "knn_k": 5,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.85,
      "production_candidate_ready": true,
      "ready_families": [
        {
          "family": "sector-wave",
          "task_count": 20
        }
      ],
      "ready_task_counts": [
        20
      ],
      "safe_radius_multiplier": 0.75,
      "safe_radius_quantile": 1.0,
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 4,
        "total_delay_queue_count": 125,
        "total_high_priority_count": 4,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 9,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 107,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      },
      "family_scheduler_ready": true,
      "knn_k": 5,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.8,
      "production_candidate_ready": true,
      "ready_families": [
        {
          "family": "sector-wave",
          "task_count": 20
        }
      ],
      "ready_task_counts": [
        20
      ],
      "safe_radius_multiplier": 1.0,
      "safe_radius_quantile": 0.8,
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 126,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 9,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 107,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      },
      "family_scheduler_ready": true,
      "knn_k": 5,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.8,
      "production_candidate_ready": true,
      "ready_families": [
        {
          "family": "sector-wave",
          "task_count": 20
        }
      ],
      "ready_task_counts": [
        20
      ],
      "safe_radius_multiplier": 1.0,
      "safe_radius_quantile": 0.9,
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 126,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 9,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 107,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      },
      "family_scheduler_ready": true,
      "knn_k": 5,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.85,
      "production_candidate_ready": true,
      "ready_families": [
        {
          "family": "sector-wave",
          "task_count": 20
        }
      ],
      "ready_task_counts": [
        20
      ],
      "safe_radius_multiplier": 1.0,
      "safe_radius_quantile": 0.8,
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 126,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 9,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 107,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      },
      "family_scheduler_ready": true,
      "knn_k": 5,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.85,
      "production_candidate_ready": true,
      "ready_families": [
        {
          "family": "sector-wave",
          "task_count": 20
        }
      ],
      "ready_task_counts": [
        20
      ],
      "safe_radius_multiplier": 1.0,
      "safe_radius_quantile": 0.9,
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 126,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 9,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 2,
        "total_delay_queue_count": 108,
        "total_high_priority_count": 2,
        "unsafe_high_priority_fold_count": 0
      },
      "family_scheduler_ready": true,
      "knn_k": 5,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.9,
      "production_candidate_ready": true,
      "ready_families": [
        {
          "family": "sector-wave",
          "task_count": 20
        }
      ],
      "ready_task_counts": [
        20
      ],
      "safe_radius_multiplier": 0.75,
      "safe_radius_quantile": 1.0,
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 4,
        "total_delay_queue_count": 125,
        "total_high_priority_count": 4,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 2,
        "total_delay_queue_count": 10,
        "total_high_priority_count": 2,
        "unsafe_high_priority_fold_count": 0
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 2,
        "total_delay_queue_count": 108,
        "total_high_priority_count": 2,
        "unsafe_high_priority_fold_count": 0
      },
      "family_scheduler_ready": true,
      "knn_k": 5,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.9,
      "production_candidate_ready": true,
      "ready_families": [
        {
          "family": "sector-wave",
          "task_count": 20
        }
      ],
      "ready_task_counts": [
        20
      ],
      "safe_radius_multiplier": 1.0,
      "safe_radius_quantile": 0.8,
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 126,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 2,
        "total_delay_queue_count": 10,
        "total_high_priority_count": 2,
        "unsafe_high_priority_fold_count": 0
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 2,
        "total_delay_queue_count": 108,
        "total_high_priority_count": 2,
        "unsafe_high_priority_fold_count": 0
      },
      "family_scheduler_ready": true,
      "knn_k": 5,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.9,
      "production_candidate_ready": true,
      "ready_families": [
        {
          "family": "sector-wave",
          "task_count": 20
        }
      ],
      "ready_task_counts": [
        20
      ],
      "safe_radius_multiplier": 1.0,
      "safe_radius_quantile": 0.9,
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 126,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 2,
        "total_delay_queue_count": 10,
        "total_high_priority_count": 2,
        "unsafe_high_priority_fold_count": 0
      }
    },
    {
      "all_checks_pass": true,
      "family20_totals": {
        "evaluated_count": 13,
        "productive_high_priority_fold_count": 1,
        "total_delay_queue_count": 109,
        "total_high_priority_count": 1,
        "unsafe_high_priority_fold_count": 0
      },
      "family_scheduler_ready": true,
      "knn_k": 5,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.8,
      "production_candidate_ready": true,
      "ready_families": [
        {
          "family": "sector-wave",
          "task_count": 20
        }
      ],
      "ready_task_counts": [
        20
      ],
      "safe_radius_multiplier": 0.75,
      "safe_radius_quantile": 0.9,
      "scale20_totals": {
        "evaluated_count": 18,
        "productive_high_priority_fold_count": 3,
        "total_delay_queue_count": 126,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 0
      },
      "scale_scheduler_ready": true,
      "scheduler_ready": true,
      "sector_wave_totals": {
        "evaluated_count": 6,
        "productive_high_priority_fold_count": 1,
        "total_delay_queue_count": 11,
        "total_high_priority_count": 1,
        "unsafe_high_priority_fold_count": 0
      }
    }
  ],
  "production_candidate_count": 14,
  "radius_candidate_histogram": {
    "q=0.8,m=1.0": 3,
    "q=0.9,m=0.75": 2,
    "q=0.9,m=1.0": 3,
    "q=1.0,m=0.75": 6
  },
  "robust_candidate_ready": true,
  "trial_count": 81
}
```

## 解释

- production candidate 仍只是离线候选，不等于 production ready；
- robust candidate 要求候选不只出现在一个 safe-radius 参数点；
- 所有 trial 必须保持 delay-queue exactness guard 和 proof-budget guard；
- 下一步仍只能做独立验证或 audit-only smoke，不能接 worker/certificate。
