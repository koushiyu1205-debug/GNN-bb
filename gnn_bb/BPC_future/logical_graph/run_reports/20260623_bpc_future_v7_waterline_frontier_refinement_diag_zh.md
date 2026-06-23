# BPC_future V7 水位式 frontier refinement 诊断

日期：2026-06-23

## 背景

专家修正指出：不能只盯一个最差 active token。corrected node bound 是否能 fathom，取决于当前 branch node 的 `z_RMP`、incumbent `UB`、journey 数上界 `R_N` 和所有阻碍达到水位的 critical tokens。

因此 V7 做了几件事：

- final-probe pricing 接收 `fathom_rc_target`，只有 `z_RMP >= UB - eps` 时才允许 refinement；
- frontier ledger 输出水位诊断：`frontier_critical_token_count`、`frontier_floor_multiplicity`、`frontier_second_active_lb`、`frontier_active_lb_p05/p10/median`、`frontier_required_rc_lift`；
- 新增 floor band 统计：`frontier_floor_band_count_0_1/1/5/10` 和 `frontier_target_band_count`；
- driver audit 新增 Tail Action Controller 字段，用于区分 A/B/C/D 类节点。

当前实现已经有严格 gated 的 one-step micro-expansion 接口，但它还不是最终验收完成的 Tier 1：two-step split、离线 child coverage 穷举验证、批量 ROI 验证和 random-TW 20 gate 尚未完成。后续 Tier 1 必须只在 A 类节点运行，并证明所有合法子区域被覆盖。

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

## Tail Action Controller 分类

后续日志需要显式区分四类节点：

| 类别 | 条件 | 动作 |
|---|---|---|
| A: 可 fathom + 稀疏低水位 | `z_RMP >= UB - eps`，critical token 和 floor multiplicity 都小 | Tier 1 micro-expansion + local route-aware refinement |
| B: 可 fathom + 大面积低水位 | `z_RMP >= UB - eps`，但几百/几千 token 低于 target | 不逐 token refinement，改用 aggregate bound/cuts/formulation/region 重组 |
| C: 不可 fathom + CG 仍有效 | `z_RMP < UB - eps`，仍找到有用负列 | 继续短预算 pricing/GAT admission 完成 LP closure |
| D: 不可 fathom + CG 拖尾 | `z_RMP < UB - eps`，objective flat，新增列主要 inactive-only/weak | exact-safe early branch；不把当前 RMP objective 当 exact node bound |

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

## 下一步

1. 完成严格 gated 的 Tier 1 critical-token micro-expansion：只在 A 类节点运行；父 token 必须在所有合法 child 成功注册后才能移除，任何超时/child 超限/bound 缺失都 fail-closed。
2. 输出 token snapshot/replay：rank、base LB、refined LB、remaining task count、method、CPU、global floor before/after。
3. 在 random-TW 60-instance 的 20 规模集合中统计：有多少 final-probe 节点满足 `z_RMP >= UB - eps`，以及 critical token 面积分布。
4. 并行推进 incumbent heuristic、pricing-compatible cuts、branch strong-bound gain、child proof cost 和 child ordering；这些才是把 node 1 类节点推入可剪枝区间的方向。
