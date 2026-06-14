# CBF Gate Dataset Readiness 审计报告

日期：2026-06-14

## 目的

本报告只审计已构建的 `cbf_gate_transitions.jsonl`，判断其是否具备
离线 CBF/RMP-impact gate 训练或校准的最低覆盖。它不运行 BPC / pricing / RMP，
也不训练模型。

## 机器字段

```text
cbf_gate_dataset_readiness = current
status = cbf_gate_dataset_training_ready
diagnostic_only = true
runs_bpc_or_pricing = false
all_checks_pass = true
training_ready = true
production_ready = false
```

## 摘要

```json
{
  "bad_mode_transition_count": 139,
  "cbf_feasible_count": 30,
  "cbf_infeasible_count": 151,
  "checks": {
    "all_rows_no_certificate_effect": true,
    "cbf_label_coverage": true,
    "instance_count_meets_minimum": true,
    "no_decode_errors": true,
    "row_count_meets_minimum": true,
    "task20_coverage": true
  },
  "decode_error_count": 0,
  "input_file_count": 1,
  "row_count": 181,
  "task_count_histogram": {
    "10": 4,
    "20": 172,
    "4": 5
  },
  "unique_instance_count": 14
}
```

## 解释

- `training_ready=false` 表示当前数据只能用于链路 smoke 或人工审计；
- `all_checks_pass=true` 只表示数据行保持 no-certificate-effect，不代表样本足够；
- production gate 仍需后续 holdout / calibration / no-regression A/B。
