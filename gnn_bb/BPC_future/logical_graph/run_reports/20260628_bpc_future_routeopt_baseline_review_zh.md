# RouteOpt 开源基线调研与 BPC_future 迁移判断

## 结论

RouteOpt 值得作为 exact VRP branch-price-and-cut 工程基线来学习，但不适合直接替换 `BPC_future`。

原因是：RouteOpt 面向 CVRP/VRPTW 的通用 exact solver 框架，而我们的 `BPC_future` 是 journey/sortie 结构、logical graph、true-dual exact pricing、completion-bound proof tail 和 GAT branch overlay 组合起来的定制求解器。两边的列、pricing 状态、分支约束、certificate 语义都不一样。

真正可迁移的是算法结构和工程思想，优先级如下：

1. 分支候选的多阶段测试与动态候选数。
2. pricing-compatible cuts / 更强 formulation。
3. 列池压缩、变量固定、节点状态恢复。
4. 学习分支的标签定义和候选覆盖设计。

## RouteOpt 关键信息

公开资料显示 RouteOpt 是一个开源模块化 exact VRP solver，支持 CVRP/VRPTW，强调 modular branch/cut/variable reduction，并包含 learning-to-branch 相关模块。

需要注意许可证：RouteOpt 2.0 是 GPLv3。因此我们不应直接复制源码进当前项目；可以阅读、理解后重新实现思想，或把它作为独立外部工具/参考实现。

官方来源：

- GitHub: `https://github.com/Zhengzhong-You/RouteOpt`
- Docs: `https://zhengzhong-you.github.io/RouteOpt-Docs/`
- Branching docs: `https://zhengzhong-you.github.io/RouteOpt-Docs/branching/branching_index.html`
- Best K Formula docs: `https://zhengzhong-you.github.io/RouteOpt-Docs/branching/bkf.html`
- Branch-and-bound tree docs: `https://zhengzhong-you.github.io/RouteOpt-Docs/branching/bbt.html`
- DeLuxing docs: `https://zhengzhong-you.github.io/RouteOpt-Docs/deluxing/deluxing_index.html`
- 仓库源码树确认存在 `packages/rank1_cuts`、`packages/rounded_cap_cuts`、`packages/deluxing`、`packages/branching/bkf`、`packages/branching/candidate_selector`。

## 对当前 BPC_future 问题的映射

### 当前问题不是单纯找列

近期结果显示：

- V545 在 20-scale random-TW full60 上达到 `36/60 OPTIMAL`，capped mean `341.54s`。
- V545 收益来自 state-scoped branch score path，early branch 和 admission 都关闭。
- hard case seed61311 中，root `[16,17]` 相比 baseline `[17,20]` 能改善 gap、incumbent、fathom 和 branch 数，但 600s 内仍未闭环。
- 对这些节点，root lower bound / best dual 没有实质改善，completion-bound / final-judge retry 仍高。

这说明 branch pair 确实能改变 proof-tail 结构，但仅靠当前 replay overlay 覆盖太窄；而对 `z_RMP < UB` 的节点，只加更多列或做更多 final-probe 本身不能剪枝。

## RouteOpt 可借鉴方向

### 1. 多阶段 branch candidate testing

RouteOpt 的 branching 模块不是只给候选打一个静态分数，而是使用多阶段候选测试：initial screening、LP testing、heuristic testing、exact testing，并用 BKF 动态权衡测试时间和候选质量。

这对应我们当前最需要补的一块：不要只依赖 replay score map 的静态分数，应在真正分支前，对少量 top candidates 做受控 child-probe / LP-bound / proof-cost 预估。

建议迁移方式：

- 在 `journey_branch_candidates` 后增加 exact-safe limited branch testing 层。
- 对 top-k pair 计算短预算 child 指标：
  - child corrected LB gain
  - child width/balance
  - child pricing productivity
  - child completion-bound retry risk
  - child incumbent/gap/fathom proxy
- k 不固定为 top200，而是按节点剩余预算、最近 proof-tail 成本、候选 score spread 动态调整。
- 分数仍只用于排序，不作为 official bound。

### 2. Cuts / formulation 是必须补的主线

RouteOpt 强调 Rank-1 cuts、limited-memory cut handling、RCC 等切平面，并且在 labeling 中维护对应 reduced cost 更新。

这正好对应我们的硬瓶颈：很多 20-scale hard nodes 是 `z_RMP < UB`，即使 pricing 完整证明没有负列，也只能证明 LP bound，不能 fathom。要让节点进入可剪枝区间，需要：

- 更好的 incumbent；
- 更强 formulation；
- 有效、pricing-compatible 的 cuts；
- 或者能同时抬高两个 child LP bound 的强分支。

建议迁移方式：

- 先做一个 `journey subset-row / rank-1-like cut feasibility audit`：
  - cut 是否对 journey columns 有稳定系数计算；
  - pricing reduced cost 是否能精确加入 cut dual；
  - completion-bound 是否能安全处理 cut reward；
  - cut 是否会显著破坏 labeling dominance。
