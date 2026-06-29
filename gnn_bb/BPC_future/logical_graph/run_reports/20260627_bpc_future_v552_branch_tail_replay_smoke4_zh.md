# 20260627 V552 Branch-Tail Forced Replay Smoke4 总结

## 结论

V552 用 V549 failure typing 中的 `branch_tree_plus_completion_tail` 未解实例做了 4 个 forced deep tail-action replay smoke。结果：

| run | instance | status | wall_time |
|---|---|---:|---:|
| `03_tail_action_child_order_d1_n1_1_10` | `apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103` | `EXTERNAL_TIME_LIMIT` | 600.021937 |
| `07_tail_action_child_order_d2_n3_1_5` | `apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103` | `EXTERNAL_TIME_LIMIT` | 600.021383 |
| `27_tail_action_child_order_d1_n1_2_3` | `apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308` | `EXTERNAL_TIME_LIMIT` | 600.024508 |
| `33_tail_action_child_order_d1_n1_1_15` | `apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410` | `EXTERNAL_TIME_LIMIT` | 600.022645 |

这批没有产生 strict positive，也没有产生可用于训练的完整 branch-impact 正例。它们应作为 hard negative / risk diagnostic，而不是 production score-map 数据。

## 与 V545 对比

这 3 个 apollo greedy 实例在 V545 中本来就是未解：

- seed61103：`EXTERNAL_TIME_LIMIT`
- seed61308：`EXTERNAL_TIME_LIMIT`
- seed61410：`EXTERNAL_TIME_LIMIT`

V552 强制替换深层 tail-action branch path 后仍是 600 秒外部超时，因此没有带来 wall-time gain，也没有从 non-OPTIMAL 转成 OPTIMAL。

## 日志审计

Tail-action controller：

- tail action rows：211
- `EARLY_BRANCH` class：103
- actual early branch triggers：4
- tail-action queued children：8
- no-column gate rows：54
- no-column gate main failure reasons：
  - `depth_above_max`: 30
  - `depth_below_min`: 8
  - `tail_action_not_early_branch`: 12
  - `width_guard_pool_child_width_exceeds_cap`: 4

Branch-impact audit：

- branch count：40
- forced pair branch count：9
- forced pair matched：9
- right-censored branch count：40
- usable branch-impact training count：0
- tail class：
  - `completion_bound_tail`: 27
  - `negative_chain_continues`: 1
  - `unprocessed_children`: 12
- total child completion-bound retries：148
- total child exact pricing events：219
- total child negative pricing events：225

Completion-tail profile：

- completion retry classes：
  - `completion_bound_certified_no_negative`: 3
  - `completion_bound_time_limit_no_column_uncertified`: 1
- total generated sequences：30,916,324
- total evaluated timed trips：4,749,925
- total profile generation time：762.981023s
- tail min-fill candidate：6
- tail min-fill applied：0

## 解释

V552 比 V550 更进一步：V550 是 score-gated early branch fail-closed，没有触发；V552 则强制走了 tail-action branch path，并且确实触发了 early branch。

但结果仍然没有闭环。这说明剩余失败的核心不是“没有提前分支”这么简单，而是：

1. branch 后子树仍然继续产生负列或进入 completion-bound tail；
2. child proof cost 仍然高；
3. 当前强制 path 没有显著降低完整 certificate 时间；
4. 这些 forced rows 全部右删失，不能当作稳定正例。

因此，把 early branch 裸开或继续扩 root/top-k forced replay，预期收益很低。

## 对当前优化主线的影响

当前有效结论仍然是 V545：

- branch-score ordering 可以带来真实收益；
- 真实收益来自 state-scoped branch policy path；
- 但覆盖太窄，无法解决多数失败 context。

V552 新增的负面证据说明：

- 对 `branch_tree_plus_completion_tail`，仅靠强制 tail early branch 不够；
- 下一阶段要把重点放到 child proof-cost 降低和更高质量的深层 counterfactual 标签；
- completion-bound harvest/cache/min-fill/profile cost 应与 branch policy 同步推进；
- hard negative 要进入训练/score-map guard，避免 GAT 学到“只要 tail 就提前分支”。

## Exact-Safe 边界

本轮 forced replay / early branch 仍只改变搜索顺序和子节点展开路径：

- 不把当前 RMP objective 当 exact node bound；
- 不用学习分数提供 official bound；
- 不用 replay 结果做剪枝证书；
- 子节点仍需依赖 exact pricing closure。

因此 V552 是安全的诊断实验，但不是性能改进版本。
