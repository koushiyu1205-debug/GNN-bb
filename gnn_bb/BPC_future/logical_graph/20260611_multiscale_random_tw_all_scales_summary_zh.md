# 5/10/20/30/50/100 多规模随机时间窗实例生成汇总报告

生成/汇总日期：2026-06-11。报告语言：中文。

## 执行边界

- 本报告只读取已生成的 manifest、canonical logical graph 和 GNN tensor 元数据。
- 按用户要求，未启动、停止、重启或干预任何 20 规模求解运行。
- 生成侧的 pair/triple feasible ratio、Wilson interval、抽样方差只用于实例筛选和论文审计，不参与 solver 的可行性证明、lower bound 或 certificate。
- 正式 benchmark logical graph 默认不剪边；若后续做求解加载阶段剪边，必须输出独立 pruned graph/tensor，并证明每条删除边在时间窗上双向不可行。

## 总体结论

- 六个规模均已形成 canonical logical graph：每个规模 60 个实例，总计 360 个实例。
- 每个规模均覆盖 2 个地形、3 种时间窗模式，每个地形/模式 10 个 accepted 实例。
- 所有规模均保留完整 directed pair graph；5/10 已被当前 exact solver 用作 no-GNN baseline，20 规模求解另行运行中，本报告不依赖 20 求解结果。
- 这些实例不是全松约束：时间 triple 可行率和能量高阶可行率随规模保持受限，尤其 energy large feasible 中位数多数接近 0。
- 这些实例也不是不可行压力测试：accepted 实例均通过 singleton timed feasible、roundtrip feasible、logical graph reachability 等生成侧检查。
- 对 exact BPC 来说，5/10 是快速回归层，20 是当前最关键压力层，30/50/100 更适合 GNN 泛化和数据规模实验。

## 产物位置

- canonical logical graph 根目录：`BPC_future/logical_graph/`
- 汇总索引：`BPC_future/logical_graph/index.json`
- manifest：`BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks{N}_ablation_20260610/manifest.json`
- scenario 与 GNN tensor：仍保留在各规模的 `BPC_future/data/generated/...` 输出目录；`index.json` 记录了关联路径。

## 规模与图结构

| 任务数 | accepted | attempts | skip | 接受率 | 节点数 | directed edges | option数 min/median/max | x shape | pair_edge_index | tensor缺失 | fleet | Q | S_bar | B_use min/median/max |
| ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | 60 | 140 | 80 | 42.9% | 6 | 30 | 82/90/90 | [6, 9] | [2, 30] | 无 | 1 | 6.0 | 8 | 28.738/43.848/69.485 |
| 10 | 60 | 427 | 367 | 14.1% | 11 | 110 | 318/326/330 | [11, 9] | [2, 110] | 无 | 2 | 6.0 | 8 | 30.986/40.003/53.843 |
| 20 | 60 | 105 | 45 | 57.1% | 21 | 420 | 1220/1246/1260 | [21, 9] | [2, 420] | 无 | 3 | 6.0 | 8 | 31.112/40.908/68.141 |
| 30 | 60 | 106 | 46 | 56.6% | 31 | 930 | 2696/2761/2786 | [31, 9] | [2, 930] | 无 | 3 | 6.0 | 8 | 32.495/41.632/68.027 |
| 50 | 60 | 115 | 55 | 52.2% | 51 | 2550 | 7454/7563/7616 | [51, 9] | [2, 2550] | 无 | 3 | 6.0 | 8 | 32.907/45.562/64.335 |
| 100 | 60 | 87 | 27 | 69.0% | 101 | 10100 | 29662/29961/30142 | [101, 9] | [2, 10100] | 无 | 3 | 6.0 | 8 | 33.484/46.358/70.000 |

解读：完整 directed graph 的边数为 `(N+1)*N`，option 数近似随任务数平方增长。100 规模约 3 万 option 对 GNN 仍可处理，但对 exact labeling pricing 会显著放大候选扩展和 dominance 成本。

## 关键审计分布

下表格式为 `min / p25 / median / p75 / p90 / max`。

