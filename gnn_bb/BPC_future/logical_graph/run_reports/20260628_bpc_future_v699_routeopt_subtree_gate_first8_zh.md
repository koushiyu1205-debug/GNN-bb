# V699 RouteOpt/BKF Root-Subtree Gate First8 Smoke

## 结论

V699 将 V698 的 `score-protected + root-score subtree gate` 扩展到 Apollo greedy-anchor random-TW 20-scale first8。

结果：

| version | rows | OPTIMAL | TIME_LIMIT | EXTERNAL | capped mean | <=200s OPTIMAL |
|---|---:|---:|---:|---:|---:|---:|
| V545 / V543 score overlay | 8 | 3 | 1 | 4 | `459.132413s` | 0 |
| V692/V693 RouteOpt full-open | 8 | 4 | 1 | 3 | `451.145286s` | 1 |
| V699 subtree gate | 8 | 4 | 1 | 3 | `424.457383s` | 1 |

V699 的正面结果：

- 保留 seed61103 的 RouteOpt hard-case 正信号：V545 `EXTERNAL` → V699 `421.554874s OPTIMAL`。
- 保住 seed61614 的 V545 好路径：V693 full-open `589.554913s` → V699 `342.712624s`。
- 保留 seed61716 的明显加速：V545 `245.683781s` → V699 `144.175356s`。
- first8 capped mean 比 V545 和 full-open RouteOpt 都更好。

V699 的负面/未解决结果：

- seed61000 从 full-open RouteOpt 的 `310.997477s` 回到 V545 级别 `345.483486s`，说明保护 score-covered root 会牺牲一部分 full-open 探索收益。
- seed61308、seed61410、seed61512 仍 `EXTERNAL_TIME_LIMIT`。
- seed61205 仍 `TIME_LIMIT` 且 branch count 为 0，继续证明它属于 root proof / no-exact-dual-bound 问题，不是 branch controller 能解决。

因此，V699 是比 full-open RouteOpt 更稳的 hybrid，但还没有达到 “20-scale all OPTIMAL within 600s”。

## 配置

核心配置同 V698：

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

未启用：

- admission scheduler
- new cuts
- new incumbent heuristic
- Tier 1 refinement

exact-safe 边界不变：branch testing 和 gate 只改变分支排序，不提供 official bound、certificate 或剪枝依据。

## 运行产物

```text
BPC_future/results/20260628_v699_routeopt_score_protected_root_subtree_gate_first8_tasks20/results.csv
```

## Instance 结果

| instance | status | wall | gap | branch count | fathom | retry | path prefix |
|---|---:|---:|---:|---:|---:|---:|---|
| seed61000 | OPTIMAL | `345.483486` | `0.0` | 2 | 3 | 5 | `[12,20] -> [2,10]` |
| seed61103 | OPTIMAL | `421.554874` | `0.0` | 6 | 7 | 14 | `[12,13] -> [3,17] -> [1,2] -> [3,8] -> [6,8] -> [1,18]` |
| seed61205 | TIME_LIMIT | `341.732726` | unavailable | 0 | 0 | 2 | root only |
| seed61308 | EXTERNAL | `600.020097` | `0.046097` | 3 | 0 | 8 | `[2,6] -> [3,8] -> [3,9]` |
| seed61410 | EXTERNAL | `600.022855` | `0.066532` | 7 | 1 | 12 | `[15,16] -> [1,4] -> [1,9] -> [1,17] -> [1,19] -> [5,15] -> [3,6]` |
| seed61512 | EXTERNAL | `600.024442` | `0.078552` | 8 | 0 | 11 | `[12,19] -> [15,19] -> [12,15] -> [12,16] -> [1,10] -> [1,18] -> [7,14] -> [12,19]` |
| seed61614 | OPTIMAL | `342.712624` | `0.0` | 3 | 4 | 7 | `[4,19] -> [1,2] -> [1,4]` |
| seed61716 | OPTIMAL | `144.175356` | `0.0` | 1 | 2 | 3 | `[2,16]` |

## 关键诊断

