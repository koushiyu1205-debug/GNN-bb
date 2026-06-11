# 20260610 多规模随机时间窗实例生成汇总与算法影响分析

## 结论摘要

本轮生成链路已经在 `BPC_future/logical_graph/` 下形成 6 个规模的 canonical logical graph 集合：

- 规模：5、10、20、30、50、100。
- 每个规模 60 个实例：2 个地形 × 3 种时间窗模式 × 每组 10 个。
- 总计 360 个 logical graph JSON。
- 所有规模都保留完整 directed pair logical graph，没有在 benchmark 默认版本中剪边。
- 每个实例均配套生成侧审计：时间 pair/triple 可行率、能量密度、时间窗宽度、multi-path spread/window、skip reason。

核心判断：

1. 这批实例不是“全松约束”数据。时间 triple 可行率随规模总体下降，能量 large feasible ratio 大多接近 0 或很低，说明 multi-trip 组合空间被时间和电量共同约束。
2. 这批实例也不是“极紧不可行”数据。所有 accepted 实例通过 singleton timed feasible、roundtrip feasible、logical graph reachability 等生成侧检查。
3. 对 exact BPC 来说，10 和 20 规模是最有诊断价值的区间：约束已经有效，但 pair/triple 仍有足够组合空间，容易暴露 final judge 证明慢、replacement-tail、hidden negative 等问题。
4. 30、50、100 规模主要适合 GNN 和数据分布实验，不适合直接要求当前 exact BPC 快速求全局最优。原因不是数据不可读，而是完整 directed pair 图和多路径 option 数按近似二次规模增长。

## 数据来源

本报告只读取已落盘的生成结果，不修改实例，不停止或干预正在运行的 20 规模 no-GNN baseline。

主要来源：

- `BPC_future/logical_graph/index.json`
- `BPC_future/logical_graph/tasks_005/`
- `BPC_future/logical_graph/tasks_010/`
- `BPC_future/logical_graph/tasks_020/`
- `BPC_future/logical_graph/tasks_030/`
- `BPC_future/logical_graph/tasks_050/`
- `BPC_future/logical_graph/tasks_100/`
- `BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks*_ablation_20260610/manifest.json`

## 规模与图结构汇总

| 任务数 | accepted | attempts | 接受率 | 节点数 | directed edges | option 数范围 | fleet |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 60 | 140 | 42.9% | 6 | 30 | 82-90 | 1 |
| 10 | 60 | 427 | 14.1% | 11 | 110 | 318-330 | 2 |
| 20 | 60 | 105 | 57.1% | 21 | 420 | 1220-1260 | 3 |
| 30 | 60 | 106 | 56.6% | 31 | 930 | 2696-2786 | 3 |
| 50 | 60 | 115 | 52.2% | 51 | 2550 | 7454-7616 | 3 |
| 100 | 60 | 87 | 69.0% | 101 | 10100 | 29662-30142 | 3 |

解读：

- 图规模按完整 directed pair 增长，边数为 `n_nodes * (n_nodes - 1)`。
- option 数近似随 directed edge 二次增长，并受每条物理 pair 的 multi-path 可选路径数量影响。
- 100 规模的 3 万级 option 对 GNN 仍可接受，但对 exact labeling pricing 是非常大的底层展开空间。
- 10 规模接受率最低，主要来自生成侧严格筛选，不是求解结果筛选。这一点后续写论文或 benchmark 说明时必须保留 skip 统计，避免被质疑选择性保留样本。

## 时间窗与能量约束审计

下表给出每个规模 accepted 实例的关键分布，格式为 `min / p25 / median / p75 / p90 / max`。

