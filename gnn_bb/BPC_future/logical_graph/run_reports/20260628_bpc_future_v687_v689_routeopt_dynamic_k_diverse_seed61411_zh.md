# V687-V689 RouteOpt/BKF Dynamic-K Diverse Pool：seed61411 严格正信号

## 结论

RouteOpt/BKF 式 phased branch testing 在 seed61411 上出现了一个严格正信号：

- 非多样性 dynamic-K：90 秒预算内 `TIME_LIMIT`，gap `0.013779`。
- 多样性 dynamic-K：90 秒预算内 `OPTIMAL`，wall `48.680485s`，gap `0.0`。

这不是改证书边界得到的结果。分支仍然只改变 Ryan-Foster pair 的选择；child 最终仍靠 RMP/true pricing/completion-bound 证明闭环。

## 输入实例

`BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json`

这是 random-TW 20 规模 hard instance。此前 V680 forced replay 已证明：

| root pair | status | wall |
|---|---:|---:|
| `[2,10]` | OPTIMAL | `345.18s` |
| `[3,10]` | OPTIMAL | `50.19s` |

因此 `[3,10]` 是该 state 下的严格更优 root pair。

## V687：调用错误修复

V687 先暴露出实现问题：

```text
TypeError: _log_journey_branch_candidates() got an unexpected keyword argument 'solver_config'
```

原因是 formal branch 处调用 `_log_journey_branch_candidates(...)` 时传了不存在的 `solver_config` 形参。已在 `BPC_future/solver/journey_driver.py` 中移除两处错误参数，保留内部 `_ordered_journey_branch_candidates_for_priority(... solver_config=config)`。

验证：

```text
PYTHONDONTWRITEBYTECODE=1 python -m py_compile BPC_future/solver/journey_driver.py BPC_future/tests/test_bpc_future.py
```

通过。

## V688：普通 dynamic-K 失败原因

配置：

- priority：`routeopt_bkf_staged`
- Phase 1：child LP testing ON
- Phase 2：heuristic probe ON
- dynamic-K：ON
- `max_candidates=4`
- diverse pool：OFF

结果：

| status | wall | primal | dual | gap | nodes | columns |
|---|---:|---:|---:|---:|---:|---:|
| TIME_LIMIT | `89.485807s` | `641.659225` | `632.817928` | `0.013779` | 9 | 412 |

关键诊断：

- root candidate count：`35`
- root selected pair：`[2,10]`
- `[3,10]` 在原始/fractionality order 中 rank 为 `8`
- dynamic-K 只测前 `4` 个，因此 `[3,10]` 被 `dynamic_k_excluded`

这说明直接借鉴 BKF 的“少测候选”不够；如果候选池只来自单一排序，真正好的 pair 会被排除在测试之外。

## Phase 2 预算修正

V688 还暴露出 Phase 2 的预算分配问题：每个 pair 的第一个 child 可能吃完整个 probe budget，第二个 child 变成 `NO_TIME`。

修正后：

- `phase2_time_limit` 仍表示 pair 总预算；
- 内部按 child 均分预算；
- 每个 child 有独立 `absolute_deadline`；
- 日志记录每个 child 的 `budget`。

修正后的 V688 统计：

- Phase 2 reasons：`ok=15`，`incomplete_heuristic_probe=1`，`dynamic_k_excluded=112`
- 绝大多数被测试 pair 的两个 child 都不再是 `NO_TIME`

## V689：多样性 dynamic-K 成功

新增配置：

```text
journey_branch_candidate_phased_testing_dynamic_k_diverse_pool_enabled=True
journey_branch_candidate_phased_testing_dynamic_k_diverse_pool_extra_candidates=8
```

diverse pool 会在原始前 K 外，额外加入 cheap balance-frontier 候选，排序依据包括：

- `pool_balance_gap`
- `pool_max_child_width`
- `fractionality`
- task ids 稳定 tie-break

结果：

| status | wall | primal | dual | gap | nodes | columns |
|---|---:|---:|---:|---:|---:|---:|
| OPTIMAL | `48.680485s` | `641.659225` | `641.659225` | `0.0` | 3 | 401 |

V689 root branch：

| selected pair | Phase 1 min gain | Phase 1 gain product | Phase 2 negative child count |
|---|---:|---:|---:|
| `[3,10]` | `8.841297` | `93.393926856` | 0 |

对比 `[2,10]`：

| pair | Phase 1 min gain | Phase 1 gain product | child width balance |
|---|---:|---:|---:|
| `[3,10]` | `8.841297` | `93.393926856` | 69 |
| `[2,10]` | `8.841297` | `79.511163163` | 47 |

两者 min child LP gain 一样，但 `[3,10]` 的双侧 gain product 更好，最终闭环时间接近此前 forced root replay 的 `50.19s`。

## 当前判断

这次结果支持三个判断：

1. RouteOpt/BKF 的核心启发是正确的：branch pair 需要 phased testing，而不是只靠静态 score map。
2. dynamic-K 必须保持候选多样性；单一排序 top-K 会漏掉强 pair。
3. branch 标签应强化双 child 均衡收益，至少包含：
   - `min(child_lb_gain)`
   - `child_gain_product`
   - `child_width_balance`
   - `fathom_gain`
   - `completion_bound_retry_delta`
   - `gap_improvement`

## 风险

这个结果还不是 full60 结论。它只证明 seed61411 上 `routeopt_bkf_staged + diverse dynamic-K` 找到了正确 root pair，并在 90 秒内闭环。

下一步必须验证：

- 5/10 是否无退化；
- 20 full60 是否提升 OPTIMAL 数和 capped mean；
- diverse extra candidates 增加的 probe CPU 是否在多数实例上值得；
- depth 1/2 是否也需要同样的 diverse pool；
- Phase 2 heuristic probe 的 incomplete 状态是否足够区分 pair。

## 下一步

1. 对 seed61311 等 V631/V636 hard case 跑同一 V689 配置，检查是否也能改善。
2. 跑 12-instance smoke，再进入 20 full60。
3. 把 Phase 1/2 字段纳入 branch action dataset：
   - `phase1_min_child_lp_gain`
   - `phase1_child_lp_gain_product`
   - `phase1_child_width_balance`
   - `phase2_negative_child_count`
   - `phase2_child_status`
   - `phase2_wall_time`
4. 后续 score map 不再只学习 wall-time gain，应学习 `gap/fathom/retry/proof-cost` 多目标 ranking。
