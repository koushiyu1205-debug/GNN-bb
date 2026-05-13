# GNN_BB 项目进度与运行命令

本文档记录根目录新实现的优化实验框架。后续每次新增功能、脚本或实验结果，都应同步更新本文档。

注意：`model/scip-version/` 是旧版参考实现，本轮新增代码不修改该目录。当前根目录主线已在 legacy route-slot 分支定价基础上进一步改成 route-vehicle master，用于降低 slot 对称性。

## 1. 当前进度

已完成：

- Step 1：完成模型审查和设计文档。
  - 文档：`docs/ml_branch_price_design.md`
  - 内容包括当前问题结构、legacy 代码审查、compact MILP baseline、Dantzig-Wolfe 分解、branch-and-price 设计、3PB/2LBB 映射。

- Step 2：实现纯 SCIP compact MILP baseline。
  - 代码：`src/gnn_bb/baseline/scip_milp.py`
  - 入口：`scripts/run_scip_baseline.py`
  - 配置：`configs/scip_baseline.yaml`
  - 输出：`results/scip_baseline.csv`

- Step 3：实现 no-ML branch-and-price baseline。
  - 当前主线代码：`src/gnn_bb/bp/route_slot_branch_price.py`
  - 当前主线架构：route-vehicle master + SCIP 原生 Pricer + Farkas pricing + warm start
  - 入口：`scripts/run_bp_no_ml.py`
  - 配置：`configs/bp_no_ml.yaml`
  - 输出：`results/bp_no_ml.csv`
  - 保留实验代码：`src/gnn_bb/bp/schedule_branch_price.py`

尚未完成：

- 3PB without ML：pseudocost/fractionality 初筛、LP testing、heuristic/partial testing。
- ML 数据采集。
- M1/M2 learning-to-branch。
- 2LBB 在线集成。
- dynamic K / BKF。
- 完整 3600s 对比实验表。

## 2. 目录结构

```text
configs/                 配置文件
docs/                    设计文档和后续实验报告
json/instances/          实例 JSON
results/                 CSV、日志、解文件
scripts/                 命令行入口
src/gnn_bb/              新实现代码
tests/                   单元测试
model/scip-version/      legacy 参考实现，不在新框架中直接修改
```

## 3. Python 环境

默认使用 `ecole` conda 环境：

```bash
/home/kai/miniconda3/envs/ecole/bin/python
```

所有命令都从仓库根目录执行：

```bash
cd /home/kai/work/gnn_bb
```

## 4. 运行命令

### 4.1 单元测试

```bash
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests/test_data_and_baseline.py tests/test_bp_no_ml.py
```

当前期望结果：

```text
Ran 20 tests ... OK
```

### 4.2 纯 SCIP compact MILP baseline

运行 very_small：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_scip_baseline.py --instances very_small --time-limit 3600
```

运行 20 任务规模，即 `medium`：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_scip_baseline.py --instances medium --time-limit 3600
```

运行多个实例：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_scip_baseline.py --instances very_small medium 30 --time-limit 3600
```

隐藏 SCIP 控制台日志：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_scip_baseline.py --instances medium --time-limit 3600 --quiet
```

输出文件：

```text
results/scip_baseline.csv
results/logs/scip_baseline/<instance>.log
json/instances/instance_<instance>.json
```

说明：该 baseline 是 compact MILP，20 规模会比 `model/scip-version` 的列生成版本更难求解，这是预期现象。

### 4.2.1 规模实例参数策略

`medium`、`30`、`40`、`50`、`100` 等规模实例使用 `medium_like_scaled_v1` 参数配置。根目录加载实例时会自动应用这个配置，现有 JSON 也已经同步更新。

固定车辆物理参数：

```text
Q=9.0, B_max=50.0, B_surv=10.0, B_use=40.0,
rho=5.0, F=100.0, H=240.0
```

车队规模自动生成。`S_bar` 不再是固定常数，而是由车辆总工作时间 `H` 和最短单任务 sortie 的 cycle time 决定：

```text
single_task_cycle_i = return_time_i + energy_i / rho
S_bar = floor(H / min_i single_task_cycle_i)
```

`R_bar` 不再用手工比例给定，而是把每个任务的单任务 sortie cycle time 按 first-fit decreasing 装箱到车辆工作时间 `H` 中得到一个可复现上界：

```text
R_bar = first_fit_decreasing(single_task_cycle_times, H, S_bar)
```

当前自动计算结果：

```text
20规模 medium: R_bar=3,  S_bar=17
30规模:        R_bar=4,  S_bar=21
40规模:        R_bar=5,  S_bar=26
50规模:        R_bar=7,  S_bar=23
100规模:       R_bar=24, S_bar=24
```

统一任务服务和需求公式：

```text
r_i     = 2 * (i mod 5)
D_i     = 40 + 8.5 i
sigma_i = 2 + (i mod 3)
d_i     = 1 + (i mod 3)
g_i     = 0.8 + 0.08 * (i mod 5)
c_srv_i = 1.5 + 0.12 i
```

保留差异：

```text
不同规模保留任务数量和地形位置差异
```

也就是说，现在不同规模的主要差异是任务数量和地形位置，不再混入手工调整的车辆物理能力、载重需求和服务参数。`S_bar/R_bar` 仍然会随实例资源自然变化，但由固定公式生成，不手动调参。

注意：`S_bar` 自动变大后，如果继续使用旧 route-slot master，会产生大量 slot 对称列。因此当前主线已经改成 route-vehicle master，`S_bar` 只作为每车 sortie 数上界，不再复制 slot 列。

### 4.3 no-ML branch-and-price baseline

当前 no-ML B&P 主线使用 route-vehicle 原生 SCIP Pricer 架构。它保留 legacy 的 RCSP pricing、Farkas pricing 和 warm start，但去掉了 slot 维度：

```text
lambda[p,r] = 1 表示车辆 r 执行 route p
y[r]        = 1 表示车辆 r 被启用
u[i]        = 1 表示 Phase-I 人工覆盖任务 i
```

集合和参数：

```text
N      任务集合
R      车辆集合
P      所有资源可行 route 集合
a_ip   route p 是否服务任务 i
c_p    route p 的行驶 + 服务成本
gamma_p = cycle_time(p)
F      固定车辆成本
H      单车总工作时间上界
S_bar  单车最多 sortie 数上界
M      Phase-I 人工覆盖大惩罚
```

目标函数：

```text
min  sum_{r in R} sum_{p in P} c_p lambda[p,r]
   + F sum_{r in R} y[r]
   + M sum_{i in N} u[i]
```

约束：

```text
sum_{r in R} sum_{p in P} a_ip lambda[p,r] + u[i] = 1
    for all i in N

sum_{p in P} lambda[p,r] <= S_bar y[r]
    for all r in R

sum_{p in P} gamma_p lambda[p,r] <= H y[r]
    for all r in R

y[r+1] <= y[r]
    for r = 1,...,R_bar-1

lambda[p,r] in {0,1}, y[r] in {0,1}, u[i] in {0,1}
```

