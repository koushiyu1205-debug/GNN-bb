# CBF Delay-Queue kNN+OOD External Validation 报告

日期：2026-06-14

## 目的

用独立 train / validation trajectory datasets 验证 kNN+OOD delay scheduler。
该脚本只读 JSONL，不运行 BPC / pricing / RMP，不生成列，不产生
certificate 或 official bound。

## 机器字段

```text
cbf_delay_queue_knn_ood_external_validation = current
status = external_validation_audited
diagnostic_only = true
runs_bpc_or_pricing = false
train_row_count = 40
validation_row_count = 99
validation_candidate_ready = false
production_ready = false
all_checks_pass = true
```

## 摘要

```json
{
  "safe_radius": 5.250101333032731,
  "threshold": 0.8,
  "train_label_counts": {
    "0": 22,
    "1": 18
  },
  "validation_candidate_ready": false,
  "validation_label_counts": {
    "0": 81,
    "1": 18
  },
  "validation_metrics": {
    "by_family": {
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
        "fn": 17,
        "fp": 0,
        "negative_count": 1,
        "positive_count": 17,
        "precision": null,
        "predicted_positive": 0,
        "recall": 0.0,
        "tn": 1,
        "total": 18,
        "tp": 0
      }
    },
    "by_scale": {
      "20": {
        "false_positive_rate": 0.0,
        "fn": 18,
        "fp": 0,
        "negative_count": 81,
        "positive_count": 18,
        "precision": null,
        "predicted_positive": 0,
        "recall": 0.0,
        "tn": 81,
        "total": 99,
        "tp": 0
      }
    },
    "overall": {
      "false_positive_rate": 0.0,
      "fn": 18,
      "fp": 0,
      "negative_count": 81,
      "positive_count": 18,
      "precision": null,
      "predicted_positive": 0,
      "recall": 0.0,
      "tn": 81,
      "total": 99,
      "tp": 0
    }
  }
}
```

## 解释

- validation candidate 仍只是离线验证，不等于 production ready；
- false positive 表示 unsafe transition 被放进 HIGH_PRIORITY，必须阻止上线；
- zero high-priority 表示过于保守，不能证明 ROI；
- delay queue 仍不能 discard true-RC negative，也不能扩展 proof budget。
