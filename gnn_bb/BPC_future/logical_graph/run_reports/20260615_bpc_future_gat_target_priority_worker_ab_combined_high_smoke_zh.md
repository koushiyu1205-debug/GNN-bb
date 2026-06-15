# GAT Target-Priority Worker A/B Combined HIGH Smoke 报告

日期：2026-06-15

## 目标

本轮验证 combined same-run GAT + kNN/OOD 产出的 HIGH_PRIORITY 候选，在真实 20-task target-priority worker A/B 中是否有可观察 ROI。

边界保持不变：

- GAT 只做 embedding / trajectory-impact 表达；
- kNN/OOD 只做安全壳；
- HIGH_PRIORITY 只是优先级，不是 certificate；
- DELAY_QUEUE 不永久丢弃负列；
- worker 只显式 opt-in；
- 不产生 official lower bound / certificate effect；
- 5/10 默认路径不能退化。

## 输入

候选来源：

`BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json`

本轮只取前 4 个 task20 HIGH_PRIORITY 候选：

`BPC_future/results/gat_target_priority_worker_ab_combined_high_smoke_20260615/top4_task20_high_candidates.json`

Runbook：

`BPC_future/results/gat_target_priority_worker_ab_combined_high_smoke_20260615/summary.json`

执行日志：

`BPC_future/results/gat_target_priority_worker_ab_combined_high_smoke_20260615/sequential_execution_log.jsonl`

## 5/10 No-regression

5-task：

| instance | status | time | primal | dual | gap |
|---|---:|---:|---:|---:|---:|
| Apollo sector-wave 005-01 | OPTIMAL | 2.44s | 284.084294 | 284.084294 | 0 |
| Tranquillitatis sector-wave 005-01 | OPTIMAL | 2.14s | 179.982081 | 179.982081 | 0 |

10-task：

| instance | status | time | primal | dual | gap |
|---|---:|---:|---:|---:|---:|
| Apollo sector-wave 010-01 | OPTIMAL | 4.91s | 456.756326 | 456.756326 | 0 |
| Tranquillitatis sector-wave 010-01 | OPTIMAL | 3.49s | 330.363821 | 330.363821 | 0 |

结论：本轮 smoke 没有观察到 5/10 no-regression 失败。

## 20-task Worker A/B

只读 audit 输出：

`BPC_future/results/gat_target_priority_worker_ab_combined_high_smoke_20260615/audit/summary.json`

审计摘要：

- record_count: 4
- positive_primal_roi_count: 0
- roi_class_counts:
  - columns_only_roi: 2
  - no_observed_roi: 2
- official_bound_effect: false
- production_ready: false
- all_checks_pass: false

`all_checks_pass=false` 的原因不是安全失败，而是没有同时观察到 positive primal ROI 和 nonpositive evidence。也就是说，本轮没有证明 worker 有收益。

| candidate | baseline | worker | baseline primal | worker primal | columns delta | exact calls delta | ROI |
|---|---:|---:|---:|---:|---:|---:|---|
| Apollo20 random-wave 61715 / d519 | TIME_LIMIT | TIME_LIMIT | 619.142683 | 619.142683 | +1 | +1 | columns_only |
| Apollo20 random-wave 61715 / 67c1 | TIME_LIMIT | TIME_LIMIT | 619.142683 | 619.142683 | -8 | 0 | none |
| Tranq20 random-wave 61205 / ddcb | TIME_LIMIT | TIME_LIMIT | 568.523092 | 568.523092 | -20 | +1 | none |
| Tranq20 random-wave 61205 / 5c52 | TIME_LIMIT | TIME_LIMIT | 568.523092 | 568.523092 | +1 | +1 | columns_only |

## 判断

这轮结果说明：

1. GAT+kNN/OOD 的离线安全壳可以产出 conservative HIGH_PRIORITY；
2. 5/10 小规模路径没有退化；
3. 但前 4 个 HIGH_PRIORITY 目标没有带来 20-task primal 改善；
4. worker 目前不能进入默认路径，也不能作为 production gate；
5. 当前问题仍然是“候选是否有长期 trajectory ROI”，而不是“候选是否 true-RC negative”。

## 下一步

不建议继续放大 worker time limit，也不建议默认启用 worker。

下一步应做两件事：

1. 对 HIGH_PRIORITY 候选加入更强的 ROI 过滤，例如优先选择历史上 `new_support_changing` 且能降低下一轮 retry / objective 的候选；
2. 继续采集 hard-tail boundary / delay-producing 样本，增加 non-improving / DELAY 标签比例。

当前结论：GAT 已经能训练，安全壳可用，但 target worker 的真实加速 ROI 尚未成立。