pricing 是每个 route 的资源约束最短路。若 `pi_i` 是任务覆盖约束对偶，`eta_r` 是车辆 sortie 数约束对偶，`beta_r` 是车辆总工作时间约束对偶，则 route-vehicle 列的 reduced cost 为：

```text
rc(p,r) = c_p
        - sum_{i in N} a_ip pi_i
        - eta_r
        - beta_r gamma_p
```

SCIP 调用 `pricerredcost` 时找负 reduced-cost 路径-车辆列；RMP 不可行时调用 `pricerfarkas` 做 Farkas pricing。pricing 标签使用 parent pointer，避免在搜索过程中复制完整路径。

运行 very_small：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bp_no_ml.py --instances very_small --time-limit 3600
```

运行 20 任务规模，即 `medium`：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bp_no_ml.py --instances medium --time-limit 3600 --memory-limit-mb 12000
```

运行 30 任务规模：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bp_no_ml.py --instances 30 --time-limit 3600 --memory-limit-mb 12000
```

限制搜索节点数，用于 smoke test：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bp_no_ml.py \
  --instances medium \
  --time-limit 300 \
  --max-nodes 1000 \
  --memory-limit-mb 12000 \
  --results-csv results/smoke/bp_route_vehicle_medium.csv \
  --log-dir results/smoke/logs/bp_route_vehicle \
  --solution-dir results/smoke/solutions/bp_route_vehicle
```

只写结果、不打印 SCIP 过程日志：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bp_no_ml.py --instances medium --time-limit 3600 --quiet
```

输出文件：

```text
results/bp_no_ml.csv
results/logs/bp_no_ml/<instance>.log
results/solutions/bp_no_ml/solution_<instance>.json
```

注意：当前 `results/logs/bp_no_ml/<instance>.log` 是 JSON 摘要，不是逐行 SCIP 文本日志。逐行 SCIP 进度直接输出在终端；需要留存时可以使用 shell 重定向，例如：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bp_no_ml.py --instances medium --time-limit 3600 --memory-limit-mb 12000 \
  > results/logs/bp_no_ml/medium_terminal.log 2>&1
```

### 4.3.1 最小 route-vehicle branch-price-and-cut

为保留当前 4 秒级 route-vehicle baseline，BPC 版本新建为独立文件，不覆盖原主线：

```text
src/gnn_bb/bp/schedule_checker.py
src/gnn_bb/bp/route_vehicle_bpc.py
scripts/run_route_vehicle_bpc.py
```

这个最小 BPC 版本仍以单条 sortie route 作为列，但增加一个 exact schedule checker。若某辆车选中的 route 集合无法排成真实执行顺序，就加入安全的 no-good cut。当前实现已经接入 SCIP 树内 lazy constraint handler；外层 cut-and-resolve 只作为兼容性保护保留。

集合和参数：

```text
N        任务集合
R        车辆集合
P        所有资源可行 sortie route 集合
a_ip     route p 是否服务任务 i
c_p      route p 的行驶 + 服务成本
w_p      route p 至少占用的车辆工作时间下界
F        固定车辆成本
H        单车总工作时间上界
S_bar    单车最多 sortie 数上界
M        Phase-I 人工覆盖大惩罚
C        已分离出的 schedule infeasible route-set cuts
P(C)     cut C 中禁止同车同时选择的 route 集合
```

变量：

```text
lambda[p,r] ∈ {0,1}   车辆 r 是否执行 route p
y[r]        ∈ {0,1}   车辆 r 是否启用
u[i]        ∈ {0,1}   Phase-I 人工覆盖任务 i
```

目标函数：

```text
min  sum_{r in R} sum_{p in P} c_p lambda[p,r]
   + F sum_{r in R} y[r]
   + M sum_{i in N} u[i]
```

基础 master 约束：

```text
sum_{r in R} sum_{p in P} a_ip lambda[p,r] + u[i] = 1
    for all i in N

sum_{p in P} lambda[p,r] <= S_bar y[r]
    for all r in R

sum_{p in P} w_p lambda[p,r] <= H y[r]
    for all r in R

y[r+1] <= y[r]
    for r = 1,...,R_bar-1
```

BPC schedule cuts：

```text
sum_{p in P(C)} lambda[p,r] <= |P(C)| - 1
    for all C in C, for all r in R
```

这类 cut 的含义是：如果 exact schedule checker 证明某个 route 集合 `P(C)` 无法按任意顺序在时间窗、电量、充电/恢复时间和 horizon 内完成，则该集合不能被任何一辆同质车同时选中。车辆同质时，这个全局 cut 比按车辆单独加 cut 更强，而且不改变可行域。

pricing reduced cost。设 `pi_i` 是任务覆盖约束对偶，`eta_r` 是 sortie 数约束对偶，`beta_r` 是车辆工作时间约束对偶，`gamma_C` 是 schedule cut 对偶，则：

```text
rc(p,r) = c_p
        - sum_{i in N} a_ip pi_i
        - eta_r
        - beta_r w_p
        - sum_{C in C: p in P(C)} gamma_{C,r}
```

exactness 说明：

```text
1. pricing 仍是 RCSP/Farkas pricing；新列会自动带上 schedule cut 系数。
2. cut 只在 exact schedule checker 证明 route 集合不可排程时加入。
3. 只有最后一次选中 route 集合通过 exact schedule checker，才输出 schedule-feasible primal。
4. 存在 schedule cut duals 时，dominance key 会加入当前 route 前缀序列；只有同签名前缀标签才比较，避免漏列。
5. ML 尚未介入；没有删列、漏列、误剪枝。
6. 树内 lazy handler 只影响整数候选解和 valid cuts，不用 ML、不误剪枝；当前默认关闭，作为实验选项保留。
```

运行 very_small：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_route_vehicle_bpc.py \
  --instances very_small \
  --time-limit 3600 \
  --memory-limit-mb 12000
```

运行 20 任务规模：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_route_vehicle_bpc.py \
  --instances medium \
  --time-limit 3600 \
  --memory-limit-mb 12000 \
  --max-cut-rounds 20 \
  --pricing-time-budget 20 \
  --pricing-progress-interval 200000 \
  --results-csv results/bpc_no_ml_medium.csv \
  --log-dir results/logs/bpc_no_ml \
  --solution-dir results/solutions/bpc_no_ml
```

启用树内 lazy cuts 做实验对照：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_route_vehicle_bpc.py \
  --instances medium \
  --time-limit 3600 \
  --memory-limit-mb 12000 \
  --max-cut-rounds 20 \
  --enable-tree-cuts \
  --pricing-time-budget 20 \
  --pricing-progress-interval 200000 \
  --results-csv results/bpc_no_ml_medium_tree.csv \
  --log-dir results/logs/bpc_no_ml_tree \
  --solution-dir results/solutions/bpc_no_ml_tree
```

运行 30 任务规模：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_route_vehicle_bpc.py \
  --instances 30 \
  --time-limit 3600 \
  --memory-limit-mb 12000 \
  --max-cut-rounds 20 \
  --results-csv results/bpc_no_ml_30.csv \
  --log-dir results/logs/bpc_no_ml \
  --solution-dir results/solutions/bpc_no_ml
```