### 1. Hybrid gate 有效

seed61614 是最关键的回归防护样本：

- V693 full-open RouteOpt：`[6,18] -> ...`，`589.554913s`；
- V694 root score-protected：`[4,19] -> [6,18] -> [4,10]`，约 `409s`；
- V699 root-subtree gate：`[4,19] -> [1,2] -> [1,4]`，`342.712624s`。

这说明只保护 root 不够，必须保护高置信 root score 子树里的深层 fallback path。

### 2. RouteOpt 仍应处理 score-missing hard context

seed61103 root 没有被 score gate 保护，继续走 RouteOpt/BKF 路径：

```text
[12,13] -> [3,17] -> [1,2] -> [3,8] -> [6,8] -> [1,18]
```

结果 `421.554874s OPTIMAL`，复现 V692/V695 的 `EXTERNAL -> OPTIMAL` 收益。

### 3. branch controller 不能解决 root proof 类

seed61205：

- branch count：0
- fathom：0
- gap unavailable：`no_exact_dual_bound`

这类实例需要 root CG/proof、completion-bound、cuts/formulation，而不是继续调 branch score。

### 4. branch tree 宽但下界仍不够

seed61410/61512 已进入多层分支，但 600s 内仍不能闭环：

- seed61410：7 branches，1 fathom，gap `0.066532`
- seed61512：8 branches，0 fathom，gap `0.078552`

这说明 RouteOpt/BKF 能组织分支树，但 LP/formulation 下界和 child proof cost 仍是瓶颈。继续增加 branch testing 深度大概率只会增加证明成本。

## Failure Typing

| instance | failure type | evidence | recommended next action |
|---|---|---|---|
| seed61205 | `ROOT_PROOF_NO_EXACT_DUAL` | branch `0`, fathom `0`, gap unavailable / `no_exact_dual_bound` | root CG/proof、completion-bound、pricing-compatible cuts |
| seed61308 | `BRANCH_TREE_WIDE_LP_GAP_NO_FATHOM` | branch `3`, fathom `0`, gap `0.046097` | cuts/formulation 或更强 child bound；仅换 branch pair 不够 |
| seed61410 | `BRANCH_TREE_PROOF_TOO_SLOW_WITH_GAP` | branch `7`, fathom `1`, retry `12`, gap `0.066532` | child proof cost / retry gate / cuts 并行推进 |
| seed61512 | `BRANCH_TREE_WIDE_LP_GAP_NO_FATHOM` | branch `8`, fathom `0`, retry `11`, gap `0.078552` | cuts/formulation 和 child ordering；避免继续盲目加深 branch testing |

这个分型很重要：first8 的未解实例不是同一种失败。seed61205 还没进入 branch，branch controller 没作用点；seed61308/61410/61512 已经进 branch，但下界和证明成本不够，说明需要 stronger formulation / cuts / child proof，而不是继续扩大 top-k 或无条件加深 RouteOpt。

## 测试

本轮相关窄测通过：

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase0_filters_high_score_candidate \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase1_logs_child_lp_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_staged_phase2_logs_heuristic_probe \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_routeopt_bkf_dynamic_k_diverse_pool_adds_balance_frontier
```

## 当前判断

V699 可以作为下一轮 full60 候选配置，但不能单独完成最终目标。

推荐下一步：

1. 跑 V699 full60，确认 capped mean / OPTIMAL 数是否优于 V545 和 full-open RouteOpt。
2. 对 seed61308/61410/61512 建立 failure typing：
   - `z_RMP < UB`？
   - child proof 太慢？
   - final-probe/retry 太重？
   - branch tree 太宽？
3. 并行启动 pricing-compatible cuts/formulation，因为 first8 里未解决的 3 个 EXTERNAL 都有稳定 gap，说明光靠 branch path 很难把节点推进到可剪枝区间。
4. 对 seed61000 研究“高置信 score-covered 但 full-open 更快”的条件，可能需要将 root-subtree gate 从硬门改成 risk-aware gate，而不是所有 root score pass 都保护。
