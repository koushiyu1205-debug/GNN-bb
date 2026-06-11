# 20规模随机时间窗实例生成报告

生成日期：2026-06-10。报告语言：中文。

## 产物位置

- 合并 manifest：`BPC_future/data/generated/moon_trek_multiscale_random_tw_tasks20_ablation_20260610/manifest.json`
- canonical logical graph：`BPC_future/logical_graph/tasks_020/`
- 校验 JSON：`BPC_future/results/20260610_tasks20_generation_validation.json`
- 分组生成日志目录：`BPC_future/results/multiscale_generation_logs/tasks_020`
- scenario、`.pt`、`.npz` tensor 仍保留在 generated part 输出目录；solver-facing logical graph JSON 只保留在 `BPC_future/logical_graph`。

## 生成与校验总览

- accepted 实例数：`60`
- attempts：`105`
- skips：`45`
- post-dedup 校验问题数：`0`
- canonical logical graph JSON 数：`60`
- generated 源目录残留 logical graph JSON 数：`0`
- 每个实例图规模：`21` nodes / `420` directed pair edges。
- option 数范围：`1220` 到 `1260`。

## 分组接受率与关键分布

| 地形 | 时间窗模式 | accepted/attempts | 接受率 | skip | time pair中位数 | time triple中位数 | energy pair中位数 | energy triple中位数 | window/horizon中位数 | spread/window中位数 | 最小点距中位数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| apollo15_20km | greedy-anchor | 10/13 | 0.769 | 3 | 0.634 | 0.396 | 0.761 | 0.461 | 0.247 | 0.163 | 1.138 |
| apollo15_20km | random-wave | 10/11 | 0.909 | 1 | 0.642 | 0.245 | 0.745 | 0.457 | 0.256 | 0.153 | 1.263 |
| apollo15_20km | sector-wave | 10/11 | 0.909 | 1 | 0.529 | 0.257 | 0.745 | 0.457 | 0.180 | 0.225 | 1.263 |
| tranquillitatis_balmer_like_20km | greedy-anchor | 10/40 | 0.250 | 30 | 0.708 | 0.458 | 0.379 | 0.062 | 0.242 | 0.118 | 1.100 |
| tranquillitatis_balmer_like_20km | random-wave | 10/15 | 0.667 | 5 | 0.705 | 0.449 | 0.397 | 0.077 | 0.247 | 0.124 | 1.177 |
| tranquillitatis_balmer_like_20km | sector-wave | 10/15 | 0.667 | 5 | 0.679 | 0.391 | 0.397 | 0.072 | 0.160 | 0.178 | 1.089 |

## skip 原因

| 地形 | 时间窗模式 | skip原因计数 |
| --- | --- | --- |
| apollo15_20km | greedy-anchor | time triple density out of band: 2; single task seed feasibility failed: 1 |
| apollo15_20km | random-wave | single task seed feasibility failed: 1 |
| apollo15_20km | sector-wave | single task seed feasibility failed: 1 |
| tranquillitatis_balmer_like_20km | greedy-anchor | time triple density out of band: 30 |
| tranquillitatis_balmer_like_20km | random-wave | time triple density out of band: 5 |
| tranquillitatis_balmer_like_20km | sector-wave | time triple density out of band: 5 |

## 审计解释

- `pair/triple feasible ratio`、Wilson interval 和抽样方差只用于生成筛选，不进入求解器证明逻辑。
- 正式 benchmark 默认保留完整 directed pair logical graph；没有在生成阶段剪边。
- `spread/window` 使用多路径时间差与时间窗宽度的比例，数值过高表示多路径替换空间偏窄；本报告用于后续诊断而不是过滤证明。

## 结论

- 20规模 60 个实例已生成、去重并通过读取校验，可以进入后续汇总。
