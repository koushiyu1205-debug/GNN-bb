# BPC_future V7 水位式 frontier refinement 诊断

日期：2026-06-23

## 背景

专家修正指出：不能只盯一个最差 active token。corrected node bound 是否能 fathom，取决于当前 branch node 的 `z_RMP`、incumbent `UB`、journey 数上界 `R_N` 和所有阻碍达到水位的 critical tokens。

因此 V7 做了几件事：

- final-probe pricing 接收 `fathom_rc_target`，只有 `z_RMP >= UB - eps` 时才允许 refinement；
- frontier ledger 输出水位诊断：`frontier_critical_token_count`、`frontier_floor_multiplicity`、`frontier_second_active_lb`、`frontier_active_lb_p05/p10/median`、`frontier_required_rc_lift`；
- 新增 floor band 统计：`frontier_floor_band_count_0_1/1/5/10` 和 `frontier_target_band_count`；
- driver audit 新增 Tail Action Controller 字段，用于区分 A/B/C/D 类节点。

当前实现已经有严格 gated 的 one-step micro-expansion 接口和 ledger 原子替换单测，但它还不是最终验收完成的 Tier 1：完整 one-step/two-step split、离线 child coverage 穷举验证、批量 ROI 验证和 random-TW 20 gate 尚未完成。后续 Tier 1 必须只在 A 类节点运行，并证明所有合法子区域被覆盖。

更准确地说，V7 已完成的是诊断层，不是完整 refinement 算法层。

已完成：

- frontier ledger；
- `global_remaining_rc_lb`；
- `fathom_rc_target` gate；
- critical-token 数量；
- frontier 水位分布；
- token bound 安全更新；
- refinement 配置和结果接口；
- Tail Action Controller 需要的 A/B/C/D 分类字段。

尚未完成：

- critical token 的完整 one-step split；
- 必要时 two-step split；
- 父 token 到全部合法 child region 的覆盖证明；
- 父 token 到所有合法 child region 的原子替换覆盖证明；
- 超时、缺失 child、child 数超限、child bound 缺失或 coverage 校验失败时 fail-closed。

## 代码改动

- `JourneyPricingConfig` 新增：
  - `direct_journey_label_frontier_refinement_max_critical_tokens`
  - `direct_journey_label_frontier_refinement_floor_eps`
  - `direct_journey_label_frontier_refinement_fathom_rc_target`
- `JourneyPricingResult` 新增水位诊断、floor band 和 micro-expansion 计数字段。
- `FrontierBoundLedger` 新增 `update_lower_bound()` 和 `active_tokens_sorted()`；heap stale key 会被丢弃，避免更新 token bound 后错误返回旧 floor。
- driver 在 final-probe 前根据 `z_RMP/incumbent/R_N` 设置 `fathom_rc_target`；若 `z_RMP < UB - eps`，target 保持为空，pricing 只记录诊断，不花 refinement 预算。
- driver audit 新增 `tail_action/tail_action_reason/rmp_to_incumbent_gap/fathom_possible_if_rc_zero`。

## 验证

通过：

```bash
PYTHONDONTWRITEBYTECODE=1 /home/kai/miniconda3/bin/python -m compileall -q \
  BPC_future/pricing/journey_pricing.py \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py
```

通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_frontier_bound_ledger_replaces_parent_atomically \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_frontier_bound_ledger_keeps_parent_for_interrupted_expansion \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_frontier_bound_ledger_update_lower_bound_discards_stale_heap_keys \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_corrected_node_bound_audit_logs_proof_artifact \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_tail_action_controller_classifies_sparse_broad_and_branch_tail \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_pricing_config_maps_frontier_bound_ledger_flag \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_frontier_refinement_target_requires_rmp_to_reach_incumbent_floor
```

通过：

```bash
git diff --check -- \
  BPC_future/pricing/journey_pricing.py \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py \
  BPC_future/logical_graph/计划.md \
  BPC_future/logical_graph/run_reports/20260623_bpc_future_v7_waterline_frontier_refinement_diag_zh.md \
  BPC_future/logical_graph/run_reports/20260623_bpc_future_stage4_gat_on_20scale_speed_status_zh.md
