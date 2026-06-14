# Root Cause Selector Pool/Overlap Feature Probe 报告

日期：2026-06-14

## 目的

本报告只读 replay manifests 与 candidate impact rows，在内存中派生
 candidate-vs-pool / candidate-vs-returned-batch overlap 特征，并检查
这些 addition-before 特征是否已经足以形成 production selector。

它不运行 BPC / pricing / RMP / Pulse / replay / benchmark，也不重写
`candidate_impact_rows.csv`。

## 机器字段

```text
root_cause_selector_pool_overlap_feature_probe = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_pool_overlap_feature_probe_audited
row_count = 280
manifest_case_count = 122
missing_manifest_join_count = 0
derived_feature_count = 31
robust_all_holdout_derived_feature_count = 0
robust_all_holdout_model_count = 0
best_context_model = linear_mean_diff
best_context_model_context_folds = 17/28
best_context_model_instance_folds = 4/4
best_context_model_dataset_folds = 5/5
explicit_forbidden_signature_list_available_count = 18
all_checks_pass = true
```

## 结论

现有 manifest 足以派生 pool/returned-batch overlap 特征并与 280 行 candidate impact rows 完整 join；但这些派生特征仍没有产生 robust context/instance/dataset all-holdout selector 或 multifeature model。此外当前全局 manifests 已出现显式 forbidden signature list，但这些 targeted payload 仍未形成通过 holdout 的 production selector。

## Top Derived Feature Summaries

