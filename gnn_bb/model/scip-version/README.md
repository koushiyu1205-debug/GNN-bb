# SCIP 严格分支定价版 CVRPTW 模型

这个版本只保留严格分支定价这一条求解路径，不再保留根节点列生成路径池或静态枚举路径池模式。

整体流程是：

1. 生成可复现实例，包括地形点、地形边、任务点和车辆参数。
2. 在底层地形图上计算基地与任务点之间的最短路闭包。
3. 用单任务路径和 Phase-I 人工列初始化主问题，避免根节点 restricted master 因列不足直接不可行。
4. SCIP 在分支定界过程中调用 Pricer。
5. 如果某个节点的 restricted master LP 仍不可行，Pricer 用 Farkas pricing 搜索能恢复可行性的路径列。
6. 如果 LP 可行，Pricer 用 reduced cost pricing 搜索负 reduced cost 的路径-槽位列。
7. Pricing 子问题使用资源约束最短路标签算法搜索所有资源可行 elementary sortie 路径。
8. Pricing 找到第一条能加列的真实路径后立即返回 SCIP，下一轮 LP 需要时会继续调用 Pricer。
9. 标签搜索使用 parent pointer 保存路径，只在真正准备加列或输出时回溯完整路径。
10. 标签搜索使用保守的安全 dominance，只剪掉当前位置和已访问任务集合完全相同且资源与成本都不更优的标签。
11. 当 SCIP 返回 `OPTIMAL`、没有触发时间/节点/gap 限制，并且没有使用人工列时，得到完整路径列集合意义下的整数最优解。
12. 输出解、生成列、校验结果，并可选画图。

## 目录结构

```text
main.py                 主入口：串联实例、地形闭包、分支定价求解、校验和输出
src/branch_price.py     严格分支定价实现，包含 SCIP Pricer 和 pricing 标签算法
src/route_generation.py 路径可行性评估工具，用于初始化单任务路径
src/instance_data.py    生成 very_small 和 medium 测试实例
src/terrain.py          构建地形图并计算最短路闭包
src/validation.py       校验求解结果
src/plotting.py         使用 matplotlib 输出路径图
src/io_utils.py         JSON、路径、日志等通用工具
```

## 运行

```bash
cd /home/kai/work/gnn_bb/model/scip-version
python3.12 main.py --instance very_small --time-limit 30
python3.12 main.py --instance medium --time-limit 3600
python3.12 main.py --instance 30 --time-limit 3600
python3.12 main.py --instance 40 --time-limit 3600
python3.12 main.py --instance 50 --time-limit 3600
python3.12 main.py --instance 100 --time-limit 3600
```

如果不显式传入 `--time-limit`，默认时间限制也是 3600 秒。

生成路径图：

```bash
python3.12 main.py --instance very_small --time-limit 3600 --plot
```

30、40、50、100 规模入口分别表示任务点数量。这些入口不再用载重人为规定每条 sortie 最多服务几个任务；`Q` 给得足够大，路径长度主要由时间窗、单车时间域、地形行驶时间和电池能耗自然限制。算法本身没有使用固定路径池截断。

静默 SCIP 日志：

```bash
python3.12 main.py --instance medium --time-limit 3600 --quiet
```

输出默认写到 `outputs/`：

- `instance_<name>.json`：实例数据
- `routes_<name>.json`：分支定价过程中实际生成出的路径列
- `solution_<name>.json`：SCIP 求解结果和校验结果
- `task_routes_<name>.png`：任务层路径图（使用 `--plot` 时生成）
- `terrain_routes_<name>.png`：底层地形路径图（使用 `--plot` 时生成）

## 最优性说明

本版本没有使用固定路径池截断。严格模式下，Pricer 会在 SCIP 的分支定界节点内继续生成 Farkas 可行性列和负 reduced cost 列。

主问题中加入了 Phase-I 人工覆盖变量 `u_k`，它只用于让 restricted master 初始可行。最终结果必须满足：

```text
sum_k u_k = 0
```

如果输出中 `summary.uses_artificial = true`，说明仍有任务由人工列覆盖，该解不能视为原问题可行解。

因此，当输出满足：

```text
summary.status = OPTIMAL
```

并且没有触发：

```text
TIME_LIMIT
NODE_LIMIT
GAP_LIMIT
```

同时满足：

```text
summary.uses_artificial = false
```

则该解是完整可行路径集合意义下的整数最优解。

## 分支定价数学形式

集合：

```text
K = 任务集合
R = 车辆集合
S = 每辆车的架次槽位集合
P = 所有资源可行 elementary sortie 路径集合
```

路径参数：

```text
c_p      = 路径 p 的运行成本
gamma_p  = 路径 p 的车辆周期占用时间
a_{k,p}  = 若路径 p 服务任务 k，则为 1，否则为 0
F        = 启用一辆车的固定成本
H        = 单车时间域
```

决策变量：