| 任务数 | time pair feasible | time triple feasible | window_width/horizon | multi_path_spread/window | energy pair feasible | energy triple feasible | energy large feasible | 最小点距km |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | 0.400 / 0.675 / 0.700 / 0.900 / 0.900 / 1.000 | 0.100 / 0.300 / 0.500 / 0.700 / 0.800 / 0.800 | 0.257 / 0.288 / 0.307 / 0.326 / 0.339 / 0.362 | 0.049 / 0.079 / 0.109 / 0.140 / 0.183 / 0.545 | 0.500 / 0.600 / 0.700 / 0.800 / 0.900 / 0.900 | 0.200 / 0.200 / 0.200 / 0.300 / 0.400 / 0.500 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 1.163 / 1.999 / 2.981 / 4.416 / 4.946 / 6.416 |
| 10 | 0.378 / 0.578 / 0.667 / 0.739 / 0.778 / 0.844 | 0.083 / 0.240 / 0.400 / 0.492 / 0.545 / 0.617 | 0.224 / 0.236 / 0.241 / 0.250 / 0.262 / 0.269 | 0.092 / 0.113 / 0.130 / 0.201 / 0.245 / 0.412 | 0.378 / 0.444 / 0.489 / 0.533 / 0.556 / 0.622 | 0.067 / 0.075 / 0.083 / 0.092 / 0.117 / 0.167 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 1.003 / 1.253 / 1.555 / 1.824 / 2.104 / 2.909 |
| 20 | 0.416 / 0.604 / 0.674 / 0.701 / 0.737 / 0.774 | 0.146 / 0.285 / 0.386 / 0.452 / 0.482 / 0.500 | 0.146 / 0.180 / 0.241 / 0.250 / 0.259 / 0.268 | 0.093 / 0.122 / 0.152 / 0.193 / 0.244 / 0.364 | 0.274 / 0.389 / 0.513 / 0.754 / 0.818 / 0.884 | 0.033 / 0.074 / 0.183 / 0.450 / 0.549 / 0.662 | 0.000 / 0.000 / 0.002 / 0.043 / 0.100 / 0.163 | 1.000 / 1.043 / 1.154 / 1.290 / 1.366 / 1.796 |
| 30 | 0.439 / 0.549 / 0.611 / 0.670 / 0.704 / 0.807 | 0.129 / 0.270 / 0.345 / 0.423 / 0.448 / 0.459 | 0.172 / 0.192 / 0.233 / 0.260 / 0.284 / 0.296 | 0.092 / 0.125 / 0.149 / 0.186 / 0.322 / 0.574 | 0.299 / 0.447 / 0.559 / 0.777 / 0.814 / 0.841 | 0.034 / 0.099 / 0.195 / 0.479 / 0.523 / 0.554 | 0.000 / 0.000 / 0.006 / 0.063 / 0.079 / 0.086 | 1.004 / 1.032 / 1.101 / 1.135 / 1.199 / 1.452 |
| 50 | 0.351 / 0.509 / 0.562 / 0.693 / 0.708 / 0.726 | 0.109 / 0.198 / 0.310 / 0.368 / 0.384 / 0.398 | 0.151 / 0.170 / 0.223 / 0.227 / 0.231 / 0.241 | 0.126 / 0.137 / 0.160 / 0.196 / 0.254 / 0.396 | 0.327 / 0.406 / 0.595 / 0.752 / 0.807 / 0.845 | 0.046 / 0.088 / 0.233 / 0.466 / 0.519 / 0.614 | 0.000 / 0.000 / 0.013 / 0.062 / 0.074 / 0.171 | 1.000 / 1.005 / 1.019 / 1.053 / 1.083 / 1.172 |
| 100 | 0.364 / 0.420 / 0.538 / 0.589 / 0.610 / 0.635 | 0.080 / 0.118 / 0.225 / 0.250 / 0.311 / 0.338 | 0.141 / 0.158 / 0.187 / 0.192 / 0.196 / 0.202 | 0.157 / 0.171 / 0.205 / 0.237 / 0.278 / 0.369 | 0.360 / 0.439 / 0.612 / 0.839 / 0.909 / 0.921 | 0.068 / 0.093 / 0.260 / 0.569 / 0.680 / 0.715 | 0.000 / 0.001 / 0.017 / 0.107 / 0.208 / 0.238 | 1.000 / 1.001 / 1.005 / 1.009 / 1.023 / 1.027 |