当前短测结果：

```text
very_small, pricing_time_budget=5, time_limit=30s:
status=OPTIMAL
primal=132.270984
dual=132.270984
gap=0.0
time=0.082337s
cut_rounds=1
generated_columns=14
schedule_feasible_start.submitted=true

medium, default outer global cuts, time_limit=60s, max_cut_rounds=3, pricing_time_budget=20:
status=CUT_ROUND_LIMIT
primal=None
dual=524.340684
gap=None
time=57.075243s
cut_rounds=3
schedule_cuts_added=6
generated_columns=821
pricing_calls=558
pricing_label_pops=1077211
schedule_feasible_start.submitted=true
schedule_feasible_solution=false

medium, pricing_time_budget=0.000001:
status=PRICING_TIME_BUDGET
primal=743.688845
dual=None
gap=None
strict_pricing=false
```

解释：当前默认 BPC 使用外层全局 cuts，能稳定返回；schedule-aware start 能提交真实可排程 incumbent；pricing budget 超时时会安全中断并清空 dual/gap。树内 lazy cuts 已实现，但 20 规模短测不稳定，暂时作为实验开关保留。

### 4.3.2 根目录 `bpc/` clean BPC 主线

新增根目录独立实现：

```text
bpc/
scripts/run_bpc_clean.py
configs/bpc_clean.yaml
docs/bpc_clean_formulation.md
```

这个版本用于验收“规范、完整、可审查”的 BPC 流程。它不调用旧 `src/gnn_bb/bp/` 的 BPC 主入口，不使用 SCIP 默认 B&B 树，也不使用 outer cut-and-resolve、SCIP lazy handler、column pool、stabilized pricing、reduced graph pricing、ng relaxation 或 ML。SCIP 只负责求解每个节点的 RMP LP 并返回 dual；节点循环、pricing、cuts、branching、incumbent 校验和 bound 证明由 `bpc/` 自己控制。

clean BPC 的硬规则：

```text
1. Phase-I 人工列保证 RMP 初始可行。
2. reduced cost 使用当前 RMP true dual。
3. exact pricing 完整结束后，节点 bound 才能用于剪枝或证明。
4. schedule no-good cut 只在 exact schedule checker 证明不可排程后加入。
5. integer incumbent 必须通过原问题 schedule feasibility 检查。
6. pricing 若被中断，该节点不能声明完成。
```

运行 very_small：

```bash
cd /home/kai/work/gnn_bb

/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_clean.py \
  --instances very_small \
  --time-limit 3600 \
  --results-csv results/bpc_clean_very_small.csv \
  --log-dir results/logs/bpc_clean \
  --solution-dir results/solutions/bpc_clean
```

运行 20 任务规模：

```bash
cd /home/kai/work/gnn_bb
mkdir -p results/logs/bpc_clean_terminal

/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_clean.py \
  --instances medium \
  --time-limit 3600 \
  --config configs/bpc_clean.yaml \
  --results-csv results/bpc_clean_medium.csv \
  --log-dir results/logs/bpc_clean \
  --solution-dir results/solutions/bpc_clean \
  2>&1 | tee results/logs/bpc_clean_terminal/medium_terminal.log
```

输出文件：

```text
results/bpc_clean_<instance>.csv
results/logs/bpc_clean/<instance>.jsonl
results/solutions/bpc_clean/solution_<instance>.json
```

数学与证明文档：

```text
docs/bpc_clean_formulation.md
docs/bpc_clean_optimality_proof.md
docs/bpc_clean_equivalence_proof.md
```

说明：clean BPC 第一版优先保证流程和证明逻辑清楚，不承诺比旧 route-vehicle pricer 更快。性能优化必须在这个版本的日志能够解释 root、pricing、cut、branching 行为之后再逐项加入。

### 4.4 真实 vehicle schedule column master

为保留当前 route-vehicle baseline，新增了独立文件：

```text
src/gnn_bb/bp/vehicle_schedule_branch_price.py
scripts/run_schedule_bp.py
```

该模型的列是一辆车的完整日程，不是单条 route：

```text
schedule k = (route_1, route_2, ..., route_m)
```

其中每条 route 是一次 sortie。第 `q+1` 条 sortie 的出发时间必须不早于第 `q` 条 sortie 返回并完成能耗折算之后：

```text
start_{q+1} >= return_q + energy_q / rho
```

日程列必须满足：

```text
m <= S_bar
final_ready_time <= H
每条 sortie 单独满足 Q、B_use、任务时间窗、服务时间
同一 schedule 内任务不重复
```

Master 变量：

```text
theta[k] = 1 表示选择车辆日程 k
u[i]     = 1 表示 Phase-I 人工覆盖任务 i
```

目标函数：

```text
min  sum_{k in K} C_k theta[k] + M sum_{i in N} u[i]
```

其中：

```text
C_k = F + sum_{route q in schedule k} cost_q
```

约束：

```text
sum_{k in K} a_ik theta[k] + u[i] = 1
    for all i in N

sum_{k in K} theta[k] <= R_bar

theta[k] in {0,1}, u[i] in {0,1}
```

pricing reduced cost：

```text
rc(k) = C_k - sum_{i in N} a_ik pi_i - mu
```

其中 `pi_i` 是任务覆盖约束对偶，`mu` 是车辆数量约束对偶。

运行 very_small：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_schedule_bp.py --instances very_small --time-limit 3600
```

运行 20 任务规模：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_schedule_bp.py \
  --instances medium \
  --time-limit 3600 \
  --memory-limit-mb 12000 \
  --max-columns-per-pricing 20 \
  --column-pool-size 200 \
  --column-pool-rc-margin 50 \
  --stabilization-alpha 0.7 \
  --stabilization-label-limit 20000
```

带 Python pricer 单次回调时间预算运行 20 任务规模：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_schedule_bp.py \
  --instances medium \
  --time-limit 3600 \
  --memory-limit-mb 12000 \
  --max-columns-per-pricing 20 \
  --column-pool-size 200 \
  --column-pool-rc-margin 50 \
  --stabilization-alpha 0.7 \
  --stabilization-label-limit 20000 \
  --pricing-time-budget 30
```

短测 20 任务规模：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_schedule_bp.py \
  --instances medium \
  --time-limit 10 \
  --memory-limit-mb 12000 \
  --max-columns-per-pricing 20 \
  --column-pool-size 200 \
  --column-pool-rc-margin 50 \
  --stabilization-alpha 0.7 \
  --stabilization-label-limit 20000 \
  --quiet \
  --results-csv results/smoke/bp_schedule_medium_10.csv \
  --log-dir results/smoke/logs/bp_schedule_medium_10 \
  --solution-dir results/smoke/solutions/bp_schedule_medium_10
```

注意：Python pricer 的单次 DP 调用不能被 SCIP 时间限制中途打断，所以 schedule pricing 的实际运行时间可能略超过 `--time-limit`。

