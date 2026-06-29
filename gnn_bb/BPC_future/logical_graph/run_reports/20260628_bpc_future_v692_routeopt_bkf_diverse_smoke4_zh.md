# V692 RouteOpt/BKF Dynamic-K Diverse Pool：Random-TW 5/10/20 Smoke4

## 结论

V692 将 `routeopt_bkf_staged + dynamic-K diverse pool` 从单实例验证扩展到 fixed random-TW smoke：

- 5-task smoke4：`4/4 OPTIMAL`
- 10-task smoke4：`4/4 OPTIMAL`
- 20-task smoke4：`2/4 OPTIMAL`，`1 TIME_LIMIT`，`1 EXTERNAL_TIME_LIMIT`

20-task 的关键正信号：

- seed61000：V545 `342.221005s OPTIMAL` → V692 `310.997477s OPTIMAL`
- seed61103：V545 `EXTERNAL_TIME_LIMIT` → V692 `422.843567s OPTIMAL`

关键负信号：

- seed61205：仍是 root-level `TIME_LIMIT`，没有 branch event，说明 RouteOpt/BKF branch testing 无法处理还没进入 branch 的 root proof/CG 问题。
- seed61308：仍 `EXTERNAL_TIME_LIMIT`，但 V692 记录到 exact-safe gap：`0.046097`，best primal `510.712329`，best dual `487.169894`。

因此当前判断是：RouteOpt/BKF staged testing 是有效主线，已经能把部分 hard20 从 timeout 推到 OPTIMAL；但要达成“所有 20 规模 600s 内最优”，还必须并行处理 root CG/proof 和 formulation/cuts。

## 配置

共同配置：

```text
journey_branch_candidate_priority=routeopt_bkf_staged
journey_branch_candidate_phased_testing_enabled=true
journey_branch_candidate_phased_testing_base_priority=fractionality
journey_branch_candidate_phased_testing_phase1_lp_enabled=true
journey_branch_candidate_phased_testing_phase2_heuristic_enabled=true
journey_branch_candidate_phased_testing_phase2_time_limit=0.04
journey_branch_candidate_phased_testing_phase2_max_returned_journeys=1
journey_branch_candidate_phased_testing_dynamic_k_enabled=true
journey_branch_candidate_phased_testing_dynamic_k_min_candidates=1
journey_branch_candidate_phased_testing_dynamic_k_max_candidates=4
journey_branch_candidate_phased_testing_dynamic_k_sqrt_factor=1.0
journey_branch_candidate_phased_testing_dynamic_k_diverse_pool_enabled=true
journey_branch_candidate_phased_testing_dynamic_k_diverse_pool_extra_candidates=8
journey_branch_candidate_log_top_n=50
```

未启用：

- admission scheduler
- new cuts
- new incumbent heuristic
- Tier 1 refinement

exact-safe 边界不变：Phase 1/2 只改变 branch candidate ordering，不提供 official bound 或 certificate。

## 运行产物

5-task：

`BPC_future/results/20260628_v692_routeopt_bkf_diverse_smoke4_tasks5_batch1/results.csv`

10-task：

`BPC_future/results/20260628_v692_routeopt_bkf_diverse_smoke4_tasks10/results.csv`

20-task：

`BPC_future/results/20260628_v692_routeopt_bkf_diverse_smoke4_tasks20/results.csv`

注：最初尝试的 `20260628_v691_routeopt_bkf_diverse_smoke4_tasks5` 使用 `max-workers=4 + force-child-exit-after-run`，4 个 5-task 子进程长时间处于加载/I/O 等待且没有 JSONL 输出，已废弃。单实例前台复现同配置 `0.236442s OPTIMAL`，后续 5-task smoke 使用去掉 `force-exit` 的 batch1 结果。

## 5-task Smoke4

| instance | V692 status | V692 wall | baseline status | baseline wall |
|---|---:|---:|---:|---:|
| seed46001 | OPTIMAL | `3.665660` | OPTIMAL | `71.463795` |
| seed46105 | OPTIMAL | `3.699081` | OPTIMAL | `3.997843` |
| seed46207 | OPTIMAL | `3.647664` | OPTIMAL | `3.959274` |
| seed46311 | OPTIMAL | `3.690641` | OPTIMAL | `3.883802` |

汇总：

- OPTIMAL：`4/4`
- capped mean：`3.675762s`

## 10-task Smoke4

| instance | V692 status | V692 wall | baseline status | baseline wall |
|---|---:|---:|---:|---:|
| seed51001 | OPTIMAL | `3.774506` | OPTIMAL | `3.904791` |
| seed51106 | OPTIMAL | `3.502970` | OPTIMAL | `3.689801` |
| seed51209 | OPTIMAL | `3.825200` | OPTIMAL | `3.959150` |
| seed51317 | OPTIMAL | `7.047002` | OPTIMAL | `9.083393` |

汇总：

- OPTIMAL：`4/4`
- capped mean：`4.537420s`

## 20-task Smoke4

| instance | V692 status | V692 wall | V692 gap | V545 status | V545 wall | early baseline status |
|---|---:|---:|---:|---:|---:|---:|
| seed61000 | OPTIMAL | `310.997477` | `0.0` | OPTIMAL | `342.221005` | EXTERNAL_TIME_LIMIT |
| seed61103 | OPTIMAL | `422.843567` | `0.0` | EXTERNAL_TIME_LIMIT | `600.021953` | EXTERNAL_TIME_LIMIT |
| seed61205 | TIME_LIMIT | `341.369882` | unavailable | TIME_LIMIT | `340.774743` | TIME_LIMIT |
| seed61308 | EXTERNAL_TIME_LIMIT | `600.029541` | `0.046097` | EXTERNAL_TIME_LIMIT | `600.033104` | EXTERNAL_TIME_LIMIT |

