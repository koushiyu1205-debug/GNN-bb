# 5/10/20 no-GNN baseline 全量运行最终报告

生成时间：2026-06-11 14:12 CST。  
报告性质：最终验收版。5、10、20 规模全量均已跑完并落盘。

## 1. 执行边界

- 目标：用 no-GNN baseline 跑 5、10、20 规模全量实例。
- 时间限制：
  - 5 规模：600 秒。
  - 10 规模：600 秒。
  - 20 规模：3600 秒。
- no-GNN 覆盖参数：
  - `journey_learning_enabled=False`
  - `journey_learning_required=False`
  - `journey_learning_fail_hard=False`
  - `journey_learning_force_light_profile_pricing=False`
  - `journey_learning_prewarm_enabled=False`
  - `journey_learning_pricing_enabled=False`
- 20 规模使用外部 `timeout --kill-after 30s 3600s` 包裹单实例运行，并用 `max-workers=4` 的 controller 推进全量；CSV 逐实例追加，最终 60 行全部落盘。
- 本轮没有启用 GNN、RPCE 或 AMCB。20 规模 JSONL 聚合中 `rpce_any=0`、`amcb_any=0`、`learn_any=0`。

## 2. 产物路径

- 5 规模结果：`BPC_future/results/20260610_post360_tasks5_no_gnn_baseline.csv`
- 10 规模结果：`BPC_future/results/20260610_post360_tasks10_no_gnn_baseline.csv`
- 20 规模结果：`BPC_future/results/20260611_post360_tasks20_no_gnn_baseline_external_timeout_parallel.csv`
- 5 规模日志：`BPC_future/results/logs/20260610_post360_tasks5_no_gnn_baseline/`
- 10 规模日志：`BPC_future/results/logs/20260610_post360_tasks10_no_gnn_baseline/`
- 20 规模 JSONL 日志：`BPC_future/results/logs/20260611_post360_tasks20_no_gnn_baseline_external_timeout_parallel/`
- 20 规模 controller 日志：`BPC_future/results/20260611_post360_tasks20_no_gnn_baseline_external_timeout_parallel_controller.log`

## 3. 总体结果

| 规模 | 实例数 | 状态分布 | 是否满足目标 |
| ---: | ---: | --- | --- |
| 5 | 60 | `OPTIMAL: 60` | 满足；全量精确最优，远低于 600 秒 |
| 10 | 60 | `OPTIMAL: 60` | 满足；全量精确最优，最慢 53.04 秒 |
| 20 | 60 | `OPTIMAL: 12`, `TIME_LIMIT: 22`, `EXTERNAL_TIME_LIMIT: 26` | 不满足；仅 12/60 证明最优 |

解释：

- `OPTIMAL`：本次求解给出 primal/dual 一致的最优证书。
- `TIME_LIMIT`：solver 内部时间限制返回，`return_code=0`，但没有最优证书。
- `EXTERNAL_TIME_LIMIT`：外部 timeout 杀掉子进程，常见 `return_code=124` 或早期 `143`，没有最优证书。
- 因此 20 规模实际未证优实例为 `48/60`，远超“最多 1 个没有最优解”的要求。

## 4. 5规模结果

| 指标 | min | mean | median | p90 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| solving_time(s) | 0.233 | 0.347 | 0.306 | 0.406 | 1.416 |
| node_count | 1.000 | 1.067 | 1.000 | 1.000 | 3.000 |
| rmp_solves | 1.000 | 1.950 | 2.000 | 3.000 | 6.000 |
| pricing_calls | 4.000 | 4.583 | 4.000 | 6.000 | 12.000 |
| exact_pricing_calls | 3.000 | 3.517 | 3.000 | 5.000 | 10.000 |
| generated_sequences | 454 | 1952.267 | 1734 | 2929 | 5571 |
| evaluated_timed_trips | 228 | 901.733 | 733.5 | 1497.6 | 3473 |
| columns | 7 | 16.517 | 15 | 24.2 | 30 |

分组表现：

| 时间窗模式 | 地形 | 状态 | mean(s) | median(s) | max(s) |
| --- | --- | --- | ---: | ---: | ---: |
| greedy-anchor | apollo15_20km | `OPTIMAL: 10` | 0.421 | 0.307 | 1.416 |
| greedy-anchor | tranquillitatis_balmer_like_20km | `OPTIMAL: 10` | 0.364 | 0.363 | 0.442 |
| random-wave | apollo15_20km | `OPTIMAL: 10` | 0.330 | 0.271 | 0.868 |
| random-wave | tranquillitatis_balmer_like_20km | `OPTIMAL: 10` | 0.303 | 0.299 | 0.339 |
| sector-wave | apollo15_20km | `OPTIMAL: 10` | 0.296 | 0.311 | 0.365 |
| sector-wave | tranquillitatis_balmer_like_20km | `OPTIMAL: 10` | 0.366 | 0.328 | 0.838 |

