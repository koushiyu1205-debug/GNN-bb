# 10规模实例生成与 logical_graph 汇总报告

生成日期：2026-06-10。后续报告按中文口径输出。

## 产物位置

- 5规模 manifest：`BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks5_ablation_20260610/manifest.json`
- 10规模合并 manifest：`BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks10_ablation_20260610/manifest.json`
- 5/10 logical graph 汇总目录：`BPC_future/logical_graph/`
- logical graph 索引：`BPC_future/logical_graph/index.json`
- 校验 JSON：`BPC_future/results/20260610_tasks5_tasks10_logical_graph_collection_validation.json`
- 说明：`BPC_future/logical_graph/` 只复制 solver 可直接读取的 logical graph JSON；scenario/tensor 原文件仍保留在各自 generated 数据目录，索引中记录了原始来源。

## 10规模生成方式

- 按 6 个分组并行生成：2 个地形 × 3 种时间窗模式，每组 10 个 accepted 实例。
- 三种模式：`greedy-anchor`、`random-wave`、`sector-wave`。
- 本次为了加速，按地形/模式拆成 6 个独立进程生成；因此同一地形下不同模式复用了相同 seed 序列，几何/能量结构更可比，主要差异来自时间窗模式。
- 并行生成耗时：`real 2934.14s`，总 CPU 时间：`user 11600.31s`。
- 10规模 accepted：`60`；attempts：`427`；skips：`367`。

## logical_graph 汇总校验

- 校验问题数：`0`
- 复制后计数：`{'10': 60, '5': 60}`
- 模式计数：`{'tasks_10|greedy-anchor': 20, 'tasks_10|random-wave': 20, 'tasks_10|sector-wave': 20, 'tasks_5|greedy-anchor': 20, 'tasks_5|random-wave': 20, 'tasks_5|sector-wave': 20}`
- 地形计数：`{'tasks_10|apollo15_20km': 30, 'tasks_10|tranquillitatis_balmer_like_20km': 30, 'tasks_5|apollo15_20km': 30, 'tasks_5|tranquillitatis_balmer_like_20km': 30}`
- 全部复制后的 JSON 已通过 `load_future_data` 和 `FutureGraphBuilder` 读取校验。
- 5规模每个实例为完整 directed graph：6 nodes / 30 directed pair edges。
- 10规模每个实例为完整 directed graph：11 nodes / 110 directed pair edges。

## 10规模分组接受率与分布

| 地形 | 时间窗模式 | accepted/attempts | 接受率 | skip | pair可行率中位数 | triple可行率中位数 | energy pair中位数 | energy triple中位数 | window/horizon中位数 | spread/window中位数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| apollo15_20km | greedy-anchor | 10/108 | 0.093 | 98 | 0.633 | 0.354 | 0.500 | 0.083 | 0.240 | 0.203 |
| apollo15_20km | random-wave | 10/108 | 0.093 | 98 | 0.567 | 0.183 | 0.500 | 0.083 | 0.245 | 0.193 |
| apollo15_20km | sector-wave | 10/108 | 0.093 | 98 | 0.556 | 0.233 | 0.478 | 0.079 | 0.240 | 0.193 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10/21 | 0.476 | 11 | 0.711 | 0.504 | 0.478 | 0.079 | 0.242 | 0.125 |
| tranquillitatis_balmer_like_20km | random-wave | 10/21 | 0.476 | 11 | 0.689 | 0.433 | 0.478 | 0.079 | 0.242 | 0.125 |
| tranquillitatis_balmer_like_20km | sector-wave | 10/61 | 0.164 | 51 | 0.756 | 0.512 | 0.478 | 0.083 | 0.240 | 0.120 |

## 10规模 skip 原因

| 地形 | 时间窗模式 | skip原因计数 |
| --- | --- | --- |
| apollo15_20km | greedy-anchor | single task seed feasibility failed: 78; single task roundtrip infeasible after cap selection: 13; no balanced energy cap found: 3; time triple density out of band: 3; logical graph has unreachable pair: 1 |
| apollo15_20km | random-wave | single task seed feasibility failed: 78; single task roundtrip infeasible after cap selection: 14; no balanced energy cap found: 3; time triple density out of band: 2; logical graph has unreachable pair: 1 |
| apollo15_20km | sector-wave | single task seed feasibility failed: 72; time triple density out of band: 11; single task roundtrip infeasible after cap selection: 10; time pair density out of band: 3; no balanced energy cap found: 1; logical graph has unreachable pair: 1 |
| tranquillitatis_balmer_like_20km | greedy-anchor | time triple density out of band: 5; single task seed feasibility failed: 5; time pair density out of band: 1 |
| tranquillitatis_balmer_like_20km | random-wave | single task seed feasibility failed: 8; time triple density out of band: 3 |
| tranquillitatis_balmer_like_20km | sector-wave | time triple density out of band: 34; single task seed feasibility failed: 10; time pair density out of band: 7 |

## 5规模分组接受率回顾

| 地形 | 时间窗模式 | accepted/attempts | 接受率 | skip | pair可行率中位数 | triple可行率中位数 | energy pair中位数 | energy triple中位数 | window/horizon中位数 | spread/window中位数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| apollo15_20km | greedy-anchor | 10/22 | 0.455 | 12 | 0.700 | 0.550 | 0.600 | 0.200 | 0.289 | 0.134 |
| apollo15_20km | random-wave | 10/14 | 0.714 | 4 | 0.650 | 0.200 | 0.700 | 0.250 | 0.333 | 0.078 |
| apollo15_20km | sector-wave | 10/17 | 0.588 | 7 | 0.650 | 0.350 | 0.650 | 0.200 | 0.311 | 0.156 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10/51 | 0.196 | 41 | 0.700 | 0.800 | 0.600 | 0.200 | 0.302 | 0.114 |
| tranquillitatis_balmer_like_20km | random-wave | 10/10 | 1.000 | 0 | 0.900 | 0.600 | 0.700 | 0.200 | 0.311 | 0.094 |
| tranquillitatis_balmer_like_20km | sector-wave | 10/26 | 0.385 | 16 | 0.900 | 0.550 | 0.750 | 0.200 | 0.295 | 0.100 |

## 关键观察

- 10规模的筛选成本明显高于5规模，尤其 `apollo15_20km` 三个模式均为 `10/108`，接受率约 `0.093`。主要拒绝原因是 `no balanced energy cap found`，说明该地形的随机点集在当前能量密度 profile 下经常过松或不落入目标带。
- `tranquillitatis` 的 greedy/random 接受率较高，均为 `10/21`；sector-wave 为 `10/61`，说明 sector-wave 在该地形上更容易导致 time/energy density 不落带。
- 10规模 accepted 样本的 `window_width / horizon` 中位数约 `0.241`，比5规模更窄；`multi_path_spread / window_width` 中位数约 `0.130`，仍给多路径替换留有空间。
- `BPC_future/logical_graph/` 现在是后续 solver/GNN 批处理更方便的入口；若要跑求解器，直接从 `BPC_future/logical_graph/tasks_005/...` 或 `tasks_010/...` 取 JSON 即可。

