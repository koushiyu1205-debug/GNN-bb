# V525 seed61001 Node1 Controlled Replay

日期：2026-06-27

## 目的

验证 root 强制 `[5,19]` 后，node1 的 Ryan-Foster pair 到底哪些能帮助完整求解闭环。该实验只生成反事实训练标签，不改变求解器默认行为。

共同设置：

```text
instance = BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json
time_limit = 600s
root_force = force_pair_path:0:5,19=same_vehicle
journey_child_priority_mode = force_child_kind_depth:0:same_vehicle
early_branch = off
admission = off
candidate_log_top_n = 200
```

## 结果

| node1 attempt | force matched | actual selected | status | wall time | objective |
|---|---:|---|---|---:|---:|
| `[8,12]` | yes | `[8,12]` | OPTIMAL | 509.48s | 690.693243 |
| `[12,13]` | yes | `[12,13]` | OPTIMAL | 501.45s | 690.693243 |
| `[17,18]` | no | `[2,5]` | EXTERNAL_TIME_LIMIT | 600.02s | - |
| `[13,19]` | no | `[2,5]` | EXTERNAL_TIME_LIMIT | 600.03s | - |

关键解释：

`[17,18]` 和 `[13,19]` 在 root `[5,19]` 的 same-child node1 上没有匹配到 eligible candidate，force 失败后 fail-closed 回退为 baseline `[2,5]`。因此这两个结果不能作为 `[17,18]` / `[13,19]` 的严格负例，只能说明 fallback baseline `[2,5]` 在该上下文下超时。

## 严格标签

已生成：

```text
BPC_future/data/gat_branch_action_sanity/v525_seed61001_node1_controlled_replay_labels_20260627/tree_policy_event_rows.jsonl
```

标签数：

```text
controlled_replay_positive = 2
controlled_replay_hard_negative = 1
```

有效正例：

```text
[12,13] -> OPTIMAL 501.45s
[8,12]  -> OPTIMAL 509.48s
```

有效负例：

```text
[2,5] -> EXTERNAL_TIME_LIMIT 600s
```

## 关键发现

1. V490 成功路径里的 `[8,12]` 不是唯一有效 node1 正例；`[12,13]` 更快闭环。
2. 不能把“成功 run 中出现的 selected pair”直接拆成单 pair 因果正例。
3. V468 baseline log 的 node1 和 root 改成 `[5,19]` 后的 node1 不是同一个上下文；用 V468 log 导出的静态 score map 去评价 changed-tree node1 是不可靠的。
4. 离线 score map 的 `node_id/depth/pair` key 对 tree 改写后的 child context 不够用。若 branch score 要在真实 BPC 中稳定发挥作用，需要在线 GAT scoring，或者至少要把 branch-state/context hash 纳入 score key。

## 对主线的影响

当前不应继续把 V520/V522/V524 这类静态 score map 直接放进 600s full smoke。它们只能解释 baseline tree 上的候选排序，不能覆盖 GAT 自己改变 root 后产生的新 child context。

下一步更合理：

1. 将 V525 严格标签合入 tree-policy 数据；
2. 改 score-map key 或实现在线 GAT branch scoring；
3. 若暂时不做在线 scoring，则 branch score 只能安全地限制在 root/depth0，不能让静态 map 控制后续 changed-tree 节点。

## 精确性边界

```text
runs_bpc_or_pricing = true for replay only
official_bound_effect = false
certificate_effect = false
production_ready = false
solver_default_effect = false
```
