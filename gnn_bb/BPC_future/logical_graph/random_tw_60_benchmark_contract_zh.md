# BPC_future 主 benchmark 口径：分层 random-TW 60-instance

日期：2026-06-23

## 结论

后续实验、测试、加速效果、no-regression 结论和最终达标声明，都必须在分层 random-TW 60-instance 集合上给出证据。

旧 `moon_trek_60`、旧 `tranq10_01`、旧 `apollo20_physical_*` 等实例可以继续用于机制诊断、日志解剖和历史问题复现，但不能作为主效果结论。

20 规模的日常运行预算可以放宽到 600s，用来观察 proof tail、late negative、branch 行为和失败原因；但最终目标不变：canonical `tasks_020` 的 60 个实例都必须在 200s 内返回 `OPTIMAL`，600s 结果不能替代 200s 达标声明。

## Canonical 目录

主 benchmark logical graph 目录：

```text
BPC_future/logical_graph/tasks_005
BPC_future/logical_graph/tasks_010
BPC_future/logical_graph/tasks_020
BPC_future/logical_graph/tasks_030
BPC_future/logical_graph/tasks_050
BPC_future/logical_graph/tasks_100
```

每个规模 60 个实例。

## 分层结构

每个规模均为：

```text
2 个地形 × 3 个时间窗模式 × 10 个 seed = 60 个实例
```

地形：

```text
apollo15_20km
tranquillitatis_balmer_like_20km
```

时间窗模式：

```text
greedy-anchor
random-wave
sector-wave
```

这里的 random-TW 指“时间窗由带随机 seed / jitter / 可行密度筛选的生成器产生”，不是没有分类的无结构随机抽样。它是分层 benchmark：先按地形和时间窗模式分类，再在每类中保留 10 个 accepted seed。

## 效果声明规则

允许作为主效果证据：

- `BPC_future/logical_graph/tasks_005/...`
- `BPC_future/logical_graph/tasks_010/...`
- `BPC_future/logical_graph/tasks_020/...`
- `BPC_future/logical_graph/tasks_030/...`
- `BPC_future/logical_graph/tasks_050/...`
- `BPC_future/logical_graph/tasks_100/...`

不允许作为主效果证据，只能标注为诊断：

- `BPC_future/data/generated/moon_trek_60/...`
- `BPC_future/data/generated/moon_trek_balanced_60_20260609/...`
- `BPC_future/configs/apollo20_physical_*` 默认实例
- 单个旧 hard-case 的 historical probe

报告中如果使用非 canonical 实例，必须明确写：

```text
用途 = 诊断，不计入主 benchmark 效果结论
```

## 当前已验证结果

5/10 规模 600s no-regression 当前结果（V3 corrected-bound guarded fathom 合入后，默认配置）：

- 5 规模：60/60 OPTIMAL，当前 avg `0.338764s`，上一份 current avg `0.347385s`，旧基线 avg `0.321070s`。
- 10 规模：60/60 OPTIMAL，当前 avg `4.750018s`，上一份 current avg `5.479933s`，旧基线 avg `5.030619s`。

结果文件：

```text
BPC_future/results/20260623_after_v3_default_full600_randomtw60_tasks5.csv
BPC_future/results/20260623_after_v3_default_full600_randomtw60_tasks10.csv
```

20 规模当前阻塞代表：

```text
BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json
```

这是 canonical `tasks_020` 60-instance 集合内的实例，不是旧 hard-set。

20 规模 V3 诊断补充：

```text
BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json
```

在 V3 corrected-bound opt-in + 600s 下仍为 `EXTERNAL_TIME_LIMIT`，且没有 `journey_corrected_node_bound_fathom`。这不能作为 20 规模加速达标证据。

20 规模时间口径：

- 诊断/采样/尾部观察：允许 per-instance `600s`。
- 正式达标 gate：必须 per-instance `200s`，且 `60/60 OPTIMAL`。

## 2026-06-24 20规模当前水平

canonical `tasks_020` 60-instance 已按 600s 单实例预算、4 并行完成一次全量测试：

```text
csv = BPC_future/results/20260624_full600_randomtw60_tasks20_parallel4.csv
report = BPC_future/logical_graph/run_reports/20260624_bpc_future_full600_randomtw60_tasks20_parallel4_zh.md
OPTIMAL = 26/60
OPTIMAL <= 200s = 20/60
OPTIMAL > 200s = 6/60
EXTERNAL_TIME_LIMIT = 30/60
TIME_LIMIT = 4/60
```

结论：当前版本没有达到 20 规模目标；即使把诊断预算放宽到 600s，也只有 26/60 证明最优。后续任何“20 规模已加速/已达标”声明都必须覆盖这 60 个 canonical 实例，并且最终以 200s gate 为准。

## 20规模诊断日志最低口径

下一轮 20 规模 600s 诊断/采样至少应保留以下只读诊断信号：

- `journey_tail_action_audit_enabled=true`：写出 `journey_corrected_node_bound_audit`，用于 Tail Action Controller A/B/C/D 分类、水位和 productivity 统计。
- `journey_branch_candidate_log_top_n=100`：写出 `journey_branch_candidates` top-N 特征，用于 branch-impact / child-proof-cost / coverage-gap replay 采样。
- late-negative audit 输入所需的 `journey_pricing`、`journey_column_addition`、weak filtered 字段必须保留，用于区分 active-support-changing、inactive-only 和 weak/profile filtered tail。

这些字段只用于诊断和训练数据构造，不能当 official bound、certificate 或剪枝依据。行为开关仍需单独 opt-in，例如 corrected-bound fathom、tail-action early branch、branch-score/horizon candidate priority。