解读：

- 时间窗没有退化成全天候窗口。`window_width/horizon` 中位数从 5 规模约 0.307 降到 100 规模约 0.187。
- `time triple feasible` 中位数从 5 规模约 0.500 降到 100 规模约 0.227，说明多任务串接受时间窗有效约束。
- `multi_path_spread/window` 大多低于 0.3，说明 smart jitter 给多路径替换留下空间，但没有把路径选择变成无约束。
- 能量高阶约束有效：`energy large feasible` 中位数在 5/10 为 0，20 约 0.002，100 也只有约 0.032。

## 分地形与时间窗模式明细

### 5 规模

| 地形 | 时间窗模式 | accepted/attempts | 接受率 | skip | time pair med | time triple med | energy pair med | energy triple med | window/horizon med | spread/window med | spacing med |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| apollo15_20km | greedy-anchor | 10/22 | 45.5% | 12 | 0.700 | 0.550 | 0.600 | 0.200 | 0.289 | 0.134 | 2.836 |
| apollo15_20km | random-wave | 10/14 | 71.4% | 4 | 0.650 | 0.200 | 0.700 | 0.250 | 0.333 | 0.078 | 2.204 |
| apollo15_20km | sector-wave | 10/17 | 58.8% | 7 | 0.650 | 0.350 | 0.650 | 0.200 | 0.311 | 0.156 | 4.278 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10/51 | 19.6% | 41 | 0.700 | 0.800 | 0.600 | 0.200 | 0.302 | 0.114 | 4.280 |
| tranquillitatis_balmer_like_20km | random-wave | 10/10 | 100.0% | 0 | 0.900 | 0.600 | 0.700 | 0.200 | 0.311 | 0.094 | 2.293 |
| tranquillitatis_balmer_like_20km | sector-wave | 10/26 | 38.5% | 16 | 0.900 | 0.550 | 0.750 | 0.200 | 0.295 | 0.100 | 3.169 |

### 10 规模

| 地形 | 时间窗模式 | accepted/attempts | 接受率 | skip | time pair med | time triple med | energy pair med | energy triple med | window/horizon med | spread/window med | spacing med |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| apollo15_20km | greedy-anchor | 10/108 | 9.3% | 98 | 0.633 | 0.354 | 0.500 | 0.083 | 0.240 | 0.203 | 1.728 |
| apollo15_20km | random-wave | 10/108 | 9.3% | 98 | 0.567 | 0.183 | 0.500 | 0.083 | 0.245 | 0.193 | 1.728 |
| apollo15_20km | sector-wave | 10/108 | 9.3% | 98 | 0.556 | 0.233 | 0.478 | 0.079 | 0.240 | 0.193 | 1.691 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10/21 | 47.6% | 11 | 0.711 | 0.504 | 0.478 | 0.079 | 0.242 | 0.125 | 1.432 |
| tranquillitatis_balmer_like_20km | random-wave | 10/21 | 47.6% | 11 | 0.689 | 0.433 | 0.478 | 0.079 | 0.242 | 0.125 | 1.432 |
| tranquillitatis_balmer_like_20km | sector-wave | 10/61 | 16.4% | 51 | 0.756 | 0.512 | 0.478 | 0.083 | 0.240 | 0.120 | 1.492 |

### 20 规模

