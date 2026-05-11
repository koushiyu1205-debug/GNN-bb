# 机器学习 + 分支定价设计文档

本文档对应当前项目的 Step 1：先审查现有模型，明确后续从纯 SCIP、分支定价到 2LBB 的改造路径。本文档不要求也不修改 `model/scip-version` 下的旧实现。

## 1. 当前问题和数据结构

当前问题可以理解为一个带地形网络的多车辆路径覆盖问题。底层地形图由节点坐标和无向边组成，边上有距离、时间、能耗和成本。任务点挂在某些地形节点上，每个任务有时间窗、服务时间、载重需求、服务能耗和服务成本。车辆有数量上限、每车 sortie 数量上限、载重容量、电池可用能量、充电/补能速率、固定启用成本和总工作时间上限。

求解前会先把底层地形图压缩成任务层完全有向图：

- 逻辑节点 `0` 表示基地；
- 逻辑节点 `i in N` 表示任务；
- 每条逻辑弧 `(i,j)` 的 `tau/energy/cost/path` 来自底层地形最短路。

因此后续 MILP、列生成和 pricing 都可以先在任务层图上工作，只有画图或解释路径时再回到底层地形路径。

## 2. 现有 legacy 代码审查

`model/scip-version` 当前已有一个 PySCIPOpt 版本的 route-column 模型：

- `main.py`：串联实例生成、闭包计算、求解、校验和画图。
- `src/branch_price.py`：注册 SCIP pricer，动态生成路径列。
- `src/terrain.py`：构建地形图和任务层闭包。
- `src/route_generation.py`：给定任务序列，检查时间、载重、能耗可行性并计算路径成本。
- `src/validation.py`：校验输出解是否覆盖所有任务且满足资源约束。

legacy 模型已经具备一些分支定价所需组件：

- RMP 变量：路径-车辆-sortie 列 `x[p,r,s]`，车辆启用变量 `y[r]`，sortie 启用变量 `z[r,s]`；
- 主约束：任务覆盖、slot 使用、车辆总 cycle time、车辆/sortie 顺序；
- pricing：elementary resource constrained shortest path；
- Farkas pricing：RMP 初始不可行时补列；
- Phase-I 人工列：保证 restricted master 初始可行；
- warm start：用贪心插入生成初始真实列。

但它还不是论文意义上的完整 branch-and-price / branch-price-and-cut 框架，主要缺口是：

- 分支由 SCIP 默认变量 branching 处理，没有显式的 problem-specific arc/edge branching；
- branching 约束没有作为状态传入 pricing；
- 没有 3PB 的 initial screening、LP testing、heuristic testing；
- 没有稳定的 branching candidate、特征、标签和测试日志。

因此后续 2LBB 不能直接套在当前 SCIP 默认分支上，必须先建立可审计的 B&P branching 框架。

## 3. 当前 compact MILP baseline

Step 2 先实现纯 SCIP baseline，不使用列生成。任务层 compact MILP 使用以下变量：

- `x[r,s,i,j] in {0,1}`：车辆 `r` 的 sortie `s` 是否走任务层弧 `(i,j)`；
- `z[r,s] in {0,1}`：sortie 是否启用；
- `y[r] in {0,1}`：车辆是否启用；
- `T[r,s,i] >= 0`：任务 `i` 的服务开始时间；
- `L[r,s,i] >= 0`：到达并完成任务 `i` 后的累计载重；
- `E[r,s,i] >= 0`：到达并完成任务 `i` 后的累计能耗；
- `RT[r,s] >= 0`：sortie 返回基地的时间；
- `RE[r,s] >= 0`：sortie 返回基地时的总能耗。

目标函数：

```math
\min
\sum_{r,s}\sum_{i\ne j} (c_{ij}+c^{srv}_j)x_{rsij}
+ \sum_r F y_r,
```

其中 `j=0` 时服务成本为 0。

核心约束：

```math
\sum_{r,s}\sum_{i\ne k} x_{rsik} = 1, \quad \forall k \in N
```

```math
\sum_{j\in N} x_{rs0j} = z_{rs},\quad
\sum_{i\in N} x_{rsi0} = z_{rs}
```

```math
\sum_{i\ne k} x_{rsik} = \sum_{j\ne k} x_{rskj},\quad
\forall r,s,k\in N
```

```math
T_{rsj} \ge T_{rsi} + \sigma_i + \tau_{ij} - M^T_{ij}(1-x_{rsij})
```

```math
L_{rsj} \ge L_{rsi} + d_j - M^L_j(1-x_{rsij})
```

```math
E_{rsj} \ge E_{rsi} + e_{ij} + g_j - M^E_{ij}(1-x_{rsij})
```

