# CBF kNN+OOD Sector-Wave Audit-Only Smoke 结果报告

日期：2026-06-14

## 目标

验证第一个通过 scale-level 与 family-level 离线审计的 kNN+OOD delay
scheduler 候选，在真实 `20|sector-wave` solver capture 轨迹中是否会产生
high-priority admission 信号。

本轮仍是 audit-only：

- 不启用 active worker；
- 不改变 RMP；
- 不生成列；
- 不影响 certificate；
- 不影响 official lower bound；
- 不延长 final judge 证明预算。

## Runbook

- 脚本：`BPC_future/scripts/build_cbf_knn_ood_sector_wave_smoke_runbook.py`
- 摘要：`BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/summary.json`
- Runbook 报告：
  `BPC_future/logical_graph/run_reports/20260614_bpc_future_cbf_knn_ood_sector_wave_smoke_runbook_zh.md`

候选参数：

```text
knn_k = 3
max_neighbor_unsafe_fraction = 0.0
min_high_priority_threshold = 0.8
safe_radius_quantile = 1.0
safe_radius_multiplier = 1.0
unsafe_action = delay_not_reject
```

## Capture Smoke

目标实例：

```text
apollo sector-wave 01
tranquillitatis sector-wave 01
apollo sector-wave 05
tranquillitatis sector-wave 05
```

结果：

```text
capture_event_count = 16
trajectory_validation_row_count = 8
task_count_histogram = {"20": 8}
horizon_cbf_feasible_count = 5
horizon_cbf_infeasible_count = 3
```

solver 状态：

```text
apollo sector-wave 01: EXTERNAL_TIME_LIMIT
tranquillitatis sector-wave 01: TIME_LIMIT
apollo sector-wave 05: TIME_LIMIT
tranquillitatis sector-wave 05: TIME_LIMIT
```

## kNN+OOD Capture Validation

摘要：

```text
summary = BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_knn_ood_capture_validation/summary.json
report = BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_knn_ood_capture_validation_zh.md
```

结果：

```text
all_checks_pass = true
validation_candidate_ready = false
validation_row_count = 8
fp = 0
predicted_positive = 0
tp = 0
fn = 5
tn = 3
recall = 0.0
false_positive_rate = 0.0
production_ready = false
official_bound_effect = false
```

新增逐行 decision 诊断后，拒绝原因是：

```text
decision_reason_counts = {
  delay_probability_below_threshold: 5,
  delay_neighbor_unsafe_fraction: 3
}

positive_delay_reason_counts = {
  delay_probability_below_threshold: 3,
  delay_neighbor_unsafe_fraction: 2
}

threshold = 0.8
safe_radius = 7.000135110710308
decision_records = BPC_future/results/cbf_knn_ood_sector_wave_smoke_runbook_20260614/sector_wave_knn_ood_capture_validation/external_validation/decision_records.jsonl
```

## 解释

本轮最重要的结论是：

```text
真实 sector-wave audit-only smoke 中，k=3 kNN+OOD 候选仍然全 delay。
```

这说明：

- 候选仍然安全，没有 unsafe high-priority；
- 但它没有产生任何 high-priority admission；
- 主要不是 safe-radius OOD 在挡，而是 probability threshold 与 kNN unsafe-neighbor 两层在挡；
- 因此没有 RMP movement / tail retry ROI 证据；
- 不能进入 active worker；
- 不能进入 production gate；
- 不能影响 certificate / official lower bound。

## 结论

这个候选没有“继续到 worker”的原因已经从“缺真实 smoke”变成了：

```text
真实 sector-wave smoke 下 predicted_positive = 0。
```

也就是说，当前 kNN+OOD gate 仍然过保守。下一步如果继续 CBF 路线，应优先
增加真实 mixed / positive trajectory capture，或用更强结构表示区分
“probability 低但真实稳定”的正例，以及“邻居里有 unsafe 但当前 action
实际稳定”的边界正例。GAT 的合理位置是在这里提供 residual-family / graph
embedding，再由 kNN/OOD 或等价安全壳保守放行；不应直接启用 worker，也不应
扩大 proof/final-judge 时间预算。
