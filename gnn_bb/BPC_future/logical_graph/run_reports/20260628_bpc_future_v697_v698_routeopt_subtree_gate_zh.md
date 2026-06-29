# V697-V698 RouteOpt/BKF Root-Subtree Gate 验证

## 结论

V698 验证了一个更合理的 hybrid 策略：

- 对 root 已经命中高置信 V543 state-scoped score 的子树，限制 RouteOpt/BKF 深层改写；
- 对 score 缺失或低置信 hard context，继续允许 RouteOpt/BKF phased testing 深入生效。

两条目标实例均 `OPTIMAL`：

| instance | V698 status | solver time | wall | 对比结论 |
|---|---:|---:|---:|---|
| seed61103 | OPTIMAL | `417.560312s` | `441.991747s` | 保留 RouteOpt hard-case 闭环能力 |
| seed61614 | OPTIMAL | `342.822163s` | `378.232295s` | 恢复到 V545/root-only 水平，避免 full-open 回归 |

这说明当前方向不是 `RouteOpt full-open`，而是 `score-protected + conditional subtree gate`。

## 背景

前一轮结果：

| version | seed61103 | seed61614 |
|---|---:|---:|
| V545 / V543 score overlay | EXTERNAL | `344.379775s OPTIMAL` |
| V692/V693 RouteOpt full-open | `422.843567s OPTIMAL` | `589.554913s OPTIMAL` |
| V694/V696 score-protected | `422.462635s OPTIMAL` | `399.479899s OPTIMAL` |
| V697 root-only max_depth=0 | EXTERNAL, gap `0.026290` | `342.339548s OPTIMAL` |
| V698 root-score subtree gate | `417.560312s OPTIMAL` | `342.822163s OPTIMAL` |

解释：

- full-open RouteOpt 可以救 seed61103，但会破坏 seed61614 的已验证好路径。
- 全局 root-only 可以救 seed61614，但会丢掉 seed61103 的深层 RouteOpt 闭环能力。
- V698 用 root 分支的 score gate 决定是否保护整个子树，正好避开这两个极端。

## V698 配置

核心配置：

```text
journey_branch_candidate_priority=routeopt_bkf_staged
journey_branch_candidate_phased_testing_enabled=true
journey_branch_candidate_phased_testing_base_priority=branch_score_horizon
journey_branch_candidate_score_path=BPC_future/results/gat_branch_tree_policy_merged_overlay_v543_v467_plus_v540_20260627/journey_branch_score_rows.json
journey_branch_candidate_score_selection_gate_enabled=true
journey_branch_candidate_score_selection_gate_min_score=0.67
journey_branch_candidate_score_selection_gate_require_score_source=true
journey_branch_candidate_score_require_state_key=true
journey_branch_candidate_phased_testing_preserve_score_gate_winner_enabled=true
journey_branch_candidate_phased_testing_root_score_gate_subtree_max_depth=0
journey_branch_candidate_phased_testing_phase1_lp_enabled=true
journey_branch_candidate_phased_testing_phase2_heuristic_enabled=true
journey_branch_candidate_phased_testing_dynamic_k_enabled=true
journey_branch_candidate_phased_testing_dynamic_k_diverse_pool_enabled=true
```

注意：V698 没有设置全局 `journey_branch_candidate_phased_testing_max_depth=0`。因此只有 root score gate 通过的子树会被保护；低置信/缺 score 子树仍允许 RouteOpt/BKF 深层 testing。

## 运行产物

```text
BPC_future/results/20260628_v698_routeopt_score_protected_root_subtree_gate_seeds61103_61614/results.csv
```

## Branch Path 诊断

### seed61103

结果：

- status：`OPTIMAL`
- solver time：`417.560312s`
- nodes：`13`
- branch count：`6`
- fathom：`bound=7`
- completion-bound retry：`14`

Branch path：

| depth | selected pair | subtree gate |
|---:|---|---|
| 0 | `[12,13]` | not gated |
| 1 | `[3,17]` | not gated |
| 1 | `[1,2]` | not gated |
| 2 | `[3,8]` | not gated |
| 2 | `[6,8]` | not gated |
| 2 | `[1,18]` | not gated |

这和 V692/V695 的 RouteOpt hard-case 路径一致，说明 root-score 子树保护没有误伤 score-missing hard context。

### seed61614

结果：

- status：`OPTIMAL`
- solver time：`342.822163s`
- nodes：`7`
- branch count：`3`
- fathom：`bound=4`
- completion-bound retry：`7`

Branch path：

| depth | selected pair | gate evidence |
|---:|---|---|
| 0 | `[4,19]` | `preserve_score_gate_winner=True` |
| 1 | `[1,2]` | `root_score_gate_subtree_depth_exceeds_max`, root `[4,19]`, score `0.74` |
| 2 | `[1,4]` | `root_score_gate_subtree_depth_exceeds_max`, root `[4,19]`, score `0.74` |

这恢复了 V545 的好路径前缀 `[4,19] -> [1,2] -> [1,4]`。V694 虽然保护了 root，但 depth1/depth2 仍被 RouteOpt 改写，因此慢到 `399s`；V698 把这一点修正了。

## 实现状态

新增 opt-in 配置：

```text
journey_branch_candidate_phased_testing_root_score_gate_subtree_max_depth
```

语义：

- 仅在 `routeopt_bkf_staged` 下生效；
- 当 `branch_depth > root_score_gate_subtree_max_depth` 时，读取当前节点第一条 branch constraint 作为 root pair；
- 用 root context 查询 `branch_score_map`；
- 若 root pair 通过 `branch_score_selection_gate`，则该子树回退到 base priority，不执行 RouteOpt Phase 1/2 改写；
- 若 root score 缺失、低于阈值或 source 不合法，则继续 RouteOpt/BKF phased testing。

exact-safe 边界：

- 该 gate 只改变 branch ordering；
- 不提供 official bound；
- 不提供 certificate；
- 不剪枝；
- child 仍靠 exact pricing closure。

日志证据：

- `journey_branch_candidates.priority_top/top` 记录：
  - `phased_testing_depth_gate_reason`
  - `phased_testing_root_score_gate_subtree_pair`
  - `phased_testing_root_score_gate_subtree_score`
  - `phased_testing_root_score_gate_subtree_score_source`
- `journey_branch` selection metadata 记录同类字段。

## 测试

已通过：

```text
PYTHONDONTWRITEBYTECODE=1 python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py

PYTHONDONTWRITEBYTECODE=1 python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase0_filters_high_score_candidate \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase1_logs_child_lp_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase2_logs_heuristic_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_diverse_pool_adds_balance_frontier
```

## 当前判断

V698 是目前 RouteOpt/BKF hybrid 方向里最干净的正信号：

1. seed61103 保留 `EXTERNAL -> OPTIMAL` 的 RouteOpt 收益。
2. seed61614 避免 full-open RouteOpt 回归，回到 V545 级别。
3. gate 的行为可解释、可审计，并保持 exact-safe。

下一步不应直接跑 full-open full60，而应跑：

1. V698 配置的 Apollo greedy-anchor first8/first12；
2. 若 first12 不退化，再跑 full60；
3. 并行继续做 root proof / cuts / formulation，因为 seed61205 这类 root 未进 branch 的实例仍不是 branch controller 能解决的。

