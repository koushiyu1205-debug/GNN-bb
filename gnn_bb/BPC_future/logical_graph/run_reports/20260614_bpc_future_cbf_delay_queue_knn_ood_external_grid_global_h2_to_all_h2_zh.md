# CBF Delay-Queue kNN+OOD External Grid 审计报告

日期：2026-06-14

## 目的

在显式 train / validation 分离下枚举 kNN+OOD scheduler 参数，检查是否存在
zero-FP 且有 high-priority 的外部验证候选。该脚本只读 JSONL，不运行
BPC / pricing / RMP，不生成列，不产生 certificate 或 official bound。

## 机器字段

```text
cbf_delay_queue_knn_ood_external_grid = current
status = cbf_delay_queue_knn_ood_external_grid_audited
diagnostic_only = true
runs_bpc_or_pricing = false
trial_count = 81
external_candidate_count = 36
external_candidate_ready = true
production_ready = false
all_checks_pass = true
```

## 摘要

```json
{
  "best_trials": [
    {
      "all_checks_pass": true,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.8,
      "safe_radius": 7.000135110710308,
      "safe_radius_multiplier": 1.0,
      "safe_radius_quantile": 1.0,
      "threshold": 0.8,
      "validation_by_family": {
        "20|greedy-anchor": {
          "false_positive_rate": 0.0,
          "fn": 0,
          "fp": 0,
          "negative_count": 80,
          "positive_count": 0,
          "precision": null,
          "predicted_positive": 0,
          "recall": null,
          "tn": 80,
          "total": 80,
          "tp": 0
        },
        "20|random-wave": {
          "false_positive_rate": null,
          "fn": 1,
          "fp": 0,
          "negative_count": 0,
          "positive_count": 1,
          "precision": null,
          "predicted_positive": 0,
          "recall": 0.0,
          "tn": 0,
          "total": 1,
          "tp": 0
        },
        "20|sector-wave": {
          "false_positive_rate": 0.0,
          "fn": 9,
          "fp": 0,
          "negative_count": 1,
          "positive_count": 17,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.47058823529411764,
          "tn": 1,
          "total": 18,
          "tp": 8
        }
      },
      "validation_by_scale": {
        "20": {
          "false_positive_rate": 0.0,
          "fn": 10,
          "fp": 0,
          "negative_count": 81,
          "positive_count": 18,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.4444444444444444,
          "tn": 81,
          "total": 99,
          "tp": 8
        }
      },
      "validation_candidate_ready": true,
      "validation_overall": {
        "false_positive_rate": 0.0,
        "fn": 10,
        "fp": 0,
        "negative_count": 81,
        "positive_count": 18,
        "precision": 1.0,
        "predicted_positive": 8,
        "recall": 0.4444444444444444,
        "tn": 81,
        "total": 99,
        "tp": 8
      }
    },
    {
      "all_checks_pass": true,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.85,
      "safe_radius": 7.000135110710308,
      "safe_radius_multiplier": 1.0,
      "safe_radius_quantile": 1.0,
      "threshold": 0.85,
      "validation_by_family": {
        "20|greedy-anchor": {
          "false_positive_rate": 0.0,
          "fn": 0,
          "fp": 0,
          "negative_count": 80,
          "positive_count": 0,
          "precision": null,
          "predicted_positive": 0,
          "recall": null,
          "tn": 80,
          "total": 80,
          "tp": 0
        },
        "20|random-wave": {
          "false_positive_rate": null,
          "fn": 1,
          "fp": 0,
          "negative_count": 0,
          "positive_count": 1,
          "precision": null,
          "predicted_positive": 0,
          "recall": 0.0,
          "tn": 0,
          "total": 1,
          "tp": 0
        },
        "20|sector-wave": {
          "false_positive_rate": 0.0,
          "fn": 9,
          "fp": 0,
          "negative_count": 1,
          "positive_count": 17,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.47058823529411764,
          "tn": 1,
          "total": 18,
          "tp": 8
        }
      },
      "validation_by_scale": {
        "20": {
          "false_positive_rate": 0.0,
          "fn": 10,
          "fp": 0,
          "negative_count": 81,
          "positive_count": 18,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.4444444444444444,
          "tn": 81,
          "total": 99,
          "tp": 8
        }
      },
      "validation_candidate_ready": true,
      "validation_overall": {
        "false_positive_rate": 0.0,
        "fn": 10,
        "fp": 0,
        "negative_count": 81,
        "positive_count": 18,
        "precision": 1.0,
        "predicted_positive": 8,
        "recall": 0.4444444444444444,
        "tn": 81,
        "total": 99,
        "tp": 8
      }
    },
    {
      "all_checks_pass": true,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.9,
      "safe_radius": 7.000135110710308,
      "safe_radius_multiplier": 1.0,
      "safe_radius_quantile": 1.0,
      "threshold": 0.9,
      "validation_by_family": {
        "20|greedy-anchor": {
          "false_positive_rate": 0.0,
          "fn": 0,
          "fp": 0,
          "negative_count": 80,
          "positive_count": 0,
          "precision": null,
          "predicted_positive": 0,
          "recall": null,
          "tn": 80,
          "total": 80,
          "tp": 0
        },
        "20|random-wave": {
          "false_positive_rate": null,
          "fn": 1,
          "fp": 0,
          "negative_count": 0,
          "positive_count": 1,
          "precision": null,
          "predicted_positive": 0,
          "recall": 0.0,
          "tn": 0,
          "total": 1,
          "tp": 0
        },
        "20|sector-wave": {
          "false_positive_rate": 0.0,
          "fn": 9,
          "fp": 0,
          "negative_count": 1,
          "positive_count": 17,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.47058823529411764,
          "tn": 1,
          "total": 18,
          "tp": 8
        }
      },
      "validation_by_scale": {
        "20": {
          "false_positive_rate": 0.0,
          "fn": 10,
          "fp": 0,
          "negative_count": 81,
          "positive_count": 18,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.4444444444444444,
          "tn": 81,
          "total": 99,
          "tp": 8
        }
      },
      "validation_candidate_ready": true,
      "validation_overall": {
        "false_positive_rate": 0.0,
        "fn": 10,
        "fp": 0,
        "negative_count": 81,
        "positive_count": 18,
        "precision": 1.0,
        "predicted_positive": 8,
        "recall": 0.4444444444444444,
        "tn": 81,
        "total": 99,
        "tp": 8
      }
    },
    {
      "all_checks_pass": true,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.8,
      "safe_radius": 6.53463810982654,
      "safe_radius_multiplier": 1.25,
      "safe_radius_quantile": 0.9,
      "threshold": 0.8,
      "validation_by_family": {
        "20|greedy-anchor": {
          "false_positive_rate": 0.0,
          "fn": 0,
          "fp": 0,
          "negative_count": 80,
          "positive_count": 0,
          "precision": null,
          "predicted_positive": 0,
          "recall": null,
          "tn": 80,
          "total": 80,
          "tp": 0
        },
        "20|random-wave": {
          "false_positive_rate": null,
          "fn": 1,
          "fp": 0,
          "negative_count": 0,
          "positive_count": 1,
          "precision": null,
          "predicted_positive": 0,
          "recall": 0.0,
          "tn": 0,
          "total": 1,
          "tp": 0
        },
        "20|sector-wave": {
          "false_positive_rate": 0.0,
          "fn": 9,
          "fp": 0,
          "negative_count": 1,
          "positive_count": 17,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.47058823529411764,
          "tn": 1,
          "total": 18,
          "tp": 8
        }
      },
      "validation_by_scale": {
        "20": {
          "false_positive_rate": 0.0,
          "fn": 10,
          "fp": 0,
          "negative_count": 81,
          "positive_count": 18,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.4444444444444444,
          "tn": 81,
          "total": 99,
          "tp": 8
        }
      },
      "validation_candidate_ready": true,
      "validation_overall": {
        "false_positive_rate": 0.0,
        "fn": 10,
        "fp": 0,
        "negative_count": 81,
        "positive_count": 18,
        "precision": 1.0,
        "predicted_positive": 8,
        "recall": 0.4444444444444444,
        "tn": 81,
        "total": 99,
        "tp": 8
      }
    },
    {
      "all_checks_pass": true,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.8,
      "safe_radius": 8.750168888387885,
      "safe_radius_multiplier": 1.25,
      "safe_radius_quantile": 1.0,
      "threshold": 0.8,
      "validation_by_family": {
        "20|greedy-anchor": {
          "false_positive_rate": 0.0,
          "fn": 0,
          "fp": 0,
          "negative_count": 80,
          "positive_count": 0,
          "precision": null,
          "predicted_positive": 0,
          "recall": null,
          "tn": 80,
          "total": 80,
          "tp": 0
        },
        "20|random-wave": {
          "false_positive_rate": null,
          "fn": 1,
          "fp": 0,
          "negative_count": 0,
          "positive_count": 1,
          "precision": null,
          "predicted_positive": 0,
          "recall": 0.0,
          "tn": 0,
          "total": 1,
          "tp": 0
        },
        "20|sector-wave": {
          "false_positive_rate": 0.0,
          "fn": 9,
          "fp": 0,
          "negative_count": 1,
          "positive_count": 17,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.47058823529411764,
          "tn": 1,
          "total": 18,
          "tp": 8
        }
      },
      "validation_by_scale": {
        "20": {
          "false_positive_rate": 0.0,
          "fn": 10,
          "fp": 0,
          "negative_count": 81,
          "positive_count": 18,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.4444444444444444,
          "tn": 81,
          "total": 99,
          "tp": 8
        }
      },
      "validation_candidate_ready": true,
      "validation_overall": {
        "false_positive_rate": 0.0,
        "fn": 10,
        "fp": 0,
        "negative_count": 81,
        "positive_count": 18,
        "precision": 1.0,
        "predicted_positive": 8,
        "recall": 0.4444444444444444,
        "tn": 81,
        "total": 99,
        "tp": 8
      }
    },
    {
      "all_checks_pass": true,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.85,
      "safe_radius": 6.53463810982654,
      "safe_radius_multiplier": 1.25,
      "safe_radius_quantile": 0.9,
      "threshold": 0.85,
      "validation_by_family": {
        "20|greedy-anchor": {
          "false_positive_rate": 0.0,
          "fn": 0,
          "fp": 0,
          "negative_count": 80,
          "positive_count": 0,
          "precision": null,
          "predicted_positive": 0,
          "recall": null,
          "tn": 80,
          "total": 80,
          "tp": 0
        },
        "20|random-wave": {
          "false_positive_rate": null,
          "fn": 1,
          "fp": 0,
          "negative_count": 0,
          "positive_count": 1,
          "precision": null,
          "predicted_positive": 0,
          "recall": 0.0,
          "tn": 0,
          "total": 1,
          "tp": 0
        },
        "20|sector-wave": {
          "false_positive_rate": 0.0,
          "fn": 9,
          "fp": 0,
          "negative_count": 1,
          "positive_count": 17,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.47058823529411764,
          "tn": 1,
          "total": 18,
          "tp": 8
        }
      },
      "validation_by_scale": {
        "20": {
          "false_positive_rate": 0.0,
          "fn": 10,
          "fp": 0,
          "negative_count": 81,
          "positive_count": 18,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.4444444444444444,
          "tn": 81,
          "total": 99,
          "tp": 8
        }
      },
      "validation_candidate_ready": true,
      "validation_overall": {
        "false_positive_rate": 0.0,
        "fn": 10,
        "fp": 0,
        "negative_count": 81,
        "positive_count": 18,
        "precision": 1.0,
        "predicted_positive": 8,
        "recall": 0.4444444444444444,
        "tn": 81,
        "total": 99,
        "tp": 8
      }
    },
    {
      "all_checks_pass": true,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.85,
      "safe_radius": 8.750168888387885,
      "safe_radius_multiplier": 1.25,
      "safe_radius_quantile": 1.0,
      "threshold": 0.85,
      "validation_by_family": {
        "20|greedy-anchor": {
          "false_positive_rate": 0.0,
          "fn": 0,
          "fp": 0,
          "negative_count": 80,
          "positive_count": 0,
          "precision": null,
          "predicted_positive": 0,
          "recall": null,
          "tn": 80,
          "total": 80,
          "tp": 0
        },
        "20|random-wave": {
          "false_positive_rate": null,
          "fn": 1,
          "fp": 0,
          "negative_count": 0,
          "positive_count": 1,
          "precision": null,
          "predicted_positive": 0,
          "recall": 0.0,
          "tn": 0,
          "total": 1,
          "tp": 0
        },
        "20|sector-wave": {
          "false_positive_rate": 0.0,
          "fn": 9,
          "fp": 0,
          "negative_count": 1,
          "positive_count": 17,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.47058823529411764,
          "tn": 1,
          "total": 18,
          "tp": 8
        }
      },
      "validation_by_scale": {
        "20": {
          "false_positive_rate": 0.0,
          "fn": 10,
          "fp": 0,
          "negative_count": 81,
          "positive_count": 18,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.4444444444444444,
          "tn": 81,
          "total": 99,
          "tp": 8
        }
      },
      "validation_candidate_ready": true,
      "validation_overall": {
        "false_positive_rate": 0.0,
        "fn": 10,
        "fp": 0,
        "negative_count": 81,
        "positive_count": 18,
        "precision": 1.0,
        "predicted_positive": 8,
        "recall": 0.4444444444444444,
        "tn": 81,
        "total": 99,
        "tp": 8
      }
    },
    {
      "all_checks_pass": true,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.9,
      "safe_radius": 6.53463810982654,
      "safe_radius_multiplier": 1.25,
      "safe_radius_quantile": 0.9,
      "threshold": 0.9,
      "validation_by_family": {
        "20|greedy-anchor": {
          "false_positive_rate": 0.0,
          "fn": 0,
          "fp": 0,
          "negative_count": 80,
          "positive_count": 0,
          "precision": null,
          "predicted_positive": 0,
          "recall": null,
          "tn": 80,
          "total": 80,
          "tp": 0
        },
        "20|random-wave": {
          "false_positive_rate": null,
          "fn": 1,
          "fp": 0,
          "negative_count": 0,
          "positive_count": 1,
          "precision": null,
          "predicted_positive": 0,
          "recall": 0.0,
          "tn": 0,
          "total": 1,
          "tp": 0
        },
        "20|sector-wave": {
          "false_positive_rate": 0.0,
          "fn": 9,
          "fp": 0,
          "negative_count": 1,
          "positive_count": 17,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.47058823529411764,
          "tn": 1,
          "total": 18,
          "tp": 8
        }
      },
      "validation_by_scale": {
        "20": {
          "false_positive_rate": 0.0,
          "fn": 10,
          "fp": 0,
          "negative_count": 81,
          "positive_count": 18,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.4444444444444444,
          "tn": 81,
          "total": 99,
          "tp": 8
        }
      },
      "validation_candidate_ready": true,
      "validation_overall": {
        "false_positive_rate": 0.0,
        "fn": 10,
        "fp": 0,
        "negative_count": 81,
        "positive_count": 18,
        "precision": 1.0,
        "predicted_positive": 8,
        "recall": 0.4444444444444444,
        "tn": 81,
        "total": 99,
        "tp": 8
      }
    },
    {
      "all_checks_pass": true,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.9,
      "safe_radius": 8.750168888387885,
      "safe_radius_multiplier": 1.25,
      "safe_radius_quantile": 1.0,
      "threshold": 0.9,
      "validation_by_family": {
        "20|greedy-anchor": {
          "false_positive_rate": 0.0,
          "fn": 0,
          "fp": 0,
          "negative_count": 80,
          "positive_count": 0,
          "precision": null,
          "predicted_positive": 0,
          "recall": null,
          "tn": 80,
          "total": 80,
          "tp": 0
        },
        "20|random-wave": {
          "false_positive_rate": null,
          "fn": 1,
          "fp": 0,
          "negative_count": 0,
          "positive_count": 1,
          "precision": null,
          "predicted_positive": 0,
          "recall": 0.0,
          "tn": 0,
          "total": 1,
          "tp": 0
        },
        "20|sector-wave": {
          "false_positive_rate": 0.0,
          "fn": 9,
          "fp": 0,
          "negative_count": 1,
          "positive_count": 17,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.47058823529411764,
          "tn": 1,
          "total": 18,
          "tp": 8
        }
      },
      "validation_by_scale": {
        "20": {
          "false_positive_rate": 0.0,
          "fn": 10,
          "fp": 0,
          "negative_count": 81,
          "positive_count": 18,
          "precision": 1.0,
          "predicted_positive": 8,
          "recall": 0.4444444444444444,
          "tn": 81,
          "total": 99,
          "tp": 8
        }
      },
      "validation_candidate_ready": true,
      "validation_overall": {
        "false_positive_rate": 0.0,
        "fn": 10,
        "fp": 0,
        "negative_count": 81,
        "positive_count": 18,
        "precision": 1.0,
        "predicted_positive": 8,
        "recall": 0.4444444444444444,
        "tn": 81,
        "total": 99,
        "tp": 8
      }
    },
    {
      "all_checks_pass": true,
      "knn_k": 3,
      "max_neighbor_unsafe_fraction": 0.0,
      "min_high_priority_threshold": 0.8,
      "safe_radius": 5.394263307815682,
      "safe_radius_multiplier": 1.25,
      "safe_radius_quantile": 0.8,
      "threshold": 0.8,
      "validation_by_family": {
        "20|greedy-anchor": {
          "false_positive_rate": 0.0,
          "fn": 0,
          "fp": 0,
          "negative_count": 80,
          "positive_count": 0,
          "precision": null,
          "predicted_positive": 0,
          "recall": null,
          "tn": 80,
          "total": 80,
          "tp": 0
        },
        "20|random-wave": {
          "false_positive_rate": null,
          "fn": 1,
          "fp": 0,
          "negative_count": 0,
          "positive_count": 1,
          "precision": null,
          "predicted_positive": 0,
          "recall": 0.0,
          "tn": 0,
          "total": 1,
          "tp": 0
        },
        "20|sector-wave": {
          "false_positive_rate": 0.0,
          "fn": 10,
          "fp": 0,
          "negative_count": 1,
          "positive_count": 17,
          "precision": 1.0,
          "predicted_positive": 7,
          "recall": 0.4117647058823529,
          "tn": 1,
          "total": 18,
          "tp": 7
        }
      },
      "validation_by_scale": {
        "20": {
          "false_positive_rate": 0.0,
          "fn": 11,
          "fp": 0,
          "negative_count": 81,
          "positive_count": 18,
          "precision": 1.0,
          "predicted_positive": 7,
          "recall": 0.3888888888888889,
          "tn": 81,
          "total": 99,
          "tp": 7
        }
      },
      "validation_candidate_ready": true,
      "validation_overall": {
        "false_positive_rate": 0.0,
        "fn": 11,
        "fp": 0,
        "negative_count": 81,
        "positive_count": 18,
        "precision": 1.0,
        "predicted_positive": 7,
        "recall": 0.3888888888888889,
        "tn": 81,
        "total": 99,
        "tp": 7
      }
    }
  ],
  "external_candidate_count": 36,
  "external_candidate_ready": true,
  "predicted_positive_histogram": {
    "0": 45,
    "1": 9,
    "4": 3,
    "5": 6,
    "6": 6,
    "7": 3,
    "8": 9
  },
  "trial_count": 81
}
```

## 解释

- external candidate 仍只是离线验证，不等于 production ready；
- 如果所有 trial predicted_positive=0，则当前 gate 外部验证过度保守；
- 如果任何 trial fp>0，则该参数不安全；
- 所有 trial 都必须保持 delay-queue exactness guard 和 proof-budget guard。
