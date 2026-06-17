# 2026-06-16 GAT Target Mode Stage 3/4 v34 v15 Context-Priority Runbook Synthesis

## 结论

v34 把 v33 的 context-level structural-gap 诊断接入了 same-context
target-materialization 采样计划。它不再只按 point ROI 或普通 missed opportunity
排序，而是优先选择 negative-neighbor mixture、deep candidate gap、缺
same-context contrast 的 context。

本轮仍是 data-collection / diagnostic-only，不是 Stage 4 admission candidate：

```text
stage = Stage 3 data collection -> Stage 4 guarded A/B runbook
source = v15 score-margin + v32 embedding separation + v33 context priority
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
runs_bpc_or_pricing = false
training_label_allowed_before_worker_reachability = false
```

## Plan Artifact

```text
plan_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v34_v15_context_priority_20260616/summary.json
plan_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v34_v15_context_priority_intervention_plan_zh.md

status = ready
all_checks_pass = true
context_priority_row_count = 10
planned_context_count = 10
selected_context_count = 9
pairwise_context_target_count = 9
candidate_count = 26
skipped_counts = {'not_enough_unique_negative_targets': 1}
```

`e6b17bbf825984ae` 被跳过，因为当前 capture 下 unique true-RC negative target 只有
1 个，不能形成同 context pairwise contrast。该 context 后续需要先补 capture /
harvest 样本，而不是强行造训练标签。

候选覆盖：

```text
candidate_task_count_counts = {'20': 20, '50': 6}
candidate_family_region_counts =
  {'random-wave|tranquillitatis_balmer_like_20km': 6,
   'sector-wave|apollo15_20km': 5,
   'sector-wave|tranquillitatis_balmer_like_20km': 15}
candidate_selection_ranking_counts =
  {'active_replacement': 8, 'best_rc': 9, 'impact': 9}
candidate_impact_bucket_counts =
  {'new_support_changing': 19,
   'new_task_set': 4,
   'replacement_like': 2,
   'support_changing': 1}
```

所有 candidate 仍满足：

```text
all_candidates_true_rc_negative = true
all_candidates_have_full_capture_context = true
all_candidates_have_arc_targets = true
labels_blocked_until_worker_reachability = true
no_certificate_effect = true
```

## Runbook Artifact

```text
runbook_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v34_v15_context_priority_20260616/worker_ab_runbook/summary.json
runbook_report =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v34_v15_context_priority_20260616/worker_ab_runbook.md

status = ready
all_checks_pass = true
input_candidate_count = 26
candidate_group_count = 26
worker_batch_size = 1
worker_method = target_materialization_fixed
command_count = 54
```

54 条命令包括 5/10 sentinel no-regression commands，以及 26 组 candidate 的
baseline / target-worker 对照命令。命令只是 runbook；本轮没有执行 BPC/pricing/RMP。

## 为什么这是下一步

v32/v33 已经证明 v15 missed high-ROI 不是阈值差一点：

```text
missed_high_roi = 16
near-threshold = 0
deep/moderate candidate gap = 16
nearest_negative_closer = 10 / 16
```

因此 v34 的正确目标是补 causal same-context contrast，而不是：

- 降低 candidate threshold；
- 放宽 rescue window；
- 把 true-RC negative / exact-safe hit 当 positive label；
- 把 GAT / kNN / OOD 当 certificate source。

v23 的经验也要求保守：补 contrast 和 positive boost 能提升 high-ROI recall，但如果
没有 delay-risk / low-ROI suppression，会出现 false-safe / low-ROI 误收。因此
v34 worker 结果回流时必须同时保留 positive ROI 和 hard-negative / delay rows。

## 后续审计链条

真正运行 v34 runbook 后，必须按下面顺序处理：

1. runbook execution summary；
2. target intervention reachability audit；
3. same-context A/B ROI / tail-risk audit；
4. certificate boundary audit；
5. 使用 reachability summary 过滤 worker rows；
6. 只把 causal-valid rows 合入下一版 dataset；
7. 重新训练并跑 threshold frontier、kNN/OOD、opportunity mining、score margin、
   embedding separation；
8. 只有 precision / ROI / CI / false-safe / coverage / holdout gate 全部通过，
   才能考虑 Stage 4 shadow。

## Exact-safe 边界

- `GAT` 仍只负责定位要采样的 candidate family / context；
- target-materialization worker 只能显式 opt-in；
- 所有进入 RMP 的列仍需当前 true dual / cut / branch 下 true-RC 验证；
- worker no-column / GAT no-column / OOD no-column 不能产生 certificate；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