### 4.5 汇总结果表

汇总 SCIP baseline 和 no-ML B&P：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/collect_results.py \
  --inputs results/scip_baseline.csv results/bp_no_ml.csv \
  --output results/per_instance_results.csv
```

输出文件：

```text
results/per_instance_results.csv
```

## 5. 当前技术判断

- compact MILP baseline 用于和纯 SCIP 对比，不应和 B&P baseline 混在一起。
- route-vehicle 原生 SCIP Pricer 是当前更稳定的 no-ML B&P 主线，适合在此基础上实现 3PB / 2LBB。
- vehicle schedule column master 是真实 schedule-CVRPTW 建模分支，但 pricing 明显更难，不作为当前 3PB/2LBB baseline。
- 30 规模是已知风险：目前已把规模实例改成自动 scaling policy，后续仍需要针对 pricing、branching、stabilization 和 primal heuristic 单独优化。

当前 20 规模 route-vehicle smoke test：

```text
command=/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bp_no_ml.py --instances medium --time-limit 10 --memory-limit-mb 12000 --quiet
profile=medium_like_scaled_v1
R_bar=3
S_bar=17
status=OPTIMAL
primal=526.902419
dual=526.902419
gap=0.0
time=4.565085s
nodes=69
generated_routes=187
generated_columns=530
pricing_calls=233
```

当前 30 规模 route-vehicle smoke test：

```text
command=/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bp_no_ml.py --instances 30 --time-limit 60 --memory-limit-mb 12000 --quiet
profile=medium_like_scaled_v1
R_bar=4
S_bar=21
status=TIME_LIMIT
primal=495.91827
dual=None
nodes=1
generated_routes=528
generated_columns=1785
pricing_calls=499
warm_start_routes=7
```

结论：route-vehicle master 显著降低了 slot 复制。20 规模在动态 `S_bar=17` 下 4.6 秒证明最优；30 规模 60 秒内仍停在根节点 pricing，但列数已从旧 route-slot 临时测试的 13860 降到 1785。

当前真实 vehicle schedule column master 短测：

```text
very_small:
status=OPTIMAL
primal=132.270984
time=0.003454s
generated_columns=10

medium, 10s:
status=TIME_LIMIT
primal=690.973326
dual=None
nodes=1
generated_routes=108
generated_columns=127
pricing_calls=105
dominated_labels=229348

30, 10s:
status=TIME_LIMIT
primal=526.060316
dual=None
nodes=1
generated_routes=54
generated_columns=49
pricing_calls=17
dominated_labels=349463
```

对比结论：真实 schedule-CVRPTW 的列更少，但每次 pricing 要同时决定 sortie 顺序和绝对时间衔接，根节点更难完成 exact pricing。20 规模 route-vehicle 4.6 秒证明最优，而真实 schedule master 10 秒仍没有 dual bound。

当前 20 规模真实 schedule master 完整运行尝试：

```text
command=/home/kai/miniconda3/envs/ecole/bin/python scripts/run_schedule_bp.py --instances medium --time-limit 3600 --memory-limit-mb 12000 --quiet
status=INTERRUPTED
reason=运行约 9.5 分钟时 Python 进程 RSS 约 7.7GB，为避免 WSL 内存/磁盘风险主动中止
solver_runtime=641.428454s
primal=690.973326
dual=524.574877
gap=0.317206
nodes=1
generated_routes=212
generated_columns=620
pricing_calls=599
dominated_labels=6996881
output=results/bp_schedule_medium_full.csv
```

结论：20 规模真实 schedule master 目前仍不健康。它能产生有效 dual bound，但根节点 pricing 的 label 数量已经达到百万级，远慢于 route-vehicle baseline。

已完成的 schedule pricing 调整：

```text
每次 pricerredcost/pricerfarkas 最多返回 K 个负 reduced-cost schedule
默认 K=20，可通过 --max-columns-per-pricing 修改
若找到 K 个负 schedule，会立即返回给 SCIP 添加列
若没有返回负列，说明 schedule-labeling DP 已经穷尽，pricing 结论仍然是 exact
```

当前 top-K schedule pricing 短测：

```text
very_small, K=20, time_limit=10s:
status=OPTIMAL
primal=132.270984
dual=132.270984
time=0.006404s
generated_columns=12

medium, K=20, time_limit=60s:
status=TIME_LIMIT
primal=690.973326
dual=None
runtime=88.206502s
nodes=1
pricing_calls=51
generated_columns=1042
dominated_labels=734357
```

解释：K=20 后每次 pricing 会补更多列，pricing 调用次数从单列模式下降，但根节点仍没有完成 exact pricing，因此 60 秒短测还没有 dual bound。这个改动不改变 exactness；它只改变每次 SCIP pricing 调用补列的批量大小。

已完成的 label dominance 调整：

```text
open label 的 dominance key 从
  (covered, route_tasks, current_node, used_sorties)
放宽为
  (covered, current_node, used_sorties)

dominance 比较项包括：
  route_time
  route_load
  route_energy
  open_total_cost = closed_cost + current_route_cost
  return_ready_time = route_time + tau(current, depot) + return_energy / rho