评价：5 规模非常稳定。即使最慢实例也只有 1.416 秒，节点数基本保持在根节点，说明当前 no-GNN baseline 在 5 规模没有明显性能风险。

## 5. 10规模结果

| 指标 | min | mean | median | p90 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| solving_time(s) | 1.336 | 5.033 | 1.724 | 9.405 | 53.040 |
| node_count | 1.000 | 3.133 | 1.000 | 7.000 | 33.000 |
| rmp_solves | 1.000 | 6.133 | 3.000 | 14.000 | 47.000 |
| pricing_calls | 3.000 | 12.950 | 5.000 | 28.200 | 113.000 |
| exact_pricing_calls | 3.000 | 12.950 | 5.000 | 28.200 | 113.000 |
| generated_sequences | 298 | 15881.683 | 2834 | 26741.8 | 223160 |
| evaluated_timed_trips | 143 | 5199.417 | 1095.5 | 9116.2 | 64778 |
| columns | 20 | 65.567 | 65 | 100 | 111 |

分组表现：

| 时间窗模式 | 地形 | 状态 | mean(s) | median(s) | max(s) |
| --- | --- | --- | ---: | ---: | ---: |
| greedy-anchor | apollo15_20km | `OPTIMAL: 10` | 2.183 | 1.723 | 6.664 |
| greedy-anchor | tranquillitatis_balmer_like_20km | `OPTIMAL: 10` | 8.271 | 2.792 | 34.828 |
| random-wave | apollo15_20km | `OPTIMAL: 10` | 1.638 | 1.447 | 3.156 |
| random-wave | tranquillitatis_balmer_like_20km | `OPTIMAL: 10` | 11.472 | 1.886 | 53.040 |
| sector-wave | apollo15_20km | `OPTIMAL: 10` | 1.653 | 1.518 | 2.953 |
| sector-wave | tranquillitatis_balmer_like_20km | `OPTIMAL: 10` | 4.979 | 1.742 | 26.779 |

最慢实例：

| time(s) | instance | nodes | pricing_calls | generated_sequences | columns |
| ---: | --- | ---: | ---: | ---: | ---: |
| 53.040 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_06_seed51521_logical_graph.json` | 29 | 110 | 223160 | 103 |
| 47.011 | `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_04_seed51316_logical_graph.json` | 33 | 113 | 162745 | 88 |
| 34.828 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_10_seed51929_logical_graph.json` | 21 | 79 | 116223 | 100 |
| 26.779 | `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_09_seed51864_logical_graph.json` | 15 | 52 | 124572 | 90 |
| 18.129 | `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_08_seed51725_logical_graph.json` | 13 | 53 | 60240 | 93 |

评价：10 规模全量 60/60 均为 `OPTIMAL`，最慢 53.040 秒，满足 600 秒限制。慢例集中在 `tranquillitatis_balmer_like_20km`，并伴随节点数、pricing calls、generated sequences 同时上升。10 规模已经能看到 branch/pricing 交互变重，但仍没有进入 20 规模那种 root proof 长尾。

## 6. 20规模结果

| 指标 | min | mean | median | p90 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| solving_time(s) | 541.621 | 2771.771 | 3480.107 | 3480.639 | 3480.774 |
| wall_time(s) | 542.374 | 3136.457 | 3481.419 | 3600.013 | 3920.000 |
| node_count | 1.000 | 1.176 | 1.000 | 1.000 | 5.000 |
| rmp_solves | 6.000 | 11.265 | 11.000 | 14.700 | 21.000 |
| pricing_calls | 9.000 | 16.588 | 16.000 | 23.400 | 32.000 |
| exact_pricing_calls | 3.000 | 7.353 | 6.500 | 13.100 | 21.000 |
| generated_sequences | 72629 | 636911.882 | 634149 | 1026108.5 | 1761998 |
| evaluated_timed_trips | 12878 | 292921.265 | 212516.5 | 694009.3 | 1345782 |
| columns | 234 | 445.647 | 401 | 680.3 | 967 |

分组表现：

