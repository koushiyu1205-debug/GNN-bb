# B4.1 V4 Partition Proof Speed Audit

## Boundary

- official objective: `normalized_cost + normalized_risk + 0.4 * normalized_weighted_completion`
- makespan: metric only
- 本报告只审计 B4V4 final judge proof-tail 的 partition/region proof 速度。
- partition rows 仍是 diagnostic/ledger evidence；单个 k 或部分 k 覆盖不能 claim full-space certificate。

## Code Changes Audited

- compact pricing 增加 slot-task sequence capacity / matching capacity 上界。
- compact pricing 增加 gated task-slot pair-conflict capacity 上界。
- 新增 `scripts/merge_lunar_ice_b4_1_partition_probes.py`，用于合并 low-time + targeted partition rows，避免重复 full rerun。
- 追加审计 `V4_current_quad_time_window_infeasible` 与 `V4_current_dual_task_slot_lb_gate`。二者均保持 diagnostic/opt-in，不作为默认 final judge。
- 新增 opt-in incremental route-template negative probe：
  - 修复 partial direct-label seed 合并层的候选大小过滤：multi-sortie seed task set 上限应为 `max_direct_tasks`，不是单 sortie 的 `max_tasks_per_trip`。
  - 新增 `price_direct_journey_columns_incremental`，按当前 label 的真实 start time 动态生成下一次 sortie，而不是先枚举 start=0 的完整 route-template 全集。
  - 新增 `scripts/run_lunar_ice_route_template_negative_probe.py`，从 active pool task-set seeds 在 true dual 下找负列。
  - 该路径只用于 exact-safe negative discovery，不输出 no-negative certificate。

## Main Evidence

旧 B4V4 30-scale instance001 tree closure baseline:

```text
549.355622s
```

当前 partition proof 证据：

| k | wall_s | proven | incomplete | negative |
|---:|---:|---:|---:|---:|
| 9 | 75.391216 | 9 | 0 | 0 |
| 10 | 78.905116 | 10 | 0 | 0 |
| 11 | 74.037252 | 11 | 0 | 0 |
| 12 | 67.284066 | 12 | 0 | 0 |
| 13 | 46.735653 | 13 | 0 | 0 |
| 14 | 38.493005 | 14 | 0 | 0 |
| 15 | 31.006723 | 15 | 0 | 0 |
| 16 | 22.797570 | 16 | 0 | 0 |
| 17 | 11.485600 | 17 | 0 | 0 |
| 18 | 11.846798 | 18 | 0 | 0 |
| 19 | 11.132216 | 19 | 0 | 0 |
| 20 | 11.457211 | 20 | 0 | 0 |
| 21 | 11.343840 | 21 | 0 | 0 |
| 22 | 11.433314 | 22 | 0 | 0 |
| 23 | 11.429906 | 23 | 0 | 0 |
| 24 | 11.463028 | 24 | 0 | 0 |
| 25 | 10.316396 | 25 | 0 | 0 |
| 26 | 10.460642 | 26 | 0 | 0 |
| 27 | 10.663907 | 27 | 0 | 0 |
| 28 | 10.800993 | 28 | 0 | 0 |
| 29 | 1.354468 | 29 | 0 | 0 |
| 30 | 1.393152 | 30 | 0 | 0 |

```text
k=9..30 total = 571.232072s
vs baseline = +21.876450s
```

This excludes k=1..8, so full partition replacement is not faster yet.

## Extra Aggressive Probe After Review

用户指出逐个 k 手调 quad/triple 不具备未知 30-scale 泛化保证。这个判断成立，因此追加了两类更明确的 probe：

### Quad / triple time-window strengthening

| region | pair_only_s | triple_s | quad_s | best_s | conclusion |
|---|---:|---:|---:|---:|---|
| k=9 | 75.391216 |  | 82.040784 | 75.391216 | quad 更慢 |
| k=10 | 78.905116 |  | 87.150215 | 78.905116 | quad 更慢 |
| k=11 | 74.037252 |  | 74.159413 | 74.037252 | 基本无收益 |
| k=12 | 67.284066 | 64.636263 | 62.687788 | 62.687788 | 仅省 4.596278s |

