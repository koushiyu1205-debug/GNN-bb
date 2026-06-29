# 20260627 V538-V541：State-Rehydrated Tree Policy Overlay

## 结论

本轮把 branch-score 主线从“裸 GAT 概率 score map”推进到“strict replay evidence 的 state-scoped score map”。

关键结果：

- V537 GAT tree-policy 分数没有达到 opt-in 条件：最大分数约 `0.011`，已知严格正例排序不稳定。
- 新增 `apply_gat_tree_policy_strict_overlay.py`，把 strict tree-policy / controlled replay 标签叠加到 score rows。
- V538 只使用已有 `ancestor_forced_path`，能修 seed61001 的 node1，但无法覆盖旧成功树深层节点。
- V540 从 `source_log_file` 的 `journey_node_start.branch_constraints` 回填真实 `branch_state_key`，使深层 replay 标签可以 exact-safe 地命中。
- V541 3-instance smoke 全部 `OPTIMAL`，其中两个 V539 超时实例被修复。

这说明：当前最有效的不是继续相信裸 GAT 分数，而是先把成功树的 branch-state 上下文精确记录下来，再让 GAT 学这种 state policy。

## 实现内容

新增脚本：

`BPC_future/scripts/apply_gat_tree_policy_strict_overlay.py`

作用：

- 输入 base branch score rows。
- 输入 strict `tree_policy_event_rows.jsonl`。
- 对正例写入高分 `0.91`。
- 对 hard negative 写入低分 `0.01`。
- 对 depth > 0 的标签必须有 state key，否则 fail-closed。
- state key 来源优先级：
  - event 自带 `branch_state_key` / `branch_constraints`
  - `ancestor_forced_path`
  - `source_log_file` 中对应 `journey_node_start.branch_constraints`

新增测试：

`BPC_future/tests/test_gat_tree_policy_strict_overlay.py`

覆盖：

- ancestor path 到 `RF(...)=...` state key 的转换。
- 正例 boost / 负例 suppress。
- 从 source log 回填深层 branch state。
- 输出继续标记 `official_bound_effect=false`、`certificate_effect=false`、`production_ready=false`。

## V540 Score Map

输出：

`BPC_future/results/gat_tree_policy_strict_overlay_v540_v537_plus_v529_state_rehydrated_20260627/journey_branch_score_rows.json`

机器字段：

```text
score_row_count = 19931
events_seen = 84
overlay_counts = {'appended_overlay_row': 72, 'boost_positive': 31, 'suppress_negative': 53}
production_ready = false
official_bound_effect = false
certificate_effect = false
```

V538 之前会跳过 `70` 条 depth>0 标签；V540 通过 source-log rehydration 后全部转成 state-scoped rows。

## V541 Smoke 结果

配置：

- 3 个 20-scale random-TW 实例。
- `time_limit=600`
- `max_workers=3`
- branch score ON
- selection gate ON：`min_score=0.85`
- `journey_branch_candidate_score_require_state_key=True`
- early branch OFF
- admission OFF

结果：

| instance | baseline | V468 | V539 | V541 |
|---|---:|---:|---:|---:|
| random/tranq seed61001 | EXTERNAL 600.02 | EXTERNAL 600.02 | OPTIMAL 546.60 | OPTIMAL 546.28 |
| random/tranq seed61309 | EXTERNAL 600.02 | EXTERNAL 600.02 | EXTERNAL 600.03 | OPTIMAL 465.06 |
| sector/tranq seed61513 | EXTERNAL 600.02 | EXTERNAL 600.02 | EXTERNAL 600.03 | OPTIMAL 358.40 |

对比旧 replay：

- seed61309 旧 tree replay：`OPTIMAL 468.54`；V541：`OPTIMAL 465.06`。
- seed61513 旧 tree replay：`OPTIMAL 360.20`；V541：`OPTIMAL 358.40`。
- seed61001 controlled replay 最好约 `501.45`；V541 `546.28`，说明 seed61001 仍缺更深层 state-policy 标签。

## Gate 审计

V541 中没有 early branch：

```text
journey_early_branch_trigger = 0
exact_bad = 0
```

branch score gate：

- seed61001：`ok=3`，`missing_score_source=16`
- seed61309：`ok=14`
- seed61513：`ok=12`

这解释了性能差异：

- seed61309 / seed61513 的旧成功树基本被完整 state replay。
- seed61001 只覆盖 root 和 depth1，之后回默认分支，所以仍然慢。