```

## 300s canonical seed61000 探针

实例：

```text
BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
```

输出：

- CSV: `BPC_future/results/20260623_v7_waterline_refinement_diag_300_randomtw20_seed61000.csv`
- JSONL: `BPC_future/results/logs_20260623_v7_waterline_refinement_diag_300_randomtw20_seed61000/BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json.jsonl`

结果：

- status: `EXTERNAL_TIME_LIMIT`
- wall: `300.020187s`
- root CB certificate: `105.138437s`
- node 1 CB retry: `181.350206s`，`INCOMPLETE/time_limit`
- node 2 CB certificate: `233.528963s`

node 1 关键诊断：

| 指标 | 值 |
|---|---:|
| `z_RMP` | `580.221453667` |
| 当前 incumbent | 约 `584.354872` |
| `global_remaining_rc_lb` | `-412.683770667` |
| `corrected_node_lb` | `-6435.402647667` |
| `frontier_region_count` | `23470` |
| `frontier_min_active_lb` | `-412.683770667` |
| `frontier_second_active_lb` | `-412.540795667` |
| `frontier_active_lb_p05` | `-405.143052667` |
| `frontier_active_lb_p10` | `-403.151726666` |
| `frontier_active_lb_median` | `-395.956203667` |
| `frontier_refinement_reason` | `missing_fathom_rc_target` |

## 结论

V7 说明 node 1 当时不是“只差把 frontier floor 从 -412 抬到 0 就能剪枝”。因为 `z_RMP < UB - eps`，即使 `global_remaining_rc_lb=0`，corrected node bound 也只能到 `z_RMP≈580.22`，仍低于 incumbent `≈584.35`，不能 fathom。

这里有一个关键边界：在最小化列生成里，加入新的负 reduced-cost 列只会让 RMP objective 下降或不变，不会提高 `z_RMP`。继续 CG 的作用是得到正确 LP closure，而不是把当前节点推入可剪枝区间。要让类似 node 1 的节点进入可剪枝区间，只能依靠更好的 incumbent、有效割/更强 formulation，或更有效的分支让子节点 LP bound 上升。

因此 seed61000 的 node 1 更接近 Tail Action Controller 的 D 类：`z_RMP < UB - eps`，final probe 即使完美也不能直接 fathom；如果 CG 已经拖尾且新增列主要 inactive-only/weak，就应该考虑 exact-safe early branch，而不是消耗 micro-expansion 预算。

因此 proof-tail refinement 必须受水位 gate 控制：

- 若 `z_RMP < UB - eps`，不要花 final-probe refinement 预算；
- 若 target 存在但 critical token 数很大，局部 top-1/top-2 没意义，应 fail-fast；
- Tier 1 只适用于“可 fathom + 稀疏低水位”的 A 类节点；
- 对“可 fathom + 大面积低水位”的 B 类节点，不要逐 token split，应走 aggregate route-aware bound、更强 completion relaxation、cuts/formulation 或 token region 重组；
- 对“不可 fathom”的 C/D 类节点，micro-expansion 不能直接剪枝，应转向 LP closure、incumbent、cuts 或 branch action。

Tier 1 的精确性契约必须是 fail-closed：

- 对父 token 枚举所有合法下一步，包括继续当前 sortie、结束当前 sortie、开始下一 sortie、下一 sortie 的合法首任务，以及当前状态允许的终止分支；
- 对每个 child 使用 `LB_child=max(LB_parent, LB_child_raw)`；
- 只有全部 child 成功构造、覆盖校验通过、全部 child token 注册完成后，才能注销 parent token；
- 任一超时、child 超限、transition 无法生成、child 无安全 bound 或 coverage 失败，parent token 都必须保持不变；
  - 无 `fathom_rc_target`、global RC LB 无效/coverage 不完整、global floor 已达 target 或 critical token 超限时，refinement 调用次数必须为 0。

## Tail Action Controller 分类

后续日志需要显式区分四类节点：

| 类别 | 条件 | 动作 |
|---|---|---|
| A: 可 fathom + 稀疏低水位 | `z_RMP >= UB - eps`、`fathom_rc_target` 存在、global RC LB valid/coverage complete、global floor 低于 target，critical token 和 floor multiplicity 都小 | Tier 1 micro-expansion + local route-aware refinement |
| B: 可 fathom + 大面积低水位 | `z_RMP >= UB - eps`，但几百/几千 token 低于 target | 不逐 token refinement，改用 aggregate bound/cuts/formulation/region 重组 |
| C: 不可 fathom + CG 仍有效 | `z_RMP < UB - eps`，仍找到有用负列 | 继续短预算 pricing/GAT admission 完成 LP closure |
| D: 不可 fathom + CG 拖尾 | `z_RMP < UB - eps`，objective flat，新增列主要 inactive-only/weak | exact-safe early branch；不把当前 RMP objective 当 exact node bound |

A/B 类还有一个必要前提：本轮 final-probe 不能已经返回 true-RC 负列。若 pricing 已有待加入负列，即使当前 `z_RMP >= UB - eps`，也必须先加入负列并继续 LP closure，因为最小化 RMP 加列会让后续 `z_RMP` 下降或不变。后续控制器已把这种情况记录为 `CONTINUE_COLUMN_GENERATION / fathom_possible_but_negative_column_requires_lp_closure`，避免把未闭合轮次误算成 Tier 1 refinement 机会。

2026-06-24 进一步收紧：Tail Action Controller 的 `FRONTIER_REFINEMENT` 标签现在与执行层必要条件对齐。只有 target 存在、global RC LB valid、coverage complete、global floor 仍低于 target，且 critical token/floor multiplicity 未超 cap 时才标为 A 类；缺 target、coverage 不完整、缺 global LB 或 floor 已达 target 都不会进入 A 类机会统计。

已在日志侧新增/计划新增字段：

- `tail_action`
- `tail_action_reason`
- `rmp_to_incumbent_gap`
- `fathom_possible_if_rc_zero`
- `frontier_floor_band_count_0_1/1/5/10`
- `frontier_target_band_count`
- `recent_true_rc_productivity`
- `recent_active_support_additions`
- `recent_rmp_objective_progress`

## V8 Tail Action Controller 复验

第一次 300s 诊断暴露出一个实现问题：corrected-bound audit 事件已经有 `tail_action` 字段，但部分调用点没有传入 incumbent，导致 `tail_action=UNKNOWN`。已修复所有节点求解路径的 audit 调用，统一传入 `local_incumbent`。

复验命令使用同一个 canonical random-TW 20 seed61000，外部时间限制缩短到 220s，因为 node 1 final retry 在约 198s 已经写出：

```text
BPC_future/results/20260623_v8_tail_action_controller_220_randomtw20_seed61000.csv
BPC_future/results/logs_20260623_v8_tail_action_controller_220_randomtw20_seed61000/...
```

结果仍为 `EXTERNAL_TIME_LIMIT`，但 controller 日志已按预期工作：

| 节点 | 时间 | `z_RMP` | incumbent | `global_remaining_rc_lb` | `tail_action` | `fathom_possible_if_rc_zero` | micro attempts |
|---:|---:|---:|---:|---:|---|---|---:|
| root | `104.954704s` | `580.044467333` | `584.354872` | `0.0` | `EARLY_BRANCH` | `false` | `0` |
| node 1 | `198.026044s` | `580.221453667` | `584.354872` | `-412.683770667` | `EARLY_BRANCH` | `false` | `0` |

node 1 的水位带：

- `frontier_floor_band_count_0_1=1`
- `frontier_floor_band_count_1=8`
- `frontier_floor_band_count_5=761`
- `frontier_floor_band_count_10=2704`
- `frontier_region_count=25589`
- `frontier_refinement_reason=missing_fathom_rc_target`

这说明当前 gate 正常：`z_RMP < UB - eps` 时 `fathom_rc_target` 为空，micro-expansion 没有误触发；node 1 被归到 D 类/early-branch 方向，而不是 A 类 refinement 方向。

新增诊断脚本：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python \
  BPC_future/scripts/audit_journey_tail_action_controller.py \
  BPC_future/results/logs_20260623_v8_tail_action_controller_220_randomtw20_seed61000 \
  --output-dir BPC_future/results/journey_tail_action_controller_audit_v8_seed61000_220_20260623 \
  --report BPC_future/logical_graph/run_reports/20260623_bpc_future_journey_tail_action_controller_audit_v8_seed61000_220_zh.md
```