| 任务数 | time pair feasible | time triple feasible | window_width / horizon | spread / window | energy pair feasible | energy triple feasible | energy large feasible |
|---:|---|---|---|---|---|---|---|
| 5 | 0.400 / 0.700 / 0.700 / 0.900 / 0.900 / 1.000 | 0.100 / 0.300 / 0.500 / 0.700 / 0.800 / 0.800 | 0.257 / 0.289 / 0.308 / 0.325 / 0.339 / 0.362 | 0.049 / 0.079 / 0.110 / 0.136 / 0.176 / 0.545 | 0.500 / 0.600 / 0.700 / 0.800 / 0.900 / 0.900 | 0.200 / 0.200 / 0.200 / 0.300 / 0.400 / 0.500 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 |
| 10 | 0.378 / 0.578 / 0.667 / 0.733 / 0.778 / 0.844 | 0.083 / 0.242 / 0.400 / 0.492 / 0.542 / 0.617 | 0.224 / 0.236 / 0.241 / 0.250 / 0.262 / 0.269 | 0.092 / 0.114 / 0.130 / 0.199 / 0.245 / 0.412 | 0.378 / 0.444 / 0.489 / 0.533 / 0.556 / 0.622 | 0.067 / 0.075 / 0.083 / 0.092 / 0.117 / 0.167 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 |
| 20 | 0.416 / 0.605 / 0.674 / 0.700 / 0.737 / 0.774 | 0.146 / 0.286 / 0.388 / 0.452 / 0.482 / 0.500 | 0.146 / 0.181 / 0.241 / 0.250 / 0.259 / 0.268 | 0.093 / 0.123 / 0.153 / 0.192 / 0.240 / 0.364 | 0.274 / 0.389 / 0.553 / 0.747 / 0.816 / 0.884 | 0.033 / 0.075 / 0.224 / 0.442 / 0.544 / 0.662 | 0.000 / 0.000 / 0.002 / 0.043 / 0.100 / 0.163 |
| 30 | 0.439 / 0.549 / 0.611 / 0.669 / 0.703 / 0.807 | 0.129 / 0.274 / 0.347 / 0.422 / 0.447 / 0.459 | 0.172 / 0.192 / 0.233 / 0.260 / 0.284 / 0.296 | 0.092 / 0.125 / 0.149 / 0.186 / 0.318 / 0.574 | 0.299 / 0.448 / 0.561 / 0.777 / 0.814 / 0.841 | 0.034 / 0.100 / 0.196 / 0.478 / 0.522 / 0.554 | 0.000 / 0.000 / 0.010 / 0.063 / 0.079 / 0.086 |
| 50 | 0.351 / 0.509 / 0.562 / 0.692 / 0.708 / 0.726 | 0.109 / 0.199 / 0.310 / 0.367 / 0.384 / 0.398 | 0.151 / 0.170 / 0.223 / 0.226 / 0.231 / 0.241 | 0.126 / 0.137 / 0.161 / 0.195 / 0.253 / 0.396 | 0.327 / 0.407 / 0.679 / 0.749 / 0.804 / 0.845 | 0.046 / 0.089 / 0.326 / 0.464 / 0.517 / 0.614 | 0.000 / 0.000 / 0.024 / 0.062 / 0.072 / 0.171 |
| 100 | 0.364 / 0.420 / 0.546 / 0.588 / 0.610 / 0.635 | 0.080 / 0.118 / 0.227 / 0.248 / 0.309 / 0.338 | 0.141 / 0.158 / 0.187 / 0.192 / 0.196 / 0.202 | 0.157 / 0.171 / 0.206 / 0.231 / 0.277 / 0.369 | 0.360 / 0.440 / 0.706 / 0.833 / 0.908 / 0.921 | 0.068 / 0.093 / 0.371 / 0.566 / 0.680 / 0.715 | 0.000 / 0.001 / 0.032 / 0.104 / 0.208 / 0.238 |

解读：

- 时间窗没有退化成全天候窗口。100 规模的 `window_width / horizon` 中位数约 0.187，50 规模约 0.223，10 规模约 0.241。
- `time triple feasible` 从 5 规模中位数 0.500 降到 100 规模中位数 0.227，说明多任务串接不是任意可行。
- `spread / window` 大多低于 0.3，说明 smart jitter 给 multi-path 路径替换留下空间，但没有让路径选择完全无约束。
- 能量约束不是全松的。10 规模 `energy triple feasible` 中位数只有 0.083，20 规模中位数 0.224；100 规模虽然能量 pair 较松，但 large feasible 中位数仍只有 0.032。

