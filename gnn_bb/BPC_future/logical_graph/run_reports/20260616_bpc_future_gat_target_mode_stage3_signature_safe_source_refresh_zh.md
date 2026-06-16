# GAT Batch Impact Safe-source Export 报告

日期：2026-06-16

## 结论

`safe_source_ready = false`
`safe_candidate_id_count = 0`

本轮完成了 Stage 3 -> Stage 4 safe-source artifact 的 signature-id 刷新：

- 使用新版 `build_gat_batch_impact_dataset.py` 重建 v3 dataset；
- 同一批 same-context rows 全部候选都生成了在线 admission 可匹配的
  `candidate_signature_ids`；
- 复跑 training / kNN-OOD / safe-source export；
- 确认旧 blocker `candidate_signature_ids_missing_or_incomplete` 已消除。

但当前 checkpoint 仍然不能作为 Stage 4 safe source。剩余 blocker 全部来自训练硬门槛：

```text
training_validation_local_gate_not_passed
knn_ood_validation_candidate_not_ready
knn_ood_validation_safety_not_ready
knn_ood_safe_precision_ci_low_met_failed
knn_ood_accepted_batch_roi_ci_low_met_failed
```

因此本轮结论是：artifact 链路已能从 offline decision records 安全映射到 online
journey signature ids；模型/样本本身仍没有通过 confidence-aware precision / ROI gate。
不能启用 mutating admission，也不能进入 20-task opt-in A/B。

该导出只服务 Stage 4 admission scheduling。它不运行 BPC / pricing / RMP，不产生
official bound，也不能作为 no-negative certificate source。

## 机器字段

```text
status = safe_source_blocked
decision_record_count = 78
high_priority_decision_record_count = 2
safe_ids_exportable = false
blockers = ['knn_ood_accepted_batch_roi_ci_low_met_failed', 'knn_ood_safe_precision_ci_low_met_failed', 'knn_ood_validation_candidate_not_ready', 'knn_ood_validation_safety_not_ready', 'training_validation_local_gate_not_passed']
production_ready = false
default_enabled = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## v3 Dataset Refresh

输入 rows：

```text
BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_same_run_dataset/same_run_batch_impact_rows_combined_v13_v14.jsonl
```

输出 dataset：

```text
BPC_future/data/gat_batch_impact/v3_signature_20260616
```

结果：

```text
sample_count = 294
candidate_count = 4569
context_match_rate = 1.0
candidate_signature_source_coverage = 1.0
candidate_signature_source_present_count = 4569
family_counts = {'greedy-anchor': 54, 'random-wave': 190, 'sector-wave': 50}
task_count_counts = {'10': 8, '100': 1, '20': 118, '30': 76, '5': 2, '50': 89}
training_ready = true
production_ready = false
```

这一步只重新物化离线样本，不重新跑 solver，不改变 benchmark 默认配置。

## Training / kNN-OOD Refresh

训练输出：

```text
BPC_future/results/gat_batch_impact_training_v3_signature_20260616/summary.json
```

关键指标：

```text
checkpoint_gate_pass = false
stage4_candidate_ready = false
best_loss_epoch_gate_pass = false
accepted_batch_count = 2
accepted_batch_rate = 0.02564102564102564
accepted_batch_roi = 0.9396930038928986
accepted_batch_roi_ci_low = 0.6137750887870789
safe_precision = 1.0
safe_precision_ci_low = 0.3423719528896193
high_priority_precision = 1.0
high_priority_precision_ci_low = 0.9229238226702192
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
```

kNN/OOD 输出：

```text
BPC_future/results/gat_batch_impact_knn_ood_audit_v3_signature_20260616/summary.json
```

关键指标：

```text
validation_candidate_ready = false
validation_safety_ready = false
accepted_batch_count = 2
safe_precision_ci_low_met = false
accepted_batch_roi_ci_low_met = false
production_block_reasons = [
  validation_safe_precision_ci_low_below_min,
  validation_accepted_batch_roi_ci_low_below_min,
  validation_candidate_not_ready
]
```

Decision records id 链路抽检：

```text
decision_records = 78
high_priority_records = 2
candidate_signature_ids_complete_all = true
high_priority_signature_ids_complete_all = true
high_priority_signature_counts = [32, 7]
```

因此 safe-source export 不再因为缺 signature id 被拦截；拦截原因已经收敛为真实
confidence lower-bound 不足。

## Config Snippet

```json
{
  "journey_gat_admission_allow_unsourced_delay": false,
  "journey_gat_admission_safe_source_ready": false,
  "journey_gat_admission_scheduler_enabled": false,
  "journey_gat_certificate_hard_filter_enabled": false,
  "journey_gat_safe_candidate_ids": [],
  "journey_gat_shadow_safe_candidate_ids": []
}
```

该 snippet 保持 scheduler disabled，避免 Stage 4 在无 safe source 时延迟 true-RC negative。

## Exactness Boundary

本轮没有运行 BPC、pricing、RMP 或 final judge，没有修改 reduced-cost 公式、pricing
universe 或 certificate 判定。

GAT / kNN / OOD 仍然：

- 不是 pricing oracle；
- 不能产生 official lower bound；
- 不能产生 certificate；
- 不能永久丢弃 true-RC negative；
- 只能在通过 Stage 3 confidence gate、Stage 4 5/10 no-regression、20-task ROI 和
  certificate safety audit 后，作为 opt-in admission scheduling safe source。

最终 optimality proof 仍只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的
no-negative closure。

## 下一步

当前最窄 blocker 已经不是 id 链路，而是 accepted batch 数太少导致 confidence lower-bound
不过线。下一步应优先做两类事情：

1. 继续采集 same-context intervention rows，尤其增加 validation holdout 上的 high-ROI
   accepted opportunities，使 `safe_precision_ci_low` 和 `accepted_batch_roi_ci_low` 有足够样本支撑；
2. 增加 threshold-grid/frontier artifact，系统列出每个候选 threshold 的 precision、ROI、
   coverage 和 reject reason，定位是模型分数排序问题、family fallback 问题，还是样本量问题。

在这两个 blocker 消除前，Stage 4 mutating admission 仍必须保持 pass-through。
