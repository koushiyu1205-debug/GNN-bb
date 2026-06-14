# CBF Delay-Queue Feature Gap 审计报告

日期：2026-06-14

## 目的

分析 delay scheduler 的 false-positive 是否来自在线特征缺口。
本脚本只读 H=2 dataset 和 false-positive catalog，不运行 BPC / pricing / RMP，
不生成列，不产生 certificate 或 official lower bound。

## 机器字段

```text
cbf_delay_queue_feature_gap_audit = current
status = cbf_delay_queue_feature_gap_audited
diagnostic_only = true
runs_bpc_or_pricing = false
unique_false_positive_row_count = 5
safe_like_false_positive_ratio = 0.6
single_feature_guard_available = true
production_ready = false
all_checks_pass = true
```

## 摘要

```json
{
  "false_positive_by_family": {
    "20|greedy-anchor": 1,
    "20|random-wave": 1,
    "20|sector-wave": 4
  },
  "label_counts": {
    "0": 103,
    "1": 36
  },
  "row_count": 139,
  "safe_like_false_positive_count": 3,
  "safe_like_false_positive_ratio": 0.6,
  "single_feature_guard_available": true,
  "top_single_feature_guards": [
    {
      "direction": "delay_low",
      "false_positive_count": 5,
      "false_positive_coverage": 1.0,
      "feature": "state_t_dual_l1_delta",
      "safe_delayed_count": 16,
      "safe_retained_count": 20,
      "safe_retention": 0.5555555555555556,
      "threshold": 104.269554
    }
  ],
  "unique_false_positive_row_count": 5
}
```

## 结论

- 如果 FP 在在线特征空间里更接近 safe 样本，说明当前特征不足以稳定区分 H=2 风险；
- 单特征 guard 只可作为补采/诊断线索，不能直接上线；
- 当前建议仍是 affected bucket force-delay / abstain，并补采 false-positive 邻域。