汇总：

- OPTIMAL：`2/4`
- capped mean：`418.802731s`
- OPTIMAL-only mean：`366.920522s`
- V545 对比：
  - seed61000：加速约 `31.22s`
  - seed61103：`EXTERNAL_TIME_LIMIT -> OPTIMAL`
  - seed61205：基本无变化
  - seed61308：仍失败，但现在有可用 exact-safe gap

## 20-task Phase Testing 诊断

### seed61000

- status：`OPTIMAL`
- selected root pair：`[12,17]`
- branch count：`1`
- Phase 1：`ok=12`，`dynamic_k_excluded=38`
- Phase 2：`ok=8`，`dynamic_k_excluded=42`
- completion-bound retry：`6`
- fathom：`bound=2`

选中 root pair 的阶段指标：

| pair | min child LP gain | child gain product |
|---|---:|---:|
| `[12,17]` | `4.310404667` | `67.078448636` |

### seed61103

- status：`OPTIMAL`
- branch count：`6`
- Phase 1：`ok=69`，`dynamic_k_excluded=144`
- Phase 2：`ok=52`，`dynamic_k_excluded=161`
- completion-bound retry：`14`
- fathom：`bound=7`

前几个 selected pair：

| depth | pair | min child LP gain | child gain product |
|---:|---|---:|---:|
| 0 | `[12,13]` | `3.831199417` | `67.309559710` |
| 1 | `[3,17]` | `20.756855300` | `543.138837321` |
| 1 | `[1,2]` | `0.258784500` | `0.107202644` |
| 2 | `[3,8]` | `4.014694167` | `105.317181678` |
| 2 | `[6,8]` | `11.907472750` | `154.280876431` |

这是 V692 最重要的正例：当前 best V545 没闭环，V692 在 422.84 秒闭环。

### seed61205

- status：`TIME_LIMIT`
- branch count：`0`
- incumbent：`642.291219`
- exact gap unavailable：`no_exact_dual_bound`

解释：该实例没有进入 branch，因此 RouteOpt/BKF branch testing 没有机会发挥作用。后续要看 root CG/final proof、completion-bound certificate、cuts/formulation。

### seed61308

- status：`EXTERNAL_TIME_LIMIT`
- branch count：`3`
- best primal：`510.712329`
- best dual：`487.169894`
- exact-safe gap：`0.046097`
- Phase 1：`ok=34`，`dynamic_k_excluded=116`
- Phase 2：`ok=28`，`dynamic_k_excluded=122`
- completion-bound retry：`8`

前几个 selected pair：

| depth | pair | min child LP gain | child gain product |
|---:|---|---:|---:|
| 0 | `[6,12]` | `3.893887300` | `95.709380404` |
| 1 | `[3,8]` | `8.982674451` | `93.349206358` |
| 1 | `[3,9]` | `1.556960833` | `28.348545499` |

解释：它已经进入 branch tree，但 600 秒仍不能闭环。这类实例需要继续看 depth 2+ pair、retry cost、以及 LP/formulation bound。

## 判断

V692 支持继续推进 RouteOpt/BKF staged controller：

1. 小规模 smoke 未观察到退化。
2. 20-task 有 `EXTERNAL_TIME_LIMIT -> OPTIMAL` 的强正信号。
3. Phase 1 的双 child LP gain product 对 seed61000/61103 的选择有实际解释力。

但 V692 同时说明：

1. 只优化 branch 不够。seed61205 没进入 branch，branch controller 没有作用点。
2. seed61308 即使进了 branch 仍失败，说明后续 child proof cost、retry 和 formulation bound 仍是主瓶颈。
3. full60 前应保留 exact-safe gap 输出，否则 timeout 的进展无法评估。

## 下一步

1. 跑 20-task smoke12 或 first12，继续验证 `EXTERNAL_TIME_LIMIT -> OPTIMAL` 是否稳定。
2. 将 V692 的 Phase 1/2 字段加入 branch action dataset：
   - `phase1_min_child_lp_gain`
   - `phase1_child_lp_gain_product`
   - `phase1_child_width_balance`
   - `phase1_wall_time`
   - `phase2_negative_child_count`
   - `phase2_best_reduced_cost`
   - `phase2_wall_time`
3. 对 seed61205 做 root failure typing：为什么没有 branch，卡在 root CG 还是 final proof。
4. 对 seed61308 做 depth 2+ replay 和 completion-bound retry profile。
5. 并行启动 pricing-compatible cuts/formulation 线，解决 best dual 不动和 root proof 类问题。

## 后续实现更新

已完成第 2 项：

- `BRANCH_ACTION_CONTEXT_FEATURE_SCHEMA` 已扩展 Phase 1/2 字段；
- `build_gat_branch_action_sanity_dataset.py` 已从 `alternative_raw_row` 读取这些字段；
- `export_gat_branch_action_score_map.py` 已同步用候选日志中的 Phase 1/2 字段构造 context feature；
- 相关 dataset/training/export 测试通过。

这一步只影响离线学习样本和 score-map 导出特征，不改变 solver 的 exact bound / certificate 逻辑。
