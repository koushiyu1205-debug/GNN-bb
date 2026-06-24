# V134-V140: V131 Opt-In 在 5/10 random-TW 60-instance 上的 no-regression 复验

## 背景

V131 组合把 V118 context-gated branch score map 与 D 类 no-column Tail Action Controller 组合后，在 canonical 20-scale greedy-anchor seed61001 上把单实例推进到 `OPTIMAL`，但这还不能直接进入更大规模主线。进入 20-scale 60-instance 之前，先要证明它不会污染 5/10 小规模基线。

本轮补了两个保护：

- `journey_branch_candidate_score_context_require_contains`：所有 context token 都必须命中，避免 V118 这种静态 20-scale score map 被 greedy-anchor 5/10 误用。
- `journey_tail_action_no_column_early_branch_min_tasks=20`：no-column D 类 early branch 只在 20+ 规模启用，避免 10-scale 长尾被提前分支扰动。

## 关键发现

V135 暴露了一个真实 10-scale 回退：

```text
instance = tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_10_seed51929
current baseline = 39.307545s
V135 no-column opt-in = 47.194706s
delta = +7.887161s
```

单实例复验显示，加入 `journey_tail_action_no_column_early_branch_min_tasks=20` 后，该实例回到正常区间：

```text
default single = 32.43s
V137 no min_tasks = 44.56s
V138 min_tasks=20 = 32.40s
V140 full run = 34.702234s
```

这说明问题不是 score map，而是 no-column Tail Action Controller 对 10-scale 也启用后改变了搜索路径。`min_tasks=20` 是必要保护。

## 5-scale 复验

```text
csv = BPC_future/results/20260624_v139_v131_optin_mintasks20_full600_randomtw60_tasks5.csv
rows = 60
status = 60/60 OPTIMAL
avg wall = 2.424140s
max wall = 2.893649s
```

对比 `20260623_current_full600_randomtw60_tasks5.csv`：

```text
avg delta = -2.683150s
max delta = -1.225103s
>1s regression = 0
status changes = 0
```

对比 `20260623_after_v3_default_full600_randomtw60_tasks5.csv`：

```text
avg delta = -1.994422s
max delta = +0.218848s
>1s regression = 0
status changes = 0
```

## 10-scale 复验

```text
csv = BPC_future/results/20260624_v140_v131_optin_mintasks20_full600_randomtw60_tasks10.csv
rows = 60
status = 60/60 OPTIMAL
avg wall = 6.613966s
max wall = 46.687774s
```

对比 `20260623_current_full600_randomtw60_tasks10.csv`：

```text
avg delta = -0.763676s
max delta = +0.083491s
min delta = -12.165757s
>1s regression = 0
>1s improvement = 7
status changes = 0
```

对比 `20260623_after_v3_default_full600_randomtw60_tasks10.csv`：

```text
avg delta = -0.187235s
max delta = +0.589781s
min delta = -5.303388s
>1s regression = 0
>1s improvement = 2
status changes = 0
```

和 V135 相比，`seed51929` 的回退已经消失：

```text
V135 = 47.194706s
V140 = 34.702234s
delta = -12.492472s
```

V140 相对 V135 仍有 4 个 >1s 波动，但 V135 不是 no-regression contract；正式 contract 是对 `current` 和 `after_v3` 两个小规模基线均无 >1s 回退。

## Gate 边界

这批 external batch 的 `logs_...` 目录没有保留 FutureLogger JSON start/audit 事件，CSV 也不含 branch-score gate 字段。因此 gate 行为不能从这批 run 的审计行直接统计。

当前证据链是：

- 代码层新增 all-token `require_contains` gate；
- 单测覆盖 mismatched map 禁用与 all-token required gate；
- 运行配置要求 `tasks020_01_seed61001,greedy-anchor,tranquillitatis_balmer_like_20km`，5/10 实例天然缺少 `tasks020_01_seed61001`；
- 代码层新增 no-column early branch `min_tasks` gate；
- 单实例 V138 与全量 V140 都修复了 V135 的 10-scale 回退。

## 当前结论

V131 opt-in 可以继续进入 20-scale 受控诊断，但必须带上：

```text
journey_branch_candidate_score_context_require_contains=tasks020_01_seed61001,greedy-anchor,tranquillitatis_balmer_like_20km
journey_tail_action_no_column_early_branch_min_tasks=20
```

这仍不是 20-scale 全量达标证据。它只证明：

- 静态 in-context branch score map 不会误用到 5/10；
- D 类 no-column early branch 不会再伤 5/10；
- 5/10 random-TW 60-instance 当前满足 no-regression。

下一步应该在 random-TW 20-scale 60-instance 上跑 600s 受控诊断，重点看 200s 内未闭合实例的类型：是 D 类 branch proof tail、branch pair/child ordering 错误，还是 `z_RMP < UB` 下 incumbent/cuts/formulation 不够强。