```

安全性说明：两个 open label 的 `covered/current_node/used_sorties` 相同，且其中一个在时间、载重、能耗、返回基地 ready time 和成本上均不差，则被支配 label 的所有后续扩展都可以由支配 label 完成，因此不会漏掉必要列。

当前 dominance 短测：

```text
medium, K=20, time_limit=60s:
status=TIME_LIMIT
primal=690.973326
dual=None
runtime=82.059182s
nodes=1
pricing_calls=51
generated_columns=1042
dominated_labels=874041
```

对比 top-K 但未加强 dominance 的同样短测：

```text
runtime=88.206502s
dominated_labels=734357
```

结论：该 dominance 加强后，20 规模短测运行时间略降，内存峰值也明显下降；但根节点仍没有完成 exact pricing，后续主要瓶颈仍是 schedule-labeling 的状态空间。

已完成的 schedule column pool：

```text
每次 RMP 求解后，SCIP 调用 pricing 时：
1. 先扫描历史 column pool
2. 如果 pool 内已有 schedule 在当前 dual 下变成负 reduced-cost，直接加入 RMP 并返回
3. 如果 pool 没有负列，再调用昂贵的 schedule-labeling DP
```

内存控制策略：

```text
pool 只保存紧凑信息：schedule key、task_set、cost
不保存完整 physical path，不保存 SCIP 变量对象
默认 pool size = 200
只缓存 reduced cost <= 50 的接近负列候选
pool 满后只用更接近负 reduced-cost 的候选替换当前最差候选
如果 pool 没命中负列，仍然执行 exact pricing fallback，因此不影响 exactness
```

当前 column pool 短测：

```text
medium, K=20, pool_size=200, rc_margin=50, time_limit=60s:
status=TIME_LIMIT
primal=690.973326
dual=None
runtime=83.189655s
nodes=1
pricing_calls=59
generated_columns=1051
pool_scans=47
pool_hits=8
pool_columns_added=9
pool_size=200
dominated_labels=888675
```

对比结论：pool 没有改变 primal，也没有提供 dual bound；它主要减少了一部分昂贵 pricing 入口，但目前收益有限。较大的 pool size=1000 会降低中途内存峰值但总时间更不稳定；因此默认采用更保守的 200。

已完成的 heuristic stabilized pricing + exact fallback：

```text
redcost pricing 阶段：
1. 先扫描 column pool，若命中 true negative column，直接加入 RMP
2. 若 pool 没命中，使用 pi_stab 做 heuristic schedule-labeling pricing
3. pi_stab = alpha * pi_current + (1 - alpha) * pi_center
4. heuristic 阶段找到的列必须用 pi_current 重新计算 reduced cost
5. 只有 true negative columns 才能加入 RMP
6. heuristic 阶段找不到 true negative columns 时，必须用 pi_current 做 exact fallback
7. exact fallback 也找不到负列时，才证明当前 RMP LP pricing 完成
```

动态 alpha 规则：

```text
连续找到有效列：增大 alpha，让 pi_stab 更贴近 pi_current
多轮找不到列：减小 alpha，加强 dual stabilization
dual volatility 超过阈值：减小 alpha
进入 exact fallback 时：fallback 本身始终使用 pi_current
```

配置默认值：

```text
schedule_stabilized_pricing = true
schedule_stabilization_alpha = 0.7
schedule_stabilization_min_alpha = 0.2
schedule_stabilization_max_alpha = 0.95
schedule_stabilization_label_limit = 20000
schedule_stabilization_volatility_threshold = 0.25
```

当前 stabilized pricing 短测：

```text
medium, K=20, pool_size=200, rc_margin=50, alpha=0.7, label_limit=20000, time_limit=60s:
status=TIME_LIMIT
primal=536.504258
dual=None
runtime=120.983159s
nodes=1
pricing_calls=102
generated_columns=1431
pool_hits=28
pool_columns_added=94
stabilized_calls=74
stabilized_hits=46
stabilized_columns_added=755
stabilized_fallbacks=28
exact_fallback_calls=28
final_alpha=0.54
```

对比上一版 column pool：

```text
上一版 primal=690.973326, runtime=83.189655s
stabilized primal=536.504258, runtime=120.983159s
```

结论：stabilized pricing 明显改善 primal bound，说明它确实更快找到了有价值的 schedule 列；但由于 Python pricer 的 exact fallback 单次调用不能被 SCIP time limit 中断，实际短测时间超过 60 秒。若目标是严格控制墙钟时间，可以把 `--stabilization-label-limit` 降到 5000；短测中 5000 的 runtime 为 90.025340s，但 primal 没有改善，仍为 690.973326。

已完成的 pricing 前确定性预处理剪枝：

```text
新增模块：src/gnn_bb/bp/schedule_preprocessing.py

预处理内容：
1. 检查每个任务是否能 depot -> task_i -> depot 单独服务
2. 构建 G_task=(V,A)，删除确定不可能的 task_i -> task_j 弧
3. 预处理 depot -> i 是否可能作为 route 首任务
4. 预处理 i -> depot 是否可能作为 route 末任务
```

task-to-task 弧删除条件包括：

```text
time_feasible:
  earliest_finish_i_lb + tau_ij <= D_j - sigma_j

capacity_possible:
  d_i + d_j <= Q

energy_possible:
  min_energy_before_i_lb + g_i + e_ij + g_j + min_energy_after_j_lb <= B_use

precedence / same-route compatibility:
  source/target 的最早可服务完成时间不能违反自身时间窗和 horizon
```

DP 集成方式：

```text
closed label 开启新 sortie：只遍历 depot_to_task_feasible
open label 扩展任务：只遍历 G_task 当前节点的 successors
关闭 sortie 回 depot：先检查 task_to_depot_feasible
完整时间窗、载重、电量、horizon 检查仍保留在 DP 中
```

可关闭用于 ablation：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_schedule_bp.py \
  --instances medium \
  --time-limit 60 \
  --disable-pricing-preprocess
```

当前预处理统计：

```text
medium:
single_task_feasible=20
depot_to_task_feasible=20
task_to_depot_feasible=20
task_task_feasible_arcs=366 / 380
deleted_task_arc_reasons={'task_arc_energy': 14}

30/40/50:
当前实例参数较宽，静态预处理未删除 task-task arcs
```

当前预处理短测：

```text
medium, K=20, pool_size=200, alpha=0.7, label_limit=20000, time_limit=60s:
status=TIME_LIMIT
primal=536.504258
dual=None
runtime=124.785612s
pricing_calls=102
generated_columns=1431
stabilized_label_pops=904900
exact_label_pops=3994723
dominated_labels=1130030
```

对比上一版 stabilized pricing：

```text
上一版 runtime=120.983159s
上一版 primal=536.504258
预处理版 runtime=124.785612s
预处理版 primal=536.504258
```

结论：预处理代码已经正确接入，但在当前 medium 实例上只删除 14/380 条 task-task 弧，性能没有稳定改善。它对更紧时间窗、更紧电量或更大规模实例更可能有效；当前主要瓶颈仍是 exact fallback 的 Python label DP。

已完成的 Python pricer time budget + pricing 分阶段统计：

```text
新增参数：
  --pricing-time-budget <seconds>

配置项：
  schedule_pricing_time_budget_sec = 0.0

默认行为：
  0 表示关闭预算，不改变现有 baseline 可比性。

预算作用域：
  单次 Python pricer 回调共享一个墙钟 deadline。
  redcost 阶段顺序为 pool -> stabilized heuristic -> exact fallback。
  Farkas 阶段顺序为 pool -> Farkas exact pricing。

exactness 规则：
  如果 heuristic 阶段在预算内找到 true negative column，可以安全加入 RMP。
  如果 exact fallback 找到 negative column，即使未穷尽，也可以安全加入 RMP。
  如果 exact fallback 因预算耗尽且没有找到列，不能证明“无负列”。
  此时会中断 SCIP，并把输出状态改成 PRICING_TIME_BUDGET。
  同时 dual_bound 和 gap 置空，strict_pricing=false，避免把未验证 RMP 当成最优证明。
```

日志新增字段：

```text
pricing_time_budget
pricing_budget_interrupts
pricing_incomplete_due_to_budget
pricing_budget_incomplete_phase
pricing_phase_stats
```

`pricing_phase_stats` 当前包含：

```text
redcost_pool
stabilized_heuristic
exact_fallback
farkas_pool
farkas_exact
redcost_total
farkas_total
```

每个 phase 记录：

```text
calls
seconds
label_pops
columns_added
timeouts
exhausted
not_exhausted
```

当前验证：

```text
very_small, pricing_time_budget=1:
status=OPTIMAL
primal=132.270984
dual=132.270984
time=0.128816s
strict_pricing=true

medium, time_limit=10, pricing_time_budget=1:
status=TIME_LIMIT
primal=536.504258
dual=None
time=10.306494s
pricing_budget_interrupts=0

medium, pricing_time_budget=0.000001:
status=PRICING_TIME_BUDGET
primal=690.973326
dual=None
gap=None
strict_pricing=false
pricing_budget_incomplete_phase=exact_fallback
```

