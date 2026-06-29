# V700 Dynamic SRC Depth2 Hard2 诊断

## 结论

V700 在 V699 `routeopt_bkf_staged + score-protected root-subtree gate` 基础上，额外打开 journey dynamic subset-row cuts：

```text
journey_dynamic_subset_row_cuts_enabled=true
journey_dynamic_subset_row_max_depth=2
journey_dynamic_subset_row_max_rounds=3
journey_dynamic_subset_row_cut_budget=600
journey_dynamic_subset_row_max_added=40
journey_dynamic_subset_row_max_subset_size=6
```

验证实例：

- seed61308
- seed61512

结果：两者仍为 `EXTERNAL_TIME_LIMIT`，但 gap 下降。

| instance | V699 status | V699 gap | V699 primal | V699 dual | V700 status | V700 gap | V700 primal | V700 dual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| seed61308 | EXTERNAL | `0.046097` | `510.712329` | `487.169894` | EXTERNAL | `0.033277` | `503.939606` | `487.169894` |
| seed61512 | EXTERNAL | `0.078552` | `557.840356` | `514.020685` | EXTERNAL | `0.063370` | `548.798049` | `514.020685` |

关键判断：

- dynamic SRC 能被 branch-depth 触发，代码路径有效。
- gap 下降主要来自更好的 incumbent/primal，不是 best dual 提升。
- 两个实例的 best dual 完全没变，说明当前 SRC 不是解决 hard proof tail 的充分 formulation 强化。
- 不能把现有 dynamic SRC 全局打开当作主线成功；它更适合后续作为受控 cut gate / cut feature 诊断。

## 代码改动

新增 opt-in 深度门控：

```text
journey_dynamic_subset_row_max_depth
```

默认值为 `0`，因此默认行为保持原状。显式设置为 `1/2` 后，branch node 才允许分离 dynamic SRC。

exact-safe 边界：

- SRC 仍是 master 中的有效 cut。
- pricing reduced-cost 已走现有 cut dual 支持路径。
- 不作为 official bound、certificate 或剪枝依据。
- old lower bound 仍可作为合法 inherited lower bound。

## 事件证据

### seed61308

V699：

```text
path = [2,6] -> [3,8] -> [3,9]
journey_cut_added = 0
fathom = 0
last node: depth 2, rmp = 494.548321, incumbent = 510.712329
```

V700：

```text
path = [6,12] -> [6,8]
journey_cut_added = 45
cuts_by_depth = {1: 45}
fathom = 0
last node: depth 1, rmp = 500.201931, incumbent = 503.939606
```

说明：depth1 SRC 明显改变了树和局部 RMP，但没有产出全局 dual bound 提升，也没有完成 fathom。

### seed61512

V699：

```text
path = [12,19] -> [15,19] -> [12,15] -> [12,16] -> [1,10] -> [1,18] -> [7,14] -> [12,19]
journey_cut_added = 0
fathom = 0
last node: depth 4, rmp = 544.377134, incumbent = 557.840356
```

V700：

```text
path = [12,19] -> [7,15] -> [12,16] -> [12,15] -> [7,19] -> [12,19]
journey_cut_added = 13
cuts_by_depth = {0: 6, 1: 5, 2: 2}
fathom = 0
last node: depth 3, rmp = 562.764665, incumbent = 548.798049
```

说明：V700 找到更好 incumbent，某些节点 LP 已经高于 incumbent，但最终仍没有全局闭环。这里的问题更像是 proof/certificate 和全局 node closure 不够，而不是单纯 pair 排序。

## 对 RouteOpt 启发的更新

RouteOpt-style cuts/formulation 的方向是对的，但不能理解成“打开 subset-row 就够了”。

当前证据显示：

1. 分支控制器已经能改变树，并且 V699 比 V545/full-open 更稳。
2. dynamic SRC 可以进一步改变树和改善 incumbent。
3. 但是 best dual 不动，说明还缺少更强的 pricing-compatible cut family、route-aware bound 或 child certificate 能力。
4. 后续不应继续盲目增加 SRC 数量，否则可能只增加 RMP/CG 成本。

## 下一步

优先级建议：

1. 给 dynamic SRC 加 gate，而不是默认全开：
   - 只在 `z_RMP < UB` 且 branch tree 已经展开、gap 仍明显时试。
   - 限制每节点新增 cut 数。
   - 记录 cut 后 `rmp_delta`、`incumbent_delta`、`dual_bound_delta`、`fathom_delta`。
2. 研究更强 cut/formulation：
   - route-aware subset-row；
   - capacity/route coupling cut；
   - pricing-compatible RCC 类 cut；
   - 对 child 的 safe corrected bound / certificate 加强。
3. branch 标签加入 cut 后效果字段：
   - `cut_added_by_depth`
   - `cut_rmp_gain`
   - `best_primal_delta`
   - `best_dual_delta`
   - `fathom_after_cut`
4. 对 seed61512 这种“child RMP 已超过 incumbent 但仍未闭环”的节点，单独查 final certificate / node pruning 为什么没完成。

