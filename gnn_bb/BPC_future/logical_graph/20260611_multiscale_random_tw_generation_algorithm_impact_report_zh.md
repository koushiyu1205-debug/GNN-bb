# 多规模随机时间窗实例生成与算法影响审计报告

生成/审计日期：2026-06-11。  
审计范围：`BPC_future/logical_graph/tasks_005`、`tasks_010`、`tasks_020`、`tasks_030`、`tasks_050`、`tasks_100` 及对应 `data/generated/.../manifest.json`。  
执行边界：本报告只读取已生成数据和 manifest；未启动、停止、重启或干预任何 20 规模求解运行。

## 1. 总体结论

- 六个规模均已生成完整 canonical logical graph：每个规模 `60` 个实例，总计 `360` 个实例。
- 每个规模结构完全均衡：`2` 个地形 × `3` 种时间窗模式 × 每组 `10` 个实例。
- 三种时间窗模式均已覆盖：`greedy-anchor`、`random-wave`、`sector-wave`。这可以避免 benchmark 只绑定到贪心锚定分布。
- 所有 official benchmark graph 均保留完整 directed pair logical graph；生成阶段没有剪边。
- 每个实例均导出 GNN tensor 元数据，并保留 `.pt` / `.npz` 路径；logical graph JSON 统一集中到 `BPC_future/logical_graph/`。
- 生成筛选使用 pair/triple feasible ratio、能量密度、最小点距、singleton feasibility 等审计指标；这些指标只用于生成侧筛选，不参与 exact solver 的 lower bound 或 certificate。

## 2. 数据规模总览

| 任务数 | 实例数 | attempts | skip | 接受率 | 节点数 | directed pair edges | option数 min/median/max | tensor x | pair_edge_index | fleet | Q | S_bar | B_use min/median/max |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| 5 | 60 | 140 | 80 | 42.9% | 6 | 30 | 82/90/90 | [6, 9] | [2, 30] | 1 | 6.0 | 8 | 28.738/43.848/69.485 |
| 10 | 60 | 427 | 367 | 14.1% | 11 | 110 | 318/326/330 | [11, 9] | [2, 110] | 2 | 6.0 | 8 | 30.986/40.003/53.843 |
| 20 | 60 | 105 | 45 | 57.1% | 21 | 420 | 1220/1246/1260 | [21, 9] | [2, 420] | 3 | 6.0 | 8 | 31.112/40.908/68.141 |
| 30 | 60 | 106 | 46 | 56.6% | 31 | 930 | 2696/2761/2786 | [31, 9] | [2, 930] | 3 | 6.0 | 8 | 32.495/41.632/68.027 |
| 50 | 60 | 115 | 55 | 52.2% | 51 | 2550 | 7454/7563/7616 | [51, 9] | [2, 2550] | 3 | 6.0 | 8 | 32.907/45.562/64.335 |
| 100 | 60 | 87 | 27 | 69.0% | 101 | 10100 | 29662/29961/30142 | [101, 9] | [2, 10100] | 3 | 6.0 | 8 | 33.484/46.358/70.000 |

关键解释：

- directed edge 数按完整图增长，为 `(N + 1) * N`。
- option 数近似二次增长，100 规模约 `3e4` 个物理 path option。这个量对 GNN 输入不大，但对 exact pricing 的 label extension 和 dominance 是强压力。
- 5/10 规模用于 exact solver 快速回归是合理的；20 规模开始进入 proof-path 压力区；30/50/100 更适合 GNN 泛化和数据规模实验。

## 3. 约束强度总览

下表格式为 `min / p25 / median / p75 / p90 / max`。