已撤回的实验：dynamic reduced-cost subgraph heuristic pricing。

撤回原因：

```text
思路：
  在 heuristic pricing 阶段只保留 reduced-cost proxy 较好的 depot->task 和 task->task 弧，
  先在动态子图上找负 reduced-cost schedule，再回退到 full exact pricing。

短测结果：
  medium, k_successor=6, k_depot=10:
    primal=690.973326
    runtime=88.327426s
    dynamic_subgraph_hits=60
    dynamic_subgraph_columns_added=989
    exact_label_pops=2847009

  当前 stabilized + preprocess baseline:
    primal=536.504258
    runtime=124.785612s
    exact_label_pops=3994723

判断：
  子图 heuristic 确实减少了 exact label 工作量，但找列质量明显变差。
  它找到很多 true negative columns，却没有优先找到改善 incumbent 的关键 schedule。
  这会污染 schedule baseline 的实验判断，所以不保留 CLI 开关和配置接口。
```

已撤回的实验：subgraph-stabilized pricing。

撤回原因：

```text
思路：
  把 stabilized heuristic pricing 从 full task graph 改成稳定对偶诱导的任务子图。
  子图保留低 reduced-cost 后继/前驱弧，并周期性执行 full stabilized pricing 刷新质量。
  exact fallback 仍然保留，因此理论上不破坏 exactness。

对比基准：
  当前 stabilized + preprocess + pricing_time_budget=1:
    status=TIME_LIMIT
    primal=536.504258
    runtime=10.306494s
    generated_columns=1006
    stabilized_columns_added=722
    pricing_budget_interrupts=0

默认子图参数：
  k_successor=6, k_predecessor=4, full_refresh_frequency=4:
    status=PRICING_TIME_BUDGET
    primal=690.973326
    runtime=5.025784s
    generated_columns=559
    subgraph_stabilized_columns_added=385
    pricing_budget_incomplete_phase=exact_fallback

更宽子图测试：
  k_successor=12, k_predecessor=8, full_refresh_frequency=1:
    status=PRICING_TIME_BUDGET
    primal=690.973326
    runtime=4.766828s

  k_successor=18, k_predecessor=18, full_refresh_frequency=1:
    status=PRICING_TIME_BUDGET
    primal=690.973326
    runtime=4.941207s

判断：
  子图稳定化减少了局部 label 工作量，但列质量不够，无法复现旧 stabilized pricing 早期找到的 536.50 incumbent。
  更宽子图和更频繁 full refresh 仍然触发 pricing budget，说明瓶颈不是单纯弧数量，而是 early columns 的质量和 exact fallback 时机。
  因此该实验不保留代码、配置或 CLI 开关。
```

待继续优化：

```text
1. two-level route->schedule 分解
2. 用 pricing_phase_stats 定位 exact fallback 的主要耗时来源
3. 对 exact fallback 做更强的安全 dominance / lower-bound pruning
```


## 6. 下一步计划

短期顺序：

1. 用 route-vehicle 原生 SCIP Pricer 跑 very_small 和 20 规模，确认改模后的目标值、时间、列数。
2. 对 30 规模做受控短测，记录它卡在 pricing、LP、branching 还是内存。
3. 在稳定 route-vehicle baseline 上实现 3PB：先做无 ML 的 candidate ranking 和 LP testing。
4. 记录 branching candidate 日志，为 2LBB 的 M1/M2 训练数据做准备。


## 7. Clean BPC 主线状态

当前新增的规范 BPC 主线在根目录 `bpc/` 下，旧 `src/gnn_bb/bp/` 保留为历史实验/reference。

当前 `bpc/` 模型正式定位为：

```text
route-vehicle BPC with schedule cuts
```

它不是 `vehicle-schedule BPC`。也就是说，master column 是单条 sortie route，不是一辆车完整日程；同一车辆多条 sortie 的真实先后顺序由 schedule checker 和 valid schedule no-good cuts 处理。

核心边界：

```text
SCIP 负责：
  - 每个节点的 RMP LP 求解
  - primal / dual 提取

Python BPC 负责：
  - node loop
  - column generation
  - exact RCSP pricing
  - schedule no-good cuts
  - Ryan-Foster / task-vehicle / arc-usage / vehicle-use branching
  - incumbent 校验
  - lower bound / upper bound / gap 逻辑
```

20 规模 clean BPC 测试命令：

```bash
cd /home/kai/work/gnn_bb
mkdir -p results/logs/bpc_clean_terminal

/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_clean.py \
  --instances medium \
  --time-limit 3600 \
  --config configs/bpc_clean.yaml \
  --results-csv results/bpc_clean_medium.csv \
  --log-dir results/logs/bpc_clean \
  --solution-dir results/solutions/bpc_clean \
  2>&1 | tee results/logs/bpc_clean_terminal/medium_terminal.log
```

当前 30 秒短测结果：

```text
上一版:
  status=TIME_LIMIT
  primal=743.688845
  dual=494.885971
  gap=0.334552
  nodes=149

当前 primal heuristic 加强后:
  status=TIME_LIMIT
  primal=626.902419
  dual=495.116564
  gap=0.210217
  nodes=85
```

当前判断：

```text
clean BPC 已经能按规范流程运行并输出结果；
primal heuristic 已把 20 规模 UB 从 743.69 改善到 626.90；
但 120 秒内 UB 不再改善，lower bound 平台仍明显。
下一步应优先做更强 branching / cuts，减少节点长期停在 494.89~501 的区间。
```

## 8. No-ML 3PB Branching Baseline

当前 clean BPC 已加入完整 no-ML 3PB branching baseline。它只负责选择分支候选，不负责剪枝、不证明节点最优，因此不破坏 exactness。

核心日志位置：

```text
results/logs/bpc_clean_30s_3pb/medium.jsonl
```

日志事件：

```text
branch_candidates  - 当前节点完整候选数、类型分布、筛选后的候选
branch_selection   - LP score、heuristic CG score、左右子节点测试结果、最终选择
```

当前 3PB workflow：

```text
1. Initial screening:
   有 pseudocost 的候选按 pseudocost 取 top theta_p；
   无 pseudocost 的候选按 fractionality 取 top theta_f。

2. LP testing:
   对 screened candidates 的左右 child 只解 restricted RMP LP；
   不做 column generation；
   按左右 bound improvement 计算 LP score；
   取 top theta_tilde。

3. Heuristic CG testing:
   对 top theta_tilde 全部做 limited child CG loop；
   每轮解 child RMP、limited pricing、把测试列加入局部 column set、重解 child RMP；
   测试列不加入全局 pool，测试结果不用于剪枝。
```

20 规模 30 秒短测命令：

