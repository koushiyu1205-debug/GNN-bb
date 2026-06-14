# BPC_future 根因审计补充：matched-context audit

日期：2026-06-13

## 目标

本轮继续只读分析，不运行 solver，不修改 pricing / RMP / Pulse 主线。

目标是检查更接近因果的问题：

> 在相同 instance/profile 这样的 matched context 内，pre-batch features 是否仍能稳定区分 improved / worsened？

如果 matched context 内仍然稀疏、方向混乱，就说明现有观测日志不足以推出 production selector，下一步必须做 counterfactual / replay。

## 输入与脚本

输入：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/stage_rows.csv
```

脚本：

```text
BPC_future/scripts/analyze_matched_context_audit.py
```

复跑：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_matched_context_audit.py \
--output-dir BPC_future/results/root_cause_matched_context_audit_20260613
```

输出：

```text
BPC_future/results/root_cause_matched_context_audit_20260613/summary.json
```

## 样本

20-task strict stage rows：

- rows：`288`
- improved：`136`
- worsened：`152`

## 严格 matched context：instance + profile

```text
group_count = 26
mixed_group_count = 8
mixed_rows = 94
mixed_row_share = 0.3263888888888889
```

也就是说，只有约三分之一 rows 位于同时包含 improved 和 worsened 的严格 matched context 中。

## 组内 top feature 不稳定

在 `instance + profile` mixed groups 中：

```text
top_direction_counts:
  positive = 3
  negative = 4
  flat = 1
```

top feature 分布：

```text
best_rc = 4
returned_avg_start_time = 1
returned_low_risk_arc_frac = 1
returned_pair_jaccard = 1
returned_union_size = 1
```

没有单一 top feature 支配，也没有稳定方向。

## 对根因判断的影响

这轮把结论从“跨上下文不泛化”进一步推进到：

> 在更接近可比的 matched context 内，现有观测样本仍然稀疏，并且 pre-batch feature direction 不稳定。

因此当前已有日志不足以证明一个 production selector。

## 当前不能得出的结论

不能说：

- `best_rc` 是稳定因果特征；
- `returned_union_size` 在 matched context 内可靠；
- instance/profile matched 后问题已经解决；
- 现有观测数据足以训练 production selector。

只能说：

- matched context 证据太稀疏；
- 方向仍不稳；
- 需要 counterfactual / replay 级证据。

## 下一步边界

如果继续找优化方向，应优先做：

1. 同一 pricing/RMP context 下的 batch subset / reorder replay；
2. 同一 candidate pool 的 returned batch A/B；
3. 单列或小批量列的 active-basis / incumbent impact replay；
4. 全程 no certificate effect；
5. 5/10 no-op guard。

在这些证据出现之前，不应把当前 selector 或 gate 放进生产路径。