如果只把已测最快 variant 用到 k=9..12，k=9..30 总耗时从 `571.232072s` 降到约 `566.635794s`，只节省 `4.596278s`。若粗略迁移到旧 B4V4 tree closure `549.355622s`，理论也只到约 `544.759344s`，速度提升约 `0.84%`。

结论：quad/triple 不是主线突破，只保留为局部 diagnostic。

### Dual task-slot lower-bound gate

新增 opt-in `V4_current_dual_task_slot_lb_gate`：

- 解一个小型 assignment relaxation，使用 true RMP dual、任务服务项、最早服务时间下界、每个 sortie 的最小出返弧成本和 inter-task 弧下界。
- 若 lower bound `>= -eps`，只关闭该 `(k,m)` scoped region。
- 不允许输出 full-space `can_certify_no_negative`，不允许替代 BPC tree certificate。

k=9 实测：

| variant | wall_s | scoped regions proven | dual-lb certified regions |
|---|---:|---:|---:|
| pair_only | 75.391216 | 9/9 | 0 |
| dual_task_slot_lb_gate | 76.621470 | 9/9 | 0 |

dual lower bound 在 m=2..9 的值仍约为 `-0.57` 到 `-0.48`，没有关闭任何区域，反而增加约 `1.23s`。说明当前瓶颈不是缺一个简单 dual-aware assignment bound，而是 route/time/resource formulation 的 relaxation gap 太大。

### Incremental route-template negative discovery

针对 plus57 round3 replay，同一个 true dual 下：

| method | wall_s | best RC | negative found | certificate |
|---|---:|---:|---|---|
| compact V4 replay | 356.857076 | -0.0080034 | yes | no-negative not certified |
| incremental route-template DP, target seed | 0.527012 | -0.0080034 | yes | diagnostic only |
| incremental route-template DP, active-pool seeds | 0.456755 | -0.00788215 | yes | diagnostic only |
| integrated final judge pre-harvest, target=1 | 0.426096 | -0.00788215 | yes | no-negative not certified |
| integrated final judge pre-harvest, target=5 | 11.380212 | -0.00788215 | yes, 5 columns | no-negative not certified |

active-pool seeded probe 使用 `120` 个 active column task-set seeds，实际检查 `13` 个 candidate rounds，`40106` 次 sortie attempts，`19992` 个 feasible route templates，`3870` 个 pareto labels。

相对 compact replay，active-pool seeded route-template probe 节省 `356.400321s`，找列速度约 `781.287728x`。它找到的是另一条合法负列：

```text
tasks = ice_site_006, ice_site_011, ice_site_020, ice_site_021, ice_site_023, ice_site_024, ice_site_026
rc = -0.00788215
sorties = 2
```

注意：该 probe 不能证明 no-negative，因为 selected task sets 不是 full-space coverage；但负列经过 manual reduced-cost audit，可以安全加入 master。

集成到 final judge 后，`target=1` 模式在 `0.426096s` 返回 1 条 audited negative column，compact fallback 没有被调用；相对 `356.857076s` compact replay，节省 `356.430980s`，约 `837.503933x`。`target=5` 模式在 `11.380212s` 返回 5 条 audited negative columns，用于减少后续 RMP round 数，但单轮 wall time 更高。

接入 BPC tree/root loop 后的 30-scale instance001 受控 probe：

| run | max rounds | wall_s | final judge sum_s | mean FJ_s | max FJ_s | columns added | status |
|---|---:|---:|---:|---:|---:|---:|---|
| target=1 tree probe | 3 | 6.78 | 5.33 | 1.78 | 2.11 | 3 | diagnostic frontier |
| target=1 tree probe | 10 | 28.465294 | 23.384901 | 2.338490 | 5.312009 | 10 | diagnostic frontier |
| target=5 tree probe | 3 | 36.381106 | 34.854519 | 11.618173 | 12.084336 | 10 | diagnostic frontier |

10-round 逐轮 reduced cost：