| 地形 | 时间窗模式 | accepted/attempts | 接受率 | skip | time pair med | time triple med | energy pair med | energy triple med | window/horizon med | spread/window med | spacing med |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| apollo15_20km | greedy-anchor | 10/13 | 76.9% | 3 | 0.634 | 0.396 | 0.761 | 0.461 | 0.247 | 0.163 | 1.138 |
| apollo15_20km | random-wave | 10/11 | 90.9% | 1 | 0.642 | 0.245 | 0.745 | 0.457 | 0.256 | 0.153 | 1.263 |
| apollo15_20km | sector-wave | 10/11 | 90.9% | 1 | 0.529 | 0.257 | 0.745 | 0.457 | 0.180 | 0.225 | 1.263 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10/40 | 25.0% | 30 | 0.708 | 0.458 | 0.379 | 0.062 | 0.242 | 0.118 | 1.100 |
| tranquillitatis_balmer_like_20km | random-wave | 10/15 | 66.7% | 5 | 0.705 | 0.449 | 0.397 | 0.077 | 0.247 | 0.124 | 1.177 |
| tranquillitatis_balmer_like_20km | sector-wave | 10/15 | 66.7% | 5 | 0.679 | 0.391 | 0.397 | 0.072 | 0.160 | 0.178 | 1.089 |

### 30 规模

| 地形 | 时间窗模式 | accepted/attempts | 接受率 | skip | time pair med | time triple med | energy pair med | energy triple med | window/horizon med | spread/window med | spacing med |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| apollo15_20km | greedy-anchor | 10/12 | 83.3% | 2 | 0.579 | 0.335 | 0.776 | 0.481 | 0.282 | 0.136 | 1.108 |
| apollo15_20km | random-wave | 10/10 | 100.0% | 0 | 0.533 | 0.202 | 0.785 | 0.487 | 0.236 | 0.182 | 1.108 |
| apollo15_20km | sector-wave | 10/10 | 100.0% | 0 | 0.568 | 0.281 | 0.785 | 0.487 | 0.190 | 0.213 | 1.108 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10/33 | 30.3% | 23 | 0.609 | 0.429 | 0.443 | 0.095 | 0.276 | 0.106 | 1.099 |
| tranquillitatis_balmer_like_20km | random-wave | 10/10 | 100.0% | 0 | 0.686 | 0.400 | 0.416 | 0.078 | 0.232 | 0.133 | 1.097 |
| tranquillitatis_balmer_like_20km | sector-wave | 10/31 | 32.3% | 21 | 0.692 | 0.447 | 0.471 | 0.115 | 0.180 | 0.163 | 1.074 |

### 50 规模

| 地形 | 时间窗模式 | accepted/attempts | 接受率 | skip | time pair med | time triple med | energy pair med | energy triple med | window/horizon med | spread/window med | spacing med |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| apollo15_20km | greedy-anchor | 10/12 | 83.3% | 2 | 0.509 | 0.264 | 0.755 | 0.468 | 0.228 | 0.165 | 1.017 |
| apollo15_20km | random-wave | 10/12 | 83.3% | 2 | 0.513 | 0.189 | 0.755 | 0.468 | 0.226 | 0.169 | 1.017 |
| apollo15_20km | sector-wave | 10/12 | 83.3% | 2 | 0.488 | 0.173 | 0.755 | 0.468 | 0.169 | 0.232 | 1.017 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10/48 | 20.8% | 38 | 0.573 | 0.364 | 0.413 | 0.086 | 0.225 | 0.136 | 1.022 |
| tranquillitatis_balmer_like_20km | random-wave | 10/15 | 66.7% | 5 | 0.701 | 0.372 | 0.403 | 0.086 | 0.222 | 0.140 | 1.021 |
| tranquillitatis_balmer_like_20km | sector-wave | 10/16 | 62.5% | 6 | 0.698 | 0.357 | 0.404 | 0.085 | 0.160 | 0.187 | 1.017 |

### 100 规模

