# 30规模随机时间窗实例生成报告

生成日期：2026-06-10。报告语言：中文。

## 产物位置

- 合并 manifest：`BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks30_ablation_20260610/manifest.json`
- canonical logical graph：`BPC_future/logical_graph/tasks_030/`
- 校验 JSON：`BPC_future/results/20260610_tasks30_generation_validation.json`
- 分组生成日志目录：`BPC_future/results/multiscale_generation_logs/tasks_030`
- scenario、`.pt`、`.npz` tensor 仍保留在 generated part 输出目录；solver-facing logical graph JSON 只保留在 `BPC_future/logical_graph`。

## 生成与校验总览

- accepted 实例数：`60`
- attempts：`106`
- skips：`46`
- post-dedup 校验问题数：`0`
- canonical logical graph JSON 数：`60`
- generated 源目录残留 logical graph JSON 数：`0`
- 每个实例图规模：`31` nodes / `930` directed pair edges。
- option 数范围：`2696` 到 `2786`。

## 分组接受率与关键分布

| 地形 | 时间窗模式 | accepted/attempts | 接受率 | skip | time pair中位数 | time triple中位数 | energy pair中位数 | energy triple中位数 | window/horizon中位数 | spread/window中位数 | 最小点距中位数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| apollo15_20km | greedy-anchor | 10/12 | 0.833 | 2 | 0.579 | 0.335 | 0.776 | 0.481 | 0.282 | 0.136 | 1.108 |
| apollo15_20km | random-wave | 10/10 | 1.000 | 0 | 0.533 | 0.202 | 0.785 | 0.487 | 0.236 | 0.182 | 1.108 |
| apollo15_20km | sector-wave | 10/10 | 1.000 | 0 | 0.568 | 0.281 | 0.785 | 0.487 | 0.190 | 0.213 | 1.108 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10/33 | 0.303 | 23 | 0.609 | 0.429 | 0.443 | 0.095 | 0.276 | 0.106 | 1.099 |
| tranquillitatis_balmer_like_20km | random-wave | 10/10 | 1.000 | 0 | 0.686 | 0.400 | 0.416 | 0.078 | 0.232 | 0.133 | 1.097 |
| tranquillitatis_balmer_like_20km | sector-wave | 10/31 | 0.323 | 21 | 0.692 | 0.447 | 0.471 | 0.115 | 0.180 | 0.163 | 1.074 |

## skip 原因

| 地形 | 时间窗模式 | skip原因计数 |
| --- | --- | --- |
| apollo15_20km | greedy-anchor | time triple density out of band: 2 |
| apollo15_20km | random-wave | 无 |
| apollo15_20km | sector-wave | 无 |
| tranquillitatis_balmer_like_20km | greedy-anchor | time triple density out of band: 23 |
| tranquillitatis_balmer_like_20km | random-wave | 无 |
| tranquillitatis_balmer_like_20km | sector-wave | time triple density out of band: 20; time pair density out of band: 1 |

## 审计解释

- `pair/triple feasible ratio`、Wilson interval 和抽样方差只用于生成筛选，不进入求解器证明逻辑。
- 正式 benchmark 默认保留完整 directed pair logical graph；没有在生成阶段剪边。
- `spread/window` 使用多路径时间差与时间窗宽度的比例，数值过高表示多路径替换空间偏窄；本报告用于后续诊断而不是过滤证明。

## 结论

- 30规模 60 个实例已生成、去重并通过读取校验，可以进入后续汇总。