```bash
cd /home/kai/work/gnn_bb
mkdir -p results/logs/bpc_clean_terminal

/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_clean.py \
  --instances medium \
  --time-limit 30 \
  --config configs/bpc_clean.yaml \
  --results-csv results/bpc_clean_medium_30s_3pb.csv \
  --log-dir results/logs/bpc_clean_30s_3pb \
  --solution-dir results/solutions/bpc_clean_30s_3pb \
  2>&1 | tee results/logs/bpc_clean_terminal/medium_30s_3pb_terminal.log
```

20 规模 3600 秒完整测试命令：

```bash
cd /home/kai/work/gnn_bb
mkdir -p results/logs/bpc_clean_terminal

/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_clean.py \
  --instances medium \
  --time-limit 3600 \
  --config configs/bpc_clean.yaml \
  --results-csv results/bpc_clean_medium_3pb.csv \
  --log-dir results/logs/bpc_clean_3pb \
  --solution-dir results/solutions/bpc_clean_3pb \
  2>&1 | tee results/logs/bpc_clean_terminal/medium_3pb_terminal.log
```

查看分支测试日志：

```bash
cd /home/kai/work/gnn_bb
rg -n '"event": "branch_candidates"|"event": "branch_selection"' \
  results/logs/bpc_clean_3pb/medium.jsonl
```

当前 20 规模 30 秒短测结果：

```text
status=TIME_LIMIT
primal=626.902419
dual=526.902419
gap=0.159514
nodes=17
rmp=39
pricing=25
branch_lp_test_rmp_solves=180
branch_heuristic_test_rmp_solves=76
branch_heuristic_test_pricing_calls=70
branch_testing_time=11.064354
routes=1000
cuts=12
```

备注：

```text
3PB 增加了分支测试开销，当前 CSV 已单独记录 branching testing 成本；
它的价值需要用 3600 秒完整结果比较 tree size、gap 和最终证明时间。
```

## 9. Robust RCI / RCC Cuts

当前 clean BPC 加入了保守的 robust Rounded Capacity Inequalities：

```text
x(delta(S)) >= 2 * ceil(d(S) / Q)
```

在 route-vehicle master 中用 route crossing coefficient 投影，不使用非鲁棒的 subset-row / route-count cut。

当前只在根节点枚举小任务子集，并带 inactive cut purging：

```yaml
robust_capacity_cuts_enabled: true
robust_capacity_cut_max_depth: 0
robust_capacity_cut_max_subset_size: 5
robust_capacity_cut_max_per_round: 20
cut_purge_age: 20
```

20 规模 30 秒短测中：

```text
robust_capacity_cuts_added=0
cuts_purged=0
```

说明当前实例在这个保守 separation 范围内没有明显 violated RCI；因此没有强行加割。

## 10. k-Path / Resource Lower Bound Cut

`bpc/` clean BPC 已加入严格的 k-path/resource lower bound cut：

```text
x(delta(S)) >= 2 * k(S)
k(S) = max(ceil(d(S)/Q), chi(G_S))
```

其中 \(G_S\) 是资源不兼容图：若两个任务不存在任何顺序的同 route 可行 sortie，则在图中连边。每条 route 在 \(S\) 上只能覆盖一个 independent set，所以覆盖 \(S\) 的 route 数至少是 \(\chi(G_S)\)。该 cut 仍使用 route crossing coefficient，是 robust cut，pricing 只需要处理 cut coefficient 和 cut dual。

详细证明和实现备注见：

```text
bpc/README.md
```

20 规模 30 秒短测结果：

```text
resource_lower_bound_cuts_added=0
```

这表示当前 conservative separation 范围内没有发现被 LP 解违反的严格资源下界 cut；代码不会为了“加割”而添加未违反或不可证明更强的 cut。

## 11. Task-Vehicle Linking

`bpc/` clean BPC 已加入有限 linking row：

```text
sum_{p in Omega} a[i,p] lambda[p,r] <= y[r]
    for all i in I, r in R
```

同时确认并修正文档说明：

```text
0 <= y[r] <= 1
```

pricing reduced cost 已同步加入 task-vehicle linking dual `xi[i,r]`：

```text
rc[p,r] -= sum_{i in p} xi[i,r]
```

20 规模 30 秒短测结果：

```text
results/20260512_112330_medium_3pb_task_vehicle_link_30s.csv

status=TIME_LIMIT
primal=627.942924
dual=492.686503
gap=0.215396
root_relaxation=490.283693
```

短测显示该约束没有改善当前 root relaxation，且 30 秒内 incumbent 变差；是否保留应以 3600 秒完整对比为准。

## 12. Root LP Fractional Diagnostic

新增根节点 fractional 结构诊断脚本：

```bash
cd /home/kai/work/gnn_bb
/home/kai/miniconda3/envs/ecole/bin/python scripts/diagnose_root_fractional.py \
  --instance medium \
  --config configs/bpc_clean.yaml \
  --subset-max-size 6 \
  --top 12
```

本次输出：

```text
results/root_diagnostics/20260512_113217_medium_root_fractional.json
```

核心结果：

```text
root objective = 490.283693
route pool size = 730
support route-vehicle variables = 19
fractional route-vehicle variables = 19
fractional Ryan-Foster pairs = 13
fractional arcs = 12
RCI violated count = 0
k-path/resource violated count = 0
```

判断：

```text
当前 root LP 的主要问题不是 capacity/resource subset cut violation，
而是 route pattern 在车辆和任务配对/弧结构上的 fractional mixing。
```

所以 RCI 和 k-path/resource cut 不起作用的直接原因是：当前 fractional 解已经满足这些 crossing 下界，没有 violated cut 可加。下一步更应优先加强 branching 或寻找 schedule-aware 的严格 valid inequalities。

## 13. Schedule Capacity Upper-Bound Cut

`bpc/` clean BPC 已加入 schedule-aware valid cut：

```text
z[i,r] = sum_p a[i,p] lambda[p,r]
sum_{i in S} z[i,r] <= U(S) y[r]
```

其中 `U(S)` 由 exact 单车多 sortie schedule oracle 计算；如果 oracle 超过状态上限，直接跳过，不加不确定 cut。

20 规模 30 秒短测：

```text
results/20260512_114949_medium_3pb_schedule_capacity_30s.csv

schedule_capacity_cuts_added=2
dual=491.291843
gap=0.217617
```

实际触发的 cut：

```text
S={1,2,4,5,8,12,13,14,15,16}
U(S)=9
vehicle=1 violation=0.446856637
vehicle=2 violation=0.340569913
```

这说明该 cut 能抓到 root fractional vehicle-task overload；短测中 root objective 尚未提升，下一步应改进 candidate separation，而不是继续扩大容量类 cut。

## 14. Enhanced Schedule Capacity Separation

已增强 schedule capacity cut 的候选分离：

```text
1. high-mass task combinations
2. route support union
3. near-y task set
```

这些只负责生成候选 `S`；每个 cut 仍必须由 exact oracle 证明 `U(S)` 后才加入，因此不影响精确性。

20 规模 30 秒短测：

```text
results/20260512_115549_medium_3pb_schedule_capacity_sep_30s.csv

schedule_capacity_cuts_added=5
dual=491.291843
gap=0.217617
```

