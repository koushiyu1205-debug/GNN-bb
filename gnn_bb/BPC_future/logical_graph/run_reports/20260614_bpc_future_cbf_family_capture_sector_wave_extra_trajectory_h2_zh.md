# CBF Trajectory Gate Dataset 构建报告

日期：2026-06-14

## 目的

把 one-step `state_t, action_t, state_{t+1}` transition 扩展为
`state_t, action_t, state_{t+H}` 轨迹标签。该脚本只读已有 capture 日志，
不运行 BPC / pricing / RMP，不改变 worker、certificate 或 official lower bound。

## 机器字段

```text
cbf_trajectory_gate_dataset = current
horizon_steps = 2
diagnostic_only = true
runs_bpc_or_pricing = false
status = cbf_trajectory_gate_dataset_built
all_checks_pass = true
training_ready = false
production_ready = false
```

## 摘要

```json
{
  "capture_event_count": 16,
  "csv_path": "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/trajectory_datasets/sector-wave-extra-h2/cbf_trajectory_gate_transitions.csv",
  "horizon_bad_mode_transition_count": 0,
  "horizon_cbf_feasible_count": 8,
  "horizon_cbf_infeasible_count": 0,
  "input_file_count": 4,
  "jsonl_path": "BPC_future/results/cbf_family_capture_worklist_global_available_20260614/trajectory_datasets/sector-wave-extra-h2/cbf_trajectory_gate_transitions.jsonl",
  "one_step_transition_count": 12,
  "row_count": 8,
  "task_count_histogram": {
    "20": 8
  }
}
```

## 解释

- `label_horizon_cbf_feasible` 评估的是观测 column batch 在 horizon 末端的 CBF slack；
- 它把目标从 one-step immediate impact 推向 trajectory Lyapunov control，但仍只是观测标签；
- 数据只可用于 offline calibration / holdout，不能作为 pricing oracle 或 certificate；
- 训练时必须排除 `state_next_*`、`delta_*`、`horizon_*` 和所有 label 字段。