## V701 Pre-Exact Handoff 追加验证

V701 在 V700 的 seed61512 配置上额外打开：

```text
journey_certificate_completion_bound_pre_exact_handoff_enabled=true
journey_certificate_completion_bound_pre_exact_handoff_min_flat_rounds=0
journey_certificate_completion_bound_pre_exact_handoff_disable_on_branch_depth_gt=3
```

结果：

| version | status | wall | gap | best primal | best dual | pre-exact handoff |
|---|---:|---:|---:|---:|---:|---:|
| V699 | EXTERNAL | `600.024442` | `0.078552` | `557.840356` | `514.020685` | 0 |
| V700 | EXTERNAL | `600.033314` | `0.063370` | `548.798049` | `514.020685` | 0 |
| V701 | EXTERNAL | `600.022940` | `0.063370` | `548.798049` | `514.020685` | 1 |

V701 的 handoff 事件：

```text
node_id=7
depth=3
cg_iter=1
remaining=138.173704
```

但它没有带来 fathom。反而 node 8 到 `599.109119s` 才开始第一轮 RMP，而 V700 在 node 8 已经跑到 cg_iter 3。

因此，seed61512 的当前瓶颈不是“pre-exact handoff 没开”这一单点。更准确地说：

- dynamic SRC 改善了 incumbent/gap；
- pre-exact handoff 能触发；
- 但 completion-bound/final-judge 证书成本仍然太高，或者没有命中真正能剪掉全局树的节点；
- best dual 仍不动，最终 full proof 没闭环。

后续不能把 pre-exact handoff 全局打开作为主线。它需要更强 gate：

- 只在 `rmp_objective >= incumbent` 且 `fathom_possible_if_rc_zero=true` 的节点触发；
- 需要预计 final judge 能在剩余时间内完成；
- 不应在低收益节点消耗 100s 级预算。

## 测试

通过：

```text
PYTHONDONTWRITEBYTECODE=1 python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py

PYTHONDONTWRITEBYTECODE=1 python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_dynamic_subset_row_cuts_are_branch_depth_opt_in \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_rmp_reduced_cost_matches_manual_formula_with_cuts \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_direct_journey_label_pricing_keeps_cut_dual_reward_candidate \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_profile_cut_penalty_pruning_is_sign_guarded

PYTHONDONTWRITEBYTECODE=1 python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase0_filters_high_score_candidate \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase1_logs_child_lp_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase2_logs_heuristic_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_diverse_pool_adds_balance_frontier
```

V700 运行产物：

```text
BPC_future/results/20260628_v700_routeopt_bkf_dynamic_src_depth2_seed61308_61512/results.csv
```

V701 运行产物：

```text
BPC_future/results/20260628_v701_dynamic_src_preexact_seed61512/results.csv
```

## V702 Phase1 Child Ordering 追加验证

V702 在 V700 的 seed61512 配置上额外打开：

```text
journey_child_priority_mode=phase1_lp_objective
```

它使用 branch phased testing 中已经计算出的两个 child LP objective 来决定 child 入队顺序。这个排序只影响搜索顺序，不提供 official bound、certificate 或剪枝依据。

结果：

| version | status | wall | gap | best primal | best dual | branch | fathom | completion retry |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V699 | EXTERNAL | `600.024442` | `0.078552` | `557.840356` | `514.020685` | 8 | 0 | 11 |
| V700 | EXTERNAL | `600.033314` | `0.063370` | `548.798049` | `514.020685` | 6 | 0 | 12 |
| V701 | EXTERNAL | `600.022940` | `0.063370` | `548.798049` | `514.020685` | 6 | 0 | 12 |
| V702 | EXTERNAL | `600.022738` | `0.063370` | `548.798049` | `514.020685` | 6 | 1 | 12 |

V702 的关键事件：

```text
root selected pair = [12,19]
same child objective = 523.219101333
separate child objective = 534.366347
queued first = RF(1,8)=separate_vehicle
priority_mode = phase1_lp_objective
```

V702 与 V700 的主要差异：

- V702 确实按照 Phase1 LP objective 把更高 LP 的 child 放前面。
- V702 多得到 1 次 `journey_fathom`，说明这个排序信号有局部价值。
- 但 status/gap/best primal/best dual 都没有改善，仍然没有完成全局证明。
- 这说明 child LP objective 只能作为一个低成本特征，不能单独作为完整 child ordering 策略。

对 Branch Score 主线的更新判断：

1. `phase1_lp_objective` 应进入 branch/child replay 数据集，作为 child proof 特征。
2. child ordering 不能只最大化单侧 LP objective；更应该学：
   - 两侧 child LB gain 的最小值；
   - 两侧 gain product；
   - child width balance；
   - completion-bound retry 次数；
   - child time-to-certificate；
   - fathom probability。
3. seed61512 这种 case 的瓶颈不是“先跑哪个 child”这一点，而是后续 child certificate 成本和 global closure 仍然太高。

V702 运行产物：

```text
BPC_future/results/20260628_v702_phase1_child_order_seed61512/results.csv
```