- 优先实现小维度、有限 memory、易验证的 subset-row-like cuts。
- 每个 cut 必须有：
  - RMP coefficient getter；
  - pricing RC updater；
  - exact pricing / final judge 一致性测试；
  - no-cut vs with-cut 目标值和 certificate 审计。

### 3. DeLuxing / 列池压缩思想

RouteOpt 的 DeLuxing 是基于 LP dual 和 UB 的变量固定/列池缩减，用于减少大规模 enumerated column pool。

我们不能直接照搬，因为 `BPC_future` 主要是按需生成 journey columns，而不是稳定的大枚举池。但思想可以迁移为：

- inactive column pool compression；
- branch subtree 内重复列的按需恢复；
- 对只影响 RMP 性能、不影响 exact pricing 证书的列池清理；
- 对已枚举 route/journey pool 做 UB-safe 的诊断性压缩。

关键限制：

- 删除 RMP 列不能破坏当前可行基和 incumbent 回放。
- 若列可能参与 certificate 或当前 LP optimum，必须可恢复或禁止删除。
- 任何压缩都不能替代 exact pricing closure。

### 4. Node restoration / 状态快照

RouteOpt 的 BBT 设计支持节点读写、状态恢复和并行树处理。我们的 full replay、child probe、retry gate、branch path overlay 现在反复重建节点状态，成本很高。

建议迁移方式：

- 为 journey node 增加可审计 snapshot：
  - branch constraints；
  - active columns；
  - incumbent；
  - RMP basis/dual 可选；
  - completion-bound cache 可选；
  - GAT/score context key；
  - exact-safe lower-bound metadata。
- snapshot 只用于加速恢复，不新增剪枝依据。
- 先用于 replay/数据采集，再考虑进入正式 solver。

### 5. Learning-to-branch 的正确标签

RouteOpt / 2LBB 的方向说明，在 BPC 里 learning-to-branch 的核心难点是候选测试成本和 branch 质量之间的 tradeoff，而不是单纯分类“某 pair 好不好”。

这对我们现在的训练很关键：

- V637 的 weak gap/fathom positive 可以做辅助标签，但不是 strict full-solve positive。
- V641/V642 的 child-probe hard negatives 说明短预算 wall gain 会误导。
- GAT branch score 应学习多目标：
  - full replay wall gain；
  - gap improvement；
  - fathom gain；
  - child proof CPU；
  - completion-bound retry risk；
  - child tree width/balance。

## 不建议做的事

- 不建议直接把 RouteOpt 接进来求我们的 random-TW logical graph。建模和 pricing 状态不一致，转换成本高，比较也不公平。
- 不建议复制 GPLv3 源码到当前 repo。
- 不建议把 RouteOpt 的 cut/branching 代码机械搬进 Python；应先抽象出 contract，再做小规模 proof-safe 原型。
- 不建议继续只扩大 replay overlay。V545 已经证明 replay path 有用，但覆盖太窄，不能解决大部分陌生 state。

## 建议下一步

### 短期：Branch Testing Controller

在现有 branch score 之前加一层受控的 `JourneyBranchTestingController`：

- 输入：当前 node 的 top candidates、score map、baseline pair。
- 输出：selected pair 和审计字段。
- 阶段：
  1. cheap screen：fractionality、support、width、score；
  2. short child LP/probe；
  3. 只对少数候选做更贵的 exact-ish child proof probe；
  4. 用多目标 score 选择 pair。

这比继续盲目找 strong positive 更可控。

### 中期：pricing-compatible cut audit

建立一条 cut feasibility line，优先研究 subset-row-like / rank-1-like cuts：

- 目标不是马上加速，而是确认它是否能安全提高 `z_RMP` / child LP bound。
- 如果 cut 能把 hard nodes 从 `z_RMP < UB` 推近 UB，收益会比 retry gate 更根本。

### 中期：Node Snapshot / Replay 加速

把 RouteOpt 的 node restoration 思想迁移到我们的数据采集：

- 减少 full replay/child probe 重复初始化时间；
- 更快采集反事实 branch labels；
- 保持 exact-safe，只做状态恢复，不做剪枝捷径。

## 总判断

RouteOpt 对当前主线有参考价值，而且方向和我们最近结论一致：真正的加速要靠 branch candidate testing、cuts/formulation、列池/节点管理，而不是继续把 proof tail 当成单一 GAT 找列问题。

当前最应该借鉴 RouteOpt 的是：

1. BKF/3PB 式的受控分支候选测试；
2. Rank-1 / subset-row / limited-memory cut 的 pricing-compatible 设计；
3. DeLuxing 和 node restoration 的工程思想。

这三项都要保持我们的 exact-safe 边界：学习和启发式只排序、调度、选择测试对象；official bound、certificate、fathom 仍只来自合法 RMP + exact pricing closure。
