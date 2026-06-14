# GAT Embedding kNN/OOD Capture Validation 报告

日期：2026-06-14

## 目的

把已有 capture JSONL 日志串成 GAT embedding + kNN/OOD 外部验证。
该脚本只读日志和数据集，不运行 BPC / pricing / RMP，不生成列，
不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_embedding_knn_ood_capture_validation = current
status = gat_embedding_knn_ood_capture_validation_audited
diagnostic_only = true
runs_bpc_or_pricing = false
validation_row_count = 8
validation_candidate_ready = true
production_ready = false
all_checks_pass = true
```

## 摘要

```json
{
  "capture_paths": [
    "BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_capture/logs"
  ],
  "decision_reason_counts": {
    "delay_probability_below_threshold": 4,
    "high_priority": 4
  },
  "gat_validation_dataset_dir": "BPC_future/results/gat_embedding_knn_ood_sector_wave_capture_validation_20260614/gat_validation_dataset",
  "trajectory_dataset": "BPC_future/results/gat_embedding_knn_ood_sector_wave_capture_validation_20260614/trajectory_validation_dataset/cbf_trajectory_gate_transitions.jsonl",
  "validation_candidate_ready": true,
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
  },
  "validation_row_count": 8
}
```

## Exactness Guard

- GAT embedding 不是 pricing oracle；
- kNN/OOD gate 只能把负列排成 HIGH_PRIORITY 或 DELAY_QUEUE；
- DELAY_QUEUE 不能永久丢弃 true-RC negative，也不能延长 exact proof budget；
- 该验证通过也只表示值得做 opt-in audit-only smoke，不表示 production ready。