## 时间窗模式对实例分布的影响

三种模式都保留了 20 个 accepted 实例，分别对应：

- `greedy-anchor`：时间窗锚定于随机化 greedy tour，天然更接近可行调度骨架。
- `random-wave`：不依赖具体 greedy route，是重要 ablation control（消融控制）。
- `sector-wave`：用空间扇区和 wave 结构引入空间时间相关性。

关键观察：

- 5 规模中 `greedy-anchor` 的 time triple 中位数最高，为 0.700；`random-wave` 和 `sector-wave` 分别约 0.300 和 0.400。这意味着 5 规模下 greedy-anchor 更容易形成多任务串接。
- 10 规模中 `sector-wave` 的 time triple 中位数约 0.475，高于 `random-wave` 的 0.308。这会让 sector-wave 的 pricing 候选空间更大，可能使 exact judge 更慢。
- 20 规模中三种模式的 time triple 中位数分别约 0.449、0.363、0.311。sector-wave 窗口更窄，可能更利于时间窗剪枝。
- 50 和 100 规模中 sector-wave 的 window ratio 明显更低，100 规模 sector-wave 约 0.151；这对 GNN 学习空间-时间结构有价值，但对 exact pricing 来说仍然面对完整 pair 图和大量 option。

## Skip 原因汇总

| 任务数 | 主要 skip 原因 |
|---:|---|
| 5 | time triple density out of band: 65；no balanced energy cap found: 8；single task 相关失败: 6 |
| 10 | single task seed feasibility failed: 251；time triple density out of band: 58；single task roundtrip infeasible after cap selection: 37；time pair density out of band: 11 |
| 20 | time triple density out of band: 42；single task seed feasibility failed: 3 |
| 30 | time triple density out of band: 45；time pair density out of band: 1 |
| 50 | time triple density out of band: 49；single task seed feasibility failed: 6 |
| 100 | time triple density out of band: 15；single task seed feasibility failed: 12 |

解读：

- 10 规模接受率低的主要原因是 seed-level 单任务可行性筛选非常严格，不是因为跑 BPC 后挑选了容易实例。
- 20、30、50 的主要拒绝来自 time triple density out of band，说明生成器在控制“不要过松、不要过紧”的组合可行性。
- 100 规模接受率反而较高，原因是窗口策略和预算化审计对大规模做了可行性保护；但这不代表求解更容易，因为图规模和候选路径数量已经大幅增长。

## 对 exact BPC 算法的影响

### 1. Pricing label frontier 会随规模显著扩大

完整 directed pair graph 保留了所有任务间逻辑边：

- 20 规模：420 条 directed edges，约 1220-1260 个 option。
- 50 规模：2550 条 directed edges，约 7454-7616 个 option。
- 100 规模：10100 条 directed edges，约 29662-30142 个 option。

这会直接放大 direct-label pricing 的扩展候选数。即使时间窗和能量能剪掉部分组合，初始 branching factor 仍然很高。

### 2. 时间窗有效，但没有强到让 final proof 轻松

20 规模 time pair 中位数 0.674、time triple 中位数 0.388。这个区间对算法很敏感：

- pair 层面大量边仍可行，label 扩展不会很快断掉。
- triple 层面已有明显约束，启发式 worker 可以找到负列，但 final judge 证明 no negative 时仍要排除大量近似可行组合。
- 这类分布容易出现 root-tail final judge 很慢，而不是简单的无约束路径爆炸或不可行早停。

### 3. 能量约束对高阶组合有效，但不是单独支配

20 规模 energy pair 中位数 0.553，energy triple 中位数 0.224，energy large 中位数 0.002。说明：

- 单条边和少量任务组合仍有较多可行空间。
- 高阶路线会被能量约束强烈压缩。
- 这有利于 exact bound 的资源剪枝，但如果 completion bound 只看很粗的 bucket 或只看任务 dual，很可能仍不足以快速证明。

