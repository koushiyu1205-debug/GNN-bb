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
  "capture_event_count": 22,
  "csv_path": "BPC_future/results/cbf_trajectory_gate_dataset_random_wave_h2_20260614/cbf_trajectory_gate_transitions.csv",
  "horizon_bad_mode_transition_count": 6,
  "horizon_cbf_feasible_count": 7,
  "horizon_cbf_infeasible_count": 7,
  "input_file_count": 4,
  "jsonl_path": "BPC_future/results/cbf_trajectory_gate_dataset_random_wave_h2_20260614/cbf_trajectory_gate_transitions.jsonl",
  "one_step_transition_count": 18,
  "row_count": 14,
  "task_count_histogram": {
    "20": 14
  }
}
```

## 解释

- `label_horizon_cbf_feasible` 评估的是观测 action 在 horizon 末端的 CBF slack；
- 它比 one-step 标签更接近 trajectory Lyapunov control，但仍只是观测标签；
- 数据只可用于 offline calibration / holdout，不能作为 pricing oracle 或 certificate；
- 训练时必须排除 `state_next_*`、`delta_*`、`horizon_*` 和所有 label 字段。
