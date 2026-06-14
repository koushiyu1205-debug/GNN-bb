# BPC_future 根因 Counterfactual Capture Priority 报告

日期：2026-06-13

## 目标

本轮只回答一个问题：

> 现有 exact-context replay 数据还不够支撑 production selector 时，下一步应该优先补哪个 no-certificate-effect capture context？

这不是优化实验，不改变 solver，不开启 worker，不产生 certificate，也不证明 20-task wall time 已经可改善。

## 输入

使用已有诊断产物：

- `BPC_future/results/root_cause_counterfactual_replay_candidates_20260613/candidates.csv`
- `BPC_future/results/root_cause_counterfactual_replay_candidates_20260613/summary.json`
- `BPC_future/results/root_cause_counterfactual_capture_target_coverage_20260613/summary.json`
- `BPC_future/results/root_cause_counterfactual_replay_dataset_structure_20260613/summary.json`

## 结果摘要

```text
candidate_count = 40
recommended_candidate_ids = replay_candidate_001, replay_candidate_003, replay_candidate_004
covered_recommended_candidate_ids = replay_candidate_001, replay_candidate_004
uncovered_recommended_candidate_ids = replay_candidate_003
all_checks_pass = true
```

最高优先级：

```text
candidate_id = replay_candidate_003
priority_reason = recommended_target_uncovered
candidate_risk = low_context_noise
context_key = mt20_greedy_apollo_01|3|heuristic|16862add48072518|780.586496
context_label_counts = {"improved": 1, "worsened": 1}
improved_best_rc = -20.1912655
worsened_best_rc = -64.283449
```

含义：

- `replay_candidate_003` 是当前唯一未被 exact capture 覆盖的推荐 replay target；
- 它对应的 context 同时有 improved / worsened 标签，适合补充 selector calibration；
- 它不是 production selector，也不是 wall-time speedup 证据。

## Dataset 结构约束

当前 exact replay 数据仍然标签覆盖不均衡：

```text
dataset_mixed_label_group_count = 1
context_mixed_label_group_count = 5
context_single_label_row_share = 0.6135265700483091
```

所以 priority 结果的正确用法是：

1. 先补 `replay_candidate_003` 对应 exact context；
2. 再继续补 uncovered mixed-context candidates；
3. 等数据跨 dataset / context 有更均衡的 dual-label coverage 后，再重新评估 addition-before selector。

## Checks

```text
has_uncovered_recommended_target = true
top_priority_is_uncovered_recommended_target = true
has_additional_uncovered_candidates = true
dataset_structure_still_needs_dual_label_coverage = true
priority_is_calibration_only = true
```

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_counterfactual_capture_priority.py \
--output-dir BPC_future/results/root_cause_counterfactual_capture_priority_20260613
```

结果：

```text
all_checks_pass = true
top_priority_candidate_id = replay_candidate_003
top_priority_reason = recommended_target_uncovered
```

## 结论

下一步最合理的 evidence action 是 targeted exact-context capture，而不是继续扩大 Pulse worker、开放 certificate gate 或堆更复杂 selector。

当前优先级：

1. `replay_candidate_003`
2. uncovered mixed-context candidates
3. 已覆盖 context 的 additional descriptor candidates

这一步只服务于 selector calibration。它不会改变当前总判断：

```text
has_stable_addition_before_selector = false
has_20_walltime_speedup_evidence = false
production_direction_proven = false
goal_complete = false
```