| 任务数 | time pair feasible | time triple feasible | window_width/horizon | multi_path_spread/window | energy pair feasible | energy triple feasible | energy large feasible | 最小点距 km |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | 0.400 / 0.675 / 0.700 / 0.900 / 0.900 / 1.000 | 0.100 / 0.300 / 0.500 / 0.700 / 0.800 / 0.800 | 0.257 / 0.288 / 0.307 / 0.326 / 0.339 / 0.362 | 0.049 / 0.079 / 0.109 / 0.140 / 0.183 / 0.545 | 0.500 / 0.600 / 0.700 / 0.800 / 0.900 / 0.900 | 0.200 / 0.200 / 0.200 / 0.300 / 0.400 / 0.500 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 1.163 / 1.999 / 2.981 / 4.416 / 4.946 / 6.416 |
| 10 | 0.378 / 0.578 / 0.667 / 0.739 / 0.778 / 0.844 | 0.083 / 0.240 / 0.400 / 0.492 / 0.545 / 0.617 | 0.224 / 0.236 / 0.241 / 0.250 / 0.262 / 0.269 | 0.092 / 0.113 / 0.130 / 0.201 / 0.245 / 0.412 | 0.378 / 0.444 / 0.489 / 0.533 / 0.556 / 0.622 | 0.067 / 0.075 / 0.083 / 0.092 / 0.117 / 0.167 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 1.003 / 1.253 / 1.555 / 1.824 / 2.104 / 2.909 |
| 20 | 0.416 / 0.604 / 0.674 / 0.701 / 0.737 / 0.774 | 0.146 / 0.285 / 0.386 / 0.452 / 0.482 / 0.500 | 0.146 / 0.180 / 0.241 / 0.250 / 0.259 / 0.268 | 0.093 / 0.122 / 0.152 / 0.193 / 0.244 / 0.364 | 0.274 / 0.389 / 0.513 / 0.754 / 0.818 / 0.884 | 0.033 / 0.074 / 0.183 / 0.450 / 0.549 / 0.662 | 0.000 / 0.000 / 0.002 / 0.043 / 0.100 / 0.163 | 1.000 / 1.043 / 1.154 / 1.290 / 1.366 / 1.796 |
| 30 | 0.439 / 0.549 / 0.611 / 0.670 / 0.704 / 0.807 | 0.129 / 0.270 / 0.345 / 0.423 / 0.448 / 0.459 | 0.172 / 0.192 / 0.233 / 0.260 / 0.284 / 0.296 | 0.092 / 0.125 / 0.149 / 0.186 / 0.322 / 0.574 | 0.299 / 0.447 / 0.559 / 0.777 / 0.814 / 0.841 | 0.034 / 0.099 / 0.195 / 0.479 / 0.523 / 0.554 | 0.000 / 0.000 / 0.006 / 0.063 / 0.079 / 0.086 | 1.004 / 1.032 / 1.101 / 1.135 / 1.199 / 1.452 |
| 50 | 0.351 / 0.509 / 0.562 / 0.693 / 0.708 / 0.726 | 0.109 / 0.198 / 0.310 / 0.368 / 0.384 / 0.398 | 0.151 / 0.170 / 0.223 / 0.227 / 0.231 / 0.241 | 0.126 / 0.137 / 0.160 / 0.196 / 0.254 / 0.396 | 0.327 / 0.406 / 0.595 / 0.752 / 0.807 / 0.845 | 0.046 / 0.088 / 0.233 / 0.466 / 0.519 / 0.614 | 0.000 / 0.000 / 0.013 / 0.062 / 0.074 / 0.171 | 1.000 / 1.005 / 1.019 / 1.053 / 1.083 / 1.172 |
| 100 | 0.364 / 0.420 / 0.538 / 0.589 / 0.610 / 0.635 | 0.080 / 0.118 / 0.225 / 0.250 / 0.311 / 0.338 | 0.141 / 0.158 / 0.187 / 0.192 / 0.196 / 0.202 | 0.157 / 0.171 / 0.205 / 0.237 / 0.278 / 0.369 | 0.360 / 0.439 / 0.612 / 0.839 / 0.909 / 0.921 | 0.068 / 0.093 / 0.260 / 0.569 / 0.680 / 0.715 | 0.000 / 0.001 / 0.017 / 0.107 / 0.208 / 0.238 | 1.000 / 1.001 / 1.005 / 1.009 / 1.023 / 1.027 |

关键解释：

