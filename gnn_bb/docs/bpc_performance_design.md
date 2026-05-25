# Clean BPC Performance Design Notes

本文只记录后续性能方向，不改变当前 route-vehicle clean BPC 主线。

## Task-Level Schedule-Capacity Separator

当前 route-vehicle master 的主要松弛之一是：单条 sortie route 各自可行，但同一车辆上的多条 sortie 未必能排成真实 schedule。task-level schedule-capacity cut 把 exact 单车多 sortie oracle 的容量证书投影回 master：

```text
z_ir = sum_p a_ip lambda_pr
sum_{i in S} z_ir <= U(S) y_r
```

其中 `U(S)` 必须由 `exact_schedule_task_capacity()` 完整证明。oracle incomplete 时只写缓存和诊断，不加 cut、不更新 bound、不参与 fathoming。当前车辆同质，因此 run-local cache 用排序后的 `S` 复用 exact `U(S)`；若未来支持异构车辆，cache key 必须加入 vehicle type。

实现边界：
- separator 默认关闭：`task_schedule_capacity_cuts_enabled: false`；
- pair/triple/small-set 候选分层生成，cheap precheck 统一为 `activity > y_r + eps`，避免漏掉 `U(S)=1` 的 triple；
- small set 只从 RIM、route-pack、schedule incompatibility 等 strong witness 生成，默认 budget 为 0；
- candidate memory 从 route-set schedule packing、RIM rejected assignment、integral validation conflict 和 schedule incompatibility witness 接收 route task union；
- 成功的 task-level cut 会写入 branching witness summary，默认只记录，不改变 branch path；实际 tie-break boost 需要显式打开 `task_schedule_capacity_branch_signal_apply_enabled`；
- 该方向不改 pricing reduced-cost 公式，不引入 PersistentRMP/native pricing，也不替换 vehicle-schedule master。

消融入口：

```bash
python scripts/run_task_schedule_capacity_ablation.py --instances very_small --quiet
python scripts/run_task_schedule_capacity_ablation.py --instances bench_10_01 bench_20_01 --time-limit 300 --variants baseline root_only pair_triple witness_only
```

判断是否值得进入默认主线时，优先看 root bound、node count、pricing calls、label pops、RIM rejected count、route-pack low-improvement cut 数量、branch path 和 oracle time。若 root/shallow bound 没有提升但 oracle time 或 cut 数量明显上升，应继续保持默认关闭。

## Persistent RMP / Incremental RMP

当前 `solve_rmp_lp` 每轮重新构建 SCIP 模型。hard instances 中 RMP solve 和 branch testing RMP 次数很多，模型重建开销会被重复支付。

2026-05-25 已实现第一阶段 `bpc.persistent_rmp.PersistentRMP`，默认仍关闭：

```text
persistent_rmp_enabled: false
```

第一阶段边界：
- 只替换 `CleanBPCTree._process_node` 中主节点的 RMP-CG loop；
- branch testing 的 `_restricted_child_lp_gain` 和 `_heuristic_child_gain` 仍调用原 `solve_rmp_lp`；
- 每个 processed node 内部单独持有 persistent model，不传给 child node；
- Phase-I 切到 Phase-II 时重建；
- cut purge 后重建；
- route columns 和 cuts 仅在同一 phase、同一 branch constraints 内追加同步；
- dual 仍来自 SCIP 当前 LP，pricing 仍使用当前 Python exact pricing；
- `lambda_reduced_costs` 仍来自 SCIP variable redcost，并通过 reduced-cost consistency 测试审计。

该实现是工程优化，不改变 RMP 数学模型、cut validity、pricing reduced cost、lower-bound certificate 或 fathoming 规则。persistent sync/solve 失败时，当前节点记录 `persistent_rmp_fallback` 并回退到原 rebuild RMP。

后续完整 Persistent RMP 仍可继续设计：
- 更细粒度复用 branch testing 的临时 RMP；
- 更系统的 cut lifecycle 和 basis warm-start；
- 更明确地区分可增量同步与必须 rebuild 的模型变更。

这些后续项暂未实现，因为 branch testing 路径敏感，且容易混入 temporary branch rows/cuts 的生命周期风险；当前阶段先验证主节点 CG loop 的 objective、dual 和 reduced-cost 一致性。

## High-Performance Exact Pricing Kernel

20 规模 timeout 中 Python labeling 的 `label_pops` 可到 6e7 到 1e8+。此时瓶颈主要是 exact pricing certificate，而不是单纯 RMP 求解。

长期可以保留 Python 层的 tree、RMP、cut manager、logger，把 exact pricing 内核数组化：
- Cython 或 pybind11/C++ 实现 label storage、dominance、extension；
- 输入真实 dual、branch constraints、valid cuts；
- 输出 negative routes 与 exhausted certificate；
- certificate 必须对应 true dual 下完整枚举，不能用 heuristic/relaxed dual 代替。

本阶段明确不实现 pybind11/C++ 或其他 native pricing backend。原因是 native pricing kernel 会显著增加构建、debug 和 exactness audit 成本；当前优先把 RMP 增量化做好。Python exact pricing fallback 保留为唯一 pricing backend，reduced cost 公式未改。

## Dual Stabilization

Dual stabilization 只能作为 column generation 加速器：
- stabilized dual 可用于尝试生成列、缓解振荡；
- 节点完成证明前必须回到 true dual；
- official lower bound 和 fathoming 只能使用 true-dual exact pricing certificate。

不在本次实现的原因：没有必要先引入影响 CG 路径的复杂策略；当前更需要诊断哪些节点 proof-heavy。

## 2LBB / ML Branch Ranking

2LBB 或 ML ranking 只能用于候选排序和减少测试预算：
- 不参与剪枝；
- 不参与 lower bound；
- 不替代 exact pricing certificate；
- 必须保留 fallback 到现有 3PB。

不在本次实现的原因：branching 改动路径敏感，可能改善 testing time 但恶化 incumbent 或搜索树。应先用新增日志确认 branch-hard 实例，再做受控消融。
