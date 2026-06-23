# GAT Multi-Batch Worker Batch-Impact Rows 报告

日期：2026-06-19

## 目的

把 guarded target-materialization worker A/B 的日志转换成 Stage 3 可用的
same-context target intervention rows。只有 expected context 命中、target materialized、
同 stage 发生 column addition、并且下一轮 RMP 可见时，才允许输出训练 row。

该脚本只读日志，不运行 BPC / pricing / RMP / worker，不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_multibatch_worker_batch_impact_rows = current
status = built
candidate_count = 38
row_count = 35
positive_objective_improvement_count = 23
non_improving_objective_count = 12
positive_trajectory_roi_count = 23
nonpositive_trajectory_roi_count = 12
roi_class_counts = {'not_audited': 35}
signature_sample_row_count = 35
context_count = 35
pairwise_context_count = 0
largest_context_size = 1
reachability_record_count = 0
reachability_allowed_candidate_count = 0
skipped_counts = {'missing_target_materialized_worker_event': 3}
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = false
```

## 边界

- CSV-level ROI 不能直接变成训练标签；必须有 worker target causal match；
- 如果提供 A/B audit summary，最终 trajectory ROI 覆盖即时 RMP objective 标签；
- batch target row 必须带 worker returned signature samples，避免把 batch8 退化成单列标签；
- target materialization 只说明该负列被找到并加入，不说明 no-negative closure；
- 输出 row 仍是 diagnostic-only，后续 dataset/training/checkpoint 也必须保持 production_ready=false；
- 最终 certificate 仍只能来自当前 branch/cut/dual 的 full exact pricing closure。