| 时间窗模式 | 地形 | 状态分布 | mean wall(s) | median wall(s) | max wall(s) |
| --- | --- | --- | ---: | ---: | ---: |
| greedy-anchor | apollo15_20km | `EXTERNAL_TIME_LIMIT: 4`, `TIME_LIMIT: 6` | 3560.772 | 3481.577 | 3920.000 |
| greedy-anchor | tranquillitatis_balmer_like_20km | `EXTERNAL_TIME_LIMIT: 6`, `TIME_LIMIT: 3`, `OPTIMAL: 1` | 3489.979 | 3600.007 | 3600.009 |
| random-wave | apollo15_20km | `TIME_LIMIT: 3`, `EXTERNAL_TIME_LIMIT: 4`, `OPTIMAL: 3` | 3011.658 | 3481.187 | 3600.043 |
| random-wave | tranquillitatis_balmer_like_20km | `EXTERNAL_TIME_LIMIT: 3`, `TIME_LIMIT: 4`, `OPTIMAL: 3` | 3031.121 | 3481.229 | 3600.007 |
| sector-wave | apollo15_20km | `EXTERNAL_TIME_LIMIT: 5`, `OPTIMAL: 3`, `TIME_LIMIT: 2` | 2763.465 | 3540.775 | 3600.013 |
| sector-wave | tranquillitatis_balmer_like_20km | `OPTIMAL: 2`, `TIME_LIMIT: 4`, `EXTERNAL_TIME_LIMIT: 4` | 2961.747 | 3481.119 | 3600.017 |

20 规模结果解读：

- 只有 `12/60` 实例证明 `OPTIMAL`。
- `48/60` 没有最优证书，其中 `22` 个 solver 内部 `TIME_LIMIT`，`26` 个外部 timeout。
- 多数可记录的超时实例 `node_count=1`，说明不是 branch tree 爆炸，而是根节点或很浅节点内的 pricing proof 没完成。
- `sector-wave` 相对略好，但仍只有 `5/20` OPTIMAL；不能认为换时间窗模式已经解决 20 规模问题。

## 7. 20规模日志归因

20 规模 JSONL 日志目录中当前可聚合到 57 份日志；外部硬杀实例可能没有完整 `finish` 事件，因此 CSV 是状态统计的权威来源，JSONL 用于分析瓶颈。

聚合结果：

| 指标 | 数值 |
| --- | ---: |
| `journey_exact_pricing_completion_bound_retry` 事件数 | 121 |
| hidden-negative patrol 事件数 | 121 |
| `pricing_kind=exact_completion_bound_retry` 记录数 | 99 |
| RPCE 启用/查询命中实例数 | 0 |
| AMCB 启用/查询命中实例数 | 0 |
| learning/GNN 事件数 | 0 |

按最终状态聚合的 final judge 指标：

| 状态 | 日志数 | retry事件均值 | cb pricing均值 | cb_retry_time_max均值(s) | max expanded before均值 | max expanded after均值 | max lb pruned均值 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| OPTIMAL | 12 | 1.250 | 1.250 | 1287.253 | 267182 | 96396 | 174792 |
| TIME_LIMIT | 22 | 1.364 | 1.364 | 3127.781 | 1042642 | 503824 | 538818 |
| EXTERNAL_TIME_LIMIT | 23 | 3.304 | 2.348 | 2350.500 | 1338807 | 975684 | 374923 |

典型超时实例：