| round | FJ wall_s | best true RC | candidate rounds |
|---:|---:|---:|---:|
| 1 | 1.619486 | -0.000294000 | 18 |
| 2 | 2.114984 | -0.000325000 | 27 |
| 3 | 1.616276 | -0.001214520 | 16 |
| 4 | 2.469610 | -0.000772000 | 27 |
| 5 | 5.312009 | -0.002273104 | 66 |
| 6 | 1.796851 | -0.000025110 | 28 |
| 7 | 1.735207 | -0.000451917 | 27 |
| 8 | 2.277323 | -0.000701999 | 35 |
| 9 | 1.998104 | -0.000054999 | 29 |
| 10 | 2.445051 | -0.001331226 | 36 |

解释：pre-harvest 已经把“发现下一条真负列”从数百秒级 compact MILP 降到秒级，并且能在 BPC loop 中连续添加列；但 10 轮后仍有负列，状态仍是 `DIAGNOSTIC_PRICING_FRONTIER`。因此它解决的是 negative discovery tail，不是 final no-negative certificate。下一步真正剩下的是：当 pre-harvest 找不到 addable negative 后，如何让 compact proof/region proof 更快地证明无负列。

`target=5` 批量模式在该实例上不作为默认：3 轮共加 10 列，耗时 `36.381106s`，比 `target=1` 的 10 轮加 10 列 `28.465294s` 更慢。原因是 target=5 需要继续扫到约 132 个 candidate rounds 才凑够候选，单轮 wall 约 11-12s；target=1 找到第一条 addable negative 即停，吞吐更好。

新增 opt-in env：

```text
LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST=1
LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_TIME_CAP_SEC=15
LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_DIRECT_TASKS=8
LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_ACTIVE_SEEDS=120
LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_MAX_CANDIDATE_SETS=180
LUNAR_ICE_COMPACT_ROUTE_TEMPLATE_PRE_HARVEST_TARGET=1   # fastest single-column mode
```

当前建议：未知 30-scale 默认先用 `target=1` 快速推进；若连续多轮都命中且 RMP round 数过多，再比较 `target=3/5` 批量 harvest。无论 target 值如何，route-template no-column 仍然只能 fall through 到 compact proof，不能 claim certificate。

## Interpretation

- `(k,m)` partition proof is useful as a diagnostic and reusable ledger.
- It is not currently a faster replacement for the original B4V4 final judge.
- The dominant cost is still k=9..12 middle active-sortie regions.
- 手动打开 quad/triple 不具备泛化保证，且实测收益不足。
- dual task-slot lower-bound gate 是 exact-safe 的，但 relaxation 太弱，不能解决 k=9..12。
- High k becomes cheap:
  - k=29: 1.354468s
  - k=30: 1.393152s
- gated pair-conflict capacity is useful near the global matching upper bound:
  - k=29: 25 pair-conflict infeasible regions, all 0-variable.
  - k=30: 26 pair-conflict infeasible regions, all 0-variable.

## Current Recommendation

- Do not replace the original final judge with full `(k,m)` enumeration.
- Keep partition proof as a fallback/ledger for tail regions.
- 不再把 quad/triple 手调作为主线优化。
- 下一步主线应改成 hybrid proof-tail：
  - active-pool seeded incremental route-template DP 先快速收割负列；
  - compact V4 只在 route-template probe 找不到负列后进入 final no-negative proof；
  - 所有 returned negative columns 必须 manual RC audit；
  - route-template no-column 仍保持 diagnostic，不得 claim certificate；
  - 只有完整覆盖的 route-template universe 或 compact exact proof 才允许 no-negative certificate。

## 2026-07-09 Pivot After Review

用户指出：逐个 `(k,m)` 或 quad/triple 手动调参不具备未知 30-scale 泛化保证，且当前加速效果不足。这个判断成立。本轮把主线从“手调局部 cut/region”改成更激进但 exact-safe 的自动 portfolio：

```text
1. route-template pre-harvest seed-first；
2. active column task-set seeds；
3. true-dual cover 驱动的 add/drop/swap neighborhood seeds；
4. 所有候选列用 current true RMP dual 重新计算 manual RC；
5. 只有 addability audit 通过的负列才能进 master；
6. selected-set no-column 不能 claim certificate，只能 fail-closed 或 fall back 到 compact proof。
```