对比上一版 schedule capacity separation：

```text
cut 数: 2 -> 5
node 数: 6 -> 4
branch_testing_time: 约 10.65s -> 约 7.49s
root_relaxation: 仍为 490.283693
```

结论：candidate separation 更会找 cut 了，但这些 cut 仍未切掉 root 最优面。后续需要继续寻找能改变 root bound 的 schedule-aware inequality，或转入 2LBB branching 加速树搜索。

## 15. Long-Run Output Fields

clean BPC 终端输出已补充 cut 对比字段：

```text
schedule-cap candidates={...}
cut_added family=schedule_capacity node=... added=...
finish ... cuts=... sched_cap=...
summary ... rci=... kpath=... sched_cap=... cuts_purged=... branch_test_time=...
```

用于 3600 秒实验时直接观察：

- RCI/RCC 是否触发；
- k-path/resource cut 是否触发；
- schedule capacity cut 是否触发；
- cut purging 是否发生；
- branching testing 时间是否过大。

## 16. Clean BPC Linking / Schedule-Cap Long-Run Ablation

新增 3600 秒消融入口，固定同一 seed 和 BPC 参数，只切换 `task_vehicle_linking_enabled` 与 `schedule_capacity_cuts_enabled`。

目的：判断 20 规模 gap 改善主要来自 task-vehicle linking、schedule-cap cut、两者叠加，还是 branch tree 偶然路径。

默认 variant：

```text
no_link_no_schedcap
link_only
schedcap_only
link_schedcap
```

运行 20 规模四组 3600s 对照。该命令不会覆盖历史日志，因为 `RUN_ID` 带时间戳：

```bash
cd /home/kai/work/gnn_bb
RUN_ID="$(date +%Y%m%d_%H%M%S)_medium_link_schedcap_ablation_3600"
mkdir -p results/logs/bpc_ablation_terminal

/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_ablation.py \
  --config configs/bpc_ablation.yaml \
  --instances medium \
  --time-limit 3600 \
  --run-id "$RUN_ID" \
  2>&1 | tee "results/logs/bpc_ablation_terminal/${RUN_ID}_terminal.log"
```

输出：

```text
results/ablation/<RUN_ID>/summary.csv
results/ablation/<RUN_ID>/logs/<variant>/medium.jsonl
results/ablation/<RUN_ID>/solutions/<variant>/solution_medium.json
results/logs/bpc_ablation_terminal/<RUN_ID>_terminal.log
```

只跑当前主线和 linking-only 对照：

```bash
/home/kai/miniconda3/envs/ecole/bin/python scripts/run_bpc_ablation.py \
  --config configs/bpc_ablation.yaml \
  --instances medium \
  --variants link_only link_schedcap \
  --time-limit 3600 \
  --run-id "$RUN_ID"
```

## 17. Clean BPC Crossing Cut Unification / Sortie Ordering

更新时间：2026-05-12 20:02:24 CST +0800

本次更新 clean BPC 主线：

- 将 RCI 和 k-path/resource lower bound cut 合并为统一 `CrossingCut`；
- 同一任务子集 `S` 使用 key `("crossing_cut", frozenset(S))`，只保留 RHS 最大的 cut；
- 新增相邻车辆 sortie-count ordering：

```text
sum_p lambda[p,r] >= sum_p lambda[p,r+1]
```

- 将该 ordering row 的 dual 加入 route pricing reduced cost；
- 扩展 reduced-cost consistency test，确认 SCIP reduced cost 与手算公式在 `1e-6` 内一致。

验证命令：

```bash
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_bpc_clean
/home/kai/miniconda3/envs/ecole/bin/python -m py_compile bpc/*.py scripts/run_bpc_clean.py scripts/diagnose_root_fractional.py tests/test_bpc_clean.py
```

## 20. Remove Schedule Pair Conflict From Mainline

更新时间：2026-05-13 10:52:35 CST +0800

根据 20 规模 3600 秒对比，`schedule_pair_conflict` cut 虽然数学有效，但没有改善主线表现：dual bound 不变，cut 数和 RMP/branching 开销增加，最终 gap 变差。

当前主线回到：

```text
task_vehicle_linking_enabled = true
schedule_capacity_cuts_enabled = true
schedule_pair_conflict = removed
```

整数 route assignment 若真实 schedule 不可行，现在直接使用：

```text
schedule_nogood_core
schedule_nogood_full
```

输出字段保留：

```text
schedule_nogood_cuts_added
schedule_capacity_cuts_added
```

验证结果：

```text
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_bpc_clean
Ran 10 tests in 2.870s
OK

/home/kai/miniconda3/envs/ecole/bin/python -m py_compile bpc/*.py scripts/run_bpc_clean.py scripts/run_bpc_ablation.py scripts/diagnose_root_fractional.py tests/test_bpc_clean.py
OK
```

## 19. Schedule Pair Conflict Cuts

更新时间：2026-05-13 09:01:21 CST +0800

为减少大量后验 schedule no-good cuts，clean BPC 新增 schedule pair conflict cut。

当整数 route assignment 在某辆车上不可排程时，先检查该车辆当前选中的 route pair。如果两条 route `p,q` 任意顺序都不可排程，则优先加入：

```text
lambda[p,r] + lambda[q,r] <= 1
```

该 cut 对所有同质车辆添加，使用 canonical route signature 计算 coefficient，不依赖对象 id。找不到 pair conflict 时，才退回原来的 schedule no-good core cut。

新增输出字段：

```text
schedule_pair_conflict_cuts_added
schedule_nogood_cuts_added
```

验证命令：

```bash
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_bpc_clean
/home/kai/miniconda3/envs/ecole/bin/python -m py_compile bpc/*.py scripts/run_bpc_clean.py scripts/run_bpc_ablation.py scripts/diagnose_root_fractional.py tests/test_bpc_clean.py
```

## 18. Revert Sortie-Count Ordering

更新时间：2026-05-13 08:28:15 CST +0800

根据 20 规模 3600 秒对比结果，撤回 sortie-count ordering；保留 `link_schedcap` 作为当前主线。

当前主线保留：

- `task_vehicle_linking_enabled=true`
- `schedule_capacity_cuts_enabled=true`
- 统一 `CrossingCut`
- 车辆启用顺序 `y[r+1] <= y[r]`

当前主线撤回：

```text
sum_p lambda[p,r] >= sum_p lambda[p,r+1]
```

原因：该排序改变了 branch tree 和 incumbent 搜索路径，最新对比中 `schedcap_only` 的 primal bound 明显变差，而 crossing cut 本身没有触发。撤回该 row 不影响精确性，只是移除一个对称破除约束。

验证命令：

```bash
/home/kai/miniconda3/envs/ecole/bin/python -m unittest tests.test_bpc_clean
/home/kai/miniconda3/envs/ecole/bin/python -m py_compile bpc/*.py scripts/run_bpc_clean.py scripts/diagnose_root_fractional.py tests/test_bpc_clean.py
```
