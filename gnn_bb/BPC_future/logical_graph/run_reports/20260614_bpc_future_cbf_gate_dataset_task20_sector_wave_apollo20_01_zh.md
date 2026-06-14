# CBF Gate Dataset 构建报告

日期：2026-06-14

## 目的

把 `journey_counterfactual_replay_capture` 日志重建出的 transition
压平成 CBF/RMP-impact gate 可训练表。该脚本只读日志，不运行 BPC / pricing，
也不改变 solver、certificate 或 official lower bound。

## 机器字段

```text
cbf_gate_dataset = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = cbf_gate_dataset_built
all_checks_pass = true
training_ready = false
production_ready = false
```

## 摘要

```json
{
  "bad_mode_transition_count": 1,
  "capture_event_count": 4,
  "cbf_feasible_count": 2,
  "cbf_infeasible_count": 1,
  "csv_path": "BPC_future/results/cbf_gate_dataset_task20_sector_wave_apollo20_01_20260614/cbf_gate_transitions.csv",
  "input_file_count": 1,
  "jsonl_path": "BPC_future/results/cbf_gate_dataset_task20_sector_wave_apollo20_01_20260614/cbf_gate_transitions.jsonl",
  "row_count": 3,
  "task_count_histogram": {
    "20": 3
  },
  "transition_count": 3
}
```

## 解释

- `label_cbf_feasible` 是当前 Lyapunov surrogate 下的观测标签，不是数学证明；
- `label_bad_mode_transition` 表示 mode switch 且 `V_next > V_t`；
- 数据只可用于 offline calibration / holdout，不可作为 pricing oracle 或 certificate；
- 当前 `training_ready` 只有在有足够覆盖且正负标签同时存在时才会变为 true。
