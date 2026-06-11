# 50规模随机时间窗实例生成报告

生成日期：2026-06-10。报告语言：中文。

## 产物位置

- 合并 manifest：`BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks50_ablation_20260610/manifest.json`
- canonical logical graph：`BPC_future/logical_graph/tasks_050/`
- 校验 JSON：`BPC_future/results/20260610_tasks50_generation_validation.json`
- 分组生成日志目录：`BPC_future/results/multiscale_generation_logs/tasks_050`
- scenario、`.pt`、`.npz` tensor 仍保留在 generated part 输出目录；solver-facing logical graph JSON 只保留在 `BPC_future/logical_graph`。

## 生成与校验总览

- accepted 实例数：`60`
- attempts：`115`
- skips：`55`
- post-dedup 校验问题数：`0`
- canonical logical graph JSON 数：`60`
- generated 源目录残留 logical graph JSON 数：`0`
- 每个实例图规模：`51` nodes / `2550` directed pair edges。
- option 数范围：`7454` 到 `7616`。

## 分组接受率与关键分布

| 地形 | 时间窗模式 | accepted/attempts | 接受率 | skip | time pair中位数 | time triple中位数 | energy pair中位数 | energy triple中位数 | window/horizon中位数 | spread/window中位数 | 最小点距中位数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| apollo15_20km | greedy-anchor | 10/12 | 0.833 | 2 | 0.509 | 0.264 | 0.755 | 0.468 | 0.228 | 0.165 | 1.017 |
| apollo15_20km | random-wave | 10/12 | 0.833 | 2 | 0.513 | 0.189 | 0.755 | 0.468 | 0.226 | 0.169 | 1.017 |
| apollo15_20km | sector-wave | 10/12 | 0.833 | 2 | 0.488 | 0.173 | 0.755 | 0.468 | 0.169 | 0.232 | 1.017 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10/48 | 0.208 | 38 | 0.573 | 0.364 | 0.413 | 0.086 | 0.225 | 0.136 | 1.022 |
| tranquillitatis_balmer_like_20km | random-wave | 10/15 | 0.667 | 5 | 0.701 | 0.372 | 0.403 | 0.086 | 0.222 | 0.140 | 1.021 |
| tranquillitatis_balmer_like_20km | sector-wave | 10/16 | 0.625 | 6 | 0.698 | 0.357 | 0.404 | 0.085 | 0.160 | 0.187 | 1.017 |

## skip 原因

| 地形 | 时间窗模式 | skip原因计数 |
| --- | --- | --- |
| apollo15_20km | greedy-anchor | single task seed feasibility failed: 2 |
| apollo15_20km | random-wave | single task seed feasibility failed: 2 |
| apollo15_20km | sector-wave | single task seed feasibility failed: 2 |
| tranquillitatis_balmer_like_20km | greedy-anchor | time triple density out of band: 38 |
| tranquillitatis_balmer_like_20km | random-wave | time triple density out of band: 5 |
| tranquillitatis_balmer_like_20km | sector-wave | time triple density out of band: 6 |

## 审计解释

- `pair/triple feasible ratio`、Wilson interval 和抽样方差只用于生成筛选，不进入求解器证明逻辑。
- 正式 benchmark 默认保留完整 directed pair logical graph；没有在生成阶段剪边。
- `spread/window` 使用多路径时间差与时间窗宽度的比例，数值过高表示多路径替换空间偏窄；本报告用于后续诊断而不是过滤证明。

## 结论

- 50规模 60 个实例已生成、去重并通过读取校验，可以进入后续汇总。
