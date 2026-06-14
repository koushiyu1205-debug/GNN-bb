# GAT Embedding kNN/OOD External Validation 报告

日期：2026-06-14

## 目的

用 trajectory-CBF GAT checkpoint 生成 embedding，再用 kNN/OOD safety shell
做外部验证。该脚本只读 GAT dataset，不运行 BPC / pricing / RMP，不生成列，
不产生 certificate 或 official bound。

## 机器字段

```text
gat_embedding_knn_ood_external_validation = current
status = gat_embedding_knn_ood_external_validation_audited
diagnostic_only = true
runs_bpc_or_pricing = false
train_row_count = 136
validation_row_count = 8
validation_candidate_ready = true
production_ready = false
all_checks_pass = true
```

## 摘要

```json
{
  "decision_reason_counts": {
    "delay_probability_below_threshold": 4,
    "high_priority": 4
  },
  "positive_delay_reason_counts": {
    "delay_probability_below_threshold": 1
  },
  "safe_radius": 5.210550097131844,
  "threshold": 0.8,
  "validation_metrics": {
    "by_family": {
      "20|gat_embedding": {
        "false_positive_rate": 0.0,
        "fn": 1,
        "fp": 0,
        "negative_count": 3,
        "positive_count": 5,
        "precision": 1.0,
        "predicted_positive": 4,
        "recall": 0.8,
        "tn": 3,
        "total": 8,
        "tp": 4
      }
    },
    "by_scale": {
      "20": {
        "false_positive_rate": 0.0,
        "fn": 1,
        "fp": 0,
        "negative_count": 3,
        "positive_count": 5,
        "precision": 1.0,
        "predicted_positive": 4,
        "recall": 0.8,
        "tn": 3,
        "total": 8,
        "tp": 4
      }
    },
    "overall": {
      "false_positive_rate": 0.0,
      "fn": 1,
      "fp": 0,
      "negative_count": 3,
      "positive_count": 5,
      "precision": 1.0,
      "predicted_positive": 4,
      "recall": 0.8,
      "tn": 3,
      "total": 8,
      "tp": 4
    }
  }
}
```

## 解释

- validation candidate 仍只是离线验证，不等于 production ready；
- fp>0 表示 GAT embedding safety shell 不安全，不能接 worker；
- predicted_positive=0 表示仍过于保守，不能证明 ROI；
- delay queue 不能 discard true-RC negative，也不能扩展 proof budget。