```json
[
  {
    "all_holdouts_pass": false,
    "context_folds": "18/28",
    "dataset_folds": "4/5",
    "feature": "returned_batch_min_true_rc",
    "instance_folds": "3/4",
    "worst_context_folds": [
      {
        "fold": "c5a59a95c2c9971a",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "returned_batch_min_true_rc",
          "operator": "<=",
          "threshold": -12.0449185,
          "train_metrics": {
            "accuracy": 0.8483754512635379,
            "fn": 9,
            "fp": 33,
            "precision": 0.8583690987124464,
            "predicted_positive": 233,
            "recall": 0.9569377990430622,
            "tn": 35,
            "total": 277,
            "tp": 200
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      },
      {
        "fold": "d60fcf4b919b7d22",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "returned_batch_min_true_rc",
          "operator": "<=",
          "threshold": -12.0449185,
          "train_metrics": {
            "accuracy": 0.8483754512635379,
            "fn": 9,
            "fp": 33,
            "precision": 0.8583690987124464,
            "predicted_positive": 233,
            "recall": 0.9569377990430622,
            "tn": 35,
            "total": 277,
            "tp": 200
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      },
      {
        "fold": "e55ea3e7d277b6d1",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "returned_batch_min_true_rc",
          "operator": "<=",
          "threshold": -12.0449185,
          "train_metrics": {
            "accuracy": 0.8483754512635379,
            "fn": 9,
            "fp": 33,
            "precision": 0.8583690987124464,
            "predicted_positive": 233,
            "recall": 0.9569377990430622,
            "tn": 35,
            "total": 277,
            "tp": 200
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      }
    ]
  },
  {
    "all_holdouts_pass": false,
    "context_folds": "18/28",
    "dataset_folds": "4/5",
    "feature": "returned_batch_mean_true_rc",
    "instance_folds": "3/4",
    "worst_context_folds": [
      {
        "fold": "c5a59a95c2c9971a",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "returned_batch_mean_true_rc",
          "operator": "<=",
          "threshold": -10.379221073,
          "train_metrics": {
            "accuracy": 0.8483754512635379,
            "fn": 9,
            "fp": 33,
            "precision": 0.8583690987124464,
            "predicted_positive": 233,
            "recall": 0.9569377990430622,
            "tn": 35,
            "total": 277,
            "tp": 200
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      },
      {
        "fold": "d60fcf4b919b7d22",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "returned_batch_mean_true_rc",
          "operator": "<=",
          "threshold": -10.379221073,
          "train_metrics": {
            "accuracy": 0.8483754512635379,
            "fn": 9,
            "fp": 33,
            "precision": 0.8583690987124464,
            "predicted_positive": 233,
            "recall": 0.9569377990430622,
            "tn": 35,
            "total": 277,
            "tp": 200
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      },
      {
        "fold": "e55ea3e7d277b6d1",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "returned_batch_mean_true_rc",
          "operator": "<=",
          "threshold": -10.379221073,
          "train_metrics": {
            "accuracy": 0.8483754512635379,
            "fn": 9,
            "fp": 33,
            "precision": 0.8583690987124464,
            "predicted_positive": 233,
            "recall": 0.9569377990430622,
            "tn": 35,
            "total": 277,
            "tp": 200
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      }
    ]
  },
  {
    "all_holdouts_pass": false,
    "context_folds": "18/28",
    "dataset_folds": "3/5",
    "feature": "pool_candidate_task_set_near_050_count",
    "instance_folds": "3/4",
    "worst_context_folds": [
      {
        "fold": "79de1ece885a7f67",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_set_near_050_count",
          "operator": "<=",
          "threshold": 10.0,
          "train_metrics": {
            "accuracy": 0.8339622641509434,
            "fn": 9,
            "fp": 35,
            "precision": 0.8491379310344828,
            "predicted_positive": 232,
            "recall": 0.9563106796116505,
            "tn": 24,
            "total": 265,
            "tp": 197
          }
        },
        "test": {
          "accuracy": 0.2,
          "fn": 3,
          "fp": 9,
          "precision": 0.0,
          "predicted_positive": 9,
          "recall": 0.0,
          "tn": 3,
          "total": 15,
          "tp": 0
        },
        "test_row_count": 15
      },
      {
        "fold": "3f914a0d2b97fd27",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_set_near_050_count",
          "operator": "<=",
          "threshold": 11.0,
          "train_metrics": {
            "accuracy": 0.8109090909090909,
            "fn": 6,
            "fp": 46,
            "precision": 0.8152610441767069,
            "predicted_positive": 249,
            "recall": 0.9712918660287081,
            "tn": 20,
            "total": 275,
            "tp": 203
          }
        },
        "test": {
          "accuracy": 0.4,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 2,
          "total": 5,
          "tp": 0
        },
        "test_row_count": 5
      },
      {
        "fold": "c5a59a95c2c9971a",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_set_near_050_count",
          "operator": "<=",
          "threshold": 11.0,
          "train_metrics": {
            "accuracy": 0.8122743682310469,
            "fn": 6,
            "fp": 46,
            "precision": 0.8152610441767069,
            "predicted_positive": 249,
            "recall": 0.9712918660287081,
            "tn": 22,
            "total": 277,
            "tp": 203
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      }
    ]
  },
  {
    "all_holdouts_pass": false,
    "context_folds": "17/28",
    "dataset_folds": "4/5",
    "feature": "pool_candidate_task_freq_mean_fraction",
    "instance_folds": "4/4",
    "worst_context_folds": [
      {
        "fold": "c5a59a95c2c9971a",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_freq_mean_fraction",
          "operator": "<=",
          "threshold": 0.177777778,
          "train_metrics": {
            "accuracy": 0.7833935018050542,
            "fn": 3,
            "fp": 57,
            "precision": 0.7832699619771863,
            "predicted_positive": 263,
            "recall": 0.9856459330143541,
            "tn": 11,
            "total": 277,
            "tp": 206
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      },
      {
        "fold": "d60fcf4b919b7d22",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_freq_mean_fraction",
          "operator": "<=",
          "threshold": 0.157622739,
          "train_metrics": {
            "accuracy": 0.7978339350180506,
            "fn": 13,
            "fp": 43,
            "precision": 0.8200836820083682,
            "predicted_positive": 239,
            "recall": 0.937799043062201,
            "tn": 25,
            "total": 277,
            "tp": 196
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      },
      {
        "fold": "e55ea3e7d277b6d1",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_freq_mean_fraction",
          "operator": "<=",
          "threshold": 0.157622739,
          "train_metrics": {
            "accuracy": 0.7978339350180506,
            "fn": 13,
            "fp": 43,
            "precision": 0.8200836820083682,
            "predicted_positive": 239,
            "recall": 0.937799043062201,
            "tn": 25,
            "total": 277,
            "tp": 196
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      }
    ]
  },
  {
    "all_holdouts_pass": false,
    "context_folds": "17/28",
    "dataset_folds": "4/5",
    "feature": "pool_candidate_task_set_mean_jaccard",
    "instance_folds": "3/4",
    "worst_context_folds": [
      {
        "fold": "d60fcf4b919b7d22",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_set_mean_jaccard",
          "operator": "<=",
          "threshold": 0.110658915,
          "train_metrics": {
            "accuracy": 0.7978339350180506,
            "fn": 13,
            "fp": 43,
            "precision": 0.8200836820083682,
            "predicted_positive": 239,
            "recall": 0.937799043062201,
            "tn": 25,
            "total": 277,
            "tp": 196
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      },
      {
        "fold": "e55ea3e7d277b6d1",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_set_mean_jaccard",
          "operator": "<=",
          "threshold": 0.110658915,
          "train_metrics": {
            "accuracy": 0.7978339350180506,
            "fn": 13,
            "fp": 43,
            "precision": 0.8200836820083682,
            "predicted_positive": 239,
            "recall": 0.937799043062201,
            "tn": 25,
            "total": 277,
            "tp": 196
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      },
      {
        "fold": "3f914a0d2b97fd27",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_set_mean_jaccard",
          "operator": "<=",
          "threshold": 0.110658915,
          "train_metrics": {
            "accuracy": 0.7927272727272727,
            "fn": 13,
            "fp": 44,
            "precision": 0.8166666666666667,
            "predicted_positive": 240,
            "recall": 0.937799043062201,
            "tn": 22,
            "total": 275,
            "tp": 196
          }
        },
        "test": {
          "accuracy": 0.6,
          "fn": 0,
          "fp": 2,
          "precision": 0.0,
          "predicted_positive": 2,
          "recall": null,
          "tn": 3,
          "total": 5,
          "tp": 0
        },
        "test_row_count": 5
      }
    ]
  },
  {
    "all_holdouts_pass": false,
    "context_folds": "16/28",
    "dataset_folds": "3/5",
    "feature": "pool_candidate_task_set_exact_count",
    "instance_folds": "2/4",
    "worst_context_folds": [
      {
        "fold": "3f914a0d2b97fd27",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_set_exact_count",
          "operator": "<=",
          "threshold": 1.0,
          "train_metrics": {
            "accuracy": 0.76,
            "fn": 0,
            "fp": 66,
            "precision": 0.76,
            "predicted_positive": 275,
            "recall": 1.0,
            "tn": 0,
            "total": 275,
            "tp": 209
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 5,
          "precision": 0.0,
          "predicted_positive": 5,
          "recall": null,
          "tn": 0,
          "total": 5,
          "tp": 0
        },
        "test_row_count": 5
      },
      {
        "fold": "46e7a2883459d4fb",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_set_exact_count",
          "operator": "<=",
          "threshold": 1.0,
          "train_metrics": {
            "accuracy": 0.7572463768115942,
            "fn": 0,
            "fp": 67,
            "precision": 0.7572463768115942,
            "predicted_positive": 276,
            "recall": 1.0,
            "tn": 0,
            "total": 276,
            "tp": 209
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 4,
          "precision": 0.0,
          "predicted_positive": 4,
          "recall": null,
          "tn": 0,
          "total": 4,
          "tp": 0
        },
        "test_row_count": 4
      },
      {
        "fold": "c5a59a95c2c9971a",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_set_exact_count",
          "operator": "<=",
          "threshold": 1.0,
          "train_metrics": {
            "accuracy": 0.7545126353790613,
            "fn": 0,
            "fp": 68,
            "precision": 0.7545126353790613,
            "predicted_positive": 277,
            "recall": 1.0,
            "tn": 0,
            "total": 277,
            "tp": 209
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      }
    ]
  },
  {
    "all_holdouts_pass": false,
    "context_folds": "16/28",
    "dataset_folds": "3/5",
    "feature": "pool_candidate_task_freq_min",
    "instance_folds": "1/4",
    "worst_context_folds": [
      {
        "fold": "3f914a0d2b97fd27",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_freq_min",
          "operator": "<=",
          "threshold": 24.0,
          "train_metrics": {
            "accuracy": 0.7927272727272727,
            "fn": 9,
            "fp": 48,
            "precision": 0.8064516129032258,
            "predicted_positive": 248,
            "recall": 0.9569377990430622,
            "tn": 18,
            "total": 275,
            "tp": 200
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 5,
          "precision": 0.0,
          "predicted_positive": 5,
          "recall": null,
          "tn": 0,
          "total": 5,
          "tp": 0
        },
        "test_row_count": 5
      },
      {
        "fold": "46e7a2883459d4fb",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_freq_min",
          "operator": "<=",
          "threshold": 24.0,
          "train_metrics": {
            "accuracy": 0.7898550724637681,
            "fn": 9,
            "fp": 49,
            "precision": 0.8032128514056225,
            "predicted_positive": 249,
            "recall": 0.9569377990430622,
            "tn": 18,
            "total": 276,
            "tp": 200
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 4,
          "precision": 0.0,
          "predicted_positive": 4,
          "recall": null,
          "tn": 0,
          "total": 4,
          "tp": 0
        },
        "test_row_count": 4
      },
      {
        "fold": "d60fcf4b919b7d22",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_freq_min",
          "operator": "<=",
          "threshold": 24.0,
          "train_metrics": {
            "accuracy": 0.7870036101083032,
            "fn": 9,
            "fp": 50,
            "precision": 0.8,
            "predicted_positive": 250,
            "recall": 0.9569377990430622,
            "tn": 18,
            "total": 277,
            "tp": 200
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      }
    ]
  },
  {
    "all_holdouts_pass": false,
    "context_folds": "16/28",
    "dataset_folds": "3/5",
    "feature": "pool_candidate_task_freq_max",
    "instance_folds": "1/4",
    "worst_context_folds": [
      {
        "fold": "3f914a0d2b97fd27",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_freq_max",
          "operator": ">=",
          "threshold": 5.0,
          "train_metrics": {
            "accuracy": 0.7636363636363637,
            "fn": 0,
            "fp": 65,
            "precision": 0.7627737226277372,
            "predicted_positive": 274,
            "recall": 1.0,
            "tn": 1,
            "total": 275,
            "tp": 209
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 5,
          "precision": 0.0,
          "predicted_positive": 5,
          "recall": null,
          "tn": 0,
          "total": 5,
          "tp": 0
        },
        "test_row_count": 5
      },
      {
        "fold": "46e7a2883459d4fb",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_freq_max",
          "operator": ">=",
          "threshold": 5.0,
          "train_metrics": {
            "accuracy": 0.7608695652173914,
            "fn": 0,
            "fp": 66,
            "precision": 0.76,
            "predicted_positive": 275,
            "recall": 1.0,
            "tn": 1,
            "total": 276,
            "tp": 209
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 4,
          "precision": 0.0,
          "predicted_positive": 4,
          "recall": null,
          "tn": 0,
          "total": 4,
          "tp": 0
        },
        "test_row_count": 4
      },
      {
        "fold": "c5a59a95c2c9971a",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_freq_max",
          "operator": ">=",
          "threshold": 5.0,
          "train_metrics": {
            "accuracy": 0.7581227436823105,
            "fn": 0,
            "fp": 67,
            "precision": 0.7572463768115942,
            "predicted_positive": 276,
            "recall": 1.0,
            "tn": 1,
            "total": 277,
            "tp": 209
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      }
    ]
  },
  {
    "all_holdouts_pass": false,
    "context_folds": "16/28",
    "dataset_folds": "2/5",
    "feature": "pool_candidate_task_set_same_size_overlap_max",
    "instance_folds": "0/4",
    "worst_context_folds": [
      {
        "fold": "3f914a0d2b97fd27",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_set_same_size_overlap_max",
          "operator": "<=",
          "threshold": 2.0,
          "train_metrics": {
            "accuracy": 0.7672727272727272,
            "fn": 6,
            "fp": 58,
            "precision": 0.7777777777777778,
            "predicted_positive": 261,
            "recall": 0.9712918660287081,
            "tn": 8,
            "total": 275,
            "tp": 203
          }
        },
        "test": {
          "accuracy": 0.4,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 2,
          "total": 5,
          "tp": 0
        },
        "test_row_count": 5
      },
      {
        "fold": "c5a59a95c2c9971a",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_set_same_size_overlap_max",
          "operator": "<=",
          "threshold": 2.0,
          "train_metrics": {
            "accuracy": 0.7689530685920578,
            "fn": 6,
            "fp": 58,
            "precision": 0.7777777777777778,
            "predicted_positive": 261,
            "recall": 0.9712918660287081,
            "tn": 10,
            "total": 277,
            "tp": 203
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      },
      {
        "fold": "d60fcf4b919b7d22",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_set_same_size_overlap_max",
          "operator": "<=",
          "threshold": 2.0,
          "train_metrics": {
            "accuracy": 0.7689530685920578,
            "fn": 6,
            "fp": 58,
            "precision": 0.7777777777777778,
            "predicted_positive": 261,
            "recall": 0.9712918660287081,
            "tn": 10,
            "total": 277,
            "tp": 203
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      }
    ]
  },
  {
    "all_holdouts_pass": false,
    "context_folds": "15/28",
    "dataset_folds": "4/5",
    "feature": "pool_candidate_task_set_max_jaccard",
    "instance_folds": "2/4",
    "worst_context_folds": [
      {
        "fold": "3f914a0d2b97fd27",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_set_max_jaccard",
          "operator": "<=",
          "threshold": 1.0,
          "train_metrics": {
            "accuracy": 0.76,
            "fn": 0,
            "fp": 66,
            "precision": 0.76,
            "predicted_positive": 275,
            "recall": 1.0,
            "tn": 0,
            "total": 275,
            "tp": 209
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 5,
          "precision": 0.0,
          "predicted_positive": 5,
          "recall": null,
          "tn": 0,
          "total": 5,
          "tp": 0
        },
        "test_row_count": 5
      },
      {
        "fold": "46e7a2883459d4fb",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_set_max_jaccard",
          "operator": "<=",
          "threshold": 1.0,
          "train_metrics": {
            "accuracy": 0.7572463768115942,
            "fn": 0,
            "fp": 67,
            "precision": 0.7572463768115942,
            "predicted_positive": 276,
            "recall": 1.0,
            "tn": 0,
            "total": 276,
            "tp": 209
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 4,
          "precision": 0.0,
          "predicted_positive": 4,
          "recall": null,
          "tn": 0,
          "total": 4,
          "tp": 0
        },
        "test_row_count": 4
      },
      {
        "fold": "c5a59a95c2c9971a",
        "passes": false,
        "rule": {
          "available": true,
          "feature": "pool_candidate_task_set_max_jaccard",
          "operator": "<=",
          "threshold": 1.0,
          "train_metrics": {
            "accuracy": 0.7545126353790613,
            "fn": 0,
            "fp": 68,
            "precision": 0.7545126353790613,
            "predicted_positive": 277,
            "recall": 1.0,
            "tn": 0,
            "total": 277,
            "tp": 209
          }
        },
        "test": {
          "accuracy": 0.0,
          "fn": 0,
          "fp": 3,
          "precision": 0.0,
          "predicted_positive": 3,
          "recall": null,
          "tn": 0,
          "total": 3,
          "tp": 0
        },
        "test_row_count": 3
      }
    ]
  }
]
```

## Checks

```json
{
  "all_rows_joined_to_manifest": true,
  "derived_features_populated": true,
  "diagnostic_not_production_selector": true,
  "explicit_forbidden_signature_payload_status_accounted": true,
  "input_rows_exist": true,
  "manifest_cases_exist": true,
  "no_robust_multifeature_model_with_derived_features": true,
  "no_robust_single_derived_feature": true
}
```