```text
x_{p,r,s} in {0,1}  路径 p 是否分配给车辆 r 的架次 s
z_{r,s}   in {0,1}  车辆 r 的架次 s 是否启用
y_r       in {0,1}  车辆 r 是否启用
u_k       in {0,1}  Phase-I 人工覆盖变量，最终必须为 0
```

完整主问题：

```text
min  F sum_r y_r + sum_p sum_r sum_s c_p x_{p,r,s}

s.t. sum_p sum_r sum_s a_{k,p} x_{p,r,s} = 1,       forall k in K
     sum_p x_{p,r,s} - z_{r,s} = 0,                  forall r in R, s in S
     z_{r,s} <= y_r,                                 forall r in R, s in S
     sum_p sum_s gamma_p x_{p,r,s} <= H y_r,         forall r in R
     z_{r,s+1} <= z_{r,s},                           forall r in R, s = 1,...,|S|-1
     y_{r+1} <= y_r,                                 forall r = 1,...,|R|-1
     x_{p,r,s}, z_{r,s}, y_r in {0,1}
```

代码里的 restricted master 为了 Phase-I 可行性实际使用：

```text
min  F sum_r y_r + sum_p sum_r sum_s c_p x_{p,r,s} + M sum_k u_k

s.t. sum_p sum_r sum_s a_{k,p} x_{p,r,s} + u_k = 1, forall k in K
     其余约束同上
     u_k in {0,1}
```

其中 `M` 是很大的人工惩罚。若最终 `u_k` 仍为 1，说明任务 `k` 没有被真实路径覆盖，输出会标记为校验失败。

每条路径 `p` 在 pricing 中必须满足：

```text
q_p <= Q
e_p <= B_use
return_p <= H
T_k + sigma_k <= D_k,  forall k in p
路径 p 不重复访问任务
```

在每个 SCIP LP 节点，Pricer 读取对偶价格：

```text
pi_k        = 任务覆盖约束对偶价格
alpha_{r,s} = 槽位约束对偶价格
beta_r      = 车辆总时间约束对偶价格
```

路径-槽位列的 reduced cost：

```text
rc(p,r,s) = c_p
          - sum_k a_{k,p} pi_k
          - alpha_{r,s}
          - gamma_p beta_r
```

如果：

```text
rc(p,r,s) < 0
```

则把对应列 `x_{p,r,s}` 加入 SCIP 当前节点。代码不会在一次 pricing 调用里攒完所有负列；找到第一条能加列的路径后就返回 SCIP。若 pricing 完整搜索后仍找不到负 reduced cost 列，则当前节点 LP 对完整列集合已经定价完成。

当 restricted master LP 不可行时，SCIP 调用 Farkas pricing。令 Farkas 对偶射线为：

```text
phi_k        = 任务覆盖约束的 Farkas 对偶值
eta_{r,s}    = 槽位约束的 Farkas 对偶值
theta_r      = 车辆总时间约束的 Farkas 对偶值
```

路径-槽位列的 Farkas 值：

```text
fv(p,r,s) = sum_k a_{k,p} phi_k
          + eta_{r,s}
          + gamma_p theta_r
```

如果：

```text
fv(p,r,s) > 0
```

则该列能破坏当前 restricted master 的不可行性证明，Pricer 会把它加入 SCIP。代码里为了和 reduced cost pricing 共用排序逻辑，实际判断的是：

```text
-fv(p,r,s) < 0
```

为了避免一次 pricing 生成过多路径列，代码采用早返回：

```text
找到第一条能加列的路径后立即返回 SCIP
```

这不是路径池截断，不影响严格性；因为如果 SCIP 还需要更多列，会继续调用 Pricer。只有当一次完整 pricing 搜索后仍找不到可加入列时，才说明当前节点没有可用列。

标签 dominance 使用保守条件。两个标签 `L1, L2` 只有在满足：

```text
当前位置相同
已访问任务集合完全相同
time(L1)   <= time(L2)
load(L1)   <= load(L2)
energy(L1) <= energy(L2)
cost(L1)   <= cost(L2)
```

时，才认为 `L1` 支配 `L2`。这种 dominance 不使用“已访问集合包含关系”，因此不会误删覆盖任务集合不同的候选路径。

标签内部不再保存完整 `physical_paths` 和完整 `service_start` 字典，而是保存：

```text
parent pointer
当前任务
当前任务服务开始时间
上一节点到当前任务的底层地形路径
```

只有当某个标签真的要生成列时，代码才沿 parent pointer 回溯完整路径。这样 pricing 过程中不会为每个中间标签复制整条路径对象。

cd /home/kai/work/gnn_bb/model/scip-version
python3.12 main.py --instance medium --plot

cd /home/kai/work/gnn_bb/model/scip-version
python3.12 main.py --instance medium --plot --no-warm-start

cd /home/kai/work/gnn_bb/model/scip-version
python3.12 main.py --instance 30 --time-limit 3600 --plot