- 时间窗不是“全天候”：`window_width/horizon` 中位数从 5 规模的约 `0.307` 下降到 100 规模的约 `0.187`。
- 三任务时间可行率随规模下降：5 规模中位数约 `0.500`，20 规模约 `0.386`，100 规模约 `0.225`。这说明时间窗对多任务组合有实质剪枝。
- `multi_path_spread/window` 大多低于 `0.3`，说明 smart jitter 留出了多路径替换空间，但没有把所有路径选择都放开。
- 能量约束主要压缩长 route：pair 层面仍有相当可行性，高阶 `energy large feasible` 中位数在多数规模接近 0。这会让 early pricing 仍有大量边可扩展，但长尾证明必须依赖 completion bound / dominance。

## 4. skip 统计与分布偏差风险

| 任务数 | skip 总数 | 主要原因 |
| ---: | ---: | --- |
| 5 | 80 | time triple density out of band: 65；no balanced energy cap found: 8；single task roundtrip infeasible after cap selection: 3；single task seed feasibility failed: 3；time pair density out of band: 1 |
| 10 | 367 | single task seed feasibility failed: 251；time triple density out of band: 58；single task roundtrip infeasible after cap selection: 37；time pair density out of band: 11；no balanced energy cap found: 7；logical graph has unreachable pair: 3 |
| 20 | 45 | time triple density out of band: 42；single task seed feasibility failed: 3 |
| 30 | 46 | time triple density out of band: 45；time pair density out of band: 1 |
| 50 | 55 | time triple density out of band: 49；single task seed feasibility failed: 6 |
| 100 | 27 | time triple density out of band: 15；single task seed feasibility failed: 12 |

审稿风险判断：

- `10` 规模接受率最低，且大量 rejected 来自 singleton feasibility，而不是求解时间结果；这可以说明筛选不是按 solver 难易度 cherry-pick，但论文里必须报告 skip 分布。
- `time triple density out of band` 是多数规模的主筛选项，说明生成器在控制“过松/过紧”两端，而不是只保留简单实例。
- `100` 规模接受率较高，可能被误读为大规模更简单。实际原因是大规模生成策略更重视 singleton/route-set 可行性保护；对 exact solver 难度仍由完整图和 option 数放大。

## 5. 对 exact BPC 的算法影响

### 5.1 Pricing label frontier

这批数据最核心的算法影响是：pair 可行性保留得足够多，triple/large route 可行性又被时间窗和能量约束压缩。因此 label algorithm 不会在第一跳就被剪掉，仍会产生大量 partial labels；但在尾部证明阶段又必须排除很多“近似可行但最终不可完成”的组合。

这类结构会放大：

- direct-label pricing 的 extension 数；
- dominance rule 的比较压力；
- completion-bound final judge 的 no-negative proof 成本；
- replacement-only physical path 反复出现的概率。

### 5.2 Completion bound

时间窗和能量约束有效后，completion bound 理论上更有剪枝空间，但前提是 bound 能识别 task memory、available mask 和资源可完成性。只看资源 Pareto 或只看标量 task dual 的 bound 容易出现两类问题：

- 如果没有任务记忆，可能重复领取同一任务 dual，bound 会过松或被迫禁用。
- 如果资源维度太高，Pareto front 爆炸，查询开销超过节省的 label extension。

所以这批实例适合检验 completion-bound 的数学质量，但不会自动让已有 proof path 变快。

### 5.3 RMP tail 和 column replacement

数据保留多路径 option，且 `spread/window` 留出了路径替换空间。这会增加同一 task-set 下不同物理 route 的竞争。好处是模型更真实；坏处是 RMP tail 可能出现很多 replacement-only negative columns。

因此后续评价算法时不能只看“新增列数”，必须同时看：

- selected_new_mask_count；
- selected_support_changing_count；
- selected_weak_replacement_count；
- replacement-only ratio；
- root-tail RMP rounds；
- hidden-negative audit 次数。

### 5.4 Branching 和 cuts

时间窗/能量约束越有效，分支子树里不可完成 route-set 越多，理论上更有利于 cuts 和 branching 缩小搜索空间。但如果 pricing final judge 不能快速证明无负列，branch-heavy 子树会把开销转移到 repeated true-dual pricing proof 上。

这意味着 20 规模以后真正的瓶颈很可能不是 LP 本身，而是：

- branch 节点内的 true-dual final judge；
- completion-bound retry；
- hidden negative patrol；
- route replacement 与 active support 不稳定。

## 6. 对 GNN 的算法影响