### 4. 10 规模并不一定比 20 规模“简单很多”

10 规模 option 数较小，但接受率只有 14.1%，且单任务 seed feasibility skip 很多。accepted 实例是经过严格生成约束筛选后的样本，可能包含较强的边界结构：

- 时间 triple 中位数 0.400。
- energy triple 中位数 0.083。
- fleet 为 2。

这类结构会让路径组合受限但仍有足够替代列，可能造成 tail RMP 小步迭代或 hidden negative 反复出现。

### 5. 30/50/100 更适合 GNN，不适合直接作为当前 exact BPC 目标

这些规模保留完整 graph 和 tensor，是 GNN 学习、泛化和候选排序实验的合适数据。但 exact BPC 的瓶颈会快速放大：

- 30 规模 option 中位数约 2764。
- 50 规模 option 中位数约 7580。
- 100 规模 option 中位数约 30074。

如果 solver 不在加载阶段或 pricing 阶段做 exact-safe 的 edge dominance、time-window infeasible edge pruning、resource-compatible lower bound、branch-compatible candidate gating，直接全精确求解 50/100 规模不现实。

## 对 GNN 的影响

### 正向影响

- 三种时间窗模式提供了 distribution ablation，GNN 不会只学习 greedy-anchor。
- 每个规模都有两个地形，空间结构不完全单一。
- 完整 pair graph 让 GNN 能看到全局 pair/option 结构，适合学习候选排序、task-cover dual anchor、negative-column prior。
- 5/10/20/30/50/100 多规模连续扩展，有利于测试 size generalization。

### 风险

- 如果 GNN 训练只用 accepted 实例，不看 skip 分布，模型可能学到“已筛选后的干净分布”，对更松或更紧的真实实例泛化弱。
- 100 规模完整图非常密，GNN message passing 若不做 sampling 或 edge feature gating，训练成本会明显增加。
- 如果训练标签来自当前 exact solver 的求解轨迹，10/20 的 hard-tail 行为可能让标签偏向局部 RMP 状态，而不是全局结构。
- GNN 只能作为排序和 worker 辅助，不能进入 official certificate path；否则会破坏 exact BPC 证明边界。

## 对 benchmark 公信力的影响

这批实例有两个优点：

1. 保留了 rejected attempt 和 skip reason，可以解释 accepted 数据如何产生。
2. 同时提供 greedy-anchor、random-wave、sector-wave 三组时间窗模式，可以避免“只为 greedy-anchor 调参”的质疑。

仍需在论文或报告中明确：

- 时间窗和能量阈值是生成侧质量控制，不是根据 BPC 求解时间反调。
- Monte Carlo density audit 只用于生成筛选，不进入 solver proof。
- 正式 benchmark 如果用于论文，建议冻结生成规则后用新 seed 再生成一版，避免调试数据和正式结果混用。
- 不要只报告 solved 实例，也要报告每个规模的接受率、skip 原因和密度分布。

## 对后续算法实验的建议

1. 5/10/20 用于 exact BPC 主性能报告；30/50/100 用于 GNN 与 scalability 诊断。
2. 20 规模优先看 final judge 的单次证明耗时、label frontier、completion-bound winner、hidden negative audit，而不是先调 GNN。
3. 如果要让 30+ 进入 exact solver，应先做 solver-load 阶段的 exact-safe pruning，并输出 pruned graph/tensor 独立版本；默认 benchmark 不剪边是正确的。
4. GNN 训练应分模式、分规模报告效果，至少比较 greedy-anchor / random-wave / sector-wave，避免单一分布加速被误认为普适泛化。
5. 继续保留 no-GNN baseline 作为主对照；GNN 加速必须证明减少 pricing 搜索或 RMP tail rounds，而不是只减少某个 worker 的局部时间。

## 当前状态备注

本报告生成时，20 规模 no-GNN baseline 进程仍在运行。本报告没有停止、重启或修改该进程，也没有根据求解结果筛选或更改任何实例。
