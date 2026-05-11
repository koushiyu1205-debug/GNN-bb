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
Ran 14 tests ... OK
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

待继续优化：

```text
1. two-level route->schedule 分解
2. 给 Python pricer 增加显式时间检查，减少 exact fallback 超时尾巴
```


## 6. 下一步计划

短期顺序：

1. 用 route-vehicle 原生 SCIP Pricer 跑 very_small 和 20 规模，确认改模后的目标值、时间、列数。
2. 对 30 规模做受控短测，记录它卡在 pricing、LP、branching 还是内存。
3. 在稳定 route-vehicle baseline 上实现 3PB：先做无 ML 的 candidate ranking 和 LP testing。
4. 记录 branching candidate 日志，为 2LBB 的 M1/M2 训练数据做准备。
