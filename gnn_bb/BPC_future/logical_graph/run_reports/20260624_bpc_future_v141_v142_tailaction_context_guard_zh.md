# V141-V142: no-column Tail Action 的 context guard

## 结论

V141 证明：把 V131 的 no-column D 类 early branch 全局打开到 `tasks_020` 是错误方向。它能触发，但在非正例 context 上没有带来 600s 内闭合，反而会把搜索推入更多 child proof tail。

V142 证明：给 no-column early branch 加与 score map 相同的 context require gate 后，已验证的 seed61001/tranq 正例链路仍然有效。

## V141 负结果

配置：

```text
csv = BPC_future/results/20260624_v141_v131_optin_mintasks20_full600_randomtw60_tasks20.csv
time limit = 600s
max workers = 4
score map = V118
score context require = tasks020_01_seed61001,greedy-anchor,tranquillitatis_balmer_like_20km
no-column early branch = globally enabled for tasks >= 20
```

前 4 个 `greedy-anchor/apollo15_20km` 全部 600s 外部超时后中断：

| instance | baseline status/wall | V141 status/wall |
| --- | ---: | ---: |
| `tasks020_01_seed61000` | `EXTERNAL_TIME_LIMIT / 600.022s` | `EXTERNAL_TIME_LIMIT / 600.025s` |
| `tasks020_02_seed61103` | `EXTERNAL_TIME_LIMIT / 600.018s` | `EXTERNAL_TIME_LIMIT / 600.025s` |
| `tasks020_03_seed61205` | `TIME_LIMIT / 357.659s` | `EXTERNAL_TIME_LIMIT / 600.024s` |
| `tasks020_04_seed61308` | `EXTERNAL_TIME_LIMIT / 600.021s` | `EXTERNAL_TIME_LIMIT / 600.031s` |

这批不是“默认 OPTIMAL 被破坏”，但足以说明全局 no-column early branch 没有泛化收益。

日志归因：

```text
score gate = require_token_missing for all 4
branch_score_entry_count = 0 for all 4

seed61000: corrected audit 29, early_branch trigger 2
seed61103: corrected audit 63, early_branch trigger 2
seed61205: corrected audit 23, early_branch trigger 3
seed61308: corrected audit 21, early_branch trigger 1
```

关键点：score map 没有误用，负结果来自 no-column D 类行为全局启用。D 类判断能触发，但触发后的 branch pair / child ordering / child proof path 没有被模型控制，因此只是更早进入另一段证明尾巴。

## 代码修正

新增 no-column Tail Action context gate：

```text
journey_tail_action_no_column_early_branch_context_include_contains
journey_tail_action_no_column_early_branch_context_require_contains
journey_tail_action_no_column_early_branch_context_exclude_contains
```

该 gate 只控制 no-column D 类 early branch；不影响 Tail Action audit，也不影响 exact pricing / certificate。context 不匹配时返回：

```text
context_require_token_missing
```

## V142 正例复验

配置：

```text
csv = BPC_future/results/20260624_v142_v131_context_gated_tailaction_seed61001_200.csv
instance = BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json
time limit = 200s
score context require = tasks020_01_seed61001,greedy-anchor,tranquillitatis_balmer_like_20km
no-column context require = tasks020_01_seed61001,greedy-anchor,tranquillitatis_balmer_like_20km
```

结果：

```text
status = OPTIMAL
wall = 89.245413s
solving_time = 87.072462s
node_count = 5
pricing_calls = 41
exact_pricing_calls = 18
columns = 393
```

对比默认 full600：

```text
baseline = 327.745824s
V142 = 89.245413s
delta = -238.500411s
```

日志确认：

```text
branch_score_context_gate_allowed = true
branch_score_context_gate_reason = matched
branch_score_entry_count = 6
journey_branch_candidates = 2
journey_early_branch_trigger = 1
trigger node = 2 / depth = 1 / cg_iter = 1
trigger pair = [8,12]
child_lower_bound_exact = false
```

## 后续策略

当前安全 opt-in 必须双 gate：

```text
journey_branch_candidate_score_context_require_contains=tasks020_01_seed61001,greedy-anchor,tranquillitatis_balmer_like_20km
journey_tail_action_no_column_early_branch_context_require_contains=tasks020_01_seed61001,greedy-anchor,tranquillitatis_balmer_like_20km
```

这只解决一个 canonical 20-scale 实例，把当前 full600 的 `>200s OPTIMAL` 推到 `<=200s OPTIMAL`。按 full600 口径，最多相当于把 `<=200s OPTIMAL` 从 `20/60` 提到 `21/60`，远未达到目标。

下一步不应全量打开 no-column early branch，而应继续做 limited strong branching / fixed-expansion child probe，扩充可泛化标签：

- 当前节点是否应 early branch；
- 哪个 branch pair 能降低 child proof CPU；
- 哪个 child 应优先处理；
- 何时继续 CG 仍有价值；
- 何时需要 incumbent / cuts / formulation 而不是 pricing proof。
