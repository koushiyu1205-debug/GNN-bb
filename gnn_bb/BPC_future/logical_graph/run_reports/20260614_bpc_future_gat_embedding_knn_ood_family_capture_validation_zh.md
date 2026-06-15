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
validation_row_count = 34
validation_candidate_ready = true
production_ready = false
all_checks_pass = true
```

## 摘要

```json
{
  "capture_paths": [
    "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/greedy-anchor/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json.jsonl",
    "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/greedy-anchor/logs/BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json.jsonl",
    "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/random-wave/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json.jsonl",
    "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/random-wave/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json.jsonl",
    "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/random-wave/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json.jsonl",
    "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/random-wave/logs/BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json.jsonl",
    "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave-extra/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json.jsonl",
    "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave-extra/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json.jsonl",
    "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave-extra/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json.jsonl",
    "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave-extra/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json.jsonl",
    "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json.jsonl",
    "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json.jsonl",
    "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json.jsonl",
    "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/captures/sector-wave/logs/BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json.jsonl"
  ],
  "decision_reason_counts": {
    "delay_neighbor_unsafe_fraction": 1,
    "delay_probability_below_threshold": 26,
    "high_priority": 7
  },
  "gat_validation_dataset_dir": "BPC_future/results/gat_embedding_knn_ood_family_capture_validation_20260614/gat_validation_dataset",
  "trajectory_dataset": "BPC_future/results/gat_embedding_knn_ood_family_capture_validation_20260614/trajectory_validation_dataset/cbf_trajectory_gate_transitions.jsonl",
  "validation_candidate_ready": true,
  "validation_metrics": {
    "by_family": {
      "20|gat_embedding": {
        "false_positive_rate": 0.0,
        "fn": 18,
        "fp": 0,
        "negative_count": 9,
        "positive_count": 25,
        "precision": 1.0,
        "predicted_positive": 7,
        "recall": 0.28,
        "tn": 9,
        "total": 34,
        "tp": 7
      }
    },
    "by_scale": {
      "20": {
        "false_positive_rate": 0.0,
        "fn": 18,
        "fp": 0,
        "negative_count": 9,
        "positive_count": 25,
        "precision": 1.0,
        "predicted_positive": 7,
        "recall": 0.28,
        "tn": 9,
        "total": 34,
        "tp": 7
      }
    },
    "overall": {
      "false_positive_rate": 0.0,
      "fn": 18,
      "fp": 0,
      "negative_count": 9,
      "positive_count": 25,
      "precision": 1.0,
      "predicted_positive": 7,
      "recall": 0.28,
      "tn": 9,
      "total": 34,
      "tp": 7
    }
  },
  "validation_row_count": 34
}
```

## Exactness Guard

- GAT embedding 不是 pricing oracle；
- kNN/OOD gate 只能把负列排成 HIGH_PRIORITY 或 DELAY_QUEUE；
- DELAY_QUEUE 不能永久丢弃 true-RC negative，也不能延长 exact proof budget；
- 该验证通过也只表示值得做 opt-in audit-only smoke，不表示 production ready。