审计摘要：

- `row_count=12`
- `CONTINUE_COLUMN_GENERATION=7`
- `EARLY_BRANCH=5`
- `FRONTIER_REFINEMENT=0`
- `BROAD_PLATEAU_FALLBACK=0`
- `unknown_action_count=0`
- `micro_expansion_attempt_row_count=0`

## V9 signal run：接入 active-support / objective-progress 与 D 类 opt-in

220s 复验只确认了 incumbent 绑定和 A/B/D gate，但无法判断“有负列”到底是有效 CG 还是 weak tail。后续补充接入两个 CG history 字段：

- `recent_active_support_additions`
- `recent_rmp_objective_progress`

同时修正了一个边界：当 active-support 信号缺失时，不把 `recent_rmp_objective_progress=0` 单独当作 D 类证据，避免 root 前段误触发。V9 新增默认关闭的 `journey_tail_action_early_branch_enabled`，只在 D 类证据完整时执行 exact-safe early branch；它不打开旧 generic early branch，不使用当前 RMP objective 作为 exact node bound。

180s canonical random-TW 20 `seed61000` V9 opt-in run：

```text
BPC_future/results/20260623_v9_tail_action_early_branch_180_randomtw20_seed61000.csv
BPC_future/results/logs_20260623_v9_tail_action_early_branch_180_randomtw20_seed61000/...
BPC_future/results/journey_tail_action_controller_audit_v9_tail_action_early_branch_180_seed61000_20260623/summary.json
```