## Exact-Safe 边界

本轮所有学习/overlay 只影响 Ryan-Foster pair 排序：

- 不产生 official bound。
- 不产生 certificate。
- 不参与 fathom/prune。
- depth > 0 标签必须带 `branch_state_key`，否则 fail-closed。
- child 最终仍靠原 exact pricing / completion-bound closure。

## 当前判断

V540/V541 证明了一个重要方向：

> 对 20-scale proof tail，branch decision 的关键不是单个 root pair，而是带 branch-state 的整棵 tree policy。

裸 GAT 分数的问题是：

- 分数未校准，max 远低于 score gate。
- 已知正例 rank 不稳定。
- 没有真实 branch-state 时，深层正例不能安全泛化。

因此下一步不是继续盲目训练概率头，而是：

1. 对 V468/V541 仍未 OPTIMAL 的实例采集更多 strict state replay。
2. 每条正例必须记录完整 `branch_state_key`。
3. 把 `branch_state_key`、child ordering、child proof CPU、certificate time 一起纳入训练标签。
4. 再让 GAT 学 state-conditioned tree policy，而不是只学 pair 静态分数。

## 下一步

## V542 回归与 V543 修正

V541 后直接用 V540 进入 full-60 是错误的，因为它丢掉了 V467/V468 已经验证过的 conservative root overlay 正例。

V542 partial full60 只跑出前 4 行就发现回归：

| instance | V468 | V542 |
|---|---:|---:|
| apollo greedy seed61000 | OPTIMAL 347.79 | EXTERNAL 600.02 |

原因不是 solver gate bug，而是证据缺失：

- V468 依靠 root `[12,20]`，score `0.74`，gate min `0.67`，成功闭环。
- V542 只用 V540，V540 没有这条 V467 证据。
- seed61000 因而退回 baseline root `[3,7]`，最终超时。

修正为 V543：

`BPC_future/results/gat_branch_tree_policy_merged_overlay_v543_v467_plus_v540_20260627/journey_branch_score_rows.json`

V543 合并：

- V467 当前 best conservative root overlay；
- V540 state-rehydrated tree overlay。

机器字段：

```text
score_row_count = 20768
score_ge_067_count = 44
score_ge_085_count = 30
recommended_min_score = 0.67
recommended_require_state_key = true
production_ready = false
official_bound_effect = false
certificate_effect = false
```

## V544 Merge Smoke

V544 用 V543 跑 4 个关键实例：

- V542 回归实例 seed61000；
- V541 的三个新增收益实例 seed61001 / seed61309 / seed61513。

配置：

- `journey_branch_candidate_score_path=...v543.../journey_branch_score_rows.json`
- `journey_branch_candidate_score_selection_gate_min_score=0.67`
- `journey_branch_candidate_score_require_state_key=True`
- early branch OFF
- admission OFF

结果：

| instance | V468 | V542 partial | V544 |
|---|---:|---:|---:|
| apollo greedy seed61000 | OPTIMAL 347.79 | EXTERNAL 600.02 | OPTIMAL 328.32 |
| random/tranq seed61001 | EXTERNAL 600.02 | - | OPTIMAL 547.31 |
| random/tranq seed61309 | EXTERNAL 600.02 | - | OPTIMAL 463.12 |
| sector/tranq seed61513 | EXTERNAL 600.02 | - | OPTIMAL 356.79 |

Gate 审计：

- seed61000：root `[12,20]`，score `0.74`，gate=ok。
- seed61001：3 个 state-scoped hits。
- seed61309：14 个 state-scoped hits。
- seed61513：12 个 state-scoped hits。
- `journey_early_branch_trigger=0`。

这说明 V543 是当前可进入 full60 的候选；V540 不能单独使用。

## 下一步

V544 smoke 通过后，可以进入 full-60 20-scale 测试：

- score path：`BPC_future/results/gat_branch_tree_policy_merged_overlay_v543_v467_plus_v540_20260627/journey_branch_score_rows.json`
- `journey_branch_candidate_score_require_state_key=True`
- `journey_branch_candidate_score_selection_gate_min_score=0.67`
- early branch/admission 仍关闭，避免混入额外变量。

预期：

- 至少应保住 V468 已有正例，并把 seed61001、seed61309、seed61513 从 V468 的 EXTERNAL 修成 OPTIMAL。
- 但不应期待直接达到 60/60，因为 V540 只覆盖已有 strict replay 上下文，未覆盖剩余 20 多个失败实例。
