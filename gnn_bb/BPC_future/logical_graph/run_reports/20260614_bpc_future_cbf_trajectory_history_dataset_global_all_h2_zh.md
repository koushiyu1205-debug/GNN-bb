# CBF Trajectory History Dataset 构建报告

日期：2026-06-14

## 目的

给 H=2 trajectory rows 添加只来自过去 transition 的 `history_prev_*`
在线历史特征。该脚本只读已有 dataset，不运行 BPC / pricing / RMP，
不生成列，不产生 certificate 或 official lower bound。

## 机器字段

```text
cbf_trajectory_history_dataset = current
status = cbf_trajectory_history_dataset_built
diagnostic_only = true
runs_bpc_or_pricing = false
row_count = 139
history_feature_count = 29
training_ready = true
production_ready = false
all_checks_pass = true
```

## 摘要

```json
{
  "feature_count": 59,
  "history_feature_count": 29,
  "jsonl_path": "BPC_future/results/cbf_trajectory_history_dataset_global_all_h2_20260614/cbf_trajectory_history_transitions.jsonl",
  "label_counts": {
    "0": 103,
    "1": 36
  },
  "row_count": 139,
  "task_count_histogram": {
    "10": 3,
    "20": 133,
    "4": 3
  }
}
```

## 解释

- `history_prev_*` 只来自同一 trajectory 中更早的 one-step transition；
- 不加入当前 row 的 `horizon_*`、`state_next_*` 或 `delta_*` 未来字段；
- 该数据集只能用于 offline holdout / feature-gap 诊断，不能直接接 production。
