# 多规模随机时间窗实例生成总汇总报告

生成日期：2026-06-10。报告语言：中文。

## 范围与产物

- 规模：`5, 10, 20, 30, 50, 100`。
- 每个规模 60 个实例：2 个地形 × 3 种时间窗模式 × 每组 10 个。
- solver-facing logical graph 统一存放在：`BPC_future/logical_graph/`。
- scenario、`.pt`、`.npz` tensor 保留在对应 `BPC_future/data/generated/...` 目录。
- 正式数据未在生成阶段剪边；完整 directed pair logical graph 保留。

## 全局校验

| 规模 | manifest实例数 | canonical logical graph数 | generated源目录残留logical graph | 校验问题数 | nodes | directed edges | option数范围 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 5 | 60 | 60 | 0 | 0 | 6 | 30 | 82-90 |
| 10 | 60 | 60 | 0 | 0 | 11 | 110 | 318-330 |
| 20 | 60 | 60 | 0 | 0 | 21 | 420 | 1220-1260 |
| 30 | 60 | 60 | 0 | 0 | 31 | 930 | 2696-2786 |
| 50 | 60 | 60 | 0 | 0 | 51 | 2550 | 7454-7616 |
| 100 | 60 | 60 | 0 | 0 | 101 | 10100 | 29662-30142 |

- 当前共计 accepted 实例：`360`。
- 当前每个规模 canonical logical graph 均为 60 个，总计 360 个。

## 规模级统计

| 规模 | attempts | skips | 总接受率 | time pair中位数 | time triple中位数 | energy pair中位数 | energy triple中位数 | window/horizon中位数 | spread/window中位数 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 140 | 80 | 0.429 | 0.700 | 0.500 | 0.700 | 0.200 | 0.307 | 0.109 |
| 10 | 427 | 367 | 0.141 | 0.667 | 0.400 | 0.489 | 0.083 | 0.241 | 0.130 |
| 20 | 105 | 45 | 0.571 | 0.674 | 0.386 | 0.513 | 0.183 | 0.241 | 0.152 |
| 30 | 106 | 46 | 0.566 | 0.611 | 0.345 | 0.559 | 0.195 | 0.233 | 0.149 |
| 50 | 115 | 55 | 0.522 | 0.562 | 0.310 | 0.595 | 0.233 | 0.223 | 0.160 |
| 100 | 87 | 27 | 0.690 | 0.538 | 0.225 | 0.612 | 0.260 | 0.187 | 0.205 |

## 分布与审计说明

- `pair/triple feasible ratio`、Wilson interval、抽样方差只用于生成筛选，不是求解器证明逻辑。
- 生成器按规模和时间窗模式使用统一校准规则，目标是让时间窗约束有效参与，而不是让实例退化成全天候任务集合。
- 5/10 是先前已生成并迁移到 canonical `logical_graph` 的数据；20/30/50/100 使用同一 pipeline 生成、去重、校验并输出中文报告。
- 100 规模使用 `jobs=1` 完整生成，原因是单实例完整 tensor 导出峰值 RSS 约 5GB；串行运行避免并行内存风险。
- 所有正式 benchmark 默认不剪边；如果后续做大规模 solver-load 剪边，必须输出独立 pruned graph/tensor 版本并证明每条被删边在时间窗上双向不可行。

## 对后续求解实验的含义

- 5/10/20 可进入 no-GNN baseline 全量求解测试；按当前目标，5/10 限时 600 秒，20 限时 3600 秒。
- 30/50/100 当前目标是提供 solver-compatible 数据和 GNN 输入，不要求 exact BPC 在这些规模上快速求完。
- GNN 训练应使用新的 tensor 路径字段和 canonical logical graph 路径，避免读到已删除的 generated-root logical graph 副本。

## 相关报告

- 5规模：`BPC_future/results/20260610_multiscale_random_tw_tasks5_ablation_report.md`
- 10规模：`BPC_future/results/20260610_tasks10_generation_and_logical_graph_collection_report_zh.md`
- 20规模：`BPC_future/results/20260610_tasks20_generation_report_zh.md`
- 30规模：`BPC_future/results/20260610_tasks30_generation_report_zh.md`
- 50规模：`BPC_future/results/20260610_tasks50_generation_report_zh.md`
- 100规模：`BPC_future/results/20260610_tasks100_generation_report_zh.md`

## 结论

- 六种规模共 360 个实例已经生成完成，canonical logical graph 数量正确。
- 下一步是按目标运行 no-GNN baseline：5/10/20 全量，分别使用 600/600/3600 秒限时。