并用类似约束处理 `0->j` 和 `i->0`。所有 Big-M 都由实例上界计算，例如时间窗上界、`H`、`Q`、`B_use` 和对应弧资源值，不使用任意超大常数。

车辆总工作时间约束：

```math
\sum_s \left(RT_{rs} + \frac{RE_{rs}}{\rho}\right) \le H y_r,\quad \forall r.
```

该 compact MILP 的目的不是替代后续分支定价，而是提供统一的 SCIP baseline 和小实例 correctness reference。

## 4. Dantzig-Wolfe / branch-and-price 分解

更自然的分解是 set-partitioning formulation。令 `P` 为所有资源可行 sortie 路径集合，每条路径 `p` 是从基地出发、访问若干任务、返回基地的 elementary route。

主问题变量：

```math
\lambda_{prs}\in\{0,1\}
```

表示车辆 `r` 的 sortie `s` 选择路径 `p`。

RMP：

```math
\min
\sum_{p,r,s} c_p\lambda_{prs} + \sum_r F y_r
```

```math
\sum_{p,r,s: i\in p}\lambda_{prs}=1,\quad \forall i\in N
```

```math
\sum_p\lambda_{prs}=z_{rs},\quad \forall r,s
```

```math
\sum_{p,s}\gamma_p\lambda_{prs}\le H y_r,\quad \forall r
```

其中 `c_p` 是路径成本，`\gamma_p=return_time_p+energy_p/\rho`。

pricing 子问题是 elementary resource constrained shortest path：

```math
\bar c_{prs}(p)
= c_p
- \sum_{i\in p}\pi_i
- \alpha_{rs}
- \beta_r\gamma_p.
```

若存在 `\bar c < 0` 的路径，则加入 RMP。声明某个节点 LP 完成前，必须执行 exact pricing；启发式 pricing 或 ML pricing 只能提前找列，不能用于证明无负 reduced-cost 列。

初始可行性：

- 单任务可行路径；
- 贪心 warm start 路径；
- Phase-I 人工覆盖列，目标惩罚足够大，只用于保证 RMP 可行。

## 5. 分支策略和 3PB/2LBB 映射

论文中的 2LBB 建立在 arc/edge branching 和 3PB 之上。对本项目，branching candidate 可以定义为任务层有向弧 `(i,j)` 的当前 LP 流量：

```math
f_{ij}=\sum_{p,r,s:(i,j)\in p}\lambda_{prs}.
```

当 `f_ij` 分数时生成左右子节点：

- 左子节点：禁止该弧，`f_ij <= floor(f_ij)`；常见二元弧流场景下为 `f_ij=0`；
- 右子节点：强制该弧，`f_ij >= ceil(f_ij)`；常见二元弧流场景下为 `f_ij=1`。

pricing 必须读取节点 branching state：

- 禁用弧不能扩展；
- 强制弧需要通过分支约束系数进入 RMP，并在 pricing 的 reduced cost 中计入对应 dual；
- 若 arc-flow 已整数但 RMP 列变量仍分数，使用 column-fixing 或 Ryan-Foster 类 fallback branching，保证搜索完整。

3PB without ML baseline：

1. 初筛：候选分为已有 pseudocost 与无 pseudocost 两组；前者按 pseudocost，后者按 fractionality；
2. LP testing：对候选左右子节点解 starting child LP，不做 CG；
3. heuristic testing：对少数候选做有限 CG 或 heuristic pricing；
4. 选择 score 最好的候选正式分支。

2LBB with ML：

- M1 在 LP testing 前用便宜特征 `FI + FD` 缩小候选；
- M2 在 LP testing 后用 `FE` 相关特征判断哪些 starting child LP 需要 partial testing；
- BKF 动态调整进入关键 testing 阶段的候选数；
- 若模型缺失、schema 不匹配、置信度低或候选为空，回退到 3PB。

ML 不允许：

- 删除必要列；
- 跳过 exact pricing fallback；
- 直接剪枝节点；
- 声明 lower bound / upper bound；
- 让 branching 子节点不覆盖完整解空间。

## 6. 后续仓库结构

新增代码位于仓库根目录：

```text
configs/
docs/
json/instances/
results/
scripts/
src/gnn_bb/
tests/
```

`model/scip-version` 保留为 legacy reference，不在 Step 1/2 中修改。

## 7. 论文对实现顺序的影响

论文强调 2LBB 的收益来自减少 branching candidate testing 成本，而不是改变 pricing 的正确性。因此后续实现顺序应为：

1. pure SCIP compact MILP baseline；
2. 显式 RMP/pricing/tree 的 no-ML branch-and-price；
3. 3PB branching baseline；
4. ML 数据采集；
5. M1/M2 训练；
6. 2LBB 在线集成；
7. BKF dynamic K；
8. 实验与 ablation。