| instance | status | cb_retry_time_max(s) | expanded_before | expanded_after | lb_pruned | generated_sequences | evaluated_timed_trips |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json` | TIME_LIMIT | 3461.686 | 1702840 | 1069944 | 632896 | 883300 | 425532 |
| `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json` | TIME_LIMIT | 3458.100 | 1038033 | 513200 | 524833 | 637517 | 200872 |
| `tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json` | TIME_LIMIT | 3454.870 | 1201438 | 548360 | 653078 | 858489 | 182551 |
| `apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json` | TIME_LIMIT | 3432.412 | 1393143 | 584881 | 808262 | 974282 | 212528 |
| `apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json` | TIME_LIMIT | 3406.905 | 760468 | 324621 | 435847 | 497853 | 135437 |

关键判断：

1. 20 规模失败主要来自 true-dual completion-bound final judge 的单次证明成本。
2. 不是 GNN 问题：本轮 no-GNN 覆盖参数生效，日志中无 learning/GNN 事件。
3. 不是 RPCE/AMCB 负优化：本轮两者均未启用。
4. 不是内存问题：运行期间可用内存基本保持约 `10-11 GiB`，worker RSS 通常在数百 MiB；结束后可用内存约 `11 GiB`。
5. 不是 branch tree 爆炸：20 规模可记录实例 `node_count` 中位数为 `1`，p90 仍为 `1`。
6. completion bound 有剪枝，但不够强：TIME_LIMIT 组仍出现百万级 `expanded_labels_before_bound`，剪后仍有几十万级 `expanded_labels_after_bound`。

## 8. 问题来源与原因分析

### 8.1 规模从 10 到 20 出现质变

10 规模最慢 53 秒，20 规模中位 wall time 已接近内部/外部时限。主要变化不是 RMP LP 本身，而是 pricing search space。20 规模的完整 directed pair graph 和多路径 option 使 partial label、next-sortie 组合和 completion proof 的状态空间明显扩大。

### 8.2 时间窗/电量约束让数据更真实，但没有消除 root proof 长尾

新实例的时间窗和电量约束比旧松约束更有效，确实能削掉部分不可行路径。但 20 规模仍保留足够高的 pair feasible ratio 和多路径替换空间。结果是：

- early/streaming/profile worker 能找到负列；
- RMP 可以逐步改善；
- 到 tail 阶段需要证明“没有任何 true-RC 负列”时，final judge 必须枚举或排除大量接近可行的 completion。

因此，约束收紧改善了普通列生成，但没有自动解决 final certificate。

### 8.3 Completion-bound final judge 是当前主瓶颈

日志中 `journey_exact_pricing_completion_bound_retry` 后的 exact completion-bound pricing 常消耗数千秒。典型 TIME_LIMIT 实例在一次 final judge 内耗尽约 3400 秒，仍未完成全局 no-negative 证明。

当前 bound 组合包括 bucket completion bound、two-cycle、unique-task、unique-route exact-first-step 等，但在 20 规模下仍不能把 `expanded_labels_after_bound` 压到足够小。

### 8.4 Column replacement / tail 小步仍可能存在

20 规模的一些实例在前期能不断找到负列，但 final judge 仍反复进入 retry。多路径 option 和相同 task-set 的物理替代路径会制造 replacement-only negative column，导致 RMP tail 可能小步迭代。这个问题需要继续用 active support 变化、replacement ratio、hidden negative audit 细分，而不能只看总新增列数。

### 8.5 `TIME_LIMIT` 与 `EXTERNAL_TIME_LIMIT` 的语义差异

- `TIME_LIMIT`：solver 自己返回，CSV 里通常还能保留 `node_count/pricing_calls/generated_sequences` 等诊断字段。
- `EXTERNAL_TIME_LIMIT`：外部 timeout 杀进程，诊断字段可能为空，不能当作 solver 正常结论。
- 两者都不是最优证书；都不能算作 20 规模达到目标。

## 9. 内存与运行稳定性

运行期间持续观察内存：

- 系统总内存约 `15 GiB`。
- 20 规模并发 4 worker 运行时，可用内存通常约 `10-11 GiB`。
- 结束后可用内存约 `11 GiB`。
- swap 使用约 `2.2 GiB`，但未观察到 worker 因 OOM 退出。
- 20 规模子进程大多 RSS 数百 MiB，远低于内存耗尽风险。

结论：本轮性能失败不是内存导致的，也不是后台进程失控导致的。

## 10. 最终评价

- 5 规模：通过。60/60 全精确最优，平均 0.347 秒，适合作为快速 exactness 回归。
- 10 规模：通过。60/60 全精确最优，平均 5.033 秒，最慢 53.040 秒，适合作为性能回归主层。
- 20 规模：不通过。仅 12/60 最优，48/60 未证优，根本瓶颈是 true-dual completion-bound final judge 在 root/tail 证明阶段的状态空间和单次证明成本。

当前最重要结论是：20 规模问题不是 GNN 开关、RPCE/AMCB 负优化、内存或 branch tree 数量造成的；它是 exact pricing proof path 自身没有压住状态空间。后续如果继续优化 20 规模，应优先围绕 final judge 的 completion bound、hidden-negative audit、replacement-only tail 和 support-changing column 诊断展开，而不是先调 worker 参数或重新启用 GNN。

## 11. 完成审计

- 5 规模 CSV 行数：`60`；状态：`OPTIMAL: 60`。
- 10 规模 CSV 行数：`60`；状态：`OPTIMAL: 60`。
- 20 规模 CSV 行数：`60`；状态：`OPTIMAL: 12`, `TIME_LIMIT: 22`, `EXTERNAL_TIME_LIMIT: 26`。
- 20 规模 controller 已完成，未发现仍在运行的 benchmark worker。
- 本报告已经按 5/10/20 全量结果写入。