审计摘要：

- `row_count=10`
- `CONTINUE_COLUMN_GENERATION=6`
- `EARLY_BRANCH=4`
- `recent_active_support_addition_row_count=4`
- `recent_rmp_objective_progress_row_count=3`
- `fathom_possible_if_rc_zero_count=0`
- `micro_expansion_attempt_row_count=0`

关键分界：

| 节点 | cg_iter | true-RC productivity | active-support additions | RMP progress | action |
|---:|---:|---:|---:|---:|---|
| root | 29 | 26 | null | `0.0` | `CONTINUE_COLUMN_GENERATION` / signal incomplete |
| root | 30 | 12 | 4 | `2.407180667` | `CONTINUE_COLUMN_GENERATION` |
| root | 34 | 1 | 1 | `0.0540045` | `CONTINUE_COLUMN_GENERATION` |
| node 1 | 1 | 2 | null | null | `CONTINUE_COLUMN_GENERATION` |
| node 1 | 2 | 1 | 0 | `0.0` | `EARLY_BRANCH` |

这修正了原先“只要有负列就继续 CG”的粗判定：node 1 第 2 轮虽然仍找到 1 个 true-RC 负列，但它没有改变 active support，RMP objective 也没有移动，因此被归为 D 类 `rmp_below_incumbent_weak_columns_no_active_or_objective_progress`。

V9 opt-in 实际触发：

```text
time=139.743157
event=journey_early_branch_trigger
node_id=1
cg_iter=2
trigger=tail_action_controller
reason=rmp_below_incumbent_weak_columns_no_active_or_objective_progress
inherited_lower_bound=580.044467
rmp_objective=580.221454
exact_bound_available=false
child_lower_bound_exact=false
```

随后 node 1 的 children 只继承父节点合法下界，且 `lower_bound_exact=false`。这符合专家修正：D 类 early branch 可以调度搜索，但不能把当前 RMP objective 当作 exact node bound。该 180s 探针仍为 `EXTERNAL_TIME_LIMIT`，说明它安全避开了一次 node 1 tail，但还没有解决后续 child proof tail。

扩展后的审计脚本还能把 `journey_early_branch_trigger` 与 child queue 绑定：

- `early_branch_trigger_count=1`
- `tail_action_early_branch_trigger_count=1`
- `nonexact_early_branch_trigger_count=1`
- `tail_action_queued_child_count=2`
- `tail_action_nonexact_queued_child_count=2`
- `tail_action_observed_child_audit_count=0`

V9 的 D 类触发确实生成了两个 child：`queued_child_ids=3,4`，`allowed_current_journeys=118/167`，且两个 child 都是 `lower_bound_exact=false`。但 180s 内没有观察到这些 child 的 audit row，因为搜索先处理了 root sibling node 2。这说明下一步不能只看“是否提前分支”，还要看 child ordering / branch-impact：D 类触发后的 child 是否应优先进入证明，或者哪些 child 更可能减少后续 pricing/CB tail。

已新增默认关闭的 D 类 child-priority opt-in：`journey_tail_action_child_priority_enabled=true` 时，tail-action early branch 生成的 child 可使用 `journey_tail_action_child_priority_width` 调整队列顺序。该开关只影响调度，不改变 official bound、分支约束、剪枝或 certificate；审计脚本会在 `early_branch_trigger_rows` 中汇总 child 的 `queue_priority_width` min/max。现有 V9 日志早于该补丁，因此还不能说明该 opt-in 的实际速度收益。

V10 fresh probe 打开该 opt-in 后，node 1 的 D 类 child 3/4 均以 `queue_priority_width=-1` 入队，并且下一条 RMP 是 node 3，说明队列顺序已被正确改变；但 220s 仍 `EXTERNAL_TIME_LIMIT`，node 3 在 `216.582741s` 进入 `exact_pricing_completion_bound_retry`。V10 旧日志中 node 3 前几轮出现的 `FRONTIER_REFINEMENT` 只是 `rmp_objective >= incumbent` 的分类结果，仍伴随 `negative_journey_requires_column_addition`，不是 final-probe 可直接 fathom 的 Tier 1 机会；后续控制器已收紧为“有负列先继续 CG”。到 no-negative 时 node 3 已变成 `rmp_objective < incumbent`。