同时修复两个资源/性能问题：

- `solve_node_pricing_with_b2b_r3` 在已有 `initial_columns` 时不再先跑 30-scale B0 direct baseline。
- `_node_payload -> _columns_from_primal_context` 不再在没有 priced columns 时枚举 30-task direct universe；这只是 incumbent payload 的解释性候选，不是证书所需。
- incremental DP 和 sortie generation 增加更细 deadline 检查。
- `INCOMPLETE_LIMIT + added=0` 时立即 fail-closed，不重复跑相同 selected-set no-column probe。

新 probe：

| run | wall_s | rounds | added columns | final state | certificate |
|---|---:|---:|---:|---|---|
| direct route-template negative probe | 0.044443 | 1 candidate round | 1 negative found | negative discovery | no certificate |
| tree 5s deadline smoke | 5.012241 | 3 | 2 | fail-closed | no certificate |
| tree 60s, fallback to compact | 60.592199 | 5 | 4 | compact optimization proof incomplete | no certificate |
| tree 60s harvest-only, stop-on-no-add | 49.351942 | 17 | 16 | selected-set no-negative, fail-closed | no certificate |

解释：

- 自动 seed portfolio 明显优于 quad/triple 手动方向：能在约 `49.35s` 内连续收割 `16` 条 true-dual audited negative columns。
- 这仍然没有正式闭合 30-scale instance001；当前卡点已经更清楚地变成：route-template selected candidate space 找不到 addable negative 后，full-space no-negative proof 仍然需要 compact proof 或完整 partition coverage。
- 因此不能声称“比旧 B4V4 约 549s/接近 600s 更快求得精确最优”。目前能声称的是：negative discovery 阶段显著变快，但 exact no-negative certificate 尚未变快到可闭合。
- 下一步不应继续手调 quad/triple；应做 full-space proof 改造：
  - either 构造完整 task-set/region partition coverage，并把每个 region 的 nonnegative proof 纳入 ledger；
  - or 强化 compact proof 的 lower bound，使 selected-set no-negative 后的 full-space proof 不再退化成长时间 MILP。

## Verification

```text
PYTHONPATH=src python -m compileall -q src scripts tests
git diff --check
PYTHONPATH=src python -m unittest -q tests.test_lunar_ice_smoke.LunarIceSmokeTests
```

Previous full smoke result: `188 tests OK`.

Additional targeted check after dual-lb gate:

```text
PYTHONPATH=src python -m unittest -q tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_highs_compact_dual_task_slot_lower_bound_certifies_scoped_region_only
```

Result: `OK`.

Additional route-template checks:

```text
PYTHONPATH=src python -m unittest -q \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_partial_direct_pricing_keeps_multi_sortie_seed_task_sets \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_incremental_direct_pricing_matches_template_pricing_on_seed_set

PYTHONPATH=src python -m unittest -q \
  tests.test_lunar_ice_smoke.LunarIceSmokeTests.test_b4_1_route_template_pre_harvest_returns_audited_negative

PYTHONPATH=src python scripts/run_lunar_ice_route_template_negative_probe.py \
  --source-json runs/b4_1_true_dual_proof_tail_stage_b_30_v4_replay_merge/v4_round3_replay.json \
  --active-pool-json runs/objective_normalized_cost_risk_completion_full/compact_pricing_replay_plus57_stage001_round3_negative_feas_mtz_endpoint_pair_600s/plus57_stage001_plus_replay_probe.json \
  --output-dir runs/b4_1_route_template_negative_probe_plus57_round3 \
  --max-direct-tasks 8 \
  --max-active-seeds 120 \
  --max-candidate-sets 160 \
  --time-limit-sec 60
```

Result: tests `OK`; route-template probe wrote `runs/b4_1_route_template_negative_probe_plus57_round3/route_template_negative_probe_zh.md`; integrated final judge target=1 probe wrote `runs/b4_1_route_template_preharvest_final_judge_plus57_round3_target1/final_judge_route_template_preharvest_probe_zh.md`.
