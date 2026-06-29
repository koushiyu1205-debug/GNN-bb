# V526 Branch State-Key Score Gate Implementation

日期：2026-06-27

## 目标

落实 branch score 主线里的关键修正：GAT/score map 只能影响 Ryan-Foster 分支候选排序和 opt-in early branch 触发，不能提供 official bound、certificate 或剪枝依据；同时避免把 baseline tree 的 `node_id/depth/pair` 分数误用于 branch policy 改变后的 child context。

## 已实现

1. `journey_branch_candidates` 日志继续记录 baseline/scored/selected pair、score coverage、candidate coverage，并新增：
   - `branch_constraints`
   - `branch_state_key`
   - `branch_score_require_state_key`

2. solver 的 branch score lookup 支持 state-specific key：
   - 普通 key：`node:1:depth:1:8,12`
   - state key：`state:RF(5,19)=same_vehicle::node:1:depth:1:8,12`

3. 新增配置：
   - `journey_branch_candidate_score_require_state_key=True`

   打开后，score lookup 只接受当前 branch constraints 对应的 state key；缺失时回退到正常 fractionality/CG/final-probe 路径，不会裸触发 score-gated early branch。

4. `journey_early_branch_score_gate` 已接入 state-key：
   - score availability 按当前 `node.branch_constraints` 统计；
   - score 缺失或上下文不匹配时 fail closed；
   - child 仍只继承合法旧 lower bound，不把当前 RMP objective 当 exact node bound。

5. `export_gat_branch_action_score_map.py` 已导出 state fields：
   - `branch_constraints`
   - `branch_state_key`
   - `state_key`
   - `state_scoped_key`

   对旧日志的处理规则：
   - 有 `branch_state_key`：直接使用；
   - 有 `branch_constraints`：拼成 state key；
   - 无约束且 `depth=0`：标为 `root`；
   - 无约束且 `depth>0`：不伪造 state key。

## 为什么需要这个修改

V525 controlled replay 显示，同一个 seed61001 的 `node 1` 在不同 root branch 后代表不同 child context。仅用 `node_id/depth/pair` 会把 baseline tree 的 node1 分数套到 changed-tree 的 node1 上。

这会导致两个问题：

- score map coverage 看起来命中，但实际命中的是错误上下文；
- early branch gate 可能在不该相信分数的节点上触发。

state-key 后，score 必须同时匹配 instance、node/depth/pair 和 branch constraints，才能进入 opt-in 分支排序。

## 验证

已通过：

```text
python -m py_compile BPC_future/solver/journey_driver.py BPC_future/scripts/export_gat_branch_action_score_map.py BPC_future/scripts/train_gat_branch_action_sanity.py BPC_future/scripts/build_gat_tree_policy_event_dataset.py BPC_future/scripts/expand_gat_tree_policy_context_competitors.py

python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_score_rows_filter_by_instance_context \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_score_rows_do_not_collapse_duplicate_instance_keys \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_score_rows_preserve_branch_state_keys \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_early_branch_score_gate_requires_confident_scored_pair \
  BPC_future.tests.test_gat_branch_action_sanity_training \
  BPC_future.tests.test_gat_tree_policy_event_dataset \
  BPC_future.tests.test_expand_gat_tree_policy_context_competitors
```

结果：`Ran 11 tests ... OK`

## 当前状态

代码层已经支持 state-aware score map，但还没有重新导出新的 state-key score map，也没有重新跑 12-instance smoke / full60。

下一步应按这个顺序走：

1. 用带 `branch_state_key` 的新日志重新导出 V527 score map；
2. 配置 `journey_branch_candidate_score_require_state_key=True`；
3. 先跑 12-instance smoke；
4. 若 5/10 无退化、20 有真实 capped mean 或 OPTIMAL 数改善，再跑 random-TW 20 full60。

## 边界

这个改动不解决训练标签不足，也不直接提高 LP bound。它解决的是 branch score 的上下文错配问题，是让后续 GAT branch policy 能安全接入真实求解的必要前置条件。