| 地形 | 时间窗模式 | accepted/attempts | 接受率 | skip | time pair med | time triple med | energy pair med | energy triple med | window/horizon med | spread/window med | spacing med |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| apollo15_20km | greedy-anchor | 10/14 | 71.4% | 4 | 0.492 | 0.222 | 0.844 | 0.571 | 0.192 | 0.208 | 1.005 |
| apollo15_20km | random-wave | 10/14 | 71.4% | 4 | 0.400 | 0.100 | 0.844 | 0.571 | 0.197 | 0.201 | 1.005 |
| apollo15_20km | sector-wave | 10/14 | 71.4% | 4 | 0.401 | 0.108 | 0.844 | 0.571 | 0.157 | 0.262 | 1.005 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10/25 | 40.0% | 15 | 0.565 | 0.325 | 0.440 | 0.100 | 0.186 | 0.168 | 1.005 |
| tranquillitatis_balmer_like_20km | random-wave | 10/10 | 100.0% | 0 | 0.593 | 0.230 | 0.428 | 0.090 | 0.191 | 0.163 | 1.004 |
| tranquillitatis_balmer_like_20km | sector-wave | 10/10 | 100.0% | 0 | 0.609 | 0.232 | 0.428 | 0.090 | 0.145 | 0.211 | 1.004 |

## Skip 原因汇总

| 任务数 | skip 总数 | 原因计数 |
| ---: | ---: | --- |
| 5 | 80 | time triple density out of band: 65; no balanced energy cap found: 8; single task roundtrip infeasible after cap selection: 3; single task seed feasibility failed: 3; time pair density out of band: 1 |
| 10 | 367 | single task seed feasibility failed: 251; time triple density out of band: 58; single task roundtrip infeasible after cap selection: 37; time pair density out of band: 11; no balanced energy cap found: 7; logical graph has unreachable pair: 3 |
| 20 | 45 | time triple density out of band: 42; single task seed feasibility failed: 3 |
| 30 | 46 | time triple density out of band: 45; time pair density out of band: 1 |
| 50 | 55 | time triple density out of band: 49; single task seed feasibility failed: 6 |
| 100 | 27 | time triple density out of band: 15; single task seed feasibility failed: 12 |

解读：

- 10 规模接受率最低，主要来自 `single task seed feasibility failed` 和 roundtrip/energy-cap 筛选；这说明生成器没有为了提高接受率而放松单任务和能量底线。
- 20/30/50 的主 skip 原因是 `time triple density out of band`，说明生成器在主动排除过松或过紧的三任务时间窗结构。
- 100 规模接受率较高，是因为窗口策略和预算化审计对大规模做了可行性保护；这不意味着求解简单，因为完整图和 option 数已经大幅增长。

## 对 exact BPC 的影响分析

### 1. Pricing label frontier 的规模压力

完整 directed pair graph 对 exact pricing 是最直接的压力源。20 规模已有 420 条 directed edges 和约 1,240 个 option；100 规模达到 10,100 条 directed edges 和约 30,000 个 option。即使时间窗和能量约束能剪掉部分扩展，direct-label pricing 的候选分支和 dominance 检查仍会随规模快速放大。

### 2. 时间窗有效，但不会自动让 final judge 变快

20 规模 `time pair` 中位数约 0.674、`time triple` 中位数约 0.388。这是一个对 exact BPC 很敏感的区间：pair 层面大量边仍可行，heuristic/profile worker 能找到负列；triple 层面又已有约束，final judge 需要排除大量接近可行的组合才能证明 no negative。因此这批 20 规模实例很容易暴露 completion-bound final judge 慢，而不是简单的 infeasible 早停。

### 3. 能量约束主要压缩高阶路线

20 规模 `energy pair` 中位数约 0.553，但 `energy large` 中位数约 0.002；100 规模 `energy pair` 可达较高水平，但 `energy large` 中位数仍约 0.032。这意味着能量约束不会显著减少所有一阶边，但会强烈压缩长路线。对 pricing 来说，单步扩展仍多，后段证明依赖 completion bound、resource-aware 下界和 dominance 的质量。

### 4. RMP tail 可能更容易出现小步迭代

这批实例保留多路径 option，且 `spread/window` 没有过大，求解器能在同一 task-set 上替换不同物理路径。这对模型真实性是好事，但也容易制造 replacement-only negative column：RMP objective 缓慢改进、active support 变化小、final judge 多次返回物理替代列。后续评估 harvesting、hidden-negative audit、tail dual center 时，应报告 replacement-only 比例而不是只看 selected column 数。

### 5. Branching 与 cuts 的影响