## 2026-06-24 修正：Tier 1 的使用边界

一个关键边界必须写死：最小化列生成中，加入负 reduced-cost 列只会让 RMP objective 下降或不变，不会提高 `z_RMP`。因此 micro-expansion / frontier refinement 只能帮助证明“剩余未探索 pricing region 的 RC 下界”，不能把 `z_RMP` 本身抬到 incumbent 之上。

对 seed61000 的 node 1：

```text
z_RMP = 580.221453667
UB    ≈ 584.354872
```

即使完整证明 `global_remaining_rc_lb >= 0`，节点下界最多回到 `LB=z_RMP≈580.22145`，仍低于 UB，不能 fathom。因此 node 1 不属于 Tier 1 可直接解决的节点；继续在这里做 critical-token split 只会消耗预算。

节点分类需要按下面四类执行：

- A 类：`z_RMP >= UB - eps`，critical token 和 frontier floor multiplicity 都小，且 child 总数可控。只在这类节点执行 Tier 1 micro-expansion / route-aware refinement，尝试抬高 global floor 并直接 fathom。
- B 类：`z_RMP >= UB - eps`，但几百或几千个 token 都低于 target。不要逐 token refinement；问题是 relaxation 系统性过松，应改用 aggregate route-aware bound、更强 completion relaxation、更紧 master/cuts 或 token region 重组。
- C 类：`z_RMP < UB - eps` 且 CG 仍持续找到 active-support-changing negative columns，RMP objective / basis 仍明显变化。继续短预算 pricing / GAT admission，目标是正确闭合 LP。
- D 类：`z_RMP < UB - eps` 且 objective flat，新增列主要 inactive-only / weak，final probe 不可能立即 fathom。执行 exact-safe early branch，但不能把当前 RMP objective 当 exact node bound，不能用它剪枝，child 最终仍靠 exact pricing closure。

所以“下一步实现所有 critical token 的 one-step/two-step split”需要改成“只在 A 类稀疏低水位节点上，对预算内 critical token 做 fail-closed split”。如果 target 接近 0 且 critical token 成百上千，逐 token split 会制造更严重的状态爆炸，应立即走 B 类 fallback，而不是扩大 micro-expansion。

Tier 1 真正完成时还必须满足算法层契约：父 token 要枚举所有合法 child region，全部 child 成功构造、验证覆盖、注册并拿到安全 bound 后，才能注销 parent；任一超时、child 超限、transition 缺失、bound 缺失或 coverage 校验失败时，parent 保持不变。

## 下一步

1. 完成严格 gated 的 Tier 1 critical-token micro-expansion：只在 A 类节点运行，且只处理预算内的稀疏 critical token；父 token 必须在所有合法 child 成功注册后才能移除，任何超时/child 超限/bound 缺失都 fail-closed。不要在 B 类大面积低水位节点上逐 token split。
2. 输出 token snapshot/replay：rank、base LB、refined LB、remaining task count、method、CPU、global floor before/after。
3. 在 random-TW 60-instance 的 20 规模集合中统计：有多少 final-probe 节点满足 `z_RMP >= UB - eps`，以及 critical token 面积分布。
4. 并行推进 incumbent heuristic、pricing-compatible cuts、branch strong-bound gain、child proof cost 和 child ordering；这些才是把 node 1 类节点推入可剪枝区间的方向。
5. 同步推进 late-negative tail 审计和 support-aware admission/delay：分清 active-support-changing true negative、inactive-only true negative 与 weak filtered tail；V18 已有默认关闭的 admission/delay 骨架，并增加 root-safe depth gate，默认不在 root 延迟 inactive-only。V19 的 seed61000 220s branch-tail paired probe 表明，该实例 depth=1 的 exact true negatives 全部是 active-support-changing / new task-set，不是 inactive-only delay 正例；V20 已新增 `audit_journey_support_aware_branch_exact_tail.py` 和 shadow-only 跑法；V21 已扩到 random-TW 20 的 60-instance，结果显示 branch exact tail 的 inactive-only share 约 `5.55%`，纯 inactive-only 主类只有 `4/219`。因此当前不应继续做 inactive-only delay A/B，应转向 branch-impact、child proof-cost / ordering、incumbent improvement 和 cuts/formulation。
