# CBF Delay-Queue kNN+OOD Capture Validation 报告

日期：2026-06-14

## 目的

把现有 capture JSONL 日志转成 trajectory validation dataset，然后用
训练集拟合的 kNN+OOD delay scheduler 做外部验证。该脚本只读日志，不运行
BPC / pricing / RMP，不生成列，不产生 certificate 或 official bound。

## 机器字段

```text
cbf_delay_queue_knn_ood_capture_validation = current
status = cbf_delay_queue_knn_ood_capture_validation_audited
diagnostic_only = true
runs_bpc_or_pricing = false
validation_row_count = 33
validation_candidate_ready = false
production_ready = false
all_checks_pass = true
```

## 摘要

```json
{
  "capture_paths": [
    "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614"
  ],
  "trajectory_dataset": "BPC_future/results/cbf_delay_queue_knn_ood_capture_validation_holdout_config_matched_20260614/trajectory_validation_dataset/cbf_trajectory_gate_transitions.jsonl",
  "validation_candidate_ready": false,
  "validation_metrics": {
    "by_family": {
      "20|greedy-anchor": {
        "false_positive_rate": 0.0,
        "fn": 0,
        "fp": 0,
        "negative_count": 33,
        "positive_count": 0,
        "precision": null,
        "predicted_positive": 0,
        "recall": null,
        "tn": 33,
        "total": 33,
        "tp": 0
      }
    },
    "by_scale": {
      "20": {
        "false_positive_rate": 0.0,
        "fn": 0,
        "fp": 0,
        "negative_count": 33,
        "positive_count": 0,
        "precision": null,
        "predicted_positive": 0,
        "recall": null,
        "tn": 33,
        "total": 33,
        "tp": 0
      }
    },
    "overall": {
      "false_positive_rate": 0.0,
      "fn": 0,
      "fp": 0,
      "negative_count": 33,
      "positive_count": 0,
      "precision": null,
      "predicted_positive": 0,
      "recall": null,
      "tn": 33,
      "total": 33,
      "tp": 0
    }
  },
  "validation_row_count": 33
}
```

## 解释

- validation candidate 仍只是只读日志验证，不等于 production ready；
- 如果 predicted_positive=0，说明当前 scheduler 对真实日志过于保守；
- 如果 fp>0，说明 scheduler 不安全，不能接 worker；
- 即使 validation 通过，下一步仍只能做 opt-in audit-only smoke。