时间窗和能量约束越有效，分支子树内 infeasible route-set 越多，理论上更容易靠 branching/cuts 收紧。但如果 lower bound 不能快速识别不可完成 tail，branch-heavy 子树仍会反复调用 true-dual final judge。因此 20 规模以后，瓶颈更可能从 RMP LP 转移到 pricing proof path。

## 对 GNN 的影响分析

- 数据优点：三种时间窗模式提供 ablation，两个地形提供空间分布变化，六种规模提供 size generalization；完整 pair graph 也保留了 GNN 学习多路径结构所需的信息。
- 训练风险：如果只用 accepted 实例训练，GNN 学到的是生成器筛选后的条件分布，不是原始随机分布；论文中应同时报告 skip 分布。
- 规模风险：50/100 的完整图对 message passing 成本较高，训练时需要 batch size、edge sampling 或候选子图策略，否则 GNN 本身可能成为开销源。
- 精确性边界：GNN 只能用于 early/mid pricing 的排序、候选覆盖或 dual anchor 辅助，不能进入 official lower bound 或 `CERTIFIED_NO_NEGATIVE` 证书路径。

## 对 benchmark 公信力的影响

- 有利点：保留所有 skip 统计，且三种时间窗模式能回应“是否只为 greedy-anchor 制造简单数据”的质疑。
- 风险点：10 规模接受率明显低，审稿人可能质疑 rejection sampling 是否改变分布；应解释筛选目标是约束有效性区间，而非按求解器结果筛选。
- 风险点：大规模窗口策略更保护可行性，100 规模接受率较高；应强调大规模用于 GNN/数据规模实验，不承诺当前 exact BPC 快速求全局最优。
- 风险点：若后续只报告 solved 子集，会造成偏差；正式报告应同时列 accepted/attempts、skip 原因、pair/triple 密度和能量密度。

## 建议的算法实验分层

1. 5 规模：回归层，检查默认配置、exactness、日志字段和无 GNN baseline 是否稳定。
2. 10 规模：性能比较层，适合对比 harvesting、completion bound、GNN 排序是否真正减少 tail rounds。
3. 20 规模：proof-path 压力层，重点分析 completion-bound final judge、hidden negative、replacement-only negative column。
4. 30/50/100：GNN 泛化和数据规模层，先不要把当前 exact BPC 的 200s 目标直接扩展到这些规模。
5. 若要让 50/100 进入 exact solver，应先实现 solver-load 阶段 exact-safe pruning，并输出独立 pruned graph/tensor 版本；不要修改 canonical benchmark graph。

## 文件校验摘要

- 5 规模：canonical logical graph `60` 个；`.pt/.npz/meta` 缺失：`无`；manifest：`BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks5_ablation_20260610/manifest.json`。
- 10 规模：canonical logical graph `60` 个；`.pt/.npz/meta` 缺失：`无`；manifest：`BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks10_ablation_20260610/manifest.json`。
- 20 规模：canonical logical graph `60` 个；`.pt/.npz/meta` 缺失：`无`；manifest：`BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks20_ablation_20260610/manifest.json`。
- 30 规模：canonical logical graph `60` 个；`.pt/.npz/meta` 缺失：`无`；manifest：`BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks30_ablation_20260610/manifest.json`。
- 50 规模：canonical logical graph `60` 个；`.pt/.npz/meta` 缺失：`无`；manifest：`BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks50_ablation_20260610/manifest.json`。
- 100 规模：canonical logical graph `60` 个；`.pt/.npz/meta` 缺失：`无`；manifest：`BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks100_ablation_20260610/manifest.json`。

## 结论

这批实例对算法的影响是“双刃剑”：它们比旧的松约束实例更能让时间窗和电量约束发挥剪枝作用，但因为保留完整 directed pair graph、多路径 option 和足够的 pair 可行空间，exact pricing 的 final proof 仍会很重。它们适合作为精确 BPC 的严肃测试集，而不是简单数据；但 30/50/100 应优先作为 GNN 和可扩展性数据集，不能直接拿当前 exact solver 的 5/10/20 目标外推。