这批数据对 GNN 有正负两面。

正面：

- 六个规模提供 size generalization。
- 两个地形提供空间分布 shift。
- 三种时间窗模式提供机制 ablation，避免只学 greedy-anchor。
- 完整 directed graph 保留了多路径 option 和 pair 结构。

风险：

- accepted 实例是 rejection sampling 后的条件分布，GNN 可能学习到筛选器偏好；训练和论文都应报告 skip 分布。
- 50/100 规模完整图的 edge/option 数较大，message passing 成本可能超过它在 pricing 中节省的时间。
- GNN 若只优化 early worker 找负列，不优化 true-dual final judge，则对 20 规模 root-tail proof 可能帮助有限。
- GNN 不能进入 official certificate path；它最多做候选排序、task-cover dual anchor 或 early/mid pricing 辅助。

建议的 GNN 使用方式：

- 训练目标不要只预测是否在最终解中，而要预测“能改变 active support 的 task-set / mask”。
- 对 replacement-only column 降权，否则 GNN 会加剧 tail 小步迭代。
- 训练/评估必须按时间窗模式和地形分层，避免在 greedy-anchor 上好、random-wave 上退化。
- 50/100 训练时考虑 edge sampling 或候选子图，但 canonical tensor 仍保留全图。

## 7. 按规模的推荐用途

| 规模 | 推荐用途 | 不建议用途 | 算法风险 |
| ---: | --- | --- | --- |
| 5 | exactness 回归、日志字段验证、基础 smoke | 评价复杂优化收益 | 实例太小，branch/pricing tail 不代表真实瓶颈 |
| 10 | 主要性能回归、GNN/no-GNN 对比、harvesting 对比 | 直接外推 20 规模证明性能 | 10 规模接受率低，需报告 rejection sampling 偏差 |
| 20 | 当前 exact BPC 的关键压力层、final judge 诊断 | 在未优化 proof path 前追求全量快速 | completion-bound proof 和 replacement-tail 可能主导时间 |
| 30 | GNN 泛化、solver-load pruning 实验 | 作为当前 exact solver 的默认全量 benchmark | 完整图 option 数已明显放大 |
| 50 | 大图 GNN、可扩展性实验、pruned graph 研究 | 不剪边直接要求 exact BPC 快速最优 | edge/option 规模会压垮 labeling |
| 100 | GNN scaling、数据工程和特征泛化 | 当前 exact BPC 全精确性能目标 | 完整图对 exact pricing 几乎必然过重 |

## 8. 对论文/报告的表达建议

- 明确说明生成筛选只基于可行性和密度审计，不基于求解器运行时间、最优值或 solver 成败。
- 同时报告 accepted 和 rejected；不要只报告 360 个 accepted 实例。
- pair/triple feasible ratio、Wilson interval、抽样方差属于 Monte Carlo generation audit，不是 exact solver proof logic。
- official benchmark 默认不剪边；若做剪边实验，必须生成独立 pruned graph/tensor，并证明每条删除边在时间窗上双向不可行。
- 20/30/50/100 不应混用同一个“平均 200s exact optimum”口径。当前目标应保留在 5/10/20，30+ 更适合作为泛化数据。

## 9. 结论

这批实例不是“简单数据”。它们通过时间窗和能量约束避免了旧数据中可能存在的过松结构，但仍保留足够 pair 可行性、多路径选择和完整 logical graph，使 exact BPC 的 pricing proof path 会被真实放大。

对算法的直接影响是：

1. 5/10 规模会更适合稳定回归，因为约束能剪枝，求解不至于被全天候窗口拖垮。
2. 20 规模会集中暴露 true-dual final judge、completion bound、hidden negative 和 replacement-only tail 的瓶颈。
3. 30/50/100 对当前 exact solver 不是自然延伸的“同难度更大版”，而是 GNN/数据规模和 solver-load pruning 的实验层。
4. 如果后续算法在这批数据上变快，需要进一步拆解是时间窗剪枝、能量剪枝、support-changing columns、还是 final judge 调用次数下降带来的，不能只报告总时间。

详细基础统计已保存在：`BPC_future/logical_graph/20260611_multiscale_random_tw_all_scales_summary_zh.md`。
