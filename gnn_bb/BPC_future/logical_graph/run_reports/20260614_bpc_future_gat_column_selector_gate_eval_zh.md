# BPC_future GAT Column Selector Conservative Gate 评估

日期：2026-06-14

## 目的

本报告评估 GAT 加列选择器的保守 ADD/ABSTAIN 阈值。该评估只读离线样本，
不运行 BPC / pricing / RMP / Pulse，也不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_column_selector_gate_eval = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = gat_column_selector_gate_evaluated
all_checks_pass = true
production_ready = false
```

## Raw argmax 指标

```json
{
  "train": {
    "abstain_count": 0,
    "add_actual_count": 63,
    "add_false_negative_count": 0,
    "add_false_positive_count": 21,
    "add_precision": 0.75,
    "add_predicted_count": 84,
    "add_recall": 1.0,
    "add_true_positive_count": 63,
    "total": 90
  },
  "validation": {
    "abstain_count": 0,
    "add_actual_count": 120,
    "add_false_negative_count": 2,
    "add_false_positive_count": 24,
    "add_precision": 0.8309859154929577,
    "add_predicted_count": 142,
    "add_recall": 0.9833333333333333,
    "add_true_positive_count": 118,
    "total": 163
  }
}
```

## 选择的保守 gate

```json
{
  "reason": "max_validation_recall_under_false_positive_cap",
  "threshold": 0.923,
  "train": {
    "abstain_count": 60,
    "add_actual_count": 63,
    "add_false_negative_count": 33,
    "add_false_positive_count": 0,
    "add_precision": 1.0,
    "add_predicted_count": 30,
    "add_recall": 0.47619047619047616,
    "add_true_positive_count": 30,
    "total": 90
  },
  "validation": {
    "abstain_count": 105,
    "add_actual_count": 120,
    "add_false_negative_count": 62,
    "add_false_positive_count": 0,
    "add_precision": 1.0,
    "add_predicted_count": 58,
    "add_recall": 0.48333333333333334,
    "add_true_positive_count": 58,
    "total": 163
  }
}
```

解释：生产前策略只允许高置信 ADD；其他候选一律 ABSTAIN，交回现有 exact path。
当前 gate 只是离线阈值校准，不代表 5/10 no-regression 或 20-task speedup 已证明。

## 仍然阻塞 production 的原因

- training data has only two 20-task instances
- no 5/10 no-regression BPC A/B
- no 20/30/50/100 speedup BPC A/B
- no broad context/instance/dataset holdout
- no online opt-in solver integration yet

## 检查项

```json
{
  "chosen_respects_false_positive_cap": true,
  "diagnostic_only": true,
  "has_train_and_validation_scores": true,
  "runs_bpc_or_pricing_false": true,
  "selector_cannot_certificate": true,
  "selector_not_pricing_oracle": true
}
```
