# 2026-06-16 BPC_future GAT Stage 4 v14 Exact Safe-hit Batch8 A/B 结果报告

## 结论

已完整执行 v14 exact safe-id hit batch8 target-materialization A/B runbook：

```text
runbook = BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/summary.json
execution_log = BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/runbook_execution_log.jsonl
command_count = 10
failed_command_count = 0
```

5/10 no-regression 保持通过，但 20-task batch8 ROI gate 失败：

```text
stage4_v14_exact_safe_hit_batch8_roi_gate = failed
positive_trajectory_roi_count = 0
nonpositive_roi_count = 4
roi_class_counts = {'negative_retry_roi': 3, 'no_observed_roi': 1}
stage4_mutating_admission_ready = false
production_ready = false
certificate_ready = false
default_enabled = false
```

本轮最重要的结论是：exact safe-id hit 能把 candidate 定位到 true-RC negative
journey，但不能证明这些列提前加入 RMP 后有 trajectory ROI。true-RC negative、
exact-id hit、甚至局部 RMP objective 下降，都不能直接当 `HIGH_PRIORITY`
正例标签。

## 5/10 No-regression

| scale | instance | status | primal | dual | time | RMP | pricing | exact |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | apollo15 sector-wave 01 | OPTIMAL | 284.084294 | 284.084294 | 1.349622 | 2 | 6 | 4 |
| 5 | tranquillitatis sector-wave 01 | OPTIMAL | 179.982081 | 179.982081 | 0.424822 | 2 | 6 | 4 |
| 10 | apollo15 sector-wave 01 | OPTIMAL | 456.756326 | 456.756326 | 3.254514 | 5 | 16 | 11 |
| 10 | tranquillitatis sector-wave 01 | OPTIMAL | 330.363821 | 330.363821 | 1.764336 | 2 | 6 | 4 |

这说明本轮 explicit runbook 没有破坏小规模 official result；但这只是 pass-through
no-regression，不是 20-task 加速证明。

## 20-task Batch8 A/B

四组 20-task batch8 A/B 均运行在同一个 `sector-wave/tranq20_01`
`expected_context_hash=ac056820151e9ad7` 上。baseline 与 worker 均为
`TIME_LIMIT`，均无 official dual bound。

| batch | ROI class | baseline primal | worker primal | time delta | RMP delta | pricing delta | exact delta | generated delta | columns delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| r00 tasks16_20 | no_observed_roi | 632.987632 | 632.987632 | -0.067634 | 0 | 0 | 0 | -65 | -6 |
| r08 tasks3_6_11 | negative_retry_roi | 632.987632 | 632.987632 | +0.285552 | +1 | +2 | +1 | +2255 | +6 |
| r16 tasks1_15 | negative_retry_roi | 632.987632 | 632.987632 | +0.518375 | +2 | +3 | +1 | +4472 | -1 |
| r24 tasks7_15_17 | negative_retry_roi | 632.987632 | 632.987632 | +0.173593 | +1 | +2 | +1 | +2251 | +24 |

机器审计：

```text
audit_summary = BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_audit_20260616/summary.json
audit_report = BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_exact_safe_hits_batch8_ab_audit_zh.md
all_checks_pass = false
next_decision = collect_more_ab_evidence
```

这里的 `all_checks_pass=false` 是 gate 失败信号，不是脚本崩溃：A/B 样本没有任何
positive trajectory ROI，且 3/4 增加了尾部 RMP/pricing/exact workload。

## Worker 轨迹解释

target-materialization worker 确实把 32 个 exact-id hit 分成 4 组，每组加入 8 个
true-RC negative journey。加入事件和后续 RMP objective 轨迹如下：

| batch | worker addition | immediate RMP movement | later exact behavior | final A/B verdict |
| --- | --- | --- | --- | --- |
| r00 | cg7 added 8, new 8, replacement 0, active changed 0, changed_inactive_only | 655.276646 -> 635.508935 | cg8 exact added 48, active replacement 1; final 632.987632 | no observed ROI |
| r08 | cg7 added 8, new 8, replacement 0, active changed 0, changed_inactive_only | 655.276646 -> 655.276646 | cg8 exact active replacement 4; cg9 extra inactive-only exact | negative retry ROI |
| r16 | cg7 added 8, new 8, replacement 0, active changed 0, changed_inactive_only | 655.276646 -> 652.893098 | cg9 exact active replacement 3; cg10 extra inactive-only exact | negative retry ROI |
| r24 | cg7 added 8, new 7, replacement 1, active changed 1, active_replacement_task_set | 655.276646 -> 653.300606 | cg8 exact active replacement 2; cg9 extra inactive-only exact | negative retry ROI |

因此，局部 objective 改善也不是充分标签：r00/r16/r24 都有即时 RMP objective
下降，但最终没有减少 exact/pricing tail；r08 完全不动 objective，还增加尾部
retry。训练标签必须升级为 longer-horizon sequential trajectory utility，并显式惩罚
会诱发额外 exact/pricing/RMP retry 的 batch。

## Certificate Safety

本轮 certificate audit 通过：

```text
certificate_audit_summary =
  BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_certificate_audit_20260616/summary.json
certificate_audit_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_exact_safe_hits_batch8_certificate_audit_zh.md

all_checks_pass = true
violation_count = 0
global_certificate_pricing_events = 6
log_files = 13
events = 1243
finish_events = 22
optimal_finish_events = 4
```

非 OPTIMAL 的 20-task runs 没有 official dual bound。GAT / worker 没有产生
certificate、official lower bound 或 no-negative conclusion；最终 certificate
仍只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive
no-negative closure。

## 判定

本轮保留以下产物用于后续训练/审计：

```text
exact_safe_hit_candidates = true
target_materialization_rows = true
trajectory_roi_labels = negative_or_no_observed
```

但禁止把本轮候选升级为 mutating admission policy：

```text
stage4_mutating_admission_ready = false
stage4_model_scored_online_safe_source_ready = false
production_ready = false
default_enabled = false
```

下一步应从两个方向推进：

1. 对 exact-id hit 做更细的 same-context intervention 采样，构造同 context 下强正、
   弱正、负 ROI 对照，而不是把所有 true-RC negative 视为正例。
2. 训练 / threshold / checkpoint selection 继续按
   `precision_constrained_roi_maximization` 执行，目标必须直接优化 accepted ROI、
   precision、false-safe、coverage 和 tail workload，而不是只优化 rc 命中率或
   即时 objective delta。
