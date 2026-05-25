# Clean BPC Performance Design Notes

本文只记录后续性能方向，不改变当前 route-vehicle clean BPC 主线。

## Persistent RMP / Incremental RMP

当前 `solve_rmp_lp` 每轮重新构建 SCIP 模型。hard instances 中 RMP solve 和 branch testing RMP 次数很多，模型重建开销会被重复支付。

建议设计 `PersistentRMP`：
- 以节点为生命周期保留 SCIP 模型、变量、约束和 dual capture；
- 增量添加 route columns、cuts、branch rows；
- 每轮 LP 后读取真实 dual，仍调用现有 exact pricing 证书；
- 只降低建模 overhead，不改变 master、pricing、cut 有效性或 lower bound 语义。

不在本次实现的原因：需要重构 RMP 变量索引、cut 生命周期、branch 测试临时约束和 dual capture，风险高于本次小步改造目标。

## High-Performance Exact Pricing Kernel

20 规模 timeout 中 Python labeling 的 `label_pops` 可到 6e7 到 1e8+。此时瓶颈主要是 exact pricing certificate，而不是单纯 RMP 求解。

建议保留 Python 层的 tree、RMP、cut manager、logger，把 exact pricing 内核数组化：
- Cython 或 pybind11/C++ 实现 label storage、dominance、extension；
- 输入真实 dual、branch constraints、valid cuts；
- 输出 negative routes 与 exhausted certificate；
- certificate 必须对应 true dual 下完整枚举，不能用 heuristic/relaxed dual 代替。

不在本次实现的原因：需要严格对齐 reduced cost 公式和 dominance 语义，应单独配套 regression tests 与 profile。

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

