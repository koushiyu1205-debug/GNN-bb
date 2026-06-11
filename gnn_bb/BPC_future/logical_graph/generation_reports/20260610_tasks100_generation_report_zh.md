# 100规模随机时间窗实例生成报告

生成日期：2026-06-10。报告语言：中文。

## 产物位置

- 合并 manifest：`BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks100_ablation_20260610/manifest.json`
- canonical logical graph：`BPC_future/logical_graph/tasks_100/`
- 校验 JSON：`BPC_future/results/20260610_tasks100_generation_validation.json`
- 分组生成日志目录：`BPC_future/results/multiscale_generation_logs/tasks_100`
- scenario、`.pt`、`.npz` tensor 仍保留在 generated part 输出目录；solver-facing logical graph JSON 只保留在 `BPC_future/logical_graph`。

## 生成与校验总览

- accepted 实例数：`60`
- attempts：`87`
- skips：`27`
- post-dedup 校验问题数：`0`
- canonical logical graph JSON 数：`60`
- generated 源目录残留 logical graph JSON 数：`0`
- 每个实例图规模：`101` nodes / `10100` directed pair edges。
- option 数范围：`29662` 到 `30142`。

## 分组接受率与关键分布

| 地形 | 时间窗模式 | accepted/attempts | 接受率 | skip | time pair中位数 | time triple中位数 | energy pair中位数 | energy triple中位数 | window/horizon中位数 | spread/window中位数 | 最小点距中位数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| apollo15_20km | greedy-anchor | 10/14 | 0.714 | 4 | 0.492 | 0.222 | 0.844 | 0.571 | 0.192 | 0.208 | 1.005 |
| apollo15_20km | random-wave | 10/14 | 0.714 | 4 | 0.400 | 0.100 | 0.844 | 0.571 | 0.197 | 0.201 | 1.005 |
| apollo15_20km | sector-wave | 10/14 | 0.714 | 4 | 0.401 | 0.108 | 0.844 | 0.571 | 0.157 | 0.262 | 1.005 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10/25 | 0.400 | 15 | 0.565 | 0.325 | 0.440 | 0.100 | 0.186 | 0.168 | 1.005 |
| tranquillitatis_balmer_like_20km | random-wave | 10/10 | 1.000 | 0 | 0.593 | 0.230 | 0.428 | 0.090 | 0.191 | 0.163 | 1.004 |
| tranquillitatis_balmer_like_20km | sector-wave | 10/10 | 1.000 | 0 | 0.609 | 0.232 | 0.428 | 0.090 | 0.145 | 0.211 | 1.004 |

## skip 原因

| 地形 | 时间窗模式 | skip原因计数 |
| --- | --- | --- |
| apollo15_20km | greedy-anchor | single task seed feasibility failed: 4 |
| apollo15_20km | random-wave | single task seed feasibility failed: 4 |
| apollo15_20km | sector-wave | single task seed feasibility failed: 4 |
| tranquillitatis_balmer_like_20km | greedy-anchor | time triple density out of band: 15 |
| tranquillitatis_balmer_like_20km | random-wave | 无 |
| tranquillitatis_balmer_like_20km | sector-wave | 无 |

## 审计解释

- `pair/triple feasible ratio`、Wilson interval 和抽样方差只用于生成筛选，不进入求解器证明逻辑。
- 正式 benchmark 默认保留完整 directed pair logical graph；没有在生成阶段剪边。
- `spread/window` 使用多路径时间差与时间窗宽度的比例，数值过高表示多路径替换空间偏窄；本报告用于后续诊断而不是过滤证明。

## 结论

- 100规模 60 个实例已生成、去重并通过读取校验，可以进入后续汇总。
